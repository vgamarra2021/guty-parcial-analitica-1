"""
Script para extraer datos de placas del dataset y guardarlos en un formato estructurado.
"""
import pandas as pd
import json

def extract_plates_data(csv_file='dataset_plates.csv', output_file='plates_data.json'):
    """
    Extrae un arreglo de diccionarios con solo las placas, tenencia, marca, ruc, ANIO_FAB
    
    Args:
        csv_file: Ruta al archivo CSV con los datos de placas
        output_file: Ruta donde se guardará el JSON con los datos extraídos
    """
    print(f"Leyendo archivo: {csv_file}")
    
    # Leer el CSV
    df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
    
    print(f"Total de registros: {len(df)}")
    
    # Seleccionar solo las columnas necesarias
    columnas_necesarias = ['PLACA', 'TENENCIA', 'MARCA', 'RUC', 'ANIO_FAB']
    
    # Verificar que las columnas existen
    for col in columnas_necesarias:
        if col not in df.columns:
            print(f"Advertencia: Columna '{col}' no encontrada en el dataset")
    
    # Filtrar las columnas necesarias
    df_filtrado = df[columnas_necesarias].copy()
    
    # Eliminar filas donde PLACA esté vacío
    df_filtrado = df_filtrado[df_filtrado['PLACA'].notna()]
    
    # Convertir a lista de diccionarios
    plates_data = df_filtrado.to_dict('records')
    
    print(f"Total de placas válidas: {len(plates_data)}")
    
    # Mostrar algunos ejemplos
    print("\nPrimeros 5 registros:")
    for i, plate in enumerate(plates_data[:5]):
        print(f"{i+1}. {plate}")
    
    # Guardar en JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(plates_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDatos guardados en: {output_file}")
    
    return plates_data

if __name__ == "__main__":
    plates_data = extract_plates_data()
    print(f"\n✓ Proceso completado. Se extrajeron {len(plates_data)} placas.")
