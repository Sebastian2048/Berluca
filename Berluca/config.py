import os

# 📁 Carpetas base utilizadas por Beluga
CARPETA_SALIDA = "Beluga"
CARPETA_ORIGEN = os.path.join(CARPETA_SALIDA, "compilados")
CARPETA_SEGMENTADOS = os.path.join(CARPETA_SALIDA, "segmentados")
CARPETA_LOGS = os.path.join(CARPETA_SALIDA, "logs")

# 🧱 Crear carpetas si no existen
for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
    os.makedirs(carpeta, exist_ok=True)

# 🧹 Palabras clave para excluir contenido no deseado (AÑADIDO: 24/7, Loop, Adulto, Test)
exclusiones = [
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", "rosario", # Religioso
    "24h", "24/7", "perpetuo", "perpetua", "siempre", "loop", "maraton", "test", "demo", "vacio", # 24/7 y prueba
    "xxx", "adult", "porno", "erotic", "hot", "hentai", "contenido_adulto", "contenido_sensible" # Contenido Adulto y sensible
]

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 0  
LIMITE_BLOQUES = 100 # <--- ¡LÍMITE ESTRICTO DE 100 ENLACES POR CATEGORÍA!
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 

# 🗂️ Clasificación semántica extendida por nombre de canal
CLAVES_CATEGORIA = {
    "peliculas_accion": ["space", "tnt", "cinecanal", "hbo", "amc", "sony movies", "peliculas"],
    "peliculas_drama": ["cinemax", "studio universal", "film&arts", "paramount", "drama"],
    "peliculas_terror": ["space", "syfy", "dark tv", "horror channel", "terror"],
    "series_comedia": ["warner", "comedy central", "fx", "star channel", "sony channel", "series", "comedia"],
    "series_drama": ["universal tv", "axn", "paramount", "hbo series", "drama"],
    "anime_adultos": ["crunchyroll", "adult swim", "bitme", "senpai tv", "anime onegai", "anime", "otaku"],
    "anime_infantil": ["paka paka", "discovery kids", "babytv", "boomerang", "infantil"],
    "infantil_educativo": ["encuentro", "canal rural", "discovery kids", "natgeo kids", "educativo"],
    "documentales_ciencia": ["discovery science", "history", "natgeo", "animal planet", "documental", "ciencia"],
    "documentales_cultura": ["encuentro", "canal rural", "film&arts", "arte tv", "cultura"],
    "deportes_en_vivo": ["espn", "fox sports", "tyc", "tnt sports", "nba", "fútbol", "deportes", "sports"],
    "deportes_extremos": ["eurosport", "red bull tv", "xtreme sports"],
    "noticias_internacionales": ["cnn", "bbc", "al jazeera", "euronews", "noticias"],
    "noticias_latinoamerica": ["tn", "c5n", "a24", "cronica", "todo noticias"],
    "abiertos_arg_general": ["telefe", "el trece", "canal 13", "canal 9", "america tv", "net tv", "elnueve"],
    "musica_latina": ["qube music", "mtv latino", "concert channel", "telehit", "musica"],
}

# 🌐 URL base para acceder a listas segmentadas desde GitHub (No se usa aquí, pero se mantiene)
URL_BASE_SEGMENTADOS = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/segmentados"

# 🐳 Imagen por defecto
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/beluga.png"

# 🖼️ Logos específicos por categoría (Se mantienen para compatibilidad)
LOGOS_CATEGORIA = {
    "infantil_educativo": LOGO_DEFAULT, "musica_latina": LOGO_DEFAULT,
    "documental_cultural": LOGO_DEFAULT, "deportes": LOGO_DEFAULT,
    "cine_terror": LOGO_DEFAULT
}

# ✨ Títulos visuales por categoría (Se mantienen para compatibilidad)
TITULOS_VISUALES = {
    "series": "★ SERIES ★", "peliculas": "★ PELICULAS ★",
    "iptv": "★ TELEVISION ★", "deportes": "★ DEPORTES ★",
    "documental_cultural": "★ DOCUMENTALES ★", "cine_terror": "★ TERROR ★"
}

# 🔍 Función para detectar exclusiones
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in exclusiones)