#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal para la generación de videos a partir de imágenes.
"""

from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, 
    CompositeVideoClip, vfx
)
from moviepy.audio import fx as afx
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip

import os
import re
from glob import glob
from pathlib import Path
import traceback

# Importar efectos personalizados
from efectos import (
    ZoomEffect, PanUpEffect, PanDownEffect, PanLeftEffect, 
    FlipEffect, PanRightEffect, KenBurnsEffect, 
    VignetteZoomEffect, RotateEffect
)
from transiciones import TransitionEffect
from overlay_effects import OverlayEffect
from subtitles import SubtitleEffect

class VideoGenerator:
    """
    Clase para generar videos a partir de imágenes con efectos, transiciones, audio y subtítulos.
    """
    
    def __init__(self, project_folder, settings=None):
        """
        Inicializa el generador de videos.
        
        Args:
            project_folder: Ruta a la carpeta del proyecto
            settings: Configuración personalizada para los efectos
        """
        self.project_folder = Path(project_folder)
        self.image_folder = self.project_folder / "imagenes"
        self.output_filename_base = self.project_folder.name
        self.output_video_path = self.project_folder / f"{self.output_filename_base}_final.mp4"
        
        # Cargar configuración desde settings.json si existe
        settings_path = self.project_folder / "settings.json"
        if settings_path.exists():
            import json
            with open(settings_path, 'r') as f:
                settings_data = json.load(f)
                # Usar configuración personalizada si se proporciona, sino usar la predeterminada
                self.settings = settings or settings_data.get('default_effects', {
                    'zoom_ratio': 0.5,
                    'zoom_quality': 'high',
                    'pan_scale_factor': 1.2,
                    'pan_easing': True,
                    'pan_quality': 'high',
                    'kb_zoom_ratio': 0.3,
                    'kb_scale_factor': 1.3,
                    'kb_quality': 'high',
                    'kb_direction': 'random'
                })
        else:
            # Configuración por defecto
            self.settings = settings or {
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
        
        # Imágenes encontradas
        self.image_files = []
        
        # Progreso de generación
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """
        Establece la función de callback para reportar el progreso.
        
        Args:
            callback: Función que recibe (current_step, total_steps)
        """
        self.progress_callback = callback
    
    def find_images(self):
        """
        Busca imágenes en la carpeta del proyecto.
        
        Returns:
            bool: True si encontró imágenes, False en caso contrario
        """
        # Verificar si existe la carpeta de imágenes
        if not self.image_folder.is_dir():
            print(f"ERROR: No se encontró la subcarpeta de imágenes: {self.image_folder}")
            print("Por favor, crea la carpeta 'imagenes' dentro de la carpeta del proyecto y añade imágenes.")
            return False
        
        # Obtener lista de archivos de imagen
        self.image_files = []
        formatos = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        for formato in formatos:
            self.image_files.extend(glob(str(self.image_folder / formato)))
        
        # Ordenar archivos por el número que aparece al final del nombre
        self.image_files.sort(key=self._extract_number)
        
        # Imprimir los nombres de los archivos ordenados para depuración
        print("Orden de archivos:")
        for archivo in self.image_files:
            print(f"  - {os.path.basename(archivo)}")
        
        if not self.image_files:
            print(f"No se encontraron imágenes en {self.image_folder}")
            return False
        
        print(f"Se encontraron {len(self.image_files)} imágenes")
        return True
    
    def generate_video(self, **kwargs):
        """
        Genera un video con las imágenes encontradas.
        
        Args:
            **kwargs: Argumentos de configuración para la generación del video
            
        Returns:
            str: Ruta al video generado, o None si hubo un error
        """
        if not self.find_images():
            return None
        
        # Extraer parámetros o usar valores por defecto
        duracion_img = kwargs.get('duracion_img', 6)
        fps = kwargs.get('fps', 24)
        aplicar_efectos = kwargs.get('aplicar_efectos', True)
        secuencia_efectos = kwargs.get('secuencia_efectos', None)
        aplicar_transicion = kwargs.get('aplicar_transicion', False)
        tipo_transicion = kwargs.get('tipo_transicion', 'none')
        duracion_transicion = kwargs.get('duracion_transicion', 2.0)
        aplicar_fade_in = kwargs.get('aplicar_fade_in', False)
        duracion_fade_in = kwargs.get('duracion_fade_in', 2.0)
        aplicar_fade_out = kwargs.get('aplicar_fade_out', False)
        duracion_fade_out = kwargs.get('duracion_fade_out', 2.0)
        aplicar_overlay = kwargs.get('aplicar_overlay', False)
        archivos_overlay = kwargs.get('archivos_overlay', None)
        opacidad_overlay = kwargs.get('opacidad_overlay', 0.3)
        aplicar_musica = kwargs.get('aplicar_musica', False)
        archivo_musica = kwargs.get('archivo_musica', None)
        volumen_musica = kwargs.get('volumen_musica', 1.0)
        aplicar_fade_in_musica = kwargs.get('aplicar_fade_in_musica', False)
        duracion_fade_in_musica = kwargs.get('duracion_fade_in_musica', 2.0)
        aplicar_fade_out_musica = kwargs.get('aplicar_fade_out_musica', False)
        duracion_fade_out_musica = kwargs.get('duracion_fade_out_musica', 2.0)
        archivo_voz = kwargs.get('archivo_voz', None)
        volumen_voz = kwargs.get('volumen_voz', 1.0)
        aplicar_fade_in_voz = kwargs.get('aplicar_fade_in_voz', False)
        duracion_fade_in_voz = kwargs.get('duracion_fade_in_voz', 1.0)
        aplicar_fade_out_voz = kwargs.get('aplicar_fade_out_voz', False)
        duracion_fade_out_voz = kwargs.get('duracion_fade_out_voz', 1.0)
        aplicar_subtitulos = kwargs.get('aplicar_subtitulos', False)
        archivo_subtitulos = kwargs.get('archivo_subtitulos', None)
        tamano_fuente_subtitulos = kwargs.get('tamano_fuente_subtitulos', None)
        color_fuente_subtitulos = kwargs.get('color_fuente_subtitulos', 'orange')
        color_borde_subtitulos = kwargs.get('color_borde_subtitulos', 'black')
        grosor_borde_subtitulos = kwargs.get('grosor_borde_subtitulos', 6)
        subtitulos_align = kwargs.get('subtitulos_align', 'center')
        subtitulos_position_h = kwargs.get('subtitulos_position_h', 'center')
        subtitulos_position_v = kwargs.get('subtitulos_position_v', 'bottom')
        subtitulos_margen = kwargs.get('subtitulos_margen', 0.05)
        
        # Actualizar la función de progreso si se proporciona
        if 'progress_callback' in kwargs:
            self.set_progress_callback(kwargs['progress_callback'])
        
        # Crear clips de imagen
        clips = self._create_image_clips(
            duracion_img=duracion_img,
            aplicar_efectos=aplicar_efectos,
            secuencia_efectos=secuencia_efectos
        )
        
        # Aplicar transiciones si se solicita
        video_final = self._apply_transitions(
            clips=clips,
            aplicar_transicion=aplicar_transicion,
            tipo_transicion=tipo_transicion,
            duracion_transicion=duracion_transicion
        )
        
        # Aplicar fade in/out al video
        video_final = self._apply_fade_effects(
            video=video_final,
            aplicar_fade_in=aplicar_fade_in,
            duracion_fade_in=duracion_fade_in,
            aplicar_fade_out=aplicar_fade_out,
            duracion_fade_out=duracion_fade_out
        )
        
        # Aplicar overlay si se solicita
        video_final = self._apply_overlays(
            video=video_final,
            clips=clips,
            aplicar_overlay=aplicar_overlay,
            archivos_overlay=archivos_overlay,
            opacidad_overlay=opacidad_overlay,
            aplicar_transicion=aplicar_transicion,
            tipo_transicion=tipo_transicion,
            duracion_transicion=duracion_transicion
        )
        
        # Aplicar audio (música de fondo y/o voz en off)
        video_final = self._apply_audio(
            video=video_final,
            aplicar_musica=aplicar_musica,
            archivo_musica=archivo_musica,
            volumen_musica=volumen_musica,
            aplicar_fade_in_musica=aplicar_fade_in_musica,
            duracion_fade_in_musica=duracion_fade_in_musica,
            aplicar_fade_out_musica=aplicar_fade_out_musica,
            duracion_fade_out_musica=duracion_fade_out_musica,
            archivo_voz=archivo_voz,
            volumen_voz=volumen_voz,
            aplicar_fade_in_voz=aplicar_fade_in_voz,
            duracion_fade_in_voz=duracion_fade_in_voz,
            aplicar_fade_out_voz=aplicar_fade_out_voz,
            duracion_fade_out_voz=duracion_fade_out_voz
        )
        
        # Aplicar subtítulos si se solicita
        video_final = self._apply_subtitles(
            video=video_final,
            aplicar_subtitulos=aplicar_subtitulos,
            archivo_subtitulos=archivo_subtitulos,
            tamano_fuente_subtitulos=tamano_fuente_subtitulos,
            color_fuente_subtitulos=color_fuente_subtitulos,
            color_borde_subtitulos=color_borde_subtitulos,
            grosor_borde_subtitulos=grosor_borde_subtitulos,
            subtitulos_align=subtitulos_align,
            subtitulos_position_h=subtitulos_position_h,
            subtitulos_position_v=subtitulos_position_v,
            subtitulos_margen=subtitulos_margen
        )
        
        # Guardar el video
        return self._save_video(video_final, fps)
    
    def _extract_number(self, file_path):
        """
        Extrae el número que aparece al final del nombre del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            int: Número extraído, o 0 si no hay número
        """
        nombre_base = os.path.basename(file_path)
        match = re.search(r'_(\d+)\.', nombre_base)
        if match:
            return int(match.group(1))
        return 0
    
    def _create_image_clips(self, duracion_img, aplicar_efectos, secuencia_efectos):
        """
        Crea clips de imagen con efectos si se solicita.
        
        Args:
            duracion_img: Duración en segundos de cada imagen
            aplicar_efectos: Aplicar efectos a las imágenes
            secuencia_efectos: Lista de efectos a aplicar en secuencia
            
        Returns:
            list: Lista de clips de imagen
        """
        clips = []
        total_imagenes = len(self.image_files)
        
        for i, archivo in enumerate(self.image_files):
            clip = ImageClip(archivo).with_duration(duracion_img)
            
            # Aplicar efectos si se solicita
            if aplicar_efectos and secuencia_efectos:
                # Obtener el efecto para este clip según la secuencia
                efecto_idx = i % len(secuencia_efectos)
                tipo_efecto = secuencia_efectos[efecto_idx]
                print(f"DEBUG: Procesando imagen {i+1}, tipo_efecto = '{tipo_efecto}'")
                
                clip = self._apply_effect_to_clip(clip, tipo_efecto, duracion_img, i)
            
            clips.append(clip)
            
            # Actualizar progreso si hay un callback definido
            if self.progress_callback:
                self.progress_callback(i+1, total_imagenes)
        
        return clips
    
    def _apply_effect_to_clip(self, clip, tipo_efecto, duracion_img, indice_imagen):
        """
        Aplica un efecto específico a un clip.
        
        Args:
            clip: Clip de imagen
            tipo_efecto: Tipo de efecto a aplicar
            duracion_img: Duración del clip en segundos
            indice_imagen: Índice de la imagen (para mostrar en logs)
            
        Returns:
            ImageClip: Clip con el efecto aplicado
        """
        effect = None
        
        if tipo_efecto.lower() == 'in':
            # Usar los ajustes personalizados para el zoom
            zoom_ratio = self.settings.get('zoom_ratio', 0.5)
            zoom_quality = self.settings.get('zoom_quality', 'high')
            effect = ZoomEffect(zoom_in=True, ratio=zoom_ratio, clip_duration=duracion_img, quality=zoom_quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto zoom in a la imagen {indice_imagen+1} (ratio={zoom_ratio}, quality={zoom_quality})")
            
        elif tipo_efecto.lower() == 'out':
            # Usar los ajustes personalizados para el zoom
            zoom_ratio = self.settings.get('zoom_ratio', 0.5)
            zoom_quality = self.settings.get('zoom_quality', 'high')
            effect = ZoomEffect(zoom_in=False, ratio=zoom_ratio, clip_duration=duracion_img, quality=zoom_quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto zoom out a la imagen {indice_imagen+1} (ratio={zoom_ratio}, quality={zoom_quality})")
            
        elif tipo_efecto.lower() == 'panup':
            # Usar los ajustes personalizados para el pan
            scale_factor = self.settings.get('pan_scale_factor', 1.2)
            easing = self.settings.get('pan_easing', True)
            quality = self.settings.get('pan_quality', 'high')
            effect = PanUpEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto pan up a la imagen {indice_imagen+1} (scale_factor={scale_factor}, easing={easing})")
            
        elif tipo_efecto.lower() == 'pandown':
            # Usar los ajustes personalizados para el pan
            scale_factor = self.settings.get('pan_scale_factor', 1.2)
            easing = self.settings.get('pan_easing', True)
            quality = self.settings.get('pan_quality', 'high')
            effect = PanDownEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto pan down a la imagen {indice_imagen+1} (scale_factor={scale_factor}, easing={easing})")
            
        elif tipo_efecto.lower() == 'panleft':
            # Usar los ajustes personalizados para el pan
            scale_factor = self.settings.get('pan_scale_factor', 1.2)
            easing = self.settings.get('pan_easing', True)
            quality = self.settings.get('pan_quality', 'high')
            effect = PanLeftEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto pan left a la imagen {indice_imagen+1} (scale_factor={scale_factor}, easing={easing})")
            
        elif tipo_efecto.lower() == 'panright':
            # Usar los ajustes personalizados para el pan
            scale_factor = self.settings.get('pan_scale_factor', 1.2)
            easing = self.settings.get('pan_easing', True)
            quality = self.settings.get('pan_quality', 'high')
            effect = PanRightEffect(speed=0.25, clip_duration=duracion_img, scale_factor=scale_factor, easing=easing, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto pan right a la imagen {indice_imagen+1} (scale_factor={scale_factor}, easing={easing})")
            
        elif tipo_efecto.lower() in ['kenburns', 'kb']:
            # Usar los ajustes personalizados para Ken Burns
            zoom_ratio = self.settings.get('kb_zoom_ratio', 0.3)
            scale_factor = self.settings.get('kb_scale_factor', 1.3)
            quality = self.settings.get('kb_quality', 'high')
            direction = self.settings.get('kb_direction', 'random')
            
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
            print(f"Aplicando efecto Ken Burns a la imagen {indice_imagen+1} (zoom_ratio={zoom_ratio}, scale_factor={scale_factor}, direction={direction})")
            
        elif tipo_efecto.lower() == 'kenburns1':
            # Variante 1: zoom in con pan left
            zoom_ratio = self.settings.get('kb_zoom_ratio', 0.3)
            scale_factor = self.settings.get('kb_scale_factor', 1.3)
            quality = self.settings.get('kb_quality', 'high')
            effect = KenBurnsEffect(zoom_direction='in', pan_direction='left', 
                                   clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                   scale_factor=scale_factor, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto Ken Burns (variante 1) a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'kenburns2':
            # Variante 2: zoom out con pan right
            zoom_ratio = self.settings.get('kb_zoom_ratio', 0.3)
            scale_factor = self.settings.get('kb_scale_factor', 1.3)
            quality = self.settings.get('kb_quality', 'high')
            effect = KenBurnsEffect(zoom_direction='out', pan_direction='right', 
                                   clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                   scale_factor=scale_factor, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto Ken Burns (variante 2) a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'kenburns3':
            # Variante 3: zoom out con pan down
            zoom_ratio = self.settings.get('kb_zoom_ratio', 0.3)
            scale_factor = self.settings.get('kb_scale_factor', 1.3)
            quality = self.settings.get('kb_quality', 'high')
            effect = KenBurnsEffect(zoom_direction='out', pan_direction='down', 
                                   clip_duration=duracion_img, zoom_ratio=zoom_ratio, 
                                   scale_factor=scale_factor, quality=quality)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto Ken Burns (variante 3) a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'flip_horizontal':
            effect = FlipEffect(direction='horizontal')
            # Nota: FlipEffect no necesita clip_duration
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto flip_horizontal a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'flip_vertical':
            effect = FlipEffect(direction='vertical')
            # Nota: FlipEffect no necesita clip_duration
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto flip_vertical a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'vignette_zoom_in':
            effect = VignetteZoomEffect(zoom_in=True, zoom_ratio=0.05,
                             vignette_strength=0.7, vignette_radius=0.8,
                             vignette_fade_duration=2.0, clip_duration=duracion_img)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto vignette_zoom_in a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'vignette_zoom_out':
            effect = VignetteZoomEffect(zoom_in=False, zoom_ratio=0.05,
                             vignette_strength=0.7, vignette_radius=0.8,
                             vignette_fade_duration=2.0, clip_duration=duracion_img)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto vignette_zoom_out a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'rotate_clockwise':
            effect = RotateEffect(speed=30, direction='clockwise', clip_duration=duracion_img)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto de rotación en sentido horario a la imagen {indice_imagen+1}")
            
        elif tipo_efecto.lower() == 'rotate_counter_clockwise':
            effect = RotateEffect(speed=30, direction='counter-clockwise', clip_duration=duracion_img)
            clip = clip.transform(effect.apply)
            print(f"Aplicando efecto de rotación en sentido antihorario a la imagen {indice_imagen+1}")
            
        else:
            print(f"Tipo de efecto desconocido: {tipo_efecto}")
        
        return clip
    
    def _apply_transitions(self, clips, aplicar_transicion, tipo_transicion, duracion_transicion):
        """
        Aplica transiciones entre clips si se solicita.
        
        Args:
            clips: Lista de clips
            aplicar_transicion: Aplicar transiciones entre clips
            tipo_transicion: Tipo de transición a aplicar
            duracion_transicion: Duración de la transición en segundos
            
        Returns:
            VideoClip: Video resultante
        """
        if aplicar_transicion and tipo_transicion != 'none':
            print(f"Aplicando transición {tipo_transicion} con duración {duracion_transicion} segundos")
            return TransitionEffect.apply_transition(clips, tipo_transicion, duracion_transicion)
        else:
            # Concatenar clips sin transiciones
            return concatenate_videoclips(clips)
    
    def _apply_fade_effects(self, video, aplicar_fade_in, duracion_fade_in, aplicar_fade_out, duracion_fade_out):
        """
        Aplica fade in/out al video si se solicita.
        
        Args:
            video: Clip de video
            aplicar_fade_in: Aplicar fade in al inicio del video
            duracion_fade_in: Duración del fade in en segundos
            aplicar_fade_out: Aplicar fade out al final del video
            duracion_fade_out: Duración del fade out en segundos
            
        Returns:
            VideoClip: Video con fade in/out aplicado
        """
        effects = []
        
        # Aplicar fade in al inicio del video si se solicita
        if aplicar_fade_in and duracion_fade_in > 0:
            print(f"Aplicando fade in con duración {duracion_fade_in} segundos")
            effects.append(vfx.FadeIn(duracion_fade_in))
        
        # Aplicar fade out al final del video si se solicita
        if aplicar_fade_out and duracion_fade_out > 0:
            print(f"Aplicando fade out con duración {duracion_fade_out} segundos")
            effects.append(vfx.FadeOut(duracion_fade_out))
        
        # Aplicar efectos si hay alguno
        if effects:
            return video.with_effects(effects)
        return video
    
    def _apply_overlays(self, video, clips, aplicar_overlay, archivos_overlay, opacidad_overlay, 
                        aplicar_transicion, tipo_transicion, duracion_transicion):
        """
        Aplica overlays al video si se solicita.
        
        Args:
            video: Clip de video
            clips: Lista de clips originales
            aplicar_overlay: Aplicar overlay
            archivos_overlay: Lista de rutas a los archivos de overlay
            opacidad_overlay: Opacidad del overlay (0.0 a 1.0)
            aplicar_transicion: Aplicar transiciones entre clips
            tipo_transicion: Tipo de transición a aplicar
            duracion_transicion: Duración de la transición en segundos
            
        Returns:
            VideoClip: Video con overlays aplicados
        """
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
                    return TransitionEffect.apply_transition(clips_con_overlay, tipo_transicion, duracion_transicion)
                else:
                    return concatenate_videoclips(clips_con_overlay)
            else:
                # Si solo hay un overlay, aplicar el overlay al video final
                overlay_path = archivos_overlay[0]
                print(f"Aplicando overlay {os.path.basename(overlay_path)} con opacidad {opacidad_overlay}")
                return OverlayEffect.apply_overlay(video, overlay_path, opacidad_overlay)
        else:
            if aplicar_overlay:
                print("Se seleccionó aplicar overlay pero no se proporcionaron archivos de overlay")
            else:
                print("No se seleccionó aplicar overlay")
            return video
    
    def _apply_audio(self, video, aplicar_musica, archivo_musica, volumen_musica,
                    aplicar_fade_in_musica, duracion_fade_in_musica,
                    aplicar_fade_out_musica, duracion_fade_out_musica,
                    archivo_voz, volumen_voz,
                    aplicar_fade_in_voz, duracion_fade_in_voz,
                    aplicar_fade_out_voz, duracion_fade_out_voz):
        """
        Aplica audio (música y/o voz) al video.
        
        Args:
            video: Clip de video
            aplicar_musica: Aplicar música de fondo
            archivo_musica: Ruta al archivo de música
            volumen_musica: Volumen de la música (0.0 a 1.0)
            aplicar_fade_in_musica: Aplicar fade in a la música
            duracion_fade_in_musica: Duración del fade in de la música en segundos
            aplicar_fade_out_musica: Aplicar fade out a la música
            duracion_fade_out_musica: Duración del fade out de la música en segundos
            archivo_voz: Ruta al archivo de voz en off
            volumen_voz: Volumen de la voz (0.0 a 1.0)
            aplicar_fade_in_voz: Aplicar fade in a la voz
            duracion_fade_in_voz: Duración del fade in de la voz en segundos
            aplicar_fade_out_voz: Aplicar fade out a la voz
            duracion_fade_out_voz: Duración del fade out de la voz en segundos
            
        Returns:
            VideoClip: Video con audio aplicado
        """
        audio_clips = []
        
        # Aplicar voz en off primero si se proporciona
        if archivo_voz and os.path.exists(archivo_voz):
            print(f"Aplicando voz en off: {os.path.basename(archivo_voz)}")
            voz = AudioFileClip(archivo_voz)
            
            # Ajustar la duración de la voz a la duración del video si es necesario
            if voz.duration > video.duration:
                voz = voz.subclipped(0, video.duration)
            
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
            if musica.duration > video.duration:
                musica = musica.subclipped(0, video.duration)
            else:
                # Si la música es más corta que el video, repetirla hasta cubrir todo el video
                repeticiones = int(video.duration / musica.duration) + 1
                musica = concatenate_audioclips([musica] * repeticiones).subclipped(0, video.duration)
            
            # Ajustar el volumen
            # Aplicar un factor de reducción moderado (0.7) para música ambiental suave pero audible
            volumen_musica_ajustado = volumen_musica * 0.7
            print(f"Volumen de música original: {volumen_musica}, ajustado: {volumen_musica_ajustado}")
            musica = musica.with_effects([afx.MultiplyVolume(volumen_musica_ajustado)])
            
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
                return video.with_audio(audio_clips[0])
            else:
                # Si hay múltiples clips de audio, mezclarlos
                audio_final = CompositeAudioClip(audio_clips)
                return video.with_audio(audio_final)
        return video
    
    def _apply_subtitles(self, video, aplicar_subtitulos, archivo_subtitulos, 
                       tamano_fuente_subtitulos, color_fuente_subtitulos,
                       color_borde_subtitulos, grosor_borde_subtitulos,
                       subtitulos_align, subtitulos_position_h, 
                       subtitulos_position_v, subtitulos_margen):
        """
        Aplica subtítulos al video si se solicita.
        
        Args:
            video: Clip de video
            aplicar_subtitulos: Aplicar subtítulos
            archivo_subtitulos: Ruta al archivo de subtítulos
            tamano_fuente_subtitulos: Tamaño de la fuente de los subtítulos
            color_fuente_subtitulos: Color de la fuente de los subtítulos
            color_borde_subtitulos: Color del borde de los subtítulos
            grosor_borde_subtitulos: Grosor del borde de los subtítulos
            subtitulos_align: Alineación del texto de los subtítulos
            subtitulos_position_h: Posición horizontal de los subtítulos
            subtitulos_position_v: Posición vertical de los subtítulos
            subtitulos_margen: Margen desde el borde para los subtítulos
            
        Returns:
            VideoClip: Video con subtítulos aplicados
        """
        if aplicar_subtitulos and archivo_subtitulos and Path(archivo_subtitulos).is_file():
            print(f"Aplicando subtítulos desde: {archivo_subtitulos}")
            try:
                # Verificar si el archivo tiene contenido
                with open(archivo_subtitulos, 'r', encoding='utf-8') as f:
                    contenido = f.read().strip()
                    if not contenido:
                        print(f"ADVERTENCIA: El archivo de subtítulos está vacío: {archivo_subtitulos}")
                        raise ValueError("Archivo de subtítulos vacío")
                    else:
                        print(f"Archivo de subtítulos tiene {len(contenido)} caracteres")
                
                # Calcular tamaño de fuente si no se especifica
                if tamano_fuente_subtitulos is None:
                    # Ajustar automáticamente según la resolución del video
                    base_height = 1080  # Altura base de referencia
                    tamano_fuente_subtitulos = int((video.h / base_height) * 60)  # 60pt para 1080p
                    print(f"Tamaño de fuente de subtítulos ajustado automáticamente: {tamano_fuente_subtitulos}")
                
                # Calculamos el ancho del texto como un entero (no float)
                text_width = int(video.w * 0.9)
                
                # Obtener la ruta de la fuente (usar la especificada o intentar una fuente del sistema)
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       'fonts', 'Roboto-Regular.ttf')
                if not os.path.exists(font_path):
                    # Intentar con una fuente del sistema como respaldo
                    for system_font in ['/System/Library/Fonts/Helvetica.ttc', '/Library/Fonts/Arial.ttf']:
                        if os.path.exists(system_font):
                            font_path = system_font
                            print(f"Usando fuente del sistema: {font_path}")
                            break
                
                # Definir la posición con margen personalizado
                posicion_v_ajustada = subtitulos_position_v
                
                # Si la posición es 'bottom', convertirla a valor numérico con margen
                if subtitulos_position_v == 'bottom':
                    posicion_v_ajustada = 1.0 - subtitulos_margen
                elif subtitulos_position_v == 'top':
                    posicion_v_ajustada = 0.0 + subtitulos_margen
                
                # Crear la tupla de posición
                subtitulos_position = (subtitulos_position_h, posicion_v_ajustada)
                print(f"Posición de subtítulos ajustada: {subtitulos_position}")
                
                # Generator con los parámetros correctos
                generator = lambda txt: TextClip(
                    font_path,  # Primer argumento posicional debe ser font
                    text=txt,   # Texto como argumento nombrado
                    font_size=tamano_fuente_subtitulos,
                    color=color_fuente_subtitulos,
                    stroke_color=color_borde_subtitulos,
                    stroke_width=grosor_borde_subtitulos,
                    method='caption',
                    size=(text_width, None),  # Ancho como entero, no float
                    #align=subtitulos_align    # Usar el parámetro de alineación del texto
                )

                # Crear SubtitlesClip
                print("Creando SubtitlesClip...")
                subs_clip = SubtitlesClip(
                    archivo_subtitulos,
                    make_textclip=generator,
                    encoding='utf-8'
                )
                print("SubtitlesClip creado.")
                
                # Verificación de tipo y atributos
                print(f"Tipo de subs_clip: {type(subs_clip)}")
                
                if hasattr(subs_clip, 'duration'):
                    print(f"Duración de subtítulos: {subs_clip.duration}")
                    
                    # IMPORTANTE: Ajustar la duración de los subtítulos a la duración del video
                    if subs_clip.duration > video.duration:
                        print(f"Ajustando duración de subtítulos de {subs_clip.duration}s a {video.duration}s")
                        subs_clip = subs_clip.with_duration(video.duration)
                    
                    # Establecer posición para los subtítulos
                    positioned_subs = subs_clip.with_position(subtitulos_position, relative=True)
                    
                    # Crear clip final compuesto
                    print("Componiendo vídeo + subtítulos...")
                    return CompositeVideoClip(
                        [video, positioned_subs],
                        size=video.size
                    )
                else:
                    print("ERROR: SubtitlesClip no tiene atributo 'duration'. No se aplicarán subtítulos.")

            except Exception as e:
                print(f"Error al aplicar subtítulos: {str(e)}")
                traceback.print_exc()
                print("Continuando sin subtítulos...")
        
        return video
    
    def _save_video(self, video, fps):
        """
        Guarda el video en disco.
        
        Args:
            video: Clip de video
            fps: Frames por segundo
            
        Returns:
            str: Ruta al video guardado
        """
        print(f"Escribiendo archivo de video final en: {self.output_video_path}")
        video.write_videofile(
            str(self.output_video_path),
            fps=fps,
            codec='libx264', 
            audio_codec='aac',
            threads=os.cpu_count(), 
            preset='medium',
            ffmpeg_params=['-crf', '23']
        )
        print(f"Video guardado como {self.output_video_path}")
        
        # Indicar que el proceso ha terminado (100% completado)
        if self.progress_callback:
            self.progress_callback(1, 1)  # Asegurar que la barra llegue al 100%
        
        return str(self.output_video_path)