import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import os
import random

# --- VAE ARCHITECTURE (same as training) ---
class VAE(nn.Module):
    def __init__(self, input_dim=400, hidden_dim=128, latent_dim=32):
        super(VAE, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Latent space
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_var = nn.Linear(hidden_dim, latent_dim)
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid()
        )
    
    def encode(self, x):
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_var(h)
    
    def reparameterize(self, mu, log_var):
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z):
        return self.decoder(z)
    
    def forward(self, x):
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        return self.decode(z), mu, log_var

# --- LEVEL GENERATION ---
def generate_level_with_vae(model_path='vae_model_final.pth', device=None, level_num=5):
    """
    Generate a level using the trained VAE model.
    Returns level data in the format expected by the game.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load model
    model = VAE().to(device)
    
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded VAE model from {model_path}")
    except FileNotFoundError:
        print(f"Model file {model_path} not found. Using fallback generation.")
        return generate_fallback_level(level_num)
    except Exception as e:
        print(f"Error loading model: {e}. Using fallback generation.")
        return generate_fallback_level(level_num)
    
    model.eval()
    
    with torch.no_grad():
        # Generate a random latent vector
        z = torch.randn(1, 32).to(device)
        generated_level = model.decode(z)
        
        # Convert to level format
        level = [[' ' for _ in range(20)] for _ in range(20)]
        
        # Apply threshold to determine walls
        threshold = 0.5
        for i in range(20):
            for j in range(20):
                if generated_level[0][i * 20 + j] > threshold:
                    level[i][j] = 'W'
        
        # Post-process the level to ensure playability
        level = post_process_level(level)
        
        # Convert grid back to game format
        return convert_grid_to_game_format(level, level_num)

def convert_grid_to_game_format(grid, level_num):
    """
    Convert the 20x20 grid back to the game's level format
    """
    SCREEN_HEIGHT = 800
    ground_y = SCREEN_HEIGHT - 100
    base_length = 1600 + (level_num - 1) * 200  # Progressive level length
    
    # Scale back to game coordinates
    scale_x = base_length / 20.0
    scale_y = SCREEN_HEIGHT / 20.0
    
    platforms = extract_horizontal_platforms(grid, scale_x, scale_y, ground_y)
    enemies = []
    coins = []
    decorations = []
    
    # Extract enemies from grid
    for i in range(20):
        for j in range(20):
            if grid[i][j] == 'E':
                game_x = int(j * scale_x)
                game_y = int(i * scale_y)
                enemy_type = random.choice(['slime', 'bee'])
                enemies.append((game_x, game_y, enemy_type))
    
    # Extract coins from grid
    for i in range(20):
        for j in range(20):
            if grid[i][j] == 'C':
                game_x = int(j * scale_x)
                game_y = int(i * scale_y)
                coins.append((game_x, game_y))
    
    # Add some decorations
    if random.random() < 0.7:
        decoration_x = random.randint(200, int(base_length - 200))
        decorations.append(('Sprites/Tiles/Default/bush.png', decoration_x, ground_y - 48, 64, 48))
    
    # Create flag at the end
    flag = (base_length - 100, ground_y - 64)
    
    return {
        'ground_y': ground_y,
        'ground_length': base_length,
        'platforms': platforms,
        'enemies': enemies,
        'coins': coins,
        'decorations': decorations,
        'flag': flag
    }

def extract_horizontal_platforms(grid, scale_x, scale_y, ground_y):
    platforms = []
    for i in range(20):
        j = 0
        while j < 20:
            if grid[i][j] == 'W':
                start = j
                while j + 1 < 20 and grid[i][j + 1] == 'W':
                    j += 1
                end = j
                length = end - start + 1
                if length >= 2:  # Only consider runs of 2+ tiles
                    game_x = int(start * scale_x)
                    game_y = int(i * scale_y)
                    game_w = int(length * scale_x)
                    game_h = 40
                    platform_type = "stone" if game_y < ground_y - 150 else "wood"
                    platforms.append((game_x, game_y, game_w, game_h, platform_type))
            j += 1
    return platforms

def post_process_level(level):
    """
    Post-process the generated level to ensure it's playable.
    """
    # Ensure there's a ground floor
    for x in range(20):
        level[19][x] = 'W'
    
    # Ensure there's a starting platform
    for x in range(3, 7):
        level[18][x] = 'W'
    
    # Add some coins
    coin_positions = []
    for _ in range(random.randint(3, 8)):
        x = random.randint(1, 18)
        y = random.randint(5, 17)
        if level[y][x] == ' ' and level[y+1][x] == 'W':  # Coin above a platform
            level[y][x] = 'C'
            coin_positions.append((x, y))
    
    # Add some enemies
    enemy_positions = []
    for _ in range(random.randint(2, 5)):
        x = random.randint(1, 18)
        y = random.randint(5, 17)
        if level[y][x] == ' ' and level[y+1][x] == 'W':  # Enemy on a platform
            level[y][x] = 'E'
            enemy_positions.append((x, y))
    
    # Ensure there's a path to the end
    # Add some platforms if the level is too sparse
    wall_count = sum(row.count('W') for row in level)
    if wall_count < 50:  # Too few walls
        for _ in range(random.randint(5, 10)):
            x = random.randint(1, 18)
            y = random.randint(10, 16)
            length = random.randint(2, 5)
            for dx in range(length):
                if x + dx < 19:
                    level[y][x + dx] = 'W'
    
    return level

def generate_fallback_level(level_num=5):
    """
    Generate a fallback level if VAE is not available.
    """
    SCREEN_HEIGHT = 800
    ground_y = SCREEN_HEIGHT - 100
    base_length = 1600 + (level_num - 1) * 200
    
    platforms = [
        (100, ground_y - 120, 150, 40, "wood"),
        (400, ground_y - 200, 150, 40, "stone"),
        (700, ground_y - 150, 120, 40, "wood"),
        (1000, ground_y - 250, 100, 40, "stone"),
        (1300, ground_y - 180, 120, 40, "wood"),
        (1600, ground_y - 220, 100, 40, "stone"),
    ]
    
    enemies = [
        (300, ground_y - 48, "slime"),
        (800, ground_y - 48, "bee"),
        (1400, ground_y - 48, "slime"),
    ]
    
    coins = [
        (200, ground_y - 60), (500, ground_y - 160), (800, ground_y - 110),
        (1100, ground_y - 210), (1400, ground_y - 140), (1700, ground_y - 180)
    ]
    
    decorations = [
        ('Sprites/Tiles/Default/bush.png', 350, ground_y - 48, 64, 48),
        ('Sprites/Tiles/Default/bush.png', 1200, ground_y - 48, 64, 48),
    ]
    
    flag = (base_length - 100, ground_y - 64)
    
    return {
        'ground_y': ground_y,
        'ground_length': base_length,
        'platforms': platforms,
        'enemies': enemies,
        'coins': coins,
        'decorations': decorations,
        'flag': flag
    }

def generate_multiple_levels(num_levels=5, model_path='vae_model_final.pth'):
    """
    Generate multiple levels and save them to files.
    """
    levels = []
    
    for i in range(num_levels):
        print(f"Generating level {i+1}/{num_levels}...")
        level_data = generate_level_with_vae(model_path, level_num=i+1)
        levels.append(level_data)
        
        # Save individual level
        with open(f'generated_level_{i+1}.json', 'w') as f:
            json.dump(level_data, f, indent=2)
    
    # Save all levels
    with open('all_generated_levels.json', 'w') as f:
        json.dump(levels, f, indent=2)
    
    print(f"Generated {num_levels} levels and saved to files.")

def visualize_level(level):
    """
    Visualize a level grid for debugging
    """
    symbols = {'W': '█', 'C': '●', 'E': '☠', ' ': ' '}
    print("Level visualization:")
    print("=" * 42)
    for i, row in enumerate(level):
        print(f"{i:2d} |", end=" ")
        for tile in row:
            print(symbols.get(tile, tile), end="")
        print(" |")
    print("=" * 42)
    print("   ", end="")
    for i in range(20):
        print(f"{i%10}", end="")
    print()

def test_level_generation():
    """
    Test the level generation system
    """
    print("Testing VAE level generation...")
    
    # Try to generate a level
    level_data = generate_level_with_vae()
    
    print("Generated level data:")
    print(f"Ground Y: {level_data['ground_y']}")
    print(f"Ground Length: {level_data['ground_length']}")
    print(f"Platforms: {len(level_data['platforms'])}")
    print(f"Enemies: {len(level_data['enemies'])}")
    print(f"Coins: {len(level_data['coins'])}")
    
    # Save test level
    with open('test_level.json', 'w') as f:
        json.dump(level_data, f, indent=2)
    
    print("Test level saved to test_level.json")

if __name__ == "__main__":
    test_level_generation() 