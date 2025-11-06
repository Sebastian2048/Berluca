# segmentador.py

import os
from typing import List

# Importaciones de módulos centrales
from config import CARPETA_ORIGEN, CARPETA_SEGMENTADOS, LIMITE_BLOQUES
from m3u_core import extraer_bloques_m3u
from file_manager import leer_archivo_m3u, guardar_segmentado, limpiar_carpeta

# =========================================================================================
# ✂️ FUNCIONES DE SEGMENTACIÓN
# =========================================================================================

def segmentar_archivo_categoria(nombre_categoria: str) -> bool:
    """
    Lee un archivo de categoría grande, lo divide en segmentos más pequeños
    y los guarda en CARPETA_SEGMENTADOS.
    Retorna True si ocurrió la segmentación, False si no fue necesaria.
    """
    ruta_origen = os.path.join(CARPETA_ORIGEN, f"{nombre_categoria}.m3u")

    if not os.path.exists(ruta_origen):
        print(f"⚠️ Archivo no encontrado para segmentar: {ruta_origen}")
        return False

    # 1. Leer y extraer bloques
    lineas = leer_archivo_m3u(ruta_origen)
    bloques = extraer_bloques_m3u(lineas)

    if len(bloques) <= LIMITE_BLOQUES:
        # Si el archivo es pequeño, no es necesario segmentar
        return False

    print(f"✂️ Segmentando {nombre_categoria} ({len(bloques)} bloques)...")

    segmentos_escritos = 0
    contador_bloques = 0
    segmento_actual = []

    # 2. Iterar y guardar en lotes
    for bloque in bloques:
        segmento_actual.append(bloque)
        contador_bloques += 1

        if contador_bloques >= LIMITE_BLOQUES:
            # 3. Guardar el segmento completo (I/O delegado a file_manager)
            guardar_segmentado(nombre_categoria, segmento_actual, segmentos_escritos + 1)
            segmentos_escritos += 1
            contador_bloques = 0
            segmento_actual = []

    # 4. Guardar el segmento sobrante (el último)
    if segmento_actual:
        guardar_segmentado(nombre_categoria, segmento_actual, segmentos_escritos + 1)
        segmentos_escritos += 1

    print(f"✅ {nombre_categoria} segmentado en {segmentos_escritos} archivos.")
    return True

def segmentar_todas_las_categorias() -> List[str]:
    """
    Segmenta todos los archivos .m3u encontrados en CARPETA_ORIGEN que superen LIMITE_BLOQUES.
    """
    # 1. Aseguramos la limpieza de la carpeta de segmentos antes de iniciar
    limpiar_carpeta(CARPETA_SEGMENTADOS, extension=".m3u")

    # 2. Buscar archivos de categoría clasificados
    try:
        archivos_en_origen = [f for f in os.listdir(CARPETA_ORIGEN) if f.endswith(".m3u")]
    except FileNotFoundError:
        print(f"⚠️ La carpeta de origen {CARPETA_ORIGEN} no existe o está vacía.")
        return []

    categorias_segmentadas = []

    if not archivos_en_origen:
        print("ℹ️ No hay archivos de categoría para segmentar.")
        return []

    print("\n--- INICIO DE SEGMENTACIÓN ---")

    for archivo in archivos_en_origen:
        nombre_categoria = archivo.replace(".m3u", "")
        if segmentar_archivo_categoria(nombre_categoria):
            categorias_segmentadas.append(nombre_categoria)

    print("--- FIN DE SEGMENTACIÓN ---")
    return categorias_segmentadas

# =========================================================================================
# 🧪 MÓDULO DE PRUEBA
# =========================================================================================
if __name__ == "__main__":
    print("Módulo segmentador listo. Debe ser invocado por generador.py.")