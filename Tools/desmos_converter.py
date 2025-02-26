from latex2sympy2 import latex2sympy
import math
import pygame
from re import match as reMatch
from os import environ as osEnviron, path as osPath
from easygui import enterbox, msgbox, indexbox, integerbox, choicebox, ynbox
from tkinter import colorchooser
from json import load as jsonLoad, dump as jsonDump

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

    # Prepare the local variables with evaluated constants
    local_vars = {k: eval(v) for k, v in constants.items()}
    
    # Evaluate expressions for each value of x
    for x in range(width):
        # Add the current x value to the local_vars
        local_vars['x'] = x
        
        # Evaluate all expressions except 'y'
        for key, expression in expressions.items():
            # Process the expression with foo before evaluating
            try:
                result = eval(expression, {"__builtins__": safe_builtins}, local_vars)
            except:
                result = float('inf')
            
            # Add the result to local_vars to be used in the 'y' expressions
            local_vars[key] = result
        
        # Evaluate all y expressions and find the maximum
        max_y = float('-inf')  # Start with a very low number
        for y_expr in y_expressions:
            try:
                y = eval(y_expr, {"__builtins__": safe_builtins}, local_vars)
            except:
                try:
                    local_vars['x'] += 0.0001
                    if eval(y_expr, {"__builtins__": safe_builtins}, local_vars) < 0:
                        y = float('-inf')
                    else:
                        y = float('inf')
                except:
                    y = float('inf')
            max_y = max(max_y, y)
        
        # Append the maximum y value to the list
        results.append(max_y)

    return results

pygame.init()
MAX_WIDTH = pygame.display.Info().current_w - 200
MAX_HEIGHT = pygame.display.Info().current_h - 200
osEnviron['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((200, 200))
pygame.display.set_caption("Mathematical Graph")
clock = pygame.time.Clock()

show_checker = True

def draw_graph(data,mode,color,visibility):
    if visibility != None:
        surf = pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        for x in range(WIDTH):
            if mode == 'Fill':
                pygame.draw.line(surf, color, (x, XAXIS-data[x]), (x, HEIGHT), 1)
            elif mode == 'Line':
                try:
                    nextData = data[x+1]
                except:
                    nextData = data[x]
                pygame.draw.line(surf, color, (x, XAXIS-data[x]), (x+1, XAXIS-nextData), 1)
        if visibility == True:
            surf.set_alpha(128)
        screen.blit(surf,(0,0))

graph_datas = None
checkered_graph = None
graph = None
scale = None
def make_graph():
    global graph_datas,XAXIS,HEIGHT,screen,graph,scale,checkered_graph
    graph_datas = []
    for (exp,mode,color,visibility) in y_expressions:
        if visibility != None:
            graph_data = []
            parsed = parse_desmos(WIDTH,constants,expressions,[exp])
            for y in parsed:
                try:
                    graph_data.append(round(y))
                except:
                    graph_data.append(str(y))
            graph_datas.append([graph_data,mode,color,visibility])
    highest_val = max(0,*[0,*[max([0,*[v for v in g[0] if not v in ['inf','-inf']]]) for g in graph_datas]])
    lowest_val = min(0,*[0,*[min([0,*[v for v in g[0] if not v in ['inf','-inf']]]) for g in graph_datas]])
    furthest_val = highest_val
    if lowest_val < 0:
        furthest_val = max(highest_val,-1*lowest_val)
    if lowest_val < 0:
        if highest_val == 0:
            HEIGHT = furthest_val
            if any([[v for v in g[0] if v == 0] for g in graph_datas]):
                XAXIS = 0
                HEIGHT += 1
            else:
                XAXIS = -1
        else:
            HEIGHT = furthest_val*2+1
            XAXIS = furthest_val
    else:
        HEIGHT = furthest_val
        XAXIS = HEIGHT
        if any([[v for v in g[0] if v == 0] for g in graph_datas]):
            HEIGHT += 1
            XAXIS = HEIGHT-1
        else:
            XAXIS = HEIGHT
    if HEIGHT == 0:
        HEIGHT = 1
        XAXIS = 0
    for i,g in enumerate(graph_datas):
        for ii,v in enumerate(g[0]):
            if v == 'inf':
                graph_datas[i][0][ii] = highest_val
            elif v == '-inf':
                graph_datas[i][0][ii] = lowest_val
    osEnviron['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen.fill((255, 255, 255))
    for g in graph_datas:
        draw_graph(g[0],g[1],g[2],g[3])
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
    osEnviron['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode(new_size)
    checkered_graph = pygame.transform.scale(checkered_graph, screen.get_size())
    screen.fill((255, 255, 255))
    screen.blit(pygame.transform.scale(graph, screen.get_size()), (0, 0))
    if show_checker:
        screen.blit(checkered_graph, (0, 0))
    pygame.display.flip()


while True:
    history = {}
    if osPath.isfile('graph_history.json'):
        history = jsonLoad(open('graph_history.json','r'))
    else:
        with open('graph_history.json','w') as f:
            jsonDump(history,f)
            f.close()

    historyMode = None
    while True:
        name = None
        constants = {}
        expressions = {}
        y_expressions = []
        WIDTH = None
        HEIGHT = None
        XAXIS = None

        choices = ('Select Saved Graph','Create New Graph')
        if len(history.keys()) > 0:
            historyMode = indexbox('Would you like to open a saved graph or create a new one?','Mathematical Graph - Select Saved Graph or Create New Graph',choices)
            if historyMode == None:
                exit()
            historyMode = choices[historyMode]
        else:
            historyMode = choices[1]

        if historyMode == 'Select Saved Graph':
            if len(history.keys()) == 1:
                inp = list(history.keys())[0]
                if ynbox(f'There is only one saved graph, do you want to open \'{inp}\'?','Mathematical Graph - Select Saved Graph'):
                    (constants,expressions,y_expressions,WIDTH) = history[inp]
                    name = inp
                    break
            else:
                choices = sorted(list(history.keys()))
                inp = choicebox('Please select a saved graph.','Mathematical Graph - Select Saved Graph',choices=choices)
                if inp != None:
                    name = inp
                    (constants,expressions,y_expressions,WIDTH) = history[inp]
                    break
        else:
            break
    if historyMode != 'Select Saved Graph':
        while True:
            inp = enterbox('Please type a name below.','Mathematical Graph - Input Name',strip=True)
            if inp != None and inp != '':
                if not inp in history.keys():
                    name = inp
                    break
                else:
                    msgbox('There is already a graph with this name, please pick another name.','Mathematical Graph - Input Name')
            else:
                exit()
        while True:
            inp = enterbox('Please type a constant below.\n(You will be able to write more. When you have finished, type nothing.)','Mathematical Graph - Input Constants',strip=True)
            if inp != None and inp != '':
                match = reMatch(r'\s*([a-zA-z]+)\s?=\s?(.*)\s*',inp)
                if match:
                    if reMatch(r'^-?(\d*\.\d+|\d+\.\d*|\d+)$',match.groups()[1]):
                        constants[match.groups()[0]]=match.groups()[1]
                    else:
                        msgbox('Invalid input, please try again.','Mathematical Graph - Input Constants')
                else:
                    msgbox('Invalid input, please try again.','Mathematical Graph - Input Constants')
            else:
                break
        while True:
            inp = enterbox('Please type an expression below.\n(You will be able to write more. When you have finished, type nothing.)\n(Expressions must be defined in order.)','Mathematical Graph - Input Expressions',strip=True)
            if inp != None and inp != '':
                match = reMatch(r'\s*([a-zA-z]+)\s?=\s?(.*)\s*',inp)
                if match:
                    try:
                        expressions[match.groups()[0]]=parseLatex(match.groups()[1])
                    except:
                        msgbox('Invalid input, please try again.','Mathematical Graph - Input Expressions')
                else:
                    msgbox('Invalid input, please try again.','Mathematical Graph - Input Expressions')
            else:
                break
        while True:
            inp = enterbox('Please type a y= expression below.\n(You will be able to write more. When you have finished, type nothing.)',f'Mathematical Graph - Input y= Expressions',strip=True)
            if inp != None and inp != '':
                match = reMatch(r'\s*(?:y=\s*)?(.*)\s*',inp)
                if match: 
                    try:
                        exp = parseLatex(match.groups()[0])
                        choices = ('Line','Fill')
                        mode = None
                        while mode == None:
                            mode = indexbox('Select a draw mode below.','Mathematical Graph - Choose y= Expression Draw Mode',choices)
                        mode = choices[mode]
                        color = None
                        while color == None:
                            color = colorchooser.askcolor(title='Mathematical Graph - Choose y= Expression Draw Color',color=(0,0,0))[0]
                        y_expressions.append((exp,mode,color,False))
                    except:
                        msgbox('Invalid input, please try again.','Mathematical Graph - Input y= Expressions')
                else:
                    msgbox('Invalid input, please try again.',f'Mathematical Graph - Input y= Expressions')
            else:
                if len(y_expressions) == 0:
                    msgbox('At least one y= expression is required.',f'Mathematical Graph - Input y= Expressions')
                else:
                    break
        while WIDTH == None:
            WIDTH = integerbox('Please input the width of the graph.','Mathematical Graph - Input Graph Width',default=60,lowerbound=0,upperbound=600)
        history[name] = (constants,expressions,y_expressions,WIDTH)
        with open('graph_history.json','w') as f:
            jsonDump(history,f)
            f.close()

    make_graph()
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                # exit
                if event.key == pygame.K_ESCAPE:
                    running = False
                # output
                elif event.key in [pygame.K_o]:
                    pygame.image.save(graph,'output_graph.png')
                    msgbox('Saved graph as \'output_graph.png\'','Mathematical Graph - Output Graph')
                # save
                elif event.key in [pygame.K_s]:
                    if ynbox('Do you want to save this graph?','Save this graph?'):
                        history[name] = (constants,expressions,y_expressions,WIDTH)
                        with open('graph_history.json','w') as f:
                            jsonDump(history,f)
                            f.close()
                # del from history
                elif event.key in [pygame.K_DELETE]:
                    if name in history.keys():
                        if ynbox('Are you sure you want to remove this graph from saved graphs?','Are you sure?'):
                            history.pop(name)
                            with open('graph_history.json','w') as f:
                                jsonDump(history,f)
                                f.close()
                # toggle checker
                elif event.key in [pygame.K_c]:
                    show_checker = not show_checker
                elif event.key in [pygame.K_RETURN]:
                    while True:
                        choices = ['Edit Name','Edit Width','Edit Line' + ('s' if len(y_expressions) > 1 else ''),'Reset Graph','Back']
                        if len(constants) > 0:
                            choices.insert(2,'Edit Constant' + ('s' if len(constants) > 1 else ''))
                        editing = indexbox('What would you like to edit?','Mathematical Graph - Edit Graph',choices)
                        if editing != None:
                            editing = choices[editing]
                            if editing != 'Back':
                                if editing == 'Reset Graph':
                                    if osPath.isfile('graph_history.json'):
                                        history = jsonLoad(open('graph_history.json','r'))
                                        (constants,expressions,y_expressions,WIDTH) = history[name]
                                        make_graph()
                                    else:
                                        with open('graph_history.json','w') as f:
                                            jsonDump(history,f)
                                            f.close()
                                        msgbox('\'graph_history.json\' File has been removed at some point. Attempting to recreate.\nAny edits made to this graph have been saved to saved graphs.')
                                elif editing == 'Edit Name':
                                    while True:
                                        inp = enterbox('Please type a name below.','Mathematical Graph - Input Name',strip=True,default=name)
                                        if inp in [name,None]:
                                            break
                                        if inp != None and inp != '':
                                            if not inp in history.keys():
                                                history[inp] = history.pop(name)
                                                name = inp
                                                break
                                            else:
                                                msgbox('There is already a graph with this name, please pick another name.','Mathematical Graph - Input Name')
                                elif editing == 'Edit Width':
                                    inp = integerbox('Please input the new width of the graph.','Mathematical Graph - Edit Graph Width',default=WIDTH,lowerbound=0,upperbound=600)
                                    if inp != None:
                                        WIDTH = inp
                                        make_graph()
                                elif editing.startswith('Edit Constant'):
                                    editing = True
                                    while editing:
                                        edit_constant = None
                                        if len(constants) > 1:
                                            choices = sorted(list(constants.keys()))
                                            for i,choice in enumerate(choices):
                                                choices[i] = choice+': '+constants[choice]
                                            edit_constant = choicebox('Please select a constant to edit.','Mathematical Graph - Edit Constants',choices=choices)
                                        else:
                                            edit_constant = list(constants.keys())[0]+': '+list(constants.values())[0]
                                        if edit_constant == None:
                                            editing = False
                                        else:
                                            edit_constant = edit_constant.split(':')[0]
                                            inp = 'unset'
                                            while inp == 'unset':
                                                inp = enterbox(f'Please input the new value of {edit_constant}.\n(Old value: {constants[edit_constant]})',f'Mathematical Graph - Edit Constant {edit_constant}',default=constants[edit_constant],strip=True)
                                                try:
                                                    if inp != None:
                                                        inp = float(inp)
                                                except:
                                                    msgbox('Invalid input, please try again.',f'Mathematical Graph - Edit Constant {edit_constant}')
                                            if inp != None:
                                                constants[edit_constant] = str(inp)
                                                make_graph()
                                            if len(constants) == 1:
                                                editing = False
                                elif editing.startswith('Edit Line'):
                                    editing = True
                                    while editing:
                                        edit_line = None
                                        if len(y_expressions) > 1:
                                            choices = sorted([value[0] for value in y_expressions])
                                            for i,choice in enumerate(choices):
                                                choices[i] = 'y='+choice
                                            edit_line = choicebox('Please select a line to edit.','Mathematical Graph - Edit Lines',choices=choices)
                                        else:
                                            edit_line = 'y='+y_expressions[0][0]
                                        
                                        if edit_line == None:
                                            editing = False
                                        else:
                                            edit_line = y_expressions.index(next((x for x in y_expressions if x[0] == edit_line.removeprefix('y=')), None))
                                            editing_line = True
                                            while editing_line:
                                                choices = ['Edit Color','Edit Draw Mode','Back']
                                                if len(y_expressions) > 1:
                                                    choices.insert(0,'Cycle Visibility')
                                                editing_attribute = indexbox('What would you like to edit?',f'Mathematical Graph - Edit Line \'y={y_expressions[edit_line][0]}\'',choices)
                                                if editing_attribute != None:
                                                    editing_attribute = choices[editing_attribute]
                                                    if editing_attribute != 'Back':
                                                        if editing_attribute == 'Edit Color':
                                                            color = colorchooser.askcolor(title=f'Mathematical Graph - Edit Line \'y={y_expressions[edit_line][0]}\' Color')[0]
                                                            if color != None:
                                                                y_expressions[edit_line][2] = color
                                                                make_graph()
                                                        elif editing_attribute == 'Edit Draw Mode':
                                                            choices = ('Line','Fill')
                                                            mode = None
                                                            while mode == None:
                                                                mode = indexbox('Select a draw mode below.',f'Mathematical Graph - Edit Line \'y={y_expressions[edit_line][0]}\' Draw Mode',choices)
                                                            y_expressions[edit_line][1] = choices[mode]
                                                            make_graph()
                                                        elif editing_attribute == 'Cycle Visibility':
                                                            if y_expressions[edit_line][3] == None:
                                                                y_expressions[edit_line][3] = False
                                                            elif y_expressions[edit_line][3] == False:
                                                                y_expressions[edit_line][3] = True
                                                            elif y_expressions[edit_line][3] == True:
                                                                y_expressions[edit_line][3] = None
                                                            make_graph()
                                                    else:
                                                        break
                                                else:
                                                    if len(y_expressions) == 1:
                                                        editing = False
                                                    break
                                            if len(y_expressions) == 1:
                                                editing = False
                                            break
                                elif editing == 'Back':
                                    break
                            else:
                                break
                        else:
                            break
        screen.fill((255, 255, 255))
        screen.blit(pygame.transform.scale(graph, screen.get_size()), (0, 0))
        if show_checker:
            screen.blit(checkered_graph, (0, 0))
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        if mouse_pos.x > 0 and mouse_pos.y > 0 and mouse_pos.x < screen.get_width() and mouse_pos.y < screen.get_height():
            mouse_pos = round((mouse_pos/scale)-(0.5,0.5))
            pygame.display.set_caption(f'Mathematical Graph - (x:{int(mouse_pos.x)},y:{int(XAXIS-mouse_pos.y)})')
        pygame.display.flip()


#Todo:
"""
add res option (e.g. res=1 by default, if res = 0.1 then each pixel is 0.1 across on the grid rather than 1)
cool idea, no clue how to do: Display thumbnails of each graph during saved graph selection
dont allow x,y, or e as vafriable names
"""