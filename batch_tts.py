import traceback
import logging
import queue
import threading
import os
import re
import time
import math
import asyncio
import logging
import traceback
import tkinter as tk
from tkinter import ttk, messagebox # Añadido messagebox que faltaba en los imports
from pathlib import Path
from datetime import datetime
from queue import Queue
from threading import Thread, Event
from typing import Any, Dict, List
#from moviepy.editor import AudioFileClip # Corregido import de moviepy
from moviepy import *

# <<< MODIFICADO: Importación directa desde video_creator >>>
try:
    from app.video_creator import crear_video_desde_imagenes
    VIDEO_CREATOR_AVAILABLE = True
except ImportError:
    print("Advertencia: No se pudo importar 'crear_video_desde_imagenes' desde 'app.video_creator'.")
    print("Asegúrate de que el archivo app/video_creator.py esté accesible y la función exista.")
    VIDEO_CREATOR_AVAILABLE = False
    # Define una función simulada si la importación falla
    def crear_video_desde_imagenes(project_folder, **kwargs):
        print(f"Simulando: Creando video para el proyecto '{project_folder}' con args: {kwargs}")
        # Simula la creación de un archivo de video vacío
        simulated_path = Path(project_folder) / "video_final_simulado.mp4"
        simulated_path.touch()
        return str(simulated_path) # Devuelve la ruta simulada como string

from prompt_generator import GEMINI_AVAILABLE, generar_prompts_con_gemini
from image_generator import generar_imagen_con_replicate, REPLICATE_AVAILABLE

# Importar el generador de voz en off
try:
    from tts_generator import create_voiceover_from_script, OUTPUT_FORMAT
except ImportError:
    print("Advertencia: No se pudo importar 'create_voiceover_from_script' o 'OUTPUT_FORMAT'.")
    print("Asegúrate de que el archivo tts_generator.py esté accesible.")
    # Define valores por defecto si la importación falla
    async def create_voiceover_from_script(script_path, output_audio_path, voice=None): # Corregido nombre del arg
        print(f"Simulando: Generando audio desde '{script_path}' a '{output_audio_path}'")
        # En una ejecución real, esto crearía el archivo
        Path(output_audio_path).touch()  # Crea un archivo vacío como marcador
        return output_audio_path  # Devuelve la ruta simulada
    OUTPUT_FORMAT = "mp3"

# Importar generador de subtítulos
try:
    from subtitles import generate_srt_with_whisper, WHISPER_AVAILABLE, get_whisper_model # Añadido get_whisper_model
    if WHISPER_AVAILABLE:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("Advertencia: No se pudo importar WhisperModel a pesar de que WHISPER_AVAILABLE es True")
            WHISPER_AVAILABLE = False
except ImportError:
    print("Advertencia: No se pudo importar 'generate_srt_with_whisper', 'WHISPER_AVAILABLE' o 'get_whisper_model'.")
    print("Asegúrate de que el archivo subtitles.py esté accesible.")
    WHISPER_AVAILABLE = False
    # Fallback si get_whisper_model no se importa
    def get_whisper_model(*args, **kwargs):
        print("Simulando: get_whisper_model no disponible.")
        return None


class BatchTTSManager:
    """Gestor de procesamiento por lotes para la generación de voz en off."""

    def __init__(self, root, default_voice="es-MX-JorgeNeural"):
        """
        Inicializa el gestor de procesamiento por lotes.

        Args:
            root: La ventana principal de Tkinter
            default_voice: La voz predeterminada para la generación de TTS
        """
        self.root = root
        self.default_voice = default_voice

        # Configuración de directorios
        self.project_base_dir = Path("proyectos_video")
        self.project_base_dir.mkdir(parents=True, exist_ok=True)

        # Cola de trabajos y contador
        self.job_queue = queue.Queue()
        self.jobs_in_gui = {}  # Diccionario para rastrear trabajos y sus IDs en el Treeview
        self.job_counter = 0  # Para IDs únicos

        # Estado del worker
        self.worker_running = False
        self.worker_thread = None

        # Variables para la interfaz
        self.tree_queue = None  # Se inicializará cuando se cree la interfaz

    def sanitize_filename(self, filename):
        """Limpia un string para usarlo como nombre de archivo/carpeta seguro."""
        # Quitar caracteres inválidos
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        # Reemplazar espacios con guiones bajos
        sanitized = sanitized.replace(" ", "_")
        # Limitar longitud
        return sanitized[:100]  # Limitar a 100 caracteres

    def add_project_to_queue(self, title, script, voice=None, video_settings=None):
        """
        Añade un nuevo proyecto a la cola de procesamiento.

        Args:
            title: Título del proyecto
            script: Texto del guion para la voz en off
            voice: Voz a utilizar (opcional, usa default_voice si no se especifica)
            video_settings: Diccionario con ajustes para la creación del video

        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        if not title:
            messagebox.showerror("Error", "Por favor, introduce un título para el proyecto.")
            return False

        if not script:
            messagebox.showerror("Error", "Por favor, introduce un guion para el proyecto.")
            return False

        # Crear carpeta de proyecto
        safe_title = self.sanitize_filename(title)
        # Añadir timestamp para evitar colisiones si se procesa el mismo título varias veces
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_folder = self.project_base_dir / f"{safe_title}_{timestamp}" # Modificado para unicidad

        try:
            project_folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta del proyecto:\n{project_folder}\nError: {e}")
            return False

        # Guardar guion
        script_file_path = project_folder / "guion.txt"
        try:
            with open(script_file_path, "w", encoding="utf-8") as f:
                f.write(script)
        except IOError as e:
            messagebox.showerror("Error", f"No se pudo guardar el guion:\n{script_file_path}\nError: {e}")
            # Considerar eliminar la carpeta creada si falla el guardado del guion
            # try:
            #     project_folder.rmdir()
            # except OSError:
            #     pass # Ignorar si no se puede borrar
            return False

        # Crear y añadir trabajo a la cola
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"

        job_data = {
            'id': job_id,
            'titulo': title,  # Guardamos el título original para mostrar
            'guion_path': str(script_file_path),
            'carpeta_salida': str(project_folder),
            'voz': voice or self.default_voice,
            'estado': 'Pendiente',
            'tiempo_inicio': None,
            'tiempo_fin': None,
            # Guardar ajustes para la creación del video (asegurarse que es un dict)
            'video_settings': video_settings if isinstance(video_settings, dict) else {}
        }

        # Guardar configuración del proyecto en un archivo JSON
        settings_file_path = project_folder / "settings.json"
        try:
            import json
            with open(settings_file_path, "w", encoding="utf-8") as f:
                # Asegurarse de que los datos sean serializables
                serializable_settings = {}
                current_settings = job_data['video_settings'] # Usar los settings del job_data
                if current_settings:
                    serializable_settings = current_settings.copy()
                    # Convertir rutas a strings si es necesario
                    for key, value in serializable_settings.items():
                        if isinstance(value, Path):
                            serializable_settings[key] = str(value)
                        elif isinstance(value, list) and value and isinstance(value[0], Path):
                            serializable_settings[key] = [str(p) for p in value]
                json.dump(serializable_settings, f, indent=4, ensure_ascii=False)
            print(f"Configuración guardada en {settings_file_path}")
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            # Continuamos aunque falle el guardado de la configuración

        self.job_queue.put(job_data)

        # Añadir a la GUI (Treeview) si ya existe
        if self.tree_queue:
            self.tree_queue.insert("", tk.END, iid=job_id, values=(title, 'Pendiente', '-'))
            self.jobs_in_gui[job_id] = job_data # Asegurarse de añadirlo aquí

        print(f"Proyecto '{title}' añadido a la cola (ID: {job_id}).")
        return True

    def add_existing_project_to_queue(self, title, script, project_folder, voice=None, video_settings=None):
        """
        Añade un proyecto existente a la cola de procesamiento.
        (Esta función principalmente añade a la GUI, no re-procesa automáticamente)

        Args:
            title: Título del proyecto
            script: Texto del guion para la voz en off
            project_folder: Ruta a la carpeta del proyecto existente
            voice: Voz a utilizar (opcional, usa default_voice si no se especifica)
            video_settings: Diccionario con ajustes para la creación del video (leídos de settings.json si existe)

        Returns:
            str: ID del trabajo si se añadió correctamente, None en caso contrario
        """
        if not title or not script or not project_folder:
            print("Error: Título, guion y carpeta del proyecto son obligatorios")
            return None

        # Convertir a Path si es un string
        if isinstance(project_folder, str):
            project_folder = Path(project_folder)

        # Verificar que la carpeta existe
        if not project_folder.exists() or not project_folder.is_dir():
            print(f"Error: La carpeta del proyecto {project_folder} no existe")
            return None

        # Cargar settings.json si existe
        loaded_settings = {}
        settings_file_path = project_folder / "settings.json"
        if settings_file_path.exists():
            try:
                import json
                with open(settings_file_path, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                print(f"Configuración cargada desde {settings_file_path}")
            except Exception as e:
                print(f"Error al cargar configuración desde {settings_file_path}: {e}")

        # Combinar/priorizar settings: los pasados como argumento tienen prioridad
        final_video_settings = loaded_settings.copy()
        if isinstance(video_settings, dict):
            final_video_settings.update(video_settings) # Los nuevos sobreescriben los cargados

        # Usar la voz predeterminada si no se especifica
        if not voice:
            voice = self.default_voice

        # Generar un ID único para el trabajo
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"

        # Crear datos del trabajo
        job_data = {
            'id': job_id,
            'titulo': title,
            'guion_path': str(project_folder / "guion.txt"), # Asumimos que existe
            'carpeta_salida': str(project_folder),
            'voz': voice,
            'estado': 'Cargado',
            'tiempo_inicio': None,
            'tiempo_fin': None,
            'script': script,  # Guardamos una copia del script en memoria
            'video_settings': final_video_settings # Usar los settings combinados
        }

        # Verificar si existen archivos generados previamente
        audio_path = project_folder / f"voz.{OUTPUT_FORMAT}"
        if audio_path.exists():
            job_data['archivo_voz'] = str(audio_path)
            job_data['estado'] = 'Audio Existente'

        subtitles_path = project_folder / "subtitulos.srt"
        if subtitles_path.exists():
            job_data['archivo_subtitulos'] = str(subtitles_path)
            job_data['aplicar_subtitulos'] = True # Asumimos que si existe, se quiere aplicar

        prompts_path = project_folder / "prompts.txt"
        if prompts_path.exists():
            try:
                with open(prompts_path, "r", encoding="utf-8") as f:
                    prompts_content = f.read()
                import re
                segments = re.findall(r"Segmento Guion \(ES\):\n(.*?)\n\n", prompts_content, re.DOTALL)
                prompts = re.findall(r"Prompt Generado \(EN\):\n(.*?)\n=", prompts_content, re.DOTALL)
                if segments and prompts and len(segments) == len(prompts):
                    prompts_data = [{'segmento_es': s.strip(), 'prompt_en': p.strip()} for s, p in zip(segments, prompts)]
                    job_data['prompts_data'] = prompts_data
                    job_data['num_imagenes'] = len(prompts_data)
                    print(f"Cargados {len(prompts_data)} prompts desde {prompts_path}")
            except Exception as e:
                print(f"Error al cargar prompts desde {prompts_path}: {e}")

        images_folder = project_folder / "imagenes"
        if images_folder.exists() and images_folder.is_dir():
            image_extensions = [".jpg", ".jpeg", ".png"]
            images = []
            # Ordenar imágenes por nombre para mantener secuencia
            all_files = sorted(images_folder.iterdir())
            for file in all_files:
                if file.suffix.lower() in image_extensions:
                    images.append(str(file))

            if images:
                job_data['imagenes_generadas'] = images
                print(f"Encontradas {len(images)} imágenes en {images_folder}")
                if 'num_imagenes' not in job_data: # Si no se cargaron prompts, usar número de imágenes
                     job_data['num_imagenes'] = len(images)

        video_path = project_folder / "video_final.mp4" # Asumiendo nombre por defecto
        if video_path.exists():
             job_data['archivo_video'] = str(video_path)
             job_data['estado'] = 'Video Existente' # Actualizar estado si el video ya está

        # Añadir a la GUI (Treeview) si ya existe
        if self.tree_queue:
            # Mostrar el estado más avanzado detectado
            self.tree_queue.insert("", tk.END, iid=job_id, values=(title, job_data['estado'], '-'))
            self.jobs_in_gui[job_id] = job_data

        print(f"Proyecto existente '{title}' cargado en la cola (ID: {job_id}).")
        return job_id

    def start_worker(self):
        """Inicia el hilo trabajador si no está en ejecución."""
        if not self.worker_running:
            self.worker_running = True
            # Pasar self.root a _process_queue si es necesario para acceder a la GUI directamente
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            print("Worker de cola iniciado.")

    def stop_worker(self):
        """Detiene el hilo trabajador (completará el trabajo actual)."""
        self.worker_running = False
        print("Worker de cola detenido. Completará el trabajo actual antes de terminar.")

    def _process_queue(self):
        """Procesa los trabajos en la cola de forma secuencial."""
        while self.worker_running:
            current_job = None # Para manejo de errores y finally
            try:
                # Esperar un trabajo con timeout para poder comprobar worker_running
                try:
                    current_job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    # No hay trabajos, seguir esperando
                    continue

                job_id = current_job['id']
                title = current_job['titulo']
                script_path = current_job['guion_path']
                output_folder = Path(current_job['carpeta_salida'])
                voice = current_job['voz']
                audio_output_path = str(output_folder / f"voz.{OUTPUT_FORMAT}")

                # Actualizar estado y tiempo de inicio
                current_job['tiempo_inicio'] = time.time()
                self.update_job_status_gui(job_id, "Generando Audio...", "-")

                print(f"Procesando trabajo {job_id}: '{title}'")

                final_audio_path = None
                success_tts = False
                error_msg = ""

                try:
                    # --- 1. Generación de Audio ---
                    final_audio_path = asyncio.run(create_voiceover_from_script(
                        script_path=script_path,
                        output_audio_path=audio_output_path,
                        voice=voice
                    ))

                    audio_tiempo_fin = time.time()
                    audio_tiempo_transcurrido = audio_tiempo_fin - current_job['tiempo_inicio']
                    audio_tiempo_formateado = f"{int(audio_tiempo_transcurrido // 60)}m {int(audio_tiempo_transcurrido % 60)}s"

                    if final_audio_path and Path(final_audio_path).is_file():
                        print(f"Audio generado para {job_id}: {final_audio_path}")
                        current_job['archivo_voz'] = final_audio_path
                        success_tts = True

                        # --- 2. Generación de Subtítulos ---
                        srt_success = False
                        if WHISPER_AVAILABLE:
                            self.update_job_status_gui(job_id, "Audio OK. Generando SRT...", audio_tiempo_formateado)
                            srt_output_path = str(output_folder / "subtitulos.srt")

                            # Buscar el modelo Whisper (simplificado, asume que se puede crear)
                            whisper_model = None
                            app_instance = None # Para buscar configuraciones de la GUI
                            for widget in self.root.winfo_children():
                                if hasattr(widget, 'whisper_model'): # Asumiendo que la GUI tiene 'whisper_model'
                                    app_instance = widget
                                    whisper_model = getattr(app_instance, 'whisper_model', None)
                                    break
                            if not whisper_model:
                                print("No se encontró modelo Whisper en GUI, intentando crear 'base'...")
                                try:
                                     whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                                except Exception as e_wm:
                                     print(f"No se pudo crear modelo Whisper base: {e_wm}")


                            if whisper_model:
                                try:
                                    # Obtener configuración de la GUI o usar defaults
                                    whisper_language = getattr(app_instance.whisper_language, 'get', lambda: 'es')() if app_instance else 'es'
                                    word_timestamps = getattr(app_instance.whisper_word_timestamps, 'get', lambda: True)() if app_instance else True
                                    uppercase = getattr(app_instance.subtitles_uppercase, 'get', lambda: False)() if app_instance else False

                                    print(f"Generando subtítulos con idioma: {whisper_language}, timestamps: {word_timestamps}, mayúsculas: {uppercase}")

                                    srt_success = generate_srt_with_whisper(
                                        whisper_model,
                                        final_audio_path, # Pasar modelo primero
                                        srt_output_path,
                                        language=whisper_language,
                                        word_timestamps=word_timestamps,
                                        uppercase=uppercase
                                    )
                                    if srt_success:
                                        self.update_job_status_gui(job_id, "Audio y SRT OK", audio_tiempo_formateado)
                                        current_job['archivo_subtitulos'] = srt_output_path
                                        current_job['aplicar_subtitulos'] = True
                                        print(f"Subtítulos generados: {srt_output_path}")
                                    else:
                                        raise ValueError("generate_srt_with_whisper retornó False")

                                except Exception as e_srt:
                                    print(f"Error al generar subtítulos: {e_srt}")
                                    traceback.print_exc()
                                    self.update_job_status_gui(job_id, "Audio OK. Error SRT", audio_tiempo_formateado)
                                    current_job['aplicar_subtitulos'] = False
                            else:
                                print("Whisper model no disponible, omitiendo subtítulos.")
                                self.update_job_status_gui(job_id, "Audio OK. SRT Omitido (no model)", audio_tiempo_formateado)

                        else: # Whisper no disponible globalmente
                            print("Whisper no disponible, omitiendo subtítulos.")
                            self.update_job_status_gui(job_id, "Audio OK. SRT Omitido", audio_tiempo_formateado)


                        # --- 3. Generación de Prompts ---
                        prompts_ok = False
                        if GEMINI_AVAILABLE:
                            self.update_job_status_gui(job_id, "Audio/SRT OK. Generando Prompts...")
                            try:
                                with open(script_path, 'r', encoding='utf-8') as f:
                                    script_content = f.read()

                                temp_audio_clip = AudioFileClip(final_audio_path)
                                audio_duration = temp_audio_clip.duration
                                temp_audio_clip.close()

                                # Obtener parámetros de video del job
                                video_settings_job = current_job.get('video_settings', {})
                                duracion_por_imagen = float(video_settings_job.get('duracion_img', 15.0)) # Default 15s
                                aplicar_transicion = video_settings_job.get('aplicar_transicion', False)
                                duracion_transicion_setting = float(video_settings_job.get('duracion_transicion', 1.0))
                                duracion_transicion_usada = duracion_transicion_setting if aplicar_transicion else 0.0
                                respetar_duracion_exacta_setting = video_settings_job.get('respetar_duracion_exacta', True)
                                fade_in = float(video_settings_job.get('duracion_fade_in', 0.0)) # Defaults a 0 si no están
                                fade_out = float(video_settings_job.get('duracion_fade_out', 0.0))

                                print(f"\n--- Calculando Imágenes Óptimas (Prompt Gen) para Job {job_id} ---")
                                # ... (impresiones de depuración como antes) ...

                                num_imagenes_necesarias, tiempos_imagenes = self.calcular_imagenes_optimas(
                                    audio_duration=audio_duration,
                                    duracion_por_imagen=duracion_por_imagen,
                                    duracion_transicion=duracion_transicion_usada,
                                    aplicar_transicion=aplicar_transicion,
                                    fade_in=fade_in,
                                    fade_out=fade_out,
                                    respetar_duracion_exacta=respetar_duracion_exacta_setting
                                )

                                current_job['tiempos_imagenes'] = tiempos_imagenes
                                current_job['num_imagenes'] = num_imagenes_necesarias

                                # Guardar info de repetición si existe en los tiempos
                                for clip_info in tiempos_imagenes:
                                     if clip_info.get('repetir'):
                                          current_job['repetir_ultimo_clip'] = True
                                          current_job['tiempo_repeticion_ultimo_clip'] = clip_info.get('tiempo_repeticion', 0.0)
                                          break # Solo necesitamos saber si alguna lo tiene


                                estilo = video_settings_job.get('estilo_imagenes', 'default')
                                # ... (lógica para verificar/ajustar 'estilo' como antes) ...
                                try:
                                     from prompt_manager import PromptManager
                                     # (Opcional: verificar si el estilo existe como antes)
                                except ImportError:
                                     print("Advertencia: No se pudo importar PromptManager para verificar estilos.")

                                if not estilo or estilo == "None" or estilo == "": estilo = "default"
                                print(f"Estilo final para prompts: '{estilo}'")

                                lista_prompts = generar_prompts_con_gemini(
                                    script_content,
                                    num_imagenes_necesarias,
                                    current_job['titulo'],
                                    estilo_base=estilo,
                                    tiempos_imagenes=tiempos_imagenes
                                )

                                if lista_prompts:
                                    current_job['prompts_data'] = lista_prompts
                                    # Asegurar que num_imagenes coincide con prompts generados
                                    current_job['num_imagenes'] = len(lista_prompts)
                                    prompt_file_path = output_folder / "prompts.txt"
                                    with open(prompt_file_path, "w", encoding="utf-8") as f:
                                         for p_idx, data in enumerate(lista_prompts):
                                              f.write(f"--- Imagen {p_idx+1} ---\n")
                                              f.write(f"Segmento Guion (ES):\n{data.get('segmento_es', 'N/A')}\n\n") # Usar .get
                                              f.write(f"Prompt Generado (EN):\n{data.get('prompt_en', 'N/A')}\n") # Usar .get
                                              f.write("="*30 + "\n\n")
                                    print(f"Prompts guardados en {prompt_file_path}")
                                    self.update_job_status_gui(job_id, "Prompts OK. Generando Imágenes...")
                                    prompts_ok = True
                                else:
                                    raise ValueError("generar_prompts_con_gemini no devolvió prompts.")

                            except Exception as e_prompt:
                                print(f"Error durante la generación de prompts para {job_id}: {e_prompt}")
                                traceback.print_exc()
                                self.update_job_status_gui(job_id, "Audio/SRT OK. Error Prompts.")
                                # Continuar sin prompts? O marcar error? Decidimos continuar pero sin prompts_ok
                        else:
                            print("Gemini no disponible, omitiendo generación de prompts.")
                            self.update_job_status_gui(job_id, "Audio/SRT OK. Prompts Omitidos.")
                            # Necesitamos calcular tiempos igualmente si queremos generar video con imágenes existentes
                            try:
                                temp_audio_clip = AudioFileClip(final_audio_path)
                                audio_duration = temp_audio_clip.duration
                                temp_audio_clip.close()
                                video_settings_job = current_job.get('video_settings', {})
                                duracion_por_imagen = float(video_settings_job.get('duracion_img', 15.0))
                                aplicar_transicion = video_settings_job.get('aplicar_transicion', False)
                                duracion_transicion_setting = float(video_settings_job.get('duracion_transicion', 1.0))
                                duracion_transicion_usada = duracion_transicion_setting if aplicar_transicion else 0.0
                                respetar_duracion_exacta_setting = video_settings_job.get('respetar_duracion_exacta', True)
                                fade_in = float(video_settings_job.get('duracion_fade_in', 0.0))
                                fade_out = float(video_settings_job.get('duracion_fade_out', 0.0))

                                num_imagenes_necesarias, tiempos_imagenes = self.calcular_imagenes_optimas(
                                    audio_duration=audio_duration, duracion_por_imagen=duracion_por_imagen,
                                    duracion_transicion=duracion_transicion_usada, aplicar_transicion=aplicar_transicion,
                                    fade_in=fade_in, fade_out=fade_out, respetar_duracion_exacta=respetar_duracion_exacta_setting
                                )
                                current_job['tiempos_imagenes'] = tiempos_imagenes
                                # Si no hay prompts, num_imagenes se basará en cálculo o imágenes existentes
                                if 'imagenes_generadas' in current_job:
                                     current_job['num_imagenes'] = len(current_job['imagenes_generadas'])
                                else:
                                     current_job['num_imagenes'] = num_imagenes_necesarias # Usar calculado
                            except Exception as e_calc:
                                print(f"Error calculando tiempos sin Gemini: {e_calc}")
                                self.update_job_status_gui(job_id, "Error calculando tiempos")


                        # --- 4. Generación de Imágenes ---
                        images_ok = False
                        imagenes_generadas_paths = [] # Lista para guardar rutas de imágenes generadas
                        if prompts_ok and REPLICATE_AVAILABLE: # Solo generar si hay prompts y Replicate
                             self.update_job_status_gui(job_id, "Generando Imágenes...")
                             try:
                                 image_output_folder = output_folder / "imagenes"
                                 image_output_folder.mkdir(parents=True, exist_ok=True)
                                 lista_prompts_data = current_job.get('prompts_data', [])

                                 for idx, prompt_data in enumerate(lista_prompts_data):
                                     prompt_en = prompt_data.get('prompt_en')
                                     if not prompt_en or prompt_en.startswith("Error"):
                                         print(f"Omitiendo imagen {idx+1} por prompt inválido.")
                                         continue

                                     self.update_job_status_gui(job_id, f"Generando imagen {idx+1}/{len(lista_prompts_data)}...")

                                     # Usar nombre de carpeta base para el nombre de archivo
                                     base_name = output_folder.name
                                     img_filename = f"{base_name}_{idx+1:03d}.png"
                                     img_path_str = str(image_output_folder / img_filename)

                                     # Llamada a la generación de imagen
                                     generated_img_path = generar_imagen_con_replicate(prompt_en, img_path_str)

                                     if generated_img_path and Path(generated_img_path).exists():
                                         imagenes_generadas_paths.append(generated_img_path)
                                         print(f"Imagen {idx+1} generada: {generated_img_path}")
                                     else:
                                         print(f"Error o no se generó imagen {idx+1}")
                                         # ¿Continuar o fallar el job? Decidimos continuar por ahora.

                                 if imagenes_generadas_paths:
                                     current_job['imagenes_generadas'] = imagenes_generadas_paths # Guardar rutas generadas
                                     self.update_job_status_gui(job_id, "Imágenes generadas OK", "-") # Tiempo se calculará al final
                                     images_ok = True
                                 else:
                                      # Si se intentó generar pero fallaron todas
                                      if lista_prompts_data:
                                           self.update_job_status_gui(job_id, "Error generando imágenes", "-")
                                      else: # No había prompts para generar
                                           self.update_job_status_gui(job_id, "Imágenes Omitidas (sin prompts)", "-")


                             except Exception as e_img:
                                 print(f"Error generando imágenes con Replicate: {e_img}")
                                 traceback.print_exc()
                                 self.update_job_status_gui(job_id, "Error generando imágenes", str(e_img))
                        elif 'imagenes_generadas' in current_job and current_job['imagenes_generadas']:
                             # Si ya existían imágenes (cargadas de proyecto existente)
                             print("Usando imágenes preexistentes.")
                             imagenes_generadas_paths = current_job['imagenes_generadas'] # Usar las existentes
                             images_ok = True
                             self.update_job_status_gui(job_id, "Usando Imágenes Existentes", "-")
                        else:
                             print("Replicate no disponible o no hay prompts, omitiendo generación de imágenes.")
                             if prompts_ok and not REPLICATE_AVAILABLE:
                                 self.update_job_status_gui(job_id, "Imágenes Omitidas (no Replicate)", "-")
                             elif not prompts_ok:
                                  self.update_job_status_gui(job_id, "Imágenes Omitidas (no prompts)", "-")


                        # --- 5. Creación de Video ---
                        # <<< INICIO: Lógica Creación Video >>>
                        if images_ok and current_job.get('archivo_voz') and VIDEO_CREATOR_AVAILABLE:
                            try:
                                self.update_job_status_gui(job_id, "Generando Video...", "")
                                print(f"Iniciando creación de video para job {job_id} ('{title}')")

                                # Preparar argumentos para crear_video_desde_imagenes
                                video_creation_args = current_job.get('video_settings', {}).copy()

                                # Rutas y parámetros esenciales (asegurar strings donde sea necesario)
                                audio_path_vid = current_job.get('archivo_voz')
                                if audio_path_vid: video_creation_args['audio_path'] = str(audio_path_vid)

                                # Usar las rutas de imágenes (generadas o existentes)
                                image_paths_vid = imagenes_generadas_paths # Usar la lista poblada en el paso anterior
                                if image_paths_vid: video_creation_args['image_paths'] = [str(p) for p in image_paths_vid]

                                tiempos_imgs_vid = current_job.get('tiempos_imagenes')
                                if tiempos_imgs_vid: video_creation_args['tiempos_imagenes'] = tiempos_imgs_vid

                                # Subtítulos
                                subtitle_path_vid = current_job.get('archivo_subtitulos')
                                if subtitle_path_vid and current_job.get('aplicar_subtitulos'):
                                    video_creation_args['subtitle_path'] = str(subtitle_path_vid)
                                    # Podrías necesitar un flag si tu función lo requiere explícitamente
                                    # video_creation_args['apply_subtitles'] = True

                                # Pasar info de repetición si existe
                                if current_job.get('repetir_ultimo_clip'):
                                     video_creation_args['repetir_ultimo_clip'] = True
                                     video_creation_args['tiempo_repeticion_ultimo_clip'] = current_job.get('tiempo_repeticion_ultimo_clip', 0.0)


                                # Limpiar Nones para evitar problemas con **kwargs
                                video_creation_args_clean = {k: v for k, v in video_creation_args.items() if v is not None}
                                
                                # SOLUCIÓN 1: Asegurarse de que secuencia_efectos sea una lista válida
                                if 'secuencia_efectos' not in video_creation_args_clean or not video_creation_args_clean.get('secuencia_efectos'):
                                    print("Añadiendo secuencia_efectos predeterminada para asegurar que se apliquen efectos")
                                    video_creation_args_clean['secuencia_efectos'] = ['in', 'out', 'panup', 'kb']  # Efectos predeterminados
                                
                                # SOLUCIÓN 2: Activar subtítulos si existe el archivo
                                if 'archivo_subtitulos' in video_creation_args_clean and video_creation_args_clean['archivo_subtitulos']:
                                    print(f"Activando aplicar_subtitulos porque existe archivo: {video_creation_args_clean['archivo_subtitulos']}")
                                    video_creation_args_clean['aplicar_subtitulos'] = True
                                
                                # SOLUCIÓN 3: Asegurarse de que archivo_voz sea una ruta absoluta
                                if 'archivo_voz' in video_creation_args_clean:
                                    voz_path = Path(video_creation_args_clean['archivo_voz'])
                                    if not voz_path.is_absolute():
                                        voz_path = output_folder / voz_path.name
                                        print(f"Convirtiendo ruta de voz a absoluta: {voz_path}")
                                    video_creation_args_clean['archivo_voz'] = str(voz_path)

                                print("-" * 30)
                                print(f"DEBUG JOB {job_id} - Settings ANTES de llamar a crear_video:")
                                print(f"  >> Contenido de current_job['video_settings']:")
                                import json; print(json.dumps(current_job.get('video_settings', {}), indent=2)) # Imprimir formateado
                                print(f"  >> Argumentos FINALES pasados (video_creation_args_clean):")
                                print(json.dumps(video_creation_args_clean, indent=2)) # Imprimir formateado
                                print("-" * 30)

                                video_final_path = crear_video_desde_imagenes(
                                    project_folder=str(output_folder),
                                    **video_creation_args_clean
                                )

                                if video_final_path and Path(video_final_path).exists():
                                    current_job['archivo_video'] = str(video_final_path)
                                    current_job['tiempo_fin'] = time.time() # Marcar fin aquí
                                    tiempo_total = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                                    tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                                    self.update_job_status_gui(job_id, "Video Completo", tiempo_formateado)
                                    print(f"Video generado exitosamente para {job_id}: {video_final_path}")
                                else:
                                    raise ValueError("La función crear_video_desde_imagenes no devolvió una ruta válida o el archivo no existe.")

                            except Exception as e_video:
                                current_job['tiempo_fin'] = time.time() # Marcar fin en error
                                tiempo_total = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                                tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                                print(f"Error durante la creación del video para {job_id}: {e_video}")
                                traceback.print_exc()
                                self.update_job_status_gui(job_id, f"Error Video: {str(e_video)[:50]}", tiempo_formateado)
                        else:
                             # Si no se pudo crear el video por falta de assets o función
                             current_job['tiempo_fin'] = time.time()
                             tiempo_total = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                             tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                             reason = ""
                             if not images_ok: reason += "Faltan Imágenes. "
                             if not current_job.get('archivo_voz'): reason += "Falta Audio. "
                             if not VIDEO_CREATOR_AVAILABLE: reason += "Video Creator Indisponible."
                             print(f"Omitiendo creación de video para {job_id}. Razón: {reason}")
                             self.update_job_status_gui(job_id, f"Video Omitido ({reason.strip()})", tiempo_formateado)
                        # <<< FIN: Lógica Creación Video >>>


                    else: # Falló la generación TTS inicial
                        error_msg = "Falló generación TTS"
                        print(f"{error_msg} para {job_id}")
                        current_job['tiempo_fin'] = audio_tiempo_fin # Usar tiempo de fallo TTS
                        tiempo_total = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                        tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                        self.update_job_status_gui(job_id, f"Error: {error_msg}", tiempo_formateado)

                except Exception as e_inner: # Captura errores dentro del procesamiento del job (TTS, SRT, Prompts, etc.)
                    error_msg = f"Excepción procesando {job_id}: {e_inner}"
                    print(error_msg)
                    logging.error(f'Error procesando trabajo: {job_id}', exc_info=True)
                    traceback.print_exc()

                    # Calcular tiempo transcurrido incluso en caso de error
                    if 'tiempo_inicio' in current_job and current_job['tiempo_inicio']:
                         current_job['tiempo_fin'] = time.time()
                         tiempo_transcurrido = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                         tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
                         self.update_job_status_gui(job_id, f"Error: {str(e_inner)[:60]}", tiempo_formateado)
                    else:
                         # Si el error ocurrió antes de fijar tiempo_inicio
                         self.update_job_status_gui(job_id, f"Error: {str(e_inner)[:60]}", "-")


            except Exception as e_outer: # Captura errores al obtener job de la cola o errores muy tempranos
                print(f"Error inesperado en el bucle principal del worker: {e_outer}")
                logging.error('Error en worker: %s', str(e_outer), exc_info=True)
                traceback.print_exc()
                # Si sabemos qué job falló, intentar actualizarlo
                if current_job and 'id' in current_job:
                     self.update_job_status_gui(current_job['id'], f"Error Worker: {str(e_outer)[:50]}", "-")


            finally:
                # Marcar la tarea como completada en la cola, si se obtuvo un job
                if current_job:
                    try:
                        self.job_queue.task_done()
                    except ValueError as e_td:
                        if "task_done() called too many times" in str(e_td):
                             # Esto puede pasar si hay un error y se llama task_done dos veces
                             print(f"Advertencia recuperable: task_done() llamado demasiadas veces para job {current_job.get('id', 'N/A')}. Ignorando.")
                        else:
                             print(f"ValueError inesperado en task_done() para job {current_job.get('id', 'N/A')}: {e_td}")
                             traceback.print_exc() # Imprimir traceback para errores inesperados
                    except Exception as e_final:
                        print(f"Excepción inesperada en finally/task_done para job {current_job.get('id', 'N/A')}: {e_final}")
                        traceback.print_exc()


        print("Worker de cola finalizado.")


    def calcular_imagenes_optimas(self, audio_duration, duracion_por_imagen=6.0, duracion_transicion=1.0, aplicar_transicion=False, fade_in=2.0, fade_out=2.0, respetar_duracion_exacta=True, repetir_ultimo_clip_config=True): # Renombrado arg
        """
        Calcula el número óptimo de imágenes y sus tiempos basado en la duración del audio.
        (Código de esta función sin cambios respecto a la versión anterior tuya)
        """
        # --- Código de calcular_imagenes_optimas sin cambios ---
        # ... (pega aquí tu código existente para calcular_imagenes_optimas) ...
        # Asegúrate de que al final devuelva: return num_imagenes, tiempos_imagenes
        # --- Ejemplo resumido de la lógica ---
        print(f"Calculando imágenes para audio de {audio_duration:.2f} segundos.")
        print(f" - Duración deseada: {duracion_por_imagen:.2f}s, Transición: {duracion_transicion:.2f}s (Aplicada: {aplicar_transicion})")
        print(f" - Respetar Duración: {respetar_duracion_exacta}, Repetir Último: {repetir_ultimo_clip_config}")

        num_imagenes = 1
        tiempos_imagenes = []
        duracion_efectiva = audio_duration # Simplificado, ya que fades no afectan cálculo aquí

        # Asegurar que la duración por imagen sea válida
        try:
             duracion_por_imagen = float(duracion_por_imagen)
             if duracion_por_imagen <= 0:
                  print("ADVERTENCIA: Duración por imagen <= 0. Ajustando a 1s.")
                  duracion_por_imagen = 1.0
        except (ValueError, TypeError):
             print("ADVERTENCIA: Duración por imagen inválida. Usando 15s.")
             duracion_por_imagen = 15.0

        # Asegurar duración transición válida
        try:
             duracion_transicion = float(duracion_transicion)
             if duracion_transicion < 0: duracion_transicion = 0.0
        except (ValueError, TypeError):
             duracion_transicion = 0.0 # Sin transición si el valor es inválido

        # Lógica principal (simplificada para ejemplo, usa tu lógica completa)
        if aplicar_transicion and duracion_transicion > 0:
             solapamiento = duracion_transicion / 2.0
             # Fórmula ajustada para estimar N imágenes con N-1 transiciones
             # total_dur = N * img_dur - (N-1) * solapamiento
             if duracion_por_imagen <= solapamiento:
                  print(f"Advertencia: Duración imagen ({duracion_por_imagen}) <= solapamiento ({solapamiento}). Ajustando a 1 imagen.")
                  num_imagenes = 1
                  duracion_ajustada = duracion_efectiva
             else:
                  # Estimación inicial (puede requerir tu lógica más compleja para videos largos)
                  num_imagenes = math.ceil((duracion_efectiva + solapamiento) / (duracion_por_imagen - solapamiento))
                  num_imagenes = max(2, num_imagenes) # Necesita al menos 2 para transición

                  # Recalcular duración para ajustar exactamente
                  duracion_ajustada = (duracion_efectiva + (num_imagenes - 1) * solapamiento) / num_imagenes
                  print(f"Ajuste con transiciones: {num_imagenes} imágenes, duración ajustada {duracion_ajustada:.2f}s")

             # Calcular tiempos con solapamiento
             tiempo_actual = 0.0
             for i in range(num_imagenes):
                  inicio = tiempo_actual
                  # El clip necesita durar 'duracion_ajustada' en total
                  fin_visual = inicio + duracion_ajustada
                  # El siguiente clip empieza antes si no es el último
                  if i < num_imagenes - 1:
                       tiempo_actual = fin_visual - solapamiento
                  else:
                       fin_visual = duracion_efectiva # Último clip termina exacto
                       tiempo_actual = duracion_efectiva
                  duracion_clip = fin_visual - inicio
                  tiempos_imagenes.append({'indice': i, 'inicio': inicio, 'fin': fin_visual, 'duracion': duracion_clip})

        else: # Sin transiciones
             if respetar_duracion_exacta:
                  # ... (tu lógica para respetar duración exacta y posible repetición) ...
                  num_imagenes_completas = int(duracion_efectiva / duracion_por_imagen) if duracion_por_imagen > 0 else 0
                  tiempo_restante = duracion_efectiva - (num_imagenes_completas * duracion_por_imagen)
                  umbral = 0.1 # Umbral pequeño para decidir si añadir clip

                  repetir_flag = False
                  tiempo_repeticion = 0.0

                  if tiempo_restante < umbral and num_imagenes_completas > 0:
                       num_imagenes = num_imagenes_completas
                  elif repetir_ultimo_clip_config and tiempo_restante < duracion_por_imagen * 0.7 and num_imagenes_completas > 0:
                       num_imagenes = num_imagenes_completas
                       repetir_flag = True
                       tiempo_repeticion = tiempo_restante
                       print(f"Repitiendo último clip por {tiempo_repeticion:.2f}s")
                  else:
                       num_imagenes = num_imagenes_completas + 1

                  num_imagenes = max(1, num_imagenes) # Al menos 1

                  tiempo_actual = 0.0
                  for i in range(num_imagenes):
                       inicio = tiempo_actual
                       if i == num_imagenes - 1: # Última imagen
                            if repetir_flag:
                                fin = inicio + duracion_por_imagen + tiempo_repeticion
                            else:
                                fin = duracion_efectiva
                       else:
                            fin = inicio + duracion_por_imagen
                       duracion_clip = fin - inicio
                       clip_info = {'indice': i, 'inicio': inicio, 'fin': fin, 'duracion': duracion_clip}
                       if i == num_imagenes -1 and repetir_flag:
                            clip_info['repetir'] = True
                            clip_info['tiempo_repeticion'] = tiempo_repeticion
                       tiempos_imagenes.append(clip_info)
                       tiempo_actual = fin

             else: # Distribuir uniformemente sin transiciones
                  num_imagenes = math.ceil(duracion_efectiva / duracion_por_imagen) if duracion_por_imagen > 0 else 1
                  num_imagenes = max(1, num_imagenes)
                  duracion_ajustada = duracion_efectiva / num_imagenes
                  print(f"Distribución uniforme: {num_imagenes} imágenes, duración {duracion_ajustada:.2f}s")
                  tiempo_actual = 0.0
                  for i in range(num_imagenes):
                       inicio = tiempo_actual
                       fin = min(inicio + duracion_ajustada, duracion_efectiva) if i < num_imagenes - 1 else duracion_efectiva
                       duracion_clip = fin - inicio
                       tiempos_imagenes.append({'indice': i, 'inicio': inicio, 'fin': fin, 'duracion': duracion_clip})
                       tiempo_actual = fin

        # Validación final (opcional pero recomendada)
        if tiempos_imagenes and abs(tiempos_imagenes[-1]['fin'] - duracion_efectiva) > 0.05:
            print(f"ADVERTENCIA: Tiempo final ({tiempos_imagenes[-1]['fin']:.2f}) no coincide con duración audio ({duracion_efectiva:.2f}). Ajustando.")
            tiempos_imagenes[-1]['fin'] = duracion_efectiva
            tiempos_imagenes[-1]['duracion'] = tiempos_imagenes[-1]['fin'] - tiempos_imagenes[-1]['inicio']

        print(f"Cálculo final: {num_imagenes} imágenes.")
        #for t in tiempos_imagenes: print(f"  {t}") # Descomentar para depuración detallada

        return num_imagenes, tiempos_imagenes
        # --- Fin Ejemplo resumido ---


    def update_job_status_gui(self, job_id, status, tiempo=""):
        """Actualiza el estado de un trabajo en la GUI."""
        # Usar root.after para asegurar que la actualización de la GUI
        # se ejecute en el hilo principal de Tkinter
        if hasattr(self.root, 'after'): # Verificar si root tiene 'after' (es Tk)
             self.root.after(0, self._update_treeview_item, job_id, status, tiempo)
        else: # Si root no es Tk (ej. pruebas unitarias), imprimir en consola
             print(f"GUI Update (Job {job_id}): Status='{status}', Time='{tiempo}'")


    def _update_treeview_item(self, job_id, status, tiempo=""):
        """Actualiza un elemento en el Treeview (debe llamarse desde el hilo principal)."""
        try:
            # Actualizar el item en el Treeview
            if self.tree_queue and self.tree_queue.exists(job_id):
                self.tree_queue.set(job_id, column="estado", value=status)
                if tiempo != "-": # Solo actualizar si no es el placeholder
                    self.tree_queue.set(job_id, column="tiempo", value=tiempo)

                # Actualizar también el estado en nuestro diccionario de rastreo
                if job_id in self.jobs_in_gui:
                    self.jobs_in_gui[job_id]['estado'] = status
            # else: # Comentado para reducir ruido en consola
            #     print(f"Advertencia: Job ID {job_id} no encontrado en Treeview para actualizar estado.")
        except tk.TclError as e:
            # Puede ocurrir si la ventana se cierra mientras se actualiza
            if "invalid command name" not in str(e): # Ignorar errores comunes de cierre
                 print(f"Error Tcl al actualizar Treeview (puede ser normal al cerrar): {e}")
        except Exception as e:
            print(f"Error inesperado al actualizar Treeview: {e}")
            traceback.print_exc()


    def get_queue_status(self):
        """Devuelve un resumen del estado de la cola."""
        # Contar trabajos directamente desde self.jobs_in_gui que es el reflejo de la GUI
        total_in_gui = len(self.jobs_in_gui)
        pendientes_en_cola = self.job_queue.qsize() # Los que aún no han empezado

        # Contar estados desde el diccionario que refleja la GUI
        completados = sum(1 for job in self.jobs_in_gui.values() if 'Video Completo' in job.get('estado', ''))
        errores = sum(1 for job in self.jobs_in_gui.values() if 'Error' in job.get('estado', ''))
        # Pendientes en GUI son los que no están completados ni con error ni en la cola real
        pendientes_gui = total_in_gui - completados - errores

        return {
            'total': total_in_gui + pendientes_en_cola, # Total trabajos añadidos
            'pendientes': pendientes_en_cola + pendientes_gui, # Suma de los en cola y los en proceso/cargados en GUI
            'completados': completados,
            'errores': errores
        }

    def regenerar_audio(self, job_id):
        """(Experimental) Intenta regenerar solo el audio y poner el job de nuevo en cola."""
        # --- Implementación similar a la anterior ---
        # ... (código de regenerar_audio) ...
        # NOTA: Esta función debería probablemente añadir un NUEVO job a la cola
        # con los datos actualizados, en lugar de modificar uno existente directamente.
        # O requeriría una lógica más compleja para reinsertar el job en el worker.
        print(f"Regeneración de audio para {job_id} - A IMPLEMENTAR CORRECTAMENTE (reinserción en cola)")
        return False # Placeholder


    def regenerar_subtitulos(self, job_id):
        """(Experimental) Intenta regenerar solo los subtítulos."""
        # --- Implementación similar a la anterior ---
        # ... (código de regenerar_subtitulos) ...
        print(f"Regeneración de subtítulos para {job_id} - A IMPLEMENTAR")
        return False # Placeholder


    def regenerar_prompts(self, job_id):
        """(Experimental) Intenta regenerar solo los prompts."""
        # --- Implementación similar a la anterior ---
        # ... (código de regenerar_prompts) ...
        print(f"Regeneración de prompts para {job_id} - A IMPLEMENTAR")
        return False # Placeholder


    def regenerar_imagenes(self, job_id):
        """(Experimental) Intenta regenerar solo las imágenes."""
        # --- Implementación similar a la anterior ---
        # ... (código de regenerar_imagenes) ...
        print(f"Regeneración de imágenes para {job_id} - A IMPLEMENTAR")
        return False # Placeholder

    # El método process_job ya no es necesario, _process_queue hace todo el trabajo.

# --- Fin de la clase BatchTTSManager ---

# (Puedes añadir aquí código de prueba si ejecutas este archivo directamente)
# if __name__ == '__main__':
#     # Ejemplo de cómo podrías probarlo (requiere un root Tkinter básico)
#     root = tk.Tk()
#     root.withdraw() # Ocultar ventana principal si solo es para prueba
#     manager = BatchTTSManager(root)
#     # ... añadir trabajos de prueba ...
#     # manager.add_project_to_queue(...)
#     # manager.start_worker()
#     # ... esperar o manejar la cola ...
#     # root.mainloop() # Necesario si hay GUI real