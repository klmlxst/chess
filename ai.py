import random
import chess

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def evaluate_board(board):
    if board.is_checkmate():
        if board.turn:
            return -99999
        else:
            return 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += val
            else:
                score -= val
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing_player:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_ai_move(board, difficulty):
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    if difficulty == 1:
        if random.random() < 0.5:
            return random.choice(legal_moves)
        depth = 1
    elif difficulty == 2:
        if random.random() < 0.2:
            return random.choice(legal_moves)
        depth = 2
    else:
        depth = 3

    best_move = None
    best_value = -float('inf') if board.turn == chess.WHITE else float('inf')

    moves = legal_moves
    random.shuffle(moves)

    for move in moves:
        board.push(move)
        board_val = minimax(board, depth - 1, -float('inf'), float('inf'), board.turn == chess.WHITE)
        board.pop()

        if board.turn == chess.WHITE:
            if board_val > best_value:
                best_value = board_val
                best_move = move
        else:
            if board_val < best_value:
                best_value = board_val
                best_move = move

    if best_move is None:
        best_move = random.choice(legal_moves)

    return best_move
