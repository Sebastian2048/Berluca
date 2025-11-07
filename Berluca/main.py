# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
from generador import generar_listas_finales # ¡Importamos solo generar_listas_finales!
# from verificador import verificar_enlaces 
import sys 

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga ---")
    
    recolectar_enlaces(url_lista)
    
    # 0. Limpieza de caducidad eliminada
    
    # 1. Clasificación/Fusión: Aplica la lógica de Idioma y Fallback a roll_over_general.
    clasificar_enlaces()
    
    # 2. Verificación (Filtra 404): Comentada para evitar el bloqueo del servidor.
    # verificar_enlaces() 
    
    # 3. Generación Final: Consolida los archivos principales en RP_S2048.m3u 
    # y el contenido de roll_over_general en RP_Sxxxx.m3u.
    generar_listas_finales()
    
    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")