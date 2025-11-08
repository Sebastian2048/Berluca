# generar_maestro.py
import os
import re
import logging

# 📦 Importaciones de módulos locales
try:
    from config import (
        CARPETA_SALIDA, NOMBRE_BASE_SERVIDOR, MAX_SERVIDORES_BUSCAR, 
        URL_BASE_REPOSITORIO, LOGO_DEFAULT
    )
except ImportError as e:
    logging.error(f"Error al importar módulos en generar_maestro.py: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def generar_maestro_m3u():
    """
    Genera el archivo Berluca.m3u usando el formato #EXTALB para las listas 
    anidadas. Este es un formato no estándar pero que a veces es requerido 
    por clientes sensibles (como Movian) para identificar sub-listas.
    """
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra (Formato #EXTALB): {NOMBRE_ARCHIVO_FINAL} ---")

    if not URL_BASE_REPOSITORIO or not URL_BASE_REPOSITORIO.startswith("http"):
        logging.error("❌ ERROR: URL_BASE_REPOSITORIO no está definida o es inválida en config.py. Verifica la ruta.")
        return

    try:
        with open(ruta_final, "w", encoding="utf-8") as salida:
            salida.write("#EXTM3U\n")
            
            servidores_encontrados = 0

            for i in range(1, MAX_SERVIDORES_BUSCAR + 10): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                if not os.path.exists(ruta_local):
                    if servidores_encontrados > 0 and i > MAX_SERVIDORES_BUSCAR:
                        break
                    continue 

                ruta_relativa_github = os.path.join(CARPETA_SALIDA, nombre_servidor).replace('\\', '/')
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}{ruta_relativa_github}"
                
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()
                
                # 📌 Formato #EXTALB
                # 1. Usamos #EXTINF con el nombre del servidor (para que Movian muestre el título)
                salida.write(
                    f'\n#EXTINF:-1 tvg-logo="{LOGO_DEFAULT}",{nombre_lista_cliente}\n'
                )
                # 2. Agregamos #EXTALB o #EXTGRP para intentar forzar el comportamiento de lista anidada
                # Usaremos #EXTALB como pediste, pero es la línea de URL la que debe ser leída
                salida.write(f'#EXTALB:{nombre_lista_cliente}\n')
                
                # 3. La URL es la URL RAW del archivo M3U del servidor.
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")
        print(f"   -> ¡Importante! Este es el formato #EXTALB/No-estándar. Prueba en Movian.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

# 🚀 Punto de entrada
if __name__ == "__main__":
    generar_maestro_m3u()