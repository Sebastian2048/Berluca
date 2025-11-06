# gui_core.py

import tkinter as tk
from tkinter import messagebox
import webbrowser

from gui_logic import (
    resolver_url,
    iniciar_proceso,
    verificar_peliculas_series,
    ejecutar_push,
    abrir_carpeta_salida # Nueva función
)
# Deberías agregar esta línea en gui_utils.py, pero la redefinimos en la función para simplificar
# from gui_utils import mostrar_listas_disponibles, mostrar_listas_en_release 

# 🪟 Crear ventana principal
ventana = tk.Tk()
ventana.title("Berluca IPTV") # 🌟 CAMBIO DE NOMBRE 🌟
ventana.geometry("950x600")
ventana.configure(bg="#f0f0f0")

# 🧠 Variables de estado
resultado_url = tk.StringVar()
contador_resultado = tk.StringVar()
contador_resultado.set("Listo para iniciar.")

# 🔤 Campo de entrada de URL
tk.Label(ventana, text="🔗 URL del repositorio o lista:", bg="#f0f0f0").pack(pady=5)
entrada_url = tk.Entry(ventana, textvariable=resultado_url, width=100)
entrada_url.pack(pady=5)

# 🔘 Botones principales
frame_botones = tk.Frame(ventana, bg="#f0f0f0")
frame_botones.pack(pady=5)

# Necesitamos definir 'texto_listas' y 'boton_abrir' antes de usarlo en lambdas
texto_listas = tk.Text(ventana, height=15, width=100, wrap="word")
boton_abrir = tk.Button(frame_botones, text="🌐 Abrir URL", state="disabled")
boton_git = tk.Button(frame_botones, text="📤 Subir a Git", state="disabled")

boton_resolver = tk.Button(
    frame_botones,
    text="🔍 Resolver URL",
    command=lambda: resolver_url(entrada_url, resultado_url, texto_listas, boton_abrir)
)
boton_resolver.grid(row=0, column=0, padx=5)

boton_abrir.config(
    command=lambda: webbrowser.open(resultado_url.get())
)
boton_abrir.grid(row=0, column=1, padx=5)

boton_procesar = tk.Button(
    frame_botones,
    text="🚀 Procesar listas",
    # Se pasa 'boton_git' para que la lógica lo habilite al finalizar
    command=lambda: iniciar_proceso(resultado_url, texto_listas, contador_resultado, boton_git)
)
boton_procesar.grid(row=0, column=2, padx=5)

boton_verificar = tk.Button(
    frame_botones,
    text="🔎 Verificar Películas/Series (Muestra)",
    command=lambda: verificar_peliculas_series(contador_resultado)
)
boton_verificar.grid(row=0, column=3, padx=5)

boton_git.config(
    command=ejecutar_push
)
boton_git.grid(row=0, column=4, padx=5)

boton_carpeta = tk.Button(
    frame_botones,
    text="📂 Abrir Carpeta Berluca",
    command=abrir_carpeta_salida
)
boton_carpeta.grid(row=0, column=5, padx=5)


# 📋 Área de texto para mostrar listas
tk.Label(ventana, text="💡 Estado / Log de la ejecución:", bg="#f0f0f0").pack(pady=5)
texto_listas.pack(pady=5)

# 📊 Contador de estado
tk.Label(ventana, textvariable=contador_resultado, bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=10)

# Inicializar y correr el loop de la GUI (main loop)
if __name__ == "__main__":
    ventana.mainloop()