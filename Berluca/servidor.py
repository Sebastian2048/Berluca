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
        CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR, LIMITE_BLOQUES_SERVIDOR, 
        PRIORIDAD_ESTADO, TITULOS_VISUALES, LOGO_DEFAULT, MAX_SERVIDORES_BUSCAR
    )
    from auxiliar import (
        extraer_bloques_m3u, extraer_url, extraer_nombre_canal, 
        extraer_estado, extraer_prioridad, extraer_categoria_del_bloque
    )
except ImportError as e:
    # Este error debe manejarse en el main.py
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
    Carga los bloques de un servidor M3U existente en una estructura de inventario.
    
    CORRECCIÓN CRÍTICA: Asegura que cada canal cargado tenga la clave 'categoria'.
    """
    ruta_servidor = obtener_servidor_path(servidor_num)
    inventario = defaultdict(list)
    
    if not os.path.exists(ruta_servidor):
        return inventario
    
    with open(ruta_servidor, "r", encoding="utf-8", errors="ignore") as f:
        bloques = extraer_bloques_m3u(f.readlines())
        
    for bloque in bloques:
        categoria = extraer_categoria_del_bloque(bloque)
        
        if categoria:
            inventario[categoria].append({
                "bloque": bloque,
                "url": extraer_url(bloque),
                "nombre_limpio": extraer_nombre_canal(bloque).strip().lower().replace(" ", "").replace("ñ", "n"),
                "estado": extraer_estado(bloque),
                "categoria": categoria,  # <--- CORRECCIÓN AÑADIDA
                "prioridad": extraer_prioridad(bloque) 
            })
        
    return inventario

def guardar_inventario_servidor(servidor_num: int, inventario: Dict[str, List[Dict]]):
    """Guarda el inventario modificado reescribiendo el archivo M3U del servidor."""
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
                # Escribir las líneas del bloque
                for linea in canal['bloque']:
                    # Omitimos escribir la línea #ESTADO:X, solo es metadata interna
                    if not linea.startswith("#ESTADO:"):
                        salida.write(linea + "\n")
                salida.write("\n") # Espacio entre bloques
                
    print(f"✅ {os.path.basename(ruta_servidor)} actualizado.")


# =========================================================================================
# 🧠 DISTRIBUCIÓN PRINCIPAL
# =========================================================================================

def distribuir_por_servidor(bloques_enriquecidos: List[Dict]):
    """
    Asigna bloques a servidores basado en: 1. Categoría, 2. Límite, 3. Prioridad, 4. Balanceo.
    """
    
    # Pre-procesar los bloques entrantes para priorizar los de mejor calidad
    bloques_entrantes = sorted(bloques_enriquecidos, key=lambda b: PRIORIDAD_ESTADO.get(b['estado'], 0), reverse=True)
    
    bloques_pendientes = list(bloques_entrantes)
    servidor_actual = 1
    
    print(f"\n--- 🌐 Iniciando Distribución en {MAX_SERVIDORES_BUSCAR} Servidores ---")

    while bloques_pendientes and servidor_actual <= MAX_SERVIDORES_BUSCAR + 1:
        
        print(f"\nProcesando Servidor {servidor_actual:02d}...")
        inventario_servidor = obtener_inventario_servidor(servidor_actual)
        
        bloques_desplazados = []
        bloques_asignados_en_servidor = set()

        nuevos_pendientes = [] 
        
        # Agrupar los pendientes por categoría para procesar por grupos
        pendientes_por_categoria = defaultdict(list)
        for bloque in bloques_pendientes:
            # Línea 121: Ahora los bloques desplazados tienen la clave 'categoria'
            pendientes_por_categoria[bloque['categoria']].append(bloque) 
            
        
        for categoria in sorted(pendientes_por_categoria.keys()):
            
            canales_categoria = inventario_servidor[categoria][:] 
            
            for nuevo_canal in pendientes_por_categoria[categoria]:
                
                url = nuevo_canal['url']
                prioridad_nueva = PRIORIDAD_ESTADO.get(nuevo_canal['estado'], 0)
                nombre_limpio = nuevo_canal['nombre_limpio']

                # 4. Regla de Balanceo (Deduplicación por Servidor)
                if any(c['nombre_limpio'] == nombre_limpio for c in canales_categoria):
                    nuevos_pendientes.append(nuevo_canal)
                    continue

                # 5. Regla de Capacidad (Límite 60)
                if len(canales_categoria) < LIMITE_BLOQUES_SERVIDOR:
                    # Ingreso directo: Hay espacio.
                    
                    # Asegurar que el nuevo canal tenga la clave 'prioridad'
                    nuevo_canal['prioridad'] = prioridad_nueva 
                    
                    canales_categoria.append(nuevo_canal) 
                    bloques_asignados_en_servidor.add(url)
                    
                else:
                    # 6. Regla de Prioridad/Desplazamiento
                    
                    # Buscar el canal con la prioridad más baja (ahora seguro por la corrección anterior)
                    canal_a_desplazar = min(canales_categoria, key=lambda c: c['prioridad']) 
                    
                    if prioridad_nueva > canal_a_desplazar['prioridad']:
                        
                        # El canal entrante es de mejor calidad: Desplazar al de peor calidad
                        canales_categoria.remove(canal_a_desplazar)
                        
                        # Asegurar que el nuevo canal tenga la clave 'prioridad'
                        nuevo_canal['prioridad'] = prioridad_nueva 
                        
                        canales_categoria.append(nuevo_canal)
                        
                        # Añadir el bloque desplazado a la lista para re-procesar en el siguiente servidor
                        bloques_desplazados.append(canal_a_desplazar)
                        bloques_asignados_en_servidor.add(url)
                        
                    else:
                        # El nuevo canal no tiene prioridad suficiente para desplazar, pasa al siguiente.
                        nuevos_pendientes.append(nuevo_canal)
            
            # Actualizar la categoría en el inventario
            inventario_servidor[categoria] = canales_categoria

        # 7. Guardar el estado del servidor actual
        guardar_inventario_servidor(servidor_actual, inventario_servidor)
        
        # 8. Mover bloques desplazados y no asignados al inicio de la siguiente iteración
        bloques_pendientes = nuevos_pendientes + bloques_desplazados
        
        servidor_actual += 1 # Ir al siguiente servidor

    if bloques_pendientes:
        print(f"\n⚠️ {len(bloques_pendientes)} bloques no pudieron ser asignados a ningún servidor (Roll-Over).")