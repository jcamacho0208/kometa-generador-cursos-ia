# Kometa - Generador de cursos con IA para Moodle

Aplicación fullstack que, a partir de una instrucción en lenguaje natural (ej. *"crea un curso de Excel intermedio con 4 módulos"*), genera la estructura de un curso usando IA, muestra una vista previa, y al confirmar publica el curso real en una instancia de Moodle — incluyendo texto, PDF, imagen y podcast (audio) para cada módulo. Incluye además un chat de dudas que responde preguntas sobre el contenido real del curso ya publicado.

## Stack usado

- **Backend:** Python + FastAPI
- **Frontend:** HTML + JavaScript simple (servido por el propio backend, sin build step)
- **IA de texto (estructura, contenido, chat):** [Groq](https://console.groq.com) (modelo `llama-3.3-70b-versatile`)
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
MOODLE_URL=http://localhost
MOODLE_TOKEN=tu_token_de_moodle
GROQ_API_KEY=tu_api_key_de_groq
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
4. Clic en **"Confirmar y publicar en Moodle"** — se genera PDF, imagen y audio de cada módulo, se sube todo a Moodle, y se crea el curso real con sus secciones (tarda 2-5 min, ya que genera 3 archivos por módulo).
5. Al terminar, se muestra un link directo al curso creado en Moodle.
6. Debajo aparece un chat donde puedes preguntar sobre el contenido del curso (ej. *"¿qué se ve en el módulo 2?"*), respondido por la IA basándose en el texto real generado.

## 4. Decisiones técnicas

- **Groq en vez de Claude/Gemini para la IA de texto:** se intentó primero con Gemini, pero la cuenta de Google AI Studio usada tenía el límite de la capa gratuita en 0 (requiere facturación habilitada incluso para uso gratuito, según la región). Se optó por Groq, que da acceso gratuito real sin pedir tarjeta y con tiempos de respuesta muy rápidos (modelos Llama). El enunciado permite usar cualquier herramienta de IA, así que se priorizó una opción sin fricción de costos para el desarrollo y para quien evalúe el proyecto.
- **Pollinations.ai para imágenes y gTTS para audio:** ambos sin necesidad de API key, para simplificar el setup de quien clone el repo (no hay que configurar credenciales adicionales de terceros).
- **Plugin `local_wsmanagesections`:** la API REST estándar de Moodle no expone una forma de crear/editar secciones de curso con nombre y contenido (solo acciones de visibilidad como ocultar/mostrar). Instalar este plugin fue la forma de cumplir con el requisito de "crear el curso, sus secciones y subir el contenido... vía su API" de forma real, en vez de simular todo el contenido dentro del resumen general del curso.
- **Contenido embebido en el resumen de la sección, no como "actividades" (mod_resource) separadas:** crear actividades/módulos de Moodle (como "Recurso" o "Página") vía web service estándar tampoco tiene una función nativa limpia sin plugins adicionales más invasivos. En su lugar, cada sección incluye: el texto explicativo completo, la imagen embebida directamente (`<img>`), y enlaces de descarga al PDF y al audio — todos alojados realmente en Moodle (subidos vía `core_files_upload` / `webservice/upload.php`), cumpliendo con "adjuntado al curso" e "integrada al curso" del enunciado, dentro del tiempo disponible.
- **Almacenamiento en memoria (no base de datos):** dado que el enunciado aclara que no hace falta soportar múltiples cursos en paralelo, el curso generado en `/preview` se guarda en un diccionario en memoria (identificado por un UUID), que luego usan `/confirmar` y `/chat`. Esto se pierde si el servidor se reinicia, lo cual es aceptable para el alcance de la prueba.
- **Generación de PDF/imagen/audio diferida a `/confirmar`, no en `/preview`:** el preview solo genera estructura + texto (más rápido), para no gastar tiempo/recursos generando PDF, imagen y audio de un curso que el usuario podría no llegar a confirmar.

## 5. Qué se implementó como extra

- Ninguno de los 3 extras opcionales (video interactivo, reintentos robustos, edición pre-publicación) se alcanzó a implementar dentro del tiempo disponible — se priorizó que el flujo obligatorio funcionara de punta a punta de forma confiable.

## 6. Qué no se alcanzó a hacer / limitaciones conocidas

- No hay manejo de reintentos automáticos si falla una llamada a Moodle o a la IA a mitad del proceso de `/confirmar` — si falla, el curso puede quedar creado en Moodle pero incompleto, y habría que revisar manualmente o volver a intentar.
- No se implementó edición del contenido generado antes de confirmar la publicación (el preview es de solo lectura).
- No hay contenido interactivo (video interactivo) en ningún módulo.
- El manejo de errores es básico: se capturan y muestran, pero no hay lógica de reintento ni backoff.
- Con más tiempo, se implementaría: edición de texto/imagen antes de publicar, reintentos automáticos ante fallos transitorios de la API de Moodle o de Groq, y posiblemente mover el almacenamiento de "cursos pendientes" a una base de datos ligera (SQLite) para que sobreviva a reinicios del servidor.