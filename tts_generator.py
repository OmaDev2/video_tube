import asyncio
import edge_tts
import os
from pathlib import Path
from pydub import AudioSegment

# --- Configuración ---
# Puedes obtener la lista de voces con: edge-tts --list-voices
# Ejemplo: es-ES-ElviraNeural (España), es-MX-DaliaNeural (México), es-AR-ElenaNeural (Argentina)
DEFAULT_VOICE = "es-MX-JorgeNeural"
MAX_CHUNK_CHARS = 4000  # Límite de caracteres por chunk (ajusta si es necesario)
TEMP_AUDIO_DIR = "temp_audio_chunks" # Directorio para archivos temporales
OUTPUT_FORMAT = "mp3" # Formato de salida final y de los chunks

# --- Funciones ---

def split_text_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """
    Divide el texto en chunks basados en párrafos, sin exceder max_chars.
    """
    paragraphs = text.split('\n\n') # Asume párrafos separados por doble salto de línea
    paragraphs = [p.strip() for p in paragraphs if p.strip()] # Limpia párrafos vacíos

    if not paragraphs:
        return []

    chunks = []
    current_chunk_paragraphs = []
    current_length = 0

    for paragraph in paragraphs:
        para_len = len(paragraph)
        # +2 para contar el separador '\n\n' si no es el primer párrafo del chunk
        projected_length = current_length + para_len + (2 if current_chunk_paragraphs else 0)

        # Si añadir el párrafo excede el límite Y el chunk actual no está vacío,
        # finaliza el chunk actual y empieza uno nuevo.
        if current_chunk_paragraphs and projected_length > max_chars:
            chunks.append("\n\n".join(current_chunk_paragraphs))
            current_chunk_paragraphs = [paragraph]
            current_length = para_len
        else:
            # Añade el párrafo al chunk actual
            current_chunk_paragraphs.append(paragraph)
            # Actualiza longitud (suma 2 del separador solo si no es el primer párrafo)
            current_length += para_len + (2 if len(current_chunk_paragraphs) > 1 else 0)

    # Añade el último chunk restante
    if current_chunk_paragraphs:
        chunks.append("\n\n".join(current_chunk_paragraphs))

    print(f"Texto dividido en {len(chunks)} chunks.")
    return chunks

async def text_chunk_to_speech(text: str, voice: str, output_path: str):
    """
    Convierte un único chunk de texto a audio usando edge-tts.
    """
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print(f"Chunk de audio guardado en: {output_path}")
    except Exception as e:
        print(f"Error generando audio para chunk: {e}")
        # Podrías querer manejar este error de forma más robusta
        # (e.g., reintentar, registrar, devolver un indicador de error)

async def generate_speech_for_chunks(chunks: list[str], voice: str, temp_dir: str) -> list[str]:
    """
    Genera archivos de audio para una lista de chunks de texto de forma asíncrona.
    Devuelve la lista de rutas a los archivos de audio generados.
    """
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True) # Asegura que el directorio exista
    tasks = []
    chunk_files = []

    for i, chunk in enumerate(chunks):
        output_file = temp_path / f"chunk_{i+1}.{OUTPUT_FORMAT}"
        chunk_files.append(str(output_file))
        # Crea la tarea asíncrona para generar el audio de este chunk
        tasks.append(text_chunk_to_speech(chunk, voice, str(output_file)))

    # Ejecuta todas las tareas de generación de audio concurrentemente
    await asyncio.gather(*tasks)

    # Verifica si realmente se crearon los archivos (importante si text_chunk_to_speech puede fallar)
    existing_files = [f for f in chunk_files if Path(f).is_file()]
    print(f"Generados {len(existing_files)} archivos de audio en {temp_dir}.")
    return existing_files # Devuelve solo los archivos que existen

def concatenate_audio(file_list: list[str], output_filename: str):
    """
    Concatena una lista de archivos de audio en uno solo usando pydub.
    """
    if not file_list:
        print("No hay archivos de audio para concatenar.")
        return False

    combined = AudioSegment.empty()
    print("Concatenando archivos de audio...")
    for file_path in file_list:
        try:
            # Asume formato MP3 basado en OUTPUT_FORMAT, ajusta si usas otro
            if OUTPUT_FORMAT == "mp3":
                 segment = AudioSegment.from_mp3(file_path)
            elif OUTPUT_FORMAT == "wav":
                 segment = AudioSegment.from_wav(file_path)
            # Añade más formatos si es necesario
            else:
                 print(f"Formato {OUTPUT_FORMAT} no soportado directamente para carga. Usando detección automática.")
                 segment = AudioSegment.from_file(file_path) # Intenta detectar

            combined += segment
            print(f" - Añadido {Path(file_path).name}")
        except Exception as e:
            print(f"Error al procesar {file_path}: {e}. Saltando archivo.")
            # Decide si quieres detener el proceso o continuar

    try:
        combined.export(output_filename, format=OUTPUT_FORMAT)
        print(f"Audio final guardado en: {output_filename}")
        return True
    except Exception as e:
        print(f"Error al exportar el audio final: {e}")
        return False

def cleanup_files(file_list: list[str], temp_dir: str):
    """
    Elimina los archivos de audio temporales y el directorio si está vacío.
    """
    print("Limpiando archivos temporales...")
    for file_path in file_list:
        try:
            os.remove(file_path)
            # print(f" - Eliminado {file_path}")
        except OSError as e:
            print(f"Error al eliminar {file_path}: {e}")
    try:
        # Intenta eliminar el directorio temporal si está vacío
        os.rmdir(temp_dir)
        print(f"Directorio temporal {temp_dir} eliminado.")
    except OSError:
        # Falla si el directorio no está vacío (quizás por errores previos)
        print(f"No se pudo eliminar el directorio temporal {temp_dir} (puede que no esté vacío).")

# --- Función Principal de Orquestación ---

async def create_voiceover_from_script(script_path: str, output_audio_path: str, voice: str = DEFAULT_VOICE):
    """
    Orquesta el proceso completo: leer guion, dividir, generar TTS, concatenar y limpiar.
    """
    print(f"Iniciando generación de voz en off para: {script_path}")
    # 1. Leer el guion
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
        if not script_text.strip():
            print("Error: El archivo de guion está vacío.")
            return None
    except FileNotFoundError:
        print(f"Error: Archivo de guion no encontrado en {script_path}")
        return None
    except Exception as e:
        print(f"Error al leer el archivo de guion {script_path}: {e}")
        return None

    # 2. Dividir en chunks
    chunks = split_text_into_chunks(script_text, MAX_CHUNK_CHARS)
    if not chunks:
        print("Error: No se pudieron generar chunks del texto.")
        return None

    # 3. Generar audio para cada chunk
    temp_audio_files = await generate_speech_for_chunks(chunks, voice, TEMP_AUDIO_DIR)
    if not temp_audio_files:
        print("Error: No se generaron archivos de audio para los chunks.")
        cleanup_files([], TEMP_AUDIO_DIR) # Intenta limpiar el directorio si se creó
        return None

    # 4. Concatenar audios
    success = concatenate_audio(temp_audio_files, output_audio_path)

    # 5. Limpiar archivos temporales
    cleanup_files(temp_audio_files, TEMP_AUDIO_DIR)

    if success:
        print(f"¡Voz en off generada exitosamente en {output_audio_path}!")
        return output_audio_path # Devuelve la ruta del archivo final
    else:
        print("La generación de la voz en off falló durante la concatenación.")
        return None

# --- Ejemplo de Uso ---
async def main():
    script_file = "guiones/005_estructura_santa_ines.txt"  # <--- CAMBIA ESTO
    output_file = "voz_final.mp3"        # <--- CAMBIA ESTO
    # Opcional: especificar una voz diferente
    # voice_selection = "es-MX-DaliaNeural"
    # await create_voiceover_from_script(script_file, output_file, voice=voice_selection)

    final_audio = await create_voiceover_from_script(script_file, output_file)

    if final_audio:
        print(f"\nProceso completado. El archivo final es: {final_audio}")
    else:
        print("\nEl proceso no se completó correctamente.")

if __name__ == "__main__":
    # Para ejecutar la función asíncrona principal
    # En Python 3.7+
    try:
        asyncio.run(main())
    except ImportError: # Para versiones < 3.7 (menos común ahora)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())