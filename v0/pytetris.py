import pygame
import random

# i uh, did a lot.
# as far as i'm aware, this is what we have left to do:
# fix controls,
# fix rotation on right side bug (only for I piece?),
# fix gui and scale stuffs (bg, icon, stats section, and maybe recolour blocks),
# make pieces from single 1x1 cube sprite,
# add colisions,
# add placement prediction ghost,
# add score on actions,
# change speed over time,
# holding pieces maybe?
# make line clearing possible,
# maybe remake program once all of above is done, to make it cleaner and more optimised,, this is already in progress

pygame.init()
pygame.font.init()
clock = pygame.time.Clock()
font = pygame.font.SysFont('Nintendo NES Font Regular', 12)

background_colour = (255,100,255)
line_colour = (96,38,96)
(screen_width,screen_height) = (400,720)
screen_title = 'PyTetris'

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption(screen_title)

stamps = []
def draw_stamps(target_surf):
    for pos, sprite in stamps:
        target_surf.blit(sprite.image, pos)
def draw_grid():
    for row in range(20):
        for col in range(10):
            x = col * 16
            y = row * 16
            pygame.draw.rect(screen, (166,65,166), (screen_width/2-82+2+x, 20+2+y, 16, 16), 1)

tileMap = []
for i in range(20):
    ii = []
    for iii in range(10):
        ii.append('')
    tileMap.append(ii)
def setTileonMap(x,y,value):
    tileMap[y][x] += value
def getTileonMap(x,y):
    return tileMap[y][x]

def rotateTable(table):
    return [[*r][::-1] for r in zip(*table)]

class Pieces:
    class piece:
        def __rotshape(self,rotid):
            if rotid == 0:
                return tuple(self.__shape)
            elif rotid == 1:
                return tuple(map(tuple, rotateTable(list(map(list, self.__shape)))))
            elif rotid == 2:
                return tuple(map(tuple, rotateTable(rotateTable(list(map(list, self.__shape))))))
            elif rotid == 3:
                return tuple(map(tuple, rotateTable(rotateTable(rotateTable(list(map(list, self.__shape)))))))
        def __makeRot(self,rotid):
            rot = pygame.sprite.Sprite()
            rot.image = pygame.image.load(f'images/{self.id}{rotid}.png').convert_alpha()
            rot.width = round(rot.image.get_width()/16)
            rot.height = round(rot.image.get_height()/16)
            rot.rect = rot.image.get_rect()
            rot.shape = self.__rotshape(rotid)
            return rot
        def __init__(self,id: str,rot0shape: tuple) -> None:
            self.id = id
            self.__shape = rot0shape
            self.rotations = (self.__makeRot(0),self.__makeRot(1),self.__makeRot(2),self.__makeRot(3))
            del self.__shape
            self.rotation = 0
            self.x = 4
            self.y = 0
        def getSprite(self) -> pygame.sprite.Sprite:
            return self.rotations[self.rotation]
        def rotate(self,dir):
            self.rotation = self.rotation+dir
            if self.rotation == -1:
                self.rotation = 3
            elif self.rotation == 4:
                self.rotation = 0
        def stamp(self):
            stamps.append(((thisPiece.getSprite().rect.x,thisPiece.getSprite().rect.y),thisPiece.getSprite()))
            iy = 0
            for y in self.getSprite().shape:
                ix = 0
                for x in y:
                    setTileonMap(self.x+ix,self.y+iy,x)
                    ix += 1
                iy += 1
    I = piece('I',(('I'),('I'),('I'),('I')))
    J = piece('J',(('','J'),('','J'),('J','J')))
    L = piece('L',(('L',''),('L',''),('L','L')))
    O = piece('O',(('O','O'),('O','O')))
    S = piece('S',(('','S','S'),('S','S','')))
    T = piece('T',(('T','T','T'),('','T','')))
    Z = piece('Z',(('Z','Z',''),('','Z','Z')))

def choosePiece():
    return random.choice([Pieces.I,Pieces.J,Pieces.L,Pieces.O,Pieces.S,Pieces.T,Pieces.Z])
def movePiece(sprite,x,y):
    sprite.rect.x = screen_width/2-82+2+(x*16)
    sprite.rect.y = 20+2+(y*16)

thisPieceG = pygame.sprite.Group()
nextUpFont = font.render('NEXT UP', False, line_colour)

frameRate = 10
gameTick = 0
speed = 2
thisPiece = choosePiece()
nextPiece = choosePiece()
score = 1000
stats = {'I':0,'J':0,'L':0,'O':0,'S':0,'T':0,'Z':0}

running = True
while running:
    keys = pygame.key.get_pressed()
    colided = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill(background_colour)
    pygame.draw.rect(screen, line_colour, pygame.Rect(screen_width/2-82, 20, 164, 324),  2)
    pygame.draw.rect(screen, line_colour, pygame.Rect(screen_width-20-68, 20, 68, 68),  2)
    pygame.draw.rect(screen, line_colour, pygame.Rect(screen_width-30-68, 20+68+20, 88, 32),  2)
    draw_grid()
    scoreTitleFont = font.render('SCORE', False, line_colour)
    scoreFont = font.render(str(score), False, line_colour)
    screen.blit(scoreTitleFont, (screen_width-85,2+20+68+2))
    screen.blit(scoreFont, (screen_width-54-scoreFont.get_width()/2,20+68+20+16+2-scoreFont.get_height()/2-1))
    screen.blit(nextUpFont, (screen_width-(54+nextUpFont.get_width()/2),2+2))
    screen.blit(nextPiece.rotations[0].image,(screen_width-54-nextPiece.rotations[0].image.get_width()/2,54-nextPiece.rotations[0].image.get_height()/2))
    draw_stamps(screen)

    if keys[pygame.K_LEFT] or keys[pygame.K_a] and thisPiece.x > 0:
        thisPiece.x -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d] and thisPiece.x < 10-thisPiece.getSprite().width:
        thisPiece.x += 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s] and (thisPiece.y < (20-thisPiece.getSprite().height) and not colided):
        thisPiece.y += 1
    if keys[pygame.K_q] or keys[pygame.K_RCTRL]:
        curWidth = thisPiece.getSprite().width
        thisPiece.rotate(-1)
        newWidth = thisPiece.getSprite().width
        if curWidth < newWidth and thisPiece.x + curWidth >= 10:
            thisPiece.x -= newWidth-curWidth
    if keys[pygame.K_e] or keys[pygame.K_KP0]:
        curWidth = thisPiece.getSprite().width
        thisPiece.rotate(1)
        newWidth = thisPiece.getSprite().width
        if curWidth < newWidth and thisPiece.x + curWidth >= 10:
            thisPiece.x -= newWidth-curWidth
        

    movePiece(thisPiece.getSprite(),thisPiece.x,thisPiece.y)
    thisPieceG.empty()
    thisPieceG.add(thisPiece.getSprite())
    thisPieceG.draw(screen)

    pygame.display.flip()
    clock.tick(frameRate)

    if thisPiece.y == (20-thisPiece.getSprite().height) or colided:
        thisPiece.stamp()
        stats[thisPiece.id] += 1
        thisPiece.rotation = 0
        thisPiece.x = 4
        thisPiece.y = 0
        thisPiece = nextPiece
        nextPiece = choosePiece()
    elif gameTick >= frameRate/speed:
        thisPiece.y += 1
        gameTick = 0
    else:
        gameTick += 1
else:
    print('crashed :(')
    ii = 0
    for row in tileMap:
        i = 0
        for x in row:
            if x == '':
                tileMap[ii][i] = ' '
            i += 1
        ii += 1
        print(row)