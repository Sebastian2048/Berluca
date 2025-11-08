# actualizar_servidores.py
import os
import re
from typing import Dict, List, Any
import logging

# 📦 Importaciones de módulos locales
try:
    from config import CARPETA_SALIDA, MAX_SERVIDORES_BUSCAR
    from auxiliar import extraer_bloques_m3u, extraer_url
    from servidor import (
        obtener_servidor_path, guardar_inventario_servidor, 
        obtener_inventario_servidor, auditar_y_balancear_servidores
    )
except ImportError as e:
    logging.error(f"Error al importar módulos en actualizar_servidores.py: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN ---
RUTA_RESUMEN_AUDITORIA = os.path.join(CARPETA_SALIDA, "RP_Resumen_Auditoria.m3u")

def cargar_estados_auditados() -> Dict[str, str]:
    """Carga un mapa de URL -> Estado (abierto/dudoso/fallido) desde el resumen."""
    if not os.path.exists(RUTA_RESUMEN_AUDITORIA):
        logging.error(f"❌ Error: No se encontró el archivo de auditoría: {RUTA_RESUMEN_AUDITORIA}")
        print("Ejecuta 'auditor_conectividad.py' primero.")
        return {}

    estados = {}
    
    with open(RUTA_RESUMEN_AUDITORIA, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    bloques_auditados = extraer_bloques_m3u(lineas)
    
    for bloque in bloques_auditados:
        url = extraer_url(bloque)
        
        # El #EXTINF modificado en la auditoría tiene el estado real
        extinf_line = bloque[0]
        match = re.search(r'#ESTADO_AUDITORIA:(\w+)', extinf_line)
        
        if url and match:
            estados[url] = match.group(1)
            
    return estados


def actualizar_servidores_con_auditoria():
    """
    Actualiza el estado interno de los canales en los servidores y luego fuerza
    una re-distribución basada en los nuevos estados.
    """
    print("--- 🔄 Iniciando Actualización y Reclasificación por Auditoría ---")
    
    estados_auditados = cargar_estados_auditados()
    if not estados_auditados:
        return

    servidores_modificados = []
    
    # 1. Recorrer todos los servidores para actualizar el estado interno
    for i in range(1, MAX_SERVIDORES_BUSCAR + 10):
        ruta_servidor = obtener_servidor_path(i)
        
        if not os.path.exists(ruta_servidor):
            # Si ya encontramos servidores y el siguiente no existe, paramos
            if len(servidores_modificados) > 0 and i > MAX_SERVIDORES_BUSCAR:
                break
            continue

        inventario = obtener_inventario_servidor(i)
        cambios_servidor = 0

        for categoria, canales in inventario.items():
            for canal in canales:
                url = canal['url']
                
                # Obtener el estado real de la auditoría
                nuevo_estado = estados_auditados.get(url, canal['estado'])
                
                if nuevo_estado != canal['estado']:
                    # Reemplazar la línea #ESTADO: en el bloque
                    
                    # 1. Actualizar el diccionario interno del canal
                    canal['estado'] = nuevo_estado
                    
                    # 2. Actualizar la línea #ESTADO: dentro del bloque (para que guardar_inventario_servidor la use)
                    linea_estado_antigua = [l for l in canal['bloque'] if l.startswith("#ESTADO:")][0]
                    linea_estado_nueva = f"#ESTADO:{nuevo_estado}"
                    
                    index_estado = canal['bloque'].index(linea_estado_antigua)
                    canal['bloque'][index_estado] = linea_estado_nueva
                    
                    # 3. Actualizar la prioridad interna (para el reordenamiento)
                    from config import PRIORIDAD_ESTADO
                    canal['prioridad'] = PRIORIDAD_ESTADO.get(nuevo_estado, 0)
                    
                    cambios_servidor += 1
        
        if cambios_servidor > 0:
            print(f"✅ Servidor {i:02d} actualizado: {cambios_servidor} canales con nuevo estado.")
            guardar_inventario_servidor(i, inventario) # Guardar con los nuevos estados
            servidores_modificados.append(i)
        else:
            # Aunque no hubo cambios, lo guardamos para el balanceo final
            guardar_inventario_servidor(i, inventario)


    # 2. Ejecutar la Auditoría y Balanceo Global (Reclasificación)
    print("\n--- ⚖️ Ejecutando Reclasificación por Prioridad ---")
    
    # Esto forzará a los canales con bajo #ESTADO: (Fallido) a ser desplazados
    # si los servidores exceden el límite de 2000.
    auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
    
    print("\n--- ✅ Proceso de Reclasificación por Auditoría Finalizado ---")

if __name__ == "__main__":
    actualizar_servidores_con_auditoria()