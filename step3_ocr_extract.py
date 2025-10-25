"""
Script para extraer información de imágenes usando OCR (EasyOCR).
Lee las imágenes de la carpeta output_images y extrae la información estructurada.
"""
import os
import json
import re
from PIL import Image
import easyocr
import cv2
import numpy as np

# Inicializar el lector de EasyOCR (se hará una sola vez)
reader = None

def crop_image(image_path):
    """
    Recorta la imagen eliminando partes superior e inferior no relevantes
    
    Args:
        image_path: Ruta a la imagen
        
    Returns:
        Imagen recortada (numpy array)
    """
    # Leer imagen
    img = cv2.imread(image_path)
    
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    
    height, width = img.shape[:2]
    
    # Eliminar 120px de arriba y 10px de abajo
    top_crop = 120
    bottom_crop = 10
    
    # Validar que la imagen sea lo suficientemente grande
    if height <= (top_crop + bottom_crop):
        print(f"   ⚠️  Imagen muy pequeña para recortar, usando imagen completa")
        return img
    
    # Recortar imagen: [inicio_y:fin_y, inicio_x:fin_x]
    cropped = img[top_crop:height-bottom_crop, :]
    
    return cropped

def preprocess_image(image_path):
    """
    Pre-procesa la imagen para mejorar el OCR, eliminando marcas de agua
    
    Args:
        image_path: Ruta a la imagen
        
    Returns:
        Imagen procesada
    """
    # Primero recortar la imagen para eliminar áreas no relevantes
    img = crop_image(image_path)
    
    # Convertir de BGR a RGB para trabajar con colores correctamente
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Eliminar el color gris de la marca de agua (#E3E3E3 y tonos similares)
    # Convertir a HSV para mejor detección de colores
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Definir rango de colores grises claros (marca de agua)
    lower_gray = np.array([0, 0, 200])    # H, S, V
    upper_gray = np.array([180, 30, 245])  # Captura grises claros como #E3E3E3
    
    # Crear máscara para la marca de agua
    mask_watermark = cv2.inRange(img_hsv, lower_gray, upper_gray)
    
    # Aplicar la máscara - hacer la marca de agua blanca
    img_no_watermark = img.copy()
    img_no_watermark[mask_watermark > 0] = [255, 255, 255]  # Blanco
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img_no_watermark, cv2.COLOR_BGR2GRAY)
    
    # Aumentar el contraste para hacer el texto más oscuro y legible
    # Usar CLAHE antes de la umbralización
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Aplicar sharpening para hacer el texto más nítido
    kernel_sharpen = np.array([[-1,-1,-1],
                               [-1, 9,-1],
                               [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
    
    # Usar umbralización de Otsu para separar texto del fondo
    _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invertir si el fondo es oscuro
    white_pixels = np.sum(thresh == 255)
    black_pixels = np.sum(thresh == 0)
    
    if black_pixels > white_pixels:
        thresh = cv2.bitwise_not(thresh)
    
    # Dilatar ligeramente el texto para hacerlo más grueso y legible
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    return dilated

def preprocess_image_alternative(image_path):
    """
    Método alternativo de preprocesamiento más agresivo
    
    Args:
        image_path: Ruta a la imagen
        
    Returns:
        Imagen procesada
    """
    # Primero recortar la imagen
    img = crop_image(image_path)
    
    # Método alternativo: Eliminar marca de agua por rango de color en RGB
    # #E3E3E3 = RGB(227, 227, 227)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Definir rango de colores grises claros en RGB
    lower_gray_rgb = np.array([210, 210, 210])  # Un poco más oscuro que #E3E3E3
    upper_gray_rgb = np.array([240, 240, 240])  # Un poco más claro
    
    # Crear máscara para píxeles grises (marca de agua)
    mask = cv2.inRange(img_rgb, lower_gray_rgb, upper_gray_rgb)
    
    # Convertir píxeles de marca de agua a blanco
    img_clean = img.copy()
    img_clean[mask > 0] = [255, 255, 255]
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img_clean, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbral adaptativo agresivo
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )
    
    # Invertir si es necesario
    white_pixels = np.sum(thresh == 255)
    black_pixels = np.sum(thresh == 0)
    if black_pixels > white_pixels:
        thresh = cv2.bitwise_not(thresh)
    
    return thresh

def extract_text_from_image(image_path, preprocess=True):
    """
    Extrae texto de una imagen usando OCR (EasyOCR)
    
    Args:
        image_path: Ruta a la imagen
        preprocess: Si debe preprocesar la imagen
        
    Returns:
        Texto extraído
    """
    global reader
    
    try:
        # Inicializar el lector si no existe
        if reader is None:
            print("   ⚙️  Inicializando EasyOCR (esto puede tomar un momento la primera vez)...")
            reader = easyocr.Reader(['es', 'en'], gpu=False)  # Español e Inglés
        
        # Leer la imagen
        if preprocess:
            # Intentar con preprocesamiento principal
            img = preprocess_image(image_path)
        else:
            # Usar imagen recortada pero sin preprocesamiento adicional
            img = crop_image(image_path)
        
        # Realizar OCR con configuración para mejor detección
        # Parámetros ajustados para reconocer texto normal (no solo negrita)
        results = reader.readtext(
            img, 
            detail=0, 
            paragraph=False,  # No agrupar en párrafos, obtener línea por línea
            batch_size=8,
            text_threshold=0.5,  # Umbral más bajo para captar texto normal
            low_text=0.2,  # Umbral muy bajo para detectar texto tenue
            link_threshold=0.3,  # Umbral para unir palabras
            width_ths=0.7,  # Ancho para combinar cajas de texto
            height_ths=0.7,  # Alto para combinar cajas
            decoder='greedy',  # Decodificador más rápido
            beamWidth=5,
            contrast_ths=0.1,  # Umbral de contraste bajo para texto suave
            adjust_contrast=0.5  # Ajustar contraste
        )
        
        # Si no se obtuvo suficiente texto, intentar con método alternativo
        if len(results) < 5 or len('\n'.join(results)) < 50:
            print("   ⚙️  Probando con preprocesamiento alternativo...")
            img_alt = preprocess_image_alternative(image_path)
            results_alt = reader.readtext(
                img_alt,
                detail=0,
                paragraph=False,
                batch_size=8,
                text_threshold=0.4,
                low_text=0.2,
                contrast_ths=0.1,
                adjust_contrast=0.5
            )
            # Usar el resultado con más texto
            if len('\n'.join(results_alt)) > len('\n'.join(results)):
                results = results_alt
                print(f"   ✓ Método alternativo obtuvo más texto")
        
        # Si aún no hay resultados, intentar sin preprocesamiento
        if len(results) < 5:
            print("   ⚙️  Probando sin preprocesamiento...")
            img_original = crop_image(image_path)  # Usar recortada
            results_orig = reader.readtext(
                img_original,
                detail=0,
                paragraph=False,
                batch_size=8,
                text_threshold=0.4,
                low_text=0.2
            )
            if len('\n'.join(results_orig)) > len('\n'.join(results)):
                results = results_orig
                print(f"   ✓ Sin preprocesamiento obtuvo más texto")
        
        # Unir todos los textos
        text = '\n'.join(results)
        
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
        'n_serie': '',
        'n_vin': '',
        'n_motor': '',
        'color': '',
        'marca': '',
        'modelo': '',
        'placa_vigente': '',
        'placa_anterior': '',
        'estado': '',
        'anotaciones': '',
        'sede': '',
        'año_modelo': '',
        'propietarios': '',
        'raw_text': text
    }
    
    # Normalizar texto para búsqueda
    text_upper = text.upper()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Patrones mejorados basados en el formato visual de SUNARP
    # Los campos vienen como "ETIQUETA: VALOR" o "ETIQUETA:VALOR"
    patterns = {
        'placa': [
            r'N[°º]?\s*PLACA\s*[:\s]+\s*([A-Z0-9\-]+)',
            r'PLACA\s*[:\s]+\s*([A-Z0-9\-]+)',
        ],
        'n_serie': [
            r'N[°º]?\s*SERIE\s*[:\s]+\s*([A-Z0-9]+)',
            r'SERIE\s*[:\s]+\s*([A-Z0-9]+)',
        ],
        'n_vin': [
            r'N[°º]?\s*VIN\s*[:\s]+\s*([A-Z0-9]+)',
            r'VIN\s*[:\s]+\s*([A-Z0-9]+)',
        ],
        'n_motor': [
            r'N[°º]?\s*MOTOR\s*[:\s]+\s*([A-Z0-9]+)',
            r'MOTOR\s*[:\s]+\s*([A-Z0-9]+)',
        ],
        'color': [
            r'COLOR\s*[:\s]+\s*([A-Z\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'marca': [
            r'MARCA\s*[:\s]+\s*([A-Z\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'modelo': [
            r'MODELO\s*[:\s]+\s*([A-Z0-9\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'placa_vigente': [
            r'PLACA\s+VIGENTE\s*[:\s]+\s*([A-Z0-9\-]+)',
        ],
        'placa_anterior': [
            r'PLACA\s+ANTERIOR\s*[:\s]*\s*([A-Z0-9\-]+|NINGUNA)',
        ],
        'estado': [
            r'ESTADO\s*[:\s]+\s*([A-Z\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'anotaciones': [
            r'ANOTACIONES\s*[:\s]+\s*([A-Z\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'sede': [
            r'SEDE\s*[:\s]+\s*([A-Z\s]+?)(?=\s*$|\s*[A-Z]+\s*:)',
        ],
        'año_modelo': [
            r'A[ÑN]O\s+DE\s+MODELO\s*[:\s]+\s*(\d{4})',
            r'A[ÑN]O\s+MODELO\s*[:\s]+\s*(\d{4})',
        ],
        'propietarios': [
            r'PROPIETARIO\s*\(\s*S\s*\)\s*[:\s]+\s*(.+?)(?=\n\n|\Z)',
            r'PROPIETARIOS\s*[:\s]+\s*(.+?)(?=\n\n|\Z)',
        ],
    }
    
    # Buscar patrones en el texto
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_upper, re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Limpiar espacios múltiples
                value = re.sub(r'\s+', ' ', value)
                data[key] = value
                break  # Usar el primer patrón que coincida
    
    # Método alternativo: buscar línea por línea
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        # N° PLACA:
        if 'PLACA' in line_upper and 'VIGENTE' not in line_upper and 'ANTERIOR' not in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['placa']:
                data['placa'] = parts[-1].strip()
        
        # N° SERIE:
        if line_upper.startswith('N') and 'SERIE' in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=2)
            if len(parts) > 1 and not data['n_serie']:
                data['n_serie'] = parts[-1].strip()
        
        # N° VIN:
        if 'VIN' in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=2)
            if len(parts) > 1 and not data['n_vin']:
                data['n_vin'] = parts[-1].strip()
        
        # N° MOTOR:
        if 'MOTOR' in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=2)
            if len(parts) > 1 and not data['n_motor']:
                data['n_motor'] = parts[-1].strip()
        
        # COLOR:
        if line_upper.startswith('COLOR'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['color']:
                data['color'] = parts[-1].strip()
        
        # MARCA:
        if line_upper.startswith('MARCA'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['marca']:
                data['marca'] = parts[-1].strip()
        
        # MODELO:
        if line_upper.startswith('MODELO'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['modelo']:
                data['modelo'] = parts[-1].strip()
        
        # PLACA VIGENTE:
        if 'PLACA' in line_upper and 'VIGENTE' in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=2)
            if len(parts) > 1 and not data['placa_vigente']:
                data['placa_vigente'] = parts[-1].strip()
        
        # PLACA ANTERIOR:
        if 'PLACA' in line_upper and 'ANTERIOR' in line_upper:
            parts = re.split(r'[:\s]+', line_upper, maxsplit=2)
            if len(parts) > 1 and not data['placa_anterior']:
                data['placa_anterior'] = parts[-1].strip()
        
        # ESTADO:
        if line_upper.startswith('ESTADO'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['estado']:
                data['estado'] = parts[-1].strip()
        
        # ANOTACIONES:
        if line_upper.startswith('ANOTACIONES'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['anotaciones']:
                data['anotaciones'] = parts[-1].strip()
        
        # SEDE:
        if line_upper.startswith('SEDE'):
            parts = re.split(r'[:\s]+', line_upper, maxsplit=1)
            if len(parts) > 1 and not data['sede']:
                data['sede'] = parts[-1].strip()
        
        # AÑO DE MODELO:
        if 'AÑO' in line_upper and 'MODELO' in line_upper:
            parts = re.split(r'[:\s]+', line_upper)
            if len(parts) > 1 and not data['año_modelo']:
                # Buscar el año (4 dígitos)
                for part in parts:
                    if re.match(r'\d{4}', part):
                        data['año_modelo'] = part.strip()
                        break
        
        # PROPIETARIO(S):
        if 'PROPIETARIO' in line_upper:
            # Capturar desde esta línea hasta el final o línea vacía
            propietario_text = []
            for j in range(i, len(lines)):
                if 'PROPIETARIO' in lines[j].upper():
                    parts = re.split(r'[:\s]+', lines[j], maxsplit=1)
                    if len(parts) > 1:
                        propietario_text.append(parts[-1])
                elif lines[j].strip() and not ':' in lines[j]:
                    propietario_text.append(lines[j])
                elif not lines[j].strip() or ':' in lines[j]:
                    break
            if propietario_text and not data['propietarios']:
                data['propietarios'] = ' '.join(propietario_text).strip()
    
    # Si no se encontró la placa en el texto, usar el nombre del archivo
    if not data['placa'] or data['placa'] == 'N/A':
        data['placa'] = plate_number
    
    return data

def process_images(input_folder='output_images', output_file='vehicle_data_extracted.csv'):
    """
    Procesa todas las imágenes en la carpeta y extrae información
    
    Args:
        input_folder: Carpeta con las imágenes
        output_file: Archivo CSV donde guardar los resultados
    """
    print("\n" + "="*60)
    print("OCR - EXTRACCIÓN DE DATOS VEHICULARES")
    print("="*60)
    
    if not os.path.exists(input_folder):
        print(f"❌ Error: La carpeta {input_folder} no existe")
        print("   Por favor, ejecuta primero step2_scrape_sunarp.py")
        return
    
    # Obtener lista de imágenes - SOLO las que terminan en _resultado.png
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith('_resultado.png')
        and not 'ERROR' in f.upper()
    ]
    
    if not image_files:
        print(f"❌ No se encontraron imágenes con formato *_resultado.png en {input_folder}")
        return
    
    print(f"\n✓ Encontradas {len(image_files)} imágenes '_resultado.png' para procesar")
    
    # Verificar instalación de EasyOCR
    try:
        print("✓ EasyOCR disponible")
        print("ℹ️  Nota: La primera ejecución descargará modelos (~100MB), puede tardar unos minutos")
    except Exception as e:
        print(f"\n❌ ERROR: EasyOCR no está disponible: {str(e)}")
        print("\nPara instalar: pip install easyocr")
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
                
                # Mostrar campos extraídos
                print(f"   ✓ Placa: {vehicle_data['placa'] or 'N/A'}")
                print(f"   ✓ Serie: {vehicle_data['n_serie'] or 'N/A'}")
                print(f"   ✓ Motor: {vehicle_data['n_motor'] or 'N/A'}")
                print(f"   ✓ Marca: {vehicle_data['marca'] or 'N/A'}")
                print(f"   ✓ Modelo: {vehicle_data['modelo'] or 'N/A'}")
                print(f"   ✓ Color: {vehicle_data['color'] or 'N/A'}")
                print(f"   ✓ Estado: {vehicle_data['estado'] or 'N/A'}")
                print(f"   ✓ Propietario(s): {vehicle_data['propietarios'][:50] or 'N/A'}...")
                
                successful += 1
            else:
                print("   ❌ No se pudo extraer texto de la imagen")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed += 1
    
    # Guardar resultados
    if results:
        # Convertir a DataFrame
        import pandas as pd
        df = pd.DataFrame(results)
        
        # Reordenar columnas para mejor visualización
        columns_order = [
            'placa', 'n_serie', 'n_vin', 'n_motor', 'color', 'marca', 'modelo',
            'placa_vigente', 'placa_anterior', 'estado', 'anotaciones', 'sede',
            'año_modelo', 'propietarios', 'raw_text'
        ]
        
        # Asegurar que todas las columnas existan
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[columns_order]
        
        # Guardar como CSV (principal)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Resultados guardados en CSV: {output_file}")
        
        # También guardar como JSON (backup)
        json_file = output_file.replace('.csv', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✓ Backup JSON guardado en: {json_file}")
        
        # Crear un CSV simplificado sin raw_text para fácil lectura
        simple_csv = output_file.replace('.csv', '_simple.csv')
        df_simple = df.drop('raw_text', axis=1, errors='ignore')
        df_simple.to_csv(simple_csv, index=False, encoding='utf-8-sig')
        print(f"✓ CSV simplificado (sin raw_text) guardado en: {simple_csv}")
    
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
