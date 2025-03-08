from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os
from typing import List, Tuple, Optional

class SubtitleEffect:
    """
    Clase para aplicar subtítulos a videos.
    Permite agregar texto sincronizado que aparece en momentos específicos del video.
    """
    
    @staticmethod
    def create_subtitle_clip(text: str, start_time: float, end_time: float,
                           font_size: int = 24, font_color: str = 'white',
                           stroke_color: str = 'black', stroke_width: int = 1,
                           position: Tuple[str, str] = ('center', 'bottom')) -> TextClip:
        """
        Crea un clip de subtítulo con el texto y estilo especificados.
        
        Args:
            text: Texto del subtítulo
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            font_size: Tamaño de la fuente
            font_color: Color del texto
            stroke_color: Color del borde del texto
            stroke_width: Grosor del borde del texto
            position: Tupla con la posición (x, y) del texto
            
        Returns:
            Clip de texto configurado con los parámetros especificados
        """
        subtitle_clip = TextClip(text,
                                font_size=font_size,
                                color=font_color,
                                stroke_color=stroke_color,
                                stroke_width=stroke_width)
        
        # Configurar la duración y posición del subtítulo
        subtitle_clip = subtitle_clip.set_start(start_time).set_end(end_time)
        subtitle_clip = subtitle_clip.set_position(position)
        
        return subtitle_clip
    
    @staticmethod
    def apply_subtitles(video_clip: VideoFileClip,
                       subtitles: List[Tuple[float, float, str]],
                       font_size: int = 24,
                       font_color: str = 'white',
                       stroke_color: str = 'black',
                       stroke_width: int = 1,
                       position: Tuple[str, str] = ('center', 'bottom')) -> CompositeVideoClip:
        """
        Aplica una lista de subtítulos a un video.
        
        Args:
            video_clip: Clip de video base
            subtitles: Lista de tuplas (tiempo_inicio, tiempo_fin, texto)
            font_size: Tamaño de la fuente
            font_color: Color del texto
            stroke_color: Color del borde del texto
            stroke_width: Grosor del borde del texto
            position: Tupla con la posición (x, y) del texto
            
        Returns:
            Clip de video con los subtítulos aplicados
        """
        # Crear clips de subtítulos
        subtitle_clips = []
        for start_time, end_time, text in subtitles:
            subtitle_clip = SubtitleEffect.create_subtitle_clip(
                text, start_time, end_time,
                font_size, font_color,
                stroke_color, stroke_width,
                position
            )
            subtitle_clips.append(subtitle_clip)
        
        # Combinar el video con los subtítulos
        final_clip = CompositeVideoClip([video_clip] + subtitle_clips)
        return final_clip
    
    @staticmethod
    def parse_srt_file(srt_file: str) -> List[Tuple[float, float, str]]:
        """
        Parsea un archivo .srt y retorna una lista de subtítulos.
        
        Args:
            srt_file: Ruta al archivo .srt
            
        Returns:
            Lista de tuplas (tiempo_inicio, tiempo_fin, texto)
        """
        if not os.path.exists(srt_file):
            raise FileNotFoundError(f"Archivo SRT no encontrado: {srt_file}")
            
        def time_to_seconds(time_str: str) -> float:
            """Convierte el formato de tiempo SRT (HH:MM:SS,mmm) a segundos"""
            h, m, s = time_str.replace(',', '.').split(':')
            return float(h) * 3600 + float(m) * 60 + float(s)
        
        subtitles = []
        current_text = []
        start_time = end_time = 0.0
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if line.isdigit():  # Número de subtítulo
                    if current_text:  # Guardar subtítulo anterior
                        subtitles.append((start_time, end_time, ' '.join(current_text)))
                        current_text = []
                elif ' --> ' in line:  # Línea de tiempo
                    start, end = line.split(' --> ')
                    start_time = time_to_seconds(start)
                    end_time = time_to_seconds(end)
                elif line:  # Línea de texto
                    current_text.append(line)
        
        # Agregar el último subtítulo
        if current_text:
            subtitles.append((start_time, end_time, ' '.join(current_text)))
        
        return subtitles