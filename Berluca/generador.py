import os
import glob 
from collections import Counter
from typing import List

# Importaciones de constantes y funciones necesarias
# Debemos importar ARCHIVO_SALIDA y las rutas correctas desde el config del usuario
from config import (
    CARPETA_ORIGEN, ARCHIVO_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
    TITULOS_VISUALES, MINIMO_BLOQUES_VALIDOS
)

# NOTA: Estas funciones deben existir o importarse. Las añado como stubs si no están en m3u_core.
def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    """Función stub para extraer bloques (asumimos que existe en clasificador/m3u_core)"""
    # Implementación básica para que funcione si se copia aquí
    bloques = []
    buffer = []
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            if buffer:
                bloques.append(buffer)
            buffer = [linea]
        elif buffer and linea.startswith("http"):
            buffer.append(linea)
    if len(buffer) == 2:
        bloques.append(buffer)
    return bloques

def extraer_nombre_canal(bloque: List[str]) -> str:
    """Función stub para extraer nombre (asumimos que existe en clasificador/m3u_core)"""
    if bloque and bloque[0].startswith("#EXTINF"):
        partes = bloque[0].split(",", 1)
        return partes[1].strip() if len(partes) > 1 else "Sin nombre"
    return "Sin nombre"

def extraer_url(bloque: List[str]) -> str:
    """Función stub para extraer URL (asumimos que existe en clasificador/m3u_core)"""
    return bloque[-1] if bloque and bloque[-1].startswith("http") else ""


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN
# =========================================================================================

def generar_listas_finales():
    """
    Consolida todos los archivos clasificados en CARPETA_ORIGEN 
    en el archivo final RP_S2048.m3u.
    """
    
    print("\n📦 Iniciando consolidación de listas finales...")

    # 🛑 CORRECCIÓN CLAVE: Buscar archivos en CARPETA_ORIGEN (compilados) 
    # donde clasificador.py los dejó.
    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_finales = glob.glob(patron_busqueda)
    
    # Excluir el archivo temporal y asegurar que existan bloques
    listas_finales = [
        ruta for ruta in listas_finales 
        if "TEMP_MATERIAL" not in os.path.basename(ruta)
    ]
    
    # Ordenar las listas por nombre
    listas_finales.sort(key=lambda x: os.path.basename(x))
    
    totales_por_categoria = Counter()
    total_consolidado = 0

    # 5. Escribir el archivo de salida
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8", errors="ignore") as salida:
        # Escribir cabecera
        salida.write("#EXTM3U\n\n")

        for ruta in listas_finales:
            archivo_base = os.path.basename(ruta)
            nombre_categoria = archivo_base.replace(".m3u", "").replace("_", " ")
            
            # Obtener el título visual (e.g., "★ ANIME ★")
            titulo_visual = TITULOS_VISUALES.get(
                nombre_categoria.replace(" ", "_"),
                f"★ {nombre_categoria.upper()} ★"
            )
            
            # Obtener el logo por defecto o específico
            logo = LOGOS_CATEGORIA.get(nombre_categoria.replace(" ", "_"), LOGO_DEFAULT)
            
            # 5.1. Escribir el título de grupo
            salida.write(f"\n# ====== {titulo_visual} (Cat: {nombre_categoria.upper()}) ======\n\n")

            # 5.2. Abrir el archivo de categoría (e.g., anime.m3u)
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                bloques = extraer_bloques_m3u(f.readlines())
            
            # 5.3. Escribir los bloques
            for bloque in bloques:
                nombre = extraer_nombre_canal(bloque)
                url = extraer_url(bloque)
                
                # Re-formatear la línea EXTINF para el archivo final
                if url:
                    salida.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre}\n')
                    salida.write(f"{url}\n\n")
                    total_consolidado += 1
            
            totales_por_categoria[nombre_categoria] = len(bloques)

    # 6. Diagnóstico final y Reporte
    print(f"\n✅ RP_S2048.m3u generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA}")
    print(f"📊 Total de enlaces consolidados: {total_consolidado}")
    print("\n📊 Totales por categoría:")
    for cat, count in totales_por_categoria.most_common():
        print(f"   -> {cat.capitalize()}: {count} enlaces")

# La función generadora de listas finales debería ser llamada por main.py