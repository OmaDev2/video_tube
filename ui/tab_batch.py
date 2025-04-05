# -*- coding: utf-8 -*-
# Archivo: ui/tab_batch.py

import tkinter as tk
from tkinter import ttk
from pathlib import Path

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
            "es-CL-CatalinaNeural"  # Chile (femenino)
        ]
        
        self.app.selected_voice = tk.StringVar(value=voces[0])
        voice_combo = ttk.Combobox(frame_input, textvariable=self.app.selected_voice, values=voces, width=30)
        voice_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Guion del proyecto
        lbl_script = ttk.Label(frame_input, text="Guion:")
        lbl_script.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        
        # Frame para el Text y Scrollbar
        frame_text = ttk.Frame(frame_input)
        frame_text.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        frame_input.grid_columnconfigure(1, weight=1)  # Hacer que columna 1 se expanda
        frame_input.grid_rowconfigure(2, weight=1)     # Hacer que fila 2 se expanda

        self.txt_script = tk.Text(frame_text, wrap="word", height=15, width=60)
        scrollbar_script = ttk.Scrollbar(frame_text, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar_script.set)
        self.txt_script.pack(side="left", fill="both", expand=True)
        scrollbar_script.pack(side="right", fill="y")

        # Botones de acción
        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=3, column=1, padx=5, pady=10, sticky="e")
        
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
                                          show="headings", height=10)
        self.app.tree_queue.heading("titulo", text="Título del Proyecto")
        self.app.tree_queue.heading("estado", text="Estado")
        self.app.tree_queue.heading("tiempo", text="Tiempo")
        self.app.tree_queue.column("titulo", width=400)
        self.app.tree_queue.column("estado", width=150, anchor="center")
        self.app.tree_queue.column("tiempo", width=100, anchor="center")

        # Scrollbar para el Treeview
        scrollbar_queue = ttk.Scrollbar(frame_queue, orient="vertical", command=self.app.tree_queue.yview)
        self.app.tree_queue.configure(yscrollcommand=scrollbar_queue.set)

        self.app.tree_queue.pack(side="left", fill="both", expand=True)
        scrollbar_queue.pack(side="right", fill="y")
        
        # --- NUEVO BOTÓN ---
        frame_acciones_cola = ttk.Frame(frame_queue)
        frame_acciones_cola.pack(fill="x", pady=10)

        btn_generate_video = ttk.Button(frame_acciones_cola,
                                        text="Generar Vídeo del Proyecto Seleccionado",
                                        command=self.app.trigger_video_generation_for_selected,
                                        style="Action.TButton")
        btn_generate_video.pack(side="right", padx=5)
        
        # Asignar el Treeview al gestor de cola
        self.app.batch_tts_manager.tree_queue = self.app.tree_queue
        
        # Etiqueta de estado de la cola
        self.app.lbl_queue_status = ttk.Label(self, text="Cola vacía", style="Header.TLabel")
        self.app.lbl_queue_status.pack(anchor="w", padx=10, pady=5)

    def _add_project_to_queue(self):
        """Añade un nuevo proyecto a la cola de procesamiento."""
        title = self.entry_title.get().strip()
        script = self.txt_script.get("1.0", tk.END).strip()
        voice = self.app.selected_voice.get()
        
        # Capturar todos los ajustes actuales de la GUI para la creación de video
        # Obtener secuencia de efectos
        selected_effects_sequence = self.app.obtener_secuencia_efectos()
        
        # Recoger ajustes específicos de efectos
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
            'overlay_opacity': self.app.settings_overlay_opacity.get(),
            'overlay_blend_mode': self.app.settings_overlay_blend_mode.get()
        }
        
        # Obtener overlays seleccionados
        overlays = self.app.obtener_overlays_seleccionados()
        
        # Crear diccionario con todos los ajustes para la creación de video
        video_settings = {
            'duracion_img': self.app.duracion_img.get(),
            'fps': self.app.fps.get(),
            'aplicar_efectos': self.app.aplicar_efectos.get(),
            'secuencia_efectos': selected_effects_sequence,
            'aplicar_transicion': self.app.aplicar_transicion.get(),
            'tipo_transicion': self.app.tipo_transicion.get(),
            'duracion_transicion': self.app.duracion_transicion.get(),
            'aplicar_fade_in': self.app.aplicar_fade_in.get(),
            'duracion_fade_in': self.app.duracion_fade_in.get(),
            'aplicar_fade_out': self.app.aplicar_fade_out.get(),
            'duracion_fade_out': self.app.duracion_fade_out.get(),
            'aplicar_overlay': bool(overlays),
            'archivos_overlay': [str(Path(ov).resolve()) for ov in overlays] if overlays else None,
            'opacidad_overlay': self.app.opacidad_overlay.get(),
            'aplicar_musica': self.app.aplicar_musica.get(),
            'archivo_musica': str(Path(self.app.archivo_musica.get()).resolve()) if self.app.archivo_musica.get() else None,
            'volumen_musica': self.app.volumen_musica.get(),
            'aplicar_fade_in_musica': self.app.aplicar_fade_in_musica.get(),
            'duracion_fade_in_musica': self.app.duracion_fade_in_musica.get(),
            'aplicar_fade_out_musica': self.app.aplicar_fade_out_musica.get(),
            'duracion_fade_out_musica': self.app.duracion_fade_out_musica.get(),
            'volumen_voz': self.app.volumen_voz.get(),
            'aplicar_fade_in_voz': self.app.aplicar_fade_in_voz.get(),
            'duracion_fade_in_voz': self.app.duracion_fade_in_voz.get(),
            'aplicar_fade_out_voz': self.app.aplicar_fade_out_voz.get(),
            'duracion_fade_out_voz': self.app.duracion_fade_out_voz.get(),
            'aplicar_subtitulos': False,  # Por ahora no soportamos subtítulos automáticos
            'settings': effect_settings
        }
        
        success = self.app.batch_tts_manager.add_project_to_queue(title, script, voice, video_settings)
        
        if success:
            from tkinter import messagebox
            messagebox.showinfo("Proyecto Añadido", 
                              f"El proyecto '{title}' ha sido añadido a la cola.\n\n" +
                              "Nota: Para generar el video, crea manualmente una carpeta 'imagenes' " +
                              "dentro de la carpeta del proyecto y coloca ahí las imágenes que quieres usar.")
            self._clear_project_fields()
            self.app.update_queue_status()

    def _clear_project_fields(self):
        """Limpia los campos del formulario de proyecto."""
        self.entry_title.delete(0, tk.END)
        self.txt_script.delete("1.0", tk.END)