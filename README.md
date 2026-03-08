# Tina the Destroyer

One-screen local arcade game built with Python + Pygame.

<img width="1536" height="1024" alt="title" src="https://github.com/user-attachments/assets/3b5de0a0-223b-43cf-bb4b-8707a293e2f2" />

You control Tina near the bottom of the screen. Rats fall from above. Time your ground smash to squash them before they reach the bottom. Missed rats cost lives. Survive as long as possible and beat your best score.

## Controls

<img width="960" height="672" alt="image" src="https://github.com/user-attachments/assets/11db2d1d-7027-46fd-95ce-8bf95ac3996b" />
<img width="966" height="678" alt="image" src="https://github.com/user-attachments/assets/8ef23d97-9b82-47ea-85de-9e4e17e1191f" />
https://github.com/user-attachments/assets/ad44d684-724f-4075-8b46-88d51ed25a5a

- Title:
  - Any key: start
  - `Esc`: quit
- Gameplay:
  - `A` / `D` or Left / Right: move
  - `Space`: ground smash
  - `R`: restart immediately
  - `Esc`: quit
- Game Over:
  - `R` or `Enter`: restart
  - `Esc`: quit

## Installation

1. Install Python 3.
2. Install pygame:

```bash
pip install pygame
```

## Run

```bash
python main.py
```

## Expected Asset Filenames

Place these in `assets/`:

- `impact.png`
- `player_idle.png`
- `player_smash.png`
- `rat.png`
- `rat_squashed.png`
- `title.png`
- `miss.wav` or `miss.mp3`
- `smash.wav` or `punch.mp3` (also supports `smash.mp3` as extra fallback)
- `game_over.wav` or `game_over.mp3` (falls back to miss sound if missing)
- Background music:
  - `music_loop.mp3`
  - or typo variant `musinc_loop.mp3` (explicitly supported)

## Notes

- Missing images fall back to generated placeholders.
- Missing sounds are skipped safely.
- Best score is stored in `best_score.json`.
tina-the-destroyer
