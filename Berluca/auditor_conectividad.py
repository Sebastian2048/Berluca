# auditor_conectividad.py
import os
import re
import requests
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List
import logging
from urllib.parse import urlparse

# 📦 Importaciones de configuración y auxiliares
try:
    from config import CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR, MAX_SERVIDORES_BUSCAR
    from auxiliar import (
        extraer_bloques_m3u, extraer_nombre_canal, extraer_url
    )
    from servidor import obtener_servidor_path # Para obtener rutas de servidor
except ImportError as e:
    logging.error(f"Error al importar módulos en auditor_conectividad.py: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DE AUDITORÍA (Basada en tu lógica) ---

# 🧠 Dominios confiables (simplificados)
DOMINIOS_CONFIABLES = [
    "pluto.tv", "akamaized.net", "googlevideo.com", "llnwd.net", "fastly.net",
    "cdn", "m3u8", "hls", "raw.githubusercontent.com", "dai.google.com"
]

# ⚠️ Indicadores de fuente dudosa
PATRONES_DUDOSOS = [
    r"http://(?!s)", r"https://(?:\d{1,3}\.){3}\d{1,3}", r"bit\.ly", 
    r"tinyurl\.com", r"redirect", r"token=", r"streamingvip", 
    r"iptvlinks", r"adult", r"xxx", r"test", r"demo"
]

TIMEOUT_CHECK = 8 # Timeout ampliado para el chequeo de conectividad real

# ---------------------------------------------------------------------------------

def es_fuente_abierta_y_confiable(url: str) -> bool:
    """Clasifica la URL como confiable por patrón."""
    url_lower = url.lower()
    return any(dominio in url_lower for dominio in DOMINIOS_CONFIABLES)

def es_fuente_dudosa_por_patron(url: str) -> bool:
    """Clasifica la URL como dudosa por patrón (ej. IP directa, acortador)."""
    return any(re.search(pat, url) for pat in PATRONES_DUDOSOS)


def verificar_conectividad_completa(url: str) -> str:
    """Verifica la conectividad real y clasifica la URL."""
    # 1. Chequeo por Patrón (Rápido)
    if es_fuente_dudosa_por_patron(url):
        return "dudoso" # Los patrones dudosos tienen menor confianza

    # 2. Chequeo de Conectividad (Lento)
    try:
        response = requests.get(url, timeout=TIMEOUT_CHECK, stream=True)
        status_code = response.status_code

        if 200 <= status_code < 400:
            # Si el estado es OK y es un dominio confiable, es Abierto
            if es_fuente_abierta_y_confiable(url):
                 return "abierto"
            else:
                 return "dudoso" # Éxito pero la fuente no es de patrón confiable
        
        elif status_code in [403, 401]:
            return "fallido" # 403 y 401 (Prohibido/No Autorizado)
        
        else:
            return "fallido"
            
    except requests.exceptions.RequestException:
        return "fallido"


def auditar_canales_servidores():
    """
    Recorre todos los servidores existentes, audita cada canal 
    y consolida los resultados en un archivo de auditoría.
    """
    print("\n--- 🌐 Iniciando Auditoría Completa de Conectividad (Lento) ---")
    
    resultados_agrupados = {
        "abierto": [],
        "dudoso": [],
        "fallido": []
    }
    total_canales_auditados = 0
    total_bloques_servidores = 0
    
    # 1. Recorrer todos los servidores generados
    archivos_servidores = []
    for i in range(1, MAX_SERVIDORES_BUSCAR + 10):
        ruta = obtener_servidor_path(i)
        if os.path.exists(ruta):
            archivos_servidores.append(ruta)
        elif len(archivos_servidores) > 0 and i > MAX_SERVIDORES_BUSCAR:
            # Parar si ya encontramos servidores y llegamos al final lógico
            break
    
    if not archivos_servidores:
        print("❌ No se encontraron archivos de servidor para auditar.")
        return

    # 2. Procesar bloques de todos los archivos
    for ruta_servidor in archivos_servidores:
        with open(ruta_servidor, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
            bloques = extraer_bloques_m3u(lineas)
            total_bloques_servidores += len(bloques)
            
            # 3. Auditar cada bloque con barra de progreso
            print(f"Auditoría: {os.path.basename(ruta_servidor)} - {len(bloques)} canales.")
            for bloque in tqdm(bloques, desc=f"Chequeando conectividad", unit="canal"):
                
                extinf = bloque[0]
                url = bloque[-1]
                nombre = extraer_nombre_canal(bloque)
                
                if not url or url.startswith('#'): continue
                
                estado = verificar_conectividad_completa(url)
                
                # Reconstruir el bloque para el archivo de resumen
                bloque_auditoria = f"{extinf} #ESTADO_AUDITORIA:{estado}\n{url}"
                
                resultados_agrupados[estado].append(bloque_auditoria)
                total_canales_auditados += 1

    # 4. Generar el archivo de resumen
    ruta_resumen = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")
    guardar_resumen_auditoria(ruta_resumen, resultados_agrupados)
    
    print(f"\n✅ Auditoría completa finalizada. Canales auditados: {total_canales_auditados}")
    print(f"   -> Abiertos: {len(resultados_agrupados['abierto'])}")
    print(f"   -> Dudosos: {len(resultados_agrupados['dudoso'])}")
    print(f"   -> Fallidos: {len(resultados_agrupados['fallido'])}")


def guardar_resumen_auditoria(ruta: str, resultados: Dict[str, List[str]]):
    """Guarda el resumen consolidado de la auditoría."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Auditoría de Conectividad - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # Escribir Abiertos
        f.write("\n# ====== ★ ABIERTOS Y CONFIABLES ★ ======\n\n")
        for bloque in resultados['abierto']:
            f.write(bloque + "\n\n")
            
        # Escribir Dudosos
        f.write("\n# ====== ★ DUDOSOS / PATRÓN NO CONFIABLE ★ ======\n\n")
        for bloque in resultados['dudoso']:
            f.write(bloque + "\n\n")
            
        # Escribir Fallidos
        f.write("\n# ====== ★ FALLIDOS / NO CONECTAN (4XX/5XX) ★ ======\n\n")
        for bloque in resultados['fallido']:
            f.write(bloque + "\n\n")

    print(f"\n✅ Resumen de Auditoría generado: {ruta}")


# 🚀 Punto de entrada
if __name__ == "__main__":
    auditar_canales_servidores()