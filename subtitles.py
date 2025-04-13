from tkinter.font import Font
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os
import re
import srt
from datetime import timedelta
from pathlib import Path
from typing import List, Tuple, Optional

# Importar faster-whisper condicionalmente
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("ADVERTENCIA: faster-whisper no instalado. Generación automática de SRT no disponible.")
    print("Para instalar: pip install faster-whisper srt")
    WhisperModel = None

class SubtitleEffect:
    """
    Clase para aplicar subtítulos a videos.
    Permite agregar texto sincronizado que aparece en momentos específicos del video.
    """
    
    @staticmethod
    def parse_srt_file_with_library(srt_file_path: str) -> List[srt.Subtitle]:
        """Parsea un archivo SRT usando la librería srt."""
        srt_path = Path(srt_file_path)
        if not srt_path.is_file() or srt_path.stat().st_size == 0:
            print(f"Advertencia: Archivo SRT no encontrado o vacío en {srt_file_path}")
            return []
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                return list(srt.parse(f.read()))
        except Exception as e:
            print(f"Error al parsear SRT con librería: {e}")
            return []

    @staticmethod
    def create_subtitle_clip(
        text: str,
        start_time: float,
        end_time: float,
        font: str,
        font_size: int = 80,
        font_color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: int = 3,
        position: Tuple[str, str] = ('center', 'bottom'),
        video_width: int = None,  # Ahora es opcional
        align: str = 'center'
    ) -> TextClip:
        """
        Crea un clip de subtítulo con el texto y estilo especificados.
        
        Args:
            text: Texto del subtítulo
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            font: Ruta a la fuente a usar
            font_size: Tamaño de la fuente
            font_color: Color del texto
            stroke_color: Color del borde
            stroke_width: Grosor del borde
            position: Posición del subtítulo (horizontal, vertical)
            video_width: Ancho del video para calcular el tamaño del TextClip
            align: Alineación del texto ('left', 'center', 'right')
        """
        try:
            # Determinar el ancho a utilizar
            if video_width is None:
                # Si no se especifica el ancho, usar un valor predeterminado
                # pero imprimir una advertencia
                video_width = 1280
                print(f"ADVERTENCIA: No se especificó el ancho del video para los subtítulos. Usando valor por defecto: {video_width}")
            
            # Calcular el ancho del texto como un 90% del ancho del video
            text_width = int(video_width * 0.9)
            print(f"Creando subtítulo con ancho: {text_width} (90% del ancho del video: {video_width})")
            
            # Crear TextClip con parámetros específicos según la documentación de MoviePy 2.x
            print(f"Creando TextClip con: font={font}, text={text[:20]}..., font_size={font_size}")
            subtitle_clip = TextClip(
                font=font,                     # Ruta a la fuente a usar
                text=text,                     # Texto a mostrar
                font_size=font_size,           # Tamaño de la fuente
                color=font_color,              # Color del texto
                stroke_color=stroke_color,     # Color del borde
                stroke_width=stroke_width,     # Grosor del borde
                method='caption',              # Método caption para mejor control
                size=(text_width, None),       # Ancho fijo, altura automática
                text_align=align,              # Alineación del texto
                horizontal_align='center',     # Alineación horizontal del bloque
                vertical_align='center',       # Alineación vertical del bloque
                transparent=True               # Permitir transparencia
            )
            
            # Establecer duración y posición usando los métodos correctos para MoviePy 2.x
            subtitle_clip = subtitle_clip.with_duration(end_time - start_time)
            subtitle_clip = subtitle_clip.with_start(start_time)
            subtitle_clip = subtitle_clip.with_position(position)
            
            return subtitle_clip
            
        except Exception as e:
            print(f"Error al crear TextClip: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def apply_subtitles(
        video_clip: VideoFileClip,
        subtitles: List[srt.Subtitle],
        font: str = '/System/Library/Fonts/Helvetica.ttc',
        font_size: int = 24,
        font_color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: int = 1,
        position: Tuple[str, str] = ('center', 'bottom'),
        align: str = 'center'
    ) -> VideoFileClip:
        """
        Aplica subtítulos a un video usando TextClips.
        
        Args:
            video_clip: Clip de video base
            subtitles: Lista de objetos srt.Subtitle
            font: Ruta a la fuente a usar
            font_size: Tamaño de la fuente
            font_color: Color del texto
            stroke_color: Color del borde
            stroke_width: Grosor del borde
            position: Posición del subtítulo (horizontal, vertical)
            align: Alineación del texto ('left', 'center', 'right')
            
        Returns:
            VideoFileClip con los subtítulos aplicados
        """
        if not hasattr(video_clip, 'duration') or not video_clip.duration:
            print("ERROR: Clip de vídeo base no tiene duración válida.")
            return video_clip

        video_duration = video_clip.duration
        video_width = video_clip.w
        
        subtitle_clips = []
        for sub in subtitles:
            start = sub.start.total_seconds()
            end = sub.end.total_seconds()
            
            # Validar tiempos
            if start >= video_duration: continue
            end = min(end, video_duration)
            if end <= start: continue
            
            # Crear y añadir el clip de subtítulo
            clip = SubtitleEffect.create_subtitle_clip(
                sub.content,
                start,
                end,
                font,
                font_size,
                font_color,
                stroke_color,
                stroke_width,
                position,
                video_width,
                align
            )
            
            if clip:
                subtitle_clips.append(clip)

        # Componer si hay clips de subtítulo
        if subtitle_clips:
            return CompositeVideoClip([video_clip] + subtitle_clips, size=video_clip.size)
        else:
            return video_clip

    @staticmethod
    def format_srt_time(total_seconds):
        """Convierte segundos a formato timedelta para srt"""
        total_seconds = max(0, total_seconds)
        return timedelta(seconds=total_seconds)

    @staticmethod
    def generate_srt_with_whisper(
        whisper_model: WhisperModel,
        audio_path: str,
        output_srt_path: str,
        max_chars_per_line: int = 42,
        max_words_per_line: int = 10,
        language: str = "es"
    ) -> bool:
        """
        Genera SRT usando faster-whisper con timestamps por palabra,
        agrupando palabras en líneas de subtítulo.
        """
        if not WHISPER_AVAILABLE or not whisper_model:
            print("ERROR SRT: Modelo Whisper no disponible.")
            return False
        
        audio_file = Path(audio_path)
        if not audio_file.is_file():
            print(f"ERROR SRT: Archivo de audio no encontrado: {audio_path}")
            return False
        
        print(f"Generando SRT desde: {audio_file.name} -> {Path(output_srt_path).name}")
        try:
            segments, info = whisper_model.transcribe(audio_path, word_timestamps=True, language=language)
            print(f" - Idioma detectado: {info.language} (Prob: {info.language_probability:.2f})")

            all_words = [word for segment in segments if segment.words for word in segment.words]
            if not all_words:
                print("Advertencia: Whisper no detectó palabras con timestamps.")
                return False

            srt_subs = []
            subtitle_index = 1
            current_line_words = []
            line_start_time = all_words[0].start

            for i, word_info in enumerate(all_words):
                current_line_words.append(word_info)
                current_line_text = " ".join(w.word.strip() for w in current_line_words)
                line_end_time = word_info.end

                # Decidir si cortar la línea
                is_last_word = (i == len(all_words) - 1)
                line_too_long = len(current_line_text) >= max_chars_per_line
                too_many_words = len(current_line_words) >= max_words_per_line

                if line_too_long or too_many_words or is_last_word:
                    sub = srt.Subtitle(
                        index=subtitle_index,
                        start=format_srt_time(line_start_time),
                        end=format_srt_time(line_end_time),
                        content=current_line_text
                    )
                    srt_subs.append(sub)
                    subtitle_index += 1
                    current_line_words = []
                    if not is_last_word:
                        line_start_time = all_words[i+1].start

            if not srt_subs:
                print("Advertencia: No se generaron entradas de subtítulo.")
                return False

            final_srt_content = srt.compose(srt_subs)
            output_file = Path(output_srt_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_srt_content)

            if not output_file.is_file() or output_file.stat().st_size == 0:
                print(f"ERROR: Archivo SRT no se creó o está vacío: {output_srt_path}")
                return False

            print(f"Archivo SRT generado con {len(srt_subs)} entradas en: {output_srt_path}")
            return True

        except Exception as e:
            print(f"ERROR durante la transcripción o generación de SRT: {e}")
            import traceback
            traceback.print_exc()
            return False

# Funciones para generar subtítulos con faster-whisper

def split_into_sentences(text):
    """Divide texto en frases (simple, puede necesitar mejoras)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' ').strip())
    return [s.strip() for s in sentences if s.strip()]


def format_srt_time(total_seconds):
    """Convierte segundos a formato timedelta para srt"""
    # Asegurarse de que no sea negativo por errores de precisión pequeños
    total_seconds = max(0, total_seconds)
    return timedelta(seconds=total_seconds)


def generate_srt_with_whisper(
    whisper_model,  # Recibe el modelo cargado
    audio_path: str,
    output_srt_path: str,
    max_chars_per_line: int = 42,  # Límite de caracteres común
    max_words_per_line: int = 10,  # Límite de palabras
    language: str = "es",  # Idioma para transcripción
    word_timestamps: bool = True  # Usar timestamps por palabra
) -> bool:
    """
    Genera SRT usando faster-whisper con timestamps por palabra,
    e intenta agrupar palabras en líneas de subtítulo.
    """
    if not WHISPER_AVAILABLE:
        print("ERROR SRT: faster-whisper no está disponible.")
        return False
        
    if not whisper_model:
        print("ERROR SRT: Modelo Whisper no proporcionado.")
        return False
    if not Path(audio_path).is_file():
        print(f"ERROR SRT: Archivo de audio no encontrado: {audio_path}")
        return False

    print(f"Generando SRT desde: {Path(audio_path).name} -> {Path(output_srt_path).name}")

    try:
        # Verificar que el archivo de audio existe y tiene contenido
        audio_file = Path(audio_path)
        if not audio_file.is_file():
            print(f"ERROR SRT: Archivo de audio no encontrado: {audio_path}")
            return False
        
        if audio_file.stat().st_size == 0:
            print(f"ERROR SRT: Archivo de audio vacío: {audio_path}")
            return False
        
        print(f"Iniciando transcripción de audio: {audio_file.name} ({audio_file.stat().st_size} bytes)")
        
        # Configurar parámetros de transcripción
        transcribe_options = {
            "word_timestamps": word_timestamps,
        }
        
        # Si se especifica un idioma diferente a "auto", usarlo
        if language and language.lower() != "auto":
            transcribe_options["language"] = language
            print(f" - Usando idioma configurado: {language}")
        
        print(f" - Opciones de transcripción: {transcribe_options}")
        
        # Transcribir obteniendo segmentos y palabras
        print(" - Iniciando transcripción con faster-whisper...")
        segments, info = whisper_model.transcribe(audio_path, **transcribe_options)
        print(f" - Transcripción completada. Idioma detectado: {info.language} (Prob: {info.language_probability:.2f})")

        srt_subs = []
        subtitle_index = 1
        all_words = []
        # Recopilar todas las palabras con sus tiempos
        for segment in segments:
            if segment.words:  # Asegurarse de que hay palabras
                all_words.extend(segment.words)

        if not all_words:
            print("Advertencia: Whisper no detectó palabras con timestamps.")
            return False

        # Agrupar palabras en líneas
        current_line = []
        line_start_time = all_words[0].start  # Tiempo de inicio de la primera palabra de la línea actual
        for i, word_info in enumerate(all_words):
            current_line.append(word_info)
            line_text = " ".join(w.word.strip() for w in current_line)  # Unir palabras con espacios
            line_end_time = word_info.end  # Tiempo final de la palabra actual

            # Comprobar si debemos cortar la línea aquí
            # Condición 1: Límite de caracteres
            # Condición 2: Límite de palabras
            # Condición 3: Si es la última palabra de todas
            cut_line = False
            if len(line_text) >= max_chars_per_line: cut_line = True
            if len(current_line) >= max_words_per_line: cut_line = True
            if i == len(all_words) - 1: cut_line = True

            if cut_line:
                # Crear el subtítulo SRT para la línea actual
                sub_content = " ".join(w.word.strip() for w in current_line)

                sub = srt.Subtitle(
                    index=subtitle_index,
                    start=format_srt_time(line_start_time),
                    end=format_srt_time(line_end_time),
                    content=sub_content
                )
                srt_subs.append(sub)
                subtitle_index += 1

                # Resetear para la siguiente línea
                current_line = []
                # Establecer el tiempo de inicio de la siguiente línea (si hay más palabras)
                if i < len(all_words) - 1:
                    line_start_time = all_words[i+1].start

        # Componer y guardar SRT
        if not srt_subs:
            print("Advertencia: No se generaron entradas de subtítulo.")
            return False

        # Verificar que se hayan generado subtítulos
        if not srt_subs:
            print("ERROR: No se generaron subtítulos. La transcripción no produjo resultados.")
            return False
            
        # Componer el archivo SRT
        final_srt_content = srt.compose(srt_subs)
        
        # Verificar que el contenido no esté vacío
        if not final_srt_content.strip():
            print("ERROR: El contenido SRT generado está vacío.")
            return False
            
        # Guardar el archivo SRT
        output_file = Path(output_srt_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)  # Crear directorio si no existe
        
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            f.write(final_srt_content)
            
        # Verificar que el archivo se haya creado correctamente
        if not output_file.is_file() or output_file.stat().st_size == 0:
            print(f"ERROR: El archivo SRT no se creó correctamente o está vacío: {output_srt_path}")
            return False
            
        print(f"Archivo SRT generado exitosamente con {len(srt_subs)} entradas en: {output_srt_path}")
        print(f"Tamaño del archivo: {output_file.stat().st_size} bytes")
        return True

    except Exception as e:
        print(f"ERROR durante la transcripción o generación de SRT: {e}")
        import traceback
        traceback.print_exc()
        
        # Intentar crear un archivo SRT vacío para evitar errores posteriores
        try:
            Path(output_srt_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_srt_path, 'w', encoding='utf-8') as f:
                f.write("1\n00:00:00,000 --> 00:00:05,000\nError al generar subtítulos.\n\n")
            print(f"Se creó un archivo SRT de emergencia en: {output_srt_path}")
        except Exception as e_file:
            print(f"No se pudo crear archivo SRT de emergencia: {e_file}")
        return False