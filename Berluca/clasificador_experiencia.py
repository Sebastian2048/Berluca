# clasificador_experiencia.py

from typing import List, Optional

# Este módulo no necesita importar nada del Core/File Manager, 
# ya que solo se enfoca en las reglas de negocio.

# 💾 Simulación de una base de datos de canales problemáticos/preferidos.
# En una versión real, esto se cargaría desde un archivo JSON/CSV.
REGLAS_EXPERIENCIA = {
    # Si contiene estas palabras, asigna una categoría de 'baja calidad'
    "Baja_Calidad": [
        "4k-test", "no-funciona", "vod-lento", "mala-calidad", "backup-problema"
    ],
    # Si contiene estas palabras, garantiza una categoría alta
    "Alta_Calidad_Premium": [
        "hbo-max", "netflix-tv", "star-plus-hd", "disney-channel-4k"
    ]
}


def clasificar_por_experiencia(bloque: List[str], nombre_canal: str) -> Optional[str]:
    """
    Aplica reglas de clasificación basadas en un historial de calidad/etiquetas específicas.
    """
    nombre_lower = nombre_canal.lower()

    # 1. Aplicar reglas de Baja Calidad
    if any(keyword in nombre_lower for keyword in REGLAS_EXPERIENCIA["Baja_Calidad"]):
        return "sin_clasificar_baja_calidad"
    
    # 2. Aplicar reglas de Alta Calidad
    if any(keyword in nombre_lower for keyword in REGLAS_EXPERIENCIA["Alta_Calidad_Premium"]):
        return "premium_alta_calidad"

    # 3. Reglas de limpieza específicas (Ej: quitar la numeración de títulos)
    if any(c in nombre_lower for c in ["orden-", "canal-n", "c-", "tv-"]):
        return "sin_clasificar_limpieza"

    return None

# Si el clasificador principal lo necesita, se puede integrar de la siguiente manera:
# (Ver la actualización de clasificador.py más adelante)