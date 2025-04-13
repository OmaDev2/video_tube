# -*- coding: utf-8 -*-
# Archivo: prompt_manager.py

"""
Gestor de plantillas de prompts personalizados.
Permite crear, guardar, editar y eliminar plantillas de prompts para la generación de imágenes.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

# Ruta al archivo de prompts personalizados
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_PROMPTS_FILE = os.path.join(DATA_DIR, "custom_prompts.json")

# Asegurarse de que el directorio data existe
os.makedirs(DATA_DIR, exist_ok=True)

# Estructura de una plantilla de prompt
DEFAULT_PROMPT_TEMPLATE = {
    "name": "Nuevo Estilo",
    "description": "Descripción del estilo",
    "system_prompt": """Eres un asistente experto en visualización creativa para vídeos. Generas prompts concisos y descriptivos para modelos de generación de imágenes como Stable Diffusion.""",
    "user_prompt": """Genera un prompt en inglés para una imagen de estilo cinematográfico basado en el siguiente texto: '{titulo}: {escena}'. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El aspect ratio es 16:9.""",
    "negative_prompt": "text, watermark, low quality, blurry"
}

class PromptManager:
    """Clase para gestionar plantillas de prompts personalizados"""
    
    def __init__(self, prompts_file: str = DEFAULT_PROMPTS_FILE):
        """Inicializa el gestor de prompts
        
        Args:
            prompts_file: Ruta al archivo de prompts personalizados
        """
        self.prompts_file = prompts_file
        self.prompts = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Carga las plantillas de prompts desde el archivo"""
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(self.prompts_file), exist_ok=True)
        
        # Cargar prompts si el archivo existe
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except Exception as e:
                print(f"Error al cargar prompts: {e}")
                self.prompts = {}
        
        # Si no hay prompts, crear algunos por defecto
        if not self.prompts:
            self._create_default_prompts()
    
    def _save_prompts(self) -> None:
        """Guarda las plantillas de prompts en el archivo"""
        try:
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(self.prompts_file), exist_ok=True)
            
            # Guardar los prompts en el archivo
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
            
            print(f"Prompts guardados correctamente en: {self.prompts_file}")
            print(f"Número de prompts guardados: {len(self.prompts)}")
        except Exception as e:
            print(f"Error al guardar prompts: {e}")
            print(f"Ruta del archivo: {self.prompts_file}")
            print(f"Directorio: {os.path.dirname(self.prompts_file)}")
    
    def _create_default_prompts(self) -> None:
        """Crea algunas plantillas de prompts por defecto"""
        self.prompts = {
            "default": {
                "name": "Cinematográfico",
                "description": "Estilo visual cinematográfico general, con buena iluminación y composición",
                "system_prompt": """Eres un asistente experto en visualización creativa para vídeos. Generas prompts concisos y descriptivos para modelos de generación de imágenes como Stable Diffusion.""",
                "user_prompt": """Genera un prompt en inglés para una imagen de estilo cinematográfico basado en el siguiente texto: '{titulo}: {escena}'. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El aspect ratio es 16:9.""",
                "prompt_template": """Cinematic scene: {escena}. Professional lighting, high detail, dramatic composition. 16:9 aspect ratio.""",
                "negative_prompt": "text, watermark, low quality, blurry"
            },
            "terror": {
                "name": "Terror",
                "description": "Estilo visual de película de terror, oscuro y atmosférico",
                "system_prompt": """Eres un asistente experto en visualización creativa para vídeos de terror. Generas prompts concisos y descriptivos para modelos de generación de imágenes como Stable Diffusion.""",
                "user_prompt": """Genera un prompt en inglés para una imagen de estilo terror basado en el siguiente texto: '{titulo}: {escena}'. El prompt debe capturar la atmósfera oscura, inquietante y aterradora del texto. Usa elementos visuales como sombras, niebla, iluminación tenue y composición inquietante. El aspect ratio es 16:9.""",
                "prompt_template": """Horror movie scene: {escena}. Dark atmosphere, eerie lighting, unsettling composition, cinematic quality. 16:9 aspect ratio.""",
                "negative_prompt": "bright colors, daylight, cheerful, cartoon, text, watermark, low quality"
            },
            "animacion": {
                "name": "Animación",
                "description": "Estilo visual de animación 3D tipo Pixar",
                "system_prompt": """Eres un asistente experto en visualización creativa para películas de animación. Generas prompts concisos y descriptivos para modelos de generación de imágenes como Stable Diffusion.""",
                "user_prompt": """Genera un prompt en inglés para una imagen de estilo animación 3D tipo Pixar basado en el siguiente texto: '{titulo}: {escena}'. El prompt debe capturar colores vibrantes, personajes expresivos, texturas detalladas e iluminación suave. El aspect ratio es 16:9.""",
                "prompt_template": """3D animated scene in Pixar style: {escena}. Vibrant colors, expressive characters, detailed textures, soft lighting. 16:9 aspect ratio.""",
                "negative_prompt": "realistic, photographic, live action, dark, horror, text, watermark, low quality"
            }
        }
        self._save_prompts()
    
    def get_all_prompts(self) -> Dict:
        """Obtiene todas las plantillas de prompts
        
        Returns:
            Dict: Diccionario con todas las plantillas de prompts
        """
        return self.prompts
    
    def get_prompt_ids(self) -> List[str]:
        """Obtiene los IDs de todas las plantillas de prompts
        
        Returns:
            List[str]: Lista con los IDs de las plantillas
        """
        return list(self.prompts.keys())
    
    def get_prompt_names(self) -> List[tuple]:
        """Obtiene los nombres de todas las plantillas de prompts
        
        Returns:
            List[tuple]: Lista de tuplas (id, nombre) de las plantillas
        """
        return [(prompt_id, info["name"]) for prompt_id, info in self.prompts.items()]
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Obtiene una plantilla de prompt por su ID
        
        Args:
            prompt_id: ID de la plantilla
            
        Returns:
            Dict: Información de la plantilla o None si no existe
        """
        return self.prompts.get(prompt_id)
    
    def add_prompt(self, prompt_id: str, name: str, description: str, 
                   system_prompt: str, user_prompt: str, negative_prompt: str = "") -> bool:
        """Añade una nueva plantilla de prompt
        
        Args:
            prompt_id: ID único para la plantilla
            name: Nombre de la plantilla
            description: Descripción de la plantilla
            system_prompt: Instrucciones para Gemini sobre cómo generar prompts
            user_prompt: Instrucciones específicas para generar el prompt de cada escena
            negative_prompt: Prompt negativo (opcional)
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        if prompt_id in self.prompts:
            return False  # Ya existe una plantilla con ese ID
        
        self.prompts[prompt_id] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "negative_prompt": negative_prompt
        }
        
        self._save_prompts()
        return True
    
    def update_prompt(self, prompt_id: str, name: str, description: str, 
                      system_prompt: str, user_prompt: str, negative_prompt: str = "") -> bool:
        """Actualiza una plantilla de prompt existente
        
        Args:
            prompt_id: ID de la plantilla a actualizar
            name: Nuevo nombre
            description: Nueva descripción
            system_prompt: Instrucciones para Gemini sobre cómo generar prompts
            user_prompt: Instrucciones específicas para generar el prompt de cada escena
            negative_prompt: Nuevo prompt negativo
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        if prompt_id not in self.prompts:
            return False  # No existe la plantilla
        
        self.prompts[prompt_id] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "negative_prompt": negative_prompt
        }
        
        self._save_prompts()
        return True
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Elimina una plantilla de prompt
        
        Args:
            prompt_id: ID de la plantilla a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        if prompt_id not in self.prompts:
            return False  # No existe la plantilla
        
        # No permitir eliminar la plantilla por defecto
        if prompt_id == "default":
            return False
        
        del self.prompts[prompt_id]
        self._save_prompts()
        return True
    
    def generate_prompt(self, prompt_id: str, titulo: str, escena: str) -> str:
        """Genera un prompt basado en una plantilla, título y escena
        
        Args:
            prompt_id: ID de la plantilla
            titulo: Título del video
            escena: Texto de la escena
            
        Returns:
            str: Prompt generado
        """
        # Si no existe la plantilla, usar la plantilla por defecto
        if prompt_id not in self.prompts:
            prompt_id = "default"
        
        template = self.prompts[prompt_id]["prompt_template"]
        
        # Generar el prompt usando la plantilla con título y escena como placeholders separados
        try:
            # Intentar usar la plantilla con ambos placeholders
            prompt = template.format(titulo=titulo, escena=escena)
        except KeyError:
            # Si falta alguno de los placeholders, usar el formato antiguo por compatibilidad
            context = f"{titulo}: {escena}" if titulo else escena
            prompt = template.format(escena=context)
        
        return prompt
        
    def get_system_prompt(self, prompt_id: str) -> str:
        """Obtiene el system prompt para una plantilla específica
        
        Args:
            prompt_id: ID de la plantilla
            
        Returns:
            str: System prompt
        """
        # Si no existe la plantilla, usar la plantilla por defecto
        if prompt_id not in self.prompts:
            prompt_id = "default"
        
        return self.prompts[prompt_id].get("system_prompt", "")
        
    def get_user_prompt(self, prompt_id: str, titulo: str, escena: str) -> str:
        """Obtiene el user prompt para una plantilla específica
        
        Args:
            prompt_id: ID de la plantilla
            titulo: Título del video
            escena: Texto de la escena
            
        Returns:
            str: User prompt
        """
        # Si no existe la plantilla, usar la plantilla por defecto
        if prompt_id not in self.prompts:
            prompt_id = "default"
        
        user_prompt_template = self.prompts[prompt_id].get("user_prompt", "")
        
        # Generar el user prompt usando la plantilla con título y escena como placeholders
        try:
            # Intentar usar la plantilla con ambos placeholders
            user_prompt = user_prompt_template.format(titulo=titulo, escena=escena)
        except KeyError:
            # Si falta alguno de los placeholders, usar el formato antiguo por compatibilidad
            context = f"{titulo}: {escena}" if titulo else escena
            user_prompt = user_prompt_template.format(escena=context)
        
        return user_prompt
    
    def get_negative_prompt(self, prompt_id: str) -> str:
        """Obtiene el prompt negativo para una plantilla específica
        
        Args:
            prompt_id: ID de la plantilla
            
        Returns:
            str: Prompt negativo
        """
        # Si no existe la plantilla, usar la plantilla por defecto
        if prompt_id not in self.prompts:
            prompt_id = "default"
        
        return self.prompts[prompt_id].get("negative_prompt", "")
