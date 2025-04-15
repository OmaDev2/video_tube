# -*- coding: utf-8 -*-
# Archivo: project_manager.py

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

class ProjectManager:
    """
    Clase para gestionar la carga y guardado de proyectos.
    """
    def __init__(self, app_instance):
        """
        Inicializa el gestor de proyectos.
        
        Args:
            app_instance: La instancia principal de la aplicación para acceder a sus variables y métodos.
        """
        self.app = app_instance
        self.current_project_path = None
        self.project_settings = {}
    
    def select_project_folder(self):
        """
        Permite al usuario seleccionar una carpeta de proyecto existente.
        
        Returns:
            str: Ruta a la carpeta de proyecto seleccionada o None si se canceló.
        """
        folder_path = filedialog.askdirectory(
            title="Seleccionar Carpeta de Proyecto",
            initialdir=os.path.expanduser("~")
        )
        
        if folder_path:
            # Verificar si es una carpeta de proyecto válida
            settings_path = os.path.join(folder_path, "settings.json")
            images_folder = os.path.join(folder_path, "imagenes")
            
            if not os.path.exists(images_folder):
                messagebox.showerror(
                    "Error",
                    f"La carpeta seleccionada no contiene una subcarpeta 'imagenes' y no parece ser un proyecto válido."
                )
                return None
            
            self.current_project_path = folder_path
            print(f"Proyecto seleccionado: {folder_path}")
            
            # Cargar configuración si existe
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        self.project_settings = json.load(f)
                    print("Configuración del proyecto cargada.")
                except Exception as e:
                    print(f"Error al cargar configuración del proyecto: {e}")
                    self.project_settings = {}
            else:
                self.project_settings = {}
                
            return folder_path
        
        return None
    
    def load_project_settings(self, project_path=None):
        """
        Carga las configuraciones del proyecto a la aplicación.
        
        Args:
            project_path: Ruta opcional al proyecto. Si no se proporciona, se usa self.current_project_path.
            
        Returns:
            bool: True si se cargó correctamente, False en caso contrario.
        """
        if project_path:
            self.current_project_path = project_path
        
        if not self.current_project_path:
            print("No hay proyecto seleccionado.")
            return False
        
        settings_path = os.path.join(self.current_project_path, "settings.json")
        
        if not os.path.exists(settings_path):
            print(f"No se encontró archivo settings.json en {self.current_project_path}")
            return False
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Aplicar configuraciones a la aplicación
            self._apply_settings_to_app(settings)
            
            print(f"Configuración cargada desde {settings_path}")
            return True
            
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            return False
    
    def _apply_settings_to_app(self, settings):
        """
        Aplica las configuraciones cargadas a las variables de la aplicación.
        
        Args:
            settings: Diccionario con las configuraciones del proyecto.
        """
        # Mapping de las claves de configuración a las variables de la aplicación
        mapping = {
            # Configuraciones básicas
            "duracion_img": self.app.duracion_img,
            "fps": self.app.fps,
            "aplicar_efectos": self.app.aplicar_efectos,
            
            # Secuencia de efectos
            "efectos_seleccionados": self.app.efectos_seleccionados,
            
            # Transiciones
            "aplicar_transicion": self.app.aplicar_transicion,
            "tipo_transicion": self.app.tipo_transicion,
            "duracion_transicion": self.app.duracion_transicion,
            
            # Fade in/out video
            "aplicar_fade_in": self.app.aplicar_fade_in,
            "duracion_fade_in": self.app.duracion_fade_in,
            "aplicar_fade_out": self.app.aplicar_fade_out,
            "duracion_fade_out": self.app.duracion_fade_out,
            
            # Música
            "aplicar_musica": self.app.aplicar_musica,
            "archivo_musica": self.app.archivo_musica,
            "volumen_musica": self.app.volumen_musica,
            "aplicar_fade_in_musica": self.app.aplicar_fade_in_musica,
            "duracion_fade_in_musica": self.app.duracion_fade_in_musica,
            "aplicar_fade_out_musica": self.app.aplicar_fade_out_musica,
            "duracion_fade_out_musica": self.app.duracion_fade_out_musica,
            
            # Voz
            "archivo_voz": self.app.archivo_voz,
            "volumen_voz": self.app.volumen_voz,
            "aplicar_fade_in_voz": self.app.aplicar_fade_in_voz,
            "duracion_fade_in_voz": self.app.duracion_fade_in_voz,
            "aplicar_fade_out_voz": self.app.aplicar_fade_out_voz,
            "duracion_fade_out_voz": self.app.duracion_fade_out_voz,
            
            # Subtítulos
            "aplicar_subtitulos": self.app.aplicar_subtitulos,
            "archivo_subtitulos": self.app.archivo_subtitulos,
            "settings_subtitles_font_size": self.app.settings_subtitles_font_size,
            "settings_subtitles_font_color": self.app.settings_subtitles_font_color,
            "settings_subtitles_stroke_color": self.app.settings_subtitles_stroke_color, 
            "settings_subtitles_stroke_width": self.app.settings_subtitles_stroke_width,
            "settings_subtitles_align": self.app.settings_subtitles_align,
            "settings_subtitles_position_h": self.app.settings_subtitles_position_h,
            "settings_subtitles_position_v": self.app.settings_subtitles_position_v,
            "settings_subtitles_margin": self.app.settings_subtitles_margin
        }
        
        # Si están disponibles las configuraciones para fuentes
        if hasattr(self.app, 'settings_subtitles_font_name'):
            mapping["settings_subtitles_font_name"] = self.app.settings_subtitles_font_name
        
        if hasattr(self.app, 'settings_use_system_font'):
            mapping["settings_use_system_font"] = self.app.settings_use_system_font
            
        # Opción de subtítulos en mayúsculas
        if hasattr(self.app, 'subtitles_uppercase'):
            mapping["subtitles_uppercase"] = self.app.subtitles_uppercase
        
        # Aplicar cada configuración si está presente en el archivo settings.json
        for key, var in mapping.items():
            if key in settings:
                try:
                    if isinstance(var, tk.BooleanVar):
                        var.set(bool(settings[key]))
                    elif isinstance(var, tk.StringVar):
                        var.set(str(settings[key]))
                    elif isinstance(var, tk.DoubleVar):
                        var.set(float(settings[key]))
                    elif isinstance(var, tk.IntVar):
                        var.set(int(settings[key]))
                    else:
                        print(f"Tipo de variable no soportado para {key}: {type(var)}")
                except Exception as e:
                    print(f"Error al aplicar configuración {key}: {e}")
    
    def save_project_settings(self):
        """
        Guarda las configuraciones actuales de la aplicación en el archivo settings.json.
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if not self.current_project_path:
            print("No hay proyecto seleccionado para guardar configuración.")
            return False
        
        settings_path = os.path.join(self.current_project_path, "settings.json")
        
        # Recopilar configuraciones actuales
        settings = self._get_app_settings()
        
        try:
            # Guardar configuraciones en archivo JSON
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            print(f"Configuración guardada en {settings_path}")
            return True
            
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            return False
    
    def _get_app_settings(self):
        """
        Recopila las configuraciones actuales de la aplicación.
        
        Returns:
            dict: Diccionario con las configuraciones.
        """
        settings = {
            # Configuraciones básicas
            "duracion_img": self.app.duracion_img.get(),
            "fps": self.app.fps.get(),
            "aplicar_efectos": self.app.aplicar_efectos.get(),
            
            # Secuencia de efectos (convertir ListVar a lista)
            "efectos_seleccionados": list(self.app.efectos_seleccionados.get()),
            
            # Transiciones
            "aplicar_transicion": self.app.aplicar_transicion.get(),
            "tipo_transicion": self.app.tipo_transicion.get(),
            "duracion_transicion": self.app.duracion_transicion.get(),
            
            # Fade in/out video
            "aplicar_fade_in": self.app.aplicar_fade_in.get(),
            "duracion_fade_in": self.app.duracion_fade_in.get(),
            "aplicar_fade_out": self.app.aplicar_fade_out.get(),
            "duracion_fade_out": self.app.duracion_fade_out.get(),
            
            # Música
            "aplicar_musica": self.app.aplicar_musica.get(),
            "archivo_musica": self.app.archivo_musica.get(),
            "volumen_musica": self.app.volumen_musica.get(),
            "aplicar_fade_in_musica": self.app.aplicar_fade_in_musica.get(),
            "duracion_fade_in_musica": self.app.duracion_fade_in_musica.get(),
            "aplicar_fade_out_musica": self.app.aplicar_fade_out_musica.get(),
            "duracion_fade_out_musica": self.app.duracion_fade_out_musica.get(),
            
            # Voz
            "archivo_voz": self.app.archivo_voz.get(),
            "volumen_voz": self.app.volumen_voz.get(),
            "aplicar_fade_in_voz": self.app.aplicar_fade_in_voz.get(),
            "duracion_fade_in_voz": self.app.duracion_fade_in_voz.get(),
            "aplicar_fade_out_voz": self.app.aplicar_fade_out_voz.get(),
            "duracion_fade_out_voz": self.app.duracion_fade_out_voz.get(),
            
            # Subtítulos
            "aplicar_subtitulos": self.app.aplicar_subtitulos.get(),
            "archivo_subtitulos": self.app.archivo_subtitulos.get(),
            "settings_subtitles_font_size": self.app.settings_subtitles_font_size.get(),
            "settings_subtitles_font_color": self.app.settings_subtitles_font_color.get(),
            "settings_subtitles_stroke_color": self.app.settings_subtitles_stroke_color.get(),
            "settings_subtitles_stroke_width": self.app.settings_subtitles_stroke_width.get(),
            "settings_subtitles_align": self.app.settings_subtitles_align.get(),
            "settings_subtitles_position_h": self.app.settings_subtitles_position_h.get(),
            "settings_subtitles_position_v": self.app.settings_subtitles_position_v.get(),
            "settings_subtitles_margin": self.app.settings_subtitles_margin.get(),
            "subtitles_uppercase": self.app.subtitles_uppercase.get() if hasattr(self.app, 'subtitles_uppercase') else False
        }
        
        # Añadir configuraciones de fuentes si están disponibles
        if hasattr(self.app, 'settings_subtitles_font_name'):
            settings["settings_subtitles_font_name"] = self.app.settings_subtitles_font_name.get()
        
        if hasattr(self.app, 'settings_use_system_font'):
            settings["settings_use_system_font"] = self.app.settings_use_system_font.get()
        
        return settings