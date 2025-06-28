# MUSTAFA SUPER BROS 🎮

A 2D platformer game with AI-generated levels using Variational Autoencoders (VAE).

## Quick Start 🚀

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Game**:
   ```bash
   python mustafa_super_bros.py
   ```

## Controls 🎯

- **Movement**: Arrow Keys or WASD
- **Jump**: Up Arrow, W, or Spacebar
- **Restart**: R (when game over)
- **Quit**: Close window

## Features ✨

- **5 Playable Characters**: Beige, Green, Pink, Purple, Yellow
- **AI-Generated Levels**: VAE model creates unique levels
- **Sound Effects**: Full audio experience
- **Progressive Difficulty**: Levels get harder as you advance
- **Score System**: Collect coins and defeat enemies

## Game Structure 📁

```
mustafa_super_bros.py    # Main game
vae_sample.py           # AI level generation
vae_model_final.pth     # Trained AI model
Sounds/                 # Audio files
Sprites/               # Graphics
```

## How It Works 🤖

- **Levels 1-6**: Hand-crafted levels with increasing difficulty
- **Levels 7+**: AI-generated using the VAE model
- **Fallback**: If AI model fails, uses simple procedural generation

## Troubleshooting 🔧

- **Missing sprites/sounds**: Ensure all files are in the correct directories
- **AI not working**: Game will use fallback generation automatically
- **Performance issues**: Reduce screen resolution in the code

## Credits 🙏

- **Sprites**: Kenney's Platformer Pack
- **Sounds**: Kenney's Sound Pack
- **AI**: PyTorch VAE implementation

---

**Enjoy playing MUSTAFA SUPER BROS!** 🎉 