# -*- coding: utf-8 -*-
# Archivo: ui/tab_efectos.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path
from overlay_effects import OverlayEffect

class EffectsTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Efectos Visuales'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de efectos.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña de efectos visuales, transiciones y fade in/out."""
        # Crear un notebook interno para organizar las secciones
        self.notebook_efectos = ttk.Notebook(self)
        self.notebook_efectos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear las subpestañas
        tab_movimiento = ttk.Frame(self.notebook_efectos, style="Card.TFrame")
        tab_transiciones = ttk.Frame(self.notebook_efectos, style="Card.TFrame")
        tab_fade = ttk.Frame(self.notebook_efectos, style="Card.TFrame")
        tab_overlay = ttk.Frame(self.notebook_efectos, style="Card.TFrame")
        
        # Añadir las subpestañas al notebook
        self.notebook_efectos.add(tab_movimiento, text="Efectos de Movimiento")
        self.notebook_efectos.add(tab_transiciones, text="Transiciones")
        self.notebook_efectos.add(tab_fade, text="Fade In/Out")
        self.notebook_efectos.add(tab_overlay, text="Overlays")
        
        # Configurar cada subpestaña
        self._setup_tab_efectos_movimiento(tab_movimiento)
        self._setup_tab_transiciones(tab_transiciones)
        self._setup_tab_fade(tab_fade)
        self._setup_tab_efectos_overlay(tab_overlay)

    def _setup_tab_efectos_movimiento(self, tab):
        """Configura la interfaz de usuario para la subpestaña de efectos de movimiento."""

        # --- Contenedor Principal ---
        frame_principal = ttk.Frame(tab)
        frame_principal.pack(fill="both", expand=True)
        frame_principal.columnconfigure(0, weight=1)  # Hacer que la columna se expanda

        # --- Checkbox General ---
        chk_efectos = ttk.Checkbutton(frame_principal, text="Aplicar efectos de movimiento",
                                      variable=self.app.aplicar_efectos, command=self._actualizar_estado_controles)
        # Usamos grid para mejor control dentro del frame_principal
        chk_efectos.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="w")

        # --- Frame para Modos ---
        self.frame_opciones = ttk.LabelFrame(frame_principal, text="Modo de Efecto")
        self.frame_opciones.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.frame_opciones.columnconfigure(1, weight=1)  # Columna de radiobuttons se expande un poco

        modos = [
            ("Un solo tipo de efecto", "1"),
            ("Secuencia personalizada", "2"),
            ("Alternar automáticamente (in/out)", "3"),
            ("Secuencia Ken Burns (Preset)", "4")  # Cambiado nombre para claridad
        ]

        for i, (texto, valor) in enumerate(modos):
            rb = ttk.Radiobutton(self.frame_opciones, text=texto, variable=self.app.modo_efecto,
                                 value=valor, command=self._actualizar_visibilidad_paneles)
            # Colocar en una sola columna para claridad
            rb.grid(row=i, column=0, columnspan=2, padx=10, pady=3, sticky="w")

        # --- Frame para "Un Solo Tipo de Efecto" ---
        self.frame_tipo = ttk.LabelFrame(frame_principal, text="Seleccionar Tipo Único")
        # Se añadirá con grid más adelante, inicialmente oculto si no es el modo 1
        self.frame_tipo.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        self.frame_tipo.columnconfigure(0, weight=1)
        self.frame_tipo.columnconfigure(1, weight=1)
        self.frame_tipo.columnconfigure(2, weight=1)  # Tres columnas para radio buttons

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
            rb = ttk.Radiobutton(self.frame_tipo, text=texto, variable=self.app.tipo_efecto, value=valor)
            row_num = i // num_cols_tipo
            col_num = i % num_cols_tipo
            rb.grid(row=row_num, column=col_num, padx=10, pady=3, sticky="w")

        # --- Frame para "Secuencia Personalizada" ---
        self.frame_secuencia = ttk.LabelFrame(frame_principal, text="Configurar Secuencia")
        # Se añadirá con grid más adelante, inicialmente oculto si no es el modo 2
        self.frame_secuencia.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        self.frame_secuencia.columnconfigure(0, weight=1)  # Hacer que la columna 0 se expanda
        
        # Etiqueta para la secuencia
        lbl_secuencia = ttk.Label(self.frame_secuencia, text="Selecciona los efectos para la secuencia:")
        lbl_secuencia.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Frame para contener los checkboxes en columnas
        frame_checkboxes = ttk.Frame(self.frame_secuencia)
        frame_checkboxes.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        # Crear checkboxes en tres columnas para mejor organización
        num_cols = 3
        efectos_lista = self.app._efectos_ordenados_secuencia
        
        for i, efecto in enumerate(efectos_lista):
            col = i % num_cols
            row = i // num_cols
            
            chk = ttk.Checkbutton(frame_checkboxes, 
                                 text=self.app.efectos_texto[efecto],
                                 variable=self.app.efecto_checkboxes[efecto],
                                 command=self._actualizar_secuencia_efectos)
            chk.grid(row=row, column=col, padx=10, pady=2, sticky="w")
        
        # Etiqueta para mostrar la secuencia actual
        lbl_secuencia_actual = ttk.Label(self.frame_secuencia, text="Secuencia actual:")
        lbl_secuencia_actual.grid(row=2, column=0, padx=5, pady=(10,0), sticky="w")
        
        self.app.lbl_secuencia_preview = ttk.Label(self.frame_secuencia, text="", wraplength=400)
        self.app.lbl_secuencia_preview.grid(row=3, column=0, padx=5, pady=(0,5), sticky="w")
        
        # Botones para manipular el orden
        frame_botones = ttk.Frame(self.frame_secuencia)
        frame_botones.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        btn_mover_arriba = ttk.Button(frame_botones, text="↑ Mover Arriba", 
                                    command=lambda: self._mover_efecto(-1))
        btn_mover_arriba.pack(side="left", padx=5)
        
        btn_mover_abajo = ttk.Button(frame_botones, text="↓ Mover Abajo", 
                                   command=lambda: self._mover_efecto(1))
        btn_mover_abajo.pack(side="left", padx=5)
        
        # Inicialmente, mostrar el panel correcto según el modo seleccionado
        self._actualizar_visibilidad_paneles()

    def _actualizar_visibilidad_paneles(self):
        """Actualiza la visibilidad de los paneles según el modo seleccionado."""
        modo = self.app.modo_efecto.get()
        
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
        estado = "normal" if self.app.aplicar_efectos.get() else "disabled"
        
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

    def _actualizar_secuencia_efectos(self):
        """Actualiza la lista de efectos seleccionados para la secuencia."""
        # Obtener los efectos seleccionados en orden
        efectos_seleccionados = []
        for efecto, var in self.app.efecto_checkboxes.items():
            if var.get():
                efectos_seleccionados.append(efecto)
        
        # Actualizar la variable de secuencia
        self.app.secuencia_efectos.set(','.join(efectos_seleccionados))
        
        # Actualizar la etiqueta de vista previa
        if efectos_seleccionados:
            texto_preview = "Secuencia: " + " → ".join(efectos_seleccionados)
        else:
            texto_preview = "No hay efectos seleccionados"
        self.app.lbl_secuencia_preview.config(text=texto_preview)

    def _mover_efecto(self, direccion):
        """Mueve un efecto hacia arriba o hacia abajo en la secuencia.
        
        Args:
            direccion: -1 para mover hacia arriba, 1 para mover hacia abajo
        """
        # Obtener la secuencia actual
        secuencia = self.app.secuencia_efectos.get().split(',') if self.app.secuencia_efectos.get() else []
        if not secuencia:
            return
        
        # Encontrar el último efecto seleccionado
        seleccionados = []
        for efecto, var in self.app.efecto_checkboxes.items():
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
            self.app.secuencia_efectos.set(','.join(secuencia))
            
            # Actualizar la vista previa
            texto_preview = "Secuencia: " + " → ".join(secuencia)
            self.app.lbl_secuencia_preview.config(text=texto_preview)

    def _setup_tab_transiciones(self, tab):
        """Configura la interfaz de usuario para la subpestaña de transiciones."""
        # Checkbox para activar transiciones
        chk_transiciones = ttk.Checkbutton(tab, text="Aplicar transiciones entre imágenes", 
                                          variable=self.app.aplicar_transicion)
        chk_transiciones.pack(anchor="w", padx=10, pady=10)
        
        # Frame para las opciones de transición
        frame_transicion = ttk.LabelFrame(tab, text="Opciones de Transición")
        frame_transicion.pack(fill="x", padx=10, pady=10)
        
        # Tipo de transición
        lbl_tipo = ttk.Label(frame_transicion, text="Tipo de transición:")
        lbl_tipo.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Obtener las transiciones disponibles
        from transiciones import TransitionEffect
        transiciones = TransitionEffect.get_available_transitions()
        
        # Combobox para seleccionar la transición
        combo_transicion = ttk.Combobox(frame_transicion, textvariable=self.app.tipo_transicion, 
                                       values=transiciones, state="readonly")
        combo_transicion.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        combo_transicion.current(1)  # Seleccionar 'dissolve' como elemento por defecto
        
        # Duración de la transición
        lbl_duracion = ttk.Label(frame_transicion, text="Duración de la transición (segundos):")
        lbl_duracion.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        spin_duracion = ttk.Spinbox(frame_transicion, from_=0.5, to=5.0, increment=0.5, 
                                   textvariable=self.app.duracion_transicion, width=5)
        spin_duracion.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def _setup_tab_fade(self, tab):
        """Configura la interfaz de usuario para la subpestaña de fade in/out."""
        # Fade In
        frame_fade_in = ttk.LabelFrame(tab, text="Fade In")
        frame_fade_in.pack(fill="x", padx=10, pady=10)
        
        chk_fade_in = ttk.Checkbutton(frame_fade_in, text="Aplicar fade in al inicio del video", 
                                     variable=self.app.aplicar_fade_in)
        chk_fade_in.pack(anchor="w", padx=5, pady=5)
        
        lbl_duracion_in = ttk.Label(frame_fade_in, text="Duración del fade in (segundos):")
        lbl_duracion_in.pack(anchor="w", padx=5, pady=5)
        
        spin_duracion_in = ttk.Spinbox(frame_fade_in, from_=0.5, to=5.0, increment=0.5, 
                                      textvariable=self.app.duracion_fade_in, width=5)
        spin_duracion_in.pack(anchor="w", padx=5, pady=5)
        
        # Fade Out
        frame_fade_out = ttk.LabelFrame(tab, text="Fade Out")
        frame_fade_out.pack(fill="x", padx=10, pady=10)
        
        chk_fade_out = ttk.Checkbutton(frame_fade_out, text="Aplicar fade out al final del video", 
                                      variable=self.app.aplicar_fade_out)
        chk_fade_out.pack(anchor="w", padx=5, pady=5)
        
        lbl_duracion_out = ttk.Label(frame_fade_out, text="Duración del fade out (segundos):")
        lbl_duracion_out.pack(anchor="w", padx=5, pady=5)
        
        spin_duracion_out = ttk.Spinbox(frame_fade_out, from_=0.5, to=5.0, increment=0.5, 
                                       textvariable=self.app.duracion_fade_out, width=5)
        spin_duracion_out.pack(anchor="w", padx=5, pady=5)

    def _setup_tab_efectos_overlay(self, tab):
        """Configura la interfaz de usuario para la subpestaña de overlays dentro de efectos visuales."""
        # Frame para overlays
        frame_overlay = ttk.LabelFrame(tab, text="Efectos de Overlay")
        frame_overlay.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar overlay
        chk_overlay = ttk.Checkbutton(frame_overlay, text="Aplicar overlay", 
                                     variable=self.app.aplicar_overlay)
        chk_overlay.pack(anchor="w", padx=5, pady=5)
        
        # Frame para la lista de overlays
        frame_lista = ttk.Frame(frame_overlay)
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Listbox con scrollbar para overlays
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.app.listbox_overlays = tk.Listbox(
            frame_lista, 
            selectmode="multiple", 
            yscrollcommand=scrollbar.set,
            height=6, 
            activestyle="none", 
            bg="#e0e0e0", 
            fg="black",
            selectbackground="#d35400", 
            selectforeground="white"
        )
        self.app.listbox_overlays.pack(side="left", fill="both", expand=True)
        
        # Agregar binding para actualizar automáticamente cuando se hace clic
        self.app.listbox_overlays.bind('<<ListboxSelect>>', 
                                      lambda e: self.actualizar_overlays_seleccionados())
        
        scrollbar.config(command=self.app.listbox_overlays.yview)
        
        # Frame para botones
        frame_botones = ttk.Frame(frame_overlay)
        frame_botones.pack(fill="x", padx=5, pady=5)
        
        # Botón para buscar overlays
        btn_buscar = ttk.Button(frame_botones, text="Buscar Overlays", 
                               command=self.buscar_overlays)
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
        self.app.lbl_valor_opacidad = ttk.Label(frame_opacidad, 
                                              text=f"{self.app.opacidad_overlay.get():.2f}")
        self.app.lbl_valor_opacidad.pack(side="right", padx=5)
        
        # Función para actualizar la etiqueta cuando cambia el valor
        def actualizar_valor_opacidad(*args):
            self.app.lbl_valor_opacidad.config(text=f"{self.app.opacidad_overlay.get():.2f}")
        
        # Vincular la función al cambio de valor
        self.app.opacidad_overlay.trace_add("write", actualizar_valor_opacidad)
        
        scale_opacidad = ttk.Scale(frame_opacidad, from_=0.0, to=1.0, orient="horizontal", 
                                  variable=self.app.opacidad_overlay)
        scale_opacidad.pack(side="left", fill="x", expand=True, padx=5)
        
        # Etiqueta para mostrar los overlays seleccionados
        self.app.lbl_overlays_seleccionados = ttk.Label(
            frame_overlay, 
            text="No hay overlays seleccionados", 
            foreground="#e74c3c"
        )
        self.app.lbl_overlays_seleccionados.pack(anchor="w", padx=5, pady=5)
        
        # Etiqueta informativa
        lbl_info = ttk.Label(
            frame_overlay, 
            text="Haz clic en los overlays que deseas aplicar. Se actualizarán automáticamente."
        )
        lbl_info.pack(anchor="w", padx=5, pady=5)

    def buscar_overlays(self):
        """Busca archivos de overlay en la carpeta de overlays y los muestra en el listbox."""
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'overlays')
        
        # Verificar si el directorio existe
        if not os.path.exists(overlay_dir):
            os.makedirs(overlay_dir)  # Crear el directorio si no existe
            messagebox.showinfo("Información", 
                              "Se ha creado la carpeta 'overlays'. Coloca tus archivos de overlay en esta carpeta.")
            return
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Limpiar la lista actual
        self.app.listbox_overlays.delete(0, tk.END)
        
        # Mostrar los overlays en el Listbox
        if not overlays_disponibles:
            messagebox.showinfo("Información", 
                              "No se encontraron archivos de overlay en la carpeta 'overlays'.\n"
                              "Coloca archivos de video (.mp4, .mov, .avi, .webm) en la carpeta 'overlays'.")
        else:
            for overlay in overlays_disponibles:
                self.app.listbox_overlays.insert(tk.END, overlay)
            
            # Actualizar el estado
            self.app.lbl_estado.config(text=f"Se encontraron {len(overlays_disponibles)} overlays")
            # Seleccionar automáticamente el primer overlay
            self.app.listbox_overlays.selection_set(0)
            # Actualizar la lista de overlays seleccionados
            self.actualizar_overlays_seleccionados()

    def seleccionar_overlays(self):
        """Confirma la selección de overlays actual y muestra un mensaje informativo."""
        # Actualizar la lista de overlays seleccionados
        self.actualizar_overlays_seleccionados()
        
        # Mostrar mensaje de confirmación
        if self.app.overlays_seleccionados:
            messagebox.showinfo(
                "Overlays Seleccionados", 
                f"Se han seleccionado {len(self.app.overlays_seleccionados)} overlays:\n\n" + 
                "\n".join([os.path.basename(o) for o in self.app.overlays_seleccionados])
            )
        else:
            messagebox.showinfo("Información", "No has seleccionado ningún overlay")

    def actualizar_overlays_seleccionados(self):
        """Actualiza la lista de overlays seleccionados basándose en la selección del listbox."""
        # Obtener los índices seleccionados
        indices = self.app.listbox_overlays.curselection()
        
        # Limpiar la lista actual de overlays seleccionados
        self.app.overlays_seleccionados = []
        
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'overlays')
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Agregar los overlays seleccionados a la lista
        for indice in indices:
            if indice < len(overlays_disponibles):
                ruta_overlay = os.path.join(overlay_dir, overlays_disponibles[indice])
                self.app.overlays_seleccionados.append(ruta_overlay)
        
        # Actualizar el estado y la etiqueta de overlays seleccionados
        if self.app.overlays_seleccionados:
            self.app.lbl_estado.config(text=f"Se han seleccionado {len(self.app.overlays_seleccionados)} overlays")
            
            # Actualizar la etiqueta con los nombres de los overlays seleccionados
            nombres_overlays = [os.path.basename(path) for path in self.app.overlays_seleccionados]
            if len(nombres_overlays) <= 3:
                texto_overlays = "Seleccionados: " + ", ".join(nombres_overlays)
            else:
                texto_overlays = f"Seleccionados: {nombres_overlays[0]}, {nombres_overlays[1]} y {len(nombres_overlays)-2} más"
            
            self.app.lbl_overlays_seleccionados.config(text=texto_overlays, foreground="#27ae60")
        else:
            self.app.lbl_overlays_seleccionados.config(text="No hay overlays seleccionados", foreground="#e74c3c")
            
    def buscar_y_seleccionar_overlays(self):
        """Busca y selecciona automáticamente todos los overlays disponibles"""
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'overlays')
        
        # Verificar si el directorio existe
        if not os.path.exists(overlay_dir):
            os.makedirs(overlay_dir)  # Crear el directorio si no existe
            print("Se ha creado la carpeta 'overlays'. Coloca tus archivos de overlay en esta carpeta.")
            return
        
        # Obtener los overlays disponibles
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        # Limpiar la lista actual
        self.app.listbox_overlays.delete(0, tk.END)
        
        # Mostrar los overlays en el Listbox
        if not overlays_disponibles:
            print("No se encontraron archivos de overlay en la carpeta 'overlays'.")
            self.app.aplicar_overlay.set(False)  # Desactivar si no hay overlays
            self.app.lbl_overlays_seleccionados.config(text="No hay overlays disponibles", foreground="#e74c3c")
        else:
            # Asegurar que la opción de aplicar overlay esté activada
            self.app.aplicar_overlay.set(True)
            
            for overlay in overlays_disponibles:
                self.app.listbox_overlays.insert(tk.END, overlay)
            
            # Seleccionar automáticamente todos los overlays
            for i in range(len(overlays_disponibles)):
                self.app.listbox_overlays.selection_set(i)
            
            # Actualizar la lista de overlays seleccionados
            self.actualizar_overlays_seleccionados()
            
            # Actualizar la etiqueta de estado
            self.app.lbl_estado.config(text=f"Se cargaron {len(overlays_disponibles)} overlays automáticamente")
            print(f"Se cargaron y seleccionaron automáticamente {len(overlays_disponibles)} overlays")
            
    def obtener_overlays_seleccionados(self):
        """
        Obtiene la lista de overlays seleccionados para usar en la creación de video.
        
        Returns:
            list: Lista de rutas a los archivos de overlay seleccionados.
        """
        # Si hay overlays seleccionados y la opción de aplicar overlay está activada
        if self.app.overlays_seleccionados and self.app.aplicar_overlay.get():
            return self.app.overlays_seleccionados
        else:
            return []