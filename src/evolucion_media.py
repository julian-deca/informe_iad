import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product

from utils import load_sanitized_eph_data
#

# --- Configuración ---
# Directorio donde se encuentran los archivos CSV filtrados
SANITIZED_DIR = './data/data_sanitized'
# Definimos el rango de años que ya hemos procesado
START_ANO4 = 2016
END_ANO4 = 2025

# Los mismos códigos usados para nombrar los archivos (deben coincidir)
AGLOMERADOS_INTERES = [31, 32]
# 32 CABA
# 31 USUHAIA
AGLOMERADOS_STR = "_".join(map(str, AGLOMERADOS_INTERES))
# Nombre de archivo estandarizado: EPH_T{trim}_YYYY_AGLOS_{codes}.csv

# Configuración inicial de visualización
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)

# --- Funciones de Carga y Análisis ---


def run_analysis():
    """
    Función principal de análisis y visualización.
    """
    df_eph = load_sanitized_eph_data()

    if df_eph is None:
        return

    tasa_empleo_caba = calcular_tasa_empleo_por_aglomerado(32, df_eph)
    tasa_empleo_ushuaia = calcular_tasa_empleo_por_aglomerado(31, df_eph)
    print(f"{tasa_empleo_caba}")

    # --- Análisis y Preparación ---


def calcular_tasa_empleo_por_aglomerado(aglomerado, df):
    """
    Calcula la Tasa de Empleo (TE), Tasa de Desocupación (TD) y Tasa de Actividad (TA) 
    agrupando por Año, Trimestre y Aglomerado.
    """

    # 1. Asegurar tipos de datos y definir Poblaciones clave
    df['PONDERA'] = pd.to_numeric(df['PONDERA'], errors='coerce')
    df['ESTADO'] = pd.to_numeric(df['ESTADO'], errors='coerce')
    df['CH06'] = pd.to_numeric(df['CH06'], errors='coerce')
    df['AGLOMERADO'] = pd.to_numeric(df['AGLOMERADO'], errors='coerce')

    # Población Total de Referencia (PTR: Edad >= 14)
    df_ptr = df[df['CH06'] >= 14].copy()

    # Población Activa (PA: Ocupados [1] + Desocupados [2])
    df_pa = df_ptr[df_ptr['ESTADO'].isin([1, 2])].copy()

    # Población Ocupada (PO: ESTADO = 1)
    df_po = df_ptr[df_ptr['ESTADO'] == 1].copy()

    # Población Desocupada (PD: ESTADO = 2)
    df_pd = df_ptr[df_ptr['ESTADO'] == 2].copy()

    # 2. Calcular Ponderadores (Suma de Poblaciones) por Grupo
    group_keys = ['ANO4', 'TRIMESTRE', 'AGLOMERADO']

    # --- Sumas de Población ---

    # A. Denominador para TE y TA
    df_total = df_ptr.groupby(group_keys)[
        'PONDERA'].sum().reset_index(name='Total_PTR')

    # B. Denominador para TD y Numerador para TA
    df_activa = df_pa.groupby(group_keys)['PONDERA'].sum(
    ).reset_index(name='Poblacion_Activa')

    # C. Numerador para TE
    df_ocupada = df_po.groupby(group_keys)['PONDERA'].sum(
    ).reset_index(name='Poblacion_Ocupada')

    # D. Numerador para TD
    df_desocupada = df_pd.groupby(group_keys)['PONDERA'].sum(
    ).reset_index(name='Poblacion_Desocupada')

    # 3. Combinar las series de población en un único DataFrame de resultados
    df_resultado = pd.merge(df_total, df_activa, on=group_keys, how='left')
    df_resultado = pd.merge(df_resultado, df_ocupada,
                            on=group_keys, how='left')
    df_resultado = pd.merge(df_resultado, df_desocupada,
                            on=group_keys, how='left')

    # Rellenar los conteos nulos con 0 (si un aglomerado no tiene desocupados, por ejemplo)
    df_resultado[['Poblacion_Activa', 'Poblacion_Ocupada', 'Poblacion_Desocupada']] = \
        df_resultado[['Poblacion_Activa', 'Poblacion_Ocupada',
                      'Poblacion_Desocupada']].fillna(0)

    # 4. Aplicar Fórmulas para calcular las Tasas

    # Tasa de Empleo (TE)
    df_resultado['Tasa_Empleo'] = (
        df_resultado['Poblacion_Ocupada'] / df_resultado['Total_PTR']) * 100

    # Tasa de Actividad (TA)
    df_resultado['Tasa_Actividad'] = (
        df_resultado['Poblacion_Activa'] / df_resultado['Total_PTR']) * 100

    # Tasa de Desocupación (TD)
    # Importante: El denominador es la Población Activa, no la PTR.
    df_resultado['Tasa_Desocupacion'] = (
        df_resultado['Poblacion_Desocupada'] / df_resultado['Poblacion_Activa']) * 100

    # Manejar división por cero (si la Población Activa es 0)
    df_resultado['Tasa_Desocupacion'] = df_resultado['Tasa_Desocupacion'].fillna(
        0)

    # 5. Limpieza final (opcional): Crear columna PERIODO para graficación
    df_resultado['PERIODO'] = df_resultado['ANO4'] + \
        (df_resultado['TRIMESTRE'] - 1) / 4

    return df_resultado

# --- Ejecución ---
# resultados_te_aglomerado = calcular_te_por_periodo_y_aglomerado(df)
# print(resultados_te_aglomerado)


run_analysis()
