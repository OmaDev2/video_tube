#!/usr/bin/env python3
from moviepy import *
from efectos import ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, PanRightEffect, KenBurnsEffect
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

# Crear video con el efecto especificado
def crear_video_efecto(tipo_efecto, nombre_salida):
    print(f"Creando video con efecto {tipo_efecto}...")
    
    # Crear clips de imagen
    clips = []
    for imagen in imagenes:
        # Cargar imagen y configurar duración
        clip = ImageClip(imagen).with_duration(duracion_img)
        
        # Redimensionar si es necesario
        if clip.size != size:
            clip = clip.resized(size)
        
        # Aplicar el efecto correspondiente
        if tipo_efecto == 'zoom_in':
            effect = ZoomEffect(zoom_in=True, ratio=0.04)
        elif tipo_efecto == 'zoom_out':
            effect = ZoomEffect(zoom_in=False, ratio=0.04)
        elif tipo_efecto == 'pan_up':
            effect = PanUpEffect(speed=0.05)
        elif tipo_efecto == 'pan_down':
            effect = PanDownEffect(speed=0.05)
        elif tipo_efecto == 'pan_left':
            effect = PanLeftEffect(speed=0.05)
        elif tipo_efecto == 'pan_right':
            effect = PanRightEffect(speed=0.05)
        elif tipo_efecto == 'kenburns':
            effect = KenBurnsEffect(zoom_direction='in', pan_direction='up')
        else:
            print(f"Tipo de efecto desconocido: {tipo_efecto}")
            continue
        
        # Aplicar el efecto
        clip = clip.transform(effect.apply)
        clips.append(clip)
    
    # Concatenar clips
    video = concatenate_videoclips(clips)
    
    # Guardar video
    video.write_videofile(nombre_salida, fps=fps)
    print(f"Video guardado como {nombre_salida}")

# Crear videos de ejemplo para cada tipo de efecto
efectos = {
    'zoom_in': 'zoom_in_ejemplo.mp4',
    'zoom_out': 'zoom_out_ejemplo.mp4',
    'pan_up': 'pan_up_ejemplo.mp4',
    'pan_down': 'pan_down_ejemplo.mp4',
    'pan_left': 'pan_left_ejemplo.mp4',
    'pan_right': 'pan_right_ejemplo.mp4',
    'kenburns': 'kenburns_ejemplo.mp4'
}

# Crear todos los videos de ejemplo o solo uno específico
def crear_todos_los_videos():
    for tipo_efecto, nombre_salida in efectos.items():
        crear_video_efecto(tipo_efecto, nombre_salida)

def mostrar_menu():
    print("\nCreador de Videos de Ejemplo con Efectos")
    print("========================================")
    print("1. Zoom In (acercamiento)")
    print("2. Zoom Out (alejamiento)")
    print("3. Pan Up (movimiento hacia arriba)")
    print("4. Pan Down (movimiento hacia abajo)")
    print("5. Pan Left (movimiento hacia la izquierda)")
    print("6. Pan Right (movimiento hacia la derecha)")
    print("7. Ken Burns (efecto cinematográfico)")
    print("8. Crear todos los ejemplos")
    print("0. Salir")
    
    opcion = input("\nSelecciona una opción (0-8): ")
    
    if opcion == '0':
        return False
    elif opcion == '8':
        crear_todos_los_videos()
    else:
        opciones_map = {
            '1': 'zoom_in',
            '2': 'zoom_out',
            '3': 'pan_up',
            '4': 'pan_down',
            '5': 'pan_left',
            '6': 'pan_right',
            '7': 'kenburns'
        }
        
        if opcion in opciones_map:
            tipo_efecto = opciones_map[opcion]
            crear_video_efecto(tipo_efecto, efectos[tipo_efecto])
        else:
            print("Opción no válida")
    
    return True

if __name__ == "__main__":
    continuar = True
    while continuar:
        continuar = mostrar_menu()