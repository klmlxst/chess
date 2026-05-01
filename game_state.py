import pygame
import pygame.gfxdraw
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
    def __init__(self, screen, mode, difficulty=1, is_lan_server=False, lan_ip=None, load_saved=False, player_color=chess.WHITE, time_control=None):
        self.screen = screen
        self.mode = mode
        self.difficulty = difficulty
        self.time_control = time_control
        self.player_color = player_color
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
                self.net.start_server(lan_ip) # lan_ip holds the room name for the server
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

        self.flip_board = False
        if mode == "lan" and not is_lan_server:
            self.flip_board = True
        elif mode == "ai" and self.player_color == chess.BLACK:
            self.flip_board = True

        self.btn_menu = Button(50, 50, 200, 50, "Main Menu", FONT_SMALL, (70,70,70), (100,100,100))
        self.btn_rematch = Button(sw//2 - 110, sh//2 + 50, 100, 40, "Rematch", FONT_SMALL, (70,130,180), (100,160,210))
        self.btn_quit = Button(sw//2 + 10, sh//2 + 50, 100, 40, "Menu", FONT_SMALL, (180,70,70), (210,100,100))

        self.game_over = False
        self.winner_text = ""
        self.history_scroll_y = 0

        self.last_update_ticks = pygame.time.get_ticks()
        self.time_white = self.time_control * 60 if self.time_control else None
        self.time_black = self.time_control * 60 if self.time_control else None
        self.ai_thinking = False

    def on_net_receive(self, move_uci):
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.apply_move(move)

    def apply_move(self, move):
        san = self.board.san(move)

        captured_piece = self.board.piece_at(move.to_square)
        if self.board.is_en_passant(move):
            captured_piece = chess.Piece(chess.PAWN, not self.board.turn)

        captured_name = piece_to_name(captured_piece) if captured_piece else None

        self.board.push(move)
        self.last_move = move

        # Append empty quality first, it will be updated asynchronously
        self.move_history.append({"san": san, "quality": "pending", "captured": captured_name})

        # Start async evaluation
        import threading
        eval_board = self.board.copy()
        eval_board.pop() # board before move
        threading.Thread(target=self._async_evaluate, args=(eval_board, move, len(self.move_history)-1), daemon=True).start()

        if self.mode != "lan":
            storage.save_game(self.board.fen(), self.mode, self.difficulty)

        self.check_game_over()

    def _async_evaluate(self, board, move, index):
        quality = ai.evaluate_move_quality(board, move)
        if index < len(self.move_history):
            self.move_history[index]["quality"] = quality

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

        if event.type == pygame.MOUSEWHEEL:
            hist_x = sw - 300
            if hist_x <= mouse_pos[0] <= sw:
                self.history_scroll_y += event.y * 20

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
        if self.mode == "ai" and self.board.turn != self.player_color:
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
                sq = self.get_square_from_coords(c, r)

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

    def _async_ai_move(self):
        ai_move = ai.get_ai_move(self.board, self.difficulty)
        if ai_move and not self.game_over:
            self.apply_move(ai_move)
        self.ai_thinking = False

    def update(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_update_ticks) / 1000.0
        self.last_update_ticks = now

        if not self.game_over:
            # Handle Timers
            if self.time_control is not None and len(self.move_history) > 0:
                if self.board.turn == chess.WHITE:
                    self.time_white -= dt
                    if self.time_white <= 0:
                        self.time_white = 0
                        self.game_over = True
                        if self.board.has_insufficient_material(chess.BLACK):
                            self.winner_text = "Draw (Timeout vs Insufficient)"
                            storage.add_to_history("1/2-1/2", self.mode, len(self.move_history))
                        else:
                            self.winner_text = "Black wins on time!"
                            storage.add_to_history("0-1", self.mode, len(self.move_history))
                        storage.clear_saved_game()
                else:
                    self.time_black -= dt
                    if self.time_black <= 0:
                        self.time_black = 0
                        self.game_over = True
                        if self.board.has_insufficient_material(chess.WHITE):
                            self.winner_text = "Draw (Timeout vs Insufficient)"
                            storage.add_to_history("1/2-1/2", self.mode, len(self.move_history))
                        else:
                            self.winner_text = "White wins on time!"
                            storage.add_to_history("1-0", self.mode, len(self.move_history))
                        storage.clear_saved_game()

            if self.mode == "ai" and self.board.turn != self.player_color and not self.ai_thinking:
                self.ai_thinking = True
                import threading
                threading.Thread(target=self._async_ai_move, daemon=True).start()

    def get_screen_coords(self, sq):
        c = chess.square_file(sq)
        r = 7 - chess.square_rank(sq)
        if self.flip_board:
            c = 7 - c
            r = 7 - r
        return c, r

    def get_square_from_coords(self, c, r):
        if self.flip_board:
            c = 7 - c
            r = 7 - r
        return chess.square(c, 7 - r)

    def draw_eval_icon(self, screen, q, x, y):
        radius = 12
        center = (x + self.sq_size - radius - 4, y + radius + 4)
        color = (128, 128, 128)
        sym = ""
        font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        if q == "brilliant": color, sym = (26, 184, 172), "!!"
        elif q == "great": color, sym = (92, 142, 168), "!"
        elif q == "best": color, sym = (164, 199, 57), "★"
        elif q == "inaccuracy": color, sym = (245, 196, 60), "?!"
        elif q == "mistake": color, sym = (235, 151, 78), "?"
        elif q == "blunder": color, sym = (220, 50, 50), "??"

        if sym:
            pygame.gfxdraw.aacircle(screen, center[0], center[1], radius, color)
            pygame.gfxdraw.filled_circle(screen, center[0], center[1], radius, color)

            # Use Pygame shape for 'best' star if char unsupported, otherwise use text
            if q == "best":
                star_points = [
                    (center[0], center[1] - 8),
                    (center[0] + 2, center[1] - 2),
                    (center[0] + 8, center[1] - 2),
                    (center[0] + 3, center[1] + 2),
                    (center[0] + 5, center[1] + 8),
                    (center[0], center[1] + 4),
                    (center[0] - 5, center[1] + 8),
                    (center[0] - 3, center[1] + 2),
                    (center[0] - 8, center[1] - 2),
                    (center[0] - 2, center[1] - 2)
                ]
                pygame.gfxdraw.aapolygon(screen, star_points, (255,255,255))
                pygame.gfxdraw.filled_polygon(screen, star_points, (255,255,255))
            else:
                txt = font.render(sym, True, (255,255,255))
                txt_rect = txt.get_rect(center=center)
                screen.blit(txt, txt_rect)

    def format_time(self, seconds):
        if seconds is None:
            return "--:--"
        secs = int(max(0, seconds))
        mins = secs // 60
        secs = secs % 60
        return f"{mins:02}:{secs:02}"

    def draw(self):
        self.screen.fill((30, 30, 30))
        sw, sh = self.screen.get_size()

        pygame.draw.rect(self.screen, (40, 40, 40), (0, 0, 300, sh))
        self.btn_menu.draw(self.screen)

        if self.time_control is not None:
            tw_str = self.format_time(self.time_white)
            tb_str = self.format_time(self.time_black)

            w_timer_y = self.board_offset_y + self.board_size + 20
            b_timer_y = self.board_offset_y - 60

            if self.flip_board:
                w_timer_y, b_timer_y = b_timer_y, w_timer_y

            tw_txt = FONT_MAIN.render(tw_str, True, (255, 255, 255) if self.board.turn == chess.WHITE else (150, 150, 150))
            tb_txt = FONT_MAIN.render(tb_str, True, (255, 255, 255) if self.board.turn == chess.BLACK else (150, 150, 150))

            # Draw timer backgrounds
            w_bg_color = (80, 80, 80) if self.board.turn == chess.WHITE else (50, 50, 50)
            b_bg_color = (80, 80, 80) if self.board.turn == chess.BLACK else (50, 50, 50)

            pygame.draw.rect(self.screen, w_bg_color, (self.board_offset_x + self.board_size - 100, w_timer_y, 100, 40), border_radius=5)
            pygame.draw.rect(self.screen, b_bg_color, (self.board_offset_x + self.board_size - 100, b_timer_y, 100, 40), border_radius=5)

            self.screen.blit(tw_txt, (self.board_offset_x + self.board_size - 90, w_timer_y + 2))
            self.screen.blit(tb_txt, (self.board_offset_x + self.board_size - 90, b_timer_y + 2))

        hist_x = sw - 300
        pygame.draw.rect(self.screen, (40, 40, 40), (hist_x, 0, 300, sh))

        # History Table Header
        w_header = FONT_SMALL.render("White", True, (255, 255, 255))
        b_header = FONT_SMALL.render("Black", True, (255, 255, 255))
        self.screen.blit(w_header, (hist_x + 80, 20))
        self.screen.blit(b_header, (hist_x + 200, 20))

        if "wQ" in piece_images:
            wQ_img = pygame.transform.smoothscale(piece_images["wQ"], (24, 24))
            self.screen.blit(wQ_img, (hist_x + 50, 20))
        if "bQ" in piece_images:
            bQ_img = pygame.transform.smoothscale(piece_images["bQ"], (24, 24))
            self.screen.blit(bQ_img, (hist_x + 170, 20))

        # History panel
        hist_surface = pygame.Surface((300, sh - 60), pygame.SRCALPHA)
        row_count = (len(self.move_history) + 1) // 2
        max_scroll = max(0, row_count * 35 - (sh - 80))
        self.history_scroll_y = max(-max_scroll, min(0, self.history_scroll_y))

        y_off = self.history_scroll_y
        for i in range(0, len(self.move_history), 2):
            if 0 <= y_off + 35 and y_off <= sh - 60:
                # Move Number
                num_txt = FONT_SMALL.render(f"{(i//2) + 1}.", True, (150, 150, 150))
                hist_surface.blit(num_txt, (10, y_off))

                # Helper to draw a move cell
                def draw_move_cell(idx, start_x):
                    if idx < len(self.move_history):
                        m = self.move_history[idx]
                        q = m["quality"]
                        c = (200,200,200)
                        if q == "pending": c = (100,100,100)
                        elif q == "brilliant": c = (26, 184, 172)
                        elif q == "great": c = (92, 142, 168)
                        elif q == "best": c = (164, 199, 57)
                        elif q == "inaccuracy": c = (245, 196, 60)
                        elif q == "mistake": c = (235, 151, 78)
                        elif q == "blunder": c = (220, 50, 50)

                        txt = FONT_SMALL.render(m["san"], True, c)
                        hist_surface.blit(txt, (start_x, y_off))

                        if m["captured"] and m["captured"] in piece_images:
                            img = pygame.transform.smoothscale(piece_images[m["captured"]], (18, 18))
                            img_rect = img.get_rect(topleft=(start_x + 75, y_off + 4))
                            hist_surface.blit(img, img_rect)
                            pygame.draw.line(hist_surface, (220, 50, 50), (start_x + 75, y_off + 4), (start_x + 93, y_off + 22), 2)
                            pygame.draw.line(hist_surface, (220, 50, 50), (start_x + 93, y_off + 4), (start_x + 75, y_off + 22), 2)

                draw_move_cell(i, 45)       # White move
                draw_move_cell(i + 1, 165)  # Black move

            y_off += 35

        self.screen.blit(hist_surface, (hist_x, 60))

        # Draw board
        for r in range(8):
            for c in range(8):
                is_light = (r + c) % 2 == 0
                color = COLOR_LIGHT if is_light else COLOR_DARK
                x = self.board_offset_x + c * self.sq_size
                y = self.board_offset_y + r * self.sq_size
                rect = pygame.Rect(x, y, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, color, rect)

                # Coordinates
                coord_color = COLOR_DARK if is_light else COLOR_LIGHT
                font_coord = pygame.font.SysFont("Segoe UI", 16, bold=True)

                real_r = 7 - r if not self.flip_board else r
                real_c = c if not self.flip_board else 7 - c

                if c == 0:
                    lbl = font_coord.render(str(real_r + 1), True, coord_color)
                    self.screen.blit(lbl, (x + 4, y + 4))
                if r == 7:
                    lbl = font_coord.render(chr(ord('a') + real_c), True, coord_color)
                    self.screen.blit(lbl, (x + self.sq_size - 12, y + self.sq_size - 20))

        if self.last_move:
            for sq in [self.last_move.from_square, self.last_move.to_square]:
                c, r = self.get_screen_coords(sq)
                rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect)

        if self.selected_square is not None:
            c, r = self.get_screen_coords(self.selected_square)
            rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect)

        if self.board.is_check():
            k_sq = self.board.king(self.board.turn)
            if k_sq is not None:
                c, r = self.get_screen_coords(k_sq)
                rect = pygame.Rect(self.board_offset_x + c * self.sq_size, self.board_offset_y + r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, COLOR_CHECK, rect)

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                c, r = self.get_screen_coords(sq)
                name = piece_to_name(piece)
                x = self.board_offset_x + c * self.sq_size
                y = self.board_offset_y + r * self.sq_size
                if name in piece_images:
                    self.screen.blit(piece_images[name], (x, y))

        # Move quality icon
        if self.last_move and len(self.move_history) > 0:
            c, r = self.get_screen_coords(self.last_move.to_square)
            x = self.board_offset_x + c * self.sq_size
            y = self.board_offset_y + r * self.sq_size
            last_q = self.move_history[-1]["quality"]
            if last_q != "pending":
                self.draw_eval_icon(self.screen, last_q, x, y)

        if self.selected_square is not None:
            moves = [m for m in self.board.legal_moves if m.from_square == self.selected_square]
            for move in moves:
                to_sq = move.to_square
                c, r = self.get_screen_coords(to_sq)
                surface = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
                center = (self.sq_size // 2, self.sq_size // 2)
                if self.board.piece_at(to_sq):
                    pygame.draw.circle(surface, COLOR_POSSIBLE_MOVE, center, self.sq_size // 2, 5)
                    # Use aa circles for better drawing where possible, but a thick outline needs multiple radii
                    for i in range(5):
                        pygame.gfxdraw.aacircle(surface, center[0], center[1], self.sq_size // 2 - i, COLOR_POSSIBLE_MOVE)
                else:
                    r_circle = self.sq_size // 6
                    pygame.gfxdraw.aacircle(surface, center[0], center[1], r_circle, COLOR_POSSIBLE_MOVE)
                    pygame.gfxdraw.filled_circle(surface, center[0], center[1], r_circle, COLOR_POSSIBLE_MOVE)
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
