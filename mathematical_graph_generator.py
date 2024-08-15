import enum
import pygame

WIDTH = 30
EQUATIONS = ['y=x^(2)/8.4','y=20-x','y=10+(10/(10-x))','y=10+(10/(-10+x))']

# Initialize Pygame
HEIGHT = 1000
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mathematical Graph")
clock = pygame.time.Clock()

def run_equations(x: int):
    y_values = []
    for equation in EQUATIONS:
        equation = equation.replace('^', '**')
        equation = equation.replace('x', str(x))
        try:
            y = eval(equation.split('=')[1])
            if y == float('inf'):
                return 'inf'
            elif y == float('-inf'):
                y_values.append(0)
            elif y != y:
                y_values.append(0)
            else:
                y_values.append(y)
        except ZeroDivisionError:
            return 'inf'
        except Exception as e:
            print(f"Error evaluating equation: {e}")
            return 'inf'
    
    return int(max(y_values))

graph_data = []

# Run the simulation and collect data
for x in range(WIDTH):
    graph_data.append(run_equations(x))
for i,y in enumerate(graph_data):
    if y == 'inf':
        graph_data[i] = max([item for item in graph_data if item != 'inf'])
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