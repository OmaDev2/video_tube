# ai_script_generator.py
import os
import re
import json
import asyncio
from dotenv import load_dotenv

# Importar el gestor de prompts
try:
    from script_prompt_manager import ScriptPromptManager
    SCRIPT_PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: No se pudo importar ScriptPromptManager. Se usarán prompts internos si existen.")
    SCRIPT_PROMPT_MANAGER_AVAILABLE = False

# --- IMPORTACIÓN CORREGIDA ---
AI_PROVIDER_AVAILABLE = False
try:
    # Importa la INSTANCIA creada en ai_providers.py
    from ai_providers import ai_providers, GEMINI_AVAILABLE, OPENAI_AVAILABLE

    # Comprueba si al menos uno de los clientes se inicializó
    if GEMINI_AVAILABLE or OPENAI_AVAILABLE:
        AI_PROVIDER_AVAILABLE = True
        print("INFO: Instancia ai_providers importada para generación de guiones.")
    else:
        print("ADVERTENCIA: ai_providers importado pero ningún cliente IA (Gemini/OpenAI) configurado.")

except ImportError:
    print("ADVERTENCIA: No se pudo importar 'ai_providers' o sus flags.")
    print("              La generación de guiones AI no funcionará.")
    AI_PROVIDER_AVAILABLE = False
    # Mantenemos la simulación solo si la importación falla
    def generar_prompt_simulado(system_prompt, user_prompt, *args, **kwargs):
        print("--- SIMULACIÓN AI (Import Fallido) ---")
        print(f"System Prompt (inicio): {system_prompt[:100]}...")
        print(f"User Prompt (inicio): {user_prompt[:100]}...")
        print("--- FIN SIMULACIÓN AI ---")
        if "esquema" in user_prompt.lower():
            return "1. Introducción Simulada\n2. Desarrollo Simulado\n3. Conclusión Simulada", "Simulated"
        elif "metadata" in user_prompt.lower():
            return json.dumps({
                "titulos": ["Título Simulado 1", "Título 2"],
                "frases_miniatura": ["Frase Sim 1", "Frase Sim 2"],
                "prompts_miniatura": ["Prompt Sim 1", "Prompt Sim 2"],
                "descripcion": "Desc Sim.",
                "tags": ["sim1", "sim2"]
            }), "Simulated"
        else:
            return f"Texto simulado generado para la sección {kwargs.get('instruccion_seccion', 'N/A')}", "Simulated"
except Exception as e:
    print(f"ERROR inesperado importando/configurando ai_providers: {e}")
    AI_PROVIDER_AVAILABLE = False


# --- Instancia del Gestor de Prompts de Guion ---
if SCRIPT_PROMPT_MANAGER_AVAILABLE:
    script_manager = ScriptPromptManager()  # Asume que encuentra script_prompts.json
    print("INFO: Gestor de prompts de guion inicializado.")
else:
    script_manager = None  # No hay gestor disponible
    print("ADVERTENCIA: Gestor de prompts no disponible. Se usarán prompts internos.")
# --- Fin Instancia ---

# --- Gestión de Prompts (Usando ScriptPromptManager) ---
# Los prompts ahora se gestionan a través del ScriptPromptManager y se cargan desde script_prompts.json

def obtener_prompt(estilo: str, tipo_prompt: str) -> str:
    """Obtiene la plantilla de prompt usando el ScriptPromptManager."""
    if script_manager:  # Verifica si el gestor se pudo crear
        return script_manager.get_prompt_template(estilo, tipo_prompt)
    else:
        # Fallback si el manager no está disponible (error crítico)
        print(f"ERROR FATAL: ScriptPromptManager no disponible. No se puede obtener prompt '{tipo_prompt}' para estilo '{estilo}'.")
        # Devuelve un string vacío o lanza una excepción según prefieras
        return ""  # O: raise RuntimeError("ScriptPromptManager no disponible")

# --- Funciones de Generación ---

def generar_esquema(titulo: str, contexto: str, estilo_prompt: str = 'default', num_secciones: int = 5) -> list[str] | None:
    """Genera el esquema del guion y devuelve una lista de instrucciones por sección."""
    if not AI_PROVIDER_AVAILABLE: return None
    
    # Obtener la plantilla de prompt para el esquema
    prompt_template = obtener_prompt(estilo_prompt, 'esquema')
    if not prompt_template: return None
    
    # Dividir en system prompt y user prompt
    system_prompt_esquema = f"Genera una estructura de guion detallada con exactamente {num_secciones} secciones para un video de YouTube."
    user_prompt_completo = prompt_template.format(
        titulo=titulo, 
        contexto=contexto,
        num_secciones=num_secciones
    )
    
    # --- LLAMADA CORREGIDA A LA IA ---
    # Usar la instancia ai_providers y su método generate_prompt_with_fallback
    try:
        if 'generar_prompt_simulado' in globals(): # Modo simulación si falló la importación
            respuesta_ai, proveedor = generar_prompt_simulado(system_prompt_esquema, user_prompt_completo)
        else:
            respuesta_ai, proveedor = ai_providers.generate_prompt_with_fallback(
                system_prompt=system_prompt_esquema,
                user_prompt=user_prompt_completo
            )
        print(f"Proveedor usado para esquema: {proveedor}")
    except Exception as e:
        print(f"Error al llamar a la IA: {e}")
        return None
    
    if not respuesta_ai:
        print("ERROR: La IA no generó respuesta para el esquema.")
        return None

    # --- Parsear la respuesta JSON para obtener la lista de instrucciones ---
    print(f"Respuesta AI (Esquema):\n{respuesta_ai[:200]}...\n---")
    
    try:
        # Intentar parsear la respuesta como JSON
        # Primero, limpiar posible texto antes/después del JSON
        json_match = re.search(r'\{.*\}', respuesta_ai, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Extraer la lista de secciones del JSON
            if "secciones" in data and isinstance(data["secciones"], list):
                esquema = data["secciones"]
                if len(esquema) == 0:
                    print("ERROR: La lista de secciones está vacía.")
                    return None
            else:
                # Intento alternativo si no hay clave "secciones"
                # Buscar cualquier lista en el JSON
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"ADVERTENCIA: Usando lista alternativa '{key}' en lugar de 'secciones'.")
                        esquema = value
                        break
                else:
                    print("ERROR: No se encontró ninguna lista en el JSON.")
                    print(f"JSON parseado:\n{data}")
                    return None
        else:
            # Fallback: intentar el método anterior basado en expresiones regulares
            print("ADVERTENCIA: No se encontró JSON válido. Intentando parseo alternativo...")
            lineas = respuesta_ai.strip().split('\n')
            esquema = [linea.split('.', 1)[-1].strip() for linea in lineas if re.match(r'^\s*\d+\.\s+', linea)]
            
            if not esquema:
                print("ERROR: No se pudo parsear el esquema desde la respuesta AI.")
                print(f"Respuesta AI completa:\n{respuesta_ai}")
                return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Falló el parseo JSON: {e}")
        print(f"JSON intentado: {json_match.group(0) if json_match else 'No encontrado'}")
        
        # Fallback: intentar el método anterior basado en expresiones regulares
        print("Intentando parseo alternativo...")
        lineas = respuesta_ai.strip().split('\n')
        esquema = [linea.split('.', 1)[-1].strip() for linea in lineas if re.match(r'^\s*\d+\.\s+', linea)]
        
        if not esquema:
            print("ERROR: No se pudo parsear el esquema desde la respuesta AI.")
            print(f"Respuesta AI completa:\n{respuesta_ai}")
            return None
    except Exception as e:
        print(f"ERROR inesperado parseando esquema: {e}")
        return None

    print(f"Esquema generado con {len(esquema)} secciones.")
    return esquema

def generar_seccion(numero_seccion: int, instruccion_seccion: str, titulo: str, contexto: str, num_palabras: int, estilo_prompt: str = 'default') -> str | None:
    """Genera el texto para una sección específica del guion."""
    if not AI_PROVIDER_AVAILABLE: return None
    
    # Obtener la plantilla de prompt para la sección
    prompt_template = obtener_prompt(estilo_prompt, 'seccion')
    if not prompt_template: return None
    
    # Dividir en system prompt y user prompt
    system_prompt_seccion = f"Escribe la sección {numero_seccion} de un guion para un video de YouTube."
    user_prompt_completo = prompt_template.format(
        numero_seccion=numero_seccion,
        instruccion_seccion=instruccion_seccion,
        titulo=titulo,
        contexto=contexto,
        num_palabras=num_palabras
    )
    
    # --- LLAMADA CORREGIDA A LA IA ---
    try:
        if 'generar_prompt_simulado' in globals(): # Modo simulación si falló la importación
            respuesta_ai, proveedor = generar_prompt_simulado(
                system_prompt_seccion, 
                user_prompt_completo, 
                instruccion_seccion=instruccion_seccion
            )
        else:
            respuesta_ai, proveedor = ai_providers.generate_prompt_with_fallback(
                system_prompt=system_prompt_seccion,
                user_prompt=user_prompt_completo
            )
        print(f"Proveedor usado para sección {numero_seccion}: {proveedor}")
    except Exception as e:
        print(f"Error al llamar a la IA para sección {numero_seccion}: {e}")
        return None
    
    if not respuesta_ai:
        print(f"ERROR: La IA no generó respuesta para la sección {numero_seccion}.")
        return None

    print(f"Texto generado para sección {numero_seccion} ({len(respuesta_ai)} caracteres).")
    return respuesta_ai.strip()

def revisar_guion(guion_borrador: str, titulo: str, estilo_prompt: str = 'default') -> str | None:
    """Revisa y pule el guion completo usando IA y un modelo de contexto largo."""
    if not AI_PROVIDER_AVAILABLE: return None
    
    # Obtener la plantilla de prompt para la revisión
    prompt_template = obtener_prompt(estilo_prompt, 'revision')
    if not prompt_template: return None
    
    # Usaremos un modelo de contexto largo, por lo que no necesitamos truncar el guion
    # Solo registramos la longitud para referencia
    print(f"DEBUG: Iniciando revisar_guion para '{titulo}'. Longitud borrador: {len(guion_borrador)} caracteres.")
    guion_truncado = guion_borrador  # Ya no truncamos
    
    # Dividir en system prompt y user prompt
    system_prompt_revision = "Revisa y mejora este guion para un video de YouTube manteniendo su estructura y contenido principal."
    user_prompt_completo = prompt_template.format(titulo=titulo, guion_borrador=guion_truncado)
    
    # --- LLAMADA CORREGIDA A LA IA ---
    try:
        if 'generar_prompt_simulado' in globals(): # Modo simulación si falló la importación
            respuesta_ai, proveedor = generar_prompt_simulado(system_prompt_revision, user_prompt_completo)
            respuesta_ai = f"--- GUION REVISADO (SIMULADO) ---\n{respuesta_ai}" # Añadir prefijo
        else:
            print(f"Enviando guion de {len(guion_borrador)} caracteres para revisión (usando modelo grande)...")
            # Llamar a la IA pidiendo explícitamente un modelo de contexto largo
            respuesta_ai, proveedor = ai_providers.generate_prompt_with_fallback(
                system_prompt=system_prompt_revision,
                user_prompt=user_prompt_completo,
                use_large_context_model=True  # <-- ¡Importante para guiones largos!
            )
        print(f"Proveedor usado para revisión de guion: {proveedor}")
    except Exception as e:
        print(f"Error al llamar a la IA para revisar guion: {e}")
        return None
    
    if not respuesta_ai:
        print("ERROR: La IA no generó respuesta para la revisión del guion.")
        return None

    print(f"Guion completo revisado por IA ({len(respuesta_ai)} caracteres).")
    return respuesta_ai.strip()

def generar_metadata(guion_final: str, titulo: str, estilo_prompt: str = 'default') -> dict | None:
    """Genera metadata para YouTube."""
    if not AI_PROVIDER_AVAILABLE: return None
    
    # Obtener la plantilla de prompt para la metadata
    prompt_template = obtener_prompt(estilo_prompt, 'metadata')
    if not prompt_template: return None
    
    # Truncar el guion final si es muy largo para el prompt
    guion_corto = guion_final[:8000] # Limitamos a 8000 caracteres
    if len(guion_final) > 8000:
        print(f"ADVERTENCIA: Guion truncado de {len(guion_final)} a 8000 caracteres para generar metadata.")
    
    # Dividir en system prompt y user prompt
    system_prompt_metadata = "Genera metadatos para un video de YouTube en formato JSON estricto."
    user_prompt_completo = prompt_template.format(titulo=titulo, guion_final=guion_corto)
    
    # --- LLAMADA CORREGIDA A LA IA ---
    try:
        if 'generar_prompt_simulado' in globals(): # Modo simulación si falló la importación
            respuesta_ai, proveedor = generar_prompt_simulado(system_prompt_metadata, user_prompt_completo)
        else:
            respuesta_ai, proveedor = ai_providers.generate_prompt_with_fallback(
                system_prompt=system_prompt_metadata,
                user_prompt=user_prompt_completo
            )
        print(f"Proveedor usado para generar metadata: {proveedor}")
    except Exception as e:
        print(f"Error al llamar a la IA para generar metadata: {e}")
        return None
    
    if not respuesta_ai:
        print("ERROR: La IA no generó respuesta para la metadata.")
        return None

    # --- Parsear la respuesta JSON ---
    try:
        # Limpiar posible texto antes/después del JSON
        json_match = re.search(r'\{.*\}', respuesta_ai, re.DOTALL)
        if json_match:
            metadata_dict = json.loads(json_match.group(0))
            print(f"Metadata generada y parseada con {len(metadata_dict)} claves.")
            # Validar que las claves esperadas existan (opcional)
            return metadata_dict
        else:
            print("ERROR: No se encontró un JSON válido en la respuesta de metadata AI.")
            print(f"Respuesta AI (primeros 200 caracteres):\n{respuesta_ai[:200]}...")
            return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Falló el parseo JSON de la metadata: {e}")
        print(f"Respuesta AI (primeros 200 caracteres):\n{respuesta_ai[:200]}...")
        return None
    except Exception as e:
        print(f"ERROR inesperado parseando metadata: {e}")
        return None
      
# Dentro de ai_script_generator.py

async def crear_guion_completo_y_metadata(titulo: str, contexto: str, estilo_prompt: str = 'default', palabras_seccion: int = 500, num_secciones: int = 5):
    """
    Orquesta el proceso completo: genera esquema, genera todas las secciones,
    revisa guion, genera metadata.
    """
    print(f"\n--- Iniciando Creación Completa para '{titulo}' (Estilo: {estilo_prompt}) ---")
    guion_final = None
    metadata = None
    guion_borrador = None # Inicializa por si falla antes

    try:
        # 1. Generar Esquema
        print("\nPaso 1: Generando esquema...")
        # Usamos asyncio.to_thread si generar_esquema puede bloquear (llamada síncrona a API)
        instrucciones_esquema = await asyncio.to_thread(
            generar_esquema,
            titulo, contexto, estilo_prompt, num_secciones
        )

        if not instrucciones_esquema:
            print("ERROR: Fallo al generar esquema. Abortando.")
            return None, None
        print(f"Esquema recibido con {len(instrucciones_esquema)} secciones.")

        # --- ============================================ ---
        # --- BUCLE PARA GENERAR TODAS LAS SECCIONES ---
        # --- ============================================ ---
        print("\nPaso 2: Generando texto para cada sección...")
        secciones_texto = [] # Lista para guardar el texto de cada sección
        num_secciones_total = len(instrucciones_esquema)

        for i, instruccion in enumerate(instrucciones_esquema):
            numero_seccion_actual = i + 1
            print(f" - Generando sección {numero_seccion_actual}/{num_secciones_total}: '{instruccion[:60].strip()}...'")

            try:
                # Llama a generar_seccion para obtener el texto de esta parte
                texto_seccion = await asyncio.to_thread(
                     generar_seccion, # Tu función para generar una sección
                     numero_seccion_actual,
                     instruccion,
                     titulo,
                     contexto,
                     palabras_seccion,
                     estilo_prompt
                )

                # Verifica si hubo error o la respuesta está vacía
                if not texto_seccion:
                    print(f"\u00a1ERROR! Fallo al generar texto para la sección {numero_seccion_actual}.")
                    print("Abortando generación del resto del guion.")
                    return None, None # Aborta todo si una sección falla
                else:
                    # Éxito, añade el texto a la lista
                    print(f"   -> Sección {numero_seccion_actual} generada OK ({len(texto_seccion)} caracteres).")
                    secciones_texto.append(texto_seccion.strip())

            except Exception as e_sec:
                 # Captura errores inesperados durante la generación de esta sección
                 print(f"\u00a1ERROR EXCEPCIÓN GRAVE! al generar sección {numero_seccion_actual}: {e_sec}")
                 import traceback
                 traceback.print_exc()
                 return None, None # Abortar todo

            # Pausa opcional entre llamadas a la API para evitar problemas de límites de velocidad
            await asyncio.sleep(1.5) # Espera 1.5 segundos

        # Une todas las secciones generadas para formar el borrador
        guion_borrador = "\n\n".join(secciones_texto)
        print(f"\nGuion borrador completo generado ({len(guion_borrador)} caracteres).")
        # --- FIN DEL BUCLE ---

        # 3. Revisar Guion
        print("\nPaso 3: Revisando guion completo...")
        try:
            guion_final = await asyncio.to_thread(revisar_guion, guion_borrador, titulo, estilo_prompt)
            if not guion_final:
                print("Fallo al revisar el guion. Usando versión borrador.")
                guion_final = guion_borrador # Usar el borrador si la revisión falla
            else:
                print(f"Guion revisado y mejorado ({len(guion_final)} caracteres).")
        except Exception as e_rev:
            print(f"Error durante la revisión del guion: {e_rev}")
            guion_final = guion_borrador # Usar borrador si hay excepción

        # 4. Generar Metadata
        print("\nPaso 4: Generando metadata...")
        try:
            metadata = await asyncio.to_thread(generar_metadata, guion_final, titulo, estilo_prompt)
            if not metadata:
                print("Fallo al generar metadata.")
                metadata = {} # Devolver dict vacío si falla
            else:
                print(f"Metadata generada con {len(metadata)} claves.")
        except Exception as e_meta:
            print(f"Error durante la generación de metadata: {e_meta}")
            metadata = {} # Dict vacío si hay excepción

        print("\n--- Proceso de Creación AI Completo ---")

    except Exception as e_main:
        print(f"\u00a1ERROR FATAL en el proceso principal de creación AI!: {e_main}")
        import traceback
        traceback.print_exc()
        return None, None # Devuelve None si algo falla en el flujo general

    # Devuelve el guion final y la metadata
    return guion_final, metadata


# Código para pruebas
if __name__ == "__main__":
    print("--- Probando ai_script_generator.py ---")
    test_titulo = "La Verdad Oculta de Santa Eduviges"
    test_contexto = "Basado en recientes hallazgos arqueológicos y textos apócrifos..."
    test_estilo = "default" # O el estilo que quieras probar
    test_palabras = 150 # Pocas palabras por sección para pruebas rápidas
    test_num_secciones = 3 # Número de secciones para el guion (reducido para pruebas rápidas)

    # Prueba básica del esquema
    print(f"\nIntentando generar esquema para: '{test_titulo}' (Pidiendo {test_num_secciones} secciones)")
    esquema_generado = generar_esquema(test_titulo, test_contexto, test_estilo, test_num_secciones)

    if esquema_generado:
        print("\nEsquema Generado y Parseado:")
        for i, instruccion in enumerate(esquema_generado):
            print(f"{i+1}. {instruccion}")
    else:
        print("\nNo se pudo generar o parsear el esquema.")
        
    # Ejemplo de prueba de una sola sección
    if esquema_generado and len(esquema_generado) > 0:
        print("\nProbando generación de una sección...")
        seccion_texto = generar_seccion(
            1, esquema_generado[0], test_titulo, test_contexto, 200, test_estilo
        )
        if seccion_texto:
            print(f"\nSección generada (primeros 200 caracteres):\n{seccion_texto[:200]}...")
        else:
            print("\nNo se pudo generar la sección de prueba.")
    
    # Prueba completa (descomentar para probar la generación completa)
    print(f"\n\n=== PRUEBA DE GENERACIÓN COMPLETA ===\n")
    print(f"Intentando generar guion completo para: '{test_titulo}'")
    
    async def run_test_completo():
        # Llama a la función orquestadora principal
        script, meta = await crear_guion_completo_y_metadata(
            test_titulo, 
            test_contexto, 
            test_estilo, 
            test_palabras,
            test_num_secciones
        )
        if script:
            print("\n--- GUION FINAL (Extracto) ---")
            # Imprime solo una parte para no llenar la consola
            print(script[:1000] + "\n...")
            print(f"\nLongitud total del guion: {len(script)} caracteres")
            print("\n--- METADATA ---")
            print(meta)
        else:
            print("\n--- FALLO EN LA GENERACIÓN DEL GUION ---")
    
    # Ejecuta la función de prueba asíncrona
    import asyncio
    asyncio.run(run_test_completo())