# script_prompt_manager.py
import json
import os
from pathlib import Path

DEFAULT_SCRIPT_PROMPTS_FILE = "script_prompts.json"

class ScriptPromptManager:
    def __init__(self, filepath=DEFAULT_SCRIPT_PROMPTS_FILE):
        self.filepath = Path(filepath)
        self.styles = {}
        self.load_prompts()

    def load_prompts(self):
        """Carga los prompts desde el archivo JSON."""
        if not self.filepath.is_file():
            print(f"ADVERTENCIA: Archivo de prompts de guion no encontrado en {self.filepath}. Creando uno por defecto.")
            self._create_default_file()
            return # Carga lo que se creó por defecto

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.styles = json.load(f)
            print(f"Prompts de guion cargados desde {self.filepath}")
        except json.JSONDecodeError:
            print(f"ERROR: Error al decodificar JSON en {self.filepath}. Verifica el formato.")
            self.styles = {"default": self._get_default_style_data()} # Carga default si falla
        except Exception as e:
            print(f"ERROR: No se pudieron cargar los prompts de guion: {e}")
            self.styles = {"default": self._get_default_style_data()} # Carga default si falla

    def save_prompts(self):
        """Guarda los prompts actuales en el archivo JSON."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.styles, f, indent=2, ensure_ascii=False)
            print(f"Prompts de guion guardados en {self.filepath}")
        except Exception as e:
            print(f"ERROR: No se pudieron guardar los prompts de guion: {e}")

    def get_style_names(self) -> list[tuple[str, str]]:
        """Devuelve una lista de tuplas (id_estilo, nombre_mostrado)."""
        return [(style_id, data.get("name", style_id)) for style_id, data in self.styles.items()]

    def get_prompt_template(self, style_id: str, prompt_type: str) -> str:
        """Obtiene una plantilla de prompt específica, con fallback a 'default'. (Modo legacy: devuelve string plano)"""
        style_data = self.styles.get(style_id, self.styles.get('default', {}))
        template = style_data.get(prompt_type, "")
        if not template and style_id != 'default':
            # Fallback a default si el tipo no existe en el estilo específico
            print(f"ADVERTENCIA: Tipo de prompt '{prompt_type}' no encontrado para estilo '{style_id}'. Usando default.")
            default_style_data = self.styles.get('default', {})
            template = default_style_data.get(prompt_type, "")
        if not template:
            print(f"ERROR FATAL: Tipo de prompt '{prompt_type}' no encontrado ni en estilo '{style_id}' ni en 'default'.")
        # Si es un dict, devuelve solo el user_prompt (legacy)
        if isinstance(template, dict):
            return template.get('user_prompt', '')
        return template

    def get_full_prompt(self, style_id: str, prompt_type: str) -> dict:
        """
        Devuelve tanto el system_prompt como el user_prompt para el tipo de prompt y estilo indicados.
        Si el prompt es un string plano (legacy), lo pone en 'user_prompt' y deja system_prompt vacío.
        """
        style_data = self.styles.get(style_id, self.styles.get('default', {}))
        prompt_obj = style_data.get(prompt_type, "")
        if not prompt_obj and style_id != 'default':
            # Fallback a default si el tipo no existe en el estilo específico
            print(f"ADVERTENCIA: Tipo de prompt '{prompt_type}' no encontrado para estilo '{style_id}'. Usando default.")
            default_style_data = self.styles.get('default', {})
            prompt_obj = default_style_data.get(prompt_type, "")
        if not prompt_obj:
            print(f"ERROR FATAL: Tipo de prompt '{prompt_type}' no encontrado ni en estilo '{style_id}' ni en 'default'.")
            return {"system_prompt": "", "user_prompt": ""}
        if isinstance(prompt_obj, dict):
            return {
                "system_prompt": prompt_obj.get("system_prompt", ""),
                "user_prompt": prompt_obj.get("user_prompt", "")
            }
        else:
            # Compatibilidad hacia atrás
            return {"system_prompt": "", "user_prompt": str(prompt_obj)}

    def get_style_data(self, style_id: str) -> dict:
        """Obtiene todos los datos (nombre y prompts) para un estilo."""
        # Devuelve una copia para evitar modificaciones accidentales
        return self.styles.get(style_id, {}).copy()

    def update_style(self, style_id: str, data: dict):
        """Añade o actualiza un estilo completo."""
        if not all(k in data for k in ["name", "esquema", "seccion", "revision", "metadata"]):
             print("ERROR: Datos para actualizar estilo están incompletos.")
             return False
        self.styles[style_id] = data
        print(f"Estilo '{style_id}' actualizado/añadido.")
        self.save_prompts()
        return True

    def delete_style(self, style_id: str):
        """Elimina un estilo (no permite borrar 'default')."""
        if style_id == 'default':
            print("ERROR: No se puede eliminar el estilo 'default'.")
            return False
        if style_id in self.styles:
            del self.styles[style_id]
            print(f"Estilo '{style_id}' eliminado.")
            return True
        else:
            print(f"ERROR: Estilo '{style_id}' no encontrado para eliminar.")
            return False

    def _get_default_style_data(self) -> dict:
        """Devuelve la estructura de un estilo por defecto si el archivo no existe."""
        # Puedes poner aquí un prompt muy básico o un mensaje de error
        return {
            "name": "Predeterminado (Archivo Creado)",
            "esquema": "ERROR: Plantilla de esquema por defecto no definida.",
            "seccion": "ERROR: Plantilla de sección por defecto no definida.",
            "revision": "ERROR: Plantilla de revisión por defecto no definida.",
            "metadata": "ERROR: Plantilla de metadata por defecto no definida."
        }

    def _create_default_file(self):
        """Crea un archivo JSON por defecto si no existe."""
        default_data = {"default": self._get_default_style_data()}
        self.styles = default_data
        self.save_prompts()