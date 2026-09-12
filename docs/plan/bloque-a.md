# Plan — Bloque A (interfaz de chat)

Contrato completo en `SPEC.md` §1 y §2. Esto no lo duplica: es la secuencia de
commits para llegar de "SPEC escrita" a "interfaz funcionando", cada uno con su
verificacion.

## Decisiones resumidas

REPL de terminal (`python3 -m chat`), solo stdlib, `urllib` para HTTP (sin
`requests` ni SDK de OpenAI: el SDK puede ocultar campos del usage crudo). Cuatro slots
hardcodeados (tabla en `SPEC.md` §1.2). Cambiar de modelo o de parametro de
sesion cierra la conversacion. `/effort` y `/schema` validados contra la tabla
de slots. Un log por conversacion, formato contrato en `SPEC.md` §2.
`scripts/extract_code.py` standalone, nunca importa de `chat/`.

Detalle completo de las 19 decisiones: ver `SPEC.md` y `docs/adr/`.

## Tareas

- [ ] 1. `docs:` SPEC + este plan (este commit)
  **Verifica**: `SPEC.md` no tiene ningun `TBD` salvo el proveedor del slot 4.

- [x] 2. `feat:` `chat/slots.py` + `chat/env.py`, commitear `.env.example`
  **Verifica**: tests de `env.py` — precedencia (env real gana sobre archivo),
  comentarios en el `.env`, falla clara si falta la key.

- [x] 3. `feat:` `chat/openrouter.py`
  **Verifica**: el body armado es exacto por slot — `cache_control` solo en el
  slot 2, `estatico + delta` sin separador agregado, `reasoning` solo si hay
  `/effort` activo, `provider` solo en los slots que lo fijan.

- [x] 4. `feat:` `chat/log.py`
  **Verifica**: test de contrato del formato de log, con un parser **independiente**
  escrito contra `SPEC.md` §2 (no reutiliza el codigo de escritura).

- [x] 5. `feat:` `chat/usage.py`
  **Verifica**: un campo ausente en la respuesta de la API se muestra `n/d`,
  nunca `0`.

- [x] 6. `feat:` `chat/repl.py` + `chat/__main__.py`
  **Verifica**: cambiar de modelo o de cualquier parametro abre conversacion
  nueva; un effort invalido para el slot activo se rechaza antes de mandar el
  request; aparece la confirmacion `[y/N]` antes del tercer prompt; un request
  fallido no entra al historial y se registra como `## error`.

- [x] 7. `feat:` `--check-models`
  **Verifica**: compara la tabla hardcodeada contra `GET /models` en vivo y
  reporta diferencias.

- [x] 8. `feat:` `scripts/extract_code.py`
  **Verifica**: extraccion byte a byte contra el fence del log; falla si la
  respuesta tiene mas de un fence `python`; ignora el texto de `### reasoning`.

- [ ] 9. `docs:` README "Usar la interfaz de chat"
  **Verifica**: smoke manual, un chat por slot — son los 4 logs que pide el
  criterio 1.1 de la rubrica.

Cada tarea lleva sus tests y tilda su checkbox en el mismo commit que la
implementa. Correr todos con:

```sh
python3 -m unittest discover chat/tests
```
