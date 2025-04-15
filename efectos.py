from collections.abc import Callable
from moviepy import *
from PIL import Image, ImageEnhance
from PIL.Image import Resampling
import math
import numpy as np



class ZoomEffect(Effect):
    """
    Efecto de zoom (in o out) que depende de la duración real del clip.
    """
    def __init__(self, zoom_in=True, ratio=0.5, clip_duration=None, quality='high'):
        """
        Inicializa el efecto de zoom.

        Args:
            zoom_in: True para zoom in, False para zoom out.
            ratio: Factor total de zoom a aplicar durante la duración del clip.
                   Ej: ratio=0.5 significa un 50% de zoom total (factor final 1.5 para zoom-in).
            clip_duration: Duración TOTAL del clip (¡Obligatorio!).
            quality: Calidad del redimensionado ('high' para LANCZOS, 'medium' para BILINEAR).
        """
        if clip_duration is None or clip_duration <= 0:
            raise ValueError(f"{self.__class__.__name__} requiere una clip_duration válida > 0.")

        self.zoom_in = zoom_in
        self.total_zoom_change = abs(ratio)
        self.clip_duration = clip_duration
        self.resample_mode = Resampling.LANCZOS if quality == 'high' else Resampling.BILINEAR

    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        img = None # Inicializar
        try:
            progress = min(1.0, max(0.0, t / self.clip_duration))

            if self.zoom_in:
                zoom_factor = 1.0 + self.total_zoom_change * progress
            else:
                start_zoom_factor = 1.0 + self.total_zoom_change
                zoom_factor = start_zoom_factor - self.total_zoom_change * progress

            img = Image.fromarray(get_frame(t))
            base_size = img.size

            new_size = (math.ceil(base_size[0] * zoom_factor), math.ceil(base_size[1] * zoom_factor))
            new_size = (max(2, new_size[0] + (new_size[0] % 2)), max(2, new_size[1] + (new_size[1] % 2)))

            img_resized = img.resize(new_size, self.resample_mode)

            x = max(0, math.ceil((new_size[0] - base_size[0]) / 2))
            y = max(0, math.ceil((new_size[1] - base_size[1]) / 2))
            box_width = min(base_size[0], new_size[0] - x)
            box_height = min(base_size[1], new_size[1] - y)
            box = (x, y, x + box_width, y + box_height)

            img_zoomed = img_resized.crop(box)

            if img_zoomed.size != base_size:
                img_zoomed = img_zoomed.resize(base_size, self.resample_mode)

            result = np.array(img_zoomed)

            # Cerrar imágenes intermedias
            if img_resized is not img: img_resized.close()
            if img_zoomed is not img_resized and img_zoomed is not img: img_zoomed.close()

            return result
        except Exception as e:
            print(f"Error en {self.__class__.__name__} (t={t:.2f}): {e}. Devolviendo frame original.")
            return get_frame(t)
        finally:
            if img: img.close()


    
class PanEffect(Effect):
    """Efecto base para los efectos de paneo que mueve una 'cámara virtual' sobre una imagen."""
    
    def __init__(self, direction='up', speed=100, scale_factor=1.5, clip_duration=None, easing=True, quality='high'):
        """
        Inicializa el efecto de paneo.

        Args:
            direction: Dirección del paneo ('up', 'down', 'left', 'right')
            speed: Velocidad del paneo en píxeles por segundo (o píxeles/seg para recorridos largos).
                   Valores más altos resultan en un paneo más rápido y visible.
            scale_factor: Factor para redimensionar la imagen original antes del paneo.
                         Valores más altos permiten más movimiento pero pueden reducir calidad.
            clip_duration: Duración del clip en segundos. Si no se proporciona, se usará un valor por defecto.
            easing: Si se debe aplicar suavizado al movimiento.
            quality: Calidad del redimensionado ('high' para LANCZOS, 'medium' para BILINEAR).
        """
        self.direction = direction.lower()
        self.speed = speed
        self.scale_factor = scale_factor
        self.clip_duration = clip_duration
        self.easing = easing
        self.resample_mode = Resampling.LANCZOS if quality == 'high' else Resampling.BILINEAR

        
    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        try:
            # Obtener el frame
            img = Image.fromarray(get_frame(t))
            base_size = img.size
            
            # Calcular el nuevo tamaño con el factor de escala
            # Aplicamos un factor de escala para tener suficiente área para el paneo
            scaled_size = (
                math.ceil(img.size[0] * self.scale_factor),
                math.ceil(img.size[1] * self.scale_factor),
            )
            
            # Redimensionar la imagen original para tener más área para el paneo
            scaled_img = img.resize(scaled_size, self.resample_mode)
            
            # Calcular el desplazamiento máximo posible (el rango en el que podemos movernos)
            max_offset_x = scaled_size[0] - base_size[0]
            max_offset_y = scaled_size[1] - base_size[1]

            # Calcular posición inicial (centro)
            start_x = max_offset_x // 2
            start_y = max_offset_y // 2

            # Inicializar offset con la posición central
            offset_x = start_x
            offset_y = start_y

            # --- NUEVO: Movimiento SIEMPRE de borde a borde ---
            # La distancia total de paneo será siempre el máximo permitido (max_movement),
            # así el efecto es igual de dinámico en cualquier duración.
            movement_range = 0.8

            if self.direction in ['up', 'down']:
                max_movement = max_offset_y * movement_range
            else:
                max_movement = max_offset_x * movement_range
            total_movement = max_movement  # SIEMPRE recorre todo el rango permitido

            # Calcular el progreso normalizado (0.0 a 1.0) basado en el tiempo actual
            progress = t / max(0.1, self.clip_duration)
            progress = max(0.0, min(1.0, progress))

            if self.easing:
                if progress < 0.5:
                    ease_factor = 2 * progress * progress
                else:
                    ease_factor = -1 + (4 * progress) - (2 * progress * progress)
            else:
                ease_factor = progress

            # Movimiento de borde a borde
            if self.direction == 'up':
                # Paneo hacia arriba: desde abajo hacia arriba
                offset_y = start_y + (max_movement / 2) - (ease_factor * total_movement)
            elif self.direction == 'down':
                # Paneo hacia abajo: desde arriba hacia abajo
                offset_y = start_y - (max_movement / 2) + (ease_factor * total_movement)
            elif self.direction == 'left':
                # Paneo hacia la izquierda
                offset_x = start_x + (max_movement / 2) - (ease_factor * total_movement)
            elif self.direction == 'right':
                # Paneo hacia la derecha
                offset_x = start_x - (max_movement / 2) + (ease_factor * total_movement)
            
            # Asegurar que los offsets estén dentro de los límites
            offset_x = max(0, min(max_offset_x, int(round(offset_x))))
            offset_y = max(0, min(max_offset_y, int(round(offset_y))))
            
            # Recortar la imagen para obtener la parte visible
            crop_box = (
                int(offset_x),
                int(offset_y),
                int(offset_x + base_size[0]),
                int(offset_y + base_size[1])
            )
            
            # Asegurarse de que el recorte está dentro de los límites de la imagen
            crop_box = (
                max(0, crop_box[0]),
                max(0, crop_box[1]),
                min(scaled_size[0], crop_box[2]),
                min(scaled_size[1], crop_box[3])
            )
            
            img_result = scaled_img.crop(crop_box)

            # Convertir a array de numpy y retornar
            result = np.array(img_result)
            
            # Liberar recursos
            img.close()
            scaled_img.close()
            img_result.close()
            
            return result
        except Exception as e:
            print(f"Error en PanEffect (t={t:.2f}): {e}. Devolviendo frame original.")
            return get_frame(t)


class PanUpEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de abajo hacia arriba sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2, clip_duration=None, easing=True, quality='high'):
        super().__init__(direction='up', speed=speed, scale_factor=scale_factor, 
                        clip_duration=clip_duration, easing=easing, quality=quality)


class PanDownEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de arriba hacia abajo sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2, clip_duration=None, easing=True, quality='high'):
        super().__init__(direction='down', speed=speed, scale_factor=scale_factor, 
                        clip_duration=clip_duration, easing=easing, quality=quality)


class PanLeftEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de derecha a izquierda sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2, clip_duration=None, easing=True, quality='high'):
        super().__init__(direction='left', speed=speed, scale_factor=scale_factor, 
                        clip_duration=clip_duration, easing=easing, quality=quality)


class PanRightEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de izquierda a derecha sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2, clip_duration=None, easing=True, quality='high'):
        super().__init__(direction='right', speed=speed, scale_factor=scale_factor, 
                        clip_duration=clip_duration, easing=easing, quality=quality)


class KenBurnsEffect(Effect):
    """
    Efecto Ken Burns que combina zoom y paneo para crear una sensación de movimiento cinematográfico.
    El efecto Ken Burns clásico consiste en un movimiento lento de zoom mientras simultáneamente
    se realiza un paneo suave sobre diferentes áreas de la imagen.
    """
    
    def __init__(self, zoom_direction='in', pan_direction='up', 
                 zoom_ratio=0.05, pan_speed=0.12, scale_factor=1.3, clip_duration=None):
        """Inicializa el efecto Ken Burns.
        
        Args:
            zoom_direction: Dirección del zoom ('in' o 'out')
            pan_direction: Dirección del paneo ('up', 'down', 'left', 'right', 'diagonal_up_right',
                          'diagonal_up_left', 'diagonal_down_right', 'diagonal_down_left')
            zoom_ratio: Factor de zoom por segundo
            pan_speed: Velocidad del paneo
            scale_factor: Factor para redimensionar la imagen original
            clip_duration: Duración del clip en segundos. Si no se proporciona, se usará un valor predeterminado.
        """
        self.zoom_in = zoom_direction.lower() == 'in'
        self.zoom_ratio = zoom_ratio
        self.pan_direction = pan_direction.lower()
        self.pan_speed = pan_speed
        self.scale_factor = scale_factor
        self.clip_duration = clip_duration
    
    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        try:
            # Obtener el frame original
            img = Image.fromarray(get_frame(t))
            base_size = img.size
            
            # Usar la duración real del clip para el cálculo de movimiento
            progress = min(1.0, t / max(0.1, self.clip_duration))
            
            # Calcular el factor de zoom basado en la dirección y el tiempo
            if self.zoom_in:
                # Zoom In: Empezamos con imagen normal y la agrandamos
                zoom_factor = 1 + (self.zoom_ratio * self.clip_duration * progress)
            else:
                # Zoom Out: Empezamos con imagen más grande y la reducimos
                max_zoom = 1 + (self.zoom_ratio * self.clip_duration)
                zoom_factor = max_zoom - (self.zoom_ratio * self.clip_duration * progress)
            
            # Aplicar el factor de escala adicional (para tener área para el paneo)
            total_scale = zoom_factor * self.scale_factor
            
            # Calcular el nuevo tamaño con zoom y escala
            new_size = (
                math.ceil(img.size[0] * total_scale),
                math.ceil(img.size[1] * total_scale),
            )
            
            # Redimensionar la imagen con zoom aplicado
            img_zoomed = img.resize(new_size, Resampling.LANCZOS)
            
            # Calcular desplazamientos máximos posibles
            max_offset_x = new_size[0] - base_size[0]
            max_offset_y = new_size[1] - base_size[1]
            
            # Posición central (punto de partida por defecto)
            center_x = max_offset_x // 2
            center_y = max_offset_y // 2
            
            # Calcular el rango de movimiento (usar 90% del desplazamiento máximo)
            range_factor = 0.90
            move_range_x = max_offset_x * range_factor
            move_range_y = max_offset_y * range_factor
            
            # Calcular los desplazamientos iniciales y finales según la dirección del paneo
            start_x, start_y = center_x, center_y
            end_x, end_y = center_x, center_y
            
            # Configurar puntos iniciales y finales según la dirección
            if self.pan_direction == 'up':
                start_y = center_y + (move_range_y / 2)
                end_y = center_y - (move_range_y / 2)
            elif self.pan_direction == 'down':
                start_y = center_y - (move_range_y / 2)
                end_y = center_y + (move_range_y / 2)
            elif self.pan_direction == 'left':
                start_x = center_x + (move_range_x / 2)
                end_x = center_x - (move_range_x / 2)
            elif self.pan_direction == 'right':
                start_x = center_x - (move_range_x / 2)
                end_x = center_x + (move_range_x / 2)
            elif self.pan_direction == 'diagonal_up_right':
                start_x = center_x - (move_range_x / 2)
                start_y = center_y + (move_range_y / 2)
                end_x = center_x + (move_range_x / 2)
                end_y = center_y - (move_range_y / 2)
            elif self.pan_direction == 'diagonal_up_left':
                start_x = center_x + (move_range_x / 2)
                start_y = center_y + (move_range_y / 2)
                end_x = center_x - (move_range_x / 2)
                end_y = center_y - (move_range_y / 2)
            elif self.pan_direction == 'diagonal_down_right':
                start_x = center_x - (move_range_x / 2)
                start_y = center_y - (move_range_y / 2)
                end_x = center_x + (move_range_x / 2)
                end_y = center_y + (move_range_y / 2)
            elif self.pan_direction == 'diagonal_down_left':
                start_x = center_x + (move_range_x / 2)
                start_y = center_y - (move_range_y / 2)
                end_x = center_x - (move_range_x / 2)
                end_y = center_y + (move_range_y / 2)
            
            # Interpolar entre los puntos inicial y final basado en el progreso
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
            
            # Asegurar que los offsets estén dentro de los límites
            current_x = max(0, min(max_offset_x, current_x))
            current_y = max(0, min(max_offset_y, current_y))
            
            # Recortar la imagen para obtener la parte visible
            crop_box = (
                int(current_x),
                int(current_y),
                int(current_x + base_size[0]),
                int(current_y + base_size[1])
            )
            
            # Asegurarse de que el recorte está dentro de los límites de la imagen
            crop_box = (
                max(0, crop_box[0]),
                max(0, crop_box[1]),
                min(new_size[0], crop_box[2]),
                min(new_size[1], crop_box[3])
            )
            
            # Verificar que el recorte tiene dimensiones válidas
            if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
                print(f"Advertencia: Recorte inválido en KenBurnsEffect (t={t:.2f}). Usando frame original.")
                result = np.array(img)
            else:
                img_result = img_zoomed.crop(crop_box)

                # Si el tamaño del recorte no coincide con el tamaño base, redimensionar
                if img_result.size != base_size:
                    img_result = img_result.resize(base_size, Resampling.LANCZOS)
                
                result = np.array(img_result)
                img_result.close()
            
            # Liberar recursos
            img.close()
            img_zoomed.close()
            
            return result
        except Exception as e:
            print(f"Error en KenBurnsEffect (t={t:.2f}): {e}. Devolviendo frame original.")
            return get_frame(t)


# Variantes predefinidas del efecto Ken Burns con diferentes configuraciones

class KenBurnsZoomInPanRight(KenBurnsEffect):
    """Ken Burns: Zoom In + Pan Right (efecto clásico de documental)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.4, clip_duration=None):
        super().__init__(zoom_direction='in', pan_direction='right', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor, clip_duration=clip_duration)


class KenBurnsZoomOutPanLeft(KenBurnsEffect):
    """Ken Burns: Zoom Out + Pan Left (variante dramática)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.4, clip_duration=None):
        super().__init__(zoom_direction='out', pan_direction='left', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor, clip_duration=clip_duration)


class KenBurnsDiagonalIn(KenBurnsEffect):
    """Ken Burns: Zoom In + Paneo Diagonal (muy dinámico)"""
    def __init__(self, zoom_ratio=0.04, pan_speed=0.05, scale_factor=1.5, clip_duration=None):
        super().__init__(zoom_direction='in', pan_direction='diagonal_up_right', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor, clip_duration=clip_duration)


class KenBurnsDiagonalOut(KenBurnsEffect):
    """Ken Burns: Zoom Out + Paneo Diagonal (variante cinematográfica)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.5, clip_duration=None):
        super().__init__(zoom_direction='out', pan_direction='diagonal_down_left', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor, clip_duration=clip_duration)
        
class FlipEffect(Effect):
    """
    Voltea la imagen horizontal o verticalmente (efecto estático).
    No necesita clip_duration ya que no varía con el tiempo.
    """
    def __init__(self, direction='horizontal'):
        self.direction = direction.lower()

    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        img = None
        img_flipped = None
        try:
            # t no se usa aquí, el efecto es constante
            img = Image.fromarray(get_frame(t))

            if self.direction == 'horizontal':
                img_flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif self.direction == 'vertical':
                img_flipped = img.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                img_flipped = img # Sin cambios si la dirección no es válida

            result = np.array(img_flipped)
            return result
        except Exception as e:
            print(f"Error en {self.__class__.__name__} (t={t:.2f}): {e}. Devolviendo frame original.")
            return get_frame(t)
        finally:
             if img_flipped and img_flipped is not img: img_flipped.close()
             if img: img.close()
             
# --- Añade esto a tu archivo de efectos ---

class ZoomBounceEffect(Effect):
    """
    Efecto de zoom con rebote: realiza un zoom in rápido seguido de un pequeño rebote (overshoot y retorno),
    y luego un zoom in progresivo hasta el final del clip si la duración es larga.
    """
    def __init__(self, zoom_ratio=0.3, bounce_intensity=0.1, clip_duration=2.0, quality='high', zoom_final=0.2, bounce_duration=None):
        """
        Args:
            zoom_ratio: Factor de zoom principal (ejemplo 0.3 para 30% de zoom).
            bounce_intensity: Porcentaje extra de zoom para el rebote (ejemplo 0.1 para 10% de overshoot).
            clip_duration: Duración total del efecto.
            quality: Calidad del redimensionado ('high' para LANCZOS, 'medium' para BILINEAR).
            zoom_final: Zoom adicional tras el rebote, aplicado progresivamente hasta el final del clip (ejemplo 0.2 para 20% más de zoom).
            bounce_duration: Duración del rebote inicial (en segundos). Si None, será el 25% del clip o 2s, lo que sea menor.
        """
        self.zoom_ratio = zoom_ratio
        self.bounce_intensity = bounce_intensity
        self.clip_duration = max(0.1, clip_duration)
        self.resample_mode = Resampling.LANCZOS if quality == 'high' else Resampling.BILINEAR
        self.zoom_final = zoom_final
        if bounce_duration is None:
            self.bounce_duration = min(2.0, 0.25 * self.clip_duration)
        else:
            self.bounce_duration = min(bounce_duration, self.clip_duration)

    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        try:
            img = Image.fromarray(get_frame(t))
            base_size = img.size
            # --- Zoom Bounce (rebote inicial) ---
            if t < self.bounce_duration:
                t_norm = t / self.bounce_duration
                s = 1.70158
                if t_norm < 0.8:
                    zoom = 1 + self.zoom_ratio * (t_norm * t_norm * ((s + 1) * t_norm - s))
                else:
                    t_bounce = (t_norm - 0.8) / 0.2
                    overshoot = self.zoom_ratio * (1 + self.bounce_intensity)
                    zoom = 1 + overshoot * (1 - t_bounce) * (1 - t_bounce)
                zoom = max(1.0, zoom)
            else:
                # --- Zoom progresivo (in) tras el rebote ---
                t_norm = (t - self.bounce_duration) / max(0.01, (self.clip_duration - self.bounce_duration))
                # Zoom inicial tras rebote:
                s = 1.70158
                zoom_start = 1 + self.zoom_ratio * (0.8 * 0.8 * ((s + 1) * 0.8 - s))
                zoom_start = max(1.0, zoom_start)
                zoom_end = zoom_start + self.zoom_final
                zoom = zoom_start + (zoom_end - zoom_start) * t_norm
            # Redimensionar la imagen
            new_size = (
                max(1, int(base_size[0] * zoom)),
                max(1, int(base_size[1] * zoom))
            )
            img_zoomed = img.resize(new_size, self.resample_mode)
            # Centrar el recorte
            left = (new_size[0] - base_size[0]) // 2
            top = (new_size[1] - base_size[1]) // 2
            crop_box = (
                left,
                top,
                left + base_size[0],
                top + base_size[1]
            )
            img_result = img_zoomed.crop(crop_box)
            result = np.array(img_result)
            img.close()
            img_zoomed.close()
            img_result.close()
            return result
        except Exception as e:
            print(f"Error en ZoomBounceEffect (t={t:.2f}): {e}. Devolviendo frame original.")
            return get_frame(t)

class VignetteZoomEffect(Effect):
    """
    Combina un efecto de zoom (in o out) con un viñeteado gradual.
    """
    def __init__(self,
                 # Parámetros de Zoom
                 zoom_in=True,
                 zoom_ratio=0.04, # Factor de zoom por segundo relativo a la duración
                 # Parámetros de Vignette
                 vignette_strength=0.7,
                 vignette_radius=0.8,
                 vignette_fade_duration=2.0,
                 # Duración del clip (¡Importante!)
                 clip_duration=5.0):
        """
        Inicializa el efecto combinado.

        Args:
            zoom_in: True para zoom in, False para zoom out.
            zoom_ratio: Factor de zoom por segundo (más alto = más rápido).
            vignette_strength: Fuerza del oscurecimiento del viñeteado (0.0 a 1.0).
            vignette_radius: Radio del área central clara del viñeteado (0.0 a 1.0).
            vignette_fade_duration: Tiempo para que el viñeteado alcance su fuerza máxima.
            clip_duration: Duración TOTAL del clip al que se aplica el efecto.
        """
        # Zoom params
        self.zoom_in = zoom_in
        self.zoom_ratio = zoom_ratio

        # Vignette params
        self.vignette_strength = np.clip(vignette_strength, 0.0, 1.0)
        self.vignette_radius = np.clip(vignette_radius, 0.01, 1.0)
        self.vignette_fade_duration = max(0.1, vignette_fade_duration)

        # Common params
        self.clip_duration = max(0.1, clip_duration) # Evitar división por cero
        self._mask = None # Cache para la máscara de viñeteado
        self._mask_shape = None

    def _create_vignette_mask(self, shape):
        """Crea la máscara de viñeteado (va de 1 en el centro a ~0 en los bordes)."""
        height, width = shape[:2]
        center_x, center_y = width / 2, height / 2
        Y, X = np.ogrid[:height, :width]
        dist_normalized = np.sqrt( ((X - center_x)/(width/2.))**2 + ((Y - center_y)/(height/2.))**2 )
        falloff_factor = 4
        mask = 1.0 - np.clip(dist_normalized / self.vignette_radius, 0, 1)**falloff_factor
        return mask[:, :, np.newaxis] # Añadir dimensión para broadcasting RGB

    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        # --- Lógica de Zoom (Corregida con clip_duration) ---
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        progress = t / self.clip_duration # Progreso normalizado (0 a 1)

        if self.zoom_in:
            # Zoom In: Tamaño aumenta con el tiempo
            current_zoom = 1 + (self.zoom_ratio * self.clip_duration * progress)
        else:
            # Zoom Out: Tamaño disminuye con el tiempo
            # Empieza grande (zoom_factor al final) y se reduce a 1
            max_zoom_factor = 1 + self.zoom_ratio * self.clip_duration
            current_zoom = max_zoom_factor - (self.zoom_ratio * self.clip_duration * progress)
            current_zoom = max(1.0, current_zoom) # No reducir más allá del tamaño original

        # Calcular nuevo tamaño y asegurar que sea par
        new_size = (math.ceil(base_size[0] * current_zoom), math.ceil(base_size[1] * current_zoom))
        new_size = (new_size[0] + (new_size[0] % 2), new_size[1] + (new_size[1] % 2))

        # Redimensionar
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Calcular recorte para volver al tamaño original
        x = max(0, math.ceil((new_size[0] - base_size[0]) / 2))
        y = max(0, math.ceil((new_size[1] - base_size[1]) / 2))
        box = (x, y, x + base_size[0], y + base_size[1])

        # Recortar a tamaño original
        # Puede que necesite ajustar si box excede img_resized.size con zooms muy rápidos
        # Pero para zooms moderados debería estar bien.
        img_zoomed = img_resized.crop(box)
        # Asegurar tamaño final exacto si el recorte fue impreciso
        if img_zoomed.size != base_size:
             img_zoomed = img_zoomed.resize(base_size, Image.Resampling.LANCZOS)

        # Convertir la imagen zoomeada a array para aplicar viñeteado
        zoomed_array = np.array(img_zoomed)
        img.close()
        img_resized.close()
        img_zoomed.close()

        # --- Lógica de Vignette ---
        current_vignette_strength = self.vignette_strength * min(1.0, t / self.vignette_fade_duration)

        # Crear o reutilizar la máscara de viñeteado (basada en el tamaño final/base)
        if self._mask is None or self._mask_shape != zoomed_array.shape:
            self._mask = self._create_vignette_mask(zoomed_array.shape)
            self._mask_shape = zoomed_array.shape

        # Aplicar la máscara para oscurecer los bordes del frame zoomeado
        vignette_factor = 1.0 - current_vignette_strength * (1.0 - self._mask)
        final_frame = np.clip(zoomed_array * vignette_factor, 0, 255)

        return final_frame.astype(np.uint8)
    
    
    
class RotateEffect(Effect):
    """
    Efecto que rota la imagen gradualmente alrededor de su centro.
    """
    def __init__(self, speed=30, direction='clockwise', clip_duration=5.0):
        """
        Inicializa el efecto de rotación.

        Args:
            speed: Velocidad de rotación en grados por segundo.
            direction: Dirección de la rotación ('clockwise' o 'counter-clockwise').
            clip_duration: Duración del clip al que se aplicará el efecto (¡Importante!).
        """
        self.speed = speed
        self.direction_multiplier = 1 if direction.lower() == 'clockwise' else -1
        self.clip_duration = clip_duration # Guarda la duración real del clip

    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        # Obtener el frame
        img = Image.fromarray(get_frame(t))
        original_size = img.size

        # Calcular el ángulo actual basado en el tiempo y la velocidad
        current_angle = (self.speed * t * self.direction_multiplier) % 360

        # Rotar la imagen
        # expand=False evita que la imagen cambie de tamaño, pero corta las esquinas.
        # expand=True mantiene toda la imagen pero cambia el tamaño, requeriría un recorte complejo.
        # Usamos BILINEAR para velocidad, LANCZOS es más lento pero de mayor calidad.
        rotated_img = img.rotate(current_angle, resample=Image.Resampling.BILINEAR, expand=False)

        # Asegurarse de que la imagen rotada tenga el tamaño original (si expand=False, ya lo tiene)
        if rotated_img.size != original_size:
             # Si usáramos expand=True, aquí necesitaríamos recortar al centro
             # Pero con expand=False, esto no debería ser necesario.
             rotated_img = rotated_img.crop((0, 0, original_size[0], original_size[1]))


        result = np.array(rotated_img)
        img.close()
        rotated_img.close()
        return result