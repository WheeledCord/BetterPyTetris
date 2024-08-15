import pygame

WIDTH = 30
EQUATIONS = ['y=x^(2)/8.4']

# Initialize Pygame
HEIGHT = 1000
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mathematical Graph")
clock = pygame.time.Clock()

def run_equations(x: int):
    y_values = []
    for equation in EQUATIONS:
        # Replace "^" with "**" for Python exponentiation and evaluate the equation
        equation = equation.replace('^', '**')
        equation = equation.replace('x', str(x))
        equation = equation.replace('\cdot', '*')
        equation = equation.replace('{', '(').replace('}', ')')
        # Evaluate the equation using Python's eval function
        y = eval(equation.split('=')[1])
        y_values.append(y)
    
    # Return the maximum y value (or adjust based on your needs)
    return int(max(y_values))

graph_data = []

# Run the simulation and collect data
for x in range(WIDTH):
    graph_data.append(run_equations(x))
HEIGHT = max(graph_data)
screen = pygame.display.set_mode((WIDTH, HEIGHT))

print(len(graph_data))
print(graph_data)

def draw_graph():
    screen.fill((255, 255, 255))  # Clear screen with white
    # Draw the graph
    for x in range(WIDTH):
        pygame.draw.line(screen, (0, 0, 0), (x, HEIGHT-graph_data[x]), (x, HEIGHT), 1)

    pygame.display.flip()
    return graph_data

# Main loop
running = True
while running:
    clock.tick(60)
    draw_graph()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                pygame.image.save(screen,'output_graph.png')
            running = False
pygame.quit()