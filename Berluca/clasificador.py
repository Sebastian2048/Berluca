# clasificador.py
import os
import re 
from typing import List, Dict, Optional, Tuple, Set
import logging
import requests 
from tqdm import tqdm 

# 📦 Importaciones de configuración y auxiliares
try:
    from config import (
        CLAVES_CATEGORIA, contiene_exclusion, CLAVES_NO_ESPANOL, 
        TITULOS_VISUALES, CLAVES_CATEGORIA_N2, PRIORIDAD_ESTADO, CARPETA_SALIDA
    )
    import auxiliar
    # Intentamos importar file_manager, si existe
    try:
        from file_manager import asegurar_archivo_categoria
    except ImportError:
        pass # No es crítico para este archivo
except ImportError as e:
    logging.error(f"Error al importar configuración/auxiliares: {e}")
    # Definiciones de fallback si falla la importación
    PRIORIDAD_ESTADO = {"abierto": 3, "dudoso": 2, "fallido": 1, "desconocido": 0}
    CARPETA_SALIDA = "Beluga"
    class auxiliar: 
        @staticmethod
        def extraer_nombre_canal(bloque): return "sin_nombre"
        @staticmethod
        def extraer_url(bloque): return ""
        @staticmethod
        def extraer_bloques_m3u(lineas): return []


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DEL CHECK REAL ---
TIMEOUT_CHECK = 15 
contador_verificacion = 0

# =========================================================================================
# 🧠 LÓGICA DE ASIGNACIÓN (CRÍTICO: FUNCIÓN CLASIFICAR_BLOQUE)
# =========================================================================================

def clasificar_bloque(bloque: List[str]) -> str:
    """Asigna una categoría a un bloque de canal."""
    nombre = auxiliar.extraer_nombre_canal(bloque).lower() 
    
    # 1. Búsqueda por CLAVES_CATEGORIA (Nivel 1)
    for categoria_clave, palabras in CLAVES_CATEGORIA.items():
        if categoria_clave in ["roll_over"]:
            continue
            
        if any(palabra in nombre for palabra in palabras):
            return categoria_clave

    # 2. Búsqueda por CLAVES_CATEGORIA_N2 (Nivel 2)
    for categoria_clave, palabras in CLAVES_CATEGORIA_N2.items():
        if any(palabra in nombre for palabra in palabras):
            return categoria_clave
            
    # 3. Categoría por defecto si no hay coincidencia
    return "roll_over"


def verificar_estado_canal(url: str, nombre: str, index: int) -> str:
    """Verificación de URL por HTTP para obtener el estado real (Quick Audit)."""
    global contador_verificacion
    contador_verificacion += 1

    if 'localhost' in url or '127.0.0.1' in url:
        return 'fallido' 

    # Prueba rápida HEAD
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, timeout=TIMEOUT_CHECK, headers=headers, allow_redirects=True)
        
        # Evaluación de estado HTTP
        if response.status_code in (200, 301, 302, 303, 307, 308):
            return 'abierto'
        else:
            return 'fallido'
            
    except requests.exceptions.RequestException:
        return 'dudoso'

# =========================================================================================
# 📝 FUNCIONES DE ESCRITURA Y CLASIFICACIÓN FINAL
# =========================================================================================

def clasificar_enlaces(rutas_lista_nueva: List[str], inventario_existente: Dict[str, List[str]]):
    """
    Combina el inventario existente, lo fusiona con TODAS las listas nuevas de las rutas 
    y ejecuta la Auditoría Rápida solo en los canales nuevos o fallidos.
    """
    
    # 1. Leer los bloques de TODAS las listas M3U nuevas y consolidar
    bloques_nuevos = []
    for ruta in rutas_lista_nueva:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            lineas_nueva = f.readlines()
        bloques_nuevos.extend(auxiliar.extraer_bloques_m3u(lineas_nueva)) 
    
    # 2. Compilar inventario total (Existente + Nuevo)
    inventario_total = inventario_existente.copy() 
    total_canales_nuevos = 0
    
    for bloque in bloques_nuevos:
        url = auxiliar.extraer_url(bloque) 
        if url and url not in inventario_total:
            
            extinf_line = [l for l in bloque if l.startswith("#EXTINF")][0]
            bloque_simple = [extinf_line, url] 
            inventario_total[url] = bloque_simple 
            total_canales_nuevos += 1
            
    bloques_para_auditar = list(inventario_total.values())

    print(f"Total de canales combinados (deduplicados) para auditar: {len(bloques_para_auditar)}")
    print(f"Canales nuevos añadidos de la(s) URL(s): {total_canales_nuevos}") 
    
    # 3. EJECUTAR LA LÓGICA DE CLASIFICACIÓN Y AUDITORÍA
    bloques_enriquecidos = []
    
    for i, bloque_completo in tqdm(enumerate(bloques_para_auditar), 
                                desc="Clasificando y Auditando Rápido", 
                                total=len(bloques_para_auditar)):
        
        url = auxiliar.extraer_url(bloque_completo) 
        nombre = auxiliar.extraer_nombre_canal(bloque_completo) 
        
        estado_base = "desconocido"
        if len(bloque_completo) > 1 and bloque_completo[1].startswith("#ESTADO:"):
            estado_base = bloque_completo[1].split(':')[1].strip().lower()

        categoria = clasificar_bloque(bloque_completo)

        # Prioridad de Auditoría: No re-auditar canales 'abierto' existentes.
        if estado_base == "abierto":
            estado_final = "abierto"
        else:
            estado_final = verificar_estado_canal(url, nombre, i)
        
        # 4. Enriquecer el bloque para el resumen final
        extinf_line = [l for l in bloque_completo if l.startswith("#EXTINF")][0]
        
        titulo_visual = TITULOS_VISUALES.get(categoria, f"★ {categoria.replace('_', ' ').upper()} ★")
        extinf_line_mod = re.sub(r'group-title=\"[^\"]*\"', f'group-title=\"{titulo_visual}\"', extinf_line)
        if 'group-title' not in extinf_line_mod:
            extinf_line_mod = extinf_line_mod.replace(f",{nombre}", f' group-title="{titulo_visual}",{nombre}')

        # El bloque final para el inventario (Resumen_Auditoria.m3u):
        bloques_enriquecidos.append({
            "bloque": [extinf_line_mod, f"#ESTADO:{estado_final}", url], 
            "url": url,
            "nombre_limpio": nombre.strip().lower().replace(" ", "").replace("ñ", "n"),
            "categoria": categoria,
            "estado": estado_final
        })
        
    # 5. Escribir el resumen de auditoría
    RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")
    
    print(f"\n--- 💾 Escribiendo Resumen de Auditoría Rápida: {RUTA_RESUMEN_AUDITORIA} ---")
    
    with open(RUTA_RESUMEN_AUDITORIA, "w", encoding="utf-8", errors="ignore") as f:
        f.write("#EXTM3U\n")
        canales_totales_resumen = 0
        for canal in bloques_enriquecidos:
            f.write("\n".join(canal["bloque"]) + "\n")
            canales_totales_resumen += 1

    print(f"✅ Archivo de Resumen de Auditoría (Quick Audit) generado con {canales_totales_resumen} canales.")
    print("✅ Consolidación y Quick Audit finalizada. Archivo de resumen listo para auditoría lenta.")