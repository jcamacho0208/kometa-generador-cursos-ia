"""
Punto de entrada de la aplicación FastAPI.
"""
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app import moodle_client, ia_client, pdf_generator, image_generator, audio_generator, estado

app = FastAPI(title="Kometa - Generador de cursos con IA")


class InstruccionRequest(BaseModel):
    instruccion: str


class TextoModuloRequest(BaseModel):
    nombre_curso: str
    titulo_modulo: str
    descripcion_modulo: str


class ImagenRequest(BaseModel):
    descripcion_imagen: str


class SeccionesRequest(BaseModel):
    course_id: int
    cantidad: int


class ActualizarSeccionRequest(BaseModel):
    course_id: int
    sectionnum: int
    nombre: str
    resumen_html: str


class ConfirmarRequest(BaseModel):
    curso_id: str


class ChatRequest(BaseModel):
    curso_id: str
    pregunta: str


@app.get("/")
def home():
    return {"mensaje": "Backend de Kometa corriendo correctamente"}


@app.get("/test/moodle")
async def test_moodle():
    try:
        cursos = await moodle_client.probar_conexion()
        return {"conectado": True, "cursos_existentes": cursos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/crear-curso-prueba")
async def test_crear_curso():
    try:
        curso = await moodle_client.crear_curso(
            nombre_completo="Curso de prueba desde FastAPI",
            nombre_corto="prueba-fastapi-1",
            resumen="Este curso fue creado automáticamente para probar la conexión.",
        )
        return {"creado": True, "curso": curso}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generar-estructura")
async def generar_estructura(body: InstruccionRequest):
    try:
        estructura = await ia_client.generar_estructura_curso(body.instruccion)
        return estructura
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generar-texto-modulo")
async def generar_texto_modulo_endpoint(body: TextoModuloRequest):
    try:
        texto = await ia_client.generar_texto_modulo(
            body.nombre_curso, body.titulo_modulo, body.descripcion_modulo
        )
        return {"texto": texto}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/generar-pdf")
async def test_generar_pdf(body: TextoModuloRequest):
    try:
        texto = await ia_client.generar_texto_modulo(
            body.nombre_curso, body.titulo_modulo, body.descripcion_modulo
        )
        ruta_pdf = pdf_generator.generar_pdf_modulo(
            body.titulo_modulo, texto, "modulo_prueba.pdf"
        )
        return FileResponse(ruta_pdf, media_type="application/pdf", filename="modulo_prueba.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/generar-imagen")
async def test_generar_imagen(body: ImagenRequest):
    try:
        ruta_imagen = await image_generator.generar_imagen_modulo(
            body.descripcion_imagen, "imagen_prueba.png"
        )
        return FileResponse(ruta_imagen, media_type="image/png", filename="imagen_prueba.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/generar-audio")
async def test_generar_audio(body: TextoModuloRequest):
    try:
        texto = await ia_client.generar_texto_modulo(
            body.nombre_curso, body.titulo_modulo, body.descripcion_modulo
        )
        guion = await ia_client.generar_guion_podcast(body.titulo_modulo, texto)
        ruta_audio = audio_generator.generar_audio_podcast(guion, "audio_prueba.mp3")
        return FileResponse(ruta_audio, media_type="audio/mpeg", filename="audio_prueba.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preview")
async def preview_curso(body: InstruccionRequest):
    try:
        estructura = await ia_client.generar_estructura_curso(body.instruccion)

        for modulo in estructura["modulos"]:
            texto = await ia_client.generar_texto_modulo(
                estructura["nombre_curso"], modulo["titulo"], modulo["descripcion"]
            )
            modulo["texto"] = texto

        curso_id = estado.guardar_curso_pendiente(estructura)

        return {"curso_id": curso_id, **estructura}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/crear-secciones")
async def test_crear_secciones(body: SeccionesRequest):
    try:
        secciones = await moodle_client.crear_secciones(body.course_id, body.cantidad)
        return {"secciones_creadas": secciones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/actualizar-seccion")
async def test_actualizar_seccion(body: ActualizarSeccionRequest):
    """
    Endpoint de prueba: actualiza el nombre y contenido de una sección.
    """
    try:
        resultado = await moodle_client.actualizar_seccion(
            body.course_id, body.sectionnum, body.nombre, body.resumen_html
        )
        return {"actualizado": True, "resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/confirmar")
async def confirmar_curso(body: ConfirmarRequest):
    """
    Publica en Moodle el curso que fue generado y guardado en /preview.

    Pasos:
    1. Recupera el curso guardado en memoria por su curso_id.
    2. Crea el curso real en Moodle.
    3. Crea una sección por cada módulo.
    4. Para cada módulo: genera PDF, imagen y audio (guion), los sube
       a Moodle, y actualiza la sección con el texto + enlaces/imagen.
    """
    estructura = estado.obtener_curso_pendiente(body.curso_id)
    if estructura is None:
        raise HTTPException(status_code=404, detail="curso_id no encontrado. Genera un /preview primero.")

    try:
        # 1. Crear el curso real en Moodle
        nombre_corto = f"kometa-{uuid.uuid4().hex[:8]}"
        curso_moodle = await moodle_client.crear_curso(
            nombre_completo=estructura["nombre_curso"],
            nombre_corto=nombre_corto,
            resumen=estructura["resumen_curso"],
        )
        course_id = curso_moodle["id"]

        # 2. Crear una sección por cada módulo
        modulos = estructura["modulos"]
        await moodle_client.crear_secciones(course_id, len(modulos))

        # 3. Para cada módulo: generar contenido, subir archivos, actualizar sección
        for i, modulo in enumerate(modulos):
            sectionnum = i + 1  # la sección 0 es "General", los módulos empiezan en 1

            texto = modulo["texto"]  # ya generado en /preview

            # PDF
            nombre_pdf = f"modulo_{sectionnum}.pdf"
            ruta_pdf = pdf_generator.generar_pdf_modulo(modulo["titulo"], texto, nombre_pdf)
            info_pdf = await moodle_client.subir_archivo(ruta_pdf, nombre_pdf)

            # Imagen
            nombre_imagen = f"modulo_{sectionnum}.png"
            descripcion_imagen = f"Ilustración educativa sobre: {modulo['titulo']}"
            ruta_imagen = await image_generator.generar_imagen_modulo(descripcion_imagen, nombre_imagen)
            info_imagen = await moodle_client.subir_archivo(ruta_imagen, nombre_imagen)

            # Audio (guion + conversión a voz)
            guion = await ia_client.generar_guion_podcast(modulo["titulo"], texto)
            nombre_audio = f"modulo_{sectionnum}.mp3"
            ruta_audio = audio_generator.generar_audio_podcast(guion, nombre_audio)
            info_audio = await moodle_client.subir_archivo(ruta_audio, nombre_audio)

            # Armar el HTML de la sección con todo el contenido
            texto_html = texto.replace("\n\n", "</p><p>")
            resumen_html = f"""
            <p>{texto_html}</p>
            <p><img src="{info_imagen['url']}" alt="Ilustración del módulo" style="max-width:100%;"></p>
            <p><a href="{info_pdf['url']}" target="_blank">📄 Descargar PDF del módulo</a></p>
            <p><a href="{info_audio['url']}" target="_blank">🎧 Escuchar podcast del módulo</a></p>
            """

            await moodle_client.actualizar_seccion(course_id, sectionnum, modulo["titulo"], resumen_html)

        return {
            "publicado": True,
            "course_id": course_id,
            "url_curso": f"{moodle_client.MOODLE_URL}/course/view.php?id={course_id}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_curso(body: ChatRequest):
    """
    Responde una pregunta sobre un curso ya generado, basándose en el
    contenido real de sus módulos (guardado en memoria desde /preview).
    """
    estructura = estado.obtener_curso_pendiente(body.curso_id)
    if estructura is None:
        raise HTTPException(status_code=404, detail="curso_id no encontrado.")

    try:
        respuesta = await ia_client.responder_pregunta_curso(
            estructura["nombre_curso"],
            estructura["resumen_curso"],
            estructura["modulos"],
            body.pregunta,
        )
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import os

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_FRONTEND = os.path.join(RUTA_BASE, "static", "index.html")


@app.get("/app")
def frontend():
    """
    Sirve la interfaz web simple (HTML+JS) para usar la app sin
    depender de la documentación interactiva de /docs.
    """
    if not os.path.exists(RUTA_FRONTEND):
        raise HTTPException(status_code=404, detail=f"No se encontró el archivo en: {RUTA_FRONTEND}")
    return FileResponse(RUTA_FRONTEND)