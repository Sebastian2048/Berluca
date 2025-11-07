# auxiliar.py
import re
import os
import requests
import logging
from typing import List, Dict, Tuple, Set, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================================================================================
# ⬇️ DESCARGA Y MANEJO DE ARCHIVOS
# =========================================================================================

def descargar_lista(url: str, ruta_destino: str) -> bool:
    """Descarga el contenido de la URL en la ruta_destino."""
    try:
        # Usamos stream=True y un chunksize para manejar archivos muy grandes
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status() # Lanza HTTPError si el status code es 4xx o 5xx
        
        # Crear la carpeta de destino si no existe
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: # filtrar por seguridad
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la descarga desde {url}: {e}")
        return False
    except Exception as e:
        logging.error(f"Error inesperado al descargar o escribir el archivo: {e}")
        return False

def limpiar_archivos_temporales(ruta_temp: str):
    """Elimina el archivo temporal M3U."""
    try:
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
            print(f"🗑️ Archivo temporal {os.path.basename(ruta_temp)} eliminado.")
    except Exception as e:
        logging.error(f"No se pudo eliminar el archivo temporal {ruta_temp}: {e}")

# =========================================================================================
# ✂️ PARSEO Y EXTRACCIÓN
# =========================================================================================

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """Divide las líneas de un archivo M3U en bloques de canales."""
    bloques = []
    bloque_actual = []
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
            
        if linea.startswith("#EXTINF"):
            if bloque_actual:
                bloques.append(bloque_actual)
            bloque_actual = [linea]
        elif bloque_actual:
            bloque_actual.append(linea)
            
    if bloque_actual:
        bloques.append(bloque_actual)
        
    return bloques

def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal de la línea #EXTINF."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            # Busca el nombre del canal después de la coma (,)
            if ',' in linea:
                return linea.split(',')[-1].strip()
    return "Desconocido"

def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL del canal (la última línea del bloque)."""
    # La URL siempre es la última línea de un bloque M3U válido
    return bloque[-1].strip() if bloque and not bloque[-1].startswith('#') else ""

# =========================================================================================
# ⚙️ EXTRACCIÓN DE METADATA ENRIQUECIDA (PARA INVENTARIO)
# =========================================================================================

def extraer_estado(bloque: List[str]) -> str:
    """Extrae el estado del bloque (ej: #ESTADO:abierto)."""
    for linea in bloque:
        if linea.startswith("#ESTADO:"):
            return linea.split(':')[-1].strip().lower()
    return "desconocido"

def extraer_prioridad(bloque: List[str]) -> int:
    """Extrae la prioridad (solo si se necesita para comparar bloques)."""
    # Mapeo simple basado en el estado (debería coincidir con config.PRIORIDAD_ESTADO)
    estado = extraer_estado(bloque)
    return {"abierto": 3, "dudoso": 2, "fallido": 1, "desconocido": 0}.get(estado, 0)

def extraer_categoria_del_bloque(bloque: List[str]) -> str:
    """Extrae la categoría del atributo group-title."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            match = re.search(r'group-title="([^"]*)"', linea)
            if match:
                # Normaliza el título visual a snake_case para usarlo como clave
                titulo_visual = match.group(1).strip()
                # Eliminamos emojis, estrellas y convertimos a snake_case (ej: TV ARGENTINA -> tv_argentina)
                limpio = re.sub(r'[^\w\s]', '', titulo_visual).lower()
                return '_'.join(limpio.split())
    return ""