"""
Módulo para gestionar diferentes proveedores de IA (Gemini, OpenAI) con manejo de errores
y lógica de fallback cuando se exceden las cuotas o hay otros problemas.
"""

import os
import time
import logging
from typing import Tuple, Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuración de proveedores de IA ---
try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
    GEMINI_AVAILABLE = True
except ImportError:
    logging.warning("No se pudo importar google.generativeai. Instala con 'pip install google-generativeai'.")
    GEMINI_AVAILABLE = False
except Exception as e:
    logging.error(f"Error al importar Gemini: {e}")
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletion
    from openai import RateLimitError as OpenAIRateLimitError, APIError as OpenAIAPIError
    OPENAI_AVAILABLE = True
except ImportError:
    logging.warning("No se pudo importar openai. Instala con 'pip install openai'.")
    OPENAI_AVAILABLE = False
except Exception as e:
    logging.error(f"Error al importar OpenAI: {e}")
    OPENAI_AVAILABLE = False

# --- Excepción Personalizada para Señalar Fallo de Gemini ---
class GeminiAPIFailure(Exception):
    """Excepción para indicar que Gemini falló y se debe intentar el fallback."""
    pass

class AIProviders:
    """Clase para gestionar diferentes proveedores de IA con lógica de fallback."""
    
    def __init__(self):
        """Inicializa los clientes de IA si las claves están disponibles."""
        self.gemini_model = None
        self.openai_client = None
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")  # Usar la misma variable que ya usas
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Inicializar Gemini si está disponible
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')  # Usar el mismo modelo que ya usas
                logging.info("Cliente Gemini configurado correctamente.")
            except Exception as e:
                logging.error(f"Error al configurar Gemini: {e}")
        elif not self.gemini_api_key:
            logging.warning("GOOGLE_API_KEY no encontrada en variables de entorno.")
        
        # Inicializar OpenAI si está disponible
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logging.info("Cliente OpenAI configurado correctamente.")
            except Exception as e:
                logging.error(f"Error al configurar OpenAI: {e}")
        elif not self.openai_api_key:
            logging.warning("OPENAI_API_KEY no encontrada en variables de entorno.")
    
    def call_gemini_api(self, system_prompt: str, user_prompt: str, 
                       retries: int = 1, initial_delay: int = 45,
                       safety_settings: Optional[list] = None) -> str:
        """
        Intenta llamar a la API de Gemini, maneja errores 429 con reintentos.
        
        Args:
            system_prompt: Instrucciones del sistema para el modelo.
            user_prompt: Prompt del usuario ya formateado.
            retries: Número de reintentos si hay error de cuota.
            initial_delay: Tiempo inicial de espera entre reintentos (segundos).
            safety_settings: Configuración de seguridad para Gemini.
            
        Returns:
            Texto generado por Gemini.
            
        Raises:
            GeminiAPIFailure: Si Gemini falla después de todos los reintentos.
        """
        if not self.gemini_model:
            raise GeminiAPIFailure("Cliente Gemini no configurado o falló al inicializar.")
        
        # Combinar system_prompt y user_prompt como se hace en tu código actual
        meta_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        current_delay = initial_delay
        for attempt in range(retries + 1):
            try:
                logging.info(f"Llamando a Gemini (Intento {attempt + 1}/{retries + 1})...")
                
                # Realizar la llamada a Gemini con la misma configuración que ya usas
                response = self.gemini_model.generate_content(
                    meta_prompt,
                    safety_settings=safety_settings
                )
                
                # Validar la respuesta
                if not response.text:
                    logging.warning(f"Intento {attempt + 1}: Respuesta de Gemini sin contenido.")
                    if attempt < retries:
                        logging.info(f"Reintentando en {current_delay} segundos debido a respuesta vacía...")
                        time.sleep(current_delay)
                        current_delay *= 2  # Backoff exponencial
                        continue
                    else:
                        raise GeminiAPIFailure("Respuesta de Gemini vacía tras reintentos.")
                
                logging.info(f"Intento {attempt + 1}: Éxito con Gemini.")
                return response.text.strip()
                
            except ResourceExhausted as e:
                # Error 429 - Cuota Excedida
                logging.warning(f"Intento {attempt + 1}: Cuota Gemini Excedida (429). {e}")
                if attempt < retries:
                    # Intentar obtener el delay del error si existe
                    delay = current_delay
                    try:
                        # Extraer retry_delay si está disponible
                        retry_info = getattr(e, 'retry', None)
                        if retry_info and hasattr(retry_info, 'delay'):
                            delay = max(int(retry_info.delay.total_seconds()), 1)
                            logging.info(f"Usando retry delay de la API: {delay}s")
                    except Exception:
                        logging.info("No se pudo extraer retry delay de la API, usando backoff.")
                    
                    logging.info(f"Reintentando llamada a Gemini en {delay} segundos...")
                    time.sleep(delay)
                    current_delay *= 2  # Backoff exponencial
                else:
                    logging.error("Cuota Gemini Excedida, sin más reintentos.")
                    raise GeminiAPIFailure("Cuota Gemini Excedida tras reintentos.") from e
                    
            except (InternalServerError, ServiceUnavailable) as e:
                # Errores 5xx - Problemas temporales del servidor
                logging.warning(f"Intento {attempt + 1}: Error Temporal del Servidor Gemini (5xx). {e}")
                if attempt < retries:
                    logging.info(f"Reintentando llamada a Gemini en {current_delay} segundos...")
                    time.sleep(current_delay)
                    current_delay *= 2
                else:
                    logging.error("Error del Servidor Gemini persiste tras reintentos.")
                    raise GeminiAPIFailure("Error del Servidor Gemini tras reintentos.") from e
                    
            except Exception as e:
                # Cualquier otro error inesperado con Gemini
                logging.error(f"Intento {attempt + 1}: Error inesperado con Gemini: {e}")
                raise GeminiAPIFailure(f"Error inesperado con Gemini: {e}") from e
        
        # Si se agotan los reintentos sin éxito
        raise GeminiAPIFailure("Llamada a Gemini falló tras todos los reintentos.")
    
    def call_openai_api(self, system_prompt: str, user_prompt: str, 
                       model: str = "gpt-3.5-turbo") -> Optional[str]:
        """
        Llama a la API de OpenAI.
        
        Args:
            system_prompt: Instrucciones del sistema para el modelo.
            user_prompt: Prompt del usuario ya formateado.
            model: Modelo de OpenAI a utilizar.
            
        Returns:
            Texto generado por OpenAI o None si hay error.
        """
        if not self.openai_client:
            logging.error("Cliente OpenAI no configurado.")
            return None
        
        try:
            logging.info(f"Llamando a OpenAI API (Modelo: {model})...")
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Validar la respuesta
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                logging.info("Éxito con OpenAI.")
                return response.choices[0].message.content.strip()
            else:
                finish_reason = response.choices[0].finish_reason if response.choices else "desconocida"
                logging.error(f"Respuesta de OpenAI inesperada o vacía. Razón final: {finish_reason}")
                return None
                
        except OpenAIRateLimitError as e:
            logging.error(f"Cuota OpenAI Excedida: {e}")
            return None
        except OpenAIAPIError as e:
            logging.error(f"Error de API OpenAI: {e}")
            return None
        except Exception as e:
            logging.error(f"Error inesperado con OpenAI: {e}")
            return None
    
    def generate_prompt_with_fallback(self, system_prompt: str, user_prompt: str,
                                     openai_model: str = "gpt-3.5-turbo",
                                     gemini_retries: int = 1,
                                     gemini_initial_delay: int = 45,
                                     safety_settings: Optional[list] = None) -> Tuple[Optional[str], str]:
        """
        Intenta generar prompt con Gemini, si falla, usa OpenAI como fallback.
        
        Args:
            system_prompt: Instrucciones del sistema para el modelo.
            user_prompt: Prompt del usuario ya formateado.
            openai_model: Modelo de OpenAI a usar en fallback.
            gemini_retries: Número de reintentos para Gemini.
            gemini_initial_delay: Delay inicial para reintento Gemini.
            safety_settings: Configuración de seguridad para Gemini.
            
        Returns:
            Tupla con (prompt generado, proveedor usado).
            El proveedor puede ser 'Gemini', 'OpenAI', o 'None'.
        """
        prompt = None
        provider = "None"
        
        # Intentar con Gemini
        try:
            prompt = self.call_gemini_api(
                system_prompt,
                user_prompt,
                retries=gemini_retries,
                initial_delay=gemini_initial_delay,
                safety_settings=safety_settings
            )
            if prompt:
                provider = "Gemini"
                
        except GeminiAPIFailure as e:
            logging.warning(f"Fallo de Gemini detectado ({e}). Intentando fallback con OpenAI...")
            # Continuar al bloque de OpenAI
            
        except Exception as e_gemini_unhandled:
            logging.error(f"Error grave no manejado durante la llamada a Gemini: {e_gemini_unhandled}")
            # Intentar fallback de todas formas
        
        # Si Gemini falló, intentar con OpenAI
        if not prompt:
            prompt = self.call_openai_api(system_prompt, user_prompt, model=openai_model)
            if prompt:
                provider = f"OpenAI ({openai_model})"
            else:
                logging.error("Fallback a OpenAI también falló.")
                provider = "None"
        
        if not prompt:
            logging.error("GENERACIÓN DE PROMPT FALLIDA - Ambos proveedores (Gemini y OpenAI) fallaron.")
        
        return prompt, provider


# Instancia global para uso en todo el proyecto
ai_providers = AIProviders()
