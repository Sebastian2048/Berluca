# auditor_conectividad.py (Auditoría Lenta Multihilo)
import os
import re
import logging
import subprocess
from typing import Dict, List, Any
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor 

# 📦 Importaciones de módulos locales
try:
    from config import CARPETA_SALIDA, LOGO_DEFAULT
    from auxiliar import extraer_bloques_m3u, extraer_url, extraer_nombre_canal
except ImportError as e:
    logging.error(f"Error al importar módulos en auditor_conectividad.py: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN MULTIHILO Y STREAMLINK ---
RUTA_PRE_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Pre_Auditoria.m3u")
RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")

COMANDO_PRUEBA_LENTA = ['streamlink', '--json', '--stream-url', '--loglevel', 'none']
TIMEOUT_LENTO = 25  
MAX_THREADS_LENTO = 15 # Hilos para pruebas Streamlink (ajusta según tu CPU/Red)

def realizar_prueba_reproduccion_real(url: str) -> bool:
    """
    Intenta resolver la URL de streaming usando Streamlink.
    """
    try:
        resultado = subprocess.run(
            COMANDO_PRUEBA_LENTA + [url, 'best'], 
            timeout=TIMEOUT_LENTO, 
            capture_output=True, 
            check=False 
        )
        
        if resultado.returncode == 0 and "http" in resultado.stdout.decode():
             return True
        else:
             return False

    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        # Esto debería haberse manejado antes, pero es una buena seguridad.
        logging.error("❌ ERROR CRÍTICO: La herramienta 'streamlink' no se encuentra.")
        return False
    except Exception:
        return False


def auditar_conectividad():
    """
    Ejecuta la prueba de auditoría LENTA SOLO sobre los canales marcados como 'dudoso' 
    en el archivo de pre-auditoría, usando multithreading.
    """
    if not os.path.exists(RUTA_PRE_AUDITORIA):
        print(f"❌ Error: No se encontró el archivo de Pre-Auditoría: {RUTA_PRE_AUDITORIA}")
        print("Ejecuta 'actualizar_servidores.py' primero para generar la pre-auditoría rápida.")
        return

    print("--- 🐢 Iniciando Auditoría LENTA Multihilo (Prueba de Reproducción REAL) ---")

    with open(RUTA_PRE_AUDITORIA, "r", encoding="utf-8", errors="ignore") as f:
        bloques_pre_auditados = extraer_bloques_m3u(f.readlines())
        
    canales_a_probar = []
    
    # 1. Identificar y recolectar solo los canales 'dudoso'
    for bloque in bloques_pre_auditados:
        extinf_line = bloque[0]
        match = re.search(r'#ESTADO_AUDITORIA:(\w+)', extinf_line)
        estado_previo = match.group(1) if match else "desconocido"
        
        if estado_previo == "dudoso":
            canales_a_probar.append({
                'bloque': bloque,
                'url': extraer_url(bloque),
                'nombre': extraer_nombre_canal(bloque)
            })

    canales_totales = len(canales_a_probar)
    resumen_final_bloques = []
    
    print(f"✅ Canales dudosos detectados: {canales_totales}. Iniciando pruebas paralelas...")

    # 2. Ejecutar la auditoría en paralelo (solo en los 'dudosos')
    resultados_auditoria = {}
    
    if canales_totales > 0:
        with ThreadPoolExecutor(max_workers=MAX_THREADS_LENTO) as executor:
            resultados_futures = {
                executor.submit(realizar_prueba_reproduccion_real, canal['url']): canal
                for canal in canales_a_probar
            }
            
            with tqdm(total=canales_totales, desc="Prueba de Streamlink", unit="canales") as pbar:
                for future in resultados_futures:
                    canal = resultados_futures[future]
                    url = canal['url']
                    
                    try:
                        pasa_prueba = future.result() 
                    except Exception as exc:
                        logging.debug(f"Error en hilo de auditoría para {url}: {exc}")
                        pasa_prueba = False 

                    estado_final = "abierto" if pasa_prueba else "dudoso"
                    resultados_auditoria[url] = estado_final
                    
                    pbar.update(1)

    # 3. Consolidar todos los bloques
    for bloque in bloques_pre_auditados:
        url = extraer_url(bloque)
        nombre = extraer_nombre_canal(bloque)
        
        estado_final = resultados_auditoria.get(url)
        
        if estado_final is None:
            # Si no se probó (no era dudoso), mantener su estado previo (fallido o desconocido)
            match = re.search(r'#ESTADO_AUDITORIA:(\w+)', bloque[0])
            estado_final = match.group(1) if match else "desconocido"

        # Reconstruir el bloque para el resumen final (solo #EXTINF y la URL)
        extinf_base = f'#EXTINF:-1 tvg-logo="{LOGO_DEFAULT}",{nombre.strip()}'
        extinf_final = f"{extinf_base} #ESTADO_AUDITORIA:{estado_final}"

        # Filtrar las líneas internas de estado
        bloque_base = [l for l in bloque if not l.startswith("#ESTADO_AUDITORIA:")]
        
        bloque_final = [extinf_final] + bloque_base[1:-1] + [url]
        resumen_final_bloques.append(bloque_final)


    # 4. Escribir el Resumen de Auditoría Final
    print(f"\n--- 💾 Escribiendo Resumen de Auditoría Final: {RUTA_RESUMEN_AUDITORIA} ---")
    
    with open(RUTA_RESUMEN_AUDITORIA, "w", encoding="utf-8", errors="ignore") as f:
        f.write("#EXTM3U\n")
        
        for bloque in resumen_final_bloques:
            f.write("\n")
            f.writelines([linea.strip() + "\n" for linea in bloque])

    print("--- ✅ Proceso de Auditoría Lenta Finalizado ---")
    print("   Ejecuta 'actualizar_servidores.py' para aplicar estos estados y balancear.")


if __name__ == "__main__":
    auditar_conectividad()