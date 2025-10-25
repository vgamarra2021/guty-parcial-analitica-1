from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests

def iniciar_sesion_y_descargar():
    # === CONFIGURACIÓN DEL NAVEGADOR ===
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://conoce-aqui.sunarp.gob.pe/conoce-aqui/inicio")

    wait = WebDriverWait(driver, 20)

    # === 1️⃣ ACEPTAR TÉRMINOS ===
    try:
        span_aceptar = wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Sí Acepto')]"))
        )
        boton_aceptar = span_aceptar.find_element(By.XPATH, "./ancestor::button")
        driver.execute_script("arguments[0].click();", boton_aceptar)
        print("✅ Botón 'Sí Acepto' presionado correctamente.")
    except Exception as e:
        print("⚠ No se pudo hacer clic en 'Sí Acepto':", e)

    # === 2️⃣ ESPERAR QUE CARGUE EL FORMULARIO ===
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='numeroDocumento']")))
        print("✅ Formulario cargado correctamente.")
    except Exception as e:
        print("❌ No se pudo cargar el formulario:", e)
        driver.quit()
        return []

    # === 3️⃣ LLENAR LOS CAMPOS CON SIMULACIÓN REALISTA ===
    try:
        # Número de DNI
        campo_dni = driver.find_element(By.XPATH, "//input[@formcontrolname='numeroDocumento']")
        campo_dni.clear()
        campo_dni.send_keys("73524480")
        campo_dni.send_keys(Keys.TAB)
        time.sleep(1)

        # Dígito de verificación
        campo_digito = driver.switch_to.active_element
        driver.execute_script("arguments[0].removeAttribute('readonly')", campo_digito)
        campo_digito.clear()
        campo_digito.send_keys("4")
        campo_digito.send_keys(Keys.TAB)
        time.sleep(1)

        # Fecha de emisión
        campo_fecha = driver.switch_to.active_element
        driver.execute_script("arguments[0].removeAttribute('readonly')", campo_fecha)
        campo_fecha.clear()
        campo_fecha.send_keys("23/06/2025")
        campo_fecha.send_keys(Keys.TAB)
        time.sleep(1)

        print("✅ Todos los campos completados correctamente.")
    except Exception as e:
        print("❌ Error al rellenar los campos:", e)

    # === 4️⃣ ESPERAR VALIDACIÓN MANUAL (CAPTCHA) ===
    print("\n⚠ Completa el CAPTCHA y presiona el botón 'Validar' en el sitio.")
    input("Presiona ENTER cuando hayas terminado la verificación en el navegador...")

    

    # === 6️⃣ DESCARGAR IMÁGENES ===
    # (Tu código original para descargar imágenes)
    print("\nEsperando a que carguen los resultados...")
    time.sleep(5) # Damos tiempo para que la búsqueda procese
    
    imagenes = driver.find_elements(By.TAG_NAME, "img")
    rutas_descargadas = []

    # === 5️⃣ DESCARGAR IMÁGENES ===
    time.sleep(5)
    imagenes = driver.find_elements(By.TAG_NAME, "img")
    rutas_descargadas = []

    output_dir = "imagenes_sunarp"
    os.makedirs(output_dir, exist_ok=True)

    for i, img in enumerate(imagenes):
        src = img.get_attribute("src")
        if src and src.startswith("http"):
            nombre_archivo = os.path.join(output_dir, f"imagen_{i+1}.png")
            try:
                img_data = requests.get(src).content
                with open(nombre_archivo, "wb") as handler:
                    handler.write(img_data)
                rutas_descargadas.append(nombre_archivo)
            except Exception as e:
                print(f"Error al descargar {src}: {e}")

    print(f"\n✅ {len(rutas_descargadas)} imágenes descargadas en '{output_dir}'.")
    driver.quit()
    return rutas_descargadas


def main():
    imagenes = iniciar_sesion_y_descargar()
    print("📄 Imágenes extraídas:", imagenes)


if _name_ == "_main_":
    main()