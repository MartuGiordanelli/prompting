# Proximos pasos por bloque

Que recibe cada bloque del bloque A, que produce, donde vive, y que decisiones
quedan abiertas. El plan de A en si esta en `docs/plan/bloque-a.md`.

## B — Prompts del ejercicio 1

**Recibe de A**: la interfaz de chat funcionando (`chat/repl.py`), la tabla de
slots (`SPEC.md` §1.2).

**Produce**: `prompts/ej1/slot{1..4}-*.md` + `prompts/ej1/slot3-schema.json`
(ver `SPEC.md` §4.1). Puede arrancar ya — escribir los prompts no depende del
codigo, solo de la tabla de slots.

**Decisiones abiertas**:
- Slot 2: el estatico tiene que superar el minimo de tokens cacheable de
  Claude Haiku 4.5. **Verificar el numero exacto** — la documentacion de
  OpenRouter solo lista el minimo de Haiku 3.5 (2048 tokens), no confirma que
  Haiku 4.5 use el mismo umbral.
- Slot 4 corre la **misma pregunta** que el slot 2, para la tabla de costo
  comparado (`SPEC.md` §3).

## C — Ejercicio 2 (Conway)

**Recibe de A**: la interfaz funcionando, `/effort` operativo, el mecanismo de
`/file <estatico> [<delta>]`.

**Produce**: el slug de proveedor fijado para el slot 4 en `chat/slots.py`
(hoy `TBD` en `SPEC.md` §1.2), elegido con una prueba de 2 llamadas donde la
segunda de `cache_read < prompt` — es la evidencia de que el proveedor elegido
sostiene el cache entre llamadas. Anotar el slug elegido y por que en
`SPEC.md` o en un ADR.

Corre la serie de intentos de Conway con `/effort` **explicito** en cada envio
(nunca implicito). Pide un unico bloque de codigo por respuesta. `vida.py`
sale **solo** de `scripts/extract_code.py` — nunca se copia a mano del log.

## D — Reporte de usage

**Recibe de A**: los logs con el formato contrato de `SPEC.md` §2.

**Produce**: `scripts/usage_report.py` segun `SPEC.md` §3, incluida la tabla
"slot 2 vs slot 4". Solo lee fences ` ```json `; un bloque `## error` (fence
`text`) no lo rompe. Cualquier diferencia contra el dashboard de OpenRouter se
explica en `INFORME.md`, no se oculta.

## Cierre comun

- `logs/README.md` con todos los logs, incluidos los intentos quemados.
- `scripts/extract_code.py --check vida.py` antes de entregar, para confirmar
  que `vida.py` sigue siendo byte a byte el del log ganador.
