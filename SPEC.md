# SPEC

Contrato de lo que se construye. Se escribe antes de codear y se reconcilia
contra el codigo al cierre del proyecto.

Vocabulario: `CONTEXT.md`. Decisiones y su porque: `docs/adr/`.

---

## 1. Interfaz de chat (ejercicio 1)

### 1.1 Forma

REPL de terminal, `python3 -m chat`. Solo biblioteca estandar: HTTP con
`urllib`, sin `requests` ni el SDK de OpenAI (el SDK puede ocultar campos del
usage crudo).

Layout del paquete:

```
chat/
  __main__.py    punto de entrada, `python3 -m chat`
  slots.py       tabla de slots hardcodeada + validacion
  env.py         parser minimo de .env
  openrouter.py  armado de requests y llamada HTTP
  log.py         escritura del log (contrato en §2)
  usage.py       formateo de la linea de usage
  repl.py        loop de comandos
  tests/         unittest, sin red
scripts/
  extract_code.py   standalone, NO importa de chat/
```

Comandos del REPL: `/model N`, `/effort [nivel|off]`, `/schema <ruta.json>|off`,
`/file <estatico> [<delta>]`, `/show-reasoning`. Enter envia el mensaje;
multilinea entre `"""`.

### 1.2 Modelos servidos

Cuatro slots, uno por proveedor (tabla completa en `CONTEXT.md`). Ids
re-verificados contra `GET https://openrouter.ai/api/v1/models` el 2026-09-12:
siguen vigentes, sin sustituciones.

| Slot | Modelo | Efforts (catalogo) | Default | `cache_control` | Proveedor fijado |
|---|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | max, xhigh, high, medium, low, none | medium | no | — |
| 2 | `anthropic/claude-haiku-4.5` | ninguno | — | si | `anthropic` |
| 3 | `google/gemini-3.7-flash` | high, medium, low (razonamiento obligatorio) | medium | no | — |
| 4 | `deepseek/deepseek-v4-flash-0731` | max, high, low | high | no | `sail-research` |

Los efforts de cada slot salen del campo `reasoning.supported_efforts` /
`default_effort` que trae `/models` para ese modelo. Sin `/effort` no se manda
`reasoning`.

Proveedor fijado = `provider: {order: [slug], allow_fallbacks: false}`. Motivo:
al slot 4 (DeepSeek v4 flash) lo sirven ~28 terceros y el sticky routing de
OpenRouter para cache vence a los 10 min de inactividad; sin fijar proveedor, el
segundo intento de una serie puede caer en otro proveedor y dar
`cached_tokens: 0`, perdiendo el criterio 2.4 de la rubrica.

`python3 -m chat --check-models` compara esta tabla contra `/models` en vivo y
avisa diferencias (id caido del catalogo, efforts que cambiaron).

### 1.3 Comportamiento requerido

- Permite elegir el modelo.
- **Cambiar de modelo o cualquier parametro de sesion (`/effort`, `/schema`)
  cierra la conversacion actual y empieza una nueva.** No se arrastra historial
  entre configuraciones. Pide confirmacion si la conversacion actual ya tiene
  turnos.
- `/effort` y `/schema` son de sesion, validas en cualquier slot, y se validan
  contra la tabla de slots antes de mandar el request. Sin `/effort` no se manda
  `reasoning`.
- Slot 1: permite elegir el nivel de `reasoning.effort`.
- Slot 2: marca el bloque estatico con `cache_control: {"type": "ephemeral"}`.
- Slot 3: acepta un JSON Schema y lo manda como salida estructurada.
- `/file <estatico> [<delta>]` arma **un** mensaje `user`. En el slot 2, el
  `content` va en 2 partes con `cache_control: {"type": "ephemeral"}` en la
  primera (el estatico). En el resto de los slots, `content` es un string
  `estatico + delta`, **sin separador agregado** entre ambos. Nada de esto va en
  el rol `system`.
- `/schema <ruta.json>` manda `response_format: {type: "json_schema",
  json_schema: {name, strict: true, schema}}`. El REPL solo chequea que la
  respuesta parsee como JSON valido (✓/✗ en pantalla), no valida contra el
  schema. `/schema off` lo saca de la sesion.
- Confirmacion `[y/N]` antes de mandar el **tercer** prompt de una conversacion
  ("esto quema el intento", ver `CONTEXT.md`).
- Un request fallido **no** es turno: no entra al historial de la conversacion,
  se registra en el log como bloque `## error`. Timeout de 600s.
- Despues de **cada** respuesta muestra el usage en una linea:
  `in N (cached N) · out N (reasoning N) · $cost · cache_discount $X`. Un campo
  ausente en la respuesta de la API se muestra como `n/d`, **nunca `0`**
  (hallazgo del criterio 3.2: `0` implica "se cobro y dio cero", `n/d` implica
  "la API no informo este campo", son cosas distintas). Sin acumulados entre
  turnos ni entre conversaciones — eso lo hace el bloque D con
  `usage_report.py`.
- El razonamiento del modelo se muestra colapsado en pantalla salvo que se pida
  `/show-reasoning`.
- Al cerrar cada turno, escribe/actualiza el log de la conversacion.

### 1.4 Configuracion

La key se lee de la variable de entorno `OPENROUTER_API_KEY`. Hay un
`.env.example` versionado como plantilla; `.env` esta ignorado. El parser de
`.env` es minimo y de stdlib; si la variable de entorno real ya esta seteada,
gana sobre lo que diga el archivo. Sin key en ninguno de los dos lados, el
programa falla al arrancar.

---

## 2. Formato del log

**Este formato es un contrato**, no una preferencia de presentacion: lo escribe
la interfaz y lo lee `scripts/usage_report.py`. Cambiarlo se hace aca primero.
Ver ADR-0003.

### 2.1 Nombre y ubicacion

`logs/<YYYYMMDD-HHMMSS>-<proveedor>-<modelo>.md`, con el timestamp del primer
turno de la conversacion. Lo genera la interfaz. Nadie lo renombra.

### 2.2 Estructura

Encabezado con: modelo, proveedor fijado (si lo hay), effort (`high` explicito
si se pidio, o `default del modelo (high)` si se uso el default sin pedirlo),
ruta del schema (si lo hay), `cache_control` (si lo hay), y timestamp de inicio.

El archivo se crea en el **primer intento de envio** de la conversacion, no
recien en el primer turno exitoso: asi se puede registrar un error previo al
primer turno. La escritura es append-only.

Despues, un bloque por turno:

```md
## user — <timestamp>

<el mensaje tal cual se envio>

## assistant — <timestamp>

### reasoning

```text
<texto de razonamiento, si la API lo devolvio, ANTES de la respuesta>
```

<la respuesta tal cual llego>

```json
{ ...el objeto `usage` crudo que devolvio OpenRouter, sin reformatear... }
```
```

La subseccion `### reasoning` solo aparece si la API devolvio texto de
razonamiento para ese turno.

Un request fallido se registra como bloque `## error — <timestamp>`, con el
status y el body en un fence ` ```text ` (**nunca** ` ```json `: el script de
usage extrae los fences `json` y un error ahi rompe el reporte). No cuenta como
turno.

El bloque de usage se emite **tal cual viene de la API**. No se filtran campos,
no se redondean numeros, no se renombran claves. Es lo que hace que el log sea
evidencia y no un resumen.

**Verificar pendiente en implementacion**: si la respuesta de OpenRouter trae un
campo `provider` (la doc no lo confirma). Si viene, va al log.

### 2.3 Invariantes

- Un log = una conversacion = un modelo.
- Los timestamps son monotonos crecientes dentro del archivo.
- Todo turno de `assistant` tiene su bloque de usage. Sin excepciones.
- Los **unicos** fences `json` del log son los bloques de usage. Cualquier otro
  bloque de codigo o de error usa `text` (o el lenguaje que corresponda, nunca
  `json`).

### 2.4 Extraccion de codigo

`scripts/extract_code.py <log> [--out vida.py | --check vida.py]` es standalone:
**no importa nada de `chat/`**. Toma el **ultimo** fence ` ```python ` de la
respuesta del **ultimo turno assistant** del log (nunca de la subseccion
`### reasoning`) y escribe su contenido, mas un `\n` final, en la ruta de
`--out`; con `--check` compara byte a byte contra el archivo dado en vez de
escribir.

Falla si esa respuesta tiene mas de un fence `python`: la ambiguedad de cual es
"el" bloque de codigo no se resuelve en silencio — **excepto** el caso en que
el turno tiene subseccion `### reasoning`: como el razonamiento puede contener
fences ` ```python ` anidados (caso adversarial) que hacen ver "mas de uno"
donde la respuesta real tiene un solo bloque, ahi el script cae al **ultimo**
fence `python` de todo el turno (razonamiento + respuesta) en vez de fallar.
Sin `### reasoning`, la regla estricta se mantiene: mas de un fence es error.
Este fallback esta cubierto en `scripts/tests/test_extract_code.py` y es el
motivo por el que el intento 02 de Conway (`logs/20260916-153227-...md`,
descartado en su momento por "no extraible sin ambiguedad") extrae limpio con
la version actual de la herramienta — ver `logs/README.md`.

---

## 3. Reporte de usage

`scripts/usage_report.py` recorre `logs/`, usa `logs/README.md` para clasificar
cada archivo y extrae los bloques ` ```json ` de los turnos assistant. Falla si
un log no figura en el indice o si el indice nombra un archivo ausente. Emite
en stdout las tablas markdown que van a `INFORME.md`:

- Por intento: tokens de entrada, salida, razonamiento, cacheados y costo.
- Totales separados para demos, Conway y validacion, mas el total de todos los
  logs con usage registrado.
- Ahorro por caching, **derivado** (no solo el conteo de `cached_tokens`).
- Tabla "ej1: slot 2 vs slot 4, misma pregunta" — contrasta el costo de la misma
  consulta entre el slot con cache explicito y el escalon barato (§4.1).

El script solo lee fences ` ```json ` de turnos assistant; un bloque
`## error` con fence `text` no lo confunde. Un log sin respuesta figura como
`sin usage`: su facturacion real no se infiere como cero. Los campos ausentes
tambien se muestran `n/d`. Las diferencias contra el dashboard de OpenRouter
se explican en `INFORME.md`.

Para derivar el ahorro, si OpenRouter informa `cache_discount` se usa ese
valor. Si no lo informa, se compara el costo de entrada desglosado del turno
con el costo esperado sin cache a la tarifa observada en un turno previo sin
cache del mismo modelo y proveedor fijado. Sin proveedor fijado, solo se
compara con un turno previo de la misma conversacion. Sin referencia comparable,
el ahorro se muestra `n/d` y no se suma como cero. La tabla de slots 2 y 4
senala si los mensajes tienen contextos distintos; no presenta su diferencia
de costo como una medicion equivalente.

No transcribir estos numeros a mano. El punto del script es que el informe no
pueda reportar menos intentos de los que hay.

---

## 4. Prompts

### 4.1 Ejercicio 1 — demos guionadas

Un prompt por slot en `prompts/ej1/`. No son chats improvisados: son experimentos
con un control y una variable, porque la rubrica compara dos corridas.

| Archivo | Slot | Que demuestra |
|---|---|---|
| `slot1-effort.md` | 1 | El mismo prompt corrido con dos niveles de effort distintos |
| `slot2-cache.md` | 2 | Un bloque estatico grande, corrido dos veces: la segunda tiene que dar `cached_tokens > 0` |
| `slot3-json.md` | 3 | Una respuesta que valida contra un JSON Schema |
| `slot4-costo.md` | 4 | La misma pregunta que el slot 2, para contrastar costo |
| `slot4-costo-con-catalogo.md` | 4 | La misma pregunta **y** el mismo catalogo que recibio el slot 2 (byte a byte igual a `slot2-cache.md`), para una comparacion de costo con tarea equivalente (mission.md:47); `slot4-costo.md` solo mandaba la pregunta y no es comparable |

Ojo con el slot 2: Anthropic tiene un minimo de tokens para activar el cache. Un
bloque estatico corto **no cachea** aunque lleve `cache_control`.

### 4.2 Ejercicio 2 — Conway

La serie inicial usa `prompts/conway/estatico.md` (inmutable) +
`prompts/conway/intento-NN.md` (el delta). La serie 02 usa
`prompts/conway/serie-02/estatico.md` + `intento-NN.md` en esa carpeta. Se
abrio una serie nueva porque la primera no mostro cache hits entre intentos;
ningun prefijo anterior se modifico. La interfaz concatena estatico + delta,
en ese orden. Ver ADR-0002 e `INFORME.md` §2.4.

El estatico tiene que cubrir los seis componentes: rol, contexto, instrucciones,
restricciones, ejemplos e input. El contrato de `vida.py` va completo adentro:

- Uso: `python3 vida.py <archivo_estado_inicial> <generaciones>`
- Grilla rectangular, `#` viva, `.` muerta, una linea por fila.
- Mundo **finito**, sin wrap-around: fuera del borde todo esta muerto.
- Imprime por stdout la grilla tras N generaciones, en el mismo formato.
- `generaciones = 0` imprime el estado inicial tal cual.
- Un solo script, **solo stdlib**.

---

## 5. `vida.py`

Output del intento ganador 06, extraido de su log con
`scripts/extract_code.py`, sin edicion manual. Pasa los 9 tests de
`test_vida.py`. Vive en la raiz, hermano del test (ADR-0001).

---

## 6. `INFORME.md`

Dos partes:

1. **Trabajo previo**: que es un router de modelos y que problema resuelve; el
   mapa de los siete proveedores (precio in/out por millon, ventana de contexto,
   posicion en benchmarks); la comparacion de `supported_parameters` entre
   fichas de proveedores distintos.
2. **La cuenta final**: las tablas de `usage_report.py`, los tokens de
   pensamiento y que se facturo por ellos, el ahorro por cache derivado, el gasto
   total contrastado **explicitamente** contra el dashboard de OpenRouter, y una
   conclusion de tres lineas que nombre una decision concreta (un modelo, un
   parametro, un cambio de prompt).

Si hubo sustitucion de algun id del catalogo, se anota aca.
