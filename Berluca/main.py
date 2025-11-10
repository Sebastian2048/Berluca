# main.py
import os
import sys
import requests
import logging

# 📦 Importaciones de módulos locales
# Importamos auditar_y_balancear_servidores (la función principal de balanceo)
try:
    from config import CARPETA_SALIDA, MAX_SERVIDORES_BUSCAR
    from auxiliar import (
        descargar_lista, limpiar_archivos_temporales
    )
    # NOTA: clasificador.py DEBE existir y su función clasificar_enlaces() debe estar disponible.
    from clasificador import clasificar_enlaces 
    from servidor import auditar_y_balancear_servidores # <--- ÚNICA FUNCIÓN DE SERVIDOR NECESARIA
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
    """
    Ejecuta el flujo completo: Recolección, Clasificación, y Balanceo/Auditoría Final.
    NOTA: Para una ejecución completa (incluyendo Streamlink), se debe ejecutar 
    'auditor_conectividad.py' entre la clasificación y el balanceo.
    """
    ruta_temp = recolectar_lista(url)
    if not ruta_temp:
        return

    try:
        # 1. CLASIFICACIÓN Y CONSOLIDACIÓN (Asumimos que clasificar_enlaces también hace la Quick Audit y guarda el Resumen)
        # En una arquitectura modular, esta función (clasificar_enlaces) debe ahora incluir:
        # a) Lectura de la lista TEMP.
        # b) Consolidación con servidores existentes.
        # c) Quick Audit (requests.head) y etiquetado de estados iniciales.
        # d) Guardado en RP_Resumen_Auditoria.m3u o similar.
        print("\n--- 🧠 Clasificando y Consolidando Inventario (FASE 1 - Rápida) ---")
        clasificar_enlaces(ruta_temp) # <-- Se asume que esto ahora hace la FASE 1 y guarda el archivo RP_Resumen_Auditoria.m3u
        print("✅ Consolidación y Quick Audit finalizada. Archivo de resumen listo para balanceo.")
        
        # 2. BALANCEO ESTRATÉGICO Y EXCLUSIÓN (FASE 3)
        # auditar_y_balancear_servidores ahora lee el archivo de resumen auditado 
        # y distribuye SOLO los canales 'abierto'
        auditar_y_balancear_servidores(MAX_SERVIDORES_BUSCAR)
            
    except Exception as e:
        print(f"\nERROR CRÍTICO durante el proceso: {e}")
    finally:
        limpiar_archivos_temporales(ruta_temp)
        print("--- ✅ Proceso Completo Finalizado ---")

# =========================================================================================
# 🚀 PUNTO DE ENTRADA
# =========================================================================================

if __name__ == "__main__":
    
    # ⚠️ IMPORTANTE: Esta es una ejecución simplificada (sin Streamlink)
    print("--- 🚀 Iniciando Flujo Simplificado de Beluga (FASE 1 y 3) ---")
    
    # 1. Solicitar URL
    url_m3u = input("🔗 Ingresa la URL de la lista .m3u: ").strip()

    if not url_m3u:
        print("ERROR: URL no ingresada. Saliendo.")
        sys.exit(0)
    
    # 2. Ejecutar
    ejecutar_proceso_completo(url_m3u)