# Archivo: image_generator.py

import replicate
import requests # Para descargar la imagen desde la URL
from pathlib import Path
import os
import time # Para posibles reintentos o esperas

# La API Key de Replicate se lee automáticamente de la variable de entorno
# REPLICATE_API_TOKEN si está definida (gracias a load_dotenv() en gui.py)

# Verificar si la librería replicate está disponible y configurada
REPLICATE_AVAILABLE = False
REPLICATE_API_TOKEN_CHECK = os.getenv("REPLICATE_API_TOKEN")
if REPLICATE_API_TOKEN_CHECK:
    try:
        # Intenta inicializar el cliente para ver si la API key es válida
        # (Aunque la librería a menudo no necesita inicialización explícita si usa env var)
        # client = replicate.Client(api_token=REPLICATE_API_TOKEN_CHECK) # Opcional, sólo para testeo inicial
        print("INFO: Token API Replicate encontrado en entorno.")
        REPLICATE_AVAILABLE = True
    except Exception as e:
        print(f"ERROR: Token API Replicate encontrado pero falló la configuración/verificación: {e}")
else:
    print("ADVERTENCIA: Variable de entorno REPLICATE_API_TOKEN no encontrada. Generación de imágenes desactivada.")


def generar_imagen_con_replicate(
    prompt_en: str,
    output_image_path: str, # Ruta completa donde guardar la imagen PNG
    aspect_ratio: str = "16:9",
    num_inference_steps: int = 4,
    output_quality: int = 90, # Calidad para jpg/webp, png ignora esto
    go_fast: bool = True,
    megapixels: str = "1"
    ) -> bool:
    """
    Genera una imagen usando un prompt con Flux Schnell en Replicate y la guarda.
    """
    if not REPLICATE_AVAILABLE:
        print("ERROR: API Replicate no disponible o no configurada.")
        return False

    print(f" - Enviando prompt a Replicate/Flux Schnell: '{prompt_en[:80]}...'")
    output_image_path = Path(output_image_path) # Convertir a Path si no lo es
    output_image_path.parent.mkdir(parents=True, exist_ok=True) # Asegurar que la carpeta de salida exista

    # Definir los inputs para el modelo Replicate
    input_data = {
        "prompt": prompt_en,
        "go_fast": go_fast,
        "megapixels": megapixels,
        "num_outputs": 1, # Generamos una imagen por prompt
        "aspect_ratio": aspect_ratio,
        "output_format": "png", # Pedimos PNG
        "output_quality": output_quality, # Relevante si pides jpg/webp
        "num_inference_steps": num_inference_steps
        # "seed": podrías añadir un seed si quieres reproducibilidad
        # "disable_safety_checker": False # Por defecto es False
    }

    try:
        start_time = time.time()
        # Llamar a la API de Replicate
        # NOTA: replicate.run() puede ser BLOQUEANTE y tardar MUCHO.
        output = replicate.run(
            "black-forest-labs/flux-schnell", # ID del modelo/versión
            input=input_data
        )
        end_time = time.time()
        print(f"   - Replicate tardó {end_time - start_time:.2f}s en generar.")

        # Procesar la salida (normalmente es una lista de URLs)
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
            print(f"   - URL de imagen generada: {image_url}")

            # Descargar la imagen desde la URL
            print(f"   - Descargando imagen...")
            response = requests.get(image_url, stream=True)
            response.raise_for_status() # Lanza error si la descarga falla (ej. 404)

            # Guardar la imagen descargada
            with open(output_image_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verificar que se guardó
            if output_image_path.is_file() and output_image_path.stat().st_size > 0:
                 print(f"   - Imagen guardada exitosamente en: {output_image_path.name}")
                 return True
            else:
                 print(f"   - ERROR: Faltó guardar la imagen descargada en {output_image_path}")
                 return False

        else:
            print(f"   - ERROR: La salida de Replicate no fue la esperada: {output}")
            return False

    except replicate.exceptions.ReplicateError as r_err:
         print(f"   - ERROR de API Replicate: {r_err}")
         # Podrías mirar r_err.status o r_err.detail para más info (ej. rate limits)
         return False
    except requests.exceptions.RequestException as req_err:
         print(f"   - ERROR al descargar imagen desde URL: {req_err}")
         return False
    except Exception as e:
        print(f"   - ERROR inesperado durante generación/descarga de imagen: {e}")
        import traceback
        traceback.print_exc()
        return False