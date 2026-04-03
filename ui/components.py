"""
Poligame — UI Komponensek

Újrafelhasználható Pygame GUI elemek: Button, InputBox.
"""

import pygame

from engine.constants import GOLD_ACCENT, TEXT_PRIMARY, TEXT_MUTED


class Button:
    """HoI IV stílusú gomb hover-effekttel és stílus variánsokkal."""
    
    STYLES = {
        "default": ((45, 85, 130), (55, 110, 170)),
        "gold":    ((160, 130, 30), (200, 165, 50)),
        "danger":  ((140, 35, 35), (180, 50, 50)),
    }
    
    def __init__(self, x, y, w, h, text, style="default", font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.style = style
        self.is_hovered = False
        self.font = font or pygame.font.SysFont("Segoe UI", 30, bold=True)
    
    def update_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
    
    def draw(self, surface, disabled=False):
        if disabled:
            pygame.draw.rect(surface, (50, 50, 60), self.rect, border_radius=6)
            pygame.draw.rect(surface, (70, 70, 80), self.rect, 2, border_radius=6)
            txt = self.font.render(self.text, True, (100, 100, 110))
        else:
            normal, hover = self.STYLES.get(self.style, self.STYLES["default"])
            base = hover if self.is_hovered else normal
            pygame.draw.rect(surface, base, self.rect, border_radius=6)
            # Felső highlight vonal
            hl = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 2)
            pygame.draw.rect(surface, tuple(min(255, c + 40) for c in base), hl, border_radius=2)
            txt = self.font.render(self.text, True, TEXT_PRIMARY)
        
        surface.blit(txt, txt.get_rect(center=self.rect.center))


class InputBox:
    """Numerikus beviteli mező fókusz-kezeléssel."""
    
    COLOR_INACTIVE = (100, 120, 160)
    COLOR_ACTIVE   = (80, 180, 255)
    
    def __init__(self, x, y, w, h, text='0', font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = False
        self.font = font or pygame.font.SysFont("Segoe UI", 44, bold=True)
    
    @property
    def color(self):
        return self.COLOR_ACTIVE if self.active else self.COLOR_INACTIVE
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                if self.text == "0":
                    self.text = ""
            else:
                self.active = False
                if self.text == "":
                    self.text = "0"
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != pygame.K_RETURN:
                if event.unicode.isnumeric() and len(self.text) < 3:
                    self.text += event.unicode
    
    def draw(self, surface):
        pygame.draw.rect(surface, (25, 30, 45), self.rect, border_radius=4)
        bw = 3 if self.active else 2
        pygame.draw.rect(surface, self.color, self.rect, bw, border_radius=4)
        tc = TEXT_PRIMARY if self.active else (180, 190, 210)
        txt = self.font.render(self.text, True, tc)
        surface.blit(txt, txt.get_rect(center=self.rect.center))
    
    def get_value(self):
        try:
            return int(self.text)
        except ValueError:
            return 0
