# CLAUDE.md

Instrucciones para cualquier agente o persona que trabaje en este repo.

Leer antes: `CONTEXT.md` (glosario) y `SPEC.md` (que se construye).
El vocabulario de `CONTEXT.md` es obligatorio: "intento", "quemado", "ganador",
"prefijo estatico" y "delta" significan lo que dice ahi, no lo que parezcan.

---

## Prohibiciones duras

Estas no son preferencias de estilo. Cada una protege evidencia que, si se
rompe, no se puede reconstruir.

### 1. `vida.py` JAMAS se edita a mano

`vida.py` es **output de un modelo**, no codigo nuestro. Tiene que coincidir byte
a byte con el bloque de codigo que aparece en el log del intento ganador.

Si los tests fallan, la respuesta correcta **nunca** es tocar `vida.py`. Es:

1. Si el intento va por su primer prompt: mandar un segundo prompt puliendo.
2. Si ya va por el segundo: el intento esta quemado. Cerrarlo, reescribir el
   delta desde cero y abrir un intento nuevo.

Lo que se mejora entre intentos es **el prompt**, no el codigo.

Esto incluye: no reformatear, no correr un linter sobre el archivo, no arreglar
un import, no sacar un comentario, no renombrar una variable. Nada.

### 2. Los logs de `logs/` no se editan nunca

Se escriben automaticamente y quedan como quedaron. No se renombran, no se
reordenan, no se les corrige el usage, no se les agrega contexto.

Toda anotacion humana va en `logs/README.md`.

Un intento quemado se entrega igual que el ganador. Borrar un log es peor que
haber fallado.

### 3. `prompts/conway/estatico.md` es inmutable mientras la serie este abierta

El cache por prefijo se rompe con un solo caracter de diferencia. Si hay que
cambiarlo, se abre una serie nueva de intentos y se documenta en el informe.

Lo que se reescribe entre intentos es `prompts/conway/intento-NN.md`.

### 4. Ningun secreto entra al repo

La key se lee de `OPENROUTER_API_KEY`. `.env` esta en `.gitignore`. No hardcodear
keys, no pegarlas en logs, no pegarlas en el informe.

---

## Convenciones

- **Python 3**, biblioteca estandar como default. Cada dependencia hay que
  justificarla. `vida.py` en particular **solo** puede usar la stdlib: es parte
  del contrato de la mision.
- **Docs e informe en espaniol**, codigo e identificadores en ingles. Los
  archivos de la catedra (`mission.md`, `rubric.md`, `test_vida.py`) no se tocan.
- **Commits convencionales** (`feat:`, `docs:`, `chore:`...), en imperativo, uno
  por unidad de trabajo. El criterio 4.3 de la rubrica evalua la historia: nada
  de un unico commit "todo".
- **Sin atribucion de IA** en los mensajes de commit.

## Layout

```
vida.py              output del modelo ganador. INTOCABLE (ver prohibicion 1)
test_vida.py         de la catedra, tal cual se entrego. Hermano de vida.py a proposito (ADR-0001)
CONTEXT.md           glosario
SPEC.md              que se construye y con que contrato
INFORME.md           trabajo previo + la cuenta final del ejercicio 3
docs/adr/            decisiones dificiles de revertir, con su porque
prompts/ej1/         prompts guionados de las demos de los 4 slots
prompts/conway/      estatico.md (inmutable) + intento-NN.md (el delta)
logs/                logs crudos + README.md como indice
scripts/             usage_report.py: agrega los totales desde logs/
```

## Como se corren los tests

```sh
python3 test_vida.py           # busca vida.py al lado
python3 test_vida.py ruta/a/vida.py
```

Los 9 tienen que dar verde. Ocho no alcanza: el criterio es binario por test.

## Antes de dar algo por terminado

- Los numeros de `INFORME.md` salen de `scripts/usage_report.py`, no de
  transcribir a mano.
- `logs/README.md` lista **todos** los intentos, incluidos los quemados.
- `SPEC.md` describe lo que el codigo hace de verdad (se reconcilia al cierre).
