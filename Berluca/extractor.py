# extractor.py
import requests
import os
import logging
from typing import Optional

try:
    from config import CARPETA_SALIDA
except ImportError:
    CARPETA_SALIDA = "Beluga"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def recolectar_enlaces(url: str, nombre_temp: str = "TEMP_MATERIAL.m3u") -> Optional[str]:
    """
    Descarga la lista M3U de la URL y la guarda temporalmente.
    Retorna la ruta del archivo temporal si es exitoso.
    """
    ruta_temp = os.path.join(CARPETA_SALIDA, nombre_temp)
    
    print(f"🔗 Recolectando lista desde: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() 

        # Decodificación y limpieza (Movian a veces requiere encoding específico)
        contenido = response.text
        
        with open(ruta_temp, "w", encoding="utf-8", errors="ignore") as f:
            f.write(contenido)
        
        logging.info(f"✅ Lista guardada temporalmente en: {ruta_temp}")
        return ruta_temp
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error al descargar la lista: {e}")
        return None