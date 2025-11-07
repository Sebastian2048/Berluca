# generar_maestro.py
import os
from typing import List
import logging

# 📦 Importaciones de configuración y auxiliares
try:
    # Necesitas importar MAX_SERVIDORES_BUSCAR, CARPETA_SALIDA, y NOMBRE_BASE_SERVIDOR
    from config import MAX_SERVIDORES_BUSCAR, CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR
except ImportError as e:
    print(f"ERROR: No se pudo importar la configuración. Asegúrate de que config.py esté completo. Detalle: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURACIÓN DE GITHUB ---
# ¡IMPORTANTE! Reemplaza esto con la URL base RAW de TU repositorio y rama:
# El formato debe ser: https://raw.githubusercontent.com/USUARIO/REPOSITORIO/RAMA/
URL_BASE_REPOSITORIO = "https://raw.githubusercontent.com/Sebastian2048/Berluca/main/"
# Si tu repositorio es diferente, ¡ajusta la URL anterior!
# Ejemplo para Danga1963/Beluca en rama master: 
# URL_BASE_REPOSITORIO = "https://raw.githubusercontent.com/Danga1963/Beluca/master/"


def generar_maestro_m3u():
    """Genera el archivo Berluca.m3u con enlaces RAW a todos los servidores segmentados."""
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra: {NOMBRE_ARCHIVO_FINAL} ---")

    try:
        with open(ruta_final, "w", encoding="utf-8") as salida:
            salida.write("#EXTM3U\n")
            
            servidores_encontrados = 0

            # Iterar sobre los posibles servidores (de 1 a MAX_SERVIDORES_BUSCAR + 1, para incluir nuevos)
            # Buscamos hasta 20 servidores para cubrir el balanceo de 2000 bloques.
            for i in range(1, MAX_SERVIDORES_BUSCAR + 10): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                # Verificar si el archivo del servidor existe localmente antes de crear el enlace
                if not os.path.exists(ruta_local):
                    if servidores_encontrados > 0:
                        # Si ya encontramos servidores, paramos cuando el siguiente no existe
                        break
                    # Si no encontramos el 01, continuamos buscando por si hay huecos
                    continue 

                # Construir la URL RAW de GitHub (formato EXIFtab/EXTINF)
                
                # La ruta relativa en GitHub es: CARPETA_SALIDA/NOMBRE_SERVIDOR.m3u
                ruta_relativa_github = os.path.join(CARPETA_SALIDA, nombre_servidor).replace('\\', '/')
                
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}{ruta_relativa_github}"

                # Línea EXINTF (como has solicitado, con EXIFtab si es tu estándar)
                # Usaremos EXTINF con group-title para que sea un bloque M3U válido para clientes IPTV
                
                salida.write(
                    f'\n#EXTINF:-1 group-title="★ SERVIDORES BELUGA ★" tvg-logo="https://i.imgur.com/2sR2O0t.png",Servidor {i:02d}\n'
                )
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

if __name__ == "__main__":
    generar_maestro_m3u()