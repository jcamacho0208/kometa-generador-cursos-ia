"""
Este archivo contiene todas las funciones que hablan directamente
con la API REST de Moodle. Es la única parte del código que sabe
cómo comunicarse con Moodle - el resto de la app no necesita saberlo.
"""
import os
import httpx
from dotenv import load_dotenv
from app.retry_utils import con_reintentos

load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
ENDPOINT = f"{MOODLE_URL}/webservice/rest/server.php"


async def llamar_moodle(wsfunction: str, params: dict = None):
    """
    Función genérica que llama a cualquier función de la API de Moodle.
    Todas las demás funciones de este archivo usan esta por debajo.
    Incluye reintentos automáticos ante fallos temporales de red.
    """
    if params is None:
        params = {}

    query = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
        **params,
    }

    async def _hacer_peticion():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ENDPOINT, data=query)
            response.raise_for_status()
            return response.json()

    data = await con_reintentos(_hacer_peticion, intentos=3, espera_segundos=2)

    # Moodle devuelve errores como un diccionario con "exception",
    # incluso con status HTTP 200, así que hay que revisarlo a mano.
    if isinstance(data, dict) and "exception" in data:
        raise Exception(f"Error de Moodle: {data.get('message')}")

    return data


async def probar_conexion():
    """Prueba simple: trae la lista de cursos existentes."""
    return await llamar_moodle("core_course_get_courses")


async def crear_curso(nombre_completo: str, nombre_corto: str, resumen: str = ""):
    """
    Crea un curso nuevo en Moodle.
    Devuelve el curso creado, incluyendo su 'id' (lo vas a necesitar
    para crear secciones y subir archivos después).
    """
    params = {
        "courses[0][fullname]": nombre_completo,
        "courses[0][shortname]": nombre_corto,
        "courses[0][categoryid]": 1,  # categoría por defecto "Miscelánea"
        "courses[0][summary]": resumen,
    }
    resultado = await llamar_moodle("core_course_create_courses", params)
    return resultado[0]  # Moodle devuelve una lista, tomamos el primer curso


async def obtener_contenido_curso(course_id: int):
    """Trae las secciones y actividades de un curso (para el chat de dudas)."""
    params = {"courseid": course_id}
    return await llamar_moodle("core_course_get_contents", params)


async def crear_secciones(course_id: int, cantidad: int):
    """
    Crea 'cantidad' secciones nuevas en un curso (usando el plugin
    local_wsmanagesections). Devuelve la lista de secciones creadas,
    cada una con su 'id' y 'sectionnum'.
    """
    params = {"courseid": course_id, "position": 0, "number": cantidad}
    return await llamar_moodle("local_wsmanagesections_create_sections", params)


async def actualizar_seccion(course_id: int, sectionnum: int, nombre: str, resumen_html: str):
    """
    Actualiza el nombre y el contenido (resumen) de una sección específica.
    'resumen_html' puede incluir HTML, por ejemplo enlaces a archivos subidos.
    """
    params = {
        "courseid": course_id,
        "sections[0][type]": "num",
        "sections[0][section]": sectionnum,
        "sections[0][name]": nombre,
        "sections[0][summary]": resumen_html,
        "sections[0][summaryformat]": 1,  # 1 = formato HTML
    }
    return await llamar_moodle("local_wsmanagesections_update_sections", params)


async def subir_archivo(ruta_archivo: str, nombre_archivo: str) -> dict:
    """
    Sube un archivo (PDF, imagen, audio) al área de "archivos en borrador"
    de Moodle. Devuelve un diccionario con 'itemid' y 'url' del archivo,
    construyendo la URL manualmente a partir de los datos que Moodle
    devuelve (contextid, itemid, filepath, filename) ya que no siempre
    viene una clave 'url' directa en la respuesta.

    Usamos draftfile.php (no pluginfile.php) porque el archivo vive
    en el área de borrador del usuario, no en el área final del curso.

    Incluye reintentos automáticos ante fallos temporales de red.
    """
    url_upload = f"{MOODLE_URL}/webservice/upload.php"

    with open(ruta_archivo, "rb") as f:
        contenido = f.read()

    async def _hacer_subida():
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url_upload,
                params={"token": MOODLE_TOKEN},
                files={"file_1": (nombre_archivo, contenido)},
            )
            response.raise_for_status()
            return response.json()

    resultado = await con_reintentos(_hacer_subida, intentos=3, espera_segundos=2)

    if isinstance(resultado, dict) and "error" in resultado:
        raise Exception(f"Error al subir archivo: {resultado.get('error')}")

    archivo_info = resultado[0]

    contextid = archivo_info["contextid"]
    itemid = archivo_info["itemid"]
    filepath = archivo_info.get("filepath", "/")
    filename = archivo_info["filename"]

    url_archivo = (
        f"{MOODLE_URL}/webservice/draftfile.php/{contextid}/user/draft/"
        f"{itemid}{filepath}{filename}?token={MOODLE_TOKEN}"
    )

    return {"itemid": itemid, "url": url_archivo}