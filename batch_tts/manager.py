# Importa tu módulo generador de IA
try:
    import ai_script_generator # ¡Asegúrate de que el nombre del archivo sea correcto!
    AI_SCRIPT_GEN_AVAILABLE = ai_script_generator.AI_PROVIDER_AVAILABLE
except ImportError:
    print("ERROR FATAL: No se pudo importar el módulo ai_script_generator.")
    AI_SCRIPT_GEN_AVAILABLE = False
# También importa los workers que ya usabas
from . import audio_worker
from . import subtitles_worker
from . import image_worker
from . import video_worker
from . import utils
import asyncio
import json
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
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

# Importar OUTPUT_FORMAT desde tts_generator o usar el valor de audio_worker
try:
    from tts_generator import OUTPUT_FORMAT
except ImportError:
    from .audio_worker import OUTPUT_FORMAT


class BatchTTSManager:
    """Gestor de procesamiento por lotes para la generación de voz en off."""

    def __init__(self, root):
        
        """
        Inicializa el gestor de procesamiento por lotes.

        Args:
            root: La ventana principal de Tkinter
            default_voice: La voz predeterminada para la generación de TTS
        """
        self.root = root
        self.job_queue = queue.Queue()
        self.jobs_in_gui = {}
        self.job_counter = 0
        self.worker_thread = None
        self.worker_running = False
        self.project_base_dir = Path("proyectos_video")
        self.project_base_dir.mkdir(parents=True, exist_ok=True)
        self.default_voice = "es-MX-JorgeNeural" # O leer de config
        self.tree_queue = None # Se asignará desde BatchTabFrame
        
       
  

    def add_project_to_queue(self, title, script, voice=None, video_settings=None,script_contexto=None):
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
            return None  

        if not script:
            messagebox.showerror("Error", "Por favor, introduce un guion para el proyecto.")
            return False

        # Crear carpeta de proyecto
        safe_title = utils.sanitize_filename(title)
        # Añadir timestamp para evitar colisiones si se procesa el mismo título varias veces
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_folder = self.project_base_dir / f"{safe_title}_{timestamp}" # Modificado para unicidad

        try:
            project_folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta del proyecto:\n{project_folder}\nError: {e}")
            return False

       # Guardar guion MANUAL si se proporcionó
        script_file_path = None
        if script: # Si se pasó un guion (modo manual)
            script_file_path = project_folder / "guion.txt"
            try:
                with open(script_file_path, "w", encoding="utf-8") as f:
                    f.write(script)
                print(f"Guion manual guardado en {script_file_path}")
            except IOError as e:
                messagebox.showerror("Error", f"No se pudo guardar el guion:\n{script_file_path}\nError: {e}")
                return None

        # Crear y añadir trabajo a la cola
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"
        needs_ai_generation = (script is None) # True si no se pasó guion manual

        job_data = {
            'id': job_id,
            'titulo': title,  # Guardamos el título original para mostrar
            'guion_path': str(script_file_path) if script_file_path else None,
            'carpeta_salida': str(project_folder),
            'voz': voice or self.default_voice,
            'estado': 'Pendiente',
            'tiempo_inicio': None,
            'tiempo_fin': None,
            # Guarda video_settings (que ahora puede incluir params de IA)
            'video_settings': video_settings if isinstance(video_settings, dict) else {},
            'needs_script_generation': needs_ai_generation,
            'script_contexto': script_contexto # Guarda el contexto si se pasó
        }

        # Guardar configuración del proyecto en un archivo JSON
        # En batch_tts/manager.py, dentro de add_project_to_queue

# (Asegúrate de tener 'import json' y 'from pathlib import Path' al principio del archivo .py)

        settings_file_path = project_folder / "settings.json"
        try:
            # 1. Obtener el diccionario de video_settings de forma segura
            settings_to_save = job_data.get('video_settings', {})
            serializable_settings = {} # Diccionario para la versión serializable

            if settings_to_save: # Solo si hay algo que guardar
                # 2. Preparar la versión serializable UNA SOLA VEZ
                #    Convierte objetos Path a string para que JSON los entienda
                print("DEBUG MANAGER: Preparando settings para guardar...") # Debug opcional
                for key, value in settings_to_save.items():
                    if isinstance(value, Path):
                        serializable_settings[key] = str(value)
                        # print(f"  - Convertido Path a str para key '{key}'") # Debug detallado
                    elif isinstance(value, list) and value and isinstance(value[0], Path):
                        # Si es una lista y el primer elemento es Path, asume que todos lo son
                        serializable_settings[key] = [str(p) for p in value]
                        # print(f"  - Convertida lista de Paths a strs para key '{key}'") # Debug detallado
                    # Puedes añadir más conversiones aquí si usas otros tipos no serializables por defecto
                    else:
                        # Asume que los demás tipos son serializables (str, int, float, bool, list, dict, None)
                        serializable_settings[key] = value
            else:
                print("DEBUG MANAGER: No hay video_settings que guardar.") # Debug opcional

            # 3. Guardar el diccionario serializable en el archivo UNA SOLA VEZ
            with open(settings_file_path, "w", encoding="utf-8") as f:
                json.dump(serializable_settings, f, indent=4, ensure_ascii=False)

            print(f"Configuración (video_settings) guardada en {settings_file_path}") # Mensaje de éxito

        except Exception as e:
            # Captura cualquier error durante la preparación o guardado
            print(f"ERROR al preparar o guardar la configuración en {settings_file_path}: {e}")
            import traceback
            traceback.print_exc()
            # Considera si quieres continuar si falla el guardado. Por ahora continuamos.

        self.job_queue.put(job_data)

        # Añadir a la GUI (Treeview) si ya existe
        if self.tree_queue:
            self.tree_queue.insert("", tk.END, iid=job_id, values=(title, 'Pendiente', '-'))
            self.jobs_in_gui[job_id] = job_data # Asegurarse de añadirlo aquí

        print(f"Proyecto '{title}' añadido a la cola (ID: {job_id}).")
        return job_id # Devuelve el ID del trabajo añadido

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
        """Procesa los trabajos en la cola de forma secuencial llamando a los workers."""
        while self.worker_running:
            current_job = None
            job_id = None # Inicializar job_id fuera del try principal
            output_folder = None # Inicializar output_folder
            
            try:
                try:
                    current_job = self.job_queue.get(timeout=1)
                    job_id = current_job['id']
                    title = current_job['titulo']
                    output_folder = Path(current_job['carpeta_salida'])
                    print(f"Procesando trabajo {job_id}: '{title}'")
                except queue.Empty:
                    continue
                
                # Actualizar estado y tiempo de inicio
                current_job['tiempo_inicio'] = time.time()
                self.update_job_status_gui(job_id, "Iniciando...", "-")
                
                # --- ============================================ ---
                # --- PASO NUEVO: GENERACIÓN DE GUION CON IA (si aplica) ---
                # --- ============================================ ---
                if current_job.get('needs_script_generation'):
                    if not AI_SCRIPT_GEN_AVAILABLE:
                         raise ValueError("Se requiere generación AI pero el módulo/proveedor no está disponible.")

                    self.update_job_status_gui(job_id, "Generando Guion AI...", "-")
                    print(f"Trabajo {job_id}: Iniciando generación de guion con IA...")

                    # Extraer parámetros necesarios de job_data y video_settings
                    titulo_script = current_job.get('titulo')
                    contexto_script = current_job.get('script_contexto', "") # Usar "" si no hay contexto
                    video_settings = current_job.get('video_settings', {})
                    estilo_script = video_settings.get('script_style', 'default')
                    num_sec = video_settings.get('script_num_secciones', 5)
                    pal_sec = video_settings.get('script_palabras_seccion', 300)

                    # Llamar a la función orquestadora de ai_script_generator
                    # Usamos asyncio.run porque estamos en un thread síncrono
                    # ¡Esto puede bloquear este hilo mientras la IA trabaja!
                    # Considera alternativas más avanzadas si necesitas que el manager haga otras cosas mientras.
                    try:
                        guion_final, metadata = asyncio.run(
                            ai_script_generator.crear_guion_completo_y_metadata(
                                titulo=titulo_script,
                                contexto=contexto_script,
                                estilo_prompt=estilo_script,
                                palabras_seccion=pal_sec,
                                num_secciones=num_sec
                            )
                        )
                    except Exception as e_async_run:
                         print(f"ERROR al ejecutar asyncio.run para el generador de IA: {e_async_run}")
                         raise ValueError(f"Fallo en asyncio para Guion AI: {e_async_run}")


                    if not guion_final:
                        raise ValueError("Fallo completo en la generación del guion con IA.")

                    # Guardar el guion generado en guion.txt
                    script_file_path = output_folder / "guion.txt"
                    try:
                        with open(script_file_path, "w", encoding="utf-8") as f:
                            f.write(guion_final)
                        current_job['guion_path'] = str(script_file_path) # Actualiza el path en job_data
                        print(f"Guion AI guardado en: {script_file_path}")
                    except IOError as e_write_script:
                        raise ValueError(f"Error al guardar guion AI: {e_write_script}")

                    # Guardar metadata (opcional)
                    if metadata:
                        metadata_file_path = output_folder / "metadata.json"
                        try:
                            with open(metadata_file_path, "w", encoding="utf-8") as f:
                                json.dump(metadata, f, indent=4, ensure_ascii=False)
                            print(f"Metadata AI guardada en: {metadata_file_path}")
                            current_job['metadata_path'] = str(metadata_file_path) # Guardar path si quieres
                        except Exception as e_write_meta:
                            print(f"ADVERTENCIA: No se pudo guardar metadata AI: {e_write_meta}")

                    # Marcar como completado y actualizar estado GUI
                    current_job['needs_script_generation'] = False
                    self.update_job_status_gui(job_id, "Guion AI OK", "-") # Actualiza estado

                # --- FIN PASO NUEVO ---
                # --- ================ ---
                
                
                
                
                
                
                

                # --- 1. Generación de Audio ---
                if not current_job.get('guion_path'): # Comprobar si tenemos guion ahora
                    raise ValueError("No hay guion disponible para generar audio.")
                
                self.update_job_status_gui(job_id, "Generando Audio...", "-")
                success_audio, audio_result = audio_worker.generar_audio(current_job, self.root) # Pasar root si es necesario para config
                if not success_audio:
                    raise ValueError(f"Error en Audio: {audio_result}") # Lanza excepción para ir al finally
                current_job.update(audio_result) # Actualiza el job con 'archivo_voz', etc.
                audio_tiempo_formateado = audio_result.get("tiempo_formateado", "-")
                self.update_job_status_gui(job_id, "Audio OK", audio_tiempo_formateado)


                # --- 2. Generación de Subtítulos ---
                if subtitles_worker.SUBTITLES_AVAILABLE: # Verificar disponibilidad aquí
                     self.update_job_status_gui(job_id, "Generando Subtítulos...", audio_tiempo_formateado)
                     success_srt, srt_result = subtitles_worker.generar_subtitulos(current_job, self.root) # Pasar GUI root si necesitas config
                     if success_srt:
                          current_job.update(srt_result)
                          print(f"DEBUG Manager - Después de SRT: aplicar_subtitulos={current_job.get('aplicar_subtitulos')}, archivo_subtitulos={current_job.get('archivo_subtitulos')}")
                          self.update_job_status_gui(job_id, "Audio y SRT OK", audio_tiempo_formateado)
                          print(f"Subtítulos generados: {srt_result.get('archivo_subtitulos')}")
                     else:
                          print(f"Advertencia: No se generaron subtítulos ({srt_result.get('error', 'Razón desconocida')})")
                          self.update_job_status_gui(job_id, f"Audio OK. {srt_result.get('status_msg', 'SRT Omitido')}", audio_tiempo_formateado)
                else:
                     print("Worker de subtítulos no disponible, omitiendo.")
                     self.update_job_status_gui(job_id, "Audio OK. SRT Omitido (no disponible)", audio_tiempo_formateado)


                # --- 3 & 4. Generación de Prompts e Imágenes ---
                self.update_job_status_gui(job_id, "Procesando Imágenes...", audio_tiempo_formateado)
                success_img, img_result = image_worker.procesar_imagenes(current_job, self.root) # Pasa root si necesita config
                if success_img:
                     current_job.update(img_result)
                     self.update_job_status_gui(job_id, f"Imágenes OK ({img_result.get('status_msg', '')})", audio_tiempo_formateado)
                     print(f"Proceso de imágenes completado para {job_id}")
                else:
                     # El worker de imágenes puede decidir si es un error fatal o no
                     print(f"Advertencia/Error en proceso de imágenes: {img_result.get('error', 'Razón desconocida')}")
                     self.update_job_status_gui(job_id, f"Error/Omitido Imágenes ({img_result.get('status_msg', '')})", audio_tiempo_formateado)
                     # Decidir si continuar o no. Por ahora, continuaremos para intentar video si hay imágenes preexistentes.


                # --- 5. Creación de Video ---
                # Verificar si tenemos lo necesario (audio y *algunas* imágenes)
                if current_job.get('archivo_voz') and current_job.get('imagenes_usadas_para_video'): # 'imagenes_usadas_para_video' debe ser poblado por image_worker
                     if video_worker.VIDEO_CREATOR_AVAILABLE:
                          self.update_job_status_gui(job_id, "Generando Video...", "")
                          success_vid, vid_result = video_worker.crear_video(current_job, self.root) # Pasa root si necesita config
                          if success_vid:
                               current_job.update(vid_result)
                               current_job['tiempo_fin'] = time.time() # Marcar fin aquí
                               tiempo_total = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                               tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                               self.update_job_status_gui(job_id, "Video Completo", tiempo_formateado)
                               print(f"Video generado: {vid_result.get('archivo_video')}")
                          else:
                               raise ValueError(f"Error en Video: {vid_result.get('error', 'Razón desconocida')}")
                     else:
                          print("Worker de video no disponible, omitiendo.")
                          self.update_job_status_gui(job_id, "Video Omitido (no disponible)", "-")
                else:
                     # Razones por las que no se crea el video
                     reason = ""
                     if not current_job.get('archivo_voz'): reason += "Falta Audio. "
                     if not current_job.get('imagenes_usadas_para_video'): reason += "Faltan Imágenes."
                     print(f"Omitiendo creación de video para {job_id}. Razón: {reason.strip()}")
                     # Marcar como completado (sin video) o error? Depende de tu lógica.
                     # Por ahora, lo marcamos como completado pero indicando omisión.
                     current_job['tiempo_fin'] = time.time()
                     tiempo_total = current_job.get('tiempo_fin', time.time()) - current_job['tiempo_inicio']
                     tiempo_formateado = f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s"
                     self.update_job_status_gui(job_id, f"Completado (Video Omitido: {reason.strip()})", tiempo_formateado)


            except Exception as e_job:
                # Captura errores lanzados por los workers o en la orquestación
                error_msg = f"Error procesando job {job_id}: {e_job}"
                print(error_msg)
                logging.error(error_msg, exc_info=True)
                traceback.print_exc()
                # ... (actualizar GUI con error) ...
                if job_id: self.update_job_status_gui(job_id, f"Error: {str(e_job)[:60]}", tiempo_formateado_error)

                # Calcular tiempo transcurrido incluso en caso de error
                tiempo_formateado_error = "-"
                if current_job and 'tiempo_inicio' in current_job and current_job['tiempo_inicio']:
                     current_job['tiempo_fin'] = time.time()
                     tiempo_transcurrido = current_job['tiempo_fin'] - current_job['tiempo_inicio']
                     tiempo_formateado_error = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"

                if current_job:
                     self.update_job_status_gui(job_id, f"Error: {str(e_job)[:60]}", tiempo_formateado_error)
                # Si el error ocurrió antes de tener job_id, no podemos actualizar GUI

            finally:
                # Marcar tarea como completada en la cola
                if current_job:
                    try:
                        self.job_queue.task_done()
                    except Exception as e_final:
                        print(f"Excepción inesperada en finally/task_done para job {current_job.get('id', 'N/A')}: {e_final}")
                        traceback.print_exc()

        print("Worker de cola finalizado.")


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
        """Regenera el audio para un trabajo existente utilizando los parámetros actuales."""
        from . import audio_worker
        import time
        
        # Buscar el trabajo en la lista
        job_data = None
        for job in self.jobs:
            if job['id'] == job_id:
                job_data = job
                break
        
        if not job_data:
            print(f"Error: No se encontró el trabajo con ID {job_id}")
            self.update_job_status_gui(job_id, "Error: Trabajo no encontrado", "-")
            return False
        
        try:
            # Actualizar estado
            self.update_job_status_gui(job_id, "Regenerando Audio...", "-")
            
            # Regenerar el audio
            success_audio, audio_result = audio_worker.generar_audio(job_data, self.root)
            
            if not success_audio:
                raise ValueError(f"Error en Audio: {audio_result}") 
            
            # Actualizar el job con los resultados
            job_data.update(audio_result)
            audio_tiempo_formateado = audio_result.get("tiempo_formateado", "-")
            
            # Actualizar estado
            self.update_job_status_gui(job_id, "Audio Regenerado", audio_tiempo_formateado)
            print(f"Audio regenerado exitosamente para el trabajo {job_id}")
            
            # Guardar los cambios en el archivo settings.json
            self._save_job_settings(job_data)
            
            return True
            
        except Exception as e:
            import traceback
            print(f"Error al regenerar audio: {e}")
            print(traceback.format_exc())
            self.update_job_status_gui(job_id, f"Error: {str(e)}", "-")
            return False


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