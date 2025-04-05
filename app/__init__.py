# -*- coding: utf-8 -*-
"""
Paquete principal de la aplicación de creación de videos.
"""

# Import specific modules instead of circular imports
from app.video_generator import VideoGenerator

# Export these names for easier imports
__all__ = ['VideoGenerator', 'crear_video_desde_imagenes']

# Import video creation function
from .video_creator import crear_video_desde_imagenes