"""
Almacenamiento simple en memoria para guardar el curso generado
mientras el usuario revisa el preview y decide si confirma o no.

No usamos base de datos porque la prueba no requiere manejar
múltiples cursos en paralelo ni persistencia entre reinicios.
"""
import uuid

# Diccionario en memoria: { "id-generado": {datos del curso} }
cursos_pendientes = {}


def guardar_curso_pendiente(estructura: dict) -> str:
    """Guarda un curso generado y devuelve un ID único para recuperarlo después."""
    curso_id = str(uuid.uuid4())
    cursos_pendientes[curso_id] = estructura
    return curso_id


def obtener_curso_pendiente(curso_id: str) -> dict:
    """Recupera un curso guardado por su ID. Devuelve None si no existe."""
    return cursos_pendientes.get(curso_id)


def actualizar_curso_pendiente(curso_id: str, estructura: dict):
    """Actualiza los datos de un curso ya guardado (ej. tras publicarlo)."""
    cursos_pendientes[curso_id] = estructura