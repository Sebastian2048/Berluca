import os
import re
from typing import List, Optional
from collections import Counter

# 📦 Importaciones de configuración (Asegúrate que LIMITE_BLOQUES esté en config.py)
from config import (
    CARPETA_ORIGEN, CARPETA_SALIDA, CLAVES_CATEGORIA, 
    contiene_exclusion, UMBRAL_EXCLUSION_ARCHIVO, LIMITE_BLOQUES
)

# =========================================================================================
# 📦 PARSEO DE BLOQUES M3U 
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
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            partes = linea.split(",", 1)
            if len(partes) > 1:
                return partes[1].strip()
    return "Sin nombre"

def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL del canal."""
    return bloque[-1].strip() if len(bloque) > 1 and bloque[-1].startswith("http") else ""

def extraer_linea_extinf(bloque: List[str]) -> str:
    """Extrae la línea #EXTINF."""
    return bloque[0] if bloque and bloque[0].startswith("#EXTINF") else ""

# =========================================================================================
# 💾 GUARDADO DE BLOQUES CLASIFICADOS (OPTIMIZADO PARA MOVIAN)
# =========================================================================================

def guardar_en_categoria(categoria: str, bloque: List[str]):
    """Guarda un bloque en su archivo de categoría correspondiente, limpio para reproductores."""
    os.makedirs(CARPETA_ORIGEN, exist_ok=True)
    ruta = os.path.join(CARPETA_ORIGEN, f"{categoria}.m3u")

    if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        with open(ruta, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")

    # 🛑 CORRECCIÓN MOVIAN: Escribe EXTINF y URL limpias, cada uno en su línea.
    with open(ruta, "a", encoding="utf-8", errors="ignore") as f:
        if len(bloque) >= 2:
            f.write(bloque[0].strip() + "\n")      
            f.write(bloque[1].strip() + "\n\n")    

# =========================================================================================
# ⚙️ CLASIFICACIÓN SEMÁNTICA 
# =========================================================================================

def clasificar_por_experiencia(bloque: List[str], nombre: str) -> Optional[str]:
    if "premium" in nombre.lower() and "deportes" in nombre.lower():
        return "deportes_premium"
    return None

def clasificar_por_nombre(nombre: str) -> Optional[str]:
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    for categoria, claves in CLAVES_CATEGORIA.items():
        if any(clave in nombre_lower for clave in claves):
            return categoria
    return None

def clasificar_por_metadato(bloque: List[str]) -> Optional[str]:
    extinf = extraer_linea_extinf(bloque)
    if not extinf: return None
    metadatos_lower = extinf.lower()
    match_group = re.search(r'group-title="([^"]*)"', metadatos_lower)
    if match_group:
        group_title = match_group.group(1).lower().replace(" ", "_")
        if "peliculas" in group_title: return "peliculas"
        if "series" in group_title: return "series"
        if "deportes" in group_title: return "deportes"
    return None

def clasificar_por_url(url: str) -> Optional[str]:
    url_lower = url.lower()
    if "movies" in url_lower or "vod" in url_lower:
        return "series_general" if "series" in url_lower else "peliculas_general"
    return None

def clasificacion_doble(bloque: List[str]) -> str:
    """Combina todas las estrategias de clasificación con resolución de colisiones."""
    nombre = extraer_nombre_canal(bloque)
    url = extraer_url(bloque)

    experiencia = clasificar_por_experiencia(bloque, nombre)
    if experiencia: return experiencia

    tema = clasificar_por_nombre(nombre) or clasificar_por_metadato(bloque)
    contexto = clasificar_por_url(url)

    if tema and contexto:
        if tema in ["peliculas", "series"] and contexto.endswith("_general"): return contexto
        elif tema in ["cine_terror", "anime"]: return tema

    return tema or contexto or "sin_clasificar"

def clasificar_bloque_por_contenido(bloque: List[str]) -> str:
    """Clasificación final con normalización de categoría."""
    categoria = clasificacion_doble(bloque)
    return categoria.lower().replace(" ", "_").replace("/", "_").replace("-", "_").replace(".", "_")

# =========================================================================================
# 🧠 BUCLE PRINCIPAL DE CLASIFICACIÓN (FINAL Y CORREGIDO)
# =========================================================================================

def clasificar_enlaces():
    """
    Clasifica bloques, descarta 'sin_clasificar' y aplica LIMITE_BLOQUES
    antes de guardar.
    """
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    if not os.path.exists(ruta_temp):
        print("❌ Error: No se encontró el archivo TEMP_MATERIAL.m3u.")
        return

    print("🧠 Iniciando clasificación y guardado de bloques...")

    with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques = extraer_bloques_m3u(lineas)
    totales_por_categoria = Counter()
    excluidos_por_contenido = 0
    total_bloques_procesados = len(bloques)

    for bloque in bloques:
        nombre = extraer_nombre_canal(bloque)
        
        # 1. Exclusión por contenido (incluye el nuevo 24/7)
        if contiene_exclusion(nombre):
            excluidos_por_contenido += 1
            continue

        categoria = clasificar_bloque_por_contenido(bloque)
        
        # 🛑 REGLA 1: Descartar la categoría sin_clasificar
        if categoria == "sin_clasificar":
            totales_por_categoria[categoria] += 1
            continue 
            
        # 🛑 REGLA 2: Aplicar límite de bloques por categoría (Evita la densidad)
        if totales_por_categoria[categoria] >= LIMITE_BLOQUES:
             continue 

        # 3. Guardado en CARPETA_ORIGEN
        guardar_en_categoria(categoria, bloque)
        totales_por_categoria[categoria] += 1

    print(f"✅ Clasificación finalizada. Total bloques procesados: {total_bloques_procesados}")
    print(f"   -> Excluidos por contenido (24/7, religioso, etc.): {excluidos_por_contenido}")
    print(f"   -> Bloques no clasificados y descartados: {totales_por_categoria.get('sin_clasificar', 0)}")
    print(f"   -> Categorías generadas: {', '.join(k for k in totales_por_categoria.keys() if k != 'sin_clasificar')}")
    print(f"📁 Archivos clasificados en: {CARPETA_ORIGEN}/")