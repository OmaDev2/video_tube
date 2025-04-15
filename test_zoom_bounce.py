from moviepy import *
from efectos import ZoomBounceEffect
import os

# Carpeta y nombre de la imagen de prueba (ajusta si es necesario)
IMG_DIR = "Tests/imagenes_test"
IMAGEN = "foto1.jpg"  # Cambia por el nombre real de tu imagen
DURACION = 8  # segundos

os.makedirs("videos_prueba", exist_ok=True)

img_path = os.path.join(IMG_DIR, IMAGEN)
effect = ZoomBounceEffect(zoom_ratio=0.3, bounce_intensity=0.12, clip_duration=DURACION, zoom_final=0.2)

def make_frame(t):
    return effect.apply(lambda _: ImageClip(img_path).get_frame(0), t)

clip = VideoClip(make_frame, duration=DURACION).with_fps(24)
clip.write_videofile("videos_prueba/zoom_bounce_test.mp4", fps=24, codec="libx264")
print("Video generado: videos_prueba/zoom_bounce_test.mp4")
