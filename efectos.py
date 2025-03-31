from collections.abc import Callable
from moviepy import *
from PIL import Image
from PIL.Image import Resampling
import math
import numpy as np

class ZoomEffect(Effect):
    """Efecto de zoom que permite hacer zoom in o zoom out en una imagen."""
    
    def __init__(self, zoom_in=True, ratio=0.04):
        """Inicializa el efecto de zoom.
        
        Args:
            zoom_in: Si es True, hace zoom in. Si es False, hace zoom out.
            ratio: Factor de zoom por segundo. Valores más altos resultan en zoom más rápido.
        """
        self.zoom_in = zoom_in
        self.ratio = ratio
        
        # Para zoom out, usamos un valor positivo pero aplicamos una lógica diferente
        # en el método apply
    
    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        # Obtener el frame
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        
        if self.zoom_in:
            # Zoom In: Empezamos con imagen normal y la agrandamos
            zoom_factor = 1 + (self.ratio * t)
        else:
            # Zoom Out: Empezamos con imagen más grande y la reducimos
            # Calculamos el factor máximo para el final del clip
            max_zoom = 1 + (self.ratio * 5)  # Asumiendo duración de 5 segundos
            # Empezamos con el zoom máximo y vamos reduciendo
            zoom_factor = max_zoom - (self.ratio * t)
        
        # Calcular el nuevo tamaño
        new_size = (
            math.ceil(img.size[0] * zoom_factor),
            math.ceil(img.size[1] * zoom_factor),
        )

        # Hacer el tamaño par
        new_size = (
            new_size[0] + (new_size[0] % 2),
            new_size[1] + (new_size[1] % 2),
        )

        # Redimensionar la imagen
        img = img.resize(new_size, Resampling.LANCZOS)

        # Recortar la imagen
        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)
        img = img.crop((x, y, new_size[0] - x, new_size[1] - y)).resize(
            base_size, Resampling.LANCZOS
        )

        # Convertir a array de numpy y retornar
        result = np.array(img)
        img.close()
        return result
    
class PanEffect(Effect):
    """Efecto base para los efectos de paneo que mueve una 'cámara virtual' sobre una imagen."""
    
    def __init__(self, direction='up', speed=0.12, scale_factor=1.2):
        """Inicializa el efecto de paneo.
        
        Args:
            direction: Dirección del paneo ('up', 'down', 'left', 'right')
            speed: Velocidad del paneo como fracción de la imagen por segundo.
                   Valores más altos resultan en un paneo más rápido.
            scale_factor: Factor para redimensionar la imagen original antes del paneo.
                         Valores más altos permiten más movimiento pero pueden reducir calidad.
        """
        self.direction = direction.lower()
        self.speed = speed
        self.scale_factor = scale_factor
        self.clip_duration = None
        
    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
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
        scaled_img = img.resize(scaled_size, Resampling.LANCZOS)
        
        # Calcular el desplazamiento máximo posible (el rango en el que podemos movernos)
        max_offset_x = scaled_size[0] - base_size[0]
        max_offset_y = scaled_size[1] - base_size[1]
        
        # Calcular posición inicial (centro)
        start_x = max_offset_x // 2
        start_y = max_offset_y // 2
        
        # Inicializar offset con la posición central
        offset_x = start_x
        offset_y = start_y
        
        # Obtener la duración del clip si no la tenemos
        if self.clip_duration is None:
            # Intentar obtener la duración del clip actual
            try:
                # Intentamos acceder al atributo 'duration' del clip actual
                # Esto funciona si el clip tiene un atributo duration
                from moviepy import VideoClip
                current_clip = VideoClip.current_clip
                if hasattr(current_clip, 'duration'):
                    self.clip_duration = current_clip.duration
                else:
                    # Si no podemos obtener la duración, usamos un valor por defecto más largo
                    self.clip_duration = 30.0  # Valor suficientemente grande para la mayoría de casos
            except (ImportError, AttributeError, NameError):
                # Si hay algún error, usamos un valor por defecto más largo
                self.clip_duration = 30.0
        
        # Calcular el desplazamiento basado en el tiempo y la dirección
        # Limitamos el movimiento al 80% del desplazamiento máximo para evitar llegar a los bordes
        movement_range = 0.8
        
        # Calcular el progreso normalizado (0.0 a 1.0) basado en el tiempo actual
        # Usamos la duración real del clip o un valor suficientemente grande
        progress = t / self.clip_duration
        # Aseguramos que el progreso esté entre 0 y 1
        progress = max(0.0, min(1.0, progress))
        
        if self.direction == 'up':
            # Para "up", nos movemos desde abajo hacia arriba (valores de y más pequeños)
            max_movement = max_offset_y * movement_range
            offset_y = start_y + max_offset_y * movement_range * 0.5 - (progress * max_movement)
        elif self.direction == 'down':
            # Para "down", nos movemos desde arriba hacia abajo (valores de y más grandes)
            max_movement = max_offset_y * movement_range
            offset_y = start_y - max_offset_y * movement_range * 0.5 + (progress * max_movement)
        elif self.direction == 'left':
            # Para "left", nos movemos desde derecha hacia izquierda (valores de x más pequeños)
            max_movement = max_offset_x * movement_range
            offset_x = start_x + max_offset_x * movement_range * 0.5 - (progress * max_movement)
        elif self.direction == 'right':
            # Para "right", nos movemos desde izquierda hacia derecha (valores de x más grandes)
            max_movement = max_offset_x * movement_range
            offset_x = start_x - max_offset_x * movement_range * 0.5 + (progress * max_movement)
        
        # Asegurar que los offsets estén dentro de los límites
        offset_x = max(0, min(max_offset_x, offset_x))
        offset_y = max(0, min(max_offset_y, offset_y))
        
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
        img.close()
        scaled_img.close()
        img_result.close()
        return result

class PanUpEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de abajo hacia arriba sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2):
        super().__init__(direction='up', speed=speed, scale_factor=scale_factor)


class PanDownEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de arriba hacia abajo sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2):
        super().__init__(direction='down', speed=speed, scale_factor=scale_factor)


class PanLeftEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de derecha a izquierda sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2):
        super().__init__(direction='left', speed=speed, scale_factor=scale_factor)


class PanRightEffect(PanEffect):
    """Efecto que mueve la 'cámara virtual' de izquierda a derecha sobre la imagen."""
    
    def __init__(self, speed=0.12, scale_factor=1.2):
        super().__init__(direction='right', speed=speed, scale_factor=scale_factor)


class KenBurnsEffect(Effect):
    """
    Efecto Ken Burns que combina zoom y paneo para crear una sensación de movimiento cinematográfico.
    El efecto Ken Burns clásico consiste en un movimiento lento de zoom mientras simultáneamente
    se realiza un paneo suave sobre diferentes áreas de la imagen.
    """
    
    def __init__(self, zoom_direction='in', pan_direction='up', 
                 zoom_ratio=0.05, pan_speed=0.12, scale_factor=1.3):
        """Inicializa el efecto Ken Burns.
        
        Args:
            zoom_direction: Dirección del zoom ('in' o 'out')
            pan_direction: Dirección del paneo ('up', 'down', 'left', 'right', 'diagonal_up_right',
                          'diagonal_up_left', 'diagonal_down_right', 'diagonal_down_left')
            zoom_ratio: Factor de zoom por segundo
            pan_speed: Velocidad del paneo
            scale_factor: Factor para redimensionar la imagen original
        """
        self.zoom_in = zoom_direction.lower() == 'in'
        self.zoom_ratio = zoom_ratio
        self.pan_direction = pan_direction.lower()
        self.pan_speed = pan_speed
        self.scale_factor = scale_factor
    
    def apply(self, get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
        # Obtener el frame original
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        
        # Duración estimada para cálculo de movimiento
        estimated_duration = 5.0  # segundos
        progress = min(1.0, t / estimated_duration)
        
        # Calcular el factor de zoom basado en la dirección y el tiempo
        if self.zoom_in:
            # Zoom In: Empezamos con imagen normal y la agrandamos
            zoom_factor = 1 + (self.zoom_ratio * t)
        else:
            # Zoom Out: Empezamos con imagen más grande y la reducimos
            max_zoom = 1 + (self.zoom_ratio * estimated_duration)
            zoom_factor = max_zoom - (self.zoom_ratio * t)
        
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
        
        # Aplicar curva de aceleración/desaceleración (ease in-out)
        # Esto hace que el movimiento sea más natural
        if progress < 0.5:
            # Aceleración inicial (ease in)
            ease_factor = 2 * progress * progress
        else:
            # Desaceleración final (ease out)
            ease_factor = -1 + (4 * progress) - (2 * progress * progress)
        
        # Calcular posición actual usando interpolación con factor de facilidad
        current_x = start_x + (end_x - start_x) * ease_factor
        current_y = start_y + (end_y - start_y) * ease_factor
        
        # Asegurar que los offsets estén dentro de los límites
        offset_x = max(0, min(max_offset_x, int(current_x)))
        offset_y = max(0, min(max_offset_y, int(current_y)))
        
        # Recortar la imagen para obtener la parte visible
        crop_box = (
            offset_x,
            offset_y,
            offset_x + base_size[0],
            offset_y + base_size[1]
        )
        
        # Asegurarse de que el recorte está dentro de los límites de la imagen
        crop_box = (
            max(0, crop_box[0]),
            max(0, crop_box[1]),
            min(new_size[0], crop_box[2]),
            min(new_size[1], crop_box[3])
        )
        
        # Verificar que el tamaño del recorte sea correcto
        if crop_box[2] - crop_box[0] != base_size[0] or crop_box[3] - crop_box[1] != base_size[1]:
            # Ajustar el recorte para mantener el tamaño original
            crop_width = min(base_size[0], new_size[0])
            crop_height = min(base_size[1], new_size[1])
            
            # Ajustar el recorte para mantener centrada la imagen
            crop_box = (
                max(0, (new_size[0] - crop_width) // 2),
                max(0, (new_size[1] - crop_height) // 2),
                min(new_size[0], max(0, (new_size[0] - crop_width) // 2) + crop_width),
                min(new_size[1], max(0, (new_size[1] - crop_height) // 2) + crop_height)
            )
        
        img_result = img_zoomed.crop(crop_box)
        
        # Redimensionar al tamaño original si es necesario
        if img_result.size != base_size:
            img_result = img_result.resize(base_size, Resampling.LANCZOS)
        
        # Convertir a array de numpy y retornar
        result = np.array(img_result)
        img.close()
        img_zoomed.close()
        img_result.close()
        return result


# Variantes predefinidas del efecto Ken Burns con diferentes configuraciones

class KenBurnsZoomInPanRight(KenBurnsEffect):
    """Ken Burns: Zoom In + Pan Right (efecto clásico de documental)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.4):
        super().__init__(zoom_direction='in', pan_direction='right', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor)


class KenBurnsZoomOutPanLeft(KenBurnsEffect):
    """Ken Burns: Zoom Out + Pan Left (variante dramática)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.4):
        super().__init__(zoom_direction='out', pan_direction='left', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor)


class KenBurnsDiagonalIn(KenBurnsEffect):
    """Ken Burns: Zoom In + Paneo Diagonal (muy dinámico)"""
    def __init__(self, zoom_ratio=0.04, pan_speed=0.05, scale_factor=1.5):
        super().__init__(zoom_direction='in', pan_direction='diagonal_up_right', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor)


class KenBurnsDiagonalOut(KenBurnsEffect):
    """Ken Burns: Zoom Out + Paneo Diagonal (variante cinematográfica)"""
    def __init__(self, zoom_ratio=0.03, pan_speed=0.04, scale_factor=1.5):
        super().__init__(zoom_direction='out', pan_direction='diagonal_down_left', 
                         zoom_ratio=zoom_ratio, pan_speed=pan_speed, 
                         scale_factor=scale_factor)