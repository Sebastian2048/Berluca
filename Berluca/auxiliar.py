# auxiliar.py
from typing import List, Optional
import re
import os
import sys

# 📦 Importaciones de configuración. Intentamos importar config directamente.
try:
    # Intenta importar del módulo local (asumiendo que Beluca es la carpeta raíz)
    # Esto ayuda a VSCode a resolver las rutas.
    from config import PRIORIDAD_ESTADO
except ImportError:
    # Si falla la importación (ej. al ejecutar directamente), usamos un diccionario vacío 
    # para que el script no crashee antes de tiempo.
    PRIORIDAD_ESTADO = {}

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """Extrae bloques M3U completos (EXTINF + URL) como listas de líneas."""
    bloques = []
    buffer = []
    for linea in lineas:
        linea = linea.strip()
        if not linea or (linea.startswith("#") and not linea.startswith(("#EXTINF", "#ESTADO"))):
            continue
        
        # Inicio de un nuevo bloque
        if linea.startswith("#EXTINF"):
            if buffer: bloques.append(buffer)
            buffer = [linea]
        elif linea.startswith("#ESTADO:"):
            buffer.insert(1, linea)
        elif buffer and linea.startswith("http"): 
            buffer.append(linea)
            bloques.append(buffer)
            buffer = []
        elif buffer: 
            buffer.append(linea)
            
    if buffer: bloques.append(buffer)
    
    # Filtrar solo bloques que tienen EXTINF y una URL
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
    """Extrae la URL del canal."""
    for linea in bloque:
        if linea.startswith("http"):
            return linea.strip()
    return ""

def extraer_categoria_del_bloque(bloque: List[str]) -> Optional[str]:
    """Extrae la categoría del group-title si existe."""
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            match = re.search(r'group-title="([^"]*)"', linea)
            if match:
                raw_title = match.group(1).strip().lower()
                # Quitar caracteres especiales y reemplazar espacio por _
                cleaned_title = re.sub(r'[^\w\s]', '', raw_title).strip().replace(" ", "_")
                return cleaned_title
    return None

def extraer_estado(bloque: List[str]) -> str:
    """Busca la línea #ESTADO:X y devuelve X."""
    for linea in bloque:
        if linea.startswith("#ESTADO:"):
            estado = linea.split(":", 1)[-1].strip().lower()
            # Usamos la variable PRIORIDAD_ESTADO importada
            return estado if estado in PRIORIDAD_ESTADO else "desconocido"
    return "desconocido"

def extraer_prioridad(bloque: List[str]) -> int:
    """Devuelve el nivel de prioridad del canal."""
    estado = extraer_estado(bloque)
    # Usamos la variable PRIORIDAD_ESTADO importada
    return PRIORIDAD_ESTADO.get(estado, 0)