# actualizar_servidores.py 
import os
import re
import logging
import requests
from typing import Dict, List, Any
from tqdm import tqdm 
from concurrent.futures import ThreadPoolExecutor 

# 📦 Importaciones de módulos locales
try:
    from config import CARPETA_SALIDA, MAX_SERVIDORES_BUSCAR, PRIORIDAD_ESTADO
    from auxiliar import extraer_bloques_m3u, extraer_url, extraer_nombre_canal
    from servidor import (
        obtener_servidor_path, guardar_inventario_servidor, 
        obtener_inventario_servidor, auditar_y_balancear_servidores
    )
except ImportError as e:
    logging.error(f"Error al importar módulos en actualizar_servidores.py: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DE AUDITORÍA RÁPIDA ---
RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")
TIMEOUT_RAPIDO = 3 
MAX_THREADS = 50   

def verificar_conectividad_head(url: str) -> str:
    """Intenta una petición HEAD o GET rápida para determinar el estado (abierto/fallido/dudoso)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, timeout=TIMEOUT_RAPIDO, headers=headers, allow_redirects=True)
        response.raise_for_status() # Lanza excepción para 4xx/5xx

        if response.status_code in (200, 301, 302, 303, 307, 308):
            return 'abierto'
        else:
            return 'fallido' 
            
    except requests.exceptions.HTTPError:
        return 'fallido'
    except requests.exceptions.RequestException:
        return 'dudoso' 
    except Exception:
        return 'dudoso'


def actualizar_servidores_con_auditoria(ruta_inventario_auditado: str):
    """
    Lee el inventario auditado (resumen de clasificador.py), 
    actualiza el estado de los canales en los servidores existentes y re-balancea.
    """
    
    if not os.path.exists(ruta_inventario_auditado):
        print(f"⚠️ Archivo de inventario auditado no encontrado: {ruta_inventario_auditado}. Abortando actualización.")
        return

    # 1. Cargar el mapa URL -> Estado auditado
    estados_auditados = {}
    try:
        with open(ruta_inventario_auditado, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
            
        bloques = extraer_bloques_m3u(lineas)
        for bloque in bloques:
            url = extraer_url(bloque)
            if not url:
                continue
            
            # Buscar el estado en el bloque (formato #ESTADO:estado)
            estado_line = next((l for l in bloque if l.startswith("#ESTADO:")), None)
            if estado_line:
                estado = estado_line.split(':')[1].strip().lower()
                estados_auditados[url] = estado
            # else: Si no tiene estado, se ignorará y usará el que tiene en el servidor existente.

        print(f"✅ Estados de {len(estados_auditados)} canales cargados del Quick Audit.")

    except Exception as e:
        logging.error(f"Error al cargar estados auditados: {e}")
        return

    # 2. Actualizar el estado de los canales en los archivos de servidor existentes (RP_Servidor_XX.m3u)
    servidores_modificados = []

    for i in range(1, MAX_SERVIDORES_BUSCAR + 1):
        path = obtener_servidor_path(i)
        if not os.path.exists(path):
            continue
        
        # obtener_inventario_servidor debe devolver una lista de diccionarios 
        # con 'bloque' (List[str]), 'url', 'estado' y 'categoria'.
        inventario = obtener_inventario_servidor(i) 
        cambios_servidor = 0
        
        for categoria, canales in inventario.items():
            for canal in canales:
                url = canal['url']
                
                # Obtener el nuevo estado auditado o mantener el existente (si fue excluido del quick audit)
                nuevo_estado = estados_auditados.get(url, canal.get('estado', 'desconocido'))
                
                if nuevo_estado != canal.get('estado', 'desconocido'):
                    
                    # 1. Actualizar el diccionario interno del canal
                    canal['estado'] = nuevo_estado
                    
                    # 2. Actualizar la línea #ESTADO: dentro del bloque M3U
                    
                    linea_encontrada = False
                    
                    # R1: Buscar y actualizar si ya existe (el más común)
                    for idx, linea in enumerate(canal['bloque']):
                         if linea.startswith("#ESTADO:"):
                             canal['bloque'][idx] = f"#ESTADO:{nuevo_estado}"
                             linea_encontrada = True
                             break
                    
                    # R2: Si la línea #ESTADO: no existía, añadirla antes de la URL
                    if not linea_encontrada:
                         # La URL siempre es la última línea
                         canal['bloque'].insert(len(canal['bloque']) - 1, f"#ESTADO:{nuevo_estado}")
                    
                    # 3. Actualizar la prioridad interna para el re-balanceo
                    canal['prioridad'] = PRIORIDAD_ESTADO.get(nuevo_estado, 0)
                    
                    cambios_servidor += 1
        
        # Guardar solo si hubo cambios de estado
        if cambios_servidor > 0:
            if guardar_inventario_servidor(i, inventario):
                servidores_modificados.append(i)

    # 3. Ejecutar la Auditoría y Balanceo Global (Reclasificación)
    # Esta función leerá los archivos de servidor ACTUALIZADOS, ordenará por 
    # prioridad (abierto > dudoso > fallido) y distribuirá según los límites (800/30).
    print("\n--- ⚖️ Iniciando Re-Balanceo Estratégico (Prioridad) ---")
    auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
    
    print("\n--- ✅ Proceso de Reclasificación por Auditoría Finalizado ---")

if __name__ == "__main__":
    # Si se desea probar directamente, usar una ruta de archivo de resumen de prueba.
    # actualizar_servidores_con_auditoria(RUTA_RESUMEN_AUDITORIA)
    pass