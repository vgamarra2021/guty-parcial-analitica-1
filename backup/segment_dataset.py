import pandas as pd

# Configuración
input_file = 'dataset_ruc_202510.csv'
output_file = 'dataset_ruc_202510_100k.csv'
num_records = 100000

print(f"Leyendo los primeros {num_records} registros de {input_file}...")

# Leer solo los primeros 100,000 registros del CSV
# Intentar con diferentes codificaciones
try:
    df = pd.read_csv(input_file, nrows=num_records, encoding='utf-8')
except UnicodeDecodeError:
    print("⚠ UTF-8 falló, intentando con latin-1...")
    df = pd.read_csv(input_file, nrows=num_records, encoding='latin-1')

print(f"Total de registros leídos: {len(df)}")
print(f"Columnas: {list(df.columns)}")

# Guardar en un nuevo archivo CSV
df.to_csv(output_file, index=False)

print(f"Archivo segmentado guardado como: {output_file}")
