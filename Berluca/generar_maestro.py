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

# --- DEFINICIÓN DE SUBDIRECTORIOS DE SALIDA (Añadido) ---
# Se asume que el archivo maestro y Beluga/ están un nivel arriba del repositorio,
# por lo que la ruta relativa debe incluir la carpeta de la que se parte.
CARPETA_BASE_GITHUB = "Berluca" # Nombre de la carpeta del proyecto en el repositorio
CARPETA_LISTAS = "Beluga"      # Nombre de la carpeta de listas de salida (CARPETA_SALIDA)


def generar_maestro_m3u():
    """
    Genera el archivo Berluca.m3u usando el formato #EXTALB personalizado,
    enlazando a los archivos de servidor individuales con URL de referencia de rama.
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

            for i in range(1, MAX_SERVIDORES_BUSCAR + 100): 
                
                nombre_servidor = f"{NOMBRE_BASE_SERVIDOR}_{i:02d}.m3u"
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_servidor)
                
                if not os.path.exists(ruta_local):
                    if servidores_encontrados > 0 and i > MAX_SERVIDORES_BUSCAR:
                        break
                    continue 
                
                # 🛠️ CONCATENACIÓN CRÍTICA MODIFICADA
                # Construye la ruta completa: BASE_URL/Berluca/Beluga/RP_Servidor_xx.m3u
                ruta_completa_github = f"{CARPETA_BASE_GITHUB}/{CARPETA_LISTAS}/{nombre_servidor}"
                
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}/{ruta_completa_github}"
                
                # Ejemplo: "RP_Servidor_01.m3u" -> "Rp Servidor 01"
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()
                
                
                # --- ALTERNATIVAS DE FORMATO ---
                
                # 📌 OPCIÓN 1: Formato EXTALB Minimalista (el que preferimos ahora)
                salida.write(f'\n#EXTALB:{nombre_lista_cliente}\n')
                
                # 📌 OPCIÓN 2: Formato EXTALB con metadata (La versión anterior)
                # salida.write(f'\n#EXTALB:{nombre_lista_cliente} tvg-logo="{LOGO_DEFAULT}",{nombre_lista_cliente}\n')
                
                
                # Escribir la URL (Aplicable a ambas opciones de EXTALB)
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")
        print(f"   -> URLs generadas usando la referencia de rama (refs/heads/main).")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

# 🚀 Punto de entrada
if __name__ == "__main__":
    generar_maestro_m3u()