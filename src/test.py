import pandas as pd
import os

# --- Configuración ---
SANITIZED_DIR = './data/data_sanitized'
AGLOMERADOS_INTERES = [31, 32]  # Asumimos que incluiste CABA (01)
AGLOMERADOS_STR = "_".join(map(str, AGLOMERADOS_INTERES))

# Definimos el periodo y el aglomerado de interés
TARGET_YEAR = 2020
TARGET_TRIMESTER = 1
CABA_CODE = 32  # Código de Aglomerado para CABA


def load_caba_2020_t1_data():
    """Carga el archivo CSV filtrado para el T1/2020."""
    filename = f"EPH_T{TARGET_TRIMESTER}_{TARGET_YEAR}_AGLOS_{AGLOMERADOS_STR}.csv"
    filepath = os.path.join(SANITIZED_DIR, filename)

    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, low_memory=False)
            return df
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return None
    else:
        print(
            f"ERROR: Archivo no encontrado. Asegúrese de que {filename} existe en {SANITIZED_DIR}.")
        return None


def calculate_employment_rate_caba_women():
    """Calcula la Tasa de Empleo para mujeres en CABA (T1/2020)."""

    df = load_caba_2020_t1_data()
    if df is None:
        return None

    # Aseguramos que las columnas clave sean numéricas (para sumar)
    # y manejamos posibles errores de tipo introducidos al guardar en CSV
    df['PONDERA'] = pd.to_numeric(df['PONDERA'], errors='coerce')
    df['CH04'] = pd.to_numeric(df['CH04'], errors='coerce')
    df['ESTADO'] = pd.to_numeric(df['ESTADO'], errors='coerce')
    df['AGLOMERADO'] = pd.to_numeric(df['AGLOMERADO'], errors='coerce')

    # --- A. Filtrado de la Población de Referencia ---

    # 1. Filtro por CABA (código 01)
    df_caba = df[df['AGLOMERADO'] == CABA_CODE]

    # 2. Filtro por Mujeres (código 2 en CH04)
    df_caba_mujeres = df_caba[(df_caba['CH04'] == 2) & (df_caba["CH06"] >= 14)]

    # La Población Total de Mujeres en CABA es la suma de sus ponderadores.

    poblacion_total_mujeres = df_caba_mujeres['PONDERA'].sum()

    # --- B. Filtrado de la Población Ocupada ---

    # 3. Filtro por Ocupadas (código 1 en ESTADO)
    # (ESTADO = 1 corresponde a la población OCUPADA)
    df_ocupadas_mujeres = df_caba_mujeres[df_caba_mujeres['ESTADO'] == 1]

    # La Población Ocupada de Mujeres en CABA es la suma de sus ponderadores.
    poblacion_ocupada_mujeres = df_ocupadas_mujeres['PONDERA'].sum()

    # --- C. Cálculo Final ---

    if poblacion_total_mujeres > 0:
        tasa_empleo = (poblacion_ocupada_mujeres /
                       poblacion_total_mujeres) * 100

        print(f"\n--- Resultado Tasa de Empleo (Mujeres, CABA, T1/2020) ---")
        print(
            f"Población Ocupada de Mujeres (estimada): {poblacion_ocupada_mujeres:,.0f}")
        print(
            f"Población Total de Mujeres (estimada): {poblacion_total_mujeres:,.0f}")
        print(
            f"Tasa de Empleo (TE) Mujeres CABA T1/2020: **{tasa_empleo:.2f}%**")
        print(
            f"Tasa de Empleo (TE) Mujeres CABA T1/2020 segun informe de prensa del INDEC: {53.00}%")
        print(
            f"Margen de error: **{abs(53.00 - tasa_empleo):.5f}%**")
        return tasa_empleo
    else:
        print("ERROR: La Población Total de Mujeres en CABA es cero. Verifique los códigos de aglomerado/sexo.")
        return 0


calculate_employment_rate_caba_women()
