# file_manager.py

import os
import glob
from typing import List, Optional

# Importar rutas y constantes
from config import CARPETA_ORIGEN, CARPETA_SEGMENTADOS

# =========================================================================================
# 💾 OPERACIONES DE ESCRITURA (Segmentación y Clasificación)
# =========================================================================================

def asegurar_archivo_categoria(categoria: str, carpeta_destino: str = CARPETA_ORIGEN):
    """Asegura que el archivo de categoría exista y contenga el encabezado #EXTM3U."""
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta = os.path.join(carpeta_destino, f"{categoria}.m3u")

    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
    return ruta

def guardar_en_categoria(categoria: str, bloque: List[str]):
    """
    Guarda un bloque saneado en el archivo de categoría correspondiente.
    Utiliza CARPETA_ORIGEN como destino predeterminado.
    (Antigua función de clasificador.py)
    """
    ruta = asegurar_archivo_categoria(categoria, CARPETA_ORIGEN)
    
    try:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("\n".join(bloque).strip() + "\n\n")
    except Exception as e:
        print(f"❌ Error al escribir en {ruta}: {e}")
        
def guardar_segmentado(categoria: str, bloques: List[List[str]], contador: int):
    """
    Guarda un lote de bloques segmentados en CARPETA_SEGMENTADOS.
    """
    os.makedirs(CARPETA_SEGMENTADOS, exist_ok=True)
    nombre = f"{categoria}_{contador}.m3u"
    ruta = os.path.join(CARPETA_SEGMENTADOS, nombre)

    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# Segmentado por Berluca\n\n")
            for bloque in bloques:
                f.write("\n".join(bloque).strip() + "\n\n")
        # print(f"📤 Segmentado: {nombre} ({len(bloques)} bloques)")
    except Exception as e:
        print(f"❌ Error al guardar {nombre}: {e}")

# =========================================================================================
# 📚 OPERACIONES DE LECTURA
# =========================================================================================

def leer_archivo_m3u(ruta_archivo: str) -> List[str]:
    """Lee el contenido de un archivo M3U y devuelve sus líneas."""
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"⚠️ Archivo no encontrado: {ruta_archivo}")
        return []
    except Exception as e:
        print(f"❌ Error al leer {ruta_archivo}: {e}")
        return []

# =========================================================================================
# 🧹 OPERACIONES DE LIMPIEZA
# =========================================================================================

def limpiar_carpeta(carpeta: str, extension: str = ".m3u"):
    """Elimina todos los archivos con la extensión especificada en la carpeta."""
    archivos = glob.glob(os.path.join(carpeta, f"*{extension}"))
    if not archivos:
        # print(f"ℹ️ No hay archivos {extension} para limpiar en {carpeta}")
        return

    print(f"\n🧹 Eliminando {len(archivos)} archivos antiguos de {carpeta}/...")
    for archivo in archivos:
        try:
            os.remove(archivo)
        except Exception as e:
            print(f"❌ Error al eliminar {os.path.basename(archivo)}: {e}")
    print("✅ Limpieza completada.")


def verificar_archivos_movian():
    """Verifica y elimina archivos temporales relacionados con Movian."""
    carpeta_compilados = CARPETA_ORIGEN
    archivos_a_eliminar = [
        os.path.join(carpeta_compilados, "peliculas_movian.m3u"),
        os.path.join(carpeta_compilados, "series_movian.m3u")
    ]
    
    for archivo in archivos_a_eliminar:
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
                # print(f"🧹 Eliminado archivo temporal de Movian: {os.path.basename(archivo)}")
            except Exception as e:
                print(f"❌ Error al eliminar el archivo temporal {os.path.basename(archivo)}: {e}")

# La lógica de 'analizar_log' se mantendría en un módulo de logging o utils, 
# pero su llamada desde generador.py debería ser limpia.