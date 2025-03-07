# Efectos de Zoom con MoviePy

Este proyecto proporciona herramientas para crear videos a partir de imágenes aplicando efectos de zoom (acercamiento y alejamiento).

## Características

- Creación de videos a partir de imágenes estáticas
- Efecto de zoom in (acercamiento)
- Efecto de zoom out (alejamiento)
- Control sobre la velocidad del efecto de zoom
- Interfaz de línea de comandos sencilla

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

Sigue las instrucciones en pantalla para:
1. Seleccionar la carpeta con imágenes
2. Definir el nombre del archivo de salida
3. Configurar la duración de cada imagen
4. Establecer los FPS del video
5. Elegir si aplicar efectos de zoom
6. Seleccionar el tipo de zoom (in/out)

### Ejemplos

Puedes ejecutar el archivo de ejemplo para ver cómo funcionan los efectos de zoom:

```bash
python ejemplo_zoom.py
```

Este script creará dos videos de ejemplo:
- `zoom_in_ejemplo.mp4`: Muestra el efecto de acercamiento
- `zoom_out_ejemplo.mp4`: Muestra el efecto de alejamiento

## Implementación personalizada

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

## Parámetros del efecto de zoom

- `zoom_in`: Boolean que indica si el zoom es de acercamiento (`True`) o alejamiento (`False`)
- `ratio`: Factor de zoom por segundo. Valores más altos resultan en un zoom más rápido

## Notas

Este proyecto utiliza MoviePy v2.0 y su nuevo sistema de efectos basado en objetos.