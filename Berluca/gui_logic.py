# gui_logic.py

import threading
import os
from tkinter import messagebox, filedialog
import random
import subprocess

# Importaciones de la lógica de negocio refactorizada
from main import ejecutar_proceso_completo
from utils import resolver_redireccion, verificar_disponibilidad
from file_manager import leer_archivo_m3u
from m3u_core import extraer_bloques_m3u, extraer_url
from config import CARPETA_ORIGEN # Para construir rutas de verificación

# =========================================================================================
# 🔗 Paso 1: Resolver URL acortada o directa
# =========================================================================================

def resolver_url(entrada_url, resultado_url, texto_listas, boton_abrir):
    """Resuelve la redirección de una URL y actualiza la GUI."""
    url = entrada_url.get().strip()
    if not url:
        messagebox.showwarning("Advertencia", "Por favor ingresa una URL.")
        return

    url_resuelta = resolver_redireccion(url)
    resultado_url.set(url_resuelta)

    if url_resuelta.startswith("❌"):
        boton_abrir.config(state="disabled")
        texto_listas.delete("1.0", "end")
        texto_listas.insert("end", url_resuelta)
    else:
        boton_abrir.config(state="normal")
        # Aquí se podría llamar a una función para listar archivos en GitHub/Repo si fuera necesario.
        texto_listas.delete("1.0", "end")
        texto_listas.insert("end", "✅ URL resuelta correctamente. Lista lista para el procesamiento.")


# =========================================================================================
# 🚀 Paso 2: Ejecutar el Proceso Completo (HILO SECUNDARIO)
# =========================================================================================

def iniciar_proceso(resultado_url, texto_listas, contador_resultado, boton_git):
    """
    Inicia la ejecución completa de Berluca en un hilo separado para 
    evitar congelar la UI.
    """
    url = resultado_url.get().strip()
    if not url or url.startswith("❌"):
        messagebox.showwarning("Advertencia", "URL inválida o no resuelta.")
        return
        
    def tarea_pesada():
        # Limpiar y actualizar el estado
        texto_listas.delete("1.0", "end")
        texto_listas.insert("end", "🚀 PROCESAMIENTO INICIADO...")
        contador_resultado.set("Procesando...")
        boton_git.config(state="disabled")

        try:
            # LLAMADA AL ORQUESTADOR PRINCIPAL
            ejecutar_proceso_completo(url)
            
            # 💡 NOTA: La salida de 'ejecutar_proceso_completo' se imprime a consola
            # Si quieres que vaya a la GUI, debes redirigir stdout/stderr.
            
            contador_resultado.set("✅ PROCESO TERMINADO - Listo para Subir a Git.")
            boton_git.config(state="normal")
        except Exception as e:
            contador_resultado.set(f"❌ ERROR: {e}")
            messagebox.showerror("Error de Proceso", f"Ocurrió un error: {e}")
        
    # Iniciar la tarea en un hilo
    threading.Thread(target=tarea_pesada).start()


# =========================================================================================
# 🔎 Paso 3: Verificar Enlaces (Ejemplo en Hilo)
# =========================================================================================

def verificar_peliculas_series(contador_resultado):
    """Verifica la disponibilidad de una muestra de enlaces en Películas y Series."""
    
    contador_resultado.set("🔎 Verificando enlaces de películas y series...")

    def tarea_verificacion():
        # Rutas a los archivos de categoría
        rutas_verificar = [
            os.path.join(CARPETA_ORIGEN, "peliculas.m3u"), 
            os.path.join(CARPETA_ORIGEN, "series.m3u")
        ]
        
        enlaces_a_verificar = []

        for ruta in rutas_verificar:
            if os.path.exists(ruta):
                lineas = leer_archivo_m3u(ruta)
                bloques = extraer_bloques_m3u(lineas)
                for bloque in bloques:
                    url = extraer_url(bloque)
                    if url and not url.startswith("❌"):
                        enlaces_a_verificar.append(url)

        if not enlaces_a_verificar:
            contador_resultado.set("⚠️ No se encontraron enlaces en películas o series.")
            return

        # Seleccionar una muestra aleatoria (máx. 50)
        muestra = random.sample(enlaces_a_verificar, min(50, len(enlaces_a_verificar)))
        
        # Verificar concurrente (aunque usamos un loop simple aquí para simplificar)
        exitosos = 0
        fallidos = 0
        
        for url in muestra:
            if verificar_disponibilidad(url):
                exitosos += 1
            else:
                fallidos += 1
                
        total_verificado = len(muestra)

        contador_resultado.set(f"✅ {exitosos} válidos | ❌ {fallidos} fallidos | Total: {total_verificado}")

    threading.Thread(target=tarea_verificacion).start()

# =========================================================================================
# 📤 Ejecutar push al repositorio (manual o después de la compilación)
# =========================================================================================

def ejecutar_push():
    """Ejecuta la sincronización de Git."""
    
    def tarea_git():
        try:
            sincronizar_con_git()
            messagebox.showinfo("Git", "Sincronización Git completada.")
        except Exception as e:
            messagebox.showerror("Error Git", f"No se pudo completar la sincronización. Asegúrate de tener Git instalado y configurado. Error: {e}")

    threading.Thread(target=tarea_git).start()

# 🪟 Función auxiliar para abrir la carpeta de salida
def abrir_carpeta_salida():
    """Abre la carpeta de salida del proyecto Berluca."""
    from config import CARPETA_SALIDA # Importar aquí para evitar dependencias
    try:
        os.startfile(os.path.abspath(CARPETA_SALIDA))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")