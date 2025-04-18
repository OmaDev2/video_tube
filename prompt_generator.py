# En app.py o prompt_generator.py
import os
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Importar el nuevo sistema de proveedores de IA
from ai_providers import ai_providers, GEMINI_AVAILABLE

# Configuración de logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verificar si OpenAI está disponible como fallback
from ai_providers import OPENAI_AVAILABLE
if OPENAI_AVAILABLE:
    print("INFO: OpenAI está disponible como fallback si Gemini falla.")
else:
    print("ADVERTENCIA: OpenAI no está disponible como fallback. Verifica la instalación y la API key.")


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


def generar_prompts_con_gemini(script_text: str, num_imagenes: int, video_title: str, estilo_base: str = "default", tiempos_imagenes: List[Dict[str, Any]] = None) -> List[Dict[str, str]] | None:
    """Genera prompts de imagen en INGLÉS usando Gemini (con fallback a OpenAI) para segmentos de un guion,
    incluyendo el título del vídeo como contexto. Devuelve una lista de diccionarios
    con el segmento original y el prompt generado."""
    if not GEMINI_AVAILABLE and not OPENAI_AVAILABLE:
        logging.error("ERROR: Ni Gemini ni OpenAI están configurados o disponibles.")
        return None

    logging.info(f"Generando {num_imagenes} prompts (Gemini con fallback a OpenAI)...")
    # Usar la información de tiempos si está disponible
    segmentos = segmentar_script(script_text, num_imagenes, tiempos_imagenes)
    if not segmentos:
        logging.error("ERROR: No se pudo segmentar el guion.")
        return None

    # Ajustar si el número de segmentos no coincide exactamente (usar hasta num_imagenes)
    segmentos = segmentos[:num_imagenes]
    if len(segmentos) < num_imagenes:
        logging.warning(f"Advertencia: Se generarán solo {len(segmentos)} prompts porque hay pocos segmentos.")
    
    # Resumen simple de los prompts a generar
    logging.info(f"[PROMPTS] Título: '{video_title}' | Estilo: '{estilo_base}' | Total prompts a generar: {len(segmentos)}")
    logging.info(f"[PROMPTS] Proceso de generación de prompts iniciado...")
    # Si quieres ver un ejemplo del primer segmento, lo mostramos truncado
    if segmentos:
        logging.info(f"[PROMPTS] Ejemplo de segmento 1: '{segmentos[0][:100]}{'...' if len(segmentos[0]) > 100 else ''}'")
    # (Opcional: si quieres mostrar todos los segmentos, puedes habilitar un flag o usar nivel DEBUG)
    # logging.debug(f"Todos los segmentos: {segmentos}")

    resultados_prompts = []  # Lista para almacenar resultados
    for i, segmento in enumerate(segmentos):
        porcentaje = ((i+1) / len(segmentos)) * 100
        logging.info(f"[PROMPTS] Generando prompt {i+1} de {len(segmentos)}... ({porcentaje:.1f}% completado)")

        # Usar el gestor de prompts si está disponible
        try:
            from prompt_manager import PromptManager
            prompt_manager = PromptManager()
            
            #logging.info(f"\n\nEstilo solicitado: '{estilo_base}'")
            #logging.info(f"Estilos disponibles: {prompt_manager.get_prompt_ids()}")
            
            # Caso especial para el estilo psicodélico
            if estilo_base == 'psicodelicas' or (estilo_base == 'default' and video_title and 'psicod' in video_title.lower()):
                estilo_base = 'psicodelicas'
                #logging.info(f"*** APLICANDO ESTILO PSICODÉLICO ***")
            
            # Comprobar si el estilo existe en el gestor de prompts
            if estilo_base in prompt_manager.get_prompt_ids():
                #logging.info(f"Usando estilo: '{estilo_base}'")
                
                # Obtener el system prompt y user prompt del estilo seleccionado
                system_prompt = prompt_manager.get_system_prompt(estilo_base)
                user_prompt = prompt_manager.get_user_prompt(estilo_base, video_title, segmento)
                negative_prompt = prompt_manager.get_prompt(estilo_base)["negative_prompt"]
                
                # Imprimir los valores que se van a usar para formatear el prompt
                #logging.info(f"\n=== VALORES PARA FORMATEO DE PROMPT ===")
                #logging.info(f"SEGMENTO ORIGINAL: '{segmento[:100]}...' (truncado)" if len(segmento) > 100 else f"SEGMENTO ORIGINAL: '{segmento}'")
                #logging.info(f"TITULO DEL VIDEO: '{video_title}'")
                #logging.info(f"USER PROMPT ORIGINAL: '{user_prompt[:100]}...' (truncado)" if len(user_prompt) > 100 else f"USER PROMPT ORIGINAL: '{user_prompt}'")
                
                # Verificar si el user_prompt contiene los placeholders esperados
                has_titulo_placeholder = "{titulo}" in user_prompt
                has_escena_placeholder = "{escena}" in user_prompt
                #logging.info(f"USER PROMPT CONTIENE PLACEHOLDER TITULO: {has_titulo_placeholder}")
                #logging.info(f"USER PROMPT CONTIENE PLACEHOLDER ESCENA: {has_escena_placeholder}")
                
                # Asegurarse de que los placeholders {titulo} y {escena} se reemplacen correctamente
                try:
                    # Intentar usar el user prompt con ambos placeholders
                    user_prompt_formateado = user_prompt.format(titulo=video_title, escena=segmento)
                    #logging.info(f"FORMATEO EXITOSO CON AMBOS PLACEHOLDERS")
                except KeyError as e:
                    # Si falta alguno de los placeholders, usar el formato antiguo
                    logging.warning(f"ERROR DE FORMATEO: {e}")
                    logging.info(f"INTENTANDO FORMATO ALTERNATIVO")
                    context = f"{video_title}: {segmento}" if video_title else segmento
                    try:
                        user_prompt_formateado = user_prompt.format(escena=context)
                        logging.info(f"FORMATEO ALTERNATIVO EXITOSO")
                    except Exception as e2:
                        logging.error(f"ERROR EN FORMATEO ALTERNATIVO: {e2}")
                        # En caso de error, usar un formato simple sin placeholders
                        user_prompt_formateado = f"Generate an image prompt for the following scene from '{video_title}': {segmento}"
                        logging.info(f"USANDO FORMATO DE EMERGENCIA SIN PLACEHOLDERS")
                
                logging.info(f"\n=== PROMPT COMPLETO ENVIADO A IA ===\n")
                logging.info(f"SYSTEM PROMPT:\n{system_prompt}\n")
                logging.info(f"USER PROMPT FORMATEADO:\n{user_prompt_formateado}\n")
                logging.info(f"NEGATIVE PROMPT:\n{negative_prompt}\n")
                logging.info(f"=== FIN DEL PROMPT ===\n")
                
                # Configurar safety settings para Gemini
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                # Usar el sistema de fallback para generar el prompt
                generated_prompt, provider = ai_providers.generate_prompt_with_fallback(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt_formateado,
                    openai_model="gpt-3.5-turbo",  # Puedes cambiar a gpt-4-turbo si prefieres
                    gemini_retries=2,  # Número de reintentos para Gemini
                    gemini_initial_delay=3,  # Delay inicial en segundos (ajustado a 3)
                    safety_settings=safety_settings
                )
                
                # Registrar qué proveedor se usó
                logging.info(f"Prompt generado usando: {provider}")
                
            else:
                # Si el estilo no existe, usar el prompt por defecto
                system_prompt = f"""Eres un asistente experto en visualización creativa para vídeos. El título general del vídeo es "{video_title}". A partir del siguiente fragmento de texto de ese guion, genera un prompt conciso y descriptivo (máximo 60 palabras) **en INGLÉS** para un modelo de generación de imágenes como Flux Schnell o Stable Diffusion. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El estilo visual general es cinematográfico. El aspect ratio es 16:9. Describe la escena, los elementos principales, la iluminación y la atmósfera."""
                user_prompt_formateado = f"Fragmento del Guion:\n\"{segmento}\"\n\nGenerated English Prompt:"
                
                # Configurar safety settings para Gemini
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                # Usar el sistema de fallback para generar el prompt
                generated_prompt, provider = ai_providers.generate_prompt_with_fallback(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt_formateado,
                    openai_model="gpt-3.5-turbo",
                    gemini_retries=2,
                    gemini_initial_delay=3,
                    safety_settings=safety_settings
                )
                
                # Registrar qué proveedor se usó
                logging.info(f"Prompt generado usando: {provider}")
                
        except ImportError:
            # Si no se puede importar el gestor de prompts, usar el prompt por defecto
            system_prompt = f"""Eres un asistente experto en visualización creativa para vídeos. El título general del vídeo es "{video_title}". A partir del siguiente fragmento de texto de ese guion, genera un prompt conciso y descriptivo (máximo 60 palabras) **en INGLÉS** para un modelo de generación de imágenes como Flux Schnell o Stable Diffusion. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El estilo visual general es {estilo_base}. El aspect ratio es 16:9. Describe la escena, los elementos principales, la iluminación y la atmósfera."""
            user_prompt_formateado = f"Fragmento del Guion:\n\"{segmento}\"\n\nGenerated English Prompt:"
            
            # Configurar safety settings para Gemini
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            # Usar el sistema de fallback para generar el prompt
            generated_prompt, provider = ai_providers.generate_prompt_with_fallback(
                system_prompt=system_prompt,
                user_prompt=user_prompt_formateado,
                openai_model="gpt-3.5-turbo",
                gemini_retries=2,
                gemini_initial_delay=3,
                safety_settings=safety_settings
            )
            
            # Registrar qué proveedor se usó
            logging.info(f"Prompt generado usando: {provider}")
        
        try:
            # Procesar la respuesta generada por el sistema de fallback
            if generated_prompt:
                # Limpiar el prompt generado
                prompt_actual_en = generated_prompt.strip()
                # Eliminar prefijos comunes que los modelos pueden añadir
                prompt_actual_en = re.sub(r'^(Generated English Prompt:|English Prompt:|Prompt:|Here\'s the prompt:|Here is the prompt:|Aquí tienes el prompt:)\s*', '', prompt_actual_en, flags=re.IGNORECASE).strip()
                
                logging.info(f"   - Prompt generado ({provider}): {prompt_actual_en[:100]}..." if len(prompt_actual_en) > 100 else f"   - Prompt generado ({provider}): {prompt_actual_en}")
            else:
                # Si ambos proveedores fallaron
                error_msg = f"Error: Todos los proveedores de IA fallaron al generar el prompt para el segmento {i+1}"
                logging.error(error_msg)
                prompt_actual_en = error_msg
                provider = "None"
                
        except Exception as e:
            error_msg = f"ERROR al procesar respuesta para segmento {i+1}: {e}"
            logging.error(error_msg)
            prompt_actual_en = f"ERROR: {segmento[:50]}..."
            provider = "Error"

        # Guardar el resultado (segmento original, prompt generado y proveedor)
        resultados_prompts.append({
            "segmento_es": segmento,
            "prompt_en": prompt_actual_en,
            "provider": provider,
            "negative_prompt": negative_prompt if 'negative_prompt' in locals() else ""
        })

    logging.info(f"Generados {len(resultados_prompts)} prompts.")
    
    # Mostrar estadísticas de proveedores utilizados
    providers_count = {}
    for result in resultados_prompts:
        provider = result.get("provider", "Desconocido")
        providers_count[provider] = providers_count.get(provider, 0) + 1
    
    logging.info("Estadísticas de proveedores utilizados:")
    for provider, count in providers_count.items():
        logging.info(f"  - {provider}: {count} prompts ({count/len(resultados_prompts)*100:.1f}%)")
    
    return resultados_prompts # Devuelve lista de diccionarios