import os
import datetime

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
    "religion", "evangelio", "cristo", "biblia", "jesus", "adoracion", "misa", "rosario", # Religioso
    "24h", "24/7", "perpetuo", "perpetua", "siempre", "loop", "maraton", "test", "demo", "vacio", # 24/7 y prueba
    "xxx", "porno", "erotic", "hot", "contenido_sensible" # Se mantiene 'adult' en la categoría de Anime para clasificación
]

# 🔢 Parámetros de control
MINIMO_BLOQUES_VALIDOS = 0  
LIMITE_BLOQUES = 100 
UMBRAL_EXCLUSION_ARCHIVO = 0.999999 

# ⏳ Configuración de Caducidad (Solo aplica a miscelaneo_otros)
DIAS_EXPIRACION_MISCELANEO = 7 

# 🚦 Desbordamiento Específico (Overflow)
# Define qué categoría principal debe intentar mover su excedente a una categoría_extra.
OVERFLOW_MAP = {
    "peliculas_principal": "peliculas_extras",
    "series_principal": "series_extras", 
    "deportes_en_vivo": "deportes_extras", 
}

# 🗂️ Clasificación Estricta y Amplia (INCLUYE LAS CATEGORÍAS EXTRA)
CLAVES_CATEGORIA = {
    "tv_argentina": ["telefe", "el trece", "canal 13", "canal 9", "america tv", "net tv", "elnueve"],
    
    # 🎬 Cine y Series
    "peliculas_principal": ["hbo", "cinecanal", "tnt", "amc", "paramount", "cinemax", "sony movies", "peliculas", "cine"],
    "peliculas_extras": ["película", "movie", "film"], 
    "series_principal": ["warner", "comedy central", "fx", "star channel", "sony channel", "universal tv", "axn", "series"],
    "series_extras": ["serie", "show", "episodio"],
    "cine_terror": ["syfy", "dark tv", "horror channel", "terror", "miedo"],
    
    # ⚽ Deportes
    "deportes_en_vivo": ["espn", "fox sports", "tyc", "tnt sports", "nba", "fútbol", "deportes", "sports"],
    "deportes_extras": ["liga", "canal deportivo", "deporte 2"],
    
    # 👶 Infancia y Animación
    "infantil_kids": ["discovery kids", "cartoon network", "disney", "nickelodeon", "paka paka", "babytv", "infantil"],
    "anime_general": ["crunchyroll", "adult swim", "bitme", "senpai tv", "anime", "manga", "otaku", "funimation"], 
    "anime_adulto": ["anime onegai", "h-anime", "uncensored", "hentai", "adult"], 
    
    "documentales_ciencia": ["discovery science", "history", "natgeo", "animal planet", "documental"],
    "noticias_global": ["cnn", "bbc", "al jazeera", "euronews", "tn", "c5n", "a24", "cronica", "noticias"],
    
    "musica_general": ["mtv", "telehit", "qube music", "musica", "concert"],
    
    "miscelaneo_otros": ["tv", "canal", "online", "hd"] # Último recurso
}

# 🌐 URL base para acceder a listas segmentadas desde GitHub (Se mantiene)
URL_BASE_SEGMENTADOS = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/segmentados"

# 🐳 Imagen por defecto
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Beluga/main/beluga.png"

# 🖼️ Logos específicos por categoría (Puedes expandir esto)
LOGOS_CATEGORIA = {
    "tv_argentina": LOGO_DEFAULT, "peliculas_principal": LOGO_DEFAULT,
    "series_principal": LOGO_DEFAULT, "deportes_en_vivo": LOGO_DEFAULT
}

# ✨ Títulos visuales por categoría (AÑADIDOS LOS EXTRAS)
TITULOS_VISUALES = {
    "tv_argentina": "★ TV ARGENTINA ★",
    "peliculas_principal": "★ CINE Y PELÍCULAS ★",
    "peliculas_extras": "★ CINE EXTRA (Desbordamiento) ★",
    "series_principal": "★ SERIES DE TV ★",
    "series_extras": "★ SERIES EXTRA (Desbordamiento) ★",
    "deportes_en_vivo": "★ DEPORTES EN VIVO ★",
    "deportes_extras": "★ DEPORTES EXTRA (Desbordamiento) ★",
    "anime_adulto": "★ ANIME ADULTO ★",
    "documentales_ciencia": "★ DOCUMENTALES Y CIENCIA ★",
    "noticias_global": "★ NOTICIAS GLOBAL ★",
    "musica_general": "★ MÚSICA GENERAL ★",
    "infantil_kids": "★ INFANTILES KIDS ★",
    "cine_terror": "★ CINE TERROR ★",
    "miscelaneo_otros": "★ OTROS CANALES (Misceláneo/Temporal) ★",
}

# 🔍 Función para detectar exclusiones
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in exclusiones)