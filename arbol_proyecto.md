Actualización del Árbol de Directorios del Proyecto VideoPython
==================================================

Este documento contiene la estructura de directorios del proyecto **VideoPython**, una herramienta para la creación y edición de videos a partir de imágenes.

## Estructura de Directorios

```
VideoPython/
├── .env                    # Archivo de variables de entorno
├── app.py                  # Aplicación principal
├── batch_tts.py            # Procesamiento por lotes de texto a voz
├── config.py               # Configuración general del proyecto
├── directory_tree.py       # Script para generar árbol de directorios
├── efectos.py              # Efectos visuales para los videos
├── gui.py                  # Interfaz gráfica de usuario y punto de entrada de la app
├── image_generator.py      # Generador de imágenes
├── overlay_effects.py      # Efectos de superposición
├── prompt_generator.py     # Generador de prompts
├── settings.json           # Configuración de la aplicación
├── subtitles.py            # Manejo de subtítulos
├── transiciones.py         # Efectos de transición
├── tts_generator.py        # Generador de texto a voz
│
├── app/                    # Módulo principal de la aplicación
│   ├── __init__.py
│   ├── video_creator.py    # Creador de videos
│   └── video_generator.py  # Generador de videos
│
├── Docs/                   # Documentación del proyecto
│
├── fonts/                  # Fuentes utilizadas en los videos
│   ├── BungeeTint-Regular.ttf
│   └── Roboto-Regular.ttf
│
└── ui/                     # Componentes de la interfaz de usuario
    ├── __init__.py
    ├── tab_audio.py        # Pestaña de audio
    ├── tab_basico.py       # Pestaña básica
    ├── tab_batch.py        # Pestaña de procesamiento por lotes
    ├── tab_efectos.py      # Pestaña de efectos
    ├── tab_settings.py     # Pestaña de configuración
    └── tab_subtitles.py    # Pestaña de subtítulos
```

## Descripción de los componentes principales

### Archivos principales

- **gui.py**: Interfaz gráfica de usuario y punto de entrada de la app
- **app.py**: Aplicación principal que conecta la interfaz con el backend
- **efectos.py**: Contiene las clases para los efectos visuales como zoom, rotación, etc.
- **transiciones.py**: Define las transiciones entre clips de video
- **tts_generator.py**: Generador de texto a voz para voz en off
- **batch_tts/**: Módulo de procesamiento por lotes para TTS, imágenes y video (ver detalle abajo)
- **subtitles.py**: Manejo de subtítulos para los videos
- **config.py**: Configuraciones generales como tamaño de imágenes, FPS, etc.

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
- **fonts/**: Fuentes personalizadas utilizadas en los videos y subtítulos
- **Docs/**: Documentación del proyecto (puede incluir guías, tutoriales, etc.)