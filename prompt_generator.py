# En app.py o prompt_generator.py
import google.generativeai as genai
import os
import math
import re
from pathlib import Path
from typing import List, Dict, Any # Importar Dict, Any, List

# --- Configuración API Key (Leer desde entorno) ---
# (Asegúrate de que esta configuración se ejecute ANTES de llamar a generar_prompts...)
# Puedes ponerla al principio del archivo app.py o gui.py
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ADVERTENCIA: Variable de entorno GOOGLE_API_KEY no encontrada. La generación de prompts fallará.")
        GEMINI_AVAILABLE = False
    else:
        genai.configure(api_key=api_key)
        print("INFO: Clave API de Google configurada.")
        GEMINI_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar google.generativeai. Instala con 'pip install google-generativeai'.")
    GEMINI_AVAILABLE = False
except Exception as e:
    print(f"ERROR configurando la API de Google: {e}")
    GEMINI_AVAILABLE = False


def segmentar_script(texto_completo: str, num_segmentos: int, tiempos_imagenes: List[Dict[str, Any]] = None) -> list[str]:
    """Divide el texto en un número aproximado de segmentos.
    
    Args:
        texto_completo: El texto completo del guion
        num_segmentos: Número de segmentos deseados
        tiempos_imagenes: Lista de diccionarios con información de tiempos para cada imagen
            Cada diccionario contiene: 'indice', 'inicio', 'fin', 'duracion'
    
    Returns:
        Lista de segmentos de texto
    """
    if num_segmentos <= 0: return []
    
    # Dividir por párrafos
    parrafos = [p.strip() for p in texto_completo.split('\n\n') if p.strip()]
    if not parrafos: return []
    
    # Si tenemos información de tiempos, intentamos dividir el texto proporcionalmente
    if tiempos_imagenes and len(tiempos_imagenes) == num_segmentos:
        print(f"Usando información de tiempos para {len(tiempos_imagenes)} imágenes")
        
        # Calcular la duración total del audio
        duracion_total = tiempos_imagenes[-1]['fin']
        
        # Dividir los párrafos según los tiempos de las imágenes
        segmentos = []
        total_caracteres = len(texto_completo)
        texto_completo_limpio = "\n\n".join(parrafos)
        
        for tiempo in tiempos_imagenes:
            # Calcular qué porcentaje del tiempo total corresponde a esta imagen
            porcentaje_tiempo = tiempo['duracion'] / duracion_total
            
            # Calcular cuántos caracteres corresponden a este segmento
            caracteres_segmento = int(total_caracteres * porcentaje_tiempo)
            
            # Asegurarse de que no nos pasamos del texto disponible
            if texto_completo_limpio:
                # Tomar el segmento correspondiente
                if caracteres_segmento >= len(texto_completo_limpio):
                    segmento = texto_completo_limpio
                    texto_completo_limpio = ""
                else:
                    # Intentar cortar por un salto de línea o espacio para no cortar palabras
                    indice_corte = min(caracteres_segmento, len(texto_completo_limpio) - 1)
                    while indice_corte > 0 and indice_corte < len(texto_completo_limpio) and texto_completo_limpio[indice_corte] not in [' ', '\n', '.', ',', ';', ':', '!', '?']:
                        indice_corte -= 1
                    
                    if indice_corte <= 0:
                        indice_corte = min(caracteres_segmento, len(texto_completo_limpio))
                    
                    segmento = texto_completo_limpio[:indice_corte].strip()
                    texto_completo_limpio = texto_completo_limpio[indice_corte:].strip()
                
                segmentos.append(segmento)
            else:
                # Si ya no queda texto, añadir un segmento vacío
                segmentos.append("")
        
        print(f"Script dividido en {len(segmentos)} segmentos basados en tiempos para {num_segmentos} imágenes.")
        return segmentos
    
    # Estrategia tradicional: dividir por párrafos y luego agrupar/dividir
    total_parrafos = len(parrafos)
    parrafos_por_segmento = max(1, math.ceil(total_parrafos / num_segmentos))

    segmentos = []
    for i in range(0, total_parrafos, parrafos_por_segmento):
        segmento = "\n\n".join(parrafos[i:i + parrafos_por_segmento])
        segmentos.append(segmento)

    # Ajustar si tenemos demasiados o pocos segmentos
    segmentos = segmentos[:num_segmentos]  # Limitar al número máximo de segmentos
    
    # Si tenemos menos segmentos que imágenes, repetir el último segmento
    while len(segmentos) < num_segmentos:
        segmentos.append(segmentos[-1] if segmentos else "")
    
    print(f"Script dividido en {len(segmentos)} segmentos para {num_segmentos} imágenes deseadas.")
    return segmentos


def generar_prompts_con_gemini(script_text: str, num_imagenes: int, video_title: str, estilo_base: str = "cinematográfico", tiempos_imagenes: List[Dict[str, Any]] = None) -> List[Dict[str, str]] | None:
    """Genera prompts de imagen en INGLÉS usando Gemini para segmentos de un guion,
    incluyendo el título del vídeo como contexto. Devuelve una lista de diccionarios
    con el segmento original y el prompt generado."""
    if not GEMINI_AVAILABLE:
        print("ERROR: La API de Gemini no está configurada o disponible.")
        return None

    print(f"Generando {num_imagenes} prompts con Gemini...")
    # Usar la información de tiempos si está disponible
    segmentos = segmentar_script(script_text, num_imagenes, tiempos_imagenes)
    if not segmentos:
        print("ERROR: No se pudo segmentar el guion.")
        return None

    # Ajustar si el número de segmentos no coincide exactamente (usar hasta num_imagenes)
    segmentos = segmentos[:num_imagenes]
    if len(segmentos) < num_imagenes:
        print(f"Advertencia: Se generarán solo {len(segmentos)} prompts porque hay pocos segmentos.")

    # Configurar modelo Gemini (ej: gemini-pro, verifica modelos disponibles)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
    except Exception as e:
         print(f"Error al inicializar el modelo Gemini: {e}")
         return None

    resultados_prompts = []  # Lista para almacenar resultados
    for i, segmento in enumerate(segmentos):
        print(f" - Generando prompt para segmento {i+1}/{len(segmentos)}...")

        # Crear el "meta-prompt"
        meta_prompt = f"""Eres un asistente experto en visualización creativa para vídeos. El título general del vídeo es "{video_title}". A partir del siguiente fragmento de texto de ese guion, genera un prompt conciso y descriptivo (máximo 60 palabras) **en INGLÉS** para un modelo de generación de imágenes como Flux Schnell o Stable Diffusion. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El estilo visual general es {estilo_base}. El aspect ratio es 16:9. Describe la escena, los elementos principales, la iluminación y la atmósfera.

Fragmento del Guion:
"{segmento}"

Generated English Prompt:""" # Pedimos que continúe en inglés

        try:
            
            # Llamar a la API de Gemini
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            response = model.generate_content(meta_prompt, safety_settings=safety_settings)
            
                         

           # Intentar extraer texto, manejar posible bloqueo de seguridad
            if response.parts:
                 generated_prompt_en = response.text.strip()
                 generated_prompt_en = re.sub(r'^(Generated English Prompt:|Prompt:|Aquí tienes el prompt:)\s*', '', generated_prompt_en, flags=re.IGNORECASE).strip()
            elif response.prompt_feedback.block_reason:
                 print(f"   - ADVERTENCIA: Respuesta bloqueada por seguridad ({response.prompt_feedback.block_reason}).")
                 generated_prompt_en = f"Error: Respuesta bloqueada ({response.prompt_feedback.block_reason})"
            else:
                 # Caso raro: no hay partes ni bloqueo
                 print("   - ADVERTENCIA: Gemini no devolvió contenido ni razón de bloqueo.")
                 generated_prompt_en = f"Error: Respuesta vacía de Gemini."


            if generated_prompt_en and not generated_prompt_en.startswith("Error"):
                print(f"   - Prompt (EN): {generated_prompt_en}")
                prompt_actual_en = generated_prompt_en # Guardar el bueno
            else:
                # Mantener el prompt de error si no se generó bien
                 print(f"   - INFO: Se usará prompt de error para segmento {i+1}")


        except Exception as e:
            print(f"   - ERROR al llamar a la API de Gemini para segmento {i+1}: {e}")
            prompt_actual_en = f"ERROR API Gemini para: {segmento[:50]}..."

        # Guardar el resultado (segmento original y prompt generado en inglés)
        resultados_prompts.append({
            "segmento_es": segmento,
            "prompt_en": prompt_actual_en
        })

    print(f"Generados {len(resultados_prompts)} prompts.")
    return resultados_prompts # Devuelve lista de diccionarios