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
    Genera el archivo Berluca.m3u usando el formato #EXTALB personalizado,
    enlazando a los archivos de servidor individuales.
    """
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra (Formato #EXTALB Personalizado): {NOMBRE_ARCHIVO_FINAL} ---")

    if not URL_BASE_REPOSITORIO or not URL_BASE_REPOSITORIO.startswith("http"):
        logging.error("❌ ERROR: URL_BASE_REPOSITORIO no está definida o es inválida en config.py. Verifica la ruta.")
        return

    try:
        with open(ruta_final, "w", encoding="utf-8") as salida:
            salida.write("#EXTM3U\n")
            
            servidores_encontrados = 0

            # Buscar más allá de MAX_SERVIDORES_BUSCAR para asegurar la captura de todos los archivos generados
            for i in range(1, MAX_SERVIDORES_BUSCAR + 100): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                # Dejamos de buscar si no encontramos archivos nuevos después de empezar a contarlos
                if not os.path.exists(ruta_local):
                    # Si ya encontramos al menos un servidor, podemos detenernos si ya superamos el límite configurado
                    if servidores_encontrados > 0 and i > MAX_SERVIDORES_BUSCAR:
                        break
                    continue 

                ruta_relativa_github = os.path.join(CARPETA_SALIDA, nombre_servidor).replace('\\', '/')
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}/{ruta_relativa_github}" # Añadido '/' por seguridad
                
                # Ejemplo: "RP_Servidor_01.m3u" -> "Rp Servidor 01"
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()
                
                # 📌 FORMATO SOLICITADO (Solo #EXTALB y el nombre del servidor)
                # La estructura es: #EXTALB:Nombre \n URL
                
                # CORRECCIÓN: Se elimina el tvg-logo y la metadata adicional
                salida.write(
                    f'\n#EXTALB:{nombre_lista_cliente}\n'
                )
                
                # La URL es el enlace RAW del archivo M3U del servidor.
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")
        print(f"   -> Formato final #EXTALB listo para ser consumido por clientes.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

# 🚀 Punto de entrada
if __name__ == "__main__":
    generar_maestro_m3u()