# verificador.py

import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Tuple

# Importaciones de módulos centrales
from m3u_core import extraer_bloques_m3u, extraer_url, sanear_bloque_m3u, hash_bloque
from file_manager import leer_archivo_m3u
from utils import verificar_disponibilidad # Función optimizada en utils.py
from config import CARPETA_ORIGEN # Para buscar archivos

# =========================================================================================
# 🔗 FUNCIONES DE VERIFICACIÓN CONCURRENTE
# =========================================================================================

def verificar_url(url: str, hash_bloque: str) -> Tuple[str, bool]:
    """
    Verifica la disponibilidad de una única URL.
    Retorna: (hash_bloque, True si disponible, False si roto)
    """
    return hash_bloque, verificar_disponibilidad(url)

def verificar_enlaces_en_archivos(archivos_a_verificar: List[str], max_workers: int = 10, muestra_por_archivo: int = 50) -> Set[str]:
    """
    Escanea archivos .m3u, verifica una muestra de sus enlaces de forma concurrente,
    y devuelve un set de HASHES de los bloques ROTOS.
    """
    hashes_a_verificar: List[Tuple[str, str]] = [] # Lista de (URL, Hash)

    print("\n🔎 Recopilando enlaces para verificación...")
    
    # 1. Recopilar URLs y Hashes
    for archivo_ruta in archivos_a_verificar:
        if not os.path.exists(archivo_ruta):
            continue
            
        lineas = leer_archivo_m3u(archivo_ruta)
        bloques = extraer_bloques_m3u(lineas)
        
        # Filtrar solo una muestra aleatoria si el archivo es grande
        if len(bloques) > muestra_por_archivo:
            bloques_muestra = random.sample(bloques, muestra_por_archivo)
        else:
            bloques_muestra = bloques
            
        for bloque in bloques_muestra:
            bloque_saneado = sanear_bloque_m3u(bloque)
            if bloque_saneado:
                url = extraer_url(bloque_saneado)
                h = hash_bloque(bloque_saneado)
                if url and h:
                    hashes_a_verificar.append((url, h))

    print(f"🔗 Total de enlaces únicos a verificar: {len(set(h for _, h in hashes_a_verificar))}")
    if not hashes_a_verificar:
        return set()

    # 2. Ejecutar verificación concurrente
    hashes_rotos: Set[str] = set()
    
    print(f"⏱️ Iniciando verificación concurrente con {max_workers} hilos...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_hash = {
            executor.submit(verificar_url, url, h): h 
            for url, h in hashes_a_verificar
        }
        
        for i, future in enumerate(as_completed(future_to_hash)):
            h, disponible = future.result()
            
            # 3. Registrar los rotos
            if not disponible:
                hashes_rotos.add(h)
                
            # Opcional: Mostrar progreso cada N iteraciones
            if (i + 1) % 50 == 0:
                print(f"   -> Progreso: {i + 1}/{len(hashes_a_verificar)} verificados. Rotos: {len(hashes_rotos)}")

    print(f"✅ Verificación finalizada. {len(hashes_rotos)} enlaces rotos detectados en la muestra.")
    return hashes_rotos

# NOTA: En generador.py, invocaremos esto con la lista de archivos en CARPETA_ORIGEN.