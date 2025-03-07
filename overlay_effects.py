from moviepy import *
import os
from glob import glob
import numpy as np

class OverlayEffect:
    """
    Clase para aplicar efectos de superposición (overlays) en videos.
    Permite superponer videos de efectos (como nieve, lluvia, partículas) sobre clips de imágenes.
    También permite aplicar diferentes overlays de forma secuencial a una serie de clips.
    """
    
    @staticmethod
    def get_available_overlays(overlay_dir):
        """
        Obtiene una lista de los archivos de overlay disponibles en el directorio especificado.
        
        Args:
            overlay_dir: Directorio donde se encuentran los archivos de overlay
            
        Returns:
            Lista de nombres de archivos de overlay disponibles
        """
        # Verificar que el directorio existe
        if not os.path.exists(overlay_dir):
            return []
        
        # Buscar archivos de video en el directorio
        formatos = ['*.mp4', '*.mov', '*.avi', '*.webm']
        archivos = []
        for formato in formatos:
            archivos.extend(glob(os.path.join(overlay_dir, formato)))
        
        # Obtener solo los nombres de archivo sin la ruta completa
        nombres = [os.path.basename(archivo) for archivo in archivos]
        return nombres
    
    @staticmethod
    def apply_overlay(base_clip, overlay_path, opacity=0.5):
        """
        Aplica un video de overlay sobre un clip base.
        
        Args:
            base_clip: Clip base sobre el que se aplicará el overlay
            overlay_path: Ruta al archivo de video de overlay
            opacity: Opacidad del overlay (0.0 a 1.0)
            
        Returns:
            Clip con el overlay aplicado
        """
        if not os.path.exists(overlay_path):
            print(f"Archivo de overlay no encontrado: {overlay_path}")
            return base_clip
        
        # Cargar el video de overlay
        overlay_clip = VideoFileClip(overlay_path)
        
        # Redimensionar el overlay para que coincida con el tamaño del clip base
        overlay_clip = overlay_clip.resized(base_clip.size)
        
        # Ajustar la opacidad del overlay
        overlay_clip = overlay_clip.with_opacity(opacity)
        
        # Implementar looping manual si es necesario
        if overlay_clip.duration < base_clip.duration:
            # Calcular cuántas repeticiones necesitamos
            repetitions = int(np.ceil(base_clip.duration / overlay_clip.duration))
            # Crear una lista de clips para concatenar
            clips_to_concat = [overlay_clip] * repetitions
            # Concatenar los clips
            extended_overlay = concatenate_videoclips(clips_to_concat)
            # Recortar al tamaño exacto que necesitamos
            overlay_clip = extended_overlay.with_duration(base_clip.duration)
        else:
            # Si el overlay es más largo, lo recortamos
            overlay_clip = overlay_clip.with_duration(base_clip.duration)
        
        # Combinar los clips
        final_clip = CompositeVideoClip([base_clip, overlay_clip])
        
        return final_clip
        
    @staticmethod
    def apply_sequential_overlays(clips, overlay_paths, opacity=0.5):
        """
        Aplica múltiples overlays de forma secuencial a una lista de clips.
        Cada clip recibe un overlay según su posición, rotando entre los overlays disponibles.
        
        Args:
            clips: Lista de clips base sobre los que se aplicarán los overlays
            overlay_paths: Lista de rutas a los archivos de overlay
            opacity: Opacidad de los overlays (0.0 a 1.0)
            
        Returns:
            Lista de clips con los overlays aplicados secuencialmente
        """
        if not clips or not overlay_paths:
            return clips
        
        # Verificar que todos los archivos de overlay existen
        valid_overlays = [path for path in overlay_paths if os.path.exists(path)]
        
        if not valid_overlays:
            print("Ninguno de los archivos de overlay especificados existe.")
            return clips
        
        # Aplicar overlays secuencialmente a cada clip
        clips_con_overlay = []
        for i, clip in enumerate(clips):
            # Seleccionar el overlay según la posición del clip (rotando)
            overlay_idx = i % len(valid_overlays)
            overlay_path = valid_overlays[overlay_idx]
            
            # Aplicar el overlay al clip actual
            print(f"Aplicando overlay {os.path.basename(overlay_path)} a la imagen {i+1}")
            clip_con_overlay = OverlayEffect.apply_overlay(clip, overlay_path, opacity)
            clips_con_overlay.append(clip_con_overlay)
        
        return clips_con_overlay