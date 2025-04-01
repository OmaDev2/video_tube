#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from PIL import Image, ImageTk
from glob import glob
import time

# Importar tqdm para la barra de progreso
from tqdm.tk import tqdm as tqdm_tk

# Importar los módulos personalizados
from efectos import ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, PanRightEffect, KenBurnsEffect
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect
from app import crear_video_desde_imagenes

class VideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Creator")
        self.root.geometry("900x950")
        
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
        self.directorio_imagenes = tk.StringVar()
        self.archivo_salida = tk.StringVar(value="video_salida.mp4")
        self.duracion_img = tk.DoubleVar(value=10.0)
        self.fps = tk.IntVar(value=24)
        self.aplicar_efectos = tk.BooleanVar(value=True)
        self.tipo_efecto = tk.StringVar(value="in")
        self.modo_efecto = tk.StringVar(value="2")
        self.secuencia_efectos = tk.StringVar()
        self.aplicar_transicion = tk.BooleanVar(value=True)
        self.tipo_transicion = tk.StringVar(value="dissolve")
        self.duracion_transicion = tk.DoubleVar(value=2.0)
        self.aplicar_fade_in = tk.BooleanVar(value=True)
        self.duracion_fade_in = tk.DoubleVar(value=1.0)
        self.aplicar_fade_out = tk.BooleanVar(value=True)
        self.duracion_fade_out = tk.DoubleVar(value=1.0)
        self.aplicar_overlay = tk.BooleanVar(value=True)
        self.opacidad_overlay = tk.DoubleVar(value=0.5)
        
        # Variables para audio
        self.aplicar_musica = tk.BooleanVar(value=True)
        self.archivo_musica = tk.StringVar()
        self.volumen_musica = tk.DoubleVar(value=1.0)
        self.aplicar_fade_in_musica = tk.BooleanVar(value=True)
        self.duracion_fade_in_musica = tk.DoubleVar(value=2.0)
        self.aplicar_fade_out_musica = tk.BooleanVar(value=True)
        self.duracion_fade_out_musica = tk.DoubleVar(value=2.0)
        
        self.aplicar_voz = tk.BooleanVar(value=False)
        self.archivo_voz = tk.StringVar()
        self.volumen_voz = tk.DoubleVar(value=1.0)
        self.aplicar_fade_in_voz = tk.BooleanVar(value=False)
        self.duracion_fade_in_voz = tk.DoubleVar(value=1.0)
        self.aplicar_fade_out_voz = tk.BooleanVar(value=False)
        self.duracion_fade_out_voz = tk.DoubleVar(value=1.0)
        
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
        self.settings_overlay_opacity = tk.DoubleVar(value=0.8)
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
    
    def crear_interfaz(self):
        # Crear un notebook (pestañas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de configuración básica
        tab_basico = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_basico, text="Configuración Básica")
        
        # Pestaña de efectos
        tab_efectos = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_efectos, text="Efectos Visuales")
        
        # Pestaña de transiciones
        tab_transiciones = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_transiciones, text="Transiciones")
        
        # Pestaña de fade in/out
        tab_fade = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_fade, text="Fade In/Out")
        
        # Pestaña de overlays
        tab_overlay = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_overlay, text="Overlays")
        
        # Pestaña de audio
        tab_audio = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_audio, text="Audio")
        
        # Pestaña de vista previa
        tab_preview = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_preview, text="Vista Previa")
        
        # Pestaña de ajustes de efectos
        tab_settings = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(tab_settings, text="Ajustes de Efectos")
        
        # Configurar cada pestaña
        self.configurar_tab_basico(tab_basico)
        self.configurar_tab_efectos(tab_efectos)
        self.configurar_tab_transiciones(tab_transiciones)
        self.configurar_tab_fade(tab_fade)
        self.configurar_tab_overlay(tab_overlay)
        self.configurar_tab_audio(tab_audio)
        self.configurar_tab_preview(tab_preview)
        self.configurar_tab_settings(tab_settings)
        
        # Botón para crear el video (en la parte inferior)
        frame_botones = ttk.Frame(self.root)
        frame_botones.pack(fill="x", padx=10, pady=10)
        
        btn_crear = ttk.Button(frame_botones, text="Crear Video", command=self.crear_video, style="Primary.TButton")
        btn_crear.pack(side="right", padx=5)
        
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
    # Checkbox para activar efectos
        chk_efectos = ttk.Checkbutton(tab, text="Aplicar efectos de movimiento", variable=self.aplicar_efectos)
        chk_efectos.pack(anchor="w", padx=10, pady=10)
        
        # Frame para las opciones de efectos
        frame_opciones = ttk.LabelFrame(tab, text="Opciones de Efectos")
        frame_opciones.pack(fill="x", padx=10, pady=10)
        
        # Opciones de modo de efecto
        lbl_modo = ttk.Label(frame_opciones, text="Modo de efecto:")
        lbl_modo.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Radiobuttons para el modo
        rb_modo1 = ttk.Radiobutton(frame_opciones, text="Un solo tipo de efecto", variable=self.modo_efecto, value="1")
        rb_modo1.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        rb_modo2 = ttk.Radiobutton(frame_opciones, text="Secuencia personalizada", variable=self.modo_efecto, value="2")
        rb_modo2.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        rb_modo3 = ttk.Radiobutton(frame_opciones, text="Alternar automáticamente (in/out)", variable=self.modo_efecto, value="3")
        rb_modo3.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        rb_modo4 = ttk.Radiobutton(frame_opciones, text="Secuencia Ken Burns", variable=self.modo_efecto, value="4")
        rb_modo4.grid(row=3, column=1, padx=5, pady=5, sticky="w")
       
        
        # Frame para un solo tipo de efecto
        frame_tipo = ttk.LabelFrame(tab, text="Un Solo Tipo de Efecto")
        frame_tipo.pack(fill="x", padx=10, pady=10)
        
        # Radiobuttons para el tipo de efecto
        tipos_efectos = [
            ("Zoom In (acercamiento)", "in"),
            ("Zoom Out (alejamiento)", "out"),
            ("Pan Up (movimiento hacia arriba)", "panup"),
            ("Pan Down (movimiento hacia abajo)", "pandown"),
            ("Pan Left (movimiento hacia la izquierda)", "panleft"),
            ("Pan Right (movimiento hacia la derecha)", "panright"),
            ("Ken Burns (efecto cinematográfico)", "kenburns"),
            ("Viñeta Zoom In (acercamiento con viñeta)", "vignette_zoom_in"),
            ("Viñeta Zoom Out (alejamiento con viñeta)", "vignette_zoom_out"),
            ("Rotación Horaria", "rotate_clockwise"),
            ("Rotación Antihoraria", "rotate_counter_clockwise")
        ]
        row_num = 0
        for texto, valor in tipos_efectos:
            rb = ttk.Radiobutton(frame_tipo, text=texto, variable=self.tipo_efecto, value=valor)
            rb.grid(row=row_num, column=0, padx=5, pady=3, sticky="w")
            row_num += 1
        # Dentro del frame_tipo en configurar_tab_efectos
        rb_flip_h = ttk.Radiobutton(frame_tipo, text="Voltear Horizontalmente", variable=self.tipo_efecto, value="flip_horizontal")
        rb_flip_h.grid(row=row_num, column=0, padx=5, pady=3, sticky="w") # Ajusta el número de fila

        rb_flip_v = ttk.Radiobutton(frame_tipo, text="Voltear Verticalmente", variable=self.tipo_efecto, value="flip_vertical")
        rb_flip_v.grid(row=row_num, column=0, padx=5, pady=3, sticky="w") # Ajusta el número de fila
        
        # Frame para secuencia personalizada
        frame_secuencia = ttk.LabelFrame(tab, text="Secuencia Personalizada")
        frame_secuencia.pack(fill="x", padx=10, pady=10)
        
        lbl_secuencia = ttk.Label(frame_secuencia, text="Selecciona los efectos para la secuencia:")
        lbl_secuencia.pack(anchor="w", padx=5, pady=5)
        
        # Frame para contener los checkboxes en dos columnas
        frame_checkboxes = ttk.Frame(frame_secuencia)
        frame_checkboxes.pack(fill="x", padx=5, pady=5)
        
        # Variables para los checkboxes
        self.efecto_checkboxes = {
            'in': tk.BooleanVar(),
            'out': tk.BooleanVar(),
            'panup': tk.BooleanVar(),
            'pandown': tk.BooleanVar(),
            'panleft': tk.BooleanVar(),
            'panright': tk.BooleanVar(),
            'kenburns': tk.BooleanVar(),
            'kenburns1': tk.BooleanVar(),
            'kenburns2': tk.BooleanVar(),
            'kenburns3': tk.BooleanVar(),
            'flip_horizontal': tk.BooleanVar(),
            'flip_vertical': tk.BooleanVar(),
            'vignette_zoom_in': tk.BooleanVar(),
            'vignette_zoom_out': tk.BooleanVar(),
            'rotate_clockwise': tk.BooleanVar(),
            'rotate_counter_clockwise': tk.BooleanVar()
        }
        
        # Textos descriptivos para los efectos
        efectos_texto = {
            'in': 'Zoom In (acercamiento)',
            'out': 'Zoom Out (alejamiento)',
            'panup': 'Pan Up (hacia arriba)',
            'pandown': 'Pan Down (hacia abajo)',
            'panleft': 'Pan Left (hacia la izquierda)',
            'panright': 'Pan Right (hacia la derecha)',
            'kenburns': 'Ken Burns (clásico)',
            'kenburns1': 'Ken Burns 1',
            'kenburns2': 'Ken Burns 2',
            'kenburns3': 'Ken Burns 3',
            'flip_horizontal': 'Voltear Horizontal',
            'flip_vertical': 'Voltear Vertical',
            'vignette_zoom_in': 'Viñeta Zoom In',
            'vignette_zoom_out': 'Viñeta Zoom Out',
            'rotate_clockwise': 'Rotación Horaria',
            'rotate_counter_clockwise': 'Rotación Antihoraria'
        }
        
        # Crear checkboxes en dos columnas
        efectos_lista = list(self.efecto_checkboxes.keys())
        efectos_lista.sort()
        mitad = len(efectos_lista) // 2
        
        for i, efecto in enumerate(efectos_lista):
            col = 0 if i < mitad else 1
            row = i if i < mitad else i - mitad
            
            chk = ttk.Checkbutton(frame_checkboxes, 
                                 text=efectos_texto[efecto],
                                 variable=self.efecto_checkboxes[efecto],
                                 command=self.actualizar_secuencia_efectos)
            chk.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        
        # Etiqueta para mostrar la secuencia actual
        lbl_secuencia_actual = ttk.Label(frame_secuencia, text="Secuencia actual:")
        lbl_secuencia_actual.pack(anchor="w", padx=5, pady=(10,0))
        
        self.lbl_secuencia_preview = ttk.Label(frame_secuencia, text="", wraplength=400)
        self.lbl_secuencia_preview.pack(anchor="w", padx=5, pady=(0,5))
        
        # Botones para manipular el orden
        frame_botones = ttk.Frame(frame_secuencia)
        frame_botones.pack(fill="x", padx=5, pady=5)
        
        btn_mover_arriba = ttk.Button(frame_botones, text="↑ Mover Arriba", 
                                    command=lambda: self.mover_efecto(-1))
        btn_mover_arriba.pack(side="left", padx=5)
        
        btn_mover_abajo = ttk.Button(frame_botones, text="↓ Mover Abajo", 
                                   command=lambda: self.mover_efecto(1))
        btn_mover_abajo.pack(side="left", padx=5)
    
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
        
        scale_volumen_musica = ttk.Scale(frame_musica, from_=0.0, to=1.0, orient="horizontal", 
                                       variable=self.volumen_musica, length=200)
        scale_volumen_musica.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
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
                                    variable=self.volumen_voz, length=200)
        scale_volumen_voz.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
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
        if not self.imagenes:
            messagebox.showerror("Error", "Por favor, selecciona al menos una imagen")
            return

        # Recoger los ajustes actuales
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
            'transition_duration': self.settings_transition_duration.get(),
            'transition_type': self.settings_transition_type.get(),
            'overlay_opacity': self.settings_overlay_opacity.get(),
            'overlay_blend_mode': self.settings_overlay_blend_mode.get()
        }

        # Obtener la secuencia de efectos
        secuencia_efectos = self.obtener_secuencia_efectos()

        # Crear el hilo para procesar el video
        thread = threading.Thread(
            target=self.procesar_video,
            args=(
                self.imagenes,
                self.duracion_img.get(),
                self.aplicar_efectos.get(),
                secuencia_efectos,
                self.aplicar_transicion.get(),
                self.archivo_musica.get() if self.aplicar_musica.get() else None,
                self.overlays_seleccionados if hasattr(self, 'overlays_seleccionados') and self.aplicar_overlay.get() else None,
                current_settings
            )
        )
        thread.daemon = True
        thread.start()
    
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
    
    def procesar_video(self, imagenes, duracion_img, aplicar_efectos, efectos, aplicar_transicion, 
                      audio_file=None, overlays=None, settings=None):
        try:
            # Actualizar el estado
            self.root.after(0, lambda: self.lbl_estado.config(
                text="Creando video... Por favor, espere."
            ))

            # Configurar parámetros para la función crear_video_desde_imagenes
            directorio_imagenes = os.path.dirname(imagenes[0]) if imagenes else ""
            archivo_salida = "video_salida.mp4"
            tipo_transicion = settings.get('transition_type', 'dissolve') if settings else 'dissolve'
            
            # Asegurarse de que el tipo de transición sea uno de los disponibles
            if tipo_transicion not in ["none", "dissolve"]:
                print(f"Tipo de transición '{tipo_transicion}' no reconocido. Usando 'dissolve' por defecto.")
                tipo_transicion = "dissolve"
                
            duracion_transicion = settings.get('transition_duration', 1.0) if settings else 1.0
            opacidad_overlay = settings.get('overlay_opacity', 0.8) if settings else 0.8

            # Crear el video
            crear_video_desde_imagenes(
                directorio_imagenes=directorio_imagenes,
                archivo_salida=archivo_salida,
                duracion_img=duracion_img,
                fps=24,
                aplicar_efectos=aplicar_efectos,
                secuencia_efectos=efectos,
                aplicar_transicion=aplicar_transicion,
                tipo_transicion=tipo_transicion,
                duracion_transicion=duracion_transicion,
                aplicar_overlay=bool(overlays),
                archivos_overlay=overlays,
                opacidad_overlay=opacidad_overlay,
                aplicar_musica=bool(audio_file),
                archivo_musica=audio_file,
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
                settings=settings,
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

# Iniciar la aplicación si se ejecuta este archivo directamente
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCreatorApp(root)
    root.mainloop()