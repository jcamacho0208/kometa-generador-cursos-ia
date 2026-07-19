"""
Este archivo contiene toda la lógica de IA: generar la estructura del
curso, generar el texto explicativo de cada módulo, generar el guion
del podcast, y responder preguntas en el chat de dudas.

Usamos Groq (modelos Llama) porque da acceso gratuito sin pedir tarjeta.
"""
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from app.retry_utils import con_reintentos

load_dotenv()

cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODELO = "llama-3.3-70b-versatile"


PROMPT_ESTRUCTURA = """Eres un diseñador instruccional experto. A partir de la instrucción
del usuario, genera la estructura de un curso online.

Instrucción del usuario: "{instruccion}"

Reglas:
- Si el usuario especifica un número de módulos, respeta ese número exactamente.
- Si el usuario NO especifica cuántos módulos quiere, decide tú un número
  razonable (normalmente entre 3 y 5) según la complejidad del tema.
- Cada módulo debe tener un título claro y una descripción breve (2-3 frases)
  de lo que se va a enseñar en ese módulo.
- Responde en español.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin explicaciones,
sin marcadores de código (nada de ```), con exactamente esta forma:

{{
  "nombre_curso": "string",
  "resumen_curso": "string (1-2 frases sobre de qué trata el curso)",
  "modulos": [
    {{
      "titulo": "string",
      "descripcion": "string"
    }}
  ]
}}
"""


PROMPT_TEXTO_MODULO = """Eres un experto creando contenido educativo. Vas a escribir el
contenido explicativo completo de un módulo de curso.

Curso: "{nombre_curso}"
Módulo: "{titulo_modulo}"
Resumen de lo que cubre este módulo: "{descripcion_modulo}"

Escribe el contenido explicativo de este módulo, como si fuera el material
de lectura que un estudiante va a estudiar. Debe:
- Tener entre 4 y 6 párrafos
- Explicar los conceptos de forma clara, con ejemplos cuando aplique
- Tener una introducción breve y un cierre que conecte con el siguiente tema
- Estar en español, con un tono profesional pero cercano

Responde ÚNICAMENTE con el texto del contenido, sin título, sin JSON,
sin marcadores de código, sin comentarios adicionales - solo el texto plano
del módulo, en párrafos separados por saltos de línea.
"""


PROMPT_GUION_PODCAST = """Eres un guionista de podcasts educativos. Vas a escribir el guion
de un episodio corto de podcast que resume el contenido de un módulo de curso.

Módulo: "{titulo_modulo}"
Contenido del módulo:
{texto_modulo}

Escribe un guion de podcast de un solo narrador (no diálogo, un locutor hablando
directo a la audiencia), que:
- Dure aproximadamente 1-2 minutos al hablarse en voz alta (150-250 palabras)
- Resuma los puntos clave del módulo de forma amena y conversacional
- Tenga un saludo breve al inicio y un cierre que invite a seguir aprendiendo
- Esté en español, listo para ser leído en voz alta (sin indicaciones de escena,
  sin corchetes, solo el texto que se va a decir)

Responde ÚNICAMENTE con el guion, sin título, sin comentarios adicionales.
"""


PROMPT_CHAT = """Eres un asistente que responde preguntas sobre un curso específico,
basándote ÚNICAMENTE en el contenido real de ese curso que se muestra abajo.

Curso: "{nombre_curso}"
Resumen: {resumen_curso}

Contenido de los módulos:
{contenido_modulos}

Pregunta del estudiante: "{pregunta}"

Instrucciones:
- Responde ÚNICAMENTE basándote en el contenido de los módulos de arriba.
- Si la pregunta no se puede responder con ese contenido, dilo honestamente
  en vez de inventar una respuesta.
- Sé conciso pero completo, en español, con un tono amigable.
"""


PROMPT_QUIZ = """Eres un diseñador instruccional. A partir del contenido de un módulo,
genera un mini-quiz de 3 preguntas de opción múltiple para reforzar el aprendizaje.

Módulo: "{titulo_modulo}"
Contenido del módulo:
{texto_modulo}

Reglas:
- Exactamente 3 preguntas.
- Cada pregunta debe tener exactamente 4 opciones.
- Solo una opción es correcta.
- Las preguntas deben poder responderse con el contenido de arriba.
- Responde en español.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin marcadores de
código, con exactamente esta forma:

{{
  "preguntas": [
    {{
      "pregunta": "string",
      "opciones": ["string", "string", "string", "string"],
      "respuesta_correcta": 0
    }}
  ]
}}

"respuesta_correcta" es el índice (0 a 3) de la opción correcta en la lista "opciones".
"""


def _limpiar_respuesta_json(texto: str) -> str:
    """Limpia posibles marcadores de código que el modelo agregue por error."""
    texto = texto.strip()
    texto = re.sub(r"^```json\s*", "", texto)
    texto = re.sub(r"^```\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


async def generar_estructura_curso(instruccion: str) -> dict:
    """
    Llama a la IA para generar la estructura de un curso.
    Devuelve un diccionario con: nombre_curso, resumen_curso, modulos (lista).
    Incluye reintentos automáticos ante fallos temporales de la API.
    """
    prompt = PROMPT_ESTRUCTURA.format(instruccion=instruccion)

    async def _llamar_groq():
        return cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

    respuesta = await con_reintentos(_llamar_groq, intentos=3, espera_segundos=2)

    texto_limpio = _limpiar_respuesta_json(respuesta.choices[0].message.content)

    try:
        estructura = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise Exception(
            "La IA no devolvió un JSON válido. Respuesta recibida: "
            + texto_limpio[:300]
        )

    return estructura


async def generar_texto_modulo(nombre_curso: str, titulo_modulo: str, descripcion_modulo: str) -> str:
    """
    Genera el contenido explicativo completo (varios párrafos) de un módulo.
    Este es el texto que luego se convierte en PDF y se usa como base
    para el guion del podcast y el chat de dudas.
    Incluye reintentos automáticos ante fallos temporales de la API.
    """
    prompt = PROMPT_TEXTO_MODULO.format(
        nombre_curso=nombre_curso,
        titulo_modulo=titulo_modulo,
        descripcion_modulo=descripcion_modulo,
    )

    async def _llamar_groq():
        return cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

    respuesta = await con_reintentos(_llamar_groq, intentos=3, espera_segundos=2)

    return respuesta.choices[0].message.content.strip()


async def generar_guion_podcast(titulo_modulo: str, texto_modulo: str) -> str:
    """
    Genera el guion de un podcast corto que resume el módulo.
    Incluye reintentos automáticos ante fallos temporales de la API.
    """
    prompt = PROMPT_GUION_PODCAST.format(
        titulo_modulo=titulo_modulo, texto_modulo=texto_modulo
    )

    async def _llamar_groq():
        return cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

    respuesta = await con_reintentos(_llamar_groq, intentos=3, espera_segundos=2)

    return respuesta.choices[0].message.content.strip()


async def responder_pregunta_curso(nombre_curso: str, resumen_curso: str, modulos: list, pregunta: str) -> str:
    """
    Responde una pregunta sobre el curso, usando como contexto el texto
    real de todos los módulos generados (RAG simple: todo el contenido
    cabe en el contexto, no hace falta un vector store).
    Incluye reintentos automáticos ante fallos temporales de la API.
    """
    contenido_modulos = "\n\n".join(
        f"--- {m['titulo']} ---\n{m['texto']}" for m in modulos
    )

    prompt = PROMPT_CHAT.format(
        nombre_curso=nombre_curso,
        resumen_curso=resumen_curso,
        contenido_modulos=contenido_modulos,
        pregunta=pregunta,
    )

    async def _llamar_groq():
        return cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

    respuesta = await con_reintentos(_llamar_groq, intentos=3, espera_segundos=2)

    return respuesta.choices[0].message.content.strip()


async def generar_quiz_interactivo(titulo_modulo: str, texto_modulo: str) -> dict:
    """
    Genera un mini-quiz de 3 preguntas de opción múltiple sobre un módulo,
    usado para el contenido interactivo (extra opcional del enunciado).
    Incluye reintentos automáticos ante fallos temporales de la API.
    """
    prompt = PROMPT_QUIZ.format(titulo_modulo=titulo_modulo, texto_modulo=texto_modulo)

    async def _llamar_groq():
        return cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )

    respuesta = await con_reintentos(_llamar_groq, intentos=3, espera_segundos=2)

    texto_limpio = _limpiar_respuesta_json(respuesta.choices[0].message.content)

    try:
        quiz = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise Exception(
            "La IA no devolvió un JSON válido para el quiz. Respuesta: "
            + texto_limpio[:300]
        )

    return quiz