# -*- coding: utf-8 -*-
# test_subtitles.py - Versión mejorada con normalización de tamaño de fuente

import os
import srt 
from datetime import timedelta
from pathlib import Path
from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import ImageFont, Image, ImageDraw

# --- CONFIGURACIÓN: MODIFICA ESTAS RUTAS ---
video_input_path = "proyectos_video/test_subs/3.mp4"
srt_input_path = "proyectos_video/test_subs/subtitulos.srt"
font_path = 'fonts/Roboto-Regular.ttf'
video_output_path = "video_con_subtitulos_TEST.mp4"
# --- FIN CONFIGURACIÓN ---

# --- Parámetros de Estilo ---
base_font_size = 54  # Tamaño base de la fuente (se ajustará según la fuente)
font_color = 'white'
stroke_color = 'black'
stroke_width = 4
subtitulo_margen = 0.20  # 20% de margen desde abajo
text_bg_color = None  # Fondo transparente (None) o color como 'black', 'blue', etc.
text_bg_opacity = 0.5  # Si se usa fondo, opacidad del fondo (0.0-1.0)

# --- Función para normalizar el tamaño de la fuente ---
def normalize_font_size(font_path, base_size=80, reference_text="ABCDEFGabcdefg"):
    """
    Normaliza el tamaño de la fuente para que tengan una altura visual similar
    independientemente de la fuente utilizada.
    
    Args:
        font_path: Ruta a la fuente
        base_size: Tamaño base de referencia
        reference_text: Texto para probar el tamaño
        
    Returns:
        Tamaño de fuente normalizado
    """
    # Cargar la fuente de referencia (Helvetica o similar)
    reference_font_path = '/System/Library/Fonts/Helvetica.ttc'  # Cambia a una fuente base si es necesario
    
    try:
        # Si la fuente de referencia no existe, usar la fuente solicitada como referencia
        if not os.path.exists(reference_font_path):
            reference_font_path = font_path
            print(f"Fuente de referencia no encontrada, usando {font_path} como referencia")
        
        # Crear la fuente de referencia y medir su altura
        ref_font = ImageFont.truetype(reference_font_path, base_size)
        ref_size = ref_font.getbbox(reference_text)
        ref_height = ref_size[3] - ref_size[1]
        
        # Cargar la fuente a probar
        test_font = ImageFont.truetype(font_path, base_size)
        test_bbox = test_font.getbbox(reference_text)
        test_height = test_bbox[3] - test_bbox[1]
        
        # Factor de ajuste
        size_ratio = ref_height / test_height
        
        # Ajustar el tamaño para que coincida con la altura de referencia
        normalized_size = int(base_size * size_ratio)
        
        print(f"Tamaño normalizado para {os.path.basename(font_path)}: {normalized_size} (original: {base_size})")
        return normalized_size
        
    except Exception as e:
        print(f"Error normalizando tamaño: {e}")
        return base_size  # Devolver tamaño original en caso de error

# --- Función principal ---
def run_test():
    print(f"--- Iniciando Test de Subtítulos con Normalización de Tamaño ---")
    video_clip = None
    final_clip = None

    # Verificar archivos de entrada
    srt_path_obj = Path(srt_input_path)
    font_path_obj = Path(font_path)
    video_path_obj = Path(video_input_path)
    
    if not video_path_obj.is_file(): 
        print(f"ERROR: Vídeo no encontrado: {video_input_path}")
        return
    if not srt_path_obj.is_file(): 
        print(f"ERROR: SRT no encontrado: {srt_input_path}")
        return
    if not font_path_obj.is_file(): 
        print(f"ERROR: Fuente no encontrada: {font_path}")
        return

    print(f"Cargando vídeo: {video_input_path}")
    print(f"Cargando SRT: {srt_input_path}")
    print(f"Usando fuente: {font_path}")

    try:
        # Cargar el video
        video_clip = VideoFileClip(video_input_path)
        video_duration = video_clip.duration
        video_width = video_clip.w
        video_height = video_clip.h
        video_fps = video_clip.fps
        video_size = video_clip.size
        print(f"Vídeo cargado. Duración: {video_duration:.2f}s, Tamaño: {video_size}")

        # --- Normalizar el tamaño de la fuente ---
        # Esto ajustará el tamaño según la fuente elegida para mantener consistencia visual
        adjusted_font_size = normalize_font_size(font_path, base_size=base_font_size)
        print(f"Usando tamaño de fuente ajustado: {adjusted_font_size}px")

        # --- Generar subtítulos ---
        print("\n--- Generando subtítulos con tamaño normalizado ---")
        try:
            # Calcular ancho disponible para el texto (80% del ancho de video)
            text_width = int(video_width * 0.8)
            
            # Crear una función generadora para los subtítulos
            def create_subtitle_clip(txt):
                clip = TextClip(
                    font_path,  # Primer argumento debe ser la fuente
                    text=txt,   # Texto como argumento nombrado
                    font_size=adjusted_font_size,  # Usar el tamaño normalizado
                    color=font_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method='caption',  # Método caption para mejor control
                    size=(text_width, None),  # Ancho fijo, altura automática
                    bg_color=text_bg_color,  # Color de fondo (None=transparente)
                    text_align='center',  # Alineación del texto dentro del área
                    horizontal_align='center',  # Alineación horizontal del bloque
                    vertical_align='center',  # Alineación vertical del bloque
                    transparent=True,  # Permitir transparencia
                )
                
                # Si hay color de fondo y opacidad personalizada, aplicar
                if text_bg_color and text_bg_opacity < 1.0:
                    clip = clip.with_opacity(text_bg_opacity)
                    
                return clip

            # Crear SubtitlesClip
            print("Creando SubtitlesClip...")
            subs_clip = SubtitlesClip(
                srt_input_path,
                make_textclip=create_subtitle_clip,
                encoding='utf-8'
            )
            print("SubtitlesClip creado.")
            
            # Verificación
            print(f"Tipo de subs_clip: {type(subs_clip)}")
            
            if hasattr(subs_clip, 'duration'):
                print(f"Duración de subtítulos: {subs_clip.duration}")
                
                # Ajustar duración si es necesario
                if subs_clip.duration > video_duration:
                    print(f"Ajustando duración de subtítulos de {subs_clip.duration}s a {video_duration}s")
                    subs_clip = subs_clip.with_duration(video_duration)
                
                # Calcular posición vertical con margen
                pos_vertical = 1.0 - subtitulo_margen  # 1.0 = bottom, 0.0 = top
                position = ('center', pos_vertical)
                
                # Establecer posición para los subtítulos
                positioned_subs = subs_clip.with_position(position, relative=True)
                
                # Componer el video final
                print("Componiendo vídeo + subtítulos...")
                final_clip = CompositeVideoClip(
                    [video_clip, positioned_subs],
                    size=video_size
                )
                print("Composición exitosa.")
            else:
                print("ERROR: SubtitlesClip no tiene atributo 'duration'.")
                final_clip = video_clip

        except Exception as e:
            print(f"ERROR en generación de subtítulos: {e}")
            import traceback
            traceback.print_exc()
            final_clip = video_clip  # Usar vídeo original si falla

        # --- Escribir el Video ---
        if final_clip is not None:
            print(f"\nEscribiendo vídeo final: {video_output_path}")
            final_clip.write_videofile(
                video_output_path,
                fps=video_fps,
                codec='libx264', audio_codec='aac',
                threads=os.cpu_count(), preset='medium',
                ffmpeg_params=['-crf', '23']
            )
            print("¡Vídeo con subtítulos generado exitosamente!")
        else:
            print("\nERROR: No se pudo generar el clip final.")

    except Exception as e_main:
        print("\n--- ERROR GENERAL DURANTE EL PROCESO ---")
        print(f"Error: {e_main}")
        import traceback
        traceback.print_exc()

    finally:
        # Cerrar clips
        print("Cerrando clips...")
        if 'final_clip' in locals() and final_clip:
            try: final_clip.close()
            except Exception as e: 
                print(f"Error al cerrar final_clip: {e}")
        
        if 'video_clip' in locals() and video_clip:
            try: video_clip.close()
            except Exception as e:
                print(f"Error al cerrar video_clip: {e}")

        print("--- Test Finalizado ---")

# --- Ejecutar el test ---
if __name__ == "__main__":
    run_test()