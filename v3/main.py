# - Imports - #
import pygame
import os
import random
from typing import Literal

# - Inits - #
pygame.init()
clock = pygame.time.Clock()

# - Create window - #
(display_width,display_height) = (256,224)
display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('PyTetris')

def setScale(scale: int):
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_mode((scale*display_width, scale*display_height))
setScale(3)
# - Create window - #

# - Load assets - #
screen = pygame.image.load(f'images/gui/bg.png').convert_alpha()
paused_overlay = pygame.image.load(f'images/gui/paused.png').convert_alpha()
death_overlay = pygame.image.load(f'images/gui/gameOver.png').convert_alpha()
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

pieces = {
    0:pygame.image.load(f'images/pieces/0.png').convert_alpha(), # pink
    1:pygame.image.load(f'images/pieces/1.png').convert_alpha(), # pink + white
    2:pygame.image.load(f'images/pieces/2.png').convert_alpha(), # green
    'G':pygame.image.load(f'images/pieces/ghost.png').convert_alpha() # ghost
}
# - Load assets - #

# - Load controls - #
controls = {
    'left': {pygame.K_a,pygame.K_LEFT},
    'right': {pygame.K_d,pygame.K_RIGHT},
    'down': {pygame.K_s,pygame.K_DOWN},
    'hard_down': {pygame.K_SPACE},
    'hold': {pygame.K_h},
    'left_rot': {pygame.K_q,pygame.K_RSHIFT},
    'right_rot': {pygame.K_e,pygame.K_END},
    'pause': {pygame.K_RETURN},
    'quit': {pygame.K_ESCAPE},
    'ghost': {pygame.K_g,},
    'scale1': {pygame.K_1},
    'scale2': {pygame.K_2},
    'scale3': {pygame.K_3},
    'scale4': {pygame.K_4},
    'vol_up': {pygame.K_KP_PLUS},
    'vol_down': {pygame.K_KP_MINUS},
    'mute': {pygame.K_0}
}
# - Load controls - #

# - Define variables - # 
frameRate = 60

running = True
closed = False
paused = False

score = 0
lines = 0
lvl = 0
speed = 48
stats = {'I':0,'J':0,'L':0,'O':0,'S':0,'T':0,'Z':0}

currentShape = None
nextShape = None
holdShape = None
ghostShape = None
heldThisTurn = False

show_ghost = True
# - Define variables - #

# - Map storage - #
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
        tileMap[y][x] = value
        return value
    except IndexError:
        return (x,y)

def getTileonMap(x,y):
    try:
        return tileMap[y][x]
    except IndexError:
        return (x,y)
# - Map storage - #

# - Rendering functions - #
def writeNums(pos: tuple, num: int, length: int):
    full_num = str(num)
    full_num = (length-len(full_num))*'0'+full_num
    i = 0
    for c in full_num:
        screen.blit(pygame.image.load(f'images/text/{c}.png').convert_alpha(), (pos[0]+8*i,pos[1]))
        i += 1
# - Rendering functions - #

# - Misc functions - #
def rotateTable(table):
    return [[*r][::-1] for r in zip(*table)]

def add_stat(shapeID):
    if shapeID in stats.keys():
        stats[shapeID] += 1
    else:
        stats[shapeID] = 1

def getInp(control_scheme):
    keys = pygame.key.get_pressed()
    for key in controls[control_scheme]:
        if keys[key]:
            return True
    return False

def hsv_to_rgb( h:int, s:int, v:int, a:int = 255 ) -> tuple:
    out = pygame.Color(0)
    out.hsva = (h,s,v,a)
    return (out.r, out.g, out.b, out.a)

def num_wrap(value:int,max:int):
    out = value
    while out > max:
        out = out - max
    return out
# - Misc functions - #

# - Pieces & shapes - #
allShapes = {}
class Shapes:
    class Shape:
        class __Piece__():
            def __init__(self,localPos:tuple,spriteImage:pygame.Surface) -> None:
                self.sprite = pygame.sprite.Sprite()
                self.sprite.image = spriteImage
                self.sprite.rect = self.sprite.image.get_rect()
                self.localPos = pygame.Vector2(*localPos)
                self.pos = pygame.Vector2(*localPos)
            
            def rotate(self,pivotPos: pygame.Vector2,angle: Literal[90,-90,180]):
                return pivotPos + (self.pos - pivotPos).rotate(angle)

        def __init__(self,ID:str,spriteID:int or str,hitbox:tuple,rotatable:bool = True) -> None: # type: ignore
            self.ID = ID
            self.spriteID = spriteID
            self.hitbox = hitbox
            self.rotateable = rotatable
            self.pos = pygame.Vector2(0,0)
            self.width = 0
            self.height = 0
            self.piecesGroup = pygame.sprite.Group()
            temp = []
            for localPos in hitbox:
                piece = self.__Piece__(localPos,pieces[spriteID])
                self.piecesGroup.add(piece.sprite)
                temp.append(piece)
                self.width = max(self.width,localPos[0]+1)
                self.height = max(self.height,localPos[1]+1)
            self.pieces: tuple[self.__Piece__] = tuple(temp)
            del temp
            allShapes[self.ID] = self
            self.setPos((4,0))

        def setPos(self,pos: tuple):
            self.pos = pygame.Vector2(*pos)
            for piece in self.pieces:
                piece.pos = self.pos + piece.localPos

        def move(self,direction: Literal['up','down','left','right']):
            if direction == 'up':
                if self.pos.y > 0:
                    self.setPos(self.pos-(0,1))
            elif direction == 'down':
                if self.pos.y + self.height < 20:
                    self.setPos(self.pos+(0,1))
            elif direction == 'left':
                if self.pos.x > 0:
                    self.setPos(self.pos-(0,1))
            elif direction == 'right':
                if self.pos.x + self.width < 10:
                    self.setPos(self.pos+(0,1))
            else:
                raise ValueError()
        
        def rotate(self,angle: Literal[90,-90,180]):
            if self.rotateable:
                if angle in [90,-90,180]:
                    pivotPos = self.pieces[0].pos
                    newPositions = [piece.rotate(pivotPos,angle) for piece in self.pieces]

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
                    sounds['rotate'].play()
                else:
                    raise ValueError()
        def getGhost(self):
            return self.__class__('G'+self.ID,'G',self.hitbox,self.rotateable)
        
        def draw(self):
            for piece in self.pieces:
                piece.sprite.rect.x = 96+8*piece.pos.x
                piece.sprite.rect.y = 40+8*piece.pos.y
            self.piecesGroup.draw(screen)
        
        def land(self):
            for piece in self.pieces:
                setTileonMap(int(piece.pos.x),int(piece.pos.y),self.ID)
            self.reset()

        def reset(self):
            self.__init__(self.ID,self.spriteID,self.hitbox,self.rotateable)
            
    
    I = Shape('I',1,((1,0),(0,0),(2,0),(3,0)))
    J = Shape('J',0,((1,1),(0,0),(0,1),(2,1)))
    L = Shape('L',2,((1,1),(2,0),(0,1),(2,1)))
    O = Shape('O',1,((0,0),(1,0),(0,1),(1,1)),False)
    S = Shape('S',1,((1,1),(1,0),(2,0),(0,1)))
    T = Shape('T',1,((1,1),(1,0),(0,1),(2,1)))
    Z = Shape('Z',1,((1,1),(0,0),(1,0),(2,1)))

    def makeBag():
        out = []
        for shape in allShapes.values():
            out.insert(random.randint(0,len(out)),shape)
        return out
    bag = makeBag()
    def fromBag() -> Shape:
        if len(Shapes.bag) == 0:
            Shapes.bag = Shapes.makeBag()
        return Shapes.bag.pop(0)
# - Pieces & shapes - #

# - Timers - #
class Timer:
    def __init__(self, duration, repeated = False, func = None) -> None:
        self.duration = duration
        self.repeated = repeated
        self.finished = False
        self.func = func

        self.startTime = 0
        self.active = False

    def activate(self):
        self.active = True
        self.finished = False
        self.startTime = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.finished = True
        self.startTime = 0


    def update(self):
        currentTime = pygame.time.get_ticks()
        if self.active and currentTime - self.startTime >= self.duration:
            if self.func and self.startTime != 0:
                self.func()
            self.deactivate()
            if self.repeated:
                self.activate()

def fall():
    currentShape.move('down')
timers = {
    'fall': Timer(1000/60*speed,True,fall),
    'landed': Timer(1000/60*speed,False)
}
# - Timers - #


# - Main game loop - #
replay = True
while replay:
    clearMap()
    running = True
    closed = False
    paused = False

    score = 0
    lines = 0
    lvl = 0
    speed = 48
    stats = {'I':0,'J':0,'L':0,'O':0,'S':0,'T':0,'Z':0}

    currentShape = Shapes.fromBag()
    ghostShape = currentShape.getGhost()
    nextShape = Shapes.fromBag()
    holdShape = None
    heldThisTurn = False

    pygame.mixer.music.play(-1)

    timers['fall'].activate()

    while running and not closed:
        clock.tick(frameRate)
        for timer in timers.values():
            timer.update()
        for event in pygame.event.get():
            # Detect window closed
            if event.type == pygame.QUIT:
                closed = True
                replay = False
            # Single press input
            if event.type == pygame.KEYDOWN:
                if event.key in controls['scale1']:
                    setScale(1)
                elif event.key in controls['scale2']:
                    setScale(2)
                elif event.key in controls['scale3']:
                    setScale(3)
                elif event.key in controls['scale4']:
                    setScale(4)
                if event.key in controls['pause']:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                if event.key in controls['quit']:
                    closed = True
                    replay = False
                if event.key in controls['ghost']:
                    show_ghost = not show_ghost
                if not paused:
                    if event.key in controls['left_rot']:
                        currentShape.rotate(-90)
                        ghostShape.rotate(-90)
                    if event.key in controls['right_rot']:
                        currentShape.rotate(90)
                        ghostShape.rotate(90)
                    if event.key in controls['hold']:
                        currentShape.reset()
                        if holdShape == None:
                            holdShape = currentShape
                            currentShape = nextShape
                            nextShape = Shapes.fromBag()
                        else:
                            temp = holdShape
                            holdShape = currentShape
                            currentShape = temp
                            del temp
                        ghostShape = currentShape.getGhost()
        
        if not paused:
            ghostShape.setPos((ghostShape.pos.x,20-ghostShape.height))
            if currentShape.pos.y + currentShape.height == 20:
                if not timers['landed'].finished:
                    if not timers['landed'].active:
                        timers['landed'].activate()
                else:
                    currentShape.land()
                    currentShape = nextShape
                    ghostShape = currentShape.getGhost()
                    nextShape = Shapes.fromBag()
                    timers['landed'].finished = False

            for c in tileMap[0]:
                if c != '':
                    running = False
                    break

        # - Rendering - #
        screen = pygame.image.load(f'images/gui/bg.png').convert_alpha()
        screen.fill('black')
        
        for y,row in enumerate(tileMap):
            for x,tile in enumerate(row):
                if tile != '':
                    screen.blit(pieces[allShapes[tile].spriteID],(96+8*x,40+8*y))
        
        if running:
            if show_ghost:
                ghostShape.draw()
            currentShape.draw()
        
        if lvl == 0:
            layer1 = pygame.image.load(f'images/gui/bg.png').convert_alpha()
            layer1.fill(hsv_to_rgb(300,41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load(f'images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(300,20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer1,(0,0))
            screen.blit(layer2,(0,0))
            screen.blit(layer2,(0,0))
            screen.blit(pygame.image.load(f'images/gui/bg2.png').convert_alpha(),(0,0))
        else:
            screen.blit(pygame.image.load(f'images/gui/bg.png').convert_alpha(),(0,0))
            screen.fill(hsv_to_rgb(num_wrap(lvl*12,360),41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load(f'images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(num_wrap(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer2,(0,0))
            layer3 = pygame.image.load(f'images/gui/bg2.png').convert_alpha()
            layer3.fill(hsv_to_rgb(num_wrap(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer3,(0,0))
        screen.blit(pygame.image.load(f'images/gui/staticText.png').convert_alpha(),(0,0))

        writeNums((152,16),lines,3)
        writeNums((192,32),score,6)
        writeNums((208,72),lvl,2)
        for i, shape in enumerate('IJLOSTZ'):
            writeNums((48,88+16*i),stats[shape],3)

        if paused and running:
            screen.blit(paused_overlay,(0,0))
        if not running:
            screen.blit(death_overlay,(0,0))
        
        scaled = pygame.transform.scale(screen, display.get_size())
        display.blit(scaled, (0, 0))
        pygame.display.flip()
# - Main game loop - #