## Rol

Sos una persona desarrolladora experta en Python y en el Juego de la Vida de
Conway. Tu tarea es producir un único script ejecutable que resuelva el
problema descripto abajo.

## Contexto

El script se ejecutará desde la línea de comandos sobre un estado inicial
representado como una grilla rectangular. La grilla usa `#` para una célula
viva y `.` para una célula muerta. El objetivo es simular un número dado de
generaciones del Juego de la Vida de Conway.

## Instrucciones

Escribí `vida.py` para que lea los argumentos de la línea de comandos, cargue
el estado inicial desde el archivo indicado, simule exactamente la cantidad de
generaciones solicitada y escriba el estado final por stdout.

En cada generación, para cada célula contá sus ocho vecinos. Una célula viva
sobrevive con dos o tres vecinos vivos; en cualquier otro caso muere. Una
célula muerta nace exactamente con tres vecinos vivos. Aplicá las
actualizaciones simultáneamente, usando el estado anterior para calcular toda
la generación siguiente.

## Restricciones

- La interfaz es `python3 vida.py <archivo_estado_inicial> <generaciones>`.
- La grilla es rectangular y tiene una línea por fila.
- El mundo es finito: no hay wrap-around; fuera del borde todo está muerto.
- `generaciones = 0` debe imprimir el estado inicial exactamente.
- La salida debe conservar la misma cantidad de filas y columnas y terminar
  con una línea nueva.
- El programa debe ser un único archivo y usar solamente la biblioteca
  estándar de Python.
- No agregues dependencias, archivos auxiliares ni cambios al test.
- La respuesta debe contener exactamente un bloque de código `python` con el
  contenido completo de `vida.py`, sin texto antes ni después y sin otros
  bloques de código.

## Ejemplos

Entrada de archivo:

```text
...
.#.
...
```

Con cero generaciones, la salida debe ser exactamente la misma grilla.

Un blinker vertical:

```text
.#.
.#.
.#.
```

Después de una generación debe transformarse en un blinker horizontal:

```text
...
###
...
```

## Input

El delta que sigue a este prefijo indicará cualquier detalle específico del
intento actual. Si no hay delta, aplicá directamente este contrato completo y
entregá la implementación solicitada.
