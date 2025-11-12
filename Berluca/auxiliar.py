# auxiliar.py
import re
import os
import requests
import logging
import json
from typing import List, Dict, Tuple, Set, Any, Optional

# 📦 Importaciones de configuración
try:
    # CRÍTICO: Importar estas configuraciones para la lógica de prioridad y categoría
    from config import PRIORIDAD_ESTADO, TITULOS_VISUALES, CLAVES_CATEGORIA, CLAVES_CATEGORIA_N2
except ImportError:
    # Definiciones de fallback si falla la importación
    PRIORIDAD_ESTADO = {"abierto": 3, "dudoso": 2, "fallido": 1, "desconocido": 0}
    TITULOS_VISUALES = {}
    CLAVES_CATEGORIA = {}
    CLAVES_CATEGORIA_N2 = {}


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
            print(f"🗑️ Archivo temporal {os.path.basename(ruta_temp)} eliminado.") # Se mantiene el print del usuario
    except Exception as e:
        logging.error(f"No se pudo eliminar el archivo temporal {ruta_temp}: {e}")


# =========================================================================================
# 📝 EXTRACCIÓN Y PARSEO DE BLOQUES M3U
# =========================================================================================

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """Divide las líneas de un archivo M3U en bloques de canal."""
    bloques = []
    bloque_actual = []
    in_block = False

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        if linea.startswith("#EXTM3U"):
            continue

        if linea.startswith("#EXTINF"):
            if in_block and bloque_actual:
                # Si el bloque anterior no terminó en URL, se añade
                # (Esto no debería pasar con archivos bien formados)
                pass 
                
            # Iniciar nuevo bloque con la línea EXTINF
            bloque_actual = [linea]
            in_block = True
            
        elif in_block:
            if re.match(r'^https?://', linea):
                # Si la línea es una URL, termina el bloque
                bloque_actual.append(linea)
                bloques.append(bloque_actual)
                bloque_actual = []
                in_block = False
            else:
                # Si es metadata como #ESTADO:, se añade al bloque
                bloque_actual.append(linea)
        
    return bloques


def extraer_url(bloque: List[str]) -> str:
    """Extrae la URL (última línea que no empieza por #) del bloque de canal."""
    # Buscar la última línea que parezca una URL
    for linea in reversed(bloque):
        if re.match(r'^https?://', linea.strip()):
            return linea.strip()
    return ""


def extraer_nombre_canal(bloque: List[str]) -> str:
    """Extrae el nombre del canal de la línea #EXTINF."""
    if not bloque:
        return "Sin Nombre"
    
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            match = re.search(r',(.+)$', linea)
            nombre = match.group(1).strip() if match else "Sin Nombre"
            # Limpieza básica
            nombre = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)|\-HD|\-SD|\-HQ', '', nombre).strip()
            return nombre
            
    return "Sin Nombre"


def extraer_estado(bloque: List[str]) -> str:
    """Extrae el estado ('abierto', 'dudoso', 'fallido', 'desconocido') del bloque."""
    for linea in bloque:
        if linea.startswith("#ESTADO:"):
            return linea.split(':')[1].strip().lower()
    return "desconocido"


def extraer_prioridad(bloque: List[str]) -> int:
    """Extrae la prioridad (numérica) del bloque basada en el estado."""
    estado = extraer_estado(bloque)
    return PRIORIDAD_ESTADO.get(estado, 0)


def normalizar_nombre(nombre: str) -> str:
    """
    Normaliza un nombre para usarlo como clave interna (snake_case).
    Función base para normalización de texto.
    """
    if not nombre: return "sin_categoria"
        
    nombre = nombre.strip().lower()

    # Reemplazos de caracteres
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', '&': 'y', ' ': '_', '-': '_',
    }
    for k, v in reemplazos.items():
        nombre = nombre.replace(k, v)
        
    nombre = re.sub(r'[^a-z0-9_]', '', nombre)
    nombre = re.sub(r'_+', '_', nombre).strip('_')
    
    return nombre if nombre else "sin_categoria"


def extraer_categoria_del_bloque(bloque: List[str]) -> str:
    """
    Extrae la categoría del campo 'group-title' del bloque.
    Retorna la clave interna de categoría (snake_case).
    """
    if not bloque: return "roll_over"
        
    # Buscar group-title
    match = re.search(r'group-title="([^"]+)"', bloque[0])
    if match:
        titulo_visual = match.group(1).strip()
        
        # 1. Intentar reversar el mapeo TITULOS_VISUALES (para archivos generados)
        for clave, titulo in TITULOS_VISUALES.items():
            if titulo.strip().lower() == titulo_visual.strip().lower():
                 return clave
        
        # 2. Si no es un título visual conocido, normalizar y clasificar
        nombre_normalizado = normalizar_nombre(titulo_visual) 

        # 3. Mapeo a las claves principales (como fallback)
        for clave_principal in CLAVES_CATEGORIA.keys():
             if clave_principal in nombre_normalizado:
                 return clave_principal
        
        # 4. Fallback: roll_over
        return "roll_over" 

    # 5. Fallback final
    return "roll_over"


# =========================================================================================
# 🧠 FUNCIONES DE EXTRACCIÓN Y BALANCEO (CRÍTICO PARA SERVIDOR.PY)
# =========================================================================================

def obtener_inventario_general(ruta_resumen_auditoria: str) -> List[Dict[str, Any]]:
    """
    CRÍTICA: Lee el archivo final de auditoría (RP_Resumen_Auditoria.m3u) y 
    retorna una lista plana de diccionarios de canales, incluyendo el estado y la prioridad.
    """
    
    if not os.path.exists(ruta_resumen_auditoria):
        logging.warning(f"⚠️ Archivo de resumen de auditoría no encontrado: {ruta_resumen_auditoria}")
        return []

    with open(ruta_resumen_auditoria, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques = extraer_bloques_m3u(lineas)
    inventario_plano = []

    for bloque in bloques:
        url = extraer_url(bloque)
        if not url:
            continue
        
        estado = extraer_estado(bloque)
        prioridad = PRIORIDAD_ESTADO.get(estado, 0)
        nombre = extraer_nombre_canal(bloque)
        categoria = extraer_categoria_del_bloque(bloque)

        inventario_plano.append({
            "bloque": bloque,
            "url": url,
            "nombre": nombre,
            "estado": estado,
            "prioridad": prioridad,
            "categoria": categoria,
        })
        
    logging.info(f"Inventario general cargado: {len(inventario_plano)} canales.")
    return inventario_plano