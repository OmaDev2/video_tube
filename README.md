# Creador de Videos con Efectos

Este proyecto proporciona herramientas para crear videos a partir de imágenes aplicando diversos efectos visuales como zoom, transiciones, fade in/out y overlays.

## Características

- Creación de videos a partir de imágenes estáticas
- Efectos de zoom:
  - Zoom in (acercamiento)
  - Zoom out (alejamiento)
  - Secuencias personalizadas de efectos
  - Alternancia automática entre zoom in y zoom out
- Transiciones entre imágenes
- Efectos de fade in/out
- Efectos de overlay (superposición):
  - Aplicación de overlays individuales
  - Aplicación secuencial de múltiples overlays
- Control sobre la duración y velocidad de los efectos
- Interfaz de línea de comandos interactiva

## Requisitos

```
moviepy
Pillow
numpy
```

Puedes instalar las dependencias con:

```bash
pip install -r requirements.txt
```

## Uso

### Aplicación principal

Ejecuta el archivo `app.py` para iniciar la aplicación interactiva:

```bash
python app.py
```

Sigue las instrucciones en pantalla para configurar tu video con las siguientes opciones:

1. Seleccionar la carpeta con imágenes
2. Definir el nombre del archivo de salida
3. Configurar la duración de cada imagen
4. Establecer los FPS del video
5. Elegir si aplicar efectos de zoom y su configuración:
   - Un solo tipo de efecto (in/out)
   - Secuencia personalizada de efectos
   - Alternancia automática entre zoom in y zoom out
6. Aplicar transiciones entre imágenes
7. Configurar efectos de fade in/out
8. Aplicar efectos de overlay (superposición)

### Ejemplos

Puedes ejecutar el archivo de ejemplo para ver cómo funcionan los efectos de zoom:

```bash
python ejemplo_zoom.py
```

Este script creará dos videos de ejemplo:
- `zoom_in_ejemplo.mp4`: Muestra el efecto de acercamiento
- `zoom_out_ejemplo.mp4`: Muestra el efecto de alejamiento

## Implementación personalizada

### Efectos de Zoom

Puedes usar la clase `ZoomEffect` directamente en tu código:

```python
from moviepy import *
from efectos import ZoomEffect

# Cargar una imagen
clip = ImageClip("mi_imagen.jpg").with_duration(5)

# Aplicar zoom in
effect = ZoomEffect(zoom_in=True, ratio=0.04)
clip_con_zoom = clip.transform(effect.apply)

# Guardar el video
clip_con_zoom.write_videofile("mi_video.mp4", fps=24)
```

### Transiciones

Puedes aplicar transiciones entre clips:

```python
from moviepy import *
from transiciones import TransitionEffect

# Crear clips
clip1 = ImageClip("imagen1.jpg").with_duration(5)
clip2 = ImageClip("imagen2.jpg").with_duration(5)
clips = [clip1, clip2]

# Aplicar transición
video_final = TransitionEffect.apply_transition(clips, "fade", 2.0)

# Guardar el video
video_final.write_videofile("video_con_transicion.mp4", fps=24)
```

### Efectos de Overlay

Puedes aplicar efectos de superposición (overlay):

```python
from moviepy import *
from overlay_effects import OverlayEffect

# Cargar un clip base
clip = ImageClip("mi_imagen.jpg").with_duration(5)

# Aplicar overlay
clip_con_overlay = OverlayEffect.apply_overlay(clip, "overlay.mp4", opacity=0.5)

# Guardar el video
clip_con_overlay.write_videofile("video_con_overlay.mp4", fps=24)
```

También puedes aplicar overlays secuenciales a múltiples clips:

```python
from moviepy import *
from overlay_effects import OverlayEffect

# Crear clips
clip1 = ImageClip("imagen1.jpg").with_duration(5)
clip2 = ImageClip("imagen2.jpg").with_duration(5)
clips = [clip1, clip2]

# Definir overlays
overlays = ["overlay1.mp4", "overlay2.mp4"]

# Aplicar overlays secuencialmente
clips_con_overlay = OverlayEffect.apply_sequential_overlays(clips, overlays, opacity=0.5)

# Concatenar clips
video_final = concatenate_videoclips(clips_con_overlay)

# Guardar el video
video_final.write_videofile("video_con_overlays.mp4", fps=24)
```

## Parámetros

### Efectos de Zoom
- `zoom_in`: Boolean que indica si el zoom es de acercamiento (`True`) o alejamiento (`False`)
- `ratio`: Factor de zoom por segundo. Valores más altos resultan en un zoom más rápido

### Transiciones
- Tipos disponibles: fade, crossfade, wipe, slide, etc.
- `duracion_transicion`: Duración en segundos de la transición

### Overlays
- `opacity`: Opacidad del overlay (0.1 a 1.0)
- Formatos soportados: .mp4, .mov, .avi, .webm

## Notas

Este proyecto utiliza MoviePy v2.0 y su nuevo sistema de efectos basado en objetos.

Para usar los efectos de overlay, debes colocar tus archivos de video de overlay en la carpeta `overlays` del proyecto.