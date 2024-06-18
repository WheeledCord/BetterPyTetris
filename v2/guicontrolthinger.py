import pygame
import json

pygame.init()

# Screen dimensions
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Configure Controls")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# Define font
font = pygame.font.Font(None, 36)

# Define initial controls
controls = {
    'left': pygame.K_a,
    'right': pygame.K_d,
    'down': pygame.K_s,
    'hard_down': pygame.K_SPACE,
    'hold': pygame.K_h,
    'left_rot': pygame.K_q,
    'right_rot': pygame.K_e,
    'pause': pygame.K_RETURN,
    'quit': pygame.K_ESCAPE,
    'ghost': pygame.K_g,
    'scale1': pygame.K_1,
    'scale2': pygame.K_2,
    'scale3': pygame.K_3,
    'scale4': pygame.K_4,
    'vol_up': pygame.K_KP_PLUS,
    'vol_down': pygame.K_KP_MINUS,
    'mute': pygame.K_0
}

# Button class
class Button:
    def __init__(self, text, x, y, width, height, action):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.color = GRAY

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = font.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Create buttons for each control
buttons = []
button_width = 200
button_height = 40
start_y = 50
gap = 50

controls_names = list(controls.keys())

for i, control in enumerate(controls_names):
    button = Button(f"{control}: {pygame.key.name(controls[control])}",
                    (SCREEN_WIDTH - button_width) // 2,
                    start_y + i * gap,
                    button_width,
                    button_height,
                    control)
    buttons.append(button)

# Save button
save_button = Button("Save", (SCREEN_WIDTH - button_width) // 2, start_y + len(buttons) * gap, button_width, button_height, "save")

# Function to handle button click
def handle_button_click(button):
    global waiting_for_key
    if button.action == "save":
        with open("controls_config.json", "w") as f:
            json.dump({k: pygame.key.name(v) for k, v in controls.items()}, f)
        print("Controls saved to controls_config.json")
    else:
        waiting_for_key = button.action

waiting_for_key = None
running = True
while running:
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for button in buttons:
                if button.is_clicked(pos):
                    handle_button_click(button)
            if save_button.is_clicked(pos):
                handle_button_click(save_button)
        elif event.type == pygame.KEYDOWN and waiting_for_key:
            controls[waiting_for_key] = event.key
            for button in buttons:
                if button.action == waiting_for_key:
                    button.text = f"{waiting_for_key}: {pygame.key.name(event.key)}"
            waiting_for_key = None

    for button in buttons:
        button.draw()
    save_button.draw()

    pygame.display.flip()

pygame.quit()
