#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Archivo: ui/prompt_updater.py

"""
Módulo para actualizar los dropdowns de estilos de prompts en todas las pestañas.
"""

def update_dropdowns_in_other_tabs(app_instance):
    """
    Actualiza los dropdowns de estilos de prompts en todas las pestañas.
    
    Args:
        app_instance: La instancia principal de VideoCreatorApp
    """
    try:
        # Verificar si la pestaña de cola de proyectos está disponible
        if hasattr(app_instance, 'tab_batch'):
            # Actualizar el dropdown en la pestaña de cola de proyectos
            app_instance.tab_batch.update_prompt_styles_dropdown()
            print("Dropdown de estilos actualizado en la pestaña 'Cola de Proyectos'")
        else:
            print("La pestaña 'Cola de Proyectos' no está disponible")
    except Exception as e:
        print(f"Error al actualizar dropdowns en otras pestañas: {e}")
