import numpy as np
from PIL import Image
from efectos import PanEffect

# Crear una imagen de prueba (800x600, fondo blanco)
def crear_imagen_prueba():
    img = Image.new('RGB', (800, 600), color='white')
    for x in range(200, 600):
        for y in range(150, 450):
            img.putpixel((x, y), (255, 0, 0))  # Añade un rectángulo rojo para ver el paneo
    return np.array(img)

def test_pan_effect(duracion, direccion, speed, nombre_salida):
    print(f"Probando PanEffect: duracion={duracion}s, direccion={direccion}, speed={speed}")
    effect = PanEffect(direction=direccion, speed=speed, scale_factor=1.3, clip_duration=duracion)
    frames = []
    for t in np.linspace(0, duracion, num=5):
        frame = effect.apply(lambda _: crear_imagen_prueba(), t)
        img = Image.fromarray(frame)
        img.save(f"{nombre_salida}_t{int(t)}.png")
        frames.append(img)
    print(f"Guardadas 5 imágenes para {nombre_salida}")

if __name__ == "__main__":
    test_pan_effect(8, 'right', 100, 'pan8s')
    test_pan_effect(15, 'right', 100, 'pan15s')
    test_pan_effect(20, 'right', 100, 'pan20s')
    print("Pruebas completadas. Revisa los archivos pan8s_t*.png, pan15s_t*.png, pan20s_t*.png.")
