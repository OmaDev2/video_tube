#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de depuración para verificar el funcionamiento del gestor de prompts
"""

import os
import json
from prompt_manager import PromptManager
from prompt_generator import generar_prompts_con_gemini

def main():
    # Mostrar los estilos disponibles
    prompt_manager = PromptManager()
    #print("\n=== ESTILOS DE PROMPTS DISPONIBLES ===")
    #for prompt_id, prompt_info in prompt_manager.get_all_prompts().items():
    #print(f"ID: '{prompt_id}', Nombre: '{prompt_info['name']}'")
    
    # Verificar el mapeo de nombres a IDs
    prompt_styles = prompt_manager.get_prompt_names()
    prompt_style_values = [name for _, name in prompt_styles]
    prompt_style_ids = [id for id, _ in prompt_styles]
    prompt_style_map = dict(zip(prompt_style_values, prompt_style_ids))
    
    #print("\n=== MAPEO DE NOMBRES A IDS ===")
    #for name, id in prompt_style_map.items():
    #    print(f"Nombre: '{name}' -> ID: '{id}'")
    
    # Probar la generación de prompts con cada estilo
    #print("\n=== PRUEBA DE GENERACIÓN DE PROMPTS ===")
    
    # Texto de prueba
    titulo = "Meditación de Yoga"
    escena = "La meditación es una práctica ancestral que entrena la mente para enfocar la atención."
    
    for estilo_id in prompt_manager.get_prompt_ids():
        #print(f"\n--- Estilo: {estilo_id} ---")
        
        # Obtener system prompt y user prompt
        system_prompt = prompt_manager.get_system_prompt(estilo_id)
        user_prompt = prompt_manager.get_user_prompt(estilo_id, titulo, escena)
        
        #print(f"System Prompt: {system_prompt[:50]}...")
        #print(f"User Prompt: {user_prompt[:50]}...")
        
        # Generar prompt usando la plantilla
        prompt = prompt_manager.generate_prompt(estilo_id, titulo, escena)
        #print(f"Prompt generado: {prompt}")
    
    # Probar específicamente el estilo psicodélico
    #print("\n=== PRUEBA ESPECÍFICA DEL ESTILO PSICODÉLICO ===")
    estilo_id = "psicodelicas"
    
    # Verificar si existe
    if estilo_id in prompt_manager.get_prompt_ids():
        #print(f"El estilo '{estilo_id}' existe en el gestor de prompts.")
        
        # Mostrar información completa
        prompt_info = prompt_manager.get_prompt(estilo_id)
        #print(f"Información completa: {json.dumps(prompt_info, indent=2, ensure_ascii=False)}")
        
        # Generar un prompt de ejemplo
        prompt = prompt_manager.generate_prompt(estilo_id, titulo, escena)
        #print(f"Prompt generado: {prompt}")
    else:
        print(f"El estilo '{estilo_id}' NO existe en el gestor de prompts.")

if __name__ == "__main__":
    main()
