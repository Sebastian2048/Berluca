# extractor.py

import os
import requests
import re
from config import CARPETA_SALIDA # Necesitas importar la ubicación de la carpeta de salida

def recolectar_enlaces(url_lista: str):
    """
    Descarga el contenido de una URL de lista M3U y lo guarda en 
    TEMP_MATERIAL.m3u dentro de la carpeta de salida.
    """
    ruta_salida_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    
    # 1. Adaptar la URL (si es necesario)
    # Algunas plataformas requieren cambiar el 'view' o el final de la URL a 'raw'
    if "github" in url_lista.lower() and "/blob/" in url_lista.lower():
        url_raw = url_lista.replace("/blob/", "/raw/")
        print(f"🔗 URL RAW convertida: {url_raw}")
    else:
        url_raw = url_lista
        print(f"🔗 URL RAW: {url_raw}")

    # 2. Descargar el contenido
    print("📥 Descargando contenido RAW...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url_raw, headers=headers, timeout=30)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP malos (4xx o 5xx)
        
        contenido = response.text
        
        # 3. Limpieza y estandarización (opcional pero recomendado)
        # Aseguramos que el contenido empiece con #EXTM3U (si es necesario)
        if not contenido.strip().startswith("#EXTM3U"):
            contenido = "#EXTM3U\n" + contenido
        
        # 4. Guardar en el archivo temporal
        with open(ruta_salida_temp, "w", encoding="utf-8", errors="ignore") as f:
            f.write(contenido)
            
        # Contar enlaces (aproximado)
        num_enlaces = contenido.count("#EXTINF")
        
        print(f"✅ Lista almacenada en: {ruta_salida_temp} ({num_enlaces} enlaces)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de descarga o conexión: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")