"""
Poligame — In-Game HUD (Head-Up Display)

A térkép nézet bal alsó sarkában megjelenő átlátszó panel,
amely a szimuláció eredményeit mutatja HoI IV stílusban.
"""

import pygame

from engine.constants import (
    PARTY_COLORS, GOLD_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


def draw_hud(surface, width, height, parties, custom_pcts, sim_res, selected_party):
    """
    Rajzolja a mandátum-összesítő HUD panelt.
    
    Args:
        surface:  Pygame felület
        width:    Ablak szélesség
        height:   Ablak magasság
        parties:  Párt nevek listája
        custom_pcts: {party: pct} — felhasználó által megadott %
        sim_res:  Szimuláció eredmény dict
        selected_party: Kiválasztott párt neve
    """
    font_small  = pygame.font.SysFont("Segoe UI", 24)
    font_tiny   = pygame.font.SysFont("Segoe UI", 18)
    font_micro  = pygame.font.SysFont("Segoe UI", 14)
    
    panel_w, panel_h = 440, 320
    panel_rect = pygame.Rect(15, height - panel_h - 15, panel_w, panel_h)
    
    # Háttér panel
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((10, 14, 24, 220))
    pygame.draw.line(panel, (*GOLD_ACCENT, 200), (0, 0), (panel_w, 0), 2)
    surface.blit(panel, panel_rect.topleft)
    
    y = panel_rect.y + 10
    
    # Irányított párt
    if selected_party:
        pc = PARTY_COLORS.get(selected_party, TEXT_PRIMARY)
        s = font_small.render(f"▶ {selected_party}", True, pc)
        surface.blit(s, (panel_rect.x + 15, y))
    y += 30
    
    # Elválasztó
    pygame.draw.line(surface, (80, 80, 100),
                     (panel_rect.x + 10, y), (panel_rect.x + panel_w - 10, y))
    y += 8
    
    # Cím
    title = font_tiny.render("SZIMULÁCIÓ  ·  199 MANDÁTUM", True, GOLD_ACCENT)
    surface.blit(title, (panel_rect.x + 15, y))
    y += 28
    
    # Fejlécek
    headers = [("PÁRT", 15), ("MANDÁTUM", 155), ("OEVK", 260), ("LISTA", 320), ("%", 385)]
    for label, ox in headers:
        h = font_micro.render(label, True, TEXT_SECONDARY)
        surface.blit(h, (panel_rect.x + ox, y))
    y += 22
    
    pygame.draw.line(surface, (50, 50, 70),
                     (panel_rect.x + 10, y), (panel_rect.x + panel_w - 10, y))
    y += 6
    
    # Pártok (mandátum szerint rendezve)
    if sim_res:
        sorted_p = sorted(parties, key=lambda x: sim_res["mandates_total"].get(x, 0), reverse=True)
    else:
        sorted_p = parties
    
    for p in sorted_p:
        color = PARTY_COLORS.get(p, TEXT_PRIMARY)
        pct = custom_pcts.get(p, 0)
        tot = sim_res["mandates_total"].get(p, 0) if sim_res else 0
        evk = sim_res["mandates_oevk"].get(p, 0) if sim_res else 0
        lst = sim_res["mandates_list"].get(p, 0) if sim_res else 0
        
        # Színes csík
        pygame.draw.rect(surface, color, (panel_rect.x + 12, y + 2, 4, 18), border_radius=2)
        
        surface.blit(font_small.render(p, True, TEXT_PRIMARY), (panel_rect.x + 22, y))
        surface.blit(font_small.render(str(tot), True, (255, 255, 255)), (panel_rect.x + 165, y))
        surface.blit(font_tiny.render(str(evk), True, (180, 180, 200)), (panel_rect.x + 268, y))
        surface.blit(font_tiny.render(str(lst), True, (180, 180, 200)), (panel_rect.x + 328, y))
        surface.blit(font_tiny.render(f"{pct}%", True, (80, 200, 255)), (panel_rect.x + 385, y))
        y += 30
    
    # Összesen
    y += 5
    pygame.draw.line(surface, (80, 80, 100),
                     (panel_rect.x + 10, y), (panel_rect.x + panel_w - 10, y))
    y += 8
    total_m = sum(sim_res["mandates_total"].values()) if sim_res else 0
    surface.blit(font_tiny.render(f"Összesen: {total_m} / 199", True, GOLD_ACCENT),
                 (panel_rect.x + 15, y))
