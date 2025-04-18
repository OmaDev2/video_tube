# batch_tts/video_worker.py
import time
import traceback
from pathlib import Path
import json

# Importa la función real de creación de video
try:
    # Ajusta la ruta según tu estructura
    from app.video_creator import crear_video_desde_imagenes
    VIDEO_CREATOR_AVAILABLE = True
except ImportError:
    print("Advertencia: No se pudo importar 'crear_video_desde_imagenes'.")
    VIDEO_CREATOR_AVAILABLE = False
    def crear_video_desde_imagenes(project_folder, **kwargs): # Simulación
        print(f"Simulando crear_video_desde_imagenes para '{project_folder}'")
        return None

def crear_video(job_data, gui_root=None):
    """Crea el archivo de video final."""
    if not VIDEO_CREATOR_AVAILABLE:
        return False, {"error": "Video Creator no disponible", "status_msg": "Video Omitido (No Creador)"}

    # Verificar requisitos mínimos
    audio_path = job_data.get('archivo_voz')
    image_paths = job_data.get('imagenes_usadas_para_video') # Usar la lista validada por image_worker
    tiempos_imagenes = job_data.get('tiempos_imagenes')
    output_folder = Path(job_data['carpeta_salida'])

    if not audio_path or not Path(audio_path).exists():
         return False, {"error": "Archivo de audio no encontrado para video", "status_msg": "Video Omitido (Sin Audio)"}
    if not image_paths:
         return False, {"error": "No hay imágenes para crear el video", "status_msg": "Video Omitido (Sin Imágenes)"}
    if not tiempos_imagenes:
         return False, {"error": "No hay información de tiempos para las imágenes", "status_msg": "Video Omitido (Sin Tiempos)"}


    try:
        # Preparar argumentos, combinando settings del job y datos calculados
        video_creation_args = job_data.get('video_settings', {}).copy()

        # Esenciales (asegurar strings y rutas absolutas si es necesario)
        audio_path_abs = Path(audio_path)
        if not audio_path_abs.is_absolute():
             audio_path_abs = output_folder / audio_path_abs.name # Asumir está en la carpeta del proyecto
        video_creation_args['audio_path'] = str(audio_path_abs)

        video_creation_args['image_paths'] = [str(p) for p in image_paths]
        video_creation_args['tiempos_imagenes'] = tiempos_imagenes

        # Subtítulos (si existen y se deben aplicar)
        subtitle_path = job_data.get('archivo_subtitulos')
        aplicar_subtitulos_flag = job_data.get('video_settings', {}).get('aplicar_subtitulos') 
        print(f"DEBUG VideoWorker - Antes del IF: subtitle_path='{subtitle_path}', aplicar_subtitulos_flag={aplicar_subtitulos_flag}")
        if subtitle_path and aplicar_subtitulos_flag:
             subtitle_path_abs = Path(subtitle_path)
             if not subtitle_path_abs.is_absolute():
                  subtitle_path_abs = output_folder / subtitle_path_abs.name
             video_creation_args['subtitle_path'] = str(subtitle_path_abs)
             video_creation_args['aplicar_subtitulos'] = True # Asegurar que esté explícito si tu función lo requiere
        else:
             video_creation_args['aplicar_subtitulos'] = False # Desactivar explícitamente

        # Información de repetición (asegurarse de que se pasa correctamente)
        if job_data.get('repetir_ultimo_clip'):
            video_creation_args['repetir_ultimo_clip'] = True
            video_creation_args['tiempo_repeticion_ultimo_clip'] = job_data.get('tiempo_repeticion_ultimo_clip', 0.0)


        # Limpiar Nones y asegurar tipos correctos si es necesario antes de llamar
        video_creation_args_clean = {k: v for k, v in video_creation_args.items() if v is not None}

        print("-" * 30)
        print(f"DEBUG JOB {job_data['id']} - Args para crear_video_desde_imagenes:")
        # Usar json.dumps para una mejor visualización de diccionarios/listas
        print(json.dumps(video_creation_args_clean, indent=2, default=str)) # default=str para manejar Paths si quedan
        print("-" * 30)


        video_final_path = crear_video_desde_imagenes(
            project_folder=str(output_folder),
            **video_creation_args_clean
        )

        if video_final_path and Path(video_final_path).exists():
             return True, {'archivo_video': str(video_final_path)}
        else:
             error_msg = "crear_video_desde_imagenes no devolvió ruta válida o archivo no existe."
             print(error_msg)
             return False, {"error": error_msg, "status_msg": "Error Creación Video"}

    except Exception as e:
        print(f"Error en crear_video: {e}")
        traceback.print_exc()
        # Intentar dar un mensaje de error más específico si es posible
        error_detalle = str(e)
        if "KeyError" in error_detalle:
            error_detalle = f"Falta parámetro requerido: {e}"
        elif "IndexError" in error_detalle:
             error_detalle = f"Error de índice, ¿imágenes/tiempos no coinciden?: {e}"

        return False, {"error": error_detalle, "status_msg": f"Error Video ({error_detalle[:30]})"}