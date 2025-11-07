# generador.py
import os
import glob 
import datetime
import re 
from collections import Counter, defaultdict
from typing import List, Tuple, Dict

# 📦 Importaciones de configuración y funciones de parseo
try:
    from config import (
        CARPETA_ORIGEN, CARPETA_SALIDA, LOGO_DEFAULT, LOGOS_CATEGORIA, 
        TITULOS_VISUALES, CATEGORIAS_PRINCIPALES_ESPANOL, CLAVES_ROLL_OVER
    )
    from clasificador import extraer_bloques_m3u, extraer_nombre_canal, extraer_url
except ImportError as e:
    print(f"Error al importar configuración: {e}")
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
    CLAVES_ROLL_OVER = {}


# Definición del archivo final PRINCIPAL
ARCHIVO_SALIDA_BASE = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")
PATRON_CORRELATIVO = os.path.join(CARPETA_SALIDA, "RP_S????.m3u")


# =========================================================================================
# 🆕 FUNCIONES AUXILIARES
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

def limpiar_archivos_temporales(ruta_archivos: str):
    """Elimina los archivos de compilados/ que no pertenecen al RP_S2048."""
    
    ruta_roll_over = os.path.join(CARPETA_ORIGEN, "roll_over_general.m3u")
    
    if os.path.exists(ruta_roll_over):
        try:
            os.remove(ruta_roll_over)
            print(f"🗑️ Archivo temporal {os.path.basename(ruta_roll_over)} eliminado.")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar {os.path.basename(ruta_roll_over)}: {e}")


def reclasificar_roll_over(bloques: List[List[str]]) -> List[Tuple[str, List[str]]]:
    """
    Toma bloques y los clasifica en categorías específicas para el roll-over,
    usando CLAVES_ROLL_OVER.
    """
    bloques_clasificados = []
    
    for bloque in bloques:
        nombre = extraer_nombre_canal(bloque)
        nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
        
        categoria_asignada = None
        
        for categoria, claves in CLAVES_ROLL_OVER.items():
            if any(clave in nombre_lower for clave in claves):
                categoria_asignada = categoria 
                break
        
        if categoria_asignada:
            bloques_clasificados.append((categoria_asignada, bloque))
        else:
            # Si no coincide, va a la categoría de último recurso del roll-over
            bloques_clasificados.append(("SIN_CLASIFICAR_ROLLOVER", bloque))
            
    return bloques_clasificados


# =========================================================================================
# 🧱 CONSOLIDACIÓN DE LISTAS
# =========================================================================================

def consolidar_lista(rutas_archivos: List[str], ruta_salida: str, es_roll_over: bool) -> Tuple[int, Counter]:
    """Lógica unificada para generar la lista M3U principal."""
    
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
            
            # Títulos para RP_S2048.m3u
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
                    # Usamos el título del bloque para group-title
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


def consolidar_lista_reclasificada(bloques_por_subcategoria: defaultdict[str, List[List[str]]], ruta_salida: str) -> Tuple[int, Counter]:
    """
    Escribe el archivo roll-over (RP_Sxxxx.m3u) usando las nuevas sub-categorías.
    """
    
    totales_por_categoria = Counter()
    total_consolidado = 0
    urls_escritas_global = set()
    
    # Ordenar las sub-categorías según las claves de CLAVES_ROLL_OVER para una mejor presentación
    orden_claves = list(CLAVES_ROLL_OVER.keys()) + ["SIN_CLASIFICAR_ROLLOVER"]
    categorias_a_escribir = [c for c in orden_claves if c in bloques_por_subcategoria]

    with open(ruta_salida, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n\n")

        for nombre_categoria_snake in categorias_a_escribir:
            
            # Usar el título visual definido para la sub-categoría
            titulo_visual = TITULOS_VISUALES.get(nombre_categoria_snake, f"★ {nombre_categoria_snake.replace('_', ' ').upper()} ★")
            logo = LOGO_DEFAULT 
            
            salida.write(f"\n# ====== {titulo_visual} ======\n\n")

            bloques_escritos_en_categoria = 0
            
            for bloque in bloques_por_subcategoria[nombre_categoria_snake]:
                nombre = extraer_nombre_canal(bloque)
                url = extraer_url(bloque)
                
                if url in urls_escritas_global: continue 
                
                if url:
                    extinf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{titulo_visual}",{nombre.strip()}'
                    salida.write(extinf_line + "\n")
                    salida.write(f"{url.strip()}\n\n")
                    
                    urls_escritas_global.add(url)
                    total_consolidado += 1
                    bloques_escritos_en_categoria += 1
            
            if bloques_escritos_en_categoria > 0:
                totales_por_categoria[nombre_categoria_snake] += bloques_escritos_en_categoria
                
    return total_consolidado, totales_por_categoria


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN
# =========================================================================================

def generar_listas_finales():
    """
    Genera RP_S2048.m3u con categorías de habla hispana, 
    y RP_Sxxxx.m3u con el contenido re-clasificado de roll_over_general.
    """
        
    print("\n📦 Iniciando consolidación con deduplicación y gestión de respaldos...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_clasificadas = glob.glob(patron_busqueda)
    
    # 1. Archivos para RP_S2048.m3u (SOLO ESPAÑOL/PRINCIPAL)
    listas_principal = [
        ruta for ruta in listas_clasificadas 
        if os.path.basename(ruta).replace(".m3u", "") in CATEGORIAS_PRINCIPALES_ESPANOL
    ]
    
    ruta_roll_over = os.path.join(CARPETA_ORIGEN, "roll_over_general.m3u")
    
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

    if os.path.exists(ruta_roll_over):
        
        with open(ruta_roll_over, "r", encoding="utf-8", errors="ignore") as f:
            lineas_roll_over = f.readlines()
        
        bloques_roll_over = extraer_bloques_m3u(lineas_roll_over)
        
        if bloques_roll_over:
            
            # 1. RE-CLASIFICAR el contenido de roll_over_general
            bloques_reclasificados = reclasificar_roll_over(bloques_roll_over)
            
            # 2. Organizar por las nuevas sub-categorías
            bloques_por_subcategoria = defaultdict(list)
            for categoria, bloque in bloques_reclasificados:
                bloques_por_subcategoria[categoria].append(bloque)

            # 3. Generar la lista final
            archivo_correlativo = encontrar_siguiente_correlativo()
            ruta_correlativa = os.path.join(CARPETA_SALIDA, archivo_correlativo)

            total_consolidado_roll_over, totales_roll_over = consolidar_lista_reclasificada(
                bloques_por_subcategoria, ruta_correlativa
            )

            print(f"\n✅ {archivo_correlativo} (Roll-Over/No Español) generado con éxito.")
            print(f"📁 Ubicación: {ruta_correlativa}")
            print(f"📊 Total de enlaces consolidados: {total_consolidado_roll_over}")
            print("📊 Totales por sub-categoría (Respaldo):")
            for cat, count in totales_roll_over.most_common():
                print(f"   -> {cat.replace('_', ' ').title()}: {count} enlaces")
        else:
            print("⚠️ roll_over_general.m3u está vacío. No se genera archivo correlativo.")
        
        # 4. Eliminar roll_over_general.m3u
        limpiar_archivos_temporales(ruta_roll_over)
    else:
        print("ℹ️ No se encontró roll_over_general.m3u. No se genera archivo correlativo.")


if __name__ == "__main__":
    generar_listas_finales()