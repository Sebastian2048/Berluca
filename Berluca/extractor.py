# extractor.py

import requests
import os 
from config import CARPETA_SALIDA
from utils import github_blob_a_raw, extraer_enlaces_m3u

def recolectar_enlaces(url_lista):
    print(f"\n📥 Descargando lista desde: {url_lista}\n")

    # 1. Convertir GitHub blob a raw si aplica
    url_final = github_blob_a_raw(url_lista)
    print(f"🔗 URL RAW convertida: {url_final}") 

    # 2. Definir la ruta temporal CORRECTA: Beluga/TEMP_MATERIAL.m3u
    # 🛑 CORRECCIÓN CLAVE: Usar CARPETA_SALIDA para la ruta temporal.
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    
    try:
        r = requests.get(url_final, timeout=10)
        if r.status_code != 200:
            print(f"❌ Error al descargar la lista (status {r.status_code}). URL usada: {url_final}")
            return

        enlaces = extraer_enlaces_m3u(r.text)
        enlaces_unicos = sorted(set(enlaces))

        # 3. Guardar en la ruta temporal correcta
        with open(ruta_temp, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")
            for enlace in enlaces_unicos:
                f.write(enlace + "\n\n") # Doble salto para bloques separados

        print(f"✅ Lista almacenada en: {ruta_temp} ({len(enlaces_unicos)} enlaces)\n")

    except Exception as e:
        print(f"❌ Error al procesar la URL: {e}")