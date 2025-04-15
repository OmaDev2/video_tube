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
    
    def add_existing_project_to_queue(self, title, script, project_folder, voice=None, video_settings=None):
        """
        Añade un proyecto existente a la cola de procesamiento.
        
        Args:
            title: Título del proyecto
            script: Texto del guion para la voz en off
            project_folder: Ruta a la carpeta del proyecto existente
            voice: Voz a utilizar (opcional, usa default_voice si no se especifica)
            video_settings: Diccionario con ajustes para la creación del video
        
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
            'guion_path': str(project_folder / "guion.txt"),
            'carpeta_salida': str(project_folder),
            'voz': voice,
            'estado': 'Cargado',
            'tiempo_inicio': None,
            'tiempo_fin': None,
            'script': script  # Guardamos una copia del script en memoria
        }
        
        # Verificar si existen archivos de audio, subtítulos, prompts e imágenes
        audio_path = project_folder / f"voz.{OUTPUT_FORMAT}"
        if audio_path.exists():
            job_data['archivo_voz'] = str(audio_path)
            job_data['estado'] = 'Audio Existente'
        
        subtitles_path = project_folder / "subtitulos.srt"
        if subtitles_path.exists():
            job_data['archivo_subtitulos'] = str(subtitles_path)
            job_data['aplicar_subtitulos'] = True
        
        prompts_path = project_folder / "prompts.txt"
        if prompts_path.exists():
            # Intentar cargar los prompts desde el archivo
            try:
                # Leer el archivo de prompts y reconstruir la estructura
                with open(prompts_path, "r", encoding="utf-8") as f:
                    prompts_content = f.read()
                
                # Procesar el contenido para extraer los prompts
                # Este es un enfoque simple, podría necesitar ajustes según el formato exacto
                import re
                
                # Buscar patrones de segmentos y prompts
                segments = re.findall(r"Segmento Guion \(ES\):\n(.+?)\n\n", prompts_content, re.DOTALL)
                prompts = re.findall(r"Prompt Generado \(EN\):\n(.+?)\n=", prompts_content, re.DOTALL)
                
                if segments and prompts and len(segments) == len(prompts):
                    prompts_data = []
                    for i in range(len(segments)):
                        prompts_data.append({
                            'segmento_es': segments[i].strip(),
                            'prompt_en': prompts[i].strip()
                        })
                    
                    job_data['prompts_data'] = prompts_data
                    job_data['num_imagenes'] = len(prompts_data)
                    print(f"Cargados {len(prompts_data)} prompts desde {prompts_path}")
            except Exception as e:
                print(f"Error al cargar prompts desde {prompts_path}: {e}")
        
        # Buscar imágenes en la carpeta de imágenes
        images_folder = project_folder / "imagenes"
        if images_folder.exists() and images_folder.is_dir():
            # Buscar archivos de imagen
            image_extensions = [".jpg", ".jpeg", ".png"]
            images = []
            for ext in image_extensions:
                images.extend(list(images_folder.glob(f"*{ext}")))
            
            if images:
                job_data['imagenes_generadas'] = [str(img) for img in images]
                print(f"Encontradas {len(images)} imágenes en {images_folder}")
        
        # Agregar configuración de video si se proporciona
        if video_settings:
            job_data['video_settings'] = video_settings
        
        # Añadir a la GUI (Treeview) si ya existe
        if self.tree_queue:
            self.tree_queue.insert("", tk.END, iid=job_id, values=(title, job_data['estado'], '-'))
            self.jobs_in_gui[job_id] = job_data
        
        print(f"Proyecto existente '{title}' cargado en la cola (ID: {job_id}).")        
        return job_id
    
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
                                    
                                    # Obtener la opción de subtítulos en mayúsculas
                                    uppercase = False
                                    if hasattr(app_instance, 'subtitles_uppercase') and hasattr(app_instance.subtitles_uppercase, 'get'):
                                        uppercase = app_instance.subtitles_uppercase.get()
                                    
                                    print(f"Generando subtítulos con idioma: {whisper_language}, timestamps por palabra: {word_timestamps}, mayúsculas: {uppercase}")
                                    
                                    # Generar subtítulos con la configuración
                                    srt_success = generate_srt_with_whisper(
                                        whisper_model,
                                        final_audio_path,
                                        srt_output_path,
                                        language=whisper_language,
                                        word_timestamps=word_timestamps,
                                        uppercase=uppercase
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

                                        # Calcular número de imágenes usando la función optimizada
                                        temp_audio_clip = AudioFileClip(final_audio_path)
                                        audio_duration = temp_audio_clip.duration
                                        temp_audio_clip.close()
                                        
                                        # Imprimir todos los parámetros del job para depuración
                                        print("\nParámetros del trabajo:")
                                        for k, v in job.items():
                                            if k != 'script' and k != 'prompts_data':  # Evitar imprimir textos largos
                                                print(f"  {k}: {v}")
                                        
                                        # Obtener parámetros relevantes del job
                                        # Intentar obtener la duración de imagen de diferentes fuentes posibles
                                        duracion_por_imagen = None
                                        
                                        # 1. Intentar obtener de video_settings.duracion_img (valor de la interfaz gráfica)
                                        if 'video_settings' in job and isinstance(job['video_settings'], dict) and 'duracion_img' in job['video_settings']:
                                            duracion_por_imagen = job['video_settings'].get('duracion_img')
                                            print(f"Duración obtenida de video_settings.duracion_img: {duracion_por_imagen}")
                                        
                                        # 2. Intentar obtener de settings.duracion_img
                                        elif 'settings' in job and isinstance(job['settings'], dict) and 'duracion_img' in job['settings']:
                                            duracion_por_imagen = job['settings'].get('duracion_img')
                                            print(f"Duración obtenida de settings.duracion_img: {duracion_por_imagen}")
                                        
                                        # 3. Intentar obtener directamente de duracion_img
                                        elif 'duracion_img' in job:
                                            duracion_por_imagen = job.get('duracion_img')
                                            print(f"Duración obtenida de duracion_img: {duracion_por_imagen}")
                                        
                                        # 4. Usar valor predeterminado si no se encuentra
                                        else:
                                            duracion_por_imagen = 20.0  # Valor predeterminado igual al de la interfaz gráfica
                                            print(f"Usando duración predeterminada: {duracion_por_imagen}")
                                        
                                        # Asegurarse de que sea un número válido
                                        try:
                                            duracion_por_imagen = float(duracion_por_imagen)
                                        except (ValueError, TypeError):
                                            duracion_por_imagen = 15.0
                                            print(f"Error al convertir duración, usando valor predeterminado: {duracion_por_imagen}")
                                        
                                        # Obtener parámetros de configuración desde video_settings
                                        video_settings_job = job.get('video_settings', {})
                                        
                                        # Obtener configuración de transiciones
                                        aplicar_transicion = video_settings_job.get('aplicar_transicion', False)
                                        duracion_transicion_setting = video_settings_job.get('duracion_transicion', 1.0)
                                        
                                        # Usar la duración de transición solo si se aplican
                                        duracion_transicion_usada = duracion_transicion_setting if aplicar_transicion else 0.0
                                        
                                        # Obtener la preferencia de respetar duración exacta
                                        respetar_duracion_exacta_setting = video_settings_job.get('respetar_duracion_exacta', True)
                                        
                                        # Obtener configuración de fade in/out
                                        fade_in = video_settings_job.get('duracion_fade_in', 2.0)
                                        fade_out = video_settings_job.get('duracion_fade_out', 2.0)
                                        
                                        print(f"\n--- Calculando Imágenes Óptimas para Job {job_id} ---")
                                        print(f"Audio Duration: {audio_duration:.2f}s")
                                        print(f"Duración por Imagen (config): {duracion_por_imagen:.2f}s")
                                        print(f"Aplicar Transición: {aplicar_transicion}")
                                        print(f"Duración Transición (config): {duracion_transicion_setting:.2f}s")
                                        print(f"Respetar Duración Exacta (config): {respetar_duracion_exacta_setting}")
                                        print(f"Fade In: {fade_in:.2f}s, Fade Out: {fade_out:.2f}s")
                                        print(f"----------------------------------------------------\n")
                                        
                                        # Calcular el número óptimo de imágenes
                                        num_imagenes_necesarias, tiempos_imagenes = self.calcular_imagenes_optimas(
                                            audio_duration=audio_duration,
                                            duracion_por_imagen=duracion_por_imagen,
                                            duracion_transicion=duracion_transicion_usada,
                                            aplicar_transicion=aplicar_transicion,
                                            fade_in=fade_in,
                                            fade_out=fade_out,
                                            respetar_duracion_exacta=respetar_duracion_exacta_setting
                                        )
                                        
                                        # Guardar los tiempos de las imágenes para usarlos en la generación de video
                                        job['tiempos_imagenes'] = tiempos_imagenes
                                        job['num_imagenes'] = num_imagenes_necesarias  # Actualizar el número de imágenes en el job
                                        
                                        # Verificar si hay información de repetición del último clip
                                        for clip in tiempos_imagenes:
                                            if 'repetir' in clip and clip['repetir']:
                                                job['repetir_ultimo_clip'] = True
                                                job['tiempo_repeticion_ultimo_clip'] = clip['tiempo_repeticion']
                                                print(f"Configurando repetición del último clip durante {clip['tiempo_repeticion']:.2f}s")
                                                break
                                        
                                        # Asegurar que los parámetros estén en el job para la creación del video
                                        if 'video_settings' not in job:
                                            job['video_settings'] = {}
                                        job['video_settings']['aplicar_transicion'] = aplicar_transicion
                                        job['video_settings']['duracion_transicion'] = duracion_transicion_usada

                                        # Llamar a la función de generación de prompts
                                        # Obtener el estilo de prompts seleccionado del diccionario 'video_settings' dentro del job
                                        video_settings_del_job = job.get('video_settings', {})  # Obtener el diccionario de ajustes, o uno vacío si no existe
                                        estilo = video_settings_del_job.get('estilo_imagenes', 'default')  # Obtener el estilo de ese diccionario
                                        
                                        # Imprimir información detallada para depuración
                                        print(f"\n\n=== INFORMACIÓN DE ESTILO DE PROMPTS ===\n")
                                        print(f"Estilo seleccionado en interfaz: '{estilo}'")
                                        print(f"Nombre del estilo: '{video_settings_del_job.get('nombre_estilo', 'No especificado')}'")
                                        print(f"Ajustes completos: {video_settings_del_job}")
                                        
                                        # Verificar que el estilo existe en el gestor de prompts
                                        try:
                                            from prompt_manager import PromptManager
                                            prompt_manager = PromptManager()
                                            estilos_disponibles = prompt_manager.get_prompt_ids()
                                            print(f"Estilos disponibles: {estilos_disponibles}")
                                            
                                            # Si el estilo no existe, intentar encontrar una coincidencia por nombre
                                            if estilo not in estilos_disponibles:
                                                print(f"ADVERTENCIA: El estilo '{estilo}' no existe en el gestor de prompts.")
                                                
                                                # Intentar encontrar el estilo por nombre
                                                nombre_estilo = video_settings_del_job.get('nombre_estilo', '')
                                                if nombre_estilo:
                                                    # Mapa de nombres a IDs
                                                    nombre_a_id = {
                                                        'Cinematográfico': 'default',
                                                        'Terror': 'terror',
                                                        'Animación': 'animacion',
                                                        'imagenes Psicodelicas': 'psicodelicas'
                                                    }
                                                    
                                                    if nombre_estilo in nombre_a_id:
                                                        estilo = nombre_a_id[nombre_estilo]
                                                        print(f"Usando estilo '{estilo}' basado en el nombre '{nombre_estilo}'")
                                        except Exception as e:
                                            print(f"Error al verificar estilos: {e}")
                                        
                                        # Asegurarse de que el estilo sea un string válido
                                        if not estilo or estilo == "None" or estilo == "":
                                            estilo = "default"
                                        
                                        # Mostrar información detallada para depuración
                                        print(f"\n\n=== GENERACIÓN DE PROMPTS ===\n")
                                        print(f"Estilo seleccionado: '{estilo}'")
                                        print(f"Título del proyecto: '{job['titulo']}'")
                                        print(f"Nombre del estilo: '{job.get('nombre_estilo', 'No especificado')}'")                                        
                                        
                                        # Verificar que el estilo existe en el gestor de prompts
                                        try:
                                            from prompt_manager import PromptManager
                                            prompt_manager = PromptManager()
                                            estilos_disponibles = prompt_manager.get_prompt_ids()
                                            print(f"Estilos disponibles: {estilos_disponibles}")
                                            
                                            if estilo not in estilos_disponibles:
                                                print(f"ADVERTENCIA: El estilo '{estilo}' no existe. Usando estilo por defecto.")
                                                estilo = "default"
                                        except Exception as e:
                                            print(f"Error al verificar estilos: {e}")
                                        
                                        print(f"Estilo final utilizado: '{estilo}'\n")
                                        
                                        # Generar los prompts con el estilo seleccionado
                                        lista_prompts = generar_prompts_con_gemini(
                                            script_content,
                                            num_imagenes_necesarias,
                                            job['titulo'],  # <--- Pasar el título del proyecto
                                            estilo_base=estilo,
                                            tiempos_imagenes=tiempos_imagenes  # <--- Pasar la información de tiempos
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
    
    def calcular_imagenes_optimas(self, audio_duration, duracion_por_imagen=6.0, duracion_transicion=1.0, aplicar_transicion=False, fade_in=2.0, fade_out=2.0, respetar_duracion_exacta=True, repetir_ultimo_clip=True):
        """
        Calcula el número óptimo de imágenes y sus tiempos basado en la duración del audio.

        Esta función tiene en cuenta:
        - La duración total del audio
        - La duración deseada por imagen
        - La duración de las transiciones (si se aplican)
        - Los efectos de fade in/out (actualmente no usados en el cálculo de número/duración)

        Args:
            audio_duration (float): Duración total del audio en segundos
            duracion_por_imagen (float): Duración deseada para cada imagen en segundos
            duracion_transicion (float): Duración de cada transición en segundos
            aplicar_transicion (bool): Si se aplicarán transiciones entre imágenes
            fade_in (float): Duración del fade in al inicio del video
            fade_out (float): Duración del fade out al final del video
            respetar_duracion_exacta (bool): Si es True y NO hay transiciones, respeta la duración exacta. Si hay transiciones, se ignora para ajustar.

        Returns:
            tuple: (num_imagenes, tiempos_imagenes)
                - num_imagenes (int): Número óptimo de imágenes
                - tiempos_imagenes (list): Lista de diccionarios con los tiempos de cada imagen
        """
        print(f"Calculando imágenes para audio de {audio_duration:.2f} segundos.")
        print(f" - Duración por imagen deseada: {duracion_por_imagen:.2f}s")
        print(f" - Transiciones aplicadas: {aplicar_transicion}")
        if aplicar_transicion:
            print(f" - Duración transición: {duracion_transicion:.2f}s")
        print(f" - Respetar duración exacta (solo si no hay transiciones): {respetar_duracion_exacta}")
        print(f" - Repetir último clip si falta poco tiempo: {repetir_ultimo_clip}")


        # Asegurarse de que la duración por imagen sea mayor que la transición si se aplica
        if aplicar_transicion and duracion_por_imagen <= duracion_transicion:
             print(f"ADVERTENCIA: La duración por imagen ({duracion_por_imagen}s) es menor o igual a la duración de la transición ({duracion_transicion}s). Esto puede causar problemas.")
             # Forzar una duración mínima para evitar problemas con videos largos
             duracion_por_imagen = duracion_transicion + 1.0
             print(f"Ajustando duración por imagen a {duracion_por_imagen}s para evitar problemas")


        # Ajustar la duración efectiva teniendo en cuenta los fades (actualmente no se usa, pero se mantiene la variable)
        duracion_efectiva = audio_duration

        # --- Lógica Principal ---
        if aplicar_transicion:
            # SIEMPRE ajustar si hay transiciones para cubrir el tiempo total
            print("Aplicando lógica de ajuste debido a transiciones.")

            # MoviePy crossfade solapa la mitad de la duración de la transición
            solapamiento_por_transicion = duracion_transicion / 2.0

            # Estimación inicial del número de imágenes
            # El tiempo efectivo que cubre cada imagen (menos el solapamiento que se pierde con la siguiente)
            tiempo_efectivo_por_imagen = duracion_por_imagen - solapamiento_por_transicion
            if tiempo_efectivo_por_imagen <= 0:
                 print("ADVERTENCIA: Tiempo efectivo por imagen <= 0 debido a transición larga. Ajustando a 1 imagen.")
                 num_imagenes = 1
                 duracion_ajustada = duracion_efectiva # La única imagen dura todo el audio
            else:
                # N imágenes necesitan N-1 transiciones. La duración total es aprox:
                # N * duracion_por_imagen - (N-1) * solapamiento_por_transicion
                # Método mejorado para calcular el número de imágenes para videos largos
                # Fórmula: (duracion_total + solapamiento) / (duracion_imagen - solapamiento/2)
                # Esta fórmula es más precisa para videos largos con transiciones
                num_imagenes_estimado = math.ceil((duracion_efectiva + solapamiento_por_transicion) / 
                                               max(0.5, tiempo_efectivo_por_imagen)) # Evitar división por valores muy pequeños
                
                # Para videos largos (>60s), usar una aproximación más conservadora
                if duracion_efectiva > 60.0:
                    # Usar floor en lugar de ceil para videos largos y añadir 1
                    # Esto evita tener demasiadas imágenes con duraciones muy cortas
                    num_imagenes_alternativo = math.floor(duracion_efectiva / duracion_por_imagen) + 1
                    # Tomar el menor de los dos valores para evitar sobrestimación
                    num_imagenes_estimado = min(num_imagenes_estimado, num_imagenes_alternativo)
                    print(f"Video largo detectado: Usando estimación conservadora de {num_imagenes_estimado} imágenes")
                
                num_imagenes = max(2, num_imagenes_estimado) # Necesitamos al menos 2 para una transición

            # Recalcular la duración por imagen para distribuir uniformemente y llenar el audio
            # duracion_efectiva = num_imagenes * duracion_ajustada - (num_imagenes - 1) * solapamiento_por_transicion
            if num_imagenes <= 1:
                 duracion_ajustada = duracion_efectiva
            else:
                # Despejamos duracion_ajustada:
                duracion_ajustada = (duracion_efectiva + (num_imagenes - 1) * solapamiento_por_transicion) / num_imagenes
                
                # Verificación adicional para videos largos
                # Si la duración ajustada es significativamente menor que la duración deseada,
                # podría indicar un cálculo incorrecto del número de imágenes
                if duracion_ajustada < duracion_por_imagen * 0.5 and duracion_efectiva > 60.0:
                    print(f"ADVERTENCIA: La duración ajustada ({duracion_ajustada:.2f}s) es mucho menor que la duración deseada ({duracion_por_imagen:.2f}s).")
                    print("Recalculando número de imágenes para evitar clips demasiado cortos...")
                    # Usar un enfoque más conservador para videos largos
                    num_imagenes_nuevo = math.floor(duracion_efectiva / duracion_por_imagen) + 1
                    num_imagenes = max(2, num_imagenes_nuevo)
                    # Recalcular la duración ajustada con el nuevo número de imágenes
                    duracion_ajustada = (duracion_efectiva + (num_imagenes - 1) * solapamiento_por_transicion) / num_imagenes

            print(f"Ajustando para transiciones: {num_imagenes} imágenes con duración ajustada de {duracion_ajustada:.2f}s")

            # Calcular los tiempos exactos de cada imagen
            tiempos_imagenes = []
            tiempo_actual = 0.0

            for i in range(num_imagenes):
                tiempo_inicio = tiempo_actual
                # La duración visual del clip antes de que empiece a solaparse el siguiente
                tiempo_fin_visual = tiempo_inicio + duracion_ajustada

                # El punto donde empieza el siguiente clip (teniendo en cuenta el solapamiento)
                if i < num_imagenes - 1:
                     tiempo_actual = tiempo_fin_visual - solapamiento_por_transicion
                else:
                    # La última imagen termina exactamente al final del audio
                     tiempo_fin_visual = audio_duration
                     tiempo_actual = audio_duration # No hay siguiente imagen

                duracion_clip_actual = tiempo_fin_visual - tiempo_inicio

                tiempos_imagenes.append({
                    'indice': i,
                    'inicio': tiempo_inicio,
                    'fin': tiempo_fin_visual, # El tiempo donde este clip termina visualmente
                    'duracion': duracion_clip_actual
                })

        else:
            # --- SIN TRANSICIONES ---
            print("No se aplican transiciones.")
            if respetar_duracion_exacta:
                print(f"Usando duración exacta de {duracion_por_imagen:.2f}s por imagen.")
                if duracion_por_imagen <= 0:
                    print("ADVERTENCIA: Duración por imagen es <= 0. Usando 1 imagen.")
                    num_imagenes = 1
                else:
                    # Calcular el número de imágenes completas que caben en el audio
                    num_imagenes_completas = int(duracion_efectiva / duracion_por_imagen)
                    tiempo_restante = duracion_efectiva - (num_imagenes_completas * duracion_por_imagen)

                    # Umbral mejorado para videos largos (0.5s en lugar de 0.01s)
                    # Esto evita crear imágenes muy cortas al final
                    umbral_tiempo_restante = 0.5 if duracion_efectiva > 60.0 else 0.01
                    
                    # Decidir si añadir una imagen más o repetir la última
                    if tiempo_restante > umbral_tiempo_restante:
                        if repetir_ultimo_clip and tiempo_restante < duracion_por_imagen * 0.7 and num_imagenes_completas > 0:
                            # Si falta menos del 70% de una duración completa, repetir el último clip en lugar de añadir uno nuevo
                            print(f"Tiempo restante ({tiempo_restante:.2f}s) menor al 70% de duración por imagen. Repitiendo último clip.")
                            num_imagenes = num_imagenes_completas
                            # Marcar que el último clip se repetirá
                            self.repetir_ultimo_clip = True
                            self.tiempo_repeticion_ultimo_clip = tiempo_restante
                        else:
                            # Añadir una imagen completa nueva
                            num_imagenes = num_imagenes_completas + 1
                            self.repetir_ultimo_clip = False
                    elif num_imagenes_completas == 0:
                         num_imagenes = 1 # Asegurar al menos una imagen si la duración es muy corta
                         self.repetir_ultimo_clip = False
                    else:
                        num_imagenes = num_imagenes_completas
                        self.repetir_ultimo_clip = False

                # Asegurarnos de que tenemos al menos 1 imagen
                num_imagenes = max(1, num_imagenes)
                print(f"Número de imágenes necesarias: {num_imagenes}")
                
                # Mostrar información sobre repetición si está activada
                if hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip:
                    print(f"El último clip se repetirá durante {self.tiempo_repeticion_ultimo_clip:.2f}s adicionales")

                # Calcular los tiempos exactos de cada imagen
                tiempos_imagenes = []
                tiempo_actual = 0.0

                for i in range(num_imagenes):
                    tiempo_inicio = tiempo_actual
                    # La última imagen ocupa el tiempo restante o se repite
                    if i == num_imagenes - 1:
                        # Si es la última imagen y estamos repitiendo
                        if hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip:
                            # La duración normal + el tiempo de repetición
                            tiempo_fin = tiempo_inicio + duracion_por_imagen + self.tiempo_repeticion_ultimo_clip
                            print(f"Clip {i+1} extendido: duración normal ({duracion_por_imagen:.2f}s) + repetición ({self.tiempo_repeticion_ultimo_clip:.2f}s)")
                        else:
                            # Comportamiento normal: la última imagen llega hasta el final
                            tiempo_fin = audio_duration
                    else:
                        tiempo_fin = min(tiempo_inicio + duracion_por_imagen, audio_duration)

                    duracion_actual = tiempo_fin - tiempo_inicio
                    tiempo_actual = tiempo_fin

                    # Crear el diccionario base
                    clip_info = {
                        'indice': i,
                        'inicio': tiempo_inicio,
                        'fin': tiempo_fin,
                        'duracion': duracion_actual
                    }
                    
                    # Añadir información de repetición si es el último clip y se repite
                    if i == num_imagenes - 1 and hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip:
                        clip_info['repetir'] = True
                        clip_info['duracion_normal'] = duracion_por_imagen
                        clip_info['tiempo_repeticion'] = self.tiempo_repeticion_ultimo_clip
                    
                    tiempos_imagenes.append(clip_info)

            else:
                # Distribuir uniformemente SIN transiciones
                 print("Distribuyendo imágenes uniformemente (sin transiciones).")
                 if duracion_por_imagen <= 0:
                     print("ADVERTENCIA: Duración por imagen es <= 0. Usando 1 imagen.")
                     num_imagenes = 1
                     duracion_ajustada = duracion_efectiva
                 else:
                    # Para videos largos, usar una aproximación más conservadora
                    # que evite tener demasiadas imágenes con duraciones muy cortas
                    if duracion_efectiva > 60.0:
                        # Usar floor en lugar de ceil para videos largos
                        # y añadir 1 para compensar, esto da duraciones más cercanas a lo deseado
                        num_imagenes = math.floor(duracion_efectiva / duracion_por_imagen) + 1
                    else:
                        num_imagenes = math.ceil(duracion_efectiva / duracion_por_imagen)
                    
                    num_imagenes = max(1, num_imagenes) # Al menos 1 imagen
                    duracion_ajustada = duracion_efectiva / num_imagenes

                 print(f"{num_imagenes} imágenes con duración ajustada de {duracion_ajustada:.2f}s")

                 tiempos_imagenes = []
                 tiempo_actual = 0.0
                 for i in range(num_imagenes):
                     tiempo_inicio = tiempo_actual
                     # La última imagen llena hasta el final exacto
                     if i == num_imagenes - 1:
                         tiempo_fin = audio_duration
                     else:
                         tiempo_fin = tiempo_inicio + duracion_ajustada

                     duracion_actual = tiempo_fin - tiempo_inicio
                     tiempo_actual = tiempo_fin

                     tiempos_imagenes.append({
                         'indice': i,
                         'inicio': tiempo_inicio,
                         'fin': tiempo_fin,
                         'duracion': duracion_actual
                     })

        # --- FIN Lógica Principal ---

        # Imprimir información detallada para depuración
        print("Distribución final de tiempos de imágenes:")
        total_duration_check = 0
        for t in tiempos_imagenes:
            print(f"  Imagen {t['indice']+1}: Inicio={t['inicio']:.2f}s, Fin={t['fin']:.2f}s (Duración Clip: {t['duracion']:.2f}s)")
            if not aplicar_transicion:
                total_duration_check += t['duracion']
            # Si hay transiciones, la suma simple de duraciones no es igual a audio_duration debido al solapamiento

        if not aplicar_transicion:
             print(f"Duración total cubierta (sin transiciones): {total_duration_check:.2f}s (Audio: {audio_duration:.2f}s)")
        else:
             # Con transiciones, el 'fin' de la última imagen debe coincidir con audio_duration
             if tiempos_imagenes:
                 print(f"Tiempo final de la última imagen: {tiempos_imagenes[-1]['fin']:.2f}s (Audio: {audio_duration:.2f}s)")


        # Validar que la última imagen termine al final del audio
        if tiempos_imagenes and abs(tiempos_imagenes[-1]['fin'] - audio_duration) > 0.05: # Tolerancia pequeña
             print(f"ADVERTENCIA: El tiempo final calculado ({tiempos_imagenes[-1]['fin']:.2f}s) no coincide exactamente con la duración del audio ({audio_duration:.2f}s).")
             # Corregir el tiempo final de la última imagen para asegurar que coincida
             tiempos_imagenes[-1]['fin'] = audio_duration
             tiempos_imagenes[-1]['duracion'] = tiempos_imagenes[-1]['fin'] - tiempos_imagenes[-1]['inicio']
             print(f"Corregido: La última imagen ahora termina en {tiempos_imagenes[-1]['fin']:.2f}s con duración {tiempos_imagenes[-1]['duracion']:.2f}s")
             
             # Marcar si esta imagen tiene repetición
             if hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip:
                 tiempos_imagenes[-1]['repetir'] = True
                 tiempos_imagenes[-1]['duracion_normal'] = duracion_por_imagen
                 tiempos_imagenes[-1]['tiempo_repeticion'] = self.tiempo_repeticion_ultimo_clip
                 print(f"Marcada la última imagen para repetición durante {self.tiempo_repeticion_ultimo_clip:.2f}s")
        
        # Verificación final del número de imágenes para videos largos
        if audio_duration > 120.0 and num_imagenes < 10:
            print(f"ADVERTENCIA: Video largo ({audio_duration:.2f}s) con pocas imágenes ({num_imagenes}). Esto podría no ser lo esperado.")
            print("Considera revisar la configuración de duración por imagen y transiciones.")
        
        # Imprimir resumen final para facilitar depuración
        print(f"\nRESUMEN FINAL: {num_imagenes} imágenes para {audio_duration:.2f}s de audio")
        if aplicar_transicion:
            print(f"Con transiciones de {duracion_transicion:.2f}s y duración ajustada de {duracion_ajustada:.2f}s por imagen")
        else:
            if respetar_duracion_exacta:
                print(f"Sin transiciones, respetando duración exacta de {duracion_por_imagen:.2f}s (excepto posiblemente la última imagen)")
            else:
                print(f"Sin transiciones, con duración ajustada uniforme de {duracion_ajustada:.2f}s por imagen")
        
        # Verificación final del número de imágenes para videos largos
        if audio_duration > 120.0 and num_imagenes < 10:
            print(f"ADVERTENCIA: Video largo ({audio_duration:.2f}s) con pocas imágenes ({num_imagenes}). Esto podría no ser lo esperado.")
            print("Considera revisar la configuración de duración por imagen y transiciones.")
        
        # Imprimir resumen final para facilitar depuración
        print(f"\nRESUMEN FINAL: {num_imagenes} imágenes para {audio_duration:.2f}s de audio")
        if aplicar_transicion:
            print(f"Con transiciones de {duracion_transicion:.2f}s y duración ajustada de {duracion_ajustada:.2f}s por imagen")
        else:
            if respetar_duracion_exacta:
                print(f"Sin transiciones, respetando duración exacta de {duracion_por_imagen:.2f}s (excepto posiblemente la última imagen)")
            else:
                print(f"Sin transiciones, con duración ajustada uniforme de {duracion_ajustada:.2f}s por imagen")

        # Añadir información sobre repetición al resultado para que pueda ser usada por el generador de video
        resultado = {
            'num_imagenes': num_imagenes,
            'tiempos_imagenes': tiempos_imagenes,
            'repetir_ultimo_clip': hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip
        }
        
        # Si hay repetición, incluir la información adicional
        if hasattr(self, 'repetir_ultimo_clip') and self.repetir_ultimo_clip:
            resultado['tiempo_repeticion_ultimo_clip'] = self.tiempo_repeticion_ultimo_clip
        
        # Limpiar atributos temporales
        if hasattr(self, 'repetir_ultimo_clip'):
            delattr(self, 'repetir_ultimo_clip')
        if hasattr(self, 'tiempo_repeticion_ultimo_clip'):
            delattr(self, 'tiempo_repeticion_ultimo_clip')
            
        return num_imagenes, tiempos_imagenes
        
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
    
    def regenerar_audio(self, job_id):
        """Regenera el audio para un proyecto específico.
        
        Args:
            job_id: ID del trabajo a regenerar
        """
        try:
            # Obtener datos del trabajo
            if job_id not in self.jobs_in_gui:
                print(f"Error: No se encontró el trabajo {job_id} en la cola.")
                return False
            
            job = self.jobs_in_gui[job_id]
            title = job['titulo']
            script_path = job['guion_path']
            output_folder = Path(job['carpeta_salida'])
            voice = job['voz']
            audio_output_path = str(output_folder / f"voz.{OUTPUT_FORMAT}")
            
            # Actualizar estado
            self.update_job_status_gui(job_id, "Regenerando Audio...", "-")
            print(f"Regenerando audio para trabajo {job_id}: '{title}'")
            
            # Eliminar archivo de audio anterior si existe
            if 'archivo_voz' in job and job['archivo_voz']:
                try:
                    audio_path = Path(job['archivo_voz'])
                    if audio_path.exists():
                        audio_path.unlink()
                        print(f"Archivo de audio anterior eliminado: {audio_path}")
                except Exception as e:
                    print(f"Error al eliminar archivo de audio anterior: {e}")
            
            # Registrar tiempo de inicio
            job['tiempo_inicio_regeneracion'] = time.time()
            
            # Generar nuevo audio
            final_audio_path = asyncio.run(create_voiceover_from_script(
                script_path=script_path,
                output_audio_path=audio_output_path,
                voice=voice
            ))
            
            # Calcular tiempo transcurrido
            audio_tiempo_fin = time.time()
            audio_tiempo_transcurrido = audio_tiempo_fin - job['tiempo_inicio_regeneracion']
            audio_tiempo_formateado = f"{int(audio_tiempo_transcurrido // 60)}m {int(audio_tiempo_transcurrido % 60)}s"
            
            if final_audio_path and Path(final_audio_path).is_file():
                print(f"Audio regenerado para {job_id}: {final_audio_path}")
                # Actualizar el job con la ruta del audio generado
                job['archivo_voz'] = final_audio_path
                self.update_job_status_gui(job_id, "Audio Regenerado OK", audio_tiempo_formateado)
                return True
            else:
                error_msg = "Falló regeneración de audio"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}", audio_tiempo_formateado)
                return False
                
        except Exception as e:
            error_msg = f"Excepción en regeneración de audio: {e}"
            print(f"Error regenerando audio para {job_id}: {e}")
            traceback.print_exc()
            self.update_job_status_gui(job_id, f"Error: {error_msg}")
            return False
    
    def regenerar_subtitulos(self, job_id):
        """Regenera los subtítulos para un proyecto específico.
        
        Args:
            job_id: ID del trabajo a regenerar
        """
        try:
            # Obtener datos del trabajo
            if job_id not in self.jobs_in_gui:
                print(f"Error: No se encontró el trabajo {job_id} en la cola.")
                return False
            
            job = self.jobs_in_gui[job_id]
            title = job['titulo']
            output_folder = Path(job['carpeta_salida'])
            
            # Verificar que existe el archivo de audio
            if 'archivo_voz' not in job or not job['archivo_voz'] or not Path(job['archivo_voz']).is_file():
                error_msg = "No existe archivo de audio para generar subtítulos"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Actualizar estado
            self.update_job_status_gui(job_id, "Regenerando Subtítulos...", "-")
            print(f"Regenerando subtítulos para trabajo {job_id}: '{title}'")
            
            # Eliminar archivo de subtítulos anterior si existe
            if 'archivo_subtitulos' in job and job['archivo_subtitulos']:
                try:
                    srt_path = Path(job['archivo_subtitulos'])
                    if srt_path.exists():
                        srt_path.unlink()
                        print(f"Archivo de subtítulos anterior eliminado: {srt_path}")
                except Exception as e:
                    print(f"Error al eliminar archivo de subtítulos anterior: {e}")
            
            # Registrar tiempo de inicio
            job['tiempo_inicio_regeneracion'] = time.time()
            
            # Verificar si Whisper está disponible
            if not WHISPER_AVAILABLE:
                error_msg = "Whisper no está disponible para generar subtítulos"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Generar subtítulos
            srt_output_path = str(output_folder / "subtitulos.srt")
            srt_success = False
            
            try:
                # Obtener el modelo Whisper usando la función implementada
                from subtitles import get_whisper_model
                whisper_model = get_whisper_model(model_size="large-v3", device="cpu", compute_type="int8")
                if whisper_model is None:
                    print("No se pudo obtener el modelo Whisper para generar subtítulos.")
                
                if whisper_model:
                    # Configuración para la generación de subtítulos
                    whisper_language = "es"
                    word_timestamps = True
                    
                    # Generar subtítulos
                    # Obtener la opción de subtítulos en mayúsculas
                    uppercase = False
                    if hasattr(self.root, 'subtitles_uppercase') and hasattr(self.root.subtitles_uppercase, 'get'):
                        uppercase = self.root.subtitles_uppercase.get()
                    
                    print(f"Regenerando subtítulos con idioma: {whisper_language}, timestamps por palabra: {word_timestamps}, mayúsculas: {uppercase}")
                    
                    srt_success = generate_srt_with_whisper(
                        audio_path=job['archivo_voz'],
                        output_srt_path=srt_output_path,
                        whisper_model=whisper_model,
                        language=whisper_language,
                        word_timestamps=word_timestamps,
                        uppercase=uppercase
                    )
                else:
                    print("No se encontró el modelo Whisper para generar subtítulos.")
                    self.update_job_status_gui(job_id, "Error: No se encontró modelo Whisper")
                    return False
            except Exception as e_srt:
                print(f"Error al generar subtítulos: {e_srt}")
                self.update_job_status_gui(job_id, f"Error: {e_srt}")
                return False
            
            # Calcular tiempo transcurrido
            tiempo_fin = time.time()
            tiempo_transcurrido = tiempo_fin - job['tiempo_inicio_regeneracion']
            tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
            
            # Actualizar el job con la información de subtítulos
            if srt_success:
                job['archivo_subtitulos'] = srt_output_path
                job['aplicar_subtitulos'] = True
                print(f"Subtítulos regenerados exitosamente en: {srt_output_path}")
                self.update_job_status_gui(job_id, "Subtítulos Regenerados OK", tiempo_formateado)
                return True
            else:
                error_msg = "Falló regeneración de subtítulos"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}", tiempo_formateado)
                return False
                
        except Exception as e:
            error_msg = f"Excepción en regeneración de subtítulos: {e}"
            print(f"Error regenerando subtítulos para {job_id}: {e}")
            traceback.print_exc()
            self.update_job_status_gui(job_id, f"Error: {error_msg}")
            return False
    
    def regenerar_prompts(self, job_id):
        """Regenera los prompts para un proyecto específico.
        
        Args:
            job_id: ID del trabajo a regenerar
        """
        try:
            # Obtener datos del trabajo
            if job_id not in self.jobs_in_gui:
                print(f"Error: No se encontró el trabajo {job_id} en la cola.")
                return False
            
            job = self.jobs_in_gui[job_id]
            title = job['titulo']
            script_path = job['guion_path']
            output_folder = Path(job['carpeta_salida'])
            
            # Verificar que existe el archivo de audio para calcular duración
            if 'archivo_voz' not in job or not job['archivo_voz'] or not Path(job['archivo_voz']).is_file():
                error_msg = "No existe archivo de audio para calcular duración"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Verificar que Gemini está disponible
            if not GEMINI_AVAILABLE:
                error_msg = "Gemini no está disponible para generar prompts"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Actualizar estado
            self.update_job_status_gui(job_id, "Regenerando Prompts...", "-")
            print(f"Regenerando prompts para trabajo {job_id}: '{title}'")
            
            # Registrar tiempo de inicio
            job['tiempo_inicio_regeneracion'] = time.time()
            
            try:
                # Leer guion
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()

                # Calcular número de imágenes usando la función optimizada
                temp_audio_clip = AudioFileClip(job['archivo_voz'])
                audio_duration = temp_audio_clip.duration
                temp_audio_clip.close()
                
                # Obtener parámetros relevantes del job
                # Intentar obtener la duración de imagen de diferentes fuentes posibles
                duracion_por_imagen = None
                
                # 1. Intentar obtener de video_settings.duracion_img (valor de la interfaz gráfica)
                if 'video_settings' in job and isinstance(job['video_settings'], dict) and 'duracion_img' in job['video_settings']:
                    duracion_por_imagen = job['video_settings'].get('duracion_img')
                    print(f"Duración obtenida de video_settings.duracion_img: {duracion_por_imagen}")
                
                # 2. Intentar obtener de settings.duracion_img
                elif 'settings' in job and isinstance(job['settings'], dict) and 'duracion_img' in job['settings']:
                    duracion_por_imagen = job['settings'].get('duracion_img')
                    print(f"Duración obtenida de settings.duracion_img: {duracion_por_imagen}")
                
                # 3. Intentar obtener directamente de duracion_img
                elif 'duracion_img' in job:
                    duracion_por_imagen = job.get('duracion_img')
                    print(f"Duración obtenida de duracion_img: {duracion_por_imagen}")
                
                # 4. Usar valor predeterminado si no se encuentra
                else:
                    duracion_por_imagen = 20.0  # Valor predeterminado igual al de la interfaz gráfica
                    print(f"Usando duración predeterminada: {duracion_por_imagen}")
                
                # Asegurarse de que sea un número válido
                try:
                    duracion_por_imagen = float(duracion_por_imagen)
                except (ValueError, TypeError):
                    duracion_por_imagen = 15.0
                    print(f"Error al convertir duración, usando valor predeterminado: {duracion_por_imagen}")
                
                # Obtener parámetros de configuración desde video_settings
                video_settings_job = job.get('video_settings', {})
                
                # Obtener configuración de transiciones
                aplicar_transicion = video_settings_job.get('aplicar_transicion', False)
                duracion_transicion_setting = video_settings_job.get('duracion_transicion', 1.0)
                
                # Usar la duración de transición solo si se aplican
                duracion_transicion_usada = duracion_transicion_setting if aplicar_transicion else 0.0
                
                # Obtener la preferencia de respetar duración exacta
                respetar_duracion_exacta_setting = video_settings_job.get('respetar_duracion_exacta', True)
                
                # Obtener configuración de fade in/out
                fade_in = video_settings_job.get('duracion_fade_in', 2.0)
                fade_out = video_settings_job.get('duracion_fade_out', 2.0)
                
                print(f"\n--- Calculando Imágenes Óptimas para Regeneración de Imágenes ---")
                print(f"Audio Duration: {audio_duration:.2f}s")
                print(f"Duración por Imagen (config): {duracion_por_imagen:.2f}s")
                print(f"Aplicar Transición: {aplicar_transicion}")
                print(f"Duración Transición (config): {duracion_transicion_setting:.2f}s")
                print(f"Respetar Duración Exacta (config): {respetar_duracion_exacta_setting}")
                print(f"Fade In: {fade_in:.2f}s, Fade Out: {fade_out:.2f}s")
                print(f"----------------------------------------------------\n")
                
                # Calcular el número óptimo de imágenes
                num_imagenes_necesarias, tiempos_imagenes = self.calcular_imagenes_optimas(
                    audio_duration=audio_duration,
                    duracion_por_imagen=duracion_por_imagen,
                    duracion_transicion=duracion_transicion_usada,
                    aplicar_transicion=aplicar_transicion,
                    fade_in=fade_in,
                    fade_out=fade_out,
                    respetar_duracion_exacta=respetar_duracion_exacta_setting
                )
                
                # Guardar los tiempos de las imágenes para usarlos en la generación de video
                job['tiempos_imagenes'] = tiempos_imagenes
                job['num_imagenes'] = num_imagenes_necesarias  # Actualizar el número de imágenes en el job
                
                # Asegurar que los parámetros estén en el job para la creación del video
                if 'video_settings' not in job:
                    job['video_settings'] = {}
                job['video_settings']['aplicar_transicion'] = aplicar_transicion
                job['video_settings']['duracion_transicion'] = duracion_transicion_usada

                # Obtener el estilo de prompts seleccionado del diccionario 'video_settings' dentro del job
                video_settings_del_job = job.get('video_settings', {})  # Obtener el diccionario de ajustes, o uno vacío si no existe
                estilo = video_settings_del_job.get('estilo_imagenes', 'default')  # Obtener el estilo de ese diccionario
                
                # Verificar que el estilo existe en el gestor de prompts
                try:
                    from prompt_manager import PromptManager
                    prompt_manager = PromptManager()
                    estilos_disponibles = prompt_manager.get_prompt_ids()
                    
                    # Si el estilo no existe, intentar encontrar una coincidencia por nombre
                    if estilo not in estilos_disponibles:
                        print(f"ADVERTENCIA: El estilo '{estilo}' no existe en el gestor de prompts.")
                        
                        # Intentar encontrar el estilo por nombre
                        nombre_estilo = video_settings_del_job.get('nombre_estilo', '')
                        if nombre_estilo:
                            # Mapa de nombres a IDs
                            nombre_a_id = {
                                'Cinematográfico': 'default',
                                'Terror': 'terror',
                                'Animación': 'animacion',
                                'imagenes Psicodelicas': 'psicodelicas'
                            }
                            
                            if nombre_estilo in nombre_a_id:
                                estilo = nombre_a_id[nombre_estilo]
                                print(f"Usando estilo '{estilo}' basado en el nombre '{nombre_estilo}'")
                except Exception as e:
                    print(f"Error al verificar estilos: {e}")
                
                # Asegurarse de que el estilo sea un string válido
                if not estilo or estilo == "None" or estilo == "":
                    estilo = "default"
                
                print(f"Estilo final utilizado: '{estilo}'\n")
                
                # Generar los prompts con el estilo seleccionado
                lista_prompts = generar_prompts_con_gemini(
                    script_content,
                    num_imagenes_necesarias,
                    job['titulo'],  # <--- Pasar el título del proyecto
                    estilo_base=estilo,
                    tiempos_imagenes=tiempos_imagenes  # <--- Pasar la información de tiempos
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
                    
                    # Calcular tiempo transcurrido
                    tiempo_fin = time.time()
                    tiempo_transcurrido = tiempo_fin - job['tiempo_inicio_regeneracion']
                    tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
                    
                    self.update_job_status_gui(job_id, "Prompts Regenerados OK", tiempo_formateado)
                    return True
                else:
                    error_msg = "Falló regeneración de prompts"
                    print(f"{error_msg} para {job_id}")
                    self.update_job_status_gui(job_id, f"Error: {error_msg}")
                    return False
            except Exception as e_prompt:
                error_msg = f"Error durante la regeneración de prompts: {e_prompt}"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                traceback.print_exc()
                return False
                
        except Exception as e:
            error_msg = f"Excepción en regeneración de prompts: {e}"
            print(f"Error regenerando prompts para {job_id}: {e}")
            traceback.print_exc()
            self.update_job_status_gui(job_id, f"Error: {error_msg}")
            return False
    
    def regenerar_imagenes(self, job_id):
        """Regenera las imágenes para un proyecto específico.
        
        Args:
            job_id: ID del trabajo a regenerar
        """
        try:
            # Obtener datos del trabajo
            if job_id not in self.jobs_in_gui:
                print(f"Error: No se encontró el trabajo {job_id} en la cola.")
                return False
            
            job = self.jobs_in_gui[job_id]
            title = job['titulo']
            output_folder = Path(job['carpeta_salida'])
            
            # Verificar que existen los prompts
            if 'prompts_data' not in job or not job['prompts_data']:
                error_msg = "No existen prompts para generar imágenes"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Verificar que Replicate está disponible
            if not REPLICATE_AVAILABLE:
                error_msg = "Replicate no está disponible para generar imágenes"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}")
                return False
            
            # Actualizar estado
            self.update_job_status_gui(job_id, "Regenerando Imágenes...", "-")
            print(f"Regenerando imágenes para trabajo {job_id}: '{title}'")
            
            # Registrar tiempo de inicio
            job['tiempo_inicio_regeneracion'] = time.time()
            
            # Crear carpeta de imágenes si no existe
            image_output_folder = output_folder / "imagenes"
            image_output_folder.mkdir(parents=True, exist_ok=True)
            
            # Eliminar imágenes anteriores si existen
            if 'imagenes_generadas' in job and job['imagenes_generadas']:
                for img_path in job['imagenes_generadas']:
                    try:
                        img_file = Path(img_path)
                        if img_file.exists():
                            img_file.unlink()
                            print(f"Imagen anterior eliminada: {img_file}")
                    except Exception as e:
                        print(f"Error al eliminar imagen anterior: {e}")
            
            # Generar nuevas imágenes
            imagenes_generadas = []
            
            for idx, prompt_data in enumerate(job['prompts_data']):
                prompt_en = prompt_data['prompt_en']
                if prompt_en.startswith("Error"):
                    continue

                self.update_job_status_gui(job_id, f"Generando imagen {idx+1}/{len(job['prompts_data'])}...")

                img_filename = f"{output_folder.name}_{idx+1:03d}.png"
                img_path = generar_imagen_con_replicate(prompt_en, str(image_output_folder / img_filename))

                if img_path:
                    imagenes_generadas.append(img_path)
                    print(f"Imagen {idx+1} generada: {img_path}")
                else:
                    print(f"Error generando imagen {idx+1}")
            
            # Calcular tiempo transcurrido
            tiempo_fin = time.time()
            tiempo_transcurrido = tiempo_fin - job['tiempo_inicio_regeneracion']
            tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
            
            if imagenes_generadas:
                job['imagenes_generadas'] = imagenes_generadas
                self.update_job_status_gui(job_id, "Imágenes Regeneradas OK", tiempo_formateado)
                return True
            else:
                error_msg = "Falló regeneración de imágenes"
                print(f"{error_msg} para {job_id}")
                self.update_job_status_gui(job_id, f"Error: {error_msg}", tiempo_formateado)
                return False
                
        except Exception as e:
            error_msg = f"Excepción en regeneración de imágenes: {e}"
            print(f"Error regenerando imágenes para {job_id}: {e}")
            traceback.print_exc()
            self.update_job_status_gui(job_id, f"Error: {error_msg}")
            return False