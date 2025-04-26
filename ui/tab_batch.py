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
# from datetime import datetime # Duplicado, eliminado
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
    # Asegurarse de que la ruta base del proyecto esté en sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from tts_generator import text_chunk_to_speech
    TTS_AVAILABLE = True
except ImportError as e:
    print(f"ADVERTENCIA: No se pudo importar tts_generator en tab_batch: {e}")
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
        self.script_style_map = {} # Inicializar mapeo de estilos de guion
        self.prompt_style_map = {} # Inicializar mapeo de estilos de prompt

        # Crear variables de control si no existen en app_instance (importante hacerlo aquí)
        if not hasattr(self.app, 'script_creation_mode'):
             self.app.script_creation_mode = tk.StringVar(value="manual") # Valor inicial por defecto
        if not hasattr(self.app, 'selected_voice'):
            self.app.selected_voice = tk.StringVar(value="es-MX-JorgeNeural")
        if not hasattr(self.app, 'selected_script_style'):
            self.app.selected_script_style = tk.StringVar()
        if not hasattr(self.app, 'ai_num_sections'): # Renombrado para claridad AI
            self.app.ai_num_sections = tk.IntVar(value=5)
        if not hasattr(self.app, 'ai_words_per_section'): # Renombrado para claridad AI
            self.app.ai_words_per_section = tk.IntVar(value=300)
        if not hasattr(self.app, 'selected_prompt_style'):
            self.app.selected_prompt_style = tk.StringVar(value="Cinematográfico")
        if not hasattr(self.app, 'aplicar_subtitulos'):
            self.app.aplicar_subtitulos = tk.BooleanVar(value=True)
        # Variable para Auto-Queue (importante definirla antes de _setup_widgets)
        if not hasattr(self, 'auto_queue_ai_script'):
             self.auto_queue_ai_script = tk.BooleanVar(value=False)
        # Variables TTS
        if not hasattr(self.app, 'tts_rate_value'): self.app.tts_rate_value = tk.IntVar(value=-10)
        if not hasattr(self.app, 'tts_pitch_value'): self.app.tts_pitch_value = tk.IntVar(value=-5)
        if not hasattr(self.app, 'tts_rate_str'): self.app.tts_rate_str = tk.StringVar(value="-10%")
        if not hasattr(self.app, 'tts_pitch_str'): self.app.tts_pitch_str = tk.StringVar(value="-5Hz")
        # Variable para la duración de la imagen
        if not hasattr(self.app, 'duracion_img'): self.app.duracion_img = tk.IntVar(value=5)  # Valor por defecto: 5 segundos
        # Variable para el aspect ratio
        if not hasattr(self.app, 'aspect_ratio'): self.app.aspect_ratio = tk.StringVar(value="16:9")  # Valor por defecto: 16:9
        # Variables para los prompts
        if not hasattr(self.app, 'selected_image_prompt'): self.app.selected_image_prompt = tk.StringVar(value="default")
        if not hasattr(self.app, 'selected_script_prompt'): self.app.selected_script_prompt = tk.StringVar(value="default")

        # Llamar al método que crea y posiciona los widgets
        self._setup_widgets()

    def _toggle_script_inputs(self):
        """Muestra u oculta los campos según el modo de creación de guion."""
        mode = self.app.script_creation_mode.get()
        # Asegurarse de que el contenedor exista y los frames internos también
        if not hasattr(self, 'script_container'): return
        frame_manual_exists = hasattr(self, 'frame_script_manual')
        frame_ai_exists = hasattr(self, 'frame_script_ai')

        if mode == "manual":
            # Ocultar AI, Mostrar Manual
            if frame_ai_exists: self.frame_script_ai.pack_forget()
            if frame_manual_exists: self.frame_script_manual.pack(fill="both", expand=True, padx=2, pady=2)
            if hasattr(self, 'lbl_title'): self.lbl_title.config(text="Título:")
        elif mode == "ai":
            # Ocultar Manual, Mostrar AI
            if frame_manual_exists: self.frame_script_manual.pack_forget()
            if frame_ai_exists: self.frame_script_ai.pack(fill="both", expand=True, padx=2, pady=2)
            if hasattr(self, 'lbl_title'): self.lbl_title.config(text="Título/Idea Guion:")
        else:
            # Ocultar ambos en caso de error
            if frame_manual_exists: self.frame_script_manual.pack_forget()
            if frame_ai_exists: self.frame_script_ai.pack_forget()

    def _recargar_estilos_script(self):
        """Recarga la lista de estilos de guion desde el gestor."""
        print("Recargando estilos de guion...")
        style_names = ["(No disponible)"]
        self.script_style_map = {} # Limpiar mapeo anterior
        if SCRIPT_PROMPT_MANAGER_AVAILABLE and hasattr(self.app, 'script_prompt_manager') and self.app.script_prompt_manager:
            try:
                self.app.script_prompt_manager.load_prompts()  # Recarga desde el JSON
                style_tuples = self.app.script_prompt_manager.get_style_names()
                # Filtrar tuplas vacías o inválidas si es necesario
                valid_tuples = [(id_style, name) for id_style, name in style_tuples if id_style and name]
                if valid_tuples:
                    style_names = [name for _, name in valid_tuples]
                    self.script_style_map = dict(valid_tuples)  # Mapeo id -> nombre
                    print(f"Estilos cargados: {style_names}")
                    print(f"Mapeo de estilos: {self.script_style_map}")
                else:
                     print("No se encontraron estilos válidos.")
            except Exception as e:
                print(f"Error obteniendo estilos de guion: {e}")
                messagebox.showerror("Error Estilos", f"No se pudieron cargar los estilos de guion: {e}")

        # Mantener selección si existe y es válida
        current_style_name = self.app.selected_script_style.get() if hasattr(self.app, 'selected_script_style') else ""

        # Actualizar valores del Combobox
        if hasattr(self, 'combo_estilo_script'):
             self.combo_estilo_script['values'] = style_names

             if current_style_name in style_names:
                 self.combo_estilo_script.set(current_style_name)
                 print(f"Estilo actual '{current_style_name}' mantenido.")
             elif style_names and style_names[0] != "(No disponible)":
                 self.combo_estilo_script.current(0) # Seleccionar el primero válido
                 self.app.selected_script_style.set(style_names[0]) # Actualizar variable
                 print(f"Seleccionado primer estilo disponible: {style_names[0]}")
             else:
                 self.combo_estilo_script.set("(No disponible)")
                 self.app.selected_script_style.set("") # Limpiar variable si no hay estilos
                 print("No hay estilos disponibles, combobox seteado a (No disponible).")
        else:
             print("Error: combo_estilo_script no encontrado para actualizar.")


    def _generar_guion_ai(self):
        """Genera un guion usando IA y lo gestiona (muestra o encola)."""
        print("\n--- INICIANDO GENERACIÓN DE GUION CON IA ---")
        print(f"Estado actual de guiones_pendientes: {len(self.guiones_pendientes)} guiones")

        # Obtener los datos necesarios para la generación
        titulo = self.entry_title.get().strip()
        contexto = self.txt_contexto_ai.get("1.0", tk.END).strip()
        estilo_nombre = self.app.selected_script_style.get() # Nombre legible del estilo
        num_secciones = self.app.ai_num_sections.get()
        palabras_por_seccion = self.app.ai_words_per_section.get()
        voice = self.app.selected_voice.get()

        # Buscar el ID del estilo a partir del nombre seleccionado
        # Necesitamos invertir el mapeo si 'script_style_map' es id -> nombre
        style_name_to_id_map = {name: id_style for id_style, name in self.script_style_map.items()}
        estilo_id = style_name_to_id_map.get(estilo_nombre)

        if not estilo_id:
             messagebox.showerror("Error", f"No se encontró el ID para el estilo de guion '{estilo_nombre}'. Asegúrate de que los estilos estén cargados.")
             return

        # Leer el estado del checkbox de encolado automático
        auto_queue = self.auto_queue_ai_script.get()
        print(f"Encolado automático: {'Sí' if auto_queue else 'No'}")

        # Capturar contexto antes de iniciar hilo
        titulo_capturado = titulo
        contexto_capturado = contexto
        estilo_id_capturado = estilo_id # Usamos el ID para la generación
        estilo_nombre_capturado = estilo_nombre # Guardamos el nombre para mensajes
        num_secciones_capturado = num_secciones
        palabras_por_seccion_capturado = palabras_por_seccion
        voice_capturada = voice

        print(f"Título: '{titulo_capturado}'")
        print(f"ID Estilo: '{estilo_id_capturado}' (Nombre: '{estilo_nombre_capturado}')")
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

        # Validar enteros (ya son tk.IntVar, pero una comprobación extra no hace daño)
        try:
            num_sec_int = int(num_secciones_capturado)
            pal_sec_int = int(palabras_por_seccion_capturado)
            if num_sec_int <= 0 or pal_sec_int <= 0:
                 raise ValueError("Los valores deben ser positivos.")
        except ValueError as e:
            messagebox.showerror("Error", f"Valores inválidos para secciones o palabras: {e}")
            return

        # --- Recopilar video_settings si se va a encolar automáticamente ---
        video_settings_capturados = {}
        if auto_queue:
            print("Recopilando video_settings para encolado automático...")
            try:
                # Reutiliza la lógica de _add_project_to_queue para obtener settings
                # Esto evita duplicar código y asegura consistencia
                # Necesitamos pasar un 'modo falso' para que recoja todo
                temp_settings = self._get_current_video_settings("ai") # Pide settings como si fuera AI
                if temp_settings is None:
                     # _get_current_video_settings ya muestra el error
                     return
                video_settings_capturados = temp_settings
                print("DEBUG UI: video_settings recopilados para encolado.")
            except Exception as e:
                messagebox.showerror("Error", f"Error crítico al leer parámetros de la UI necesarios para encolar: {e}")
                print(f"ERROR LEYENDO PARÁMETROS UI (Auto-Queue): {e}")
                import traceback
                traceback.print_exc()
                return # No continuar si fallan los settings y se quería encolar

        # Mostrar mensaje de progreso
        messagebox.showinfo("Generando Guion", f"Generando guion para '{titulo_capturado}' con estilo '{estilo_nombre_capturado}'... Esto puede tardar unos minutos.")
        self.update_idletasks() # Actualizar la interfaz

        # Cambiar el cursor a "espera"
        self.config(cursor="wait")

        try:
            # Importar la función de generación de guiones (asumiendo que existe)
            # Asegúrate de que ai_script_generator está accesible
            try:
                 from ai_script_generator import generar_guion
            except ImportError:
                 messagebox.showerror("Error", "No se encontró el módulo 'ai_script_generator'.")
                 self.config(cursor="")
                 return

            # Función para ejecutar en segundo plano
            def generar_en_segundo_plano(captured_title, captured_context, captured_style_id,
                                         captured_num_sec, captured_words_sec, captured_voice,
                                         captured_settings, should_auto_queue, captured_style_name):
                try:
                    print(f"DEBUG HILO: Iniciando generación para '{captured_title}', Estilo ID: {captured_style_id}, AutoQueue={should_auto_queue}")
                    # Asegúrate de que 'generar_guion' acepte el ID del estilo
                    guion = generar_guion(
                        titulo=captured_title,
                        contexto=captured_context,
                        estilo=captured_style_id, # Pasar el ID del estilo
                        num_secciones=captured_num_sec,
                        palabras_por_seccion=captured_words_sec
                    )

                    if guion:
                        print(f"DEBUG HILO: Guion generado para '{captured_title}'. Longitud: {len(guion)} caracteres.")
                        # Decidir qué callback llamar basado en el flag
                        if should_auto_queue:
                            print(f"DEBUG HILO: Llamando a _encolar_proyecto_generado para '{captured_title}'.")
                            # Pasar también el contexto original, podría ser útil guardarlo
                            self.after(0, lambda: self._encolar_proyecto_generado(
                                captured_title, guion, captured_voice, captured_settings, captured_context
                            ))
                        else:
                            print(f"DEBUG HILO: Llamando a _mostrar_guion_generado para '{captured_title}'.")
                            # Pasar también el contexto y el nombre del estilo usado
                            self.after(0, lambda: self._mostrar_guion_generado(
                                captured_title, guion, captured_context, captured_style_name
                            ))
                    else:
                        raise ValueError(f"La función generar_guion no devolvió contenido para '{captured_title}'.")
                except Exception as e:
                    print(f"DEBUG HILO: Error en generación para '{captured_title}': {e}")
                    import traceback
                    traceback.print_exc()
                    # Pasar el título original al error handler también
                    self.after(0, lambda: self._mostrar_error_generacion(captured_title, str(e)))

            # Iniciar el hilo pasando el contexto capturado
            thread = threading.Thread(target=generar_en_segundo_plano, args=(
                titulo_capturado,
                contexto_capturado,
                estilo_id_capturado, # Pasar ID
                num_secciones_capturado,
                palabras_por_seccion_capturado,
                voice_capturada,
                video_settings_capturados,
                auto_queue,
                estilo_nombre_capturado # Pasar nombre para mensajes
            ))
            thread.daemon = True # El hilo se cerrará cuando se cierre la aplicación
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la generación del guion para '{titulo_capturado}': {str(e)}")
            self.config(cursor="") # Restaurar cursor en caso de error al iniciar hilo


    def _mostrar_guion_generado(self, titulo_recibido, guion, contexto_usado=None, estilo_usado=None):
        """Gestiona un guion generado añadiéndolo a la cola de guiones pendientes."""
        self.config(cursor="") # Restaurar cursor inmediatamente

        if guion is None:
            print(f"ERROR INTERNO: _mostrar_guion_generado recibió guion None para '{titulo_recibido}'")
            self._mostrar_error_generacion(titulo_recibido, "La generación devolvió un resultado vacío.")
            return

        print(f"\n--- GUION GENERADO EXITOSAMENTE PARA '{titulo_recibido}' ---\nLongitud: {len(guion)} caracteres")
        print(f"Estilo Usado: {estilo_usado if estilo_usado else 'N/A'}")
        #print(f"Contexto Usado: {contexto_usado[:100] if contexto_usado else 'N/A'}...") # Opcional mostrar contexto
        print(f"Primeros 200 caracteres: {guion[:200]}...")
        print(f"Estado actual de guiones_pendientes antes de añadir: {len(self.guiones_pendientes)} guiones")

        try:
            # Usar el título recibido del hilo
            titulo = titulo_recibido or f"Guion_Generado_{len(self.guiones_pendientes) + 1}"
            print(f"Título final para el nuevo guion pendiente: '{titulo}'")

            # Añadir el guion a la cola de guiones pendientes
            self.guiones_pendientes.append({
                'titulo': titulo,
                'guion': guion,
                'contexto': contexto_usado, # Guardar contexto original
                'estilo': estilo_usado,     # Guardar nombre del estilo usado
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"Guion añadido a la cola de pendientes. Ahora hay {len(self.guiones_pendientes)} guiones pendientes.")

            # Actualizar el botón (o crearlo si no existe)
            self._actualizar_boton_guiones_pendientes()

            # Preguntar al usuario si desea ver el guion ahora
            print(f"Mostrando diálogo de confirmación al usuario para '{titulo}'...")
            respuesta = messagebox.askyesno(
                "Guion Generado",
                f"El guion '{titulo}' (Estilo: {estilo_usado if estilo_usado else 'N/A'}) ha sido generado.\n\n"
                f"Tienes {len(self.guiones_pendientes)} guion(es) pendiente(s) de revisar.\n\n"
                "¿Deseas cargar este guion en el editor manual ahora para revisarlo/editarlo?"
            )
            print(f"Respuesta del usuario para '{titulo}': {respuesta}")

            if respuesta:
                # Mostrar el último guion añadido (que es el que acabamos de generar)
                self._mostrar_guion_especifico(len(self.guiones_pendientes) - 1)
            # else: # No hacer nada más si dice que no, el botón ya está actualizado

            print(f"Proceso de gestión de guion generado para '{titulo}' completado.")

        except Exception as e:
            print(f"ERROR al gestionar guion generado '{titulo_recibido}': {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error Interno", f"Se generó el guion '{titulo_recibido}' pero hubo un error al añadirlo a la lista de pendientes: {e}")


    def _mostrar_guion_especifico(self, indice):
        """Muestra un guion específico de la cola de pendientes en el editor manual."""
        if not (0 <= indice < len(self.guiones_pendientes)):
             messagebox.showerror("Error", "Índice de guion pendiente inválido.")
             return

        try:
            guion_info = self.guiones_pendientes.pop(indice) # Sacarlo de la lista al mostrarlo
            print(f"Mostrando guion pendiente '{guion_info['titulo']}' (índice {indice}). {len(self.guiones_pendientes)} restantes.")

            # Cambiar al modo manual para mostrar el guion
            self.app.script_creation_mode.set("manual")
            self._toggle_script_inputs() # Actualizar la UI para mostrar campos manuales

            # Actualizar el título en la UI
            self.entry_title.delete(0, tk.END)
            self.entry_title.insert(0, guion_info['titulo'])

            # Limpiar el campo de texto manual y mostrar el guion generado
            self.txt_script.delete("1.0", tk.END)
            self.txt_script.insert("1.0", guion_info['guion'])

            # Actualizar el botón de pendientes (ahora hay uno menos)
            self._actualizar_boton_guiones_pendientes()

            # Mostrar un mensaje informativo
            messagebox.showinfo(
                "Guion Cargado",
                f"El guion '{guion_info['titulo']}' ha sido cargado en el editor manual.\n\n"
                f"Puedes revisarlo y editarlo antes de añadir el proyecto a la cola de procesamiento.\n\n"
                f"({len(self.guiones_pendientes)} guiones generados restantes en la lista de pendientes)."
            )

        except IndexError:
             messagebox.showerror("Error", "El guion seleccionado ya no está en la lista de pendientes.")
             self._actualizar_boton_guiones_pendientes() # Asegurarse de que el botón refleje el estado real
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al mostrar el guion pendiente: {e}")
            import traceback
            traceback.print_exc()


    def _actualizar_boton_guiones_pendientes(self):
        """Actualiza o crea/destruye el botón de guiones pendientes."""
        num_pendientes = len(self.guiones_pendientes)

        if num_pendientes > 0:
            button_text = f"Ver Guiones Pendientes ({num_pendientes})"
            # Si ya existe el botón, actualizar su texto y asegurarse de que sea visible
            if hasattr(self, 'btn_guiones_pendientes') and self.btn_guiones_pendientes.winfo_exists():
                self.btn_guiones_pendientes.config(text=button_text)
                # Asegurarse de que esté empaquetado correctamente (podría haberse quitado)
                # Lo colocamos después del frame de entrada
                if hasattr(self, 'frame_input'):
                     self.btn_guiones_pendientes.pack(after=self.frame_input, side="top", padx=10, pady=5, fill="x")
                else: # Fallback si frame_input no existe aún
                     self.btn_guiones_pendientes.pack(side="top", padx=10, pady=5, fill="x")

            else:
                # Crear el botón si no existe (o fue destruido)
                # Necesitamos saber dónde colocarlo, idealmente después de la sección de entrada
                parent_widget = self.scroll_frame if hasattr(self, 'scroll_frame') else self # Usar scroll_frame si existe

                self.btn_guiones_pendientes = ttk.Button(
                    parent_widget, # Añadir al frame scrolleable
                    text=button_text,
                    command=self._mostrar_menu_guiones_pendientes,
                    style="Accent.TButton" # Usar un estilo que resalte
                )
                # Empaquetarlo después del frame de entrada si es posible
                if hasattr(self, 'frame_input'):
                     self.btn_guiones_pendientes.pack(after=self.frame_input, side="top", padx=10, pady=5, fill="x")
                else: # Fallback
                     self.btn_guiones_pendientes.pack(side="top", padx=10, pady=5, fill="x")

        else:
            # Si no hay pendientes, destruir el botón si existe
            if hasattr(self, 'btn_guiones_pendientes') and self.btn_guiones_pendientes.winfo_exists():
                self.btn_guiones_pendientes.pack_forget()
                self.btn_guiones_pendientes.destroy()
                # Eliminar el atributo para que se cree de nuevo si es necesario
                delattr(self, 'btn_guiones_pendientes')


    def _mostrar_menu_guiones_pendientes(self):
        """Muestra un menú con los guiones pendientes de revisar."""
        if not self.guiones_pendientes:
            messagebox.showinfo("Guiones Pendientes", "No hay guiones pendientes de revisar.")
            # Asegurarse de que el botón desaparezca si se llega aquí por alguna razón
            if hasattr(self, 'btn_guiones_pendientes') and self.btn_guiones_pendientes.winfo_exists():
                 self.btn_guiones_pendientes.pack_forget()
                 self.btn_guiones_pendientes.destroy()
                 delattr(self, 'btn_guiones_pendientes')
            return

        # Crear un menú emergente
        menu = tk.Menu(self, tearoff=0)

        # Añadir una opción para cada guion pendiente
        for i, guion_info in enumerate(self.guiones_pendientes):
            menu.add_command(
                label=f"{i+1}. '{guion_info['titulo']}' (Estilo: {guion_info.get('estilo', 'N/A')}, {guion_info['fecha']})",
                # Usar lambda idx=i para capturar el índice correcto en el momento de la creación
                command=lambda idx=i: self._mostrar_guion_especifico(idx)
            )

        # Añadir opción para limpiar toda la lista
        menu.add_separator()
        menu.add_command(label="Descartar Todos", command=self._limpiar_guiones_pendientes)

        # Mostrar el menú cerca del botón que lo invocó
        if hasattr(self, 'btn_guiones_pendientes') and self.btn_guiones_pendientes.winfo_exists():
             button_x = self.btn_guiones_pendientes.winfo_rootx()
             button_y = self.btn_guiones_pendientes.winfo_rooty() + self.btn_guiones_pendientes.winfo_height()
             try:
                  menu.tk_popup(button_x, button_y)
             finally:
                  menu.grab_release()
        else:
            # Fallback: mostrar en la posición del ratón si el botón no existe
             try:
                  menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
             finally:
                  menu.grab_release()

    def _limpiar_guiones_pendientes(self):
        """Limpia la lista de guiones pendientes tras confirmación."""
        if not self.guiones_pendientes:
             messagebox.showinfo("Limpiar Guiones", "La lista de guiones pendientes ya está vacía.")
             return

        if messagebox.askyesno("Descartar Guiones", f"¿Estás seguro de que deseas descartar los {len(self.guiones_pendientes)} guiones generados pendientes? Esta acción no se puede deshacer."):
            print(f"Limpiando {len(self.guiones_pendientes)} guiones pendientes.")
            self.guiones_pendientes = []
            # Ocultar/destruir el botón
            self._actualizar_boton_guiones_pendientes()


    def _mostrar_error_generacion(self, titulo_fallido, error_msg):
        """Muestra un mensaje de error si la generación del guion falla."""
        print(f"\n--- ERROR AL GENERAR GUION PARA '{titulo_fallido}' ---\n{error_msg}")
        self.config(cursor="") # Restaurar cursor siempre
        try:
            messagebox.showerror("Error de Generación", f"Error al generar el guion para '{titulo_fallido}':\n\n{error_msg}")
            print(f"Mensaje de error mostrado al usuario para '{titulo_fallido}'.")
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudo mostrar el mensaje de error de generación: {e}")

    # --- Métodos de configuración de la UI ---

    def _setup_widgets(self):
        """Configura todos los widgets de la pestaña usando un Canvas para scroll."""
        # --- Scroll principal para toda la pestaña ---
        main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        self.scroll_frame = ttk.Frame(main_canvas, style="Card.TFrame") # Frame interior que contendrá TODO

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(
                scrollregion=main_canvas.bbox("all")
            )
        )
        main_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # Permitir scroll con rueda del ratón sobre el canvas y el frame interior
        def _on_mousewheel(event):
             # Ajustar la velocidad del scroll si es necesario
             scroll_speed = int(-1 * (event.delta / 60))
             main_canvas.yview_scroll(scroll_speed, "units")

        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.scroll_frame.bind_all("<MouseWheel>", _on_mousewheel) # También en el frame

        # --- Sección de Entrada (Dentro de scroll_frame) ---
        self.frame_input = ttk.LabelFrame(self.scroll_frame, text="Nuevo Proyecto", style="Card.TFrame")
        self.frame_input.pack(fill="both", expand=True, padx=10, pady=10) # Cambiado a fill="both", expand=True

        # Configurar columnas para el frame de entrada
        self.frame_input.columnconfigure(1, weight=1) # Columna para Título/Guion/Contexto
        self.frame_input.columnconfigure(0, weight=0)

        # --- Fila 0: Modo ---
        frame_mode = ttk.Frame(self.frame_input)
        frame_mode.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 10), sticky="w")
        lbl_mode = ttk.Label(frame_mode, text="Método Guion:")
        lbl_mode.pack(side="left", padx=(0, 5))
        rb_manual = ttk.Radiobutton(frame_mode, text="Manual",
                                    variable=self.app.script_creation_mode, value="manual",
                                    command=self._toggle_script_inputs, style="Toolbutton")
        rb_manual.pack(side="left", padx=3)
        rb_ai = ttk.Radiobutton(frame_mode, text="Generar con IA",
                                variable=self.app.script_creation_mode, value="ai",
                                command=self._toggle_script_inputs, style="Toolbutton")
        rb_ai.pack(side="left", padx=3)

        # --- Fila 1: Título ---
        self.lbl_title = ttk.Label(self.frame_input, text="Título:") # Texto se actualiza en _toggle
        self.lbl_title.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_title = ttk.Entry(self.frame_input)
        self.entry_title.grid(row=1, column=1, padx=5, pady=5, sticky="ew") # sticky="ew" para expandir

        # --- Fila 2: Contenedor para Guion Manual o Parámetros AI ---
        self.script_container = ttk.Frame(self.frame_input)
        self.script_container.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew") # sticky="nsew" para expandir
        self.frame_input.rowconfigure(2, weight=1)
        self.script_container.columnconfigure(0, weight=1) # Permitir que el contenido crezca

        # --- Frame Guion Manual (Dentro de script_container) ---
        self.frame_script_manual = ttk.Frame(self.script_container)
        # NO USAR pack/grid aquí, se controla en _toggle_script_inputs
        text_frame = ttk.Frame(self.frame_script_manual)
        text_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.txt_script = tk.Text(text_frame, wrap="word", height=10, undo=True,
                                 bg="#23272e", fg="#f5f6fa", insertbackground="#f5f6fa", relief="sunken", borderwidth=1)
        scrollbar_script = ttk.Scrollbar(text_frame, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar_script.set)
        self.txt_script.pack(side="left", fill="both", expand=True)
        scrollbar_script.pack(side="right", fill="y")


        # --- Frame Parámetros AI (Dentro de script_container) ---
        self.frame_script_ai = ttk.Frame(self.script_container)
        # NO USAR pack/grid aquí

        # Sub-Frame para Contexto y Estilo de Guion
        ai_top_frame = ttk.Frame(self.frame_script_ai)
        ai_top_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        # Contexto AI (dentro de ai_top_frame)
        contexto_frame = ttk.LabelFrame(ai_top_frame, text="Contexto/Notas para Generación IA")
        contexto_frame.pack(side="top", fill="both", expand=True, padx=5, pady=(5, 2))
        self.txt_contexto_ai = tk.Text(contexto_frame, wrap="word", height=8, width=40, undo=True,
                                     bg="#23272e", fg="#f5f6fa", insertbackground="#f5f6fa", relief="sunken", borderwidth=1)
        scrollbar_contexto = ttk.Scrollbar(contexto_frame, orient="vertical", command=self.txt_contexto_ai.yview)
        self.txt_contexto_ai.configure(yscrollcommand=scrollbar_contexto.set)
        self.txt_contexto_ai.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar_contexto.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.txt_contexto_ai.insert("1.0", "Escribe aquí el contexto o notas para guiar la generación del guion...")

        # Estilo Guion (debajo del contexto, dentro de ai_top_frame)
        style_frame = ttk.Frame(ai_top_frame)
        style_frame.pack(side="top", fill="x", padx=5, pady=(3, 5))
        lbl_estilo_script = ttk.Label(style_frame, text="Estilo Guion:")
        lbl_estilo_script.pack(side="left", padx=5, pady=2)
        self.combo_estilo_script = ttk.Combobox(style_frame, textvariable=self.app.selected_script_style,
                                                state="readonly", width=25) # Ancho ajustado
        self.combo_estilo_script.pack(side="left", fill="x", expand=True, padx=5, pady=2)
        btn_recargar_estilos = ttk.Button(style_frame, text="🔄", command=self._recargar_estilos_script, width=3, style="Toolbutton") # Botón pequeño
        btn_recargar_estilos.pack(side="left", padx=(0, 5), pady=2)
        self._recargar_estilos_script() # Cargar estilos al inicio

        # Sub-Frame para Opciones Adicionales (Secciones, Palabras, Estilo Imagen, Auto-Queue)
        ai_options_frame = ttk.Frame(self.frame_script_ai)
        ai_options_frame.pack(side="top", fill="x", padx=0, pady=0)

        # Nº Secciones y Palabras/Sección (en una línea)
        sections_words_frame = ttk.Frame(ai_options_frame)
        sections_words_frame.pack(side="top", fill="x", padx=5, pady=2)

        lbl_num_sec = ttk.Label(sections_words_frame, text="Nº Secciones:")
        lbl_num_sec.pack(side="left", padx=(5, 0), pady=2)
        spin_num_sec = ttk.Spinbox(sections_words_frame, from_=3, to=15, increment=1,
                                   textvariable=self.app.ai_num_sections, width=5)
        spin_num_sec.pack(side="left", padx=(2, 10), pady=2)

        lbl_pal_sec = ttk.Label(sections_words_frame, text="Palabras/Sección:")
        lbl_pal_sec.pack(side="left", padx=(5, 0), pady=2)
        spin_pal_sec = ttk.Spinbox(sections_words_frame, from_=100, to=800, increment=50,
                                   textvariable=self.app.ai_words_per_section, width=7)
        spin_pal_sec.pack(side="left", padx=(2, 5), pady=2)

        # Estilo Imágenes
        images_style_frame = ttk.Frame(ai_options_frame)
        images_style_frame.pack(side="top", fill="x", padx=5, pady=2)
        lbl_prompt_style = ttk.Label(images_style_frame, text="Estilo Imágenes:")
        lbl_prompt_style.pack(side="left", padx=5, pady=2)
        prompt_styles = [("default", "Cinematográfico")] # Valor por defecto
        if PROMPT_MANAGER_AVAILABLE:
            try:
                prompt_manager = PromptManager()
                prompt_styles = prompt_manager.get_prompt_names()
            except Exception as e:
                print(f"Error obteniendo estilos de prompt: {e}")
        prompt_style_values = [name for _, name in prompt_styles]
        prompt_style_ids = [id_style for id_style, _ in prompt_styles]
        self.prompt_style_map = dict(zip(prompt_style_values, prompt_style_ids)) # nombre -> id
        self.prompt_style_dropdown = ttk.Combobox(images_style_frame, textvariable=self.app.selected_prompt_style,
                                                  values=prompt_style_values, state="readonly", width=25) # Ancho ajustado
        self.prompt_style_dropdown.pack(side="left", fill="x", expand=True, padx=5, pady=2)
        # Set default if current value is not in list or if list is empty
        if self.app.selected_prompt_style.get() not in prompt_style_values:
            if prompt_style_values:
                self.prompt_style_dropdown.current(0)
                self.app.selected_prompt_style.set(prompt_style_values[0])
            else:
                self.app.selected_prompt_style.set("") # o un valor por defecto

        # Auto-Queue Checkbox
        auto_queue_frame = ttk.Frame(ai_options_frame)
        auto_queue_frame.pack(side="top", fill="x", padx=5, pady=2)
        chk_auto_queue = ttk.Checkbutton(auto_queue_frame, text="Encolar automáticamente al generar",
                                         variable=self.auto_queue_ai_script, style="Switch.TCheckbutton")
        chk_auto_queue.pack(side="left", padx=5, pady=2)

        # Botón Generar Guion (Sólo en modo AI)
        btn_generar_guion = ttk.Button(self.frame_script_ai, text="Generar Guion", command=self._generar_guion_ai, style="Accent.TButton")
        btn_generar_guion.pack(side="top", padx=5, pady=10)


        # --- Fila 3: Voz y Ajustes TTS (Común a ambos modos) ---
        voice_frame = ttk.LabelFrame(self.frame_input, text="Ajustes de Voz", style="Card.TFrame")
        voice_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Selector de Voz
        voice_select_frame = ttk.Frame(voice_frame)
        voice_select_frame.pack(fill="x", padx=5, pady=5)
        lbl_voice = ttk.Label(voice_select_frame, text="Voz:")
        lbl_voice.pack(side="left", padx=5)
        # Lista de voces, idealmente debería cargarse dinámicamente
        voces = [ "es-EC-LuisNeural", "es-ES-ElviraNeural", "es-MX-DaliaNeural",
                  "es-AR-ElenaNeural", "es-CO-GonzaloNeural", "es-CL-CatalinaNeural",
                  "es-MX-JorgeNeural"] # Ejemplo
        voice_combo = ttk.Combobox(voice_select_frame, textvariable=self.app.selected_voice, values=voces, state="readonly", width=25)
        voice_combo.pack(side="left", fill="x", expand=True, padx=5)
        # Asegurarse de que el valor inicial esté en la lista
        if self.app.selected_voice.get() not in voces and voces:
            self.app.selected_voice.set(voces[0])


        # Controles Rate/Pitch
        tts_controls_frame = ttk.Frame(voice_frame)
        tts_controls_frame.pack(fill="x", padx=5, pady=5)
        tts_controls_frame.columnconfigure(1, weight=1) # Hacer que las escalas se expandan

        # Rate
        lbl_rate = ttk.Label(tts_controls_frame, text="Velocidad:")
        lbl_rate.grid(row=0, column=0, padx=(5,0), pady=2, sticky="w")
        scale_rate = ttk.Scale(tts_controls_frame, from_=-50, to=50, orient="horizontal",
                               variable=self.app.tts_rate_value, length=200) # Longitud ajustada
        scale_rate.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        lbl_rate_value = ttk.Label(tts_controls_frame, text=self.app.tts_rate_str.get(), width=6, anchor="e")
        lbl_rate_value.grid(row=0, column=2, padx=(0,5), pady=2, sticky="e")

        # Pitch
        lbl_pitch = ttk.Label(tts_controls_frame, text="Tono:")
        lbl_pitch.grid(row=1, column=0, padx=(5,0), pady=2, sticky="w")
        scale_pitch = ttk.Scale(tts_controls_frame, from_=-50, to=50, orient="horizontal",
                                variable=self.app.tts_pitch_value, length=200)
        scale_pitch.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        lbl_pitch_value = ttk.Label(tts_controls_frame, text=self.app.tts_pitch_str.get(), width=6, anchor="e")
        lbl_pitch_value.grid(row=1, column=2, padx=(0,5), pady=2, sticky="e")

        # Botón de vista previa TTS
        self.btn_preview = ttk.Button(tts_controls_frame, text="Probar Voz", command=self._preview_voice, style="Secondary.TButton", width=10)
        self.btn_preview.grid(row=0, rowspan=2, column=3, padx=10, pady=2, sticky="e")

        # Funciones para actualizar etiquetas Rate/Pitch
        def update_rate_str(*args):
            rate_val = self.app.tts_rate_value.get()
            text = f"+{rate_val}%" if rate_val >= 0 else f"{rate_val}%"
            lbl_rate_value.config(text=text)
            self.app.tts_rate_str.set(text)

        def update_pitch_str(*args):
            pitch_val = self.app.tts_pitch_value.get()
            text = f"+{pitch_val}Hz" if pitch_val >= 0 else f"{pitch_val}Hz"
            lbl_pitch_value.config(text=text)
            self.app.tts_pitch_str.set(text)

        # Vincular variables a funciones de actualización
        self.app.tts_rate_value.trace_add("write", update_rate_str)
        self.app.tts_pitch_value.trace_add("write", update_pitch_str)

        # Inicializar etiquetas
        update_rate_str(); update_pitch_str()

        # --- Fila 4: Ajustes de Video ---
        video_frame = ttk.LabelFrame(self.frame_input, text="Ajustes de Video", style="Card.TFrame")
        video_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Duración de la imagen
        duration_frame = ttk.Frame(video_frame)
        duration_frame.pack(fill="x", padx=5, pady=5)
        lbl_duration = ttk.Label(duration_frame, text="Duración de la imagen (segundos):")
        lbl_duration.pack(side="left", padx=5)
        spin_duration = ttk.Spinbox(duration_frame, from_=1, to=30, increment=1,
                                  textvariable=self.app.duracion_img, width=5)
        spin_duration.pack(side="left", padx=5)

        # Aspect Ratio
        aspect_frame = ttk.Frame(video_frame)
        aspect_frame.pack(fill="x", padx=5, pady=5)
        lbl_aspect = ttk.Label(aspect_frame, text="Aspect Ratio:")
        lbl_aspect.pack(side="left", padx=5)
        rb_16_9 = ttk.Radiobutton(aspect_frame, text="16:9 (Horizontal)",
                                 variable=self.app.aspect_ratio, value="16:9")
        rb_16_9.pack(side="left", padx=5)
        rb_9_16 = ttk.Radiobutton(aspect_frame, text="9:16 (Vertical)",
                                 variable=self.app.aspect_ratio, value="9:16")
        rb_9_16.pack(side="left", padx=5)

        # Prompts de Imágenes
        image_prompt_frame = ttk.Frame(video_frame)
        image_prompt_frame.pack(fill="x", padx=5, pady=5)
        lbl_image_prompt = ttk.Label(image_prompt_frame, text="Estilo de Imágenes:")
        lbl_image_prompt.pack(side="left", padx=5)
        self.combo_image_prompt = ttk.Combobox(image_prompt_frame, textvariable=self.app.selected_image_prompt,
                                             state="readonly", width=25)
        self.combo_image_prompt.pack(side="left", fill="x", expand=True, padx=5)
        btn_reload_image_prompts = ttk.Button(image_prompt_frame, text="🔄", 
                                            command=self._recargar_prompts_imagenes, width=3, style="Toolbutton")
        btn_reload_image_prompts.pack(side="left", padx=(0, 5))

        # Prompts de Scripts
        script_prompt_frame = ttk.Frame(video_frame)
        script_prompt_frame.pack(fill="x", padx=5, pady=5)
        lbl_script_prompt = ttk.Label(script_prompt_frame, text="Estilo de Script:")
        lbl_script_prompt.pack(side="left", padx=5)
        self.combo_script_prompt = ttk.Combobox(script_prompt_frame, textvariable=self.app.selected_script_prompt,
                                              state="readonly", width=25)
        self.combo_script_prompt.pack(side="left", fill="x", expand=True, padx=5)
        btn_reload_script_prompts = ttk.Button(script_prompt_frame, text="🔄", 
                                             command=self._recargar_prompts_scripts, width=3, style="Toolbutton")
        btn_reload_script_prompts.pack(side="left", padx=(0, 5))

        # --- Fila 5: Botones de Acción Principales (Añadir / Limpiar) ---
        frame_buttons = ttk.Frame(self.frame_input)
        frame_buttons.grid(row=5, column=0, columnspan=2, padx=5, pady=10, sticky="e")
        btn_clear = ttk.Button(frame_buttons, text="Limpiar Campos", command=self._clear_project_fields, style="Secondary.TButton")
        btn_clear.pack(side="left", padx=(0, 5)) # Cambiado a left
        # Este botón SÓLO añade si está en modo manual. En AI, se usa el botón "Generar Guion"
        self.btn_add_queue = ttk.Button(frame_buttons, text="Añadir a la Cola (Manual)", command=self._add_project_to_queue, style="Action.TButton")
        self.btn_add_queue.pack(side="left", padx=5) # Cambiado a left

        # --- Sección de Cola (Debajo del frame de entrada, dentro de scroll_frame) ---
        frame_queue = ttk.LabelFrame(self.scroll_frame, text="Cola de Procesamiento", style="Card.TFrame")
        frame_queue.pack(fill="both", expand=True, padx=10, pady=(0, 10)) # Cambiado a fill="both", expand=True

        # Treeview para la cola
        frame_treeview = ttk.Frame(frame_queue)
        frame_treeview.pack(fill="both", expand=True, pady=(5, 5)) # fill="both", expand=True
        self.app.tree_queue = ttk.Treeview(frame_treeview, columns=("titulo", "estado", "tiempo"), show="headings", height=8) # Altura ajustada
        self.app.tree_queue.heading("titulo", text="Título del Proyecto"); self.app.tree_queue.column("titulo", width=400, stretch=tk.YES)
        self.app.tree_queue.heading("estado", text="Estado"); self.app.tree_queue.column("estado", width=180, anchor="center")
        self.app.tree_queue.heading("tiempo", text="Tiempo"); self.app.tree_queue.column("tiempo", width=100, anchor="center")
        scrollbar_queue = ttk.Scrollbar(frame_treeview, orient="vertical", command=self.app.tree_queue.yview)
        self.app.tree_queue.configure(yscrollcommand=scrollbar_queue.set)
        self.app.tree_queue.pack(side="left", fill="both", expand=True)
        scrollbar_queue.pack(side="right", fill="y")

        # Frame para botones de la cola
        frame_botones_cola = ttk.Frame(frame_queue)
        frame_botones_cola.pack(fill="x", pady=(5, 5))

        # Botones lado izquierdo: Cargar, Regenerar
        frame_botones_izquierda = ttk.Frame(frame_botones_cola)
        frame_botones_izquierda.pack(side="left", padx=5, pady=5)
        btn_cargar_proyecto = ttk.Button(frame_botones_izquierda, text="Cargar Proyecto Existente", command=self._cargar_proyecto_existente, style="Secondary.TButton")
        btn_cargar_proyecto.pack(side="top", anchor="w", pady=(0,5))

        frame_regeneracion = ttk.Frame(frame_botones_izquierda)
        frame_regeneracion.pack(side="top", anchor="w")
        lbl_regenerar = ttk.Label(frame_regeneracion, text="Regenerar:")
        lbl_regenerar.pack(side="left", padx=(0, 5))
        btn_regenerar_audio = ttk.Button(frame_regeneracion, text="Audio", command=self._regenerar_audio, style="Secondary.TButton", width=8); btn_regenerar_audio.pack(side="left", padx=2)
        btn_regenerar_prompts = ttk.Button(frame_regeneracion, text="Prompts", command=self._regenerar_prompts, style="Secondary.TButton", width=8); btn_regenerar_prompts.pack(side="left", padx=2)
        btn_regenerar_imagenes = ttk.Button(frame_regeneracion, text="Imágenes", command=self._regenerar_imagenes, style="Secondary.TButton", width=9); btn_regenerar_imagenes.pack(side="left", padx=2)
        btn_regenerar_subtitulos = ttk.Button(frame_regeneracion, text="Subtítulos", command=self._regenerar_subtitulos, style="Secondary.TButton", width=10); btn_regenerar_subtitulos.pack(side="left", padx=2)


        # Botón lado derecho: Generar Video
        frame_botones_derecha = ttk.Frame(frame_botones_cola)
        frame_botones_derecha.pack(side="right", padx=5, pady=5)
        btn_generate_video = ttk.Button(frame_botones_derecha, text="Generar Vídeo Seleccionado", command=self.app.trigger_video_generation_for_selected, style="Action.TButton")
        btn_generate_video.pack() # Simple pack a la derecha

        # --- Final ---
        # Asignar treeview al manager (si batch_tts_manager existe en app)
        if hasattr(self.app, 'batch_tts_manager') and self.app.batch_tts_manager:
            self.app.batch_tts_manager.tree_queue = self.app.tree_queue
        else:
            print("ADVERTENCIA: self.app.batch_tts_manager no encontrado al asignar tree_queue.")

        # Llamada inicial para mostrar/ocultar según el modo por defecto
        self._toggle_script_inputs()
        # Llamada inicial para el botón de pendientes (si hay alguno al inicio)
        self._actualizar_boton_guiones_pendientes()

    # --- Métodos de Acción ---

    def _get_current_video_settings(self, mode):
         """Recopila los video_settings actuales de la UI principal. Separa lógica."""
         print(f"DEBUG UI: Recopilando video_settings para modo '{mode}'")
         # Verificar que los atributos necesarios existen en self.app
         required_attrs = [
             'duracion_img', 'fps', 'aplicar_efectos', 'aplicar_transicion',
             'tipo_transicion', 'duracion_transicion', 'aplicar_fade_in', 'duracion_fade_in',
             'aplicar_fade_out', 'duracion_fade_out', 'opacidad_overlay',
             'aplicar_musica', 'archivo_musica', 'volumen_musica',
             'aplicar_fade_in_musica', 'duracion_fade_in_musica',
             'aplicar_fade_out_musica', 'duracion_fade_out_musica', 'volumen_voz',
             'aplicar_fade_in_voz', 'duracion_fade_in_voz', 'aplicar_fade_out_voz',
             'duracion_fade_out_voz', 'aplicar_subtitulos',
             'settings_subtitles_font_color', 'settings_subtitles_font_size',
             'settings_subtitles_font_name', 'settings_use_system_font',
             'settings_subtitles_stroke_color', 'settings_subtitles_stroke_width',
             'settings_subtitles_align', 'settings_subtitles_position_h',
             'settings_subtitles_position_v', 'subtitles_uppercase',
             'settings_subtitles_margin', 'tts_rate_str', 'tts_pitch_str',
             # Effect settings
             'settings_zoom_ratio', 'settings_zoom_quality', 'settings_pan_scale_factor',
             'settings_pan_easing', 'settings_pan_quality', 'settings_kb_zoom_ratio',
             'settings_kb_scale_factor', 'settings_kb_quality', 'settings_kb_direction',
             'settings_overlay_opacity', 'settings_overlay_blend_mode',
             # Funciones requeridas
             'obtener_overlays_seleccionados', 'obtener_secuencia_efectos_actual'
         ]
         missing_attrs = [attr for attr in required_attrs if not hasattr(self.app, attr)]
         if missing_attrs:
              error_msg = f"Faltan atributos/métodos necesarios en 'self.app': {', '.join(missing_attrs)}"
              print(f"ERROR: {error_msg}")
              messagebox.showerror("Error de Configuración", error_msg)
              return None

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
             selected_effects_sequence = self.app.obtener_secuencia_efectos_actual()

             # Diccionario base de video_settings
             video_settings = {
                 'duracion_img': self.app.duracion_img.get(),
                 'fps': self.app.fps.get(),
                 'aplicar_efectos': self.app.aplicar_efectos.get(),
                 'secuencia_efectos': selected_effects_sequence, # Añadido aquí
                 'aplicar_transicion': self.app.aplicar_transicion.get(),
                 'tipo_transicion': self.app.tipo_transicion.get(),
                 'duracion_transicion': self.app.duracion_transicion.get(),
                 'aplicar_fade_in': self.app.aplicar_fade_in.get(),
                 'duracion_fade_in': self.app.duracion_fade_in.get(),
                 'aplicar_fade_out': self.app.aplicar_fade_out.get(),
                 'duracion_fade_out': self.app.duracion_fade_out.get(),
                 'aplicar_overlay': bool(overlays),
                 'archivos_overlay': [str(Path(ov).resolve()) for ov in overlays] if overlays else None,
                 'opacidad_overlay': self.app.opacidad_overlay.get(),
                 'aplicar_musica': self.app.aplicar_musica.get(),
                 'archivo_musica': str(Path(self.app.archivo_musica.get()).resolve()) if self.app.aplicar_musica.get() and self.app.archivo_musica.get() else None,
                 'volumen_musica': self.app.volumen_musica.get(),
                 'aplicar_fade_in_musica': self.app.aplicar_fade_in_musica.get(),
                 'duracion_fade_in_musica': self.app.duracion_fade_in_musica.get(),
                 'aplicar_fade_out_musica': self.app.aplicar_fade_out_musica.get(),
                 'duracion_fade_out_musica': self.app.duracion_fade_out_musica.get(),
                 'volumen_voz': self.app.volumen_voz.get(),
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
                 # Estilo de imágenes (obtenido del dropdown de esta pestaña)
                 'estilo_imagenes': self.prompt_style_map.get(self.app.selected_prompt_style.get(), 'default'), # Usar mapeo nombre->id
                 'nombre_estilo': self.app.selected_prompt_style.get(), # Nombre legible
                 'settings': effect_settings, # Anidar ajustes de efectos
                 # Añadir el aspect ratio seleccionado
                 'aspect_ratio': self.app.aspect_ratio.get()
             }

             # Añadir parámetros específicos de IA SOLO si estamos en modo AI
             if mode == "ai":
                  # Asegúrate de que estas variables existan en self.app o self
                  # y que los mapeos estén actualizados
                  script_style_name = self.app.selected_script_style.get()
                  style_name_to_id_map = {name: id_style for id_style, name in self.script_style_map.items()}
                  script_style_id = style_name_to_id_map.get(script_style_name)

                  video_settings['script_style'] = script_style_id # ID del estilo de guion
                  video_settings['script_style_name'] = script_style_name # Nombre del estilo de guion
                  video_settings['script_num_secciones'] = self.app.ai_num_sections.get()
                  video_settings['script_palabras_seccion'] = self.app.ai_words_per_section.get()

             # Imprimir para depuración ANTES de devolver
             # print("\n--- DEBUG UI: video_settings Recopilados ---")
             # try:
             #      print(json.dumps(video_settings, indent=2, default=str))
             # except Exception as json_e:
             #      print(f"(Error al imprimir como JSON: {json_e}) -> {video_settings}")
             # print("------------------------------------------\n")

             return video_settings

         except Exception as e:
             messagebox.showerror("Error", f"Error al leer parámetros de la UI: {e}")
             print(f"ERROR LEYENDO PARÁMETROS UI: {e}")
             import traceback
             traceback.print_exc()
             return None # Devuelve None si hay error

    def _add_project_to_queue(self):
        """
        Añade un NUEVO proyecto MANUAL a la cola de procesamiento.
        Para proyectos AI, se usa _generar_guion_ai y opcionalmente _encolar_proyecto_generado.
        """
        print("--- Iniciando _add_project_to_queue (SOLO MODO MANUAL) ---")
        modo_seleccionado = self.app.script_creation_mode.get()

        if modo_seleccionado != "manual":
             messagebox.showwarning("Acción Incorrecta", "Para generar un guion con IA y añadirlo, usa el botón 'Generar Guion'.\n\nEste botón 'Añadir a la Cola' es solo para guiones introducidos manualmente.")
             return

        # --- Variables comunes ---
        title = self.entry_title.get().strip()
        voice = self.app.selected_voice.get() # Voz seleccionada en esta pestaña
        script = self.txt_script.get("1.0", tk.END).strip()

        # --- Validaciones ---
        if not title:
            messagebox.showerror("Error", "Por favor, introduce un Título para el proyecto.")
            return
        if not script:
            messagebox.showerror("Error", "Por favor, introduce un guion para el proyecto.")
            return
        if not hasattr(self.app, 'batch_tts_manager') or not self.app.batch_tts_manager:
             messagebox.showerror("Error Crítico", "El gestor de cola (BatchTTSManager) no está disponible.")
             return

        # --- Recoger Ajustes de Video ---
        video_settings = self._get_current_video_settings("manual") # Obtener settings para modo manual
        if video_settings is None:
            return # Error ya mostrado por _get_current_video_settings

        # --- Llamar al Manager ---
        print(f"Añadiendo proyecto MANUAL '{title}' a la cola...")
        # Asegúrate de que add_project_to_queue maneja 'script_contexto=None' si no es AI
        success = self.app.batch_tts_manager.add_project_to_queue(
            title=title,
            script=script,
            voice=voice,
            video_settings=video_settings,
            script_contexto=None # No hay contexto en modo manual
            # needs_ai_generation=False # El manager debería deducirlo o no necesitarlo
        )

        # --- Mostrar mensaje y limpiar ---
        if success:
            messagebox.showinfo("Proyecto Añadido",
                                f"El proyecto manual '{title}' ha sido añadido a la cola.")
            self._clear_project_fields("manual") # Limpiar campos manuales
            if hasattr(self.app, 'update_queue_status'):
                self.app.update_queue_status()
        # else: El manager ya debería haber mostrado el error si falló

    def _clear_project_fields(self, mode=None):
        """Limpia los campos del formulario según el modo o todos."""
        # Si no se especifica el modo, limpiar todo lo posible
        if mode is None:
            mode = "all" # Limpiar todo por defecto si no se especifica

        print(f"Limpiando campos para modo: {mode}")

        # Limpiar título siempre
        if hasattr(self, 'entry_title'):
             self.entry_title.delete(0, tk.END)

        # Limpiar campos manuales
        if (mode == "manual" or mode == "all") and hasattr(self, 'txt_script'):
            self.txt_script.delete("1.0", tk.END)

        # Limpiar campos AI
        if (mode == "ai" or mode == "all"):
            if hasattr(self, 'txt_contexto_ai'):
                self.txt_contexto_ai.delete("1.0", tk.END)
                self.txt_contexto_ai.insert("1.0", "Escribe aquí el contexto o notas para guiar la generación del guion...") # Restaurar placeholder
            # Opcional: resetear spinboxes y combos de AI a valores por defecto?
            # if hasattr(self.app, 'ai_num_sections'): self.app.ai_num_sections.set(5)
            # if hasattr(self.app, 'ai_words_per_section'): self.app.ai_words_per_section.set(300)
            # if hasattr(self, 'combo_estilo_script') and self.combo_estilo_script['values']:
            #     self.combo_estilo_script.current(0)
            # if hasattr(self, 'prompt_style_dropdown') and self.prompt_style_dropdown['values']:
            #     self.prompt_style_dropdown.current(0) # Resetear a cinematográfico o el primero

        print("Campos limpiados.")


    def _get_selected_project_id(self):
        """Obtiene el ID del proyecto seleccionado en el Treeview."""
        if not hasattr(self.app, 'tree_queue'):
             print("Error: tree_queue no existe en self.app")
             messagebox.showerror("Error Interno", "La tabla de la cola no está disponible.")
             return None
        if not hasattr(self.app, 'batch_tts_manager'):
             print("Error: batch_tts_manager no existe en self.app")
             messagebox.showerror("Error Interno", "El gestor de la cola no está disponible.")
             return None

        selected_items = self.app.tree_queue.selection()
        if not selected_items:
            messagebox.showwarning("Selección Requerida", "Por favor, selecciona un proyecto de la cola.")
            return None

        selected_id = selected_items[0] # El ID es el item del treeview

        # Verificar que el ID existe en el manager (jobs_in_gui es el diccionario clave)
        if selected_id not in self.app.batch_tts_manager.jobs_in_gui:
             messagebox.showerror("Error", f"El proyecto seleccionado (ID: {selected_id}) no se encontró en los datos internos del gestor de cola.")
             # Podría ser útil refrescar la cola aquí si hay inconsistencias
             if hasattr(self.app, 'update_queue_status'): self.app.update_queue_status()
             return None

        # Devolver solo el ID, el manager ya tiene los datos asociados a ese ID
        return selected_id


    def _encolar_proyecto_generado(self, titulo, guion, voice, video_settings, contexto_original=None):
        """Encola directamente un proyecto con un guion generado por IA."""
        print(f"\n--- ENCOLANDO PROYECTO GENERADO AUTOMÁTICAMENTE ---")
        print(f"Título: '{titulo}'")
        #print(f"Longitud del guion: {len(guion)} caracteres")
        print(f"Voz: {voice}")
        #print(f"Video settings params: {len(video_settings) if video_settings else 0}")
        #print(f"Contexto Original: {'Sí' if contexto_original else 'No'}")

        if not hasattr(self.app, 'batch_tts_manager') or not self.app.batch_tts_manager:
             messagebox.showerror("Error Crítico", "El gestor de cola (BatchTTSManager) no está disponible.")
             self.config(cursor="")
             return

        try:
            self.config(cursor="") # Restaurar cursor

            # Llamar al manager para añadir el proyecto
            # Pasamos script_contexto si lo tenemos
            job_id = self.app.batch_tts_manager.add_project_to_queue(
                title=titulo,
                script=guion,
                voice=voice,
                video_settings=video_settings,
                script_contexto=contexto_original # Pasar contexto si existe
            )

            if job_id:
                messagebox.showinfo(
                    "Proyecto Encolado",
                    f"El proyecto '{titulo}' generado por IA ha sido añadido a la cola con ID: {job_id}.\n\n"
                    "Puedes ver su estado en la tabla de abajo."
                )
                print(f"Proyecto AI '{titulo}' encolado exitosamente con ID: {job_id}")
                # Limpiar campos del modo AI después de encolar exitosamente
                self._clear_project_fields("ai")

                if hasattr(self.app, 'update_queue_status'):
                    self.app.update_queue_status()
            # else: El manager ya muestra el error si job_id es None/False

        except Exception as e:
            error_msg = f"Error al encolar el proyecto generado '{titulo}': {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error de Encolado", error_msg)
            self.config(cursor="")


    def _regenerar_parte(self, parte, mensaje_confirmacion, metodo_manager):
         """Función genérica para confirmar y lanzar regeneración."""
         job_id = self._get_selected_project_id()
         if not job_id:
             return

         job_data = self.app.batch_tts_manager.jobs_in_gui.get(job_id)
         if not job_data:
              messagebox.showerror("Error", f"No se encontraron datos para el job ID {job_id}")
              return

         if messagebox.askyesno("Confirmar Regeneración",
                                mensaje_confirmacion.format(titulo=job_data['titulo'])):
             # Actualizar estado en GUI inmediatamente
             self.app.batch_tts_manager.update_job_status_gui(job_id, f"Regenerando {parte}...")
             # Lanzar en hilo
             threading.Thread(target=metodo_manager, args=(job_id,), daemon=True).start()


    def _regenerar_audio(self):
        """Regenera el audio para el proyecto seleccionado."""
        self._regenerar_parte(
            "Audio",
            "¿Estás seguro de regenerar el audio para el proyecto '{titulo}'?",
            self.app.batch_tts_manager.regenerar_audio
        )

    def _regenerar_prompts(self):
        """Regenera los prompts para el proyecto seleccionado."""
        self._regenerar_parte(
            "Prompts",
            "¿Estás seguro de regenerar los prompts para el proyecto '{titulo}'?",
            self.app.batch_tts_manager.regenerar_prompts
        )

    def _regenerar_imagenes(self):
        """Regenera las imágenes para el proyecto seleccionado."""
        self._regenerar_parte(
            "Imágenes",
            "¿Estás seguro de regenerar las imágenes para el proyecto '{titulo}'? (Esto puede usar créditos/tiempo)",
            self.app.batch_tts_manager.regenerar_imagenes
        )

    def _regenerar_subtitulos(self):
        """Regenera los subtítulos para el proyecto seleccionado."""
        self._regenerar_parte(
            "Subtítulos",
            "¿Estás seguro de regenerar los subtítulos para el proyecto '{titulo}'?",
            self.app.batch_tts_manager.regenerar_subtitulos
        )

    def _preview_voice(self):
        """Genera y reproduce una muestra de voz con los parámetros TTS actuales."""
        if not TTS_AVAILABLE:
            messagebox.showerror("Error", "El módulo TTS (text_chunk_to_speech) no está disponible o no se pudo importar.")
            return

        voice = self.app.selected_voice.get()
        rate = self.app.tts_rate_str.get()
        pitch = self.app.tts_pitch_str.get()
        test_text = "Hola, esta es una prueba de la configuración de voz seleccionada."
        print(f"DEBUG: Generando vista previa TTS: voz={voice}, rate={rate}, pitch={pitch}")

        # Crear directorio temporal seguro
        try:
            # Usar directorio temporal del sistema o uno local
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "videocreator_previews"
            temp_dir.mkdir(exist_ok=True)
            temp_audio_path = temp_dir / f"preview_{voice}_{int(time.time())}.mp3"
        except Exception as e:
             messagebox.showerror("Error", f"No se pudo crear el directorio temporal para la vista previa: {e}")
             return

        # Deshabilitar botón y mostrar estado
        if hasattr(self, 'btn_preview') and self.btn_preview.winfo_exists():
            original_text = self.btn_preview.cget("text")
            self.btn_preview.config(state="disabled", text="Generando...")
            self.update_idletasks()
        else:
             original_text = "Probar Voz" # Fallback

        # Función para ejecutar en hilo
        def generate_and_play():
            try:
                print(f"Generando archivo de vista previa en: {temp_audio_path}")
                # Ejecutar la generación de voz (asegúrate de que text_chunk_to_speech sea seguro para hilos si usa recursos compartidos)
                # Usar asyncio.run en un hilo puede ser problemático si ya hay un loop corriendo.
                # Considera ejecutar la corutina de otra manera o hacer text_chunk_to_speech síncrono si es posible.
                # Solución simple: ejecutar en un nuevo loop de eventos si es necesario.
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(text_chunk_to_speech(
                        text=test_text,
                        voice=voice,
                        output_path=str(temp_audio_path),
                        rate=rate,
                        pitch=pitch
                    ))
                    loop.close()
                except RuntimeError as e:
                     # Si ya hay un loop corriendo, intentar ejecutar directamente si la función lo permite
                     if "cannot run event loop while another loop is running" in str(e):
                          print("Advertencia: Event loop ya en ejecución. Intentando ejecutar text_chunk_to_speech directamente.")
                          # Esto asume que text_chunk_to_speech puede funcionar sin un loop explícito aquí
                          # o que maneja el loop existente correctamente. Puede fallar.
                          # Necesitarías ajustar cómo se llama la corutina aquí.
                          # Una opción es usar `self.after` para pedir al loop principal que la ejecute,
                          # pero eso bloquea la UI. La solución del nuevo loop es generalmente mejor.
                          # O, si `text_chunk_to_speech` es simple, hacerla síncrona.
                          raise NotImplementedError("Llamada a corutina desde hilo con loop existente no implementada de forma segura.") from e
                     else:
                          raise e


                print("Generación completada. Intentando reproducir...")
                # Programar la reproducción en el hilo principal de Tkinter usando 'after'
                self.after(0, lambda: self._play_audio(temp_audio_path))

            except Exception as e:
                error_msg = f"No se pudo generar la vista previa de voz: {e}"
                print(f"ERROR: {error_msg}")
                # Mostrar error en el hilo principal
                self.after(0, lambda: messagebox.showerror("Error Vista Previa", error_msg))
                import traceback
                traceback.print_exc()
            finally:
                # Restaurar botón en el hilo principal
                if hasattr(self, 'btn_preview') and self.btn_preview.winfo_exists():
                    self.after(0, lambda: self.btn_preview.config(state="normal", text=original_text))

        # Iniciar el hilo
        threading.Thread(target=generate_and_play, daemon=True).start()


    def _play_audio(self, audio_path):
        """Reproduce un archivo de audio usando el método apropiado del OS."""
        if not Path(audio_path).exists():
             print(f"Error: El archivo de audio no existe: {audio_path}")
             messagebox.showerror("Error Reproducción", "El archivo de audio generado no se encontró.")
             return

        print(f"Reproduciendo audio: {audio_path}")
        try:
            if sys.platform == "win32":
                os.startfile(audio_path)
            elif sys.platform == "darwin": # macOS
                subprocess.run(['afplay', str(audio_path)], check=True, capture_output=True)
            else: # Linux y otros POSIX
                # Intentar con diferentes reproductores comunes
                players = ['xdg-open', 'paplay', 'aplay', 'play']
                played = False
                for player in players:
                     try:
                          # Usar Popen para no bloquear si el reproductor no termina inmediatamente
                          proc = subprocess.Popen([player, str(audio_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                          # Opcional: esperar un poco para ver si falla rápido
                          # proc.wait(timeout=1)
                          print(f"Intentando reproducir con {player}...")
                          played = True
                          break # Salir si uno funciona
                     except (FileNotFoundError, subprocess.TimeoutExpired):
                          continue # Probar el siguiente
                if not played:
                     raise FileNotFoundError(f"No se encontró un reproductor de audio compatible ({', '.join(players)}).")
        except FileNotFoundError as e:
             print(f"Error al reproducir audio: {e}")
             messagebox.showwarning("Error Reproducción", f"No se encontró un comando para reproducir audio.\nAsegúrate de tener instalado un reproductor como 'afplay' (macOS), 'paplay'/'aplay' (Linux), o que 'xdg-open' funcione.")
        except subprocess.CalledProcessError as e:
            print(f"Error durante la reproducción de audio: {e}")
            # Decodificar salida de error si existe
            error_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "No error output"
            messagebox.showerror("Error Reproducción", f"El comando de reproducción falló:\n{error_output}")
        except Exception as e:
            print(f"Error inesperado al reproducir audio: {e}")
            messagebox.showerror("Error Reproducción", f"Ocurrió un error inesperado: {e}")
        finally:
             # Opcional: eliminar el archivo temporal después de intentar reproducirlo
             # Podrías querer mantenerlo para depuración
             # try:
             #      Path(audio_path).unlink()
             #      print(f"Archivo temporal eliminado: {audio_path}")
             # except OSError as e:
             #      print(f"Error al eliminar archivo temporal {audio_path}: {e}")
             pass


    def _cargar_proyecto_existente(self):
        """Carga un proyecto existente desde su carpeta guardada."""
        if not hasattr(self.app, 'batch_tts_manager') or not self.app.batch_tts_manager:
             messagebox.showerror("Error Crítico", "El gestor de cola (BatchTTSManager) no está disponible.")
             return

        proyectos_dir = self.app.batch_tts_manager.project_base_dir
        if not proyectos_dir.is_dir():
             messagebox.showerror("Error", f"El directorio base de proyectos no existe: {proyectos_dir}")
             return

        proyecto_path_str = filedialog.askdirectory(
            title="Seleccionar Carpeta del Proyecto a Cargar",
            initialdir=proyectos_dir
        )

        if not proyecto_path_str:
            return # Usuario canceló

        proyecto_path = Path(proyecto_path_str)
        settings_path = proyecto_path / "settings.json"
        guion_path = proyecto_path / "guion.txt"

        # Verificar que es una carpeta de proyecto válida (mínimo)
        if not settings_path.exists() or not guion_path.exists():
            messagebox.showerror(
                "Error",
                f"La carpeta seleccionada no parece ser un proyecto válido.\n"
                f"Falta 'settings.json' o 'guion.txt'.\n"
                f"Ruta: {proyecto_path}"
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

            # Determinar la voz usada (del settings.json si existe)
            # Usar un valor por defecto si no se encuentra o es inválido
            voz_guardada = settings.get("voz", self.app.selected_voice.get()) # Usar la actual como fallback

            # Intentar añadir el proyecto existente a la cola del manager
            job_id = self.app.batch_tts_manager.add_existing_project_to_queue(
                title=proyecto_nombre,
                script=script_content,
                project_folder=proyecto_path,
                voice=voz_guardada, # Usar la voz guardada
                video_settings=settings # Pasar todos los settings guardados
            )

            if job_id:
                messagebox.showinfo(
                    "Proyecto Cargado",
                    f"El proyecto '{proyecto_nombre}' ha sido cargado en la cola.\n"
                    f"Puedes regenerar partes o generar el video completo."
                )
                if hasattr(self.app, 'update_queue_status'):
                    self.app.update_queue_status()
            # else: El manager ya mostró error

        except json.JSONDecodeError as e:
             messagebox.showerror("Error", f"Error al leer el archivo 'settings.json':\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el proyecto desde {proyecto_path}:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _recargar_prompts_imagenes(self):
        """Carga los prompts de imágenes disponibles"""
        try:
            # Obtener los nombres de los prompts disponibles
            prompts = [name for _, name in self.app.prompt_manager.get_prompt_names()]
            self.combo_image_prompt['values'] = prompts
            if prompts:
                self.app.selected_image_prompt.set(prompts[0])
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar prompts de imágenes: {str(e)}")

    def _recargar_prompts_scripts(self):
        """Carga los prompts de scripts disponibles"""
        try:
            if hasattr(self.app, 'script_prompt_manager') and self.app.script_prompt_manager:
                prompts = [name for _, name in self.app.script_prompt_manager.get_style_names()]
                self.combo_script_prompt['values'] = prompts
                if prompts:
                    self.app.selected_script_prompt.set(prompts[0])
            else:
                self.combo_script_prompt['values'] = []
                self.app.selected_script_prompt.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar prompts de scripts: {str(e)}")