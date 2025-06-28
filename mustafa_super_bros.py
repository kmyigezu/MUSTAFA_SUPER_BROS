import pygame
import sys
import os
import random
import json
from vae_sample import generate_level_with_vae

# --- CONFIG ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
PLAYER_SIZE = 48
ENEMY_SIZE = 48
COIN_SIZE = 32
BG_COLOR = (135, 206, 235)
TITLE = "MUSTAFA SUPER BROS"

# --- SOUND MAPPING ---
SOUND_MAP = {
    'jump': 'Sounds/sfx_jump.ogg',
    'long_jump': 'Sounds/sfx_jump-high.ogg',
    'game_over': 'Sounds/sfx_disappear.ogg',
    'coin': 'Sounds/sfx_coin.ogg',
    'enemy_bump': 'Sounds/sfx_bump.ogg',
    'hurt': 'Sounds/sfx_hurt.ogg',
    'magic': 'Sounds/sfx_magic.ogg',
    'select': 'Sounds/sfx_select.ogg',
}

# --- CHARACTER OPTIONS ---
CHARACTER_OPTIONS = [
    ('Beige', 'Sprites/Characters/Default/character_beige_front.png'),
    ('Green', 'Sprites/Characters/Default/character_green_front.png'),
    ('Pink', 'Sprites/Characters/Default/character_pink_front.png'),
    ('Purple', 'Sprites/Characters/Default/character_purple_front.png'),
    ('Yellow', 'Sprites/Characters/Default/character_yellow_front.png'),
]

# --- PLATFORM TYPES ---
PLATFORM_TYPES = {
    'grass': 'Sprites/Tiles/Default/terrain_grass_block.png',
    'stone': 'Sprites/Tiles/Default/terrain_stone_block.png',
    'sand': 'Sprites/Tiles/Default/terrain_sand_block.png',
    'wood': 'Sprites/Tiles/Default/bridge_logs.png',
}

# --- INIT ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# --- LOAD SOUNDS ---
sounds = {}
for key, path in SOUND_MAP.items():
    try:
        sounds[key] = pygame.mixer.Sound(path)
    except Exception:
        sounds[key] = None

# --- LOAD BACKGROUND ---
try:
    background = pygame.image.load('Sprites/Backgrounds/Default/background_color_hills.png')
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill(BG_COLOR)

# --- PLATFORM CLASS ---
class Platform:
    def __init__(self, x, y, width, height, platform_type="grass"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.platform_type = platform_type
        try:
            sprite_path = PLATFORM_TYPES.get(platform_type, PLATFORM_TYPES['grass'])
            self.sprite = pygame.image.load(sprite_path)
            self.sprite = pygame.transform.scale(self.sprite, (width, height))
        except:
            self.sprite = pygame.Surface((width, height))
            self.sprite.fill((100, 200, 100))
    def draw(self, screen, camera_x):
        screen.blit(self.sprite, (self.x - camera_x, self.y))

# --- PLAYER CLASS ---
class Player:
    def __init__(self, x, y, char_img_path):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_power = -15
        self.speed = 5
        self.gravity = 0.8
        self.facing_right = True
        self.sprites = self.load_character_sprites(char_img_path)
        self.current_sprite = 0
        self.animation_timer = 0
        self.state = "idle"
    def load_character_sprites(self, char_img_path):
        sprites = []
        char_name = char_img_path.split('/')[-1].replace('_front.png', '')
        base_path = char_img_path.replace('_front.png', '')
        sprite_files = [
            f'{base_path}_idle.png',
            f'{base_path}_walk_a.png',
            f'{base_path}_walk_b.png',
            f'{base_path}_jump.png'
        ]
        for sprite_file in sprite_files:
            try:
                img = pygame.image.load(sprite_file)
                img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
                sprites.append(img)
            except:
                img = pygame.image.load(char_img_path)
                img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
                sprites.append(img)
        return sprites
    def update(self, platforms):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
            self.facing_right = False
            if self.on_ground:
                self.state = "walk"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
            self.facing_right = True
            if self.on_ground:
                self.state = "walk"
        else:
            self.vel_x = 0
            if self.on_ground:
                self.state = "idle"
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            self.state = "jump"
            if sounds['jump']:
                sounds['jump'].play()
        if not self.on_ground:
            self.vel_y += self.gravity
            if self.vel_y > 0:
                self.state = "fall"
            self.vel_y = min(self.vel_y, 20)
        self.x += self.vel_x
        self.y += self.vel_y
        self.on_ground = False
        for platform in platforms:
            if self.check_collision(platform):
                if self.vel_y > 0:  # Falling
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping up
                    self.y = platform.y + platform.height
                    self.vel_y = 0
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.current_sprite = (self.current_sprite + 1) % 2 + 1 if self.state == "walk" else 0
        if self.y > SCREEN_HEIGHT:
            return False
        return True
    def check_collision(self, obj):
        return (self.x < obj.x + obj.width and
                self.x + self.width > obj.x and
                self.y < obj.y + obj.height and
                self.y + self.height > obj.y)
    def draw(self, screen, camera_x):
        if self.state == "idle":
            sprite = self.sprites[0]
        elif self.state == "walk":
            sprite = self.sprites[self.current_sprite]
        elif self.state == "jump" or self.state == "fall":
            sprite = self.sprites[3]
        else:
            sprite = self.sprites[0]
        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
        screen.blit(sprite, (self.x - camera_x, self.y))

# --- ENEMY CLASS ---
class Enemy:
    def __init__(self, x, y, enemy_type='slime'):
        self.x = x
        self.y = y
        self.width = ENEMY_SIZE
        self.height = ENEMY_SIZE
        self.vel_x = -1
        self.vel_y = 0
        self.gravity = 0.8
        self.enemy_type = enemy_type
        try:
            if enemy_type == 'slime':
                sprite_path = 'Sprites/Enemies/Default/slime_normal_rest.png'
            elif enemy_type == 'bee':
                sprite_path = 'Sprites/Enemies/Default/bee_rest.png'
            else:
                sprite_path = 'Sprites/Enemies/Default/slime_normal_rest.png'
            self.sprite = pygame.image.load(sprite_path)
            self.sprite = pygame.transform.scale(self.sprite, (ENEMY_SIZE, ENEMY_SIZE))
        except:
            self.sprite = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
            self.sprite.fill((255, 0, 0))
    def update(self, platforms):
        self.vel_y += self.gravity
        self.x += self.vel_x
        self.y += self.vel_y
        for platform in platforms:
            if self.check_collision(platform):
                # Only invert velocity if colliding from the side
                if self.vel_y == 0:
                    self.vel_x *= -1
                if self.vel_y > 0:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.y = platform.y + platform.height
                    self.vel_y = 0
    def check_collision(self, obj):
        # Shrink enemy collision box to 50% of sprite, centered
        shrink = 0.5
        ex = self.x + self.width * (1 - shrink) / 2
        ey = self.y + self.height * (1 - shrink) / 2
        ew = self.width * shrink
        eh = self.height * shrink
        return (obj.x < ex + ew and
                obj.x + obj.width > ex and
                obj.y < ey + eh and
                obj.y + obj.height > ey)
    def draw(self, screen, camera_x):
        screen.blit(self.sprite, (self.x - camera_x, self.y))

# --- COIN CLASS ---
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = COIN_SIZE
        self.height = COIN_SIZE
        self.collected = False
        self.animation_timer = 0
        try:
            self.sprite = pygame.image.load('Sprites/Tiles/Default/coin_gold.png')
            self.sprite = pygame.transform.scale(self.sprite, (COIN_SIZE, COIN_SIZE))
        except:
            self.sprite = pygame.Surface((COIN_SIZE, COIN_SIZE))
            self.sprite.fill((255, 255, 0))
    def update(self):
        self.animation_timer += 1
    def draw(self, screen, camera_x):
        if not self.collected:
            angle = (self.animation_timer * 5) % 360
            rotated = pygame.transform.rotate(self.sprite, angle)
            screen.blit(rotated, (self.x - camera_x, self.y))
    def check_collision(self, player):
        return (not self.collected and
                player.x < self.x + self.width and
                player.x + player.width > self.x and
                player.y < self.y + self.height and
                player.y + player.height > self.y)

# --- FLAG CLASS ---
class Flag:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 64
        self.height = 64
        try:
            self.sprite = pygame.image.load('Sprites/Tiles/Default/flag_blue_a.png')
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
        except:
            self.sprite = pygame.Surface((self.width, self.height))
            self.sprite.fill((0, 0, 255))
    def draw(self, screen, camera_x):
        screen.blit(self.sprite, (self.x - camera_x, self.y))

# --- COIN BLOCK CLASS ---
class CoinBlock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        self.has_coin = True
        try:
            self.sprite_active = pygame.image.load('Sprites/Tiles/Default/block_coin_active.png')
            self.sprite_active = pygame.transform.scale(self.sprite_active, (self.width, self.height))
            self.sprite_empty = pygame.image.load('Sprites/Tiles/Default/block_coin.png')
            self.sprite_empty = pygame.transform.scale(self.sprite_empty, (self.width, self.height))
        except:
            self.sprite_active = pygame.Surface((self.width, self.height)); self.sprite_active.fill((255, 255, 0))
            self.sprite_empty = pygame.Surface((self.width, self.height)); self.sprite_empty.fill((200, 200, 0))
    def check_collision(self, player):
        px, py, pw, ph = player.x, player.y, player.width, player.height
        if (px + pw > self.x and px < self.x + self.width and
            py + ph > self.y and py + ph < self.y + 10 and  # Only from below
            player.vel_y < 0):
            return True
        return False
    def solid_collision(self, obj):
        return (obj.x < self.x + self.width and obj.x + obj.width > self.x and obj.y < self.y + self.height and obj.y + obj.height > self.y)
    def draw(self, screen, camera_x):
        sprite = self.sprite_active if self.has_coin else self.sprite_empty
        screen.blit(sprite, (self.x - camera_x, self.y))

# --- LOCK, KEY, EXCLAMATION BLOCK CLASSES ---
class Lock:
    def __init__(self, x, y, lock_type):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        self.lock_type = lock_type
        try:
            self.sprite_locked = pygame.image.load(f'Sprites/Tiles/Default/{lock_type}.png')
            self.sprite_locked = pygame.transform.scale(self.sprite_locked, (self.width, self.height))
            self.sprite_unlocked = pygame.image.load('Sprites/Tiles/Default/block_plank.png')
            self.sprite_unlocked = pygame.transform.scale(self.sprite_unlocked, (self.width, self.height))
        except:
            self.sprite_locked = pygame.Surface((self.width, self.height)); self.sprite_locked.fill((0, 0, 255))
            self.sprite_unlocked = pygame.Surface((self.width, self.height)); self.sprite_unlocked.fill((150, 100, 50))
        self.unlocked = False
    def check_collision(self, player):
        px, py, pw, ph = player.x, player.y, player.width, player.height
        return (px < self.x + self.width and px + pw > self.x and py < self.y + self.height and py + ph > self.y)
    def solid_collision(self, obj):
        # Solid block collision (AABB)
        return (obj.x < self.x + self.width and obj.x + obj.width > self.x and obj.y < self.y + self.height and obj.y + obj.height > self.y)
    def draw(self, screen, camera_x):
        sprite = self.sprite_unlocked if self.unlocked else self.sprite_locked
        screen.blit(sprite, (self.x - camera_x, self.y))

class Key:
    def __init__(self, x, y, key_type):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.key_type = key_type
        try:
            self.sprite = pygame.image.load(f'Sprites/Tiles/Default/{key_type}.png')
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
        except:
            self.sprite = pygame.Surface((self.width, self.height)); self.sprite.fill((255, 255, 0))
        self.collected = False
    def check_collision(self, player):
        px, py, pw, ph = player.x, player.y, player.width, player.height
        return (px < self.x + self.width and px + pw > self.x and py < self.y + self.height and py + ph > self.y)
    def draw(self, screen, camera_x):
        if not self.collected:
            screen.blit(self.sprite, (self.x - camera_x, self.y))

class ExclamationBlock:
    def __init__(self, x, y, key_type):
        self.x = x
        self.y = y
        self.width = 48
        self.height = 48
        self.key_type = key_type
        self.has_key = True
        try:
            self.sprite_active = pygame.image.load('Sprites/Tiles/Default/block_exclamation_active.png')
            self.sprite_active = pygame.transform.scale(self.sprite_active, (self.width, self.height))
            self.sprite_empty = pygame.image.load('Sprites/Tiles/Default/block_exclamation.png')
            self.sprite_empty = pygame.transform.scale(self.sprite_empty, (self.width, self.height))
        except:
            self.sprite_active = pygame.Surface((self.width, self.height)); self.sprite_active.fill((255, 255, 0))
            self.sprite_empty = pygame.Surface((self.width, self.height)); self.sprite_empty.fill((200, 200, 0))
        self.key = Key(self.x + 8, self.y - 32, f'key_{key_type.split("_")[-1]}')
    def check_collision(self, player):
        px, py, pw, ph = player.x, player.y, player.width, player.height
        if (px + pw > self.x and px < self.x + self.width and
            py + ph > self.y and py + ph < self.y + 10 and  # Only from below
            player.vel_y < 0):
            return True
        return False
    def solid_collision(self, obj):
        return (obj.x < self.x + self.width and obj.x + obj.width > self.x and obj.y < self.y + self.height and obj.y + obj.height > self.y)
    def draw(self, screen, camera_x):
        sprite = self.sprite_active if self.has_key else self.sprite_empty
        screen.blit(sprite, (self.x - camera_x, self.y))
        if not self.has_key:
            self.key.draw(screen, camera_x)

# --- SNAIL ENEMY CLASS ---
class Snail(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, enemy_type='snail')
        try:
            self.sprite_walk = pygame.image.load('Sprites/Enemies/Default/snail_walk_a.png')
            self.sprite_walk = pygame.transform.scale(self.sprite_walk, (ENEMY_SIZE, ENEMY_SIZE))
            self.sprite_shell = pygame.image.load('Sprites/Enemies/Default/snail_shell.png')
            self.sprite_shell = pygame.transform.scale(self.sprite_shell, (ENEMY_SIZE, ENEMY_SIZE))
        except:
            self.sprite_walk = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE)); self.sprite_walk.fill((150, 75, 0))
            self.sprite_shell = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE)); self.sprite_shell.fill((200, 200, 200))
        self.in_shell = False
    def update(self, platforms):
        if not self.in_shell:
            super().update(platforms)
    def draw(self, screen, camera_x):
        sprite = self.sprite_shell if self.in_shell else self.sprite_walk
        screen.blit(sprite, (self.x - camera_x, self.y))

# --- CHARACTER SELECT ---
def character_select_screen():
    font_title = pygame.font.SysFont('Arial', 72, bold=True)
    font_sub = pygame.font.SysFont('Arial', 36)
    font_label = pygame.font.SysFont('Arial', 28)
    char_imgs = []
    for name, path in CHARACTER_OPTIONS:
        try:
            img = pygame.image.load(path)
            img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
        except Exception:
            img = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
            img.fill((200, 200, 200))
        char_imgs.append((name, img))
    selected = None
    while selected is None:
        screen.blit(background, (0, 0))
        title_surf = font_title.render(TITLE, True, (30, 30, 30))
        screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 60))
        sub_surf = font_sub.render("Choose your character", True, (60, 60, 60))
        screen.blit(sub_surf, (SCREEN_WIDTH//2 - sub_surf.get_width()//2, 160))
        spacing = 60
        total_width = len(char_imgs) * PLAYER_SIZE + (len(char_imgs)-1) * spacing
        start_x = SCREEN_WIDTH//2 - total_width//2
        y = 300
        mouse = pygame.mouse.get_pos()
        for i, (name, img) in enumerate(char_imgs):
            x = start_x + i * (PLAYER_SIZE + spacing)
            rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
            if rect.collidepoint(mouse):
                pygame.draw.rect(screen, (255, 200, 0), rect.inflate(12, 12), 4)
            screen.blit(img, (x, y))
            label = font_label.render(name, True, (30, 30, 30))
            screen.blit(label, (x + PLAYER_SIZE//2 - label.get_width()//2, y + PLAYER_SIZE + 10))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, (name, img) in enumerate(char_imgs):
                    x = start_x + i * (PLAYER_SIZE + spacing)
                    rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
                    if rect.collidepoint(event.pos):
                        selected = i
                        if sounds['select']:
                            sounds['select'].play()
        pygame.display.flip()
        clock.tick(FPS)
    return CHARACTER_OPTIONS[selected][1]

# --- KEY OBJECT FOR POP-OUT ---
class FallingKey:
    def __init__(self, x, y, key_type):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.key_type = key_type
        self.vel_y = 0
        self.collected = False
        try:
            self.sprite = pygame.image.load(f'Sprites/Tiles/Default/{key_type}.png')
            self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
        except:
            self.sprite = pygame.Surface((self.width, self.height)); self.sprite.fill((255, 255, 0))
    def update(self, platforms, locks):
        if self.collected:
            return
        self.vel_y += 0.8  # gravity
        self.y += self.vel_y
        # Check for landing on platform or lock
        for obj in platforms + locks:
            if (self.x + self.width > obj.x and self.x < obj.x + obj.width and
                self.y + self.height > obj.y and self.y + self.height - obj.y < 20):
                self.y = obj.y - self.height
                self.vel_y = 0
    def draw(self, screen, camera_x):
        if not self.collected:
            screen.blit(self.sprite, (self.x - camera_x, self.y))
    def check_collision(self, player):
        return (not self.collected and
                player.x < self.x + self.width and
                player.x + player.width > self.x and
                player.y < self.y + self.height and
                player.y + player.height > self.y)

# --- LEVEL GENERATION ---
def generate_level(level_num, player_keys=None):
    platforms = []
    enemies = []
    coins = []
    decorations = []
    coin_blocks = []
    water_tiles = []
    lava_tiles = []
    bridges = []
    locks = []
    exclamation_blocks = []
    keys = []
    BLOCK_GAP = 24
    BLOCK_SIZE = 48
    lock_colors = ['blue', 'green', 'red', 'yellow']
    lock_type = None
    key_type = None
    if level_num >= 4:
        color = random.choice(lock_colors)
        lock_type = f'lock_{color}'
        key_type = f'key_{color}'
    if level_num == 1:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 1600
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        p1 = Platform(400, ground_y - 120, 150, 40, "wood")
        p2 = Platform(900, ground_y - 200, 150, 40, "stone")
        platforms.extend([p1, p2])
        enemies.append(Enemy(600, ground_y - ENEMY_SIZE, "slime"))
        coins.extend([Coin(300, ground_y - 60), Coin(800, ground_y - 160), Coin(1200, ground_y - 60)])
        # decorations only
        decorations.extend([
            Decoration(350, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(1200, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
    elif level_num == 2:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 1800
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        p1 = Platform(300, ground_y - 120, 150, 40, "wood")
        p2 = Platform(700, ground_y - 200, 150, 40, "stone")
        p3 = Platform(1200, ground_y - 150, 150, 40, "wood")
        p4 = Platform(1500, ground_y - 250, 100, 40, "stone")
        platforms.extend([p1, p2, p3, p4])
        water_tiles.append((900, ground_y, 120, 40, True))
        enemies.append(Enemy(600, ground_y - ENEMY_SIZE, "slime"))
        enemies.append(Enemy(1300, ground_y - ENEMY_SIZE, "snail"))
        coins.extend([Coin(400, ground_y - 60), Coin(1000, ground_y - 160), Coin(1400, ground_y - 60), Coin(1600, ground_y - 200)])
        decorations.extend([
            Decoration(500, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(1400, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
    elif level_num == 3:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 2000
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        p1 = Platform(400, ground_y - 120, 150, 40, "wood")
        p2 = Platform(800, ground_y - 200, 150, 40, "stone")
        p3 = Platform(1200, ground_y - 250, 100, 40, "wood")
        p4 = Platform(1600, ground_y - 180, 120, 40, "stone")
        platforms.extend([p1, p2, p3, p4])
        water_tiles.append((1100, ground_y, 120, 40, True))
        enemies.append(Enemy(600, ground_y - ENEMY_SIZE, "snail"))
        enemies.append(Enemy(1300, ground_y - ENEMY_SIZE, "bee"))
        enemies.append(Enemy(1700, ground_y - ENEMY_SIZE, "slime"))
        coins.extend([Coin(400, ground_y - 60), Coin(900, ground_y - 160), Coin(1400, ground_y - 60), Coin(1800, ground_y - 200)])
        decorations.extend([
            Decoration(500, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(1500, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
    elif level_num == 4:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 2200
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        platforms.append(Platform(300, ground_y - 120, 120, 40, "wood"))
        platforms.append(Platform(700, ground_y - 200, 120, 40, "stone"))
        platforms.append(Platform(1100, ground_y - 250, 100, 40, "wood"))
        platforms.append(Platform(1500, ground_y - 180, 120, 40, "stone"))
        platforms.append(Platform(1900, ground_y - 220, 100, 40, "wood"))
        water_tiles.append((600, ground_y, 120, 40, True))
        locks.append((1400, ground_y - 100, lock_type))
        enemies.append(Enemy(900, ground_y - ENEMY_SIZE, "snail"))
        coins.extend([Coin(350, ground_y - 60), Coin(800, ground_y - 160), Coin(1300, ground_y - 60), Coin(1700, ground_y - 200), Coin(2100, ground_y - 60)])
        decorations.extend([
            Decoration(350, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(1200, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
        # Add more reachable platforms for level 4+
        platforms.append(Platform(600, 400, 120, 40, "stone"))
        platforms.append(Platform(1000, 350, 120, 40, "wood"))
        platforms.append(Platform(1400, 300, 120, 40, "stone"))
    elif level_num == 5:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 2400
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        platforms.append(Platform(400, ground_y - 120, 150, 40, "wood"))
        platforms.append(Platform(900, ground_y - 200, 150, 40, "stone"))
        platforms.append(Platform(1400, ground_y - 250, 100, 40, "wood"))
        platforms.append(Platform(1800, ground_y - 180, 120, 40, "stone"))
        platforms.append(Platform(2100, ground_y - 220, 100, 40, "wood"))
        water_tiles.append((700, ground_y, 120, 40, True))
        locks.append((1600, ground_y - 100, lock_type))
        enemies.append(Enemy(600, ground_y - ENEMY_SIZE, "snail"))
        enemies.append(Enemy(1300, ground_y - ENEMY_SIZE, "bee"))
        coins.extend([Coin(400, ground_y - 60), Coin(900, ground_y - 160), Coin(1400, ground_y - 60), Coin(1800, ground_y - 200), Coin(2200, ground_y - 60)])
        decorations.extend([
            Decoration(500, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(2000, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
    elif level_num == 6:
        ground_y = SCREEN_HEIGHT - 100
        ground_length = 2600
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        platforms.append(Platform(400, ground_y - 120, 150, 40, "wood"))
        platforms.append(Platform(900, ground_y - 200, 150, 40, "stone"))
        platforms.append(Platform(1400, ground_y - 250, 100, 40, "wood"))
        platforms.append(Platform(1800, ground_y - 180, 120, 40, "stone"))
        platforms.append(Platform(2300, ground_y - 220, 100, 40, "wood"))
        water_tiles.append((1200, ground_y, 120, 40, True))
        locks.append((1800, ground_y - 100, lock_type))
        enemies.append(Enemy(600, ground_y - ENEMY_SIZE, "snail"))
        enemies.append(Enemy(1300, ground_y - ENEMY_SIZE, "bee"))
        enemies.append(Enemy(2000, ground_y - ENEMY_SIZE, "slime"))
        coins.extend([Coin(400, ground_y - 60), Coin(900, ground_y - 160), Coin(1400, ground_y - 60), Coin(1800, ground_y - 200), Coin(2400, ground_y - 60)])
        decorations.extend([
            Decoration(500, ground_y - 48, 'Sprites/Tiles/Default/mushroom_brown.png', 48, 48),
            Decoration(2200, ground_y - 48, 'Sprites/Tiles/Default/mushroom_red.png', 48, 48),
        ])
    else:
        from vae_sample import generate_level_with_vae
        level_data = generate_level_with_vae(level_num=level_num)
        ground_y = level_data['ground_y']
        ground_length = level_data['ground_length']
        platforms.append(Platform(0, ground_y, ground_length, 100, "grass"))
        for platform_data in level_data['platforms']:
            x, y, w, h, platform_type = platform_data
            platforms.append(Platform(x, y, w, h, platform_type))
        for enemy_data in level_data['enemies']:
            x, y, enemy_type = enemy_data
            enemies.append(Enemy(x, y, enemy_type))
        for coin_data in level_data['coins']:
            x, y = coin_data
            coins.append(Coin(x, y))
        for decoration_data in level_data['decorations']:
            sprite_path, x, y, w, h = decoration_data
            decorations.append(Decoration(x, y, sprite_path, w, h))
        flag_x, flag_y = level_data['flag']
        flag = Flag(flag_x, flag_y)
        return platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys
    flag = Flag(ground_length - 100, ground_y - 64)

    # After adding water tiles, split any platform that overlaps with water horizontally at the same y
    new_platforms = []
    for p in platforms:
        overlap = False
        for wx, wy, ww, wh, _ in water_tiles:
            if p.y == wy and p.x < wx + ww and p.x + p.width > wx:
                overlap = True
                # Left segment (if any)
                if p.x < wx:
                    new_platforms.append(Platform(p.x, p.y, wx - p.x, p.height, p.platform_type))
                # Right segment (if any)
                if p.x + p.width > wx + ww:
                    new_platforms.append(Platform(wx + ww, p.y, (p.x + p.width) - (wx + ww), p.height, p.platform_type))
                break
        if not overlap:
            new_platforms.append(p)
    platforms = new_platforms

    # Place blocks above platforms, always centered, never stacked or overlapped
    block_platforms = [p for p in platforms if p.platform_type in ('stone', 'wood') and p.width >= 48]
    block_platforms.sort(key=lambda p: (p.y, p.x))  # deterministic order
    ex_block_placed = False
    for p in block_platforms:
        block_y = p.y - 72 - BLOCK_GAP - 8  # Add 8px gap above platform
        if block_y <= 0:
            continue
        if lock_type is not None and not ex_block_placed:
            # Place both blocks side by side if possible
            if p.width >= 96:
                start_x = p.x + p.width // 2 - 48
                coin_blocks.append((start_x, block_y))
                exclamation_blocks.append((start_x + BLOCK_SIZE, block_y, key_type))
                ex_block_placed = True
                continue
            else:
                # Only exclamation block, centered
                block_x = p.x + p.width // 2 - 24
                exclamation_blocks.append((block_x, block_y, key_type))
                ex_block_placed = True
                continue
        # Otherwise, only coin block, centered
        block_x = p.x + p.width // 2 - 24
        coin_blocks.append((block_x, block_y))
    return platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys

# --- MAIN GAME LOOP ---
def main():
    # Character selection
    char_img_path = character_select_screen()
    
    # Set starting level
    current_level = 1
    
    score = 0
    coins_collected = 0
    player_keys = set()
    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
    player = Player(100, 400, char_img_path)
    camera_x = 0
    running = True
    game_over = False
    level_completed = False
    game_beaten = False  # New state for game completion
    font = pygame.font.Font(None, 36)
    instructions_font = pygame.font.Font(None, 24)
    
    try:
        btn_left = pygame.image.load('Sprites/Tiles/Default/sign_left.png')
        btn_left = pygame.transform.scale(btn_left, (80, 80))
    except:
        btn_left = pygame.Surface((80, 80)); btn_left.fill((100, 100, 100))
    try:
        btn_right = pygame.image.load('Sprites/Tiles/Default/sign_right.png')
        btn_right = pygame.transform.scale(btn_right, (80, 80))
    except:
        btn_right = pygame.Surface((80, 80)); btn_right.fill((100, 100, 100))
    try:
        btn_exit = pygame.image.load('Sprites/Tiles/Default/sign_exit.png')
        btn_exit = pygame.transform.scale(btn_exit, (80, 80))
    except:
        btn_exit = pygame.Surface((80, 80)); btn_exit.fill((100, 100, 100))
    key_collected_popup_timer = 0
    key_collected_popup_text = None
    coin_block_objs = []
    ex_block_objs = []
    falling_key_obj = None
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # FULL RESET of current level state
                    coins_collected = 0
                    player_keys = set()
                    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
                    player = Player(100, 400, char_img_path)
                    camera_x = 0
                    game_over = False
                    level_completed = False
                    game_beaten = False
                    coin_block_objs = []
                    ex_block_objs = []
                    falling_key_obj = None
                    key_collected_popup_timer = 0
                    key_collected_popup_text = None
                elif not game_over and not level_completed and not game_beaten:
                    if event.key == pygame.K_0 or (pygame.K_1 <= event.key <= pygame.K_9):
                        coin_block_objs = []
                        ex_block_objs = []
                        falling_key_obj = None
        if not game_over and not level_completed and not game_beaten:
            if not coin_block_objs:
                coin_block_objs = [CoinBlock(x, y) for x, y in coin_blocks]
            if not ex_block_objs:
                ex_block_objs = [ExclamationBlock(x, y, ex_type) for x, y, ex_type in exclamation_blocks]
            # Coin block state change
            for cb in coin_block_objs:
                if cb.has_coin and cb.check_collision(player):
                    cb.has_coin = False
                    score += 100
                    coins_collected += 1
                    if sounds['coin']:
                        sounds['coin'].play()
            # Coin collection
            for coin in coins:
                if coin.check_collision(player):
                    coin.collected = True
                    score += 100
                    coins_collected += 1
                    if sounds['coin']:
                        sounds['coin'].play()
            # Exclamation block state change
            for ex in ex_block_objs:
                if ex.has_key and ex.check_collision(player):
                    ex.has_key = False
                    # Spawn falling key above exclamation block
                    if falling_key_obj is None:
                        falling_key_obj = FallingKey(ex.x + ex.width//2 - 16, ex.y - 32, ex.key_type)
            # Update falling key
            if falling_key_obj:
                lock_objs = [Lock(x, y, lock_type) for x, y, lock_type in locks]
                falling_key_obj.update(platforms, lock_objs)
                if falling_key_obj.check_collision(player):
                    falling_key_obj.collected = True
                    player_keys.add(falling_key_obj.key_type)
                    key_collected_popup_timer = 60
                    key_collected_popup_text = 'Key collected!'
            # Key collection from exclamation block (legacy, for safety)
            for ex in ex_block_objs:
                if not ex.has_key and not ex.key.collected and ex.key.check_collision(player):
                    ex.key.collected = True
                    player_keys.add(ex.key.key_type)
                    key_collected_popup_timer = 60
                    key_collected_popup_text = 'Key collected!'
            alive = player.update(platforms)
            for enemy in enemies:
                enemy.update(platforms)
            for coin in coins:
                coin.update()
            for enemy in enemies:
                if player.check_collision(enemy):
                    game_over = True
                    if sounds['hurt']:
                        sounds['hurt'].play()
            coins = [c for c in coins if not c.collected]
            camera_x = max(0, player.x - SCREEN_WIDTH // 2)
            if player.check_collision(flag):
                level_completed = True
                # Check if this was level 10 (game completion)
                if current_level == 10:
                    game_beaten = True
            # Game over if player falls off the map (even after flag)
            if not alive or player.y > SCREEN_HEIGHT:
                game_over = True
                if sounds['hurt']:
                    sounds['hurt'].play()
        screen.blit(background, (0, 0))
        for platform in platforms:
            platform.draw(screen, camera_x)
        for coin in coins:
            coin.draw(screen, camera_x)
        for enemy in enemies:
            enemy.draw(screen, camera_x)
        player.draw(screen, camera_x)
        flag.draw(screen, camera_x)
        for decoration in decorations:
            decoration.draw(screen, camera_x)
        # Draw water tiles (fill vertically)
        for x, y, w, h, top in water_tiles:
            # Draw top tile
            try:
                sprite_top = pygame.image.load('Sprites/Tiles/Default/water_top.png')
                sprite_top = pygame.transform.scale(sprite_top, (w, h))
            except:
                sprite_top = pygame.Surface((w, h)); sprite_top.fill((0, 100, 255))
            screen.blit(sprite_top, (x - camera_x, y))
            # Fill below with water.png
            fill_y = y + h
            try:
                sprite_fill = pygame.image.load('Sprites/Tiles/Default/water.png')
                sprite_fill = pygame.transform.scale(sprite_fill, (w, h))
            except:
                sprite_fill = pygame.Surface((w, h)); sprite_fill.fill((0, 100, 255))
            while fill_y < SCREEN_HEIGHT:
                screen.blit(sprite_fill, (x - camera_x, fill_y))
                fill_y += h
        # Draw lava tiles (fill vertically)
        for x, y, w, h, top in lava_tiles:
            # Draw top tile
            try:
                sprite_top = pygame.image.load('Sprites/Tiles/Default/lava_top.png')
                sprite_top = pygame.transform.scale(sprite_top, (w, h))
            except:
                sprite_top = pygame.Surface((w, h)); sprite_top.fill((255, 80, 0))
            screen.blit(sprite_top, (x - camera_x, y))
            # Fill below with lava.png
            fill_y = y + h
            try:
                sprite_fill = pygame.image.load('Sprites/Tiles/Default/lava.png')
                sprite_fill = pygame.transform.scale(sprite_fill, (w, h))
            except:
                sprite_fill = pygame.Surface((w, h)); sprite_fill.fill((255, 80, 0))
            while fill_y < SCREEN_HEIGHT:
                screen.blit(sprite_fill, (x - camera_x, fill_y))
                fill_y += h
        # Draw coin blocks
        for cb in coin_block_objs:
            cb.draw(screen, camera_x)
        # Draw locks (make solid)
        lock_objs = [Lock(x, y, lock_type) for x, y, lock_type in locks]
        for lock in lock_objs:
            lock.draw(screen, camera_x)
        # Draw exclamation blocks
        for ex in ex_block_objs:
            ex.draw(screen, camera_x)
        # Draw falling key
        if falling_key_obj and not falling_key_obj.collected:
            falling_key_obj.draw(screen, camera_x)
        # Draw HUD (bottom left)
        hud_bg = pygame.Surface((320, 110), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 120))
        screen.blit(hud_bg, (10, SCREEN_HEIGHT - 120))
        level_text = font.render(f"LEVEL {current_level}", True, (255,255,255))
        screen.blit(level_text, (20, SCREEN_HEIGHT - 110))
        score_text = font.render(f"Score: {score}", True, (255,255,255))
        screen.blit(score_text, (20, SCREEN_HEIGHT - 80))
        coins_text = font.render(f"Coins: {coins_collected}", True, (255,255,255))
        screen.blit(coins_text, (20, SCREEN_HEIGHT - 50))
        
        # Draw controls/instructions (bottom right)
        instructions = [
            "Arrow Keys or WASD: Move",
            "Space/Up: Jump",
            "Collect all coins to win!"
        ]
        for i, instruction in enumerate(instructions):
            text = instructions_font.render(instruction, True, (255,255,255))
            screen.blit(text, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 100 + i * 20))
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0,0,0))
            screen.blit(overlay, (0,0))
            font_large = pygame.font.Font(None, 96)
            font_small = pygame.font.Font(None, 36)
            game_over_text = font_large.render("GAME OVER", True, (255,0,0))
            restart_text = font_small.render("Press R to restart", True, (255,255,255))
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        elif game_beaten:
            # Game completion celebration screen
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,0))
            screen.blit(overlay, (0,0))
            
            # Main celebration text
            font_celebration = pygame.font.Font(None, 80)  # Reduced from 120 to 80
            celebration_text = font_celebration.render("YOU BEAT MUSTAFA SUPER BROS", True, (255,0,0))
            screen.blit(celebration_text, (SCREEN_WIDTH//2 - celebration_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
            
            # "Play again!!" button
            font_play_again = pygame.font.Font(None, 48)
            play_again_text = font_play_again.render("Play again!!", True, (255,255,255))
            play_again_rect = play_again_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            
            # Check for mouse hover and click
            mouse = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()[0]
            
            if play_again_rect.collidepoint(mouse):
                # Highlight on hover
                pygame.draw.rect(screen, (255,255,0), play_again_rect.inflate(20, 10), 3)
                if click:
                    # Return to character select
                    char_img_path = character_select_screen()
                    current_level = 1
                    score = 0
                    coins_collected = 0
                    player_keys = set()
                    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
                    player = Player(100, 400, char_img_path)
                    camera_x = 0
                    game_over = False
                    level_completed = False
                    game_beaten = False
            
            screen.blit(play_again_text, play_again_rect)
        elif level_completed:
            popup_w, popup_h = 400, 260
            popup_x = SCREEN_WIDTH//2 - popup_w//2
            popup_y = SCREEN_HEIGHT//2 - popup_h//2
            popup = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
            popup.fill((30, 30, 30, 230))
            screen.blit(popup, (popup_x, popup_y))
            popup_font = pygame.font.Font(None, 48)
            popup_text = popup_font.render("LEVEL COMPLETED!", True, (255,255,0))
            screen.blit(popup_text, (SCREEN_WIDTH//2 - popup_text.get_width()//2, popup_y + 30))
            btn_y = popup_y + 120
            btn_left_rect = pygame.Rect(popup_x + 30, btn_y, 80, 80)
            btn_exit_rect = pygame.Rect(popup_x + popup_w//2 - 40, btn_y, 80, 80)
            btn_right_rect = pygame.Rect(popup_x + popup_w - 110, btn_y, 80, 80)
            screen.blit(btn_left, btn_left_rect)
            screen.blit(btn_exit, btn_exit_rect)
            screen.blit(btn_right, btn_right_rect)
            mouse = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()[0]
            # Left button (previous level)
            if btn_left_rect.collidepoint(mouse):
                pygame.draw.rect(screen, (255,255,0), btn_left_rect, 3)
                if click and current_level > 1:
                    current_level -= 1
                    coins_collected = 0
                    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
                    player = Player(100, 400, char_img_path)
                    camera_x = 0
                    game_over = False
                    level_completed = False
                    game_beaten = False
            # Right button (next level)
            if btn_right_rect.collidepoint(mouse):
                pygame.draw.rect(screen, (255,255,0), btn_right_rect, 3)
                if click:
                    current_level += 1
                    coins_collected = 0
                    score += 500
                    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
                    player = Player(100, 400, char_img_path)
                    camera_x = 0
                    game_over = False
                    level_completed = False
                    game_beaten = False
            # Exit button (home/character select)
            if btn_exit_rect.collidepoint(mouse):
                pygame.draw.rect(screen, (255,255,0), btn_exit_rect, 3)
                if click:
                    char_img_path = character_select_screen()
                    current_level = 1
                    score = 0
                    coins_collected = 0
                    player_keys = set()
                    platforms, enemies, coins, flag, decorations, coin_blocks, water_tiles, lava_tiles, bridges, locks, exclamation_blocks, keys = generate_level(current_level, player_keys)
                    player = Player(100, 400, char_img_path)
                    camera_x = 0
                    game_over = False
                    level_completed = False
                    game_beaten = False
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

# Add Decoration class
class Decoration:
    def __init__(self, x, y, sprite_path, w=48, h=48):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        try:
            self.sprite = pygame.image.load(sprite_path)
            self.sprite = pygame.transform.scale(self.sprite, (w, h))
        except:
            self.sprite = pygame.Surface((w, h))
            self.sprite.fill((0, 255, 0))
    def draw(self, screen, camera_x):
        screen.blit(self.sprite, (self.x - camera_x, self.y))

if __name__ == "__main__":
    main() 