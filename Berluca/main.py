# main.py (ACTUALIZADO)

import os
# Importaciones de la nueva arquitectura
from extractor import recolectar_enlaces
from generador import clasificar_y_segmentar_archivos, generar_listas_finales 
from git_sync import sincronizar_con_git
# Deberías tener una función en utils o config para crear carpetas
from config import crear_carpetas_iniciales, ARCHIVO_SALIDA 

def ejecutar_proceso_completo(url_lista: str):
    """
    Ejecuta el flujo completo de Berluca: descarga, clasifica, compila y sincroniza.
    """
    # 1. Asegurar la estructura de carpetas
    crear_carpetas_iniciales()
    
    # 2. Descargar y guardar en TEMP_MATERIAL.m3u
    ruta_temp = recolectar_enlaces(url_lista)
    
    if not ruta_temp:
        print("🛑 El proceso se detuvo porque no se pudo descargar o procesar la lista.")
        return

    # 3. Clasificar los bloques del archivo temporal y obtener categorías segmentadas
    # Este paso ahora incluye reclasificación y preparación para segmentación
    categorias_segmentadas = clasificar_y_segmentar_archivos(ruta_temp)
    
    # 4. Compilar la lista final, verificar enlaces y limpiar temporales
    # Se pasa la información de segmentación para saber qué carpetas compilar
    generar_listas_finales(categorias_segmentadas)
    
    # 5. Sincronizar con Git
    sincronizar_con_git()
    
    print(f"\n✨ PROCESO BERLUCA FINALIZADO. Archivo: {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    # 0. Limpiar el nombre del proyecto en consola
    print("=========================================")
    print("        🚀 INICIANDO PROYECTO BERLUCA")
    print("=========================================")
    
    # Pedir la URL
    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("🛑 URL no proporcionada. Saliendo.")