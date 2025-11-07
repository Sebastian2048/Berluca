# verificador.py
import requests
import os
import glob
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
from config import CARPETA_ORIGEN

# ⚙️ CONFIGURACIÓN DE VERIFICACIÓN
MAX_WORKERS = 10 
TIMEOUT_SECONDS = 5 # Tiempo máximo de espera por respuesta HTTP

# =========================================================================================
# 📦 FUNCIONES DE PARSEO (Copiadas del clasificador para ser autocontenido)
# =========================================================================================

def extraer_bloque_y_url(lineas: List[str]) -> List[Tuple[str, str]]:
    """Extrae la línea EXTINF y la URL como una tupla (extinf_line, url_line)."""
    bloques_con_url = []
    extinf_line = None
    
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            extinf_line = linea
        elif linea.startswith("http") and extinf_line:
            bloques_con_url.append((extinf_line, linea))
            extinf_line = None # Reset para el siguiente bloque
    return bloques_con_url

# =========================================================================================
# 🧠 BUCLE PRINCIPAL DE VERIFICACIÓN
# =========================================================================================

def verificar_url(url: str) -> bool:
    """Verifica si la URL devuelve un código de estado 200 (OK)."""
    try:
        # Usamos HEAD para no descargar el contenido, ajustamos timeout
        response = requests.head(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def verificar_enlaces():
    """Verifica todas las URLs en la carpeta compilados/ y sobrescribe los archivos solo con los enlaces válidos."""
    print("\n🔍 Iniciando Verificación de Enlaces (Puede tardar varios minutos)...")
    
    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_clasificadas = glob.glob(patron_busqueda)
    
    if not listas_clasificadas:
        print("⚠️ Advertencia: No se encontraron archivos M3U en compilados/ para verificar.")
        return

    for ruta_archivo in listas_clasificadas:
        nombre_archivo = os.path.basename(ruta_archivo)
        
        try:
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                lineas = f.readlines()
        except Exception:
            continue

        bloques_con_url = extraer_bloque_y_url(lineas)
        enlaces_totales = len(bloques_con_url)
        
        if not enlaces_totales: continue
            
        print(f"   -> Verificando {enlaces_totales} enlaces en {nombre_archivo}...")

        # 🚀 Ejecución concurrente
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Creamos un mapa de URL a su Bloque M3U original
            url_a_bloque = {url: (extinf, url) for extinf, url in bloques_con_url}
            urls = [url for extinf, url in bloques_con_url]
            
            # Mapeamos la función verificar_url sobre todas las URLs
            resultados = executor.map(verificar_url, urls)

            bloques_validos = []
            for url, es_valido in zip(urls, resultados):
                if es_valido:
                    extinf, url_line = url_a_bloque[url]
                    bloques_validos.append((extinf, url_line))
            
        enlaces_caidos = enlaces_totales - len(bloques_validos)
        
        if enlaces_caidos > 0:
            print(f"      ❌ Enlaces caídos detectados y eliminados: {enlaces_caidos}")
            
        # Sobrescribir el archivo con solo los enlaces válidos
        with open(ruta_archivo, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")
            for extinf, url_line in bloques_validos:
                f.write(extinf + "\n")
                f.write(url_line + "\n\n")

    print("✅ Verificación de enlaces finalizada. Archivos en compilados/ actualizados.")

if __name__ == "__main__":
    verificar_enlaces()