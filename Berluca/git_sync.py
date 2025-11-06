# git_sync.py

import subprocess
from datetime import datetime
from config import CARPETA_SALIDA # Asegúrate de importar CARPETA_SALIDA

def sincronizar_con_git():
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    branch = f"actualizacion-{fecha}"

    print(f"\n🔄 Iniciando sincronización con Git (branch: {branch})...\n")

    try:
        # Aquí debe ir la lógica para crear/cambiar de branch
        # ... (Asumiendo que el código de branch está correcto o manejado)

        # 🛑 CORRECCIÓN CLAVE: Agregar carpeta usando CARPETA_SALIDA ("Beluga")
        subprocess.run(["git", "add", CARPETA_SALIDA], check=True)

        # Commit con mensaje automático
        # ... (código de commit)

        # Push al repositorio remoto
        # ... (código de push)

        print(f"✅ Cambios subidos correctamente al branch: {branch}\n")

    except subprocess.CalledProcessError as e:
        print("❌ Error en el comando Git. Asegúrate de estar en un repositorio Git válido.")
        print(f"Detalle del error: {e}")