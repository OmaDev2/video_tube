# test_list_models.py
import google.generativeai as genai
import os

print("Configurando API Key...")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY no encontrada.")
else:
    try:
        genai.configure(api_key=api_key)
        print("\nModelos disponibles que soportan 'generateContent':")
        count = 0
        for m in genai.list_models():
          if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            count += 1
        if count == 0:
             print("¡No se encontraron modelos compatibles!")
    except Exception as e:
        print(f"Error al listar modelos: {e}")

print("\nTest finalizado.")
