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

# --- DEFINICIÓN DE SUBDIRECTORIOS DE SALIDA (Añadido para ruta GitHub) ---
# Estas variables deben coincidir con la estructura de carpetas del repositorio
REPO_ROOT_FOLDER = "Berluca" 
CARPETA_LISTAS = CARPETA_SALIDA # 'Beluga' (de config.py)

def generar_maestro_m3u():
    """
    Genera el archivo Berluca.m3u usando el formato estándar #EXTINF,
    enlazando a los archivos de servidor individuales con metadata de logo.
    """
    
    NOMBRE_ARCHIVO_FINAL = "Berluca.m3u"
    ruta_final = os.path.join(CARPETA_SALIDA, NOMBRE_ARCHIVO_FINAL)
    
    print(f"--- 🔗 Iniciando generación de lista Maestra (Formato #EXTINF Estándar): {NOMBRE_ARCHIVO_FINAL} ---")

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

                
                # 🛠️ Construcción de la URL de Referencia (Robust URL)
                # Formato: BASE_URL/Berluca/Beluga/RP_Servidor_xx.m3u
                ruta_completa_github = f"{REPO_ROOT_FOLDER}/{CARPETA_LISTAS}/{nombre_servidor}"
                url_raw_servidor = f"{URL_BASE_REPOSITORIO}/{ruta_completa_github}"
                
                # Ejemplo: "RP_Servidor_01.m3u" -> "RP Servidor 01"
                nombre_lista_cliente = nombre_servidor.replace(".m3u", "").replace("_", " ").title()
                
                
                # 📌 FORMATO SOLICITADO: #EXTINF con tvg-logo y group-title
                salida.write(
                    f'\n#EXTINF:-1 tvg-logo="{LOGO_DEFAULT}" group-title="SERVIDORES IPTV",{nombre_lista_cliente}\n'
                )
                
                # Escribir la URL del servidor M3U
                salida.write(f'{url_raw_servidor}\n')
                
                servidores_encontrados += 1
            
        print(f"✅ Lista maestra {NOMBRE_ARCHIVO_FINAL} generada con {servidores_encontrados} enlaces.")
        print(f"   -> Formato final #EXTINF Estándar, listo para ser consumido por la mayoría de los clientes.")

    except Exception as e:
        logging.error(f"Error al generar el archivo maestro: {e}")

# 🚀 Punto de entrada
if __name__ == "__main__":
    generar_maestro_m3u()