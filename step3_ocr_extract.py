"""
Script para extraer información de imágenes usando OCR (pytesseract).
Lee las imágenes de la carpeta output_images y extrae la información estructurada.
"""
import os
import json
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Configuración de pytesseract (ajustar según tu instalación)
# En Windows, descomentar y ajustar la ruta si es necesario:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    """
    Pre-procesa la imagen para mejorar el OCR
    
    Args:
        image_path: Ruta a la imagen
        
    Returns:
        Imagen procesada
    """
    # Leer imagen con OpenCV
    img = cv2.imread(image_path)
    
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbral adaptativo para mejorar contraste
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Reducir ruido
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised

def extract_text_from_image(image_path, preprocess=True):
    """
    Extrae texto de una imagen usando OCR
    
    Args:
        image_path: Ruta a la imagen
        preprocess: Si debe preprocesar la imagen
        
    Returns:
        Texto extraído
    """
    try:
        if preprocess:
            # Usar imagen preprocesada
            img = preprocess_image(image_path)
            # Convertir numpy array a PIL Image
            img_pil = Image.fromarray(img)
        else:
            # Usar imagen original
            img_pil = Image.open(image_path)
        
        # Configuración de pytesseract para español
        custom_config = r'--oem 3 --psm 6 -l spa'
        
        # Extraer texto
        text = pytesseract.image_to_string(img_pil, config=custom_config)
        
        return text
    
    except Exception as e:
        print(f"❌ Error al extraer texto de {image_path}: {str(e)}")
        return ""

def parse_vehicle_data(text, plate_number):
    """
    Parsea el texto extraído y estructura la información del vehículo
    
    Args:
        text: Texto extraído por OCR
        plate_number: Número de placa para referencia
        
    Returns:
        Diccionario con información estructurada
    """
    data = {
        'placa': plate_number,
        'marca': '',
        'modelo': '',
        'año_fabricacion': '',
        'año_modelo': '',
        'color': '',
        'n_motor': '',
        'n_serie': '',
        'clase': '',
        'tipo': '',
        'carroceria': '',
        'combustible': '',
        'cilindros': '',
        'asientos': '',
        'pasajeros': '',
        'propietario': '',
        'documento': '',
        'sede': '',
        'raw_text': text
    }
    
    # Normalizar texto para búsqueda
    text_upper = text.upper()
    lines = text.split('\n')
    
    # Patrones de búsqueda
    patterns = {
        'placa': r'PLACA[:\s]*([A-Z0-9\-]+)',
        'marca': r'MARCA[:\s]*([A-Z\s]+)',
        'modelo': r'MODELO[:\s]*([A-Z0-9\s]+)',
        'año_fabricacion': r'(?:AÑO|ANO)[\s]*(?:DE)?[\s]*(?:FABRICACION|FABRICACIÓN)[:\s]*(\d{4})',
        'año_modelo': r'(?:AÑO|ANO)[\s]*MODELO[:\s]*(\d{4})',
        'color': r'COLOR[:\s]*([A-Z\s]+)',
        'n_motor': r'(?:N[°º]?|NUMERO)[\s]*(?:DE)?[\s]*MOTOR[:\s]*([A-Z0-9]+)',
        'n_serie': r'(?:N[°º]?|NUMERO)[\s]*(?:DE)?[\s]*SERIE[:\s]*([A-Z0-9]+)',
        'clase': r'CLASE[:\s]*([A-Z\s]+)',
        'tipo': r'TIPO[:\s]*([A-Z\s]+)',
        'carroceria': r'CARROCER[ÍI]A[:\s]*([A-Z\s]+)',
        'combustible': r'COMBUSTIBLE[:\s]*([A-Z\s]+)',
        'cilindros': r'CILINDROS[:\s]*(\d+)',
        'asientos': r'(?:N[°º]?|NUMERO)[\s]*ASIENTOS[:\s]*(\d+)',
        'pasajeros': r'(?:N[°º]?|NUMERO)[\s]*PASAJEROS[:\s]*(\d+)',
        'documento': r'(?:DNI|RUC)[:\s]*(\d+)',
    }
    
    # Buscar patrones en el texto
    for key, pattern in patterns.items():
        match = re.search(pattern, text_upper)
        if match:
            value = match.group(1).strip()
            data[key] = value
    
    # Búsqueda de propietario (más compleja)
    propietario_match = re.search(
        r'PROPIETARIO[:\s]*([A-ZÑÁÉÍÓÚ\s]+)(?:\n|DNI|RUC)',
        text_upper
    )
    if propietario_match:
        data['propietario'] = propietario_match.group(1).strip()
    
    # Búsqueda de sede
    sede_match = re.search(r'SEDE[:\s]*([A-ZÑÁÉÍÓÚ\s]+)', text_upper)
    if sede_match:
        data['sede'] = sede_match.group(1).strip()
    
    return data

def process_images(input_folder='output_images', output_file='vehicle_data_extracted.json'):
    """
    Procesa todas las imágenes en la carpeta y extrae información
    
    Args:
        input_folder: Carpeta con las imágenes
        output_file: Archivo JSON donde guardar los resultados
    """
    print("\n" + "="*60)
    print("OCR - EXTRACCIÓN DE DATOS VEHICULARES")
    print("="*60)
    
    if not os.path.exists(input_folder):
        print(f"❌ Error: La carpeta {input_folder} no existe")
        print("   Por favor, ejecuta primero step2_scrape_sunarp.py")
        return
    
    # Obtener lista de imágenes
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        and not 'ERROR' in f.upper()
    ]
    
    if not image_files:
        print(f"❌ No se encontraron imágenes en {input_folder}")
        return
    
    print(f"\n✓ Encontradas {len(image_files)} imágenes para procesar")
    
    # Verificar instalación de Tesseract
    try:
        pytesseract.get_tesseract_version()
        print("✓ Tesseract-OCR detectado")
    except Exception as e:
        print("\n❌ ERROR: Tesseract-OCR no está instalado o no se encuentra en el PATH")
        print("\nPara instalar Tesseract:")
        print("1. Windows: Descarga desde https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Linux: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
        print("3. Mac: brew install tesseract tesseract-lang")
        print("\nDespués de instalar, actualiza la ruta en el script si es necesario.")
        return
    
    results = []
    successful = 0
    failed = 0
    
    for idx, image_file in enumerate(image_files, 1):
        image_path = os.path.join(input_folder, image_file)
        plate_number = os.path.splitext(image_file)[0].replace('_resultado', '')
        
        print(f"\n[{idx}/{len(image_files)}] Procesando: {image_file}")
        print(f"   Placa: {plate_number}")
        
        try:
            # Extraer texto con preprocesamiento
            print("   ⚙️  Aplicando OCR...")
            text = extract_text_from_image(image_path, preprocess=True)
            
            if not text.strip():
                print("   ⚠️  No se extrajo texto, intentando sin preprocesamiento...")
                text = extract_text_from_image(image_path, preprocess=False)
            
            if text.strip():
                print(f"   ✓ Texto extraído ({len(text)} caracteres)")
                
                # Parsear datos
                print("   ⚙️  Estructurando información...")
                vehicle_data = parse_vehicle_data(text, plate_number)
                results.append(vehicle_data)
                
                # Mostrar algunos campos extraídos
                print(f"   ✓ Marca: {vehicle_data['marca'] or 'N/A'}")
                print(f"   ✓ Modelo: {vehicle_data['modelo'] or 'N/A'}")
                print(f"   ✓ Año: {vehicle_data['año_fabricacion'] or 'N/A'}")
                
                successful += 1
            else:
                print("   ❌ No se pudo extraer texto de la imagen")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed += 1
    
    # Guardar resultados
    if results:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Resultados guardados en: {output_file}")
        
        # También guardar un CSV para fácil análisis
        csv_file = output_file.replace('.json', '.csv')
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            # Excluir la columna raw_text del CSV
            df_csv = df.drop('raw_text', axis=1, errors='ignore')
            df_csv.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"✓ CSV guardado en: {csv_file}")
        except Exception as e:
            print(f"⚠️  No se pudo crear CSV: {e}")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE EXTRACCIÓN")
    print("="*60)
    print(f"Total de imágenes procesadas: {successful + failed}")
    print(f"✓ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    print("="*60)

def main():
    """Función principal"""
    process_images()

if __name__ == "__main__":
    main()
