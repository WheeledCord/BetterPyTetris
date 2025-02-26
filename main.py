# ~ Imports ~ #
import pygame
import threading
import sys
from random import shuffle,randrange
from os import environ as osEnviron, path as osPath, execv,spawnl,P_NOWAIT
from copy import deepcopy
from json import load as jsonLoad
from json import dump as jsonDump

from easygui import enterbox,msgbox
from supabase import create_client, Client

import hashlib
import socket

def restart_main():
    # Restart the application...
    executable = sys.executable
    executable_filename = osPath.split(executable)[1]
    if executable_filename.lower().startswith('python'):
        # application is running within a python interpreter
        python = executable
        execv(python, [python, ] + [f'"{v}"' for i,v in enumerate(sys.argv) if i == 0])
        pass
    else:
        # application is running as a standalone executable
        # spawnl(P_NOWAIT,        # flag
        # sys.executable,               # programm
        # sys.executable, "--startup")
        # execv(executable, sys.argv)
        # pass
        msgbox('Sorry!\nThe restart feature is uh, not working great for the EXE build.\nDunno why, but surely you can take the time to open the game again yourself?','PyTetris - Oopsies')
        sys.exit()
    pass


def check_internet_connection():
    remote_server = "www.google.com"
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((remote_server, port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()

online = check_internet_connection()
supabase = None
uname = ''
salted_password = ''
if online:
    url = "https://vqlylnfgxeimreedequm.supabase.co"
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxbHlsbmZneGVpbXJlZWRlcXVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkxMTg5MTksImV4cCI6MjA0NDY5NDkxOX0.oknDiMd1LzWLcvFlF7WKnyLmZMS7iST0468TKMPXE1I'
    supabase: Client = create_client(url, key)

if online:
    # Get player name
    uname = ''
    msg = ''
    while uname == '':
        inp = enterbox('This will be used to save your score.\nYour name must be between 1 and 3 characters, and can\'t contain special characters.\nType \'offline\' to not login and save scores.'+msg,'Please input a name below.',strip=True)
        msg = ''
        if inp is None:
            sys.exit()
        elif len(inp) > 3:
            if inp.lower() == 'offline':
                online = False
                break
            msg = '\n\nYour name can\'t be longer than 3 characters.'
        elif inp == '':
            msg = '\n\nYou must input a name.'
        else:
            for c in inp.lower():
                if c not in '1234567890_-qwertyuiopasdfghjklzxcvbnm':
                    msg = '\n\nYour name can\'t contain special characters.'
                    break
        if msg == '':
            uname = inp.lower()
    del msg
if online:
    # Get player password
    allowed_chars = '1234567890_-qwertyuiopasdfghjklzxcvbnm `~!@#$%^&*()+=,.<>/?;:'
    password = ''
    salted_password = ''
    msg = ''
    while password == '':
        inp = enterbox('Your password must be between 1 and 24 characters, and can\'t contain special characters.'+msg,'Please input a password below.',strip=True)
        msg = ''
        if inp is None:
            sys.exit()
        elif len(inp) > 24:
            msg = '\n\nYour password can\'t be longer than 24 characters.'
        elif inp == '':
            msg = '\n\nYou must input a password.'
        else:
            for c in inp.lower():
                if c not in allowed_chars:
                    msg = '\n\nYour password can only contain the following characters:\n'+allowed_chars
                    break
        if msg == '':
            password = inp
    del msg
    salt = "980432894ceb2d86167649f4453b6aba"
    salted_password = hashlib.sha256((salt + password).encode()).hexdigest()

    try:
        supabase.rpc('add_user', {'p_name': uname, 'p_password':salted_password}).execute()
    except:
        if supabase.rpc('check_password', {'p_name': uname, 'p_password': salted_password}).execute().data != True:
            msgbox('Password was incorrect.','Password was incorrect.')
            sys.exit()

def update_leaderboard():
    if online:
        try:
            supabase.rpc('update_scores_and_lines', {'p_name': uname, 'p_password': salted_password, 'p_score': score, 'p_lines': lines}).execute()
        except:
            pass
        timers['update leaderboard'].activate()


# Inits
pygame.init()
clock = pygame.time.Clock()

## Create window
(display_width,display_height) = (256,224)

scale = 0
# Window scale
def setScale(_scale: int):
    global scale
    scale = _scale
    osEnviron['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_mode((scale*display_width, scale*display_height))

display = pygame.display.set_mode((display_width, display_height))
if online:
    pygame.display.set_caption(f'PyTetris - {uname.title()}')
else:
    pygame.display.set_caption('PyTetris')
icon = pygame.image.load('images/gui/icon.png').convert_alpha()
pygame.display.set_icon(icon)
setScale(3)

# Load assets
screen = pygame.image.load('images/gui/bg.png').convert_alpha()
paused_overlay = pygame.image.load('images/gui/paused.png').convert_alpha()
death_overlay = pygame.image.load('images/gui/gameOver.png').convert_alpha()
lvl_up_particle = pygame.image.load('images/gui/lvlUpParticle.png').convert_alpha()
volumeText = pygame.image.load('images/gui/volume.png').convert_alpha()
pivot_sprite = pygame.image.load(f'images/pieces/pivot.png').convert_alpha()
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

def getGraphValues(image_path):
    img = pygame.image.load('images/curves/'+image_path)
    img = img.convert()
    width, height = img.get_size()
    pixel_counts = []
    for x in range(width):
        pixel_counts.append(0)
        for y in range(height):
            color = img.get_at((x,y))
            if color != (255,255,255,255):
                pixel_counts[x] += 1
    return pixel_counts

scoreParticleSizeCurve = getGraphValues('scoreParticleSize.png')
spreadParticleSizeCurve = getGraphValues('spreadParticleSize.png')
volumeIndicatorPosCurve = getGraphValues('volumeIndicatorPos.png')
hardDropShakeOffsetCurve = getGraphValues('hardDropShakeOffset.png')
softDropShakeOffsetCurve = getGraphValues('softDropShakeOffset.png')
moveShapeAnimCurve = getGraphValues('moveShapeAnim.png')

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
    'reset': [pygame.K_r],
    'quit': [pygame.K_ESCAPE],
    'toggle shake': [pygame.K_s],
    'toggle pivot indicator': [pygame.K_d],
    'toggle fps': [pygame.K_f],
    'toggle ghost': [pygame.K_g],
    'toggle colour': [pygame.K_h],
    'toggle particles': [pygame.K_j],
    'toggle bg': [pygame.K_k],
    'scale 1': [pygame.K_1],
    'scale 2': [pygame.K_2],
    'scale 3': [pygame.K_3],
    'scale 4': [pygame.K_4],
    'volume up': [61],
    'volume down': [45],
    'mute': [pygame.K_0],
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

holding_input = False
holding_down = False
left_collided = False
right_collided = False
running = True
paused = False
coloured = True
show_fps = False
volume = 1.0
AREpaused = False
AREpauseLength = 0
linesCleared = 0

shakeFrames = 0
softShakeFrames = 0
doShakes = True
doParticles = True

scoreParticles = []
spreadParticles = []

volumeIndicatorFrames = len(volumeIndicatorPosCurve)-1

showPivot = True
altBg = False

holdAnimFrames = -1
holdAnim_mode = 'current to hold'
holdAnim_oldCurrentPos = (0,0)
holdAnim_newCurrentPos = (0,0)
holdAnim_oldCurrentRot = 0

nextAnimFrames = -1

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
        tileMap[y][x] = value
        return value
    except IndexError:
        return (x,y)

def getTileonMap(x,y,map):
    try:
        if x < 0 or x >= 10:
            return 'OUT'
        elif y >= 20:
            return 'OUT'
        elif y < 0:
            return 'ABOVE'
        else:
            return map[y][x]
    except IndexError:
        return 'OUT'
    
def rotateTable(table):
    return [[*r][::-1] for r in zip(*table)]



# Rendering
stamps = []
def drawStamps():
    for pos, sprite in stamps:
        screen.blit(sprite.image, (pos[0]+2,pos[1]+10))

TotalAREpauseLength = 60
AREFlashes = 3
flash_stamps = []
def flashStamps():
    for pos, sprite in flash_stamps:
        if AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes)) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*2 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*3) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*4 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*5):
            screen.blit(sprite.image, (pos[0]+2,pos[1]+10))
        else:
            pygame.draw.rect(screen, 'white', (pos[0]+2, pos[1]+10, 7, 7))

# Draw Text
def writeNums(pos: tuple, num: int, length: int, surface: pygame.Surface, color=(255,255,255)):
    full_num = str(num)
    if length != -1:
        full_num = (length-len(full_num))*'0'+full_num
    i = 0
    for c in full_num:
        text = pygame.image.load(f'images/text/{c}.png').convert_alpha()
        text.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(text, (pos[0]+8*i,pos[1]))
        i += 1

# Draw Score Particle
def makeScoreParticle(pos: tuple, amount: int, color=(255,255,255)):
    global scoreParticles
    surface = pygame.Surface((8*(len(str(amount))+1)-1,7), pygame.SRCALPHA)
    writeNums((0,0),'+'+str(amount),-1,surface,color=color)
    scoreParticles.append((pos,surface,0))


class SpreadParticles:
    class Particle:
        def __init__(self,x,y,xv,yv,gs,img,c=(255,255,255)) -> None:
            self.x = x
            self.y = y
            self.x_vel = xv
            self.y_vel = yv
            self.gravity_scale = gs * randrange(1,2)
            self.img = img
            self.color = c
            self.age = 0
            self.gravity = randrange(2,7)
        def draw(self,surface: pygame.Surface):
            self.age += 1
            self.gravity -= self.gravity_scale
            self.x += self.x_vel
            self.y += self.y_vel * self.gravity
            colored = self.img.copy()
            colored.fill(self.color,special_flags=pygame.BLEND_RGB_MULT)
            sized = pygame.transform.scale(colored, ((spreadParticleSizeCurve[self.age]*0.01)*self.img.get_width(),(spreadParticleSizeCurve[self.age]*0.01)*self.img.get_height()))
            surface.blit(sized,(self.x-(sized.get_width()//2),self.y-(sized.get_height()//2))) 
    def __init__(self,amount,start_x,start_y,gravity_scale,img,color=(255,255,255)) -> None:
        self.particles = []
        for i in range(amount):
            self.particles.append(self.Particle(start_x,start_y,randrange(-4,4),randrange(-2,0),gravity_scale,img,color))
    def draw(self,surface):
        for particle in self.particles:
            if particle.age >= len(spreadParticleSizeCurve)-1:
                self.particles.pop(self.particles.index(particle))
            else:
                particle.draw(surface)

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
                
        def __init__(self,id: str,piece_sprite: str,hitbox: str) -> None:
            self.id = id
            self.hitbox = hitbox
            self.base_hitbox = hitbox
            self.piece_sprite = piece_sprite
            self.rotation = 0
            self.x = 4
            self.y = 0
            self.centerPieceId = None
            self.makePieces()
            if id[0] != 'G':
                all_shapes[id] = self
                self.gui_sprite = pygame.Surface((33,42), pygame.SRCALPHA)
                shape_sprite = pygame.Surface((8*self.width,8*self.height), pygame.SRCALPHA)
                for piece in self.pieces:
                    shape_sprite.blit(piece.sprite.image,(8*piece.localx,8*piece.localy))
                rect = shape_sprite.get_rect()
                rect.center = (17,25)
                self.gui_sprite.blit(shape_sprite,rect)
                self.stat_sprite = pygame.Surface((6*self.width,6*self.height), pygame.SRCALPHA)
                for piece in self.pieces:
                    pieceSprite = pygame.Surface((6,6), pygame.SRCALPHA)
                    pieceSprite.blit(pygame.transform.scale(piece.sprite.image,(5,5)),(0,0))
                    pygame.draw.line(pieceSprite,(0,0,0),(5,0),(5,5))
                    pygame.draw.line(pieceSprite,(0,0,0),(0,5),(5,5))
                    self.stat_sprite.blit(pieceSprite,(6*piece.localx,6*piece.localy))

                
        def makePieces(self):
            self.piecesGroup = pygame.sprite.Group()
            self.pieces = []
            maxWidth = 0
            x = 0
            y = 0
            for c in self.hitbox:
                if c.isdigit():
                    piece = self.__piece(self.piece_sprite,c,x,y,self.id)
                    self.pieces.append(piece)
                    x += 1
                elif c == ' ':
                    x += 1
                elif c == '-':
                    y += 1
                    x = 0
                elif c == 'x':
                    self.centerPieceId = self.pieces[-1].id
                maxWidth = max(maxWidth,x)
            self.width = maxWidth
            self.height = self.hitbox.count('-')+1
        
        def getCenterPiece(self):
            for piece in self.pieces:
                if piece.id == self.centerPieceId:
                    return piece

        def rotate(self,dir):
            oldCenterPieceLocalX = None
            oldCenterPieceLocalY = None
            if self.centerPieceId:
                centerPiece = self.getCenterPiece()
                oldCenterPieceLocalX = centerPiece.localx
                oldCenterPieceLocalY = centerPiece.localy
            self.rotation = self.rotation + dir
            if self.rotation < 0:
                self.rotation = 3
            elif self.rotation > 3:
                self.rotation = 0
            new_hitbox = []
            for line in self.base_hitbox.split('-'):
                new_hitbox.append([])
                for c in line:
                    if c.isdigit() or c == ' ':
                        new_hitbox[-1].append(c)
            for i in range(self.rotation):
                new_hitbox = rotateTable(new_hitbox)
            str_hitbox = ''
            for line in new_hitbox:
                for c in line:
                    str_hitbox += c
                str_hitbox += '-'
            str_hitbox = str_hitbox.removesuffix('-')
            self.hitbox = str_hitbox
            self.makePieces()
            if self.centerPieceId:
                centerPiece = self.getCenterPiece()
                self.x += (oldCenterPieceLocalX - centerPiece.localx)
                self.y += (oldCenterPieceLocalY - centerPiece.localy)
            
        def draw(self):
            if showPivot and self.getCenterPiece():
                self.getCenterPiece().sprite.image.blit(pivot_sprite,(0,0))
            elif self.getCenterPiece():
                self.getCenterPiece().sprite.image = pygame.image.load(f'images/pieces/{self.piece_sprite}.png').convert_alpha()
            for piece in self.pieces:
                piece.sprite.rect.x = 96+(8*(self.x+piece.localx))+2
                piece.sprite.rect.y = 40+(8*(self.y+piece.localy))+10
                try:
                    if self.x+piece.localx < 0 or self.x+piece.localx >= 10 or self.y+piece.localy < 0 or self.y+piece.localy >= 20:
                        self.piecesGroup.remove(piece.sprite)
                    else:
                        self.piecesGroup.add(piece.sprite)
                except:
                    pass
            self.piecesGroup.draw(screen)
            
            
        def stamp(self):
            for piece in self.pieces:
                # x = 96+(8*(self.x+piece.localx))
                # y = 40+(8*(self.y+piece.localy))
                s = piece.sprite
                s.globalx = self.x+piece.localx
                s.globaly = self.y+piece.localy
                setTileonMap(self.x+piece.localx,self.y+piece.localy,self.id)
            self.makePieces()
            
    I = shape('I','1','01x23')
    J = shape('J','0','01x2-  3')
    L = shape('L','2','01x2-3  ')
    O = shape('O','1','01-23')
    S = shape('S','0',' 0x1-23 ')
    T = shape('T','1','01x2- 3 ')
    Z = shape('Z','2','01x - 23')

    def __makeBag():
        out = list(all_shapes.values())
        shuffle(out)
        return out
    bag = []

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
        if piece.globaly != y:
            temp.append((pos,piece))
        else:
            flash_stamps.append((pos,piece))
    stamps = temp
    lines += 1
    if lines % 10 == 0:
        lvl += 1
        if doParticles:
            spreadParticles.append(SpreadParticles(25,screen.get_width()//2,screen.get_height()//2,0.2,lvl_up_particle))
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

    ghostShape.x = currentShape.x
    ghostShape.y = currentShape.y-1
    ghostShape.rotation = currentShape.rotation-1
    ghostShape.rotate(1)

    while not ghostCollided:
        ghostShape.y += 1
        if ghostShape.y == (20-ghostShape.height):
            ghostCollided = True
        else:
            tempMap = deepcopy(tileMap)
            for piece in ghostShape.pieces:
                x = ghostShape.x+piece.localx
                y = ghostShape.y+piece.localy
                if x >= 0 and x < 10 and y >= 0 and y < 20:
                    tempMap[y][x] = 'x'
            x = 0
            y = 0
            for row in tempMap:
                for c in row:
                    if c == 'x':
                        if getTileonMap(x,y+1,tempMap) not in ['x','','ABOVE']:
                            ghostCollided = True
                            break
                    x += 1
                y += 1
                x = 0
            del tempMap
    
    tempMap = deepcopy(tileMap)
    for piece in currentShape.pieces:
        x = currentShape.x+piece.localx
        y = currentShape.y+piece.localy
        if x >= 0 and x < 10 and y >= 0 and y < 20:
            tempMap[y][x] = 'x'
    x = 0
    y = 0
    for row in tempMap:
        for c in row:
            if c == 'x':
                try:
                    if currentShape.y == (20-currentShape.height):
                            collided = True
                    elif getTileonMap(x,y+1,tempMap) not in ['x','','ABOVE']:
                        collided = True
                except: collided = True
                
                try:
                    if currentShape.x <= 0:
                        left_collided = True
                    elif getTileonMap(x-1,y,tempMap) not in ['x','','ABOVE']:
                        left_collided = True
                except: left_collided = True

                try:
                    if currentShape.x >= 10-currentShape.width:
                        right_collided = True
                    elif getTileonMap(x+1,y,tempMap) not in ['x','','ABOVE']:
                        right_collided = True
                except: right_collided = True
            x += 1
        y += 1
        x = 0
    del tempMap

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

# - Timers - #
class Timer:
    def __init__(self, duration) -> None:
        self.duration = duration
        self.finished = False

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
        if self.active and currentTime - self.startTime >= (self.duration*(1000/60)):
            self.deactivate()

timers = {
    # 'land': Timer(60),
    'fall': Timer(speed),
    'move': Timer(8),
    'soft down': Timer(2),
    'update leaderboard': Timer(1*60)
}
# - Timers - #


# Main game loop
clearMap()
stamps = []
flash_stamps = []
Shapes.bag = []
currentShape = Shapes.fromBag()
currentShape.x = 4
currentShape.y = 0
currentShape.rotation = 1
currentShape.rotate(-1)
nextShape = Shapes.fromBag()
nextShape.x = 4
nextShape.y = 0
nextShape.rotation = 1
nextShape.rotate(-1)
holdShape = None
holdCount = 0
ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)

pygame.mixer.music.play(-1)

timers['fall'].activate()
timers['move'].deactivate()
timers['soft down'].deactivate()
timers['update leaderboard'].activate()
while running:
    for id,sound in sounds.items():
        sound.set_volume(volume)
    pygame.mixer.music.set_volume(volume)   
    clock.tick(frameRate)
    if not paused:
        for timer in timers.values():
            timer.update()
        if shakeFrames > 0:
            shakeFrames -= 1
        if softShakeFrames > 0:
            softShakeFrames -= 1
    for event in pygame.event.get():
        # Detect window closed
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key in controls['volume up']:
                volume = round(volume+0.1,1)
                if volume < 0:
                    volume = 0.0
                elif volume > 1.0:
                    volume = 1.0
                if volumeIndicatorFrames >= len(volumeIndicatorPosCurve):
                    volumeIndicatorFrames = 0
                elif volumeIndicatorPosCurve[volumeIndicatorFrames] == 100:
                    volumeIndicatorFrames = volumeIndicatorPosCurve.index(100)
                elif volumeIndicatorFrames > len(volumeIndicatorPosCurve)-volumeIndicatorPosCurve[::-1].index(100):
                    volumeIndicatorFrames = len(volumeIndicatorPosCurve)-volumeIndicatorFrames
            elif event.key in controls['volume down']:
                volume = round(volume-0.1,1)
                if volume < 0:
                    volume = 0.0
                elif volume > 1.0:
                    volume = 1.0
                if volumeIndicatorFrames >= len(volumeIndicatorPosCurve):
                    volumeIndicatorFrames = 0
                elif volumeIndicatorPosCurve[volumeIndicatorFrames] == 100:
                    volumeIndicatorFrames = volumeIndicatorPosCurve.index(100)
                elif volumeIndicatorFrames > len(volumeIndicatorPosCurve)-volumeIndicatorPosCurve[::-1].index(100):
                    volumeIndicatorFrames = len(volumeIndicatorPosCurve)-volumeIndicatorFrames
            elif event.key in controls['mute']:
                volume = 0.0
                if volumeIndicatorFrames >= len(volumeIndicatorPosCurve):
                    volumeIndicatorFrames = 0
                elif volumeIndicatorPosCurve[volumeIndicatorFrames] == 100:
                    volumeIndicatorFrames = volumeIndicatorPosCurve.index(100)
                elif volumeIndicatorFrames > len(volumeIndicatorPosCurve)-volumeIndicatorPosCurve[::-1].index(100):
                    volumeIndicatorFrames = len(volumeIndicatorPosCurve)-volumeIndicatorFrames

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
            if event.key in controls['toggle pivot indicator']:
                showPivot = not showPivot
            if event.key in controls['toggle fps']:
                show_fps = not show_fps
            if event.key  in controls['pause']:
                paused = not paused
                if paused:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            if event.key in controls['reset']:
                restart_main()
            if event.key in controls['quit']:
                sys.exit()
            if event.key in controls['toggle ghost']:
                show_ghost = not show_ghost
            if event.key in controls['toggle shake']:
                doShakes = not doShakes
            if event.key in controls['toggle bg']:
                altBg = not altBg
            if event.key in controls['toggle particles']:
                doParticles = not doParticles
            if (not paused) and (not AREpaused) and (holdAnimFrames < 0 and nextAnimFrames < 0) and event.key in controls['left rotate'] and currentShape.getCenterPiece():
                currentShape.rotate(-1)
                i = True
                out = False
                for piece in currentShape.pieces:
                    spot = getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy,tileMap)
                    print(spot)
                    if spot == 'OUT' or (spot not in ['ABOVE','']):
                        i = False
                        out = spot == 'OUT'
                        break
                if (not i) and out:
                    oldX = currentShape.x
                    ii = False
                    for piece in currentShape.pieces:
                        if currentShape.x+piece.localx >= 10:
                            currentShape.x = 10-currentShape.width
                            ii = True
                            break
                        elif currentShape.x+piece.localx <= -1:
                            currentShape.x = 0
                            ii = True
                            break
                    if ii:
                        i = True
                        for piece in currentShape.pieces:
                            spot = getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy,tileMap)
                            if spot == 'OUT' or (spot not in ['ABOVE','']):
                                i = False
                                break
                        if not i:
                            currentShape.x = oldX
                if i:
                    sounds['rotate'].play()
                    getCollision()
                else:
                    currentShape.rotate(1)
                    getCollision()
            if (not paused) and (not AREpaused) and (holdAnimFrames < 0 and nextAnimFrames < 0) and event.key in controls['right rotate'] and currentShape.getCenterPiece():
                currentShape.rotate(1)
                i = True
                out = False
                for piece in currentShape.pieces:
                    spot = getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy,tileMap)
                    if spot == 'OUT' or (spot not in ['ABOVE','']):
                        i = False
                        out = spot == 'OUT'
                        break
                if (not i) and out:
                    oldX = currentShape.x
                    ii = False
                    for piece in currentShape.pieces:
                        if currentShape.x+piece.localx >= 10:
                            currentShape.x = 10-currentShape.width
                            ii = True
                            break
                        elif currentShape.x+piece.localx <= -1:
                            currentShape.x = 0
                            ii = True
                            break
                    if ii:
                        i = True
                        for piece in currentShape.pieces:
                            spot = getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy,tileMap)
                            if spot == 'OUT' or (spot not in ['ABOVE','']):
                                i = False
                                break
                        if not i:
                            currentShape.x = oldX
                if i:
                    sounds['rotate'].play()
                    getCollision()
                else:
                    currentShape.rotate(-1)
                    getCollision()
            if (not paused) and (not AREpaused) and (holdAnimFrames < 0 and nextAnimFrames < 0) and event.key in controls['hold'] and holdCount == 0:
                if holdShape == None:
                    holdAnim_mode = 'current to hold'
                    holdAnim_oldCurrentPos = (96+(8*(currentShape.x))+2,40+(8*(currentShape.y))+10)
                    holdAnim_oldCurrentRot = currentShape.rotation
                    currentShape.x = 4
                    currentShape.y = 0
                    currentShape.rotation = 1
                    currentShape.rotate(-1)
                    holdShape = currentShape
                    nextShape.x = 4
                    nextShape.y = 0
                    nextShape.rotation = 1
                    nextShape.rotate(-1)
                    currentShape = nextShape
                    ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
                    nextShape = Shapes.fromBag()
                    nextAnimFrames = len(moveShapeAnimCurve)
                else:
                    holdAnim_mode = 'swap'
                    holdAnim_oldCurrentPos = (96+(8*(currentShape.x))+2,40+(8*(currentShape.y))+10)
                    holdAnim_oldCurrentRot = currentShape.rotation
                    currentShape.x = 4
                    currentShape.y = 0
                    holdAnim_newCurrentPos = (96+(8*(currentShape.x))+2,40+(8*(currentShape.y))+10)
                    currentShape.rotation = 1
                    currentShape.rotate(-1)
                    holdShape.x = 4
                    holdShape.y = 0
                    holdShape.rotation = 1
                    holdShape.rotate(-1)
                    temp = currentShape
                    currentShape = holdShape
                    holdShape = temp
                    del temp
                    ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
                holdCount += 1
                getCollision()
                holdAnimFrames = len(moveShapeAnimCurve)
    if (not paused) and (not AREpaused) and (holdAnimFrames < 0 and nextAnimFrames < 0):
        # Input
        if (not getInp('move left')) and (not getInp('move right')):
            holding_input = False
            timers['move'].deactivate()
        if getInp('move left') and (not getInp('move right')) and (not left_collided) and timers['move'].finished:
            currentShape.x -= 1
            getCollision()
            sounds['move'].play()
            if holding_input == False:
                timers['move'].duration = 16
            else:
                timers['move'].duration = 6
            timers['move'].activate()
            holding_input = True
        if getInp('move right') and (not getInp('move left')) and (not right_collided) and timers['move'].finished:
            currentShape.x += 1
            getCollision()
            sounds['move'].play()
            if holding_input == False:
                timers['move'].duration = 16
            else:
                timers['move'].duration = 6
            timers['move'].activate()
            holding_input = True
        if holding_down and not (getInp('soft down') or getInp('hard down')):
            holding_down = False
        if ((not holding_down) and getInp('soft down')) and currentShape.y + currentShape.height < 20 and not collided and (timers['soft down'].finished or speed == 1):
            currentShape.y += 1
            getCollision()
            sounds['soft_drop'].play()
            score += 1
            if doParticles:
                makeScoreParticle((96+(8*(currentShape.x+(currentShape.width // 2)))+2,40+(8*(currentShape.y+(currentShape.height // 2)))+10),1)
            if score > 999999:
                score = 999999
            timers['soft down'].duration = 2
            timers['soft down'].activate()
            timers['fall'].activate()
            if softShakeFrames < len(softDropShakeOffsetCurve)//2:
                softShakeFrames = len(softDropShakeOffsetCurve)
        if ((not holding_down) and getInp('hard down')) and currentShape.y < ghostShape.y and not collided:
            score += 2*(ghostShape.y - currentShape.y)
            if doParticles:
                makeScoreParticle((96+(8*(currentShape.x+(currentShape.width // 2)))+2,40+(8*(currentShape.y+(currentShape.height // 2)))+10),2*(ghostShape.y - currentShape.y))
            currentShape.y = ghostShape.y
            getCollision()
            if score > 999999:
                score = 999999 
            shakeFrames = len(hardDropShakeOffsetCurve)

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
                    sprite.globaly = y
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
    if nextAnimFrames < 0:
        screen.blit(nextShape.gui_sprite,(191+2,95+10))
    else:
        nextShapeGui_scaled = pygame.transform.scale(nextShape.gui_sprite.copy(),pygame.Vector2(33,42)*(0.01*moveShapeAnimCurve[nextAnimFrames-1]))
        screen.blit(nextShapeGui_scaled,pygame.Vector2(193+15.5,105+21)-(pygame.Vector2(nextShapeGui_scaled.get_size())/2))
    if holdAnimFrames < 0:
        if holdShape != None:
            screen.blit(holdShape.gui_sprite,(191+2,151+10))
        if nextAnimFrames < 0:
            if show_ghost and not AREpaused:
                ghostShape.draw()
            currentShape.draw()
    layer3 = pygame.Surface((256,224), pygame.SRCALPHA)
    for id,pos in {'T':(26,85),'J':(26,100),'Z':(26,117),'O':(29,133),'S':(26,149),'L':(26,164),'I':(24,184)}.items():
        layer3.blit(all_shapes[id].stat_sprite,pos)
    if altBg:
        screen.blit(pygame.image.load('images/gui/altBg.png').convert_alpha(),(0,0))
    else:
        if lvl == 0 or not coloured:
            layer1 = pygame.image.load('images/gui/bg.png').convert_alpha()
            layer1.fill(hsv_to_rgb(300,41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load('images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(300,20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer1,(0,0))
            screen.blit(layer2,(0,0))
        else:
            screen.blit(pygame.image.load('images/gui/bg.png').convert_alpha(),(0,0))
            screen.fill(hsv_to_rgb(overflowNum(lvl*12,360),41,100,0), special_flags=pygame.BLEND_RGB_MULT)
            layer2 = pygame.image.load('images/gui/bg1.png').convert_alpha()
            layer2.fill(hsv_to_rgb(overflowNum(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(layer2,(0,0))
            layer3.fill(hsv_to_rgb(overflowNum(lvl*12,360),20,100,0), special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(layer3,(0+2,0+10))
    screen.blit(pygame.image.load('images/gui/staticText.png').convert_alpha(),(0+2,0+10))
    writeNums((152+2,16+10),lines,3,screen)
    writeNums((192+2,32+10),score,6,screen)
    writeNums((208+2,72+10),lvl,2,screen)
    i = 0
    for shape in 'TJZOSLI': # this must be in this order.
        writeNums((48+2,88+16*i+10),stats[shape],3,screen)
        i += 1
    if doParticles:
        temp = scoreParticles
        i = 0
        for [_pos,particle,_age] in temp:
            if (not paused) and running:
                pos = _pos
                age = _age
                sized = pygame.transform.scale(particle, ((scoreParticleSizeCurve[age]*0.01)*particle.get_width(),(scoreParticleSizeCurve[age]*0.01)*particle.get_height()))
                if pos[0] == 'center':
                    pos = (screen.get_width()//2,pos[1])
                if pos[1] == 'center':
                    pos = (pos[0],screen.get_height()//2 - (sized.get_height()//2))
                age += 1
                if age >= 89:
                    scoreParticles.pop(i)
                else:
                    scoreParticles[i] = (_pos,particle,age)
                    if AREpaused and screen.get_at((pos[0]-(sized.get_width()//2),pos[1])) == (255,255,255,255):
                        sized.fill('black',special_flags=pygame.BLEND_RGB_MULT)
                    screen.blit(sized,(pos[0]-(sized.get_width()//2),pos[1]))
            i += 1
        for _spreadParticles in spreadParticles:
            if len(_spreadParticles.particles) == 0:
                spreadParticles.remove(_spreadParticles)
            else:
                if (not paused) and running:
                    _spreadParticles.draw(screen)

    if not paused and holdAnimFrames >= 0:
        if holdAnimFrames > 0:
            if holdAnim_mode == 'current to hold':
                diff = pygame.Vector2(holdAnim_oldCurrentPos) - pygame.Vector2(193,161)
                rotDiff = 0
                if holdAnim_oldCurrentRot >= 2:
                    rotDiff = (90*holdAnim_oldCurrentRot)
                else:
                    rotDiff = (-90*holdAnim_oldCurrentRot)
                rotated = pygame.transform.rotate(holdShape.gui_sprite.copy(), (moveShapeAnimCurve[len(moveShapeAnimCurve)-(holdAnimFrames)]*0.01)*rotDiff)
                screen.blit(rotated,holdAnim_oldCurrentPos - ((moveShapeAnimCurve[holdAnimFrames-1]*0.01)*diff))
            elif holdAnim_mode == 'swap':
                diff = pygame.Vector2(holdAnim_oldCurrentPos) - pygame.Vector2(193,161)
                rotDiff = 0
                if holdAnim_oldCurrentRot >= 2:
                    rotDiff = (90*holdAnim_oldCurrentRot)
                else:
                    rotDiff = (-90*holdAnim_oldCurrentRot)
                rotated = pygame.transform.rotate(holdShape.gui_sprite.copy(), (moveShapeAnimCurve[len(moveShapeAnimCurve)-(holdAnimFrames)]*0.01)*rotDiff)
                screen.blit(rotated,holdAnim_oldCurrentPos - ((moveShapeAnimCurve[holdAnimFrames-1]*0.01)*diff))
                diff = pygame.Vector2(193,161) - pygame.Vector2(holdAnim_newCurrentPos)
                screen.blit(currentShape.gui_sprite,pygame.Vector2(193,161) - ((moveShapeAnimCurve[holdAnimFrames-1]*0.01)*diff))
        holdAnimFrames -= 1
    if not paused and nextAnimFrames >= 0:
        if nextAnimFrames > 0:
            diff = pygame.Vector2(193,105) - (130,50)
            screen.blit(currentShape.gui_sprite.copy(),(193,105) - ((moveShapeAnimCurve[nextAnimFrames-1]*0.01)*diff))
        else:
            timers['fall'].duration = speed
            timers['fall'].activate()
        nextAnimFrames -= 1

    if show_fps:
        pygame.draw.rect(screen,(0,0,0),pygame.Rect(0,0,21,19))
        fps_color = (255,255,255)
        if int(clock.get_fps()) < 20:
            fps_color = (255,0,0)
        elif int(clock.get_fps()) < 30:
            fps_color = (255,128,0)
        elif int(clock.get_fps()) < 40:
            fps_color = (255,255,0)
        else:
            fps_color = (255,255,255)
        writeNums((2+2,0+10),int(clock.get_fps()),2,screen,color=fps_color)

    if paused and running:
        screen.blit(paused_overlay,(0+2,0+10))

    if running:
        if volumeIndicatorFrames < len(volumeIndicatorPosCurve):
            volumeIndicatorFrame = pygame.Surface((80,30), pygame.SRCALPHA)
            volumeIndicatorFrame.fill((0,0,0,128))
            volumeIndicatorFrame.blit(volumeText,(16,20))
            for _i in range(1,11):
                i = round(0.1*_i,1)
                bar = pygame.Surface((4,_i), pygame.SRCALPHA)
                if volume >= i:
                    bar.fill((255,255,255,255))
                else:
                    bar.fill((255,255,255,0))
                volumeIndicatorFrame.blit(bar,(10+(6*(_i-1)),15-_i),special_flags=pygame.BLEND_RGBA_ADD)
            screen.blit(volumeIndicatorFrame,(screen.get_width()//2-40,0.4*volumeIndicatorPosCurve[volumeIndicatorFrames]-30))
        volumeIndicatorFrames += 1
        if volumeIndicatorFrames < 0:
            volumeIndicatorFrames = 0
        elif volumeIndicatorFrames >= len(volumeIndicatorPosCurve):
            volumeIndicatorFrames = len(volumeIndicatorPosCurve)

    if not running:
        screen.blit(death_overlay,(0+2,0+10))
    
    display_size = display.get_size()
    scaled = pygame.transform.scale(screen, (display_size[0]+(4*scale),display_size[1]+(20*scale)))
    shake = 0
    softShake = 0
    if (not paused) and running and doShakes:
        if shakeFrames > 0 and shakeFrames < len(hardDropShakeOffsetCurve):
            shake = hardDropShakeOffsetCurve[len(hardDropShakeOffsetCurve)-shakeFrames]-11
        if softShakeFrames > 0:
            softShake = softDropShakeOffsetCurve[len(softDropShakeOffsetCurve)-softShakeFrames]-5
    display.fill('black')
    display.blit(scaled, (0+(softShake*scale)-(2*scale), 0+(shake*scale)-(10*scale)))
    pygame.display.flip()


    if (not paused) and (not AREpaused):
        # Collision and line clearing
        getCollision()

        i = 0
        lines_cleared = []
        cleared_count = 0
        for row in tileMap:
            cleared = True
            for x in row:
                if x == '':
                    cleared = False
                    break
            if cleared:
                clearLine(i)
                lines_cleared.append(i)
                cleared_count += 1
            i += 1
        score += (cleared_count // 4)*(1200*(lvl+1)) # tetrises
        if doParticles and (cleared_count // 4) != 0:
            makeScoreParticle(('center',40+(8*sorted(lines_cleared)[0])+10),(cleared_count // 4)*(1200*(lvl+1)))
        score += ((cleared_count % 4) // 3)*(300*(lvl+1)) # triples
        if doParticles and ((cleared_count % 4) // 3) != 0:
            makeScoreParticle(('center',40+(8*sorted(lines_cleared)[0])+10),((cleared_count % 4) // 3)*(300*(lvl+1)))
        score += (((cleared_count % 4) % 3) // 2)*(100*(lvl+1)) # doubles
        if doParticles and (((cleared_count % 4) % 3) // 2) != 0:
            makeScoreParticle(('center',40+(8*sorted(lines_cleared)[0])+10),(((cleared_count % 4) % 3) // 2)*(100*(lvl+1)))
        score += (((cleared_count % 4) % 3) % 2)*(40*(lvl+1)) # singles
        if doParticles and (((cleared_count % 4) % 3) % 2) != 0:
            makeScoreParticle(('center',40+(8*sorted(lines_cleared)[0])+10),(((cleared_count % 4) % 3) % 2)*(40*(lvl+1)))
        if score > 999999:
            score = 999999

        getCollision()
        # if collided and timers['land'].active == False and timers['land'].finished == False:
        #     timers['land'].activate()
        if collided and (timers['fall'].finished or getInp('hard down')):
            # timers['land'].finished = False
            currentShape.stamp()
            sounds['place'].play()
            if not currentShape.id in stats.keys():
                stats[currentShape.id] = 0
            stats[currentShape.id] += 1
            if stats[currentShape.id] > 999:
                stats[currentShape.id] = 999
            nextShape.x = 4
            nextShape.y = 0
            nextShape.rotation = 1
            nextShape.rotate(-1)
            currentShape = nextShape
            ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)
            nextShape = Shapes.fromBag()
            nextAnimFrames = len(moveShapeAnimCurve)
            holdCount = 0
            if getInp('soft down') or getInp('hard down'):
                holding_down = True
        elif timers['fall'].finished and (holdAnimFrames < 0 and nextAnimFrames < 0) and not ((not holding_down) and (getInp('soft down') or getInp('hard down'))):
            currentShape.y += 1
            sounds['fall'].play()
            timers['fall'].duration = speed
            timers['fall'].activate()
    if AREpaused and AREpauseLength > 0:
        AREpauseLength -= 1
        if AREpauseLength == 0:
            AREpaused = False
            temp = []
            topBadY = 20
            for stamp in flash_stamps:
                y = stamp[1].globaly
                if y < topBadY:
                    topBadY = y
            for pos,piece in stamps:
                if piece.globaly < topBadY:
                    piece.globaly += linesCleared
                    temp.append(((pos[0],pos[1]+8*linesCleared),piece))
                else:
                    temp.append((pos,piece))
            flash_stamps = []
            stamps = temp
            linesCleared = 0
    if timers['update leaderboard'].finished:
        upd_thr = threading.Thread(target=update_leaderboard)
        upd_thr.start()
# Window closed logic
else:
    pygame.mixer.music.stop()
    sounds['death'].play()
    while True:
        for event in pygame.event.get():
            # Detect window closed
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in controls['quit']:
                    sys.exit()
                if event.key == pygame.K_RETURN or event.key in controls['reset']:
                    restart_main()
