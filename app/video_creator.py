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
    print(f"DEBUG video_creator: Recibidos kwargs claves: {list(kwargs.keys())}")
    
    # Extraer el diccionario anidado 'settings' de kwargs
    effect_settings = kwargs.get('settings', {})
    print(f"DEBUG video_creator: Ajustes de efectos extraídos: {effect_settings}")
    
    # Crear el generador de video pasando project_folder y effect_settings
    generator = VideoGenerator(project_folder, effect_settings)
    
    # Llamar a generate_video con todos los kwargs originales
    return generator.generate_video(**kwargs)