# -*- coding: utf-8 -*-
# Archivo: ui/tab_audio.py

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

class AudioTabFrame(tb.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Audio'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de audio.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _convertir_volumen_musica(self, valor_slider):
        """
        Convierte el valor lineal (0-1) a logarítmico para mejor control en niveles bajos.
        Esto da más precisión en el rango bajo (música ambiental).
        
        Args:
            valor_slider: Valor del slider (entre 0 y 1)
        
        Returns:
            Valor de volumen logarítmico (entre 0.0 y 1.0)
        """
        # Convertir el valor lineal (0-1) a logarítmico para mejor control en niveles bajos
        valor_slider = float(valor_slider)
        if valor_slider <= 0:
            return 0.0  # Permitir silenciar completamente
        
        # Escala logarítmica para un control más preciso en niveles bajos
        # Esto permite un rango de 0.0 (0%) a 1.0 (100%)
        return valor_slider ** 2  # Curva cuadrática para control más preciso en niveles bajos

    def _setup_widgets(self):
        """Configura la interfaz de usuario para la pestaña de audio."""
        # Frame para música de fondo
        frame_musica = tb.LabelFrame(self, text="Música de Fondo")
        frame_musica.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar música
        chk_musica = tb.Checkbutton(frame_musica, text="Aplicar música de fondo", 
                                    variable=self.app.aplicar_musica,
                                    bootstyle="round-toggle")
        chk_musica.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Selección de archivo de música
        lbl_archivo_musica = tb.Label(frame_musica, text="Archivo de música:")
        lbl_archivo_musica.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        frame_archivo_musica = tb.Frame(frame_musica)
        frame_archivo_musica.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        entry_musica = tb.Entry(frame_archivo_musica, textvariable=self.app.archivo_musica, width=40)
        entry_musica.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Botones con estilos modernos
        btn_musica = tb.Button(frame_archivo_musica, text="Examinar", 
                              command=self.app.seleccionar_archivo_musica,
                              bootstyle="info-outline")
        btn_musica.pack(side="right")
        
        # Control de volumen
        lbl_volumen_musica = tb.Label(frame_musica, text="Volumen:")
        lbl_volumen_musica.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Añadir una función para actualizar el volumen cuando se mueve el slider
        def actualizar_volumen_musica(valor):
            valor_float = float(valor)
            # Calcular el valor real (logarítmico)
            valor_real = self._convertir_volumen_musica(valor_float)
            # Actualizar la variable de volumen
            self.app.volumen_musica.set(valor_real)
            # Actualizar la etiqueta (mostrar como porcentaje)
            self.app.etiqueta_volumen_musica.set(f"{valor_real*100:.1f}%")
        
        # Usar un slider con escala visual lineal pero que internamente usa valores logarítmicos
        self.scale_volumen_musica = tb.Scale(frame_musica, from_=0.0, to=1.0, orient="horizontal", 
                                       length=200, command=actualizar_volumen_musica,
                                       bootstyle="info")
        # Valor inicial del slider - por defecto 30%
        self.scale_volumen_musica.set(0.3)  # Esto será aproximadamente 9% después de la conversión cuadrática
        self.scale_volumen_musica.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        # Inicializar el valor real y la etiqueta
        valor_inicial = self._convertir_volumen_musica(0.3)  # Valor cuadrático de 0.3 (aprox. 9%)
        self.app.volumen_musica.set(valor_inicial)
        self.app.etiqueta_volumen_musica.set(f"{valor_inicial*100:.1f}%")
        etiqueta_volumen_musica = tb.Label(frame_musica, textvariable=self.app.etiqueta_volumen_musica)
        etiqueta_volumen_musica.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Fade in/out para música
        frame_fade_musica = tb.Frame(frame_musica)
        frame_fade_musica.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Fade in
        chk_fade_in_musica = tb.Checkbutton(frame_fade_musica, text="Fade in", 
                                          variable=self.app.aplicar_fade_in_musica,
                                          bootstyle="round-toggle")
        chk_fade_in_musica.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_in_musica = tb.Label(frame_fade_musica, text="Duración (s):")
        lbl_fade_in_musica.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_in_musica = tb.Spinbox(frame_fade_musica, from_=0.5, to=10.0, increment=0.5, 
                                        textvariable=self.app.duracion_fade_in_musica, width=5)
        spin_fade_in_musica.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Fade out
        chk_fade_out_musica = tb.Checkbutton(frame_fade_musica, text="Fade out", 
                                           variable=self.app.aplicar_fade_out_musica,
                                           bootstyle="round-toggle")
        chk_fade_out_musica.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_out_musica = tb.Label(frame_fade_musica, text="Duración (s):")
        lbl_fade_out_musica.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_out_musica = tb.Spinbox(frame_fade_musica, from_=0.5, to=10.0, increment=0.5, 
                                         textvariable=self.app.duracion_fade_out_musica, width=5)
        spin_fade_out_musica.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Frame para voz en off
        frame_voz = tb.LabelFrame(self, text="Voz en Off")
        frame_voz.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar voz
        chk_voz = tb.Checkbutton(frame_voz, text="Aplicar voz en off", 
                                variable=self.app.aplicar_voz,
                                bootstyle="round-toggle")
        chk_voz.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Selección de archivo de voz
        lbl_archivo_voz = tb.Label(frame_voz, text="Archivo de voz:")
        lbl_archivo_voz.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        frame_archivo_voz = tb.Frame(frame_voz)
        frame_archivo_voz.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        entry_voz = tb.Entry(frame_archivo_voz, textvariable=self.app.archivo_voz, width=40)
        entry_voz.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Botones con estilos modernos
        btn_voz = tb.Button(frame_archivo_voz, text="Examinar", 
                           command=self.app.seleccionar_archivo_voz,
                           bootstyle="info-outline")
        btn_voz.pack(side="right")
        
        # Control de volumen
        lbl_volumen_voz = tb.Label(frame_voz, text="Volumen:")
        lbl_volumen_voz.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Función para actualizar la etiqueta de volumen de voz
        def actualizar_etiqueta_volumen_voz(valor):
            self.app.etiqueta_volumen_voz.set(f"{float(valor)*100:.0f}%")
        
        self.scale_volumen_voz = tb.Scale(frame_voz, from_=0.0, to=1.0, orient="horizontal", 
                                    variable=self.app.volumen_voz, length=200,
                                    command=actualizar_etiqueta_volumen_voz,
                                    bootstyle="info")
        self.scale_volumen_voz.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        self.app.etiqueta_volumen_voz.set(f"{self.app.volumen_voz.get()*100:.0f}%")
        etiqueta_volumen_voz = tb.Label(frame_voz, textvariable=self.app.etiqueta_volumen_voz)
        etiqueta_volumen_voz.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Fade in/out para voz
        frame_fade_voz = tb.Frame(frame_voz)
        frame_fade_voz.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Fade in
        chk_fade_in_voz = tb.Checkbutton(frame_fade_voz, text="Fade in", 
                                       variable=self.app.aplicar_fade_in_voz,
                                       bootstyle="round-toggle")
        chk_fade_in_voz.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_in_voz = tb.Label(frame_fade_voz, text="Duración (s):")
        lbl_fade_in_voz.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_in_voz = tb.Spinbox(frame_fade_voz, from_=0.5, to=10.0, increment=0.5, 
                                     textvariable=self.app.duracion_fade_in_voz, width=5)
        spin_fade_in_voz.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Fade out
        chk_fade_out_voz = tb.Checkbutton(frame_fade_voz, text="Fade out", 
                                        variable=self.app.aplicar_fade_out_voz,
                                        bootstyle="round-toggle")
        chk_fade_out_voz.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        lbl_fade_out_voz = tb.Label(frame_fade_voz, text="Duración (s):")
        lbl_fade_out_voz.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        spin_fade_out_voz = tb.Spinbox(frame_fade_voz, from_=0.5, to=10.0, increment=0.5, 
                                      textvariable=self.app.duracion_fade_out_voz, width=5)
        spin_fade_out_voz.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Frame para transiciones de video
        frame_transiciones = tb.LabelFrame(self, text="Transiciones de Video")
        frame_transiciones.pack(fill="x", padx=10, pady=10)
        
        # Checkbox para activar transiciones
        chk_transicion = tb.Checkbutton(frame_transiciones, text="Aplicar transiciones", 
                                    variable=self.app.aplicar_transicion)
        chk_transicion.pack(anchor="w", padx=5, pady=5)
        
        # Frame para tipo y duración de transición
        frame_tipo_transicion = tb.Frame(frame_transiciones)
        frame_tipo_transicion.pack(fill="x", padx=5, pady=5)
        
        # Tipo de transición
        lbl_tipo = tb.Label(frame_tipo_transicion, text="Tipo:")
        lbl_tipo.pack(side="left", padx=5)
        
        combo_tipo = tb.Combobox(frame_tipo_transicion, textvariable=self.app.tipo_transicion,
                              values=["dissolve", "fade", "wipe"], width=15)
        combo_tipo.pack(side="left", padx=5)
        
        # Duración de transición
        lbl_duracion = tb.Label(frame_tipo_transicion, text="Duración (s):")
        lbl_duracion.pack(side="left", padx=5)
        
        spin_duracion = tb.Spinbox(frame_tipo_transicion, from_=0.5, to=5.0, increment=0.5,
                                textvariable=self.app.duracion_transicion, width=5)
        spin_duracion.pack(side="left", padx=5)

        # Frame para fade in/out del video
        frame_fade_video = tb.LabelFrame(self, text="Fade In/Out del Video")
        frame_fade_video.pack(fill="x", padx=10, pady=10)
        
        # Frame para fade in
        frame_fade_in = tb.Frame(frame_fade_video)
        frame_fade_in.pack(fill="x", padx=5, pady=5)
        
        chk_fade_in = tb.Checkbutton(frame_fade_in, text="Fade in", 
                                  variable=self.app.aplicar_fade_in)
        chk_fade_in.pack(side="left", padx=5)
        
        lbl_fade_in = tb.Label(frame_fade_in, text="Duración (s):")
        lbl_fade_in.pack(side="left", padx=5)
        
        spin_fade_in = tb.Spinbox(frame_fade_in, from_=0.5, to=10.0, increment=0.5,
                               textvariable=self.app.duracion_fade_in, width=5)
        spin_fade_in.pack(side="left", padx=5)
        
        # Frame para fade out
        frame_fade_out = tb.Frame(frame_fade_video)
        frame_fade_out.pack(fill="x", padx=5, pady=5)
        
        chk_fade_out = tb.Checkbutton(frame_fade_out, text="Fade out",
                                   variable=self.app.aplicar_fade_out)
        chk_fade_out.pack(side="left", padx=5)
        
        lbl_fade_out = tb.Label(frame_fade_out, text="Duración (s):")
        lbl_fade_out.pack(side="left", padx=5)
        
        spin_fade_out = tb.Spinbox(frame_fade_out, from_=0.5, to=10.0, increment=0.5,
                                textvariable=self.app.duracion_fade_out, width=5)
        spin_fade_out.pack(side="left", padx=5)
        
        # Información adicional
        lbl_info = tb.Label(self, text="Nota: Los archivos de audio deben estar en formato MP3, WAV o OGG.")
        lbl_info.pack(anchor="w", padx=10, pady=10)