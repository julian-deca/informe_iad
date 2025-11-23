import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product


# --- Configuración ---
# Directorio donde se encuentran los archivos CSV filtrados
SANITIZED_DIR = './data/data_sanitized'
# Definimos el rango de años que ya hemos procesado
START_YEAR = 2016
END_YEAR = 2025

# Los mismos códigos usados para nombrar los archivos (deben coincidir)
AGLOMERADOS_INTERES = [31, 32]
# 32 CABA
# 31 USUHAIA
AGLOMERADOS_STR = "_".join(map(str, AGLOMERADOS_INTERES))
# Nombre de archivo estandarizado: EPH_T{trim}_YYYY_AGLOS_{codes}.csv

# Configuración inicial de visualización
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)


TRIMESTRES_POR_MES = {
    1: ["jan", "feb", "mar"],
    2: ["apr", "may", "jun"],
    3: ["jul", "aug", "sep"],
    4: ["oct", "nov", "dec"],
}


def load_sanitized_eph_data():
    """
    Carga todos los archivos CSV sanitizados del directorio en un único DataFrame.
    """
    all_data = []

    print(f"--- Iniciando Carga Masiva desde: {SANITIZED_DIR} ---")

    years = range(START_YEAR, END_YEAR + 1)
    trimesters = [1, 2, 3, 4]
    loaded_count = 0

    for year, trim in product(years, trimesters):
        # 1. Construir el nombre de archivo estandarizado
        filename = f"EPH_T{trim}_{year}_AGLOS_31_32.csv"
        filepath = os.path.join(SANITIZED_DIR, filename)

        # 2. Verificar la existencia y cargar
        if os.path.exists(filepath):
            try:
                # El archivo es un CSV limpio, la carga es simple y rápida
                df = pd.read_csv(filepath, low_memory=False)
                all_data.append(df)
                loaded_count += 1
                # print(f"Cargado: {filename}")
            except Exception as e:
                print(f"ERROR al cargar {filename}: {e}")
        # else:
            # print(f"Saltando: {filename} no encontrado.")

    if not all_data:
        print("ADVERTENCIA: No se encontró ningún archivo para cargar. Asegúrese de que el sanitizador se haya ejecutado.")
        return None

    # 3. Concatenar todos los DataFrames
    final_df = pd.concat(all_data, ignore_index=True)
    print(
        f"--- Carga Finalizada. {loaded_count} trimestres cargados. Total de filas: {len(final_df)} ---")

    return final_df


def cargar_df_ipc():
    """
    Carga el DataFrame del IPC desde el archivo CSV.
    """
    ipc_filepath = './data/ipc.csv'
    if os.path.exists(ipc_filepath):
        try:
            df_ipc = pd.read_csv(ipc_filepath)
            return df_ipc
        except Exception as e:
            print(f"Error al cargar el archivo IPC: {e}")
            return None
    else:
        print(f"ERROR: Archivo IPC no encontrado en {ipc_filepath}.")
        return None


def calcular_ipc_trimestral():
    """
    Calcula el IPC trimestral a partir del DataFrame del IPC mensual.
    """
    df_ipc = cargar_df_ipc()
    if df_ipc is None:
        return None

    # Asegurar que las columnas necesarias son numéricas
    df_ipc['ANIO'] = pd.to_numeric(df_ipc['ANIO'], errors='coerce')
    df_ipc['INDICE'] = pd.to_numeric(df_ipc['INDICE'], errors='coerce')

    # Crear una columna de Trimestre basada en el Mes
    df_ipc['TRIMESTRE'] = df_ipc['MES'].apply(get_trimestre)

    # Agrupar por Año y Trimestre, y calcular el IPC promedio
    df_ipc_trimestral = df_ipc.groupby(
        ['ANIO', 'TRIMESTRE'], as_index=False)['INDICE'].mean()

    return df_ipc_trimestral


def get_trimestre(mes):
    for trimestre, meses in TRIMESTRES_POR_MES.items():
        if mes.lower() in meses:
            return trimestre
    return None
