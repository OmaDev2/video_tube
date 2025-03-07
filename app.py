from moviepy import *
import os
from glob import glob
# Import the custom effects
from efectos import ZoomEffect

def crear_video_desde_imagenes(directorio_imagenes, archivo_salida, duracion_img=2, fps=24, 
                               aplicar_efectos=True, secuencia_efectos=None):
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
    for i, archivo in enumerate(archivos):
        clip = ImageClip(archivo).with_duration(duracion_img)
        
        # Aplicar efectos si se solicita
        if aplicar_efectos and secuencia_efectos:
            # Obtener el efecto para este clip según la secuencia
            # Si hay menos efectos que clips, se repite la secuencia
            efecto_idx = i % len(secuencia_efectos)
            tipo_efecto = secuencia_efectos[efecto_idx]
            
            # Determinar si es zoom in o zoom out
            zoom_in = tipo_efecto.lower() == 'in'
            
            # Aplicar efecto de zoom
            effect = ZoomEffect(zoom_in=zoom_in, ratio=0.04)
            clip = clip.transform(effect.apply)
            
            print(f"Aplicando efecto {tipo_efecto} a la imagen {i+1}")
        
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
    
    secuencia_efectos = None
    if efectos:
        opciones = input("Opciones de efectos:\n1. Un solo tipo de efecto\n2. Secuencia personalizada\n3. Alternar automáticamente (in/out)\nElige una opción (1-3): ")
        
        if opciones == "3":
            # Modo alternado automático: alternar entre in y out
            secuencia_efectos = ['in', 'out']
            print("Se aplicarán efectos alternando automáticamente entre zoom in y zoom out")
        elif opciones == "2":
            # Modo secuencia personalizada
            print("\nDefinir secuencia de efectos:")
            print("Ejemplo: in,out,in (separados por comas)")
            secuencia_input = input("Secuencia de efectos: ")
            secuencia_efectos = [efecto.strip() for efecto in secuencia_input.split(',')]
            
            # Validar cada efecto en la secuencia
            secuencia_efectos = [efecto if efecto in ['in', 'out'] else 'in' for efecto in secuencia_efectos]
            
            if not secuencia_efectos:
                secuencia_efectos = ['in']  # Valor por defecto si la secuencia está vacía
        else:
            # Modo un solo tipo: un solo tipo de efecto para todos los clips
            tipo_zoom = input("Tipo de zoom (in/out): ").lower()
            if tipo_zoom not in ['in', 'out']:
                tipo_zoom = 'in'  # Valor por defecto
            secuencia_efectos = [tipo_zoom]
    
    crear_video_desde_imagenes(directorio, salida, duracion, fps, efectos, secuencia_efectos)

if __name__ == "__main__":
    main()