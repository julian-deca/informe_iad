import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from utils import load_sanitized_eph_data
from evolucion_media import calcular_tasa_empleo_por_aglomerado
from media_ingresos import deflacionar_ingresos
import geopandas as gpd

tasas = ['Tasa_Empleo', 'Tasa_Actividad', 'Tasa_Desocupacion']
labels = ['Tasa de Empleo (TE)', 'Tasa de Actividad (TA)',
          'Tasa de Desocupación (TD)']

codigos_aglomerados = {
    31: 'Ushuaia',
    32: 'CABA'
}


def graficar_tasa_empleo_serie(df_resultado):
    """Genera un gráfico de líneas comparando la Tasa de Empleo por aglomerado a lo largo del tiempo."""

    """
    Genera un subgráfico de líneas para cada aglomerado, mostrando la Tasa de Empleo, 
    Tasa de Desocupación y Tasa de Actividad en el mismo eje temporal.
    """

    # 1. Preparación de los datos y la configuración del gráfico
    sns.set_style("whitegrid")

    # Lista de aglomerados únicos
    aglomerados = df_resultado['AGLOMERADO'].unique()
    num_aglomerados = len(aglomerados)

    # Determinar el layout (ejemplo: 2 columnas, N filas)
    ncols = 2
    nrows = int(np.ceil(num_aglomerados / ncols))

    # Crear la figura y los subgráficos
    fig, axes = plt.subplots(nrows, ncols, figsize=(
        18, 5 * nrows), sharex=True, sharey=True)
    axes = axes.flatten()  # Aplanar para facilitar la iteración

    # Nombres de las tasas a graficar
    tasas = ['Tasa_Empleo', 'Tasa_Actividad', 'Tasa_Desocupacion']
    labels = ['Tasa de Empleo (TE)', 'Tasa de Actividad (TA)',
              'Tasa de Desocupación (TD)']

    # 2. Iterar y graficar cada aglomerado
    for i, aglomerado_code in enumerate(aglomerados):
        ax = axes[i]
        df_agg = df_resultado[df_resultado['AGLOMERADO']
                              == aglomerado_code].sort_values('PERIODO')

        # Iterar sobre las tres tasas
        for tasa, label in zip(tasas, labels):
            sns.lineplot(
                data=df_agg,
                x='PERIODO',
                y=tasa,
                label=label,
                marker='.',
                ax=ax  # Asegura que se dibuje en el subgráfico actual
            )

        # 3. Personalización del Subgráfico

        # El título debe incluir el código del aglomerado
        ax.set_title(
            f'Aglomerado: {codigos_aglomerados[aglomerado_code]}', fontsize=14)
        ax.set_xlabel('Período (Año y Trimestre)')
        ax.set_ylabel('Porcentaje (%)')
        ax.legend(loc='lower left', fontsize=10)
        ax.set_ylim(0, df_resultado[['Tasa_Empleo', 'Tasa_Actividad']].max(
        ).max() * 1.05)  # Escala Y compartida

        # Opcional: Ajustar los ticks del eje X para mayor legibilidad
        if not df_agg.empty:
            year_ticks = df_agg[df_agg['TRIMESTRE'] == 1]['PERIODO'].unique()
            year_labels = df_agg[df_agg['TRIMESTRE'] == 1]['ANO4'].unique()
            ax.set_xticks(year_ticks)
            ax.set_xticklabels(year_labels, rotation=45,
                               ha='right', fontsize=10)

    # 4. Finalización de la Figura

    # Ocultar los subgráficos vacíos si el número de aglomerados es impar
    for j in range(num_aglomerados, nrows * ncols):
        fig.delaxes(axes[j])

    fig.suptitle(
        'Análisis de Series de Tiempo de Indicadores Laborales EPH', fontsize=20, y=1)
    # Ajuste para que el título no se solape
    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.show()


def graficar_media_ingreso_real(df_eph_deflacionado):
    """
    Calcula la media del ingreso real ponderado por periodo y genera el gráfico.
    """

    # 1. Calcular la Media Ponderada por Periodo y Aglomerado

    # A. Suma del Ingreso Ponderado (Numerador)
    ingreso_ponderado_sum = df_eph_deflacionado.groupby(['ANO4', 'TRIMESTRE', 'AGLOMERADO'])[
        'P21_PONDERADO_REAL'
    ].sum().reset_index(name='Suma_P21_Ponderado_Real')

    # B. Suma de los Ponderadores (Denominador)
    # Se usa el ponderador de hogar (PONDIH) para el Ingreso Total Familiar (P21)
    ponderador_sum = df_eph_deflacionado.groupby(['ANO4', 'TRIMESTRE', 'AGLOMERADO'])[
        'PONDIIO'
    ].sum().reset_index(name='Suma_PONDIIO')

    # 2. Merge y Cálculo de la Media Final
    df_media = pd.merge(ingreso_ponderado_sum, ponderador_sum, on=[
                        'ANO4', 'TRIMESTRE', 'AGLOMERADO'])

    df_media['Media_Ingreso_Real'] = (
        df_media['Suma_P21_Ponderado_Real'] / df_media['Suma_PONDIIO']
    )

    # 3. Preparar columna de período y graficar
    df_media['PERIODO'] = df_media['ANO4'] + (df_media['TRIMESTRE'] - 1) / 4

    plt.figure(figsize=(15, 6))
    sns.lineplot(
        data=df_media,
        x='PERIODO',
        y='Media_Ingreso_Real',
        hue='AGLOMERADO',
        marker='o'
    )

    plt.title(f'Evolución del Ingreso Familiar Total Promedio Real (Base: T1/2025)')
    plt.xlabel('Período')
    plt.ylabel('Ingreso Real Promedio Ponderado')
    plt.legend(title='Cód. Aglomerado')
    plt.show()



def graficar_mapa():
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    gdf_eph = gpd.read_file("./data/radios_eph.geojson")
    gdf_caba = gdf_eph[gdf_eph["eph_codagl"] == '32']
    print(gdf_caba.head())
    
    gdf_caba.plot(
       ax=ax, 
        edgecolor='black', 
        linewidth=0.5, 
        facecolor='lightblue',
        alpha=0.8
    )

    # Añadir etiquetas de interés (opcional)
    ax.set_title(f'Cobertura EPH - {"CABA"}', fontsize=14)
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')

    # Mostrar el mapa
    plt.show()


def graficar():
    """Función principal para cargar datos y generar el gráfico de Tasa de Empleo."""

    df_eph = load_sanitized_eph_data()

    if df_eph is None:
        return

    graficar_mapa()

    
    # Calcular la Tasa de Empleo por aglomerado
    #df_tasa_empleo = calcular_tasa_empleo_por_aglomerado(None, df_eph)
    #df_eph_deflacionado = deflacionar_ingresos(df_eph)
    # Generar el gráfico
    #graficar_tasa_empleo_serie(df_tasa_empleo)
    #graficar_media_ingreso_real(df_eph_deflacionado)


graficar()
