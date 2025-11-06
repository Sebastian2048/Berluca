# m3u_core.py

import hashlib
import re
from typing import List, Optional

# =========================================================================================
# 🧱 UTILIDADES DE PARSING (Extracción)
# =========================================================================================

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """
    Extrae bloques M3U completos (EXTINF + URL) como listas de líneas.
    Es la función de parsing más robusta.
    """
    bloques = []
    current_block = []

    for linea in lineas:
        linea = linea.strip()
        
        # Ignorar líneas vacías o comentarios que no sean EXTINF
        if not linea or (linea.startswith("#") and not linea.startswith("#EXTINF")):
            continue

        if linea.startswith("#EXTINF"):
            # Si hay un bloque incompleto, lo descartamos
            if current_block:
                pass 
            current_block = [linea]
        elif current_block:
            # Línea de URL (asume que la URL sigue inmediatamente al EXTINF)
            current_block.append(linea)
            bloques.append(current_block)
            current_block = [] # Bloque completo, reiniciar
    
    # Esto maneja el caso donde el EXTINF estaba al final sin URL (debe ser raro)
    # y garantiza que solo bloques EXTINF + URL se añadan
    return bloques

def extraer_linea_extinf(bloque: List[str]) -> Optional[str]:
    """Busca y extrae la línea completa #EXTINF del bloque."""
    for linea in bloque:
        if linea.startswith("#EXTINF:"):
            return linea.strip()
    return None

def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal desde EXTINF."""
    extinf = extraer_linea_extinf(bloque)
    if extinf:
        partes = extinf.split(",", 1)
        if len(partes) == 2:
            return partes[1].strip()
    return "Sin nombre"

def extraer_url(bloque: List[str]) -> Optional[str]:
    """
    Busca la URL del canal, asumiendo que es la línea que no es #EXTINF y comienza con http/rtmp/etc.
    """
    for linea in bloque:
        url = linea.strip()
        if url.startswith(("http", "https", "rtmp", "udp")):
            # Se puede añadir una verificación de extensión aquí si es necesario,
            # pero asumiremos que cualquier URL es la correcta
            if not url.startswith("#"):
                return url
    return None

# =========================================================================================
# 🧼 UTILIDADES DE SANEAMIENTO Y HASHING
# =========================================================================================

def sanear_bloque_m3u(bloque: List[str]) -> Optional[List[str]]:
    """
    Sanea un bloque M3U a un formato estándar [EXTINF, URL]. 
    Devuelve el bloque limpio o None si es irreparable.
    """
    extinf_linea = extraer_linea_extinf(bloque)
    url_linea = extraer_url(bloque)
    
    # Un bloque es irreparable si le falta el EXTINF o la URL
    if not extinf_linea or not url_linea:
        return None 
        
    saneado = [extinf_linea]
    
    # Asegurar que la URL esté en una línea separada (el formato estándar)
    # aunque la URL ya se extrajo limpia, la ponemos en una línea aparte si no está ya
    if url_linea not in extinf_linea:
        saneado.append(url_linea)
        
    return saneado

def hash_bloque(bloque: List[str]) -> str:
    """
    Genera un hash MD5 de un bloque saneado para la deduplicación.
    Es CRUCIAL que se use el bloque SANEADO para evitar hashes diferentes 
    debido a líneas basura.
    """
    # Unimos el bloque saneado y lo codificamos
    return hashlib.md5("".join(bloque).encode("utf-8")).hexdigest()

# =========================================================================================
# 🧪 MÓDULO DE PRUEBA
# =========================================================================================

if __name__ == "__main__":
    test_lines = [
        "#EXTM3U",
        "#EXTINF:-1 tvg-id=\"CNN\" group-title=\"Noticias\",CNN en Vivo",
        "http://url.cnn.com/live/stream.m3u8",
        "",
        "#EXTINF:-1 group-title=\"Peliculas\", Pelicula Rota",
        "# LÍNEA BASURA"
    ]
    
    bloques = extraer_bloques_m3u(test_lines)
    print(f"Bloques extraídos ({len(bloques)}):")
    
    for b in bloques:
        saneado = sanear_bloque_m3u(b)
        if saneado:
            h = hash_bloque(saneado)
            print(f"  Bloque: {extraer_nombre_canal(saneado)} | Hash: {h} | Saneado: {saneado}")
        else:
            print(f"  Bloque descartado (Irreparable): {b}")