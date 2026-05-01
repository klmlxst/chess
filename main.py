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

    btn_w = 260
    btn_h = 50
    btn_x = 20  # Sidebar offset

    menu_btns = {
        "pvp": Button(btn_x, 200, btn_w, btn_h, "Play vs Friend", font_small, (70,130,180), (100,160,210)),
        "ai": Button(btn_x, 260, btn_w, btn_h, "Play vs AI", font_small, (70,180,130), (100,210,160)),
        "history": Button(btn_x, 320, btn_w, btn_h, "Match History", font_small, (180,180,70), (210,210,100)),
        "quit": Button(btn_x, 380, btn_w, btn_h, "Quit", font_small, (180,70,70), (210,100,100))
    }

    btn_continue = Button(btn_x, 440, btn_w, btn_h, "Continue Game", font_small, (200,100,200), (230,130,230))

    panel_w = 400
    sidebar_w = 300
    panel_x = sidebar_w + (sw - sidebar_w) // 2 - panel_w // 2

    import chess
    ai_color_selected = chess.WHITE

    ai_btns = {
        "easy": Button(panel_x, sh//2 - 20, panel_w, btn_h, "Easy", font_main, (70,180,130), (100,210,160)),
        "med": Button(panel_x, sh//2 + 60, panel_w, btn_h, "Medium", font_main, (180,180,70), (210,210,100)),
        "hard": Button(panel_x, sh//2 + 140, panel_w, btn_h, "Hard", font_main, (180,70,70), (210,100,100))
    }

    ai_color_btns = {
        "white": Button(panel_x, sh//2 - 100, panel_w//2 - 10, btn_h, "Play White", font_small, (150,150,150), (180,180,180), (0,0,0)),
        "black": Button(panel_x + panel_w//2 + 10, sh//2 - 100, panel_w//2 - 10, btn_h, "Play Black", font_small, (50,50,50), (80,80,80))
    }

    pvp_btns = {
        "local": Button(panel_x, sh//2 - 100, panel_w, btn_h, "Local (Same PC)", font_main, (70,130,180), (100,160,210)),
        "lan_host": Button(panel_x, sh//2 - 20, panel_w, btn_h, "Host LAN Room", font_main, (70,180,130), (100,210,160)),
        "lan_join": Button(panel_x, sh//2 + 60, panel_w, btn_h, "Browse LAN Rooms", font_main, (180,180,70), (210,210,100))
    }

    # Time Control Selection UI
    tc_selected = None  # None means unlimited
    time_control_btns = {
        "none": Button(panel_x, sh//2 - 100, panel_w//2 - 10, btn_h, "Unlimited", font_small, (150,150,150), (180,180,180)),
        "3min": Button(panel_x + panel_w//2 + 10, sh//2 - 100, panel_w//2 - 10, btn_h, "3 Min", font_small, (50,50,50), (80,80,80)),
        "5min": Button(panel_x, sh//2 - 40, panel_w//2 - 10, btn_h, "5 Min", font_small, (50,50,50), (80,80,80)),
        "10min": Button(panel_x + panel_w//2 + 10, sh//2 - 40, panel_w//2 - 10, btn_h, "10 Min", font_small, (50,50,50), (80,80,80)),
        "custom": Button(panel_x, sh//2 + 20, panel_w, btn_h, "Custom (Minutes)", font_small, (50,50,50), (80,80,80))
    }
    tc_custom_input = InputBox(panel_x, sh//2 + 80, panel_w, 50, font_main, '', 'Enter custom minutes...')
    tc_next_btn = Button(panel_x, sh//2 + 140, panel_w, btn_h, "Next", font_main, (70,130,180), (100,160,210))


    room_input = InputBox(panel_x, sh//2 + 140, panel_w, 50, font_main, '', 'Enter Room Name...')

    from ui import ScrollableList
    import network
    discovery_net = network.ChessNetwork()
    room_list = ScrollableList(panel_x, sh//2 - 40, panel_w, 200, font_small)
    refresh_btn = Button(panel_x, sh//2 + 180, panel_w, 50, "Refresh", font_small, (70,130,180), (100,160,210))

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

            for k, b in menu_btns.items(): b.update(mouse_pos)
            if has_saved: btn_continue.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state != "game":
                if menu_btns["pvp"].handle_event(event): state = "pvp_time_menu"
                elif menu_btns["ai"].handle_event(event): state = "ai_menu"
                elif menu_btns["history"].handle_event(event): state = "history"
                elif menu_btns["quit"].handle_event(event):
                    pygame.quit()
                    sys.exit()
                elif has_saved and btn_continue.handle_event(event):
                    current_game = GameScreen(screen, saved["mode"], saved.get("difficulty", 1), load_saved=True)
                    state = "game"

            if state == "pvp_time_menu":
                for k, b in time_control_btns.items(): b.update(mouse_pos)
                tc_next_btn.update(mouse_pos)
                if tc_selected == "custom":
                    tc_custom_input.handle_event(event)

                if time_control_btns["none"].handle_event(event): tc_selected = None
                elif time_control_btns["3min"].handle_event(event): tc_selected = 3
                elif time_control_btns["5min"].handle_event(event): tc_selected = 5
                elif time_control_btns["10min"].handle_event(event): tc_selected = 10
                elif time_control_btns["custom"].handle_event(event): tc_selected = "custom"

                if tc_next_btn.handle_event(event):
                    state = "pvp_menu"

            elif state == "pvp_menu":
                for k, b in pvp_btns.items(): b.update(mouse_pos)
                room_input.handle_event(event)

                if pvp_btns["local"].handle_event(event):
                    tc_val = None
                    if tc_selected == "custom" and tc_custom_input.text.isdigit():
                        tc_val = int(tc_custom_input.text)
                    elif isinstance(tc_selected, int):
                        tc_val = tc_selected
                    current_game = GameScreen(screen, "pvp", time_control=tc_val)
                    state = "game"
                elif pvp_btns["lan_host"].handle_event(event):
                    room_name = room_input.text if room_input.text else "Player's Room"
                    tc_val = None
                    if tc_selected == "custom" and tc_custom_input.text.isdigit():
                        tc_val = int(tc_custom_input.text)
                    elif isinstance(tc_selected, int):
                        tc_val = tc_selected
                    current_game = GameScreen(screen, "lan", is_lan_server=True, lan_ip=room_name, time_control=tc_val)
                    state = "game"
                elif pvp_btns["lan_join"].handle_event(event):
                    state = "lan_browse"
                    discovery_net.start_discovery()

            elif state == "lan_browse":
                refresh_btn.update(mouse_pos)

                if refresh_btn.handle_event(event):
                    room_list.items.clear()
                    for ip, name in discovery_net.get_rooms().items():
                        room_list.add_item(f"{name} ({ip})", ip)

                joined_ip = room_list.handle_event(event)
                if joined_ip:
                    discovery_net.close()
                    discovery_net = network.ChessNetwork()
                    current_game = GameScreen(screen, "lan", is_lan_server=False, lan_ip=joined_ip)
                    state = "game"

            elif state == "ai_menu":
                for k, b in ai_btns.items(): b.update(mouse_pos)
                for k, b in ai_color_btns.items(): b.update(mouse_pos)

                if ai_color_btns["white"].handle_event(event):
                    ai_color_selected = chess.WHITE
                elif ai_color_btns["black"].handle_event(event):
                    ai_color_selected = chess.BLACK

                if ai_btns["easy"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 1, player_color=ai_color_selected)
                    state = "game"
                elif ai_btns["med"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 2, player_color=ai_color_selected)
                    state = "game"
                elif ai_btns["hard"].handle_event(event):
                    current_game = GameScreen(screen, "ai", 3, player_color=ai_color_selected)
                    state = "game"

            elif state == "game":
                res = current_game.handle_event(event)
                if res == "menu":
                    state = "menu"
                    current_game = None

        if state != "game":
            for k, b in menu_btns.items(): b.draw(screen)
            if has_saved: btn_continue.draw(screen)

            center_x = sidebar_w + (sw - sidebar_w) // 2

            if state == "menu":
                draw_text(screen, "Welcome to Open Chess", font_title, (255,255,255), center_x, 150)

            elif state == "pvp_time_menu":
                draw_text(screen, "Select Time Control", font_title, (255,255,255), center_x, 150)

                for k, b in time_control_btns.items():
                    b.bg_color = (150,150,150) if ((k == "none" and tc_selected is None) or
                                                   (k == "3min" and tc_selected == 3) or
                                                   (k == "5min" and tc_selected == 5) or
                                                   (k == "10min" and tc_selected == 10) or
                                                   (k == "custom" and tc_selected == "custom")) else (50,50,50)
                    b.draw(screen)

                if tc_selected == "custom":
                    tc_custom_input.draw(screen)

                tc_next_btn.draw(screen)

            elif state == "pvp_menu":
                draw_text(screen, "Select Multiplayer Mode", font_title, (255,255,255), center_x, 150)
                for k, b in pvp_btns.items(): b.draw(screen)
                room_input.draw(screen)

            elif state == "lan_browse":
                draw_text(screen, "Available LAN Rooms", font_title, (255,255,255), center_x, 150)

                # Auto refresh visually
                if len(discovery_net.get_rooms()) != len(room_list.items):
                    room_list.items.clear()
                    for ip, name in discovery_net.get_rooms().items():
                        room_list.add_item(f"{name} ({ip})", ip)

                room_list.draw(screen)
                refresh_btn.draw(screen)

            elif state == "ai_menu":
                draw_text(screen, "Select Difficulty", font_title, (255,255,255), center_x, 150)

                ai_color_btns["white"].bg_color = (200,200,200) if ai_color_selected == chess.WHITE else (100,100,100)
                ai_color_btns["black"].bg_color = (100,100,100) if ai_color_selected == chess.BLACK else (40,40,40)

                for k, b in ai_color_btns.items(): b.draw(screen)
                for k, b in ai_btns.items(): b.draw(screen)

            elif state == "history":
                draw_text(screen, "Match History", font_title, (255,255,255), center_x, 100)
                history = storage.get_history()
                y = 200
                if not history:
                    draw_text(screen, "No games played yet.", font_main, (200,200,200), center_x, y)
                for h in reversed(history[-10:]):
                    txt = f"Mode: {h['mode'].upper()} | Result: {h['result']} | Moves: {h['moves_count']}"
                    draw_text(screen, txt, font_main, (220,220,220), center_x, y)
                    y += 40

        elif state == "game":
            current_game.update()
            current_game.draw()

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
