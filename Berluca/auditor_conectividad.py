# auditor_conectividad.py
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
RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u") 

COMANDO_PRUEBA_LENTA = ['streamlink', '--json', '--stream-url', '--loglevel', 'none']
TIMEOUT_LENTO = 25  
MAX_THREADS_LENTO = 15 

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
        logging.error("❌ ERROR CRÍTICO: La herramienta 'streamlink' no se encuentra.")
        return False
    except Exception:
        return False


def auditar_conectividad():
    """
    Función principal que lee el Resumen, ejecuta la prueba LENTA SOLO sobre los 'dudoso' 
    y reescribe el resumen final.
    """
    # 1. Verificar y leer el archivo de Resumen generado por la Fase 1
    if not os.path.exists(RUTA_RESUMEN_AUDITORIA):
        print(f"❌ Error: No se encontró el archivo de Resumen de Auditoría: {RUTA_RESUMEN_AUDITORIA}")
        print("Ejecuta la Fase 1 (Clasificación/Quick Audit) primero.")
        return

    print("--- 🐢 Iniciando Auditoría LENTA Multihilo (Prueba de Reproducción REAL) ---")

    with open(RUTA_RESUMEN_AUDITORIA, "r", encoding="utf-8", errors="ignore") as f:
        bloques_auditados_fase1 = extraer_bloques_m3u(f.readlines())
        
    canales_a_probar = []
    inventario_completo = []
    
    # 2. Identificar y recolectar solo los canales 'dudoso'
    for bloque in bloques_auditados_fase1:
        # El estado viene en la segunda línea del bloque: ['#EXTINF...', '#ESTADO:dudoso', 'URL']
        estado_previo = "desconocido"
        if len(bloque) > 1 and bloque[1].startswith("#ESTADO:"):
            estado_previo = bloque[1].split(':')[1].strip().lower()
        
        canal_data = {
            'bloque': bloque,
            'url': extraer_url(bloque),
            'nombre': extraer_nombre_canal(bloque),
            'estado_previo': estado_previo
        }
        inventario_completo.append(canal_data)
        
        if estado_previo == "dudoso":
            canales_a_probar.append(canal_data)
        
    canales_totales = len(canales_a_probar)
    
    print(f"✅ Canales dudosos detectados: {canales_totales}. Iniciando pruebas paralelas...")

    # 3. Ejecutar la auditoría en paralelo (solo en los 'dudosos')
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

                    estado_final = "abierto" if pasa_prueba else "fallido"
                    resultados_auditoria[url] = estado_final
                    
                    pbar.update(1)

    # 4. Consolidar todos los bloques y RE-ESCRIBIR EL RESUMEN
    resumen_final_bloques = []
    
    for canal in inventario_completo:
        url = canal['url']
        estado_previo = canal['estado_previo']
        bloque_original = canal['bloque']
        
        estado_final_streamlink = resultados_auditoria.get(url)
        
        if estado_final_streamlink is None:
            estado_final = estado_previo
        else:
            estado_final = estado_final_streamlink
        
        # Reconstruir el bloque con el estado final (reemplazando la línea #ESTADO)
        bloque_modificado = []
        
        for linea in bloque_original:
            if linea.startswith("#ESTADO:"):
                # Reemplazamos el estado por el estado final de Streamlink
                bloque_modificado.append(f"#ESTADO:{estado_final}")
            else:
                bloque_modificado.append(linea)
            
        resumen_final_bloques.append(bloque_modificado)


    # 5. Escribir el Resumen de Auditoría Final (sobre RP_Resumen_Auditoria.m3u)
    print(f"\n--- 💾 Escribiendo Resumen de Auditoría Final: {RUTA_RESUMEN_AUDITORIA} ---")
    
    with open(RUTA_RESUMEN_AUDITORIA, "w", encoding="utf-8", errors="ignore") as f:
        f.write("#EXTM3U\n")
        
        for bloque in resumen_final_bloques:
            f.write("\n")
            f.writelines([linea.strip() + "\n" for linea in bloque])

    print("--- ✅ Proceso de Auditoría Lenta Finalizado ---")


if __name__ == "__main__":
    auditar_conectividad()