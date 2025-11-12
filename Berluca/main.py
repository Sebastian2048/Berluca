# main.py
import os
import sys
import requests
import logging
import re # Necesario para procesar URLs de GitHub
# 🌟 CORRECCIÓN CRÍTICA: Añadir 'Tuple' a la importación de typing
from typing import List, Dict, Set, Any, Tuple 

# 📦 Importaciones de módulos locales
try:
    from config import CARPETA_SALIDA, MAX_SERVIDORES_BUSCAR
    from auxiliar import (
        descargar_lista, limpiar_archivos_temporales
    )
    from clasificador import clasificar_enlaces 
    from servidor import auditar_y_balancear_servidores, compilar_inventario_existente
    from auditor_conectividad import auditar_conectividad 

except ImportError as e:
    print(f"ERROR: No se pudo importar un módulo necesario. Asegúrate de tener todos los archivos (.py) en la misma carpeta.")
    print(f"Detalle del error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================================================================================
# ⚙️ GESTIÓN DE ENTRADA (Múltiples URLs - GitHub Scraper)
# =========================================================================================

def _url_to_api(repo_url: str) -> Tuple[str, str, str, str]:
    """Convierte una URL de repositorio de GitHub a su URL de API de Contenido."""
    
    # 1. Intentar hacer match con el patrón de directorio/subdirectorio (e.g., /tree/main/path)
    match_branch = re.search(r'github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)', repo_url)
    if match_branch:
        owner, repo, branch, path = match_branch.groups()
        return owner, repo, branch, path
        
    # 2. Intentar hacer match con la raíz del repositorio
    match_root = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
    if match_root:
        owner, repo = match_root.groups()
        return owner, repo, 'main', '' # Asumir rama 'main' y path raíz
    
    raise ValueError("URL de GitHub inválida o no soporta el formato de contenido.")


def _get_api_content_url(owner: str, repo: str, branch: str, path: str) -> str:
    """Construye la URL de la API de Contenido."""
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"


def extraer_urls_m3u_de_github(owner: str, repo: str, branch: str, path: str, urls_encontradas: Set[str]) -> None:
    """Función recursiva para extraer URLs M3U de la API de Contenido de GitHub."""
    
    api_url = _get_api_content_url(owner, repo, branch, path)
    
    # Se recomienda usar un User-Agent en peticiones a la API de GitHub
    headers = {'User-Agent': 'Beluga M3U Scraper (v1.0)'}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status() # Lanza HTTPError para 4xx/5xx

        contenido = response.json()
        
        if isinstance(contenido, list):
            for item in contenido:
                if item['type'] == 'file' and item['name'].lower().endswith('.m3u'):
                    # La API proporciona 'download_url', que es la URL RAW.
                    if item.get('download_url'):
                        urls_encontradas.add(item['download_url'])
                
                elif item['type'] == 'dir':
                    # Llamada recursiva al subdirectorio
                    # path_recursivo es el camino relativo que se envía al API
                    path_recursivo = item['path'] 
                    extraer_urls_m3u_de_github(owner, repo, branch, path_recursivo, urls_encontradas)
                    
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error al acceder a la API de GitHub ({api_url.split('?')[0]}...): {e}")
    except Exception as e:
         logging.error(f"❌ Error inesperado al procesar contenido de GitHub: {e}")


def recolectar_urls_desde_repositorio(repo_url: str) -> List[str]:
    """Función principal que inicia la extracción de URLs de GitHub."""
    print(f"\n--- 🌐 Analizando Repositorio GitHub: {repo_url} ---")
    try:
        owner, repo, branch, path = _url_to_api(repo_url)
        urls_encontradas = set()
        
        extraer_urls_m3u_de_github(owner, repo, branch, path, urls_encontradas)
        
        urls_final = list(urls_encontradas)
        print(f"✅ Se encontraron {len(urls_final)} enlaces M3U en el repositorio.")
        return urls_final
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error crítico al iniciar la recolección de GitHub: {e}")
        return []

# =========================================================================================
# ⚙️ FLUJO DE CONTROL PRINCIPAL
# =========================================================================================

def ejecutar_proceso_completo(urls: List[str]):
    """Ejecuta el flujo completo para una lista de URLs."""
    rutas_temp = [] 
    print("\n--- 🚀 Iniciando Flujo de Beluga (FASE 1, 2 y 3) ---")

    # 0. COMPILAR INVENTARIO EXISTENTE (FASE 0)
    inventario_existente = compilar_inventario_existente(MAX_SERVIDORES_BUSCAR)
    
    # 1. Obtener todas las listas nuevas (Temporales)
    for i, url in enumerate(urls):
        ruta_temp = os.path.join(CARPETA_SALIDA, f"TEMP_MATERIAL_{i+1:02d}.m3u")
        print(f"\n🔗 Recolectando lista {i+1} de {len(urls)} desde: {url}")
        
        # Se asume que auxiliar.descargar_lista existe y es funcional
        if descargar_lista(url, ruta_temp):
            logging.info(f"✅ Lista {i+1} guardada temporalmente en: {ruta_temp}")
            rutas_temp.append(ruta_temp)
        else:
            logging.error(f"❌ Falló la descarga de la lista {i+1}. Omitiendo.")

    if not rutas_temp:
        print("ERROR: No se pudo descargar ninguna lista válida. Saliendo.")
        return

    try:
        # 2. CLASIFICACIÓN, FUSIÓN Y CONSOLIDACIÓN (FASE 1 - Quick Audit)
        print("\n--- 🧠 Clasificando, Fusionando y Consolidando Inventario (FASE 1 - Rápida) ---")
        clasificar_enlaces(rutas_temp, inventario_existente) 
        print("✅ Consolidación y Quick Audit finalizada. Archivo de resumen listo para Auditoría Lenta.")

        # 3. AUDITORÍA LENTA (FASE 2 - Streamlink)
        print("\n--- 🐌 Iniciando Auditoría Lenta (FASE 2 - Streamlink) ---")
        auditar_conectividad()
        print("✅ Auditoría Lenta completada. Archivo de resumen finalizado.")
        
        # 4. BALANCEO ESTRATÉGICO Y EXCLUSIÓN (FASE 3)
        print("\n--- ⚖️ Iniciando Balanceo Estratégico (FASE 3) ---")
        auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
            
    except Exception as e:
        print(f"\nERROR CRÍTICO durante el proceso: {e}")
    finally:
        for ruta in rutas_temp:
            limpiar_archivos_temporales(ruta) 
        print("\n--- ✅ Proceso Completo Finalizado ---")
        
# =========================================================================================
# 🚀 PUNTO DE ENTRADA
# =========================================================================================

if __name__ == "__main__":
    
    print("--- 🚀 Iniciando Flujo de Beluga (FASE 1, 2 y 3) ---")
    
    # 1. Solicitar URL del Repositorio/Directorio
    repo_url = input("🔗 Ingresa la URL COMPLETA del repositorio/directorio de GitHub para analizar: ").strip()

    if not repo_url:
        print("ERROR: URL no ingresada. Saliendo.")
        sys.exit(0)
    
    # 2. Extraer las URLs M3U del repositorio
    urls_fuente = recolectar_urls_desde_repositorio(repo_url)

    if not urls_fuente:
        print("ERROR: No se encontraron URLs M3U válidas en el repositorio. Saliendo.")
        sys.exit(0)
    
    # 3. Ejecutar el proceso completo
    ejecutar_proceso_completo(urls_fuente)