---
status: accepted
---

# Los logs se escriben automaticamente y no se editan; la anotacion humana vive en un indice aparte

Los logs son la evidencia de auditoria del proyecto: cualquier marca de edicion
posterior (nombres puestos a mano, timestamps fuera de orden, usage reformateado)
degrada su valor probatorio. Por eso la interfaz escribe siempre
`logs/<timestamp>-<modelo>.md` y nadie los toca despues, y toda la anotacion
humana —que archivo corresponde a que slot, cual intento se quemo, cual gano—
vive en `logs/README.md`, fuera de los logs.

El usage se embebe crudo, tal cual lo devuelve OpenRouter, en un bloque
` ```json ` al cierre de cada turno del asistente: el mismo archivo sirve al
lector humano y al script que agrega los totales del informe, sin necesidad de
un sidecar `.json` que pueda desincronizarse.

## Consecuencias

El formato del log deja de ser libre: es un contrato entre la interfaz que lo
escribe y `scripts/usage_report.py` que lo lee. Cambiar el formato del bloque de
usage rompe el reporte, asi que el formato se documenta en `SPEC.md` y se cambia
ahi primero.

Como los totales del informe se derivan de los logs y no se transcriben, el
informe no puede reportar menos intentos de los que hay.
