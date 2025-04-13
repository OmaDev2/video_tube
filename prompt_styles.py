# -*- coding: utf-8 -*-
# Archivo: prompt_styles.py

"""
Gestor de estilos de prompts para la generación de imágenes.
Este módulo contiene diferentes plantillas y estilos para generar prompts
adaptados a distintos géneros y estilos visuales (terror, animación, cine, etc.)
"""

# Diccionario de estilos de prompts
PROMPT_STYLES = {
    # Estilo por defecto (cinematográfico general)
    "default": {
        "name": "Cinematográfico",
        "description": "Estilo visual cinematográfico general, con buena iluminación y composición",
        "prompt_template": """Cinematic scene: {escena}. Professional lighting, high detail, dramatic composition. 16:9 aspect ratio.""",
        "negative_prompt": "text, watermark, low quality, blurry"
    },
    
    # Estilos de cine
    "cine_terror": {
        "name": "Terror Cinematográfico",
        "description": "Estilo visual de película de terror, oscuro y atmosférico",
        "prompt_template": """Horror movie scene: {escena}. Dark atmosphere, eerie lighting, unsettling composition, cinematic quality. Inspired by films like The Shining and Hereditary. 16:9 aspect ratio.""",
        "negative_prompt": "bright colors, daylight, cheerful, cartoon, text, watermark, low quality"
    },
    "cine_scifi": {
        "name": "Ciencia Ficción",
        "description": "Estilo visual de ciencia ficción futurista",
        "prompt_template": """Sci-fi cinematic scene: {escena}. Futuristic setting, advanced technology, dramatic lighting, lens flares, high detail. Inspired by films like Blade Runner and Dune. 16:9 aspect ratio.""",
        "negative_prompt": "historical, medieval, cartoon, text, watermark, low quality"
    },
    "cine_drama": {
        "name": "Drama",
        "description": "Estilo visual de drama cinematográfico, emotivo y personal",
        "prompt_template": """Dramatic cinematic scene: {escena}. Emotional moment, intimate framing, natural lighting, subtle color palette. Inspired by films like The Godfather and Schindler's List. 16:9 aspect ratio.""",
        "negative_prompt": "cartoon, anime, bright saturated colors, text, watermark, low quality"
    },
    
    # Estilos de animación
    "animacion_pixar": {
        "name": "Animación Estilo Pixar",
        "description": "Estilo visual de animación 3D tipo Pixar",
        "prompt_template": """3D animated scene in Pixar style: {escena}. Vibrant colors, expressive characters, detailed textures, soft lighting. 16:9 aspect ratio.""",
        "negative_prompt": "realistic, photographic, live action, dark, horror, text, watermark, low quality"
    },
    "animacion_anime": {
        "name": "Anime Japonés",
        "description": "Estilo visual de anime japonés",
        "prompt_template": """Anime scene: {escena}. Japanese animation style, vibrant colors, expressive characters, detailed backgrounds. 16:9 aspect ratio.""",
        "negative_prompt": "realistic, photographic, 3D, western cartoon, text, watermark, low quality"
    },
    "animacion_disney": {
        "name": "Animación Estilo Disney",
        "description": "Estilo visual de animación clásica de Disney",
        "prompt_template": """Disney-style animated scene: {escena}. Classic hand-drawn animation style, expressive characters, rich backgrounds, magical atmosphere. 16:9 aspect ratio.""",
        "negative_prompt": "3D, CGI, realistic, photographic, text, watermark, low quality"
    },
    
    # Estilos artísticos
    "arte_oleo": {
        "name": "Pintura al Óleo",
        "description": "Estilo visual de pintura al óleo clásica",
        "prompt_template": """Oil painting scene: {escena}. Classical oil painting style, rich textures, dramatic lighting, visible brushstrokes. Inspired by classical masters. 16:9 aspect ratio.""",
        "negative_prompt": "digital art, 3D, cartoon, anime, photographic, text, watermark, low quality"
    },
    "arte_acuarela": {
        "name": "Acuarela",
        "description": "Estilo visual de acuarela, suave y fluido",
        "prompt_template": """Watercolor painting scene: {escena}. Soft watercolor style, flowing colors, gentle transitions, artistic composition. 16:9 aspect ratio.""",
        "negative_prompt": "digital art, 3D, sharp details, photographic, text, watermark, low quality"
    },
    
    # Estilos fotográficos
    "foto_documental": {
        "name": "Fotografía Documental",
        "description": "Estilo visual de fotografía documental realista",
        "prompt_template": """Documentary photography: {escena}. Realistic photographic style, natural lighting, candid moment, journalistic approach. 16:9 aspect ratio.""",
        "negative_prompt": "cartoon, anime, painting, artificial, staged, text, watermark, low quality"
    },
    "foto_retrato": {
        "name": "Retrato Fotográfico",
        "description": "Estilo visual de retrato fotográfico profesional",
        "prompt_template": """Professional portrait photography: {escena}. Studio lighting, shallow depth of field, professional composition, high detail. 16:9 aspect ratio.""",
        "negative_prompt": "cartoon, anime, painting, wide angle, text, watermark, low quality"
    }
}

def get_style_names():
    """Devuelve una lista con los nombres de todos los estilos disponibles"""
    return [(style_id, info["name"]) for style_id, info in PROMPT_STYLES.items()]

def get_style_template(style_id):
    """Obtiene la plantilla de prompt para un estilo específico
    
    Args:
        style_id: Identificador del estilo
        
    Returns:
        dict: Información del estilo o None si no existe
    """
    return PROMPT_STYLES.get(style_id, PROMPT_STYLES["default"])

def generate_prompt(style_id, titulo, escena):
    """Genera un prompt basado en un estilo, título y escena
    
    Args:
        style_id: Identificador del estilo
        titulo: Título del video
        escena: Texto de la escena
        
    Returns:
        str: Prompt generado
    """
    style = get_style_template(style_id)
    
    # Combinar título y escena para el contexto completo
    context = f"{titulo}: {escena}" if titulo else escena
    
    # Generar el prompt usando la plantilla del estilo
    prompt = style["prompt_template"].format(escena=context)
    
    return prompt

def get_negative_prompt(style_id):
    """Obtiene el prompt negativo para un estilo específico
    
    Args:
        style_id: Identificador del estilo
        
    Returns:
        str: Prompt negativo
    """
    style = get_style_template(style_id)
    return style.get("negative_prompt", "")
