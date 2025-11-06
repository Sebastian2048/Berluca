import os
import glob 
from collections import Counter
from typing import List

# =========================================================================================
# 🛑 IMPORTACIONES DE MÓDULOS DEL PROYECTO
# =========================================================================================

# Importaciones de constantes de rutas, logos y títulos desde config.py
from config import (
    CARPETA_ORIGEN, ARCHIVO_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
    TITULOS_VISUALES
)

# Importamos las funciones de parseo M3U desde clasificador.py (donde ya están definidas)
from clasificador import (
    extraer_bloques_m3u, 
    extraer_nombre_canal, 
    extraer_url
)


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN CON DEDUPLICACIÓN
# =========================================================================================

def generar_listas_finales():
    """
    Consolida todos los archivos clasificados en CARPETA_ORIGEN 
    en el archivo final RP_S2048.m3u, eliminando duplicados por URL.
    """
    
    print("\n📦 Iniciando consolidación de listas finales y eliminación de duplicados...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_finales = glob.glob(patron_busqueda)
    
    listas_finales = [
        ruta for ruta in listas_finales 
        if "TEMP_MATERIAL" not in os.path.basename(ruta)
    ]
    
    listas_finales.sort(key=lambda x: os.path.basename(x))
    
    totales_por_categoria = Counter()
    total_consolidado = 0
    
    # 🛑 ESTRUCTURA CLAVE: Set para rastrear las URLs ya escritas (DEDUPLICACIÓN)
    urls_escritas = set() 

    # 2. Escribir el archivo de salida
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8", errors="ignore") as salida:
        # Escribir cabecera
        salida.write("#EXTM3U\n\n")

        for ruta in listas_finales:
            archivo_base = os.path.basename(ruta)
            nombre_categoria_snake = archivo_base.replace(".m3u", "")
            nombre_categoria = nombre_categoria_snake.replace("_", " ")
            
            # Obtener el título visual (e.g., "★ ANIME ★")
            titulo_visual = TITULOS_VISUALES.get(
                nombre_categoria_snake,
                f"★ {nombre_categoria.upper()} ★"
            )
            
            # Obtener el logo por defecto o específico
            logo = LOGOS_CATEGORIA.get(nombre_categoria_snake, LOGO_DEFAULT)
            
            # Escribir el título de grupo
            salida.write(f"\n# ====== {titulo_visual} (Cat: {nombre_categoria.upper()}) ======\n\n")

            # Abrir el archivo de categoría (e.g., anime.m3u)
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    bloques = extraer_bloques_m3u(f.readlines())
            except Exception as e:
                 print(f"⚠️ No se pudo leer el archivo {archivo_base}: {e}")
                 continue

            bloques_escritos_en_categoria = 0
            
            # Escribir los bloques
            for bloque in bloques:
                nombre = extraer_nombre_canal(bloque)
                url = extraer_url(bloque)
                
                # 🛑 VERIFICACIÓN DE DUPLICADOS: Si la URL ya fue escrita, saltar este bloque.
                if url in urls_escritas:
                    continue 

                # Si la URL es nueva y válida, la escribimos y la añadimos al set de control.
                if url:
                    salida.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre}\n')
                    salida.write(f"{url}\n\n")
                    
                    urls_escritas.add(url)
                    total_consolidado += 1
                    bloques_escritos_en_categoria += 1
            
            totales_por_categoria[nombre_categoria] = bloques_escritos_en_categoria

    # 3. Diagnóstico final y Reporte
    print(f"\n✅ RP_S2048.m3u generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA}")
    print(f"📊 Total de enlaces consolidados (sin duplicados): {total_consolidado}")
    print("\n📊 Totales por categoría (sin contar enlaces duplicados):")
    for cat, count in totales_por_categoria.most_common():
        print(f"   -> {cat.capitalize()}: {count} enlaces")