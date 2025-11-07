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
        TITULOS_VISUALES, DIAS_EXPIRACION_MISCELANEO
    )
    from clasificador import extraer_bloques_m3u, extraer_nombre_canal, extraer_url
except ImportError as e:
    print(f"Error al importar de config.py o clasificador.py: {e}")
    # Definiciones de fallback
    def extraer_bloques_m3u(lineas: List[str]): return []
    def extraer_nombre_canal(bloque: List[str]): return "Sin nombre"
    def extraer_url(bloque: List[str]): return ""
    CARPETA_ORIGEN = "Beluga/compilados"
    CARPETA_SALIDA = "Beluga"
    LOGO_DEFAULT = ""
    LOGOS_CATEGORIA = {}
    TITULOS_VISUALES = {}
    DIAS_EXPIRACION_MISCELANEO = 7

# Definición del archivo final PRINCIPAL
ARCHIVO_SALIDA_BASE = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")
PATRON_CORRELATIVO = os.path.join(CARPETA_SALIDA, "RP_S????.m3u")

# =========================================================================================
# 🧹 FUNCIÓN DE LIMPIEZA DE CADUCIDAD (Se mantiene igual)
# =========================================================================================

def limpiar_miscelaneo_caducado():
    """
    Lee miscelaneo_otros.m3u, elimina los enlaces que superen la caducidad
    y reescribe el archivo.
    """
    ruta_miscelaneo = os.path.join(CARPETA_ORIGEN, "miscelaneo_otros.m3u")
    
    if not os.path.exists(ruta_miscelaneo): return

    print(f"\n⌛ Verificando caducidad en miscelaneo_otros (>{DIAS_EXPIRACION_MISCELANEO} días)...")
    
    try:
        with open(ruta_miscelaneo, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
    except Exception:
        print("⚠️ No se pudo leer miscelaneo_otros.m3u.")
        return

    bloques = extraer_bloques_m3u(lineas)
    bloques_validos = []
    
    hoy = datetime.date.today()
    expirados_count = 0
    patron_fecha = re.compile(r'exp-date="(\d{4}-\d{2}-\d{2})"') 

    for bloque in bloques:
        extinf_line = bloque[0]
        match = patron_fecha.search(extinf_line)
        
        if match:
            fecha_str = match.group(1)
            try:
                fecha_creacion = datetime.date.fromisoformat(fecha_str)
                dias_pasados = (hoy - fecha_creacion).days
                if dias_pasados < DIAS_EXPIRACION_MISCELANEO:
                    bloques_validos.append(bloque)
                else:
                    expirados_count += 1
            except ValueError:
                bloques_validos.append(bloque)
        else:
            bloques_validos.append(bloque)

    # Reescribir el archivo
    with open(ruta_miscelaneo, "w", encoding="utf-8", errors="ignore") as f:
        f.write("#EXTM3U\n\n")
        for bloque in bloques_validos:
            f.write(bloque[0] + "\n")
            f.write(bloque[-1] + "\n\n")

    print(f"   -> {expirados_count} enlaces expirados eliminados de miscelaneo_otros.")


# =========================================================================================
# 🆕 FUNCIÓN PARA ENCONTRAR EL SIGUIENTE CORRELATIVO
# =========================================================================================

def encontrar_siguiente_correlativo() -> str:
    """Busca archivos RP_S????.m3u y devuelve el siguiente número disponible (a partir de 2049)."""
    archivos_existentes = glob.glob(PATRON_CORRELATIVO)
    
    numeros = []
    for archivo in archivos_existentes:
        nombre_base = os.path.basename(archivo)
        # Extraer el número entre 'RP_S' y '.m3u'
        match = re.search(r'RP_S(\d{4})\.m3u', nombre_base)
        if match:
            try:
                num = int(match.group(1))
                if num >= 2049: # Solo consideramos los archivos de respaldo
                    numeros.append(num)
            except ValueError:
                continue

    # Si no hay archivos de respaldo, empezamos en 2049
    if not numeros:
        siguiente_numero = 2049
    else:
        # Si hay archivos, el siguiente es el máximo existente + 1
        siguiente_numero = max(numeros) + 1
        
    return f"RP_S{siguiente_numero:04d}.m3u"


# =========================================================================================
# 📦 FUNCIÓN PRINCIPAL DE CONSOLIDACIÓN (MODIFICADA CON DOS SALIDAS)
# =========================================================================================

def generar_listas_finales():
    """
    Consolida todos los archivos clasificados en RP_S2048.m3u (Principal) 
    y miscelaneo_otros.m3u en un archivo correlativo RP_Sxxxx.m3u.
    """
        
    print("\n📦 Iniciando consolidación con deduplicación y gestión de respaldos...")

    patron_busqueda = os.path.join(CARPETA_ORIGEN, "*.m3u")
    listas_clasificadas = glob.glob(patron_busqueda)
    
    listas_clasificadas_principal = [
        ruta for ruta in listas_clasificadas 
        if "TEMP_MATERIAL" not in os.path.basename(ruta) and "sin_clasificar" not in os.path.basename(ruta)
        and "miscelaneo_otros" not in os.path.basename(ruta) # Excluir misceláneo para el principal
    ]
    
    ruta_miscelaneo = os.path.join(CARPETA_ORIGEN, "miscelaneo_otros.m3u")

    if os.path.exists(ruta_miscelaneo):
        listas_clasificadas_miscelaneo = [ruta_miscelaneo]
    else:
        listas_clasificadas_miscelaneo = []
        
    
    # ------------------- 1. Generar RP_S2048.m3u (Principal) -------------------
    
    total_consolidado_principal, totales_principal = consolidar_lista(
        listas_clasificadas_principal, ARCHIVO_SALIDA_BASE, es_miscelaneo=False
    )

    print(f"\n✅ {os.path.basename(ARCHIVO_SALIDA_BASE)} generado con éxito.")
    print(f"📁 Ubicación: {ARCHIVO_SALIDA_BASE}")
    print(f"📊 Total de enlaces consolidados: {total_consolidado_principal}")
    print("📊 Totales por categoría (Principal):")
    for cat, count in totales_principal.most_common():
        print(f"   -> {cat.replace('_', ' ').title()}: {count} enlaces")

    # ------------------- 2. Generar RP_Sxxxx.m3u (Misceláneo/Correlativo) -------------------

    if listas_clasificadas_miscelaneo:
        archivo_correlativo = encontrar_siguiente_correlativo()
        ruta_correlativa = os.path.join(CARPETA_SALIDA, archivo_correlativo)
        
        total_consolidado_miscelaneo, totales_miscelaneo = consolidar_lista(
            listas_clasificadas_miscelaneo, ruta_correlativa, es_miscelaneo=True
        )

        print(f"\n✅ {archivo_correlativo} (Respaldo) generado con éxito.")
        print(f"📁 Ubicación: {ruta_correlativa}")
        print(f"📊 Total de enlaces consolidados: {total_consolidado_miscelaneo}")
        print("📊 Totales por categoría (Respaldo):")
        for cat, count in totales_miscelaneo.most_common():
            print(f"   -> {cat.replace('_', ' ').title()}: {count} enlaces")
        
        # Opcional: Eliminar miscelaneo_otros.m3u de compilados/ después de generar el respaldo
        os.remove(ruta_miscelaneo)
        print(f"🗑️ Archivo temporal {os.path.basename(ruta_miscelaneo)} eliminado.")


# =========================================================================================
# 🧱 FUNCIÓN AUXILIAR DE CONSOLIDACIÓN
# =========================================================================================

def consolidar_lista(rutas_archivos: List[str], ruta_salida: str, es_miscelaneo: bool) -> Tuple[int, Counter]:
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
            
            # Si es el archivo de respaldo, forzamos un título genérico
            if es_miscelaneo:
                 titulo_visual = TITULOS_VISUALES.get(nombre_categoria_snake, "★ CANALES DE RESPALDO ★")
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
    limpiar_miscelaneo_caducado()
    generar_listas_finales()