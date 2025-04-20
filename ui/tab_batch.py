# -*- coding: utf-8 -*-
# Archivo: ui/tab_batch.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import json
import time
import threading
import asyncio
from datetime import datetime
import subprocess
from datetime import datetime
import sys

# Importar el gestor de prompts
try:
    from prompt_manager import PromptManager
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False

# Importar el gestor de prompts para guiones
try:
    from script_prompt_manager import ScriptPromptManager
    SCRIPT_PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar ScriptPromptManager en tab_batch.")
    SCRIPT_PROMPT_MANAGER_AVAILABLE = False

# Importar el módulo de TTS
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tts_generator import text_chunk_to_speech
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class BatchTabFrame(ttk.Frame):
    """
    Frame que contiene todos los widgets para la pestaña de 'Cola de Proyectos'.
    """
    def __init__(self, parent_notebook, app_instance, **kwargs):
        """
        Inicializa el Frame de la pestaña de cola de proyectos.

        Args:
            parent_notebook: El widget ttk.Notebook que contendrá esta pestaña.
            app_instance: La instancia principal de VideoCreatorApp para acceder a variables y métodos.
        """
        super().__init__(parent_notebook, style="Card.TFrame", **kwargs)
        self.app = app_instance  # Guardamos la referencia a la app principal (VideoCreatorApp)
        
        # Cola de guiones generados pendientes de revisar
        self.guiones_pendientes = []

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

        # --- Inicializar mapas y variables de estilo ---
        self.image_style_map = {}
        self.script_style_map = {}
        if not hasattr(self.app, 'selected_image_style_name'):
            self.app.selected_image_style_name = tk.StringVar()
        if not hasattr(self.app, 'selected_script_style_name'):
            self.app.selected_script_style_name = tk.StringVar()


    def _toggle_script_inputs(self):
        """Muestra u oculta los campos según el modo de creación de guion."""
        mode = self.app.script_creation_mode.get()
        if mode == "manual":
            # Mostrar campos manuales, ocultar campos AI
            if hasattr(self, 'frame_script_manual'):
                self.frame_script_manual.pack(fill="both", expand=True, padx=2, pady=2)
            if hasattr(self, 'frame_script_ai'):
                self.frame_script_ai.pack_forget()
            if hasattr(self, 'lbl_title'):
                self.lbl_title.config(text="Título:")
        elif mode == "ai":
            # Ocultar campos manuales, mostrar campos AI
            if hasattr(self, 'frame_script_manual'):
                self.frame_script_manual.pack_forget()
            if hasattr(self, 'frame_script_ai'):
                self.frame_script_ai.pack(fill="both", expand=True, padx=2, pady=2)
            if hasattr(self, 'lbl_title'):
                self.lbl_title.config(text="Título/Idea Guion:")
        else:
            # Ocultar ambos en caso de error o estado inesperado
            if hasattr(self, 'frame_script_manual'): 
                self.frame_script_manual.pack_forget()
            if hasattr(self, 'frame_script_ai'): 
                self.frame_script_ai.pack_forget()
    
    def _generar_guion_ai(self):
        """Genera un guion usando IA y lo muestra en el campo de texto del guion manual."""
        print("\n--- INICIANDO GENERACIÓN DE GUION CON IA ---")
        print(f"Estado actual de guiones_pendientes: {len(self.guiones_pendientes)} guiones")
        
        # Obtener los datos necesarios para la generación
        titulo = self.entry_title.get().strip()
        contexto = self.txt_contexto_ai.get("1.0", tk.END).strip()
        estilo = self.app.selected_script_style.get()
        num_secciones = self.app.ai_num_sections.get()
        palabras_por_seccion = self.app.ai_words_per_section.get()
        voice = self.app.selected_voice.get()
        
        # *** Leer el estado del checkbox ***
        auto_queue = self.auto_queue_ai_script.get()
        print(f"Encolado automático: {'Sí' if auto_queue else 'No'}")
        
        # *** CAPTURAR CONTEXTO ANTES DE INICIAR HILO ***
        titulo_capturado = titulo
        contexto_capturado = contexto
        estilo_capturado = estilo
        num_secciones_capturado = num_secciones
        palabras_por_seccion_capturado = palabras_por_seccion
        voice_capturada = voice
        
        print(f"Título: '{titulo_capturado}'")
        print(f"Estilo: '{estilo_capturado}'")
        print(f"Número de secciones: {num_secciones_capturado}")
        print(f"Palabras por sección: {palabras_por_seccion_capturado}")
        print(f"Voz seleccionada: {voice_capturada}")
        
        # Validar datos
        if not titulo_capturado:
            messagebox.showerror("Error", "Por favor, introduce un Título / Idea para el proyecto.")
            return
            
        if not contexto_capturado:
            messagebox.showerror("Error", "Por favor, introduce el Contexto/Notas para la generación del guion.")
            return
        
        # Convertir a enteros
        try:
            num_secciones_capturado = int(num_secciones_capturado)
            palabras_por_seccion_capturado = int(palabras_por_seccion_capturado)
        except ValueError:
            messagebox.showerror("Error", "El número de secciones y palabras por sección deben ser números enteros.")
            return
        
        # --- Usar valores predeterminados seguros para video_settings ---
        video_settings_capturados = {}  # Diccionario vacío por defecto
        try:
            if auto_queue:  # Solo recopilar settings si se va a encolar automáticamente
                # Usar valores predeterminados seguros en lugar de intentar acceder a atributos que podrían no existir
                video_settings_capturados = {
                    # Configuraciones básicas con valores predeterminados seguros
                    'duracion_imagen': 5.0,  # 5 segundos por imagen
                    'duracion_transicion': 1.0,  # 1 segundo de transición
                    'tipo_transicion': 'fade',  # Transición por defecto: fade
                    'fps': 30,  # 30 FPS
                    'resolucion': '1080p',  # Resolución Full HD
                    
                    # Configuraciones de efectos
                    'efectos_habilitados': False,  # Sin efectos por defecto
                    'efecto_seleccionado': 'none',  # Sin efecto específico
                    'modo_secuencia': 'aleatorio',  # Modo aleatorio para secuencias
                    
                    # Configuraciones de audio
                    'musica_habilitada': False,  # Sin música por defecto
                    'volumen_musica': 0.5,  # Volumen medio para música
                    'volumen_voz': 1.0,  # Volumen completo para voz
                    
                    # Configuraciones de subtítulos
                    'subtitulos_habilitados': False,  # Sin subtítulos por defecto
                    'tamano_fuente_subtitulos': 24,  # Tamaño de fuente estándar
                    'color_texto_subtitulos': 'white',  # Texto blanco
                    'color_fondo_subtitulos': 'black'  # Fondo negro
                }
                
                # Intentar obtener algunos valores de la interfaz si están disponibles
                # Usar getattr con valores predeterminados para evitar errores
                if hasattr(self.app, 'selected_voice'):
                    video_settings_capturados['voz'] = self.app.selected_voice.get()
                
                print("DEBUG UI: video_settings predeterminados preparados para encolado.")
        except Exception as e:
            # Solo muestra error si se intentaba encolar automáticamente
            if auto_queue:
                messagebox.showerror("Error", f"Error al leer parámetros de la UI necesarios para encolar: {e}")
                print(f"ERROR LEYENDO PARÁMETROS UI (Auto-Queue): {e}")
                import traceback
                traceback.print_exc()
                return  # No continuar si fallan los settings y se quería encolar
            else:
                print(f"ADVERTENCIA: Error leyendo parámetros UI, pero no se requería encolado automático: {e}")
                video_settings_capturados = {}  # Resetear por si acaso
            
        # Mostrar mensaje de progreso
        messagebox.showinfo("Generando Guion", f"Generando guion para '{titulo_capturado}'... Esto puede tardar unos minutos.")
        self.update_idletasks()  # Actualizar la interfaz
        
        # Cambiar el cursor a "espera"
        self.config(cursor="wait")
        
        try:
            # Importar la función de generación de guiones
            from ai_script_generator import generar_guion
            
            # Generar el guion en un hilo separado para no bloquear la interfaz
            def generar_en_segundo_plano(captured_title, captured_context, captured_style, 
                                         captured_num_sec, captured_words_sec, captured_voice, 
                                         captured_settings, should_auto_queue):
                try:
                    print(f"DEBUG HILO: Iniciando generación para '{captured_title}', AutoQueue={should_auto_queue}")
                    guion = generar_guion(
                        titulo=captured_title,
                        contexto=captured_context,
                        estilo=captured_style,
                        num_secciones=captured_num_sec,
                        palabras_por_seccion=captured_words_sec
                    )
                    
                    if guion:
                        print(f"DEBUG HILO: Guion generado para '{captured_title}'. Longitud: {len(guion)} caracteres.")
                        # *** Decidir qué callback llamar basado en el flag ***
                        if should_auto_queue:
                            print(f"DEBUG HILO: Llamando a _encolar_proyecto_generado para '{captured_title}'.")
                            self.after(0, lambda: self._encolar_proyecto_generado(
                                captured_title, guion, captured_voice, captured_settings
                            ))
                        else:
                            print(f"DEBUG HILO: Llamando a _mostrar_guion_generado para '{captured_title}'.")
                            self.after(0, lambda: self._mostrar_guion_generado(captured_title, guion))
                    else:
                        raise ValueError(f"La función generar_guion no devolvió contenido para '{captured_title}'.")
                except Exception as e:
                    print(f"DEBUG HILO: Error en generación para '{captured_title}': {e}")
                    # Pasar el título original al error handler también
                    self.after(0, lambda: self._mostrar_error_generacion(captured_title, str(e)))
            
            # Iniciar el hilo pasando el contexto capturado
            import threading
            thread = threading.Thread(target=generar_en_segundo_plano, args=(
                titulo_capturado,
                contexto_capturado,
                estilo_capturado,
                num_secciones_capturado,
                palabras_por_seccion_capturado,
                voice_capturada,
                video_settings_capturados,
                auto_queue
            ))
            thread.daemon = True  # El hilo se cerrará cuando se cierre la aplicación
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la generación del guion para '{titulo_capturado}': {str(e)}")
            self.config(cursor="")
    
    def _mostrar_guion_generado(self, titulo_recibido, guion):
        """Gestiona un guion generado añadiéndolo a la cola de guiones pendientes."""
        if guion is None:
            print(f"ERROR INTERNO: _mostrar_guion_generado recibió guion None para '{titulo_recibido}'")
            self._mostrar_error_generacion(titulo_recibido, "La generación devolvió un resultado vacío.")
            return
            
        print(f"\n--- GUION GENERADO EXITOSAMENTE PARA '{titulo_recibido}' ---\nLongitud: {len(guion)} caracteres")
        print(f"Primeros 200 caracteres: {guion[:200]}...")
        print(f"Estado actual de guiones_pendientes: {len(self.guiones_pendientes)} guiones")
        
        try:
            # Usar el título recibido del hilo, NO leer de la GUI
            titulo = titulo_recibido or f"Guion_{len(self.guiones_pendientes) + 1}"
            print(f"Título para el nuevo guion: '{titulo}'")
            
            # Añadir el guion a la cola de guiones pendientes
            self.guiones_pendientes.append({
                'titulo': titulo,
                'guion': guion,
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"Guion añadido a la cola. Ahora hay {len(self.guiones_pendientes)} guiones pendientes.")
            
            # Restaurar el cursor
            self.config(cursor="")
            
            # Preguntar al usuario si desea ver el guion ahora o continuar generando más
            print(f"Mostrando diálogo de confirmación al usuario para '{titulo}'...")
            respuesta = messagebox.askyesno(
                "Guion Generado", 
                f"El guion '{titulo}' ha sido generado con éxito.\n\n"
                f"Tienes {len(self.guiones_pendientes)} guion(es) pendiente(s) de revisar.\n\n"
                "¿Deseas ver este guion ahora?"
            )
            print(f"Respuesta del usuario para '{titulo}': {respuesta}")
            
            if respuesta:
                self._mostrar_guion_especifico(len(self.guiones_pendientes) - 1)  # Mostrar el último guion generado
            else:
                # Si el usuario decide no ver el guion ahora, mostrar un botón para verlo más tarde
                self._actualizar_boton_guiones_pendientes()
            
            print("Proceso de gestión de guion completado.")
        except Exception as e:
            print(f"ERROR al gestionar guion generado: {e}")
            messagebox.showerror("Error", f"Se generó el guion pero hubo un error al gestionarlo: {e}")
    
    def _mostrar_guion_especifico(self, indice):
        """Muestra un guion específico de la cola de guiones pendientes."""
        if 0 <= indice < len(self.guiones_pendientes):
            guion_info = self.guiones_pendientes[indice]
            
            # Cambiar al modo manual para mostrar el guion
            print(f"Mostrando guion '{guion_info['titulo']}'...")
            self.app.script_creation_mode.set("manual")
            self._toggle_script_inputs()
            
            # Actualizar el título si está vacío
            if not self.entry_title.get().strip():
                self.entry_title.delete(0, tk.END)
                self.entry_title.insert(0, guion_info['titulo'])
            
            # Limpiar el campo de texto y mostrar el guion
            self.txt_script.delete("1.0", tk.END)
            self.txt_script.insert("1.0", guion_info['guion'])
            
            # Mostrar un mensaje informativo
            messagebox.showinfo(
                "Guion Cargado", 
                f"El guion '{guion_info['titulo']}' ha sido cargado en el editor.\n\n"
                "Puedes revisarlo y editarlo antes de añadir el proyecto a la cola."
            )
    
    def _actualizar_boton_guiones_pendientes(self):
        """Actualiza o crea el botón de guiones pendientes."""
        # Si ya existe el botón, actualizar su texto
        if hasattr(self, 'btn_guiones_pendientes'):
            self.btn_guiones_pendientes.config(
                text=f"Ver Guiones Pendientes ({len(self.guiones_pendientes)})"
            )
        else:
            # Crear el botón si no existe
            self.btn_guiones_pendientes = ttk.Button(
                self, 
                text=f"Ver Guiones Pendientes ({len(self.guiones_pendientes)})",
                command=self._mostrar_menu_guiones_pendientes,
                style="Secondary.TButton"
            )
            self.btn_guiones_pendientes.pack(side="top", padx=10, pady=5, fill="x")
    
    def _mostrar_menu_guiones_pendientes(self):
        """Muestra un menú con los guiones pendientes de revisar."""
        if not self.guiones_pendientes:
            messagebox.showinfo("Guiones Pendientes", "No hay guiones pendientes de revisar.")
            return
        
        # Crear un menú emergente
        menu = tk.Menu(self, tearoff=0)
        
        # Añadir una opción para cada guion pendiente
        for i, guion_info in enumerate(self.guiones_pendientes):
            menu.add_command(
                label=f"{i+1}. {guion_info['titulo']} ({guion_info['fecha']})",
                command=lambda idx=i: self._mostrar_guion_especifico(idx)
            )
        
        # Añadir una opción para limpiar la lista
        menu.add_separator()
        menu.add_command(label="Limpiar lista", command=self._limpiar_guiones_pendientes)
        
        # Mostrar el menú en la posición del ratón
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()
    
    def _limpiar_guiones_pendientes(self):
        """Limpia la lista de guiones pendientes."""
        if messagebox.askyesno("Limpiar Guiones", "¿Estás seguro de que deseas eliminar todos los guiones pendientes?"):
            self.guiones_pendientes = []
            if hasattr(self, 'btn_guiones_pendientes'):
                self.btn_guiones_pendientes.pack_forget()
                delattr(self, 'btn_guiones_pendientes')
    
    def _mostrar_error_generacion(self, titulo_fallido, error_msg):
        """Muestra un mensaje de error si la generación del guion falla."""
        print(f"\n--- ERROR AL GENERAR GUION PARA '{titulo_fallido}' ---\n{error_msg}")
        try:
            messagebox.showerror("Error", f"Error al generar el guion para '{titulo_fallido}':\n{error_msg}")
            self.config(cursor="")
            print(f"Mensaje de error mostrado para '{titulo_fallido}'.")
        except Exception as e:
            print(f"ERROR al mostrar mensaje de error: {e}")
    
    def _setup_widgets(self):
        """Configura la pestaña usando grid para mejorar el layout."""
        # PanedWindow setup (se mantiene)
        self.paned_window = ttk.PanedWindow(self, orient="vertical")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Sección de Entrada (Usando Grid) ---
        frame_input = ttk.LabelFrame(self.paned_window, text="Nuevo Proyecto")
        self.paned_window.add(frame_input, weight=1) # Peso 1 para la parte de entrada

        # Configurar columnas para el frame_input (ej: 6 columnas flexibles)
        for i in range(6):
            frame_input.columnconfigure(i, weight=1, uniform="input_cols") # Uniform para que crezcan igual

        # --- Fila 0: Modo ---
        frame_mode = ttk.Frame(frame_input)
        # columnspan=6 para que ocupe todo el ancho de las columnas configuradas
        frame_mode.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky="w")
        lbl_mode = ttk.Label(frame_mode, text="Método Guion:")
        lbl_mode.pack(side="left", padx=(0, 5))
        # Asumiendo que self.app.script_creation_mode existe y es un tk.StringVar()
        rb_manual = ttk.Radiobutton(frame_mode, text="Manual",
                                variable=self.app.script_creation_mode, value="manual",
                                command=self._toggle_script_inputs)
        rb_manual.pack(side="left", padx=2)
        rb_ai = ttk.Radiobutton(frame_mode, text="Generar con IA",
                            variable=self.app.script_creation_mode, value="ai",
                            command=self._toggle_script_inputs)
        rb_ai.pack(side="left", padx=2)

        # --- Fila 1: Título, Voz, Estilo Imágenes ---
        self.lbl_title = ttk.Label(frame_input, text="Título:")
        self.lbl_title.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_title = ttk.Entry(frame_input)
        # columnspan=2 para darle más espacio al título
        self.entry_title.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        lbl_voice = ttk.Label(frame_input, text="Voz:")
        lbl_voice.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        voces = [ "es-EC-LuisNeural", "es-ES-ElviraNeural", "es-MX-DaliaNeural", "es-AR-ElenaNeural", "es-CO-GonzaloNeural", "es-CL-CatalinaNeural", "es-MX-JorgeNeural"]
        if not hasattr(self.app, 'selected_voice'): self.app.selected_voice = tk.StringVar(value="es-MX-JorgeNeural")
        voice_combo = ttk.Combobox(frame_input, textvariable=self.app.selected_voice, values=voces, state="readonly", width=20)
        voice_combo.grid(row=1, column=4, padx=5, pady=5, sticky="ew")

        lbl_img_style = ttk.Label(frame_input, text="Estilo Img:")
        lbl_img_style.grid(row=1, column=5, padx=(10, 5), pady=5, sticky="w") # Añadido padding izquierdo
        # --- Poblar Dropdown Estilo Imágenes (Usando PromptManager Unificado) ---
        style_names = ["(Error)"]
        style_ids = ["default"]
        self.image_style_map = {}
        if PROMPT_MANAGER_AVAILABLE:
            try:
                prompt_manager = PromptManager()
                style_tuples = prompt_manager.get_prompt_names()
                if style_tuples:
                     style_names = [name for _, name in style_tuples]
                     style_ids = [id for id, _ in style_tuples]
                     self.image_style_map = dict(zip(style_names, style_ids))
                     if not hasattr(self.app, 'selected_image_style_name'): self.app.selected_image_style_name = tk.StringVar()
                     default_img_style_name = "Cinematográfico" # O tu default
                     self.app.selected_image_style_name.set(default_img_style_name if default_img_style_name in style_names else style_names[0])
            except Exception as e: print(f"Error cargando estilos: {e}")
        else:
             if not hasattr(self.app, 'selected_image_style_name'): self.app.selected_image_style_name = tk.StringVar(value=style_names[0])

        self.combo_image_style = ttk.Combobox(frame_input, textvariable=self.app.selected_image_style_name, values=style_names, state="readonly", width=20)
        self.combo_image_style.grid(row=1, column=6, padx=5, pady=5, sticky="ew") # Usa columna 6
        # Aumentar columnspan de los elementos en la fila 1 para que ocupen 6 columnas en total
        frame_input.columnconfigure(6, weight=1, uniform="input_cols") # Configurar columna 6

        # --- Fila 2: Contenedor Script (ocupa todo el ancho) ---
        self.script_container = ttk.Frame(frame_input)
        self.script_container.grid(row=2, column=0, columnspan=7, padx=5, pady=5, sticky="nsew") # columnspan=7
        frame_input.rowconfigure(2, weight=1) # Fila del script expandible verticalmente
        self.script_container.rowconfigure(0, weight=1) # Contenido expandible
        self.script_container.columnconfigure(0, weight=1)

        # -- Frame Manual (se añadirá/quitará con grid en _toggle_script_inputs) --
        self.frame_script_manual = ttk.Frame(self.script_container)
        self.frame_script_manual.columnconfigure(0, weight=1)
        self.frame_script_manual.rowconfigure(0, weight=1)
        self.txt_script = tk.Text(self.frame_script_manual, wrap="word", height=10, undo=True)
        scrollbar_script = ttk.Scrollbar(self.frame_script_manual, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar_script.set)
        self.txt_script.grid(row=0, column=0, sticky="nsew")
        scrollbar_script.grid(row=0, column=1, sticky="ns")

        # -- Frame AI (se añadirá/quitará con grid en _toggle_script_inputs) --
        self.frame_script_ai = ttk.LabelFrame(self.script_container, text="Parámetros Generación IA")
        self.frame_script_ai.columnconfigure(0, weight=3) # Columna Contexto
        self.frame_script_ai.columnconfigure(1, weight=1) # Columna Controles
        self.frame_script_ai.rowconfigure(1, weight=1) # Fila Contexto expandible

        # Contexto (Col 0)
        lbl_contexto = ttk.Label(self.frame_script_ai, text="Contexto/Notas:")
        lbl_contexto.grid(row=0, column=0, sticky="nw", padx=5, pady=(5,0))
        self.txt_contexto_ai = tk.Text(self.frame_script_ai, wrap="word", height=8, undo=True) # Habilitar undo
        scrollbar_contexto = ttk.Scrollbar(self.frame_script_ai, orient="vertical", command=self.txt_contexto_ai.yview)
        self.txt_contexto_ai.configure(yscrollcommand=scrollbar_contexto.set)
        self.txt_contexto_ai.grid(row=1, column=0, rowspan=7, sticky="nsew", padx=(5,0), pady=(0,5)) # rowspan para ocupar espacio vertical
        scrollbar_contexto.grid(row=1, column=0, rowspan=7, sticky="nse", padx=(0,5), pady=(0,5))

        # Controles AI (Col 1)
        ai_controls_row = 0
        # Estilo Guion
        lbl_script_style = ttk.Label(self.frame_script_ai, text="Estilo Guion:")
        lbl_script_style.grid(row=ai_controls_row, column=1, sticky="w", padx=5, pady=2)
        # Usar la misma lista de estilos que para imágenes
        self.script_style_map = self.image_style_map # Comparten mapa Nombre->ID
        if not hasattr(self.app, 'selected_script_style_name'):
            self.app.selected_script_style_name = tk.StringVar()
            default_script_style_name = "Predeterminado (Vidas Santas - Polémico/Enganche)"
            self.app.selected_script_style_name.set(default_script_style_name if default_script_style_name in style_names else style_names[0])
        self.combo_script_style = ttk.Combobox(self.frame_script_ai, textvariable=self.app.selected_script_style_name, values=style_names, state="readonly", width=20)
        self.combo_script_style.grid(row=ai_controls_row, column=1, sticky="e", padx=5, pady=2)
        ai_controls_row += 1

        # Nº Secciones
        lbl_num_sec = ttk.Label(self.frame_script_ai, text="Nº Secciones:")
        lbl_num_sec.grid(row=ai_controls_row, column=1, sticky="w", padx=5, pady=2)
        if not hasattr(self.app, 'ai_num_sections'): self.app.ai_num_sections = tk.IntVar(value=5) # Asegurar que existe
        spin_num_sec = ttk.Spinbox(self.frame_script_ai, from_=1, to=15, increment=1, textvariable=self.app.ai_num_sections, width=5)
        spin_num_sec.grid(row=ai_controls_row, column=1, sticky="e", padx=5, pady=2)
        ai_controls_row += 1

        # Palabras/Sección
        lbl_pal_sec = ttk.Label(self.frame_script_ai, text="Palabras/Sección:")
        lbl_pal_sec.grid(row=ai_controls_row, column=1, sticky="w", padx=5, pady=2)
        if not hasattr(self.app, 'ai_words_per_section'): self.app.ai_words_per_section = tk.IntVar(value=300) # Asegurar que existe
        spin_pal_sec = ttk.Spinbox(self.frame_script_ai, from_=50, to=1000, increment=50, textvariable=self.app.ai_words_per_section, width=7)
        spin_pal_sec.grid(row=ai_controls_row, column=1, sticky="e", padx=5, pady=2)
        ai_controls_row += 1

        # Subtítulos Checkbox
        if not hasattr(self.app, 'aplicar_subtitulos'): self.app.aplicar_subtitulos = tk.BooleanVar(value=True)
        chk_subtitles = ttk.Checkbutton(self.frame_script_ai, text="Generar Subtítulos", variable=self.app.aplicar_subtitulos)
        chk_subtitles.grid(row=ai_controls_row, column=1, sticky="w", padx=5, pady=5)
        ai_controls_row += 1

        # Auto-Queue Checkbox
        self.auto_queue_ai_script = tk.BooleanVar(value=False) # Definir la variable
        chk_auto_queue = ttk.Checkbutton(self.frame_script_ai, text="Encolar Auto.", variable=self.auto_queue_ai_script)
        chk_auto_queue.grid(row=ai_controls_row, column=1, sticky="w", padx=5, pady=5)
        ai_controls_row += 1

        # GENERAR GUION Button - ¡Asegúrate de que se añade!
        self.btn_generar_guion = ttk.Button(
            self.frame_script_ai,
            text="GENERAR GUION",
            command=self._generar_guion_ai,
            style="Accent.TButton" # O usa "Action.TButton" si lo prefieres más llamativo
        )
        # sticky="ew" para que ocupe el ancho de la columna, pady para espaciarlo
        self.btn_generar_guion.grid(row=ai_controls_row, column=1, sticky="ew", padx=5, pady=(10, 5))
        ai_controls_row += 1 # Incrementar por si añades algo más debajo


        # --- Fila 3: Ajustes de Voz ---
        frame_voice_controls = ttk.LabelFrame(frame_input, text="Ajustes de Voz")
        frame_voice_controls.grid(row=3, column=0, columnspan=7, padx=5, pady=5, sticky="ew") # columnspan=7
        frame_voice_controls.columnconfigure(1, weight=1) # Columna del slider expandible

        # Rate
        lbl_rate = ttk.Label(frame_voice_controls, text="Velocidad:")
        lbl_rate.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # ... (resto de widgets de Rate, usando grid) ...
        scale_rate = ttk.Scale(frame_voice_controls, from_=-50, to=50, orient="horizontal", variable=self.app.tts_rate_value, length=200)
        scale_rate.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        lbl_rate_value = ttk.Label(frame_voice_controls, textvariable=self.app.tts_rate_str, width=6) # Usa textvariable
        lbl_rate_value.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Pitch
        lbl_pitch = ttk.Label(frame_voice_controls, text="Tono:")
        lbl_pitch.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # ... (resto de widgets de Pitch, usando grid) ...
        scale_pitch = ttk.Scale(frame_voice_controls, from_=-50, to=50, orient="horizontal", variable=self.app.tts_pitch_value, length=200)
        scale_pitch.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        lbl_pitch_value = ttk.Label(frame_voice_controls, textvariable=self.app.tts_pitch_str, width=6) # Usa textvariable
        lbl_pitch_value.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # Preview Button
        self.btn_preview = ttk.Button(frame_voice_controls, text="Probar Voz", command=self._preview_voice, style="Secondary.TButton")
        self.btn_preview.grid(row=0, rowspan=2, column=3, padx=10, pady=5, sticky="e") # Columna 3 para alinear a la derecha

        # Inicializar textos de rate/pitch (ya se hace con trace_add en __init__ si las variables existen)


        # --- Fila 4: Botones de Acción Principales ---
        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=4, column=0, columnspan=7, padx=5, pady=10, sticky="e") # Alinear a la derecha
        btn_clear = ttk.Button(frame_buttons, text="Limpiar Campos", command=self._clear_project_fields, style="Secondary.TButton")
        btn_clear.pack(side="right", padx=5) # Pack dentro de este frame está bien
        btn_add_queue = ttk.Button(frame_buttons, text="Añadir a la Cola", command=self._add_project_to_queue, style="Action.TButton")
        btn_add_queue.pack(side="right", padx=5)


        # --- Sección de Cola (Inferior) ---
        frame_queue = ttk.LabelFrame(self.paned_window, text="Cola de Procesamiento")
        self.paned_window.add(frame_queue, weight=2) # Darle más peso para que sea más grande

        # Treeview y botones de la cola (tu código aquí parece correcto, usa pack internamente)
        # ... (Código del Treeview, scrollbar, frame_botones_principales, frame_regeneracion) ...
        # ... Asegúrate de que self.app.tree_queue se asigna aquí ...
        # --- Copiado de tu código anterior para la sección de cola ---
        self.app.tree_queue = ttk.Treeview(frame_queue, columns=("titulo", "estado", "tiempo"), show="headings", height=10)
        self.app.tree_queue.heading("titulo", text="Título del Proyecto"); self.app.tree_queue.column("titulo", width=450)
        self.app.tree_queue.heading("estado", text="Estado"); self.app.tree_queue.column("estado", width=180, anchor="center")
        self.app.tree_queue.heading("tiempo", text="Tiempo"); self.app.tree_queue.column("tiempo", width=100, anchor="center")
        frame_treeview = ttk.Frame(frame_queue); frame_treeview.pack(fill="both", expand=True, pady=(5, 5)) # Añadido pady
        scrollbar_queue = ttk.Scrollbar(frame_treeview, orient="vertical", command=self.app.tree_queue.yview)
        self.app.tree_queue.configure(yscrollcommand=scrollbar_queue.set)
        self.app.tree_queue.pack(side="left", fill="both", expand=True)
        scrollbar_queue.pack(side="right", fill="y")
        # Botones de la cola
        frame_botones_principales = ttk.Frame(frame_queue); frame_botones_principales.pack(fill="x", pady=(5, 0))
        btn_cargar_proyecto = ttk.Button(frame_botones_principales, text="Cargar Proyecto Existente", command=self._cargar_proyecto_existente, style="Secondary.TButton")
        btn_cargar_proyecto.pack(side="left", padx=5, pady=5)
        btn_generate_video = ttk.Button(frame_botones_principales, text="Generar Vídeo", command=self.app.trigger_video_generation_for_selected, style="Action.TButton")
        btn_generate_video.pack(side="right", padx=5, pady=5)
        frame_regeneracion = ttk.Frame(frame_queue); frame_regeneracion.pack(fill="x", pady=(0, 5))
        lbl_regenerar = ttk.Label(frame_regeneracion, text="Regenerar:", font=("Helvetica", 10, "bold")); lbl_regenerar.pack(side="left", padx=5, pady=5)
        btn_regenerar_audio = ttk.Button(frame_regeneracion, text="Audio", command=self._regenerar_audio, style="Secondary.TButton", width=10); btn_regenerar_audio.pack(side="left", padx=5, pady=5)
        btn_regenerar_prompts = ttk.Button(frame_regeneracion, text="Prompts", command=self._regenerar_prompts, style="Secondary.TButton", width=10); btn_regenerar_prompts.pack(side="left", padx=5, pady=5)
        btn_regenerar_imagenes = ttk.Button(frame_regeneracion, text="Imágenes", command=self._regenerar_imagenes, style="Secondary.TButton", width=10); btn_regenerar_imagenes.pack(side="left", padx=5, pady=5)
        btn_regenerar_subtitulos = ttk.Button(frame_regeneracion, text="Subtítulos", command=self._regenerar_subtitulos, style="Secondary.TButton", width=10); btn_regenerar_subtitulos.pack(side="left", padx=5, pady=5)
        # --- Fin sección cola ---

        # --- Final de _setup_widgets ---

        # Asignar treeview al manager (asegúrate que esta línea esté antes del sashpos)
        if hasattr(self.app, 'batch_tts_manager') and hasattr(self.app.batch_tts_manager, 'tree_queue'):
             self.app.batch_tts_manager.tree_queue = self.app.tree_queue

        # --- NUEVO: Establecer posición inicial del separador ---
        # Forzar a Tkinter a calcular los tamaños iniciales
        self.paned_window.update_idletasks()
        try:
            # Obtener la altura total actual de la ventana (o del paned_window)
            total_height = self.paned_window.winfo_height()
            if total_height <= 1: # Si aún no tiene tamaño, usar un valor fijo
                 total_height = 800 # O un valor que sepas que es razonable para tu ventana

            # Calcular una posición inicial (ej: 60% para el panel superior)
            initial_sash_pos = int(total_height * 0.60)
            # O simplemente un valor fijo en píxeles si lo prefieres:
            # initial_sash_pos = 550 # Ajusta este valor según necesites

            if initial_sash_pos < 100: initial_sash_pos = 100 # Mínimo para el panel superior
            if initial_sash_pos > total_height - 50: initial_sash_pos = total_height - 50 # Dejar mínimo para el inferior

            print(f"DEBUG: Intentando establecer sash en {initial_sash_pos} (altura total: {total_height})")
            self.paned_window.sashpos(0, initial_sash_pos) # 0 es el índice del primer sash (solo hay uno)

        except tk.TclError as e:
             # A veces falla si la ventana es muy pequeña al inicio
             print(f"ADVERTENCIA: No se pudo establecer la posición inicial del sash: {e}")
        except Exception as e:
             print(f"ERROR inesperado estableciendo sash: {e}")
        # --- FIN NUEVO ---

        # Llamada inicial para mostrar/ocultar según el modo (esta debe ser la última línea)
        self._toggle_script_inputs()


    def _toggle_script_inputs(self):
        """Muestra u oculta los frames según el modo (usando grid)."""
        mode = self.app.script_creation_mode.get()
        # Asegurarse de que el contenedor exista
        if not hasattr(self, 'script_container'): return

        if mode == "manual":
            if hasattr(self, 'frame_script_ai'): self.frame_script_ai.grid_forget() # Ocultar AI
            if hasattr(self, 'frame_script_manual'):
                # Mostrar el frame manual dentro del contenedor
                self.frame_script_manual.grid(row=0, column=0, sticky="nsew") # Usar grid
            if hasattr(self, 'lbl_title'): self.lbl_title.config(text="Título:")
        elif mode == "ai":
            if hasattr(self, 'frame_script_manual'): self.frame_script_manual.grid_forget() # Ocultar Manual
            if hasattr(self, 'frame_script_ai'):
                # Mostrar el frame AI dentro del contenedor
                self.frame_script_ai.grid(row=0, column=0, sticky="nsew") # Usar grid
            if hasattr(self, 'lbl_title'): self.lbl_title.config(text="Título/Idea Guion:")
        else: # Ocultar ambos si modo desconocido
            if hasattr(self, 'frame_script_manual'): self.frame_script_manual.grid_forget()
            if hasattr(self, 'frame_script_ai'): self.frame_script_ai.grid_forget()

        # Reconfigurar el contenedor para que su contenido se expanda
        # Estas líneas aseguran que el frame que se muestra (manual o AI)
        # ocupe todo el espacio disponible dentro de script_container.
        self.script_container.grid_rowconfigure(0, weight=1)
        self.script_container.grid_columnconfigure(0, weight=1)

    # ... (resto de tus métodos: _add_project_to_queue, _clear_project_fields, _get_selected_project, etc.) ...
    # Asegúrate de que las referencias a self.app sean correctas y que esas variables/métodos
    # existan en la instancia principal de VideoCreatorApp pasada a __init__
    # --- Asegúrate de tener todos tus métodos necesarios aquí ---
    # _encolar_proyecto_generado, _regenerar_audio, _regenerar_prompts, etc.

    # Necesitarás estas funciones si no están definidas en otra parte de esta clase
    def _cargar_proyecto_existente(self):
        print("Placeholder: Cargar proyecto existente")
        messagebox.showinfo("Info", "Funcionalidad 'Cargar Proyecto' aún no implementada aquí.")

    def _regenerar_audio(self): print("Placeholder: Regenerar audio")
    def _regenerar_prompts(self): print("Placeholder: Regenerar prompts")
    def _regenerar_imagenes(self): print("Placeholder: Regenerar imágenes")
    def _regenerar_subtitulos(self): print("Placeholder: Regenerar subtítulos")
    def _preview_voice(self): print("Placeholder: Preview voice")

    # Ya tienes _add_project_to_queue, _clear_project_fields
    # Añadimos la función de encolar que faltaba
    def _encolar_proyecto_generado(self, titulo, guion_generado, voice, video_settings):
            """Añade un proyecto con guion recién generado a la cola del BatchTTSManager."""
            print(f"--- Encolando proyecto generado automáticamente: '{titulo}' ---")
            self.config(cursor="") # Restaurar cursor

            if not guion_generado:
                 messagebox.showerror("Error Interno", f"Se intentó encolar el proyecto '{titulo}' pero el guion estaba vacío.")
                 return

            try:
                # Llamar al manager para añadir el proyecto a la cola
                success = self.app.batch_tts_manager.add_project_to_queue(
                    title=titulo,
                    script=guion_generado, # El guion generado por IA
                    voice=voice,
                    video_settings=video_settings # Los settings capturados
                    # script_contexto se podría añadir aquí si se capturó
                )

                if success:
                    messagebox.showinfo("Éxito", f"Guion para '{titulo}' generado y añadido a la cola de procesamiento.")
                    self._clear_project_fields("ai") # Limpiar campos AI
                else:
                     print(f"Fallo al añadir '{titulo}' a la cola (ver logs manager).")
                     # El manager ya debería haber mostrado error

                # Actualizar el estado visual de la cola
                if hasattr(self.app, 'update_queue_status'):
                     self.app.update_queue_status() # Llama a la función de la app principal si existe

            except Exception as e:
                messagebox.showerror("Error", f"Error al añadir el proyecto '{titulo}' a la cola: {e}")
                print(f"ERROR al llamar a add_project_to_queue para '{titulo}': {e}")
                import traceback
                traceback.print_exc()

    def _add_project_to_queue(self):
        """
        Añade un nuevo proyecto a la cola de procesamiento, adaptándose
        al modo seleccionado (Manual o Generación AI).
        """
        print("--- Iniciando _add_project_to_queue ---")
        modo_seleccionado = self.app.script_creation_mode.get()
        print(f"DEBUG UI - Modo seleccionado: {modo_seleccionado}")

        # --- Variables comunes ---
        title = self.entry_title.get().strip() # Usamos el mismo título para ambos
        voice = self.app.selected_voice.get()
        script = None  # Inicializamos la variable script

        # --- Validar Título ---
        if not title:
            messagebox.showerror("Error", "Por favor, introduce un Título / Idea para el proyecto.")
            return

        # --- Recoger Ajustes de Video Comunes (Efectos, Transiciones, Audio, etc.) ---
        # (Estos se recogen independientemente del modo de guion)
        try:
            effect_settings = { # Ajustes específicos anidados de efectos
                'zoom_ratio': self.app.settings_zoom_ratio.get(),
                'zoom_quality': self.app.settings_zoom_quality.get(),
                'pan_scale_factor': self.app.settings_pan_scale_factor.get(),
                'pan_easing': self.app.settings_pan_easing.get(),
                'pan_quality': self.app.settings_pan_quality.get(),
                'kb_zoom_ratio': self.app.settings_kb_zoom_ratio.get(),
                'kb_scale_factor': self.app.settings_kb_scale_factor.get(),
                'kb_quality': self.app.settings_kb_quality.get(),
                'kb_direction': self.app.settings_kb_direction.get(),
                'overlay_opacity': self.app.settings_overlay_opacity.get(),
                'overlay_blend_mode': self.app.settings_overlay_blend_mode.get()
            }
            overlays = self.app.obtener_overlays_seleccionados()

            # Diccionario base de video_settings
            video_settings = {
                'duracion_img': self.app.duracion_img.get(),
                'fps': self.app.fps.get(),
                'aplicar_efectos': self.app.aplicar_efectos.get(),
                'aplicar_transicion': self.app.aplicar_transicion.get(),
                'tipo_transicion': self.app.tipo_transicion.get(),
                'duracion_transicion': self.app.duracion_transicion.get(),
                'aplicar_audio': self.app.aplicar_audio.get(),
                'audio_file': self.app.audio_file.get(),
                'audio_volume': self.app.audio_volume.get(),
                'aplicar_fade_in_audio': self.app.aplicar_fade_in_audio.get(),
                'duracion_fade_in_audio': self.app.duracion_fade_in_audio.get(),
                'aplicar_fade_out_audio': self.app.aplicar_fade_out_audio.get(),
                'duracion_fade_out_audio': self.app.duracion_fade_out_audio.get(),
                'aplicar_voz': self.app.aplicar_voz.get(),
                'voz_file': self.app.voz_file.get(),
                'voz_volume': self.app.voz_volume.get(),
                'aplicar_fade_in_voz': self.app.aplicar_fade_in_voz.get(),
                'duracion_fade_in_voz': self.app.duracion_fade_in_voz.get(),
                'aplicar_fade_out_voz': self.app.aplicar_fade_out_voz.get(),
                'duracion_fade_out_voz': self.app.duracion_fade_out_voz.get(),
                'aplicar_subtitulos': self.app.aplicar_subtitulos.get(),
                'color_fuente_subtitulos': self.app.settings_subtitles_font_color.get(),
                'tamano_fuente_subtitulos': self.app.settings_subtitles_font_size.get(),
                'font_name': self.app.settings_subtitles_font_name.get(),
                'use_system_font': self.app.settings_use_system_font.get(),
                'color_borde_subtitulos': self.app.settings_subtitles_stroke_color.get(),
                'grosor_borde_subtitulos': self.app.settings_subtitles_stroke_width.get(),
                'subtitles_align': self.app.settings_subtitles_align.get(),
                'subtitles_position_h': self.app.settings_subtitles_position_h.get(),
                'subtitles_position_v': self.app.settings_subtitles_position_v.get(),
                'subtitles_uppercase': self.app.subtitles_uppercase.get(),
                'subtitulos_margen': self.app.settings_subtitles_margin.get(),
                'tts_rate': self.app.tts_rate_str.get(),
                'tts_pitch': self.app.tts_pitch_str.get(),
                'image_prompt_style_id': self.image_style_map.get(self.app.selected_image_style_name.get(), 'default'),
                'image_prompt_style_name': self.app.selected_image_style_name.get(),
                'script_prompt_style_id': self.script_style_map.get(self.app.selected_script_style_name.get(), 'default'),
                'script_prompt_style_name': self.app.selected_script_style_name.get(),
                'settings': effect_settings
            }
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer parámetros de la UI: {e}")
            print(f"ERROR LEYENDO PARÁMETROS UI: {e}")
            import traceback
            traceback.print_exc()
            return

        # --- Variables específicas del modo ---
        script_content = None
        script_contexto = None
        needs_ai_generation = False # Flag para el manager

        # --- Lógica según el Modo Seleccionado ---
        if modo_seleccionado == "manual":
            print("DEBUG UI - Modo manual seleccionado.")
            # Recoger texto del guion
            script = self.txt_script.get("1.0", tk.END).strip()
            
            if not script:
                messagebox.showerror("Error", "Por favor, introduce un guion para el proyecto.")
                return
        elif modo_seleccionado == "ai":
            print("DEBUG UI - Modo AI seleccionado.")
            # El título ya lo leímos antes (usamos el mismo campo)
            script_contexto = self.txt_contexto_ai.get("1.0", tk.END).strip()
            estilo_script = self.app.selected_script_style.get()
            num_secciones = self.app.ai_num_sections.get()
            palabras_seccion = self.app.ai_words_per_section.get()

            if not script_contexto: # El contexto podría ser opcional, decide tú
                print("ADVERTENCIA UI: Contexto para IA está vacío.")
                # messagebox.showwarning("Advertencia", "El campo de contexto para IA está vacío.")
                # return # Opcional: requerir contexto

            # Añadir parámetros específicos de IA a video_settings
            video_settings['script_num_secciones'] = num_secciones
            video_settings['script_palabras_seccion'] = palabras_seccion
            # (script_contexto lo pasaremos como argumento separado al manager)

            needs_ai_generation = True
            script_content = None # No hay guion manual en este modo

        else:
            messagebox.showerror("Error", f"Modo de creación desconocido: {modo_seleccionado}")
            return

        # --- Obtener y añadir la secuencia de efectos (después de crear video_settings) ---
        try:
            if hasattr(self.app, 'obtener_secuencia_efectos_actual'):
                selected_effects_sequence = self.app.obtener_secuencia_efectos_actual()
                print(f"DEBUG UI: La función obtener_secuencia_efectos_actual() devolvió: {selected_effects_sequence}")
                video_settings['secuencia_efectos'] = selected_effects_sequence
            elif hasattr(self.app, 'obtener_secuencia_efectos'):
                print("ADVERTENCIA: Usando obtener_secuencia_efectos() en lugar de _actual()")
                selected_effects_sequence = self.app.obtener_secuencia_efectos()
                print(f"DEBUG UI: La función obtener_secuencia_efectos() devolvió: {selected_effects_sequence}")
                video_settings['secuencia_efectos'] = selected_effects_sequence
            else:
                print("ERROR: No se encontró la función para obtener la secuencia de efectos en self.app.")
                video_settings['secuencia_efectos'] = []
        except Exception as e_fx:
            print(f"ERROR obteniendo secuencia de efectos: {e_fx}")
            video_settings['secuencia_efectos'] = [] # Fallback seguro


        # --- Imprimir settings finales y llamar al Manager ---
        print("\n--- DEBUG UI: video_settings FINAL Enviado al Manager ---")
        try:
            print(json.dumps(video_settings, indent=2, default=str))
        except Exception as json_e:
            print(f"(Error al imprimir como JSON: {json_e}) -> {video_settings}")
        print("-------------------------------------------------------\n")

        # Llamar al Manager, pasando los datos correctos según el modo
        if modo_seleccionado == "ai":
            # En modo IA, generamos el guion primero y luego lo añadimos a la cola
            messagebox.showinfo("Generar Guion", 
                              "Primero debes generar el guion usando el botón 'Generar Guion'. \n\n"
                              "Una vez generado, podrás revisarlo y editarlo antes de añadir el proyecto a la cola.")
            return False
        else:
            # En modo manual, pasamos el script normalmente
            success = self.app.batch_tts_manager.add_project_to_queue(
                title=title,
                script=script,
                voice=voice,
                video_settings=video_settings
            )

        # --- Mostrar mensaje y limpiar ---
        if success:  # Ahora success puede ser un job_id o None/False
            messagebox.showinfo("Proyecto Añadido",
                            f"El proyecto '{title}' ha sido añadido a la cola.")
            # Limpiar los campos según el modo actual
            self._clear_project_fields(modo_seleccionado)
            # Actualizar el estado de la cola
            if hasattr(self.app, 'update_queue_status'):
                self.app.update_queue_status()


        # --- Modifica _clear_project_fields para limpiar según el modo ---

        
    def _clear_project_fields(self, mode=None):
        """Limpia los campos del formulario de proyecto según el modo."""
        # Si no se especifica el modo, usar el modo actual
        if mode is None:
            mode = self.app.script_creation_mode.get()
            
        self.entry_title.delete(0, tk.END)  # Limpia título en ambos modos
        
        if mode == "manual" or mode is None:
            if hasattr(self, 'txt_script'):
                self.txt_script.delete("1.0", tk.END)
                
        elif mode == "ai":
            if hasattr(self, 'txt_contexto_ai'):
                self.txt_contexto_ai.delete("1.0", tk.END)
                
        # En cualquier caso, limpiar ambos si se solicita limpiar todo
        if mode == "all":
            if hasattr(self, 'txt_script'):
                self.txt_script.delete("1.0", tk.END)
            if hasattr(self, 'txt_contexto_ai'):
                self.txt_contexto_ai.delete("1.0", tk.END)
        
    def _get_selected_project(self):
        """Obtiene el proyecto seleccionado en el Treeview."""
        selected_items = self.app.tree_queue.selection()
        if not selected_items:
            from tkinter import messagebox
            messagebox.showwarning("Selección Requerida", "Por favor, selecciona un proyecto de la cola.")
            return None
        
        selected_id = selected_items[0]
        if selected_id not in self.app.batch_tts_manager.jobs_in_gui:
            messagebox.showerror("Error", "No se pudo encontrar el proyecto seleccionado en la cola.")
            return None
        
        return selected_id, self.app.batch_tts_manager.jobs_in_gui[selected_id]
    
    def _encolar_proyecto_generado(self, titulo, guion, voice=None, video_settings=None):
        """Encola directamente un proyecto con un guion generado por IA."""
        print(f"\n--- ENCOLANDO PROYECTO GENERADO AUTOMÁTICAMENTE ---")
        print(f"Título: '{titulo}'")
        print(f"Longitud del guion: {len(guion)} caracteres")
        print(f"Voz seleccionada: {voice if voice else 'No especificada (usará la predeterminada)'}")
        print(f"Video settings: {len(video_settings) if video_settings else 0} parámetros")
        
        try:
            # Restaurar el cursor
            self.config(cursor="")
            
            # Obtener la voz seleccionada si no se proporcionó
            if voice is None:
                voice = self.app.selected_voice.get()
            
            # Obtener los video_settings si no se proporcionaron
            if video_settings is None:
                video_settings = {}
                # Aquí podríamos recopilar los settings actuales si fuera necesario
            
            # Obtener el contexto del guion
            contexto = self.txt_contexto_ai.get("1.0", tk.END).strip()
            
            # Añadir el proyecto a la cola
            job_id = self.app.batch_tts_manager.add_project_to_queue(
                title=titulo,
                script=guion,
                voice=voice,
                video_settings=video_settings,
                script_contexto=contexto
            )
            
            if job_id:
                messagebox.showinfo(
                    "Proyecto Encolado", 
                    f"El proyecto '{titulo}' ha sido añadido a la cola con ID: {job_id}.\n\n"
                    "Puedes ver su estado en la pestaña 'Cola de Proyectos'."
                )
                print(f"Proyecto '{titulo}' encolado exitosamente con ID: {job_id}")
                
                # Actualizar la interfaz
                self.app.update_queue_status()
            else:
                messagebox.showerror(
                    "Error", 
                    f"No se pudo añadir el proyecto '{titulo}' a la cola."
                )
                print(f"ERROR: No se pudo encolar el proyecto '{titulo}'")
        
        except Exception as e:
            print(f"ERROR al encolar proyecto generado '{titulo}': {e}")
            messagebox.showerror(
                "Error", 
                f"Error al encolar el proyecto '{titulo}': {str(e)}"
            )
    
    def _regenerar_audio(self):
        """Regenera el audio para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar el audio para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Audio...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_audio, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_prompts(self):
        """Regenera los prompts para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar los prompts para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Prompts...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_prompts, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_imagenes(self):
        """Regenera las imágenes para el proyecto seleccionado."""
        result = self._get_selected_project()
        if not result:
            return
        
        job_id, job_data = result
        
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Regeneración", 
                             f"¿Estás seguro de regenerar las imágenes para el proyecto '{job_data['titulo']}'?"):
            # Actualizar el estado en la GUI
            self.app.batch_tts_manager.update_job_status_gui(job_id, "Regenerando Imágenes...")
            
            # Iniciar el proceso de regeneración en un hilo separado
            import threading
            threading.Thread(target=self.app.batch_tts_manager.regenerar_imagenes, 
                           args=(job_id,), daemon=True).start()
    
    def _regenerar_subtitulos(self):
        """Regenera los subtítulos para el proyecto seleccionado."""
        # Obtener el proyecto seleccionado
        proyecto_id = self._get_selected_project()
        if not proyecto_id:
            return
        
        # Regenerar subtítulos
        self.app.batch_tts_manager.regenerar_subtitulos(proyecto_id)
        messagebox.showinfo("Regeneración", "Se ha iniciado la regeneración de subtítulos.")
        
    def _preview_voice(self):
        """Genera y reproduce una muestra de voz con los parámetros actuales."""
        if not TTS_AVAILABLE:
            messagebox.showerror("Error", "El módulo TTS no está disponible.")
            return
        
        # Obtener los valores actuales
        voice = self.app.selected_voice.get()
        rate = self.app.tts_rate_str.get()
        pitch = self.app.tts_pitch_str.get()
        
        print(f"DEBUG: Generando vista previa con voz={voice}, rate={rate}, pitch={pitch}")
        
        # Texto de prueba
        test_text = "Hola, esta es una prueba de la configuración de voz."
        
        # Crear un directorio temporal si no existe
        temp_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "temp_audio"
        temp_dir.mkdir(exist_ok=True)
        
        # Ruta para el archivo de audio temporal
        temp_audio_path = temp_dir / "preview_voice.mp3"
        
        # Guardar referencia al botón
        if not hasattr(self, 'btn_preview'):
            for widget in self.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.winfo_children():
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child.cget('text') == "Probar Voz":
                            self.btn_preview = child
                            break
        
        # Deshabilitar el botón mientras se genera el audio
        if hasattr(self, 'btn_preview'):
            self.btn_preview.config(state="disabled")
            self.btn_preview.config(text="Generando...")
            self.update_idletasks()
        
        # Función para ejecutar la generación de voz en un hilo separado
        def generate_voice_preview():
            try:
                # Ejecutar la generación de voz de forma asíncrona
                asyncio.run(text_chunk_to_speech(
                    text=test_text,
                    voice=voice,
                    output_path=str(temp_audio_path),
                    rate=rate,
                    pitch=pitch
                ))
                
                # Reproducir el audio generado
                self._play_audio(temp_audio_path)
                
                # Restaurar el botón
                if hasattr(self, 'btn_preview'):
                    self.btn_preview.config(state="normal")
                    self.btn_preview.config(text="Probar Voz")
            except Exception as e:
                # Manejar errores
                print(f"Error en la vista previa de voz: {e}")
                messagebox.showerror("Error", f"No se pudo generar la vista previa: {e}")
                if hasattr(self, 'btn_preview'):
                    self.btn_preview.config(state="normal")
                    self.btn_preview.config(text="Probar Voz")
        
        # Iniciar el hilo para la generación de voz
        threading.Thread(target=generate_voice_preview, daemon=True).start()
    
    def _play_audio(self, audio_path):
        """Reproduce un archivo de audio."""
        try:
            # Usar el reproductor adecuado según el sistema operativo
            if os.name == 'posix':  # macOS o Linux
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.run(['afplay', str(audio_path)], check=True)
                else:  # Linux
                    subprocess.run(['paplay', str(audio_path)], check=True)
            elif os.name == 'nt':  # Windows
                os.startfile(audio_path)
            else:
                print(f"No se pudo determinar el reproductor para el sistema {os.name}")
        except Exception as e:
            print(f"Error al reproducir el audio: {e}")
            messagebox.showerror("Error", f"No se pudo reproducir el audio: {e}")
    
    def _cargar_proyecto_existente(self):
        """Carga un proyecto existente desde la carpeta de proyectos."""
        from tkinter import filedialog, messagebox
        import json
        from pathlib import Path
        
        # Obtener la ruta base de proyectos
        proyectos_dir = self.app.batch_tts_manager.project_base_dir
        
        # Solicitar al usuario que seleccione una carpeta de proyecto
        proyecto_path = filedialog.askdirectory(
            title="Seleccionar Carpeta de Proyecto",
            initialdir=proyectos_dir
        )
        
        if not proyecto_path:
            return  # El usuario canceló la selección
        
        proyecto_path = Path(proyecto_path)
        settings_path = proyecto_path / "settings.json"
        guion_path = proyecto_path / "guion.txt"
        voz_path = proyecto_path / "voz.mp3"
        
        # Verificar que es una carpeta de proyecto válida
        if not settings_path.exists() or not guion_path.exists():
            messagebox.showerror(
                "Error", 
                f"La carpeta seleccionada no parece ser un proyecto válido.\n"
                f"Debe contener al menos settings.json y guion.txt."
            )
            return
        
        try:
            # Cargar configuración del proyecto
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # Leer el guion
            with open(guion_path, "r", encoding="utf-8") as f:
                script_content = f.read()
            
            # Obtener el nombre del proyecto (nombre de la carpeta)
            proyecto_nombre = proyecto_path.name
            
            # Determinar la voz utilizada
            voz = settings.get("voz", "es-MX-JorgeNeural")  # Valor por defecto si no se encuentra
            
            # Crear un trabajo para este proyecto
            job_id = self.app.batch_tts_manager.add_existing_project_to_queue(
                title=proyecto_nombre,
                script=script_content,
                project_folder=proyecto_path,
                voice=voz,
                video_settings=settings
            )
            
            if job_id:
                messagebox.showinfo(
                    "Proyecto Cargado", 
                    f"El proyecto '{proyecto_nombre}' ha sido cargado en la cola.\n"
                    f"Ahora puedes regenerar partes específicas o generar el video."
                )
                self.app.update_queue_status()
            else:
                messagebox.showerror(
                    "Error", 
                    f"No se pudo cargar el proyecto '{proyecto_nombre}'."
                )
        
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Error al cargar el proyecto: {str(e)}"
            )
            import traceback
            traceback.print_exc()