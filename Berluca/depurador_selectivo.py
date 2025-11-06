# depurador_selectivo.py

from typing import List, Tuple, Set

# Importaciones de módulos centrales
from config import contiene_exclusion, EXCLUSIONES
from m3u_core import sanear_bloque_m3u, extraer_nombre_canal, hash_bloque

# =========================================================================================
# 🗑️ DEPURACIÓN Y EXCLUSIÓN
# =========================================================================================

def depurar_lista_de_bloques(
    bloques_crudos: List[List[str]], 
    hashes_excluidos: Set[str] = None
) -> Tuple[List[List[str]], int]:
    """
    Procesa una lista de bloques M3U, aplicando saneamiento, exclusiones por nombre 
    y deduplicación por hash.
    
    Retorna: (Lista de bloques limpios, Contador de bloques excluidos)
    """
    bloques_finales: List[List[str]] = []
    excluidos_count = 0
    hashes_vistos: Set[str] = hashes_excluidos if hashes_excluidos is not None else set()

    for bloque_crudo in bloques_crudos:
        # 1. Saneamiento inicial
        bloque_saneado = sanear_bloque_m3u(bloque_crudo)
        if not bloque_saneado:
            excluidos_count += 1
            continue

        nombre_canal = extraer_nombre_canal(bloque_saneado)

        # 2. Exclusión por palabras clave (config.py)
        if contiene_exclusion(nombre_canal):
            excluidos_count += 1
            continue
            
        # 3. Deduplicación por hash
        h = hash_bloque(bloque_saneado)
        if h in hashes_vistos:
            excluidos_count += 1
            continue

        # Si pasa todas las validaciones
        hashes_vistos.add(h)
        bloques_finales.append(bloque_saneado)
        
    return bloques_finales, excluidos_count

def eliminar_bloques_rotos(bloques: List[List[str]], hashes_rotos: Set[str]) -> List[List[str]]:
    """
    Filtra los bloques de una lista basándose en un set de hashes de canales rotos 
    proporcionados por el verificador.
    """
    if not hashes_rotos:
        return bloques # No hay nada que filtrar

    bloques_limpios = []
    for bloque in bloques:
        # Asume que el bloque ya está saneado en este punto
        h = hash_bloque(bloque)
        if h not in hashes_rotos:
            bloques_limpios.append(bloque)
            
    return bloques_limpios

# NOTA: La lógica de depuración de Movian (que era un simple os.remove) se mantiene 
# en file_manager.py ya que es una operación de I/O simple.