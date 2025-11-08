# generar_maestro.py
import os
from typing import List
import logging

# 📦 Importaciones de configuración y auxiliares
try:
    from config import MAX_SERVIDORES_BUSCAR, CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR
except ImportError as e:
    print(f"ERROR: No se pudo importar la configuración. Asegúrate de que config.py esté completo. Detalle: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DE GITHUB ---
# 🚨 ¡IMPORTANTE! MODIFICA ESTA LÍNEA 🚨
# Debe ser la URL base RAW de TU repositorio: https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/TU_RAMA/
URL_BASE_REPOSITORIO = "https://raw.githubusercontent.com/Sebastian2048/Berluca/main/"


def generar_maestro_m3u():
    """Genera el archivo Berluca.m3u con enlaces RAW a todos los servidores segmentados."""
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra: {NOMBRE_ARCHIVO_FINAL} ---")

    try:
        with open(ruta_final, "w", encoding="utf-8") as salida:
            salida.write("#EXTM3U\n")
            
            servidores_encontrados = 0

            # Buscar hasta 20 servidores para cubrir el balanceo de 2000 bloques.
            for i in range(1, MAX_SERVIDORES_BUSCAR + 10): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                if not os.path.exists(ruta_local):
                    if servidores_encontrados > 0:
                        break
                    continue 

                # Construir la URL RAW de GitHub
                ruta_relativa_github = os.path.join(CARPETA_SALIDA, nombre_servidor).replace('\\', '/')
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}{ruta_relativa_github}"
                
                # Nombre de la lista para el cliente (Ej: Servidor 01)
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()

                # 🌟 FORMATO CORREGIDO (tvg-logo antes de group-title) 🌟
                salida.write(
                    f'\n#EXTINF:-1 tvg-logo="https://i.imgur.com/2sR2O0t.png", group-title="★ SERVIDORES BELUGA ★",{nombre_lista_cliente}\n'
                )
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

if __name__ == "__main__":
    generar_maestro_m3u()