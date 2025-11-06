import re
from typing import List, Optional

# Importaciones del nuevo módulo de experiencia
from clasificador_experiencia import clasificar_por_experiencia 

# Importaciones de constantes
from config import CLAVES_CATEGORIA 
from m3u_core import (
    extraer_nombre_canal, 
    extraer_url, 
    extraer_linea_extinf # Asumo que m3u_core existe y tiene estas funciones
)

# =========================================================================================
# ⚙️ FUNCIONES AUXILIARES DE CLASIFICACIÓN
# =========================================================================================

def clasificar_por_nombre(nombre: str) -> Optional[str]:
    """
    Clasifica un bloque M3U basándose únicamente en el nombre del canal,
    usando las claves definidas en config.py.
    """
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    
    # Usar las claves importadas desde config.py
    for categoria, claves in CLAVES_CATEGORIA.items():
        if any(clave in nombre_lower for clave in claves):
            return categoria
    return None


def clasificar_por_metadato(bloque: List[str]) -> Optional[str]:
    """Clasifica basándose en metadatos como group-title o tvg-name del EXTINF."""
    extinf = extraer_linea_extinf(bloque)
    if not extinf:
        return None
        
    metadatos_lower = extinf.lower()
    
    # 1. Buscar group-title
    match_group = re.search(r'group-title="([^"]*)"', metadatos_lower)
    if match_group:
        group_title = match_group.group(1).lower().replace(" ", "_")
        if "peliculas" in group_title: return "peliculas"
        if "series" in group_title: return "series"
        if "deportes" in group_title: return "deportes"

    # 2. Buscar tvg-name o tvg-id
    match_tvg = re.search(r'tvg-name="([^"]*)"', metadatos_lower)
    if not match_tvg:
        match_tvg = re.search(r'tvg-id="([^"]*)"', metadatos_lower)

    if match_tvg:
        tvg_data = match_tvg.group(1).lower().replace(" ", "_")
        if "kids" in tvg_data or "infantil" in tvg_data: return "infantil_educativo"
        if "vod" in tvg_data or "peliculas" in tvg_data: return "peliculas"
    
    return None


def clasificar_por_url(url: str) -> Optional[str]:
    """Clasifica basándose en patrones conocidos de la URL (país, tipo de VOD, etc.)."""
    url_lower = url.lower()

    # Si la URL apunta a un VOD/Series
    if "movies" in url_lower or "vod" in url_lower:
        if "series" in url_lower:
            return "series_general"
        return "peliculas_general"

    # Clasificación geográfica
    if "ar." in url_lower or "/ar/" in url_lower or ".ar" in url_lower.split("/")[-1]:
        return "argentina_general"
    if "mx." in url_lower or "/mx/" in url_lower or ".mx" in url_lower.split("/")[-1]:
        return "mexico_general"
    if "es." in url_lower or "/es/" in url_lower:
        if "espn" not in url_lower:
            return "españa_general"

    return None

# =========================================================================================
# 🧠 FUNCIONES PRINCIPALES DE CLASIFICACIÓN
# =========================================================================================

def clasificacion_doble(bloque: List[str]) -> str:
    """
    Combina varias estrategias de clasificación para obtener el mejor resultado.
    Prioridad: Experiencia > Nombre/Metadato > URL > Default
    """
    nombre = extraer_nombre_canal(bloque)
    url = extraer_url(bloque)

    # 1. Clasificación por experiencia (MÁXIMA PRIORIDAD)
    experiencia = clasificar_por_experiencia(bloque, nombre) 
    if experiencia:
        return experiencia
    
    # 2. Clasificación temática (Nombre y Metadato)
    tema = clasificar_por_nombre(nombre) or clasificar_por_metadato(bloque)
    
    # 3. Clasificación contextual (URL)
    contexto = clasificar_por_url(url)

    # 🚫 Detección de colisiones y resolución
    if tema and contexto:
        # Priorizar clasificación de URL si es VOD/geográfica general
        if tema in ["peliculas", "series", "sagas", "documental_cultural"] and contexto.endswith("_general"):
             return contexto
        # Priorizar el tema si es muy específico
        elif tema in ["cine_terror", "anime"]:
            return tema

    # Usar el resultado de mayor prioridad restante
    if tema:
        return tema
    
    if contexto:
        return contexto

    return "sin_clasificar"


def clasificar_bloque_por_contenido(bloque: List[str]) -> str:
    """
    Función de clasificación final.
    """
    categoria = clasificacion_doble(bloque) 

    # Limpieza final de la categoría para nombres de archivo válidos
    return categoria.lower().replace(" ", "_").replace("/", "_").replace("-", "_").replace(".", "_")

# NOTA: La función 'clasificar_enlaces' que se usaba en 'main.py' ha sido reemplazada por
# 'clasificar_y_segmentar_archivos' en el módulo 'generador.py' en la nueva arquitectura.