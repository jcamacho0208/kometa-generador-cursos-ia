"""
Convierte texto (el guion del podcast) a audio, usando gTTS
(Google Text-to-Speech) - gratis, sin necesidad de API key.
"""
import os
from gtts import gTTS

CARPETA_TEMPORAL = "archivos_generados"


def _asegurar_carpeta():
    if not os.path.exists(CARPETA_TEMPORAL):
        os.makedirs(CARPETA_TEMPORAL)


def generar_audio_podcast(guion: str, nombre_archivo: str) -> str:
    """
    Convierte el texto del guion a un archivo de audio MP3.
    Devuelve la ruta del archivo generado.
    """
    _asegurar_carpeta()
    ruta_audio = os.path.join(CARPETA_TEMPORAL, nombre_archivo)

    tts = gTTS(text=guion, lang="es")
    tts.save(ruta_audio)

    return ruta_audio