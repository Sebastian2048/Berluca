import os
import re
from typing import List, Optional
from collections import Counter

# Importaciones de constantes y rutas (Asegúrate de que 'config' tiene contiene_exclusion y las rutas)
from config import (
    CARPETA_ORIGEN, CARPETA_SALIDA, CLAVES_CATEGORIA, 
    contiene_exclusion, UMBRAL_EXCLUSION_ARCHIVO
)

# =========================================================================================
# 📦 FUNCIONES DE PARSEO M3U 
# =========================================================================================

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """Extrae bloques M3U completos (EXTINF + URL) como listas de líneas."""
    bloques = []
    buffer = []

    for linea in lineas:
        linea = linea.strip()
        if not linea or (linea.startswith("#") and not linea.startswith("#EXTINF")):
            continue
        if linea.startswith("#EXTINF"):
            if buffer and len(buffer) == 1:
                pass
            buffer = [linea]
        elif buffer and linea.startswith("http"): 
            buffer.append(linea)
            bloques.append(buffer)
            buffer = []
        elif buffer: 
            pass

    return bloques


def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal desde EXTINF."""
    if isinstance(bloque, list):
        for linea in bloque:
            if linea.startswith("#EXTINF"):
                partes = linea.split(",", 1)
                if len(partes) > 1:
                    return partes[1].strip()
    return "Sin nombre"


def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL del canal."""
    if isinstance(bloque, list) and len(bloque) > 1 and bloque[-1].startswith("http"):
        return bloque[-1].strip()
    return ""


def extraer_linea_extinf(bloque: List[str]) -> str:
    """Extrae la línea #EXTINF."""
    return bloque[0] if bloque and bloque[0].startswith("#EXTINF") else ""

# 💾 Función para guardar un bloque en su archivo de categoría correspondiente
def guardar_en_categoria(categoria: str, bloque: List[str]):
    os.makedirs(CARPETA_ORIGEN, exist_ok=True)
    ruta = os.path.join(CARPETA_ORIGEN, f"{categoria}.m3u")

    if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        with open(ruta, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")

    with open(ruta, "a", encoding="utf-8", errors="ignore") as f:
        f.write("\n".join(bloque) + "\n\n")


# =========================================================================================
# ⚙️ LÓGICA DE CLASIFICACIÓN
# =========================================================================================

def clasificar_por_experiencia(bloque: List[str], nombre: str) -> Optional[str]:
    # Función de stub, si tienes la lógica real úsala aquí.
    if "premium" in nombre.lower() and "deportes" in nombre.lower():
        return "deportes_premium"
    return None 

def clasificar_por_nombre(nombre: str) -> Optional[str]:
    """Clasifica basándose en el nombre del canal usando CLAVES_CATEGORIA."""
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    
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
    
    match_group = re.search(r'group-title="([^"]*)"', metadatos_lower)
    if match_group:
        group_title = match_group.group(1).lower().replace(" ", "_")
        if "peliculas" in group_title: return "peliculas"
        if "series" in group_title: return "series"
        if "deportes" in group_title: return "deportes"
    
    return None


def clasificar_por_url(url: str) -> Optional[str]:
    """Clasifica basándose en patrones conocidos de la URL."""
    url_lower = url.lower()
    if "movies" in url_lower or "vod" in url_lower:
        if "series" in url_lower:
            return "series_general"
        return "peliculas_general"
    return None


def clasificacion_doble(bloque: List[str]) -> str:
    """Combina todas las estrategias de clasificación."""
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

    # 🚫 Resolución de colisiones
    if tema and contexto:
        if tema in ["peliculas", "series"] and contexto.endswith("_general"):
             return contexto
        elif tema in ["cine_terror", "anime"]:
            return tema

    if tema:
        return tema
    
    if contexto:
        return contexto

    return "sin_clasificar"


def clasificar_bloque_por_contenido(bloque: List[str]) -> str:
    """Función de clasificación final."""
    categoria = clasificacion_doble(bloque) 
    return categoria.lower().replace(" ", "_").replace("/", "_").replace("-", "_").replace(".", "_")


# =========================================================================================
# 🧠 FUNCIÓN DE BUCLE PRINCIPAL (CORRECCIÓN DE RUTA DE LECTURA)
# =========================================================================================

def clasificar_enlaces():
    """
    Lee el archivo temporal desde CARPETA_SALIDA, clasifica cada bloque 
    y lo guarda en su categoría en la carpeta 'compilados' (CARPETA_ORIGEN).
    """
    # 🛑 CORRECCIÓN CLAVE: Usa CARPETA_SALIDA para el archivo temporal
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    
    if not os.path.exists(ruta_temp):
        print("❌ Error: No se encontró el archivo TEMP_MATERIAL.m3u. Asegúrate de que la descarga fue exitosa.")
        return

    print("🧠 Iniciando clasificación y guardado de bloques...")
    
    with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()
    
    bloques = extraer_bloques_m3u(lineas)
    totales_por_categoria = Counter()
    excluidos_por_contenido = 0
    total_bloques = len(bloques)

    for bloque in bloques:
        nombre = extraer_nombre_canal(bloque)
        
        # 1. Depuración selectiva (exclusión por contenido)
        if contiene_exclusion(nombre):
            excluidos_por_contenido += 1
            continue
            
        # 2. Clasificación
        categoria = clasificar_bloque_por_contenido(bloque)
        
        # 3. Guardado en CARPETA_ORIGEN
        guardar_en_categoria(categoria, bloque)
        totales_por_categoria[categoria] += 1
    
    print(f"✅ Clasificación inicial finalizada. Total bloques procesados: {total_bloques}")
    print(f"   -> Excluidos por contenido: {excluidos_por_contenido}")
    print(f"   -> Categorías generadas: {', '.join(totales_por_categoria.keys())}")
    print(f"📁 Archivos clasificados por categoría en: {CARPETA_ORIGEN}/")