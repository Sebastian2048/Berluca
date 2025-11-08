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
    Genera el archivo Berluca.m3u usando un formato simple (#EXTALB sin #EXTINF) 
    para las listas anidadas, buscando la máxima compatibilidad (Movian).
    """
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra (Formato Alternativo): {NOMBRE_ARCHIVO_FINAL} ---")

    # Si URL_BASE_REPOSITORIO no está definida o es incorrecta, terminamos.
    if not URL_BASE_REPOSITORIO or not URL_BASE_REPOSITORIO.startswith("http"):
        logging.error("❌ ERROR: URL_BASE_REPOSITORIO no está definida o es inválida en config.py.")
        return

    try:
        with open(ruta_final, "w", encoding="utf-8") as salida:
            salida.write("#EXTM3U\n")
            
            servidores_encontrados = 0

            # Buscar servidores hasta el límite + 10 por si el balanceo creó más
            for i in range(1, MAX_SERVIDORES_BUSCAR + 10): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                # Si el archivo local no existe, continuamos buscando, y si ya 
                # encontramos algo, terminamos.
                if not os.path.exists(ruta_local):
                    if servidores_encontrados > 0:
                        break
                    continue 

                # Construir la ruta relativa (ej: Beluga/RP_Servidor_01.m3u)
                ruta_relativa_github = os.path.join(CARPETA_SALIDA, nombre_servidor).replace('\\', '/')
                
                # Combinar con la URL base correcta (ej: .../main/Beluga/RP_Servidor_01.m3u)
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}{ruta_relativa_github}"
                
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()
                
                # Formato alternativo para Movian/clientes sensibles:
                # 1. Usamos #EXTINF con el nombre del servidor (para que aparezca el icono y el nombre)
                # 2. Eliminamos group-title, que confunde a algunos parsers.
                # 3. La URL es la URL del M3U del servidor (lista anidada).
                salida.write(
                    f'\n#EXTINF:-1 tvg-logo="{LOGO_DEFAULT}",{nombre_lista_cliente}\n'
                )
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")
        print(f"   -> Verifica que la URL base en config.py esté correcta para evitar el error 404.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

# 🚀 Punto de entrada
if __name__ == "__main__":
    generar_maestro_m3u()