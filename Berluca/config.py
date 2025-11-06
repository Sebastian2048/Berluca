# config.py

import os

# =========================================================================================
# ⚙️ PARÁMETROS GENERALES DEL PROYECTO BERLUCA
# =========================================================================================

# 📁 Rutas base utilizadas por Berluca (ajustar si es necesario)
CARPETA_SALIDA = "Berluca"
CARPETA_ORIGEN = os.path.join(CARPETA_SALIDA, "compilados")
CARPETA_SEGMENTADOS = os.path.join(CARPETA_SALIDA, "segmentados")
CARPETA_LOGS = os.path.join(CARPETA_SALIDA, "logs")
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "RP_B2048.m3u") # Nuevo nombre

# 🧹 Palabras clave para excluir contenido no deseado (religioso, test, ads)
EXCLUSIONES = [
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", 
    "rosario", "adblock", "test", "vacio", "publicidad", "anuncio"
]

# 🎯 Palabras clave deseadas/preferentes (pueden ser usadas por el clasificador)
PREFERENCIAS = [
    "español", "latino", "anime", "infantil", "dibujos", "comedia", "drama",
    "documental", "educativo", "cultural", "películas", "series", "musica", "cine",
    "fútbol", "deportes", "historia", "naturaleza", "estrenos", "concierto"
]

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 5  # Mínimo de bloques para considerar una lista segmentada válida
LIMITE_BLOQUES = 100       # Límite para la segmentación de archivos (I/O controlada)
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 # Umbral de porcentaje de exclusión para descartar un archivo completo

# =========================================================================================
# 🖼️ METADATOS VISUALES (para la lista final)
# =========================================================================================

# 🐳 Imagen por defecto (formato raw para compatibilidad IPTV)
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Berluca/main/berluca.png"

# 🖼️ Logos específicos por categoría
LOGOS_CATEGORIA = {
    "infantil_educativo": LOGO_DEFAULT,
    "musica_latina": LOGO_DEFAULT,
    "documental_cultural": LOGO_DEFAULT,
    "deportes": LOGO_DEFAULT,
    "cine_terror": LOGO_DEFAULT
}

# ✨ Títulos visuales por categoría
TITULOS_VISUALES = {
    "series": "★ SERIES ★",
    "peliculas": "★ PELICULAS ★",
    "sagas": "★ SAGAS ★",
    "iptv": "★ TELEVISION ★",
    "estrenos": "★ ESTRENOS ★",
    "infantil_educativo": "★ INFANTIL EDUCATIVO ★",
    "musica_latina": "★ MÚSICA LATINA ★",
    "deportes": "★ DEPORTES ★",
    "documental_cultural": "★ DOCUMENTALES ★",
    "cine_terror": "★ TERROR ★",
    "sin_clasificar": "★ SIN CLASIFICAR ★"
}

# =========================================================================================
# 🛠️ FUNCIONES DE UTILIDAD DE CONFIGURACIÓN
# =========================================================================================

def contiene_exclusion(texto):
    """Verifica si un texto contiene alguna palabra clave de exclusión."""
    texto = texto.lower()
    return any(palabra in texto for palabra in EXCLUSIONES)

# CLAVES_CATEGORIA ya no es necesario aquí; su lógica se moverá a clasificador.py

# =========================================================================================
# 🛑 EJECUTAR EN CASO DE NECESITAR INICIALIZAR CARPETAS (Normalmente en main.py)
# =========================================================================================

def crear_carpetas_iniciales():
    """Crea la estructura de carpetas si no existe."""
    print(f"📁 Creando estructura de carpetas en: {CARPETA_SALIDA}/")
    for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
        os.makedirs(carpeta, exist_ok=True)


if __name__ == "__main__":
    crear_carpetas_iniciales()
    print("Configuración inicial de carpetas lista.")