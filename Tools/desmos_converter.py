from latex2sympy2 import latex2sympy
import math

def parseLatex(v):
    out = str(latex2sympy(v))
    out = out.replace('Min','min').replace('Max','max')
    return out

# Functions and constants allowed in eval()
safe_builtins = {
    "max": max,
    "min": min,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "round": round,
    "pi": math.pi,
    "exp": math.exp,
    "log": math.log,
}

# Define the constants and expressions
def parse_desmos(width,constants,expressions,y_expressions):
    # Initialize the list to store the results
    results = []

    # Evaluate expressions for each value of x
    for x in range(width):
        # Prepare the local variables with evaluated constants
        local_vars = {k: eval(v) for k, v in constants.items()}
        
        # Add the current x value to the local_vars
        local_vars['x'] = x
        
        # Evaluate all expressions except 'y'
        for key, expression in expressions.items():
            # Process the expression with foo before evaluating
            processed_expr = parseLatex(expression)
            result = eval(processed_expr, {"__builtins__": safe_builtins}, local_vars)
            
            # Add the result to local_vars to be used in the 'y' expressions
            local_vars[key] = result
        
        # Evaluate all y expressions and find the maximum
        max_y = float('-inf')  # Start with a very low number
        for y_expr in y_expressions:
            processed_y = parseLatex(y_expr)
            y = eval(processed_y, {"__builtins__": safe_builtins}, local_vars)
            max_y = max(max_y, y)
        
        # Append the maximum y value to the list
        results.append(max_y)

    return results

import pygame,sys
from threading import Event as threading_Event, Thread as threading_Thread
from time import sleep
from re import match as reMatch
from os import environ as osEnviron, path as osPath
from easygui import enterbox, msgbox, indexbox, integerbox, choicebox, ccbox
from tkinter import colorchooser
from json import load as jsonLoad, dump as jsonDump

stop_spinner_event = threading_Event()
stop_spinner_event_error = threading_Event()
def spinner_animation(anim,msg,complete_msg,fail_msg):
    while (not stop_spinner_event.is_set()) and (not stop_spinner_event_error.is_set()):
        for frame in anim:
            sys.stdout.write(f'\r{frame} {msg}')
            sys.stdout.flush()
            sleep(0.1)
    if not stop_spinner_event_error.is_set():
        sys.stdout.write(f'\r{complete_msg}'+(' '*((len(anim[0])+len(msg)+1)-len(complete_msg)))+'\n')
        sys.stdout.flush()
    else:
        sys.stdout.write(f'\r{fail_msg}'+(' '*((len(anim[0])+len(msg)+1)-len(fail_msg)))+'\n')
        sys.stdout.flush()

loading_anim = [
"[        ]",
"[=       ]",
"[===     ]",
"[====    ]",
"[=====   ]",
"[======  ]",
"[======= ]",
"[========]",
"[ =======]",
"[  ======]",
"[   =====]",
"[    ====]",
"[     ===]",
"[      ==]",
"[       =]",
"[        ]",
"[        ]"
]

history = {}
if osPath.isfile('graph_history.json'):
    history = jsonLoad(open('graph_history.json','r'))
else:
    with open('graph_history.json','w') as f:
        jsonDump(history,f)
        f.close()

name = None
constants = {}
expressions = {}
y_expressions = []
y_expressions_mode = None
y_expressions_max_mode = None
y_expressions_max_color = None
WIDTH = None
HEIGHT = None
XAXIS = None

historyMode = None
choices = ('Select Previous Graph','Create New Graph')
if len(history.keys()) > 0:
    while historyMode == None:
        historyMode = indexbox('Would you like to open a previous graph or create a new one?','Mathematical Graph - Select Previous Graph or Create New Graph',choices)
    historyMode = choices[historyMode]
else:
    historyMode = choices[1]

if historyMode == 'Select Previous Graph':
    while True:
        if len(history.keys()) == 1:
            inp = list(history.keys())[0]
            (constants,expressions,y_expressions,y_expressions_mode,y_expressions_max_mode,y_expressions_max_color,WIDTH) = history[inp]
            name = inp
            msgbox(f'There is only one previous graph, selecting \'{inp}\'.','Mathematical Graph - Select Previous Graph')
            break
        else:
            choices = sorted(list(history.keys()))
            inp = choicebox('Please select a previous graph.','Mathematical Graph - Select Previous Graph',choices=choices)
            if inp in history.keys():
                name = inp
                (constants,expressions,y_expressions,y_expressions_mode,y_expressions_max_mode,y_expressions_max_color,WIDTH) = history[inp]
                break
else:
    while True:
        inp = enterbox('Please type a name below.','Mathematical Graph - Input Name',strip=True)
        if inp != None and inp != '':
            if not inp in history.keys():
                name = inp
                break
            else:
                msgbox('There is already a graph with this name, please pick another name.','Mathematical Graph - Input Name')
    while True:
        inp = enterbox('Please type a constant below.\n(You will be able to write more. When you have finished, type nothing.)','Mathematical Graph - Input Constants',strip=True)
        if inp != None and inp != '':
            match = reMatch(r'\s*([a-zA-z]+)\s?=\s?(.*)\s*',inp)
            if match:
                if reMatch(r'^-?(\d*\.\d+|\d+\.\d*|\d+)$',match.groups()[1]):
                    constants[match.groups()[0]]=match.groups()[1]
                else:
                    msgbox('Invalid input, please try again.','Mathematical Graph - Input Expressions')
            else:
                msgbox('Invalid input, please try again.','Mathematical Graph - Input Expressions')
        else:
            break
    while True:
        inp = enterbox('Please type an expression below.\n(You will be able to write more. When you have finished, type nothing.)\n(Expressions must be defined in order.)','Mathematical Graph - Input Expressions',strip=True)
        if inp != None and inp != '':
            match = reMatch(r'\s*([a-zA-z]+)\s?=\s?(.*)\s*',inp)
            if match:
                expressions[match.groups()[0]]=match.groups()[1]
            else:
                msgbox('Invalid input, please try again.','Mathematical Graph - Input Expressions')
        else:
            break
    choices = ('Max','Layered')
    while y_expressions_mode == None:
        y_expressions_mode = indexbox('Select a y= expressions mode below.\n(Max will draw one graph, where the y value will be the max y from all y= expressions. Layered will draw each y= expression as a seperate graph, and layer them on top of each other, with the first to be defined at the back, and the last defined at the front.)','Mathematical Graph - Choose y= Expressions mode',choices)
    y_expressions_mode = choices[y_expressions_mode]
    if y_expressions_mode == 'Max':
        choices = ('Line','Fill')
        y_expressions_max_mode = None
        while y_expressions_max_mode == None:
            y_expressions_max_mode = indexbox('Select a draw mode below.','Mathematical Graph - Choose y= Expression Draw Mode',choices)
        y_expressions_max_mode = choices[y_expressions_max_mode]
        y_expressions_max_color = None
        while y_expressions_max_color == None:
            y_expressions_max_color = colorchooser.askcolor(title='Mathematical Graph - Choose y= Expression Draw Color')[0]
    while True:
        inp = enterbox('Please type a y= expression below.\n(You will be able to write more. When you have finished, type nothing.)',f'Mathematical Graph - Input y= Expressions ({y_expressions_mode} Mode)',strip=True)
        if inp != None and inp != '':
            match = reMatch(r'\s*(?:y=\s*)?(.*)\s*',inp)
            if match:
                if y_expressions_mode == 'Max':
                    y_expressions.append(match.groups()[0])
                else:
                    choices = ('Line','Fill')
                    mode = None
                    while mode == None:
                        mode = indexbox('Select a draw mode below.','Mathematical Graph - Choose y= Expression Draw Mode',choices)
                    mode = choices[mode]
                    color = None
                    while color == None:
                        color = colorchooser.askcolor(title='Mathematical Graph - Choose y= Expression Draw Color')[0]
                    y_expressions.append((match.groups()[0],mode,color))
            else:
                msgbox('Invalid input, please try again.',f'Mathematical Graph - Input y= Expressions ({y_expressions_mode} Mode)')
        else:
            break
    while WIDTH == None:
        WIDTH = integerbox('Please input the width of the graph.','Mathematical Graph - Input Graph Width',default=60,lowerbound=0,upperbound=600)
    history[name] = (constants,expressions,y_expressions,y_expressions_mode,y_expressions_max_mode,y_expressions_max_color,WIDTH)
    with open('graph_history.json','w') as f:
        jsonDump(history,f)
        f.close()

spinner_thread = threading_Thread(target=spinner_animation,args=[loading_anim,'Parsing inputs...','Parsing complete!','Parsing failed.'])
spinner_thread.start()

graph_datas = None
graph_data = None
highest_val = None
lowest_val = None
try:
    if y_expressions_mode == 'Max':
        graph_data = []
        parsed = parse_desmos(WIDTH,constants,expressions,y_expressions)
        for y in parsed:
            graph_data.append(round(y))
        highest_val = max(0,graph_data)
        lowest_val = min(0,graph_data)
        if lowest_val < 0:
            HEIGHT = highest_val - lowest_val
            XAXIS = HEIGHT+lowest_val
        else:
            HEIGHT = highest_val
            XAXIS = HEIGHT
    elif y_expressions_mode == 'Layered':
        graph_datas = []
        for (exp,mode,color) in y_expressions:
            graph_data = []
            parsed = parse_desmos(WIDTH,constants,expressions,[exp])
            for y in parsed:
                graph_data.append(round(y))
            graph_datas.append((graph_data,mode,color))
        highest_val = max(0, *[max(g[0]) for g in graph_datas])
        lowest_val = min(0, *[min(g[0]) for g in graph_datas])
        if lowest_val < 0:
            HEIGHT = highest_val*2+1
            XAXIS = highest_val
        else:
            HEIGHT = highest_val
            XAXIS = HEIGHT
    stop_spinner_event.set()
    spinner_thread.join()
except Exception as e:
    stop_spinner_event_error.set()
    spinner_thread.join()
    raise Exception

pygame.init()
MAX_WIDTH = pygame.display.Info().current_w - 200
MAX_HEIGHT = pygame.display.Info().current_h - 200
osEnviron['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mathematical Graph")
clock = pygame.time.Clock()

def draw_graph(data,mode,color):
    # Draw the graph
    for x in range(WIDTH):
        if mode == 'Fill':
            pygame.draw.line(screen, color, (x, XAXIS-data[x]), (x, HEIGHT), 1)
        elif mode == 'Line':
            try:
                nextData = data[x+1]
            except:
                nextData = data[x]
            pygame.draw.line(screen, color, (x, XAXIS-data[x]), (x+1, XAXIS-nextData), 1)
    pygame.display.flip()
screen.fill((255, 255, 255))
if y_expressions_mode == 'Max':
    draw_graph(graph_data,y_expressions_max_mode,y_expressions_max_color)
elif y_expressions_mode == 'Layered':
    for g in graph_datas:
        draw_graph(g[0],g[1],g[2])
graph = screen.copy()
checkered_graph = pygame.Surface(graph.get_size(),pygame.SRCALPHA)
i = 0
ii = 0
for y in range(checkered_graph.get_height()):
    for x in range(checkered_graph.get_width()):
        color = None
        bc = (64,64,64,32)
        wc = (192,192,192,32)
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
pygame.draw.line(checkered_graph,(0,0,0,32),(0,XAXIS),(WIDTH,XAXIS))

scale_x = MAX_WIDTH / WIDTH
scale_y = MAX_HEIGHT / HEIGHT
scale = max(min(scale_x, scale_y),1)
new_size = (int(WIDTH * scale), int(HEIGHT * scale))
screen = pygame.display.set_mode(new_size)
screen.blit(pygame.transform.scale(graph, new_size), (0, 0))
screen.blit(pygame.transform.scale(checkered_graph, new_size), (0, 0))

while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_o]:
                pygame.image.save(graph,'output_graph.png')
            if event.key in [pygame.K_s]:
                if ccbox('Do you want to save this graph?','Save this graph?'):
                    history[name] = (constants,expressions,y_expressions,y_expressions_mode,y_expressions_max_mode,y_expressions_max_color,WIDTH)
                    with open('graph_history.json','w') as f:
                        jsonDump(history,f)
                        f.close()
            if event.key in [pygame.K_DELETE]:
                if ccbox('Are you sure you want to remove this graph from saved graphs?','Are you sure?'):
                    history.pop(name)
                    with open('graph_history.json','w') as f:
                        jsonDump(history,f)
                        f.close()
            if event.key == pygame.K_ESCAPE:
                exit()
    pygame.display.flip()


#Todo:
"""
Add option to display only certain lines during display mode,
Add option to change colors during display mode,
Display thumbnails of each graph during previous graph selection,

"""