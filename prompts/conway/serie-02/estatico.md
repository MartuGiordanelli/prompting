## Rol

Sos una persona desarrolladora experta en Python. Tu tarea es escribir un
script ejecutable para simular el Juego de la Vida de Conway. Entregá el
archivo completo en un único bloque de código `python`.

## Contexto

El programa recibe una grilla rectangular en un archivo de texto. Cada línea
representa una fila, `#` representa una célula viva y `.` una célula muerta.
El mundo es finito: cualquier posición fuera de la grilla se considera muerta.
Todas las células cambian simultáneamente de una generación a la siguiente.

La cátedra ejecuta `python3 vida.py <archivo_estado_inicial> <generaciones>` y
compara stdout con el estado esperado. El archivo del estado inicial puede no
tener un salto de línea final. La salida debe tener una fila por línea y un
salto de línea final, incluso cuando `generaciones` vale cero.

## Instrucciones

1. Leé exactamente dos argumentos: ruta del archivo y cantidad de generaciones.
2. Cargá la grilla sin cambiar los caracteres `#` y `.` ni sus dimensiones.
3. Para cada generación, contá los ocho vecinos de cada posición consultando
   únicamente celdas dentro de los bordes.
4. Una célula viva sobrevive con dos o tres vecinas vivas; con cualquier otro
   número muere. Una célula muerta nace con exactamente tres vecinas vivas.
5. Calculá toda la grilla nueva desde la grilla anterior y reemplazala recién
   al terminar esa generación.
6. Imprimí únicamente la grilla tras el número solicitado de generaciones.

## Restricciones

- El resultado es un solo archivo llamado `vida.py` y usa solo la biblioteca
  estándar de Python.
- No uses wrap-around, coordenadas negativas como índices válidos ni expansión
  de la grilla. Las celdas que salen de un borde no reaparecen en otro.
- Conservá la cantidad de filas y columnas para cualquier generación.
- No escribas títulos, explicaciones ni mensajes de diagnóstico en stdout.
- La respuesta final debe tener exactamente un bloque `python` con el script
  completo, sin texto antes o después. Si razonás antes de la respuesta,
  evitá los bloques de código dentro del razonamiento.

## Ejemplos verificables

Estos ejemplos describen entradas y salidas del programa. Los números son
cantidades de generaciones; las líneas entre comillas representan filas y no
incluyen las comillas en el archivo.

**Generación cero.** Para `N = 0`, entrada:

    "....."
    "..#.."
    "..#.."
    "..#.."
    "....."

La salida tiene las mismas cinco filas, en el mismo orden. No se aplica ni una
sola transición y no se recorta el borde vacío.

**Oscilador.** Con esa misma entrada y `N = 1`, la salida es:

    "....."
    "....."
    ".###."
    "....."
    "....."

Con `N = 2`, vuelve a la entrada original. La fila central horizontal nace
por los vecinos de la columna vertical; el cambio no se calcula en el lugar.

**Naturaleza muerta.** Para `N = 5`, entrada:

    "...."
    ".##."
    ".##."
    "...."

La salida es igual a la entrada: cada célula viva del bloque tiene tres
vecinas vivas y las demás posiciones no reúnen tres vecinas.

**Soledad.** Para `N = 1`, entrada:

    "..."
    ".#."
    "..."

La salida son tres filas `"..."`: la célula central tiene cero vecinas vivas.

**Nacimiento.** Para `N = 1`, entrada:

    "...."
    ".##."
    ".#.."
    "...."

La salida es:

    "...."
    ".##."
    ".##."
    "...."

La posición de la tercera fila y tercera columna nace con tres vecinas.

**Borde finito.** Para `N = 1`, entrada:

    "###"
    "..."
    "..."

La salida es:

    ".#."
    ".#."
    "..."

El borde superior no recibe vecinos de la última fila. Un mundo con
wrap-around produciría otro resultado y sería incorrecto.

**Glider.** En una grilla de diez filas y diez columnas, la figura inicial
ocupa las tres primeras filas así:

    ".#........"
    "..#......."
    "###......."

Las otras siete filas son `".........."`. Tras cuatro generaciones, las
primeras cuatro filas de salida son `".........."`, `"..#......."`,
`"...#......"` y `".###......"`, respectivamente; las otras seis filas
siguen vacías. La figura se desplazó una posición hacia abajo y a la derecha.

## Input

El delta agregado al final indica el intento de esta serie. Aplicá este
contrato completo y entregá el script solicitado en un solo bloque `python`.
