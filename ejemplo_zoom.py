from moviepy import *
from efectos import ZoomEffect
import os

# Configuración básica
size = (1280, 720)  # Tamaño del video (HD)
fps = 24  # Frames por segundo
duracion_img = 5  # Duración de cada imagen en segundos

# Directorio de imágenes
directorio_imagenes = "images"  # Carpeta con las imágenes de ejemplo

# Verificar que el directorio existe
if not os.path.exists(directorio_imagenes):
    print(f"Error: El directorio {directorio_imagenes} no existe")
    exit(1)

# Obtener lista de imágenes
imagenes = [os.path.join(directorio_imagenes, f) for f in os.listdir(directorio_imagenes) 
           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
imagenes.sort()

if not imagenes:
    print("No se encontraron imágenes en el directorio")
    exit(1)

print(f"Se encontraron {len(imagenes)} imágenes")

# Crear video con zoom in
def crear_video_zoom(tipo_zoom, nombre_salida):
    print(f"Creando video con zoom {tipo_zoom}...")
    
    # Crear clips de imagen
    clips = []
    for imagen in imagenes:
        # Cargar imagen y configurar duración
        clip = ImageClip(imagen).with_duration(duracion_img)
        
        # Redimensionar si es necesario
        if clip.size != size:
            clip = clip.resized(size)
        
        # Aplicar efecto de zoom
        zoom_in = tipo_zoom.lower() == 'in'
        effect = ZoomEffect(zoom_in=zoom_in, ratio=0.04)
        clip = clip.transform(effect.apply)
        
        clips.append(clip)
    
    # Concatenar clips
    video = concatenate_videoclips(clips)
    
    # Guardar video
    video.write_videofile(nombre_salida, fps=fps)
    print(f"Video guardado como {nombre_salida}")

# Crear video con zoom in
crear_video_zoom('in', 'zoom_in_ejemplo.mp4')

# Crear video con zoom out
crear_video_zoom('out', 'zoom_out_ejemplo.mp4')

print("\nProceso completado. Se han creado dos videos de ejemplo:")
print("- zoom_in_ejemplo.mp4: Efecto de acercamiento")
print("- zoom_out_ejemplo.mp4: Efecto de alejamiento")