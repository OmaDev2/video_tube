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

# Crear video con el efecto especificado y configuración personalizada
def crear_video_efecto(tipo_efecto, nombre_salida, scale_factor=1.3, speed=0.05):
    print(f"Creando video con efecto {tipo_efecto} (scale_factor={scale_factor}, speed={speed})...")
    
    # Crear clips de imagen
    clips = []
    for imagen in imagenes:
        # Cargar imagen y configurar duración
        clip = ImageClip(imagen).with_duration(duracion_img)
        
        # Redimensionar si es necesario
        if clip.size != size:
            clip = clip.resized(size)
        
        # Aplicar el efecto correspondiente con la configuración personalizada
        if tipo_efecto == 'zoom_in':
            effect = ZoomEffect(zoom_in=True, ratio=speed)
        elif tipo_efecto == 'zoom_out':
            effect = ZoomEffect(zoom_in=False, ratio=speed)
        elif tipo_efecto == 'pan_up':
            effect = PanUpEffect(speed=speed, scale_factor=scale_factor)
        elif tipo_efecto == 'pan_down':
            effect = PanDownEffect(speed=speed, scale_factor=scale_factor)
        elif tipo_efecto == 'pan_left':
            effect = PanLeftEffect(speed=speed, scale_factor=scale_factor)
        elif tipo_efecto == 'pan_right':
            effect = PanRightEffect(speed=speed, scale_factor=scale_factor)
        elif tipo_efecto == 'kenburns':
            effect = KenBurnsEffect(zoom_direction='in', pan_direction='up', 
                                    zoom_ratio=speed, pan_speed=speed, 
                                    scale_factor=scale_factor)
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

# Definir configuraciones predefinidas para probar
configuraciones = {
    'default': {'scale_factor': 1.3, 'speed': 0.05},
    'sutil': {'scale_factor': 1.2, 'speed': 0.04},
    'amplio': {'scale_factor': 1.5, 'speed': 0.06},
    'extremo': {'scale_factor': 1.8, 'speed': 0.08}
}

# Crear videos de ejemplo para cada tipo de efecto
efectos = {
    'zoom_in': 'Zoom In (acercamiento)',
    'zoom_out': 'Zoom Out (alejamiento)',
    'pan_up': 'Pan Up (movimiento hacia arriba)',
    'pan_down': 'Pan Down (movimiento hacia abajo)',
    'pan_left': 'Pan Left (movimiento hacia la izquierda)',
    'pan_right': 'Pan Right (movimiento hacia la derecha)',
    'kenburns': 'Ken Burns (efecto cinematográfico)'
}

def mostrar_menu_principal():
    print("\nCreador de Videos de Ejemplo con Efectos")
    print("========================================")
    print("1. Crear ejemplo con configuración predefinida")
    print("2. Crear ejemplo con configuración personalizada")
    print("3. Comparar diferentes configuraciones para un mismo efecto")
    print("0. Salir")
    
    opcion = input("\nSelecciona una opción (0-3): ")
    
    if opcion == '0':
        return False
    elif opcion == '1':
        crear_con_configuracion_predefinida()
    elif opcion == '2':
        crear_con_configuracion_personalizada()
    elif opcion == '3':
        comparar_configuraciones()
    else:
        print("Opción no válida")
    
    return True

def seleccionar_efecto():
    print("\nSelecciona un efecto:")
    for i, (key, value) in enumerate(efectos.items(), 1):
        print(f"{i}. {value}")
    
    while True:
        opcion = input("\nSelecciona un efecto (1-7): ")
        try:
            indice = int(opcion) - 1
            if 0 <= indice < len(efectos):
                return list(efectos.keys())[indice]
            else:
                print("Opción no válida. Introduce un número entre 1 y 7.")
        except ValueError:
            print("Por favor, introduce un número válido.")

def crear_con_configuracion_predefinida():
    tipo_efecto = seleccionar_efecto()
    
    print("\nSelecciona una configuración:")
    print("1. Default (scale_factor=1.3, speed=0.05)")
    print("2. Sutil (scale_factor=1.2, speed=0.04)")
    print("3. Amplio (scale_factor=1.5, speed=0.06)")
    print("4. Extremo (scale_factor=1.8, speed=0.08)")
    
    opcion = input("\nSelecciona una configuración (1-4): ")
    
    config_name = 'default'
    if opcion == '2':
        config_name = 'sutil'
    elif opcion == '3':
        config_name = 'amplio'
    elif opcion == '4':
        config_name = 'extremo'
    
    config = configuraciones[config_name]
    nombre_salida = f"{tipo_efecto}_{config_name}.mp4"
    
    crear_video_efecto(tipo_efecto, nombre_salida, 
                       scale_factor=config['scale_factor'], 
                       speed=config['speed'])

def crear_con_configuracion_personalizada():
    tipo_efecto = seleccionar_efecto()
    
    # Solicitar valores personalizados
    try:
        scale_factor = float(input("\nIntroduce el valor de scale_factor (1.1-2.0, recomendado 1.3): ") or "1.3")
        speed = float(input("Introduce el valor de speed (0.01-0.1, recomendado 0.05): ") or "0.05")
        
        # Validar los valores
        scale_factor = max(1.1, min(2.0, scale_factor))
        speed = max(0.01, min(0.1, speed))
        
        nombre_salida = f"{tipo_efecto}_custom.mp4"
        crear_video_efecto(tipo_efecto, nombre_salida, scale_factor=scale_factor, speed=speed)
    except ValueError:
        print("Valores no válidos. Se usarán los valores por defecto.")
        crear_video_efecto(tipo_efecto, f"{tipo_efecto}_default.mp4")

def comparar_configuraciones():
    tipo_efecto = seleccionar_efecto()
    
    print(f"\nCreando comparativas para el efecto {efectos[tipo_efecto]}...")
    
    # Crear un video para cada configuración predefinida
    for config_name, config in configuraciones.items():
        nombre_salida = f"{tipo_efecto}_{config_name}.mp4"
        crear_video_efecto(tipo_efecto, nombre_salida, 
                          scale_factor=config['scale_factor'], 
                          speed=config['speed'])
    
    print("\nSe han creado 4 videos con diferentes configuraciones para comparar:")
    for config_name in configuraciones.keys():
        print(f"- {tipo_efecto}_{config_name}.mp4")

if __name__ == "__main__":
    print("Este script te permite probar diferentes configuraciones de los efectos de paneo.")
    print("La opción 'scale_factor' controla cuánto se amplía la imagen antes del paneo:")
    print("- Valores más bajos (1.2): Mejor calidad de imagen, menos movimiento")
    print("- Valores más altos (1.5-1.8): Más movimiento, posible pérdida de calidad")
    print("\nLa opción 'speed' controla la velocidad del efecto:")
    print("- Valores más bajos (0.03): Movimiento más lento")
    print("- Valores más altos (0.08): Movimiento más rápido")
    
    continuar = True
    while continuar:
        continuar = mostrar_menu_principal()