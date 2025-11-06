# auditor_visual.py

from typing import List
import re

# Importaciones de config para metadatos por defecto
from config import TITULOS_VISUALES, LOGOS_CATEGORIA, LOGO_DEFAULT

# =========================================================================================
# 🖼️ AUDITORÍA DE METADATOS VISUALES
# =========================================================================================

def auditar_bloque_visual(bloque_saneado: List[str], categoria: str) -> List[str]:
    """
    Asegura que el bloque M3U tenga tvg-logo y group-title basados en la categoría.
    Retorna el bloque M3U con los metadatos visuales asegurados.
    """
    extinf_line = bloque_saneado[0]
    
    # 1. Determinar metadatos por defecto basados en la categoría
    base_cat = categoria.split("_")[0] # Usar la primera parte para títulos/logos
    titulo_visual = TITULOS_VISUALES.get(categoria, TITULOS_VISUALES.get(base_cat, f"★ {categoria.replace('_', ' ').upper()} ★"))
    logo_visual = LOGOS_CATEGORIA.get(categoria, LOGOS_CATEGORIA.get(base_cat, LOGO_DEFAULT))
    
    # 2. Asegurar tvg-logo
    if 'tvg-logo="' not in extinf_line:
        extinf_line = extinf_line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-logo="{logo_visual}"', 1)
    
    # 3. Asegurar group-title
    if 'group-title="' not in extinf_line:
        extinf_line = extinf_line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{titulo_visual}"', 1)
    
    # 4. Limpieza final de espacios o duplicados
    extinf_line = re.sub(r'\s+', ' ', extinf_line) 
    
    return [extinf_line] + bloque_saneado[1:] # Reemplaza el EXTINF y mantiene la URL