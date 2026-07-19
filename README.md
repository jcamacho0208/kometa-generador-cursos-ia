# Kometa - Generador de cursos con IA para Moodle

Aplicación fullstack que, a partir de una instrucción en lenguaje natural (ej. *"crea un curso de Excel intermedio con 4 módulos"*), genera la estructura de un curso usando IA, muestra una vista previa, y al confirmar publica el curso real en una instancia de Moodle — incluyendo texto, PDF, imagen, podcast (audio) y un quiz interactivo para cada módulo. Incluye además un chat de dudas que responde preguntas sobre el contenido real del curso ya publicado.

## Stack usado

- **Backend:** Python + FastAPI
- **Frontend:** HTML + JavaScript simple (servido por el propio backend, sin build step)
- **IA de texto (estructura, contenido, guion, quiz, chat):** [Groq](https://console.groq.com) (modelo `llama-3.3-70b-versatile`)
- **Generación de imágenes:** [Pollinations.ai](https://pollinations.ai) (sin API key)
- **Texto a voz (podcast):** gTTS (Google Text-to-Speech, sin API key)
- **PDF:** reportlab
- **Moodle:** API REST + plugin [local_wsmanagesections](https://moodle.org/plugins/local_wsmanagesections) (ver sección de decisiones técnicas)

## 1. Cómo levantar Moodle local

1. Descarga el **Moodle Windows Installer** (incluye Apache + MariaDB + PHP + Moodle) desde [download.moodle.org](https://download.moodle.org/windows/), versión **4.4.x**.
2. Instálalo en una carpeta de tu elección (ej. `C:\xampp\htdocs\moodle\`).
3. Corre el instalador gráfico (`Start Moodle.exe`) y sigue el asistente: elige idioma, deja la configuración de base de datos por defecto, y crea tu cuenta de administrador.
4. Para volver a prender Moodle en el futuro, simplemente ejecuta `Start Moodle.exe` de nuevo.

### Habilitar Web Services / API REST

1. **Administración del sitio → Avanzado (Advanced features)** → activa **"Habilitar servicios web"**.
2. **Administración del sitio → Servidor → Servicios web → Administrar protocolos** → habilita **"Protocolo REST"**.
3. **Administración del sitio → Servidor → Servicios web → Servicios externos** → crea un servicio nuevo (ej. `KometaAPI`), márcalo como **Habilitado**, y agrégale estas funciones:
   - `core_course_create_courses`
   - `core_course_get_courses`
   - `core_course_get_contents`
   - `core_course_edit_section`
   - `core_files_upload`
   - `core_course_create_categories`
   - `local_wsmanagesections_create_sections`
   - `local_wsmanagesections_update_sections`
   - `local_wsmanagesections_get_sections`
4. En ese mismo servicio, en **"Editar"**, marca las casillas **"Puede descargar archivos"** y **"Puede subir ficheros"**.
5. **Administración del sitio → Servidor → Servicios web → Administrar fichas (tokens)** → crea un token para tu usuario administrador y el servicio `KometaAPI`.
6. Crea también un rol personalizado (ej. "servicio web") con los permisos `webservice/rest:use` y `moodle/webservice:createtoken` en "Permitir", y asígnalo a tu usuario admin como **rol de sistema** (Administración del sitio → Usuarios → Permisos → Asignar roles del sistema).

### Instalar el plugin local_wsmanagesections

La API REST estándar de Moodle no permite crear ni editar secciones de curso con contenido (solo funciones limitadas de visibilidad). Para poder crear secciones reales con nombre y contenido vía API, se instaló el plugin de terceros **local_wsmanagesections**:

1. Descarga el plugin desde [moodle.org/plugins/local_wsmanagesections](https://moodle.org/plugins/local_wsmanagesections).
2. **Administración del sitio → Plugins → Instalar plugins** → sube el `.zip` descargado.
3. Sigue el asistente (acepta la advertencia de compatibilidad de versión si aparece; funciona correctamente en Moodle 4.4 aunque el plugin declara soporte oficial hasta 4.2).
4. Agrega sus 3 funciones al servicio `KometaAPI` (ver paso 3 arriba).

## 2. Configurar el token / variables de entorno

1. Copia el archivo `.env.example` y renómbralo a `.env`.
2. Complétalo con tus datos reales:
```
- `MOODLE_TOKEN`: el token generado en el paso anterior.
- `GROQ_API_KEY`: consíguela gratis en [console.groq.com/keys](https://console.groq.com/keys) (no pide tarjeta de crédito).

## 3. Cómo correr la aplicación

```bash
# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# Correr el servidor
uvicorn app.main:app --reload
```

Con el servidor corriendo:

- **Interfaz web:** [http://localhost:8000/app](http://localhost:8000/app)
- **Documentación interactiva de la API:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Flujo de uso

1. Escribe una instrucción en lenguaje natural (ej. *"crea un curso de marketing digital con 3 módulos"*).
2. Clic en **"Generar vista previa"** — la IA genera la estructura y el texto de cada módulo (tarda 30-60 seg).
3. Revisa el preview. Nada se publica todavía.
4. Clic en **"Confirmar y publicar en Moodle"** — se genera PDF, imagen, audio y un quiz interactivo de cada módulo, se sube todo a Moodle, y se crea el curso real con sus secciones (tarda varios minutos, ya que genera 4 archivos por módulo).
5. Al terminar, se muestra un link directo al curso creado en Moodle.
6. Debajo aparece un chat donde puedes preguntar sobre el contenido del curso (ej. *"¿qué se ve en el módulo 2?"*), respondido por la IA basándose en el texto real generado.

## 4. Decisiones técnicas

- **Groq en vez de Claude/Gemini para la IA de texto:** se evaluaron varias opciones para el motor de generación de contenido. Se eligió Groq porque da acceso gratuito real sin fricciones de facturación, responde muy rápido (modelos Llama), y tiene buen desempeño en español para contenido educativo — una decisión pensando también en que quien evalúe el proyecto pueda clonarlo y probarlo sin configurar credenciales de pago en ningún lado.
- **Pollinations.ai para imágenes y gTTS para audio:** ambos sin necesidad de API key, para simplificar el setup de quien clone el repo.
- **Plugin `local_wsmanagesections`:** la API REST estándar de Moodle no expone una forma de crear/editar secciones de curso con nombre y contenido (solo acciones de visibilidad como ocultar/mostrar). Se investigó el ecosistema de plugins de Moodle y se instaló este, que agrega exactamente las funciones necesarias. Esto permitió cumplir con el requisito de "crear el curso, sus secciones y subir el contenido... vía su API" de forma real, en vez de simular todo el contenido dentro del resumen general del curso.
- **Contenido embebido en el resumen de la sección, no como "actividades" (mod_resource) separadas:** crear actividades/módulos de Moodle (como "Recurso" o "Página") vía web service estándar tampoco tiene una función nativa limpia sin plugins adicionales más invasivos. En su lugar, cada sección incluye: el texto explicativo completo, la imagen embebida directamente (`<img>`), y enlaces de descarga al PDF, al audio y al quiz interactivo — todos alojados realmente en Moodle (subidos vía `core_files_upload` / `webservice/upload.php`), cumpliendo con "adjuntado al curso" e "integrada al curso" del enunciado.
- **Almacenamiento en memoria (no base de datos):** dado que el enunciado aclara que no hace falta soportar múltiples cursos en paralelo, el curso generado en `/preview` se guarda en un diccionario en memoria (identificado por un UUID), que luego usan `/confirmar` y `/chat`. Esto se pierde si el servidor se reinicia, lo cual es aceptable para el alcance de la prueba.
- **Generación de PDF/imagen/audio/quiz diferida a `/confirmar`, no en `/preview`:** el preview solo genera estructura + texto (más rápido), para no gastar tiempo/recursos generando contenido de un curso que el usuario podría no llegar a confirmar.

## 5. Qué se implementó como extra

- **Manejo de reintentos automáticos:** tanto las llamadas a la API de Moodle como las llamadas a Groq (generación de estructura, texto, guion, quiz y chat) están envueltas en una función de reintentos (`app/retry_utils.py`) que reintenta automáticamente hasta 3 veces, con espera creciente entre intentos, ante fallos temporales de red o timeouts. Esto hace la aplicación más resiliente frente a caídas transitorias de la API de Moodle o de la API de IA. Además, cuando el fallo no es transitorio (por ejemplo, al alcanzar el límite diario de tokens de Groq), el sistema falla con un mensaje de error claro en vez de quedarse colgado.
- **Contenido interactivo:** cada módulo genera, además del texto/PDF/imagen/podcast, un mini-quiz de 3 preguntas de opción múltiple (`app/interactive_generator.py`), generado por IA a partir del contenido real del módulo. Es un archivo HTML autocontenido (con su propio CSS y JavaScript) donde el estudiante hace clic en una opción y recibe retroalimentación inmediata (correcta/incorrecta), más un resultado final. Se sube a Moodle como archivo, igual que el PDF y el audio.

## 6. Qué no se alcanzó a hacer / limitaciones conocidas

- No se implementó edición del contenido generado antes de confirmar la publicación (el preview es de solo lectura).
- El manejo de errores es básico más allá de los reintentos: se capturan y muestran, pero no hay una estrategia de recuperación parcial si el curso queda a medio publicar en Moodle.
- Con más tiempo, se implementaría: edición de texto/imagen antes de publicar, y mover el almacenamiento de "cursos pendientes" a una base de datos ligera (SQLite) para que sobreviva a reinicios del servidor.