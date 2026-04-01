import sys
import os
import pygame

# Kényszerítjük, hogy az ablak a bal felső sarokba (0,0) igazodjon, így a NOFRAME tényleg kitölti a képernyőt.
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

pygame.init()
pygame.display.set_caption("Poligame - Főmenü")

# Lekérjük a monitorod tényleges, teljes felbontását
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Valódi Borderless Fullscreen (Keret nélküli teljes képernyő)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)

# Itt fogjuk később elvégezni a szükséges betöltéseket (fájlok olvasása, térkép betöltése)
# Most semmilyen mesterséges megállítást nem rakunk bele!

font_large = pygame.font.SysFont("Segoe UI", 48, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 24)

# Colors
BG_COLOR = (30, 30, 40)
BTN_NORMAL = (50, 150, 200)
BTN_HOVER = (70, 180, 230)
TEXT_COLOR = (255, 255, 255)

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        
    def draw(self, surface):
        color = BTN_HOVER if self.is_hovered else BTN_NORMAL
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        txt_surf = font_large.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

def main():
    clock = pygame.time.Clock()
    
    btn_play = Button(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 60, "Játék")
    btn_exit = Button(WIDTH//2 - 150, HEIGHT//2 + 40, 300, 60, "Kilépés")
    
    show_coming_soon = False
    message_timer = 0
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        btn_play.is_hovered = btn_play.rect.collidepoint(mouse_pos)
        btn_exit.is_hovered = btn_exit.rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if btn_play.is_hovered:
                        show_coming_soon = True
                        message_timer = 120 # Show message for ~2 seconds (at 60 FPS)
                    if btn_exit.is_hovered:
                        pygame.quit()
                        sys.exit()
                        
        screen.fill(BG_COLOR)
        
        # Title
        title_surf = font_large.render("POLIGAME", True, (200, 200, 200))
        title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//4))
        screen.blit(title_surf, title_rect)
        
        # Draw buttons
        btn_play.draw(screen)
        btn_exit.draw(screen)
        
        # "Hamarosan" popup message
        if show_coming_soon:
            msg_surf = font_small.render("Hamarosan!", True, (255, 200, 50))
            msg_rect = msg_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 110))
            screen.blit(msg_surf, msg_rect)
            message_timer -= 1
            if message_timer <= 0:
                show_coming_soon = False
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
