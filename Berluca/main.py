# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
from servidor import distribuir_por_servidor
import os
import sys 

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga con Prioridad Multi-Servidor ---")
    
    # 1. Extracción y Guardado Temporal
    ruta_temp = recolectar_enlaces(url_lista)
    
    if not ruta_temp:
        print("❌ No se pudo obtener la lista M3U. Terminando.")
        return
        
    # 2. Clasificación: Asigna Categoría, Idioma y Estado
    bloques_para_distribuir = clasificar_enlaces(ruta_temp)
    
    # 3. Distribución: Aplica la lógica de Servidor, Prioridad y Balanceo
    if bloques_para_distribuir:
        distribuir_por_servidor(bloques_para_distribuir)
    
    # 4. Limpieza (Opcional)
    try:
        os.remove(ruta_temp)
        print(f"🗑️ Archivo temporal {os.path.basename(ruta_temp)} eliminado.")
    except Exception as e:
        print(f"⚠️ Error al eliminar archivo temporal: {e}")

    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
        
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")