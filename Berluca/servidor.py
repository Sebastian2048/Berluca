# servidor.py
import os
import glob
from collections import defaultdict, Counter
import re
from typing import List, Dict, Tuple, Set, Any
import logging

# 📦 Importaciones de configuración y auxiliares
try:
    from config import (
        CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR, LIMITE_BLOQUES_CATEGORIA,
        LIMITE_BLOQUES_SERVIDOR_GLOBAL, PRIORIDAD_ESTADO, TITULOS_VISUALES, 
        LOGO_DEFAULT, MAX_SERVIDORES_BUSCAR
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
        categoria = extraer_categoria_del_bloque(bloque)
        
        if categoria:
            # 1. Extraer el estado (esto ahora puede ser "desconocido" si se eliminó de la escritura)
            estado_extraido = extraer_estado(bloque) 
            
            # 2. Reconstruir el bloque para el inventario, asegurando la línea #ESTADO:
            bloque_interno = []
            
            # Reconstruir líneas (ignorando estados anteriores que puedan existir)
            for linea in bloque:
                if not linea.startswith("#ESTADO:"):
                    bloque_interno.append(linea)

            # Insertar la línea de estado basada en lo que extrajimos (será 'desconocido' si no existía)
            # La insertamos después de #EXTINF, que debe ser el índice 0 del bloque_interno
            bloque_interno.insert(1, f"#ESTADO:{estado_extraido}") 

            # 3. Construir el canal enriquecido para el inventario
            inventario[categoria].append({
                "bloque": bloque_interno, # <-- Usamos el bloque reconstruido con #ESTADO:
                "url": extraer_url(bloque),
                "nombre_limpio": extraer_nombre_canal(bloque).strip().lower().replace(" ", "").replace("ñ", "n"),
                "estado": estado_extraido,
                "categoria": categoria,
                "prioridad": PRIORIDAD_ESTADO.get(estado_extraido, 0) # Usamos el estado extraído
            })
        
    return inventario


def guardar_inventario_servidor(servidor_num: int, inventario: Dict[str, List[Dict]]):
    """
    Guarda el inventario modificado reescribiendo el archivo M3U del servidor.
    Se asegura de escribir solo #EXTINF y la URL (Formato robusto para Movian).
    """
    ruta_servidor = obtener_servidor_path(servidor_num)
    
    print(f"💾 Guardando {os.path.basename(ruta_servidor)}...")
    
    categorias_a_escribir = sorted(inventario.keys())
    
    with open(ruta_servidor, "w", encoding="utf-8", errors="ignore") as salida:
        salida.write("#EXTM3U\n\n")

        for nombre_categoria_snake in categorias_a_escribir:
            
            titulo_visual = TITULOS_VISUALES.get(nombre_categoria_snake, f"★ {nombre_categoria_snake.replace('_', ' ').upper()} ★")
            
            salida.write(f"\n# ====== {titulo_visual} ======\n\n")

            # Ordenar por Prioridad (Abierto > Dudoso > Fallido)
            canales_ordenados = sorted(inventario[nombre_categoria_snake], key=lambda c: c['prioridad'], reverse=True)
            
            for canal in canales_ordenados:
                
                extinf_escrito = False
                url_escrita = False

                for linea in canal['bloque']:
                    linea = linea.strip()
                    
                    # 1. Escribir la línea #EXTINF (que está en índice 0)
                    if linea.startswith("#EXTINF") and not extinf_escrito:
                        salida.write(linea + "\n")
                        extinf_escrito = True
                        
                    # 2. Escribir la URL (la última línea, sin #)
                    elif not linea.startswith("#") and not url_escrita:
                        salida.write(linea + "\n")
                        url_escrita = True
                
                # Esto asegura un formato estricto: #EXTINF... \n URL \n \n
                if extinf_escrito and url_escrita:
                    salida.write("\n") # Espacio entre bloques
                
    print(f"✅ {os.path.basename(ruta_servidor)} actualizado.")


# =========================================================================================
# 🧠 DISTRIBUCIÓN Y AUDITORÍA
# =========================================================================================

def distribuir_por_servidor(bloques_enriquecidos: List[Dict]):
    """
    Asigna bloques a servidores basado en: 1. Categoría, 2. Límite (60), 3. Prioridad, 4. Balanceo.
    """
    
    bloques_entrantes = sorted(bloques_enriquecidos, key=lambda b: PRIORIDAD_ESTADO.get(b['estado'], 0), reverse=True)
    
    bloques_pendientes = list(bloques_entrantes)
    servidor_actual = 1
    
    print(f"\n--- 🌐 Iniciando Distribución en {MAX_SERVIDORES_BUSCAR} Servidores ---")

    while bloques_pendientes and servidor_actual <= MAX_SERVIDORES_BUSCAR + 1:
        
        print(f"\nProcesando Servidor {servidor_actual:02d}...")
        inventario_servidor = obtener_inventario_servidor(servidor_actual)
        
        bloques_desplazados = []
        nuevos_pendientes = [] 
        
        pendientes_por_categoria = defaultdict(list)
        for bloque in bloques_pendientes:
            pendientes_por_categoria[bloque['categoria']].append(bloque) 
            
        
        for categoria in sorted(pendientes_por_categoria.keys()):
            
            canales_categoria = inventario_servidor[categoria][:] 
            
            for nuevo_canal in pendientes_por_categoria[categoria]:
                
                url = nuevo_canal['url']
                prioridad_nueva = PRIORIDAD_ESTADO.get(nuevo_canal['estado'], 0)
                nombre_limpio = nuevo_canal['nombre_limpio']

                # 4. Regla de Balanceo (Deduplicación)
                if any(c['nombre_limpio'] == nombre_limpio for c in canales_categoria):
                    nuevos_pendientes.append(nuevo_canal)
                    continue

                # 5. Regla de Capacidad (Límite 60)
                if len(canales_categoria) < LIMITE_BLOQUES_CATEGORIA:
                    nuevo_canal['prioridad'] = prioridad_nueva 
                    canales_categoria.append(nuevo_canal) 
                    
                else:
                    # 6. Regla de Prioridad/Desplazamiento
                    canal_a_desplazar = min(canales_categoria, key=lambda c: c['prioridad']) 
                    
                    if prioridad_nueva > canal_a_desplazar['prioridad']:
                        
                        canales_categoria.remove(canal_a_desplazar)
                        nuevo_canal['prioridad'] = prioridad_nueva 
                        canales_categoria.append(nuevo_canal)
                        
                        bloques_desplazados.append(canal_a_desplazar)
                        
                    else:
                        nuevos_pendientes.append(nuevo_canal)
            
            inventario_servidor[categoria] = canales_categoria

        guardar_inventario_servidor(servidor_actual, inventario_servidor)
        
        bloques_pendientes = nuevos_pendientes + bloques_desplazados
        
        servidor_actual += 1 

    if bloques_pendientes:
        print(f"\n⚠️ {len(bloques_pendientes)} bloques no pudieron ser asignados en la distribución inicial.")


def auditar_y_balancear_servidores(max_servidores_a_auditar: int):
    """
    Verifica el límite global de bloques por servidor (2000) y desplaza el exceso
    a un buffer para re-distribución.
    """
    print("\n--- ⚖️ Iniciando Auditoría y Balanceo de Servidores (Límite Global) ---")
    
    bloques_excedentes = []
    
    servidor_num = 1
    
    # Bucle para auditar todos los servidores que se hayan creado 
    while True:
        ruta_servidor = obtener_servidor_path(servidor_num)
        
        # Parar la búsqueda si el archivo no existe y hemos pasado el número de servidores base
        if not os.path.exists(ruta_servidor) and servidor_num > max_servidores_a_auditar + 10:
            break
        
        if not os.path.exists(ruta_servidor) and servidor_num <= max_servidores_a_auditar + 10:
            servidor_num += 1
            continue

        inventario = obtener_inventario_servidor(servidor_num)
        total_bloques_servidor = sum(len(canales) for canales in inventario.values())
        
        if total_bloques_servidor > LIMITE_BLOQUES_SERVIDOR_GLOBAL:
            print(f"⚠️ Servidor {servidor_num:02d} excede el límite ({total_bloques_servidor} > {LIMITE_BLOQUES_SERVIDOR_GLOBAL}). Desplazando...")
            
            exceso = total_bloques_servidor - LIMITE_BLOQUES_SERVIDOR_GLOBAL
            
            conteo_por_categoria = {cat: len(canales) for cat, canales in inventario.items()}
            categorias_ordenadas = sorted(conteo_por_categoria.items(), key=lambda item: item[1], reverse=True)
            
            bloques_movidos_servidor = 0
            
            for categoria, _ in categorias_ordenadas:
                if bloques_movidos_servidor >= exceso:
                    break
                    
                canales_categoria = inventario[categoria]
                
                canales_a_mover = min(
                    len(canales_categoria), 
                    exceso - bloques_movidos_servidor
                )
                
                if canales_a_mover > 0:
                    # Mover los de menor prioridad (Fallidos) primero
                    canales_a_mover_lista = sorted(canales_categoria, key=lambda c: c['prioridad'], reverse=False)[:canales_a_mover]
                    
                    for canal in canales_a_mover_lista:
                        canales_categoria.remove(canal)
                        bloques_excedentes.append(canal)
                        bloques_movidos_servidor += 1
                        
                inventario[categoria] = canales_categoria 
            
            guardar_inventario_servidor(servidor_num, inventario)

        servidor_num += 1


    # 2. Redistribuir los bloques excedentes
    if bloques_excedentes:
        print(f"\n🔄 Redistribuyendo {len(bloques_excedentes)} bloques excedentes a nuevos servidores...")
        
        # Ordenamos por prioridad (Abierto > Dudoso > Fallido) para que los Fallidos se asignen al final
        bloques_excedentes = sorted(bloques_excedentes, key=lambda b: PRIORIDAD_ESTADO.get(b['estado'], 0), reverse=True)
        
        distribuir_excedentes(bloques_excedentes, servidor_num)
        
    print("✅ Auditoría de límite global finalizada.")


def distribuir_excedentes(bloques_pendientes: List[Dict], servidor_inicial: int):
    """
    Distribuye bloques en servidores nuevos o existentes con espacio,
    respetando el LIMITE_BLOQUES_SERVIDOR_GLOBAL.
    """
    servidor_actual = servidor_inicial 
    
    while bloques_pendientes:
        
        inventario_servidor = obtener_inventario_servidor(servidor_actual)
        nuevos_pendientes = []
        bloques_asignados_count = 0

        total_bloques_servidor = sum(len(canales) for canales in inventario_servidor.values())
        
        # Si el servidor ya está lleno, pasa al siguiente
        if total_bloques_servidor >= LIMITE_BLOQUES_SERVIDOR_GLOBAL:
            servidor_actual += 1
            continue
            
        print(f"🔄 Asignando a Servidor {servidor_actual:02d} ({total_bloques_servidor} / {LIMITE_BLOQUES_SERVIDOR_GLOBAL})...")

        for nuevo_canal in bloques_pendientes:
            
            # Si el servidor se llenó durante esta iteración, el resto queda pendiente
            if total_bloques_servidor >= LIMITE_BLOQUES_SERVIDOR_GLOBAL:
                nuevos_pendientes.append(nuevo_canal) 
                continue
            
            categoria = nuevo_canal['categoria']
            canales_categoria = inventario_servidor[categoria]
            nombre_limpio = nuevo_canal['nombre_limpio']
            
            # Chequeos de deduplicación y límite de categoría (60)
            if any(c['nombre_limpio'] == nombre_limpio for c in canales_categoria) or \
               len(canales_categoria) >= LIMITE_BLOQUES_CATEGORIA:
                nuevos_pendientes.append(nuevo_canal)
                continue

            # Asignar el canal
            nuevo_canal['prioridad'] = PRIORIDAD_ESTADO.get(nuevo_canal['estado'], 0) 
            canales_categoria.append(nuevo_canal)
            inventario_servidor[categoria] = canales_categoria
            total_bloques_servidor += 1
            bloques_asignados_count += 1
            
        
        if bloques_asignados_count > 0:
            guardar_inventario_servidor(servidor_actual, inventario_servidor)
        
        bloques_pendientes = nuevos_pendientes 

        servidor_actual += 1

    if bloques_pendientes:
        print(f"\n⚠️ {len(bloques_pendientes)} bloques no pudieron ser re-asignados y quedaron en el roll-over final.")