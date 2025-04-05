# -*- coding: utf-8 -*-
# Archivo: ui/tab_basico.py

import tkinter as tk
from tkinter import ttk, filedialog # Importar filedialog aquí si lo usa algún botón de esta pestaña directamente (aunque parece que no)

class BasicTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Configuración Básica'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña básica.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Crea y posiciona los widgets para esta pestaña."""

        # --- Frame para la selección de directorio de Imágenes ---
        # El 'padre' ahora es 'self' (la instancia de BasicTabFrame)
        frame_dir = ttk.LabelFrame(self, text="Directorio de Imágenes")
        frame_dir.pack(fill="x", padx=10, pady=10, side=tk.TOP) # side=tk.TOP es útil

        # Usamos self.app.* para acceder a variables y métodos de VideoCreatorApp
        entry_dir = ttk.Entry(frame_dir, textvariable=self.app.directorio_imagenes, width=50)
        entry_dir.pack(side="left", padx=5, pady=10, fill="x", expand=True)

        btn_dir = ttk.Button(frame_dir, text="Examinar", command=self.app.seleccionar_directorio, style="Secondary.TButton")
        btn_dir.pack(side="right", padx=5, pady=10)

        # --- Frame para el archivo de salida ---
        frame_salida = ttk.LabelFrame(self, text="Archivo de Salida") # Padre: self
        frame_salida.pack(fill="x", padx=10, pady=10, side=tk.TOP)

        entry_salida = ttk.Entry(frame_salida, textvariable=self.app.archivo_salida, width=50) # self.app.*
        entry_salida.pack(side="left", padx=5, pady=10, fill="x", expand=True)

        btn_salida = ttk.Button(frame_salida, text="Examinar", command=self.app.seleccionar_archivo_salida, style="Secondary.TButton") # self.app.*
        btn_salida.pack(side="right", padx=5, pady=10)

        # --- Frame para la duración y FPS ---
        frame_duracion = ttk.LabelFrame(self, text="Configuración de Tiempo") # Padre: self
        frame_duracion.pack(fill="x", padx=10, pady=10, side=tk.TOP)

        # Usar grid dentro de este frame
        lbl_duracion = ttk.Label(frame_duracion, text="Duración imagen (s):") # Texto más corto
        lbl_duracion.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        spin_duracion = ttk.Spinbox(frame_duracion, from_=1, to=30, increment=0.5, textvariable=self.app.duracion_img, width=5) # self.app.*
        spin_duracion.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        lbl_fps = ttk.Label(frame_duracion, text="FPS:")
        lbl_fps.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        spin_fps = ttk.Spinbox(frame_duracion, from_=15, to=60, increment=1, textvariable=self.app.fps, width=5) # self.app.*
        spin_fps.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # --- Frame para Lista de imágenes encontradas ---
        # Este frame debe expandirse para llenar el espacio restante
        frame_imagenes = ttk.LabelFrame(self, text="Imágenes Encontradas") # Padre: self
        frame_imagenes.pack(fill="both", expand=True, padx=10, pady=10, side=tk.TOP)

        # Crear el Treeview aquí dentro
        # Guardamos la referencia en la instancia principal 'app' para que otros métodos puedan usarlo
        self.app.tree_imagenes = ttk.Treeview(frame_imagenes, columns=("nombre", "ruta"), show="headings", height=6) # Ajusta height si quieres
        self.app.tree_imagenes.heading("nombre", text="Nombre")
        self.app.tree_imagenes.heading("ruta", text="Ruta")
        self.app.tree_imagenes.column("nombre", width=150, stretch=tk.NO)
        self.app.tree_imagenes.column("ruta", width=350, stretch=tk.YES) # Permitir que la ruta se expanda

        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(frame_imagenes, orient="vertical", command=self.app.tree_imagenes.yview)
        self.app.tree_imagenes.configure(yscrollcommand=scrollbar.set)

        # Empaquetar Treeview y Scrollbar DENTRO de frame_imagenes
        scrollbar.pack(side="right", fill="y") # Scrollbar a la derecha
        self.app.tree_imagenes.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5) # Treeview a la izquierda


        # --- Frame para el Botón Buscar Imágenes ---
        # Lo ponemos al final, fuera del frame del Treeview
        frame_boton_buscar = ttk.Frame(self) # Padre: self
        frame_boton_buscar.pack(fill="x", padx=10, pady=(0, 10), side=tk.TOP) # Debajo del treeview

        btn_buscar = ttk.Button(frame_boton_buscar, text="Buscar Imágenes en Directorio", command=self.app.buscar_imagenes, style="Action.TButton") # self.app.*
        btn_buscar.pack(pady=5)