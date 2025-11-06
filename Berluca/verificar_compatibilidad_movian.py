# verificar_compatibilidad_movian.py

import os
from typing import List

# Importaciones de config
from config import ARCHIVO_SALIDA

# =========================================================================================
# 🖥️ COMPATIBILIDAD CON MOVIAN
# =========================================================================================

def adaptar_para_movian(ruta_lista_final: str = ARCHIVO_SALIDA):
    """
    Aplica adaptaciones al archivo final M3U para mejorar la compatibilidad con Movian.
    Movian puede tener problemas con líneas vacías o formatos específicos.
    """
    if not os.path.exists(ruta_lista_final):
        return

    print("🖥️ Adaptando la lista final para compatibilidad con Movian...")

    try:
        with open(ruta_lista_final, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        nuevas_lineas = []
        for linea in lineas:
            linea = linea.strip()
            
            # 1. Eliminar líneas vacías innecesarias (aunque generador.py debería ser limpio)
            if not linea:
                continue

            # 2. Movian a veces prefiere el formato EXTINF con un solo espacio antes de la coma
            if linea.startswith('#EXTINF'):
                # Eliminar espacios extra después de tvg-logo/group-title
                linea = re.sub(r'"\s+', '" ', linea)
            
            nuevas_lineas.append(linea)

        # 3. Sobreescribir el archivo con las adaptaciones
        with open(ruta_lista_final, 'w', encoding='utf-8') as f:
            f.write("\n".join(nuevas_lineas) + "\n")
        
        print("✅ Adaptación a Movian completada.")

    except Exception as e:
        print(f"❌ Error al adaptar para Movian: {e}")

# NOTA: La antigua función verificar_archivos_movian (que eliminaba archivos temporales)
# se queda en file_manager.py ya que es una operación de limpieza de I/O.