import requests
import os 
from config import CARPETA_SALIDA # Importamos "Beluga"

# --- Funciones Auxiliares (Asumiendo que están en este archivo o importadas) ---

def github_blob_a_raw(url: str) -> str:
    """Convierte una URL de GitHub 'blob' (repositorio) a una URL 'raw' (contenido directo)."""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

def extraer_enlaces_m3u(contenido: str) -> list:
    """Extrae todas las líneas que inician con 'http' del contenido M3U."""
    urls = set()
    for linea in contenido.splitlines():
        linea = linea.strip()
        if linea.startswith("http"):
            urls.add(linea)
    return list(urls)

# --- Función Principal de Extracción ---

def recolectar_enlaces(url_lista: str):
    """
    Descarga la lista M3U, convierte a URL RAW si es necesario y la guarda 
    en la ruta temporal correcta: Beluga/TEMP_MATERIAL.m3u.
    """
    
    # 1. Conversión de URL (si es de GitHub)
    url_raw = github_blob_a_raw(url_lista)
    print(f"\n🔗 URL RAW convertida: {url_raw}")
    
    # 2. Descarga del contenido RAW
    try:
        print(f"📥 Descargando contenido RAW...")
        response = requests.get(url_raw, timeout=20)
        response.raise_for_status()
        contenido = response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar desde {url_raw}: {e}")
        return

    # 3. Extracción de enlaces únicos (solo para el conteo informativo)
    enlaces_unicos = extraer_enlaces_m3u(contenido)

    # 🛑 CORRECCIÓN DE RUTA CLAVE: Guarda el archivo en la carpeta de salida "Beluga".
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u") 
    
    try:
        # 4. Guardar todo el contenido (incluyendo #EXTINF) para la clasificación
        with open(ruta_temp, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")
            # Escribimos el contenido completo descargado
            f.write(contenido) 
            
        print(f"✅ Lista almacenada en: {ruta_temp} ({len(enlaces_unicos)} enlaces)")
        
    except Exception as e:
        print(f"❌ Error al guardar el archivo temporal: {e}")

# Nota: Esta función es llamada desde el main.py