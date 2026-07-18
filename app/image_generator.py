"""
Genera imágenes usando Pollinations.ai - un servicio gratuito
que no requiere API key. Solo se le manda una descripción (prompt)
en la URL y devuelve la imagen generada.
"""
import os
import httpx
from urllib.parse import quote

CARPETA_TEMPORAL = "archivos_generados"


def _asegurar_carpeta():
    if not os.path.exists(CARPETA_TEMPORAL):
        os.makedirs(CARPETA_TEMPORAL)


async def generar_imagen_modulo(descripcion_imagen: str, nombre_archivo: str) -> str:
    """
    Genera una imagen a partir de una descripción en texto (prompt).
    Devuelve la ruta del archivo de imagen guardado en disco.
    """
    _asegurar_carpeta()
    ruta_imagen = os.path.join(CARPETA_TEMPORAL, nombre_archivo)

    prompt_codificado = quote(descripcion_imagen)
    url = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=768&height=512&nologo=true"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()

        with open(ruta_imagen, "wb") as archivo:
            archivo.write(response.content)

    return ruta_imagen