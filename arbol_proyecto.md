# Árbol del Proyecto VideoPython

```
VideoPython/
├── .gitignore
├── README.md
├── batch_tts.py            # Procesamiento por lotes de texto a voz
├── check.py                # Script de verificación
├── efectos.py              # Efectos para videos
├── gemini_models.py        # Integración con modelos Gemini
├── gui.py                  # Interfaz gráfica de usuario u punto de entrada de la app
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
- **subtitles.py**: Manejo de subtítulos y generación automática con Whisper
- **tts_generator.py**: Generación de voz a partir de texto
- **image_generator.py**: Generación de imágenes para videos

### Módulos
- **app/**: Contiene la lógica principal para la creación y generación de videos
- **ui/**: Componentes de la interfaz de usuario organizados en pestañas

### Efectos y transiciones
- **efectos.py**: Implementación de efectos visuales para videos
- **overlay_effects.py**: Efectos de superposición en videos
- **transiciones.py**: Transiciones entre clips de video

### Recursos
- **fonts/**: Fuentes tipográficas utilizadas en los videos
- **Docs/**: Documentación del proyecto

### Configuración
- **settings.json**: Archivo de configuración de la aplicación