import traceback
import logging
import queue
import threading
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import time
import re
import math
import asyncio
from typing import List, Dict, Any
from moviepy import *
from prompt_generator import GEMINI_AVAILABLE, generar_prompts_con_gemini
from image_generator import generar_imagen_con_replicate, REPLICATE_AVAILABLE

# Importar el generador de voz en off
try:
    from tts_generator import create_voiceover_from_script, OUTPUT_FORMAT
except ImportError:
    print("Advertencia: No se pudo importar 'create_voiceover_from_script' o 'OUTPUT_FORMAT'.")
    print("Asegúrate de que el archivo tts_generator.py esté accesible.")
    # Define valores por defecto si la importación falla
    async def create_voiceover_from_script(script_path, output_path, voice=None):
        print(f"Simulando: Generando audio desde '{script_path}' a '{output_path}'")
        # En una ejecución real, esto crearía el archivo
        Path(output_path).touch()  # Crea un archivo vacío como marcador
        return output_path  # Devuelve la ruta simulada
    OUTPUT_FORMAT = "mp3"

# Importar generador de subtítulos
try:
    from subtitles import generate_srt_with_whisper, WHISPER_AVAILABLE
    if WHISPER_AVAILABLE:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("Advertencia: No se pudo importar WhisperModel a pesar de que WHISPER_AVAILABLE es True")
            WHISPER_AVAILABLE = False
except ImportError:
    print("Advertencia: No se pudo importar 'generate_srt_with_whisper' o 'WHISPER_AVAILABLE'.")
    print("Asegúrate de que el archivo subtitles.py esté accesible.")
    WHISPER_AVAILABLE = False

# Importar la función para crear video
try:
    from app import crear_video_desde_imagenes
except ImportError:
    print("Advertencia: No se pudo importar 'crear_video_desde_imagenes'.")
    print("Asegúrate de que el archivo app.py esté accesible.")
    # Define una función simulada si la importación falla
    def crear_video_desde_imagenes(project_folder, **kwargs):
        print(f"Simulando: Creando video para el proyecto '{project_folder}'")
        return None

class BatchTTSManager:
    """Gestor de procesamiento por lotes para la generación de voz en off."""
    
    def __init__(self, root, default_voice="es-EC-LuisNeural"):
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
        project_folder = self.project_base_dir / safe_title
        
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
            # Guardar ajustes para la creación del video
            'video_settings': video_settings or {}
        }
        
        # Guardar configuración del proyecto en un archivo JSON
        settings_file_path = project_folder / "settings.json"
        try:
            import json
            with open(settings_file_path, "w", encoding="utf-8") as f:
                # Asegurarse de que los datos sean serializables
                serializable_settings = {}
                if video_settings:
                    serializable_settings = video_settings.copy()
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
            self.jobs_in_gui[job_id] = job_data
        
        print(f"Proyecto '{title}' añadido a la cola (ID: {job_id}).")
        return True
    
    def start_worker(self):
        """Inicia el hilo trabajador si no está en ejecución."""
        if not self.worker_running:
            self.worker_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, args=(None,), daemon=True)
            self.worker_thread.start()
            print("Worker de cola iniciado.")
    
    def stop_worker(self):
        """Detiene el hilo trabajador (completará el trabajo actual)."""
        self.worker_running = False
        print("Worker de cola detenido. Completará el trabajo actual antes de terminar.")
    
    def _process_queue(self, whisper_model_loaded=None):
        """Procesa los trabajos en la cola de forma secuencial."""
        print("Worker de Cola iniciado.")
        while self.worker_running:
            try:
                # Esperar un trabajo con timeout para poder comprobar worker_running
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    # No hay trabajos, seguir esperando
                    continue
                
                job_id = job['id']
                title = job['titulo']
                script_path = job['guion_path']
                output_folder = Path(job['carpeta_salida'])
                voice = job['voz']
                audio_output_path = str(output_folder / f"voz.{OUTPUT_FORMAT}")
                
                # Actualizar estado y tiempo de inicio
                job['tiempo_inicio'] = time.time()
                self.update_job_status_gui(job_id, "Generando Audio...", "-")
                
                print(f"Procesando trabajo {job_id}: '{title}'")
                
                final_audio_path = None
                success_tts = False
                error_msg = ""
                
                try:
                    # Ejecutar la corutina create_voiceover_from_script
                    final_audio_path = asyncio.run(create_voiceover_from_script(
                        script_path=script_path,
                        output_audio_path=audio_output_path,
                        voice=voice
                    ))
                    
                    # Calcular tiempo transcurrido para la generación de audio
                    audio_tiempo_fin = time.time()
                    audio_tiempo_transcurrido = audio_tiempo_fin - job['tiempo_inicio']
                    audio_tiempo_formateado = f"{int(audio_tiempo_transcurrido // 60)}m {int(audio_tiempo_transcurrido % 60)}s"
                    
                    if final_audio_path and Path(final_audio_path).is_file():
                        print(f"Audio generado para {job_id}: {final_audio_path}")
                        # Actualizar el job con la ruta del audio generado
                        job['archivo_voz'] = final_audio_path
                        success_tts = True
                        
                        # --- Generar subtítulos con Whisper ---
                        if WHISPER_AVAILABLE:
                            self.update_job_status_gui(job_id, "Audio OK. Generando SRT...", audio_tiempo_formateado)
                            
                            # Buscar el modelo Whisper en la GUI
                            whisper_model = None
                            try:
                                # Intentar obtener el modelo Whisper directamente
                                if WHISPER_AVAILABLE:
                                    # Primero, buscar en la instancia actual de la aplicación
                                    app_instance = None
                                    for widget in self.root.winfo_children():
                                        if hasattr(widget, 'whisper_model'):
                                            app_instance = widget
                                            break
                                    
                                    if app_instance and hasattr(app_instance, 'whisper_model') and app_instance.whisper_model is not None:
                                        print("Usando modelo Whisper de la instancia de la aplicación")
                                        whisper_model = app_instance.whisper_model
                                    else:
                                        # Si no se encuentra en la GUI, crear un nuevo modelo
                                        print("No se encontró modelo Whisper en la GUI. Creando uno nuevo...")
                                        try:
                                            from faster_whisper import WhisperModel
                                            # Usar un modelo base por defecto
                                            whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                                            print("Modelo Whisper creado exitosamente")
                                        except Exception as e_model:
                                            print(f"Error al crear modelo Whisper: {e_model}")
                            except Exception as e_gui:
                                print(f"Error al buscar modelo Whisper: {e_gui}")
                            
                            # Generar subtítulos si tenemos el modelo
                            srt_output_path = str(output_folder / "subtitulos.srt")
                            srt_success = False
                            
                            if whisper_model:
                                try:
                                    # Obtener configuración del modelo Whisper de la GUI
                                    whisper_language = "es"  # Valor por defecto
                                    word_timestamps = True  # Valor por defecto
                                    
                                    # Intentar obtener configuración de la GUI
                                    if hasattr(app_instance, 'whisper_language') and hasattr(app_instance.whisper_language, 'get'):
                                        whisper_language = app_instance.whisper_language.get()
                                    
                                    if hasattr(app_instance, 'whisper_word_timestamps') and hasattr(app_instance.whisper_word_timestamps, 'get'):
                                        word_timestamps = app_instance.whisper_word_timestamps.get()
                                    
                                    print(f"Generando subtítulos con idioma: {whisper_language}, timestamps por palabra: {word_timestamps}")
                                    
                                    # Generar subtítulos con la configuración
                                    srt_success = generate_srt_with_whisper(
                                        whisper_model,
                                        final_audio_path,
                                        srt_output_path,
                                        language=whisper_language,
                                        word_timestamps=word_timestamps
                                    )
                                except Exception as e_srt:
                                    print(f"Error al generar subtítulos: {e_srt}")
                            else:
                                print("No se encontró el modelo Whisper para generar subtítulos.")
                            
                            # Actualizar el job con la información de subtítulos
                            if srt_success:
                                self.update_job_status_gui(job_id, "Audio y SRT OK", audio_tiempo_formateado)
                                job['archivo_subtitulos'] = srt_output_path
                                job['aplicar_subtitulos'] = True
                                print(f"Subtítulos generados exitosamente en: {srt_output_path}")

                                # --- NUEVO: Generación de Prompts ---
                                if GEMINI_AVAILABLE and srt_success:
                                    self.update_job_status_gui(job_id, "Audio/SRT OK. Generando Prompts...")
                                    try:
                                        # Leer guion
                                        with open(script_path, 'r', encoding='utf-8') as f:
                                            script_content = f.read()

                                        # Calcular número de imágenes
                                        temp_audio_clip = AudioFileClip(final_audio_path)
                                        audio_duration = temp_audio_clip.duration
                                        temp_audio_clip.close()
                                        duracion_por_imagen = job.get('duracion_img', 6.0)
                                        num_imagenes_necesarias = math.ceil(audio_duration / duracion_por_imagen)

                                        # Llamar a la función de generación de prompts
                                        estilo = job.get('settings', {}).get('estilo_imagenes', 'cinematográfico')
                                        lista_prompts = generar_prompts_con_gemini(
                                            script_content,
                                            num_imagenes_necesarias,
                                            job['titulo'],  # <--- Pasar el título del proyecto
                                            estilo_base=estilo
                                        )

                                        if lista_prompts:
                                            job['prompts_data'] = lista_prompts
                                            job['num_imagenes'] = len(lista_prompts)
                                            prompt_file_path = Path(output_folder) / "prompts.txt"
                                            with open(prompt_file_path, "w", encoding="utf-8") as f:
                                                for p_idx, data in enumerate(lista_prompts):
                                                    f.write(f"--- Imagen {p_idx+1} ---\n")
                                                    f.write(f"Segmento Guion (ES):\n{data['segmento_es']}\n\n")
                                                    f.write(f"Prompt Generado (EN):\n{data['prompt_en']}\n")
                                                    f.write("="*30 + "\n\n")
                                            
                                            print(f"Prompts guardados en {prompt_file_path}")
                                            self.update_job_status_gui(job_id, "Prompts OK. Esperando Vídeo/Imágenes.")

                                            # --- Generación de Imágenes con Replicate ---
                                            try:
                                                if REPLICATE_AVAILABLE:
                                                    self.update_job_status_gui(job_id, "Generando imágenes...", "")
                                                    imagenes_generadas = []
                                                    image_output_folder = output_folder / "imagenes"
                                                    image_output_folder.mkdir(parents=True, exist_ok=True)

                                                    for idx, prompt_data in enumerate(lista_prompts):
                                                        prompt_en = prompt_data['prompt_en']
                                                        if prompt_en.startswith("Error"):
                                                            continue

                                                        self.update_job_status_gui(job_id, f"Generando imagen {idx+1}/{len(lista_prompts)}...", "")

                                                        img_filename = f"{output_folder.name}_{idx+1:03d}.png"
                                                        img_path = generar_imagen_con_replicate(prompt_en, str(image_output_folder / img_filename))

                                                        if img_path:
                                                            imagenes_generadas.append(img_path)
                                                            print(f"Imagen {idx+1} generada: {img_path}")
                                                        else:
                                                            print(f"Error generando imagen {idx+1}")

                                                    if imagenes_generadas:
                                                        job['imagenes_generadas'] = imagenes_generadas
                                                        self.update_job_status_gui(job_id, "Imágenes generadas OK", "")
                                                    else:
                                                        self.update_job_status_gui(job_id, "Error generando imágenes", "")
                                            except Exception as e:
                                                print(f"Error generando imágenes con Replicate: {e}")
                                                self.update_job_status_gui(job_id, "Error generando imágenes", str(e))
                                        else:
                                            print(f"Fallo al generar prompts para {job_id}")
                                            self.update_job_status_gui(job_id, "Audio/SRT OK. Error Prompts.")

                                    except Exception as e_prompt:
                                        print(f"Error durante la generación de prompts para {job_id}: {e_prompt}")
                                        self.update_job_status_gui(job_id, "Audio/SRT OK. Error Prompts.")
                                # --- FIN NUEVO ---
                            else:
                                self.update_job_status_gui(job_id, "Audio OK. Error SRT", audio_tiempo_formateado)
                                job['aplicar_subtitulos'] = False
                        else:
                            # Si Whisper no está disponible, solo actualizar estado de audio
                            self.update_job_status_gui(job_id, "Audio Completo", audio_tiempo_formateado)
                        
                        # Guardar tiempo de finalización
                        job['tiempo_fin'] = time.time()
                    else:
                        error_msg = "Falló generación TTS"
                        print(f"{error_msg} para {job_id}")
                        self.update_job_status_gui(job_id, f"Error: {error_msg}", audio_tiempo_formateado)
                        job['tiempo_fin'] = audio_tiempo_fin
                
                except Exception as e_tts:
                    error_msg = f"Excepción TTS: {e_tts}"
                    print(f"Excepción en el worker (TTS) procesando {job_id}: {e_tts}")
                    logging.error('Error procesando trabajo: %s', job_id)
                    traceback.print_exc()
                    
                    # Calcular tiempo transcurrido incluso en caso de error
                    job['tiempo_fin'] = time.time()
                    tiempo_transcurrido = job['tiempo_fin'] - job['tiempo_inicio']
                    tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
                    
                    self.update_job_status_gui(job_id, f"Error: {error_msg}", tiempo_formateado)
                
                finally:
                    # --- Solución temporal error task_done ---
                    try:
                        self.job_queue.task_done()
                    except ValueError as e_td:
                        if "called too many times" in str(e_td):
                            print(f"Advertencia: task_done() llamado demasiadas veces para job {job_id}. Ignorando.")
                        else:
                            print(f"ValueError inesperado en task_done() para job {job_id}: {e_td}")
                    except Exception as e_final:
                        print(f"Excepción inesperada en finally para job {job_id}: {e_final}")
                    # ----------------------------------------
            
            except Exception as e:
                print(f"Error inesperado en el worker: {e}")
                logging.error('Error en worker: %s', str(e))
                traceback.print_exc()
        
        print("Worker de cola finalizado.")
    
    def update_job_status_gui(self, job_id, status, tiempo=""):
        """Actualiza el estado de un trabajo en la GUI."""
        # Usar root.after para asegurar que la actualización de la GUI
        # se ejecute en el hilo principal de Tkinter
        self.root.after(0, self._update_treeview_item, job_id, status, tiempo)
    
    def _update_treeview_item(self, job_id, status, tiempo=""):
        """Actualiza un elemento en el Treeview (debe llamarse desde el hilo principal)."""
        try:
            # Actualizar el item en el Treeview
            if self.tree_queue and self.tree_queue.exists(job_id):
                self.tree_queue.set(job_id, column="estado", value=status)
                if tiempo != "-":
                    self.tree_queue.set(job_id, column="tiempo", value=tiempo)
                
                # Actualizar también el estado en nuestro diccionario de rastreo
                if job_id in self.jobs_in_gui:
                    self.jobs_in_gui[job_id]['estado'] = status
            else:
                print(f"Advertencia: Job ID {job_id} no encontrado en Treeview para actualizar estado.")
        except tk.TclError as e:
            # Puede ocurrir si la ventana se cierra mientras se actualiza
            print(f"Error Tcl al actualizar Treeview (puede ser normal al cerrar): {e}")
        except Exception as e:
            print(f"Error inesperado al actualizar Treeview: {e}")
    
    def get_queue_status(self):
        """Devuelve un resumen del estado de la cola."""
        total = self.job_queue.qsize() + len(self.jobs_in_gui)
        pendientes = self.job_queue.qsize()
        completados = sum(1 for job in self.jobs_in_gui.values() if 'Audio Completo' in job.get('estado', ''))
        errores = sum(1 for job in self.jobs_in_gui.values() if 'Error' in job.get('estado', ''))
        
        return {
            'total': total,
            'pendientes': pendientes,
            'completados': completados,
            'errores': errores
        }