Actualización del Árbol de Directorios del Proyecto VideoPython
==================================================

Este documento contiene la estructura de directorios del proyecto **VideoPython**, una herramienta para la creación y edición de videos a partir de imágenes con efectos visuales, transiciones, música, efectos de audio y subtítulos.

## Estructura de Directorios (Actualizada)

```
VideoPython/
├── .env                    # Archivo de variables de entorno
├── config.py               # Configuración general del proyecto
├── gui.py                  # Interfaz gráfica principal y punto de entrada de la aplicación
├── efectos.py              # Definición de efectos visuales (zoom, pan, ken burns, etc.)
├── overlay_effects.py      # Efectos de superposición para videos
├── transiciones.py         # Efectos de transición entre clips
├── subtitles.py            # Manejo y renderizado de subtítulos
├── tts_generator.py        # Generador de texto a voz (TTS)
├── image_generator.py      # Generador de imágenes con IA
├── prompt_generator.py     # Generador de prompts para IA
├── prompt_manager.py       # Gestor de estilos de prompts
├── prompt_styles.py        # Definición de estilos para prompts
├── ai_providers.py         # Integración con proveedores de IA (OpenAI, Gemini)
├── gemini_models.py        # Integración específica con modelos Gemini
├── project_manager.py      # Gestor de proyectos (guardar/cargar)
├── settings.json           # Configuración de la aplicación
├── arbol_proyecto.md       # Este documento
│
├── app/                    # Módulo principal para generación de videos
│   ├── __init__.py
│   ├── video_creator.py    # Interfaz para crear videos
│   └── video_generator.py  # Motor de generación de videos
│
├── batch_tts/              # Sistema de procesamiento por lotes
│   ├── __init__.py
│   ├── manager.py          # Gestor de cola de proyectos
│   ├── audio_worker.py     # Generación de audio/voz
│   ├── image_worker.py     # Generación de imágenes
│   ├── subtitles_worker.py # Generación de subtítulos
│   ├── video_worker.py     # Generación de videos
│   └── utils.py            # Utilidades comunes
│
├── ui/                     # Componentes de la interfaz de usuario
│   ├── __init__.py
│   ├── tab_audio.py        # Pestaña de configuración de audio
│   ├── tab_basico.py       # Pestaña de configuración básica
│   ├── tab_batch.py        # Pestaña de cola de proyectos
│   ├── tab_efectos.py      # Pestaña de efectos visuales
│   ├── tab_project.py      # Pestaña de gestión de proyectos
│   ├── tab_prompts.py      # Pestaña de configuración de prompts
│   ├── tab_prompts_new.py  # Nueva pestaña de prompts (en desarrollo)
│   ├── tab_settings.py     # Pestaña de configuración general
│   ├── tab_subtitles.py    # Pestaña de configuración de subtítulos
│   └── prompt_updater.py   # Actualizador de prompts
│
├── fonts/                  # Fuentes utilizadas en los videos
│   ├── BungeeTint-Regular.ttf
│   └── Roboto-Regular.ttf
│
├── Tests/                  # Scripts de prueba
│   ├── test_replicate.py   # Prueba de integración con Replicate
│   ├── test_subtitles.py   # Prueba de generación de subtítulos
│   ├── probar_voces.py     # Prueba de voces TTS
│   └── run_tts.py          # Prueba de generación de voz
│
└── proyectos_video/        # Carpeta donde se guardan los proyectos generados
```

## Descripción de los componentes principales

### Archivos principales

- **gui.py**: Interfaz gráfica principal que integra todos los componentes
- **efectos.py**: Define los efectos visuales como zoom, pan, ken burns, rotación, etc.
- **transiciones.py**: Define las transiciones entre clips de video (dissolve, fade, slide, etc.)
- **tts_generator.py**: Generador de texto a voz para voz en off con ajustes de velocidad y tono
- **overlay_effects.py**: Efectos de superposición como viñetas, filtros de color, etc.
- **subtitles.py**: Manejo de subtítulos para los videos con soporte para generación automática
- **config.py**: Configuraciones generales como tamaño de imágenes, FPS, etc.
- **project_manager.py**: Gestor para guardar y cargar proyectos completos

#### batch_tts/
- **manager.py**: Orquestador de la cola y lógica principal
- **audio_worker.py**: Lógica de TTS y generación de audio
- **image_worker.py**: Lógica de prompts e imágenes
- **video_worker.py**: Lógica de generación de video
- **subtitles_worker.py**: Lógica de subtítulos
- **utils.py**: Funciones auxiliares

### Carpetas principales

- **app/**: Módulo que contiene la lógica principal para la creación de videos
- **ui/**: Componentes de la interfaz de usuario divididos en pestañas para diferentes funcionalidades
- **batch_tts/**: Sistema de procesamiento por lotes para generación automatizada
- **fonts/**: Fuentes personalizadas utilizadas en los videos y subtítulos
- **Tests/**: Scripts de prueba para validar funcionalidades
- **proyectos_video/**: Directorio donde se almacenan los proyectos generados

## Cambios recientes

### Mejoras en la experiencia de usuario (2025-04-19)

1. **Ajustes de voz TTS por defecto:**
   - Velocidad (rate): `-3%` para mayor claridad
   - Tono (pitch): `-6Hz` para un sonido más natural

2. **Subtítulos activados por defecto:**
   - Ahora los nuevos proyectos tienen los subtítulos habilitados automáticamente

3. **Efectos visuales preseleccionados:**
   - Efectos de zoom (in/out) marcados por defecto
   - Efectos de paneo (up/down/left/right) marcados por defecto

4. **Inicialización automática de secuencia de efectos:**
   - La secuencia de efectos se genera automáticamente basada en los checkboxes marcados
   - Solución para problemas con efectos Ken Burns reemplazándolos por alternativas más estables

### Mejoras técnicas anteriores

1. **Nueva pestaña de "Ajustes de Efectos":**
   - Permite configurar parámetros detallados para diferentes efectos visuales
   - Incluye ajustes para ZoomEffect, PanEffect, KenBurnsEffect, transiciones y overlay effects

2. **Corrección de problemas críticos:**
   - Solución para la recursión infinita en los efectos
   - Corrección del error "TypeError: unsupported callable" en transiciones
   - Mejora en la robustez del sistema de generación de videos