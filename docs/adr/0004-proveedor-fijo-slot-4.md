# ADR-0004: proveedor fijo para el slot 4

## Decision

El slot 4 (`deepseek/deepseek-v4-flash-0731`) fija el proveedor
`sail-research` y desactiva los fallbacks.

## Evidence

El 2026-09-16 se hicieron dos llamadas consecutivas con el mismo prefijo
estático y el proveedor fijado explícitamente. OpenRouter devolvió `Sail
Research` en ambas respuestas y `cached_tokens = 693` en ambas; la segunda
llamada conservó el cache en vez de cambiar de proveedor.

Una prueba previa sin proveedor fijo devolvió `Sail Research` en la primera
llamada y `OpenInference` en la segunda. Aunque hubo cache, ese cambio hacía
inestable la serie de Conway y justificaba fijar el proveedor.

La primera llamada de la prueba fijada ya encontró el prefijo caliente por las
pruebas anteriores; por eso esta evidencia demuestra retención del cache con
routing estable, no un cache miss inicial.
