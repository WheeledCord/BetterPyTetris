import pygame
from os import environ as osEnviron

WIDTH = 30
EQUATIONS = ['y=x^(2)/8.4','y=20-x','y=10+(10/(10-x))','y=10+(10/(-10+x))']

# Initialize Pygame
pygame.init()
HEIGHT = 0
MAX_WIDTH = pygame.display.Info().current_w - 300
MAX_HEIGHT = pygame.display.Info().current_h - 300
osEnviron['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mathematical Graph")
clock = pygame.time.Clock()

printed_errors = []
def run_equations(x: int):
    global printed_errors
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
        except:
            if not equation in printed_errors:
                print(f"Error evaluating equation: {equation}")
                printed_errors.append(equation)
                y_values.append(0)
    
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

print(graph_data)

def draw_graph():
    screen.fill((255, 255, 255))  # Clear screen with white
    # Draw the graph
    for x in range(WIDTH):
        pygame.draw.line(screen, (0, 0, 0), (x, HEIGHT-graph_data[x]), (x, HEIGHT), 1)

    pygame.display.flip()

draw_graph()
graph = screen.copy()

new_size = (0,0)
scale = 0
mode = max(WIDTH,HEIGHT)
if mode == WIDTH:
    scale = MAX_WIDTH / WIDTH
    new_size = (MAX_WIDTH,round(scale*HEIGHT))
else:
    scale = MAX_HEIGHT / HEIGHT
    new_size = (round(scale*WIDTH),MAX_HEIGHT)
screen = pygame.display.set_mode(new_size)
screen.blit(pygame.transform.scale(graph,new_size),(0,0))

# Main loop
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                pygame.image.save(graph,'output_graph.png')
            running = False
    pygame.display.flip()
pygame.quit()