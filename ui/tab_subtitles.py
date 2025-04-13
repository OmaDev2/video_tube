# -*- coding: utf-8 -*-
# Archivo: ui/tab_subtitles.py

import tkinter as tk
from tkinter import ttk, messagebox, font
import os
from pathlib import Path

# Importar funciones para subtítulos
from subtitles import WHISPER_AVAILABLE

# Importar Whisper si está disponible
if WHISPER_AVAILABLE:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ADVERTENCIA: No se pudo importar WhisperModel a pesar de que WHISPER_AVAILABLE es True")

class SubtitlesTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Subtítulos'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de Subtítulos.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Crear variables para la fuente si no existen
        if not hasattr(self.app, 'settings_subtitles_font_name'):
            self.app.settings_subtitles_font_name = tk.StringVar(value="Roboto-Regular")
        
        if not hasattr(self.app, 'settings_use_system_font'):
            self.app.settings_use_system_font = tk.BooleanVar(value=False)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _get_available_fonts(self):
        """
        Obtiene una lista de fuentes disponibles en el sistema y en la carpeta fonts.
        
        Returns:
            tuple: (fuentes_sistema, fuentes_custom)
        """
        # Obtener las fuentes del sistema usando tkinter
        fuentes_sistema = sorted(list(font.families()))
        
        # Obtener las fuentes personalizadas de la carpeta fonts
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fonts_dir = base_dir / "fonts"
        fuentes_custom = []
        
        if fonts_dir.exists() and fonts_dir.is_dir():
            # Buscar archivos TTF y OTF
            for ext in ['.ttf', '.otf', '.TTF', '.OTF']:
                for fuente in fonts_dir.glob(f"*{ext}"):
                    fuentes_custom.append(fuente.stem)
        
        return fuentes_sistema, fuentes_custom

    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña de subtítulos."""
        # Frame principal con padding
        main_frame = ttk.Frame(self, style="Card.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título de la sección
        lbl_title = ttk.Label(main_frame, text="Configuración de Subtítulos", 
                            style="Header.TLabel", font=("Helvetica", 14, "bold"))
        lbl_title.pack(pady=10)
        
        # Mostrar estado de Whisper
        whisper_status = "Disponible" if WHISPER_AVAILABLE else "No disponible (instala faster-whisper)"
        whisper_color = "#2ecc71" if WHISPER_AVAILABLE else "#e74c3c"
        
        lbl_status = ttk.Label(main_frame, 
                            text=f"Estado de Whisper: {whisper_status}", 
                            foreground=whisper_color,
                            font=("Helvetica", 11))
        lbl_status.pack(pady=5)
        
        # Si Whisper no está disponible, mostrar instrucciones de instalación
        if not WHISPER_AVAILABLE:
            lbl_install = ttk.Label(main_frame, 
                                text="Para instalar: pip install faster-whisper srt", 
                                foreground="#f39c12",
                                font=("Helvetica", 10))
            lbl_install.pack(pady=5)
            return
        
        # Frame para la configuración del modelo
        frame_model = ttk.LabelFrame(main_frame, text="Configuración del Modelo", style="TLabelframe")
        frame_model.pack(fill="x", padx=10, pady=10)
        
        # Tamaño del modelo
        frame_size = ttk.Frame(frame_model)
        frame_size.pack(fill="x", padx=10, pady=5)
        
        lbl_size = ttk.Label(frame_size, text="Tamaño del modelo:", width=20)
        lbl_size.pack(side="left")
        
        # Opciones de tamaño del modelo
        model_sizes = [("tiny", "Tiny (rápido, menos preciso)"), 
                     ("base", "Base (equilibrado)"), 
                     ("small", "Small (buena precisión)"), 
                     ("medium", "Medium (alta precisión, más lento)"), 
                     ("large-v3", "Large-v3 (máxima precisión, muy lento)")]
        
        size_combo = ttk.Combobox(frame_size, textvariable=self.app.whisper_model_size, state="readonly")
        size_combo['values'] = [size[0] for size in model_sizes]
        size_combo.pack(side="left", padx=5)
        
        # Descripción del modelo seleccionado
        self.app.lbl_model_desc = ttk.Label(frame_size, text="Modelo equilibrado entre velocidad y precisión", 
                                      foreground="#3498db")
        self.app.lbl_model_desc.pack(side="left", padx=10)
        
        # Función para actualizar la descripción del modelo
        def update_model_desc(event):
            selected = self.app.whisper_model_size.get()
            for size, desc in model_sizes:
                if size == selected:
                    self.app.lbl_model_desc.config(text=desc)
                    break
        
        size_combo.bind("<<ComboboxSelected>>", update_model_desc)
        
        # Dispositivo (CPU/GPU)
        frame_device = ttk.Frame(frame_model)
        frame_device.pack(fill="x", padx=10, pady=5)
        
        lbl_device = ttk.Label(frame_device, text="Dispositivo:", width=20)
        lbl_device.pack(side="left")
        
        device_combo = ttk.Combobox(frame_device, textvariable=self.app.whisper_device, state="readonly")
        device_combo['values'] = ["cpu", "cuda"]
        device_combo.pack(side="left", padx=5)
        
        lbl_device_info = ttk.Label(frame_device, 
                                 text="Usar 'cuda' solo si tienes GPU NVIDIA compatible", 
                                 foreground="#f39c12")
        lbl_device_info.pack(side="left", padx=10)
        
        # Botón para recargar el modelo
        def reload_whisper_model():
            try:
                # Verificar si ya hay un modelo cargado
                if hasattr(self.app, 'whisper_model') and self.app.whisper_model is not None:
                    # Liberar recursos del modelo anterior
                    del self.app.whisper_model
                    import gc
                    gc.collect()
                
                # Cargar el nuevo modelo
                print(f"Cargando modelo Whisper '{self.app.whisper_model_size.get()}' para {self.app.whisper_device.get()}...")
                from faster_whisper import WhisperModel
                self.app.whisper_model = WhisperModel(
                    self.app.whisper_model_size.get(),
                    device=self.app.whisper_device.get(),
                    compute_type=self.app.whisper_compute_type.get()
                )
                messagebox.showinfo(
                    "Modelo Whisper",
                    f"Modelo Whisper '{self.app.whisper_model_size.get()}' cargado exitosamente."
                )
            except Exception as e:
                print(f"Error al cargar el modelo Whisper: {e}")
                messagebox.showerror(
                    "Error",
                    f"No se pudo cargar el modelo Whisper: {e}"
                )
        
        btn_reload = ttk.Button(frame_model, text="Recargar Modelo Whisper", 
                              command=reload_whisper_model, style="Secondary.TButton")
        btn_reload.pack(pady=10)
        
        # Frame para opciones de subtítulos
        frame_options = ttk.LabelFrame(main_frame, text="Opciones de Subtítulos", style="TLabelframe")
        frame_options.pack(fill="x", padx=10, pady=10)
        
        # Idioma
        frame_lang = ttk.Frame(frame_options)
        frame_lang.pack(fill="x", padx=10, pady=5)
        
        lbl_lang = ttk.Label(frame_lang, text="Idioma:", width=20)
        lbl_lang.pack(side="left")
        
        lang_combo = ttk.Combobox(frame_lang, textvariable=self.app.whisper_language, state="readonly")
        lang_combo['values'] = ["es", "en", "fr", "de", "it", "pt", "auto"]
        lang_combo.pack(side="left", padx=5)
        
        lbl_lang_info = ttk.Label(frame_lang, 
                               text="'auto' detecta automáticamente el idioma", 
                               foreground="#3498db")
        lbl_lang_info.pack(side="left", padx=10)
        
        # Timestamps por palabra
        frame_word = ttk.Frame(frame_options)
        frame_word.pack(fill="x", padx=10, pady=5)
        
        word_check = ttk.Checkbutton(frame_word, text="Usar timestamps por palabra (más preciso)", 
                                   variable=self.app.whisper_word_timestamps)
        word_check.pack(padx=5, pady=5)
        
        # Frame para el estilo de subtítulos
        frame_style = ttk.LabelFrame(main_frame, text="Estilo de Subtítulos", style="TLabelframe")
        frame_style.pack(fill="x", padx=10, pady=10)
        
        # Crear un frame para organizar en dos columnas
        frame_columns = ttk.Frame(frame_style)
        frame_columns.pack(fill="x", padx=5, pady=5)
        
        # Columna izquierda
        frame_left_column = ttk.Frame(frame_columns)
        frame_left_column.pack(side="left", fill="both", expand=True)
        
        # Columna derecha
        frame_right_column = ttk.Frame(frame_columns)
        frame_right_column.pack(side="left", fill="both", expand=True, padx=5)
        
        # SELECTOR DE FUENTES (NUEVA FUNCIONALIDAD)
        frame_font = ttk.LabelFrame(frame_left_column, text="Selección de Fuente")
        frame_font.pack(fill="x", padx=5, pady=5)
        
        # Obtener las fuentes disponibles
        system_fonts, custom_fonts = self._get_available_fonts()
        
        # Opción para elegir entre fuentes del sistema o personalizadas
        frame_font_type = ttk.Frame(frame_font)
        frame_font_type.pack(fill="x", padx=5, pady=5)
        
        # Radio buttons para elegir entre fuentes del sistema o personalizadas
        def update_font_dropdown():
            font_dropdown['values'] = system_fonts if self.app.settings_use_system_font.get() else custom_fonts
            if len(font_dropdown['values']) > 0:
                font_dropdown.current(0)
                self.app.settings_subtitles_font_name.set(font_dropdown.get())
        
        rb_system = ttk.Radiobutton(frame_font_type, text="Fuentes del Sistema", 
                                  variable=self.app.settings_use_system_font, value=True,
                                  command=update_font_dropdown)
        rb_system.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        rb_custom = ttk.Radiobutton(frame_font_type, text="Fuentes Personalizadas", 
                                  variable=self.app.settings_use_system_font, value=False,
                                  command=update_font_dropdown)
        rb_custom.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Dropdown para seleccionar la fuente
        frame_font_select = ttk.Frame(frame_font)
        frame_font_select.pack(fill="x", padx=5, pady=5)
        
        lbl_font = ttk.Label(frame_font_select, text="Fuente:", width=10)
        lbl_font.pack(side="left", padx=5)
        
        font_dropdown = ttk.Combobox(frame_font_select, textvariable=self.app.settings_subtitles_font_name, 
                                    width=30, state="readonly")
        
        # Inicializar el dropdown con las fuentes apropiadas
        font_dropdown['values'] = custom_fonts if not self.app.settings_use_system_font.get() else system_fonts
        
        # Si la fuente actual no está en la lista, seleccionar la primera
        current_font = self.app.settings_subtitles_font_name.get()
        if current_font not in font_dropdown['values'] and len(font_dropdown['values']) > 0:
            self.app.settings_subtitles_font_name.set(font_dropdown['values'][0])
        
        font_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        
        # Mostrar vista previa de la fuente seleccionada
        def update_font_preview(event=None):
            try:
                font_name = self.app.settings_subtitles_font_name.get()
                if self.app.settings_use_system_font.get():
                    # Fuente del sistema
                    preview_font = (font_name, 12)
                else:
                    # Fuente personalizada (cargar desde la carpeta fonts)
                    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    fonts_dir = base_dir / "fonts"
                    # Buscar el archivo correspondiente
                    font_file = None
                    for ext in ['.ttf', '.otf', '.TTF', '.OTF']:
                        possible_file = fonts_dir / f"{font_name}{ext}"
                        if possible_file.exists():
                            font_file = possible_file
                            break
                    
                    if font_file:
                        # Registrar la fuente temporalmente para la vista previa
                        try:
                            temp_font = font.Font(family="PreviewFont", file=str(font_file), size=12)
                            preview_font = ("PreviewFont", 12)
                        except:
                            # Si hay error al cargar la fuente personalizada, usar una del sistema
                            preview_font = ("Helvetica", 12)
                    else:
                        preview_font = ("Helvetica", 12)
                
                # Actualizar la vista previa
                lbl_preview.config(font=preview_font)
                
            except Exception as e:
                print(f"Error al actualizar vista previa de fuente: {e}")
        
        font_dropdown.bind("<<ComboboxSelected>>", update_font_preview)
        
        # Vista previa de la fuente
        frame_preview = ttk.LabelFrame(frame_font, text="Vista previa")
        frame_preview.pack(fill="x", padx=5, pady=5)
        
        lbl_preview = ttk.Label(frame_preview, text="Texto de ejemplo con la fuente seleccionada", 
                              foreground="#ffffff", background="#333333", padding=10)
        lbl_preview.pack(fill="x", padx=5, pady=5)
        
        # Actualizar la vista previa inicial
        update_font_preview()
        
        # Tamaño de fuente
        frame_font_size = ttk.Frame(frame_left_column)
        frame_font_size.pack(fill="x", padx=5, pady=5)
        
        lbl_font_size = ttk.Label(frame_font_size, text="Tamaño de fuente:", width=20)
        lbl_font_size.pack(side="left")
        
        spin_font_size = ttk.Spinbox(frame_font_size, from_=12, to=120, increment=2, 
                                   textvariable=self.app.settings_subtitles_font_size, width=5)
        spin_font_size.pack(side="left", padx=5)
        
        # Color de fuente - Columna izquierda
        frame_font_color = ttk.Frame(frame_left_column)
        frame_font_color.pack(fill="x", padx=10, pady=5)
        
        lbl_font_color = ttk.Label(frame_font_color, text="Color de texto:", width=20)
        lbl_font_color.pack(side="left")
        
        color_combo = ttk.Combobox(frame_font_color, textvariable=self.app.settings_subtitles_font_color, state="readonly")
        color_combo['values'] = ["white", "yellow", "black", "red", "blue", "green", "orange"]
        color_combo.pack(side="left", padx=5)
        
        # Color de borde - Columna izquierda
        frame_stroke_color = ttk.Frame(frame_left_column)
        frame_stroke_color.pack(fill="x", padx=10, pady=5)
        
        lbl_stroke_color = ttk.Label(frame_stroke_color, text="Color de borde:", width=20)
        lbl_stroke_color.pack(side="left")
        
        stroke_combo = ttk.Combobox(frame_stroke_color, textvariable=self.app.settings_subtitles_stroke_color, state="readonly")
        stroke_combo['values'] = ["black", "white", "yellow", "red", "blue", "green", "orange"]
        stroke_combo.pack(side="left", padx=5)
        
        # Grosor de borde - Columna izquierda
        frame_stroke_width = ttk.Frame(frame_left_column)
        frame_stroke_width.pack(fill="x", padx=10, pady=5)
        
        lbl_stroke_width = ttk.Label(frame_stroke_width, text="Grosor de borde:", width=20)
        lbl_stroke_width.pack(side="left")
        
        spin_stroke_width = ttk.Spinbox(frame_stroke_width, from_=0, to=5, increment=1, 
                                       textvariable=self.app.settings_subtitles_stroke_width, width=5)
        spin_stroke_width.pack(side="left", padx=5)
        
        # Alineación horizontal del texto - Columna derecha
        frame_align = ttk.Frame(frame_right_column)
        frame_align.pack(fill="x", padx=10, pady=5)
        
        lbl_align = ttk.Label(frame_align, text="Alineación de texto:", width=20)
        lbl_align.pack(side="left")
        
        align_combo = ttk.Combobox(frame_align, textvariable=self.app.settings_subtitles_align, state="readonly")
        align_combo['values'] = ["left", "center", "right"]
        align_combo.pack(side="left", padx=5)
        
        # Posición vertical - Columna derecha
        frame_position_v = ttk.Frame(frame_right_column)
        frame_position_v.pack(fill="x", padx=10, pady=5)
        
        lbl_position_v = ttk.Label(frame_position_v, text="Posición vertical:", width=20)
        lbl_position_v.pack(side="left")
        
        position_v_combo = ttk.Combobox(frame_position_v, textvariable=self.app.settings_subtitles_position_v, state="readonly")
        position_v_combo['values'] = ["top", "center", "bottom"]
        position_v_combo.pack(side="left", padx=5)
        
        # Posición horizontal - Columna derecha
        frame_position_h = ttk.Frame(frame_right_column)
        frame_position_h.pack(fill="x", padx=10, pady=5)
        
        lbl_position_h = ttk.Label(frame_position_h, text="Posición horizontal:", width=20)
        lbl_position_h.pack(side="left")
        
        position_h_combo = ttk.Combobox(frame_position_h, textvariable=self.app.settings_subtitles_position_h, state="readonly")
        position_h_combo['values'] = ["left", "center", "right"]
        position_h_combo.pack(side="left", padx=5)
        
        # Margen de subtítulos - Columna derecha
        frame_margin = ttk.Frame(frame_right_column)
        frame_margin.pack(fill="x", padx=10, pady=5)
        
        lbl_margin = ttk.Label(frame_margin, text="Margen desde borde:", width=20)
        lbl_margin.pack(side="left")
        
        # Crear la variable si no existe
        if not hasattr(self.app, 'settings_subtitles_margin'):
            self.app.settings_subtitles_margin = tk.DoubleVar(value=0.20)  # Valor predeterminado 20%
        
        # Spinbox para el margen (0% a 25%)
        margin_spinbox = ttk.Spinbox(
            frame_margin, 
            from_=0.0, 
            to=0.25, 
            increment=0.01, 
            textvariable=self.app.settings_subtitles_margin, 
            width=5,
            format="%.2f"
        )
        margin_spinbox.pack(side="left", padx=5)
        
        lbl_margin_info = ttk.Label(
            frame_margin, 
            text="(0.08 = 8% de margen desde el borde)",
            foreground="#3498db"
        )
        lbl_margin_info.pack(side="left", padx=10)
        
        # Nota informativa
        lbl_note = ttk.Label(main_frame, 
                          text="Nota: Los subtítulos se generarán automáticamente a partir del audio usando Whisper si está disponible.", 
                          foreground="#e67e22",
                          font=("Helvetica", 10, "italic"))
        lbl_note.pack(pady=10)