"""
Genera un archivo HTML autocontenido (con su propio CSS y JavaScript)
que muestra un mini-quiz interactivo: el estudiante hace clic en una
opción y recibe retroalimentación inmediata (correcto/incorrecto).

Se sube a Moodle como archivo, igual que el PDF y el audio, para que
el estudiante lo abra en una pestaña nueva desde el curso.
"""
import os
import json

CARPETA_TEMPORAL = "archivos_generados"


def _asegurar_carpeta():
    if not os.path.exists(CARPETA_TEMPORAL):
        os.makedirs(CARPETA_TEMPORAL)


def generar_html_quiz(titulo_modulo: str, quiz: dict, nombre_archivo: str) -> str:
    """
    Genera un archivo HTML con el quiz interactivo.
    Devuelve la ruta del archivo generado.
    """
    _asegurar_carpeta()
    ruta_html = os.path.join(CARPETA_TEMPORAL, nombre_archivo)

    preguntas_json = json.dumps(quiz["preguntas"], ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Quiz - {titulo_modulo}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 0 20px; background: #f7f7f9; }}
  h1 {{ color: #2b2b6b; font-size: 22px; }}
  .pregunta {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
  .opcion {{ display: block; width: 100%; text-align: left; padding: 10px; margin: 6px 0; border: 1px solid #ccc; border-radius: 6px; background: white; cursor: pointer; font-size: 15px; }}
  .opcion:hover {{ background: #f0f0ff; }}
  .correcta {{ background: #d4f8d4 !important; border-color: #2ecc71 !important; }}
  .incorrecta {{ background: #f8d4d4 !important; border-color: #e74c3c !important; }}
  #resultado {{ text-align: center; font-size: 18px; margin-top: 20px; font-weight: bold; }}
</style>
</head>
<body>
<h1>🎮 Quiz interactivo: {titulo_modulo}</h1>
<div id="contenedor"></div>
<div id="resultado"></div>

<script>
const preguntas = {preguntas_json};
let respuestasElegidas = new Array(preguntas.length).fill(null);

function render() {{
  const contenedor = document.getElementById('contenedor');
  contenedor.innerHTML = '';
  preguntas.forEach((p, i) => {{
    const div = document.createElement('div');
    div.className = 'pregunta';
    div.innerHTML = '<strong>' + (i + 1) + '. ' + p.pregunta + '</strong>';
    p.opciones.forEach((op, j) => {{
      const btn = document.createElement('button');
      btn.className = 'opcion';
      btn.innerText = op;
      btn.onclick = () => elegir(i, j);
      if (respuestasElegidas[i] !== null) {{
        if (j === p.respuesta_correcta) btn.classList.add('correcta');
        else if (j === respuestasElegidas[i]) btn.classList.add('incorrecta');
        btn.disabled = true;
      }}
      div.appendChild(btn);
    }});
    contenedor.appendChild(div);
  }});
  mostrarResultado();
}}

function elegir(i, j) {{
  respuestasElegidas[i] = j;
  render();
}}

function mostrarResultado() {{
  const respondidas = respuestasElegidas.filter(r => r !== null).length;
  const resultado = document.getElementById('resultado');
  if (respondidas === preguntas.length) {{
    const correctas = preguntas.filter((p, i) => respuestasElegidas[i] === p.respuesta_correcta).length;
    resultado.innerText = `Resultado: ${{correctas}} de ${{preguntas.length}} correctas`;
  }} else {{
    resultado.innerText = '';
  }}
}}

render();
</script>
</body>
</html>
"""

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)

    return ruta_html