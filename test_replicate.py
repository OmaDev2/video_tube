# -*- coding: utf-8 -*-
# test_replicate.py

import os
import replicate
import requests
from pathlib import Path
from dotenv import load_dotenv
import time

# --- Configuración ---
# Cargar variables de entorno (buscará el archivo .env)
load_dotenv()
print("INFO: Intentando cargar .env")

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# --- ¡¡IMPORTANTE!! Revisa el identificador correcto en Replicate ---
# Ve a replicate.com, busca "flux-schnell" y copia el identificador
# que aparece en la pestaña API o ejemplos de Python.
# Prueba primero SIN el hash de versión largo.
MODEL_IDENTIFIER = "black-forest-labs/flux-schnell"
# Si el anterior no funciona, busca la versión MÁS RECIENTE en Replicate y pégala aquí:
# MODEL_IDENTIFIER = "black-forest-labs/flux-schnell:HASH_DE_VERSION_CORRECTO"

# Prompt de prueba simple en inglés
TEST_PROMPT = "A cinematic, photorealistic image of a single red rose on a dark background, detailed petals, dramatic lighting, 16:9 aspect ratio"

# Parámetros fijos que querías (asegúrate que coincidan con el schema actual del modelo en Replicate)
INPUT_PARAMS = {
    "prompt": TEST_PROMPT,
    "go_fast": True,
    "megapixels": "1",
    "num_outputs": 1,
    "aspect_ratio": "16:9", # ¡Asegúrate que este aspect ratio es válido!
    "output_format": "png",
    "output_quality": 90, # Irrelevante para PNG pero lo dejamos
    "num_inference_steps": 4
}

# Dónde guardar la imagen de prueba
output_image_name = "test_replicate_output.png"
output_image_path = Path(output_image_name)
# --- Fin Configuración ---


def run_replicate_test():
    print("--- Iniciando Test Replicate API ---")

    if not REPLICATE_API_TOKEN:
        print("ERROR: Variable de entorno REPLICATE_API_TOKEN no encontrada.")
        print("Asegúrate de tenerla en tu archivo .env y de haber ejecutado 'pip install python-dotenv'.")
        return

    # No necesitas instanciar el cliente si la variable de entorno está configurada
    # La librería 'replicate' la usará automáticamente.

    print(f"Usando modelo: {MODEL_IDENTIFIER}")
    print(f"Con input: {INPUT_PARAMS}")

    try:
        start_time = time.time()
        print("Llamando a replicate.run()... (puede tardar)")
        # Ejecutar el modelo
        output = replicate.run(
            MODEL_IDENTIFIER,
            input=INPUT_PARAMS
        )
        end_time = time.time()
        print(f"Llamada a Replicate completada en {end_time - start_time:.2f} segundos.")

        # Procesar la salida (generalmente una lista de URLs)
        print(f"Salida recibida de Replicate: {output}")

        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
            print(f"Descargando imagen desde: {image_url}")

            # Descargar usando requests
            response = requests.get(image_url, stream=True, timeout=60) # Timeout de 60s
            response.raise_for_status() # Lanza error si la descarga falla

            # Guardar la imagen
            with open(output_image_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if output_image_path.is_file() and output_image_path.stat().st_size > 0:
                 print(f"¡ÉXITO! Imagen guardada en: {output_image_path.resolve()}")
            else:
                 print(f"ERROR: Faltó guardar la imagen descargada en {output_image_path}")

        else:
            print("ERROR: La salida de Replicate no fue una lista con al menos una URL.")

    except replicate.exceptions.ReplicateError as r_err:
         print("\n!!!!!!!! ERROR DE API REPLICATE !!!!!!!!")
         print(f"Status: {getattr(r_err, 'status', 'N/A')}")
         print(f"Título: {getattr(r_err, 'title', 'N/A')}")
         print(f"Detalle: {getattr(r_err, 'detail', 'N/A')}")
         print("Verifica el MODEL_IDENTIFIER y tu API Token en Replicate.")
    except requests.exceptions.RequestException as req_err:
         print(f"\n!!!!!!!! ERROR DE DESCARGA !!!!!!!!")
         print(f"Error al descargar la imagen desde la URL: {req_err}")
    except Exception as e:
        print("\n!!!!!!!! ERROR INESPERADO !!!!!!!!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("--- Test Replicate Finalizado ---")


if __name__ == "__main__":
    run_replicate_test()