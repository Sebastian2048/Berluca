# extractor.py

import os
import requests
from typing import Optional

# Importaciones limpias
from config import CARPETA_SALIDA, CARPETA_ORIGEN
from utils import github_blob_a_raw
from m3u_core import extraer_bloques_m3u # Para asegurar que solo se guardan bloques M3U válidos

# 📁 Ruta de archivo temporal para la lista descargada
RUTA_TEMP_LISTA = os.path.join(CARPETA_ORIGEN, "TEMP_MATERIAL.m3u")

def recolectar_enlaces(url_lista: str) -> Optional[str]:
    """
    Descarga una lista M3U desde una URL, extrae los bloques válidos 
    y los guarda en un archivo temporal.
    Retorna la ruta del archivo temporal si es exitoso, sino None.
    """
    print(f"\n📥 Descargando lista desde: {url_lista}")

    # 1. Sanear URL (convertir blob a raw, si aplica)
    url_final = github_blob_a_raw(url_lista)

    try:
        # 2. Descargar contenido
        r = requests.get(url_final, timeout=15)
        r.raise_for_status() # Lanza error para códigos 4xx/5xx

        # 3. Extraer bloques y sanear
        lineas = r.text.splitlines()
        bloques = extraer_bloques_m3u(lineas)
        
        # 4. Procesar bloques y eliminar duplicados de URLs
        bloques_unicos = []
        urls_vistas = set()
        for bloque in bloques:
            # Simplificamos la deduplicación aquí antes de la clasificación pesada
            url = bloque[-1] # Asumimos URL es la última línea
            if url not in urls_vistas:
                bloques_unicos.append(bloque)
                urls_vistas.add(url)


        if not bloques_unicos:
            print("❌ La lista descargada no contiene bloques M3U válidos.")
            return None

        # 5. Guardar en archivo temporal
        os.makedirs(CARPETA_ORIGEN, exist_ok=True)
        with open(RUTA_TEMP_LISTA, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for bloque in bloques_unicos:
                f.write("\n".join(bloque).strip() + "\n\n")

        print(f"✅ Lista almacenada en: {RUTA_TEMP_LISTA} ({len(bloques_unicos)} bloques)")
        return RUTA_TEMP_LISTA

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red/descarga al procesar la URL: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None