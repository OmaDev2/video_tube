# -*- coding: utf-8 -*-
# Archivo: ui/tab_batch.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import json
import time
import threading
import asyncio
import subprocess
from datetime import datetime

# Importar el gestor de prompts
try:
    from prompt_manager import PromptManager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False

# Importar el módulo de TTS
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tts_generator import text_chunk_to_speech
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class BatchTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Cola de Proyectos'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de cola de proyectos.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la pestaña de cola de proyectos para TTS."""
        # --- Sección de Entrada ---
        frame_input = ttk.LabelFrame(self, text="Nuevo Proyecto")
        frame_input.pack(fill="x", padx=10, pady=10)

        # Título del proyecto
        lbl_title = ttk.Label(frame_input, text="Título:")
        lbl_title.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_title = ttk.Entry(frame_input, width=60)
        self.entry_title.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Selección de voz
        lbl_voice = ttk.Label(frame_input, text="Voz:")
        lbl_voice.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Lista de voces disponibles (puedes ampliar esta lista)
        voces = [
            "es-EC-LuisNeural",  # Ecuador (masculino)
            "es-ES-ElviraNeural",  # España (femenino)
            "es-MX-DaliaNeural",  # México (femenino)
            "es-AR-ElenaNeural",  # Argentina (femenino)
            "es-CO-GonzaloNeural",  # Colombia (masculino)
            "es-CL-CatalinaNeural",  # Chile (femenino)
            "es-MX-JorgeNeural",  # México (masculino)
        ]
        
        # Selección de estilo de prompts
        lbl_prompt_style = ttk.Label(frame_input, text="Estilo de Imágenes:")
        lbl_prompt_style.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Crear variable para el estilo de prompts si no existe
        if not hasattr(self.app, 'selected_prompt_style'):
            self.app.selected_prompt_style = tk.StringVar(value="Cinematográfico")  # Usar el nombre mostrado, no el ID
        
        # Obtener estilos de prompts disponibles
        prompt_styles = [("default", "Cinematográfico")]
        if PROMPT_MANAGER_AVAILABLE:
            try:
                prompt_manager = PromptManager()
                prompt_styles = prompt_manager.get_prompt_names()
                
                # Imprimir información de depuración sobre los estilos disponibles
                #print("\n\n=== ESTILOS DE PROMPTS DISPONIBLES ===")
                #for i, (id, name) in enumerate(prompt_styles):
                #print(f"  {i+1}. ID: '{id}', Nombre: '{name}'")
            except Exception as e:
                print(f"Error al cargar estilos de prompts: {e}")
        
        self.app.selected_voice = tk.StringVar(value="es-MX-JorgeNeural")
        voice_combo = ttk.Combobox(frame_input, textvariable=self.app.selected_voice, values=voces, width=30)
        voice_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Dropdown para estilos de prompts
        prompt_style_values = [name for _, name in prompt_styles]
        prompt_style_ids = [id for id, _ in prompt_styles]
        self.prompt_style_dropdown = ttk.Combobox(frame_input, textvariable=self.app.selected_prompt_style, 
                                              values=prompt_style_values, width=30, state="readonly")
        self.prompt_style_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Mapeo de nombres a IDs para recuperar el ID correcto
        self.prompt_style_map = dict(zip(prompt_style_values, prompt_style_ids))
        
        # Imprimir el mapeo para depuración
        #print("\n=== MAPEO DE NOMBRES A IDS ===")
        #for name, id in self.prompt_style_map.items():
        #    print(f"  Nombre: '{name}' -> ID: '{id}'")
            
        # Configurar un callback para cuando cambie el estilo seleccionado
        def on_prompt_style_change(event):
            selected_name = self.prompt_style_dropdown.get()
            selected_id = self.prompt_style_map.get(selected_name, "default")
            print(f"\nEstilo seleccionado: Nombre='{selected_name}', ID='{selected_id}'")
            
        self.prompt_style_dropdown.bind("<<ComboboxSelected>>", on_prompt_style_change)

        # Guion del proyecto
        lbl_script = ttk.Label(frame_input, text="Guion:")
        lbl_script.grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        
        # Frame para el Text y Scrollbar
        frame_text = ttk.Frame(frame_input)
        frame_text.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")
        frame_input.grid_columnconfigure(1, weight=1)  # Hacer que columna 1 se expanda
        frame_input.grid_rowconfigure(3, weight=1)     # Hacer que fila 3 se expanda

        self.txt_script = tk.Text(frame_text, wrap="word", height=15, width=60)
        scrollbar_script = ttk.Scrollbar(frame_text, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar_script.set)
        self.txt_script.pack(side="left", fill="both", expand=True)
        scrollbar_script.pack(side="right", fill="y")
        
        # Checkbox para subtítulos
        frame_subtitles = ttk.Frame(frame_input)
        frame_subtitles.grid(row=3, column=2, padx=5, pady=5, sticky="nw")
        
        chk_subtitles = ttk.Checkbutton(frame_subtitles, text="Generar subtítulos", 
                                      variable=self.app.aplicar_subtitulos)
        chk_subtitles.pack(side="top", anchor="w", padx=5, pady=5)
        
        # Frame para controles de voz (rate y pitch)
        frame_voice_controls = ttk.LabelFrame(frame_input, text="Ajustes de Voz")
        frame_voice_controls.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Variables numéricas para los sliders (valores internos)
        if not hasattr(self.app, 'tts_rate_value'):
            self.app.tts_rate_value = tk.IntVar(value=-10)  # Valor por defecto: -10% (un poco más lento)
        if not hasattr(self.app, 'tts_pitch_value'):
            self.app.tts_pitch_value = tk.IntVar(value=-5)  # Valor por defecto: -5Hz (tono ligeramente más bajo)
        
        # Función para convertir valor del slider a formato de edge-tts
        def update_rate_str(*args):
            rate_val = self.app.tts_rate_value.get()
            if rate_val >= 0:
                self.app.tts_rate_str.set(f"+{rate_val}%")
            else:
                self.app.tts_rate_str.set(f"{rate_val}%")
            lbl_rate_value.config(text=self.app.tts_rate_str.get())
        
        def update_pitch_str(*args):
            pitch_val = self.app.tts_pitch_value.get()
            if pitch_val >= 0:
                self.app.tts_pitch_str.set(f"+{pitch_val}Hz")
            else:
                self.app.tts_pitch_str.set(f"{pitch_val}Hz")
            lbl_pitch_value.config(text=self.app.tts_pitch_str.get())
        
        # Vincular las variables para que se actualicen automáticamente
        self.app.tts_rate_value.trace_add("write", update_rate_str)
        self.app.tts_pitch_value.trace_add("write", update_pitch_str)
        
        # Control de velocidad (Rate)
        lbl_rate = ttk.Label(frame_voice_controls, text="Velocidad:")
        lbl_rate.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Frame para slider y su valor
        rate_frame = ttk.Frame(frame_voice_controls)
        rate_frame.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Slider para Rate
        scale_rate = ttk.Scale(rate_frame, from_=-50, to=50, orient="horizontal", 
                             variable=self.app.tts_rate_value, length=200)
        scale_rate.pack(side="left", padx=5)
        
        # Etiqueta para mostrar el valor actual
        lbl_rate_value = ttk.Label(rate_frame, text=self.app.tts_rate_str.get(), width=6)
        lbl_rate_value.pack(side="left", padx=5)
        
        # Control de tono (Pitch)
        lbl_pitch = ttk.Label(frame_voice_controls, text="Tono:")
        lbl_pitch.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Frame para slider y su valor
        pitch_frame = ttk.Frame(frame_voice_controls)
        pitch_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Slider para Pitch
        scale_pitch = ttk.Scale(pitch_frame, from_=-50, to=50, orient="horizontal", 
                              variable=self.app.tts_pitch_value, length=200)
        scale_pitch.pack(side="left", padx=5)
        
        # Etiqueta para mostrar el valor actual
        lbl_pitch_value = ttk.Label(pitch_frame, text=self.app.tts_pitch_str.get(), width=6)
        lbl_pitch_value.pack(side="left", padx=5)
        
        # Botón de vista previa
        btn_preview = ttk.Button(frame_voice_controls, text="Probar Voz", 
                               command=self._preview_voice, style="Secondary.TButton")
        btn_preview.grid(row=2, column=1, padx=5, pady=10, sticky="e")
        
        # Inicializar los valores de los sliders
        update_rate_str()
        update_pitch_str()
        
        # Botones de acción
        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=5, column=1, padx=5, pady=10, sticky="e")
        
        btn_add_queue = ttk.Button(frame_buttons, text="Añadir a la Cola",
                                  command=self._add_project_to_queue, style="Action.TButton")
        btn_add_queue.pack(side="right", padx=5)
        
        btn_clear = ttk.Button(frame_buttons, text="Limpiar Campos",
                              command=self._clear_project_fields, style="Secondary.TButton")
        btn_clear.pack(side="right", padx=5)

        # --- Sección de Cola ---
        frame_queue = ttk.LabelFrame(self, text="Cola de Procesamiento")
        frame_queue.pack(fill="both", expand=True, padx=10, pady=10)

        # Usaremos un Treeview para mostrar la cola
        self.app.tree_queue = ttk.Treeview(frame_queue, columns=("titulo", "estado", "tiempo"), 
                                          show="headings", height=8)  # Reducir altura para que ocupe menos espacio
        self.app.tree_queue.heading("titulo", text="Título del Proyecto")
        self.app.tree_queue.heading("estado", text="Estado")
        self.app.tree_queue.heading("tiempo", text="Tiempo")
        self.app.tree_queue.column("titulo", width=400)
        self.app.tree_queue.column("estado", width=150, anchor="center")
        self.app.tree_queue.column("tiempo", width=100, anchor="center")

        # Frame para contener el Treeview y su scrollbar
        frame_treeview = ttk.Frame(frame_queue)
        frame_treeview.pack(fill="both", expand=True, pady=(0, 5))
        
        # Scrollbar para el Treeview
        scrollbar_queue = ttk.Scrollbar(frame_treeview, orient="vertical", command=self.app.tree_queue.yview)
        self.app.tree_queue.configure(yscrollcommand=scrollbar_queue.set)

        self.app.tree_queue.pack(side="left", fill="both", expand=True)
        scrollbar_queue.pack(side="right", fill="y")
        
        # --- BARRA DE HERRAMIENTAS DE ACCIONES ---
        # Primero crear un frame para los botones principales
        frame_botones_principales = ttk.Frame(frame_queue)
        frame_botones_principales.pack(fill="x", pady=(5, 0))
        
        # Botón para cargar proyectos existentes
        btn_cargar_proyecto = ttk.Button(frame_botones_principales,
                                      text="Cargar Proyecto Existente",
                                      command=self._cargar_proyecto_existente,
                                      style="Secondary.TButton")
        btn_cargar_proyecto.pack(side="left", padx=5, pady=5)
        
        # Botón para generar vídeo
        btn_generate_video = ttk.Button(frame_botones_principales,
                                      text="Generar Vídeo",
                                      command=self.app.trigger_video_generation_for_selected,
                                      style="Action.TButton")
        btn_generate_video.pack(side="right", padx=5, pady=5)
        
        # --- BARRA DE HERRAMIENTAS DE REGENERACIÓN ---
        # Crear un frame para los botones de regeneración
        frame_regeneracion = ttk.Frame(frame_queue)
        frame_regeneracion.pack(fill="x", pady=(0, 5))
        
        # Etiqueta para los botones de regeneración
        lbl_regenerar = ttk.Label(frame_regeneracion, text="Regenerar:", font=("Helvetica", 10, "bold"))
        lbl_regenerar.pack(side="left", padx=5, pady=5)
        
        # Botón para regenerar audio
        btn_regenerar_audio = ttk.Button(frame_regeneracion,
                                       text="Audio",
                                       command=self._regenerar_audio,
                                       style="Secondary.TButton",
                                       width=10)
        btn_regenerar_audio.pack(side="left", padx=5, pady=5)
        
        # Botón para regenerar prompts
        btn_regenerar_prompts = ttk.Button(frame_regeneracion,
                                        text="Prompts",
                                        command=self._regenerar_prompts,
                                        style="Secondary.TButton",
                                        width=10)
        btn_regenerar_prompts.pack(side="left", padx=5, pady=5)
        
        # Botón para regenerar imágenes
        btn_regenerar_imagenes = ttk.Button(frame_regeneracion,
                                         text="Imágenes",
                                         command=self._regenerar_imagenes,
                                         style="Secondary.TButton",
                                         width=10)
        btn_regenerar_imagenes.pack(side="left", padx=5, pady=5)
        
        # Botón para regenerar subtítulos
        btn_regenerar_subtitulos = ttk.Button(frame_regeneracion,
                                           text="Subtítulos",
                                           command=self._regenerar_subtitulos,
                                           style="Secondary.TButton",
                                           width=10)
        btn_regenerar_subtitulos.pack(side="left", padx=5, pady=5)
        
        # Asignar el Treeview al gestor de cola
        self.app.batch_tts_manager.tree_queue = self.app.tree_queue
        
        # Etiqueta de estado de la cola (mover arriba para que sea más visible)
        self.app.lbl_queue_status = ttk.Label(frame_queue, text="Cola vacía", style="Header.TLabel")
        self.app.lbl_queue_status.pack(anchor="w", padx=5, pady=(0, 5), before=frame_botones_principales)

    # En ui/tab_batch.py, reemplaza la función existente por esta:

    def _add_project_to_queue(self):
        """Añade un nuevo proyecto a la cola de procesamiento."""
        print("--- Iniciando _add_project_to_queue ---") # Debug
        title = self.entry_title.get().strip()
        script = self.txt_script.get("1.0", tk.END).strip()
        voice = self.app.selected_voice.get()

        # --- Validaciones básicas ---
        if not title:
            messagebox.showerror("Error", "Por favor, introduce un título para el proyecto.")
            return
        if not script:
            messagebox.showerror("Error", "Por favor, introduce un guion para el proyecto.")
            return

        # --- Recoger Ajustes Específicos de Efectos (Anidados) ---
        # (Esto parece correcto como lo tenías)
        effect_settings = {
            'zoom_ratio': self.app.settings_zoom_ratio.get(),
            'zoom_quality': self.app.settings_zoom_quality.get(),
            'pan_scale_factor': self.app.settings_pan_scale_factor.get(),
            'pan_easing': self.app.settings_pan_easing.get(),
            'pan_quality': self.app.settings_pan_quality.get(),
            'kb_zoom_ratio': self.app.settings_kb_zoom_ratio.get(),
            'kb_scale_factor': self.app.settings_kb_scale_factor.get(),
            'kb_quality': self.app.settings_kb_quality.get(),
            'kb_direction': self.app.settings_kb_direction.get(),
            'overlay_opacity': self.app.settings_overlay_opacity.get(), # ¿Esto es de efectos o overlay general? Ajustar si es necesario
            'overlay_blend_mode': self.app.settings_overlay_blend_mode.get() # ¿Esto es de efectos o overlay general? Ajustar si es necesario
        }
        print(f"DEBUG UI - effect_settings anidados: {effect_settings}") # Debug

        # --- Recoger Overlays ---
        overlays = self.app.obtener_overlays_seleccionados()
        print(f"DEBUG UI - overlays seleccionados: {overlays}") # Debug

        # --- Crear el Diccionario Principal 'video_settings' ---
        # Añadimos todos los parámetros directos aquí
        video_settings = {
            # Básicos
            'duracion_img': self.app.duracion_img.get(),
            'fps': self.app.fps.get(),

            # Efectos Generales
            'aplicar_efectos': self.app.aplicar_efectos.get(),
            # 'secuencia_efectos': None, # Lo añadiremos después

            # Transiciones
            'aplicar_transicion': self.app.aplicar_transicion.get(),
            'tipo_transicion': self.app.tipo_transicion.get(),
            'duracion_transicion': self.app.duracion_transicion.get(),

            # Fades Video
            'aplicar_fade_in': self.app.aplicar_fade_in.get(),
            'duracion_fade_in': self.app.duracion_fade_in.get(),
            'aplicar_fade_out': self.app.aplicar_fade_out.get(),
            'duracion_fade_out': self.app.duracion_fade_out.get(),

            # Overlays
            'aplicar_overlay': bool(overlays),
            'archivos_overlay': [str(Path(ov).resolve()) for ov in overlays] if overlays else None,
            'opacidad_overlay': self.app.opacidad_overlay.get(), # Opacidad general del overlay

            # Música
            'aplicar_musica': self.app.aplicar_musica.get(),
            'archivo_musica': str(Path(self.app.archivo_musica.get()).resolve()) if self.app.archivo_musica.get() else None,
            'volumen_musica': self.app.volumen_musica.get(),
            'aplicar_fade_in_musica': self.app.aplicar_fade_in_musica.get(),
            'duracion_fade_in_musica': self.app.duracion_fade_in_musica.get(),
            'aplicar_fade_out_musica': self.app.aplicar_fade_out_musica.get(),
            'duracion_fade_out_musica': self.app.duracion_fade_out_musica.get(),

            # Voz (Audio Principal)
            'volumen_voz': self.app.volumen_voz.get(),
            'aplicar_fade_in_voz': self.app.aplicar_fade_in_voz.get(),
            'duracion_fade_in_voz': self.app.duracion_fade_in_voz.get(),
            'aplicar_fade_out_voz': self.app.aplicar_fade_out_voz.get(),
            'duracion_fade_out_voz': self.app.duracion_fade_out_voz.get(),
            'tts_rate': self.app.tts_rate_str.get(), # Rate/Pitch
            'tts_pitch': self.app.tts_pitch_str.get(),

            # Subtítulos (Aplicación y Apariencia)
            'aplicar_subtitulos': self.app.aplicar_subtitulos.get(), # Leer del checkbox
            'color_fuente_subtitulos': self.app.settings_subtitles_font_color.get(),
            'tamano_fuente_subtitulos': self.app.settings_subtitles_font_size.get(),
            'font_name': self.app.settings_subtitles_font_name.get(),
            'use_system_font': self.app.settings_use_system_font.get(),
            'color_borde_subtitulos': self.app.settings_subtitles_stroke_color.get(),
            'grosor_borde_subtitulos': self.app.settings_subtitles_stroke_width.get(),
            'subtitles_align': self.app.settings_subtitles_align.get(),
            'subtitles_position_h': self.app.settings_subtitles_position_h.get(),
            'subtitles_position_v': self.app.settings_subtitles_position_v.get(),
            'subtitles_uppercase': self.app.subtitles_uppercase.get(),
            'subtitulos_margen': self.app.settings_subtitles_margin.get(),

            # Estilo Imágenes
            'estilo_imagenes': self.prompt_style_map.get(self.prompt_style_dropdown.get(), 'default'),
            'nombre_estilo': self.prompt_style_dropdown.get(),

            # Ajustes anidados de efectos
            'settings': effect_settings # El diccionario que creamos antes
        }

        # --- AHORA OBTENER Y AÑADIR LA SECUENCIA DE EFECTOS ---
        # Verifica que 'obtener_secuencia_efectos_actual' exista en self.app
        if hasattr(self.app, 'obtener_secuencia_efectos_actual'):
            
            selected_effects_sequence = self.app.obtener_secuencia_efectos_actual()
            print(f"DEBUG UI: La función obtener_secuencia_efectos_actual() devolvió: {selected_effects_sequence}")
            video_settings['secuencia_efectos'] = selected_effects_sequence # Añadir/sobrescribir la clave
        elif hasattr(self.app, 'obtener_secuencia_efectos'):
            # Fallback a la versión anterior si _actual no existe (pero recuerda que depende de len(imagenes))
            print("ADVERTENCIA: Usando obtener_secuencia_efectos() en lugar de _actual()")
            selected_effects_sequence = self.app.obtener_secuencia_efectos()
            print(f"DEBUG UI: La función obtener_secuencia_efectos() devolvió: {selected_effects_sequence}")
            video_settings['secuencia_efectos'] = selected_effects_sequence # Añadir/sobrescribir la clave
        else:
            print("ERROR: No se encontró la función para obtener la secuencia de efectos en self.app.")
            video_settings['secuencia_efectos'] = [] # Poner lista vacía como fallback seguro


        # --- IMPRIMIR TODO PARA VERIFICAR (OPCIONAL PERO ÚTIL) ---
        print("\n--- DEBUG UI: video_settings FINAL Enviado al Manager ---")
        try:
            # Usar json.dumps para una salida más legible de diccionarios/listas
            # default=str es importante para manejar objetos Path si los hubiera (aunque los convertimos)
            print(json.dumps(video_settings, indent=2, default=str))
        except Exception as json_e:
            print(f"Error al imprimir video_settings como JSON: {json_e}")
            print(video_settings) # Imprimir como diccionario normal si falla JSON
        print("-------------------------------------------------------\n")

        # --- Llamar al Manager ---
        success = self.app.batch_tts_manager.add_project_to_queue(title, script, voice, video_settings)

        # --- Mostrar mensaje y limpiar ---
        if success:
            messagebox.showinfo("Proyecto Añadido",
                            f"El proyecto '{title}' ha sido añadido a la cola.")
            # Eliminada nota sobre crear carpeta 'imagenes' manualmente si ya no aplica
            self._clear_project_fields()
            self.app.update_queue_status()
        # (El manager ya muestra errores si add_project_to_queue falla internamente)

    def update_prompt_styles_dropdown(self):
            """Actualiza el dropdown de estilos de prompts con los estilos disponibles"""
            # Obtener estilos de prompts disponibles
            prompt_styles = [("default", "Cinematográfico")]
            if PROMPT_MANAGER_AVAILABLE:
                try:
                    prompt_manager = PromptManager()
                    prompt_styles = prompt_manager.get_prompt_names()
                    
                    # Imprimir información de depuración sobre los estilos disponibles
                    print("\n\n=== ACTUALIZANDO ESTILOS DE PROMPTS ===")
                    for i, (id, name) in enumerate(prompt_styles):
                        print(f"  {i+1}. ID: '{id}', Nombre: '{name}'")
                except Exception as e:
                    print(f"Error al cargar estilos de prompts: {e}")
            
            # Actualizar el dropdown
            prompt_style_values = [name for _, name in prompt_styles]
            prompt_style_ids = [id for id, _ in prompt_styles]
            
            # Guardar el valor actual para restaurarlo si es posible
            current_value = self.app.selected_prompt_style.get()
            
            # Actualizar los valores del dropdown
            self.prompt_style_dropdown['values'] = prompt_style_values
            
            # Actualizar el mapeo de nombres a IDs
            self.prompt_style_map = dict(zip(prompt_style_values, prompt_style_ids))
            
            # Restaurar el valor seleccionado si aún existe, o seleccionar el primero
            if current_value in prompt_style_values:
                self.app.selected_prompt_style.set(current_value)
            elif prompt_style_values:
                self.app.selected_prompt_style.set(prompt_style_values[0])
            
            # Imprimir el mapeo actualizado para depuración
            print("\n=== MAPEO DE NOMBRES A IDS ACTUALIZADO ===")
            for name, id in self.prompt_style_map.items():
                print(f"  Nombre: '{name}' -> ID: '{id}'")
        
    def _clear_project_fields(self):
            """Limpia los campos del formulario de proyecto."""
            self.entry_title.delete(0, tk.END)
            self.txt_script.delete("1.0", tk.END)
        
    def _get_selected_project(self):
            """Obtiene el proyecto seleccionado en el Treeview."""
            selected_items = self.app.tree_queue.selection()
            if not selected_items:
                from tkinter import messagebox
                messagebox.showwarning("Selección Requerida", "Por favor, selecciona un proyecto de la cola.")
                return None
            
            selected_id = selected_items[0]
            if selected_id not in self.app.batch_tts_manager.jobs_in_gui:
                messagebox.showerror("Error", "No se pudo encontrar el proyecto seleccionado en la cola.")
                return None
            
            return selected_id, self.app.batch_tts_manager.jobs_in_gui[selected_id]
    
    def _regenerar_audio(self):
        """Regenera el audio para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar el audio para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Audio...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_audio, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_prompts(self):
        """Regenera los prompts para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar los prompts para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Prompts...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_prompts, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_imagenes(self):
        """Regenera las imágenes para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar las imágenes para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Imágenes...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_imagenes, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_subtitulos(self):
        """Regenera los subtítulos para el proyecto seleccionado."""
        # Obtener el proyecto seleccionado
        proyecto_id = self._get_selected_project()
        if not proyecto_id:
            return
        
        # Regenerar subtítulos
        self.app.batch_tts_manager.regenerar_subtitulos(proyecto_id)
        messagebox.showinfo("Regeneración", "Se ha iniciado la regeneración de subtítulos.")
        
    def _preview_voice(self):
        """Genera y reproduce una muestra de voz con los parámetros actuales."""
        if not TTS_AVAILABLE:
            messagebox.showerror("Error", "El módulo TTS no está disponible.")
            return
        
        # Obtener los valores actuales
        voice = self.app.selected_voice.get()
        rate = self.app.tts_rate_str.get()
        pitch = self.app.tts_pitch_str.get()
        
        print(f"DEBUG: Generando vista previa con voz={voice}, rate={rate}, pitch={pitch}")
        
        # Texto de prueba
        test_text = "Hola, esta es una prueba de la configuración de voz."
        
        # Crear un directorio temporal si no existe
        temp_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "temp_audio"
        temp_dir.mkdir(exist_ok=True)
        
        # Ruta para el archivo de audio temporal
        temp_audio_path = temp_dir / "preview_voice.mp3"
        
        # Guardar referencia al botón
        if not hasattr(self, 'btn_preview'):
            for widget in self.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.winfo_children():
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child.cget('text') == "Probar Voz":
                            self.btn_preview = child
                            break
        
        # Deshabilitar el botón mientras se genera el audio
        if hasattr(self, 'btn_preview'):
            self.btn_preview.config(state="disabled")
            self.btn_preview.config(text="Generando...")
            self.update_idletasks()
        
        # Función para ejecutar la generación de voz en un hilo separado
        def generate_voice_preview():
            try:
                # Ejecutar la generación de voz de forma asíncrona
                asyncio.run(text_chunk_to_speech(
                    text=test_text,
                    voice=voice,
                    output_path=str(temp_audio_path),
                    rate=rate,
                    pitch=pitch
                ))
                
                # Reproducir el audio generado
                self._play_audio(temp_audio_path)
                
                # Restaurar el botón
                if hasattr(self, 'btn_preview'):
                    self.btn_preview.config(state="normal")
                    self.btn_preview.config(text="Probar Voz")
            except Exception as e:
                # Manejar errores
                print(f"Error en la vista previa de voz: {e}")
                messagebox.showerror("Error", f"No se pudo generar la vista previa: {e}")
                if hasattr(self, 'btn_preview'):
                    self.btn_preview.config(state="normal")
                    self.btn_preview.config(text="Probar Voz")
        
        # Iniciar el hilo para la generación de voz
        threading.Thread(target=generate_voice_preview, daemon=True).start()
    
    def _play_audio(self, audio_path):
        """Reproduce un archivo de audio."""
        try:
            # Usar el reproductor adecuado según el sistema operativo
            if os.name == 'posix':  # macOS o Linux
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.run(['afplay', str(audio_path)], check=True)
                else:  # Linux
                    subprocess.run(['paplay', str(audio_path)], check=True)
            elif os.name == 'nt':  # Windows
                os.startfile(audio_path)
            else:
                print(f"No se pudo determinar el reproductor para el sistema {os.name}")
        except Exception as e:
            print(f"Error al reproducir el audio: {e}")
            messagebox.showerror("Error", f"No se pudo reproducir el audio: {e}")
    
    def _cargar_proyecto_existente(self):
        """Carga un proyecto existente desde la carpeta de proyectos."""
        from tkinter import filedialog, messagebox
        import json
        from pathlib import Path
        
        # Obtener la ruta base de proyectos
        proyectos_dir = self.app.batch_tts_manager.project_base_dir
        
        # Solicitar al usuario que seleccione una carpeta de proyecto
        proyecto_path = filedialog.askdirectory(
            title="Seleccionar Carpeta de Proyecto",
            initialdir=proyectos_dir
        )
        
        if not proyecto_path:
            return  # El usuario canceló la selección
        
        proyecto_path = Path(proyecto_path)
        settings_path = proyecto_path / "settings.json"
        guion_path = proyecto_path / "guion.txt"
        voz_path = proyecto_path / "voz.mp3"
        
        # Verificar que es una carpeta de proyecto válida
        if not settings_path.exists() or not guion_path.exists():
            messagebox.showerror(
                "Error", 
                f"La carpeta seleccionada no parece ser un proyecto válido.\n"
                f"Debe contener al menos settings.json y guion.txt."
            )
            return
        
        try:
            # Cargar configuración del proyecto
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # Leer el guion
            with open(guion_path, "r", encoding="utf-8") as f:
                script_content = f.read()
            
            # Obtener el nombre del proyecto (nombre de la carpeta)
            proyecto_nombre = proyecto_path.name
            
            # Determinar la voz utilizada
            voz = settings.get("voz", "es-MX-JorgeNeural")  # Valor por defecto si no se encuentra
            
            # Crear un trabajo para este proyecto
            job_id = self.app.batch_tts_manager.add_existing_project_to_queue(
                title=proyecto_nombre,
                script=script_content,
                project_folder=proyecto_path,
                voice=voz,
                video_settings=settings
            )
            
            if job_id:
                messagebox.showinfo(
                    "Proyecto Cargado", 
                    f"El proyecto '{proyecto_nombre}' ha sido cargado en la cola.\n"
                    f"Ahora puedes regenerar partes específicas o generar el video."
                )
                self.app.update_queue_status()
            else:
                messagebox.showerror(
                    "Error", 
                    f"No se pudo cargar el proyecto '{proyecto_nombre}'."
                )
        
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Error al cargar el proyecto: {str(e)}"
            )
            import traceback
            traceback.print_exc()