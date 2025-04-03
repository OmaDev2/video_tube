#!/usr/bin/env python3
import asyncio
import queue
import threading
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import time

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
    
    def add_project_to_queue(self, title, script, voice=None):
        """
        Añade un nuevo proyecto a la cola de procesamiento.
        
        Args:
            title: Título del proyecto
            script: Texto del guion para la voz en off
            voice: Voz a utilizar (opcional, usa default_voice si no se especifica)
        
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
            'tiempo_fin': None
        }
        
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
                
                try:
                    # Ejecutar la corutina create_voiceover_from_script
                    final_audio = asyncio.run(create_voiceover_from_script(
                        script_path=script_path,
                        output_audio_path=audio_output_path,
                        voice=voice
                    ))
                    
                    # Calcular tiempo transcurrido
                    job['tiempo_fin'] = time.time()
                    tiempo_transcurrido = job['tiempo_fin'] - job['tiempo_inicio']
                    tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
                    
                    if final_audio and Path(final_audio).is_file():
                        print(f"Audio generado para {job_id}: {final_audio}")
                        self.update_job_status_gui(job_id, "Audio Completo", tiempo_formateado)
                    else:
                        print(f"Fallo al generar audio para {job_id}")
                        self.update_job_status_gui(job_id, "Error TTS", tiempo_formateado)
                
                except Exception as e:
                    print(f"Excepción en el worker procesando {job_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Calcular tiempo transcurrido incluso en caso de error
                    job['tiempo_fin'] = time.time()
                    tiempo_transcurrido = job['tiempo_fin'] - job['tiempo_inicio']
                    tiempo_formateado = f"{int(tiempo_transcurrido // 60)}m {int(tiempo_transcurrido % 60)}s"
                    
                    self.update_job_status_gui(job_id, f"Error: {str(e)[:30]}...", tiempo_formateado)
                
                finally:
                    self.job_queue.task_done()  # Indicar que este trabajo se ha procesado
            
            except Exception as e:
                print(f"Error inesperado en el worker: {e}")
                import traceback
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
