import pygame
import sys
import os
import storage
from ui import Button, InputBox
from game_state import GameScreen

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def draw_text(surface, text, font, color, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Open Chess")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Segoe UI", 64, bold=True)
    font_main = pygame.font.SysFont("Segoe UI", 36)
    font_small = pygame.font.SysFont("Segoe UI", 24)

    try:
        logo_img = pygame.image.load(resource_path(os.path.join('assets', 'logo.png')))
        logo_img = pygame.transform.smoothscale(logo_img, (250, 80))
    except:
        logo_img = None

    sw, sh = screen.get_size()

    state = "menu"
    current_game = None

    btn_w = 350
    btn_h = 60
    btn_x = sw // 2 - btn_w // 2

    menu_btns = {
        "pvp": Button(btn_x, sh//2 - 100, btn_w, btn_h, "Play vs Friend", font_main, (70,130,180), (100,160,210)),
        "ai": Button(btn_x, sh//2 - 20, btn_w, btn_h, "Play vs AI", font_main, (70,180,130), (100,210,160)),
        "history": Button(btn_x, sh//2 + 60, btn_w, btn_h, "Match History", font_main, (180,180,70), (210,210,100)),
        "quit": Button(btn_x, sh//2 + 140, btn_w, btn_h, "Quit", font_main, (180,70,70), (210,100,100))
    }

    ai_btns = {
        "easy": Button(btn_x, sh//2 - 60, btn_w, btn_h, "Easy", font_main, (70,180,130), (100,210,160)),
        "med": Button(btn_x, sh//2 + 20, btn_w, btn_h, "Medium", font_main, (180,180,70), (210,210,100)),
        "hard": Button(btn_x, sh//2 + 100, btn_w, btn_h, "Hard", font_main, (180,70,70), (210,100,100)),
        "back": Button(50, 50, 150, 50, "Back", font_small, (100,100,100), (130,130,130))
    }

    pvp_btns = {
        "local": Button(btn_x, sh//2 - 60, btn_w, btn_h, "Local (Same PC)", font_main, (70,130,180), (100,160,210)),
        "lan_host": Button(btn_x, sh//2 + 20, btn_w, btn_h, "Host LAN Game", font_main, (70,180,130), (100,210,160)),
        "lan_join": Button(btn_x, sh//2 + 100, btn_w, btn_h, "Join LAN Game", font_main, (180,180,70), (210,210,100)),
        "back": Button(50, 50, 150, 50, "Back", font_small, (100,100,100), (130,130,130))
    }

    ip_input = InputBox(btn_x, sh//2 + 200, btn_w, 50, font_main, '127.0.0.1')

    hist_btns = {
        "back": Button(50, 50, 150, 50, "Back", font_small, (100,100,100), (130,130,130))
    }

    btn_continue = Button(btn_x, sh//2 - 180, btn_w, btn_h, "Continue Game", font_main, (200,100,200), (230,130,230))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((30, 30, 30))

        saved = storage.load_saved_game()
        has_saved = saved is not None and saved.get("fen") is not None

        if state != "game":
            pygame.draw.rect(screen, (40, 40, 40), (0, 0, 300, sh))
            if logo_img:
                screen.blit(logo_img, (25, 50))
            else:
                draw_text(screen, "Open Chess", font_main, (255,255,255), 150, 90)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "menu":
                for k, b in menu_btns.items(): b.update(mouse_pos)
                if has_saved: btn_continue.update(mouse_pos)

                if menu_btns["pvp"].handle_event(event): state = "pvp_menu"
                elif menu_btns["ai"].handle_event(event): state = "ai_menu"
                elif menu_btns["history"].handle_event(event): state = "history"
                elif menu_btns["quit"].handle_event(event):
                    pygame.quit()
                    sys.exit()
                elif has_saved and btn_continue.handle_event(event):
                    current_game = GameScreen(screen, saved["mode"], saved.get("difficulty", 1), load_saved=True)
                    state = "game"

            elif state == "pvp_menu":
                for k, b in pvp_btns.items(): b.update(mouse_pos)
                ip_input.handle_event(event)

                if pvp_btns["back"].handle_event(event): state = "menu"
                elif pvp_btns["local"].handle_event(event):
                    current_game = GameScreen(screen, "pvp")
                    state = "game"
                elif pvp_btns["lan_host"].handle_event(event):
                    current_game = GameScreen(screen, "lan", is_lan_server=True)
                    state = "game"
                elif pvp_btns["lan_join"].handle_event(event):
                    current_game = GameScreen(screen, "lan", is_lan_server=False, lan_ip=ip_input.text)
                    state = "game"

            elif state == "ai_menu":
                for k, b in ai_btns.items(): b.update(mouse_pos)

                if ai_btns["back"].handle_event(event): state = "menu"
                elif ai_btns["easy"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 1)
                    state = "game"
                elif ai_btns["med"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 2)
                    state = "game"
                elif ai_btns["hard"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 3)
                    state = "game"

            elif state == "history":
                hist_btns["back"].update(mouse_pos)
                if hist_btns["back"].handle_event(event): state = "menu"

            elif state == "game":
                res = current_game.handle_event(event)
                if res == "menu":
                    state = "menu"
                    current_game = None

        if state == "menu":
            draw_text(screen, "Welcome to Open Chess", font_title, (255,255,255), sw//2 + 150, 150)
            for k, b in menu_btns.items(): b.draw(screen)
            if has_saved: btn_continue.draw(screen)

        elif state == "pvp_menu":
            draw_text(screen, "Select Multiplayer Mode", font_title, (255,255,255), sw//2 + 150, 150)
            for k, b in pvp_btns.items(): b.draw(screen)
            ip_input.draw(screen)
            draw_text(screen, "Join IP:", font_small, (200,200,200), btn_x + btn_w//2, sh//2 + 180)

        elif state == "ai_menu":
            draw_text(screen, "Select Difficulty", font_title, (255,255,255), sw//2 + 150, 150)
            for k, b in ai_btns.items(): b.draw(screen)

        elif state == "history":
            draw_text(screen, "Match History", font_title, (255,255,255), sw//2 + 150, 100)
            hist_btns["back"].draw(screen)
            history = storage.get_history()
            y = 200
            if not history:
                draw_text(screen, "No games played yet.", font_main, (200,200,200), sw//2 + 150, y)
            for h in reversed(history[-10:]):
                txt = f"Mode: {h['mode'].upper()} | Result: {h['result']} | Moves: {h['moves_count']}"
                draw_text(screen, txt, font_main, (220,220,220), sw//2 + 150, y)
                y += 40

        elif state == "game":
            current_game.update()
            current_game.draw()

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
