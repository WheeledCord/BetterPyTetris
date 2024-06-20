# ~ Imports ~ #
import pygame
from random import randint
from os import environ as osEnviron
from os import path as osPath
from copy import deepcopy
from json import load as jsonLoad
from json import dump as jsonDump

# Inits
pygame.init()
clock = pygame.time.Clock()

# Create window
(display_width,display_height) = (256,224)

# Window scale
def setScale(scale: int):
    osEnviron['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_mode((scale*display_width, scale*display_height))

display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('PyTetris')
setScale(3)

# Load assets
screen = pygame.image.load('images/gui/bg.png').convert()
paused_overlay = pygame.image.load('images/gui/paused.png').convert_alpha()
death_overlay = pygame.image.load('images/gui/gameOver.png').convert_alpha()
pygame.mixer.music.load('sounds/music.mp3')

sounds = {
    'move':pygame.mixer.Sound('sounds/move.mp3'),
    'soft_drop':pygame.mixer.Sound('sounds/soft_drop.mp3'),
    'rotate':pygame.mixer.Sound('sounds/rotate.mp3'),
    'place':pygame.mixer.Sound('sounds/place.mp3'),
    'line':pygame.mixer.Sound('sounds/line.mp3'),
    'death':pygame.mixer.Sound('sounds/death.mp3'),
    'fall':pygame.mixer.Sound('sounds/fall.mp3')
}
pieces = [
    pygame.image.load('images/pieces/0.png').convert_alpha(),
    pygame.image.load('images/pieces/1.png').convert_alpha(),
    pygame.image.load('images/pieces/2.png').convert_alpha(),
    pygame.image.load('images/pieces/ghost.png').convert_alpha()
]


# - Load controls - #
controls = {
    'left rotate': [pygame.K_z],
    'right rotate': [pygame.K_UP],
    'move left': [pygame.K_LEFT],
    'move right': [pygame.K_RIGHT],
    'soft down': [pygame.K_DOWN],
    'hard down': [pygame.K_SPACE],
    'hold': [pygame.K_c],
    'pause': [pygame.K_RETURN],
    'quit': [pygame.K_ESCAPE],
    'toggle ghost': [pygame.K_g],
    'toggle colour': [pygame.K_h],
    'scale 1': [pygame.K_1],
    'scale 2': [pygame.K_2],
    'scale 3': [pygame.K_3],
    'scale 4': [pygame.K_4],
    'volume up': [61],
    'volume down': [45],
    'mute': [pygame.K_0]
}

if osPath.isfile('controls.json'):
    jsonControls = jsonLoad(open('controls.json','r'))
    for id in controls.keys():
        if id in jsonControls.keys():
            keys = jsonControls[id]
            temp = []
            for key in keys:
                try:
                    temp.append(pygame.key.key_code(key))
                except ValueError as e:
                    raise ValueError(f"Key string not recognized by Pygame: '{key}'") from e
                controls[id] = temp
else:
    with open('controls.json','w') as file:
        convertedControls = deepcopy(controls)
        for k,v in controls.items():
            temp = []
            for key in v:
                temp.append(pygame.key.name(key))
            convertedControls[k] = temp
        jsonDump(convertedControls,file)
# - Load controls - #
# Define variables

frameRate = 60
show_ghost = True

last_fall = 0
last_input = 0
last_soft_input = 0
holding_input = False
holding_down = False
left_collided = False
right_collided = False
running = True
closed = False
paused = False
coloured = True
volume = 1.0
AREpaused = False
AREpauseLength = 0
linesCleared = 0

score = 0
lines = 0
lvl = 0
speed = 48
stats = {
    'I':0,
    'J':0,
    'L':0,
    'O':0,
    'S':0,
    'T':0,
    'Z':0
}




# Map storage
tileMap = []
def clearMap():
    global tileMap
    tileMap = []
    for row in range(20):
        column = []
        for x in range(10):
            column.append('')
        tileMap.append(column)
clearMap()
    
def setTileonMap(x,y, value):
    try:
        tileMap[int(y)][int(x)] = value
        return value
    except IndexError:
        return (x,y)

def getTileonMap(x,y):
    try:
        return tileMap[y][x]
    except IndexError:
        return (x,y)
    
def rotateTable(table):
    return [[*r][::-1] for r in zip(*table)]



# Rendering
stamps = []
def drawStamps():
    for pos, sprite in stamps:
        screen.blit(sprite.image, pos)

TotalAREpauseLength = 60
AREFlashes = 3
flash_stamps = []
def flashStamps():
    for pos, sprite in flash_stamps:
        if AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes)) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*2 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*3) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*4 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*5):
            screen.blit(sprite.image, pos)
        else:
            pygame.draw.rect(screen, 'white', (pos[0], pos[1], 7, 7))

# Draw Text
def writeNums(pos: tuple, num: int, length: int):
    full_num = str(num)
    full_num = (length-len(full_num))*'0'+full_num
    i = 0
    for c in full_num:
        screen.blit(pygame.image.load(f'images/text/{c}.png').convert_alpha(), (pos[0]+8*i,pos[1]))
        i += 1




# Shapes and pieces
all_shapes = {}
class Shapes:
    class shape:
        # The individual blocks that make up a shape
        class __piece:
            def __init__(self,image,id,localx,localy,pieceid) -> None:
                self.sprite = pygame.sprite.Sprite()
                self.sprite.image = pygame.image.load(f'images/pieces/{image}.png').convert_alpha()
                self.sprite.rect = self.sprite.image.get_rect()
                self.pieceid = pieceid
                self.id = id
                self.localx = localx
                self.localy = localy
                self.center = False
                self.pos = pygame.Vector2(localx,localy)
            
            def rotate(self,pivotPos: pygame.Vector2,angle):
                return pivotPos + (self.pos - pivotPos).rotate(angle)
                
        def __init__(self,id: str,piece_sprite: str,hitbox: str) -> None:
            self.id = id
            if id[0] != 'G':
                self.gui_sprite = pygame.image.load(f'images/shapes/{id}.png').convert_alpha()

            self.hitbox = hitbox
            self.base_hitbox = hitbox
            self.piece_sprite = piece_sprite
            self.rotation = 0
            self.makePieces()
            if id[0] != 'G':
                all_shapes[id] = self
            self.setPos(4,0)

        def setPos(self,x:int,y:int):
            self.x = x
            self.y = y
            for piece in self.pieces:
                piece.pos = pygame.Vector2(x+piece.localx,y+piece.localy)

        def makePieces(self):
            self.piecesGroup = pygame.sprite.Group()
            self.pieces = []
            x = 0
            y = 0
            for c in self.hitbox:
                if c.isdigit():
                    piece = self.__piece(self.piece_sprite,c,x,y,self.id)
                    self.pieces.append(piece)
                    self.piecesGroup.add(piece.sprite)
                    x += 1
                elif c == ' ':
                    x += 1
                elif c == '-':
                    y += 1
                    x = 0
                elif c == 'x':
                    self.pieces[-1].center = True
            
        # def rotate(self,dir):
        #     self.rotation = self.rotation + dir
        #     if self.rotation < 0:
        #         self.rotation = 3
        #     elif self.rotation > 3:
        #         self.rotation = 0
        #     new_hitbox = []
        #     for line in self.base_hitbox.split('-'):
        #         new_hitbox.append([])
        #         for c in line:
        #             if c.isdigit() or c == ' ':
        #                 new_hitbox[-1].append(c)
        #     for i in range(self.rotation):
        #         new_hitbox = rotateTable(new_hitbox)
        #     str_hitbox = ''
        #     for line in new_hitbox:
        #         for c in line:
        #             str_hitbox += c
        #         str_hitbox += '-'
        #     str_hitbox = str_hitbox.removesuffix('-')
        #     self.hitbox = str_hitbox
        #     self.makePieces()
        
        def rotate(self,angle):
            if angle*90 in [90,-90,180]:
                pivotPos = None
                for piece in self.pieces:
                    if piece.center:
                        pivotPos = piece.pos
                        break
                if pivotPos:
                    newPositions = [piece.rotate(pivotPos,angle*90) for piece in self.pieces]

                    # collison checking
                    for pos in newPositions:
                        if pos.x < 0 or pos.x >= 10:
                            return # wall kick code here
                        if tileMap[int(pos.y)][int(pos.x)]:
                            return
                        if pos.y < 0 or pos.y >= 20:
                            return
                        
                    for i, piece in enumerate(self.pieces):
                        piece.pos = newPositions[i]
                        piece.localx = int(pygame.Vector2(self.x,0).distance_to(pygame.Vector2(piece.pos.x,0)))
                        piece.localy = int(pygame.Vector2(0,self.y).distance_to(pygame.Vector2(0,piece.pos.y)))
                        if self.x < piece.pos.x: piece.localx = -piece.localx
                        if self.y < piece.pos.y: piece.localy = -piece.localy
                    sounds['rotate'].play()
            else:
                raise ValueError()
            
        def draw(self):
            for piece in self.pieces:
                piece.sprite.rect.x = 96+(8*(piece.pos.x))
                piece.sprite.rect.y = 40+(8*(piece.pos.y))
            self.piecesGroup.draw(screen)
            
        def stamp(self):
            for piece in self.pieces:
                # x = 96+(8*(piece.pos.x))
                # y = 40+(8*(piece.pos.y))
                # s = piece.sprite
                setTileonMap(piece.pos.x,piece.pos.y,self.id)
            self.makePieces()
            
    I = shape('I','1','01x23')
    J = shape('J','0','01x2-  3')
    L = shape('L','2','01x2-3  ')
    O = shape('O','1','01-23')
    S = shape('S','0',' 01-23x ')
    T = shape('T','1','012- 3x ')
    Z = shape('Z','2','01 - 2x3')
    def __makeBag():
        out = []
        for shape in list(all_shapes.values()):
            out.insert(randint(0,len(out)),shape)
        return out
    bag = __makeBag()
    def fromBag() -> shape:
        if len(Shapes.bag) == 0:
            Shapes.bag = Shapes.__makeBag()
        return Shapes.bag.pop(0)



def getInp(control_scheme):
    keys = pygame.key.get_pressed()
    for key in controls[control_scheme]:
        if keys[key]:
            return True
    return False


# Clearing Lines
def clearLine(y: int):
    global linesCleared,AREpaused,AREpauseLength,stamps,lines,lvl,speed
    sounds['line'].play()
    linesCleared += 1
    AREpaused = True
    AREpauseLength = TotalAREpauseLength
    tileMap.pop(y)
    empty = []
    for i in range(10):
        empty.append('')
    tileMap.insert(0,empty)
    temp = []
    for pos,piece in stamps:
        if piece.pos.y != y:
            temp.append((pos,piece))
        else:
            flash_stamps.append((pos,piece))
    stamps = temp
    lines += 1
    if lines % 10 == 0:
        lvl += 1
        if lvl < 9:
            speed -= 5
        elif lvl == 9:
            speed -= 2
        elif lvl in [10,13,16,19,29]:
            speed -= 1
        if lvl > 99:
            lvl = 99
            speed = 48
    if lines > 999:
        lines = 999

def getCollision():
    global ghostShape,ghostCollided,collided,left_collided,right_collided

    collided = False
    ghostCollided = False
    left_collided = False
    right_collided = False

    ghostShape.setPos(currentShape.x,currentShape.y-1)
    ghostShape.rotation = currentShape.rotation-1
    ghostShape.rotate(1)

    for piece in ghostShape.pieces:
        if piece.pos.y == 19 or tileMap[int(piece.pos.y+1)][int(piece.pos.x)] != ' ':
            ghostCollided = True
            break
    
    for piece in currentShape.pieces:
        if piece.pos.y == 19 or tileMap[int(piece.pos.y+1)][int(piece.pos.x)] != ' ':
            collided = True
        if piece.pos.x >= 9:
            right_collided = True
        if piece.pos.x <= 0:
            left_collided = True
        if collided and right_collided and left_collided:
            break

def hsv_to_rgb( h:int, s:int, v:int, a:int=255 ) -> tuple:
    out = pygame.Color(0)
    out.hsva = (h,s,v,a)
    return (out.r, out.g, out.b, out.a)

def overflowNum(value, maxValue):
    # Calculate the range size
    range_size = maxValue + 1
    
    # Wrap the value around within the range
    if value < 0:
        value = maxValue - ((0 - value - 1) % range_size) - 1
    elif value > maxValue:
        value = 1 + ((value - maxValue - 1) % range_size)
    
    return value

replay = True



# Main game loop
while replay:
    clearMap()
    stamps = []
    flash_stamps = []
    last_fall = 0
    last_input = 0
    left_collided = False
    right_collided = False
    last_soft_input = 0
    holding_input = False
    holding_down = False
    running = True
    closed = False
    paused = False
    AREpaused = False
    AREpauseLength = 0
    linesCleared = 0

    score = 0
    lines = 0
    lvl = 0
    speed = 48
    stats = {'I':0,'J':0,'L':0,'O':0,'S':0,'T':0,'Z':0}

    currentShape = Shapes.fromBag()
    currentShape.setPos(4,0)
    currentShape.rotation = 1
    currentShape.rotate(-1)
    nextShape = Shapes.fromBag()
    nextShape.setPos(4,0)
    nextShape.rotation = 1
    nextShape.rotate(-1)
    holdShape = None
    holdCount = 0
    ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)

    pygame.mixer.music.play(-1)
    while running:
        for id,sound in sounds.items():
            sound.set_volume(volume)
        pygame.mixer.music.set_volume(volume)
        clock.tick(frameRate)
        for event in pygame.event.get():
            # Detect window closed
            if event.type == pygame.QUIT:
                closed = True
                replay = False
            if event.type == pygame.KEYDOWN:
                if event.key in controls['volume up']:
                    volume += 0.1
                    if volume < 0:
                        volume = 0
                    elif volume > 1.0:
                        volume = 1.0
                elif event.key in controls['volume down']:
                    volume -= 0.1
                    if volume < 0:
                        volume = 0
                    elif volume > 1.0:
                        volume = 1.0
                elif event.key in controls['mute']:
                    volume = 0

                if event.key in controls['scale 1']:
                    setScale(1)
                elif event.key in controls['scale 2']:
                    setScale(2)
                elif event.key in controls['scale 3']:
                    setScale(3)
                elif event.key in controls['scale 4']:
                    setScale(4)
                if event.key in controls['toggle colour']:
                    coloured = not coloured
                if event.key  in controls['pause']:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                if event.key in controls['quit']:
                    closed = True
                    replay = False
                if event.key in controls['toggle ghost']:
                    show_ghost = not show_ghost
                if (not paused) and (not AREpaused) and event.key in controls['left rotate']:
                    currentShape.rotate(-1)
                    getCollision()
                if (not paused) and (not AREpaused) and event.key in controls['right rotate']:
                    currentShape.rotate(1)
                    getCollision()
                if (not paused) and (not AREpaused) and event.key in controls['hold'] and holdCount == 0:
                    if holdShape == None:
                        currentShape.setPos(4,0)
                        currentShape.rotation = 1
                        currentShape.rotate(-1)
                        holdShape = currentShape
                        nextShape.setPos(4,0)
                        nextShape.rotation = 1
                        nextShape.rotate(-1)
                        currentShape = nextShape
                        ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
                        nextShape = Shapes.fromBag()
                    else:
                        currentShape.setPos(4,0)
                        currentShape.rotation = 1
                        currentShape.rotate(-1)
                        holdShape.setPos(4,0)
                        holdShape.rotation = 1
                        holdShape.rotate(-1)
                        temp = currentShape
                        currentShape = holdShape
                        holdShape = temp
                        del temp
                        ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
                    holdCount += 1
                    getCollision()
        if (not paused) and (not AREpaused):
            # Input
            if (not getInp('move left')) and (not getInp('move right')):
                holding_input = False
                last_input = 0
            if getInp('move left') and (not getInp('move right')) and (not left_collided) and last_input == 0:
                currentShape.x -= 1
                sounds['move'].play()
                if holding_input == False:
                    last_input = 16
                else:
                    last_input = 6
                holding_input = True
                getCollision()
            if getInp('move right') and (not getInp('move left')) and (not right_collided) and last_input == 0:
                currentShape.x += 1
                sounds['move'].play()
                if holding_input == False:
                    last_input = 16
                else:
                    last_input = 6
                holding_input = True
                getCollision()
            if holding_down and not (getInp('soft down') or getInp('hard down')):
                holding_down = False
            if ((not holding_down) and getInp('soft down')) and (not collided) and not collided and (last_soft_input == 0 or speed == 1):
                currentShape.y += 1
                sounds['soft_drop'].play()
                score += 1
                if score > 999999:
                    score = 999999
                last_soft_input = 2
                getCollision()
            if ((not holding_down) and getInp('hard down')) and currentShape.y < ghostShape.y and not collided:
                score += 2*(ghostShape.y - currentShape.y)
                currentShape.y = ghostShape.y
                if score > 999999:
                    score = 999999

        # Rendering
        screen = pygame.image.load('images/gui/bg.png').convert_alpha()
        screen.fill('black')
        if not AREpaused:
            stamps = []
            y = 0
            for row in tileMap:
                x = 0
                for tile in row:
                    if tile != '':
                        sprite = pygame.sprite.Sprite()
                        sprite.image = pygame.image.load(f'images/pieces/{all_shapes[tile].piece_sprite}.png').convert_alpha()
                        sprite.rect = sprite.image.get_rect()
                        stamps.append(((96+8*x,40+8*y),sprite))
                    x += 1
                y += 1
        drawStamps()
        if AREpaused:
            flashStamps()
        # Test game over
        for c in tileMap[0]:
            if c != '':
                running = False
                break
        if running:
            screen.blit(nextShape.gui_sprite,(191,95))
            if holdShape != None:
                screen.blit(holdShape.gui_sprite,(191,151))
            if show_ghost:
                ghostShape.draw()
            currentShape.draw()
        if lvl == 0 or not coloured:
            layer1 = pygame.image.load('images/gui/bg.png').convert_alpha()
            layer1.fill(hsv_to_rgb(300,41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load('images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(300,20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer1,(0,0))
            screen.blit(layer2,(0,0))
            screen.blit(layer2,(0,0))
            screen.blit(pygame.image.load('images/gui/bg2.png').convert_alpha(),(0,0))
        else:
            screen.blit(pygame.image.load('images/gui/bg.png').convert_alpha(),(0,0))
            screen.fill(hsv_to_rgb(overflowNum(lvl*12,360),41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load('images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(overflowNum(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer2,(0,0))
            layer3 = pygame.image.load('images/gui/bg2.png').convert_alpha()
            layer3.fill(hsv_to_rgb(overflowNum(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer3,(0,0))
        screen.blit(pygame.image.load('images/gui/staticText.png').convert_alpha(),(0,0))
        writeNums((152,16),lines,3)
        writeNums((192,32),score,6)
        writeNums((208,72),lvl,2)
        i = 0
        for shape in 'TJZOSLI':
            writeNums((48,88+16*i),stats[shape],3)
            i += 1
        if paused and running:
            screen.blit(paused_overlay,(0,0))
        if not running:
            screen.blit(death_overlay,(0,0))
        scaled = pygame.transform.scale(screen, display.get_size())
        display.blit(scaled, (0, 0))
        pygame.display.flip()


        if (not paused) and (not AREpaused):
            # Collision and line clearing
            getCollision()

            i = 0
            cleared_count = 0
            for row in tileMap:
                cleared = True
                for x in row:
                    if x == '':
                        cleared = False
                        break
                if cleared:
                    clearLine(i)
                    cleared_count += 1
                i += 1
            score += (cleared_count // 4)*(1200*(lvl+1)) # tetrises
            score += ((cleared_count % 4) // 3)*(300*(lvl+1)) # triples
            score += (((cleared_count % 4) % 3) // 2)*(100*(lvl+1)) # doubles 
            score += (((cleared_count % 4) % 3) % 2)*(40*(lvl+1)) # singles
            if score > 999999:
                score = 999999

            if collided and ((last_fall >= speed) or getInp('hard down')):
                currentShape.stamp()
                sounds['place'].play()
                if not currentShape.id in stats.keys():
                    stats[currentShape.id] = 0
                stats[currentShape.id] += 1
                if stats[currentShape.id] > 999:
                    stats[currentShape.id] = 999
                nextShape.setPos(4,0)
                nextShape.rotation = 1
                nextShape.rotate(-1)
                currentShape = nextShape
                ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
                nextShape = Shapes.fromBag()
                holdCount = 0
                if getInp('soft down') or getInp('hard down'):
                    holding_down = True
            elif last_fall >= speed and not ((not holding_down) and (getInp('soft down') or getInp('hard down'))):
                currentShape.y += 1
                sounds['fall'].play()
                last_fall = 0
            else:
                last_fall += 1
            if last_input > 0:
                last_input -= 1
            if last_soft_input > 0:
                last_soft_input -= 1
        if AREpaused and AREpauseLength > 0:
            AREpauseLength -= 1
            if AREpauseLength == 0:
                AREpaused = False
                temp = []
                topBadY = 20
                for stamp in flash_stamps:
                    y = stamp[1].pos.y
                    if y < topBadY:
                        topBadY = y
                for pos,piece in stamps:
                    if piece.pos.y < topBadY:
                        piece.pos.y += linesCleared
                        temp.append(((pos[0],pos[1]+8*linesCleared),piece))
                    else:
                        temp.append((pos,piece))
                flash_stamps = []
                stamps = temp
                linesCleared = 0
        if closed:
            running = False
    # Window closed logic
    else:
        pygame.mixer.music.stop()
        sounds['death'].play()
        game_over = True
        while game_over and not closed:
            for event in pygame.event.get():
                # Detect window closed
                if event.type == pygame.QUIT:
                    game_over = False
                    replay = False
                if event.type == pygame.KEYDOWN:
                    if event.key in controls['quit']:
                        closed = True
                        replay = False
                    if event.key == pygame.K_RETURN:
                        game_over = False
else:
    print('crashed :(') # we love how this is still here lmao
