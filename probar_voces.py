import asyncio
import edge_tts
from pathlib import Path

# --- Configuración ---

# 1. Lista de voces a probar
VOICES_TO_TEST = [
    "es-CR-JuanNeural",     # OK
    "es-EC-LuisNeural",     # OK
    "es-MX-JorgeNeural",    # OK
    "es-MX-DaliaNeural",    # OK
    "es-DO-EmilioNeural",   # Corregido: 'Neura' -> 'Neural'
    "es-VE-SebastianNeural",# Corregido: Faltaba 'es-'
    "es-PY-TaniaNeural",    # OK
    "es-UY-MateoNeural",    # OK
    "es-PR-KarinaNeural",   # Corregido: Eliminada 'l' extra al final
    "es-ES-AlvaroNeural",   # OK
    "es-CR-MariaNeural",    # OK
    "es-CU-ManuelNeural",   # OK
]

# 2. Texto LARGO de ejemplo que se usará para todas las voces
SAMPLE_TEXT = """Prepárate, porque lo que vas a escuchar puede que te incomode, puede que incluso te enfade. Durante siglos, la sociedad te ha vendido una idea de pureza, de santidad, como algo etéreo, inalcanzable, casi enfermizo. Te han dicho que la pureza es silencio, sumisión, ignorancia.


Te han hecho creer que los santos eran seres sin sangre en las venas, figuras de yeso rezando en altares polvorientos. Pero, ¿y si te dijera que la verdadera pureza es una rebeldía? ¿Y si la santidad no fuera esa palidez beata, sino una llama ardiente que se niega a ser apagada?


En esta historia, vas a conocer a Inés, una joven romana que vivió en el siglo tercero, en la época de la decadencia del Imperio, cuando Roma aún se creía el centro del mundo, pero ya estaba carcomida por dentro. Inés era noble, de una de esas familias patricias que se creían con derecho divino a gobernar.


Imagínatela, paseando por las calles empedradas de Roma, rodeada de lujos, con la belleza que seguramente cautivaba a cualquiera que se cruzara en su camino. Pero Inés, a pesar de su linaje y su juventud, tenía una mirada que iba más allá del mármol y el oro de su entorno.


Había abrazado una fe que entonces era perseguida, despreciada, considerada una superstición de esclavos y mujeres: el cristianismo. Y lo hizo con la fuerza y la convicción que solo tienen los jóvenes, cuando el mundo aún no ha tenido tiempo de corromper sus ideales. Inés, en medio de la opulencia romana, eligió la pobreza de espíritu.


En un mundo obsesionado con el poder, ella escogió la humildad. Y en una sociedad que veneraba los placeres carnales, Inés defendió una pureza que iba mucho más allá de lo físico, una pureza de alma, de corazón, una pureza que se convirtió en su mayor arma, en su mayor desafío al Imperio.


Si esta historia te resuena, si te provoca, si sientes curiosidad por descubrir qué hay detrás de esta joven que se atrevió a desafiar al poder más grande de su tiempo, te invito a seguir explorando con nosotros las "Vidas Santas".


Deja tu comentario, comparte tus reflexiones, suscríbete si quieres seguir descubriendo historias que te harán cuestionar lo que crees saber. Porque la santidad, la verdadera santidad, está mucho más cerca de ti de lo que imaginas, y puede que se parezca más a la rebeldía de Inés de lo que nunca te han contado.


En esta historia, te encuentras caminando por las calles empedradas de una Roma antigua, vibrante y a la vez, profundamente corrupta. El aire huele a incienso, a especias exóticas y, sutilmente, a la decadencia que se esconde tras la fachada de mármol y oro del imperio.


Has escuchado rumores, susurros sobre una joven, Inés, una belleza cuyo espíritu desafía la lógica de este mundo.


Te contaron que desde niña, Inés consagró su vida a una fe invisible, un amor que no se ve ni se toca, pero que arde en su corazón con una intensidad que desconcierta a los hombres y exaspera a las autoridades.


Imagínate la escena:  Inés, apenas una adolescente, rechaza pretendientes de noble cuna, hombres poderosos y ricos que ven en ella un trofeo, una joya para exhibir. Los desprecia con una serenidad que es más hiriente que cualquier insulto.


¿Cómo se atreve esta joven a rechazar el honor que le ofrecen, a preferir un amor etéreo a las glorias terrenales?


Observas cómo la admiración inicial del pueblo romano, esa fascinación morbosa por la rareza, comienza a transformarse en algo más profundo, algo inquietante para el poder establecido.


La gente común, los esclavos, los comerciantes, los artesanos, todos ven en Inés un reflejo de algo que anhelan en secreto:  una pureza, una integridad que contrasta brutalmente con la hipocresía y la crueldad del mundo que les rodea.


Su rechazo a los matrimonios convenientes, a las promesas de riqueza y estatus, resuena en aquellos que nada tienen, en los oprimidos que sueñan con una justicia divina.


Pero Roma no tolera desafíos, especialmente aquellos que socavan sus cimientos morales, o mejor dicho, la ausencia de moral que sustenta su dominio. Las autoridades, primero con condescendencia, luego con creciente irritación, intentan persuadir a Inés.


Le ofrecen regalos, le prometen aún mayores honores, intentan confundirla con argumentos sofisticados sobre la razón y la tradición romana. Pero Inés permanece inamovible, su fe es un muro de acero contra el que chocan todas las artimañas del poder.


Entonces, la persuasión se convierte en amenaza."""

# 3. Nombre del directorio donde se guardarán los archivos MP3 de prueba
#    Cambié ligeramente el nombre para no sobrescribir las pruebas anteriores (si las hiciste)
OUTPUT_DIR_NAME = "pruebas_de_voz_es"

# 4. Formato de salida
OUTPUT_FORMAT = "mp3"

# --- Funciones ---

async def generate_voice_sample(voice: str, text: str, output_dir: Path):
    """
    Genera un archivo de audio para una voz específica.
    El nombre del archivo será el nombre de la voz.
    """
    output_filename = output_dir / f"{voice}.{OUTPUT_FORMAT}"
    print(f"  Intentando generar: {output_filename.name}...")
    try:
        # Crea el objeto de comunicación con el texto y la voz
        communicate = edge_tts.Communicate(text, voice)
        # Guarda el audio en el archivo especificado
        await communicate.save(str(output_filename))
        print(f"   -> [ÉXITO] Archivo guardado: {output_filename.name}")
    except Exception as e:
        # Imprime un error si algo falla para esa voz específica
        print(f"   -> [ERROR] No se pudo generar para {voice}: {e}")
        # Nota: Textos muy largos pueden ocasionalmente dar problemas de timeout o límites.
        if "Timeout" in str(e) or "limit" in str(e).lower():
            print("      (Posible problema de timeout o límite con texto largo)")


async def run_voice_tests():
    """
    Orquesta la generación de muestras para todas las voces en la lista.
    """
    # Crea el objeto Path para el directorio de salida
    output_path = Path(OUTPUT_DIR_NAME)
    # Crea el directorio si no existe (y los directorios padre si son necesarios)
    output_path.mkdir(parents=True, exist_ok=True)

    print("-" * 50)
    print(f"Iniciando generación de pruebas de voz en español (Texto Largo).")
    print(f"Se guardarán en la carpeta: '{OUTPUT_DIR_NAME}'")
    # No imprimimos el texto completo por ser muy largo
    print(f"Texto de prueba a usar: (Párrafo largo sobre Inés)")
    print("-" * 50)

    # Crea una lista para almacenar todas las tareas asíncronas
    tasks = []
    for voice in VOICES_TO_TEST:
        # Añade la tarea de generar la muestra para cada voz a la lista
        tasks.append(generate_voice_sample(voice, SAMPLE_TEXT, output_path))

    # Ejecuta todas las tareas concurrentemente y espera a que terminen
    await asyncio.gather(*tasks)

    print("-" * 50)
    print("¡Proceso de generación de pruebas finalizado!")
    print(f"Revisa los archivos .{OUTPUT_FORMAT} en la carpeta '{OUTPUT_DIR_NAME}'.")
    print("-" * 50)

# --- Punto de Entrada Principal ---
if __name__ == "__main__":
    # Verifica si la librería edge-tts está instalada antes de empezar
    try:
        import edge_tts
    except ImportError:
        print("Error Fatal: La librería 'edge-tts' no parece estar instalada.")
        print("Por favor, instálala ejecutando el comando:")
        print("pip install edge-tts")
        exit(1) # Termina el script si no está la librería

    print("Ejecutando script para generar muestras de voz (Texto Largo)...")
    # Ejecuta la función principal asíncrona usando asyncio.run()
    asyncio.run(run_voice_tests())
    print("Script finalizado.")