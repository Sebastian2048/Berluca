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
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status() 
        
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: 
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
        
    # Limpieza: La URL debe ser el último elemento y no una línea de metadata.
    bloques_limpios = []
    for bloque in bloques:
        # Encontrar la línea que no es metadata (la URL)
        url_linea = [l for l in bloque if not l.startswith('#')]
        
        if url_linea:
            url = url_linea[0]
            # Bloque final: [EXTINF, #ESTADO:..., URL]
            bloque_final = [l for l in bloque if l.startswith('#EXTINF')] + \
                           [l for l in bloque if l.startswith('#ESTADO:')] + \
                           [url]
            bloques_limpios.append(bloque_final)
        
    return bloques_limpios

def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal de la línea #EXTINF."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            # Usar regex para obtener el nombre después de la última coma
            match = re.search(r',(.+?)(?:\s*#ESTADO_AUDITORIA:|$)', linea)
            if match:
                return match.group(1).strip()
    return "Desconocido"

def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL del canal (la última línea del bloque)."""
    # La URL es la última línea, siempre que no empiece por #
    return bloque[-1].strip() if bloque and not bloque[-1].startswith('#') else ""

# =========================================================================================
# ⚙️ EXTRACCIÓN Y NORMALIZACIÓN DE METADATA (PARA INVENTARIO)
# =========================================================================================

def extraer_estado(bloque: List[str]) -> str:
    """Extrae el estado del bloque (ej: #ESTADO:abierto)."""
    for linea in bloque:
        if linea.startswith("#ESTADO:"):
            return linea.split(':')[-1].strip().lower()
    return "desconocido"

def extraer_prioridad(bloque: List[str]) -> int:
    """Extrae la prioridad (solo si se necesita para comparar bloques)."""
    estado = extraer_estado(bloque)
    return {"abierto": 3, "dudoso": 2, "fallido": 1, "desconocido": 0}.get(estado, 0)


def normalizar_categoria(nombre_categoria: str) -> str:
    """
    Limpia y estandariza el nombre de la categoría (group-title) para evitar 
    duplicados y categorías genéricas. Retorna un formato limpio (snake_case).
    """
    if not nombre_categoria:
        return "sin_categoria"

    # 1. Convertir a minúsculas, eliminar acentos
    nombre = nombre_categoria.lower()
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', '&': 'y', '-': ' '
    }
    for k, v in reemplazos.items():
        nombre = nombre.replace(k, v)
        
    # 2. Mapeo de sinónimos comunes a una forma estándar (para mejorar la calidad)
    sinonimos = {
        'peliculas': 'cine_peliculas',
        'series': 'series_tv',
        'sports': 'deportes_envivo',
        'futbol': 'deportes_envivo',
        'noticias': 'noticias',
        'news': 'noticias',
        'infantil': 'infantil_kids',
        'kids': 'infantil_kids',
        'adultos': 'adulta_xxx', # Asumiendo que las quieres fuera, pero se normalizan
        'canales abiertos': 'variedad_gen'
    }
    
    for k, v in sinonimos.items():
        if k in nombre:
            # Usar el valor normalizado si encuentra un sinónimo
            nombre = v 
            break 

    # 3. Eliminar caracteres no deseados y espacios múltiples
    nombre = re.sub(r'[^\w\s]', '', nombre)
    nombre = re.sub(r'\s+', '_', nombre).strip('_')
    
    # 4. Evitar que quede vacío
    return nombre if nombre else "sin_categoria"


def extraer_categoria_del_bloque(bloque: List[str]) -> str:
    """Extrae la categoría del atributo group-title y la normaliza."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            match = re.search(r'group-title="([^"]*)"', linea)
            if match:
                # Usar la nueva función de normalización
                return normalizar_categoria(match.group(1).strip())
    return "sin_categoria"