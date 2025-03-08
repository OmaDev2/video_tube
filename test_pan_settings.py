#!/usr/bin/env python3
"""
Script para probar rápidamente diferentes configuraciones de scale_factor
específicamente para los efectos de paneo que mostraban bandas negras.

Este script creará cuatro videos, cada uno con un valor diferente de scale_factor,
para que puedas comparar y elegir la mejor configuración para tus imágenes.
"""

from moviepy import *
from efectos import PanUpEffect, PanDownEffect, PanLeftEffect, PanRightEffect
import os
import time

# Configuración básica
size = (1280, 720)  # Tamaño del video (HD)
fps = 24  # Frames por segundo
duracion_img = 5  # Duración de cada imagen en segundos

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
    
    print(f"Se encontraron {len(imagenes)} imágenes")
    
    # Seleccionar una imagen para la prueba (usando la primera)
    imagen_prueba = imagenes[0]
    print(f"Usando la imagen {os.path.basename(imagen_prueba)} para las pruebas")
    
    # Valores de scale_factor para probar
    scale_factors = [1.2, 1.3, 1.4, 1.5]
    
    # Seleccionar el efecto a probar
    print("\nSelecciona el efecto de paneo a probar:")
    print("1. Pan Up (movimiento hacia arriba)")
    print("2. Pan Down (movimiento hacia abajo)")
    print("3. Pan Left (movimiento hacia la izquierda)")
    print("4. Pan Right (movimiento hacia la derecha)")
    
    try:
        opcion = int(input("\nSelecciona un efecto (1-4): "))
        if opcion < 1 or opcion > 4:
            raise ValueError("Opción fuera de rango")
    except ValueError:
        print("Opción no válida, usando Pan Up por defecto")
        opcion = 1
    
    # Mapear opción a efecto
    efectos = {
        1: ("pan_up", PanUpEffect),
        2: ("pan_down", PanDownEffect),
        3: ("pan_left", PanLeftEffect),
        4: ("pan_right", PanRightEffect)
    }
    
    nombre_efecto, clase_efecto = efectos[opcion]
    print(f"\nCreando videos de prueba para el efecto {nombre_efecto}...")
    
    # Crear videos de prueba para cada valor de scale_factor
    for sf in scale_factors:
        # Nombre del archivo de salida
        nombre_salida = f"{nombre_efecto}_scale_{sf:.1f}.mp4"
        
        # Cargar la imagen y configurar duración
        clip = ImageClip(imagen_prueba).with_duration(duracion_img)
        
        # Redimensionar si es necesario
        if clip.size != size:
            clip = clip.resized(size)
        
        # Aplicar el efecto con el scale_factor específico
        effect = clase_efecto(speed=0.05, scale_factor=sf)
        clip = clip.transform(effect.apply)
        
        # Guardar video
        print(f"Creando {nombre_salida} con scale_factor={sf}")
        clip.write_videofile(nombre_salida, fps=fps)
        
        # Pequeña pausa para no saturar el sistema
        time.sleep(1)
    
    print("\nPruebas completadas. Se han creado los siguientes videos:")
    for sf in scale_factors:
        print(f"- {nombre_efecto}_scale_{sf:.1f}.mp4")
    
    print("\nRevisa estos videos para determinar qué valor de scale_factor funciona mejor para tus imágenes.")
    print("Una vez que lo hayas determinado, puedes usar ese valor en tu aplicación principal.")

if __name__ == "__main__":
    main()