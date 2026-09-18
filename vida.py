import sys

def leer_grilla(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

def contar_vecinos(grilla, fila, col):
    filas = len(grilla)
    columnas = len(grilla[0]) if filas else 0
    vivos = 0

    for i in range(fila - 1, fila + 2):
        for j in range(col - 1, col + 2):
            if i == fila and j == col:
                continue
            if 0 <= i < filas and 0 <= j < columnas:
                if grilla[i][j] == '#':
                    vivos += 1

    return vivos

def siguiente_generacion(grilla):
    if not grilla:
        return []

    filas = len(grilla)
    columnas = len(grilla[0])
    nueva = []

    for i in range(filas):
        fila_nueva = []
        for j in range(columnas):
            vecinos = contar_vecinos(grilla, i, j)

            if grilla[i][j] == '#':
                fila_nueva.append('#' if vecinos in (2, 3) else '.')
            else:
                fila_nueva.append('#' if vecinos == 3 else '.')

        nueva.append(''.join(fila_nueva))

    return nueva

def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Uso: python3 vida.py <archivo_estado_inicial> <generaciones>\n")
        sys.exit(1)

    ruta = sys.argv[1]

    try:
        generaciones = int(sys.argv[2])
    except ValueError:
        sys.stderr.write("Error: la cantidad de generaciones debe ser un entero.\n")
        sys.exit(1)

    grilla = leer_grilla(ruta)

    for _ in range(generaciones):
        grilla = siguiente_generacion(grilla)

    if grilla:
        sys.stdout.write('\n'.join(grilla) + '\n')

if __name__ == '__main__':
    main()
