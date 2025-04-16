# -*- coding: utf-8 -*-
# Archivo: ui/tab_batch.py

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Importar el gestor de prompts
try:
    from prompt_manager import PromptManager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False

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

        # --- Configuración de Tiempo ---
        # Duración de imagen
        lbl_duracion = ttk.Label(frame_input, text="Duración imagen (s):")
        lbl_duracion.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Crear variable para duración si no existe en la app
        if not hasattr(self.app, 'duracion_img_batch'):
            self.app.duracion_img_batch = tk.DoubleVar(value=10.0)
            
        spin_duracion = ttk.Spinbox(frame_input, from_=1, to=30, increment=0.5, 
                                    textvariable=self.app.duracion_img_batch, width=5)
        spin_duracion.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # FPS
        lbl_fps = ttk.Label(frame_input, text="FPS:")
        lbl_fps.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Crear variable para FPS si no existe en la app
        if not hasattr(self.app, 'fps_batch'):
            self.app.fps_batch = tk.IntVar(value=30)
            
        spin_fps = ttk.Spinbox(frame_input, from_=15, to=60, increment=1, 
                              textvariable=self.app.fps_batch, width=5)
        spin_fps.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Selección de voz
        lbl_voice = ttk.Label(frame_input, text="Voz:")
        lbl_voice.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
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
        lbl_prompt_style.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        
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
                print("\n\n=== ESTILOS DE PROMPTS DISPONIBLES ===")
                for i, (id, name) in enumerate(prompt_styles):
                    print(f"  {i+1}. ID: '{id}', Nombre: '{name}'")
            except Exception as e:
                print(f"Error al cargar estilos de prompts: {e}")
        
        self.app.selected_voice = tk.StringVar(value="es-MX-JorgeNeural")
        voice_combo = ttk.Combobox(frame_input, textvariable=self.app.selected_voice, values=voces, width=30)
        voice_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Dropdown para estilos de prompts
        prompt_style_values = [name for _, name in prompt_styles]
        prompt_style_ids = [id for id, _ in prompt_styles]
        self.prompt_style_dropdown = ttk.Combobox(frame_input, textvariable=self.app.selected_prompt_style, 
                                               values=prompt_style_values, width=30, state="readonly")
        self.prompt_style_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Checkbutton para aplicar subtítulos (si existen)
        if not hasattr(self.app, 'aplicar_subtitulos_batch'):
            self.app.aplicar_subtitulos_batch = tk.BooleanVar(value=True)  # Por defecto activado
            
        self.chk_aplicar_subtitulos = ttk.Checkbutton(
            frame_input, 
            text="Aplicar subtítulos (si existen) a los videos",
            variable=self.app.aplicar_subtitulos_batch
        )
        self.chk_aplicar_subtitulos.grid(row=4, column=2, padx=5, pady=5, sticky="w")
        
        # Mapeo de nombres a IDs para recuperar el ID correcto
        self.prompt_style_map = dict(zip(prompt_style_values, prompt_style_ids))
        
        # Imprimir el mapeo para depuración
        print("\n=== MAPEO DE NOMBRES A IDS ===")
        for name, id in self.prompt_style_map.items():
            print(f"  Nombre: '{name}' -> ID: '{id}'")
            
        # Configurar un callback para cuando cambie el estilo seleccionado
        def on_prompt_style_change(event):
            selected_name = self.prompt_style_dropdown.get()
            selected_id = self.prompt_style_map.get(selected_name, "default")
            print(f"\nEstilo seleccionado: Nombre='{selected_name}', ID='{selected_id}'")
            
        self.prompt_style_dropdown.bind("<<ComboboxSelected>>", on_prompt_style_change)

        # Guion del proyecto
        lbl_script = ttk.Label(frame_input, text="Guion:")
        lbl_script.grid(row=5, column=0, padx=5, pady=5, sticky="nw")
        
        # Frame para el Text y Scrollbar
        frame_text = ttk.Frame(frame_input)
        frame_text.grid(row=5, column=1, padx=5, pady=5, sticky="nsew")
        frame_input.grid_columnconfigure(1, weight=1)  # Hacer que columna 1 se expanda
        frame_input.grid_rowconfigure(5, weight=1)     # Hacer que fila 5 se expanda

        self.txt_script = tk.Text(frame_text, wrap="word", height=15, width=60)
        scrollbar_script = ttk.Scrollbar(frame_text, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar_script.set)
        self.txt_script.pack(side="left", fill="both", expand=True)
        scrollbar_script.pack(side="right", fill="y")

        # Botones de acción
        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=4, column=1, padx=5, pady=10, sticky="e")
        
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
        self.app.tree_queue.column("titulo", width=250)  # Columna de título más pequeña
        self.app.tree_queue.column("estado", width=300, anchor="center")  # Columna de estado más grande
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
                                       style="Secondary.TButton",
                                       width=20)
        btn_cargar_proyecto.pack(side="left", padx=10, pady=10)
        
        # Botón para generar vídeo (más grande y destacado)
        btn_generate_video = ttk.Button(frame_botones_principales,
                                       text="GENERAR VÍDEO",
                                       command=self.app.trigger_video_generation_for_selected,
                                       style="Action.TButton",
                                       width=20)
        btn_generate_video.pack(side="right", padx=10, pady=10)
        
        # --- BARRA DE HERRAMIENTAS DE REGENERACIÓN ---
        # Crear un frame con borde para los botones de regeneración
        frame_regeneracion = ttk.LabelFrame(frame_queue, text="Regenerar Componentes")
        frame_regeneracion.pack(fill="x", pady=10, padx=5)
        
        # Crear un grid para organizar los botones de manera más ordenada
        frame_grid = ttk.Frame(frame_regeneracion)
        frame_grid.pack(fill="x", padx=10, pady=10)
        
        # Botón para regenerar audio (más grande y con icono visual)
        btn_regenerar_audio = ttk.Button(frame_grid,
                                        text="Audio",
                                        command=self._regenerar_audio,
                                        style="Secondary.TButton",
                                        width=15)
        btn_regenerar_audio.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Botón para regenerar prompts
        btn_regenerar_prompts = ttk.Button(frame_grid,
                                         text="Prompts",
                                         command=self._regenerar_prompts,
                                         style="Secondary.TButton",
                                         width=15)
        btn_regenerar_prompts.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Botón para regenerar imágenes
        btn_regenerar_imagenes = ttk.Button(frame_grid,
                                          text="Imágenes",
                                          command=self._regenerar_imagenes,
                                          style="Secondary.TButton",
                                          width=15)
        btn_regenerar_imagenes.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Botón para regenerar subtítulos
        btn_regenerar_subtitulos = ttk.Button(frame_grid,
                                            text="Subtítulos",
                                            command=self._regenerar_subtitulos,
                                            style="Secondary.TButton",
                                            width=15)
        btn_regenerar_subtitulos.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Configurar el grid para que las columnas se expandan uniformemente
        frame_grid.columnconfigure(0, weight=1)
        frame_grid.columnconfigure(1, weight=1)
        
        # Asignar el Treeview al gestor de cola
        self.app.batch_tts_manager.tree_queue = self.app.tree_queue
        
        # Etiqueta de estado de la cola (más visible y destacada)
        status_frame = ttk.Frame(frame_queue, style="Card.TFrame")
        status_frame.pack(fill="x", padx=5, pady=5, before=frame_botones_principales)
        
        self.app.lbl_queue_status = ttk.Label(status_frame, text="Cola vacía", 
                                             style="Header.TLabel", 
                                             font=("Helvetica", 12, "bold"),
                                             foreground="#d35400")
        self.app.lbl_queue_status.pack(anchor="w", padx=10, pady=5)

    def _add_project_to_queue(self):
        """Añade un nuevo proyecto a la cola de procesamiento."""
        title = self.entry_title.get().strip()
        script = self.txt_script.get("1.0", tk.END).strip()
        voice = self.app.selected_voice.get()
        
        # --- Obtener valores necesarios ANTES de la validación ---
        # Obtener si la música está activada y la ruta del archivo
        try:
            aplicar_musica_seleccionado = self.app.aplicar_musica.get()
            archivo_musica_seleccionado = self.app.archivo_musica.get()
        except AttributeError:
            print("Advertencia: No se encontraron variables para música en self.app. Omitiendo validación de música.")
            aplicar_musica_seleccionado = False
            archivo_musica_seleccionado = ""

        # Obtener si los subtítulos están activados
        try:
            aplicar_subtitulos_seleccionado = self.app.aplicar_subtitulos_batch.get()
        except AttributeError:
            print("Advertencia: No se encontró variable para subtítulos en self.app. Asumiendo True.")
            aplicar_subtitulos_seleccionado = True

        # --- INICIO: Validación Previa ---

        # 1. Validar Música
        if aplicar_musica_seleccionado and not archivo_musica_seleccionado:
            # Mostrar una advertencia, pero permitir continuar
            messagebox.showwarning(
                title="Advertencia: Falta Archivo de Música",
                message="La opción 'Aplicar Música' está activada, pero no has seleccionado un archivo de música.\n\n"
                        "El video se generará sin música de fondo. Puedes seleccionarla en la pestaña 'Audio'."
            )

        # 2. Validar Subtítulos (Confirmar si están desactivados)
        if not aplicar_subtitulos_seleccionado:
            # Preguntar al usuario si está seguro de que NO quiere subtítulos
            confirmar_sin_subtitulos = messagebox.askyesno(
                title="Confirmar: Subtítulos Desactivados",
                message="La opción 'Aplicar Subtítulos' está desactivada.\n"
                        "El video se generará sin subtítulos, aunque se haya generado un archivo .srt.\n\n"
                        "\u00bfEstás seguro de que quieres continuar así?"
            )
            if not confirmar_sin_subtitulos: # Si el usuario presiona "No"
                print("Proceso cancelado por el usuario (confirmación de subtítulos).")
                return # Detener la función, no añadir a la cola

        # --- FIN: Validación Previa ---
        
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
            'duracion_img': self.app.duracion_img_batch.get(),  # Usar duración de la pestaña batch
            'fps': self.app.fps_batch.get(),  # Usar FPS de la pestaña batch
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
            # Usar el valor del nuevo Checkbutton para aplicar subtítulos en lotes
            'aplicar_subtitulos': self.app.aplicar_subtitulos_batch.get(),
            
            # --- CONFIGURACIÓN DE ESTILO DE SUBTÍTULOS ---
            # Fuente y tamaño
            'tamano_fuente_subtitulos': getattr(self.app, 'settings_subtitles_font_size', tk.IntVar(value=60)).get(),
            'font_name': getattr(self.app, 'settings_subtitles_font_name', tk.StringVar(value='Roboto-Regular')).get(),
            'use_system_font': getattr(self.app, 'settings_use_system_font', tk.BooleanVar(value=False)).get(),
            'subtitles_uppercase': getattr(self.app, 'subtitles_uppercase', tk.BooleanVar(value=False)).get(),
            
            # Colores y bordes
            'color_fuente_subtitulos': getattr(self.app, 'settings_subtitles_font_color', tk.StringVar(value='white')).get(),
            'color_borde_subtitulos': getattr(self.app, 'settings_subtitles_stroke_color', tk.StringVar(value='black')).get(),
            'grosor_borde_subtitulos': getattr(self.app, 'settings_subtitles_stroke_width', tk.IntVar(value=3)).get(),
            
            # Posición y alineación
            'subtitulos_align': getattr(self.app, 'settings_subtitles_align', tk.StringVar(value='center')).get(),
            'subtitulos_position_h': getattr(self.app, 'settings_subtitles_position_h', tk.StringVar(value='center')).get(),
            'subtitulos_position_v': getattr(self.app, 'settings_subtitles_position_v', tk.StringVar(value='bottom')).get(),
            'subtitulos_margen': getattr(self.app, 'settings_subtitles_margin', tk.DoubleVar(value=0.05)).get(),
            
            # Estilo de prompts para la generación de imágenes
            # Obtener el ID del estilo a partir del nombre seleccionado en el dropdown
            'estilo_imagenes': self.prompt_style_map.get(self.prompt_style_dropdown.get(), 'default'),
            # Guardar también el nombre del estilo para depuración
            'nombre_estilo': self.prompt_style_dropdown.get(),
            'settings': effect_settings
        }
        
        # Imprimir información de depuración sobre el estilo seleccionado
        print(f"\n=== ESTILO SELECCIONADO PARA EL PROYECTO ===")
        print(f"  Nombre mostrado: '{self.prompt_style_dropdown.get()}'")
        print(f"  ID interno: '{self.prompt_style_map.get(self.prompt_style_dropdown.get(), 'default')}'")        
        
        success = self.app.batch_tts_manager.add_project_to_queue(title, script, voice, video_settings)
        
        if success:
            from tkinter import messagebox
            messagebox.showinfo("Proyecto Añadido", 
                              f"El proyecto '{title}' ha sido añadido a la cola.\n\n" +
                              "Nota: Para generar el video, crea manualmente una carpeta 'imagenes' " +
                              "dentro de la carpeta del proyecto y coloca ahí las imágenes que quieres usar.")
            self._clear_project_fields()
            self.app.update_queue_status()

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
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar los subtítulos para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Subtítulos...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_subtitulos, 
                           args=(job_id,), daemon=True).start()
    
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