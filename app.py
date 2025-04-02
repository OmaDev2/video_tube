from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, vfx
# Updated import for MoviePy 2.0+
from moviepy.audio import fx as afx
import os
from glob import glob
# Import the custom effects
from efectos import ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, FlipEffect, PanRightEffect, KenBurnsEffect, VignetteZoomEffect, RotateEffect
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect
from subtitles import SubtitleEffect


def crear_video_desde_imagenes(directorio_imagenes, archivo_salida, duracion_img=6, fps=24, 
                               aplicar_efectos=True, secuencia_efectos=None,
                               aplicar_transicion=False, tipo_transicion='none', duracion_transicion=2.0,
                               aplicar_fade_in=False, duracion_fade_in=2.0,
                               aplicar_fade_out=False, duracion_fade_out=2.0,
                               aplicar_overlay=False, archivos_overlay=None, opacidad_overlay=0.3,
                               aplicar_musica=False, archivo_musica=None, volumen_musica=1.0,
                               aplicar_fade_in_musica=False, duracion_fade_in_musica=2.0,
                               aplicar_fade_out_musica=False, duracion_fade_out_musica=2.0,
                               aplicar_voz=False, archivo_voz=None, volumen_voz=1.0,
                               aplicar_fade_in_voz=False, duracion_fade_in_voz=1.0,
                               aplicar_fade_out_voz=False, duracion_fade_out_voz=1.0,
                               aplicar_subtitulos=False, archivo_subtitulos=None, 
                               tamano_fuente_subtitulos=24, color_fuente_subtitulos='white',
                               color_borde_subtitulos='black', grosor_borde_subtitulos=1,
                               progress_callback=None, settings=None):
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
        settings: Diccionario con ajustes personalizados para los efectos
    """
    # Usar ajustes por defecto si no se proporcionan
    if settings is None:
        settings = {
            'zoom_ratio': 0.5,
            'zoom_quality': 'high',
            'pan_scale_factor': 1.2,
            'pan_easing': True,
            'pan_quality': 'high',
            'kb_zoom_ratio': 0.3,
            'kb_scale_factor': 1.3,
            'kb_quality': 'high',
            'kb_direction': 'random'
        }
    
    # Obtener lista de archivos de imagen
    formatos = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    archivos = []
    for formato in formatos:
        archivos.extend(glob(os.path.join(directorio_imagenes, formato)))
    
    # Ordenar archivos por el número que aparece al final del nombre
    def extraer_numero(archivo):
        # Extraer el nombre base del archivo sin la ruta ni la extensión
        nombre_base = os.path.basename(archivo)
        # Buscar el último número en el nombre del archivo
        import re
        match = re.search(r'_(\d+)\.', nombre_base)
        if match:
            return int(match.group(1))  # Convertir a entero para ordenar numéricamente
        return 0  # Si no hay número, devolver 0
    
    # Ordenar los archivos por el número extraído
    archivos.sort(key=extraer_numero)
    
    # Imprimir los nombres de los archivos ordenados para depuración
    print("Orden de archivos:")
    for archivo in archivos:
        print(f"  - {os.path.basename(archivo)}")
    
    if not archivos:
        print(f"No se encontraron imágenes en {directorio_imagenes}")
        return
    
    print(f"Se encontraron {len(archivos)} imágenes")
    
    # Crear clips de imagen
    clips = []
    total_imagenes = len(archivos)
    for i, archivo in enumerate(archivos):
        clip = ImageClip(archivo).with_duration(duracion_img)
        
        # Aplicar efectos si se solicita
        if aplicar_efectos and secuencia_efectos:
            # Obtener el efecto para este clip según la secuencia
            # Si hay menos efectos que clips, se repite la secuencia
            efecto_idx = i % len(secuencia_efectos)
            tipo_efecto = secuencia_efectos[efecto_idx]
            print(f"DEBUG: Procesando imagen {i+1}, tipo_efecto = '{tipo_efecto}'") 
            effect = None# Mantenemos el debug
            
            # Aplicar el efecto correspondiente
            if tipo_efecto.lower() == 'in':
                # Usar los ajustes personalizados para el zoom
                zoom_ratio = settings.get('zoom_ratio', 0.5)
                zoom_quality = settings.get('zoom_quality', 'high')
                effect = ZoomEffect(zoom_in=True, ratio=zoom_ratio, clip_duration=duracion_img, quality=zoom_quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto zoom in a la imagen {i+1} (ratio={zoom_ratio}, quality={zoom_quality})")
            elif tipo_efecto.lower() == 'out':
                # Usar los ajustes personalizados para el zoom
                zoom_ratio = settings.get('zoom_ratio', 0.5)
                zoom_quality = settings.get('zoom_quality', 'high')
                effect = ZoomEffect(zoom_in=False, ratio=zoom_ratio, clip_duration=duracion_img, quality=zoom_quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto zoom out a la imagen {i+1} (ratio={zoom_ratio}, quality={zoom_quality})")
            elif tipo_efecto.lower() == 'panup':
                # Usar los ajustes personalizados para el pan
                scale_factor = settings.get('pan_scale_factor', 1.2)
                easing = settings.get('pan_easing', True)
                quality = settings.get('pan_quality', 'high')
                effect = PanUpEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto pan up a la imagen {i+1} (scale_factor={scale_factor}, easing={easing})")
            elif tipo_efecto.lower() == 'pandown':
                # Usar los ajustes personalizados para el pan
                scale_factor = settings.get('pan_scale_factor', 1.2)
                easing = settings.get('pan_easing', True)
                quality = settings.get('pan_quality', 'high')
                effect = PanDownEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto pan down a la imagen {i+1} (scale_factor={scale_factor}, easing={easing})")
            elif tipo_efecto.lower() == 'panleft':
                # Usar los ajustes personalizados para el pan
                scale_factor = settings.get('pan_scale_factor', 1.2)
                easing = settings.get('pan_easing', True)
                quality = settings.get('pan_quality', 'high')
                effect = PanLeftEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto pan left a la imagen {i+1} (scale_factor={scale_factor}, easing={easing})")
            elif tipo_efecto.lower() == 'panright':
                # Usar los ajustes personalizados para el pan
                scale_factor = settings.get('pan_scale_factor', 1.2)
                easing = settings.get('pan_easing', True)
                quality = settings.get('pan_quality', 'high')
                effect = PanRightEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto pan right a la imagen {i+1} (scale_factor={scale_factor}, easing={easing})")
            elif tipo_efecto.lower() == 'kenburns':
                # Usar los ajustes personalizados para Ken Burns
                zoom_ratio = settings.get('kb_zoom_ratio', 0.3)
                scale_factor = settings.get('kb_scale_factor', 1.3)
                quality = settings.get('kb_quality', 'high')
                direction = settings.get('kb_direction', 'random')
                
                # Determinar las direcciones basadas en el ajuste
                if direction == 'random':
                    import random
                    zoom_dir = random.choice(['in', 'out'])
                    pan_dir = random.choice(['up', 'down', 'left', 'right'])
                else:
                    zoom_dir = 'in'  # Por defecto
                    pan_dir = direction
                
                effect = KenBurnsEffect(zoom_direction=zoom_dir, pan_direction=pan_dir, 
                                       clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                       scale_factor=scale_factor, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto Ken Burns a la imagen {i+1} (zoom_ratio={zoom_ratio}, scale_factor={scale_factor}, direction={direction})")
            elif tipo_efecto.lower() == 'kenburns1':
                # Variante 1: zoom in con pan left
                zoom_ratio = settings.get('kb_zoom_ratio', 0.3)
                scale_factor = settings.get('kb_scale_factor', 1.3)
                quality = settings.get('kb_quality', 'high')
                effect = KenBurnsEffect(zoom_direction='in', pan_direction='left', 
                                       clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                       scale_factor=scale_factor, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto Ken Burns (variante 1) a la imagen {i+1}")
            elif tipo_efecto.lower() == 'kenburns2':
                # Variante 2: zoom out con pan right
                zoom_ratio = settings.get('kb_zoom_ratio', 0.3)
                scale_factor = settings.get('kb_scale_factor', 1.3)
                quality = settings.get('kb_quality', 'high')
                effect = KenBurnsEffect(zoom_direction='out', pan_direction='right', 
                                       clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                       scale_factor=scale_factor, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto Ken Burns (variante 2) a la imagen {i+1}")
            elif tipo_efecto.lower() == 'kenburns3':
                # Variante 3: zoom out con pan down
                zoom_ratio = settings.get('kb_zoom_ratio', 0.3)
                scale_factor = settings.get('kb_scale_factor', 1.3)
                quality = settings.get('kb_quality', 'high')
                effect = KenBurnsEffect(zoom_direction='out', pan_direction='down', 
                                       clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                       scale_factor=scale_factor, quality=quality)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto Ken Burns (variante 3) a la imagen {i+1}")
            
            elif tipo_efecto.lower() == 'flip_horizontal':
                 effect = FlipEffect(direction='horizontal')
                # Nota: FlipEffect no necesita clip_duration
                 if effect:
                    clip = clip.transform(effect.apply)
                    print(f"Aplicando efecto flip_horizontal a la imagen {i+1}")

            elif tipo_efecto.lower() == 'flip_vertical':
                 effect = FlipEffect(direction='vertical')
    # Nota: FlipEffect no necesita clip_duration
                 if effect:
                    clip = clip.transform(effect.apply)
                    print(f"Aplicando efecto flip_vertical a la imagen {i+1}")
            
            elif tipo_efecto.lower() == 'vignette_zoom_in':
                effect = VignetteZoomEffect(zoom_in=True, zoom_ratio=0.05,
                                 vignette_strength=0.7, vignette_radius=0.8,
                                 vignette_fade_duration=2.0, clip_duration=duracion_img)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto vignette_zoom_in a la imagen {i+1}")
                
            elif tipo_efecto.lower() == 'vignette_zoom_out':
                effect = VignetteZoomEffect(zoom_in=False, zoom_ratio=0.05,
                                 vignette_strength=0.7, vignette_radius=0.8,
                                 vignette_fade_duration=2.0, clip_duration=duracion_img)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto vignette_zoom_out a la imagen {i+1}")
            
            elif tipo_efecto.lower() == 'rotate_clockwise':
                effect = RotateEffect(speed=30, direction='clockwise', clip_duration=duracion_img)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto de rotación en sentido horario a la imagen {i+1}")
                
            elif tipo_efecto.lower() == 'rotate_counter_clockwise':
                effect = RotateEffect(speed=30, direction='counter-clockwise', clip_duration=duracion_img)
                clip = clip.transform(effect.apply)
                print(f"Aplicando efecto de rotación en sentido antihorario a la imagen {i+1}")
            
            elif effect is None:
                print(f"Tipo de efecto desconocido: {tipo_efecto}")
        
        clips.append(clip)
        
        
        
        # Actualizar progreso si hay un callback definido
        if progress_callback:
            progress_callback(1, total_imagenes)
    
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
        print(f"Aplicando overlays: {archivos_overlay}")
        # Verificar si tenemos múltiples overlays para aplicar secuencialmente a los clips
        if len(archivos_overlay) > 1:
            # Guardar los clips originales antes de aplicar transiciones
            clips_originales = clips.copy()
            
            print(f"Aplicando {len(archivos_overlay)} overlays de forma secuencial a las imágenes")
            # Aplicar overlays secuencialmente antes de las transiciones
            clips_con_overlay = OverlayEffect.apply_sequential_overlays(clips_originales, archivos_overlay, opacidad_overlay)
            
            # Volver a aplicar transiciones con los clips modificados
            if aplicar_transicion and tipo_transicion != 'none':
                video_final = TransitionEffect.apply_transition(clips_con_overlay, tipo_transicion, duracion_transicion)
            else:
                video_final = concatenate_videoclips(clips_con_overlay)
        else:
            # Si solo hay un overlay, aplicar el overlay al video final
            overlay_path = archivos_overlay[0]
            print(f"Aplicando overlay {os.path.basename(overlay_path)} con opacidad {opacidad_overlay}")
            video_final = OverlayEffect.apply_overlay(video_final, overlay_path, opacidad_overlay)
    else:
        if aplicar_overlay:
            print("Se seleccionó aplicar overlay pero no se proporcionaron archivos de overlay")
        else:
            print("No se seleccionó aplicar overlay")
    
    # Aplicar audio (música de fondo y/o voz en off)
    audio_clips = []
    
    # Aplicar voz en off primero si se solicita
    if aplicar_voz and archivo_voz and os.path.exists(archivo_voz):
        print(f"Aplicando voz en off: {os.path.basename(archivo_voz)}")
        voz = AudioFileClip(archivo_voz)
        
        # Ajustar la duración de la voz a la duración del video si es necesario
        if voz.duration > video_final.duration:
            voz = voz.subclipped(0, video_final.duration)
        
        # Ajustar el volumen
        voz = voz.with_effects([afx.MultiplyVolume(volumen_voz)])
        
        # Aplicar fade in/out a la voz si se solicita
        if aplicar_fade_in_voz and duracion_fade_in_voz > 0:
            print(f"Aplicando fade in a la voz con duración {duracion_fade_in_voz} segundos")
            voz = voz.with_effects([afx.AudioFadeIn(duracion_fade_in_voz)])
        
        if aplicar_fade_out_voz and duracion_fade_out_voz > 0:
            print(f"Aplicando fade out a la voz con duración {duracion_fade_out_voz} segundos")
            voz = voz.with_effects([afx.AudioFadeOut(duracion_fade_out_voz)])
        
        audio_clips.append(voz)
    
    # Aplicar música de fondo después si se solicita
    if aplicar_musica and archivo_musica and os.path.exists(archivo_musica):
        print(f"Aplicando música de fondo: {os.path.basename(archivo_musica)}")
        musica = AudioFileClip(archivo_musica)
        
        # Ajustar la duración de la música a la duración del video
        if musica.duration > video_final.duration:
            musica = musica.subclipped(0, video_final.duration)
        else:
            # Si la música es más corta que el video, repetirla hasta cubrir todo el video
            from moviepy.audio.AudioClip import concatenate_audioclips
            repeticiones = int(video_final.duration / musica.duration) + 1
            musica = concatenate_audioclips([musica] * repeticiones).subclipped(0, video_final.duration)
        
        # Ajustar el volumen
        musica = musica.with_effects([afx.MultiplyVolume(volumen_musica)])
        
        # Aplicar fade in/out a la música si se solicita
        if aplicar_fade_in_musica and duracion_fade_in_musica > 0:
            print(f"Aplicando fade in a la música con duración {duracion_fade_in_musica} segundos")
            musica = musica.with_effects([afx.AudioFadeIn(duracion_fade_in_musica)])
        
        if aplicar_fade_out_musica and duracion_fade_out_musica > 0:
            print(f"Aplicando fade out a la música con duración {duracion_fade_out_musica} segundos")
            musica = musica.with_effects([afx.AudioFadeOut(duracion_fade_out_musica)])
        
        audio_clips.append(musica)
    
    # Combinar los clips de audio y aplicarlos al video
    if audio_clips:
        if len(audio_clips) == 1:
            # Si solo hay un clip de audio, usarlo directamente
            video_final = video_final.with_audio(audio_clips[0])
        else:
            # Si hay múltiples clips de audio, mezclarlos
            from moviepy.audio.AudioClip import CompositeAudioClip
            audio_final = CompositeAudioClip(audio_clips)
            video_final = video_final.with_audio(audio_final)
    
    # Aplicar subtítulos si se solicita
    if aplicar_subtitulos and archivo_subtitulos and os.path.exists(archivo_subtitulos):
        print(f"Aplicando subtítulos: {os.path.basename(archivo_subtitulos)}")
        try:
            # Parsear el archivo de subtítulos
            subtitulos = SubtitleEffect.parse_srt_file(archivo_subtitulos)
            
            # Aplicar los subtítulos al video
            video_final = SubtitleEffect.apply_subtitles(
                video_final,
                subtitulos,
                font_size=tamano_fuente_subtitulos,
                font_color=color_fuente_subtitulos,
                stroke_color=color_borde_subtitulos,
                stroke_width=grosor_borde_subtitulos,
                position=('center', 'bottom')
            )
            print(f"Se aplicaron {len(subtitulos)} subtítulos al video")
        except Exception as e:
            print(f"Error al aplicar subtítulos: {str(e)}")
    
    # Guardar el video
    video_final.write_videofile(archivo_salida, fps=fps)
    print(f"Video guardado como {archivo_salida}")
    
    # Indicar que el proceso ha terminado (100% completado)
    if progress_callback:
        progress_callback(0, 1)  # Asegurar que la barra llegue al 100%

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
        print("\nOpciones de efectos:")
        print("1. Un solo tipo de efecto")
        print("2. Secuencia personalizada")
        print("3. Alternar automáticamente (in/out)")
        print("4. Secuencia Ken Burns")
        
        opciones = input("Elige una opción (1-4): ")
        
        if opciones == "4":
            # Secuencia Ken Burns predefinida
            secuencia_efectos = ['kenburns', 'kenburns1', 'kenburns2', 'kenburns3']
            print("Se aplicará una secuencia de efectos Ken Burns")
        elif opciones == "3":
            # Modo alternado automático: alternar entre in y out
            secuencia_efectos = ['in', 'out']
            print("Se aplicarán efectos alternando automáticamente entre zoom in y zoom out")
        elif opciones == "2":
            # Modo secuencia personalizada
            print("\nDefinir secuencia de efectos:")
            print("Opciones disponibles: in, out, panup, pandown, panleft, panright, kenburns")
            print("Ejemplo: in,panup,kenburns,out (separados por comas)")
            secuencia_input = input("Secuencia de efectos: ")
            secuencia_efectos = [efecto.strip() for efecto in secuencia_input.split(',')]
            
            # Validar cada efecto en la secuencia (permitir todos los efectos válidos)
            efectos_validos = ['in', 'out', 'panup', 'pandown', 'panleft', 'panright', 'kenburns', 'kenburns1', 'kenburns2', 'kenburns3']
            secuencia_efectos = [efecto if efecto in efectos_validos else 'in' for efecto in secuencia_efectos]
            
            if not secuencia_efectos:
                secuencia_efectos = ['in']  # Valor por defecto si la secuencia está vacía
        else:
            # Modo un solo tipo de efecto
            print("\nTipo de efecto:")
            print("1. Zoom In (acercamiento)")
            print("2. Zoom Out (alejamiento)")
            print("3. Pan Up (movimiento hacia arriba)")
            print("4. Pan Down (movimiento hacia abajo)")
            print("5. Pan Left (movimiento hacia la izquierda)")
            print("6. Pan Right (movimiento hacia la derecha)")
            print("7. Ken Burns (efecto cinematográfico combinado)")
            
            tipo_efecto_num = input("Elige un efecto (1-7): ")
            
            # Mapear el número al tipo de efecto
            tipo_efecto_map = {
                '1': 'in',
                '2': 'out',
                '3': 'panup',
                '4': 'pandown',
                '5': 'panleft',
                '6': 'panright',
                '7': 'kenburns'
            }
            
            tipo_efecto = tipo_efecto_map.get(tipo_efecto_num, 'in')  # Valor por defecto: 'in'
            secuencia_efectos = [tipo_efecto]
    
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