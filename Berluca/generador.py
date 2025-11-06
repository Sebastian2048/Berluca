# generador.py (ACTUALIZADO CON TODOS LOS MÓDULOS AVANZADOS)

import os
from collections import Counter
import glob
from typing import Dict, List, Set

# Importaciones de módulos centrales
from config import (
    CARPETA_SEGMENTADOS, CARPETA_ORIGEN, ARCHIVO_SALIDA, 
    TITULOS_VISUALES, LOGOS_CATEGORIA, LOGO_DEFAULT, LIMITE_BLOQUES
)
from m3u_core import extraer_bloques_m3u, extraer_nombre_canal, extraer_url, sanear_bloque_m3u, hash_bloque
from file_manager import limpiar_carpeta, verificar_archivos_movian, leer_archivo_m3u
from clasificador import clasificar_bloque_por_contenido 

# Importaciones de nuevos módulos avanzados
from segmentador import segmentar_todas_las_categorias # Segmentación
from reclasificador import reclasificar_todos_los_restantes # Reclasificación
from verificador import verificar_enlaces_en_archivos # Verificación de enlaces
from depurador_selectivo import eliminar_bloques_rotos, depurar_lista_de_bloques # Depuración
from auditor_visual import auditar_bloque_visual # Auditoría de metadatos
from verificar_compatibilidad_movian import adaptar_para_movian # Adaptación

# =========================================================================================
# 🎯 PROCESO DE CLASIFICACIÓN Y GENERACIÓN FINAL
# =========================================================================================

def clasificar_y_segmentar_archivos(archivo_temporal: str):
    """
    Lee la lista temporal, clasifica sus bloques y los escribe en CARPETA_ORIGEN.
    """
    print("\n🧠 Iniciando clasificación, saneamiento y depuración inicial...")
    
    lineas = leer_archivo_m3u(archivo_temporal)
    bloques_crudos = extraer_bloques_m3u(lineas)
    
    contador_clasificados = 0
    
    # 🛑 Usar depurador_selectivo.depurar_lista_de_bloques para el saneamiento inicial
    bloques_saneados, excluidos = depurar_lista_de_bloques(bloques_crudos)
    print(f"✅ Depuración inicial: {len(bloques_saneados)} bloques listos | {excluidos} excluidos.")

    # 💾 Clasificación y Escritura
    from file_manager import guardar_en_categoria # Importamos aquí para evitar importación circular
    
    for bloque_saneado in bloques_saneados:
        categoria = clasificar_bloque_por_contenido(bloque_saneado)
        guardar_en_categoria(categoria, bloque_saneado)
        contador_clasificados += 1

    print(f"✅ Clasificación inicial finalizada. {contador_clasificados} bloques procesados.")
    print(f"📁 Archivos clasificados por categoría en: {CARPETA_ORIGEN}/")
    
    # 1. RECLASIFICACIÓN (Mover 'sin_clasificar' a sus categorías reales si es posible)
    reclasificar_todos_los_restantes()
    
    # 2. SEGMENTACIÓN (Dividir las categorías grandes si superan el límite)
    categorias_segmentadas = segmentar_todas_las_categorias()
    
    return categorias_segmentadas


def generar_listas_finales(categorias_segmentadas: List[str]):
    """
    Compila todas las listas (segmentadas o clasificadas) en un único archivo final.
    """
    print("\n📦 Compilando lista final con auditoría y verificación...")
    
    # Directorios a escanear: Segmentados si se usaron, sino Origen.
    # Si la lista fue segmentada, solo usamos la carpeta segmentada.
    if categorias_segmentadas:
        print("💡 Usando archivos de CARPETA_SEGMENTADOS para la compilación.")
        carpetas_a_escanear = [CARPETA_SEGMENTADOS]
    else:
        carpetas_a_escanear = [CARPETA_ORIGEN]
        
    # --- PROCESO DE VERIFICACIÓN ---
    # 1. Definir los archivos a verificar (todos los clasificados/segmentados)
    archivos_a_verificar = []
    for carpeta in carpetas_a_escanear:
        archivos_a_verificar.extend(glob.glob(os.path.join(carpeta, "*.m3u")))
        
    # 2. Obtener los hashes de los bloques rotos (muestras)
    hashes_rotos = verificar_enlaces_en_archivos(archivos_a_verificar)
    
    # --- COMPILACIÓN FINAL ---
    hashes_globales: Set[str] = set()
    totales_por_categoria: Counter[str] = Counter()

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as salida:
        salida.write("#EXTM3U\n")
        salida.write(f"# Generado por Berluca - {os.path.basename(ARCHIVO_SALIDA)}\n\n")

        for ruta in archivos_a_verificar:
            archivo = os.path.basename(ruta)
            
            # Determinar la categoría base (para metadatos visuales)
            base = archivo.split("_")[0].lower().replace(".m3u", "")
            titulo = TITULOS_VISUALES.get(base, f"★ {base.replace('_', ' ').upper()} ★")
            logo = LOGOS_CATEGORIA.get(base, LOGO_DEFAULT)
            
            salida.write(f"\n# =================================================================")
            salida.write(f"\n# {titulo}")
            salida.write(f"\n# =================================================================\n\n")
            
            lineas_archivo = leer_archivo_m3u(ruta)
            bloques = extraer_bloques_m3u(lineas_archivo)
            
            for bloque in bloques:
                bloque_saneado = sanear_bloque_m3u(bloque)
                if not bloque_saneado:
                    continue
                
                h = hash_bloque(bloque_saneado)
                
                # 3. Deduplicación Global
                if h in hashes_globales:
                    continue
                
                # 4. Eliminación de Bloques Rotos (Filtrado por Hash)
                if h in hashes_rotos:
                    continue
                
                hashes_globales.add(h)
                
                # 5. Auditoría Visual (Asegurar logo y group-title)
                bloque_final = auditar_bloque_visual(bloque_saneado, base)
                
                # Escribir el bloque
                salida.write("\n".join(bloque_final).strip() + "\n\n")
                
                totales_por_categoria[base] += 1

    # 6. Adaptación final (ej: Movian)
    adaptar_para_movian(ARCHIVO_SALIDA)

    # 7. Limpieza y Diagnóstico final
    verificar_archivos_movian() # Limpia archivos temporales de Movian
    limpiar_carpeta(CARPETA_ORIGEN) # Limpiar archivos de categorías después de compilar
    limpiar_carpeta(CARPETA_SEGMENTADOS) # Limpiar archivos segmentados
    
    print(f"\n✅ Lista final generada con {len(hashes_globales)} canales únicos y verificados.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA}")
    
    print("\n📊 Totales por categoría:")
    for cat, count in totales_por_categoria.most_common():
        if count > 0:
            print(f"  - {cat.replace('_', ' ').capitalize()}: {count} canales")