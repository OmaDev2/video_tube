# -*- coding: utf-8 -*-
# Archivo: ui/prompt_updater.py

import tkinter as tk
from tkinter import ttk

def update_dropdowns_in_other_tabs(app_instance):
    """
    Busca y actualiza los Combobox de selección de estilo en diferentes pestañas.

    Args:
        app_instance: La instancia principal de VideoCreatorApp.
    """
    print("INFO: Intentando actualizar dropdowns de estilos...")
    try:
        from prompt_manager import PromptManager # Importar aquí para evitar dependencia circular
        manager = PromptManager()
        style_names_tuples = manager.get_prompt_names()
        style_names = [name for _, name in style_names_tuples]
        style_map = dict(style_names_tuples) # Mapa de nombre a ID
        print(f"INFO: Estilos obtenidos para actualizar: {style_names}")

        # Buscar y actualizar Combobox en BatchTabFrame (Estilo Imágenes)
        if hasattr(app_instance, 'tab_batch') and hasattr(app_instance.tab_batch, 'prompt_style_dropdown'):
            print("INFO: Actualizando dropdown de Estilo Imágenes en BatchTab...")
            current_selection = app_instance.tab_batch.prompt_style_dropdown.get()
            app_instance.tab_batch.prompt_style_dropdown['values'] = style_names
            app_instance.tab_batch.prompt_style_map = dict(zip(style_names, style_map.values())) # Actualizar mapa nombre->id
            # Intentar mantener la selección si aún existe
            if current_selection in style_names:
                app_instance.tab_batch.prompt_style_dropdown.set(current_selection)
            elif style_names:
                app_instance.tab_batch.prompt_style_dropdown.current(0) # Seleccionar el primero
            else:
                 app_instance.tab_batch.prompt_style_dropdown.set("") # Limpiar si no hay estilos

        # Buscar y actualizar Combobox en BatchTabFrame (Estilo Guion)
        if hasattr(app_instance, 'tab_batch') and hasattr(app_instance.tab_batch, 'combo_estilo_script'):
            print("INFO: Actualizando dropdown de Estilo Guion en BatchTab...")
            current_selection_script = app_instance.tab_batch.combo_estilo_script.get()
            app_instance.tab_batch.combo_estilo_script['values'] = style_names
            app_instance.tab_batch.script_style_map = style_map # Actualizar mapa nombre->id
             # Intentar mantener la selección si aún existe
            if current_selection_script in style_names:
                 app_instance.tab_batch.combo_estilo_script.set(current_selection_script)
            elif style_names:
                 app_instance.tab_batch.combo_estilo_script.current(0)
            else:
                 app_instance.tab_batch.combo_estilo_script.set("")


        # Añadir aquí lógica para actualizar otros dropdowns en otras pestañas si es necesario
        # Ejemplo:
        # if hasattr(app_instance, 'tab_otra') and hasattr(app_instance.tab_otra, 'combo_estilo'):
        #    app_instance.tab_otra.combo_estilo['values'] = style_names
        #    ... (lógica similar para mantener selección) ...

        print("INFO: Actualización de dropdowns completada.")

    except ImportError:
        print("ERROR: No se pudo importar PromptManager en prompt_updater.")
    except Exception as e:
        print(f"ERROR inesperado al actualizar dropdowns: {e}")
        import traceback
        traceback.print_exc()