# clasificador.py (VERSION CON BARRA DE PROGRESO - TQDM)
import os
import re 
from typing import List, Dict, Optional, Tuple, Set
import logging
import requests 
from tqdm import tqdm # NUEVA IMPORTACIÓN

# 📦 Importaciones de configuración y auxiliares
try:
    from config import (
        CLAVES_CATEGORIA, contiene_exclusion, CLAVES_NO_ESPANOL, 
        TITULOS_VISUALES, CLAVES_CATEGORIA_N2
    )
    from auxiliar import (
        extraer_bloques_m3u, extraer_nombre_canal, extraer_url
    )
except ImportError as e:
    logging.error(f"Error al importar configuración/auxiliares: {e}")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DEL CHECK REAL SELECTIVO ---
TIMEOUT_CHECK = 10 
VERIFICACION_SELECTIVA_RATIO = 500
contador_verificacion = 0

# =========================================================================================
# 🧠 LÓGICA DE ASIGNACIÓN
# =========================================================================================

def verificar_estado_canal(url: str, nombre: str, index: int) -> str:
    """
    Verificación selectiva de URL por HTTP para obtener el estado real.
    """
    global contador_verificacion
    contador_verificacion += 1

    # 1. Chequeo Selectivo
    if contador_verificacion % VERIFICACION_SELECTIVA_RATIO == 0:
        
        try:
            # Intentar obtener solo los headers (más rápido)
            response = requests.head(url, timeout=TIMEOUT_CHECK, allow_redirects=True)
            status_code = response.status_code

            # Códigos de éxito (abierto)
            if 200 <= status_code < 400:
                return "abierto"
            
            # Códigos dudosos (requiere autenticación, temporalmente no disponible, etc.)
            elif status_code in [401, 403, 408, 503]:
                return "dudoso"
            
            # 404 y otros errores se consideran fallidos
            else:
                return "fallido"
                
        except requests.exceptions.Timeout:
            return "dudoso" 
        except requests.exceptions.ConnectionError:
            return "fallido"
        except requests.exceptions.RequestException:
            return "fallido"
            
    # 2. Asignación por Defecto/Palabras Clave
    nombre_lower = nombre.lower()
    if "test" in nombre_lower or "demo" in nombre_lower or "prueba" in nombre_lower:
        return "dudoso"

    return "dudoso" 


def clasificar_bloque(bloque: List[str]) -> str:
    """Devuelve la mejor categoría (snake_case) para un bloque, usando Nivel 1 y Nivel 2."""
    nombre = extraer_nombre_canal(bloque)
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    
    # 1. Filtro de Idioma Estricto
    is_not_spanish_language = any(clave in nombre_lower for clave in CLAVES_NO_ESPANOL)
    if is_not_spanish_language:
        return "roll_over" 

    # 2. Bucle Nivel 1
    for categoria, claves in CLAVES_CATEGORIA.items():
        if categoria == "roll_over": continue
        
        if any(clave in nombre_lower for clave in claves):
            return categoria
            
    # 3. Bucle Nivel 2
    for categoria, claves in CLAVES_CATEGORIA_N2.items():
        if any(clave in nombre_lower for clave in claves):
            return categoria
            
    return "roll_over" 


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CLASIFICACIÓN
# =========================================================================================

def clasificar_enlaces(ruta_temp: str) -> List[Dict]:
    """
    Lee la lista temporal, asigna categoría, estado y retorna bloques enriquecidos.
    """
    global contador_verificacion
    contador_verificacion = 0 
    
    if not os.path.exists(ruta_temp):
        logging.error(f"Error: No se encontró el archivo temporal en {ruta_temp}.")
        return []

    print("🧠 Iniciando clasificación, asignación de estado y enriquecimiento de bloques...")

    with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques_nuevos = extraer_bloques_m3u(lineas)
    bloques_enriquecidos = []
    
    urls_procesadas = set()
    excluidos_por_contenido = 0
    
    # 🌟 IMPLEMENTACIÓN DE LA BARRA DE PROGRESO 🌟
    # Envolvemos el bucle for con tqdm para mostrar el progreso
    for i, bloque in enumerate(tqdm(bloques_nuevos, desc="Analizando Canales", unit="Canal")):
        # --- Lógica de procesamiento de bloques (sin cambios) ---
        nombre = extraer_nombre_canal(bloque)
        url = extraer_url(bloque)
        
        if not url or url in urls_procesadas:
            continue
            
        urls_procesadas.add(url)
            
        if contiene_exclusion(nombre):
            excluidos_por_contenido += 1
            continue

        # 1. Asignar Categoría (Nivel 1 y Nivel 2)
        categoria = clasificar_bloque(bloque)

        # 2. Asignar Estado (VERIFICACIÓN REAL SELECTIVA)
        estado = verificar_estado_canal(url, nombre, i)
        
        # 3. Enriquecer el bloque
        
        extinf_line = [l for l in bloque if l.startswith("#EXTINF")][0]
        
        # Añadimos la categoría como group-title 
        titulo_visual = TITULOS_VISUALES.get(categoria, f"★ {categoria.replace('_', ' ').upper()} ★")
        extinf_line_mod = re.sub(r'group-title="[^"]*"', f'group-title="{titulo_visual}"', extinf_line)
        if 'group-title' not in extinf_line_mod:
            extinf_line_mod = extinf_line_mod.replace(f",{nombre}", f' group-title="{titulo_visual}",{nombre}')

        # El bloque final para el inventario:
        bloques_enriquecidos.append({
            "bloque": [extinf_line_mod, f"#ESTADO:{estado}", url], 
            "url": url,
            "nombre_limpio": nombre.strip().lower().replace(" ", "").replace("ñ", "n"),
            "categoria": categoria,
            "estado": estado
        })
    # --- Fin de la lógica de procesamiento de bloques ---

    print(f"✅ Clasificación y Enriquecimiento finalizados. Bloques listos para distribuir: {len(bloques_enriquecidos)}")
    print(f"   -> Verificaciones de estado realizadas: {contador_verificacion // VERIFICACION_SELECTIVA_RATIO}")
    print(f"   -> Excluidos por contenido (religioso, etc.): {excluidos_por_contenido}")
    
    return bloques_enriquecidos