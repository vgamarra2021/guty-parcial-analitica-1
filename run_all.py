"""
Script principal que ejecuta todo el flujo de trabajo
"""
import subprocess
import sys
import os

def run_script(script_name, description):
    """
    Ejecuta un script de Python y muestra el resultado
    
    Args:
        script_name: Nombre del script a ejecutar
        description: Descripción del paso
    """
    print("\n" + "="*70)
    print(f"  {description}")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {description} completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error en {description}")
        print(f"   Código de error: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ No se encontró el script: {script_name}")
        return False

def main():
    """
    Ejecuta el flujo completo de trabajo
    """
    print("\n" + "="*70)
    print("  SUNARP SCRAPER - FLUJO COMPLETO")
    print("="*70)
    print("\nEste script ejecutará los 3 pasos en secuencia:")
    print("  1. Extracción de placas del dataset")
    print("  2. Scraping de SUNARP (requiere intervención manual para CAPTCHA)")
    print("  3. Extracción de datos con OCR")
    
    response = input("\n¿Deseas continuar? (s/n): ").strip().lower()
    if response != 's':
        print("Operación cancelada.")
        return
    
    # Paso 1: Extraer placas
    success = run_script('step1_extract_plates.py', 'PASO 1: Extracción de placas')
    if not success:
        print("\n❌ No se pudo completar el Paso 1. Abortando...")
        return
    
    # Verificar que se creó el archivo de placas
    if not os.path.exists('plates_data.json'):
        print("\n❌ No se generó el archivo plates_data.json. Abortando...")
        return
    
    # Paso 2: Scraping
    print("\n" + "="*70)
    print("  IMPORTANTE - PASO 2")
    print("="*70)
    print("El siguiente paso abrirá un navegador y consultará SUNARP.")
    print("Necesitarás resolver CAPTCHAs manualmente.")
    print("El navegador se mantendrá abierto y el script esperará tu intervención.")
    
    response = input("\n¿Estás listo para iniciar el scraping? (s/n): ").strip().lower()
    if response != 's':
        print("\nPuedes ejecutar el scraping manualmente más tarde con:")
        print("  python step2_scrape_sunarp.py")
        print("\nContinuando sin scraping...")
    else:
        success = run_script('step2_scrape_sunarp.py', 'PASO 2: Scraping de SUNARP')
        if not success:
            print("\n⚠️  El scraping no se completó correctamente.")
            print("Puedes intentarlo nuevamente ejecutando:")
            print("  python step2_scrape_sunarp.py")
    
    # Verificar que existan imágenes
    if not os.path.exists('output_images') or not os.listdir('output_images'):
        print("\n⚠️  No se encontraron imágenes en output_images/")
        print("No se puede continuar con el OCR.")
        print("\nPor favor ejecuta primero:")
        print("  python step2_scrape_sunarp.py")
        return
    
    # Paso 3: OCR
    print("\n" + "="*70)
    print("  PASO 3: EXTRACCIÓN CON OCR")
    print("="*70)
    print("Este paso procesará las imágenes capturadas.")
    print("Asegúrate de tener Tesseract-OCR instalado.")
    
    response = input("\n¿Deseas procesar las imágenes con OCR? (s/n): ").strip().lower()
    if response != 's':
        print("\nPuedes ejecutar el OCR manualmente más tarde con:")
        print("  python step3_ocr_extract.py")
    else:
        success = run_script('step3_ocr_extract.py', 'PASO 3: Extracción con OCR')
        if not success:
            print("\n⚠️  El OCR no se completó correctamente.")
            print("Verifica que Tesseract-OCR esté instalado correctamente.")
    
    # Resumen final
    print("\n" + "="*70)
    print("  PROCESO COMPLETADO")
    print("="*70)
    print("\nArchivos generados:")
    if os.path.exists('plates_data.json'):
        print("  ✓ plates_data.json")
    if os.path.exists('output_images'):
        num_images = len([f for f in os.listdir('output_images') if f.endswith('.png')])
        print(f"  ✓ output_images/ ({num_images} imágenes)")
    if os.path.exists('vehicle_data_extracted.json'):
        print("  ✓ vehicle_data_extracted.json")
    if os.path.exists('vehicle_data_extracted.csv'):
        print("  ✓ vehicle_data_extracted.csv")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
