"""
Utilidad de reintentos automáticos para llamadas externas (Moodle, IA).
Si una llamada falla por un problema temporal (timeout, error de red),
se reintenta automáticamente antes de darla por fallida.
"""
import asyncio


async def con_reintentos(funcion_async, *args, intentos=3, espera_segundos=2, **kwargs):
    """
    Ejecuta una función async, reintentando hasta 'intentos' veces si falla.
    Espera 'espera_segundos' entre cada intento (aumentando un poco cada vez).

    Uso:
        resultado = await con_reintentos(mi_funcion_async, arg1, arg2)
    """
    ultimo_error = None

    for intento in range(1, intentos + 1):
        try:
            return await funcion_async(*args, **kwargs)
        except Exception as e:
            ultimo_error = e
            if intento < intentos:
                print(f"Intento {intento}/{intentos} falló ({e}). Reintentando en {espera_segundos}s...")
                await asyncio.sleep(espera_segundos)
                espera_segundos *= 1.5  # cada reintento espera un poco más
            else:
                print(f"Se agotaron los {intentos} intentos. Último error: {e}")

    raise ultimo_error