"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  POLIGAME — Magyar Belpolitikai Stratégiai Szimulátor                      ║
║                                                                            ║
║  Engine:  Saját (Pygame 2.6 + Shapely GIS)                                 ║
║  Kalkulátor:  21 Kutatóközpont módszertan (D'Hondt)                        ║
║  Térkép:  NVI hivatalos OEVK GeoJSON                                       ║
║  Baseline:  2024-es EP választás (NVI vármegyei adatok)                    ║
║                                                                            ║
║  © 2026 — Minden jog fenntartva                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import pygame

# ============================================================================
#  INICIALIZÁCIÓ
# ============================================================================

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Poligame")

# --- PyInstaller Splash bezárása ---
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# --- Loading Screen ---
_font_loading_title = pygame.font.SysFont("Segoe UI", 56, bold=True)
_font_loading_sub   = pygame.font.SysFont("Segoe UI", 24)
_font_loading_text  = pygame.font.SysFont("Segoe UI", 30, bold=True)
_font_loading_ver   = pygame.font.SysFont("Segoe UI", 14)

def loading_screen(text, progress=None):
    """Professzionális betöltő képernyő progress barral."""
    screen.fill((15, 18, 28))
    
    title = _font_loading_title.render("POLIGAME", True, (200, 170, 60))
    screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//3)))
    
    sub = _font_loading_sub.render("Magyar Belpolitikai Stratégiai Szimulátor", True, (120, 120, 140))
    screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//3 + 60)))
    
    load = _font_loading_text.render(text, True, (255, 200, 50))
    screen.blit(load, load.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))
    
    if progress is not None:
        bar_w, bar_h = 400, 8
        bx = WIDTH//2 - bar_w//2
        by = HEIGHT//2 + 80
        pygame.draw.rect(screen, (40, 40, 55), (bx, by, bar_w, bar_h), border_radius=4)
        fw = int(bar_w * min(1.0, progress))
        if fw > 0:
            pygame.draw.rect(screen, (200, 170, 60), (bx, by, fw, bar_h), border_radius=4)
    
    ver = _font_loading_ver.render("v0.2.0-alpha  |  Saját Engine (Pygame + Shapely GIS)", True, (60, 60, 80))
    screen.blit(ver, ver.get_rect(center=(WIDTH//2, HEIGHT - 30)))
    
    pygame.display.flip()
    pygame.event.pump()

# ============================================================================
#  MOTOR BETÖLTÉSE
# ============================================================================

loading_screen("Térképadatok betöltése...", 0.0)

from engine.constants import PARTIES
from engine.map_renderer import MapRenderer
from engine.election import ElectionSimulator
from ui.components import Button, InputBox
from ui.screens import draw_menu, draw_party_select, draw_scenario_select, draw_custom_setup
from ui.hud import draw_hud

loading_screen("Geometria inicializálása...", 0.1)
map_engine = MapRenderer(WIDTH, HEIGHT, loading_callback=loading_screen)

loading_screen("Választási adatok betöltése...", 0.9)
sim_engine = ElectionSimulator()

loading_screen("Kész!", 1.0)
pygame.time.wait(300)

# ============================================================================
#  ÁLLAPOTGÉP
# ============================================================================

STATE_MENU            = 0
STATE_PARTY_SELECT    = 1
STATE_SCENARIO_SELECT = 2
STATE_CUSTOM_SETUP    = 3
STATE_MAP             = 4

# ============================================================================
#  JÁTÉKCIKLUS
# ============================================================================

def main():
    clock = pygame.time.Clock()
    current_state = STATE_MENU
    selected_party = None
    custom_percentages = {}
    sim_results = None
    show_oevk = False  # OEVK/Megye nézet toggle
    
    # --- UI elemek létrehozása ---
    btn_play = Button(WIDTH//2 - 160, HEIGHT//2 - 40, 320, 60, "Játék Indítása", "gold")
    btn_exit = Button(WIDTH//2 - 160, HEIGHT//2 + 50, 320, 60, "Kilépés", "danger")
    
    party_buttons = []
    sy = HEIGHT//2 - 150
    for i, p in enumerate(PARTIES):
        party_buttons.append(Button(WIDTH//2 - 160, sy + i * 70, 320, 55, p))
    
    btn_lore   = Button(WIDTH//2 - 250, HEIGHT//2 - 80, 500, 60, "Történelmi felállás (Hamarosan)")
    btn_custom = Button(WIDTH//2 - 250, HEIGHT//2 + 40, 500, 60, "Egyéni szimuláció", "gold")
    
    input_boxes = {}
    by = HEIGHT//2 - 150
    for p in PARTIES:
        input_boxes[p] = InputBox(WIDTH//2 + 80, by, 100, 50)
        by += 70
    
    btn_start = Button(WIDTH//2 - 160, HEIGHT//2 + 280, 320, 60, "Szimuláció Indítása", "gold")
    
    # OEVK toggle gomb (bal alsó, a HUD panel felett)
    font_toggle = pygame.font.SysFont("Segoe UI", 16, bold=True)
    toggle_rect = pygame.Rect(15, 0, 180, 34)  # y-t renderkor számoljuk
    
    font_esc = pygame.font.SysFont("Segoe UI", 14)
    
    # === FŐ LOOP ===
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # --- MENÜ ---
            if current_state == STATE_MENU:
                btn_play.update_hover(mouse_pos)
                btn_exit.update_hover(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play.is_hovered:
                        current_state = STATE_PARTY_SELECT
                    elif btn_exit.is_hovered:
                        pygame.quit()
                        sys.exit()
            
            # --- PÁRTVÁLASZTÓ ---
            elif current_state == STATE_PARTY_SELECT:
                for pb in party_buttons:
                    pb.update_hover(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for pb in party_buttons:
                        if pb.is_hovered:
                            selected_party = pb.text
                            current_state = STATE_SCENARIO_SELECT
                            break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
            
            # --- SZCENÁRIÓ ---
            elif current_state == STATE_SCENARIO_SELECT:
                btn_custom.update_hover(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_custom.is_hovered:
                        current_state = STATE_CUSTOM_SETUP
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_PARTY_SELECT
            
            # --- CUSTOM SETUP ---
            elif current_state == STATE_CUSTOM_SETUP:
                for box in input_boxes.values():
                    box.handle_event(event)
                
                total = sum(b.get_value() for b in input_boxes.values())
                if total == 100:
                    btn_start.update_hover(mouse_pos)
                else:
                    btn_start.is_hovered = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_start.is_hovered and total == 100:
                        for p, box in input_boxes.items():
                            custom_percentages[p] = box.get_value()
                        
                        # === SZIMULÁCIÓ FUTTATÁSA ===
                        sim_results = sim_engine.run(custom_percentages)
                        map_engine.set_colors(sim_results.get("colors", {}))
                        current_state = STATE_MAP
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_SCENARIO_SELECT
            
            # --- TÉRKÉP ---
            elif current_state == STATE_MAP:
                # Toggle gomb kattintás ellenőrzése
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if toggle_rect.collidepoint(event.pos):
                        show_oevk = not show_oevk
                    else:
                        map_engine.handle_event(event)
                else:
                    map_engine.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
        
        # ================================================================
        #  RENDERELÉS
        # ================================================================
        
        if current_state == STATE_MENU:
            draw_menu(screen, WIDTH, HEIGHT, btn_play, btn_exit)
        
        elif current_state == STATE_PARTY_SELECT:
            draw_party_select(screen, WIDTH, HEIGHT, party_buttons)
        
        elif current_state == STATE_SCENARIO_SELECT:
            draw_scenario_select(screen, WIDTH, HEIGHT, btn_lore, btn_custom)
        
        elif current_state == STATE_CUSTOM_SETUP:
            draw_custom_setup(screen, WIDTH, HEIGHT, input_boxes, btn_start)
        
        elif current_state == STATE_MAP:
            map_engine.draw(screen, mouse_pos, show_oevk=show_oevk, sim_results=sim_results)
            draw_hud(screen, WIDTH, HEIGHT, PARTIES, custom_percentages, sim_results, selected_party)
            
            # OEVK/Megye toggle gomb
            toggle_rect.y = HEIGHT - 320 - 15 - 44  # HUD panel teteje felett
            is_toggle_hovered = toggle_rect.collidepoint(mouse_pos)
            toggle_bg = (50, 90, 50) if show_oevk else (45, 55, 75)
            if is_toggle_hovered:
                toggle_bg = tuple(min(255, c + 20) for c in toggle_bg)
            pygame.draw.rect(screen, toggle_bg, toggle_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 170, 60) if show_oevk else (80, 80, 100), toggle_rect, 2, border_radius=5)
            toggle_label = "OEVK nézet: BE" if show_oevk else "OEVK nézet: KI"
            toggle_txt = font_toggle.render(toggle_label, True, (255, 255, 255))
            screen.blit(toggle_txt, toggle_txt.get_rect(center=toggle_rect.center))
            
            esc_hint = font_esc.render("[ ESC ] Főmenü", True, (80, 80, 100))
            screen.blit(esc_hint, (WIDTH - 120, 10))
        
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
