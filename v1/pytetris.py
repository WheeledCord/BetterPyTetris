# Imports
import pygame
import random
import os
import copy
    
# Potential Todo:
# Don't generate new shape until line finishes clearing (kept doing it anyways when I tried?),
# Add config file for controls
# Push shape left when rotating against wall (if collision allows it),
# Pause music on pause screen,
# Restart button on death,

controls = {
    "left": {pygame.K_a,pygame.K_LEFT},
    "right": {pygame.K_d,pygame.K_RIGHT},
    "down": {pygame.K_s,pygame.K_DOWN},
    "left_rot": {pygame.K_q,pygame.K_RSHIFT},
    "right_rot": {pygame.K_e,pygame.K_END},
    "pause": {pygame.K_RETURN},
    "quit": {pygame.K_ESCAPE},
    "ghost": {pygame.K_g,},
    "scale1": {pygame.K_1},
    "scale2": {pygame.K_2},
    "scale3": {pygame.K_3},
    "scale4": {pygame.K_4}
}

# Inits
pygame.init()
clock = pygame.time.Clock()

# Window info
(display_width,display_height) = (256,224)
window_title = 'PyTetris'

# Create window
display = pygame.display.set_mode((display_width, display_height))
screen = pygame.image.load(f'images/gui/bg.png').convert()
pygame.display.set_caption(window_title)

# Screen overlays
paused_gui = pygame.image.load(f'images/gui/paused.png').convert_alpha()
game_over_gui = pygame.image.load(f'images/gui/gameOver.png').convert_alpha()

# Window scale
def setScale(scale: int):
    global display,display_width,display_height
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    display = pygame.display.set_mode((scale*display_width, scale*display_height))
setScale(3)

def rotateTable(table):
    return [[*r][::-1] for r in zip(*table)]

# Map storage
tileMap = []
for i in range(20):
    ii = []
    for iii in range(10):
        ii.append('')
    tileMap.append(ii)
def setTileonMap(x,y,value):
    tileMap[y][x] = value

def getTileonMap(x,y):
    return tileMap[y][x]

# Draw Text
def writeNums(pos: tuple,num: int,length: int):
    full_num = str(num)
    full_num = (length-len(full_num))*'0'+full_num
    i = 0
    for c in full_num:
        screen.blit(pygame.image.load(f'images/gui/text/{c}.png').convert_alpha(), (pos[0]+8*i,pos[1]))
        i += 1

def getInp(control_scheme):
    keys = pygame.key.get_pressed()
    for key in controls[control_scheme]:
        if keys[key]:
            return True
    return False

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
            if id[0] != 'G':
                self.gui_sprite = pygame.image.load(f'images/gui/{id}.png').convert_alpha()

            self.hitbox = hitbox
            self.base_hitbox = hitbox
            self.piece_sprite = piece_sprite
            self.rotation = 0
            self.x = 4
            self.y = 0
            self.makePieces()
            if id[0] != 'G':
                all_shapes[id] = self
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
            self.width = len(self.hitbox.split('-')[0])
            self.height = self.hitbox.count('-')+1
        def rotate(self,dir):
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
        def draw(self):
            for piece in self.pieces:
                piece.sprite.rect.x = 96+(8*(self.x+piece.localx))
                piece.sprite.rect.y = 40+(8*(self.y+piece.localy))
            self.piecesGroup.draw(screen)
        def stamp(self):
            global stamps
            for piece in self.pieces:
                x = 96+(8*(self.x+piece.localx))
                y = 40+(8*(self.y+piece.localy))
                s = piece.sprite
                s.globalx = self.x+piece.localx
                s.globaly = self.y+piece.localy
                temp = []
                setTileonMap(self.x+piece.localx,self.y+piece.localy,self.id)
                for pos,piece in stamps:
                    if pos != (x,y):
                        temp.append((pos,piece))
                stamps = temp
                stamps.append(((x,y),s))
            self.makePieces()
            
    I = shape('I','toi','0123')
    J = shape('J','js','012-  3')
    L = shape('L','zl','012-3  ')
    O = shape('O','toi','01-23')
    S = shape('S','js',' 01-23 ')
    T = shape('T','toi','012- 3 ')
    Z = shape('Z','zl','01 - 23')
    def random() -> shape:
        return random.choice(list(all_shapes.values()))

# Stats and scores
top_score = 10000
score = 0
lines = 0
stats = {'I':0,'J':0,'L':0,'O':0,'S':0,'T':0,'Z':0}
lvl = 0

TotalAREpauseLength = 60
AREFlashes = 3
# Clearing Lines
def clearLine(y: int):
    global stamps,lines,lvl,speed,AREpaused,AREpauseLength,flash_stamps,linesCleared
    sounds['line_clear'].play()
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

# Stamping previous placed shapes
stamps = []
def drawStamps():
    for pos, sprite in stamps:
        screen.blit(sprite.image, pos)
flash_stamps = []
def flashStamps():
    global AREpauseLength
    for pos, sprite in flash_stamps:
        if AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes)) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*2 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*3) or (AREpauseLength > (TotalAREpauseLength/(2*AREFlashes))*4 and AREpauseLength <= (TotalAREpauseLength/(2*AREFlashes))*5):
            screen.blit(sprite.image, pos)
        else:
            pygame.draw.rect(screen, "white", (pos[0], pos[1], 7, 7))

# Frame and speed info
frameRate = 60
speed = 48 # ticks between fall
last_fall = 0
last_input = 0
last_soft_input = 0
holding_input = False
show_ghost = True

# Pick the first and second shape
currentShape = Shapes.random()
nextShape = Shapes.random()
ghostShape = Shapes.shape('G'+currentShape.id,'ghost',currentShape.hitbox)

pygame.mixer.music.load('music/music.mp3')
pygame.mixer.music.play(-1)

sounds = {
    "move":pygame.mixer.Sound('music/move.mp3'),
    "rotate":pygame.mixer.Sound('music/rotate.mp3'),
    "place":pygame.mixer.Sound('music/place.mp3'),
    "line_clear":pygame.mixer.Sound('music/line_clear.mp3'),
    "death":pygame.mixer.Sound('music/death.mp3')
}

# Main game loop
running = True
closed = False
paused = False
AREpaused = False
AREpauseLength = 0
linesCleared = 0
while running:
    clock.tick(frameRate)
    for event in pygame.event.get():
        # Detect window closed
        if event.type == pygame.QUIT:
            closed = True
        # Scale keys
        if event.type == pygame.KEYDOWN:
            if event.key in controls['scale1']:
                setScale(1)
            elif event.key in controls['scale2']:
                setScale(2)
            elif event.key in controls['scale3']:
                setScale(3)
            elif event.key in controls['scale4']:
                setScale(4)
            if event.key  in controls['pause']:
                paused = not paused
            if event.key in controls['quit']:
                closed = True
            if event.key in controls['ghost']:
                show_ghost = not show_ghost
            if (not paused) and (not AREpaused) and event.key in controls['left_rot']:
                currentShape.rotate(-1)
                i = True
                for piece in currentShape.pieces:
                    if currentShape.x+piece.localx >= 10 or currentShape.y+piece.localy >= 20 or getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy) != '':
                        currentShape.rotate(1)
                        i = False
                        break
                if i:
                    sounds['rotate'].play()
            if (not paused) and (not AREpaused) and event.key in controls['right_rot']:
                currentShape.rotate(1)
                i = True
                for piece in currentShape.pieces:
                    if currentShape.x+piece.localx >= 10 or currentShape.y+piece.localy >= 20 or getTileonMap(currentShape.x+piece.localx,currentShape.y+piece.localy) != '':
                        currentShape.rotate(-1)
                        i = False
                        break
                if i:
                    sounds['rotate'].play()
    if (not paused) and (not AREpaused):
        # Input
        if (not getInp('left')) and (not getInp('right')):
            holding_input = False
        if getInp('left') and (not getInp('right')) and (not left_collided) and last_input == 0:
            currentShape.x -= 1
            sounds['move'].play()
            if holding_input == False:
                last_input = 16
            else:
                last_input = 6
            holding_input = True
        if getInp('right') and (not getInp('left')) and (not right_collided) and last_input == 0:
            currentShape.x += 1
            sounds['move'].play()
            if holding_input == False:
                last_input = 16
            else:
                last_input = 6
            holding_input = True
        if getInp('down') and currentShape.y + currentShape.height < 20 and not collided and (last_soft_input == 0 or speed == 1):
            currentShape.y += 1
            score += 1
            if score > 999999:
                score = 999999
            last_soft_input = 2

    # Rendering
    screen = pygame.image.load(f'images/gui/bg.png').convert()
    drawStamps()
    if AREpaused:
        flashStamps()
    writeNums((152,16),lines,3)
    writeNums((192,32),top_score,6)
    writeNums((192,56),score,6)
    writeNums((208,160),lvl,2)
    i = 0
    for shape in 'TJZOSLI':
        writeNums((48,88+16*i),stats[shape],3)
        i += 1
    # Test game over
    for c in tileMap[0]:
        if c != '':
            running = False
            break
    if running:
        screen.blit(nextShape.gui_sprite,(191,95))
        if show_ghost:
            ghostShape.draw()
    currentShape.draw()
    if paused and running:
        screen.blit(paused_gui,(0,0))
    if not running:
        screen.blit(game_over_gui,(0,0))
    scaled = pygame.transform.scale(screen, display.get_size())
    display.blit(scaled, (0, 0))
    pygame.display.flip()

    if (not paused) and (not AREpaused):
        # Collision and line clearing
        collided = False
        left_collided = False
        right_collided = False
        
        tempMap = copy.deepcopy(tileMap)
        for piece in currentShape.pieces:
            x = currentShape.x+piece.localx
            y = currentShape.y+piece.localy
            tempMap[y][x] = 'x'
        x = 0
        y = 0
        for row in tempMap:
            for c in row:
                if c == 'x':
                    if currentShape.y == (20-currentShape.height):
                            collided = True
                    elif not (tempMap[y+1][x] in 'x '):
                        collided = True
                    
                    if currentShape.x <= 0:
                        left_collided = True
                    elif not (tempMap[y][x-1] in 'x '):
                        left_collided = True
                    
                    if currentShape.x >= 10-currentShape.width:
                        right_collided = True
                    elif not (tempMap[y][x+1] in 'x '):
                        right_collided = True
                x += 1
            y += 1
            x = 0
        del tempMap

        # Get next frame's ghost
        ghostCollided = False
        
        ghostShape.x = currentShape.x
        ghostShape.y = currentShape.y-1
        ghostShape.rotation = currentShape.rotation-1
        ghostShape.rotate(1)
        while not ghostCollided:
            ghostShape.y += 1
            if ghostShape.y == (20-ghostShape.height):
                ghostCollided = True
            else:
                tempMap = copy.deepcopy(tileMap)
                for piece in ghostShape.pieces:
                    x = ghostShape.x+piece.localx
                    y = ghostShape.y+piece.localy
                    tempMap[y][x] = 'x'
                x = 0
                y = 0
                for row in tempMap:
                    for c in row:
                        if c == 'x':
                            if not (tempMap[y+1][x] in 'x '):
                                ghostCollided = True
                                break
                        x += 1
                    y += 1
                    x = 0
                del tempMap

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
        if score > top_score:
            top_score = score

        if collided and last_fall >= speed:
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
            nextShape = Shapes.random()
        elif last_fall >= speed and not getInp('down'):
            currentShape.y += 1
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
            if event.type == pygame.KEYDOWN:
                if event.key in controls['quit']:
                    closed = True
    else:
        print('crashed :(') # we love how this is still here lmao