# batch_tts/subtitles_worker.py
import time
import traceback
from pathlib import Path

# Importa la función real de SRT y dependencias
try:
    # Ajusta la ruta según tu estructura
    from subtitles import generate_srt_with_whisper, WHISPER_AVAILABLE, get_whisper_model
    if WHISPER_AVAILABLE:
         from faster_whisper import WhisperModel # Necesario aquí también
    SUBTITLES_AVAILABLE = WHISPER_AVAILABLE
except ImportError:
    print("Advertencia: No se pudo importar 'generate_srt_with_whisper'.")
    SUBTITLES_AVAILABLE = False
    def get_whisper_model(*args, **kwargs): return None

# Cache simple para el modelo Whisper (opcional pero recomendado)
_whisper_model_cache = None

def _get_cached_whisper_model(model_name="base", device="cpu", compute_type="int8"):
     global _whisper_model_cache
     # TODO: Podrías hacer esto más configurable leyendo desde gui_root si lo pasas
     if _whisper_model_cache is None:
          print(f"Cargando modelo Whisper '{model_name}'...")
          try:
               _whisper_model_cache = WhisperModel(model_name, device=device, compute_type=compute_type)
               print("Modelo Whisper cargado.")
          except Exception as e:
               print(f"Error al cargar modelo Whisper: {e}")
               return None
     return _whisper_model_cache


def generar_subtitulos(job_data, gui_root=None):
    """Genera el archivo SRT para un trabajo."""
    if not SUBTITLES_AVAILABLE:
         return False, {"error": "Whisper no disponible", "status_msg": "SRT Omitido (No Whisper)"}

    audio_path = job_data.get('archivo_voz')
    if not audio_path or not Path(audio_path).exists():
        return False, {"error": "Archivo de audio no encontrado", "status_msg": "SRT Omitido (Sin Audio)"}

    output_folder = Path(job_data['carpeta_salida'])
    srt_output_path = str(output_folder / "subtitulos.srt")

    # Obtener modelo (usando caché)
    # TODO: Leer configuración del modelo desde gui_root si es necesario
    whisper_model = _get_cached_whisper_model()
    if not whisper_model:
         return False, {"error": "No se pudo cargar el modelo Whisper", "status_msg": "SRT Omitido (Sin Modelo)"}

    try:
        # TODO: Leer configuraciones (idioma, etc.) desde gui_root o job_data si las pasas
        # Ejemplo: whisper_language = gui_root.whisper_language.get() if gui_root else 'es'
        whisper_language = job_data.get('video_settings', {}).get('whisper_language', 'es') # Ejemplo leyendo de settings
        word_timestamps = job_data.get('video_settings', {}).get('whisper_word_timestamps', True)
        uppercase = job_data.get('video_settings', {}).get('subtitles_uppercase', False)


        print(f"Generando SRT con idioma: {whisper_language}, timestamps: {word_timestamps}, mayúsculas: {uppercase}")
        success = generate_srt_with_whisper(
            whisper_model, # Modelo primero
            audio_path,
            srt_output_path,
            language=whisper_language,
            word_timestamps=word_timestamps,
            uppercase=uppercase
        )

        if success:
            return True, {
                'archivo_subtitulos': srt_output_path,
                #'aplicar_subtitulos': True # Asumimos que sí si se generó
            }
        else:
             return False, {"error": "generate_srt_with_whisper retornó False", "status_msg": "Error SRT"}

    except Exception as e:
        print(f"Error en generar_subtitulos: {e}")
        traceback.print_exc()
        return False, {"error": str(e), "status_msg": "Error SRT"}