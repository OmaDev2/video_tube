import asyncio
from pathlib import Path # Para manipulación de rutas

# Asegúrate de que estas importaciones funcionen según la estructura de tu proyecto.
# Asume que tienes un archivo 'tts_generator.py' (o similar) con esta función y constante.
try:
    from tts_generator import create_voiceover_from_script, OUTPUT_FORMAT
except ImportError:
    print("Advertencia: No se pudo importar 'create_voiceover_from_script' o 'OUTPUT_FORMAT'.")
    print("Asegúrate de que el archivo tts_generator.py esté accesible.")
    # Define valores por defecto si la importación falla, para que el ejemplo se pueda entender
    async def create_voiceover_from_script(script_path, output_path, voice=None):
         print(f"Simulando: Generando audio desde '{script_path}' a '{output_path}'")
         # En una ejecución real, esto crearía el archivo
         Path(output_path).touch() # Crea un archivo vacío como marcador
         return output_path # Devuelve la ruta simulada
    OUTPUT_FORMAT = "mp3"

# --- Función main Completa ---
async def main():
    """
    Función principal que configura las rutas de entrada/salida
    y llama al proceso de generación de voz en off.
    """
    # --- 1. Configuración del Archivo de Entrada ---
    # Cambia esta línea para apuntar a tu archivo de guion
    script_file_path_str = "guiones/005_estructura_santa_ines.txt"

    # --- 2. Validación del Archivo de Entrada ---
    script_path = Path(script_file_path_str)
    if not script_path.is_file():
        print(f"Error Crítico: El archivo de guion especificado no existe.")
        print(f"Ruta buscada: {script_path.resolve()}") # Muestra la ruta absoluta buscada
        return # Termina la ejecución si el guion no se encuentra

    # --- 3. Generación Dinámica del Nombre de Archivo de Salida ---
    base_name = script_path.stem # Obtiene el nombre sin extensión (ej: "005_estructura_santa_ines")
    audio_extension = f".{OUTPUT_FORMAT}" # Obtiene la extensión (ej: ".mp3")

    # --- Elige dónde guardar el archivo de salida ---
    # Opción A: Guardar en el directorio actual de trabajo
    output_dir = Path(".")
    # Opción B: Guardar en el mismo directorio que el script de entrada
    # output_dir = script_path.parent
    # Opción C: Guardar en un subdirectorio específico (ej: 'audio_generado')
    # output_dir = Path("audio_generado")
    # output_dir.mkdir(parents=True, exist_ok=True) # Crea el directorio si no existe

    # Construye la ruta completa del archivo de salida
    output_file_path = output_dir / f"{base_name}{audio_extension}"

    print("-" * 30)
    print(f"Archivo de Guion  : {script_file_path_str}")
    print(f"Directorio Salida : {output_dir.resolve()}") # Muestra ruta absoluta de salida
    print(f"Archivo de Audio  : {output_file_path.name}")
    print("-" * 30)

    # --- 4. Llamada a la Función de Generación de Voz ---
    print("Iniciando el proceso de Texto a Voz...")
    # Llama a la función principal del otro módulo, pasando las rutas como strings
    final_audio_path = await create_voiceover_from_script(
        script_path=str(script_path), # Pasa la ruta del script como string
        output_audio_path=str(output_file_path) # Pasa la ruta de salida como string
        # Opcionalmente, puedes pasar la voz aquí si no quieres usar la default:
        # voice="es-MX-DaliaNeural"
    )
    print("Proceso de Texto a Voz finalizado.")
    print("-" * 30)


    # --- 5. Reporte Final ---
    if final_audio_path and Path(final_audio_path).is_file():
        # final_audio_path debería ser la misma ruta que output_file_path si tuvo éxito
        print(f"¡Éxito! La voz en off se ha generado correctamente.")
        print(f"Archivo guardado en: {Path(final_audio_path).resolve()}")
    else:
        print("Error: La generación de la voz en off falló o el archivo final no se encontró.")
        if final_audio_path:
             print(f"(Se esperaba el archivo en: {Path(final_audio_path).resolve()})")

    print("-" * 30)

# --- Punto de Entrada Principal ---
if __name__ == "__main__":
    print("Ejecutando script principal...")
    # Ejecuta la función asíncrona 'main'
    asyncio.run(main())
    print("Script principal ha finalizado.")