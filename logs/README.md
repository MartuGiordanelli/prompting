# Indice de logs

Los logs de este directorio los escribe la interfaz de chat y **no se editan ni
se renombran** (ADR-0003). Esta tabla es la unica anotacion humana sobre ellos, y
vive aca afuera justamente para que los logs queden intactos.

Vocabulario: `../CONTEXT.md`.

---

## Ejercicio 1 — demos de los cuatro slots

| Archivo | Slot | Modelo | Que demuestra |
|---|---|---|---|
| | 1 | | Effort bajo |
| | 1 | | Effort alto, mismo prompt |
| | 2 | | Primera pasada del contexto estatico |
| | 2 | | Segunda pasada: cache hit |
| | 3 | | Salida estructurada contra JSON Schema |
| | 4 | | Misma pregunta que el slot 2, para contrastar costo |

## Ejercicio 2 — intentos de Conway

Estan **todos**, incluidos los quemados.

| Archivo | Intento | Prompts | Delta usado | Resultado | Por que se quemo |
|---|---|---|---|---|---|
| | 01 | | `prompts/conway/intento-01.md` | | |

Ganador: PENDIENTE

El `vida.py` de la raiz es, byte a byte, el bloque de codigo de ese log.
