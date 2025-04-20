# -*- coding: utf-8 -*-
# Archivo: prompt_manager.py (Refactorizado)

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Ruta al archivo unificado de plantillas
DATA_DIR = Path(__file__).parent / "data" # Directorio 'data' relativo a este archivo
DEFAULT_PROMPTS_FILE = DATA_DIR / "prompt_templates.json" # Nuevo nombre de archivo

# Asegurarse de que el directorio data existe
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Estructura por defecto para un NUEVO estilo
DEFAULT_STYLE_TEMPLATE = {
    "name": "Nuevo Estilo",
    "description": "Descripción del estilo",
    "image_prompt": {
        "system": "Default system prompt for images.",
        "user": "Default user prompt for images. Scene: {escena}",
        "negative": "Default negative prompt for images."
    },
    "script_prompt": {
        "esquema": "Default schema prompt. Title: {titulo}",
        "seccion": "Default section prompt. Section: {numero_seccion}",
        "revision": "Default revision prompt. Draft: {guion_borrador}",
        "metadata": "Default metadata prompt. Final script: {guion_final}"
    }
}

class PromptManager:
    """Clase para gestionar plantillas de prompts unificadas (imagen y guion)."""

    def __init__(self, prompts_file: str = str(DEFAULT_PROMPTS_FILE)):
        self.prompts_file = Path(prompts_file)
        self.prompts = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Carga las plantillas desde el archivo JSON unificado."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
                print(f"INFO: Plantillas cargadas desde {self.prompts_file}")
            except Exception as e:
                print(f"ERROR: Error al cargar plantillas desde {self.prompts_file}: {e}")
                self.prompts = {}
        else:
            print(f"ADVERTENCIA: No se encontró el archivo {self.prompts_file}. Creando defaults.")
            self.prompts = {}

        # Crear estructura por defecto si está vacío o falta el estilo 'default'
        if not self.prompts or "default" not in self.prompts:
            self._create_default_style() # Solo crea 'default' si falta

    def _save_prompts(self) -> None:
        """Guarda las plantillas actuales en el archivo JSON unificado."""
        try:
            self.prompts_file.parent.mkdir(parents=True, exist_ok=True) # Asegura que el directorio exista
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
            print(f"INFO: Plantillas guardadas en {self.prompts_file}")
        except Exception as e:
            print(f"ERROR: Error al guardar plantillas en {self.prompts_file}: {e}")

    def _create_default_style(self) -> None:
        """Crea solo el estilo 'default' si no existe."""
        if "default" not in self.prompts:
             print("INFO: Creando estilo 'default' con plantillas base...")
             # Usar una copia profunda para evitar modificar la plantilla original
             import copy
             default_data = copy.deepcopy(DEFAULT_STYLE_TEMPLATE)
             # Rellenar con los prompts de ejemplo que tenías
             default_data["name"] = "Predeterminado (Vidas Santas - Polémico/Enganche)"
             default_data["description"] = "Estilo principal Vidas Santas con enfoque en polémica/enganche."
             default_data["image_prompt"]["system"] = "Eres un asistente experto en visualización creativa para vídeos. Generas prompts concisos y descriptivos para modelos de generación de imágenes como Stable Diffusion."
             default_data["image_prompt"]["user"] = "Genera un prompt en inglés para una imagen de estilo cinematográfico basado en el siguiente texto: '{titulo}: {escena}'. El prompt debe capturar la esencia visual, la acción o la emoción del texto. No incluyas nombres propios específicos a menos que sea esencial. Evita pedir que se muestre texto en la imagen. El aspect ratio es 16:9."
             default_data["image_prompt"]["negative"] = "text, watermark, low quality, blurry, words, letters, fonts, signature"
             default_data["script_prompt"]["esquema"] = "Eres un asistente experto en estructurar guiones... {titulo} ... {contexto} ... {num_secciones} ..." # Truncado por brevedad
             default_data["script_prompt"]["seccion"] = "Desarrolla la sección {numero_seccion} ({instruccion_seccion})... {titulo} ... {num_palabras} ..." # Truncado
             default_data["script_prompt"]["revision"] = "Revisa y humaniza... {titulo} ... {guion_borrador}" # Truncado
             default_data["script_prompt"]["metadata"] = "Basado en el siguiente guion... {titulo} ... {guion_final}" # Truncado
             self.prompts["default"] = default_data
             self._save_prompts()


    def get_all_prompts(self) -> Dict:
        """Devuelve todas las plantillas."""
        return self.prompts

    def get_prompt_ids(self) -> List[str]:
        """Devuelve los IDs de todos los estilos."""
        return list(self.prompts.keys())

    def get_prompt_names(self) -> List[Tuple[str, str]]:
        """Devuelve una lista de tuplas (id, nombre) para todos los estilos."""
        return [(style_id, info.get("name", style_id)) for style_id, info in self.prompts.items()]

    def get_style(self, style_id: str) -> Optional[Dict]:
        """Devuelve el diccionario completo para un estilo por su ID."""
        return self.prompts.get(style_id)

    def get_image_prompt_parts(self, style_id: str) -> Dict[str, str]:
        """Obtiene las partes del prompt de imagen (system, user, negative) para un estilo."""
        style_data = self.get_style(style_id)
        if style_data and "image_prompt" in style_data:
            return style_data["image_prompt"]
        # Fallback al default si no existe el estilo o la parte de imagen
        print(f"ADVERTENCIA: No se encontró 'image_prompt' para el estilo '{style_id}'. Usando 'default'.")
        return self.prompts.get("default", {}).get("image_prompt", {})

    def get_script_prompt_template(self, style_id: str, script_prompt_type: str) -> str:
        """Obtiene la plantilla para un tipo específico de prompt de guion (esquema, seccion, etc.)."""
        style_data = self.get_style(style_id)
        template = ""
        if style_data and "script_prompt" in style_data:
            template = style_data["script_prompt"].get(script_prompt_type, "")

        if template:
            return template
        else:
            # Fallback al default si no existe el estilo, la parte de script o el tipo específico
            print(f"ADVERTENCIA: No se encontró plantilla para script '{script_prompt_type}' en estilo '{style_id}'. Usando 'default'.")
            default_style = self.prompts.get("default", {})
            default_script_prompts = default_style.get("script_prompt", {})
            return default_script_prompts.get(script_prompt_type, "") # Devuelve "" si ni siquiera en default existe

    def add_style(self, style_id: str, name: str, description: str) -> bool:
        """Añade un nuevo estilo con plantillas de prompt por defecto."""
        if style_id in self.prompts:
            print(f"ERROR: Ya existe un estilo con ID '{style_id}'.")
            return False
        if not re.match(r'^[a-zA-Z0-9_]+$', style_id): # Validar ID
             print("ERROR: El ID solo puede contener letras, números y guiones bajos.")
             return False

        import copy # Usar copia profunda para la plantilla
        new_style_data = copy.deepcopy(DEFAULT_STYLE_TEMPLATE)
        new_style_data["name"] = name
        new_style_data["description"] = description

        self.prompts[style_id] = new_style_data
        self._save_prompts()
        print(f"INFO: Nuevo estilo '{style_id}' añadido con plantillas por defecto.")
        return True

    def update_style_metadata(self, style_id: str, name: str, description: str) -> bool:
        """Actualiza el nombre y descripción de un estilo."""
        if style_id not in self.prompts:
            return False
        self.prompts[style_id]["name"] = name
        self.prompts[style_id]["description"] = description
        self._save_prompts()
        return True

    def update_image_prompt_part(self, style_id: str, part: str, content: str) -> bool:
        """Actualiza una parte del prompt de imagen (system, user, negative)."""
        if style_id not in self.prompts or part not in ["system", "user", "negative"]:
            return False
        if "image_prompt" not in self.prompts[style_id]:
            self.prompts[style_id]["image_prompt"] = {} # Crear si no existe
        self.prompts[style_id]["image_prompt"][part] = content
        self._save_prompts()
        return True

    def update_script_prompt_template(self, style_id: str, script_prompt_type: str, template: str) -> bool:
        """Actualiza la plantilla para un tipo específico de prompt de guion."""
        if style_id not in self.prompts or script_prompt_type not in ["esquema", "seccion", "revision", "metadata"]:
            return False
        if "script_prompt" not in self.prompts[style_id]:
            self.prompts[style_id]["script_prompt"] = {} # Crear si no existe
        self.prompts[style_id]["script_prompt"][script_prompt_type] = template
        self._save_prompts()
        return True

    def delete_style(self, style_id: str) -> bool:
        """Elimina un estilo completo (excepto 'default')."""
        if style_id == "default":
            print("ERROR: No se puede eliminar el estilo 'default'.")
            return False
        if style_id not in self.prompts:
            return False

        del self.prompts[style_id]
        self._save_prompts()
        print(f"INFO: Estilo '{style_id}' eliminado.")
        return True

# --- Código de prueba opcional ---
if __name__ == "__main__":
    print("--- Probando PromptManager Refactorizado ---")
    manager = PromptManager() # Usa el archivo por defecto en ./data/

    print("\nEstilos disponibles:")
    for style_id, name in manager.get_prompt_names():
        print(f"- ID: {style_id}, Nombre: {name}")

    print("\nObteniendo partes del prompt de imagen para 'default':")
    img_parts = manager.get_image_prompt_parts("default")
    if img_parts:
        print(f"  System: {img_parts.get('system', '')[:50]}...")
        print(f"  User: {img_parts.get('user', '')[:50]}...")
        print(f"  Negative: {img_parts.get('negative', '')}")
    else:
        print("  No se encontraron partes de prompt de imagen.")


    print("\nObteniendo plantilla de 'esquema' para script 'default':")
    schema_template = manager.get_script_prompt_template("default", "esquema")
    print(f"  Plantilla Esquema: {schema_template[:100]}...")

    print("\nObteniendo plantilla de 'seccion' para script 'educativo':")
    section_template = manager.get_script_prompt_template("educativo", "seccion")
    print(f"  Plantilla Sección (Educativo): {section_template[:100]}...")

    print("\nIntentando obtener plantilla inexistente ('metadata' para 'inexistente'):")
    non_existent = manager.get_script_prompt_template("inexistente", "metadata")
    print(f"  Resultado (debería usar default): {non_existent[:100]}...")


    # Ejemplo: Añadir un nuevo estilo (descomentar para probar)
    # print("\nAñadiendo nuevo estilo 'mi_estilo'...")
    # success_add = manager.add_style("mi_estilo", "Mi Estilo Personalizado", "Descripción de mi estilo")
    # if success_add:
    #     print("  ¡Estilo añadido! Verificando...")
    #     print(f"  Datos Mi Estilo: {manager.get_style('mi_estilo')}")
    #     # Ejemplo: Actualizar una parte
    #     manager.update_script_prompt_template("mi_estilo", "seccion", "Este es mi prompt de sección personalizado.")
    #     print(f"  Prompt Sección actualizado: {manager.get_script_prompt_template('mi_estilo', 'seccion')}")
    #     # Ejemplo: Eliminar el estilo
    #     # manager.delete_style("mi_estilo")
    #     # print("  Estilo 'mi_estilo' eliminado.")
    # else:
    #     print("  Fallo al añadir el estilo (quizás ya existe).")