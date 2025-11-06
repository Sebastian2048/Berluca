# reclasificador.py

import os
from typing import List, Tuple

# Importaciones de módulos centrales
from config import CARPETA_ORIGEN, LIMITE_BLOQUES
from m3u_core import extraer_bloques_m3u, sanear_bloque_m3u
from file_manager import leer_archivo_m3u, guardar_en_categoria, limpiar_carpeta
from clasificador import clasificacion_doble # Usar la lógica de clasificación principal


# =========================================================================================
# 🔄 FUNCIONES DE RECLASIFICACIÓN
# =========================================================================================

def reclasificar_categoria(categoria_origen: str, categorias_destino: List[str]) -> int:
    """
    Lee una categoría de origen (ej: sin_clasificar) e intenta reclasificar sus bloques.
    
    Retorna: El número de bloques reubicados.
    """
    ruta_origen = os.path.join(CARPETA_ORIGEN, f"{categoria_origen}.m3u")
    
    if not os.path.exists(ruta_origen):
        return 0

    print(f"🔄 Reclasificando bloques de: {categoria_origen}...")

    lineas = leer_archivo_m3u(ruta_origen)
    bloques_crudos = extraer_bloques_m3u(lineas)
    bloques_no_reubicados: List[List[str]] = []
    reubicados_count = 0

    for bloque_crudo in bloques_crudos:
        bloque_saneado = sanear_bloque_m3u(bloque_crudo)
        if not bloque_saneado:
            continue
            
        # Reaplicar la clasificación doble
        nueva_categoria = clasificacion_doble(bloque_saneado)
        
        # 1. Verificar si la reclasificación fue exitosa (no sigue en el origen)
        if nueva_categoria != categoria_origen and nueva_categoria not in categorias_destino:
            # 2. Guardar en la nueva categoría (delegado a file_manager)
            guardar_en_categoria(nueva_categoria, bloque_saneado)
            reubicados_count += 1
        else:
            # 3. Mantener el bloque en la categoría original si no se pudo reubicar
            bloques_no_reubicados.append(bloque_saneado)

    # 4. Sobreescribir el archivo de origen solo con los bloques no reubicados
    if reubicados_count > 0:
        # La sobreescritura es I/O y debe ser cuidadosa.
        ruta = os.path.join(CARPETA_ORIGEN, f"{categoria_origen}.m3u")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# Bloques no reubicados de {categoria_origen}\n")
            for bloque in bloques_no_reubicados:
                f.write("\n".join(bloque).strip() + "\n\n")

    return reubicados_count

def reclasificar_todos_los_restantes() -> int:
    """
    Función principal para reclasificar bloques que quedaron en categorías temporales.
    """
    categorias_a_reclasificar = [
        "sin_clasificar", 
        "sin_clasificar_baja_calidad", 
        "sin_clasificar_limpieza"
    ]
    
    total_reubicados = 0
    
    for categoria in categorias_a_reclasificar:
        # Se intenta reclasificar a todas las categorías que no sean las de origen.
        categorias_destino = categorias_a_reclasificar 
        total_reubicados += reclasificar_categoria(categoria, categorias_destino)
        
    if total_reubicados > 0:
        print(f"✅ Reclasificación finalizada. Total reubicados: {total_reubicados}")
    else:
        print("ℹ️ Reclasificación finalizada. No se reubicaron bloques.")
        
    return total_reubicados