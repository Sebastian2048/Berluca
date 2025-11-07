import os

# 📁 Carpetas base utilizadas por Beluga
CARPETA_SALIDA = "Beluga"
CARPETA_ORIGEN = os.path.join(CARPETA_SALIDA, "compilados")
CARPETA_SEGMENTADOS = os.path.join(CARPETA_SALIDA, "segmentados")
CARPETA_LOGS = os.path.join(CARPETA_SALIDA, "logs")

# 🧱 Crear carpetas si no existen
for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
    os.makedirs(carpeta, exist_ok=True)

# 🧹 Palabras clave para excluir contenido no deseado
exclusiones = [
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", "rosario",
    "24h", "24/7", "perpetuo", "perpetua", "siempre", "loop", "maraton", "test", "demo", "vacio",
    "xxx", "adult", "porno", "erotic", "hot", "hentai", "contenido_adulto", "contenido_sensible"
]

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 0  
LIMITE_BLOQUES = 100 # <--- ¡LÍMITE ESTRICTO DE 100 ENLACES POR CATEGORÍA!
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 

# 🗂️ Clasificación Estricta y Amplia (Simulando IPTV Profesional)
CLAVES_CATEGORIA = {
    # 🇦🇷 Canales Locales
    "tv_argentina": ["telefe", "el trece", "canal 13", "canal 9", "america tv", "net tv", "elnueve"],
    
    # 🎬 Cine y Series
    "peliculas_principal": ["hbo", "cinecanal", "tnt", "amc", "paramount", "cinemax", "sony movies", "peliculas", "cine"],
    "series_principal": ["warner", "comedy central", "fx", "star channel", "sony channel", "universal tv", "axn", "series"],
    "cine_terror": ["syfy", "dark tv", "horror channel", "terror", "miedo"],
    
    # ⚽ Deportes
    "deportes_en_vivo": ["espn", "fox sports", "tyc", "tnt sports", "nba", "fútbol", "deportes", "sports"],
    
    # 👶 Infancia y Animación
    "infantil_kids": ["discovery kids", "cartoon network", "disney", "nickelodeon", "paka paka", "babytv", "infantil"],
    "anime_general": ["crunchyroll", "adult swim", "bitme", "senpai tv", "anime", "manga"],
    
    # 🌍 Documentales y Noticias
    "documentales_ciencia": ["discovery science", "history", "natgeo", "animal planet", "documental"],
    "noticias_global": ["cnn", "bbc", "al jazeera", "euronews", "tn", "c5n", "a24", "cronica", "noticias"],
    
    # 🎵 Música
    "musica_general": ["mtv", "telehit", "qube music", "musica", "concert"],
    
    # 🗑️ Desbordamiento (Usado en el clasificador)
    "peliculas_extras": ["película", "movie", "film"]
}

# 🌐 URL base para acceder a listas segmentadas desde GitHub (Se mantiene)
URL_BASE_SEGMENTADOS = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/segmentados"

# 🐳 Imagen por defecto
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/beluga.png"

# 🖼️ Logos específicos por categoría
LOGOS_CATEGORIA = {
    "tv_argentina": LOGO_DEFAULT, "peliculas_principal": LOGO_DEFAULT,
    "series_principal": LOGO_DEFAULT, "deportes_en_vivo": LOGO_DEFAULT
}

# ✨ Títulos visuales por categoría
TITULOS_VISUALES = {
    "tv_argentina": "★ TV ARGENTINA ★",
    "peliculas_principal": "★ CINE Y PELÍCULAS ★",
    "series_principal": "★ SERIES DE TV ★",
    "deportes_en_vivo": "★ DEPORTES EN VIVO ★",
    "peliculas_extras": "★ CINE EXTRA (Overflow) ★", # Nuevo título de desbordamiento
}

# 🔍 Función para detectar exclusiones
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in exclusiones)