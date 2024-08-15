import pygame

# Constants

# -- Hard Drop -- #
# Spring constant for the physics simulation
SPRING_CONSTANT = 100
# Damping factor to simulate energy loss
DAMPING = 0.25
# Mass of the object
MASS = 1.0
# Time step for the simulation
TIME_STEP = 0.1
# Maximum displacement (10px up or down)
MAX_DISPLACEMENT = 10

# -- Soft Drop -- #
# # Spring constant for the physics simulation
# SPRING_CONSTANT = 100
# # Damping factor to simulate energy loss
# DAMPING = 0.18
# # Mass of the object
# MASS = 1.0
# # Time step for the simulation
# TIME_STEP = 0.1
# # Maximum displacement (10px up or down)
# MAX_DISPLACEMENT = 4

# Initialize Pygame
WIDTH, HEIGHT = 1000, 1+2*MAX_DISPLACEMENT
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spring Physics Graph")
clock = pygame.time.Clock()

# Physics simulation variables
position = MAX_DISPLACEMENT
velocity = 0.0
acceleration = 0.0
time = 0.0

def find_flatline_index(lst):
    n = len(lst)
    for i in range(n):
        # Check if the rest of the list from index i is all the same
        if all(x == lst[i] for x in lst[i:]):
            return i
    return -1  # Return -1 if no flatline is found

def simulate_spring(position, velocity, acceleration, time_step):
    force = -SPRING_CONSTANT * position
    acceleration = force / MASS
    velocity += acceleration * time_step
    position += velocity * time_step
    # Apply damping
    velocity *= (1 - DAMPING)
    return position, velocity, acceleration

def draw_graph():
    screen.fill((255, 255, 255))  # Clear screen with black
    graph_data = []
    
    # Run the simulation and collect data
    pos = MAX_DISPLACEMENT
    vel = 0.0
    acc = 0.0
    for t in range(WIDTH):
        pos, vel, acc = simulate_spring(pos, vel, acc, TIME_STEP)
        # Scale the position to fit the HEIGHT of the graph
        y = int(HEIGHT / 2 - pos)
        y = max(0, min(HEIGHT - 1, y))  # Clamping to be within bounds
        graph_data.append(y)
    
    # Draw the graph
    for i in range(WIDTH - 1):
        pygame.draw.line(screen, (0, 0, 0), (i, graph_data[i]), (i + 1, graph_data[i + 1]), 1)
        pygame.draw.line(screen, (0, 0, 0), (i, graph_data[i]), (i, HEIGHT), 1)

    pygame.display.flip()
    return graph_data

flatline_index = find_flatline_index(draw_graph())
print(f"The list flatlines at index: {flatline_index}")
screen = pygame.display.set_mode((flatline_index, HEIGHT))

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