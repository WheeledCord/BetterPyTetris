import pygame

# Tetromino shapes (represented as 2D matrices)
TETROMINOS = {
    'I': [[1, 1, 1, 1]],                  # I shape
    'O': [[1, 1], [1, 1]],                # O shape
    'T': [[1, 1, 1], [0, 1, 0]],          # T shape
    'S': [[1, 1, 0], [0, 1, 1]],          # S shape
    'Z': [[0, 1, 1], [1, 1, 0]],          # Z shape
    'L': [[1, 1, 1], [1, 0, 0]],          # L shape
    'J': [[1, 1, 1], [0, 0, 1]],          # J shape
}

# Colors for specific tetrominos
COLORS = {
    'I': (0, 255, 255),  # Cyan
    'O': (255, 255, 0),  # Yellow
    'T': (128, 0, 128),  # Purple (for T)
    'S': (0, 255, 0),    # Green (for S)
    'Z': (255, 0, 0),    # Red (for Z)
    'L': (255, 165, 0),  # Orange (for L)
    'J': (0, 0, 255),    # Blue (for J)
}

# Function to rotate a tetromino 90 degrees clockwise
def rotate(tetromino):
    return [list(row) for row in zip(*tetromino[::-1])]

# Function to check if a tetromino fits in the grid at a given position
def can_place(grid, tetromino, x, y, width, height):
    for i, row in enumerate(tetromino):
        for j, cell in enumerate(row):
            if cell:
                if y + i >= height or x + j >= width or grid[y + i][x + j] != (0, 0, 0):
                    return False
    return True

# Function to place a tetromino into the grid
def place_tetromino(grid, tetromino, color, x, y):
    for i, row in enumerate(tetromino):
        for j, cell in enumerate(row):
            if cell:
                grid[y + i][x + j] = color

# Function to remove a tetromino from the grid (backtracking)
def remove_tetromino(grid, tetromino, x, y):
    for i, row in enumerate(tetromino):
        for j, cell in enumerate(row):
            if cell:
                grid[y + i][x + j] = (0, 0, 0)

# Backtracking function to try placing tetrominos optimally
def solve(grid, tetrominos, width, height):
    if not tetrominos:
        return True  # All tetrominos placed

    tetromino_name, tetromino_shape = tetrominos[0]
    remaining_tetrominos = tetrominos[1:]

    for y in range(height):
        for x in range(width):
            for _ in range(4):  # Try 4 rotations
                if can_place(grid, tetromino_shape, x, y, width, height):
                    place_tetromino(grid, tetromino_shape, COLORS[tetromino_name], x, y)
                    if solve(grid, remaining_tetrominos, width, height):
                        return True  # Solution found
                    remove_tetromino(grid, tetromino_shape, x, y)  # Backtrack
                tetromino_shape = rotate(tetromino_shape)

    return False  # No valid solution found

# Function to create an empty grid
def create_grid(width, height):
    return [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

# Main function
def main(width, height):
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Optimal Tetromino Packing")

    grid = create_grid(width, height)

    # Ordered list of tetrominos to place
    tetromino_list = list(TETROMINOS.items())

    # Solve the packing problem
    solve(grid, tetromino_list, width, height)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_o:
                    pygame.image.save(screen, "output.png")
                    print("Image saved as output.png")

        # Draw grid
        for y in range(height):
            for x in range(width):
                screen.set_at((x, y), grid[y][x])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    # Set the size of the rectangle (window)
    rect_width = 200  # Replace with desired width
    rect_height = 300  # Replace with desired height
    main(rect_width, rect_height)
