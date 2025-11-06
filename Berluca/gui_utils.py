# gui_utils.py

import requests
import re
import webbrowser
import tkinter as tk
from tkinter import messagebox

# Importar utils si es necesario, asumo que obtener_assets_de_release está allí
from utils import obtener_assets_de_release # Asumo que esta función está en utils.py

# Las variables compartidas deben pasarse como argumentos o manejarse en gui_core
# Eliminamos las variables globales inicializadas a None

# 🌐 Abrir repositorio en navegador (Ya integrada en gui_core, pero la mantenemos aquí por si acaso)
def abrir_url(url: str):
    """Abre una URL en el navegador."""
    if url:
        webbrowser.open(url)
    else:
        messagebox.showwarning("Advertencia", "No hay URL para abrir.")


# 📂 Mostrar listas desde releases (Necesita los widgets de tkinter)
def mostrar_listas_en_release(url_repo: str, texto_listas: tk.Text):
    """Obtiene y muestra los assets de releases de GitHub."""
    texto_listas.delete("1.0", "end")
    try:
        listas = obtener_assets_de_release(url_repo)
        if listas:
            texto_listas.insert("end", "✅ Listas M3U en Releases:\n")
            texto_listas.insert("end", "\n".join(listas))
        else:
            texto_listas.insert("end", "⚠️ No se encontraron listas .m3u en los releases.")
    except Exception as e:
         texto_listas.insert("end", f"❌ Error al buscar assets: {e}")

# 📂 Mostrar listas desde el repositorio principal (si la URL es un repositorio)
def mostrar_listas_disponibles(url_repo: str, texto_listas: tk.Text):
    """Busca y muestra archivos .m3u en la página principal del repositorio."""
    texto_listas.delete("1.0", "end")

    if "github.com" not in url_repo:
        texto_listas.insert("end", "❌ La URL no parece ser un repositorio válido de GitHub.")
        return

    try:
        r = requests.get(url_repo)
        if r.status_code != 200:
            texto_listas.insert("end", f"❌ Error HTTP {r.status_code} al acceder al repositorio.")
            return

        # Buscar archivos .m3u en la respuesta HTML
        archivos = re.findall(r'href="[^\"]+\\.m3u\"', r.text)
        nombres = [a.split('"')[1].split("/")[-1] for a in archivos]

        if nombres:
            texto_listas.insert("end", "✅ Archivos .m3u detectados en el repositorio:\n")
            texto_listas.insert("end", "\n".join(nombres))
        else:
            texto_listas.insert("end", "⚠️ No se encontraron archivos .m3u en el directorio principal.")

    except Exception as e:
        texto_listas.insert("end", f"❌ Error de conexión o parsing: {e}")