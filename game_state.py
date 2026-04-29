import pygame
import chess
import os
import sys
import ai
import network
import storage
from ui import Button

pygame.font.init()
FONT_MAIN = pygame.font.SysFont("Segoe UI", 32)
FONT_SMALL = pygame.font.SysFont("Segoe UI", 24)

COLOR_LIGHT = (238, 238, 210)
COLOR_DARK = (118, 150, 86)
COLOR_HIGHLIGHT = (186, 202, 68)
COLOR_POSSIBLE_MOVE = (0, 0, 0, 50)
COLOR_CHECK = (220, 50, 50)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

piece_images = {}
def load_images(sq_size):
    pieces = ['bP', 'bR', 'bN', 'bB', 'bQ', 'bK', 'wP', 'wR', 'wN', 'wB', 'wQ', 'wK']
    for p in pieces:
        path = resource_path(os.path.join('assets', 'pieces', 'alpha_png', f'{p}.png'))
        img = pygame.image.load(path)
        img = pygame.transform.smoothscale(img, (sq_size, sq_size))
        piece_images[p] = img

def piece_to_name(piece):
    if not piece: return None
    return f"{'w' if piece.color == chess.WHITE else 'b'}{piece.symbol().upper()}"

class GameScreen:
    def __init__(self, screen, mode, difficulty=1, is_lan_server=False, lan_ip=None, load_saved=False):
        self.screen = screen
        self.mode = mode
        self.difficulty = difficulty
        self.board = chess.Board()
        self.move_history = []

        if load_saved:
            saved = storage.load_saved_game()
            if saved and saved.get("fen"):
                self.board.set_fen(saved["fen"])

        self.net = None
        self.is_lan_server = is_lan_server
        self.lan_connected = False
        if mode == "lan":
            self.net = network.ChessNetwork()
            self.net.receive_callback = self.on_net_receive
            if is_lan_server:
                self.net.start_server()
            else:
                success, msg = self.net.connect(lan_ip)
                self.lan_connected = success

        self.selected_square = None
        self.last_move = None

        sw, sh = self.screen.get_size()
        self.board_size = min(sw - 600, sh - 100)
        self.sq_size = self.board_size // 8
        self.board_offset_x = 300 + (sw - 600 - self.board_size) // 2
        self.board_offset_y = (sh - self.board_size) // 2

        load_images(self.sq_size)

        self.btn_menu = Button(50, 50, 200, 50, "Main Menu", FONT_SMALL, (70,70,70), (100,100,100))
        self.btn_rematch = Button(sw//2 - 110, sh//2 + 50, 100, 40, "Rematch", FONT_SMALL, (70,130,180), (100,160,210))
        self.btn_quit = Button(sw//2 + 10, sh//2 + 50, 100, 40, "Menu", FONT_SMALL, (180,70,70), (210,100,100))

        self.game_over = False
        self.winner_text = ""

    def on_net_receive(self, move_uci):
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.apply_move(move)

    def apply_move(self, move):
        san = self.board.san(move)
        quality = ai.evaluate_move_quality(self.board, move)
        self.board.push(move)
        self.last_move = move
        self.move_history.append((san, quality))

        if self.mode != "lan":
            storage.save_game(self.board.fen(), self.mode, self.difficulty)

        self.check_game_over()

    def check_game_over(self):
        if self.board.is_game_over():
            self.game_over = True
            storage.clear_saved_game()
            res = self.board.result()
            if res == "1-0": self.winner_text = "White wins!"
            elif res == "0-1": self.winner_text = "Black wins!"
            else: self.winner_text = "Draw!"
            storage.add_to_history(res, self.mode, len(self.move_history))

    def handle_event(self, event):
        sw, sh = self.screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        self.btn_menu.update(mouse_pos)
        if self.btn_menu.handle_event(event):
            if self.net: self.net.close()
            return "menu"

        if self.game_over:
            self.btn_rematch.update(mouse_pos)
            self.btn_quit.update(mouse_pos)
            if self.btn_rematch.handle_event(event):
                self.board.reset()
                self.move_history.clear()
                self.game_over = False
                self.last_move = None
            if self.btn_quit.handle_event(event):
                if self.net: self.net.close()
                return "menu"
            return None

        is_my_turn = True
        if self.mode == "ai" and self.board.turn == chess.BLACK:
            is_my_turn = False
        if self.mode == "lan":
            if self.is_lan_server and self.board.turn == chess.BLACK:
                is_my_turn = False
            if not self.is_lan_server and self.board.turn == chess.WHITE:
                is_my_turn = False

        if event.type == pygame.MOUSEBUTTONDOWN and is_my_turn:
            x, y = event.pos
            if self.board_offset_x <= x <= self.board_offset_x + self.board_size and \
               self.board_offset_y <= y <= self.board_offset_y + self.board_size:

                c = (x - self.board_offset_x) // self.sq_size
                r = (y - self.board_offset_y) // self.sq_size
                sq = chess.square(c, 7 - r)

                if self.selected_square is None:
                    piece = self.board.piece_at(sq)
                    if piece and piece.color == self.board.turn:
                        self.selected_square = sq
                else:
                    move = None
                    for m in self.board.legal_moves:
                        if m.from_square == self.selected_square and m.to_square == sq:
                            move = m
                            if move.promotion is None and self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                                if chess.square_rank(sq) == 0 or chess.square_rank(sq) == 7:
                                    move.promotion = chess.QUEEN
                            break

                    if move:
                        self.apply_move(move)
                        if self.mode == "lan" and self.net:
                            self.net.send_move(move.uci())
                        self.selected_square = None
                    else:
                        piece = self.board.piece_at(sq)
                        if piece and piece.color == self.board.turn:
                            self.selected_square = sq
                        else:
                            self.selected_square = None
        return None

    def update(self):
        if not self.game_over and self.mode == "ai" and self.board.turn == chess.BLACK:
            ai_move = ai.get_ai_move(self.board, self.difficulty)
            if ai_move:
                self.apply_move(ai_move)

    def draw(self):
        self.screen.fill((30, 30, 30))
        sw, sh = self.screen.get_size()

        pygame.draw.rect(self.screen, (40, 40, 40), (0, 0, 300, sh))
        self.btn_menu.draw(self.screen)

        hist_x = sw - 300
        pygame.draw.rect(self.screen, (40, 40, 40), (hist_x, 0, 300, sh))
        title = FONT_MAIN.render("Move History", True, (255,255,255))
        self.screen.blit(title, (hist_x + 20, 20))

        y_off = 80
        for i, (san, q) in enumerate(self.move_history[-15:]):
            color = (255,255,255)
            if q == "great": color = (100, 255, 100)
            elif q == "blunder": color = (255, 100, 100)
            elif q == "mistake": color = (255, 165, 0)

            txt = FONT_SMALL.render(f"{len(self.move_history) - min(15, len(self.move_history)) + i + 1}. {san}", True, color)
            self.screen.blit(txt, (hist_x + 20, y_off))
            y_off += 30

        for r in range(8):
            for c in range(8):
                color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
                rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, color, rect)

        if self.last_move:
            for sq in [self.last_move.from_square, self.last_move.to_square]:
                c = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
                rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect)

        if self.selected_square is not None:
            c = chess.square_file(self.selected_square)
            r = 7 - chess.square_rank(self.selected_square)
            rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect)

        if self.board.is_check():
            k_sq = self.board.king(self.board.turn)
            if k_sq is not None:
                c = chess.square_file(k_sq)
                r = 7 - chess.square_rank(k_sq)
                rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, COLOR_CHECK, rect)

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                c = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
                name = piece_to_name(piece)
                if name in piece_images:
                    self.screen.blit(piece_images[name], (self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size))

        if self.selected_square is not None:
            moves = [m for m in self.board.legal_moves if m.from_square == self.selected_square]
            for move in moves:
                to_sq = move.to_square
                c = chess.square_file(to_sq)
                r = 7 - chess.square_rank(to_sq)
                surface = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
                center = (self.sq_size // 2, self.sq_size // 2)
                if self.board.piece_at(to_sq):
                    pygame.draw.circle(surface, COLOR_POSSIBLE_MOVE, center, self.sq_size // 2, 5)
                else:
                    pygame.draw.circle(surface, COLOR_POSSIBLE_MOVE, center, self.sq_size // 6)
                self.screen.blit(surface, (self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size))

        if self.game_over:
            popup = pygame.Rect(sw//2 - 150, sh//2 - 100, 300, 200)
            pygame.draw.rect(self.screen, (50,50,50), popup, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255), popup, 2, border_radius=10)

            txt = FONT_MAIN.render(self.winner_text, True, (255,255,255))
            txt_rect = txt.get_rect(center=(sw//2, sh//2 - 40))
            self.screen.blit(txt, txt_rect)

            self.btn_rematch.draw(self.screen)
            self.btn_quit.draw(self.screen)
