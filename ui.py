import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, bg_color, hover_color, text_color=(255, 255, 255), border_radius=12):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color

        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(surface, (20, 20, 20), shadow_rect, border_radius=self.border_radius)

        # Main Button
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        # Outline
        pygame.draw.rect(surface, (max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30)), self.rect, 2, border_radius=self.border_radius)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

class InputBox:
    def __init__(self, x, y, w, h, font, text='', placeholder=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100, 100, 100)
        self.color_active = (100, 200, 100)
        self.color = self.color_inactive
        self.text = text
        self.placeholder = placeholder
        self.font = font
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, (40, 40, 40), self.rect, border_radius=8)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=8)

        display_text = self.text if self.text or self.active else self.placeholder
        text_color = (255, 255, 255) if self.text or self.active else (150, 150, 150)

        txt_surface = self.font.render(display_text, True, text_color)
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + (self.rect.h - txt_surface.get_height()) // 2))

class ScrollableList:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.items = []
        self.scroll_y = 0
        self.item_height = 40

    def add_item(self, text, data=None):
        self.items.append({"text": text, "data": data, "rect": None})

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y += event.y * 20

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                for item in self.items:
                    if item["rect"] and item["rect"].collidepoint(mouse_pos):
                        return item["data"]
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, (35, 35, 35), self.rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 60), self.rect, 2, border_radius=10)

        # Clamp scroll
        max_scroll = max(0, len(self.items) * self.item_height - self.rect.h)
        self.scroll_y = max(-max_scroll, min(0, self.scroll_y))

        surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        y_offset = self.scroll_y
        for i, item in enumerate(self.items):
            item_rect = pygame.Rect(0, y_offset, self.rect.w, self.item_height)

            # Map surface rect to screen rect for collision
            item["rect"] = pygame.Rect(self.rect.x, self.rect.y + y_offset, self.rect.w, self.item_height)

            if 0 <= y_offset + self.item_height and y_offset <= self.rect.h:
                if item["rect"].collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, (60, 60, 60, 200), item_rect, border_radius=5)

                txt = self.font.render(item["text"], True, (230, 230, 230))
                surface.blit(txt, (10, y_offset + (self.item_height - txt.get_height()) // 2))

            y_offset += self.item_height

        screen.blit(surface, (self.rect.x, self.rect.y))
