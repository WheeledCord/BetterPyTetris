# Imports - on one line for unnecessary compactness
import pygame; from random import *; from pathlib import Path


# Window height and width varibles for easy tweaking
window_width = 1000
window_height = 1000

# Inits pygame and creates the window
pygame.init()
window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
clock = pygame.time.Clock()

# Map related definitions
lava_y = window_height - 50
starty = window_height / 2
startx = 50 - window_width

# player = pygame.sprite.Sprite()
# player.image = pygame.Surface((30, 30), pygame.SRCALPHA)
# player_size = 15
# pygame.draw.circle(player.image, (255, 0, 0), (player_size, player_size), player_size)
# player.rect = player.image.get_rect(center = (150, lava_y - player_size))


# Player related definitions
player = pygame.sprite.Sprite()
player_image = str(Path.cwd() / "images" / "I0.png")
player.image = pygame.image.load(player_image).convert_alpha()
player.rect = player.image.get_rect()
all_sprites = pygame.sprite.Group([player])


# Hides mouse cursor
pygame.mouse.set_visible(0)

# Gravity, velocity and other inits
y, vel_y = player.rect.bottom, 0
vel = 5
acceleration = 10
gravity = 0.25
inCollision = True

platforms = []

# Create rect function
def create_rect(r, g, b, topleftx, toplefty, width, height):
        thisrect = pygame.draw.rect(window, (r, g, b), (topleftx, toplefty, width, height))
        platforms.append(thisrect)

run = True
while run:
    clock.tick(100)
    acc_y = gravity
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()  

    # Jump code
    if keys[pygame.K_SPACE] or keys[pygame.K_UP] and inCollision == True:
        acc_y = -acceleration
        inCollision = False

    
    # Horizontal movement
    player.rect.centerx = (player.rect.centerx + (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * vel) % window_width
    
    # Allows player to change sprite during the game
    if keys[pygame.K_1]:
         player_image = str(Path.cwd() / "images" / "I0.png")
         player.image = pygame.image.load(player_image).convert_alpha()
    elif keys[pygame.K_2]:
         player_image = str(Path.cwd() / "images" / "I0.png")
         player.image = pygame.image.load(player_image).convert_alpha()
    elif keys[pygame.K_3]:
         player_image = str(Path.cwd() / "images" / "I0.png")
         player.image = pygame.image.load(player_image).convert_alpha()
              


    # Gravity
    vel_y += acc_y
    y += vel_y
    

    # Back to start platform if you touch lava
    if y > lava_y:
        player.rect.centerx = startx
        y = starty
        vel_y = 0
        acc_y = 0


    # Something that makes everything work
    player.rect.bottom = round(y)

    # Colour definitions for easy changing
    platform_colour = [168, 166, 165]
    lava_colour = 255, 102, 0
    sky_colour = 3, 198, 252

    # Fills bg with sky_colour
    window.fill((sky_colour))

    # Draws lava
    pygame.draw.rect(window, (lava_colour), (0, lava_y, window_width, 100))

    
    # Checks for collision and stops movement if collision is true
    if player.rect.collidelistall(platforms):
        vel_y = -0.5
        acc_y = -0.5
        inCollision = True

    

    # Draws a bunch of test platforms

    # MISC RANDOM PLATFORM #1
    create_rect(platform_colour[0], platform_colour[1], platform_colour[2], 450, starty - 300, 350, 25)

    # MISC RANDOM PLATFORM #2
    create_rect(platform_colour[0], platform_colour[1], platform_colour[2], 300, starty - 150, 500, 25)

    # MISC RANDOM PLATFORM #3
    create_rect(platform_colour[0], platform_colour[1], platform_colour[2], 150, starty, 650, 25)

    # START PLATFORM
    create_rect(255, 215, 0, 0, starty, 100, 25)
    
    # Draws all sprites
    all_sprites.draw(window)
    pygame.display.flip()

pygame.quit()
exit() 


'''
NOTES
When making moving platforms, make a random number for the platform outside of the loop then assign it to the rect during the loop to prevent it having a stroke.

'''