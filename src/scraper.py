import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from itertools import product

# --- Configuración ---
# URL de ejemplo del repositorio de microdatos del INDEC.
# **NOTA**: Debes verificar esta URL exacta en el sitio del INDEC.
BASE_URL = "https://www.indec.gob.ar/Institucional/Indec/BasesDeDatos"
TARGET_DIR = './data'
# Patrón esperado en el link: EPH_usu_T_Trim_YYYY_txt.zip
# T es el trimestre (1, 2, 3, 4) y YYYY el año (2016 a 2025)
# Esto es esencial para el filtrado.


def generate_eph_periods(start_year, end_year):
    """Genera una lista de tuplas (año, trimestre) para el rango especificado."""
    years = range(start_year, end_year + 1)
    trimesters = [1, 2, 3, 4]

    # Crea todas las combinaciones posibles (producto cartesiano)
    return list(product(years, trimesters))


def download_file(url, target_path):
    """Descarga un archivo desde una URL y lo guarda en target_path."""
    print(f"Descargando {os.path.basename(target_path)}...")

    # Usa 'stream=True' para descargar archivos grandes eficientemente
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Lanza excepción para códigos de error HTTP

        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filtrar fragmentos keep-alive
                    f.write(chunk)
        print(f"Descarga de {os.path.basename(target_path)} completada.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar {os.path.basename(target_path)}: {e}")
        return False


def get_possible_patterns(trim, year):
    """Genera los patrones de nombre de archivo posibles para un trimestre."""

    # Mapeo de trimestres: numérico a abreviado con 'er/do/er/to'
    trim_map = {
        1: "1_Trim",    # EPH_usu_1_Trim_YYYY_txt.zip
        2: "2_Trim",    # EPH_usu_2_Trim_YYYY_txt.zip
        3: "3_Trim",    # EPH_usu_3_Trim_YYYY_txt.zip
        4: "4_Trim"     # EPH_usu_4_Trim_YYYY_txt.zip
    }

    # Mapeo alternativo: numérico a abreviado con 'er/do/er/to'
    trim_alt_map = {
        1: "1erTrim",   # EPH_usu_1erTrim_YYYY_txt.zip
        2: "2doTrim",   # EPH_usu_2doTrim_YYYY_txt.zip
        3: "3erTrim",   # EPH_usu_3erTrim_YYYY_txt.zip
        4: "4toTrim"    # EPH_usu_4toTrim_YYYY_txt.zip
    }

    trim_alt_alt_map = {
        1: "1er_Trim",   # EPH_usu_1erTrim_YYYY_txt.zip
        2: "2do_Trim",   # EPH_usu_2doTrim_YYYY_txt.zip
        3: "3er_Trim",   # EPH_usu_3erTrim_YYYY_txt.zip
        4: "4to_Trim"    # EPH_usu_4toTrim_YYYY_txt.zip
    }

    # 1. Patrón Estandarizado (e.g., _2_Trim_2020_txt.zip)
    pattern_std = f"_{trim_map.get(trim)}_{year}_txt.zip"

    # 2. Patrón Alternativo (e.g., _2doTrim_2016_txt.zip)
    pattern_alt = f"_{trim_alt_map.get(trim)}_{year}_txt.zip"

    pattern_alt_alt = f"_{trim_alt_alt_map.get(trim)}_{year}_txt.zip"

    # Retorna todos los posibles finales de la URL para este periodo
    return [pattern_std, pattern_alt, pattern_alt_alt]


def scrape_and_download(start_year=2016, end_year=2025):
    """Busca, filtra y descarga los microdatos de EPH del INDEC."""
    print(f"--- Inicializando Scraper EPH ({start_year}-{end_year}) ---")

    # 1. Preparación del Entorno
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"Directorio de destino creado: {TARGET_DIR}")

    # Generar la lista de períodos a buscar
    target_periods = generate_eph_periods(start_year, end_year)

    # 2. Petición y Parseo
    try:
        response = requests.get(BASE_URL, timeout=15)
        response.raise_for_status()  # Verificar que la petición fue exitosa (código 200)
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL base {BASE_URL}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    all_links = soup.find_all('a')
    downloaded_count = 0

    # 3. Filtrado y Descarga
    for year, trim in target_periods:
        # Generar el patrón de nombre de archivo esperado para el periodo actual
        # Ejemplo de patrón: EPH_usu_1_Trim_2025_txt.zip
        expected_filename_part = get_possible_patterns(trim, year)

        found_link = None

        for link in all_links:
            href = link.get('href', '')

            # Criterios de filtrado:
            # a) El enlace debe apuntar al formato zip de txt
            # b) El enlace debe contener el año y trimestre que buscamos
            # c) El enlace debe empezar con el patrón conocido (opcional pero bueno para seguridad)
            if any(href.endswith(p) for p in expected_filename_part):
                if ("/ftp/cuadros/menusuperior/eph/" in href):

                    # Se encontró el link exacto para el periodo
                    found_link = href
                    break

        if found_link:
            # Construir la URL completa y la ruta de guardado
            standardized_filename = f"EPH_T{trim}_{year}_txt.zip"
            full_url = urljoin(BASE_URL, found_link)
            filepath = os.path.join(TARGET_DIR, standardized_filename)

            if not os.path.exists(filepath):
                if download_file(full_url, filepath):
                    downloaded_count += 1
            else:
                print(f"{standardized_filename} ya existe. Saltando descarga.")
        else:
            print(
                f"Advertencia: No se encontró el archivo TXT para el T{trim}/{year}.")

    print(f"--- Finalizado. Archivos descargados: {downloaded_count} ---")


if __name__ == '__main__':
    # El trimestre 4 de 2025 aún no existe, por eso se recomienda usar un rango
    # que se ajuste a los datos disponibles, o simplemente dejar que la lógica de
    # 'found_link' maneje la ausencia.
    scrape_and_download(start_year=2016, end_year=2025)
