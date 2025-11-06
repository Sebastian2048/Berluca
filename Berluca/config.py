import os

# =========================================================================================
# ⚙️ CONFIGURACIÓN Y RUTAS BASE
# =========================================================================================

# 📁 Carpetas base utilizadas por Beluga
CARPETA_SALIDA = "Beluga"
CARPETA_ORIGEN = os.path.join(CARPETA_SALIDA, "compilados")
CARPETA_SEGMENTADOS = os.path.join(CARPETA_SALIDA, "segmentados")
CARPETA_LOGS = os.path.join(CARPETA_SALIDA, "logs")

# 🧱 Crear carpetas si no existen
def crear_carpetas_iniciales():
    for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
        # Usamos exist_ok=True para que no falle si ya existen
        os.makedirs(carpeta, exist_ok=True)
# Llamar a la función al inicio del script para asegurar la estructura
crear_carpetas_iniciales() 

# 🧹 Palabras clave para excluir contenido no deseado (CORRECCIÓN: Renombrado a EXCLUSIONES)
EXCLUSIONES = [
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", "rosario"
]

# 🎯 Palabras clave deseadas (preferencias)
preferencias = [
    "español", "latino", "anime", "infantil", "dibujos", "comedia", "drama",
    "documental", "educativo", "cultural", "películas", "series", "musica", "cine",
    "fútbol", "deportes", "historia", "naturaleza", "estrenos", "concierto"
]

# 🧠 MAPEO DE CLAVES PARA CLASIFICADOR.PY
CLAVES_CATEGORIA = {
    "peliculas": ["pelicula", "cine", "film", "estrenos"],
    "series": ["serie", "season", "capitulo", "series"],
    "deportes": ["futbol", "deporte", "sport", "nba", "boxeo", "tenis", "fútbol"],
    "infantil_educativo": ["infantil", "kids", "dibujos", "cartoon", "educativo"],
    "documental_cultural": ["documental", "cultura", "historia", "naturaleza"],
    "anime": ["anime", "manga", "otaku"],
    "musica": ["musica", "concierto", "cumbia", "reggeaton"],
    "entretenimiento": ["comedia", "drama"]
}

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 0  
LIMITE_BLOQUES = 100
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 

# 🔗 Rutas de salida y metadatos
ARCHIVO_SALIDA = os.path.join(CARPETA_SALIDA, "RP_S2048.m3u")
URL_REPOSITORIO = "https://github.com/Sebastian2048/Beluga"
URL_BASE_RAW = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main"

# 🐳 Imagen por defecto (formato raw para compatibilidad IPTV)
LOGO_DEFAULT = f"{URL_BASE_RAW}/beluga.png"

# 🖼️ Logos y Títulos (Se mantienen)
LOGOS_CATEGORIA = {
    "infantil_educativo": LOGO_DEFAULT,
    "musica_latina": LOGO_DEFAULT,
    "documental_cultural": LOGO_DEFAULT,
    "deportes": LOGO_DEFAULT,
    "cine_terror": LOGO_DEFAULT
}

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
    "cine_terror": "★ TERROR ★"
}

# 🔍 Función de utilidad para exclusión (usará EXCLUSIONES)
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in EXCLUSIONES)