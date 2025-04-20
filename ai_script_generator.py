# -*- coding: utf-8 -*-
# Archivo: ai_script_generator.py (Refactorizado para usar PromptManager unificado)

import os
import re
import json
import asyncio
from dotenv import load_dotenv
import logging # Asegurarse de que logging esté importado

# --- NUEVO: Importar el gestor de prompts unificado ---
try:
    # Asume que prompt_manager.py está en el mismo directorio o accesible
    from prompt_manager import PromptManager
    PROMPT_MANAGER_AVAILABLE = True
    # Crear una instancia global del manager unificado
    prompt_manager = PromptManager()
    print("INFO: Gestor de prompts unificado (PromptManager) inicializado.")
except ImportError:
    print("ERROR FATAL: No se pudo importar el PromptManager unificado.")
    PROMPT_MANAGER_AVAILABLE = False
    prompt_manager = None # Establecer a None si falla la importación
# --- FIN NUEVO ---

# --- Mantener importación de proveedores AI ---
AI_PROVIDER_AVAILABLE = False
try:
    from ai_providers import ai_providers, GEMINI_AVAILABLE, OPENAI_AVAILABLE
    if GEMINI_AVAILABLE or OPENAI_AVAILABLE:
        AI_PROVIDER_AVAILABLE = True
        print("INFO: Instancia ai_providers importada para generación de guiones.")
    else:
        print("ADVERTENCIA: ai_providers importado pero ningún cliente IA configurado.")
except ImportError:
    print("ADVERTENCIA: No se pudo importar 'ai_providers'. Generación AI no funcionará.")
    AI_PROVIDER_AVAILABLE = False
    # ... (código de simulación si es necesario) ...
except Exception as e:
    print(f"ERROR inesperado importando/configurando ai_providers: {e}")
    AI_PROVIDER_AVAILABLE = False
# --- FIN Mantener importación ---


# --- ELIMINADO: Ya no necesitamos la instancia separada de ScriptPromptManager ---
# if SCRIPT_PROMPT_MANAGER_AVAILABLE:
#     script_manager = ScriptPromptManager()
#     print("INFO: Gestor de prompts de guion inicializado.")
# else:
#     script_manager = None
#     print("ADVERTENCIA: Gestor de prompts no disponible. Se usarán prompts internos.")


# --- ELIMINADO: La función obtener_prompt ya no es necesaria ---
# def obtener_prompt(estilo: str, tipo_prompt: str) -> str:
#    # ... código anterior ...


# --- Funciones de Generación (Modificadas) ---

def generar_esquema(titulo: str, contexto: str, estilo_prompt: str = 'default', num_secciones: int = 5) -> list[str] | None:
    """Genera el esquema del guion y devuelve una lista de instrucciones por sección."""
    if not AI_PROVIDER_AVAILABLE or not prompt_manager: return None # Verificar manager

    # *** CAMBIO: Obtener plantilla usando PromptManager unificado ***
    prompt_template = prompt_manager.get_script_prompt_template(estilo_prompt, 'esquema')
    if not prompt_template:
        print(f"ERROR: No se encontró plantilla de 'esquema' para estilo '{estilo_prompt}' en PromptManager.")
        return None

    # Dividir en system prompt y user prompt (adaptar si tu estructura lo necesita)
    # ASUNCIÓN: La plantilla obtenida es el 'user_prompt' completo. Necesitamos definir el 'system_prompt' aquí.
    system_prompt_esquema = f"Genera una estructura de guion detallada con exactamente {num_secciones} secciones para un video de YouTube." # O podrías añadir un system_prompt específico para script_esquema en el JSON y cargarlo
    user_prompt_completo = prompt_template.format(
        titulo=titulo,
        contexto=contexto,
        num_secciones=num_secciones
        # Asegúrate de que los placeholders coincidan con tu JSON
    )

    # --- LLAMADA A LA IA (Sin cambios aquí, usa ai_providers) ---
    try:
        # ... (modo simulación si aplica) ...
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

    # --- Parsear la respuesta JSON (Sin cambios aquí) ---
    # ... (código de parseo JSON que ya tenías) ...
    print(f"Respuesta AI (Esquema):\n{respuesta_ai[:200]}...\n---")
    try:
        json_match = re.search(r'\{.*\}', respuesta_ai, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            if "secciones" in data and isinstance(data["secciones"], list):
                esquema = data["secciones"]
                if not esquema: print("ERROR: Lista de secciones vacía."); return None
            else: # Fallback si no hay clave "secciones"
                esquema = None
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"ADVERTENCIA: Usando lista '{key}' en lugar de 'secciones'.")
                        esquema = value; break
                if esquema is None: print("ERROR: No se encontró lista en JSON."); return None
        else: # Fallback si no hay JSON
             print("ADVERTENCIA: No se encontró JSON. Intentando parseo por líneas numeradas...")
             lineas = respuesta_ai.strip().split('\n')
             esquema = [linea.split('.', 1)[-1].strip() for linea in lineas if re.match(r'^\s*\d+\.\s+', linea)]
             if not esquema: print("ERROR: No se pudo parsear esquema."); return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Falló parseo JSON: {e}. Intentando parseo por líneas...");
        lineas = respuesta_ai.strip().split('\n')
        esquema = [linea.split('.', 1)[-1].strip() for linea in lineas if re.match(r'^\s*\d+\.\s+', linea)]
        if not esquema: print("ERROR: No se pudo parsear esquema."); return None
    except Exception as e:
        print(f"ERROR inesperado parseando esquema: {e}"); return None

    print(f"Esquema generado con {len(esquema)} secciones.")
    return esquema


def generar_seccion(numero_seccion: int, instruccion_seccion: str, titulo: str, contexto: str, num_palabras: int, estilo_prompt: str = 'default') -> str | None:
    """Genera el texto para una sección específica del guion."""
    if not AI_PROVIDER_AVAILABLE or not prompt_manager: return None

    # *** CAMBIO: Obtener plantilla usando PromptManager unificado ***
    prompt_template = prompt_manager.get_script_prompt_template(estilo_prompt, 'seccion')
    if not prompt_template:
        print(f"ERROR: No se encontró plantilla de 'seccion' para estilo '{estilo_prompt}' en PromptManager.")
        return None

    # Definir system prompt
    system_prompt_seccion = f"Escribe la sección {numero_seccion} de un guion para un video de YouTube."
    user_prompt_completo = prompt_template.format(
        numero_seccion=numero_seccion,
        instruccion_seccion=instruccion_seccion,
        titulo=titulo,
        contexto=contexto,
        num_palabras=num_palabras
        # Asegúrate de que los placeholders coincidan con tu JSON
    )

    # --- LLAMADA A LA IA (Sin cambios aquí) ---
    try:
        # ... (modo simulación si aplica) ...
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
    """Revisa y pule el guion completo usando IA."""
    if not AI_PROVIDER_AVAILABLE or not prompt_manager: return None

    # *** CAMBIO: Obtener plantilla usando PromptManager unificado ***
    prompt_template = prompt_manager.get_script_prompt_template(estilo_prompt, 'revision')
    if not prompt_template:
        print(f"ERROR: No se encontró plantilla de 'revision' para estilo '{estilo_prompt}' en PromptManager.")
        return None

    print(f"DEBUG: Iniciando revisar_guion para '{titulo}'. Longitud borrador: {len(guion_borrador)} caracteres.")

    # Definir system prompt
    system_prompt_revision = "Revisa y mejora este guion para un video de YouTube manteniendo su estructura y contenido principal."
    user_prompt_completo = prompt_template.format(
        titulo=titulo,
        guion_borrador=guion_borrador # El placeholder debe ser {guion_borrador} en el JSON
        # Asegúrate de que los placeholders coincidan con tu JSON
    )

    # --- LLAMADA A LA IA (Sin cambios aquí, pero mantenemos use_large_context_model) ---
    try:
        # ... (modo simulación si aplica) ...
        print(f"Enviando guion de {len(guion_borrador)} caracteres para revisión (usando modelo grande)...")
        respuesta_ai, proveedor = ai_providers.generate_prompt_with_fallback(
            system_prompt=system_prompt_revision,
            user_prompt=user_prompt_completo,
            use_large_context_model=True
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
    if not AI_PROVIDER_AVAILABLE or not prompt_manager: return None

    # *** CAMBIO: Obtener plantilla usando PromptManager unificado ***
    prompt_template = prompt_manager.get_script_prompt_template(estilo_prompt, 'metadata')
    if not prompt_template:
        print(f"ERROR: No se encontró plantilla de 'metadata' para estilo '{estilo_prompt}' en PromptManager.")
        return None

    # Truncar el guion final si es muy largo
    guion_corto = guion_final[:8000]
    if len(guion_final) > 8000:
        print(f"ADVERTENCIA: Guion truncado de {len(guion_final)} a 8000 caracteres para generar metadata.")

    # Definir system prompt
    system_prompt_metadata = "Genera metadatos para un video de YouTube en formato JSON estricto."
    user_prompt_completo = prompt_template.format(
        titulo=titulo,
        guion_final=guion_corto # El placeholder debe ser {guion_final} en el JSON
        # Asegúrate de que los placeholders coincidan con tu JSON
    )

    # --- LLAMADA A LA IA (Sin cambios aquí) ---
    try:
        # ... (modo simulación si aplica) ...
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

    # --- Parsear la respuesta JSON (Sin cambios aquí) ---
    try:
        json_match = re.search(r'\{.*\}', respuesta_ai, re.DOTALL)
        if json_match:
            metadata_dict = json.loads(json_match.group(0))
            print(f"Metadata generada y parseada con {len(metadata_dict)} claves.")
            return metadata_dict
        else:
            print("ERROR: No se encontró un JSON válido en la respuesta de metadata AI.")
            return None
    except Exception as e:
        print(f"ERROR inesperado parseando metadata: {e}")
        return None


# --- Función Orquestadora (Sin cambios necesarios en su lógica interna) ---
async def crear_guion_completo_y_metadata(titulo: str, contexto: str, estilo_prompt: str = 'default', palabras_seccion: int = 500, num_secciones: int = 5):
    """
    Orquesta el proceso completo: genera esquema, genera todas las secciones,
    revisa guion, genera metadata.
    """
    # ... (El código interno de esta función no necesita cambios,
    #      ya que llama a las funciones individuales que hemos modificado arriba) ...

    print(f"\n--- Iniciando Creación Completa para '{titulo}' (Estilo: {estilo_prompt}) ---")
    guion_final = None
    metadata = None
    guion_borrador = None

    try:
        print("\nPaso 1: Generando esquema...")
        instrucciones_esquema = await asyncio.to_thread(
            generar_esquema, # Llama a la versión modificada
            titulo, contexto, estilo_prompt, num_secciones
        )
        if not instrucciones_esquema: raise ValueError("Fallo al generar esquema.")
        print(f"Esquema recibido con {len(instrucciones_esquema)} secciones.")

        print("\nPaso 2: Generando texto para cada sección...")
        secciones_texto = []
        for i, instruccion in enumerate(instrucciones_esquema):
            numero_seccion_actual = i + 1
            print(f" - Generando sección {numero_seccion_actual}/{len(instrucciones_esquema)}: '{instruccion[:60].strip()}...'")
            texto_seccion = await asyncio.to_thread(
                 generar_seccion, # Llama a la versión modificada
                 numero_seccion_actual, instruccion, titulo, contexto, palabras_seccion, estilo_prompt
            )
            if not texto_seccion: raise ValueError(f"Fallo al generar sección {numero_seccion_actual}.")
            print(f"   -> Sección {numero_seccion_actual} generada OK ({len(texto_seccion)} caracteres).")
            secciones_texto.append(texto_seccion.strip())
            await asyncio.sleep(1.5) # Pausa opcional

        guion_borrador = "\n\n".join(secciones_texto)
        print(f"\nGuion borrador completo generado ({len(guion_borrador)} caracteres).")

        print("\nPaso 3: Revisando guion completo...")
        guion_final = await asyncio.to_thread(
             revisar_guion, # Llama a la versión modificada
             guion_borrador, titulo, estilo_prompt
        )
        if not guion_final: print("Fallo revisión, usando borrador."); guion_final = guion_borrador
        else: print(f"Guion revisado y mejorado ({len(guion_final)} caracteres).")

        print("\nPaso 4: Generando metadata...")
        metadata = await asyncio.to_thread(
             generar_metadata, # Llama a la versión modificada
             guion_final, titulo, estilo_prompt
        )
        if not metadata: print("Fallo al generar metadata."); metadata = {}
        else: print(f"Metadata generada con {len(metadata)} claves.")

        print("\n--- Proceso de Creación AI Completo ---")

    except Exception as e_main:
        print(f"\u00a1ERROR FATAL en el proceso principal de creación AI!: {e_main}")
        import traceback; traceback.print_exc()
        return None, None # Devuelve None si algo falla

    return guion_final, metadata


# --- Función Síncrona Wrapper (Sin cambios necesarios) ---
def generar_guion(titulo: str, contexto: str, estilo: str = 'default', num_secciones: int = 5, palabras_por_seccion: int = 150):
    """Genera un guion completo para un video (wrapper síncrono)."""
    # ... (El código interno de esta función no necesita cambios) ...
    print(f"Generando guion para: '{titulo}' con estilo '{estilo}'")
    print(f"Parámetros: {num_secciones} secciones, {palabras_por_seccion} palabras por sección")
    try:
        try: loop = asyncio.get_event_loop()
        except RuntimeError: loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        guion_completo, _ = loop.run_until_complete(crear_guion_completo_y_metadata(
            titulo=titulo, contexto=contexto, estilo_prompt=estilo,
            palabras_seccion=palabras_por_seccion, num_secciones=num_secciones
        ))
        if not guion_completo: raise Exception("No se pudo generar el guion.")
        return guion_completo
    except Exception as e:
        print(f"Error al generar guion: {e}"); raise


# --- Código de prueba (Actualizado para usar el nuevo manager si se ejecuta directamente) ---
if __name__ == "__main__":
    if not prompt_manager:
         print("ERROR: PromptManager no inicializado. Abortando pruebas.")
    else:
        print("--- Probando ai_script_generator.py Refactorizado ---")
        test_titulo = "La Verdad Oculta de Santa Eduviges"
        test_contexto = "Basado en recientes hallazgos..."
        test_estilo = "educativo"
        test_palabras = 75
        test_num_secciones = 3

        print(f"\nIntentando generar esquema para: '{test_titulo}' (Estilo: {test_estilo}, Secciones: {test_num_secciones})")
        # Usar la función directamente ya que el manager ahora está instanciado globalmente
        esquema_generado = generar_esquema(test_titulo, test_contexto, test_estilo, test_num_secciones)
        # ... (resto del código de prueba como lo tenías, debería funcionar) ...
        if esquema_generado:
            print("\nEsquema Generado y Parseado:")
            for i, instruccion in enumerate(esquema_generado): print(f"{i+1}. {instruccion}")

            print("\nProbando generación de una sección...")
            seccion_texto = generar_seccion(
                1, esquema_generado[0], test_titulo, test_contexto, 200, test_estilo
            )
            if seccion_texto: print(f"\nSección generada (extracto):\n{seccion_texto[:200]}...")
            else: print("\nFallo al generar sección de prueba.")
        else:
            print("\nFallo al generar esquema de prueba.")

        print(f"\n\n=== PRUEBA DE GENERACIÓN COMPLETA ===\n")
        async def run_test_completo():
            script, meta = await crear_guion_completo_y_metadata(
                test_titulo, test_contexto, test_estilo, test_palabras, test_num_secciones
            )
            if script:
                print("\n--- GUION FINAL (Extracto) ---")
                print(script[:500] + "\n...")
                print(f"\nLongitud total: {len(script)} caracteres")
                print("\n--- METADATA ---"); print(meta)
            else:
                print("\n--- FALLO EN LA GENERACIÓN DEL GUION COMPLETO ---")
        asyncio.run(run_test_completo())