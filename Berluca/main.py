# main.py (Versión final simplificada)
# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
from generador import generar_listas_finales
# Desactivadas: from verificador import verificar_enlaces 
# Desactivadas: from git_sync import sincronizar_con_git 
import sys # Se mantiene si lo usas, si no, puedes quitarlo.

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga ---")
    
    recolectar_enlaces(url_lista)
    
    # El flujo principal de procesamiento
    clasificar_enlaces()
    # verificar_enlaces() 
    generar_listas_finales()
    
    # sincronizar_con_git()  # Desactivado a petición
    
    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")