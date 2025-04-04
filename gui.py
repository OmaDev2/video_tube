#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from PIL import Image, ImageTk
from glob import glob
import time
from pathlib import Path

# Importar tqdm para la barra de progreso
from tqdm.tk import tqdm as tqdm_tk

# Importar los módulos personalizados
from efectos import ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, PanRightEffect, KenBurnsEffect
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect
from app import crear_video_desde_imagenes

# Importar el gestor de procesamiento por lotes para TTS
from batch_tts import BatchTTSManager

# Importar el formato de salida de audio
try:
    from tts_generator import OUTPUT_FORMAT
except ImportError:
    OUTPUT_FORMAT = "mp3"  # Valor por defecto si no se puede importar

# Importar funciones para subtítulos
from subtitles import generate_srt_with_whisper, WHISPER_AVAILABLE

# Importar Whisper si está disponible
if WHISPER_AVAILABLE:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ADVERTENCIA: No se pudo importar WhisperModel a pesar de que WHISPER_AVAILABLE es True")

class VideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Creator")
        self.root.geometry("900x950")
        
        # Inicializar el gestor de procesamiento por lotes para TTS
        self.batch_tts_manager = BatchTTSManager(root)
        
        # --- Inicializar variables para subtítulos ---
        self.settings_subtitles = tk.BooleanVar(value=True)
        self.settings_subtitles_font_size = tk.IntVar(value=24)
        self.settings_subtitles_font_color = tk.StringVar(value='white')
        self.settings_subtitles_stroke_color = tk.StringVar(value='black')
        self.settings_subtitles_stroke_width = tk.IntVar(value=1)
        
        # --- Inicializar variables para configuración de Whisper ---
        self.whisper_model = None
        self.whisper_model_size = tk.StringVar(value="base")  # Opciones: "tiny", "base", "small", "medium", "large-v3"
        self.whisper_device = tk.StringVar(value="cpu")  # Usar "cuda" si tienes GPU compatible
        self.whisper_compute_type = tk.StringVar(value="int8")  # Optimizado para CPU
        self.whisper_language = tk.StringVar(value="es")  # Idioma para transcripción
        self.whisper_word_timestamps = tk.BooleanVar(value=True)  # Usar timestamps por palabra
        
        # Cargar el modelo Whisper si está disponible
        if WHISPER_AVAILABLE:
            try:
                print(f"INFO GUI: Cargando modelo Whisper '{self.whisper_model_size.get()}' para {self.whisper_device.get()}...")
                self.whisper_model = WhisperModel(
                    self.whisper_model_size.get(),
                    device=self.whisper_device.get(),
                    compute_type=self.whisper_compute_type.get()
                )
                print("INFO GUI: Modelo Whisper cargado exitosamente.")
            except Exception as e_load_model:
                print(f"ERROR GUI: No se pudo cargar el modelo Whisper: {e_load_model}")
                messagebox.showwarning(
                    "Advertencia: Modelo Whisper",
                    f"No se pudo cargar el modelo Whisper '{self.whisper_model_size.get()}'. \n"
                    f"La generación automática de subtítulos no estará disponible.\n"
                    f"Error: {e_load_model}"
                )
        else:
            print("INFO GUI: faster-whisper no está disponible. No se cargará el modelo Whisper.")
        
        # Configurar el tema y estilo
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#2c3e50")
        self.style.configure("TLabel", background="#2c3e50", font=("Helvetica", 12), foreground="white")
        self.style.configure("TButton", padding=6, relief="flat", background="#4a90e2", foreground="white")
        self.style.map("TButton",
            foreground=[("pressed", "white"), ("active", "white")],
            background=[("pressed", "#2171cd"), ("active", "#357abd")],
            relief=[("pressed", "groove"), ("!pressed", "ridge")])
        
        # Estilo para los botones principales
        self.style.configure("Primary.TButton", font=("Helvetica", 11, "bold"), padding=8,
                            background="#3498db", foreground="white")
        self.style.map("Primary.TButton",
            background=[("pressed", "#2980b9"), ("active", "#2980b9")])
        
        # Estilo para los frames
        self.style.configure("Card.TFrame", background="#34495e", relief="flat", borderwidth=0)
        self.style.configure("Header.TLabel", font=("Helvetica", 12, "bold"), foreground="white")
        
        # Estilo para el Notebook
        self.style.configure("TNotebook", background="#2c3e50", borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[15, 8], font=("Helvetica", 11, "bold"))
        self.style.map("TNotebook.Tab",
            background=[("selected", "#d35400"), ("!selected", "#34495e")],
            foreground=[("selected", "white"), ("!selected", "#ecf0f1")])
        
        # Estilo para LabelFrame
        self.style.configure("TLabelframe", background="#2c3e50", borderwidth=0, relief="flat")
        self.style.configure("TLabelframe.Label", background="#2c3e50", foreground="white", font=("Helvetica", 10, "bold"))
        
        # Estilo para Checkbutton y Radiobutton
        self.style.configure("TCheckbutton", background="#2c3e50", font=("Helvetica", 10), foreground="white")
        self.style.configure("TRadiobutton", background="#2c3e50", font=("Helvetica", 10), foreground="white")
        
        # Estilo para Entry y Spinbox
        self.style.configure("TEntry", padding=5, relief="flat")
        self.style.configure("TSpinbox", padding=5, relief="flat")
        
        # Estilo para Progressbar
        self.style.configure("TProgressbar", background="#d35400", troughcolor="#2c3e50", borderwidth=0, thickness=10)
        
        # Estilo para botones secundarios
        self.style.configure("Secondary.TButton", background="#d35400", foreground="white")
        self.style.map("Secondary.TButton",
            background=[("pressed", "#a04000"), ("active", "#e67e22")])
        
        # Estilo para botones de acción
        self.style.configure("Action.TButton", background="#28a745", foreground="white")
        self.style.map("Action.TButton",
            background=[("pressed", "#218838"), ("active", "#218838")])
        
        # Configurar el fondo principal
        self.root.configure(bg="#2c3e50")
        
        # Variables para almacenar la configuración
        self.directorio_imagenes = tk.StringVar(value="images")
        self.archivo_salida = tk.StringVar(value="video_salida.mp4")
        self.duracion_img = tk.DoubleVar(value=5.0)
        self.fps = tk.IntVar(value=24)
        self.aplicar_efectos = tk.BooleanVar(value=True)
        self.tipo_efecto = tk.StringVar(value="in")
        self.modo_efecto = tk.StringVar(value="2")
        self.secuencia_efectos = tk.StringVar()
        self.aplicar_transicion = tk.BooleanVar(value=True)
        self.tipo_transicion = tk.StringVar(value="dissolve")
        self.duracion_transicion = tk.DoubleVar(value=2.0)
        self.aplicar_fade_in = tk.BooleanVar(value=True)
        self.duracion_fade_in = tk.DoubleVar(value=2.0)
        self.aplicar_fade_out = tk.BooleanVar(value=True)
        self.duracion_fade_out = tk.DoubleVar(value=2.0)
        self.aplicar_overlay = tk.BooleanVar(value=False)  # Activar overlays por defecto
        self.opacidad_overlay = tk.DoubleVar(value=0.5)
        
        # Variables para audio
        self.aplicar_musica = tk.BooleanVar(value=True)
        self.archivo_musica = tk.StringVar()
        self.volumen_musica = tk.DoubleVar(value=0.3)
        self.aplicar_fade_in_musica = tk.BooleanVar(value=True)
        self.duracion_fade_in_musica = tk.DoubleVar(value=2.0)
        self.aplicar_fade_out_musica = tk.BooleanVar(value=True)
        self.duracion_fade_out_musica = tk.DoubleVar(value=2.0)
        
        self.aplicar_voz = tk.BooleanVar(value=True)
        self.archivo_voz = tk.StringVar()
        self.volumen_voz = tk.DoubleVar(value=0.75)
        self.aplicar_fade_in_voz = tk.BooleanVar(value=True)
        self.duracion_fade_in_voz = tk.DoubleVar(value=2.0)
        self.aplicar_fade_out_voz = tk.BooleanVar(value=True)
        self.duracion_fade_out_voz = tk.DoubleVar(value=2.0)
        
        # Variables para las etiquetas de volumen
        self.etiqueta_volumen_musica = tk.StringVar(value="100")
        self.etiqueta_volumen_voz = tk.StringVar(value="100")
        
        # Variables para los ajustes de efectos
        # ZoomEffect
        self.settings_zoom_ratio = tk.DoubleVar(value=0.5)
        self.settings_zoom_quality = tk.StringVar(value='high')
        
        # PanEffect (común para Up/Down/Left/Right)
        self.settings_pan_scale_factor = tk.DoubleVar(value=1.2)
        self.settings_pan_easing = tk.BooleanVar(value=True)
        self.settings_pan_quality = tk.StringVar(value='high')
        
        # KenBurnsEffect
        self.settings_kb_zoom_ratio = tk.DoubleVar(value=0.3)
        self.settings_kb_scale_factor = tk.DoubleVar(value=1.3)
        self.settings_kb_quality = tk.StringVar(value='high')
        self.settings_kb_direction = tk.StringVar(value='random')
        
        # Transiciones
        self.settings_transition_duration = tk.DoubleVar(value=1.0)
        self.settings_transition_type = tk.StringVar(value='fade')
        
        # Overlay Effects
        self.settings_overlay_opacity = tk.DoubleVar(value=0.3)
        self.settings_overlay_blend_mode = tk.StringVar(value='normal')
        
        # Variable para controlar la cancelación del proceso
        self.proceso_cancelado = False
        self.pbar = None
        
        # Lista para almacenar las imágenes encontradas
        self.imagenes = []
        # Lista para almacenar los overlays seleccionados
        self.overlays_seleccionados = []
        
        # Crear la interfaz
        self.crear_interfaz()
        
        # Cargar automáticamente las imágenes y overlays al iniciar
        self.root.after(500, self.buscar_imagenes)
        self.root.after(1000, self.buscar_y_seleccionar_overlays)
        
        # Iniciar el worker para procesar la cola de TTS
        self.batch_tts_manager.start_worker()
    
    def crear_interfaz(self):
        # Crear un frame superior para el botón de crear video
        frame_superior = ttk.Frame(self.root)
        frame_superior.pack(fill="x", padx=10, pady=5)
        
        # Botón para crear el video (en la parte superior derecha)
        btn_crear = ttk.Button(frame_superior, text="Crear Video", command=self.crear_video, style="Primary.TButton")
        btn_crear.pack(side="right", padx=5)
        
        # Crear un notebook (pestañas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de cola de proyectos para TTS
        tab_batch = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_batch, text="Cola de Proyectos")
        
        # Pestaña de configuración de subtítulos con Whisper
        tab_subtitles = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_subtitles, text="Subtítulos")
        
        # Pestaña de efectos visuales (incluye efectos, transiciones y fade in/out)
        tab_efectos = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_efectos, text="Efectos Visuales")
        
        # Pestaña de configuración básica
        tab_basico = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_basico, text="Configuración Básica")
           # Pestaña de audio
        tab_audio = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_audio, text="Audio")
        
        # Pestaña de overlays
        tab_overlay = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_overlay, text="Overlays")
                # Pestaña de ajustes de efectos
        tab_settings = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_settings, text="Ajustes de Efectos")
        # Pestaña de vista previa
        tab_preview = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_preview, text="Vista Previa")
        
    
        # Configurar cada pestaña
        self.configurar_tab_basico(tab_basico)
        self.configurar_tab_efectos(tab_efectos)
        self.configurar_tab_overlay(tab_overlay)
        self.configurar_tab_audio(tab_audio)
        self.configurar_tab_preview(tab_preview)
        self.configurar_tab_settings(tab_settings)
        self.configurar_tab_batch(tab_batch)
        self.configurar_tab_subtitles(tab_subtitles)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=100, mode="indeterminate", style="TProgressbar")
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Etiqueta de estado
        self.lbl_estado = ttk.Label(self.root, text="Listo", style="Header.TLabel")
        self.lbl_estado.pack(anchor="w", padx=10)
    
    def configurar_tab_basico(self, tab):
        # Frame para la selección de directorio
        frame_dir = ttk.LabelFrame(tab, text="Directorio de Imágenes")
        frame_dir.pack(fill="x", padx=10, pady=10)
        
        entry_dir = ttk.Entry(frame_dir, textvariable=self.directorio_imagenes, width=50)
        entry_dir.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        btn_dir = ttk.Button(frame_dir, text="Examinar", command=self.seleccionar_directorio, style="Secondary.TButton")
        btn_dir.pack(side="right", padx=5, pady=10)
        
        # Frame para el archivo de salida
        frame_salida = ttk.LabelFrame(tab, text="Archivo de Salida")
        frame_salida.pack(fill="x", padx=10, pady=10)
        
        entry_salida = ttk.Entry(frame_salida, textvariable=self.archivo_salida, width=50)
        entry_salida.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        btn_salida = ttk.Button(frame_salida, text="Examinar", command=self.seleccionar_archivo_salida, style="Secondary.TButton")
        btn_salida.pack(side="right", padx=5, pady=10)
        
        # Frame para la duración y FPS
        frame_duracion = ttk.LabelFrame(tab, text="Configuración de Tiempo")
        frame_duracion.pack(fill="x", padx=10, pady=10)
        
        # Duración de cada imagen
        lbl_duracion = ttk.Label(frame_duracion, text="Duración de cada imagen (segundos):", style="Header.TLabel")
        lbl_duracion.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_duracion = ttk.Spinbox(frame_duracion, from_=1, to=20, increment=0.5, textvariable=self.duracion_img, width=5)
        spin_duracion.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # FPS
        lbl_fps = ttk.Label(frame_duracion, text="Frames por segundo (FPS):", style="Header.TLabel")
        lbl_fps.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        spin_fps = ttk.Spinbox(frame_duracion, from_=15, to=60, increment=1, textvariable=self.fps, width=5)
        spin_fps.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Lista de imágenes encontradas
        frame_imagenes = ttk.LabelFrame(tab, text="Imágenes Encontradas")
        frame_imagenes.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear un Treeview para mostrar las imágenes
        self.tree_imagenes = ttk.Treeview(frame_imagenes, columns=("nombre", "ruta"), show="headings")
        self.tree_imagenes.heading("nombre", text="Nombre")
        self.tree_imagenes.heading("ruta", text="Ruta")
        self.tree_imagenes.column("nombre", width=150)
        self.tree_imagenes.column("ruta", width=350)
        self.tree_imagenes.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(self.tree_imagenes, orient="vertical", command=self.tree_imagenes.yview)
        self.tree_imagenes.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Botón para buscar imágenes
        btn_buscar = ttk.Button(frame_imagenes, text="Buscar Imágenes", command=self.buscar_imagenes, style="Action.TButton")
        btn_buscar.pack(pady=5)
    
    def configurar_tab_efectos(self, tab):
        """Configura la interfaz de usuario para la pestaña de efectos visuales, transiciones y fade in/out."""

        # Crear un notebook interno para organizar las secciones
        notebook_efectos = ttk.Notebook(tab)
        notebook_efectos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear las subpestañas
        tab_movimiento = ttk.Frame(notebook_efectos, style="Card.TFrame")
        tab_transiciones = ttk.Frame(notebook_efectos, style="Card.TFrame")
        tab_fade = ttk.Frame(notebook_efectos, style="Card.TFrame")
        
        # Añadir las subpestañas al notebook
        notebook_efectos.add(tab_movimiento, text="Efectos de Movimiento")
        notebook_efectos.add(tab_transiciones, text="Transiciones")
        notebook_efectos.add(tab_fade, text="Fade In/Out")
        
        # Configurar cada subpestaña
        self.configurar_tab_efectos_movimiento(tab_movimiento)
        self.configurar_tab_transiciones(tab_transiciones)
        self.configurar_tab_fade(tab_fade)
    
    def configurar_tab_efectos_movimiento(self, tab):
        """Configura la interfaz de usuario para la subpestaña de efectos de movimiento."""

        # --- Contenedor Principal ---
        frame_principal = ttk.Frame(tab)
        frame_principal.pack(fill="both", expand=True)
        frame_principal.columnconfigure(0, weight=1) # Hacer que la columna se expanda

        # --- Checkbox General ---
        chk_efectos = ttk.Checkbutton(frame_principal, text="Aplicar efectos de movimiento",
                                      variable=self.aplicar_efectos, command=self._actualizar_estado_controles)
        # Usamos grid para mejor control dentro del frame_principal
        chk_efectos.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="w")

        # --- Frame para Modos ---
        self.frame_opciones = ttk.LabelFrame(frame_principal, text="Modo de Efecto")
        self.frame_opciones.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.frame_opciones.columnconfigure(1, weight=1) # Columna de radiobuttons se expande un poco

        modos = [
            ("Un solo tipo de efecto", "1"),
            ("Secuencia personalizada", "2"),
            ("Alternar automáticamente (in/out)", "3"),
            ("Secuencia Ken Burns (Preset)", "4") # Cambiado nombre para claridad
        ]

        for i, (texto, valor) in enumerate(modos):
            rb = ttk.Radiobutton(self.frame_opciones, text=texto, variable=self.modo_efecto,
                                 value=valor, command=self._actualizar_visibilidad_paneles)
            # Colocar en una sola columna para claridad
            rb.grid(row=i, column=0, columnspan=2, padx=10, pady=3, sticky="w")


        # --- Frame para "Un Solo Tipo de Efecto" ---
        self.frame_tipo = ttk.LabelFrame(frame_principal, text="Seleccionar Tipo Único")
        # Se añadirá con grid más adelante, inicialmente oculto si no es el modo 1
        self.frame_tipo.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        self.frame_tipo.columnconfigure(0, weight=1)
        self.frame_tipo.columnconfigure(1, weight=1)
        self.frame_tipo.columnconfigure(2, weight=1) # Tres columnas para radio buttons

        tipos_efectos = [
            ("Zoom In", "in"), ("Zoom Out", "out"),
            ("Pan Up", "panup"), ("Pan Down", "pandown"),
            ("Pan Left", "panleft"), ("Pan Right", "panright"),
            ("Ken Burns", "kenburns"),
            ("Viñeta Zoom In", "vignette_zoom_in"), ("Viñeta Zoom Out", "vignette_zoom_out"),
            ("Rotación Horaria", "rotate_clockwise"), ("Rotación Antihoraria", "rotate_counter_clockwise"),
            ("Voltear Horizontal", "flip_horizontal"), ("Voltear Vertical", "flip_vertical")
        ]

        num_cols_tipo = 3
        for i, (texto, valor) in enumerate(tipos_efectos):
            rb = ttk.Radiobutton(self.frame_tipo, text=texto, variable=self.tipo_efecto, value=valor)
            row_num = i // num_cols_tipo
            col_num = i % num_cols_tipo
            rb.grid(row=row_num, column=col_num, padx=10, pady=3, sticky="w")

        # --- Frame para "Secuencia Personalizada" ---
        self.frame_secuencia = ttk.LabelFrame(frame_principal, text="Configurar Secuencia")
        # Se añadirá con grid más adelante, inicialmente oculto si no es el modo 2
        self.frame_secuencia.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        self.frame_secuencia.columnconfigure(0, weight=1) # Hacer que la columna 0 se expanda
        
        # Inicializar variables para los checkboxes si no existen
        if not hasattr(self, 'efecto_checkboxes'):
            self.efecto_checkboxes = {
                'in': tk.BooleanVar(), 'out': tk.BooleanVar(), 'panup': tk.BooleanVar(),
                'pandown': tk.BooleanVar(), 'panleft': tk.BooleanVar(), 'panright': tk.BooleanVar(),
                'kenburns': tk.BooleanVar(), 'kenburns1': tk.BooleanVar(), 'kenburns2': tk.BooleanVar(),
                'kenburns3': tk.BooleanVar(), 'flip_horizontal': tk.BooleanVar(), 'flip_vertical': tk.BooleanVar(),
                'vignette_zoom_in': tk.BooleanVar(), 'vignette_zoom_out': tk.BooleanVar(),
                'rotate_clockwise': tk.BooleanVar(), 'rotate_counter_clockwise': tk.BooleanVar()
            }
            
        # Lista ordenada para mantener el orden visual y de selección
        self._efectos_ordenados_secuencia = list(self.efecto_checkboxes.keys())
        self._efectos_ordenados_secuencia.sort() # Ordenar alfabéticamente
        
        # Textos descriptivos para los efectos
        self.efectos_texto = {
            'in': 'Zoom In', 'out': 'Zoom Out', 'panup': 'Pan Up',
            'pandown': 'Pan Down', 'panleft': 'Pan Left', 'panright': 'Pan Right',
            'kenburns': 'Ken Burns (Clásico)', 'kenburns1': 'Ken Burns 1',
            'kenburns2': 'Ken Burns 2', 'kenburns3': 'Ken Burns 3',
            'flip_horizontal': 'Voltear Horizontal', 'flip_vertical': 'Voltear Vertical',
            'vignette_zoom_in': 'Viñeta Zoom In', 'vignette_zoom_out': 'Viñeta Zoom Out',
            'rotate_clockwise': 'Rotación Horaria', 'rotate_counter_clockwise': 'Rotación Antihoraria'
        }
        
        # Etiqueta para la secuencia
        lbl_secuencia = ttk.Label(self.frame_secuencia, text="Selecciona los efectos para la secuencia:")
        lbl_secuencia.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Frame para contener los checkboxes en columnas
        frame_checkboxes = ttk.Frame(self.frame_secuencia)
        frame_checkboxes.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        # Crear checkboxes en tres columnas para mejor organización
        num_cols = 3
        efectos_lista = self._efectos_ordenados_secuencia
        
        for i, efecto in enumerate(efectos_lista):
            col = i % num_cols
            row = i // num_cols
            
            chk = ttk.Checkbutton(frame_checkboxes, 
                                 text=self.efectos_texto[efecto],
                                 variable=self.efecto_checkboxes[efecto],
                                 command=self.actualizar_secuencia_efectos)
            chk.grid(row=row, column=col, padx=10, pady=2, sticky="w")
        
        # Etiqueta para mostrar la secuencia actual
        lbl_secuencia_actual = ttk.Label(self.frame_secuencia, text="Secuencia actual:")
        lbl_secuencia_actual.grid(row=2, column=0, padx=5, pady=(10,0), sticky="w")
        
        self.lbl_secuencia_preview = ttk.Label(self.frame_secuencia, text="", wraplength=400)
        self.lbl_secuencia_preview.grid(row=3, column=0, padx=5, pady=(0,5), sticky="w")
        
        # Botones para manipular el orden
        frame_botones = ttk.Frame(self.frame_secuencia)
        frame_botones.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        btn_mover_arriba = ttk.Button(frame_botones, text="↑ Mover Arriba", 
                                    command=lambda: self.mover_efecto(-1))
        btn_mover_arriba.pack(side="left", padx=5)
        
        btn_mover_abajo = ttk.Button(frame_botones, text="↓ Mover Abajo", 
                                   command=lambda: self.mover_efecto(1))
        btn_mover_abajo.pack(side="left", padx=5)
        
        # Inicialmente, mostrar el panel correcto según el modo seleccionado
        self._actualizar_visibilidad_paneles()
    
    def _actualizar_visibilidad_paneles(self):
        """Actualiza la visibilidad de los paneles según el modo seleccionado."""
        modo = self.modo_efecto.get()
        
        # Ocultar todos los paneles primero
        self.frame_tipo.grid_remove()
        self.frame_secuencia.grid_remove()
        
        # Mostrar el panel correspondiente al modo seleccionado
        if modo == "1":  # Un solo tipo de efecto
            self.frame_tipo.grid()
        elif modo == "2":  # Secuencia personalizada
            self.frame_secuencia.grid()
        # Los modos 3 y 4 no tienen paneles específicos adicionales
    
    def _actualizar_estado_controles(self):
        """Actualiza el estado de los controles según si los efectos están activados."""
        estado = "normal" if self.aplicar_efectos.get() else "disabled"
        
        # Actualizar estado de los controles en el frame de opciones
        for child in self.frame_opciones.winfo_children():
            child.configure(state=estado)
        
        # Actualizar estado de los controles en el frame de tipo único
        for child in self.frame_tipo.winfo_children():
            child.configure(state=estado)
        
        # Actualizar estado de los controles en el frame de secuencia
        for child in self.frame_secuencia.winfo_children():
            if isinstance(child, ttk.Frame):  # Para frames anidados
                for subchild in child.winfo_children():
                    subchild.configure(state=estado)
            else:
                child.configure(state=estado)
    
    def actualizar_secuencia_efectos(self):
        # Obtener los efectos seleccionados en orden
        efectos_seleccionados = []
        for efecto, var in self.efecto_checkboxes.items():
            if var.get():
                efectos_seleccionados.append(efecto)
        
        # Actualizar la variable de secuencia
        self.secuencia_efectos.set(','.join(efectos_seleccionados))
        
        # Actualizar la etiqueta de vista previa
        if efectos_seleccionados:
            texto_preview = "Secuencia: " + " → ".join(efectos_seleccionados)
        else:
            texto_preview = "No hay efectos seleccionados"
        self.lbl_secuencia_preview.config(text=texto_preview)
    
    def mover_efecto(self, direccion):
        # Obtener la secuencia actual
        secuencia = self.secuencia_efectos.get().split(',') if self.secuencia_efectos.get() else []
        if not secuencia:
            return
        
        # Encontrar el último efecto seleccionado
        seleccionados = []
        for efecto, var in self.efecto_checkboxes.items():
            if var.get():
                seleccionados.append(efecto)
        
        if not seleccionados:
            return
        
        # Mover el último efecto seleccionado
        efecto_a_mover = seleccionados[-1]
        pos_actual = secuencia.index(efecto_a_mover)
        
        # Calcular nueva posición
        nueva_pos = pos_actual + direccion
        if 0 <= nueva_pos < len(secuencia):
            # Intercambiar posiciones
            secuencia[pos_actual], secuencia[nueva_pos] = secuencia[nueva_pos], secuencia[pos_actual]
            
            # Actualizar la secuencia
            self.secuencia_efectos.set(','.join(secuencia))
            
            # Actualizar la vista previa
            texto_preview = "Secuencia: " + " → ".join(secuencia)
            self.lbl_secuencia_preview.config(text=texto_preview)
    
    def configurar_tab_transiciones(self, tab):
        # Checkbox para activar transiciones
        chk_transiciones = ttk.Checkbutton(tab, text="Aplicar transiciones entre imágenes", variable=self.aplicar_transicion)
        chk_transiciones.pack(anchor="w", padx=10, pady=10)
        
        # Frame para las opciones de transición
        frame_transicion = ttk.LabelFrame(tab, text="Opciones de Transición")
        frame_transicion.pack(fill="x", padx=10, pady=10)
        
        # Tipo de transición
        lbl_tipo = ttk.Label(frame_transicion, text="Tipo de transición:")
        lbl_tipo.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Obtener las transiciones disponibles
        transiciones = TransitionEffect.get_available_transitions()
        
        # Combobox para seleccionar la transición
        combo_transicion = ttk.Combobox(frame_transicion, textvariable=self.tipo_transicion, values=transiciones, state="readonly")
        combo_transicion.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        combo_transicion.current(1)  # Seleccionar 'dissolve' como elemento por defecto
        
        # Duración de la transición
        lbl_duracion = ttk.Label(frame_transicion, text="Duración de la transición (segundos):")
        lbl_duracion.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        spin_duracion = ttk.Spinbox(frame_transicion, from_=0.5, to=5.0, increment=0.5, textvariable=self.duracion_transicion, width=5)
        spin_duracion.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    def configurar_tab_fade(self, tab):
        # Fade In
        frame_fade_in = ttk.LabelFrame(tab, text="Fade In")
        frame_fade_in.pack(fill="x", padx=10, pady=10)
        
        chk_fade_in = ttk.Checkbutton(frame_fade_in, text="Aplicar fade in al inicio del video", variable=self.aplicar_fade_in)
        chk_fade_in.pack(anchor="w", padx=5, pady=5)
        
        lbl_duracion_in = ttk.Label(frame_fade_in, text="Duración del fade in (segundos):")
        lbl_duracion_in.pack(anchor="w", padx=5, pady=5)
        
        spin_duracion_in = ttk.Spinbox(frame_fade_in, from_=0.5, to=5.0, increment=0.5, textvariable=self.duracion_fade_in, width=5)
        spin_duracion_in.pack(anchor="w", padx=5, pady=5)
        
        # Fade Out
        frame_fade_out = ttk.LabelFrame(tab, text="Fade Out")
        frame_fade_out.pack(fill="x", padx=10, pady=10)
        
        chk_fade_out = ttk.Checkbutton(frame_fade_out, text="Aplicar fade out al final del video", variable=self.aplicar_fade_out)
        chk_fade_out.pack(anchor="w", padx=5, pady=5)
        
        lbl_duracion_out = ttk.Label(frame_fade_out, text="Duración del fade out (segundos):")
        lbl_duracion_out.pack(anchor="w", padx=5, pady=5)
        
        spin_duracion_out = ttk.Spinbox(frame_fade_out, from_=0.5, to=5.0, increment=0.5, textvariable=self.duracion_fade_out, width=5)
        spin_duracion_out.pack(anchor="w", padx=5, pady=5)
    
    def configurar_tab_overlay(self, tab):
        # Frame para overlays
        frame_overlay = ttk.LabelFrame(tab, text="Efectos de Overlay")
        frame_overlay.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar overlay
        chk_overlay = ttk.Checkbutton(frame_overlay, text="Aplicar overlay", variable=self.aplicar_overlay)
        chk_overlay.pack(anchor="w", padx=5, pady=5)
        
        # Frame para la lista de overlays
        frame_lista = ttk.Frame(frame_overlay)
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Listbox con scrollbar para overlays
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox_overlays = tk.Listbox(frame_lista, selectmode="multiple", yscrollcommand=scrollbar.set,
                                          height=6, activestyle="none", bg="#e0e0e0", fg="black",
                                          selectbackground="#d35400", selectforeground="white")
        self.listbox_overlays.pack(side="left", fill="both", expand=True)
        
        # Agregar binding para actualizar automáticamente cuando se hace clic
        self.listbox_overlays.bind('<<ListboxSelect>>', lambda e: self.actualizar_overlays_seleccionados())
        
        scrollbar.config(command=self.listbox_overlays.yview)
        
        # Frame para botones
        frame_botones = ttk.Frame(frame_overlay)
        frame_botones.pack(fill="x", padx=5, pady=5)
        
        # Botón para buscar overlays
        btn_buscar = ttk.Button(frame_botones, text="Buscar Overlays", command=self.buscar_overlays)
        btn_buscar.pack(side="left", padx=5)
        
        # Botón para seleccionar overlays (más prominente)
        btn_seleccionar = ttk.Button(frame_botones, text="Aplicar Overlays Seleccionados", 
                                   command=self.seleccionar_overlays, style="Action.TButton")
        btn_seleccionar.pack(side="left", padx=5)
        
        # Control de opacidad
        frame_opacidad = ttk.Frame(frame_overlay)
        frame_opacidad.pack(fill="x", padx=5, pady=5)
        
        lbl_opacidad = ttk.Label(frame_opacidad, text="Opacidad:")
        lbl_opacidad.pack(side="left", padx=5)
        
        # Etiqueta para mostrar el valor actual de opacidad
        self.lbl_valor_opacidad = ttk.Label(frame_opacidad, text=f"{self.opacidad_overlay.get():.2f}")
        self.lbl_valor_opacidad.pack(side="right", padx=5)
        
        # Función para actualizar la etiqueta cuando cambia el valor
        def actualizar_valor_opacidad(*args):
            self.lbl_valor_opacidad.config(text=f"{self.opacidad_overlay.get():.2f}")
        
        # Vincular la función al cambio de valor
        self.opacidad_overlay.trace_add("write", actualizar_valor_opacidad)
        
        scale_opacidad = ttk.Scale(frame_opacidad, from_=0.0, to=1.0, orient="horizontal", 
                                  variable=self.opacidad_overlay)
        scale_opacidad.pack(side="left", fill="x", expand=True, padx=5)
        
        # Etiqueta para mostrar los overlays seleccionados
        self.lbl_overlays_seleccionados = ttk.Label(frame_overlay, text="No hay overlays seleccionados", 
                                                 foreground="#e74c3c")
        self.lbl_overlays_seleccionados.pack(anchor="w", padx=5, pady=5)
        
        # Etiqueta informativa
        lbl_info = ttk.Label(frame_overlay, 
                            text="Haz clic en los overlays que deseas aplicar. Se actualizarán automáticamente.")
        lbl_info.pack(anchor="w", padx=5, pady=5)
    
    def configurar_tab_audio(self, tab):
        # Frame para música de fondo
        frame_musica = ttk.LabelFrame(tab, text="Música de Fondo")
        frame_musica.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar música
        chk_musica = ttk.Checkbutton(frame_musica, text="Aplicar música de fondo", variable=self.aplicar_musica)
        chk_musica.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Selección de archivo de música
        lbl_archivo_musica = ttk.Label(frame_musica, text="Archivo de música:")
        lbl_archivo_musica.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        frame_archivo_musica = ttk.Frame(frame_musica)
        frame_archivo_musica.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        entry_musica = ttk.Entry(frame_archivo_musica, textvariable=self.archivo_musica, width=40)
        entry_musica.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_musica = ttk.Button(frame_archivo_musica, text="Examinar", command=self.seleccionar_archivo_musica)
        btn_musica.pack(side="right")
        
        # Control de volumen
        lbl_volumen_musica = ttk.Label(frame_musica, text="Volumen:")
        lbl_volumen_musica.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Añadir una función para convertir el valor del slider a un valor de volumen logarítmico
        def convertir_volumen_musica(valor_slider):
            # Convertir el valor lineal (0-1) a logarítmico para mejor control en niveles bajos
            # Esto da más precisión en el rango bajo (música ambiental)
            valor_slider = float(valor_slider)
            if valor_slider <= 0:
                return 0
            # Escala logarítmica menos agresiva: valores bajos son más audibles
            # Rango: 0.03 (3%) a 1.0 (100%)
            return 0.03 + (valor_slider * 0.97)
        
        # Añadir una función para actualizar el volumen cuando se mueve el slider
        def actualizar_volumen_musica(valor):
            valor_float = float(valor)
            # Calcular el valor real (logarítmico)
            valor_real = convertir_volumen_musica(valor_float)
            # Actualizar la variable de volumen
            self.volumen_musica.set(valor_real)
            # Actualizar la etiqueta (mostrar como porcentaje)
            self.etiqueta_volumen_musica.set(f"{valor_real*100:.1f}%")
        
        # Usar un slider con escala visual lineal pero que internamente usa valores logarítmicos
        scale_volumen_musica = ttk.Scale(frame_musica, from_=0.0, to=1.0, orient="horizontal", 
                                       length=200, command=actualizar_volumen_musica)
        # Valor inicial del slider muy bajo para volumen ambiental (3%)
        scale_volumen_musica.set(0.0)
        scale_volumen_musica.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        # Inicializar el valor real y la etiqueta
        valor_inicial = convertir_volumen_musica(0.0)  # 3% de volumen
        self.volumen_musica.set(valor_inicial)
        self.etiqueta_volumen_musica.set(f"{valor_inicial*100:.1f}%")
        etiqueta_volumen_musica = ttk.Label(frame_musica, textvariable=self.etiqueta_volumen_musica)
        etiqueta_volumen_musica.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Fade in/out para música
        frame_fade_musica = ttk.Frame(frame_musica)
        frame_fade_musica.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Fade in
        chk_fade_in_musica = ttk.Checkbutton(frame_fade_musica, text="Fade in", 
                                          variable=self.aplicar_fade_in_musica)
        chk_fade_in_musica.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_in_musica = ttk.Label(frame_fade_musica, text="Duración (s):")
        lbl_fade_in_musica.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_in_musica = ttk.Spinbox(frame_fade_musica, from_=0.5, to=10.0, increment=0.5, 
                                        textvariable=self.duracion_fade_in_musica, width=5)
        spin_fade_in_musica.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Fade out
        chk_fade_out_musica = ttk.Checkbutton(frame_fade_musica, text="Fade out", 
                                           variable=self.aplicar_fade_out_musica)
        chk_fade_out_musica.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_out_musica = ttk.Label(frame_fade_musica, text="Duración (s):")
        lbl_fade_out_musica.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_out_musica = ttk.Spinbox(frame_fade_musica, from_=0.5, to=10.0, increment=0.5, 
                                         textvariable=self.duracion_fade_out_musica, width=5)
        spin_fade_out_musica.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Frame para voz en off
        frame_voz = ttk.LabelFrame(tab, text="Voz en Off")
        frame_voz.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar voz
        chk_voz = ttk.Checkbutton(frame_voz, text="Aplicar voz en off", variable=self.aplicar_voz)
        chk_voz.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Selección de archivo de voz
        lbl_archivo_voz = ttk.Label(frame_voz, text="Archivo de voz:")
        lbl_archivo_voz.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        frame_archivo_voz = ttk.Frame(frame_voz)
        frame_archivo_voz.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        entry_voz = ttk.Entry(frame_archivo_voz, textvariable=self.archivo_voz, width=40)
        entry_voz.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_voz = ttk.Button(frame_archivo_voz, text="Examinar", command=self.seleccionar_archivo_voz)
        btn_voz.pack(side="right")
        
        # Control de volumen
        lbl_volumen_voz = ttk.Label(frame_voz, text="Volumen:")
        lbl_volumen_voz.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        scale_volumen_voz = ttk.Scale(frame_voz, from_=0.0, to=1.0, orient="horizontal", 
                                    variable=self.volumen_voz, length=200, command=self.actualizar_etiqueta_volumen_voz)
        scale_volumen_voz.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        self.etiqueta_volumen_voz.set(f"{self.volumen_voz.get()*100:.0f}%")
        etiqueta_volumen_voz = ttk.Label(frame_voz, textvariable=self.etiqueta_volumen_voz)
        etiqueta_volumen_voz.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Fade in/out para voz
        frame_fade_voz = ttk.Frame(frame_voz)
        frame_fade_voz.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Fade in
        chk_fade_in_voz = ttk.Checkbutton(frame_fade_voz, text="Fade in", 
                                       variable=self.aplicar_fade_in_voz)
        chk_fade_in_voz.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_in_voz = ttk.Label(frame_fade_voz, text="Duración (s):")
        lbl_fade_in_voz.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_in_voz = ttk.Spinbox(frame_fade_voz, from_=0.5, to=10.0, increment=0.5, 
                                     textvariable=self.duracion_fade_in_voz, width=5)
        spin_fade_in_voz.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Fade out
        chk_fade_out_voz = ttk.Checkbutton(frame_fade_voz, text="Fade out", 
                                        variable=self.aplicar_fade_out_voz)
        chk_fade_out_voz.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_out_voz = ttk.Label(frame_fade_voz, text="Duración (s):")
        lbl_fade_out_voz.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_out_voz = ttk.Spinbox(frame_fade_voz, from_=0.5, to=10.0, increment=0.5, 
                                      textvariable=self.duracion_fade_out_voz, width=5)
        spin_fade_out_voz.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Información adicional
        lbl_info = ttk.Label(tab, text="Nota: Los archivos de audio deben estar en formato MP3, WAV o OGG.")
        lbl_info.pack(anchor="w", padx=10, pady=10)
        
    def actualizar_etiqueta_volumen_musica(self, valor):
        self.etiqueta_volumen_musica.set(f"{float(valor)*100:.0f}%")
        
    def actualizar_etiqueta_volumen_voz(self, valor):
        self.etiqueta_volumen_voz.set(f"{float(valor)*100:.0f}%")
    
    def configurar_tab_preview(self, tab):
        # Frame para la vista previa
        frame_preview = ttk.LabelFrame(tab, text="Vista Previa de Imágenes")
        frame_preview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas para mostrar la imagen
        self.canvas = tk.Canvas(frame_preview, bg="black", width=640, height=360)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame para los controles
        frame_controles = ttk.Frame(tab)
        frame_controles.pack(fill="x", padx=10, pady=10)
        
        # Botones para navegar entre imágenes
        btn_anterior = ttk.Button(frame_controles, text="Anterior", command=self.mostrar_imagen_anterior)
        btn_anterior.pack(side="left", padx=5)
        
        btn_siguiente = ttk.Button(frame_controles, text="Siguiente", command=self.mostrar_imagen_siguiente)
        btn_siguiente.pack(side="left", padx=5)
        
        # Variable para almacenar el índice de la imagen actual
        self.indice_imagen_actual = 0
        
        # Variable para almacenar la imagen actual (para evitar que sea eliminada por el recolector de basura)
        self.imagen_actual = None
    
    def configurar_tab_settings(self, tab):
        """Configura la pestaña de ajustes de efectos"""
        # Crear un canvas con scrollbar para manejar muchos widgets
        canvas = tk.Canvas(tab, background="#34495e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Ajustes ZoomEffect ---
        frame_zoom = ttk.LabelFrame(scrollable_frame, text="Zoom Effect", style="Card.TLabelframe")
        frame_zoom.pack(fill="x", padx=10, pady=5)

        # Ratio de zoom
        lbl_zoom_ratio = ttk.Label(frame_zoom, text="Ratio de zoom:")
        lbl_zoom_ratio.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_zoom = ttk.Spinbox(frame_zoom, from_=0.1, to=2.0, increment=0.1, 
                              textvariable=self.settings_zoom_ratio, width=8)
        spin_zoom.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_zoom_quality = ttk.Label(frame_zoom, text="Calidad:")
        lbl_zoom_quality.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_zoom_quality = ttk.Combobox(frame_zoom, textvariable=self.settings_zoom_quality, 
                                        values=["low", "medium", "high"], width=8)
        combo_zoom_quality.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes PanEffect ---
        frame_pan = ttk.LabelFrame(scrollable_frame, text="Pan Effect", style="Card.TLabelframe")
        frame_pan.pack(fill="x", padx=10, pady=5)
        
        # Factor de escala
        lbl_pan_scale = ttk.Label(frame_pan, text="Factor de escala:")
        lbl_pan_scale.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_pan_scale = ttk.Spinbox(frame_pan, from_=1.0, to=2.0, increment=0.1, 
                                   textvariable=self.settings_pan_scale_factor, width=8)
        spin_pan_scale.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Easing
        chk_pan_easing = ttk.Checkbutton(frame_pan, text="Easing (suavizado)", 
                                       variable=self.settings_pan_easing)
        chk_pan_easing.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_pan_quality = ttk.Label(frame_pan, text="Calidad:")
        lbl_pan_quality.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        combo_pan_quality = ttk.Combobox(frame_pan, textvariable=self.settings_pan_quality, 
                                       values=["low", "medium", "high"], width=8)
        combo_pan_quality.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes KenBurnsEffect ---
        frame_kb = ttk.LabelFrame(scrollable_frame, text="Ken Burns Effect", style="Card.TLabelframe")
        frame_kb.pack(fill="x", padx=10, pady=5)
        
        # Ratio de zoom
        lbl_kb_zoom = ttk.Label(frame_kb, text="Ratio de zoom:")
        lbl_kb_zoom.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_kb_zoom = ttk.Spinbox(frame_kb, from_=0.1, to=1.0, increment=0.1, 
                                 textvariable=self.settings_kb_zoom_ratio, width=8)
        spin_kb_zoom.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Factor de escala
        lbl_kb_scale = ttk.Label(frame_kb, text="Factor de escala:")
        lbl_kb_scale.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        spin_kb_scale = ttk.Spinbox(frame_kb, from_=1.0, to=2.0, increment=0.1, 
                                  textvariable=self.settings_kb_scale_factor, width=8)
        spin_kb_scale.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Dirección
        lbl_kb_direction = ttk.Label(frame_kb, text="Dirección:")
        lbl_kb_direction.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        combo_kb_direction = ttk.Combobox(frame_kb, textvariable=self.settings_kb_direction, 
                                        values=["random", "in", "out", "left", "right", "up", "down"], width=8)
        combo_kb_direction.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_kb_quality = ttk.Label(frame_kb, text="Calidad:")
        lbl_kb_quality.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        combo_kb_quality = ttk.Combobox(frame_kb, textvariable=self.settings_kb_quality, 
                                      values=["low", "medium", "high"], width=8)
        combo_kb_quality.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes Transiciones ---
        frame_transition = ttk.LabelFrame(scrollable_frame, text="Transiciones", style="Card.TLabelframe")
        frame_transition.pack(fill="x", padx=10, pady=5)
        
        # Duración
        lbl_transition_duration = ttk.Label(frame_transition, text="Duración (s):")
        lbl_transition_duration.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_transition_duration = ttk.Spinbox(frame_transition, from_=0.5, to=3.0, increment=0.5, 
                                             textvariable=self.settings_transition_duration, width=8)
        spin_transition_duration.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Tipo
        lbl_transition_type = ttk.Label(frame_transition, text="Tipo:")
        lbl_transition_type.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_transition_type = ttk.Combobox(frame_transition, textvariable=self.settings_transition_type, 
                                           values=["none", "dissolve"], width=10)
        combo_transition_type.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        combo_transition_type.current(1)  # Seleccionar 'dissolve' por defecto
        
        # --- Ajustes Overlay ---
        frame_overlay = ttk.LabelFrame(scrollable_frame, text="Overlay Effects", style="Card.TLabelframe")
        frame_overlay.pack(fill="x", padx=10, pady=5)
        
        # Opacidad
        lbl_overlay_opacity = ttk.Label(frame_overlay, text="Opacidad:")
        lbl_overlay_opacity.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_overlay_opacity = ttk.Spinbox(frame_overlay, from_=0.1, to=1.0, increment=0.1, 
                                         textvariable=self.settings_overlay_opacity, width=8)
        spin_overlay_opacity.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Modo de mezcla
        lbl_overlay_blend = ttk.Label(frame_overlay, text="Modo de mezcla:")
        lbl_overlay_blend.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_overlay_blend = ttk.Combobox(frame_overlay, textvariable=self.settings_overlay_blend_mode, 
                                         values=["normal", "overlay", "screen", "multiply"], width=10)
        combo_overlay_blend.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Información de ayuda
        lbl_info = ttk.Label(scrollable_frame, text="Estos ajustes se aplicarán a todos los efectos del mismo tipo.", 
                           wraplength=400)
        lbl_info.pack(padx=10, pady=10)
    
    def seleccionar_directorio(self):
        directorio = filedialog.askdirectory(title="Seleccionar directorio de imágenes")
        if directorio:
            self.directorio_imagenes.set(directorio)
            self.buscar_imagenes()
    
    def seleccionar_archivo_salida(self):
        archivo = filedialog.asksaveasfilename(
            title="Guardar video como",
            defaultextension=".mp4",
            filetypes=[("Archivos MP4", "*.mp4"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.archivo_salida.set(archivo)
            
    def seleccionar_archivo_musica(self):
        # Establecer el directorio de música por defecto
        musica_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'musica')
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de música",
            initialdir=musica_dir,
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.ogg"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("OGG", "*.ogg"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.archivo_musica.set(archivo)
            
    def seleccionar_archivo_voz(self):
        # Establecer el directorio de voz por defecto
        voz_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz en off')
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de voz",
            initialdir=voz_dir,
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.ogg"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("OGG", "*.ogg"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.archivo_voz.set(archivo)
    
    def buscar_imagenes(self):
        directorio = self.directorio_imagenes.get()
        if not directorio or not os.path.exists(directorio):
            messagebox.showerror("Error", "El directorio no existe")
            return
        
        # Limpiar la lista actual
        self.tree_imagenes.delete(*self.tree_imagenes.get_children())
        self.imagenes = []
        
        # Buscar imágenes en el directorio
        formatos = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        for formato in formatos:
            self.imagenes.extend(glob(os.path.join(directorio, formato)))
        
        self.imagenes.sort()  # Ordenar alfabéticamente
        
        # Mostrar las imágenes en el Treeview
        for imagen in self.imagenes:
            nombre = os.path.basename(imagen)
            self.tree_imagenes.insert("", "end", values=(nombre, imagen))
        
        # Actualizar el estado
        self.lbl_estado.config(text=f"Se encontraron {len(self.imagenes)} imágenes")
        
        # Mostrar la primera imagen en la vista previa si hay imágenes
        if self.imagenes:
            self.indice_imagen_actual = 0
            self.mostrar_imagen_actual()
    
    def buscar_overlays(self):
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlays')
        
        # Verificar si el directorio existe
        if not os.path.exists(overlay_dir):
            os.makedirs(overlay_dir)  # Crear el directorio si no existe
            messagebox.showinfo("Información", "Se ha creado la carpeta 'overlays'. Coloca tus archivos de overlay en esta carpeta.")
            return
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Limpiar la lista actual
        self.listbox_overlays.delete(0, tk.END)
        
        # Mostrar los overlays en el Listbox
        if not overlays_disponibles:
            messagebox.showinfo("Información", "No se encontraron archivos de overlay en la carpeta 'overlays'.\nColoca archivos de video (.mp4, .mov, .avi, .webm) en la carpeta 'overlays'.")
        else:
            for overlay in overlays_disponibles:
                self.listbox_overlays.insert(tk.END, overlay)
            
            # Actualizar el estado
            self.lbl_estado.config(text=f"Se encontraron {len(overlays_disponibles)} overlays")
            # Seleccionar automáticamente el primer overlay
            self.listbox_overlays.selection_set(0)
            # Actualizar la lista de overlays seleccionados
            self.actualizar_overlays_seleccionados()
    
    def seleccionar_overlays(self):
        # Actualizar la lista de overlays seleccionados
        self.actualizar_overlays_seleccionados()
        
        # Mostrar mensaje de confirmación
        if self.overlays_seleccionados:
            messagebox.showinfo("Overlays Seleccionados", 
                              f"Se han seleccionado {len(self.overlays_seleccionados)} overlays:\n\n" + 
                              "\n".join([os.path.basename(o) for o in self.overlays_seleccionados]))
        else:
            messagebox.showinfo("Información", "No has seleccionado ningún overlay")
    
    def actualizar_overlays_seleccionados(self):
        # Obtener los índices seleccionados
        indices = self.listbox_overlays.curselection()
        
        # Limpiar la lista actual de overlays seleccionados
        self.overlays_seleccionados = []
        
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlays')
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Agregar los overlays seleccionados a la lista
        for indice in indices:
            if indice < len(overlays_disponibles):
                ruta_overlay = os.path.join(overlay_dir, overlays_disponibles[indice])
                self.overlays_seleccionados.append(ruta_overlay)
        
        # Actualizar el estado y la etiqueta de overlays seleccionados
        if self.overlays_seleccionados:
            self.lbl_estado.config(text=f"Se han seleccionado {len(self.overlays_seleccionados)} overlays")
            
            # Actualizar la etiqueta con los nombres de los overlays seleccionados
            nombres_overlays = [os.path.basename(path) for path in self.overlays_seleccionados]
            if len(nombres_overlays) <= 3:
                texto_overlays = "Seleccionados: " + ", ".join(nombres_overlays)
            else:
                texto_overlays = f"Seleccionados: {nombres_overlays[0]}, {nombres_overlays[1]} y {len(nombres_overlays)-2} más"
            
            self.lbl_overlays_seleccionados.config(text=texto_overlays, foreground="#27ae60")
        else:
            self.lbl_overlays_seleccionados.config(text="No hay overlays seleccionados", foreground="#e74c3c")
    
    def buscar_y_seleccionar_overlays(self):
        """Busca y selecciona automáticamente todos los overlays disponibles"""
        # Directorio de overlays
        overlay_dir = "/Users/olga/Development/proyectosPython/VideoPython/overlays"
        
        # Verificar si el directorio existe
        if not os.path.exists(overlay_dir):
            os.makedirs(overlay_dir)  # Crear el directorio si no existe
            print("Se ha creado la carpeta 'overlays'. Coloca tus archivos de overlay en esta carpeta.")
            return
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Limpiar la lista actual
        self.listbox_overlays.delete(0, tk.END)
        
        # Mostrar los overlays en el Listbox
        if not overlays_disponibles:
            print("No se encontraron archivos de overlay en la carpeta 'overlays'.")
            self.aplicar_overlay.set(False)  # Desactivar si no hay overlays
            self.lbl_overlays_seleccionados.config(text="No hay overlays disponibles", foreground="#e74c3c")
        else:
            # Asegurar que la opción de aplicar overlay esté activada
            self.aplicar_overlay.set(True)
            
            for overlay in overlays_disponibles:
                self.listbox_overlays.insert(tk.END, overlay)
            
            # Seleccionar automáticamente todos los overlays
            for i in range(len(overlays_disponibles)):
                self.listbox_overlays.selection_set(i)
            
            # Actualizar la lista de overlays seleccionados
            self.actualizar_overlays_seleccionados()
            
            # Actualizar la etiqueta de estado
            self.lbl_estado.config(text=f"Se cargaron {len(overlays_disponibles)} overlays automáticamente")
            print(f"Se cargaron y seleccionaron automáticamente {len(overlays_disponibles)} overlays")
    
    def mostrar_imagen_actual(self):
        if not self.imagenes or self.indice_imagen_actual < 0 or self.indice_imagen_actual >= len(self.imagenes):
            return
        
        # Obtener la ruta de la imagen actual
        ruta_imagen = self.imagenes[self.indice_imagen_actual]
        
        try:
            # Cargar la imagen con PIL
            img = Image.open(ruta_imagen)
            
            # Redimensionar la imagen para que quepa en el canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Asegurarse de que el canvas tenga un tamaño válido
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 640
                canvas_height = 360
            
            # Calcular la relación de aspecto
            img_width, img_height = img.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            
            # Calcular el nuevo tamaño
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionar la imagen
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convertir la imagen a formato Tkinter
            self.imagen_actual = ImageTk.PhotoImage(img)
            
            # Limpiar el canvas
            self.canvas.delete("all")
            
            # Calcular la posición para centrar la imagen
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # Mostrar la imagen en el canvas
            self.canvas.create_image(x, y, anchor="nw", image=self.imagen_actual)
            
            # Mostrar el nombre de la imagen
            nombre_imagen = os.path.basename(ruta_imagen)
            self.canvas.create_text(canvas_width // 2, 20, text=f"Imagen {self.indice_imagen_actual + 1}/{len(self.imagenes)}: {nombre_imagen}", fill="white")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
    
    def mostrar_imagen_anterior(self):
        if self.imagenes:
            self.indice_imagen_actual = (self.indice_imagen_actual - 1) % len(self.imagenes)
            self.mostrar_imagen_actual()
    
    def mostrar_imagen_siguiente(self):
        if self.imagenes:
            self.indice_imagen_actual = (self.indice_imagen_actual + 1) % len(self.imagenes)
            self.mostrar_imagen_actual()
    
    def crear_video(self):
        """Inicia el proceso de creación del video."""
        # Verificar si hay imágenes cargadas
        if not self.imagenes:
            messagebox.showerror("Error", "No se han cargado imágenes. Por favor, selecciona un directorio con imágenes.")
            return
        
        # Verificar si se ha seleccionado un archivo de salida
        if not self.archivo_salida.get():
            messagebox.showerror("Error", "No se ha seleccionado un archivo de salida. Por favor, selecciona un archivo de salida.")
            return
        
        # Obtener los overlays seleccionados y asegurar que la opción esté activada si hay seleccionados
        overlays = self.obtener_overlays_seleccionados()
        if overlays:
            self.aplicar_overlay.set(True)
        
        # Iniciar el proceso en un hilo separado
        self.proceso_cancelado = False
        threading.Thread(target=self.procesar_video).start()
    
    def procesar_video(self):
        try:
            # Actualizar el estado
            self.root.after(0, lambda: self.lbl_estado.config(
                text="Creando video... Por favor, espere."
            ))

            # Configurar parámetros para la función crear_video_desde_imagenes
            directorio_imagenes = "/Users/olga/Development/proyectosPython/VideoPython/images"
            archivo_salida = self.archivo_salida.get()
            
            # Crear el video
            crear_video_desde_imagenes(
                directorio_imagenes=directorio_imagenes,
                archivo_salida=archivo_salida,
                duracion_img=self.duracion_img.get(),
                fps=24,
                aplicar_efectos=self.aplicar_efectos.get(),
                secuencia_efectos=self.obtener_secuencia_efectos(),
                aplicar_transicion=self.aplicar_transicion.get(),
                tipo_transicion=self.settings_transition_type.get(),
                duracion_transicion=self.settings_transition_duration.get(),
                aplicar_overlay=bool(self.obtener_overlays_seleccionados()),
                archivos_overlay=self.obtener_overlays_seleccionados(),
                opacidad_overlay=self.settings_overlay_opacity.get(),
                aplicar_musica=bool(self.archivo_musica.get()),
                archivo_musica=self.archivo_musica.get(),
                volumen_musica=self.volumen_musica.get(),
                aplicar_fade_in_musica=self.aplicar_fade_in_musica.get(),
                duracion_fade_in_musica=self.duracion_fade_in_musica.get(),
                aplicar_fade_out_musica=self.aplicar_fade_out_musica.get(),
                duracion_fade_out_musica=self.duracion_fade_out_musica.get(),
                # Parámetros para la voz en off
                aplicar_voz=self.aplicar_voz.get(),
                archivo_voz=self.archivo_voz.get() if self.aplicar_voz.get() else None,
                volumen_voz=self.volumen_voz.get(),
                aplicar_fade_in_voz=self.aplicar_fade_in_voz.get(),
                duracion_fade_in_voz=self.duracion_fade_in_voz.get(),
                aplicar_fade_out_voz=self.aplicar_fade_out_voz.get(),
                duracion_fade_out_voz=self.duracion_fade_out_voz.get(),
                # Pasar los ajustes personalizados
                settings={
                    'zoom_ratio': self.settings_zoom_ratio.get(),
                    'zoom_quality': self.settings_zoom_quality.get(),
                    'pan_scale_factor': self.settings_pan_scale_factor.get(),
                    'pan_easing': self.settings_pan_easing.get(),
                    'pan_quality': self.settings_pan_quality.get(),
                    'kb_zoom_ratio': self.settings_kb_zoom_ratio.get(),
                    'kb_scale_factor': self.settings_kb_scale_factor.get(),
                    'kb_quality': self.settings_kb_quality.get(),
                    'kb_direction': self.settings_kb_direction.get(),
                    'transition_duration': self.settings_transition_duration.get(),
                    'transition_type': self.settings_transition_type.get(),
                    'overlay_opacity': self.settings_overlay_opacity.get(),
                    'overlay_blend_mode': self.settings_overlay_blend_mode.get()
                },
                # Parámetros para fade in/out del video
                aplicar_fade_in=self.aplicar_fade_in.get(),
                duracion_fade_in=self.duracion_fade_in.get(),
                aplicar_fade_out=self.aplicar_fade_out.get(),
                duracion_fade_out=self.duracion_fade_out.get()
            )

            # Actualizar el estado al finalizar
            self.root.after(0, lambda: self.lbl_estado.config(
                text="¡Video creado con éxito!"
            ))
            messagebox.showinfo("Éxito", "El video se ha creado correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al crear el video: {str(e)}")
            self.root.after(0, lambda: self.lbl_estado.config(
                text="Error al crear el video"
            ))
    
    def obtener_secuencia_efectos(self):
        """Obtiene la lista de efectos seleccionados para la secuencia"""
        if self.aplicar_efectos.get():
            # Si estamos en modo de un solo efecto (modo_efecto = 1), devolver ese efecto para todas las imágenes
            if self.modo_efecto.get() == "1":
                return [self.tipo_efecto.get()] * len(self.imagenes)
            # Si estamos en modo secuencia (modo_efecto = 2), devolver la secuencia de efectos
            elif self.modo_efecto.get() == "2":
                secuencia = self.secuencia_efectos.get().split(',') if self.secuencia_efectos.get() else []
                if not secuencia:
                    return None
                # Si hay menos efectos que imágenes, repetir la secuencia
                if len(secuencia) < len(self.imagenes):
                    repeticiones = (len(self.imagenes) // len(secuencia)) + 1
                    secuencia = secuencia * repeticiones
                return secuencia[:len(self.imagenes)]
            # Si estamos en modo alternar in/out (modo_efecto = 3)
            elif self.modo_efecto.get() == "3":
                return ['in', 'out'] * (len(self.imagenes) // 2 + 1)
            # Si estamos en modo Ken Burns predefinido (modo_efecto = 4)
            elif self.modo_efecto.get() == "4":
                secuencia = ['kenburns', 'kenburns1', 'kenburns2', 'kenburns3']
                repeticiones = (len(self.imagenes) // len(secuencia)) + 1
                return (secuencia * repeticiones)[:len(self.imagenes)]
        return None
    
    def finalizar_proceso(self, exito, mensaje):
        # Detener la barra de progreso
        self.progress.stop()
        
        # Actualizar el estado
        self.lbl_estado.config(text=mensaje)
        
        # Asegurarse de que la barra de progreso tqdm_tk esté cerrada
        if hasattr(self, 'pbar') and self.pbar is not None:
            try:
                self.pbar.close()
            except:
                pass
            self.pbar = None
        
        # Mostrar mensaje
        if exito:
            messagebox.showinfo("Éxito", mensaje)
        else:
            messagebox.showerror("Error", mensaje)
    
    def cancelar_proceso(self):
        # Esta función se llama cuando el usuario cancela el proceso de creación de video
        self.proceso_cancelado = True
        self.lbl_estado.config(text="Proceso cancelado por el usuario")
        messagebox.showinfo("Cancelado", "El proceso de creación de video ha sido cancelado.")
        self.progress.stop()
        
        # Cerrar la barra de progreso si existe
        if hasattr(self, 'pbar'):
            self.pbar.close()

    def configurar_tab_batch(self, tab):
        """Configura la pestaña de cola de proyectos para TTS."""
        # --- Sección de Entrada ---
        frame_input = ttk.LabelFrame(tab, text="Nuevo Proyecto")
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
        
        self.selected_voice = tk.StringVar(value=voces[0])
        voice_combo = ttk.Combobox(frame_input, textvariable=self.selected_voice, values=voces, width=30)
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
                                  command=self.add_project_to_queue, style="Action.TButton")
        btn_add_queue.pack(side="right", padx=5)
        
        btn_clear = ttk.Button(frame_buttons, text="Limpiar Campos",
                              command=self.clear_project_fields, style="Secondary.TButton")
        btn_clear.pack(side="right", padx=5)

        # --- Sección de Cola ---
        frame_queue = ttk.LabelFrame(tab, text="Cola de Procesamiento")
        frame_queue.pack(fill="both", expand=True, padx=10, pady=10)

        # Usaremos un Treeview para mostrar la cola
        self.tree_queue = ttk.Treeview(frame_queue, columns=("titulo", "estado", "tiempo"), show="headings", height=10)
        self.tree_queue.heading("titulo", text="Título del Proyecto")
        self.tree_queue.heading("estado", text="Estado")
        self.tree_queue.heading("tiempo", text="Tiempo")
        self.tree_queue.column("titulo", width=400)
        self.tree_queue.column("estado", width=150, anchor="center")
        self.tree_queue.column("tiempo", width=100, anchor="center")

        # Scrollbar para el Treeview
        scrollbar_queue = ttk.Scrollbar(frame_queue, orient="vertical", command=self.tree_queue.yview)
        self.tree_queue.configure(yscrollcommand=scrollbar_queue.set)

        self.tree_queue.pack(side="left", fill="both", expand=True)
        scrollbar_queue.pack(side="right", fill="y")
        
        # --- NUEVO BOTÓN ---
        frame_acciones_cola = ttk.Frame(frame_queue)
        frame_acciones_cola.pack(fill="x", pady=10)

        btn_generate_video = ttk.Button(frame_acciones_cola,
                                        text="Generar Vídeo del Proyecto Seleccionado",
                                        command=self.trigger_video_generation_for_selected,
                                        style="Action.TButton")
        btn_generate_video.pack(side="right", padx=5)
        
        # Asignar el Treeview al gestor de cola
        self.batch_tts_manager.tree_queue = self.tree_queue
        
        # Etiqueta de estado de la cola
        self.lbl_queue_status = ttk.Label(tab, text="Cola vacía", style="Header.TLabel")
        self.lbl_queue_status.pack(anchor="w", padx=10, pady=5)
        
        # Actualizar el estado de la cola cada 2 segundos
        self.update_queue_status()
    
    def add_project_to_queue(self):
        """Añade un nuevo proyecto a la cola de procesamiento."""
        title = self.entry_title.get().strip()
        script = self.txt_script.get("1.0", tk.END).strip()
        voice = self.selected_voice.get()
        
        # Capturar todos los ajustes actuales de la GUI para la creación de video
        # Obtener secuencia de efectos
        selected_effects_sequence = self.obtener_secuencia_efectos()
        
        # Recoger ajustes específicos de efectos
        effect_settings = {
            'zoom_ratio': self.settings_zoom_ratio.get(),
            'zoom_quality': self.settings_zoom_quality.get(),
            'pan_scale_factor': self.settings_pan_scale_factor.get(),
            'pan_easing': self.settings_pan_easing.get(),
            'pan_quality': self.settings_pan_quality.get(),
            'kb_zoom_ratio': self.settings_kb_zoom_ratio.get(),
            'kb_scale_factor': self.settings_kb_scale_factor.get(),
            'kb_quality': self.settings_kb_quality.get(),
            'kb_direction': self.settings_kb_direction.get(),
            'overlay_opacity': self.settings_overlay_opacity.get(),
            'overlay_blend_mode': self.settings_overlay_blend_mode.get()
        }
        
        # Obtener overlays seleccionados
        overlays = self.obtener_overlays_seleccionados()
        
        # Crear diccionario con todos los ajustes para la creación de video
        video_settings = {
            'duracion_img': self.duracion_img.get(),
            'fps': self.fps.get(),
            'aplicar_efectos': self.aplicar_efectos.get(),
            'secuencia_efectos': selected_effects_sequence,
            'aplicar_transicion': self.aplicar_transicion.get(),
            'tipo_transicion': self.tipo_transicion.get(),
            'duracion_transicion': self.duracion_transicion.get(),
            'aplicar_fade_in': self.aplicar_fade_in.get(),
            'duracion_fade_in': self.duracion_fade_in.get(),
            'aplicar_fade_out': self.aplicar_fade_out.get(),
            'duracion_fade_out': self.duracion_fade_out.get(),
            'aplicar_overlay': bool(overlays),
            'archivos_overlay': [str(Path(ov).resolve()) for ov in overlays] if overlays else None,
            'opacidad_overlay': self.opacidad_overlay.get(),
            'aplicar_musica': self.aplicar_musica.get(),
            'archivo_musica': str(Path(self.archivo_musica.get()).resolve()) if self.archivo_musica.get() else None,
            'volumen_musica': self.volumen_musica.get(),
            'aplicar_fade_in_musica': self.aplicar_fade_in_musica.get(),
            'duracion_fade_in_musica': self.duracion_fade_in_musica.get(),
            'aplicar_fade_out_musica': self.aplicar_fade_out_musica.get(),
            'duracion_fade_out_musica': self.duracion_fade_out_musica.get(),
            'volumen_voz': self.volumen_voz.get(),
            'aplicar_fade_in_voz': self.aplicar_fade_in_voz.get(),
            'duracion_fade_in_voz': self.duracion_fade_in_voz.get(),
            'aplicar_fade_out_voz': self.aplicar_fade_out_voz.get(),
            'duracion_fade_out_voz': self.duracion_fade_out_voz.get(),
            'aplicar_subtitulos': False,  # Por ahora no soportamos subtítulos automáticos
            'settings': effect_settings
        }
        
        success = self.batch_tts_manager.add_project_to_queue(title, script, voice, video_settings)
        
        if success:
            messagebox.showinfo("Proyecto Añadido", 
                              f"El proyecto '{title}' ha sido añadido a la cola.\n\n" +
                              "Nota: Para generar el video, crea manualmente una carpeta 'imagenes' " +
                              "dentro de la carpeta del proyecto y coloca ahí las imágenes que quieres usar.")
            self.clear_project_fields()
            self.update_queue_status()
    
    def clear_project_fields(self):
        """Limpia los campos del formulario de proyecto."""
        self.entry_title.delete(0, tk.END)
        self.txt_script.delete("1.0", tk.END)
    
    def update_queue_status(self):
        """Actualiza la etiqueta de estado de la cola."""
        status = self.batch_tts_manager.get_queue_status()
        
        if status['total'] == 0:
            self.lbl_queue_status.config(text="Cola vacía")
        else:
            self.lbl_queue_status.config(
                text=f"Total: {status['total']} | Pendientes: {status['pendientes']} | "
                     f"Completados: {status['completados']} | Errores: {status['errores']}"
            )
        
        # Programar la próxima actualización
        self.root.after(2000, self.update_queue_status)
        
    def trigger_video_generation_for_selected(self):
        """Inicia la generación de video para el proyecto seleccionado en la cola."""
        selected_items = self.tree_queue.selection()
        if not selected_items:
            messagebox.showerror("Error", "Por favor, selecciona un proyecto de la cola.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Por favor, selecciona solo un proyecto a la vez para generar el vídeo.")
            return

        job_id = selected_items[0]
        if job_id not in self.batch_tts_manager.jobs_in_gui:
            messagebox.showerror("Error", f"No se encontraron datos para el trabajo seleccionado (ID: {job_id}).")
            return

        job_data = self.batch_tts_manager.jobs_in_gui[job_id]
        project_folder = job_data['carpeta_salida']
        expected_audio_file = str(Path(project_folder) / f"voz.{OUTPUT_FORMAT}")
        image_folder = Path(project_folder) / "imagenes"

        # --- Verificaciones Previas ---
        if not Path(project_folder).is_dir():
            messagebox.showerror("Error", f"La carpeta del proyecto no existe:\n{project_folder}")
            return
        if not Path(expected_audio_file).is_file():
            messagebox.showerror("Error", f"No se encontró el archivo de audio generado:\n{expected_audio_file}\nAsegúrate de que el estado sea 'Audio Completo'.")
            return
        if not image_folder.is_dir() or not any(image_folder.iterdir()): # Verificar si existe y no está vacía
            messagebox.showerror("Error", f"No se encontró la carpeta '{image_folder.name}' o está vacía.\nPor favor, crea la carpeta y añade imágenes antes de generar el vídeo.")
            return

        print(f"\n--- Iniciando generación de vídeo para trabajo {job_id} ---")
        self.batch_tts_manager.update_job_status_gui(job_id, "Preparando vídeo...")

        # --- Recoger Ajustes ACTUALES de la GUI ---
        try:
            # Crear un diccionario con los ajustes de efectos
            current_settings = {
                'zoom_ratio': self.settings_zoom_ratio.get(),
                'zoom_quality': self.settings_zoom_quality.get(),
                'pan_scale_factor': self.settings_pan_scale_factor.get(),
                'pan_easing': self.settings_pan_easing.get(),
                'pan_quality': self.settings_pan_quality.get(),
                'kb_zoom_ratio': self.settings_kb_zoom_ratio.get(),
                'kb_scale_factor': self.settings_kb_scale_factor.get(),
                'kb_quality': self.settings_kb_quality.get(),
                'kb_direction': self.settings_kb_direction.get(),
                'overlay_opacity': self.settings_overlay_opacity.get(),
                'overlay_blend_mode': self.settings_overlay_blend_mode.get()
            }
            
            # Obtener secuencia de efectos actual
            current_efectos_sequence = self.obtener_secuencia_efectos_actual()

            # Actualizar el estado en la GUI antes de lanzar el hilo
            self.batch_tts_manager.update_job_status_gui(job_id, "Generando Vídeo...")
            self.progress['value'] = 0  # Resetear barra de progreso para este vídeo
            self.root.update_idletasks()

            # --- Lanzar Creación de Vídeo en un Hilo Separado ---
            video_thread = threading.Thread(
                target=self._run_video_generation_thread,
                args=(
                    job_id,  # Pasar ID para actualizar estado al final
                    project_folder,
                    expected_audio_file,  # Ruta al audio generado
                ),
                kwargs={
                    # Pasar todos los parámetros con nombre para evitar errores de orden
                    'duracion_img': self.duracion_img.get(),
                    'fps': self.fps.get(),
                    'aplicar_efectos': self.aplicar_efectos.get(),
                    'secuencia_efectos': current_efectos_sequence,
                    'aplicar_transicion': self.aplicar_transicion.get(),
                    'tipo_transicion': self.tipo_transicion.get(),
                    'duracion_transicion': self.duracion_transicion.get(),
                    'aplicar_fade_in': self.aplicar_fade_in.get(),
                    'duracion_fade_in': self.duracion_fade_in.get(),
                    'aplicar_fade_out': self.aplicar_fade_out.get(),
                    'duracion_fade_out': self.duracion_fade_out.get(),
                    'aplicar_overlay': self.aplicar_overlay.get(),
                    'archivos_overlay': self.obtener_overlays_seleccionados(),
                    'opacidad_overlay': self.opacidad_overlay.get(),
                    'aplicar_musica': self.aplicar_musica.get(),
                    'archivo_musica': self.archivo_musica.get() if self.aplicar_musica.get() else None,
                    'volumen_musica': self.volumen_musica.get(),
                    'aplicar_fade_in_musica': self.aplicar_fade_in_musica.get(),
                    'duracion_fade_in_musica': self.duracion_fade_in_musica.get(),
                    'aplicar_fade_out_musica': self.aplicar_fade_out_musica.get(),
                    'duracion_fade_out_musica': self.duracion_fade_out_musica.get(),
                    'volumen_voz': self.volumen_voz.get(),
                    'aplicar_fade_in_voz': self.aplicar_fade_in_voz.get(),
                    'duracion_fade_in_voz': self.duracion_fade_in_voz.get(),
                    'aplicar_fade_out_voz': self.aplicar_fade_out_voz.get(),
                    'duracion_fade_out_voz': self.duracion_fade_out_voz.get(),
                    # Usar los subtítulos generados si existen
                    'aplicar_subtitulos': job_data.get('aplicar_subtitulos', False),
                    'archivo_subtitulos': job_data.get('archivo_subtitulos', None),
                    'settings': current_settings,
                    'tamano_fuente_subtitulos': self.settings_subtitles_font_size.get(),
                    'color_fuente_subtitulos': self.settings_subtitles_font_color.get(),
                    'color_borde_subtitulos': self.settings_subtitles_stroke_color.get(),
                    'grosor_borde_subtitulos': self.settings_subtitles_stroke_width.get(),
                    'progress_callback': self.update_progress_bar
                },
                daemon=True
            )
            video_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error al preparar la generación de vídeo: {e}")
            self.batch_tts_manager.update_job_status_gui(job_id, f"Error Preparación: {e}")
    
    def _run_video_generation_thread(self, job_id, project_folder, audio_file, **kwargs):
        """Función que se ejecuta en un hilo para crear UN video."""
        success = False
        message = "Error desconocido"
        try:
            # Llamar a la función principal pasándole todos los argumentos con nombre
            kwargs['archivo_voz'] = audio_file  # Asegurar que archivo_voz esté configurado
            
            # Verificar si hay subtítulos y asegurarse de que se apliquen
            archivo_subtitulos = kwargs.get('archivo_subtitulos')
            if archivo_subtitulos and os.path.exists(archivo_subtitulos):
                print(f"Encontrado archivo de subtítulos: {archivo_subtitulos}")
                kwargs['aplicar_subtitulos'] = True
                # Verificar si el archivo tiene contenido
                try:
                    with open(archivo_subtitulos, 'r', encoding='utf-8') as f:
                        contenido = f.read().strip()
                        if contenido:
                            print(f"El archivo de subtítulos tiene {len(contenido)} caracteres")
                        else:
                            print("ADVERTENCIA: El archivo de subtítulos está vacío")
                            kwargs['aplicar_subtitulos'] = False
                except Exception as e_srt:
                    print(f"Error al leer archivo de subtítulos: {e_srt}")
            else:
                # Buscar archivo de subtítulos en la carpeta del proyecto
                srt_path = os.path.join(project_folder, "subtitulos.srt")
                if os.path.exists(srt_path):
                    print(f"Encontrado archivo de subtítulos en la carpeta del proyecto: {srt_path}")
                    kwargs['archivo_subtitulos'] = srt_path
                    kwargs['aplicar_subtitulos'] = True
            
            # Imprimir parámetros de subtítulos para depuración
            print(f"Parámetros de subtítulos: aplicar={kwargs.get('aplicar_subtitulos')}, archivo={kwargs.get('archivo_subtitulos')}")
            
            # Crear el video con todos los parámetros
            crear_video_desde_imagenes(
                project_folder,
                **kwargs
            )
            success = True
            message = "Vídeo Completo"

        except Exception as e:
            print(f"Excepción en hilo de vídeo para {job_id}: {e}")
            import traceback
            traceback.print_exc()
            message = f"Error Vídeo: {e}"
            success = False

        finally:
            # Notificar al hilo principal de Tkinter para actualizar la GUI
            self.root.after(0, self._video_thread_complete, job_id, success, message)
    
    def _video_thread_complete(self, job_id, success, message):
        """Actualiza la GUI cuando el hilo de generación de vídeo termina."""
        print(f"Hilo de vídeo para {job_id} completado. Éxito: {success}, Mensaje: {message}")
        self.batch_tts_manager.update_job_status_gui(job_id, message)  # Actualiza estado en Treeview
        if success:
            # Podrías añadir opción para abrir carpeta o vídeo
            pass
        else:
            # El error ya se muestra en el estado
            pass
        # Resetear barra de progreso
        self.progress['value'] = 0
        self.lbl_estado.config(text="Listo")
        
    def update_progress_bar(self, current_step, total_steps):
        """Actualiza la barra de progreso durante la generación de vídeo.
        
        Args:
            current_step: Paso actual en el proceso
            total_steps: Total de pasos a completar
        """
        # Asegurar ejecución en el hilo principal de Tkinter
        # Solo actualiza si el total es válido
        if total_steps > 0:
            self.root.after(0, self._update_progress, current_step, total_steps)
    
    def _update_progress(self, current_step, total_steps):
        """Actualiza la barra de progreso en el hilo principal de Tkinter."""
        # Calcular porcentaje y actualizar la barra determinate
        percentage = int((current_step / total_steps) * 100)
        self.progress['value'] = percentage
        # Actualizar etiqueta de estado
        self.lbl_estado.config(text=f"Generando Vídeo... {percentage}%")
        # Forzar actualización de la GUI
        self.root.update_idletasks()
    
    def obtener_secuencia_efectos_actual(self):
        """Obtiene la secuencia de efectos basada en la selección ACTUAL de la GUI."""
        if not self.aplicar_efectos.get():
            return None

        modo = self.modo_efecto.get()
        if modo == "1":  # Un solo tipo
            return [self.tipo_efecto.get()]
        elif modo == "2":  # Secuencia personalizada
            secuencia = self.secuencia_efectos.get().split(',') if self.secuencia_efectos.get() else []
            return secuencia if secuencia else ['in']
        elif modo == "3":  # Alternar
            return ['in', 'out']
        elif modo == "4":  # Ken Burns Seq
            return ['kenburns', 'kenburns1', 'kenburns2', 'kenburns3']
        else:
            return None
    
    def obtener_overlays_seleccionados(self):
        """Obtiene la lista de overlays seleccionados y asegura que la opción de aplicar esté activada."""
        # Verificar si ya tenemos overlays seleccionados
        if not self.overlays_seleccionados:
            # Si no hay overlays seleccionados, intentar obtenerlos del listbox
            indices = self.listbox_overlays.curselection()
            if indices:
                overlay_dir = "/Users/olga/Development/proyectosPython/VideoPython/overlays"
                overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
                
                for indice in indices:
                    if indice < len(overlays_disponibles):
                        ruta_overlay = os.path.join(overlay_dir, overlays_disponibles[indice])
                        self.overlays_seleccionados.append(ruta_overlay)
        
        # Si hay overlays seleccionados, asegurar que la opción de aplicar overlay esté activada
        if self.overlays_seleccionados and self.aplicar_overlay.get():
            return self.overlays_seleccionados
        else:
            return []
    
    def configurar_tab_subtitles(self, tab):
        """Configura la pestaña de subtítulos."""
        # Frame principal con padding
        main_frame = ttk.Frame(tab, style="Card.TFrame")
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
        
        size_combo = ttk.Combobox(frame_size, textvariable=self.whisper_model_size, state="readonly")
        size_combo['values'] = [size[0] for size in model_sizes]
        size_combo.pack(side="left", padx=5)
        
        # Descripción del modelo seleccionado
        self.lbl_model_desc = ttk.Label(frame_size, text="Modelo equilibrado entre velocidad y precisión", 
                                      foreground="#3498db")
        self.lbl_model_desc.pack(side="left", padx=10)
        
        # Función para actualizar la descripción del modelo
        def update_model_desc(event):
            selected = self.whisper_model_size.get()
            for size, desc in model_sizes:
                if size == selected:
                    self.lbl_model_desc.config(text=desc)
                    break
        
        size_combo.bind("<<ComboboxSelected>>", update_model_desc)
        
        # Dispositivo (CPU/GPU)
        frame_device = ttk.Frame(frame_model)
        frame_device.pack(fill="x", padx=10, pady=5)
        
        lbl_device = ttk.Label(frame_device, text="Dispositivo:", width=20)
        lbl_device.pack(side="left")
        
        device_combo = ttk.Combobox(frame_device, textvariable=self.whisper_device, state="readonly")
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
                if hasattr(self, 'whisper_model') and self.whisper_model is not None:
                    # Liberar recursos del modelo anterior
                    del self.whisper_model
                    import gc
                    gc.collect()
                
                # Cargar el nuevo modelo
                print(f"Cargando modelo Whisper '{self.whisper_model_size.get()}' para {self.whisper_device.get()}...")
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel(
                    self.whisper_model_size.get(),
                    device=self.whisper_device.get(),
                    compute_type=self.whisper_compute_type.get()
                )
                messagebox.showinfo(
                    "Modelo Whisper",
                    f"Modelo Whisper '{self.whisper_model_size.get()}' cargado exitosamente."
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
        
        lang_combo = ttk.Combobox(frame_lang, textvariable=self.whisper_language, state="readonly")
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
                                   variable=self.whisper_word_timestamps)
        word_check.pack(padx=5, pady=5)
        
        # Frame para el estilo de subtítulos
        frame_style = ttk.LabelFrame(main_frame, text="Estilo de Subtítulos", style="TLabelframe")
        frame_style.pack(fill="x", padx=10, pady=10)
        
        # Tamaño de fuente
        frame_font_size = ttk.Frame(frame_style)
        frame_font_size.pack(fill="x", padx=10, pady=5)
        
        lbl_font_size = ttk.Label(frame_font_size, text="Tamaño de fuente:", width=20)
        lbl_font_size.pack(side="left")
        
        spin_font_size = ttk.Spinbox(frame_font_size, from_=12, to=72, increment=2, 
                                    textvariable=self.settings_subtitles_font_size, width=5)
        spin_font_size.pack(side="left", padx=5)
        
        # Color de fuente
        frame_font_color = ttk.Frame(frame_style)
        frame_font_color.pack(fill="x", padx=10, pady=5)
        
        lbl_font_color = ttk.Label(frame_font_color, text="Color de texto:", width=20)
        lbl_font_color.pack(side="left")
        
        color_combo = ttk.Combobox(frame_font_color, textvariable=self.settings_subtitles_font_color, state="readonly")
        color_combo['values'] = ["white", "yellow", "black", "red", "blue", "green", "orange"]
        color_combo.pack(side="left", padx=5)
        
        # Color de borde
        frame_stroke_color = ttk.Frame(frame_style)
        frame_stroke_color.pack(fill="x", padx=10, pady=5)
        
        lbl_stroke_color = ttk.Label(frame_stroke_color, text="Color de borde:", width=20)
        lbl_stroke_color.pack(side="left")
        
        stroke_combo = ttk.Combobox(frame_stroke_color, textvariable=self.settings_subtitles_stroke_color, state="readonly")
        stroke_combo['values'] = ["black", "white", "yellow", "red", "blue", "green", "orange"]
        stroke_combo.pack(side="left", padx=5)
        
        # Grosor de borde
        frame_stroke_width = ttk.Frame(frame_style)
        frame_stroke_width.pack(fill="x", padx=10, pady=5)
        
        lbl_stroke_width = ttk.Label(frame_stroke_width, text="Grosor de borde:", width=20)
        lbl_stroke_width.pack(side="left")
        
        spin_stroke_width = ttk.Spinbox(frame_stroke_width, from_=0, to=5, increment=1, 
                                      textvariable=self.settings_subtitles_stroke_width, width=5)
        spin_stroke_width.pack(side="left", padx=5)
        
        # Nota informativa
        lbl_note = ttk.Label(main_frame, 
                           text="Nota: Los subtítulos se generarán automáticamente a partir del audio usando Whisper si está disponible.", 
                           foreground="#e67e22",
                           font=("Helvetica", 10, "italic"))
        lbl_note.pack(pady=10)

# Iniciar la aplicación si se ejecuta este archivo directamente
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCreatorApp(root)
    root.mainloop()