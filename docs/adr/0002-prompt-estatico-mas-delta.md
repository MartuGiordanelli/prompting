---
status: accepted
---

# El prompt del ejercicio 2 se parte en prefijo estatico inmutable + delta por intento

El cache de DeepSeek funciona por prefijo repetido byte a byte: si entre dos
intentos se mueve una coma en la parte estatica, `cached_tokens` vuelve a cero y
se pierde la evidencia de caching que pide la mision. Guardamos el bloque
estatico en `prompts/conway/estatico.md` (rol, contexto, contrato, restricciones,
ejemplos) y el bloque variable en `prompts/conway/intento-NN.md`; la interfaz
concatena estatico + delta al armar el mensaje.

## Considerado y descartado

- **Un archivo completo por intento.** Se diffean facil entre si, pero nada
  impide romper el prefijo sin darse cuenta: el invariante que produce el cache
  hit no queda protegido por la estructura, solo por la disciplina.
- **Un unico archivo que evoluciona en git.** Arbol mas limpio, pero contar los
  intentos exige arqueologia de commits y el prefijo tampoco queda protegido.

## Consecuencias

`prompts/conway/estatico.md` es **inmutable** mientras la serie de intentos este
abierta. Reescribirlo no es "mejorar el prompt": es abrir una serie nueva, y hay
que decirlo en el informe, porque el primer intento de la serie nueva no puede
mostrar cache hit.
