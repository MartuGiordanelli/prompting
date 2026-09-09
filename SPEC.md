# SPEC

Contrato de lo que se construye. Se escribe antes de codear y se reconcilia
contra el codigo al cierre del proyecto.

Vocabulario: `CONTEXT.md`. Decisiones y su porque: `docs/adr/`.

---

## 1. Interfaz de chat (ejercicio 1)

### 1.1 Forma — TBD

**Sin decidir.** Las opciones en juego son CLI de terminal, web local minima
(FastAPI + HTML) o TUI. Nada de lo que sigue depende de cual se elija: el
contrato de abajo es el mismo en los tres casos.

Al cerrar esta decision hay que fijar aca el punto de entrada y el layout del
modulo, y anotarlo en `CLAUDE.md`.

### 1.2 Modelos servidos

Cuatro slots, uno por proveedor (tabla completa en `CONTEXT.md`). Los ids estan
verificados por la catedra al 2026-09-02; **antes de codear hay que confirmarlos
contra `GET https://openrouter.ai/api/v1/models`**. Si alguno cayo del catalogo,
se reemplaza por el equivalente vigente del mismo proveedor y **la sustitucion se
anota en `INFORME.md`**.

### 1.3 Comportamiento requerido

- Permite elegir el modelo.
- **Cambiar de modelo cierra la conversacion actual y empieza una nueva.** No se
  arrastra historial entre modelos.
- Slot 1: permite elegir el nivel de `reasoning.effort`.
- Slot 2: marca el bloque estatico con `cache_control: {"type": "ephemeral"}`.
- Slot 3: acepta un JSON Schema y lo manda como salida estructurada.
- Despues de **cada** respuesta muestra los cinco valores del usage: tokens de
  entrada, de salida, de razonamiento, cacheados y costo.
- Al cerrar cada turno, escribe/actualiza el log de la conversacion.

### 1.4 Configuracion

La key se lee de la variable de entorno `OPENROUTER_API_KEY`. Hay un
`.env.example` versionado como plantilla; `.env` esta ignorado.

---

## 2. Formato del log

**Este formato es un contrato**, no una preferencia de presentacion: lo escribe
la interfaz y lo lee `scripts/usage_report.py`. Cambiarlo se hace aca primero.
Ver ADR-0003.

### 2.1 Nombre y ubicacion

`logs/<YYYYMMDD-HHMMSS>-<proveedor>-<modelo>.md`, con el timestamp del primer
turno de la conversacion. Lo genera la interfaz. Nadie lo renombra.

### 2.2 Estructura

Encabezado con: modelo, timestamp de inicio, y los parametros no-default de la
corrida (effort, schema, cache_control).

Despues, un bloque por turno:

```md
## user — <timestamp>

<el mensaje tal cual se envio>

## assistant — <timestamp>

<la respuesta tal cual llego>

```json
{ ...el objeto `usage` crudo que devolvio OpenRouter, sin reformatear... }
```
```

El bloque de usage se emite **tal cual viene de la API**. No se filtran campos,
no se redondean numeros, no se renombran claves. Es lo que hace que el log sea
evidencia y no un resumen.

### 2.3 Invariantes

- Un log = una conversacion = un modelo.
- Los timestamps son monotonos crecientes dentro del archivo.
- Todo turno de `assistant` tiene su bloque de usage. Sin excepciones.

---

## 3. Reporte de usage

`scripts/usage_report.py` recorre `logs/`, extrae los bloques ` ```json ` y emite
en stdout las tablas markdown que van a `INFORME.md`:

- Por intento: tokens de entrada, salida, razonamiento, cacheados y costo.
- Totales.
- Ahorro por caching, **derivado** (no solo el conteo de `cached_tokens`).

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

Ojo con el slot 2: Anthropic tiene un minimo de tokens para activar el cache. Un
bloque estatico corto **no cachea** aunque lleve `cache_control`.

### 4.2 Ejercicio 2 — Conway

`prompts/conway/estatico.md` (inmutable) + `prompts/conway/intento-NN.md` (el
delta). La interfaz concatena estatico + delta, en ese orden. Ver ADR-0002.

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

Output del intento ganador, copiado sin modificar. Pasa los 9 tests de
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
