# servidor.py
import os
import shutil
from collections import defaultdict, Counter
from typing import List, Dict, Any
import logging
from datetime import datetime

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

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================================================================================
# ⚙️ GESTIÓN DE INVENTARIO
# =========================================================================================

def obtener_servidor_path(servidor_num: int) -> str:
    """Devuelve la ruta del archivo M3U para un número de servidor."""
    nombre_archivo = f"{NOMBRE_BASE_SERVIDOR}_{servidor_num:02d}.m3u"
    return os.path.join(CARPETA_SALIDA, nombre_archivo)

def obtener_inventario_servidor(servidor_num: int) -> Dict[str, List[Dict]]:
    """
    Carga los bloques de un servidor M3U existente en una estructura de inventario,
    asegurando que la metadata #ESTADO: esté presente para uso interno.
    """
    ruta_servidor = obtener_servidor_path(servidor_num)
    inventario = defaultdict(list)
    
    if not os.path.exists(ruta_servidor):
        return inventario
    
    with open(ruta_servidor, "r", encoding="utf-8", errors="ignore") as f:
        bloques_raw = extraer_bloques_m3u(f.readlines())
        
    for bloque in bloques_raw:
        # Usa la extracción y normalización
        categoria = extraer_categoria_del_bloque(bloque)
        url = extraer_url(bloque)
        
        if categoria and url:
            estado_extraido = extraer_estado(bloque) 
            
            # 1. Reconstruir el bloque para el inventario, asegurando la línea #ESTADO:
            bloque_interno = []
            bloque_interno.append(bloque[0]) # #EXTINF
            bloque_interno.append(f"#ESTADO:{estado_extraido}") 
            
            for linea in bloque[1:-1]:
                 if not linea.startswith("#ESTADO:"): # Evitar duplicados
                     bloque_interno.append(linea)
            
            bloque_interno.append(url) # URL al final

            # 2. Construir el canal enriquecido para el inventario
            inventario[categoria].append({
                "bloque": bloque_interno,
                "url": url,
                "nombre_limpio": extraer_nombre_canal(bloque).strip().lower().replace(" ", "").replace("ñ", "n"),
                "estado": estado_extraido,
                "categoria": categoria,
                "prioridad": PRIORIDAD_ESTADO.get(estado_extraido, 0) 
            })
        
    return inventario


def guardar_inventario_servidor(servidor_num: int, inventario: Dict[str, List[Dict]]):
    """
    Guarda el inventario modificado reescribiendo el archivo M3U del servidor.
    """
    ruta_servidor = obtener_servidor_path(servidor_num)
    temp_ruta = ruta_servidor + ".tmp"
    
    print(f"💾 Guardando {os.path.basename(ruta_servidor)}...")
    
    categorias_a_escribir = sorted(inventario.keys())
    
    with open(temp_ruta, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n")

        for nombre_categoria_snake in categorias_a_escribir:
            
            titulo_visual = TITULOS_VISUALES.get(nombre_categoria_snake, f"★ {nombre_categoria_snake.replace('_', ' ').upper()} ★")
            
            salida.write(f"\n# ====== {titulo_visual} ======\n")

            # Ordenar por Prioridad (Abierto > Dudoso > Fallido)
            canales_ordenados = sorted(inventario[nombre_categoria_snake], key=lambda c: c['prioridad'], reverse=True)
            
            for canal in canales_ordenados:
                
                # Escribir el bloque completo del canal (incluyendo #EXTINF, #ESTADO:, y la URL)
                for linea in canal['bloque']:
                    salida.write(linea.strip() + "\n")
                
                salida.write("\n") # Espacio entre bloques
                
    os.replace(temp_ruta, ruta_servidor)
    print(f"✅ {os.path.basename(ruta_servidor)} actualizado.")

def guardar_canales_excluidos(canales_excluidos: List[Dict]):
    """Guarda los canales dudosos/fallidos en un archivo para su re-auditoría futura."""
    if not canales_excluidos:
        # Si no hay canales excluidos, elimina el archivo anterior si existe.
        ruta_pendientes = os.path.join(CARPETA_SALIDA, "RP_Pendientes_Auditoria.m3u")
        if os.path.exists(ruta_pendientes):
            os.remove(ruta_pendientes)
        return
        
    ruta_pendientes = os.path.join(CARPETA_SALIDA, "RP_Pendientes_Auditoria.m3u")
    print(f"💾 Guardando {len(canales_excluidos)} canales excluidos/pendientes en {os.path.basename(ruta_pendientes)}...")
    
    with open(ruta_pendientes, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n")
        
        # Ordenar por Prioridad (para que los 'dudoso' queden primero)
        canales_excluidos.sort(key=lambda c: c['prioridad'], reverse=True)
        
        for canal in canales_excluidos:
            for linea in canal['bloque']:
                salida.write(linea.strip() + "\n")
            salida.write("\n")
            
    print(f"✅ Canales excluidos guardados para próxima revisión.")


# =========================================================================================
# 🧠 DISTRIBUCIÓN Y AUDITORÍA ESTRATÉGICA
# =========================================================================================

def auditar_y_balancear_servidores(max_servidores_final: int):
    """
    Recolecta todos los canales, los ordena por prioridad, los distribuye 
    respetando el LIMITE_BLOQUES_CATEGORIA (30), EXCLUYE DUDOSOS/FALLIDOS,
    y elimina los vacíos.
    """
    print("\n--- ⚖️ Iniciando Balanceo Estratégico (Exclusión de Dudosos/Fallidos) ---")
    
    canales_globales = []
    urls_vistas = set()
    
    # 1. Recolección Global (Lectura de todos los servidores y deduplicación)
    for i in range(1, MAX_SERVIDORES_BUSCAR + 100): 
        if os.path.exists(obtener_servidor_path(i)):
            inventario = obtener_inventario_servidor(i)
            for _, canales in inventario.items():
                for canal in canales:
                    if canal['url'] not in urls_vistas:
                        canales_globales.append(canal)
                        urls_vistas.add(canal['url'])

    print(f"✅ Total de canales únicos recolectados: {len(canales_globales)}")

    # 2. Ordenamiento Global por Prioridad (abierto > dudoso > fallido)
    canales_globales.sort(key=lambda c: c['prioridad'], reverse=True)
    
    # 3. Distribución Estratégica con Límite de 30 por Categoría
    
    inventarios_nuevos = defaultdict(lambda: defaultdict(list))
    canales_excluidos = [] # NUEVA LISTA para canales dudosos/fallidos
    servidor_actual = 1
    canales_asignados_por_categoria = {} 
    canales_totales_servidor = 0
    
    for canal in canales_globales:
        
        # 🛑 REGLA CLAVE: Excluir dudosos y fallidos de la asignación a servidores finales.
        if canal['estado'] not in ['abierto']:
            canales_excluidos.append(canal)
            continue # Salta al siguiente canal sin asignarlo
        
        categoria = canal['categoria']

        # Inicializar el contador para la categoría
        if categoria not in canales_asignados_por_categoria:
            canales_asignados_por_categoria[categoria] = 0
            
        # --- REGLAS DE DESPLAZAMIENTO ---
        
        limite_categoria_alcanzado = canales_asignados_por_categoria[categoria] >= LIMITE_BLOQUES_CATEGORIA
        limite_global_alcanzado = canales_totales_servidor >= LIMITE_BLOQUES_SERVIDOR_GLOBAL
        
        if limite_categoria_alcanzado or limite_global_alcanzado:
            
            # 1. Pasar al siguiente servidor
            servidor_actual += 1
            
            # 2. Reiniciar contadores para el nuevo servidor
            canales_asignados_por_categoria = {} 
            canales_totales_servidor = 0

            # 3. Verificar si se excedió el límite total de servidores
            if servidor_actual > max_servidores_final:
                logging.warning(f"⚠️ Se excedió el límite de {max_servidores_final} servidores. Canales restantes descartados.")
                # NO ES NECESARIO HACER BREAK, pues los canales 'abierto' deberían caber primero.
                # Si se llega aquí, es porque ya se llenaron los límites, y el canal se perderá.
                break 

            # 4. Inicializar la categoría en el nuevo servidor
            if categoria not in canales_asignados_por_categoria:
                 canales_asignados_por_categoria[categoria] = 0

        # --- Asignación del Canal ('abierto') ---
        
        # Asignar el canal y actualizar contadores
        inventarios_nuevos[servidor_actual][categoria].append(canal)
        canales_asignados_por_categoria[categoria] += 1
        canales_totales_servidor += 1

    
    # 4. Guardar los nuevos inventarios y ELIMINAR servidores vacíos/excedentes
    
    servidores_eliminados = 0
    
    for i in range(1, max_servidores_final + 100):
        ruta = obtener_servidor_path(i)
        
        if i in inventarios_nuevos and inventarios_nuevos[i]:
            guardar_inventario_servidor(i, inventarios_nuevos[i])
            
        elif os.path.exists(ruta):
             os.remove(ruta)
             servidores_eliminados += 1
             logging.info(f"🗑️ Servidor {i:02d} eliminado (vacío/excedente).")

    # 5. Guardar los canales excluidos (dudosos/fallidos)
    guardar_canales_excluidos(canales_excluidos)
    
    # 6. Generar la Guía de Contenido
    generar_guia_contenido(inventarios_nuevos, max_servidores_final)

    print(f"✅ Balanceo Estratégico finalizado. Se eliminaron {servidores_eliminados} archivos de servidor vacíos.")


# =========================================================================================
# 📝 GENERACIÓN DE GUÍA DE CONTENIDO
# =========================================================================================

def generar_guia_contenido(inventarios_finales: Dict[int, Dict[str, List[Dict]]], max_servidores_final: int):
    """
    Genera un archivo Markdown (GUIA_CONTENIDO.md) con el resumen 
    de categorías, conteo de canales y su estado (abierto/dudoso/fallido) 
    por cada servidor activo.
    """
    ruta_guia = os.path.join(CARPETA_SALIDA, "GUIA_CONTENIDO.md")
    
    print(f"\n--- 📝 Generando Guía de Contenido: {ruta_guia} ---")
    
    fecha_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    contenido = []
    contenido.append(f"# 📊 Guía de Contenido - Beluga IPTV\n")
    contenido.append(f"Última Actualización: **{fecha_actualizacion}**\n")
    contenido.append(f"--- \n")
    contenido.append(f"Esta guía detalla el contenido clasificado y balanceado en cada servidor, \n")
    contenido.append(f"aplicando un límite de **{LIMITE_BLOQUES_CATEGORIA} canales** por categoría. \n")
    contenido.append(f"**Nota:** Solo los canales con estado `abierto` se incluyen en los servidores finales.\n")
    
    servidores_activos = sorted(inventarios_finales.keys())
    
    if not servidores_activos:
        contenido.append("\n**⚠️ Advertencia:** No se encontraron servidores activos después del balanceo.\n")
    
    for num_servidor in servidores_activos:
        inventario = inventarios_finales[num_servidor]
        if not inventario:
             continue 

        servidor_total_canales = sum(len(canales) for canales in inventario.values())
        
        contenido.append(f"\n## 💻 Servidor {num_servidor:02d} (`RP_Servidor_{num_servidor:02d}.m3u`)\n")
        contenido.append(f"**Canales Totales:** {servidor_total_canales} (Todos `abierto` 🟢)\n")
        contenido.append("| Categoría | Canales (Total) |\n")
        contenido.append("| :--- | :---: |\n")
        
        categorias_ordenadas = sorted(inventario.keys())
        
        for categoria_snake in categorias_ordenadas:
            canales = inventario[categoria_snake]
            titulo_visual = TITULOS_VISUALES.get(categoria_snake, categoria_snake.replace('_', ' ').title())

            # Escribir fila de la tabla
            contenido.append(
                f"| {titulo_visual} "
                f"| {len(canales)} |\n"
            )

    try:
        with open(ruta_guia, "w", encoding="utf-8") as f:
            f.writelines(contenido)
        print(f"✅ Guía de Contenido generada exitosamente en {ruta_guia}")
    except Exception as e:
        logging.error(f"Error al escribir la Guía de Contenido: {e}")