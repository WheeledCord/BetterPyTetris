from tkinter import W
from turtle import position
from supabase import create_client, Client
import threading
import pygame
import sys

url = "https://vqlylnfgxeimreedequm.supabase.co"
try:
    with open('supabase_key.txt','r') as f:
        key = f.read()
        f.close()
except FileNotFoundError:
    raise FileNotFoundError('Supabase Key file not found, If you aren\'t Solomon or Vincent, you shouldn\'t be running the source :)')
supabase: Client = create_client(url, key)

# Inits
pygame.init()
pygame.font.init()
clock = pygame.time.Clock()

font = pygame.font.Font('assets/nintendo-nes-font.ttf', 24)

## Create window
display = pygame.display.set_mode((768,672))
pygame.display.set_caption('PyTetris - Leaderboard')

BG = pygame.image.load('assets/bg.png')

data = {}
exit = False

def dataloop():
    global data
    while not exit:
        response = (
            supabase.table("leaderboard")
            .select("*")
            .execute()
        ).model_dump()['data']
        new_data = {}
        for row in response:
            new_data[row['username']] = [row['score'],row['lines']]
            if len([player for player in players if player.name == row['username']]) == 0:
                Player(row['username'])
        data = new_data
        # time.sleep(1)

def lerp(v1, v2, t):
    return v1 * (1 - t) + v2 * t

def clamp(v, m, M):
    return min(max(v,m),M)

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

def zeroify(v,l):
    if v < 0:
        return str(v)[0]+(l-(len(str(v)))) * '0' + str(v)[1:]
    return (l-len(str(v))) * '0' + str(v)

def ordinal(n):
    if str(n)[-1] == '1':
        return str(n) + 'st'
    elif str(n)[-1] == '2':
        return str(n) + 'nd'
    elif str(n)[-1] == '3':
        return str(n) + 'rd'
    else:
        return str(n) + 'th'

players = []

total_lerp_frames = 10
class Player:
    def __init__(self,name):
        self.name = name
        self.score = 0
        self.old_score = 0
        self.lines = 0
        self.old_lines = 0
        self.position = 0
        self.old_position = 0
        self.lerp_frames = 0
        self.hue = 0
        self.old_hue = 0
        players.append(self)

    def update_values(self):
        if self.name not in data.keys():
            players.remove(self)
            return
        if self.lerp_frames == 0:
            self.old_score = self.score
            self.old_lines = self.lines
            self.old_hue = self.hue
            pass
            self.score = data[self.name][0]
            self.lines = data[self.name][1]
            self.hue = 300
            if self.lines >= 10:
                self.hue = overflowNum((self.lines//10)*12,360)

    def set_position(self, p):
        if self.lerp_frames > total_lerp_frames-2:
            self.old_position = self.position
        self.position = p

    def draw(self):
        if self.position < 10:
            y = round(
                lerp(
                    191+30*self.old_position,
                    191+30*self.position,
                    (1/total_lerp_frames)*self.lerp_frames
                    )
                )
            place = font.render(
                ordinal(zeroify(self.position+1,2)).upper(),
                False,
                hsv_to_rgb(clamp(round(lerp(self.old_hue,self.hue,(1/total_lerp_frames)*self.lerp_frames)),0,360),41,100,100))
            display.blit(place,(66,y))
            name = font.render(
                self.name.upper(),
                False,
                hsv_to_rgb(clamp(round(lerp(self.old_hue,self.hue,(1/total_lerp_frames)*self.lerp_frames)),0,360),41,100,100))
            display.blit(name,(247,y))
            score = font.render(
                zeroify(round(lerp(self.old_score,self.score,(1/total_lerp_frames)*self.lerp_frames)),6),
                False,
                hsv_to_rgb(clamp(round(lerp(self.old_hue,self.hue,(1/total_lerp_frames)*self.lerp_frames)),0,360),41,100,100))
            display.blit(score,(404,y))
            lines = font.render(
                zeroify(round(lerp(self.old_lines,self.lines,(1/total_lerp_frames)*self.lerp_frames)),3),
                False,
                hsv_to_rgb(clamp(round(lerp(self.old_hue,self.hue,(1/total_lerp_frames)*self.lerp_frames)),0,360),41,100,100))
            display.blit(lines,(633,y))
        
        self.lerp_frames += 1
        if self.lerp_frames >= total_lerp_frames:
            self.lerp_frames = 0

def mainloop():
    global exit
    while not exit:  
        try:
            clock.tick(60)
            for event in pygame.event.get():
                # Detect window closed
                if event.type == pygame.QUIT:
                    exit = True
                    pygame.quit()
                    sys.exit()

            display.blit(BG,(0,0))
            for player in players:
                player.update_values()
            unsorted_players = {}
            for player in players:
                unsorted_players[player.name] = (player.score,player.lines)
            sorted_players = list(dict(sorted(unsorted_players.items(), reverse=True, key=lambda item: item[1])))
            for player in players:
                player.set_position(sorted_players.index(player.name))
            for player in players:
                player.draw()
            pygame.display.flip()
        except KeyboardInterrupt:
            exit = True
            pygame.quit()
            sys.exit()

if __name__ =="__main__":
    data_thread = threading.Thread(target = dataloop)
    data_thread.start()
    mainloop()