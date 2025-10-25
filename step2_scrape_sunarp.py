"""
Script para hacer scraping de consulta vehicular en SUNARP.
Consulta cada placa y guarda la imagen con los resultados.

Características:
- Delay de 10 segundos entre consultas
- Resolución manual de CAPTCHA por defecto
- Opción para usar LLM con visión (requiere API key)
- Guarda imágenes de resultados en carpeta output_images
"""
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import base64

# Configuración
USE_LLM_FOR_CAPTCHA = False  # Por defecto manual
LLM_API_KEY = ""  # Agregar tu API key aquí si quieres usar LLM

def setup_driver():
    """Configura y retorna el driver de Selenium"""
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Comentado para ver el navegador
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def solve_captcha_manual(driver):
    """
    Espera a que el usuario resuelva el CAPTCHA manualmente
    """
    print("\n" + "="*60)
    print("⚠️  CAPTCHA DETECTADO - RESOLUCIÓN MANUAL REQUERIDA")
    print("="*60)
    print("Por favor:")
    print("1. Resuelve el CAPTCHA en la ventana del navegador")
    print("2. Presiona ENTER aquí cuando hayas completado el CAPTCHA")
    print("="*60)
    
    input("Presiona ENTER después de resolver el CAPTCHA...")
    print("✓ Continuando con la consulta...")
    
    # Dar tiempo adicional para que se procese
    time.sleep(2)

def solve_captcha_llm(driver, api_key):
    """
    Resuelve el CAPTCHA usando un LLM con capacidades de visión
    NOTA: Esta función es un placeholder. Necesitarás implementar la lógica
    específica según el LLM que uses (OpenAI GPT-4V, Claude 3, etc.)
    """
    print("\n⚙️  Intentando resolver CAPTCHA con LLM...")
    
    # Aquí irían las llamadas al LLM
    # Ejemplo para OpenAI GPT-4V:
    """
    import openai
    openai.api_key = api_key
    
    # Capturar screenshot del CAPTCHA
    captcha_element = driver.find_element(By.ID, "captcha-image-id")
    captcha_screenshot = captcha_element.screenshot_as_png
    
    # Convertir a base64
    captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')
    
    # Llamar al LLM
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Resuelve este CAPTCHA y devuelve solo el texto:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{captcha_base64}"}}
                ]
            }
        ]
    )
    
    captcha_solution = response.choices[0].message.content.strip()
    
    # Ingresar la solución
    captcha_input = driver.find_element(By.ID, "captcha-input-id")
    captcha_input.clear()
    captcha_input.send_keys(captcha_solution)
    """
    
    print("⚠️  Función LLM no implementada completamente.")
    print("    Cayendo a modo manual...")
    solve_captcha_manual(driver)

def scrape_plate(driver, plate_number, output_folder='output_images'):
    """
    Realiza el scraping para una placa específica
    
    Args:
        driver: Instancia del WebDriver
        plate_number: Número de placa a consultar
        output_folder: Carpeta donde guardar las imágenes
    """
    url = "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
    
    print(f"\n{'='*60}")
    print(f"Consultando placa: {plate_number}")
    print(f"{'='*60}")
    
    try:
        # Navegar a la página
        driver.get(url)
        print("✓ Página cargada")
        
        # Esperar a que cargue el formulario
        wait = WebDriverWait(driver, 15)
        
        # Esperar un momento para que cargue completamente
        time.sleep(2)
        
        # Buscar el campo de entrada de placa
        print("⚙️  Buscando campo de placa...")
        try:
            plate_input = wait.until(
                EC.presence_of_element_located((By.ID, "nroPlaca"))
            )
            print(f"✓ Campo de placa encontrado")
        except Exception as e:
            print(f"❌ No se encontró el campo de placa con ID 'nroPlaca': {str(e)}")
            raise
        
        # Limpiar e ingresar la placa
        plate_input.clear()
        plate_input.send_keys(plate_number)
        print(f"✓ Placa ingresada: {plate_number}")
        
        # Pequeña pausa antes del CAPTCHA
        time.sleep(1)
        
        # Manejar CAPTCHA
        if USE_LLM_FOR_CAPTCHA and LLM_API_KEY:
            solve_captcha_llm(driver, LLM_API_KEY)
        else:
            solve_captcha_manual(driver)
        
        # Buscar y hacer clic en el botón de búsqueda/consulta
        print("⚙️  Buscando botón de búsqueda...")
        
        try:
            # Buscar el botón dentro del div con clase button-login
            search_button = driver.find_element(By.CSS_SELECTOR, "div.button-login button")
            print(f"✓ Botón encontrado")
            
            # Hacer clic en el botón
            try:
                search_button.click()
                print("✓ Clic en botón de búsqueda realizado")
            except:
                # Si el clic normal falla, usar JavaScript
                print("⚙️  Intentando clic con JavaScript...")
                driver.execute_script("arguments[0].click();", search_button)
                print("✓ Clic realizado con JavaScript")
                
        except Exception as e:
            print(f"❌ No se encontró el botón de búsqueda: {str(e)}")
            print("⚠️  Por favor, haz clic manualmente en el botón de búsqueda")
            input("Presiona ENTER después de hacer clic en 'Buscar' o 'Consultar'...")
        
        # Esperar a que se procese la búsqueda
        print("⏳ Esperando resultados...")
        time.sleep(3)
        
        # Esperar a que cargue el resultado (imagen dentro del div container-data-vehiculo)
        try:
            result_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.container-data-vehiculo img"))
            )
            print(f"✓ Resultado cargado (imagen encontrada)")
        except Exception as e:
            print(f"⚠️  No se detectó la imagen de resultado: {str(e)}")
            print("    Continuando de todas formas...")
        
        # Esperar adicional para que se cargue completamente la imagen
        time.sleep(2)
        
        # Crear carpeta de salida si no existe
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"✓ Carpeta creada: {output_folder}")
        
        # Verificar que hay contenido visible antes de capturar
        print("⚙️  Preparando captura de pantalla...")
        
        # Scroll para asegurar que todo el contenido esté visible
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Guardar screenshot completo de la página
        screenshot_path = os.path.join(output_folder, f"{plate_number}.png")
        driver.save_screenshot(screenshot_path)
        print(f"✓ Screenshot completo guardado: {screenshot_path}")
        
        # Capturar la imagen del resultado desde el div container-data-vehiculo
        try:
            # Buscar la imagen dentro del div con clase container-data-vehiculo
            result_img = driver.find_element(By.CSS_SELECTOR, "div.container-data-vehiculo img")
            result_screenshot_path = os.path.join(output_folder, f"{plate_number}_resultado.png")
            result_img.screenshot(result_screenshot_path)
            print(f"✓ Screenshot de resultado guardado: {result_screenshot_path}")
        except Exception as e:
            print(f"⚠️  No se pudo capturar la imagen del resultado: {str(e)}")
            print("    Se usará el screenshot completo para el OCR")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al consultar placa {plate_number}: {str(e)}")
        # Guardar screenshot del error
        error_path = os.path.join(output_folder, f"{plate_number}_ERROR.png")
        try:
            driver.save_screenshot(error_path)
            print(f"✓ Screenshot de error guardado: {error_path}")
        except:
            pass
        return False

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("SUNARP SCRAPER - Consulta Vehicular")
    print("="*60)
    
    # Cargar datos de placas
    plates_file = 'plates_data.json'
    
    if not os.path.exists(plates_file):
        print(f"❌ Error: No se encontró el archivo {plates_file}")
        print("   Por favor, ejecuta primero step1_extract_plates.py")
        return
    
    with open(plates_file, 'r', encoding='utf-8') as f:
        plates_data = json.load(f)
    
    print(f"\n✓ Cargadas {len(plates_data)} placas del archivo")
    
    # Configurar modo de CAPTCHA
    if USE_LLM_FOR_CAPTCHA:
        if not LLM_API_KEY:
            print("\n⚠️  ADVERTENCIA: USE_LLM_FOR_CAPTCHA está activado pero no hay API key")
            print("   Cambiando a modo manual...")
            mode = "Manual"
        else:
            mode = "LLM (Automático)"
    else:
        mode = "Manual"
    
    print(f"\n⚙️  Modo de resolución de CAPTCHA: {mode}")
    print(f"⏱️  Delay entre consultas: 10 segundos")
    
    # Preguntar cuántas placas procesar (para testing)
    try:
        limit = input(f"\n¿Cuántas placas deseas procesar? (Enter para todas, máximo {len(plates_data)}): ").strip()
        if limit:
            limit = int(limit)
            plates_data = plates_data[:limit]
    except:
        pass
    
    print(f"\n🚀 Iniciando scraping de {len(plates_data)} placas...")
    
    # Inicializar driver
    driver = setup_driver()
    
    successful = 0
    failed = 0
    
    try:
        for idx, plate_data in enumerate(plates_data, 1):
            plate_number = plate_data.get('PLACA', '')
            
            if not plate_number:
                print(f"\n⚠️  Registro {idx}: Placa vacía, saltando...")
                continue
            
            print(f"\n[{idx}/{len(plates_data)}] Procesando placa: {plate_number}")
            print(f"   RUC: {plate_data.get('RUC', 'N/A')}")
            print(f"   Marca: {plate_data.get('MARCA', 'N/A')}")
            print(f"   Año: {plate_data.get('ANIO_FAB', 'N/A')}")
            
            # Realizar scraping
            success = scrape_plate(driver, plate_number)
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Delay entre consultas (excepto en la última)
            if idx < len(plates_data):
                print(f"\n⏳ Esperando 10 segundos antes de la siguiente consulta...")
                time.sleep(10)
    
    finally:
        # Cerrar el navegador
        print("\n🔒 Cerrando navegador...")
        driver.quit()
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE EJECUCIÓN")
    print("="*60)
    print(f"Total de placas procesadas: {successful + failed}")
    print(f"✓ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    print("="*60)

if __name__ == "__main__":
    main()
