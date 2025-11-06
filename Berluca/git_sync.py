# git_sync.py

import subprocess
from datetime import datetime

def sincronizar_con_git():
    """
    Añade, commitea y sube los cambios de la carpeta Berluca/ al repositorio Git.
    """
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    branch = f"actualizacion-{fecha}"

    print(f"\n🔄 Iniciando sincronización con Git (branch: {branch})...")

    try:
        # 1. Comprobar si hay cambios para añadir
        resultado_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not resultado_status.stdout.strip():
            print("ℹ️ No hay cambios detectados en el repositorio. Saliendo de sincronización.")
            return

        # 2. Verificar y/o crear branch
        resultado = subprocess.run(["git", "rev-parse", "--verify", branch], capture_output=True, text=True)
        if resultado.returncode == 0:
            # Ya existe: cambiar al branch (esto es inusual para branches por fecha, pero robusto)
            subprocess.run(["git", "checkout", branch], check=True)
        else:
            # No existe: crear nuevo branch
            subprocess.run(["git", "checkout", "-b", branch], check=True)

        # 3. Agregar carpeta Berluca/
        # ¡IMPORTANTE! Cambiar de Beluga a Berluca
        subprocess.run(["git", "add", "Berluca"], check=True)
        
        # 4. Agregar otros archivos de código (si aplica, se usa -A para todo)
        # subprocess.run(["git", "add", "-A"], check=True) 

        # 5. Commit con mensaje automático
        subprocess.run(["git", "commit", "-m", f"Actualización automática Berluca {fecha}"], check=True)

        # 6. Push al repositorio remoto
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)

        print(f"✅ Cambios subidos correctamente al branch: {branch}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error en el comando Git. Asegúrate de estar en un repositorio Git válido.")
        print(f"Detalle del error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado durante la sincronización Git: {e}")