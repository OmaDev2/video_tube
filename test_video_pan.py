import os
from moviepy import *
from efectos import PanEffect

# Ruta de las imágenes de prueba
IMG_DIR = "Tests/imagenes_test"
IMAGENES = [
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_001.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_002.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_003.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_004.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_005.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_006.png",
    "Milagros_de_Santa_Eduviges_Esperanza_para_los_Endeudados_y_Matrimonios_en_Crisis_007.png"
]

# Parámetros de prueba
DURACIONES = [8, 15, 20]  # segundos
SPEED = 100  # píxeles por segundo
DIRECCION = 'right'

os.makedirs("videos_prueba", exist_ok=True)

for duracion in DURACIONES:
    clips = []
    for img_name in IMAGENES:
        path = os.path.join(IMG_DIR, img_name)
        effect = PanEffect(direction=DIRECCION, speed=SPEED, scale_factor=1.3, clip_duration=duracion)
        # Cargar imagen base
        img_clip = ImageClip(path)
        w, h = img_clip.size
        # Crear un VideoClip que aplica el efecto dinámico de paneo
        def make_frame(t):
            return effect.apply(lambda _: img_clip.get_frame(0), t)
        clip = VideoClip(make_frame, duration=duracion).with_fps(24)
        clips.append(clip)
    video = concatenate_videoclips(clips, method="compose")
    out_path = f"videos_prueba/pan_{DIRECCION}_{duracion}s.mp4"
    video.write_videofile(out_path, fps=24, codec="libx264")
    print(f"Video generado: {out_path}")

print("Todos los videos de prueba han sido generados en la carpeta videos_prueba.")
