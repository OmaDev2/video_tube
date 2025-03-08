#!/usr/bin/env python3
"""
Script para probar las diferentes variantes del efecto Ken Burns.
Este script generará varios videos de prueba con diferentes configuraciones
del efecto Ken Burns para que puedas encontrar el que mejor se adapta a tus necesidades.
"""

from moviepy import *
from efectos import KenBurnsEffect, KenBurnsZoomInPanRight, KenBurnsZoomOutPanLeft, KenBurnsDiagonalIn, KenBurnsDiagonalOut
import os
import time

# Configuración básica
size = (1280, 720)  # Tamaño del video (HD)
fps = 24  # Frames por segundo
duracion_img = 8  # Duración de cada imagen en segundos (más largo para apreciar mejor el efecto)

# Directorio de imágenes
directorio_imagenes = "images"  # Carpeta con las imágenes de ejemplo

def main():
    # Verificar que el directorio existe
    if not os.path.exists(directorio_imagenes):
        print(f"Error: El directorio {directorio_imagenes} no existe")
        return
    
    # Obtener lista de imágenes
    imagenes = [os.path.join(directorio_imagenes, f) for f in os.listdir(directorio_imagenes) 
               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    imagenes.sort()
    
    if not imagenes:
        print("No se encontraron imágenes en el directorio")
        return
    
    if len(imagenes) < 3:
        print("Se recomienda tener al menos 3 imágenes para probar adecuadamente los efectos")
    
    print(f"Se encontraron {len(imagenes)} imágenes")
    
    # Definir las variantes del efecto Ken Burns
    efectos = [
        {
            "nombre": "kenburns_classic",
            "descripcion": "Ken Burns Clásico (Zoom In + Pan Derecha)",
            "constructor": KenBurnsZoomInPanRight,
            "params": {}
        },
        {
            "nombre": "kenburns_reverse",
            "descripcion": "Ken Burns Inverso (Zoom Out + Pan Izquierda)",
            "constructor": KenBurnsZoomOutPanLeft,
            "params": {}
        },
        {
            "nombre": "kenburns_diagonal_in",
            "descripcion": "Ken Burns Diagonal In (Zoom In + Diagonal)",
            "constructor": KenBurnsDiagonalIn,
            "params": {}
        },
        {
            "nombre": "kenburns_diagonal_out",
            "descripcion": "Ken Burns Diagonal Out (Zoom Out + Diagonal)",
            "constructor": KenBurnsDiagonalOut,
            "params": {}
        },
        {
            "nombre": "kenburns_custom_up",
            "descripcion": "Ken Burns Hacia Arriba (Zoom In + Pan Arriba)",
            "constructor": KenBurnsEffect,
            "params": {"zoom_direction": "in", "pan_direction": "up", "zoom_ratio": 0.03, "pan_speed": 0.04}
        },
        {
            "nombre": "kenburns_custom_down",
            "descripcion": "Ken Burns Hacia Abajo (Zoom In + Pan Abajo)",
            "constructor": KenBurnsEffect,
            "params": {"zoom_direction": "in", "pan_direction": "down", "zoom_ratio": 0.03, "pan_speed": 0.04}
        },
        {
            "nombre": "kenburns_diagonal_up_left",
            "descripcion": "Ken Burns Diagonal Superior Izquierda",
            "constructor": KenBurnsEffect,
            "params": {"zoom_direction": "in", "pan_direction": "diagonal_up_left", "zoom_ratio": 0.03, "pan_speed": 0.04}
        },
        {
            "nombre": "kenburns_strong_zoom",
            "descripcion": "Ken Burns con Zoom Pronunciado",
            "constructor": KenBurnsEffect,
            "params": {"zoom_direction": "in", "pan_direction": "right", "zoom_ratio": 0.05, "pan_speed": 0.03, "zoom_emphasis": 0.7}
        }
    ]
    
    # Mostrar menú de opciones
    print("\nSelecciona qué efectos quieres probar:")
    print("0. Todos los efectos")
    for i, efecto in enumerate(efectos, 1):
        print(f"{i}. {efecto['descripcion']}")
    
    try:
        opcion = int(input("\nSelecciona una opción (0-8): "))
        if opcion < 0 or opcion > 8:
            raise ValueError("Opción fuera de rango")
    except ValueError:
        print("Opción no válida, probando solo el efecto clásico")
        opcion = 1
    
    # Determinar qué efectos probar
    efectos_a_probar = efectos if opcion == 0 else [efectos[opcion-1]]
    
    # Crear videos de prueba para cada efecto
    for efecto in efectos_a_probar:
        # Nombre del archivo de salida
        nombre_salida = f"{efecto['nombre']}.mp4"
        print(f"\nCreando video con {efecto['descripcion']}...")
        
        # Crear clips para cada imagen
        clips = []
        for imagen in imagenes[:3]:  # Limitamos a 3 imágenes para reducir tiempo
            # Cargar imagen y configurar duración
            clip = ImageClip(imagen).with_duration(duracion_img)
            
            # Redimensionar si es necesario
            if clip.size != size:
                clip = clip.resized(size)
            
            # Crear el efecto con los parámetros especificados
            effect = efecto['constructor'](**efecto['params'])
            
            # Aplicar el efecto
            clip = clip.transform(effect.apply)
            clips.append(clip)
        
        # Concatenar clips
        video = concatenate_videoclips(clips)
        
        # Guardar video
        video.write_videofile(nombre_salida, fps=fps)
        
        # Pequeña pausa para no saturar el sistema
        time.sleep(1)
    
    print("\nPruebas completadas. Videos generados:")
    for efecto in efectos_a_probar:
        print(f"- {efecto['nombre']}.mp4 - {efecto['descripcion']}")

if __name__ == "__main__":
    main()