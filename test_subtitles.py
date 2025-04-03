# -*- coding: utf-8 -*-
# test_subtitles.py (Solo Método 1 con rutas originales)

import os
import srt # Necesitas: pip install srt
from datetime import timedelta
from pathlib import Path
from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip # Importar SubtitlesClip

# --- CONFIGURACIÓN: MODIFICA ESTAS RUTAS ---
video_input_path = "proyectos_video/test21/test21_final.mp4" # <--- ¡¡CAMBIA ESTO!! Ruta a video SIN subtítulos
srt_input_path = "proyectos_video/test21/subtitulos.srt"      # <--- ¡¡CAMBIA ESTO!! Ruta al SRT generado
# ¡¡Usa la RUTA ABSOLUTA a la fuente que SÍ existe!!
font_path = '/Users/olga/Development/proyectosPython/VideoPython/fonts/Roboto-Regular.ttf'
# O prueba con: font_path = '/System/Library/Fonts/Helvetica.ttc'
video_output_path = "video_con_subtitulos_TEST.mp4" # Nombre del archivo de salida
# --- FIN CONFIGURACIÓN ---

# --- Parámetros de Estilo ---
font_size =80  # Tamaño de la fuente
font_color = 'white'
stroke_color = 'black'
stroke_width = 4  # Ancho del stroke
# Posición relativa (fracción de la altura desde arriba, 0.9 = 90% abajo)
position = ('center', 0.80)
position_relative = True

# --- Lógica Principal ---

def run_test():
    print(f"--- Iniciando Test de Subtítulos (Método 1) ---")
    video_clip = None
    final_clip = None # Para el finally

    srt_path_obj = Path(srt_input_path)
    font_path_obj = Path(font_path)
    video_path_obj = Path(video_input_path)

    # Verificar archivos de entrada
    if not video_path_obj.is_file(): print(f"ERROR: Vídeo no encontrado: {video_input_path}"); return
    if not srt_path_obj.is_file(): print(f"ERROR: SRT no encontrado: {srt_input_path}"); return
    if not font_path_obj.is_file(): print(f"ERROR: Fuente no encontrada: {font_path}"); return

    print(f"Cargando vídeo: {video_input_path}")
    print(f"Cargando SRT: {srt_input_path}")
    print(f"Usando fuente: {font_path}")

    try:
        video_clip = VideoFileClip(video_input_path)
        video_duration = video_clip.duration
        video_width = video_clip.w
        video_height = video_clip.h # Necesario para size en CompositeVideoClip
        video_fps = video_clip.fps
        video_size = video_clip.size
        print(f"Vídeo cargado. Duración: {video_duration:.2f}s, Tamaño: {video_size}")

        # --- MÉTODO 1: Usar SubtitlesClip (Patrón de la Documentación) ---
        print("\n--- Generando subtítulos con SubtitlesClip ---")
        try:
            # Calculamos el ancho del texto como un entero (no float)
            text_width = int(video_width * 0.9)
            
            # Generator con los parámetros correctos
            generator = lambda txt: TextClip(
                font_path,  # Primer argumento posicional debe ser font
                text=txt,   # Texto como argumento nombrado
                font_size=font_size,  # Usar font_size, no fontsize
                color=font_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='caption',
                size=(text_width, None),  # Ancho como entero, no float
                # Sin align='center' porque puede causar problemas
                text_align='center',
            )

            # Crear SubtitlesClip
            print("Creando SubtitlesClip...")
            subs_clip = SubtitlesClip(
                srt_input_path,
                make_textclip=generator,
                encoding='utf-8'
            )
            print("SubtitlesClip creado.")
            
            # Verificación de tipo y atributos
            print(f"Tipo de subs_clip: {type(subs_clip)}")
            
            if hasattr(subs_clip, 'duration'):
                print(f"Duración de subtítulos: {subs_clip.duration}")
                
                # IMPORTANTE: Ajustar la duración de los subtítulos a la duración del video
                if subs_clip.duration > video_duration:
                    print(f"Ajustando duración de subtítulos de {subs_clip.duration}s a {video_duration}s")
                    subs_clip = subs_clip.with_duration(video_duration)
                
                # Establecer posición para los subtítulos
                positioned_subs = subs_clip.with_position(position, relative=position_relative)
                
                # Crear clip final compuesto
                print("Componiendo vídeo + subtítulos...")
                final_clip = CompositeVideoClip(
                    [video_clip, positioned_subs],
                    size=video_size
                )
                print("Composición exitosa.")
            else:
                print("ERROR: SubtitlesClip no tiene atributo 'duration'.")
                final_clip = video_clip

        except Exception as e_method1:
            print(f"!!!!!!!! ERROR en SubtitlesClip: {e_method1} !!!!!!!!")
            import traceback
            traceback.print_exc()
            final_clip = video_clip  # Usar vídeo original si falla

        # --- Escritura del Vídeo ---
        # Escribir solo si final_clip se ha asignado correctamente
        if final_clip is not None:
            print(f"\nEscribiendo vídeo final: {video_output_path}")
            final_clip.write_videofile(
                video_output_path,
                fps=video_fps, # Usar fps del video original
                codec='libx264', audio_codec='aac',
                threads=os.cpu_count(), preset='medium',
                ffmpeg_params=['-crf', '23']
                # logger='bar'
            )
            print("¡Vídeo de prueba con subtítulos generado!")
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

if __name__ == "__main__":
    run_test()