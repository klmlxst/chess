Chess desktop app (prototype).

Implemented:
- Local 2-player mode
- Play vs AI mode with 3 difficulty levels
- Move highlighting (legal moves + captures), last move + check highlight
- Pawn promotion picker
- Piece SVGs downloaded from the open `lichess` “alpha” set (stored in `assets/pieces/alpha/`)

How to run (Windows / Electron):
1. Open `c:/Work/School/JEBLAN/Chess` in a terminal.
2. Install dependencies:
   - `npm install`
3. Start the app:
   - `npm start`

Notes:
- Chess rules come from `chess.js`, loaded from `unpkg` at runtime (CDN).
- AI is a lightweight minimax (no Stockfish binary) tuned by depth + randomness to make
  `Easy/Medium/Hard` feel meaningfully different.
