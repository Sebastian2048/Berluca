# servidor.py
import os
import shutil
from collections import defaultdict, Counter
from typing import List, Dict, Any
import logging
from datetime import datetime
import glob 
import re 
from tqdm import tqdm # Importamos tqdm

# 📦 Importaciones de configuración y auxiliares
try:
    from config import (
        CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR, LIMITE_BLOQUES_CATEGORIA,
        LIMITE_BLOQUES_SERVIDOR_GLOBAL, PRIORIDAD_ESTADO, TITULOS_VISUALES, 
        MAX_SERVIDORES_BUSCAR, LOGO_DEFAULT
    )
    from auxiliar import (
        extraer_bloques_m3u, extraer_url, extraer_nombre_canal, 
        extraer_estado, extraer_prioridad, extraer_categoria_del_bloque
    )
except ImportError as e:
    logging.error(f"Error al importar módulos en servidor.py: {e}")
    CARPETA_SALIDA = "Beluga"
    NOMBRE_BASE_SERVIDOR = "RP_Servidor"
    LIMITE_BLOQUES_CATEGORIA = 30
    LIMITE_BLOQUES_SERVIDOR_GLOBAL = 800
    PRIORIDAD_ESTADO = {"abierto": 3, "dudoso": 2, "fallido": 1, "desconocido": 0}
    TITULOS_VISUALES = {}
    MAX_SERVIDORES_BUSCAR = 40
    LOGO_DEFAULT = ""

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================================================================================
# ⚙️ GESTIÓN DE INVENTARIO
# =========================================================================================

def obtener_servidor_path(servidor_num: int) -> str:
    """Devuelve la ruta del archivo M3U para un número de servidor."""
    nombre_archivo = f"{NOMBRE_BASE_SERVIDOR}_{servidor_num:02d}.m3u"
    return os.path.join(CARPETA_SALIDA, nombre_archivo)

def obtener_inventario_servidor(servidor_num: int) -> Dict[str, List[Dict[str, Any]]]:
    """Lee un archivo RP_Servidor_XX.m3u y devuelve un diccionario de bloques enriquecidos."""
    ruta = obtener_servidor_path(servidor_num)
    inventario = defaultdict(list)
    if not os.path.exists(ruta):
        return inventario

    try:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
        
        bloques = extraer_bloques_m3u(lineas)
        
        for bloque in bloques:
            url = extraer_url(bloque)
            if not url: continue

            nombre = extraer_nombre_canal(bloque)
            estado = extraer_estado(bloque)
            prioridad = PRIORIDAD_ESTADO.get(estado, 0)
            categoria = extraer_categoria_del_bloque(bloque)
            
            inventario[categoria].append({
                "bloque": bloque, 
                "url": url,
                "nombre_limpio": nombre.strip().lower().replace(" ", "").replace("ñ", "n"),
                "categoria": categoria,
                "estado": estado,
                "prioridad": prioridad
            })
            
    except Exception as e:
        logging.error(f"Error al leer el inventario del servidor {servidor_num}: {e}")
        
    return inventario


def guardar_inventario_servidor(servidor_num: int, inventario: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Escribe el inventario de vuelta al archivo de servidor."""
    ruta = obtener_servidor_path(servidor_num)
    
    try:
        with open(ruta, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n")
            for categoria in inventario:
                for canal in inventario[categoria]:
                    f.write("\n".join(canal["bloque"]) + "\n")
        return True
    except Exception as e:
        logging.error(f"Error al guardar el servidor {servidor_num}: {e}")
        return False


def _limpiar_archivos_servidor():
    """CRÍTICO: Elimina todos los archivos RP_Servidor_XX.m3u de la carpeta de salida."""
    patron = os.path.join(CARPETA_SALIDA, f"{NOMBRE_BASE_SERVIDOR}_*.m3u")
    archivos = glob.glob(patron)
    
    if archivos:
        logging.info(f"🧹 Eliminando {len(archivos)} archivos de servidores antiguos para el re-balanceo.")
        for archivo in archivos:
            try:
                os.remove(archivo)
            except Exception as e:
                logging.error(f"❌ Error al eliminar {os.path.basename(archivo)}: {e}")


def compilar_inventario_existente(max_servers: int) -> Dict[str, List[str]]:
    """Lee todos los archivos de servidor existentes y devuelve un diccionario de bloques de canal."""
    inventario_compilado: Dict[str, List[str]] = {}
    
    for i in range(1, max_servers + 1):
        ruta = obtener_servidor_path(i)
        if os.path.exists(ruta):
            inventario_servidor = obtener_inventario_servidor(i)
            
            for categoria in inventario_servidor:
                for canal in inventario_servidor[categoria]:
                    url = canal['url']
                    if not url:
                        continue
                        
                    extinf_line = [l for l in canal['bloque'] if l.startswith("#EXTINF")][0]
                    
                    # Bloque final para la auditoría (se asumirá estado 'abierto')
                    bloque_final = [
                        extinf_line, 
                        "#ESTADO:abierto", 
                        url
                    ] 
                    
                    if url not in inventario_compilado:
                        inventario_compilado[url] = bloque_final
                
    logging.info(f"💾 Compilado inventario existente de {len(inventario_compilado)} canales de servidores anteriores.")
    return inventario_compilado

# =========================================================================================
# ⚖️ BALANCEO Y DISTRIBUCIÓN
# =========================================================================================

def auditar_y_balancear_servidores(max_servidores_a_buscar: int):
    """
    Lee el archivo de resumen de auditoría final, distribuye los canales 'abierto' 
    en servidores, aplicando límites y forzando el inicio desde el Servidor 01.
    """
    
    # 1. PASO CRÍTICO: Limpiar los archivos finales ANTES de escribir los nuevos.
    _limpiar_archivos_servidor()
    
    RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")
    
    if not os.path.exists(RUTA_RESUMEN_AUDITORIA):
        logging.warning("⚠️ No se encontró el archivo de resumen de auditoría. Abortando balanceo.")
        return

    # A) Cargar inventario completo desde el resumen
    with open(RUTA_RESUMEN_AUDITORIA, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()
        
    bloques_enriquecidos = []
    bloques_excluidos = []
    
    for bloque in extraer_bloques_m3u(lineas):
        url = extraer_url(bloque)
        if not url: continue
            
        estado = extraer_estado(bloque)
        prioridad = PRIORIDAD_ESTADO.get(estado, 0)
        
        canal = {
            "bloque": bloque, 
            "url": url,
            "categoria": extraer_categoria_del_bloque(bloque),
            "estado": estado,
            "prioridad": prioridad
        }
        
        if estado == "abierto":
            bloques_enriquecidos.append(canal)
        else:
            bloques_excluidos.append(canal)

    # Ordenar por prioridad y luego por categoría
    bloques_enriquecidos.sort(key=lambda x: (x['prioridad'], x['categoria']), reverse=True)

    logging.info(f"Inventario general cargado: {len(bloques_enriquecidos)} canales 'abierto'.")
    
    # B) Iniciar Balanceo Estratégico (Distribución)
    print("\n--- ⚖️ Iniciando Balanceo Estratégico (Prioridad y Límite) ---")

    servidores_activos = defaultdict(lambda: {
        'inventario': defaultdict(list), 
        'conteo_global': 0
    })
    # Empezar siempre por el Servidor 1
    servidor_actual_num = 1
    
    for canal in tqdm(bloques_enriquecidos, desc="Asignando canales por Prioridad y Límite"):
        
        categoria = canal['categoria']
        
        while True:
            servidor = servidores_activos[servidor_actual_num]
            
            conteo_cat = len(servidor['inventario'][categoria])
            conteo_global = servidor['conteo_global']
            
            if (conteo_cat < LIMITE_BLOQUES_CATEGORIA) and \
               (conteo_global < LIMITE_BLOQUES_SERVIDOR_GLOBAL):
                
                servidor['inventario'][categoria].append(canal)
                servidor['conteo_global'] += 1
                break 
            else:
                servidor_actual_num += 1

    # C) Guardar servidores
    servidores_generados = 0
    
    for num_servidor in sorted(servidores_activos.keys()):
        inventario = servidores_activos[num_servidor]['inventario']
        conteo_global = servidores_activos[num_servidor]['conteo_global']
        
        if conteo_global > 0:
            if guardar_inventario_servidor(num_servidor, inventario):
                servidores_generados += 1
            
    # D) Guardar canales dudosos/fallidos (Excluidos)
    RUTA_EXCLUIDOS = os.path.join(CARPETA_SALIDA, "RP_Canales_Excluidos_Audit.m3u")
    if bloques_excluidos:
        logging.warning(f"⚠️ {len(bloques_excluidos)} canales dudosos/fallidos guardados en: {RUTA_EXCLUIDOS}")
        with open(RUTA_EXCLUIDOS, "w", encoding="utf-8", errors="ignore") as f:
            f.write("#EXTM3U\n")
            for canal in bloques_excluidos:
                 f.write("\n".join(canal["bloque"]) + "\n")
    else:
        if os.path.exists(RUTA_EXCLUIDOS):
            os.remove(RUTA_EXCLUIDOS)

    # E) Generar Guía de Contenido
    generar_guia_contenido(servidores_activos)
    
    print(f"✅ Balanceo Estratégico finalizado. Servidores generados: {servidores_generados}.")


def generar_guia_contenido(servidores_activos: Dict[int, Any]):
    """Genera el archivo Markdown con el resumen de contenido por servidor."""
    
    RUTA_GUIA = os.path.join(CARPETA_SALIDA, "RP_Guia_Contenido.md")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    contenido = [
        "# 📊 Guía de Contenido - Beluga IPTV",
        f"Última Actualización: **{now}**",
        "---",
        f"Aplicando un límite de **{LIMITE_BLOQUES_CATEGORIA} canales** por categoría.",
        ""
    ]
    
    servidores_activos_keys = sorted(servidores_activos.keys())
    
    if not servidores_activos_keys:
        contenido.append("\n**⚠️ Advertencia:** No se encontraron servidores activos después del balanceo.\n")
    
    for num_servidor in servidores_activos_keys:
        inventario = servidores_activos[num_servidor]['inventario']
        if not inventario:
             continue 

        servidor_total_canales = sum(len(canales) for canales in inventario.values())
        
        contenido.append(f"\n## 💻 Servidor {num_servidor:02d} (`{NOMBRE_BASE_SERVIDOR}_{num_servidor:02d}.m3u`)\n")
        contenido.append(f"**Canales Totales:** {servidor_total_canales} (Todos `abierto` 🟢)\n")
        contenido.append("| Categoría | Canales (Total) |\n")
        contenido.append("| :--- | :---: |\n")
        
        categorias_ordenadas = sorted(inventario.keys())
        
        for categoria_snake in categorias_ordenadas:
            canales = inventario[categoria_snake]
            titulo_visual = TITULOS_VISUALES.get(categoria_snake, categoria_snake.replace('_', ' ').title())

            contenido.append(
                f"| {titulo_visual} "
                f"| {len(canales)} |\n"
            )

    try:
        with open(RUTA_GUIA, "w", encoding="utf-8", errors="ignore") as f:
            f.write("\n".join(contenido))
        logging.info(f"📄 Guía de Contenido generada en: {RUTA_GUIA}")
    except Exception as e:
        logging.error(f"Error al generar la guía de contenido: {e}")