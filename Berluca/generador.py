import os
import glob 
from collections import Counter, defaultdict
from typing import List

# 🛑 NOTA: Asegúrate de que estas importaciones se resuelvan
from config import (
    CARPETA_ORIGEN, CARPETA_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
    TITULOS_VISUALES
)

# 🛑 NOTA: Importar directamente desde clasificador.py (Asumido)
try:
    from clasificador import extraer_bloques_m3u, extraer_nombre_canal, extraer_url
except ImportError:
    # Definiciones placeholder si la importación falla (ajusta la ruta si es necesario)
    def extraer_bloques_m3u(lineas: List[str]): return []
    def extraer_nombre_canal(bloque: List[str]): return "Sin nombre"
    def extraer_url(bloque: List[str]): return ""

# Definición del archivo final
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")

# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN CON DEDUPLICACIÓN Y BACKUP
# =========================================================================================

def generar_listas_finales():
    """
    Consolida todos los archivos clasificados, permitiendo un máximo de 
    dos URLs distintas por nombre de canal (backup), y elimina duplicados.
    """
        
    print("\n📦 Iniciando consolidación con deduplicación y gestión de backups...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_finales = glob.glob(patron_busqueda)
    
    # 🛑 Excluir sin_clasificar
    listas_finales = [
        ruta for ruta in listas_finales 
        if "TEMP_MATERIAL" not in os.path.basename(ruta) and "sin_clasificar" not in os.path.basename(ruta)
    ]
    
    listas_finales.sort(key=lambda x: os.path.basename(x))
    
    totales_por_categoria = Counter()
    total_consolidado = 0
    
    # 🛑 ESTRUCTURA CLAVE: Diccionario para rastrear {Nombre_Canal: Set_de_URLs_Guardadas}
    urls_por_nombre = defaultdict(set)
    # Set para control de URLs a nivel global (deduplicación estricta de la URL)
    urls_escritas_global = set()

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
                
                # Normalizar el nombre para la clave de backup
                nombre_clave = nombre.strip().lower()

                # 🛑 REGLA 1: DEDUPLICACIÓN ESTRICNTA DE LA URL 
                if url in urls_escritas_global:
                    continue 

                # 🛑 REGLA 2: LÍMITE DE BACKUP POR NOMBRE (Máximo 2)
                if len(urls_por_nombre[nombre_clave]) >= 2:
                    continue # Ya tenemos dos versiones, descartamos la tercera

                # Si llegamos aquí, la URL es única globalmente Y no hemos excedido el límite de backup para ese nombre.
                if url:
                    # Escribir con formato estricto (Fix Movian)
                    salida.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre.strip()}\n')
                    salida.write(f"{url.strip()}\n\n")
                    
                    # Registrar la URL a nivel global y a nivel de nombre
                    urls_escritas_global.add(url)
                    urls_por_nombre[nombre_clave].add(url)
                    
                    total_consolidado += 1
                    bloques_escritos_en_categoria += 1
            
            totales_por_categoria[nombre_categoria] = bloques_escritos_en_categoria

    # 3. Diagnóstico final y Reporte
    print(f"\n✅ RP_S2048.m3u generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA}")
    print(f"📊 Total de enlaces consolidados (Máx. 2 por nombre): {total_consolidado}")
    print("\n📊 Totales por categoría:")
    for cat, count in totales_por_categoria.most_common():
        print(f"   -> {cat.capitalize()}: {count} enlaces")