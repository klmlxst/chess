import pygame
import chess
import os
import ai
import time

SQUARE_SIZE = 80
WIDTH = SQUARE_SIZE * 8
HEIGHT = SQUARE_SIZE * 8

COLOR_LIGHT = (238, 238, 210)
COLOR_DARK = (118, 150, 86)
COLOR_HIGHLIGHT = (186, 202, 68)
COLOR_POSSIBLE_MOVE = (0, 0, 0, 50)
COLOR_CHECK = (220, 50, 50)

piece_images = {}

def load_images():
    pieces = ['bP', 'bR', 'bN', 'bB', 'bQ', 'bK', 'wP', 'wR', 'wN', 'wB', 'wQ', 'wK']
    for p in pieces:
        path = os.path.join('assets', 'pieces', 'alpha_png', f'{p}.png')
        img = pygame.image.load(path)
        img = pygame.transform.smoothscale(img, (SQUARE_SIZE, SQUARE_SIZE))
        piece_images[p] = img

def piece_to_name(piece):
    if not piece:
        return None
    color = 'w' if piece.color == chess.WHITE else 'b'
    pt = piece.symbol().upper()
    return f"{color}{pt}"

def draw_board(screen, board, selected_square, last_move):
    for r in range(8):
        for c in range(8):
            color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
            rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)

    if last_move:
        for sq in [last_move.from_square, last_move.to_square]:
            c = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, COLOR_HIGHLIGHT, rect)

    if selected_square is not None:
        c = chess.square_file(selected_square)
        r = 7 - chess.square_rank(selected_square)
        rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, rect)

    if board.is_check():
        k_sq = board.king(board.turn)
        if k_sq is not None:
            c = chess.square_file(k_sq)
            r = 7 - chess.square_rank(k_sq)
            rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, COLOR_CHECK, rect)

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            c = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            name = piece_to_name(piece)
            if name in piece_images:
                screen.blit(piece_images[name], (c * SQUARE_SIZE, r * SQUARE_SIZE))

def draw_possible_moves(screen, board, selected_square):
    if selected_square is None:
        return
    moves = [m for m in board.legal_moves if m.from_square == selected_square]
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for move in moves:
        to_sq = move.to_square
        c = chess.square_file(to_sq)
        r = 7 - chess.square_rank(to_sq)
        center = (c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + SQUARE_SIZE // 2)
        if board.piece_at(to_sq):
            pygame.draw.circle(surface, COLOR_POSSIBLE_MOVE, center, SQUARE_SIZE // 2, 5)
        else:
            pygame.draw.circle(surface, COLOR_POSSIBLE_MOVE, center, SQUARE_SIZE // 6)
    screen.blit(surface, (0, 0))

def run_game(mode, difficulty=1):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()

    load_images()
    board = chess.Board()

    selected_square = None
    last_move = None
    running = True

    while running:
        is_human_turn = True
        if mode == "ai" and board.turn == chess.BLACK:
            is_human_turn = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return

            if event.type == pygame.MOUSEBUTTONDOWN and is_human_turn:
                x, y = event.pos
                c = x // SQUARE_SIZE
                r = y // SQUARE_SIZE
                sq = chess.square(c, 7 - r)

                if selected_square is None:
                    piece = board.piece_at(sq)
                    if piece and piece.color == board.turn:
                        selected_square = sq
                else:
                    move = None
                    for m in board.legal_moves:
                        if m.from_square == selected_square and m.to_square == sq:
                            move = m
                            if move.promotion is None and board.piece_at(selected_square).piece_type == chess.PAWN:
                                if chess.square_rank(sq) == 0 or chess.square_rank(sq) == 7:
                                    move.promotion = chess.QUEEN
                            break

                    if move:
                        board.push(move)
                        last_move = move
                        selected_square = None
                    else:
                        piece = board.piece_at(sq)
                        if piece and piece.color == board.turn:
                            selected_square = sq
                        else:
                            selected_square = None

        if not is_human_turn and not board.is_game_over():
            draw_board(screen, board, selected_square, last_move)
            pygame.display.flip()
            ai_move = ai.get_ai_move(board, difficulty)
            if ai_move:
                board.push(ai_move)
                last_move = ai_move

        draw_board(screen, board, selected_square, last_move)
        if is_human_turn:
            draw_possible_moves(screen, board, selected_square)

        pygame.display.flip()
        clock.tick(30)

        if board.is_game_over():
            time.sleep(2)
            running = False

    pygame.quit()
