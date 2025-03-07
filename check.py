# Versión corregida de check.py
import moviepy
from moviepy import *

print(f"MoviePy versión: {moviepy.__version__}")

# Verificar que FFmpeg está disponible
import subprocess
try:
    subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
    print("FFmpeg está correctamente instalado")
except:
    print("FFmpeg no está instalado o no está en el PATH")