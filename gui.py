#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from PIL import Image, ImageTk
from glob import glob
import time
from pathlib import Path
from ui.tab_basico import BasicTabFrame
from ui.tab_project import ProjectTabFrame  # Nueva pestaña de gestión de proyectos
from project_manager import ProjectManager  # Gestor de proyectos

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
        self.project_manager = ProjectManager(self)
        
        # --- Inicializar variables para subtítulos ---
        self.settings_subtitles = tk.BooleanVar(value=True)
        self.settings_subtitles_font_size = tk.IntVar(value=54)
        self.settings_subtitles_font_color = tk.StringVar(value='white')
        self.settings_subtitles_stroke_color = tk.StringVar(value='black')
        self.settings_subtitles_stroke_width = tk.IntVar(value=3)
        self.settings_subtitles_align = tk.StringVar(value='center')
        self.settings_subtitles_position_h = tk.StringVar(value='center')
        self.settings_subtitles_position_v = tk.StringVar(value='bottom')
        self.settings_subtitles_font_name = tk.StringVar(value="Roboto-Regular")
        self.settings_use_system_font = tk.BooleanVar(value=False)
        
        # --- Inicializar variables para configuración de Whisper ---
        self.whisper_model = None
        self.whisper_model_size = tk.StringVar(value="medium")  # Opciones: "tiny", "base", "small", "medium", "large-v3"
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
        self._efectos_ordenados_secuencia.sort()  # Ordenar alfabéticamente
        
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
        
        # Variables Configuración Tab Básico
        self.directorio_imagenes = tk.StringVar(value="images")
        self.archivo_salida = tk.StringVar(value="video_salida.mp4")
        self.duracion_img = tk.DoubleVar(value=20.0)
        self.fps = tk.IntVar(value=24)
        
        # Variable para plantillas
        self.template_seleccionado = tk.StringVar()
        self.templates = {
            "basic": "Básico",
            "professional": "Profesional",
            "minimal": "Mínimo"
        }
        
        # Variables Configuración Tab Efectos y Transiciones    
        self.aplicar_efectos = tk.BooleanVar(value=True)
        self.tipo_efecto = tk.StringVar(value="in")
        self.modo_efecto = tk.StringVar(value="2")
        self.secuencia_efectos = tk.StringVar()
        self.aplicar_transicion = tk.BooleanVar(value=True)
        self.tipo_transicion = tk.StringVar(value="dissolve")
        self.duracion_transicion = tk.DoubleVar(value=1.0)
        self.aplicar_fade_in = tk.BooleanVar(value=True)
        self.duracion_fade_in = tk.DoubleVar(value=2.0)
        self.aplicar_fade_out = tk.BooleanVar(value=True)
        self.duracion_fade_out = tk.DoubleVar(value=2.0)
        self.aplicar_overlay = tk.BooleanVar(value=False)  # Activar overlays por defecto
        self.opacidad_overlay = tk.DoubleVar(value=0.25)
        
        # Variables para audio
        self.aplicar_musica = tk.BooleanVar(value=True)
        self.archivo_musica = tk.StringVar()
        self.volumen_musica = tk.DoubleVar(value=0.65)
        self.aplicar_fade_in_musica = tk.BooleanVar(value=True)
        self.duracion_fade_in_musica = tk.DoubleVar(value=1.0)
        self.aplicar_fade_out_musica = tk.BooleanVar(value=True)
        self.duracion_fade_out_musica = tk.DoubleVar(value=2.0)
        
        self.aplicar_voz = tk.BooleanVar(value=True)
        self.archivo_voz = tk.StringVar()
        self.volumen_voz = tk.DoubleVar(value=0.75)
        self.aplicar_fade_in_voz = tk.BooleanVar(value=False)
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
        
        # Cargar plantillas
        self.cargar_plantillas()
        
        # Cargar plantillas
        #self.cargar_plantillas()
        
        # Cargar automáticamente las imágenes y overlays al iniciar
        #self.root.after(1000, self.buscar_imagenes)
        #self.root.after(1500, lambda: self.tab_efectos.buscar_y_seleccionar_overlays() if hasattr(self, 'tab_efectos') else None)
        
        # Iniciar el worker para procesar la cola de TTS
        self.batch_tts_manager.start_worker()
        
    def cargar_plantillas(self):
        """Carga las plantillas desde settings.json."""
        try:
            import json
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                
            if 'templates' in settings:
                self.templates = {}
                for key, value in settings['templates'].items():
                    if key == 'basic':
                        self.templates[key] = "Básico"
                    elif key == 'professional':
                        self.templates[key] = "Profesional"
                    elif key == 'minimal':
                        self.templates[key] = "Mínimo"
                    else:
                        self.templates[key] = key.capitalize()
                
        except Exception as e:
            print(f"Error al cargar plantillas: {e}")
            
    def aplicar_plantilla(self, event=None):
        """Aplica la configuración de la plantilla seleccionada."""
        template_name = self.template_seleccionado.get()
        if template_name in self.templates:
            template = self.templates[template_name]
            
            # Aplicar configuración básica
            self.aplicar_efectos.set(template.get('aplicar_efectos', False))
            self.secuencia_efectos.set(template.get('secuencia_efectos', ''))
            self.aplicar_transicion.set(template.get('aplicar_transicion', False))
            self.tipo_transicion.set(template.get('tipo_transicion', 'dissolve'))
            self.duracion_transicion.set(template.get('duracion_transicion', 1.0))
            
            # Aplicar configuración de fade
            self.aplicar_fade_in.set(template.get('aplicar_fade_in', False))
            self.duracion_fade_in.set(template.get('duracion_fade_in', 1.0))
            self.aplicar_fade_out.set(template.get('aplicar_fade_out', False))
            self.duracion_fade_out.set(template.get('duracion_fade_out', 1.0))
            
            # Aplicar configuración de audio
            self.aplicar_musica.set(template.get('aplicar_musica', False))
            self.volumen_musica.set(template.get('volumen_musica', 0.5))
            
            # Aplicar configuración de overlay
            self.aplicar_overlay.set(template.get('aplicar_overlay', False))
            self.opacidad_overlay.set(template.get('opacidad_overlay', 0.25))
    
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
        
        from ui.tab_basico import BasicTabFrame
        from ui.tab_efectos import EffectsTabFrame
        from ui.tab_audio import AudioTabFrame
        from ui.tab_subtitles import SubtitlesTabFrame
        from ui.tab_batch import BatchTabFrame
        from ui.tab_settings import SettingsTabFrame
        
        # Pestaña de cola de proyectos para TTS
        self.tab_batch = BatchTabFrame(notebook, self)
        notebook.add(self.tab_batch, text="Cola de Proyectos")
        
        # Pestaña de gestión de proyectos para TTS
        self.tab_project = ProjectTabFrame(notebook, self)
        notebook.add(self.tab_project, text="Proyecto")
        
        # Pestaña de configuración de subtítulos con Whisper
        self.tab_subtitles = SubtitlesTabFrame(notebook,self)
        notebook.add(self.tab_subtitles, text="Subtítulos")
        
        # Pestaña de efectos visuales (ahora usando la clase refactorizada)
        self.tab_efectos = EffectsTabFrame(notebook, self)
        notebook.add(self.tab_efectos, text="Efectos Visuales")
        
        # Pestaña de configuración básica (ya refactorizada)
        self.tab_basico = BasicTabFrame(notebook, self)
        notebook.add(self.tab_basico, text="Configuración Básica")
           # Pestaña de audio (ya refactorizada)
        self.tab_audio = AudioTabFrame(notebook, self)  # Usar la nueva clase
        notebook.add(self.tab_audio, text="Audio")
        
        # Pestaña de ajustes de efectos
        self.tab_settings = SettingsTabFrame(notebook, self)
        notebook.add(self.tab_settings, text="Ajustes de Efectos")
          
        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=100, mode="indeterminate", style="TProgressbar")
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Etiqueta de estado
        self.lbl_estado = ttk.Label(self.root, text="Listo", style="Header.TLabel")
        self.lbl_estado.pack(anchor="w", padx=10)
             
      
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
    def obtener_overlays_seleccionados(self):
        """Obtiene la lista de overlays seleccionados."""
        # Delegar a la instancia de EffectsTabFrame si existe
        if hasattr(self, 'tab_efectos'):
            return self.tab_efectos.obtener_overlays_seleccionados()
        # Fallback al comportamiento anterior si la instancia no existe
        elif self.overlays_seleccionados and self.aplicar_overlay.get():
            return self.overlays_seleccionados
        else:
            return []
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
        
        # Actualizar el estado con el número de imágenes encontradas
        if self.imagenes:
            self.lbl_estado.config(text=f"Se encontraron {len(self.imagenes)} imágenes")
    
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
                # Parámetros para subtítulos
                subtitulos_margen=self.settings_subtitles_margin.get() if hasattr(self, 'settings_subtitles_margin') else 0.20,
                # Parámetros para fuentes de subtítulos
                font_name=self.settings_subtitles_font_name.get() if hasattr(self, 'settings_subtitles_font_name') else None,
                use_system_font=self.settings_use_system_font.get() if hasattr(self, 'settings_use_system_font') else False,
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

      
    def refresh_projects_list(self):
        """Actualiza la lista de proyectos existentes."""
        # Limpiar la lista actual
        self.listbox_projects.delete(0, tk.END)
        
        # Obtener la lista de carpetas en el directorio de proyectos
        projects_dir = self.batch_tts_manager.project_base_dir
        if not projects_dir.exists():
            messagebox.showinfo("Información", f"El directorio de proyectos no existe: {projects_dir}")
            return
        
        # Listar todas las carpetas (proyectos)
        projects = [d.name for d in projects_dir.iterdir() if d.is_dir()]
        projects.sort()  # Ordenar alfabéticamente
        
        if not projects:
            self.listbox_projects.insert(tk.END, "No hay proyectos guardados")
            return
        
        # Añadir cada proyecto a la lista
        for project in projects:
            self.listbox_projects.insert(tk.END, project)
    
    def load_selected_project(self):
        """Carga el proyecto seleccionado en la interfaz."""
        # Obtener el proyecto seleccionado
        selected_indices = self.listbox_projects.curselection()
        if not selected_indices:
            messagebox.showinfo("Información", "Por favor, selecciona un proyecto para cargar.")
            return
        
        project_name = self.listbox_projects.get(selected_indices[0])
        if project_name == "No hay proyectos guardados":
            return
        
        # Construir la ruta al proyecto
        project_folder = self.batch_tts_manager.project_base_dir / project_name
        settings_file = project_folder / "settings.json"
        script_file = project_folder / "guion.txt"
        
        # Verificar que existan los archivos necesarios
        if not script_file.exists():
            messagebox.showerror("Error", f"No se encontró el archivo de guion en el proyecto: {script_file}")
            return
        
        # Cargar el guion
        try:
            with open(script_file, "r", encoding="utf-8") as f:
                script_content = f.read()
                # Limpiar y establecer el contenido del guion
                self.txt_script.delete("1.0", tk.END)
                self.txt_script.insert("1.0", script_content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el guion: {e}")
            return
        
        # Establecer el título del proyecto
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, project_name)
        
        # Cargar la configuración si existe
        if settings_file.exists():
            try:
                import json
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                # Aplicar la configuración a la interfaz
                self.apply_settings_to_gui(settings)
                messagebox.showinfo("Proyecto Cargado", 
                                  f"El proyecto '{project_name}' ha sido cargado correctamente.\n\n" +
                                  "Puedes modificar los ajustes antes de regenerar el vídeo.")
            except Exception as e:
                messagebox.showwarning("Advertencia", 
                                     f"Se cargó el guion pero hubo un error al cargar la configuración: {e}\n\n" +
                                     "Se usarán los ajustes actuales de la interfaz.")
        else:
            messagebox.showinfo("Proyecto Cargado", 
                              f"El proyecto '{project_name}' ha sido cargado.\n\n" +
                              "No se encontró un archivo de configuración, se usarán los ajustes actuales.")
    
    def apply_settings_to_gui(self, settings):
        """Aplica la configuración cargada a los elementos de la interfaz."""
        # Aplicar configuraciones básicas
        if 'duracion_img' in settings:
            self.duracion_img.set(settings['duracion_img'])
        if 'fps' in settings:
            self.fps.set(settings['fps'])
        
        # Aplicar configuración de efectos
        if 'aplicar_efectos' in settings:
            self.aplicar_efectos.set(settings['aplicar_efectos'])
        
        # Configurar secuencia de efectos si existe
        if 'secuencia_efectos' in settings and settings['secuencia_efectos']:
            # Determinar el modo de efectos basado en la secuencia
            secuencia = settings['secuencia_efectos']
            if len(secuencia) == 1:
                # Un solo tipo de efecto
                self.modo_efecto.set("1")
                self.tipo_efecto.set(secuencia[0])
            elif len(secuencia) == 2 and secuencia[0] == 'in' and secuencia[1] == 'out':
                # Alternar entre zoom in y zoom out
                self.modo_efecto.set("3")
            else:
                # Secuencia personalizada
                self.modo_efecto.set("2")
                # Limpiar checkboxes actuales
                for key in self.efecto_checkboxes:
                    self.efecto_checkboxes[key].set(False)
                # Marcar los efectos de la secuencia
                for efecto in secuencia:
                    if efecto in self.efecto_checkboxes:
                        self.efecto_checkboxes[efecto].set(True)
                # Actualizar la secuencia en la interfaz
                self.secuencia_efectos.set(','.join(secuencia))
                self.actualizar_secuencia_efectos()
        
        # Aplicar configuración de transiciones
        if 'aplicar_transicion' in settings:
            self.aplicar_transicion.set(settings['aplicar_transicion'])
        if 'tipo_transicion' in settings:
            self.tipo_transicion.set(settings['tipo_transicion'])
        if 'duracion_transicion' in settings:
            self.duracion_transicion.set(settings['duracion_transicion'])
        
        # Aplicar configuración de fade in/out
        if 'aplicar_fade_in' in settings:
            self.aplicar_fade_in.set(settings['aplicar_fade_in'])
        if 'duracion_fade_in' in settings:
            self.duracion_fade_in.set(settings['duracion_fade_in'])
        if 'aplicar_fade_out' in settings:
            self.aplicar_fade_out.set(settings['aplicar_fade_out']) 
        if 'duracion_fade_out' in settings:
            self.duracion_fade_out.set(settings['duracion_fade_out'])

        # Aplicar configuración de overlay    
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
                    'subtitulos_margen': self.settings_subtitles_margin.get() if hasattr(self, 'settings_subtitles_margin') else 0.20,
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
            archivo_subtitulos = kwargs.get('archivo_subtitulos', False)
            
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
            
            # Asegurarse de pasar los parámetros de fuente para los subtítulos
            if kwargs.get('aplicar_subtitulos', False):
                print("Configurando fuentes para subtítulos...")
                # Pasar la fuente seleccionada y si es del sistema o personalizada
                if hasattr(self, 'settings_subtitles_font_name') and hasattr(self, 'settings_use_system_font'):
                    kwargs['font_name'] = self.settings_subtitles_font_name.get()
                    kwargs['use_system_font'] = self.settings_use_system_font.get()
                    print(f"Fuente para subtítulos: {kwargs['font_name']}, Sistema: {kwargs['use_system_font']}")
            
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
    
    
    
    

# Iniciar la aplicación si se ejecuta este archivo directamente
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCreatorApp(root)
    root.mainloop()