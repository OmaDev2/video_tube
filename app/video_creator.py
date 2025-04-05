#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para crear videos desde imágenes, evitando importaciones circulares.
"""

from app.video_generator import VideoGenerator

def crear_video_desde_imagenes(project_folder, **kwargs):
    """
    Función wrapper para crear video desde imágenes usando VideoGenerator.
    
    Args:
        project_folder: Ruta a la carpeta del proyecto
        **kwargs: Argumentos adicionales para la generación del video
        
    Returns:
        str: Ruta al video generado o None si hubo error
    """
    generator = VideoGenerator(project_folder)
    return generator.generate_video(**kwargs)