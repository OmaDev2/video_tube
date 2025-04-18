# batch_tts/audio_worker.py
import asyncio
from pickle import TRUE
import time
import traceback
from pathlib import Path
# batch_tts/audio_worker.py line 6

# --- Inicializa las variables globales del módulo ---
TTS_AVAILABLE = False  # <--- Inicializa a False por defecto
OUTPUT_FORMAT = "mp3"  # <--- Inicializa también el formato por defecto


# Importa la función real de TTS y su formato
try:
    # Ajusta la ruta según tu estructura
    from tts_generator import create_voiceover_from_script, OUTPUT_FORMAT
    TTS_AVAILABLE = True
    print("INFO: Módulo tts_generator importado correctamente.") # Mensaje de confirmación (opcional)
except ImportError:
    print("Advertencia: No se pudo importar 'create_voiceover_from_script'.")
    TTS_AVAILABLE = False
    print("INFO: Módulo tts_generator no disponible.") # Mensaje de confirmación (opcional)
    OUTPUT_FORMAT = "mp3" # Default
    async def create_voiceover_from_script(*args, **kwargs): # Simulación
        print("Simulando create_voiceover_from_script...")
        return None

def generar_audio(job_data, gui_root=None):
    """Genera el archivo de audio para un trabajo."""
    if not TTS_AVAILABLE:
        return False, {"error": "TTS no disponible", "status_msg": "Audio Omitido (No TTS)"}

    script_path = job_data['guion_path']
    output_folder = Path(job_data['carpeta_salida'])
    voice = job_data['voz']
    audio_output_path = str(output_folder / f"voz.{OUTPUT_FORMAT}")
    start_time = time.time()

    try:
        final_audio_path = asyncio.run(create_voiceover_from_script(
            script_path=script_path,
            output_audio_path=audio_output_path,
            voice=voice
        ))

        end_time = time.time()
        elapsed = end_time - start_time
        tiempo_formateado = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        if final_audio_path and Path(final_audio_path).is_file():
            print(f"Audio generado: {final_audio_path}")
            return True, {
                'archivo_voz': final_audio_path,
                'tiempo_formateado': tiempo_formateado
            }
        else:
            return False, {"error": "create_voiceover_from_script no generó archivo", "status_msg": "Error TTS"}

    except Exception as e:
        print(f"Error en generar_audio: {e}")
        traceback.print_exc()
        return False, {"error": str(e), "status_msg": "Error TTS"}