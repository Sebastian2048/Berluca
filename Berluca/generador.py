# generador.py
import os
import glob 
import datetime
import re 
from collections import Counter, defaultdict
from typing import List, Tuple

# 📦 Importaciones de configuración y funciones de parseo
try:
    from config import (
        CARPETA_ORIGEN, CARPETA_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
        TITULOS_VISUALES, CATEGORIAS_PRINCIPALES_ESPANOL, OVERFLOW_MAP
    )
    from clasificador import extraer_bloques_m3u, extraer_nombre_canal, extraer_url
except ImportError as e:
    # Definiciones de fallback si falla la importación
    def extraer_bloques_m3u(lineas: List[str]): return []
    def extraer_nombre_canal(bloque: List[str]): return "Sin nombre"
    def extraer_url(bloque: List[str]): return ""
    CARPETA_ORIGEN = "Beluga/compilados"
    CARPETA_SALIDA = "Beluga"
    LOGO_DEFAULT = ""
    LOGOS_CATEGORIA = {}
    TITULOS_VISUALES = {}
    CATEGORIAS_PRINCIPALES_ESPANOL = []
    OVERFLOW_MAP = {}

# Definición del archivo final PRINCIPAL
ARCHIVO_SALIDA_BASE = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")
PATRON_CORRELATIVO = os.path.join(CARPETA_SALIDA, "RP_S????.m3u")

# =========================================================================================
# 🧹 FUNCIÓN DE LIMPIEZA DE CADUCIDAD (ELIMINADA)
# =========================================================================================
# NOTA: Esta función se elimina porque ya no se usa la fecha de caducidad.

def limpiar_archivos_temporales(ruta_archivos: str):
    """Elimina los archivos de compilados/ que no pertenecen al RP_S2048."""
    
    # La categoría que contiene todos los canales de descarte/no español/misceláneo
    ruta_roll_over = os.path.join(CARPETA_ORIGEN, "roll_over_general.m3u")
    
    if os.path.exists(ruta_roll_over):
        try:
            os.remove(ruta_roll_over)
            print(f"🗑️ Archivo temporal {os.path.basename(ruta_roll_over)} eliminado.")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar {os.path.basename(ruta_roll_over)}: {e}")


# =========================================================================================
# 🆕 FUNCIÓN PARA ENCONTRAR EL SIGUIENTE CORRELATIVO (Se mantiene igual)
# =========================================================================================

def encontrar_siguiente_correlativo() -> str:
    """Busca archivos RP_S????.m3u y devuelve el siguiente número disponible (a partir de 2049)."""
    archivos_existentes = glob.glob(PATRON_CORRELATIVO)
    numeros = []
    for archivo in archivos_existentes:
        nombre_base = os.path.basename(archivo)
        match = re.search(r'RP_S(\d{4})\.m3u', nombre_base)
        if match:
            try:
                num = int(match.group(1))
                if num >= 2049:
                    numeros.append(num)
            except ValueError:
                continue

    if not numeros:
        siguiente_numero = 2049
    else:
        siguiente_numero = max(numeros) + 1
        
    return f"RP_S{siguiente_numero:04d}.m3u"


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN (MODIFICADA CON DOS GRUPOS)
# =========================================================================================

def generar_listas_finales():
    """
    Genera RP_S2048.m3u con categorías de habla hispana, 
    y RP_Sxxxx.m3u con el contenido de roll_over_general.
    """
        
    print("\n📦 Iniciando consolidación con deduplicación y gestión de respaldos...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_clasificadas = glob.glob(patron_busqueda)
    
    # 1. Archivos para RP_S2048.m3u (SOLO ESPAÑOL/PRINCIPAL)
    listas_principal = []
    
    # 2. Archivos para RP_Sxxxx.m3u (ROLL-OVER / NO ESPAÑOL)
    listas_roll_over = []
    ruta_roll_over = os.path.join(CARPETA_ORIGEN, "roll_over_general.m3u")

    for ruta in listas_clasificadas:
        archivo_base = os.path.basename(ruta).replace(".m3u", "")
        if archivo_base in CATEGORIAS_PRINCIPALES_ESPANOL:
            listas_principal.append(ruta)
        elif archivo_base == "roll_over_general":
            listas_roll_over.append(ruta)
        
    
    # ------------------- A. Generar RP_S2048.m3u (Principal) -------------------
    
    total_consolidado_principal, totales_principal = consolidar_lista(
        listas_principal, ARCHIVO_SALIDA_BASE, es_roll_over=False
    )

    print(f"\n✅ {os.path.basename(ARCHIVO_SALIDA_BASE)} generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA_BASE}")
    print(f"📊 Total de enlaces consolidados (ESPAÑOL): {total_consolidado_principal}")
    print("📊 Totales por categoría (Principal):")
    for cat, count in totales_principal.most_common():
        print(f"   -> {cat.replace('_', ' ').title()}: {count} enlaces")

    # ------------------- B. Generar RP_Sxxxx.m3u (Roll-Over/Correlativo) -------------------

    if listas_roll_over:
        archivo_correlativo = encontrar_siguiente_correlativo()
        ruta_correlativa = os.path.join(CARPETA_SALIDA, archivo_correlativo)
        
        # Consolidar el contenido de roll_over_general
        total_consolidado_roll_over, totales_roll_over = consolidar_lista(
            listas_roll_over, ruta_correlativa, es_roll_over=True
        )

        print(f"\n✅ {archivo_correlativo} (Roll-Over/No Español) generado con éxito.")
        print(f"📁 Ubicación: {ruta_correlativa}")
        print(f"📊 Total de enlaces consolidados: {total_consolidado_roll_over}")
        
        # Eliminar roll_over_general.m3u de compilados/ después de generar el respaldo
        limpiar_archivos_temporales(ruta_roll_over)
        

# =========================================================================================
# 🧱 FUNCIÓN AUXILIAR DE CONSOLIDACIÓN (Se ajusta para roll_over)
# =========================================================================================

def consolidar_lista(rutas_archivos: List[str], ruta_salida: str, es_roll_over: bool) -> Tuple[int, Counter]:
    """Lógica unificada para generar la lista M3U final."""
    
    rutas_archivos.sort(key=lambda x: os.path.basename(x))
    
    totales_por_categoria = Counter()
    total_consolidado = 0
    urls_por_nombre = defaultdict(set)
    urls_escritas_global = set()

    with open(ruta_salida, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n\n")

        for ruta in rutas_archivos:
            archivo_base = os.path.basename(ruta)
            nombre_categoria_snake = archivo_base.replace(".m3u", "")
            
            if es_roll_over:
                 # Usamos el título del archivo roll_over_general.m3u
                 titulo_visual = TITULOS_VISUALES.get("roll_over_general", "★ CANALES ROLL-OVER/OTROS (Respaldo) ★")
                 logo = LOGO_DEFAULT
            else:
                titulo_visual = TITULOS_VISUALES.get(nombre_categoria_snake, f"★ {nombre_categoria_snake.replace('_', ' ').upper()} ★")
                logo = LOGOS_CATEGORIA.get(nombre_categoria_snake, LOGO_DEFAULT)
            
            salida.write(f"\n# ====== {titulo_visual} ======\n\n")

            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    lineas = f.readlines()
                    bloques = extraer_bloques_m3u(lineas)
            except Exception: continue

            bloques_escritos_en_categoria = 0
            
            for bloque in bloques:
                nombre = extraer_nombre_canal(bloque)
                url = extraer_url(bloque)
                nombre_clave = nombre.strip().lower().replace(" ", "")

                if url in urls_escritas_global: continue 
                if len(urls_por_nombre[nombre_clave]) >= 2: continue

                if url:
                    extinf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre.strip()}'
                    salida.write(extinf_line + "\n")
                    salida.write(f"{url.strip()}\n\n")
                    
                    urls_escritas_global.add(url)
                    urls_por_nombre[nombre_clave].add(url)
                    total_consolidado += 1
                    bloques_escritos_en_categoria += 1
            
            if bloques_escritos_en_categoria > 0:
                totales_por_categoria[nombre_categoria_snake] += bloques_escritos_en_categoria
                
    return total_consolidado, totales_por_categoria

if __name__ == "__main__":
    generar_listas_finales()