import pygame
import game
import sys

def draw_text(surface, text, font, color, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)
    return textrect

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((640, 640))
    pygame.display.set_caption("Chess Desktop")
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)

    while True:
        screen.fill((40, 40, 40))

        draw_text(screen, "Chess Desktop", font, (255, 255, 255), 320, 100)

        btn_pvp = pygame.Rect(170, 200, 300, 60)
        btn_ai_easy = pygame.Rect(170, 280, 300, 60)
        btn_ai_med = pygame.Rect(170, 360, 300, 60)
        btn_ai_hard = pygame.Rect(170, 440, 300, 60)

        pygame.draw.rect(screen, (70, 130, 180), btn_pvp)
        pygame.draw.rect(screen, (70, 180, 130), btn_ai_easy)
        pygame.draw.rect(screen, (180, 180, 70), btn_ai_med)
        pygame.draw.rect(screen, (180, 70, 70), btn_ai_hard)

        draw_text(screen, "Player vs Player", small_font, (255, 255, 255), 320, 230)
        draw_text(screen, "Play vs AI (Easy)", small_font, (255, 255, 255), 320, 310)
        draw_text(screen, "Play vs AI (Medium)", small_font, (255, 255, 255), 320, 390)
        draw_text(screen, "Play vs AI (Hard)", small_font, (255, 255, 255), 320, 470)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_pvp.collidepoint(event.pos):
                    pygame.quit()
                    game.run_game("pvp")
                    return
                elif btn_ai_easy.collidepoint(event.pos):
                    pygame.quit()
                    game.run_game("ai", 1)
                    return
                elif btn_ai_med.collidepoint(event.pos):
                    pygame.quit()
                    game.run_game("ai", 2)
                    return
                elif btn_ai_hard.collidepoint(event.pos):
                    pygame.quit()
                    game.run_game("ai", 3)
                    return

        pygame.display.flip()

if __name__ == "__main__":
    while True:
        main_menu()
