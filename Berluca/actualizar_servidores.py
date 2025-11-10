# actualizar_servidores.py (Auditoría Rápida Multihilo)
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
RUTA_PRE_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Pre_Auditoria.m3u")
TIMEOUT_RAPIDO = 3 # <<-- Timeout agresivo para la prueba HEAD
MAX_THREADS = 50   # Máximo de peticiones simultáneas

def verificar_conectividad_rapida(url: str) -> str:
    """Verifica la accesibilidad HTTP de la URL con requests.head."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT_RAPIDO)
        if 200 <= r.status_code < 400:
            return "dudoso" 
        return "fallido"
    except requests.exceptions.RequestException:
        return "fallido"


def generar_pre_auditoria_rapida() -> Dict[str, str]:
    """
    Ejecuta la auditoría rápida en paralelo (multihilo) y genera el archivo 
    RP_Pre_Auditoria.m3u, mostrando una barra de progreso.
    """
    print("--- 🚀 Ejecutando Auditoría Rápida Multihilo (requests.head) ---")
    
    # 1. Recopilar todos los canales únicos a auditar
    canales_a_auditar = []
    
    for i in range(1, MAX_SERVIDORES_BUSCAR + 100): 
        ruta_servidor = obtener_servidor_path(i)
        if os.path.exists(ruta_servidor):
            inventario = obtener_inventario_servidor(i)
            for _, canales in inventario.items():
                for canal in canales:
                    # Usar la URL como clave única para deduplicar
                    if not any(c['url'] == canal['url'] for c in canales_a_auditar):
                        canales_a_auditar.append(canal)

    canales_totales = len(canales_a_auditar)
    estados_auditados = {}
    bloques_pre_auditados = []

    if canales_totales == 0:
        print("❌ No se encontraron canales para auditar.")
        return {}
        
    # 2. Ejecutar la auditoría en paralelo
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        resultados_futures = {
            executor.submit(verificar_conectividad_rapida, canal['url']): canal 
            for canal in canales_a_auditar
        }

        with tqdm(total=canales_totales, desc="Filtro Rápido", unit="canales") as pbar:
            for future in resultados_futures:
                canal = resultados_futures[future]
                url = canal['url']
                
                try:
                    estado_rapido = future.result() 
                except Exception as exc:
                    logging.debug(f"Error al auditar {url}: {exc}")
                    estado_rapido = "fallido" 

                # 3. Almacenar el resultado y preparar el bloque
                estados_auditados[url] = estado_rapido
                
                extinf_original = canal['bloque'][0].strip()
                # Limpiar cualquier estado anterior y añadir el nuevo
                extinf_nuevo = re.sub(r'#ESTADO_AUDITORIA:\w+', '', extinf_original)
                extinf_final = f"{extinf_nuevo} #ESTADO_AUDITORIA:{estado_rapido}"
                
                # Reconstruir el bloque para el archivo RP_Pre_Auditoria.m3u
                bloque_nuevo = [extinf_final] + [l for l in canal['bloque'][1:-1] if not l.startswith("#ESTADO:")] + [url]
                bloques_pre_auditados.append(bloque_nuevo)
                
                pbar.update(1)

    # 4. GUARDAR EL ARCHIVO RP_Pre_Auditoria.m3u
    print(f"\n--- 💾 Guardando archivo de Pre-Auditoría: {RUTA_PRE_AUDITORIA} ---")
    with open(RUTA_PRE_AUDITORIA, "w", encoding="utf-8", errors="ignore") as f:
        f.write("#EXTM3U\n")
        for bloque in bloques_pre_auditados:
            f.write("\n")
            f.writelines([linea.strip() + "\n" for linea in bloque])
            
    return estados_auditados


def cargar_estados_auditados() -> Dict[str, str]:
    """Carga los estados finales de la auditoría lenta o del resumen rápido."""
    estados = {}
    
    # 1. Intentar cargar resultados de Auditoría Lenta (si existe)
    if os.path.exists(RUTA_RESUMEN_AUDITORIA):
        print(f"--- 📊 Cargando resultados de Auditoría Lenta: {RUTA_RESUMEN_AUDITORIA} ---")
        with open(RUTA_RESUMEN_AUDITORIA, "r", encoding="utf-8", errors="ignore") as f:
            bloques_auditados = extraer_bloques_m3u(f.readlines())
        
        for bloque in bloques_auditados:
            url = extraer_url(bloque)
            extinf_line = bloque[0]
            match = re.search(r'#ESTADO_AUDITORIA:(\w+)', extinf_line)
            if url and match:
                estados[url] = match.group(1)
        
        if estados:
            return estados
        
    # 2. Si no hay resumen final, generar la Pre-Auditoría Rápida
    return generar_pre_auditoria_rapida()


def actualizar_servidores_con_auditoria():
    """
    Actualiza el estado interno de los canales en los servidores usando los 
    resultados de la auditoría (lenta o rápida) y activa el balanceo.
    """
    print("--- 🔄 Iniciando Actualización y Reclasificación por Auditoría ---")
    
    # Cargar los estados (esto llama a generar_pre_auditoria_rapida si es necesario)
    estados_auditados = cargar_estados_auditados()
    
    if not estados_auditados:
        print("❌ No se pudieron cargar estados. Proceso cancelado.")
        return

    servidores_modificados = []
    
    # 1. Recorrer todos los servidores para aplicar el estado
    for i in range(1, MAX_SERVIDORES_BUSCAR + 100):
        ruta_servidor = obtener_servidor_path(i)
        
        if not os.path.exists(ruta_servidor):
            continue

        inventario = obtener_inventario_servidor(i)
        cambios_servidor = 0

        for categoria, canales in inventario.items():
            for canal in canales:
                url = canal['url']
                
                nuevo_estado = estados_auditados.get(url, canal['estado'])
                
                if nuevo_estado != canal['estado']:
                    
                    # 1. Actualizar el diccionario interno del canal
                    canal['estado'] = nuevo_estado
                    
                    # 2. Actualizar la línea #ESTADO: dentro del bloque (que ya está reconstruida por obtener_inventario_servidor)
                    for idx, linea in enumerate(canal['bloque']):
                         if linea.startswith("#ESTADO:"):
                             canal['bloque'][idx] = f"#ESTADO:{nuevo_estado}"
                             break
                    
                    # 3. Actualizar la prioridad interna 
                    canal['prioridad'] = PRIORIDAD_ESTADO.get(nuevo_estado, 0)
                    
                    cambios_servidor += 1
        
        # Guardar solo si hubo cambios de estado
        if cambios_servidor > 0:
            if guardar_inventario_servidor(i, inventario):
                servidores_modificados.append(i)


    # 2. Ejecutar la Auditoría y Balanceo Global (Reclasificación)
    # Esta función ahora manejará la distribución con límite de 30/cat y la limpieza de archivos vacíos.
    auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
    
    print("\n--- ✅ Proceso de Reclasificación por Auditoría Finalizado ---")

if __name__ == "__main__":
    actualizar_servidores_con_auditoria()