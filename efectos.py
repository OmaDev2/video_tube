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