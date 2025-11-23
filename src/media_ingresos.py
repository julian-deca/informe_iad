import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product

from utils import load_sanitized_eph_data
from utils import calcular_ipc_trimestral


def get_deflactores():

    deflactores_df = calcular_ipc_trimestral()

    BASE_IPC = deflactores_df[
        (deflactores_df['ANIO'] == 2025) &
        (deflactores_df['TRIMESTRE'] == 1)
    ]['INDICE'].iloc[0]

    deflactores_df['Deflactor_normalizado'] = deflactores_df['INDICE'] / BASE_IPC
    deflactores_df['Deflactor_normalizado'] = pd.to_numeric(
        deflactores_df['Deflactor_normalizado'], errors='coerce')

    return deflactores_df


def deflacionar_ingresos(df_eph):
    """Calcula el ingreso real y el ponderador del ingreso."""

    deflactores_df = get_deflactores()

    # 1. Merge para obtener el deflactor en cada fila de ingreso
    df_eph_merged = pd.merge(
        df_eph,
        deflactores_df[['ANIO', 'TRIMESTRE', 'Deflactor_normalizado']],
        left_on=['ANO4', 'TRIMESTRE'], right_on=['ANIO', 'TRIMESTRE'], how='inner')

    df_eph_merged['P21'] = pd.to_numeric(
        df_eph_merged['P21'], errors='coerce')

    # 2. Deflacionar el Ingreso (Ingreso_Real = Ingreso_Nominal / Deflactor)
    # Columna Ingreso: En EPH, el ingreso total familiar suele ser 'ITF' y el individual 'P21'
    # Asumiremos que quieres deflacionar el 'ITF' (Ingreso Total Familiar)

    # **NOTA**: Debes verificar la columna de Ingreso en tu microdato (P21 o ITF)
    df_eph_merged['P21_REAL'] = (
        df_eph_merged['P21'] / (df_eph_merged['Deflactor_normalizado'])
    )

    # Columna Ponderador de ingreso ('PONDIH' o similar)
    # El ingreso se pondera con el ponderador de hogar (PONDIH), no el individual (PONDERA)
    df_eph_merged['P21_PONDERADO_REAL'] = (
        # PONDIH: Ponderador de Hogar
        df_eph_merged['P21_REAL'] * df_eph_merged['PONDIIO']
    )

    # Quitar filas sin ingreso o sin deflactor
    return df_eph_merged.dropna(subset=['P21_REAL'])
