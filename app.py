from moviepy import *
import os
from glob import glob
# Import the custom effects
from efectos import ZoomEffect
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect


def crear_video_desde_imagenes(directorio_imagenes, archivo_salida, duracion_img=6, fps=24, 
                               aplicar_efectos=True, secuencia_efectos=None,
                               aplicar_transicion=False, tipo_transicion='none', duracion_transicion=2.0,
                               aplicar_fade_in=False, duracion_fade_in=2.0,
                               aplicar_fade_out=False, duracion_fade_out=2.0,
                               aplicar_overlay=False, archivos_overlay=None, opacidad_overlay=0.5):
    """
    Crea un video a partir de imágenes en un directorio.
    
    Args:
        directorio_imagenes: Ruta a la carpeta con imágenes
        archivo_salida: Nombre del archivo de video de salida
        duracion_img: Duración en segundos de cada imagen
        fps: Frames por segundo
        aplicar_efectos: Aplicar efectos a las imágenes
        tipo_zoom: Tipo de zoom a aplicar ('in' o 'out')
        aplicar_overlay: Aplicar efecto de superposición
        archivo_overlay: Ruta al archivo de overlay
        opacidad_overlay: Opacidad del overlay (0.0 a 1.0)
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
    
    # Aplicar transiciones si se solicita
    if aplicar_transicion and tipo_transicion != 'none':
        print(f"Aplicando transición {tipo_transicion} con duración {duracion_transicion} segundos")
        video_final = TransitionEffect.apply_transition(clips, tipo_transicion, duracion_transicion)
    else:
        # Concatenar clips sin transiciones
        video_final = concatenate_videoclips(clips)
    
    # Aplicar fade in al inicio del video si se solicita
    if aplicar_fade_in and duracion_fade_in > 0:
        print(f"Aplicando fade in con duración {duracion_fade_in} segundos")
        fade_in_effect = vfx.FadeIn(duracion_fade_in)
        video_final = video_final.with_effects([fade_in_effect])  # Pasar como lista de efectos
    
    # Aplicar fade out al final del video si se solicita
    if aplicar_fade_out and duracion_fade_out > 0:
        print(f"Aplicando fade out con duración {duracion_fade_out} segundos")
        fade_out_effect = vfx.FadeOut(duracion_fade_out)
        video_final = video_final.with_effects([fade_out_effect])  # Pasar como lista de efectos
    
    # Aplicar overlay si se solicita
    if aplicar_overlay and archivos_overlay:
        # Verificar si tenemos múltiples overlays para aplicar secuencialmente a los clips
        if len(archivos_overlay) > 1 and len(clips) > 1:
            print(f"Aplicando {len(archivos_overlay)} overlays de forma secuencial a las imágenes")
            # Aplicar overlays secuencialmente antes de las transiciones
            clips = OverlayEffect.apply_sequential_overlays(clips, archivos_overlay, opacidad_overlay)
            
            # Volver a aplicar transiciones con los clips modificados
            if aplicar_transicion and tipo_transicion != 'none':
                video_final = TransitionEffect.apply_transition(clips, tipo_transicion, duracion_transicion)
            else:
                video_final = concatenate_videoclips(clips)
        else:
            # Si solo hay un overlay o un clip, aplicar el overlay al video final
            overlay_path = archivos_overlay[0]
            print(f"Aplicando overlay {os.path.basename(overlay_path)} con opacidad {opacidad_overlay}")
            video_final = OverlayEffect.apply_overlay(video_final, overlay_path, opacidad_overlay)
    
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
    
    duracion = float(input("Duración de cada imagen en segundos (por defecto 6): ") or 6)
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
    
    # Opciones de transición
    aplicar_transicion = input("¿Aplicar transiciones entre imágenes? (s/n): ").lower() == 's'
    
    tipo_transicion = 'none'
    duracion_transicion = 2.0
    
    if aplicar_transicion:
        # Mostrar transiciones disponibles
        transiciones_disponibles = TransitionEffect.get_available_transitions()
        print("\nTransiciones disponibles:")
        for i, trans in enumerate(transiciones_disponibles):
            print(f"{i+1}. {trans}")
        
        # Seleccionar tipo de transición
        seleccion = input(f"Selecciona una transición (1-{len(transiciones_disponibles)}): ")
        try:
            indice = int(seleccion) - 1
            if 0 <= indice < len(transiciones_disponibles):
                tipo_transicion = transiciones_disponibles[indice]
            else:
                print("Selección inválida, usando 'none' por defecto")
                tipo_transicion = 'none'
        except ValueError:
            print("Entrada inválida, usando 'none' por defecto")
            tipo_transicion = 'none'
        
        # Duración de la transición
        if tipo_transicion != 'none':
            try:
                duracion_transicion = float(input("Duración de la transición en segundos (por defecto 2.0): ") or 2.0)
                if duracion_transicion <= 0:
                    print("La duración debe ser mayor que 0, usando 2.0 por defecto")
                    duracion_transicion = 2.0
            except ValueError:
                print("Entrada inválida, usando duración 2.0 por defecto")
                duracion_transicion = 2.0
    
    # Opciones de fade in/out
    aplicar_fade_in = input("¿Aplicar efecto de fade in al inicio del video? (s/n): ").lower() == 's'
    duracion_fade_in = 1.0
    if aplicar_fade_in:
        try:
            duracion_fade_in = float(input("Duración del fade in en segundos (por defecto 1.0): ") or 1.0)
            if duracion_fade_in <= 0:
                print("La duración debe ser mayor que 0, usando 2.0 por defecto")
                duracion_fade_in = 2.0
        except ValueError:
            print("Entrada inválida, usando duración 2.0 por defecto")
            duracion_fade_in = 2.0
    
    aplicar_fade_out = input("¿Aplicar efecto de fade out al final del video? (s/n): ").lower() == 's'
    duracion_fade_out = 2.0
    if aplicar_fade_out:
        try:
            duracion_fade_out = float(input("Duración del fade out en segundos (por defecto 1.0): ") or 1.0)
            if duracion_fade_out <= 0:
                print("La duración debe ser mayor que 0, usando 2.0 por defecto")
                duracion_fade_out = 2.0
        except ValueError:
            print("Entrada inválida, usando duración 2.0 por defecto")
            duracion_fade_out = 2.0
    
    # Opciones de overlay
    aplicar_overlay = input("¿Aplicar efecto de overlay (como nieve, lluvia, etc.)? (s/n): ").lower() == 's'
    archivos_overlay = []
    opacidad_overlay = 0.5
    
    if aplicar_overlay:
        # Directorio de overlays
        overlay_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlays')
        
        # Verificar si existen overlays
        overlays_disponibles = OverlayEffect.get_available_overlays(overlay_dir)
        
        if not overlays_disponibles:
            print("\nNo se encontraron archivos de overlay en la carpeta 'overlays'.")
            print("Coloca archivos de video (.mp4, .mov, .avi, .webm) en la carpeta 'overlays' para usar esta función.")
            aplicar_overlay = False
        else:
            print("\nOverlays disponibles:")
            for i, overlay in enumerate(overlays_disponibles):
                print(f"{i+1}. {overlay}")
            
            # Seleccionar múltiples overlays
            print("\nPuedes seleccionar múltiples overlays para aplicarlos secuencialmente a las imágenes.")
            print("Ejemplo: 1,3,2 (separados por comas)")
            seleccion = input(f"Selecciona los overlays (1-{len(overlays_disponibles)}): ")
            
            try:
                # Procesar la selección de múltiples overlays
                indices = [int(idx.strip()) - 1 for idx in seleccion.split(',')]
                
                # Validar cada índice y agregar los overlays válidos
                for indice in indices:
                    if 0 <= indice < len(overlays_disponibles):
                        ruta_overlay = os.path.join(overlay_dir, overlays_disponibles[indice])
                        archivos_overlay.append(ruta_overlay)
                    else:
                        print(f"Índice {indice+1} inválido, ignorando esta selección")
                
                # Verificar si se seleccionó al menos un overlay válido
                if not archivos_overlay:
                    print("No se seleccionaron overlays válidos, no se aplicará overlay")
                    aplicar_overlay = False
                else:
                    print(f"Se aplicarán {len(archivos_overlay)} overlays de forma secuencial")
            except ValueError:
                print("Entrada inválida, no se aplicará overlay")
                aplicar_overlay = False
            
            # Opacidad del overlay
            if aplicar_overlay:
                try:
                    opacidad_overlay = float(input("Opacidad del overlay (0.1-1.0, por defecto 0.5): ") or 0.5)
                    if opacidad_overlay < 0.1 or opacidad_overlay > 1.0:
                        print("La opacidad debe estar entre 0.1 y 1.0, usando 0.5 por defecto")
                        opacidad_overlay = 0.5
                except ValueError:
                    print("Entrada inválida, usando opacidad 0.5 por defecto")
                    opacidad_overlay = 0.5
    
    crear_video_desde_imagenes(directorio, salida, duracion, fps, efectos, secuencia_efectos,
                              aplicar_transicion, tipo_transicion, duracion_transicion,
                              aplicar_fade_in, duracion_fade_in, aplicar_fade_out, duracion_fade_out,
                              aplicar_overlay, archivos_overlay, opacidad_overlay)

if __name__ == "__main__":
    main()