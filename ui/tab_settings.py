# -*- coding: utf-8 -*-
# Archivo: ui/tab_settings.py

import tkinter as tk
from tkinter import ttk

class SettingsTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Ajustes de Efectos'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de ajustes de efectos.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _setup_widgets(self):
        """Configura la pestaña de ajustes de efectos"""
        # Crear un canvas con scrollbar para manejar muchos widgets
        canvas = tk.Canvas(self, background="#34495e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
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
                              textvariable=self.app.settings_zoom_ratio, width=8)
        spin_zoom.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_zoom_quality = ttk.Label(frame_zoom, text="Calidad:")
        lbl_zoom_quality.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_zoom_quality = ttk.Combobox(frame_zoom, textvariable=self.app.settings_zoom_quality, 
                                        values=["low", "medium", "high"], width=8)
        combo_zoom_quality.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes PanEffect ---
        frame_pan = ttk.LabelFrame(scrollable_frame, text="Pan Effect", style="Card.TLabelframe")
        frame_pan.pack(fill="x", padx=10, pady=5)
        
        # Factor de escala
        lbl_pan_scale = ttk.Label(frame_pan, text="Factor de escala:")
        lbl_pan_scale.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_pan_scale = ttk.Spinbox(frame_pan, from_=1.0, to=2.0, increment=0.1, 
                                   textvariable=self.app.settings_pan_scale_factor, width=8)
        spin_pan_scale.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Easing
        chk_pan_easing = ttk.Checkbutton(frame_pan, text="Easing (suavizado)", 
                                       variable=self.app.settings_pan_easing)
        chk_pan_easing.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_pan_quality = ttk.Label(frame_pan, text="Calidad:")
        lbl_pan_quality.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        combo_pan_quality = ttk.Combobox(frame_pan, textvariable=self.app.settings_pan_quality, 
                                       values=["low", "medium", "high"], width=8)
        combo_pan_quality.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes KenBurnsEffect ---
        frame_kb = ttk.LabelFrame(scrollable_frame, text="Ken Burns Effect", style="Card.TLabelframe")
        frame_kb.pack(fill="x", padx=10, pady=5)
        
        # Ratio de zoom
        lbl_kb_zoom = ttk.Label(frame_kb, text="Ratio de zoom:")
        lbl_kb_zoom.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_kb_zoom = ttk.Spinbox(frame_kb, from_=0.1, to=1.0, increment=0.1, 
                                 textvariable=self.app.settings_kb_zoom_ratio, width=8)
        spin_kb_zoom.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Factor de escala
        lbl_kb_scale = ttk.Label(frame_kb, text="Factor de escala:")
        lbl_kb_scale.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        spin_kb_scale = ttk.Spinbox(frame_kb, from_=1.0, to=2.0, increment=0.1, 
                                  textvariable=self.app.settings_kb_scale_factor, width=8)
        spin_kb_scale.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Dirección
        lbl_kb_direction = ttk.Label(frame_kb, text="Dirección:")
        lbl_kb_direction.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        combo_kb_direction = ttk.Combobox(frame_kb, textvariable=self.app.settings_kb_direction, 
                                        values=["random", "in", "out", "left", "right", "up", "down"], width=8)
        combo_kb_direction.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Calidad
        lbl_kb_quality = ttk.Label(frame_kb, text="Calidad:")
        lbl_kb_quality.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        combo_kb_quality = ttk.Combobox(frame_kb, textvariable=self.app.settings_kb_quality, 
                                      values=["low", "medium", "high"], width=8)
        combo_kb_quality.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # --- Ajustes Transiciones ---
        frame_transition = ttk.LabelFrame(scrollable_frame, text="Transiciones", style="Card.TLabelframe")
        frame_transition.pack(fill="x", padx=10, pady=5)
        
        # Duración
        lbl_transition_duration = ttk.Label(frame_transition, text="Duración (s):")
        lbl_transition_duration.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        spin_transition_duration = ttk.Spinbox(frame_transition, from_=0.5, to=3.0, increment=0.5, 
                                             textvariable=self.app.settings_transition_duration, width=8)
        spin_transition_duration.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Tipo
        lbl_transition_type = ttk.Label(frame_transition, text="Tipo:")
        lbl_transition_type.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_transition_type = ttk.Combobox(frame_transition, textvariable=self.app.settings_transition_type, 
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
                                         textvariable=self.app.settings_overlay_opacity, width=8)
        spin_overlay_opacity.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Modo de mezcla
        lbl_overlay_blend = ttk.Label(frame_overlay, text="Modo de mezcla:")
        lbl_overlay_blend.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        combo_overlay_blend = ttk.Combobox(frame_overlay, textvariable=self.app.settings_overlay_blend_mode, 
                                         values=["normal", "overlay", "screen", "multiply"], width=10)
        combo_overlay_blend.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Información de ayuda
        lbl_info = ttk.Label(scrollable_frame, text="Estos ajustes se aplicarán a todos los efectos del mismo tipo.", 
                           wraplength=400)
        lbl_info.pack(padx=10, pady=10)