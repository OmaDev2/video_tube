

import re
import math
from pathlib import Path # Si es necesario





def sanitize_filename(filename):
        """Limpia un string para usarlo como nombre de archivo/carpeta seguro."""
        # Quitar caracteres inválidos
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        # Reemplazar espacios con guiones bajos
        sanitized = sanitized.replace(" ", "_")
        # Limitar longitud
        return sanitized[:100]  # Limitar a 100 caracteres
    
    
def calcular_imagenes_optimas(audio_duration, duracion_por_imagen=6.0, duracion_transicion=1.0, aplicar_transicion=False, fade_in=2.0, fade_out=2.0, respetar_duracion_exacta=True, repetir_ultimo_clip_config=True): # Renombrado arg
        """
        Calcula el número óptimo de imágenes y sus tiempos basado en la duración del audio.
        (Código de esta función sin cambios respecto a la versión anterior tuya)
        """
        # --- Código de calcular_imagenes_optimas sin cambios ---
        # ... (pega aquí tu código existente para calcular_imagenes_optimas) ...
        # Asegúrate de que al final devuelva: return num_imagenes, tiempos_imagenes
        # --- Ejemplo resumido de la lógica ---
        print(f"Calculando imágenes para audio de {audio_duration:.2f} segundos.")
        print(f" - Duración deseada: {duracion_por_imagen:.2f}s, Transición: {duracion_transicion:.2f}s (Aplicada: {aplicar_transicion})")
        print(f" - Respetar Duración: {respetar_duracion_exacta}, Repetir Último: {repetir_ultimo_clip_config}")

        num_imagenes = 1
        tiempos_imagenes = []
        duracion_efectiva = audio_duration # Simplificado, ya que fades no afectan cálculo aquí

        # Asegurar que la duración por imagen sea válida
        try:
             duracion_por_imagen = float(duracion_por_imagen)
             if duracion_por_imagen <= 0:
                  print("ADVERTENCIA: Duración por imagen <= 0. Ajustando a 1s.")
                  duracion_por_imagen = 1.0
        except (ValueError, TypeError):
             print("ADVERTENCIA: Duración por imagen inválida. Usando 15s.")
             duracion_por_imagen = 15.0

        # Asegurar duración transición válida
        try:
             duracion_transicion = float(duracion_transicion)
             if duracion_transicion < 0: duracion_transicion = 0.0
        except (ValueError, TypeError):
             duracion_transicion = 0.0 # Sin transición si el valor es inválido

        # Lógica principal (simplificada para ejemplo, usa tu lógica completa)
        if aplicar_transicion and duracion_transicion > 0:
             solapamiento = duracion_transicion / 2.0
             # Fórmula ajustada para estimar N imágenes con N-1 transiciones
             # total_dur = N * img_dur - (N-1) * solapamiento
             if duracion_por_imagen <= solapamiento:
                  print(f"Advertencia: Duración imagen ({duracion_por_imagen}) <= solapamiento ({solapamiento}). Ajustando a 1 imagen.")
                  num_imagenes = 1
                  duracion_ajustada = duracion_efectiva
             else:
                  # Estimación inicial (puede requerir tu lógica más compleja para videos largos)
                  num_imagenes = math.ceil((duracion_efectiva + solapamiento) / (duracion_por_imagen - solapamiento))
                  num_imagenes = max(2, num_imagenes) # Necesita al menos 2 para transición

                  # Recalcular duración para ajustar exactamente
                  duracion_ajustada = (duracion_efectiva + (num_imagenes - 1) * solapamiento) / num_imagenes
                  print(f"Ajuste con transiciones: {num_imagenes} imágenes, duración ajustada {duracion_ajustada:.2f}s")

             # Calcular tiempos con solapamiento
             tiempo_actual = 0.0
             for i in range(num_imagenes):
                  inicio = tiempo_actual
                  # El clip necesita durar 'duracion_ajustada' en total
                  fin_visual = inicio + duracion_ajustada
                  # El siguiente clip empieza antes si no es el último
                  if i < num_imagenes - 1:
                       tiempo_actual = fin_visual - solapamiento
                  else:
                       fin_visual = duracion_efectiva # Último clip termina exacto
                       tiempo_actual = duracion_efectiva
                  duracion_clip = fin_visual - inicio
                  tiempos_imagenes.append({'indice': i, 'inicio': inicio, 'fin': fin_visual, 'duracion': duracion_clip})

        else: # Sin transiciones
             if respetar_duracion_exacta:
                  # ... (tu lógica para respetar duración exacta y posible repetición) ...
                  num_imagenes_completas = int(duracion_efectiva / duracion_por_imagen) if duracion_por_imagen > 0 else 0
                  tiempo_restante = duracion_efectiva - (num_imagenes_completas * duracion_por_imagen)
                  umbral = 0.1 # Umbral pequeño para decidir si añadir clip

                  repetir_flag = False
                  tiempo_repeticion = 0.0

                  if tiempo_restante < umbral and num_imagenes_completas > 0:
                       num_imagenes = num_imagenes_completas
                  elif repetir_ultimo_clip_config and tiempo_restante < duracion_por_imagen * 0.7 and num_imagenes_completas > 0:
                       num_imagenes = num_imagenes_completas
                       repetir_flag = True
                       tiempo_repeticion = tiempo_restante
                       print(f"Repitiendo último clip por {tiempo_repeticion:.2f}s")
                  else:
                       num_imagenes = num_imagenes_completas + 1

                  num_imagenes = max(1, num_imagenes) # Al menos 1

                  tiempo_actual = 0.0
                  for i in range(num_imagenes):
                       inicio = tiempo_actual
                       if i == num_imagenes - 1: # Última imagen
                            if repetir_flag:
                                fin = inicio + duracion_por_imagen + tiempo_repeticion
                            else:
                                fin = duracion_efectiva
                       else:
                            fin = inicio + duracion_por_imagen
                       duracion_clip = fin - inicio
                       clip_info = {'indice': i, 'inicio': inicio, 'fin': fin, 'duracion': duracion_clip}
                       if i == num_imagenes -1 and repetir_flag:
                            clip_info['repetir'] = True
                            clip_info['tiempo_repeticion'] = tiempo_repeticion
                       tiempos_imagenes.append(clip_info)
                       tiempo_actual = fin

             else: # Distribuir uniformemente sin transiciones
                  num_imagenes = math.ceil(duracion_efectiva / duracion_por_imagen) if duracion_por_imagen > 0 else 1
                  num_imagenes = max(1, num_imagenes)
                  duracion_ajustada = duracion_efectiva / num_imagenes
                  print(f"Distribución uniforme: {num_imagenes} imágenes, duración {duracion_ajustada:.2f}s")
                  tiempo_actual = 0.0
                  for i in range(num_imagenes):
                       inicio = tiempo_actual
                       fin = min(inicio + duracion_ajustada, duracion_efectiva) if i < num_imagenes - 1 else duracion_efectiva
                       duracion_clip = fin - inicio
                       tiempos_imagenes.append({'indice': i, 'inicio': inicio, 'fin': fin, 'duracion': duracion_clip})
                       tiempo_actual = fin

        # Validación final (opcional pero recomendada)
        if tiempos_imagenes and abs(tiempos_imagenes[-1]['fin'] - duracion_efectiva) > 0.05:
            print(f"ADVERTENCIA: Tiempo final ({tiempos_imagenes[-1]['fin']:.2f}) no coincide con duración audio ({duracion_efectiva:.2f}). Ajustando.")
            tiempos_imagenes[-1]['fin'] = duracion_efectiva
            tiempos_imagenes[-1]['duracion'] = tiempos_imagenes[-1]['fin'] - tiempos_imagenes[-1]['inicio']

        print(f"Cálculo final: {num_imagenes} imágenes.")
        #for t in tiempos_imagenes: print(f"  {t}") # Descomentar para depuración detallada

        return num_imagenes, tiempos_imagenes
        # --- Fin Ejemplo resumido ---