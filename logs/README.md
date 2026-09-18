# Indice de logs

Los logs de este directorio los escribe la interfaz de chat y **no se editan ni
se renombran** (ADR-0003). Esta tabla es la unica anotacion humana sobre ellos, y
vive aca afuera justamente para que los logs queden intactos.

Vocabulario: `../CONTEXT.md`.

---

## Ejercicio 1 — demos de los cuatro slots

| Archivo | Slot | Modelo | Que demuestra |
|---|---|---|---|
| `20260915-155338-openai-gpt-5.6-luna.md` | 1 | `openai/gpt-5.6-luna` | Effort bajo (`prompts/ej1/slot1-effort.md`) |
| `20260915-155349-openai-gpt-5.6-luna.md` | 1 | `openai/gpt-5.6-luna` | Effort alto, mismo prompt |
| `20260915-155359-anthropic-claude-haiku-4.5.md` | 2 | `anthropic/claude-haiku-4.5` | Primera pasada del contexto estatico (`prompts/ej1/slot2-cache.md`), `cached_tokens = 0` |
| `20260915-155404-anthropic-claude-haiku-4.5.md` | 2 | `anthropic/claude-haiku-4.5` | Segunda pasada: cache hit, `cached_tokens = 9346` de 9348 |
| `20260915-155410-google-gemini-3.7-flash.md` | 3 | `google/gemini-3.7-flash` | Salida estructurada contra JSON Schema (`prompts/ej1/slot3-json.md` + `slot3-schema.json`) |
| `20260915-155418-deepseek-deepseek-v4-flash-0731.md` | 4 | `deepseek/deepseek-v4-flash-0731` | Misma pregunta que el slot 2, pero **sin** el catalogo (`prompts/ej1/slot4-costo.md`). La comparacion de costo contra el slot 2 no es equivalente: distinto contexto de entrada |
| `20260916-180222-deepseek-deepseek-v4-flash-0731.md` | 4 | `deepseek/deepseek-v4-flash-0731` | Misma pregunta **con** el mismo catalogo que recibio el slot 2 (`prompts/ej1/slot4-costo-con-catalogo.md`, byte a byte igual a `prompts/ej1/slot2-cache.md`), para contrastar costo con una tarea equivalente (mission.md:47) |

## Ejercicio 2 — intentos de Conway

Estan **todos**, incluidos los quemados.

| Archivo | Intento | Prompts | Delta usado | Resultado | Por que se quemo |
|---|---|---|---|---|---|
| `20260916-153121-deepseek-deepseek-v4-flash-0731.md` | 01 | 0 turnos (envio fallido) | `prompts/conway/intento-01.md` | Sin respuesta; error de red antes del turno | No aplica: fallo previo al primer turno |
| `20260916-153227-deepseek-deepseek-v4-flash-0731.md` | 02 | 1 | `prompts/conway/intento-01.md` | Se descarto en su momento por "no extraible sin ambiguedad" | Se descarto porque `scripts/extract_code.py`, tal como estaba en ese momento, no distinguia los fences `python` que aparecian dentro de `### reasoning` de los de la respuesta y encontraba mas de uno. Con la version actual de la herramienta (commit `ff51d50`, fallback al ultimo fence cuando hay razonamiento) este mismo log **si** extrae limpio y pasa los 9 tests — verificado a `/private/tmp` sin tocar `vida.py`. No se re-elige como ganador retroactivamente: la decision de descartarlo se tomo con la herramienta disponible en ese momento |
| `20260916-153635-deepseek-deepseek-v4-flash-0731.md` | 03 | 1 | `prompts/conway/intento-02.md` | Pasa los 9 tests; reemplazado por una serie que demuestra cache entre intentos | No se quemo |
| `20260916-161840-deepseek-deepseek-v4-flash-0731.md` | 04 | 0 turnos (envio interrumpido) | `prompts/conway/serie-02/intento-01.md` | El cliente se interrumpio mientras leia la respuesta HTTP; el log solo tiene encabezado | No hay respuesta ni usage |
| `20260916-163033-deepseek-deepseek-v4-flash-0731.md` | 05 | 1 | `prompts/conway/serie-02/intento-01.md` | Pasa los 9 tests; `cached_tokens = 0` | No se quemo |
| `20260916-163302-deepseek-deepseek-v4-flash-0731.md` | 06 | 1 | `prompts/conway/serie-02/intento-02.md` | Ganador: pasa los 9 tests; `cached_tokens = 1024` | - |

Ganador: intento 06 (`20260916-163302-deepseek-deepseek-v4-flash-0731.md`).
La serie 01 usa `prompts/conway/estatico.md`; la serie 02 usa
`prompts/conway/serie-02/estatico.md`. El prefijo de cada serie se mantuvo
identico entre sus intentos. El intento 04 no tiene un bloque `## user` porque
la interfaz solo registra turnos completados; se conserva el log incompleto
para no ocultar el envio interrumpido.

El `vida.py` de la raiz es, byte a byte, el bloque de codigo de ese log.

## Validacion del proveedor del slot 4

| Archivo | Modelo | Proveedor fijado | Que demuestra |
|---|---|---|---|
| `20260916-155544-deepseek-deepseek-v4-flash-0731.md` | `deepseek/deepseek-v4-flash-0731` | No consta en el encabezado | Dos llamadas con `cached_tokens = 0` y `cached_tokens = 1558` dentro de la misma conversacion |

Esta conversacion mando el prompt de Conway (prefijo estatico de la serie 01 +
`prompts/conway/intento-02.md`) dos veces y devolvio codigo en las dos
respuestas, igual que un intento real. No es un intento del ejercicio 2: se
uso **antes** de correr la serie de intentos para confirmar que el proveedor
elegido sostiene el cache entre llamadas (ver `docs/plan/proximos-pasos.md`,
bloque C), y por eso queda clasificada aparte como validacion, no como
intento 01-06. Se anota aca para que quede transparente por que el conteo de
logs de Conway (7, incluido este) no coincide con el conteo de intentos (6).
