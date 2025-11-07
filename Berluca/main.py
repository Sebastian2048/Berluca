# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
from generador import generar_listas_finales, limpiar_carpeta_compilados # <-- 🛑 Importación de la función de limpieza
import sys 

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga ---")
    
    recolectar_enlaces(url_lista)
    
    # 🛑 PASO CLAVE: Limpiar la carpeta antes de clasificar
    print("\n🧹 Eliminando archivos clasificados obsoletos de Beluga/compilados...")
    limpiar_carpeta_compilados() # <-- 🛑 Llamada a la función de limpieza
    
    # El flujo principal de procesamiento
    clasificar_enlaces() # <-- Ahora esta función añade archivos a una carpeta VACÍA
    generar_listas_finales() # <-- Ahora esta función solo lee los archivos nuevos y limitados
    
    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")