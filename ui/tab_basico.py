# -*- coding: utf-8 -*-
# Archivo: ui/tab_basico.py

import tkinter as tk
import json
from tkinter import ttk, filedialog, messagebox # Importar filedialog aquí si lo usa algún botón de esta pestaña directamente (aunque parece que no)

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

        # --- Frame para selección de plantilla ---
        frame_plantilla = ttk.LabelFrame(self, text="Plantilla")
        frame_plantilla.pack(fill="x", padx=10, pady=10, side=tk.TOP)
        
        # Crear el menú desplegable para selección de plantilla
        self.app.template_seleccionado = tk.StringVar()
        
        # Obtener las plantillas desde settings.json
        import json
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                
            if 'templates' in settings:
                self.app.templates = {}
                for key, value in settings['templates'].items():
                    if key == 'basic':
                        self.app.templates[key] = "Básico"
                    elif key == 'professional':
                        self.app.templates[key] = "Profesional"
                    elif key == 'minimal':
                        self.app.templates[key] = "Mínimo"
                    else:
                        self.app.templates[key] = key.capitalize()
                
                # Crear el combobox
                lbl_plantilla = ttk.Label(frame_plantilla, text="Seleccionar plantilla:")
                lbl_plantilla.pack(side="left", padx=5, pady=10)
                
                self.template_menu = ttk.Combobox(
                    frame_plantilla,
                    textvariable=self.app.template_seleccionado,
                    values=[self.app.templates[key] for key in sorted(self.app.templates)],
                    state='readonly',
                    width=20
                )
                self.template_menu.pack(side="left", padx=5, pady=10, fill="x", expand=True)
                self.template_menu.bind('<<ComboboxSelected>>', self.aplicar_plantilla)
                
                # Establecer valor por defecto
                if 'basic' in self.app.templates:
                    self.app.template_seleccionado.set(self.app.templates['basic'])
        except Exception as e:
            print(f"Error al cargar plantillas: {e}")
        
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
        
    def aplicar_plantilla(self, event=None):
        """Aplica la configuración de la plantilla seleccionada."""
        # Obtener el nombre mostrado de la plantilla seleccionada
        template_display_name = self.app.template_seleccionado.get()
        
        # Buscar la clave de la plantilla basada en el nombre mostrado
        template_key = None
        for key, display_name in self.app.templates.items():
            if display_name == template_display_name:
                template_key = key
                break
        
        if not template_key:
            messagebox.showerror("Error", "No se pudo encontrar la plantilla seleccionada.")
            return
            
        # Cargar las plantillas desde settings.json
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                
            if 'templates' in settings and template_key in settings['templates']:
                template = settings['templates'][template_key]
                
                # ===== CONFIGURACIÓN BÁSICA =====
                # Duración de imagen y FPS
                if 'duracion_img' in template:
                    self.app.duracion_img.set(template.get('duracion_img', 10.0))
                if 'fps' in template:
                    self.app.fps.set(template.get('fps', 24))
                
                # Efectos
                self.app.aplicar_efectos.set(template.get('aplicar_efectos', False))
                if 'secuencia_efectos' in template:
                    secuencia = template.get('secuencia_efectos', '')
                    self.app.secuencia_efectos.set(secuencia)
                    
                    # Actualizar los checkboxes de efectos basados en la secuencia
                    # Primero, desmarcar todos los checkboxes
                    for efecto in self.app.efecto_checkboxes:
                        self.app.efecto_checkboxes[efecto].set(False)
                    
                    # Luego, marcar solo los que están en la secuencia
                    if secuencia:
                        efectos_lista = secuencia.split(',')
                        for efecto in efectos_lista:
                            if efecto in self.app.efecto_checkboxes:
                                self.app.efecto_checkboxes[efecto].set(True)
                
                # ===== CONFIGURACIÓN DE TRANSICIONES =====
                # Transiciones
                self.app.aplicar_transicion.set(template.get('aplicar_transicion', False))
                self.app.tipo_transicion.set(template.get('tipo_transicion', 'dissolve'))
                self.app.duracion_transicion.set(template.get('duracion_transicion', 1.0))
                
                # Fade in/out
                self.app.aplicar_fade_in.set(template.get('aplicar_fade_in', False))
                self.app.duracion_fade_in.set(template.get('duracion_fade_in', 1.0))
                self.app.aplicar_fade_out.set(template.get('aplicar_fade_out', False))
                self.app.duracion_fade_out.set(template.get('duracion_fade_out', 1.0))
                
                # ===== CONFIGURACIÓN DE AUDIO =====
                # Música
                self.app.aplicar_musica.set(template.get('aplicar_musica', False))
                
                # Actualizar volumen de música y su etiqueta
                volumen_musica_valor = template.get('volumen_musica', 0.5)
                self.app.volumen_musica.set(volumen_musica_valor)
                self.app.etiqueta_volumen_musica.set(f"{volumen_musica_valor*100:.1f}%")
                
                # Actualizar el resto de configuraciones de música
                self.app.aplicar_fade_in_musica.set(template.get('aplicar_fade_in_musica', True))
                self.app.duracion_fade_in_musica.set(template.get('duracion_fade_in_musica', 1.0))
                self.app.aplicar_fade_out_musica.set(template.get('aplicar_fade_out_musica', True))
                self.app.duracion_fade_out_musica.set(template.get('duracion_fade_out_musica', 2.0))
                
                # Voz
                self.app.aplicar_voz.set(template.get('aplicar_voz', False))
                
                # Actualizar volumen de voz y su etiqueta
                volumen_voz_valor = template.get('volumen_voz', 0.75)
                self.app.volumen_voz.set(volumen_voz_valor)
                self.app.etiqueta_volumen_voz.set(f"{volumen_voz_valor*100:.0f}%")
                
                # Actualizar el resto de configuraciones de voz
                self.app.aplicar_fade_in_voz.set(template.get('aplicar_fade_in_voz', False))
                self.app.duracion_fade_in_voz.set(template.get('duracion_fade_in_voz', 2.0))
                self.app.aplicar_fade_out_voz.set(template.get('aplicar_fade_out_voz', True))
                self.app.duracion_fade_out_voz.set(template.get('duracion_fade_out_voz', 2.0))
                
                # ===== CONFIGURACIÓN DE OVERLAY =====
                self.app.aplicar_overlay.set(template.get('aplicar_overlay', False))
                self.app.opacidad_overlay.set(template.get('opacidad_overlay', 0.25))
                if 'overlay_blend_mode' in template:
                    # Verificar si existe la variable antes de intentar establecerla
                    if hasattr(self.app, 'overlay_blend_mode'):
                        self.app.overlay_blend_mode.set(template.get('overlay_blend_mode', 'normal'))
                
                # ===== CONFIGURACIÓN DE SUBTÍTULOS =====
                if 'aplicar_subtitulos' in template:
                    self.app.settings_subtitles.set(template.get('aplicar_subtitulos', False))
                if 'subtitles_font_size' in template:
                    self.app.settings_subtitles_font_size.set(template.get('subtitles_font_size', 54))
                if 'subtitles_font_color' in template:
                    self.app.settings_subtitles_font_color.set(template.get('subtitles_font_color', 'white'))
                if 'subtitles_stroke_color' in template:
                    self.app.settings_subtitles_stroke_color.set(template.get('subtitles_stroke_color', 'black'))
                if 'subtitles_stroke_width' in template:
                    self.app.settings_subtitles_stroke_width.set(template.get('subtitles_stroke_width', 3))
                if 'subtitles_align' in template:
                    self.app.settings_subtitles_align.set(template.get('subtitles_align', 'center'))
                if 'subtitles_position_h' in template:
                    self.app.settings_subtitles_position_h.set(template.get('subtitles_position_h', 'center'))
                if 'subtitles_position_v' in template:
                    self.app.settings_subtitles_position_v.set(template.get('subtitles_position_v', 'bottom'))
                
                # Actualizar la interfaz de usuario si hay callbacks asociados
                # Esto es importante para que los controles que dependen de checkboxes se actualicen
                if hasattr(self.app.tab_efectos, '_actualizar_estado_controles'):
                    self.app.tab_efectos._actualizar_estado_controles()
                if hasattr(self.app.tab_efectos, '_actualizar_visibilidad_paneles'):
                    self.app.tab_efectos._actualizar_visibilidad_paneles()
                
                # Actualizar los sliders de volumen en la pestaña de audio si existe
                if hasattr(self.app, 'tab_audio'):
                    # Actualizar el slider de volumen de música
                    if hasattr(self.app.tab_audio, 'scale_volumen_musica') and hasattr(self.app.tab_audio, '_convertir_volumen_musica'):
                        # Calcular el valor inverso para el slider
                        volumen_actual = self.app.volumen_musica.get()
                        if volumen_actual <= 0.03:
                            valor_slider = 0.0
                        else:
                            valor_slider = (volumen_actual - 0.03) / 0.97
                        self.app.tab_audio.scale_volumen_musica.set(valor_slider)
                    
                    # Actualizar el slider de volumen de voz
                    if hasattr(self.app.tab_audio, 'scale_volumen_voz'):
                        # El slider de voz está vinculado directamente a la variable
                        # pero necesitamos asegurarnos de que se actualice visualmente
                        self.app.tab_audio.scale_volumen_voz.set(self.app.volumen_voz.get())
                
                messagebox.showinfo("Plantilla Aplicada", f"Se ha aplicado la plantilla '{template_display_name}' correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar la plantilla: {e}")
            print(f"Error al aplicar plantilla: {e}")