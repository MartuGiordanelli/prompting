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
| `20260915-155418-deepseek-deepseek-v4-flash-0731.md` | 4 | `deepseek/deepseek-v4-flash-0731` | Misma pregunta que el slot 2 (`prompts/ej1/slot4-costo.md`, sin el catalogo), para contrastar costo |

## Ejercicio 2 — intentos de Conway

Estan **todos**, incluidos los quemados.

| Archivo | Intento | Prompts | Delta usado | Resultado | Por que se quemo |
|---|---|---|---|---|---|
| | 01 | | `prompts/conway/intento-01.md` | | |

Ganador: PENDIENTE

El `vida.py` de la raiz es, byte a byte, el bloque de codigo de ese log.
