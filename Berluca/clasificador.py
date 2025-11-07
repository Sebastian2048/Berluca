# clasificador.py
import os
import datetime 
from collections import Counter
from typing import List, Optional, Tuple, Set
import re 
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 📦 Importaciones de configuración
try:
    from config import (
        CARPETA_ORIGEN, CARPETA_SALIDA, CLAVES_CATEGORIA, 
        contiene_exclusion, LIMITE_BLOQUES, OVERFLOW_MAP,
        CLAVES_ESPANOL, CLAVES_NO_ESPANOL
    )
except ImportError as e:
    logging.error(f"Error al importar configuración: {e}")
    CARPETA_ORIGEN = "Beluga/compilados"
    CARPETA_SALIDA = "Beluga"
    CLAVES_CATEGORIA = {"roll_over_general": ["tv"]}
    LIMITE_BLOQUES = 100
    OVERFLOW_MAP = {}
    CLAVES_ESPANOL = []
    CLAVES_NO_ESPANOL = ["eng"]
    def contiene_exclusion(texto): return False


# =========================================================================================
# 📦 FUNCIONES DE PARSEO (Se mantienen)
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
            buffer.append(linea)
            
    return [b for b in bloques if any(l.startswith("#EXTINF") for l in b) and any(l.startswith("http") for l in b)]

def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal desde EXTINF."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            partes = linea.split(",", 1)
            if len(partes) > 1:
                return partes[1].strip()
    return "Sin nombre"

def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL del canal (la primera línea que comienza con http)."""
    for linea in bloque:
        if linea.startswith("http"):
            return linea.strip()
    return ""

# =========================================================================================
# 💾 FUSIÓN Y GUARDADO CLAVE
# =========================================================================================

def obtener_urls_existentes(categoria: str) -> Tuple[Set[str], int]:
    """Lee el archivo existente de la categoría y devuelve las URLs únicas y el conteo de bloques."""
    ruta = os.path.join(CARPETA_ORIGEN, f"{categoria}.m3u")
    urls_existentes = set()
    conteo_bloques = 0
    
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                lineas = f.readlines()
            
            for bloque in extraer_bloques_m3u(lineas):
                url = extraer_url(bloque)
                if url:
                    urls_existentes.add(url)
                    conteo_bloques += 1
        except Exception as e:
            logging.warning(f"Error al leer el archivo existente {ruta}: {e}")
            
    return urls_existentes, conteo_bloques

def guardar_en_categoria(categoria: str, bloque: List[str]):
    """Añade un bloque al archivo de categoría existente (sin lógica de fecha)."""
    os.makedirs(CARPETA_ORIGEN, exist_ok=True)
    ruta = os.path.join(CARPETA_ORIGEN, f"{categoria}.m3u")

    modo_apertura = "a"
    if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        modo_apertura = "w"

    extinf = [l.strip() for l in bloque if l.startswith("#EXTINF")][0] if any(l.startswith("#EXTINF") for l in bloque) else None
    url = extraer_url(bloque)
    
    if extinf and url:
        # Limpiamos cualquier metadato de fecha antigua
        extinf = re.sub(r' exp-date="[^"]*"', '', extinf).strip()
        
        with open(ruta, modo_apertura, encoding="utf-8", errors="ignore") as f:
            if modo_apertura == "w":
                 f.write("#EXTM3U\n\n")
            f.write(extinf + "\n")      
            f.write(url + "\n\n")    

def clasificacion_multiple(bloque: List[str]) -> List[str]:
    """Devuelve una lista de categorías relevantes (snake_case) para un bloque."""
    nombre = extraer_nombre_canal(bloque)
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    
    categorias_encontradas = []
    
    for categoria, claves in CLAVES_CATEGORIA.items():
        # Excluimos las categorías de desbordamiento y roll_over_general en la primera pasada
        if categoria in OVERFLOW_MAP.values() or categoria == "roll_over_general": 
            continue 
        
        if any(clave in nombre_lower for clave in claves):
            categorias_encontradas.append(categoria)
            
    return categorias_encontradas if categorias_encontradas else ["sin_clasificar"]


# =========================================================================================
# 🧠 BUCLE PRINCIPAL DE CLASIFICACIÓN (Multi-Nivel Fallback con Idioma)
# =========================================================================================

def clasificar_enlaces():
    """
    Lee la lista TEMP_MATERIAL.m3u y FUSIONA los nuevos canales con los archivos 
    existentes en compilados/, aplicando la lógica de Idioma y Fallback.
    """
    
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    
    if not os.path.exists(ruta_temp):
        logging.error(f"Error: No se encontró el archivo TEMP_MATERIAL.m3u en {ruta_temp}.")
        return

    print("🧠 Iniciando clasificación y FUSIÓN de bloques...")

    with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques_nuevos = extraer_bloques_m3u(lineas)
    
    # Inicialización de conteo de URLs existentes
    urls_en_categoria = {}
    conteo_inicial_por_categoria = {}

    for categoria in CLAVES_CATEGORIA.keys():
        urls_en_categoria[categoria], conteo = obtener_urls_existentes(categoria)
        conteo_inicial_por_categoria[categoria] = conteo 

    totales_por_categoria = conteo_inicial_por_categoria.copy()
    
    excluidos_por_contenido = 0
    descartados_por_limite = 0
    bloques_agregados_a_disco = 0

    for bloque in bloques_nuevos:
        nombre = extraer_nombre_canal(bloque)
        url = extraer_url(bloque)
        nombre_lower = nombre.lower().replace("ñ", "n")
        
        if contiene_exclusion(nombre):
            excluidos_por_contenido += 1
            continue

        categorias_candidatas = clasificacion_multiple(bloque)
        guardado_exitoso = False
        categoria_principal = None
        
        # ⚠️ Verificación de Idioma ESTRICTA (Prioridad Máxima)
        is_not_spanish_language = any(clave in nombre_lower for clave in CLAVES_NO_ESPANOL)
        
        if is_not_spanish_language:
            
            categoria_destino = "roll_over_general" 
            
            if url not in urls_en_categoria.get(categoria_destino, set()):
                guardar_en_categoria(categoria_destino, bloque)
                urls_en_categoria[categoria_destino].add(url)
                totales_por_categoria[categoria_destino] += 1
                bloques_agregados_a_disco += 1
                guardado_exitoso = True
            
            continue 
            
        # 1. Bucle de Candidatos (Solo si el idioma es potencialmente español)
        if 'sin_clasificar' not in categorias_candidatas:
            
            for i, categoria in enumerate(categorias_candidatas):
                if i == 0:
                    categoria_principal = categoria 
                
                # A. Deduplicación
                if url in urls_en_categoria.get(categoria, set()):
                    guardado_exitoso = True
                    break
                    
                # B. Si la categoría está llena (LIMITE_BLOQUES)
                if totales_por_categoria.get(categoria, 0) >= LIMITE_BLOQUES:
                    continue 
                
                # C. Guardado exitoso
                guardar_en_categoria(categoria, bloque)
                urls_en_categoria[categoria].add(url)
                totales_por_categoria[categoria] += 1
                bloques_agregados_a_disco += 1
                guardado_exitoso = True
                break
                
            # 2. Lógica de Desbordamiento Específico (Overflow - Nivel Extra)
            if not guardado_exitoso and categoria_principal and categoria_principal in OVERFLOW_MAP:
                
                categoria_extra = OVERFLOW_MAP[categoria_principal]
                
                # Intentar guardar en la categoría EXTRA
                if url not in urls_en_categoria.get(categoria_extra, set()) and totales_por_categoria.get(categoria_extra, 0) < LIMITE_BLOQUES:
                    
                    guardar_en_categoria(categoria_extra, bloque)
                    urls_en_categoria[categoria_extra].add(url)
                    totales_por_categoria[categoria_extra] += 1
                    bloques_agregados_a_disco += 1
                    guardado_exitoso = True

        # 3. Último Recurso: Roll-Over General (Si falló la clasificación o es sin_clasificar)
        if not guardado_exitoso:
            categoria_final = "roll_over_general"
            
            if url not in urls_en_categoria.get(categoria_final, set()):
                guardar_en_categoria(categoria_final, bloque) 
                urls_en_categoria[categoria_final].add(url)
                totales_por_categoria[categoria_final] += 1
                bloques_agregados_a_disco += 1
                guardado_exitoso = True
            
        # 4. Descarte definitivo 
        if not guardado_exitoso:
            descartados_por_limite += 1
            continue


    print(f"✅ Fusión y Clasificación finalizada. Total bloques procesados: {len(bloques_nuevos)}")
    print(f"   -> Enlaces nuevos agregados a disco: {bloques_agregados_a_disco}")
    print(f"   -> Excluidos por contenido (religioso, etc.): {excluidos_por_contenido}")
    print(f"   -> Descartados por límite (no hubo fallback disponible): {descartados_por_limite}")
    
    categorias_generadas = [k for k, v in totales_por_categoria.items() if v > 0]
    categorias_finales = ", ".join(categorias_generadas)
    print(f"   -> Categorías con contenido total (incl. anterior): {categorias_finales}")
    print(f"📁 Archivos clasificados/fusionados en: {CARPETA_ORIGEN}/")
    
if __name__ == "__main__":
    clasificar_enlaces()