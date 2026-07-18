"""
Este archivo genera archivos PDF a partir del texto de un módulo,
usando la librería reportlab. El PDF resultante se guarda en disco
temporalmente, para después subirlo a Moodle.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY

CARPETA_TEMPORAL = "archivos_generados"


def _asegurar_carpeta():
    if not os.path.exists(CARPETA_TEMPORAL):
        os.makedirs(CARPETA_TEMPORAL)


def generar_pdf_modulo(titulo_modulo: str, texto: str, nombre_archivo: str) -> str:
    """
    Genera un PDF con el título y el texto del módulo.
    Devuelve la ruta del archivo PDF generado en disco.
    """
    _asegurar_carpeta()
    ruta_pdf = os.path.join(CARPETA_TEMPORAL, nombre_archivo)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=letter,
                             topMargin=1 * inch, bottomMargin=1 * inch,
                             leftMargin=1 * inch, rightMargin=1 * inch)

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloModulo", parent=estilos["Heading1"], spaceAfter=20
    )
    estilo_parrafo = ParagraphStyle(
        "ParrafoModulo", parent=estilos["Normal"],
        fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12,
    )

    elementos = [Paragraph(titulo_modulo, estilo_titulo), Spacer(1, 12)]

    for parrafo in texto.split("\n\n"):
        parrafo_limpio = parrafo.strip().replace("\n", " ")
        if parrafo_limpio:
            elementos.append(Paragraph(parrafo_limpio, estilo_parrafo))

    doc.build(elementos)
    return ruta_pdf