#import libraries
import pygame
import random
import os
from spritesheet import SpriteSheet
from enemy import Enemy
from pygame import mixer

pygame.init() #initialize pygame
mixer.init()


#game window dimensions
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

#create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Doodle Jump')

#set frame rate
clock = pygame.time.Clock()
FPS = 60

#load music and sounds
pygame.mixer.music.load('SFX/music.mp3')
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1, 0.0)

#game variables
GRAVITY = 1
MAX_PLATFORMS = 10
SCROLL_THRESH = 200
scroll = 0
bg_scroll = 0
game_over = False
score = 0
fade_counter = 0

#highscore file check
if os.path.exists('score.txt'):
    with open('score.txt', 'r') as file:
        high_score = int(file.read())
else:
    high_score = 0

# define colours
WHITE = (255,255,255)
BLACK = (0, 0, 0)
PANEL = (153, 217,234)

# define font
font_small = pygame.font.SysFont('Lucida Sans', 20)
font_big = pygame.font.SysFont('Lucida Sans', 24)

#load sfx
jump_sfx = pygame.mixer.Sound('sfx/jump.wav')
game_over_sfx = pygame.mixer.Sound('sfx/game_over.mp3')
monster_crash_sfx = pygame.mixer.Sound('sfx/monster-crash.mp3')
enemy_jump_sfx = pygame.mixer.Sound('sfx/jumponmonster.mp3')

#load images
bg_image = pygame.image.load('assets/BG.png').convert_alpha()
jumpy_image = pygame.image.load('assets/doodlejumpy.png').convert_alpha()
platform_image = pygame.image.load('assets/brick.png').convert_alpha()
#bird spritesheet
bird_sheet_img = pygame.image.load('assets/Enemies/BlueBird/Flying (32x32).png').convert_alpha()       
bird_sheet = SpriteSheet(bird_sheet_img)

#function for outputting text onto the screen
def draw_text(text,font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# function for drawing info panel
def draw_panel():
    pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 30))
    pygame.draw.line(screen, WHITE, (0, 30), (SCREEN_WIDTH, 30), 2)
    draw_text('SCORE: ' + str(score), font_small, WHITE, 0, 0)
    draw_text('HIGHSCORE: ' + str(high_score), font_small, WHITE, 210, 0)


#function for drawing the background
def draw_bg(bg_scroll):
    screen.blit(bg_image, (0,0 + bg_scroll))
    screen.blit(bg_image, (0, -850 + bg_scroll))

#player class
class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(jumpy_image, (65,60))
        self.width = 25 # for rect 25-27
        self.height = 50
        self.rect = pygame.Rect(0,0, self.width, self.height)
        self.rect.center = (x, y)
        self.flip = False
        self.direction = 0
        self.momentum = 0
        self.movement_speed = 0 #not used atm
        self.vel_y = 0


    def move(self):
        #reset variables
        scroll = 0
        dx = 0
        dy = 0

        #process keypresses
        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            #print(self.momentum)
            self.direction = -1
            dx -= 5 + self.momentum
            self.flip = True
            if(self.momentum < 5):
                self.momentum+= 0.5
        elif key[pygame.K_d]:
            self.direction = 1
            dx += 5 + self.momentum
            self.flip = False
            if(self.momentum <5):
                self.momentum += 0.5
        else:
            #if no keys pressed, gradually lower momentum
            if(self.momentum > 0):
                dx += (self.movement_speed * self.direction) + (self.momentum * self.direction)
                self.momentum -= 0.5

        #gravity
        self.vel_y += GRAVITY
        #print(GRAVITY)
        dy += self.vel_y

        #ensure player doesn't go off the edge of the screen (collision)
        if self.rect.left + dx < -10: #left side
            dx = SCREEN_WIDTH- 15     
        if self.rect.right + dx > SCREEN_WIDTH +15:#ight side
            dx = - SCREEN_WIDTH

        #check collision with platforms
        for platform in platform_group:
            #collision in the y direction
            if platform.rect.colliderect(self.rect.x, self.rect.y +dy, self.width, self.height):
                #check if above the platform
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0: #falling
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20
                        jump_sfx.play()

         #check jumping on enemy
        for enemy in enemy_group:
            #collision in the y direction
            if enemy.rect.colliderect(self.rect.x, self.rect.y +dy, self.width, self.height):
                #check if above the platform
                if self.rect.bottom < enemy.rect.centery +20:
                    if self.vel_y > 0: #falling
                        self.rect.bottom = enemy.rect.top
                        dy = 0
                        self.vel_y = -25
                        enemy_jump_sfx.play()
                      # collided_enemy = pygame.sprite.spritecollide(jumpy, enemy_group, False, pygame.sprite.collide_mask)
                        for enemy in enemy_group:
                        #  print('dead1')
                           enemy.dead = True

    

        #check collision with ground TEMP
        #if self.rect.bottom + dy > SCREEN_HEIGHT:
            #dy = 0
            #self.vel_y = -20

        #check if the player has bounced to the top of the screen
        if self.rect.top <= SCROLL_THRESH:
            #if player is jumping
            if self.vel_y <0:
                scroll = -dy


        #update rectangle position
        self.rect.x += dx
        self.rect.y += dy + scroll

        #update mask
        self.mask = pygame.mask.from_surface(self.image)

        return scroll


    def draw(self):
        # OG Flip Code screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y-10)) 
        if self.flip:
            screen.blit(pygame.transform.flip(self.image, True, False), (self.rect.right - self.image.get_width() +12, self.rect.y - 10))
        else:
            screen.blit(self.image, (self.rect.x - 12, self.rect.y-10)) #arguments draw image, draw rect at x y position
        
       #pygame.draw.rect(screen, WHITE, self.rect, 2)

#platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_image, (width, 30))
        self.moving = moving
        self.move_counter = random.randint(0,50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        #move platform side to side if it is a moving platform
        if self.moving == True:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed

        #change platform direction if it has moved fully or hit a wall
        if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.direction *= -1
            self.move_counter = 0

        #update platform's vertical position
        self.rect.y += scroll

        #check if platform has gone off the screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


#player instance
jumpy = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

#create sprite groups
platform_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

#create temporary platforms
#for p in range(MAX_PLATFORMS):
    #p_w = random.randint(40, 60)
    #p_x = random.randint(0, SCREEN_WIDTH - p_w)
    #p_y = p * random.randint(80, 120) 
    #platform = Platform(p_x, p_y, p_w)
    #platform_group.add(platform)

#create starting platform
platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT-50, 100, False)
platform_group.add(platform)

#game loop (NECESSARY TO RUN)
run = True
while run:
    
    clock.tick(FPS)

    if game_over == False:

        scroll = jumpy.move()

        #print(scroll)

        #draw background
        bg_scroll += scroll
        #print(bg_scroll)
        if bg_scroll >= 850:
            bg_scroll = 0
        draw_bg(bg_scroll)

        #generate platforms
        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, SCREEN_WIDTH-p_w)
            p_y = platform.rect.y - random.randint(80, 120)#in relation to y of last platform
            p_type = random.randint(1,2)
            if p_type == 1 and score > 2000:
                p_moving = True
            else:
                p_moving = False
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        #print(len(platform_group))


        #draw temporary scroll threshold
        #pygame.draw.line(screen, WHITE, (0, SCROLL_THRESH), (SCREEN_WIDTH, SCROLL_THRESH) )

        #update platforms
        platform_group.update(scroll)

        #generate enemies
        if len(enemy_group) == 0 and score >= 500:
            enemy = Enemy(SCREEN_WIDTH, 0,bird_sheet, 1.5)
            enemy_group.add(enemy)

        #update enemies
        enemy_group.update(scroll, SCREEN_WIDTH)

        #update score
        if scroll > 0:
            score += scroll
        
        #draw line at previous high score
        draw_text('HIGH SCORE', font_small, BLACK, SCREEN_WIDTH - 130, score- high_score + SCROLL_THRESH) 
        pygame.draw.line(screen, BLACK, (0, score - high_score + SCROLL_THRESH), (SCREEN_WIDTH, score - high_score + SCROLL_THRESH), 3)

        #draw sprites
        platform_group.draw(screen)
        jumpy.draw()
        enemy_group.draw(screen)

        #draw panel
        draw_panel()

        #check game over
        if jumpy.rect.top > SCREEN_HEIGHT+10:
            game_over_sfx.play()
            game_over = True
        #check for collision with enemies
        collided_enemies = pygame.sprite.spritecollide(jumpy, enemy_group, False)


        if collided_enemies: #if collision with any enemy
           if pygame.sprite.spritecollide(jumpy, enemy_group, False, pygame.sprite.collide_mask): #if sprite pixel collides with enemy
                if jumpy.vel_y < 0:
                    monster_crash_sfx.play()
                    game_over = True
              # elif jumpy.vel_y > 0:
                 #  for enemy in collided_enemies:
                      # if jumpy.rect.bottom >= enemy.rect.top -50:
                           #enemy.dead = True
                          # print('dead2')

                  # enemy_jump_sfx.play()

        #kill enemy once jumped on
        
          # for enemy in enemy_group:# Loop through all collided enemies
              # enemy.dead = True
         
        #if enemy.rect.colliderect(self.rect.x, self.rect.y +dy, self.width, self.height):
                #check if above the platform
              # if self.rect.bottom < enemy.rect.centery:
              #     if self.vel_y > 0: #falling
              #         self.rect.bottom = enemy.rect.top       

        #print(game_over)

    else: #game over screen
        if fade_counter < SCREEN_WIDTH:
          fade_counter += 5
          for y in range(0,6,2):
               pygame.draw.rect(screen, BLACK, (0, y * 100, fade_counter, 100))
               pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - fade_counter, (y+1) * 100, SCREEN_WIDTH, 100))
        else:
            
            #update high score
            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as file:
                    file.write(str(high_score))
            draw_text('GAME OVER!', font_big, WHITE, 130, 200)
            draw_text('SCORE: ' + str(score), font_big, WHITE, 130, 250)
            draw_text('HIGHSCORE: ' + str(high_score), font_big, WHITE, 100, 300)
            draw_text('PRESS SPACE TO PLAY AGAIN', font_big, WHITE, 30, 350)
            
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE]:
                #reset variables
                game_over = False
                score = 0
                scroll = 0
                fade_counter = 0
                #reposition jumpy
                jumpy.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
                #reset enemies
                enemy_group.empty()
                #reset platforms
                platform_group.empty()
                #create starting platform
                platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT-50, 100, False)
                platform_group.add(platform)


    #event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            #update high score
            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as file:
                    file.write(str(high_score))
            run = False

    #update display window
    pygame.display.update()
    
pygame.quit()