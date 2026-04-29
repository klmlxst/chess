const el = {
  board: document.getElementById('board'),
  status: document.getElementById('status'),
  moveList: document.getElementById('moveList'),
  newGameBtn: document.getElementById('newGameBtn'),
  aiNewGameBtn: document.getElementById('aiNewGameBtn'),
  aiControls: document.getElementById('aiControls'),
  aiHumanColor: document.getElementById('aiHumanColor'),
  aiDifficulty: document.getElementById('aiDifficulty'),
  promotionModal: document.getElementById('promotionModal'),
};

const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

function isLightSquare(fileIndex, rank) {
  // In chess: a1 is dark. So "light" iff (fileIndex + rank) is even.
  return (fileIndex + rank) % 2 === 0;
}

function squareToIndices(square) {
  const fileIndex = files.indexOf(square[0]);
  const rank = Number(square[1]);
  return { fileIndex, rank };
}

function pieceSymbol(piece) {
  // chess.js piece: {type: 'p', color:'w'|'b'}
  if (!piece) return null;
  const letter = piece.type.toUpperCase();
  return (piece.color === 'w' ? 'w' : 'b') + letter;
}

function pieceFileName(piece) {
  const sym = pieceSymbol(piece); // e.g. wK
  if (!sym) return null;
  return `../assets/pieces/alpha/${sym}.svg`;
}

function formatTurn(game) {
  if (game.turn() === 'w') return 'White to move';
  return 'Black to move';
}

function fenForDebug(game) {
  // Useful if you later want to show FEN or save games.
  return game.fen();
}

// ---------------- AI (simple minimax + PST + noise) ----------------

const PST = {
  p: [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
  ],
  n: [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
  ],
  b: [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
  ],
  r: [
    0, 0, 0, 5, 5, 0, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
  ],
  q: [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
  ],
  k: [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
  ],
};

const PIECE_VALUE = { p: 100, n: 320, b: 330, r: 500, q: 900, k: 0 };

function evaluateFromSideToMove(chess) {
  // Positive means "side to move is better".
  const board = chess.board(); // 8x8, ranks 8..1
  let whiteScore = 0;
  let blackScore = 0;

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const p = board[r][c];
      if (!p) continue;
      const idx = r * 8 + c;
      const pstIdxForPiece = p.color === 'w' ? idx : (7 - r) * 8 + c;

      const base = PIECE_VALUE[p.type] ?? 0;
      const pst = PST[p.type]?.[pstIdxForPiece] ?? 0;
      const total = base + pst;

      if (p.color === 'w') whiteScore += total;
      else blackScore += total;
    }
  }

  let score = whiteScore - blackScore;

  // Add small mobility term to reduce "dumb" play.
  // chess.js: moves() depends on side-to-move.
  const mobility = chess.moves().length;
  score += (mobility - 16) * 2;

  // Convert to "perspective of side to move".
  return chess.turn() === 'w' ? score : -score;
}

function negamax(chess, depth, alpha, beta) {
  if (depth === 0 || chess.isGameOver()) return evaluateFromSideToMove(chess);

  let best = -Infinity;
  const moves = chess.moves({ verbose: true });

  // Simple move ordering: captures first.
  moves.sort((a, b) => {
    const ac = a.captured ? (PIECE_VALUE[a.captured] ?? 0) : 0;
    const bc = b.captured ? (PIECE_VALUE[b.captured] ?? 0) : 0;
    return bc - ac;
  });

  for (const m of moves) {
    const next = new chess.constructor(chess.fen());
    next.move({ from: m.from, to: m.to, promotion: m.promotion });
    const score = -negamax(next, depth - 1, -beta, -alpha);
    if (score > best) best = score;
    if (score > alpha) alpha = score;
    if (alpha >= beta) break;
  }

  return best;
}

async function chooseMove(chess, difficulty) {
  // difficulty -> search settings (aiming for "playable Elo-ish" differences).
  const cfg =
    difficulty === 'easy'
      ? { depth: 2, noise: 0.45, topN: 3, thinkMs: 140 }
      : difficulty === 'medium'
        ? { depth: 3, noise: 0.18, topN: 2, thinkMs: 240 }
        : { depth: 4, noise: 0.0, topN: 1, thinkMs: 600 };

  // Yield to UI.
  await new Promise((r) => setTimeout(r, 20));

  const moves = chess.moves({ verbose: true });
  if (!moves.length) return null;

  const start = Date.now();
  let scored = [];

  // Score each root move with minimax.
  for (const m of moves) {
    const next = new chess.constructor(chess.fen());
    next.move({ from: m.from, to: m.to, promotion: m.promotion });
    const score = -negamax(next, cfg.depth - 1, -Infinity, Infinity);
    scored.push({ move: m, score });

    if (Date.now() - start > cfg.thinkMs && difficulty !== 'hard') {
      // For easy/medium: cut off early to make it weaker.
      break;
    }
  }

  scored.sort((a, b) => b.score - a.score);
  const bestScore = scored[0].score;

  // Extract top-N; if something goes wrong, fallback to first.
  const top = scored.slice(0, Math.max(1, cfg.topN));

  // Noise/blunders: choose suboptimal move with some probability.
  if (cfg.noise > 0) {
    const r = Math.random();
    if (r < 1 - cfg.noise) {
      // choose the best
      return top[0].move;
    }
    // choose random among top-N
    return top[Math.floor(Math.random() * top.length)].move;
  }

  // Hard: deterministic best.
  return scored[0]?.move ?? null;
}

// ---------------- Game UI ----------------

let ChessLib = null;
let game = null;
let selectedSquare = null;
let legalMoves = []; // verbose move objects
let lastMove = null; // {from,to}
let aiMode = 'local'; // 'local' | 'ai'
let aiHumanColor = 'w'; // human side color
let aiDifficulty = 'medium';
let aiEngineColor = 'b'; // computed

let busyAi = false;
let awaitingPromotion = null; // { move: verboseMove } or null

function clearSelection() {
  selectedSquare = null;
  legalMoves = [];
}

function setStatus(text) {
  el.status.textContent = text;
}

function updateMoveList(moveHistory) {
  el.moveList.innerHTML = '';
  for (let i = 0; i < moveHistory.length; i++) {
    const item = document.createElement('li');
    item.textContent = moveHistory[i];
    el.moveList.appendChild(item);
  }
}

function drawBoard() {
  if (!game) return;

  const bottomColor = aiMode === 'ai' ? aiHumanColor : 'w'; // in local: keep white at bottom
  const flipped = bottomColor === 'b';

  const inCheckKingSquare = (() => {
    try {
      if (game.inCheck && game.inCheck()) {
        const side = game.turn();
        if (game.kingSquare) return game.kingSquare(side);
      }
    } catch {
      // Ignore
    }
    return null;
  })();

  const legalTargets = new Map(); // to -> move
  for (const m of legalMoves) legalTargets.set(m.to, m);

  const lastFrom = lastMove?.from ?? null;
  const lastTo = lastMove?.to ?? null;

  el.board.innerHTML = '';

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const displayRank = flipped ? 1 + r : 8 - r;
      const displayFile = flipped ? files[7 - c] : files[c];
      const square = `${displayFile}${displayRank}`;

      const { fileIndex } = squareToIndices(square);
      const light = isLightSquare(fileIndex, displayRank);

      const sq = document.createElement('div');
      sq.className = `sq ${light ? 'light' : 'dark'}`;
      sq.dataset.square = square;

      if (square === selectedSquare) sq.classList.add('sel');
      if (square === lastFrom || square === lastTo) sq.classList.add('last');
      if (inCheckKingSquare && square === inCheckKingSquare) sq.classList.add('in-check');

      const hintMove = legalTargets.get(square);
      if (hintMove) {
        const hint = document.createElement('div');
        hint.className = 'hint' + (hintMove.captured ? ' capture' : '');
        sq.appendChild(hint);
      }

      const piece = game.get(square);
      const img = document.createElement('img');
      if (piece) {
        img.className = 'piece';
        img.src = pieceFileName(piece);
        img.alt = piece.color + ' ' + piece.type;
      } else {
        img.style.display = 'none';
      }
      sq.appendChild(img);

      sq.addEventListener('click', () => onSquareClicked(square));
      el.board.appendChild(sq);
    }
  }
}

function updateStatusAndGameOver() {
  if (!game) return;

  let text = '';
  const turn = game.turn();

  if (game.isCheckmate && game.isCheckmate()) {
    text = `Checkmate. ${turn === 'w' ? 'Black' : 'White'} wins.`;
  } else if (game.isDraw && game.isDraw()) {
    text = `Draw.`;
  } else if (game.isStalemate && game.isStalemate()) {
    text = 'Stalemate. Draw.';
  } else if (game.isThreefoldRepetition && game.isThreefoldRepetition()) {
    text = 'Draw by repetition.';
  } else if (game.isGameOver && game.isGameOver()) {
    text = 'Game over.';
  } else {
    text = formatTurn(game);
    if (game.inCheck && game.inCheck()) text += ' (Check!)';
  }

  setStatus(text);
}

function pushMoveToHistoryList(san) {
  const list = el.moveList;
  // We store SAN strings as a simple list.
  if (!window.__moveHistory) window.__moveHistory = [];
  window.__moveHistory.push(san);
  updateMoveList(window.__moveHistory);
}

function onSquareClicked(square) {
  if (!game) return;
  if (busyAi) return;
  if (awaitingPromotion) return;

  // If AI mode, block human moves when it's AI's turn.
  if (aiMode === 'ai' && game.turn() !== aiHumanColor) return;
  if (game.isGameOver && game.isGameOver()) return;

  const piece = game.get(square);
  const moveFromSel = selectedSquare;

  if (!selectedSquare) {
    if (!piece) return;
    if (piece.color !== game.turn()) return;
    selectedSquare = square;
    legalMoves = game.moves({ square, verbose: true });
    drawBoard();
    return;
  }

  // Clicking on another own piece switches selection.
  if (piece && piece.color === game.turn()) {
    selectedSquare = square;
    legalMoves = game.moves({ square, verbose: true });
    drawBoard();
    return;
  }

  // Attempt a move to the clicked square.
  const move = legalMoves.find((m) => m.to === square);
  if (!move) {
    // Invalid destination: keep selection.
    clearSelection();
    drawBoard();
    return;
  }

  if (move.promotion) {
    // Need promotion choice for human.
    awaitingPromotion = { move };
    el.promotionModal.style.display = 'flex';
    drawBoard();
    return;
  }

  doMove(move);
}

function doMove(verboseMoveOrMoveObj) {
  // For verbose move objects from .moves({verbose:true})
  const move = verboseMoveOrMoveObj;
  const from = move.from;
  const to = move.to;

  // promotion may be undefined for non-promotion moves.
  const res = game.move({ from, to, promotion: move.promotion });
  if (!res) return;

  lastMove = { from, to };

  // Update move list with SAN.
  pushMoveToHistoryList(res.san);

  clearSelection();
  awaitingPromotion = null;
  el.promotionModal.style.display = 'none';

  // Render + status.
  drawBoard();
  updateStatusAndGameOver();

  // Trigger AI if needed.
  maybeTriggerAI();
}

async function maybeTriggerAI() {
  if (aiMode !== 'ai') return;
  if (!game) return;
  if (busyAi) return;

  if (game.isGameOver && game.isGameOver()) return;
  if (game.turn() !== aiEngineColor) return;

  busyAi = true;
  setStatus('AI is thinking...');

  try {
    const aiMove = await chooseMove(game, aiDifficulty);
    if (!aiMove) {
      setStatus('AI has no legal moves.');
      return;
    }

    // Add slight delay so user perceives move.
    await new Promise((r) => setTimeout(r, 80));
    doMove(aiMove);
  } finally {
    busyAi = false;
  }
}

function newGame() {
  window.__moveHistory = [];
  el.moveList.innerHTML = '';
  el.promotionModal.style.display = 'none';
  awaitingPromotion = null;
  busyAi = false;
  lastMove = null;
  clearSelection();

  game = new ChessLib.Chess();
  updateStatusAndGameOver();
  drawBoard();
  maybeTriggerAI();
}

function updateModeUI() {
  aiMode = document.querySelector('input[name="mode"]:checked').value;
  el.aiControls.style.display = aiMode === 'ai' ? 'flex' : 'none';
  if (aiMode === 'ai') {
    aiHumanColor = el.aiHumanColor.value;
    aiDifficulty = el.aiDifficulty.value;
    aiEngineColor = aiHumanColor === 'w' ? 'b' : 'w';
  }
  newGame();
}

// Promotion click handlers
for (const btn of document.querySelectorAll('.promo-btn')) {
  btn.addEventListener('click', () => {
    if (!awaitingPromotion) return;
    const prom = btn.dataset.prom;
    const mv = awaitingPromotion.move;
    doMove({ ...mv, promotion: prom });
  });
}

// Mode buttons
el.newGameBtn.addEventListener('click', newGame);
if (el.aiNewGameBtn) el.aiNewGameBtn.addEventListener('click', newGame);

document.querySelectorAll('input[name="mode"]').forEach((r) => {
  r.addEventListener('change', updateModeUI);
});

el.aiHumanColor.addEventListener('change', () => {
  aiHumanColor = el.aiHumanColor.value;
  aiEngineColor = aiHumanColor === 'w' ? 'b' : 'w';
});
el.aiDifficulty.addEventListener('change', () => {
  aiDifficulty = el.aiDifficulty.value;
});

// Boot
(async function boot() {
  try {
    setStatus('Loading chess rules...');
    const mod = await import('https://unpkg.com/chess.js/dist/esm/chess.js');
    ChessLib = mod;
    setStatus('Ready.');
    updateModeUI();
  } catch (e) {
    console.error(e);
    setStatus('Failed to load chess.js from CDN. Check internet access.');
  }
})();

// Expose for debug if needed.
window.__getFen = () => (game ? fenForDebug(game) : '');

