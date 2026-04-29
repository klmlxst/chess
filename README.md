# Chess Desktop App

A fully functional, offline desktop chess game written in Python.

## Features
- **Local Multiplayer:** Play against a friend on the same computer.
- **Play vs AI:** Play against the computer with 3 difficulty levels (Easy, Medium, Hard).
- **Classic UI:** Clean and responsive UI with move highlighting (legal moves, captures), last move indicator, and check highlight.
- **Full Ruleset:** Supports castling, en passant, and pawn promotion.

## Installation & Running

1. **Install Python 3** (if you haven't already).
2. **Install dependencies:**
   ```bash
   pip install pygame chess
   ```
3. **Run the game:**
   ```bash
   python main.py
   ```

## Development
- `main.py` - Entry point and main menu.
- `game.py` - Core game loop, rendering, and move logic.
- `ai.py` - Minimax algorithm with alpha-beta pruning.
