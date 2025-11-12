# config.py
import os
from collections import defaultdict
import re

# 📁 Carpetas base utilizadas por Beluga
CARPETA_SALIDA = "Beluga" 
CARPETA_ORIGEN = os.path.join(CARPETA_SALIDA, "compilados")
CARPETA_SEGMENTADOS = os.path.join(CARPETA_SALIDA, "segmentados")
CARPETA_LOGS = os.path.join(CARPETA_SALIDA, "logs")

# 🧱 Crear carpetas si no existen
for carpeta in [CARPETA_SALIDA, CARPETA_ORIGEN, CARPETA_SEGMENTADOS, CARPETA_LOGS]:
    os.makedirs(carpeta, exist_ok=True)


# --- CONFIGURACIÓN DE SERVIDORES Y PRIORIDAD ---

# 📊 Prioridades de Estado (De mayor a menor)
PRIORIDAD_ESTADO = {
    "abierto": 3,
    "dudoso": 2,
    "fallido": 1,
    "desconocido": 0
}

# 🔢 Límite de Bloques (Canales) por Categoría y Servidor (REQUERIDO)
# 🚨 MODIFICADO: Límite muy alto para que no haya exclusión por categoría.
LIMITE_BLOQUES_CATEGORIA = 70 
LIMITE_BLOQUES_SERVIDOR_GLOBAL = 1200 
                                     
# ... (El resto de config.py se mantiene)
                                     
# 📄 Estructura de Nombramiento de Servidores
NOMBRE_BASE_SERVIDOR = "RP_Servidor"
MAX_SERVIDORES_BUSCAR = 1400 

# 🌐 URL BASE del Repositorio (Mantenida)
URL_BASE_REPOSITORIO = "https://raw.githubusercontent.com/Sebastian2048/Berluca/refs/heads/main"


# 🧹 Palabras clave para excluir contenido no deseado
exclusiones = [
    "religion", "cristo", "biblia", "jesus"
]

# 🌐 Definición de Idiomas
CLAVES_NO_ESPANOL = ["eng", "usa", "uk", "portugues", "br", "fr", "deu", "ger", "ru", "arabic", "turkish", "sub", "dub", "viet"]

# 🗂️ CLAVES_CATEGORIA (Nivel 1: Clasificación principal y específica)
# Mejorado con las categorías clave y eliminación de genéricos (variedad_gen eliminada)
CLAVES_CATEGORIA = {
    "tv_argentina": ["telefe", "el trece", "canal 13", "canal 9", "america tv", "net tv", "elnueve", "argentina", "argen"], # Mejorado
    "peliculas": ["cinecanal", "tnt", "amc", "paramount", "cinemax", "sony movies", "peliculas", "cine", "space", "sony"], # Mejorado
    "premium_ppv": ["hbo", "starz", "fox premium", "ppv", "pay per view", "movie city"], # <<-- NUEVA CATEGORÍA PRINCIPAL
    "series": ["warner", "comedy central", "fx", "star channel", "sony channel", "universal tv", "axn", "series"],
    "deportes_envivo": ["espn", "fox sports", "tyc", "tnt sports", "nba", "fútbol", "deportes", "sports"],
    "infantil_kids": ["discovery kids", "cartoon network", "disney", "nickelodeon", "paka paka", "babytv", "infantil", "kids"], # Mejorado
    "anime": ["crunchyroll", "adult swim", "bitme", "senpai tv", "anime", "manga", "otaku", "onegai", "locomotion"], # Mejorado
    "documentales": ["discovery science", "history", "natgeo", "animal planet", "documental"],
    "noticias": ["cnn", "bbc", "al jazeera", "euronews", "tn", "c5n", "a24", "cronica", "noticias"],
    "musica": ["mtv", "telehit", "qube music", "musica", "concert"],
    "roll_over": ["tv", "canal", "online", "hd"] # Descarte inicial
}

# 🗂️ CLAVES_CATEGORIA_N2 (Nivel 2: Reforzado para re-clasificar los bloques que caen en 'roll_over')
CLAVES_CATEGORIA_N2 = {
    # Nuevas categorías para descomponer el Roll Over
    "peliculas_clasicas": ["classic", "oro", "antiguo", "retro", "vintage"],
    "peliculas_premiun": ["hbo", "space", "universal", "paramount", "cinemax", "amc", "movie"],
    "deportes_lucha": ["wwe", "aew", "ufc", "box", "lucha", "mma"],
    "deportes_motor": ["f1", "nascar", "rally", "motor", "coche", "moto"],
    "cultura_hogar": ["cocina", "hogar", "decoracion", "recetas", "gourmet"],
    
    # Clasificación por Países/Regiones
    "tv_mexico": ["mexico", "mex", "azteca", "televisa", "galavision", "tv azteca"],
    "tv_colombia": ["colombia", "rcn", "caracol", "canal uno"],
    "tv_peru": ["peru", "america tv", "atv", "latina"],
    "tv_chile": ["chile", "tvn", "canal 13", "mega"],
    "tv_espana": ["espana", "tve", "antena 3", "la sexta"],
    
    # Clasificación por Contenido Genérico (si no se detectó en Nivel 1)
    "documentales_gen": ["ciencia", "animales", "misterio", "historia"],
    "musica_gen": ["hit", "pop", "rock", "clasic", "reguetton"],
    # ELIMINADA: "variedad_gen"
}

# 🖼️ Logos y Títulos (Necesario para la escritura del M3U)
LOGO_DEFAULT = "https://raw.githubusercontent.com/Sebastian2048/Berluca/main/beluga.png"

TITULOS_VISUALES = {
    "tv_argentina": "★ TV ARGENTINA ★",
    "peliculas": "★ CINE Y PELÍCULAS ★",
    "premium_ppv": "💎 CANALES PREMIUM (HBO, STARZ, etc.) 💎", # <<-- NUEVO TÍTULO
    "series": "★ SERIES DE TV ★",
    "deportes_envivo": "★ DEPORTES EN VIVO ★",
    "infantil_kids": "★ INFANTILES Y KIDS ★",
    "anime": "★ ANIME Y OTAKU ★", # Mejorado
    "documentales": "★ DOCUMENTALES ★",
    "noticias": "★ NOTICIAS GLOBAL ★",
    "musica": "★ MÚSICA GENERAL ★",
    "roll_over": "★ CANALES ABIERTOS/SIN CLASIFICAR ★", # Reforzado para ser un cajón de sastre
    
    # Títulos Nivel 2 (Se mantiene el resto, excepto "variedad_gen")
    "tv_mexico": "★ TV MÉXICO ★",
    "tv_colombia": "★ TV COLOMBIA ★",
    "tv_peru": "★ TV PERÚ ★",
    "tv_chile": "★ TV CHILE ★",
    "tv_espana": "★ TV ESPAÑA ★",
    "peliculas_clasicas": "★ CINE CLÁSICO ★",
    "peliculas_premiun": "★ CINE PREMIUM ★",
    "deportes_lucha": "★ DEPORTES LUCHA ★",
    "deportes_motor": "★ DEPORTES MOTOR ★",
    "cultura_hogar": "★ CULTURA Y HOGAR ★",
    "documentales_gen": "★ DOCUMENTALES VARIOS ★",
    "musica_gen": "★ MÚSICA VARIOS ★",
    # ELIMINADA: "variedad_gen"
}

# 🔍 Función para detectar exclusiones
def contiene_exclusion(texto):
    texto = texto.lower()
    return any(palabra in texto for palabra in exclusiones)