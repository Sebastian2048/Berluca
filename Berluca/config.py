import os

# 📁 Carpetas base utilizadas por Beluga
CARPETA_SALIDA = "Beluga"
CARPETA_ORIGEN = "compilados"
CARPETA_SEGMENTADOS = "segmentados"
CARPETA_LOGS = "logs"

# 🧱 Crear carpetas si no existen
for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
    os.makedirs(carpeta, exist_ok=True)

# 🧹 Palabras clave para excluir contenido no deseado
exclusiones = [
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", "rosario",
    "24h", "24/7", "perpetuo", "perpetua", "siempre", "siempre activo", "loop" # 🛑 NUEVAS EXCLUSIONES
]

# 🎯 Palabras clave deseadas
preferencias = [
    "español", "latino", "anime", "infantil", "dibujos", "comedia", "drama",
    "documental", "educativo", "cultural", "películas", "series", "musica", "cine",
    "fútbol", "deportes", "historia", "naturaleza", "estrenos", "concierto"
]

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 0  
LIMITE_BLOQUES = 100 # Se mantiene el límite para evitar categorías densas
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 

# 🗂️ Clasificación semántica extendida por nombre de canal
CLAVES_CATEGORIA = {
    "peliculas_accion": ["space", "tnt", "cinecanal", "hbo", "amc", "sony movies"],
    "peliculas_drama": ["cinemax", "studio universal", "film&arts", "paramount"],
    "peliculas_terror": ["space", "syfy", "dark tv", "horror channel"],
    "series_comedia": ["warner", "comedy central", "fx", "star channel", "sony channel"],
    "series_drama": ["universal tv", "axn", "paramount", "hbo series"],
    "anime_adultos": ["crunchyroll", "adult swim", "bitme", "senpai tv", "anime onegai"],
    "anime_infantil": ["paka paka", "discovery kids", "babytv", "boomerang"],
    "infantil_educativo": ["encuentro", "canal rural", "discovery kids", "natgeo kids"],
    "documentales_ciencia": ["discovery science", "history", "natgeo", "animal planet"],
    "documentales_cultura": ["encuentro", "canal rural", "film&arts", "arte tv"],
    "deportes_en_vivo": ["espn", "fox sports", "tyc", "tnt sports", "nba", "fútbol"],
    "deportes_extremos": ["eurosport", "red bull tv", "xtreme sports"],
    "noticias_internacionales": ["cnn", "bbc", "al jazeera", "euronews"],
    "noticias_latinoamerica": ["tn", "c5n", "a24", "cronica", "todo noticias"],
    "abiertos_arg_general": ["telefe", "el trece", "canal 13", "canal 9", "america tv", "net tv", "elnueve"],
    "musica_latina": ["qube music", "mtv latino", "concert channel", "telehit"],
    "series_24_7": ["series 24/7", "maratón", "loop", "binge"],
    "posibles_fallas": []
}

# 🌐 URL base para acceder a listas segmentadas desde GitHub
URL_BASE_SEGMENTADOS = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/segmentados"

# 🐳 Imagen por defecto (formato raw para compatibilidad IPTV)
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/beluga.png"

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
    "cine_terror": "★ TERROR ★"
}

# 🔍 Función para detectar contenido prohibido (usa la lista 'exclusiones')
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in exclusiones)

# 🧠 Clasificación dinámica si no coincide con categorías predefinidas
def clasificar_categoria_dinamica(nombre_canal):
    nombre = nombre_canal.lower()
    for categoria, claves in CLAVES_CATEGORIA.items():
        if any(clave in nombre for clave in claves):
            return categoria
    palabras = nombre.split()
    for palabra in palabras:
        if len(palabra) > 4 and palabra.isalpha():
            return f"auto_{palabra}"
    return "auto_misc"