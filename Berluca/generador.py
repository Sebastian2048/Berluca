import os
import glob 
from collections import Counter, defaultdict
from typing import List

# 📦 Importaciones de configuración y funciones de parseo
try:
    from config import (
        CARPETA_ORIGEN, CARPETA_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
        TITULOS_VISUALES
    )
    # Importar funciones de parseo de clasificador.py
    from clasificador import extraer_bloques_m3u, extraer_nombre_canal, extraer_url
except ImportError:
    # Definiciones placeholder si la importación falla (ajustar si es necesario)
    def extraer_bloques_m3u(lineas: List[str]): return []
    def extraer_nombre_canal(bloque: List[str]): return "Sin nombre"
    def extraer_url(bloque: List[str]): return ""
    
# Definición del archivo final (usando CARPETA_SALIDA="Beluga")
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")

# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN CON DEDUPLICACIÓN Y BACKUP
# =========================================================================================

def generar_listas_finales():
    """
    Consolida todos los archivos clasificados desde CARPETA_ORIGEN (compilados/),
    aplicando la regla de máximo 2 URLs distintas por nombre de canal (backup).
    """
        
    print("\n📦 Iniciando consolidación con deduplicación y gestión de backups...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_clasificadas = glob.glob(patron_busqueda)
    
    # Excluir cualquier archivo no clasificado o temporal
    listas_clasificadas = [
        ruta for ruta in listas_clasificadas 
        if "TEMP_MATERIAL" not in os.path.basename(ruta) and "sin_clasificar" not in os.path.basename(ruta)
    ]
    
    listas_clasificadas.sort(key=lambda x: os.path.basename(x))
    
    totales_por_categoria = Counter()
    total_consolidado = 0
    
    # 🛑 ESTRUCTURA CLAVE: {Nombre_Canal_Normalizado: Set_de_URLs_Guardadas}
    urls_por_nombre = defaultdict(set)
    # Set para control de URLs a nivel global (deduplicación estricta de la URL)
    urls_escritas_global = set()

    # 2. Escribir el archivo de salida
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n\n")

        for ruta in listas_clasificadas:
            archivo_base = os.path.basename(ruta)
            nombre_categoria_snake = archivo_base.replace(".m3u", "")
            
            # Obtener el título visual (se usa el nombre del archivo para buscar en TITULOS_VISUALES)
            titulo_visual = TITULOS_VISUALES.get(
                nombre_categoria_snake,
                f"★ {nombre_categoria_snake.replace('_', ' ').upper()} ★"
            )
            
            # Obtener el logo
            logo = LOGOS_CATEGORIA.get(nombre_categoria_snake, LOGO_DEFAULT)
            
            # Escribir el título de grupo
            salida.write(f"\n# ====== {titulo_visual} ======\n\n")

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
                
                # Normalizar el nombre para la clave de backup
                nombre_clave = nombre.strip().lower().replace(" ", "")

                # 🛑 REGLA 1: DEDUPLICACIÓN ESTRICNTA DE LA URL 
                if url in urls_escritas_global:
                    continue 

                # 🛑 REGLA 2: LÍMITE DE BACKUP POR NOMBRE (Máximo 2)
                if len(urls_por_nombre[nombre_clave]) >= 2:
                    continue

                # Si pasa las reglas: escribir con formato de metadatos (Fix Movian)
                if url:
                    salida.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre.strip()}\n')
                    salida.write(f"{url.strip()}\n\n")
                    
                    # Registrar la URL
                    urls_escritas_global.add(url)
                    urls_por_nombre[nombre_clave].add(url)
                    
                    total_consolidado += 1
                    bloques_escritos_en_categoria += 1
            
            if bloques_escritos_en_categoria > 0:
                totales_por_categoria[nombre_categoria_snake] = bloques_escritos_en_categoria

    # 3. Diagnóstico final y Reporte
    print(f"\n✅ RP_S2048.m3u generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA}")
    print(f"📊 Total de enlaces consolidados (Máx. 2 por nombre): {total_consolidado}")
    print("\n📊 Totales por categoría (Enlaces únicos y limitados):")
    for cat, count in totales_por_categoria.most_common():
        print(f"   -> {cat.replace('_', ' ').title()}: {count} enlaces")

if __name__ == "__main__":
    generar_listas_finales()