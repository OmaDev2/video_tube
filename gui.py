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
from efectos import ZoomEffect
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect
from app import crear_video_desde_imagenes

class VideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Creador de Videos con Efectos")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Variables para almacenar la configuración
        self.directorio_imagenes = tk.StringVar()
        self.archivo_salida = tk.StringVar(value="video_salida.mp4")
        self.duracion_img = tk.DoubleVar(value=6.0)
        self.fps = tk.IntVar(value=24)
        self.aplicar_efectos = tk.BooleanVar(value=True)
        self.tipo_efecto = tk.StringVar(value="in")
        self.modo_efecto = tk.StringVar(value="1")
        self.secuencia_efectos = tk.StringVar()
        self.aplicar_transicion = tk.BooleanVar(value=True)
        self.tipo_transicion = tk.StringVar(value="none")
        self.duracion_transicion = tk.DoubleVar(value=2.0)
        self.aplicar_fade_in = tk.BooleanVar(value=True)
        self.duracion_fade_in = tk.DoubleVar(value=1.0)
        self.aplicar_fade_out = tk.BooleanVar(value=True)
        self.duracion_fade_out = tk.DoubleVar(value=1.0)
        self.aplicar_overlay = tk.BooleanVar(value=True)
        self.opacidad_overlay = tk.DoubleVar(value=0.5)
        
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
        tab_basico = ttk.Frame(notebook)
        notebook.add(tab_basico, text="Configuración Básica")
        
        # Pestaña de efectos
        tab_efectos = ttk.Frame(notebook)
        notebook.add(tab_efectos, text="Efectos de Zoom")
        
        # Pestaña de transiciones
        tab_transiciones = ttk.Frame(notebook)
        notebook.add(tab_transiciones, text="Transiciones")
        
        # Pestaña de fade in/out
        tab_fade = ttk.Frame(notebook)
        notebook.add(tab_fade, text="Fade In/Out")
        
        # Pestaña de overlays
        tab_overlay = ttk.Frame(notebook)
        notebook.add(tab_overlay, text="Overlays")
        
        # Pestaña de vista previa
        tab_preview = ttk.Frame(notebook)
        notebook.add(tab_preview, text="Vista Previa")
        
        # Configurar cada pestaña
        self.configurar_tab_basico(tab_basico)
        self.configurar_tab_efectos(tab_efectos)
        self.configurar_tab_transiciones(tab_transiciones)
        self.configurar_tab_fade(tab_fade)
        self.configurar_tab_overlay(tab_overlay)
        self.configurar_tab_preview(tab_preview)
        
        # Botón para crear el video (en la parte inferior)
        frame_botones = ttk.Frame(self.root)
        frame_botones.pack(fill="x", padx=10, pady=10)
        
        btn_crear = ttk.Button(frame_botones, text="Crear Video", command=self.crear_video)
        btn_crear.pack(side="right", padx=5)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=100, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Etiqueta de estado
        self.lbl_estado = ttk.Label(self.root, text="Listo")
        self.lbl_estado.pack(anchor="w", padx=10)
    
    def configurar_tab_basico(self, tab):
        # Frame para la selección de directorio
        frame_dir = ttk.LabelFrame(tab, text="Directorio de Imágenes")
        frame_dir.pack(fill="x", padx=10, pady=10)
        
        entry_dir = ttk.Entry(frame_dir, textvariable=self.directorio_imagenes, width=50)
        entry_dir.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        btn_dir = ttk.Button(frame_dir, text="Examinar", command=self.seleccionar_directorio)
        btn_dir.pack(side="right", padx=5, pady=10)
        
        # Frame para el archivo de salida
        frame_salida = ttk.LabelFrame(tab, text="Archivo de Salida")
        frame_salida.pack(fill="x", padx=10, pady=10)
        
        entry_salida = ttk.Entry(frame_salida, textvariable=self.archivo_salida, width=50)
        entry_salida.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        btn_salida = ttk.Button(frame_salida, text="Examinar", command=self.seleccionar_archivo_salida)
        btn_salida.pack(side="right", padx=5, pady=10)
        
        # Frame para la duración y FPS
        frame_duracion = ttk.LabelFrame(tab, text="Configuración de Tiempo")
        frame_duracion.pack(fill="x", padx=10, pady=10)
        
        # Duración de cada imagen
        lbl_duracion = ttk.Label(frame_duracion, text="Duración de cada imagen (segundos):")
        lbl_duracion.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_duracion = ttk.Spinbox(frame_duracion, from_=1, to=20, increment=0.5, textvariable=self.duracion_img, width=5)
        spin_duracion.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # FPS
        lbl_fps = ttk.Label(frame_duracion, text="Frames por segundo (FPS):")
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
        btn_buscar = ttk.Button(frame_imagenes, text="Buscar Imágenes", command=self.buscar_imagenes)
        btn_buscar.pack(pady=5)
    
    def configurar_tab_efectos(self, tab):
        # Checkbox para activar efectos
        chk_efectos = ttk.Checkbutton(tab, text="Aplicar efectos de zoom", variable=self.aplicar_efectos)
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
        
        # Frame para un solo tipo de efecto
        frame_tipo = ttk.LabelFrame(tab, text="Un Solo Tipo de Efecto")
        frame_tipo.pack(fill="x", padx=10, pady=10)
        
        # Radiobuttons para el tipo de zoom
        rb_in = ttk.Radiobutton(frame_tipo, text="Zoom In (acercamiento)", variable=self.tipo_efecto, value="in")
        rb_in.pack(anchor="w", padx=5, pady=5)
        
        rb_out = ttk.Radiobutton(frame_tipo, text="Zoom Out (alejamiento)", variable=self.tipo_efecto, value="out")
        rb_out.pack(anchor="w", padx=5, pady=5)
        
        # Frame para secuencia personalizada
        frame_secuencia = ttk.LabelFrame(tab, text="Secuencia Personalizada")
        frame_secuencia.pack(fill="x", padx=10, pady=10)
        
        lbl_secuencia = ttk.Label(frame_secuencia, text="Secuencia de efectos (in,out,in,...):")
        lbl_secuencia.pack(anchor="w", padx=5, pady=5)
        
        entry_secuencia = ttk.Entry(frame_secuencia, textvariable=self.secuencia_efectos, width=50)
        entry_secuencia.pack(fill="x", padx=5, pady=5)
        
        lbl_ejemplo = ttk.Label(frame_secuencia, text="Ejemplo: in,out,in (separados por comas)")
        lbl_ejemplo.pack(anchor="w", padx=5, pady=5)
    
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
        combo_transicion.current(0)  # Seleccionar el primer elemento por defecto
        
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
        # Checkbox para activar overlay
        chk_overlay = ttk.Checkbutton(tab, text="Aplicar efectos de overlay", variable=self.aplicar_overlay)
        chk_overlay.pack(anchor="w", padx=10, pady=10)
        
        # Frame para las opciones de overlay
        frame_overlay = ttk.LabelFrame(tab, text="Opciones de Overlay")
        frame_overlay.pack(fill="x", padx=10, pady=10)
        
        # Opacidad del overlay
        lbl_opacidad = ttk.Label(frame_overlay, text="Opacidad del overlay (0.1-1.0):")
        lbl_opacidad.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_opacidad = ttk.Spinbox(frame_overlay, from_=0.1, to=1.0, increment=0.1, textvariable=self.opacidad_overlay, width=5)
        spin_opacidad.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Lista de overlays disponibles
        frame_lista = ttk.LabelFrame(tab, text="Overlays Disponibles")
        frame_lista.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear un Listbox para mostrar los overlays disponibles
        self.listbox_overlays = tk.Listbox(frame_lista, selectmode=tk.MULTIPLE, height=10)
        self.listbox_overlays.pack(fill="both", expand=True, padx=5, pady=5, side="left")
        
        # Scrollbar para el Listbox
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.listbox_overlays.yview)
        self.listbox_overlays.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Frame para los botones
        frame_botones = ttk.Frame(tab)
        frame_botones.pack(fill="x", padx=10, pady=10)
        
        # Botón para buscar overlays
        btn_buscar = ttk.Button(frame_botones, text="Buscar Overlays", command=self.buscar_overlays)
        btn_buscar.pack(side="left", padx=5)
        
        # Botón para seleccionar overlays
        btn_seleccionar = ttk.Button(frame_botones, text="Seleccionar Overlays", command=self.seleccionar_overlays)
        btn_seleccionar.pack(side="left", padx=5)
    
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
    
    def seleccionar_overlays(self):
        # Obtener los índices seleccionados
        indices = self.listbox_overlays.curselection()
        
        if not indices:
            messagebox.showinfo("Información", "No has seleccionado ningún overlay")
            return
        
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
        
        # Actualizar el estado
        self.lbl_estado.config(text=f"Se han seleccionado {len(self.overlays_seleccionados)} overlays")
    
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
        # Verificar que se hayan seleccionado imágenes
        if not self.imagenes:
            messagebox.showerror("Error", "No se han encontrado imágenes")
            return
        
        # Verificar que se haya especificado un archivo de salida
        archivo_salida = self.archivo_salida.get()
        if not archivo_salida:
            messagebox.showerror("Error", "Debes especificar un archivo de salida")
            return
        
        # Obtener la configuración
        directorio = self.directorio_imagenes.get()
        duracion = self.duracion_img.get()
        fps = self.fps.get()
        
        # Configuración de efectos
        aplicar_efectos = self.aplicar_efectos.get()
        secuencia_efectos = None
        
        if aplicar_efectos:
            modo = self.modo_efecto.get()
            
            if modo == "1":  # Un solo tipo de efecto
                tipo_efecto = self.tipo_efecto.get()
                secuencia_efectos = [tipo_efecto]
            elif modo == "2":  # Secuencia personalizada
                secuencia = self.secuencia_efectos.get()
                if secuencia:
                    secuencia_efectos = [efecto.strip() for efecto in secuencia.split(',')]
                    # Validar cada efecto en la secuencia
                    secuencia_efectos = [efecto if efecto in ['in', 'out'] else 'in' for efecto in secuencia_efectos]
                else:
                    secuencia_efectos = ['in']  # Valor por defecto
            elif modo == "3":  # Alternar automáticamente
                secuencia_efectos = ['in', 'out']
        
        # Configuración de transiciones
        aplicar_transicion = self.aplicar_transicion.get()
        tipo_transicion = self.tipo_transicion.get() if aplicar_transicion else 'none'
        duracion_transicion = self.duracion_transicion.get()
        
        # Configuración de fade in/out
        aplicar_fade_in = self.aplicar_fade_in.get()
        duracion_fade_in = self.duracion_fade_in.get()
        aplicar_fade_out = self.aplicar_fade_out.get()
        duracion_fade_out = self.duracion_fade_out.get()
        
        # Configuración de overlay
        aplicar_overlay = self.aplicar_overlay.get()
        
        # Verificar si hay overlays seleccionados
        if aplicar_overlay and not self.overlays_seleccionados:
            # Si no hay overlays seleccionados pero se quiere aplicar overlay, buscar overlays disponibles
            overlay_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlays')
            overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
            
            if overlays_disponibles:
                # Usar el primer overlay disponible si no hay ninguno seleccionado
                self.overlays_seleccionados = [os.path.join(overlay_dir, overlays_disponibles[0])]
                print(f"Usando overlay por defecto: {overlays_disponibles[0]}")
            else:
                messagebox.showwarning("Advertencia", "Has seleccionado aplicar overlay pero no hay archivos de overlay disponibles.\nSe creará el video sin overlay.")
                aplicar_overlay = False
        
        archivos_overlay = self.overlays_seleccionados if aplicar_overlay else None
        opacidad_overlay = self.opacidad_overlay.get()
        
        # Mostrar información sobre los overlays
        if aplicar_overlay and archivos_overlay:
            overlay_names = [os.path.basename(path) for path in archivos_overlay]
            print(f"Overlays seleccionados: {overlay_names}")
        
        # Actualizar el estado
        self.lbl_estado.config(text="Creando video...")
        self.progress.start()
        
        # Crear el video en un hilo separado para no bloquear la interfaz
        thread = threading.Thread(
            target=self.procesar_video,
            args=(directorio, archivo_salida, duracion, fps, 
                  aplicar_efectos, secuencia_efectos,
                  aplicar_transicion, tipo_transicion, duracion_transicion,
                  aplicar_fade_in, duracion_fade_in, 
                  aplicar_fade_out, duracion_fade_out,
                  aplicar_overlay, archivos_overlay, opacidad_overlay)
        )
        thread.daemon = True
        thread.start()
    
    def procesar_video(self, directorio, archivo_salida, duracion, fps, 
                      aplicar_efectos, secuencia_efectos,
                      aplicar_transicion, tipo_transicion, duracion_transicion,
                      aplicar_fade_in, duracion_fade_in, 
                      aplicar_fade_out, duracion_fade_out,
                      aplicar_overlay, archivos_overlay, opacidad_overlay):
        try:
            # Obtener la cantidad de imágenes para la barra de progreso
            formatos = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
            archivos = []
            for formato in formatos:
                archivos.extend(glob(os.path.join(directorio, formato)))
            
            total_imagenes = len(archivos)
            
            if total_imagenes == 0:
                self.root.after(0, self.finalizar_proceso, False, "No se encontraron imágenes en el directorio seleccionado")
                return
            
            # Variable para controlar si el proceso fue cancelado
            self.proceso_cancelado = False
            
            # Crear una ventana de progreso con tqdm_tk
            self.pbar = tqdm_tk(total=total_imagenes, desc="Creando video", 
                          tk_parent=self.root, grab=False,
                          cancel_callback=self.cancelar_proceso)
            
            # Definir una función de callback para actualizar la barra de progreso
            def update_progress(n, total):
                if not self.proceso_cancelado:
                    self.pbar.update(n)
                    self.pbar.refresh()
                    # Actualizar la etiqueta de estado con el progreso actual
                    progreso = min(100, int((self.pbar.n / self.pbar.total) * 100))
                    self.root.after(0, lambda: self.lbl_estado.config(text=f"Procesando... {progreso}% completado"))
            
            # Llamar a la función de creación de video con la barra de progreso
            crear_video_desde_imagenes(
                directorio, archivo_salida, duracion, fps, 
                aplicar_efectos, secuencia_efectos,
                aplicar_transicion, tipo_transicion, duracion_transicion,
                aplicar_fade_in, duracion_fade_in, 
                aplicar_fade_out, duracion_fade_out,
                aplicar_overlay, archivos_overlay, opacidad_overlay,
                progress_callback=update_progress
            )
            
            # Cerrar la barra de progreso si no fue cancelado
            if not self.proceso_cancelado:
                self.pbar.close()
                # Actualizar la interfaz cuando termine
                self.root.after(0, self.finalizar_proceso, True, f"Video creado exitosamente: {archivo_salida}")
        except Exception as e:
            # Manejar errores
            if hasattr(self, 'pbar'):
                self.pbar.close()
            self.root.after(0, self.finalizar_proceso, False, f"Error al crear el video: {str(e)}")
    
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