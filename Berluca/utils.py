import requests
import re
import os
import json
from typing import List, Optional
from urllib.parse import urlparse

# =========================================================================================
# 🔗 FUNCIONES DE RED Y VERIFICACIÓN
# =========================================================================================

def verificar_disponibilidad(url: str) -> bool:
    """
    Realiza una petición HEAD simple y rápida para verificar si una URL está activa 
    y retorna el código 200 (OK).
    """
    try:
        # Usar un timeout bajo para la verificación rápida (5 segundos)
        r = requests.head(url, timeout=5) 
        # Si el código es 200 (OK), o 301/302 (Redirección exitosa), se considera disponible
        return r.status_code in [200, 301, 302] 
    except requests.exceptions.RequestException:
        # Captura errores de conexión, timeout, DNS, etc.
        return False
    except Exception:
        return False

def github_blob_a_raw(url: str) -> str:
    """Convierte una URL de visualización de archivo de GitHub (blob) a la URL de contenido raw."""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

def resolver_redireccion(url: str) -> str:
    """
    Resuelve acortadores de URL o redirecciones, devolviendo la URL final.
    """
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        if r.status_code == 404:
            return "❌ Enlace no disponible (Error 404)"
        elif r.status_code in [200, 301, 302]:
            return r.url # Devuelve la URL final después de las redirecciones
    except Exception as e:
        return f"❌ Error al resolver la URL: {e}"
    return url

# =========================================================================================
# 📦 FUNCIONES DE PARSEO M3U
# =========================================================================================

def extraer_enlaces_m3u(texto: str) -> List[str]:
    """
    Extrae bloques M3U completos (EXTINF + URL) de un texto.
    """
    bloques = []
    lineas = texto.strip().splitlines()
    for i in range(len(lineas) - 1):
        # Buscamos el patrón: Línea #EXTINF seguida de una línea que comienza con http/https
        if lineas[i].startswith("#EXTINF") and lineas[i+1].lower().startswith("http"):
            # Devolvemos el bloque de dos líneas
            bloques.append(f"{lineas[i]}\n{lineas[i+1]}")
    return bloques


# =========================================================================================
# 📂 FUNCIONES DE UTILIDAD DE GITHUB (PARA GUI/Extractor)
# =========================================================================================

def obtener_assets_de_release(url_repo: str) -> List[str]:
    """
    Intenta obtener una lista de assets (.m3u) de la última release de un repositorio de GitHub.
    """
    # Ejemplo de URL: https://github.com/user/repo -> https://api.github.com/repos/user/repo/releases/latest
    partes = urlparse(url_repo)
    path = partes.path.strip("/")
    if not path:
        return []

    api_url = f"https://api.github.com/repos/{path}/releases/latest"

    try:
        r = requests.get(api_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            assets = data.get('assets', [])
            
            # Filtrar solo archivos m3u
            listas_m3u = [asset['name'] for asset in assets if asset['name'].endswith(('.m3u', '.m3u8'))]
            return listas_m3u
            
    except Exception:
        return []
    
    return []

def reconstruir_url_desde_nombre(url_repo: str, nombre_asset: str) -> str:
    """
    Reconstruye la URL de descarga para un asset de GitHub o un archivo en el master/main.
    Se asume que el archivo está en la raíz de la rama 'main'.
    """
    base_url = github_blob_a_raw(url_repo)
    # Ejemplo: https://raw.githubusercontent.com/user/repo/main/lista.m3u
    
    # 1. Limpieza de URL de repositorio
    if "/tree/" in base_url: # Si el usuario pegó una URL de 'tree'
         base_url = base_url.split("/tree/")[0]
         
    # 2. Aseguramos la rama 'main' (o 'master')
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')

    # Si la URL no termina con el repositorio, añadimos la rama
    if "/main" not in base_url and "/master" not in base_url:
        # Se asume la rama 'main' para la descarga raw
        base_url += "/main" 
    
    return f"{base_url}/{nombre_asset}"