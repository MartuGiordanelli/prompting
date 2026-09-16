import sys

def step(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    offsets = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )

    new_grid = []
    for r in range(rows):
        new_row = []
        for c in range(cols):
            live_neighbors = 0
            for dr, dc in offsets:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '#':
                    live_neighbors += 1

            if live_neighbors == 3 or (grid[r][c] == '#' and live_neighbors == 2):
                new_row.append('#')
            else:
                new_row.append('.')

        new_grid.append(''.join(new_row))

    return new_grid

def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: python3 vida.py <initial_state_file> <generations>\n")
        sys.exit(1)

    filename = sys.argv[1]
    generations = int(sys.argv[2])

    with open(filename) as f:
        grid = [line.rstrip('\n') for line in f]

    for _ in range(generations):
        grid = step(grid)

    if grid:
        sys.stdout.write('\n'.join(grid) + '\n')

if __name__ == '__main__':
    main()
