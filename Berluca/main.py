# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
# from verificador import verificar_enlaces # Se mantiene comentado
from generador import generar_listas_finales # Ya no se intenta importar la función 'clasificar_y_segmentar_archivos'
from git_sync import sincronizar_con_git
import sys

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga ---")
    recolectar_enlaces(url_lista)
    
    # Detener si el archivo temporal no se creó (recolectar_enlaces debería manejar esto)
    #if not os.path.exists("Beluga/TEMP_MATERIAL.m3u"):
    #    print("Flujo detenido: No se pudo descargar el material.")
    #    return

    clasificar_enlaces()
    # verificar_enlaces() # Descomentar si está implementado y quieres usarlo
    generar_listas_finales()
    sincronizar_con_git()  # ✅ Se ejecuta solo como parte del flujo completo
    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    # Asegurarse de que Python y los módulos están en el path si se usa un entorno virtual específico
    # print(f"Usando Python en: {sys.executable}") 

    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")