# main.py
import os
import sys
import requests
import logging

# 📦 Importaciones de módulos locales
try:
    from config import CARPETA_SALIDA, MAX_SERVIDORES_BUSCAR
    from auxiliar import (
        descargar_lista, limpiar_archivos_temporales
    )
    from clasificador import clasificar_enlaces
    from servidor import distribuir_por_servidor, auditar_y_balancear_servidores
except ImportError as e:
    print(f"ERROR: No se pudo importar un módulo necesario. Asegúrate de tener todos los archivos (.py) en la misma carpeta.")
    print(f"Detalle del error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================================================================================
# ⚙️ FLUJO DE CONTROL PRINCIPAL
# =========================================================================================

def recolectar_lista(url: str) -> str:
    """Descarga la lista M3U y la guarda temporalmente."""
    ruta_temp = os.path.join(CARPETA_SALIDA, "TEMP_MATERIAL.m3u")
    print(f"🔗 Recolectando lista desde: {url}")
    
    try:
        if descargar_lista(url, ruta_temp):
            logging.info(f"✅ Lista guardada temporalmente en: {ruta_temp}")
            return ruta_temp
        else:
            return ""
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al descargar la lista M3U: {e}")
        return ""


def ejecutar_proceso_completo(url: str):
    """Ejecuta el flujo completo: Recolección, Clasificación, Distribución y Auditoría."""
    ruta_temp = recolectar_lista(url)
    if not ruta_temp:
        return

    try:
        bloques_para_distribuir = clasificar_enlaces(ruta_temp)
        
        if bloques_para_distribuir:
            # 1. Distribución Inicial (Límite por Categoría 60)
            distribuir_por_servidor(bloques_para_distribuir) 
            
            # 2. Auditoría y Balanceo (Límite Global 2000)
            auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
            
        else:
            print("INFO: No hay bloques válidos para distribuir.")

    except Exception as e:
        print(f"\nERROR CRÍTICO durante el proceso: {e}")
    finally:
        limpiar_archivos_temporales(ruta_temp)
        print("--- ✅ Proceso Completo Finalizado ---")

# =========================================================================================
# 🚀 PUNTO DE ENTRADA
# =========================================================================================

if __name__ == "__main__":
    
    print("--- 🚀 Iniciando Flujo de Beluga con Prioridad Multi-Servidor ---")
    
    # 1. Solicitar URL
    url_m3u = input("🔗 Ingresa la URL de la lista .m3u: ").strip()

    if not url_m3u:
        print("ERROR: URL no ingresada. Saliendo.")
        sys.exit(0)
    
    # 2. Ejecutar
    ejecutar_proceso_completo(url_m3u)