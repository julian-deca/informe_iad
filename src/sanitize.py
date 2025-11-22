import pandas as pd
import os
import zipfile
import io
from itertools import product

# --- Configuración ---
DATA_DIR = './data'
SANITIZED_DIR = os.path.join(DATA_DIR, 'data_sanitized')

# Define los códigos de los aglomerados que quieres mantener
# **DEBES VERIFICAR ESTOS CÓDIGOS EN LA DOCUMENTACIÓN DEL INDEC**
AGLOMERADOS_INTERES = [31, 32]


def get_data_file_name_from_zip(zip_path):
    """Inspecciona el ZIP y encuentra el nombre del archivo de datos ('individual' o 'hogar')."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            all_files_in_zip = z.namelist()

            # Prioriza el archivo 'individual' sobre 'hogar'
            keywords = ["individual"]

            for keyword in keywords:
                for filename in all_files_in_zip:
                    # Busca archivos .txt o .csv que contengan la palabra clave
                    if filename.lower().endswith(('.txt', '.csv')) and keyword in filename.lower():
                        return filename
            return None
    except Exception as e:
        print(f"Error al leer el ZIP {zip_path}: {e}")
        return None


def load_eph_data(zip_path, internal_file_name):
    """Carga el archivo TXT interno en un DataFrame."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            with z.open(internal_file_name) as f:
                # Usar pd.read_csv y encoding correcto (ajusta 'sep' si es ancho fijo)
                df = pd.read_csv(
                    io.TextIOWrapper(f, encoding='latin1'),
                    sep=';',
                    low_memory=False
                )
                return df
    except Exception as e:
        print(f"Error cargando archivo interno {internal_file_name}: {e}")
        return None


def sanitize_and_filter_eph(start_year=2016, end_year=2025):
    """
    Carga, filtra por aglomerado (AGLOMERADO) y guarda los datos limpios.
    """
    print(
        f"--- Inicializando Sanitización y Filtrado ({start_year}-{end_year}) ---")

    # 1. Crear el directorio de sanitizados
    if not os.path.exists(SANITIZED_DIR):
        os.makedirs(SANITIZED_DIR)
        print(f"Directorio de sanitización creado: {SANITIZED_DIR}")

    years = range(start_year, end_year + 1)
    trimesters = [1, 2, 3, 4]

    # Lista de aglomerados para incluir en el nombre del archivo
    aglomerados_str = "_".join(map(str, AGLOMERADOS_INTERES))

    processed_count = 0

    for year, trim in product(years, trimesters):
        # 2. Definir rutas
        standardized_zip_filename = f"EPH_T{trim}_{year}_txt.zip"
        zip_path = os.path.join(DATA_DIR, standardized_zip_filename)

        # 3. Verificar existencia del ZIP
        if not os.path.exists(zip_path):
            # print(f"Saltando T{trim}/{year}: Archivo ZIP no encontrado.")
            continue

        print(f"Procesando T{trim}/{year}...")

        # 4. Encontrar nombre interno y Cargar DataFrame
        internal_file_name = get_data_file_name_from_zip(zip_path)
        if not internal_file_name:
            print(
                f"Advertencia: No se encontró el archivo de datos dentro de {standardized_zip_filename}.")
            continue

        df = load_eph_data(zip_path, internal_file_name)
        if df is None:
            continue

        # 5. Sanitización: Filtrar por la columna 'AGLOMERADO'
        if 'AGLOMERADO' not in df.columns:
            print(
                f"ERROR: Columna 'AGLOMERADO' no encontrada en T{trim}/{year}. Verifique el diseño de registro y el separador (sep) en read_csv.")
            continue

        df_filtered = df[df['AGLOMERADO'].isin(AGLOMERADOS_INTERES)].copy()

        print(
            f"Filtrado aplicado: {len(df)} filas originales, {len(df_filtered)} filas retenidas.")

        # 6. Guardar el DataFrame Sanitizado

        # Nuevo nombre: EPH_T{trim}_{year}_AGLOS_33_20_29.csv
        sanitized_filename = f"EPH_T{trim}_{year}_AGLOS_{aglomerados_str}.csv"
        sanitized_path = os.path.join(SANITIZED_DIR, sanitized_filename)

        df_filtered.to_csv(sanitized_path, index=False, encoding='utf-8')
        processed_count += 1
        print(f"Guardado como: {sanitized_filename}")

    print(
        f"--- Finalizado. Archivos procesados y guardados: {processed_count} ---")


if __name__ == '__main__':
    # Ejecuta esta función después de que el scraper haya descargado los ZIPs
    sanitize_and_filter_eph(start_year=2016, end_year=2025)
