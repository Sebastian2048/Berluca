# main.py

from extractor import recolectar_enlaces
from clasificador import clasificar_enlaces
from generador import generar_listas_finales, limpiar_miscelaneo_caducado # <-- ¡Importada la función de limpieza!
# from verificador import verificar_enlaces # Mantenemos comentada hasta resolver el problema de bloqueo
import sys 

def ejecutar_proceso_completo(url_lista):
    print("--- 🚀 Iniciando Flujo de Beluga ---")
    
    recolectar_enlaces(url_lista)
    
    # 0. Limpieza: Elimina enlaces viejos de misceláneo (más de 7 días)
    limpiar_miscelaneo_caducado() 
    
    # 1. Clasificación/Fusión: Aplica la lógica de Fallback: Principal -> Extra -> Misceláneo.
    clasificar_enlaces()
    
    # 2. Verificación (Filtra 404): Comentada para evitar el bloqueo del servidor.
    # verificar_enlaces() 
    
    # 3. Generación Final: Consolida todos los archivos de compilados/
    generar_listas_finales()
    
    print("--- ✅ Proceso Completo Finalizado ---")

if __name__ == "__main__":
    url = input("🔗 Ingresa la URL de la lista .m3u: ").strip()
    if url:
        ejecutar_proceso_completo(url)
    else:
        print("❌ URL no proporcionada. Saliendo.")