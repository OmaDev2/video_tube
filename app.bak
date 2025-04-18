#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal para la creación de videos a partir de imágenes.
Este archivo proporciona compatibilidad con el código existente.
"""

import os
from pathlib import Path

# Importamos las clases y funciones necesarias
try:
    from app.video_generator import VideoGenerator
except ImportError:
    # Si no se puede importar desde app, asumimos que estamos ejecutando el script directamente
    # o que la estructura de carpetas no está configurada correctamente
    print("ADVERTENCIA: No se pudo importar VideoGenerator desde el paquete app.")
    print("Asegúrate de tener la estructura de carpetas correcta o de importar VideoGenerator directamente.")
    
    # Importamos aquí directamente las dependencias necesarias
    from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, vfx
    from moviepy.audio import fx as afx
    import os
    from glob import glob
    from pathlib import Path
    from efectos import ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, FlipEffect, PanRightEffect, KenBurnsEffect, VignetteZoomEffect, RotateEffect
    from transiciones import TransitionEffect
    from overlay_effects import OverlayEffect
    from subtitles import SubtitleEffect


from app.video_creator import crear_video_desde_imagenes