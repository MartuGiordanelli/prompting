# ADR-0004: proveedor fijo para el slot 4

## Decision

El slot 4 (`deepseek/deepseek-v4-flash-0731`) fija el proveedor
`sail-research` y desactiva los fallbacks.

## Evidencia

El log `logs/20260916-155544-deepseek-deepseek-v4-flash-0731.md` registra dos
llamadas consecutivas con el prefijo estático de Conway. La primera devolvió
`cached_tokens = 0`; la segunda, `cached_tokens = 1558`. Esto demuestra un
cache hit dentro de esa conversación. El encabezado del log no registra un
proveedor fijado, así que no sirve como prueba de routing estable.

Los intentos anteriores de Conway, hechos sin proveedor fijo, devolvieron
`cached_tokens = 0`. La prueba de este ADR no demuestra por sí sola que el
prefijo se conserve entre conversaciones distintas: para cumplir ese criterio
se necesitan logs de una serie nueva de intentos con el mismo prefijo.
