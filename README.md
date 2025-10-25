# SUNARP Web Scraping - Consulta Vehicular

Sistema completo de scraping y extracción de datos vehiculares de SUNARP.

## 📋 Descripción

Este proyecto consta de 3 scripts que permiten:

1. **Extraer placas del dataset** → Genera un archivo JSON con las placas a consultar
2. **Hacer scraping de SUNARP** → Consulta cada placa y guarda imágenes de los resultados
3. **Extraer datos con OCR** → Procesa las imágenes y estructura la información

## 🚀 Instalación

### 1. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 2. Instalar Tesseract-OCR

**Windows:**
1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar (típicamente en `C:\Program Files\Tesseract-OCR`)
3. Agregar al PATH o actualizar la ruta en `step3_ocr_extract.py`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**Mac:**
```bash
brew install tesseract tesseract-lang
```

### 3. Instalar ChromeDriver

El script usa `webdriver-manager` que descarga automáticamente ChromeDriver.
Asegúrate de tener Google Chrome instalado.

## 📝 Uso

### Paso 1: Extraer datos de placas

```bash
python step1_extract_plates.py
```

Este script:
- Lee `dataset_plates.csv`
- Extrae: PLACA, TENENCIA, MARCA, RUC, ANIO_FAB
- Genera: `plates_data.json`

### Paso 2: Scraping de SUNARP

```bash
python step2_scrape_sunarp.py
```

Características:
- ✅ Consulta cada placa en https://consultavehicular.sunarp.gob.pe
- ✅ Delay de 10 segundos entre consultas
- ✅ Resolución manual de CAPTCHA (por defecto)
- ✅ Guarda imágenes en carpeta `output_images/`
- ⚙️ Opción para usar LLM (requiere configuración)

**Resolución de CAPTCHA:**

Por defecto es **MANUAL**. El script pausará y esperará a que resuelvas el CAPTCHA.

Para usar LLM (requiere implementación):
```python
# En step2_scrape_sunarp.py
USE_LLM_FOR_CAPTCHA = True
LLM_API_KEY = "tu-api-key-aquí"
```

### Paso 3: Extracción con OCR

```bash
python step3_ocr_extract.py
```

Este script:
- Lee imágenes de `output_images/`
- Aplica OCR con pytesseract
- Extrae información estructurada
- Genera: `vehicle_data_extracted.json` y `vehicle_data_extracted.csv`

## 📊 Datos Extraídos

El OCR intenta extraer:
- ✓ Placa
- ✓ Marca y modelo
- ✓ Año de fabricación
- ✓ Año modelo
- ✓ Color
- ✓ N° de motor
- ✓ N° de serie
- ✓ Clase y tipo
- ✓ Carrocería
- ✓ Combustible
- ✓ Cilindros
- ✓ Asientos
- ✓ Propietario
- ✓ Documento (DNI/RUC)

## 🔧 Configuración Avanzada

### Ajustar selectores de Selenium

Si la página web cambia, puede ser necesario actualizar los selectores en `step2_scrape_sunarp.py`:

```python
# Ejemplos de selectores que pueden necesitar ajuste:
plate_input = driver.find_element(By.ID, "placa")
search_button = driver.find_element(By.ID, "btnBuscar")
```

### Mejorar OCR

En `step3_ocr_extract.py` puedes ajustar:
- Preprocesamiento de imágenes
- Configuración de pytesseract
- Patrones de expresiones regulares

## ⚠️ Consideraciones

1. **Respeta los términos de servicio** de SUNARP
2. **No abuses del sistema** - el delay de 10 segundos es importante
3. **Capturas manuales** - el CAPTCHA requiere intervención humana por defecto
4. **Calidad de OCR** - depende de la calidad de las imágenes capturadas

## 📁 Estructura de Archivos

```
├── dataset_plates.csv              # Dataset original
├── requirements.txt                # Dependencias
├── step1_extract_plates.py         # Script 1: Extraer placas
├── step2_scrape_sunarp.py          # Script 2: Scraping
├── step3_ocr_extract.py            # Script 3: OCR
├── plates_data.json                # Salida del paso 1
├── output_images/                  # Carpeta con screenshots
│   ├── A0B975.png
│   ├── A0B977.png
│   └── ...
├── vehicle_data_extracted.json     # Salida del paso 3 (JSON)
└── vehicle_data_extracted.csv      # Salida del paso 3 (CSV)
```

## 🐛 Solución de Problemas

### Error: "Tesseract not found"
- Verifica que Tesseract esté instalado
- Actualiza la ruta en `step3_ocr_extract.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### Error: "ChromeDriver not compatible"
- Actualiza Google Chrome
- El script descargará automáticamente la versión compatible

### OCR con resultados pobres
- Verifica la calidad de las imágenes en `output_images/`
- Ajusta el preprocesamiento de imágenes
- Considera tomar screenshots de mayor resolución

## 📄 Licencia

Este es un proyecto educativo. Úsalo de manera responsable.
