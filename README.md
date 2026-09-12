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

PENDIENTE — se completa cuando se decida la forma de la interfaz (ver `SPEC.md` §1.1).

Antes de arrancar:

```sh
cp .env.example .env   # y completar OPENROUTER_API_KEY
```

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
| Script del juego de la vida | [`vida.py`](vida.py) |

## Lo importante en tres lineas

`vida.py` es output de un modelo y **no se edita a mano**. Los logs son evidencia
de auditoria y **no se editan nunca**. Lo que se mejora entre intentos es el
prompt, no el codigo. El detalle esta en [`CLAUDE.md`](CLAUDE.md).
