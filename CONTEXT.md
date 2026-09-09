# CONTEXT

Glosario del proyecto. Solo vocabulario: nada de decisiones de implementacion
(esas viven en `docs/adr/`) ni de alcance (eso es `SPEC.md`).

Cuando una palabra de este archivo aparece en `INFORME.md`, en `logs/README.md`
o en un mensaje de commit, significa exactamente lo que dice aca.

---

## Slot

Uno de los cuatro modelos que la interfaz de chat tiene que servir, cada uno de
un proveedor distinto. Un slot no es un modelo cualquiera: es un modelo **mas**
la capacidad que ejercita.

| Slot | Modelo | Capacidad que ejercita |
|---|---|---|
| 1 | `openai/gpt-5.6-luna` | Effort configurable |
| 2 | `anthropic/claude-haiku-4.5` | Caching explicito (`cache_control`) |
| 3 | `google/gemini-3.7-flash` | Salidas estructuradas (JSON Schema) |
| 4 | `deepseek/deepseek-v4-flash-0731` | El escalon barato |

Decir "el slot 2" es mas preciso que decir "Haiku", porque si el id cae del
catalogo y se reemplaza por el equivalente vigente, el slot sigue siendo el
mismo y la sustitucion se anota en el informe.

## Conversacion

Una secuencia de turnos con **un solo** modelo, desde el primer mensaje hasta
que se cierra. Cambiar de modelo no continua una conversacion: la termina y
empieza otra.

Una conversacion produce exactamente **un log**.

## Turno

Un par mensaje/respuesta. El turno del asistente lleva su bloque de usage.

## Prompt

Un mensaje de rol `user`. Se cuentan por turnos de rol `user`, sin excepciones:
un mensaje que solo dice "corre los tests" cuenta igual que cualquier otro.

## Intento

**Una conversacion** con el modelo del ejercicio 2 destinada a producir
`vida.py`. Contiene 1 o 2 prompts y produce 1 log.

Intento y conversacion son la misma cosa vista desde dos angulos: "conversacion"
es la unidad tecnica, "intento" es la unidad que cuenta el informe. Un intento
con dos prompts sigue siendo **un** intento.

"Corrida" es sinonimo de intento. Se prefiere "intento".

## Quemado

Un intento se quema en el momento en que se envia un **tercer** prompt. A partir
de ahi ese intento no puede ganar, se cierra, y se abre un intento nuevo con el
prompt reescrito desde cero.

Un intento tambien esta quemado si termino con menos de 3 prompts pero su
`vida.py` no pasa los 9 tests y se decidio no seguir.

Los intentos quemados **se entregan**. Esconderlos cuesta puntos.

## Ganador

El unico intento cuyo `vida.py` pasa los 9 tests de `test_vida.py`. El `vida.py`
de la raiz del repo es, byte a byte, el que produjo el ganador.

## Prefijo estatico

El bloque de texto que abre **todos** los prompts de un mismo experimento y que
no cambia nunca entre intentos: rol, contexto, contrato, restricciones y
ejemplos. Vive en `prompts/conway/estatico.md`.

Es inmutable por definicion: si cambia, deja de ser prefijo estatico y el cache
se pierde. Cambiarlo es empezar una serie nueva de intentos.

## Delta

La parte variable de un prompt, la que va **al final**, despues del prefijo
estatico. Es lo unico que se reescribe entre intentos. Vive en
`prompts/conway/intento-NN.md`.

## Cache hit

Una respuesta cuyo usage trae `cached_tokens > 0`. Significa que el proveedor
reconocio el prefijo estatico de una llamada anterior y no lo volvio a cobrar
a precio lleno.

Un cache hit en el **primer** intento de una serie es imposible: si aparece,
hubo corridas previas que no se entregaron.

## Log

El archivo `.md` que registra una conversacion completa: rol, mensaje y usage
por turno. Se escribe automaticamente y **no se edita despues**.

El log es la evidencia de auditoria del proyecto. Sin log, la corrida no existe.

## Indice de logs

`logs/README.md`. Mapea cada archivo de log a su rol (demo del slot N, intento
NN quemado, ganador). Es la unica anotacion humana sobre los logs, y vive fuera
de ellos justamente para que los logs queden intactos.
