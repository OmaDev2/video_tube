from moviepy import *
import os
from glob import glob
# Import the custom effects
from efectos import ZoomEffect

def crear_video_desde_imagenes(directorio_imagenes, archivo_salida, duracion_img=2, fps=24, 
                               aplicar_efectos=True, tipo_zoom='in'):
    """
    Crea un video a partir de imágenes en un directorio.
    
    Args:
        directorio_imagenes: Ruta a la carpeta con imágenes
        archivo_salida: Nombre del archivo de video de salida
        duracion_img: Duración en segundos de cada imagen
        fps: Frames por segundo
        aplicar_efectos: Aplicar efectos a las imágenes
        tipo_zoom: Tipo de zoom a aplicar ('in' o 'out')
    """
    # Obtener lista de archivos de imagen
    formatos = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    archivos = []
    for formato in formatos:
        archivos.extend(glob(os.path.join(directorio_imagenes, formato)))
    
    archivos.sort()  # Ordenar archivos alfabéticamente
    
    if not archivos:
        print(f"No se encontraron imágenes en {directorio_imagenes}")
        return
    
    print(f"Se encontraron {len(archivos)} imágenes")
    
    # Crear clips de imagen
    clips = []
    for archivo in archivos:
        clip = ImageClip(archivo).with_duration(duracion_img)
        
        # Aplicar efectos si se solicita
        if aplicar_efectos:
            # Determinar si es zoom in o zoom out
            zoom_in = tipo_zoom.lower() == 'in'
            
            # Aplicar efecto de zoom
            effect = ZoomEffect(zoom_in=zoom_in, ratio=0.04)
            clip = clip.transform(effect.apply)
        
        clips.append(clip)
    
    # Concatenar clips sin transiciones
    video_final = concatenate_videoclips(clips)
    
    # Guardar el video
    video_final.write_videofile(archivo_salida, fps=fps)
    print(f"Video guardado como {archivo_salida}")

def main():
    print("=== Convertidor de Imágenes a Video con Efecto Zoom ===")
    directorio = input("Ingresa la ruta de la carpeta con imágenes: ")
    if not os.path.exists(directorio):
        print("¡La carpeta no existe!")
        return
    
    salida = input("Nombre del archivo de salida (con extensión .mp4): ")
    if not salida.endswith('.mp4'):
        salida += '.mp4'
    
    duracion = float(input("Duración de cada imagen en segundos (por defecto 2): ") or 2)
    fps = int(input("Frames por segundo (por defecto 24): ") or 24)
    
    efectos = input("¿Aplicar efectos de zoom? (s/n): ").lower() == 's'
    
    if efectos:
        tipo_zoom = input("Tipo de zoom (in/out): ").lower()
        if tipo_zoom not in ['in', 'out']:
            tipo_zoom = 'in'  # Valor por defecto
    else:
        tipo_zoom = 'in'  # Valor por defecto aunque no se use
    
    crear_video_desde_imagenes(directorio, salida, duracion, fps, efectos, tipo_zoom)

if __name__ == "__main__":
    main()