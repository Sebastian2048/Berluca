import os
from collections import Counter
from typing import List, Optional

# 📦 Importaciones de configuración
from config import (
    CARPETA_ORIGEN, CARPETA_SALIDA, CLAVES_CATEGORIA, 
    contiene_exclusion, LIMITE_BLOQUES
)

# =========================================================================================
# 📦 FUNCIONES DE PARSEO (Se mantienen)
# =========================================================================================

def extraer_bloques_m3u(lineas: List[str]) -> List[List[str]]:
    # ... (código para extraer bloques)
    bloques = []
    buffer = []
    for linea in lineas:
        linea = linea.strip()
        if not linea or (linea.startswith("#") and not linea.startswith("#EXTINF")):
            continue
        if linea.startswith("#EXTINF"):
            buffer = [linea]
        elif buffer and linea.startswith("http"): 
            buffer.append(linea)
            bloques.append(buffer)
            buffer = []
        elif buffer: 
            buffer.append(linea)
            
    return [b for b in bloques if any(l.startswith("#EXTINF") for l in b) and any(l.startswith("http") for l in b)]

def extraer_nombre_canal(bloque: List[str]) -> str:
    # ... (código para extraer nombre)
    for linea in bloque:
        if linea.startswith("#EXTINF"):
            partes = linea.split(",", 1)
            if len(partes) > 1:
                return partes[1].strip()
    return "Sin nombre"

def extraer_url(bloque: List[str]) -> str:
    # ... (código para extraer URL)
    for linea in bloque:
        if linea.startswith("http"):
            return linea.strip()
    return ""

# =========================================================================================
# 💾 GUARDADO Y CLASIFICACIÓN
# =========================================================================================

def guardar_en_categoria(categoria: str, bloque: List[str]):
    """Guarda un bloque en su archivo de categoría correspondiente (solo EXTINF y URL)."""
    os.makedirs(CARPETA_ORIGEN, exist_ok=True)
    ruta = os.path.join(CARPETA_ORIGEN, f"{categoria}.m3u")

    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n\n")

    extinf = [l.strip() for l in bloque if l.startswith("#EXTINF")][0] if any(l.startswith("#EXTINF") for l in bloque) else None
    url = extraer_url(bloque)
    
    if extinf and url:
        with open(ruta, "a", encoding="utf-8", errors="ignore") as f:
            f.write(extinf + "\n")      
            f.write(url + "\n\n")    

def clasificacion_doble(bloque: List[str]) -> str:
    """Clasificación basada en CLAVES_CATEGORIA de config."""
    nombre = extraer_nombre_canal(bloque)
    nombre_lower = nombre.lower().replace("ñ", "n").replace(".", "")
    
    for categoria, claves in CLAVES_CATEGORIA.items():
        # Excluimos la categoría de desbordamiento en esta etapa
        if categoria == "peliculas_extras": continue 
        
        if any(clave in nombre_lower for clave in claves):
            return categoria
        
    return "sin_clasificar"


# =========================================================================================
# 🧠 BUCLE PRINCIPAL DE CLASIFICACIÓN (CORREGIDO CON LÓGICA DE OVERFLOW)
# =========================================================================================

def clasificar_enlaces():
    """
    Clasifica bloques, descartando 'sin_clasificar' y aplicando LIMITE_BLOQUES,
    con lógica de desbordamiento para películas.
    """
    
    # 🛑 CORRECCIÓN DE RUTA: Usa la ruta completa para encontrar el archivo descargado.
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    
    if not os.path.exists(ruta_temp):
        print(f"❌ Error: No se encontró el archivo TEMP_MATERIAL.m3u en {ruta_temp}.")
        return

    print("🧠 Iniciando clasificación y guardado de bloques...")

    with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques = extraer_bloques_m3u(lineas)
    totales_por_categoria = Counter()
    excluidos_por_contenido = 0
    total_bloques_procesados = len(bloques)
    descartados_por_limite = 0

    for bloque in bloques:
        nombre = extraer_nombre_canal(bloque)
        
        # 1. Exclusión por contenido (24/7, religioso, etc.)
        if contiene_exclusion(nombre):
            excluidos_por_contenido += 1
            continue

        categoria = clasificacion_doble(bloque)
        
        # 🛑 REGLA 1: Descartar sin_clasificar
        if "sin_clasificar" in categoria:
            totales_por_categoria[categoria] += 1
            continue 
            
        # 🛑 REGLA 2: Aplicar límite de bloques (Máximo 100)
        if totales_por_categoria[categoria] >= LIMITE_BLOQUES:
            
            # 🛑 IMPLEMENTACIÓN DE SUBCATEGORÍA DE DESBORDAMIENTO (OVERFLOW)
            if categoria == "peliculas_principal":
                categoria_final = "peliculas_extras"
                # Solo contamos como descarte si el overflow también se llena
                if totales_por_categoria[categoria_final] >= LIMITE_BLOQUES:
                    descartados_por_limite += 1
                    continue
                
                # Si el overflow no está lleno, lo usamos
                guardar_en_categoria(categoria_final, bloque)
                totales_por_categoria[categoria_final] += 1
                continue
            
            # Si no es Películas, descartamos
            descartados_por_limite += 1
            continue 

        # 3. Guardado en CARPETA_ORIGEN (Si pasa todos los filtros y límites)
        guardar_en_categoria(categoria, bloque)
        totales_por_categoria[categoria] += 1

    print(f"✅ Clasificación finalizada. Total bloques procesados: {total_bloques_procesados}")
    print(f"   -> Excluidos por contenido (religioso, etc.): {excluidos_por_contenido}")
    print(f"   -> Bloques no clasificados y descartados: {totales_por_categoria.get('sin_clasificar', 0)}")
    print(f"   -> Descartados por límite de {LIMITE_BLOQUES} canales: {descartados_por_limite}")
    
    categorias_generadas = [k for k in totales_por_categoria.keys() if k != 'sin_clasificar']
    categorias_finales = ", ".join(categorias_generadas)
    print(f"   -> Categorías generadas: {categorias_finales}")
    print(f"📁 Archivos clasificados en: {CARPETA_ORIGEN}/")
    
if __name__ == "__main__":
    clasificar_enlaces()