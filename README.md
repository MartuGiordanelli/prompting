# prompting

Mision "el prompt minimo": una interfaz de chat sobre OpenRouter que sirve cuatro
modelos de cuatro proveedores, y el juego de la vida de Conway resuelto en la
minima cantidad de prompts posible, con todo el gasto medido.

Consigna: [`mission.md`](mission.md) · Rubrica: [`rubric.md`](rubric.md)

## Correr los tests del juego de la vida

```sh
python3 test_vida.py
```

`test_vida.py` busca `vida.py` en su mismo directorio. Los dos viven en la raiz a
proposito: ver [ADR-0001](docs/adr/0001-vida-y-test-en-la-raiz.md).

## Usar la interfaz de chat

Antes de arrancar:

```sh
cp .env.example .env   # y completar OPENROUTER_API_KEY
```

Despues:

```sh
python3 -m chat
```

Arranca en el slot 1 y queda esperando texto en un prompt `>`. Escribir una
linea y Enter la manda como mensaje. Para salir: `/exit`, `/quit`, Ctrl+D o
Ctrl+C.

### Comandos

| Comando | Que hace |
|---|---|
| `/model N` | Cambia al slot `N` (1 a 4, tabla en `SPEC.md` §1.2) |
| `/effort [nivel\|off]` | Fija el `reasoning.effort` de la sesion para el slot activo, o lo saca con `off`. Sin argumento muestra el effort actual |
| `/schema <ruta.json>\|off` | Activa salida estructurada (`response_format`) con ese JSON Schema, o la saca con `off`. Sin argumento muestra el schema actual |
| `/file <estatico> [<delta>]` | Arma un mensaje `user` a partir de uno o dos archivos y lo manda |
| `/show-reasoning` | Prende/apaga que se muestre el razonamiento del modelo en pantalla (colapsado por default) |
| `"""` | Abre un mensaje multilinea; se cierra con otro `"""` en su propia linea |

`/model`, `/effort` y `/schema` son parametros de sesion: cambiar cualquiera de
los tres **cierra la conversacion actual y abre una nueva** (sin arrastrar
historial). Si la conversacion en curso ya tiene turnos, pide confirmacion
`[y/N]` antes de cerrarla.

Ademas, dentro de una misma conversacion, el tercer prompt (y cualquiera
despues) pide otra confirmacion `[y/N]` porque "quema" el intento — ver
"Quemado" en `CONTEXT.md`.

Contrato completo de comportamiento (que pasa con requests fallidos, el
formato del usage en pantalla, etc.): `SPEC.md` §1.3.

### Validar la tabla de slots

```sh
python3 -m chat --check-models
```

Compara la tabla hardcodeada de `chat/slots.py` contra el catalogo en vivo de
`GET /models` de OpenRouter y avisa diferencias (un id que cayo del catalogo,
efforts que cambiaron). No falla duro: imprime los avisos y termina.

## Generar las tablas de usage

```sh
python3 scripts/usage_report.py
```

El comando lee todos los logs y su indice, e imprime tablas Markdown para el
informe: intentos de Conway, totales, ahorro por cache y comparacion de costo
entre los slots 2 y 4. Marca `n/d` cuando un log no trae usage o cuando el
ahorro no se puede derivar con una referencia comparable. No necesita red ni
API key.

## Mapa del repo

| Que | Donde |
|---|---|
| Glosario del proyecto | [`CONTEXT.md`](CONTEXT.md) |
| Que se construye y con que contrato | [`SPEC.md`](SPEC.md) |
| Como se trabaja (y que esta prohibido) | [`CLAUDE.md`](CLAUDE.md) |
| Decisiones y su porque | [`docs/adr/`](docs/adr/) |
| Plan de implementacion por bloque | [`docs/plan/`](docs/plan/) |
| Informe del ejercicio 3 | [`INFORME.md`](INFORME.md) |
| Logs de conversaciones + indice | [`logs/`](logs/) |
| Prompts versionados | [`prompts/`](prompts/) |
| Interfaz de chat | [`chat/`](chat/) |
| Scripts standalone (extraccion de codigo, reporte de usage) | [`scripts/`](scripts/) |
| Script del juego de la vida | [`vida.py`](vida.py) |

## Lo importante en tres lineas

`vida.py` es output de un modelo y **no se edita a mano**. Los logs son evidencia
de auditoria y **no se editan nunca**. Lo que se mejora entre intentos es el
prompt, no el codigo. El detalle esta en [`CLAUDE.md`](CLAUDE.md).
