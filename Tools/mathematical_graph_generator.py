import pygame
from easygui import enterbox, choicebox, boolbox
from os import environ as osEnviron
from os import path as osPath
from json import load as jsonLoad
from json import dump as jsonDump

history = []
if osPath.isfile('graph_history.json'):
    history = jsonLoad(open('graph_history.json','r'))
else:
    with open('graph_history.json','w') as f:
        jsonDump(history,f)
        f.close()

name = None
WIDTH = None
EQUATIONS = None

msg = ''
if len(history) > 0:
    msg = 'Or type \'history\' or \'h\' to choose from previous graphs.'
inp = enterbox(msg,'Please input the width below.',strip=True)
if inp == None:
    exit()
if len(history) > 1 and inp.lower() in ['history','h']:
    choice = choicebox('','Please select a previous graph.',[f'{item['name']}: {item['graph_size']}, {str(item['EQUATIONS']).replace('\'','')}' for item in history])
    if choice == None:
        exit()
    else:
        choice = str(choice.split(':')[0]).removeprefix('Name: ')
        for item in history:
            if item['name'] == choice:
                name = choice
                WIDTH = item['WIDTH']
                EQUATIONS = item['EQUATIONS']
                break
elif len(history) == 1 and inp.lower() in ['history','h']:
    choice = choicebox('','Please select a previous graph.',[*[f'{item['name']}: {item['graph_size']}, {str(item['EQUATIONS']).replace('\'','')}' for item in history],'Cancel'])
    if choice == None or choice == 'Cancel':
        exit()
    else:
        choice = str(choice.split(':')[0]).removeprefix('Name: ')
        for item in history:
            if item['name'] == choice:
                name = choice
                WIDTH = item['WIDTH']
                EQUATIONS = item['EQUATIONS']
                break
else:
    WIDTH = int(inp)
    e = enterbox('Seperate by comma and space, e.g: \'y=1x, y=2x\'','Please input the equations below.',strip=True)
    if e == None:
        exit()
    EQUATIONS = e.split(', ')
# Initialize Pygame
pygame.init()
HEIGHT = 0
MAX_WIDTH = pygame.display.Info().current_w - 200
MAX_HEIGHT = pygame.display.Info().current_h - 200
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
        if equation.split('=')[0] == 'iy':
            equation = equation.replace('x', str(WIDTH-x))
        elif equation.split('=')[0] == 'y':
            equation = equation.replace('x', str(x))
        equation = equation.replace('{', '(').replace('}', ')').replace('\\cdot','*')
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

def draw_graph():
    screen.fill((255, 255, 255))  # Clear screen with white
    # Draw the graph
    for x in range(WIDTH):
        pygame.draw.line(screen, (0, 0, 0), (x, HEIGHT-graph_data[x]), (x, HEIGHT), 1)

    pygame.display.flip()

draw_graph()
graph = screen.copy()
checkered_graph = pygame.Surface(graph.get_size(),pygame.SRCALPHA)
i = 0
ii = 0
for y in range(checkered_graph.get_height()):
    for x in range(checkered_graph.get_width()):
        color = None
        bc = (64,64,64,64)
        wc = (192,192,192,64)
        if i == 0:
            if ii == 0:
                color = wc
                ii = 1
            else:
                color = bc
                ii = 0
        else:
            if ii == 0:
                color = bc
                ii = 1
            else:
                color = wc
                ii = 0
        pygame.draw.line(checkered_graph,color,(x,y),(x,y),1)
    if i == 0:
        i = 1
    else:
        i = 0

scale_x = MAX_WIDTH / WIDTH
scale_y = MAX_HEIGHT / HEIGHT
scale = min(scale_x, scale_y)
new_size = (int(WIDTH * scale), int(HEIGHT * scale))
screen = pygame.display.set_mode(new_size)
screen.blit(pygame.transform.scale(graph, new_size), (0, 0))
screen.blit(pygame.transform.scale(checkered_graph, new_size), (0, 0))

graph_size = f'{WIDTH}x{max(graph_data)}'
print(f'graph size: {graph_size}')

# Main loop
running = True
save = False
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if inp.lower() in ['history','h'] and event.key == pygame.K_d:
                if boolbox('',f'Are you sure you want to delete \'{name}\' from history?'):
                    for i,item in enumerate(history):
                        if item['name'] == name:
                            history.pop(i)
                            running = False
                            break
            else:
                if event.key == pygame.K_s:
                    save = True
                    running = False
                if event.key == pygame.K_ESCAPE:
                    running = False
    pygame.display.flip()
if not inp.lower() in ['history','h']:
    name = enterbox('','Please input the curve name below.',strip=True)
    if name == None:
        exit()
    for char in '<>:"/\\|?*':
        name = name.replace(char,'')
if save:
    e = False
    if inp.lower() in ['history','h']:
        e = boolbox(f'Current name: \'{name}\'','Do you want to save this curve under a different name?')
        if e == True:
            name = enterbox('Or type \'output_graph\' to save under the main directory.','Please input the curve name below.',strip=True)
            if name == None:
                e = None
            elif name == 'output_graph':
                pygame.image.save(graph,name+'.png')
                exit()
            else:
                for char in '<>:"/\\|?*':
                    name = name.replace(char,'')
    if e != None:
        pygame.image.save(graph,osPath.dirname(osPath.dirname(__file__))+'\\images\\curves\\'+name+'.png')
if not inp.lower() in ['history','h']:
    i = 0
    name_edited = True
    while name_edited:
        name_edited = False
        for item in history:
            if item['name'] == name:
                name = name+' ('+str(i)+')'
                name_edited = True
                i += 1
    history.append({'name':name,'WIDTH':WIDTH,'EQUATIONS':EQUATIONS,'graph_size':graph_size})
with open('graph_history.json','w') as f:
    jsonDump(history,f)
    f.close()