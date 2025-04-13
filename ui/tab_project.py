# -*- coding: utf-8 -*-
# Archivo: ui/tab_project.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
from pathlib import Path

# Importamos la clase ProjectManager
from project_manager import ProjectManager

class ProjectTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Proyecto'.
    Permite cargar proyectos existentes y regenerar videos.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de Proyecto.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)
        
        # Crear el gestor de proyectos
        self.project_manager = ProjectManager(self.app)
        
        # Variable para rastrear el proyecto actual
        self.current_project_var = tk.StringVar(value="Ningún proyecto cargado")
        
        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña de gestión de proyectos."""
        # Sección de información del proyecto
        frame_info = ttk.LabelFrame(self, text="Información del Proyecto")
        frame_info.pack(fill="x", padx=10, pady=10)
        
        # Mostrar proyecto actual
        frame_current = ttk.Frame(frame_info)
        frame_current.pack(fill="x", padx=10, pady=5)
        
        lbl_current = ttk.Label(frame_current, text="Proyecto actual:", width=15)
        lbl_current.pack(side="left", padx=5)
        
        lbl_project_path = ttk.Label(frame_current, textvariable=self.current_project_var, 
                                  foreground="#3498db", wraplength=400)
        lbl_project_path.pack(side="left", fill="x", expand=True, padx=5)
        
        # Sección para cargar proyecto
        frame_load = ttk.LabelFrame(self, text="Cargar Proyecto Existente")
        frame_load.pack(fill="x", padx=10, pady=10)
        
        # Botón para seleccionar proyecto
        btn_select = ttk.Button(frame_load, text="Seleccionar Carpeta de Proyecto", 
                             command=self._load_project)
        btn_select.pack(padx=10, pady=10)
        
        # Explicación
        lbl_explanation = ttk.Label(
            frame_load, 
            text="Al cargar un proyecto, se configurará automáticamente la aplicación\n"
                "con los ajustes guardados previamente en el archivo settings.json.",
            foreground="#7f8c8d",
            justify="center"
        )
        lbl_explanation.pack(padx=10, pady=5)
        
        # Sección para regenerar video
        frame_regenerate = ttk.LabelFrame(self, text="Regenerar Video del Proyecto")
        frame_regenerate.pack(fill="x", padx=10, pady=10)
        
        # Opción para verificar assets
        self.check_assets_var = tk.BooleanVar(value=True)
        chk_assets = ttk.Checkbutton(
            frame_regenerate, 
            text="Verificar assets antes de regenerar (recomendado)", 
            variable=self.check_assets_var
        )
        chk_assets.pack(padx=10, pady=5, anchor="w")
        
        # Opción para guardar configuración actual
        self.save_settings_var = tk.BooleanVar(value=True)
        chk_save = ttk.Checkbutton(
            frame_regenerate, 
            text="Guardar configuración actual antes de regenerar", 
            variable=self.save_settings_var
        )
        chk_save.pack(padx=10, pady=5, anchor="w")
        
        # Botón para regenerar
        btn_regenerate = ttk.Button(
            frame_regenerate, 
            text="Regenerar Video", 
            command=self._regenerate_video,
            style="Accent.TButton"
        )
        btn_regenerate.pack(padx=10, pady=10)
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            frame_regenerate, 
            orient="horizontal", 
            length=400, 
            mode="determinate", 
            variable=self.progress_var
        )
        self.progress_bar.pack(padx=10, pady=10, fill="x")
        
        # Etiqueta de estado
        self.status_var = tk.StringVar(value="Listo para regenerar video")
        lbl_status = ttk.Label(frame_regenerate, textvariable=self.status_var, foreground="#7f8c8d")
        lbl_status.pack(padx=10, pady=5)
        
        # Sección para gestión de proyectos
        frame_manage = ttk.LabelFrame(self, text="Gestión de Proyectos")
        frame_manage.pack(fill="x", padx=10, pady=10)
        
        # Botón para guardar configuración actual
        btn_save = ttk.Button(
            frame_manage, 
            text="Guardar Configuración Actual", 
            command=self._save_current_settings
        )
        btn_save.pack(padx=10, pady=10)
        
        # Explicación de guardado
        lbl_save_explanation = ttk.Label(
            frame_manage, 
            text="Guarda la configuración actual en el archivo settings.json del proyecto.\n"
                "Esto incluye efectos, transiciones, música, subtítulos, etc.",
            foreground="#7f8c8d",
            justify="center"
        )
        lbl_save_explanation.pack(padx=10, pady=5)

    def _load_project(self):
        """Carga un proyecto existente."""
        try:
            # Seleccionar carpeta de proyecto
            project_path = self.project_manager.select_project_folder()
            
            if not project_path:
                return  # Usuario canceló o carpeta inválida
            
            # Cargar configuración del proyecto
            if self.project_manager.load_project_settings(project_path):
                self.current_project_var.set(project_path)
                messagebox.showinfo(
                    "Proyecto Cargado",
                    f"El proyecto se ha cargado correctamente desde:\n{project_path}"
                )
            else:
                messagebox.showwarning(
                    "Advertencia",
                    "El proyecto se ha cargado pero no se encontró un archivo settings.json válido.\n"
                    "Se usará la configuración actual."
                )
                self.current_project_var.set(project_path)
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al cargar el proyecto: {str(e)}"
            )
    
    def _save_current_settings(self):
        """Guarda la configuración actual del proyecto."""
        if not self.project_manager.current_project_path:
            messagebox.showerror(
                "Error",
                "No hay un proyecto cargado actualmente.\n"
                "Por favor, carga un proyecto primero."
            )
            return
        
        if self.project_manager.save_project_settings():
            messagebox.showinfo(
                "Configuración Guardada",
                f"La configuración se ha guardado correctamente en:\n"
                f"{os.path.join(self.project_manager.current_project_path, 'settings.json')}"
            )
        else:
            messagebox.showerror(
                "Error",
                "No se pudo guardar la configuración del proyecto."
            )
    
    def _verify_assets(self):
        """
        Verifica que todos los assets necesarios estén disponibles.
        
        Returns:
            tuple: (bool, str) - (Éxito, Mensaje)
        """
        if not self.project_manager.current_project_path:
            return False, "No hay proyecto cargado."
        
        # Verificar subcarpeta de imágenes
        images_folder = os.path.join(self.project_manager.current_project_path, "imagenes")
        if not os.path.exists(images_folder) or not os.path.isdir(images_folder):
            return False, f"No se encontró la carpeta de imágenes: {images_folder}"
        
        # Verificar que haya imágenes
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            image_files.extend(Path(images_folder).glob(f'*{ext}'))
            image_files.extend(Path(images_folder).glob(f'*{ext.upper()}'))
        
        if not image_files:
            return False, f"No se encontraron imágenes en {images_folder}"
        
        # Verificar archivo de música si está activado
        if self.app.aplicar_musica.get():
            music_file = self.app.archivo_musica.get()
            if music_file and not os.path.exists(music_file):
                return False, f"No se encontró el archivo de música: {music_file}"
        
        # Verificar archivo de voz si está activado
        if self.app.aplicar_voz.get():
            voice_file = self.app.archivo_voz.get()
            if voice_file and not os.path.exists(voice_file):
                return False, f"No se encontró el archivo de voz: {voice_file}"
        
        # Verificar archivo de subtítulos si está activado
        if self.app.aplicar_subtitulos.get():
            subs_file = self.app.archivo_subtitulos.get()
            if subs_file and not os.path.exists(subs_file):
                return False, f"No se encontró el archivo de subtítulos: {subs_file}"
        
        return True, "Todos los assets verificados correctamente."
    
    def _update_progress(self, current, total):
        """
        Actualiza la barra de progreso.
        
        Args:
            current: Paso actual
            total: Total de pasos
        """
        if total <= 0:
            progress = 0
        else:
            progress = min(100, (current / total) * 100)
        
        self.progress_var.set(progress)
        self.status_var.set(f"Procesando... {current}/{total} ({progress:.1f}%)")
        
        # Forzar actualización de la interfaz
        self.update_idletasks()
    
    def _regenerate_video(self):
        """Regenera el video del proyecto actual."""
        # Verificar si hay un proyecto cargado
        if not self.project_manager.current_project_path:
            messagebox.showerror(
                "Error",
                "No hay un proyecto cargado actualmente.\n"
                "Por favor, carga un proyecto primero."
            )
            return
        
        # Verificar assets si está activada la opción
        if self.check_assets_var.get():
            self.status_var.set("Verificando assets...")
            self.update_idletasks()
            
            assets_ok, message = self._verify_assets()
            if not assets_ok:
                messagebox.showerror("Error", f"Error en la verificación de assets: {message}")
                self.status_var.set("Error en la verificación de assets")
                return
        
        # Guardar configuración si está activada la opción
        if self.save_settings_var.get():
            self.status_var.set("Guardando configuración...")
            self.update_idletasks()
            
            if not self.project_manager.save_project_settings():
                if not messagebox.askyesno(
                    "Advertencia",
                    "No se pudo guardar la configuración del proyecto.\n"
                    "¿Desea continuar con la regeneración de todas formas?"
                ):
                    self.status_var.set("Regeneración cancelada")
                    return
        
        # Iniciar regeneración en un hilo separado para no bloquear la interfaz
        self.status_var.set("Iniciando regeneración del video...")
        self.progress_var.set(0)
        self.update_idletasks()
        
        # Crear un hilo para la regeneración
        thread = threading.Thread(target=self._regenerate_video_thread)
        thread.daemon = True
        thread.start()
    
    def _regenerate_video_thread(self):
        """Método que se ejecuta en un hilo separado para regenerar el video."""
        try:
            # Preparar parámetros para la generación
            kwargs = {
                # Parámetros básicos
                'duracion_img': self.app.duracion_img.get(),
                'fps': self.app.fps.get(),
                'aplicar_efectos': self.app.aplicar_efectos.get(),
                'secuencia_efectos': list(self.app.efectos_seleccionados.get()),
                
                # Transiciones
                'aplicar_transicion': self.app.aplicar_transicion.get(),
                'tipo_transicion': self.app.tipo_transicion.get(),
                'duracion_transicion': self.app.duracion_transicion.get(),
                
                # Fade in/out video
                'aplicar_fade_in': self.app.aplicar_fade_in.get(),
                'duracion_fade_in': self.app.duracion_fade_in.get(),
                'aplicar_fade_out': self.app.aplicar_fade_out.get(),
                'duracion_fade_out': self.app.duracion_fade_out.get(),
                
                # Música
                'aplicar_musica': self.app.aplicar_musica.get(),
                'archivo_musica': self.app.archivo_musica.get(),
                'volumen_musica': self.app.volumen_musica.get(),
                'aplicar_fade_in_musica': self.app.aplicar_fade_in_musica.get(),
                'duracion_fade_in_musica': self.app.duracion_fade_in_musica.get(),
                'aplicar_fade_out_musica': self.app.aplicar_fade_out_musica.get(),
                'duracion_fade_out_musica': self.app.duracion_fade_out_musica.get(),
                
                # Voz
                'archivo_voz': self.app.archivo_voz.get() if self.app.aplicar_voz.get() else None,
                'volumen_voz': self.app.volumen_voz.get(),
                'aplicar_fade_in_voz': self.app.aplicar_fade_in_voz.get(),
                'duracion_fade_in_voz': self.app.duracion_fade_in_voz.get(),
                'aplicar_fade_out_voz': self.app.aplicar_fade_out_voz.get(),
                'duracion_fade_out_voz': self.app.duracion_fade_out_voz.get(),
                
                # Subtítulos
                'aplicar_subtitulos': self.app.aplicar_subtitulos.get(),
                'archivo_subtitulos': self.app.archivo_subtitulos.get(),
                'tamano_fuente_subtitulos': self.app.settings_subtitles_font_size.get(),
                'color_fuente_subtitulos': self.app.settings_subtitles_font_color.get(),
                'color_borde_subtitulos': self.app.settings_subtitles_stroke_color.get(),
                'grosor_borde_subtitulos': self.app.settings_subtitles_stroke_width.get(),
                'subtitulos_align': self.app.settings_subtitles_align.get(),
                'subtitulos_position_h': self.app.settings_subtitles_position_h.get(),
                'subtitulos_position_v': self.app.settings_subtitles_position_v.get(),
                'subtitulos_margen': self.app.settings_subtitles_margin.get(),
                
                # Fuente personalizada (si está disponible)
                'font_name': self.app.settings_subtitles_font_name.get() if hasattr(self.app, 'settings_subtitles_font_name') else None,
                'use_system_font': self.app.settings_use_system_font.get() if hasattr(self.app, 'settings_use_system_font') else False,
                
                # Callback para actualizar el progreso
                'progress_callback': self._update_progress
            }
            
            # Llamar al método de generación de video
            from app.video_creator import crear_video_desde_imagenes
            
            # Actualizar estado
            self.app.after(0, lambda: self.status_var.set("Generando video..."))
            
            # Generar el video
            output_path = crear_video_desde_imagenes(
                self.project_manager.current_project_path,
                **kwargs
            )
            
            # Actualizar la interfaz con el resultado
            if output_path:
                self.app.after(0, lambda: self.status_var.set("¡Video generado exitosamente!"))
                self.app.after(0, lambda: self.progress_var.set(100))
                self.app.after(0, lambda: messagebox.showinfo(
                    "Éxito",
                    f"El video ha sido regenerado exitosamente.\n\nGuardado en: {output_path}"
                ))
            else:
                self.app.after(0, lambda: self.status_var.set("Error al generar el video"))
                self.app.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Ocurrió un error al generar el video. Revisa la consola para más detalles."
                ))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            self.app.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.app.after(0, lambda: messagebox.showerror(
                "Error",
                f"Ocurrió un error durante la regeneración del video:\n\n{str(e)}"
            ))