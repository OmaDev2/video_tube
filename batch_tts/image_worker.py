# batch_tts/image_worker.py
import time
import traceback
from pathlib import Path

# Imports necesarios
# batch_tts/image_worker.py line 7
from prompt_generator import GEMINI_AVAILABLE, generar_prompts_con_gemini
from image_generator import REPLICATE_AVAILABLE, generar_imagen_con_replicate
from batch_tts.utils import calcular_imagenes_optimas # Importar desde el paquete batch_tts

# Importación de MoviePy 2.0
try:
    from moviepy import AudioFileClip  # Estilo de importación para MoviePy 2.0
except ImportError:
    print("Error: No se pudo importar AudioFileClip de moviepy")
    # Definir una clase simulada si es necesario
    class AudioFileClip:
        def __init__(self, *args, **kwargs):
            self.duration = 0

def procesar_imagenes(job_data, gui_root=None):
    """Genera prompts y/o imágenes para un trabajo."""
    audio_path = job_data.get('archivo_voz')
    output_folder = Path(job_data['carpeta_salida'])
    results = {}
    prompts_generados = []
    imagenes_generadas = []
    status_msg = ""

    # --- 0. Calcular tiempos y número de imágenes ---
    if not audio_path or not Path(audio_path).exists():
         return False, {"error": "Audio no disponible para calcular tiempos", "status_msg": "Img Omitido (Sin Audio)"}

    try:
         with AudioFileClip(audio_path) as temp_audio_clip:
             audio_duration = temp_audio_clip.duration

         # Leer configuración de video del job para el cálculo
         video_settings = job_data.get('video_settings', {})
         # Extraer parámetros con valores por defecto robustos
         duracion_por_imagen = float(video_settings.get('duracion_img', 15.0))
         aplicar_transicion = video_settings.get('aplicar_transicion', False)
         duracion_transicion = float(video_settings.get('duracion_transicion', 1.0)) if aplicar_transicion else 0.0
         respetar_duracion = video_settings.get('respetar_duracion_exacta', True)
         repetir_ultimo = video_settings.get('repetir_ultimo_clip', True) # Asegúrate que este setting exista o tenga default
         fade_in = float(video_settings.get('duracion_fade_in', 0.0))
         fade_out = float(video_settings.get('duracion_fade_out', 0.0))


         num_imagenes, tiempos_imagenes = calcular_imagenes_optimas(
             audio_duration=audio_duration,
             duracion_por_imagen=duracion_por_imagen,
             duracion_transicion=duracion_transicion,
             aplicar_transicion=aplicar_transicion,
             fade_in=fade_in,
             fade_out=fade_out,
             respetar_duracion_exacta=respetar_duracion,
             repetir_ultimo_clip_config=repetir_ultimo
         )
         results['num_imagenes_calculadas'] = num_imagenes
         results['tiempos_imagenes'] = tiempos_imagenes
         # Guardar info de repetición si existe
         results['repetir_ultimo_clip'] = False
         for clip_info in tiempos_imagenes:
              if clip_info.get('repetir'):
                   results['repetir_ultimo_clip'] = True
                   results['tiempo_repeticion_ultimo_clip'] = clip_info.get('tiempo_repeticion', 0.0)
                   break

    except Exception as e_calc:
         print(f"Error calculando tiempos: {e_calc}")
         traceback.print_exc()
         return False, {"error": f"Error calculando tiempos: {e_calc}", "status_msg": "Error Tiempos Img"}


    # --- 1. Generación de Prompts ---
    if GEMINI_AVAILABLE:
        try:
            script_path = job_data['guion_path']
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            estilo = job_data.get('video_settings', {}).get('estilo_imagenes', 'default')
            if not estilo or estilo == "None" or estilo == "": estilo = "default"

            lista_prompts = generar_prompts_con_gemini(
                script_content,
                num_imagenes, # Usar el número calculado
                job_data['titulo'],
                estilo_base=estilo,
                tiempos_imagenes=tiempos_imagenes # Pasar los tiempos calculados
            )
            num_prompts_generados = len(lista_prompts) if lista_prompts else 0
            print(f"DEBUG ImageWorker - Prompts generados: {num_prompts_generados}")

            if lista_prompts:
                prompts_generados = lista_prompts
                results['prompts_data'] = prompts_generados
                # Guardar prompts en archivo
                prompt_file_path = output_folder / "prompts.txt"
                with open(prompt_file_path, "w", encoding="utf-8") as f:
                     for p_idx, data in enumerate(lista_prompts):
                          f.write(f"--- Imagen {p_idx+1} ---\n")
                          f.write(f"Segmento Guion (ES):\n{data.get('segmento_es', 'N/A')}\n\n")
                          f.write(f"Prompt Generado (EN):\n{data.get('prompt_en', 'N/A')}\n")
                          f.write("="*30 + "\n\n")
                print(f"Prompts generados y guardados ({len(prompts_generados)})")
                status_msg += "Prompts OK. "
            else:
                 print("generar_prompts_con_gemini no devolvió prompts.")
                 status_msg += "Prompts Vacíos. "

        except Exception as e_prompt:
            print(f"Error generando prompts: {e_prompt}")
            traceback.print_exc()
            status_msg += "Error Prompts. "
            # No retornamos False aquí, podríamos intentar usar imágenes existentes
    else:
        print("Gemini no disponible, omitiendo generación de prompts.")
        status_msg += "Prompts Omitidos (No Gemini). "
        # Si no hay prompts, intentamos cargar los existentes si los hubiera
        if 'prompts_data' in job_data:
             prompts_generados = job_data['prompts_data']
             print(f"Usando {len(prompts_generados)} prompts preexistentes.")
             results['prompts_data'] = prompts_generados


    # --- 2. Generación de Imágenes ---
    image_output_folder = output_folder / "imagenes"
    if prompts_generados and REPLICATE_AVAILABLE:
        try:
            image_output_folder.mkdir(parents=True, exist_ok=True)
            for idx, prompt_data in enumerate(prompts_generados):
                prompt_en = prompt_data.get('prompt_en')
                if not prompt_en or prompt_en.startswith("Error"):
                     print(f"Omitiendo imagen {idx+1} por prompt inválido: '{prompt_en}'")
                     continue
                
                # TODO: Añadir lógica para actualizar estado en GUI aquí si es necesario (llamando al manager)
                # self.manager.update_job_status_gui(job_id, f"Generando imagen {idx+1}/{len(prompts_generados)}...")

                base_name = output_folder.name # Usar nombre de carpeta del proyecto
                img_filename = f"{base_name}_{idx+1:03d}.png"
                img_path_str = str(image_output_folder / img_filename)

                # Generar imagen
                print(f"DEBUG ImageWorker - Intentando generar imagen {idx+1}/{num_prompts_generados}...")
                generated_img_path = generar_imagen_con_replicate(prompt_en, img_path_str)
                
                if generated_img_path and Path(generated_img_path).exists():
                    print(f"DEBUG ImageWorker - Imagen {idx+1} generada OK: {generated_img_path}")
                    imagenes_generadas.append(generated_img_path)
                else:
                    print(f"DEBUG ImageWorker - Error al generar imagen {idx+1}")
            if imagenes_generadas:
                results['imagenes_generadas'] = imagenes_generadas
                results['imagenes_usadas_para_video'] = imagenes_generadas # Marcar para el worker de video
                print(f"Imágenes generadas ({len(imagenes_generadas)})")
                status_msg += "Imágenes OK. "
            else:
                 print("No se generó ninguna imagen.")
                 status_msg += "Error Imágenes. "


        except Exception as e_img:
            print(f"Error generando imágenes: {e_img}")
            traceback.print_exc()
            status_msg += "Error Imágenes. "
            # No retornamos False, podríamos usar imágenes existentes
    elif 'imagenes_generadas' in job_data and job_data['imagenes_generadas']:
         # Usar imágenes preexistentes si no se generaron nuevas
         imagenes_existentes = job_data['imagenes_generadas']
         # Validar que los archivos existen
         imagenes_validas = [p for p in imagenes_existentes if Path(p).exists()]
         if imagenes_validas:
              results['imagenes_usadas_para_video'] = imagenes_validas
              print(f"Usando {len(imagenes_validas)} imágenes preexistentes.")
              status_msg += "Usando Img Existentes. "
         else:
              print("Imágenes preexistentes no encontradas.")
              status_msg += "Img Existentes No Encontradas. "

    else:
         reason = ""
         if not prompts_generados: reason += "Sin Prompts. "
         if not REPLICATE_AVAILABLE: reason += "No Replicate. "
         print(f"Omitiendo generación de imágenes. {reason}")
         status_msg += f"Imágenes Omitidas ({reason.strip()}). "

    print(f"DEBUG ImageWorker - Total imágenes generadas exitosamente: {len(imagenes_generadas)}")
    results['imagenes_usadas_para_video'] = imagenes_generadas # o como lo almacenes
    results['status_msg'] = status_msg.strip()
    
    # Se considera éxito si al menos tenemos imágenes para intentar hacer el video
    # O si el proceso se completó sin errores fatales, aunque no se generaran imágenes.
    # El worker de video decidirá si puede continuar.
    success_final = 'Error' not in status_msg # Éxito si no hubo errores explícitos
    return success_final, results