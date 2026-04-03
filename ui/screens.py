"""
Poligame — Menü Képernyők

Minden állapothoz tartozó renderelő függvény.
A fő játékciklus ezeket hívja a current_state alapján.
"""

import pygame

from engine.constants import (
    BG_DARK, GOLD_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    PARTY_COLORS, COLOR_SUCCESS, COLOR_ERROR, VERSION, GAME_TITLE, GAME_SUBTITLE,
    PARTIES
)

# Font cache (inicializálás az első híváskor)
_fonts = {}

def _get_fonts():
    if not _fonts:
        _fonts['title']  = pygame.font.SysFont("Segoe UI", 56, bold=True)
        _fonts['large']  = pygame.font.SysFont("Segoe UI", 44, bold=True)
        _fonts['medium'] = pygame.font.SysFont("Segoe UI", 30, bold=True)
        _fonts['small']  = pygame.font.SysFont("Segoe UI", 24)
        _fonts['tiny']   = pygame.font.SysFont("Segoe UI", 18)
        _fonts['micro']  = pygame.font.SysFont("Segoe UI", 14)
    return _fonts


def draw_menu(surface, width, height, btn_play, btn_exit):
    f = _get_fonts()
    surface.fill(BG_DARK)
    
    # Cím
    title = f['title'].render(GAME_TITLE, True, GOLD_ACCENT)
    surface.blit(title, title.get_rect(center=(width//2, height//4)))
    sub = f['small'].render(GAME_SUBTITLE, True, TEXT_SECONDARY)
    surface.blit(sub, sub.get_rect(center=(width//2, height//4 + 55)))
    
    btn_play.draw(surface)
    btn_exit.draw(surface)
    
    # Verzió
    ver = f['micro'].render(
        f"v{VERSION}",
        True, (50, 50, 65)
    )
    surface.blit(ver, ver.get_rect(center=(width//2, height - 25)))


def draw_party_select(surface, width, height, party_buttons):
    f = _get_fonts()
    surface.fill(BG_DARK)
    
    title = f['large'].render("VÁLASSZ PÁRTOT", True, GOLD_ACCENT)
    surface.blit(title, title.get_rect(center=(width//2, height//7)))
    sub = f['tiny'].render("Melyik pártot irányítod a szimulációban?", True, TEXT_SECONDARY)
    surface.blit(sub, sub.get_rect(center=(width//2, height//7 + 45)))
    
    for btn in party_buttons:
        btn.draw(surface)
    
    esc = f['tiny'].render("[ ESC ] Vissza", True, TEXT_MUTED)
    surface.blit(esc, esc.get_rect(center=(width//2, height - 40)))


def draw_scenario_select(surface, width, height, btn_lore, btn_custom):
    f = _get_fonts()
    surface.fill(BG_DARK)
    
    title = f['large'].render("VÁLASSZ SZCENÁRIÓT", True, GOLD_ACCENT)
    surface.blit(title, title.get_rect(center=(width//2, height//4)))
    
    btn_lore.draw(surface, disabled=True)
    btn_custom.draw(surface)
    
    esc = f['tiny'].render("[ ESC ] Vissza", True, TEXT_MUTED)
    surface.blit(esc, esc.get_rect(center=(width//2, height - 40)))



def draw_custom_setup(surface, width, height, input_boxes, btn_start):
    f = _get_fonts()
    surface.fill(BG_DARK)
    
    title = f['large'].render("ORSZÁGOS TÁMOGATOTTSÁG BEÁLLÍTÁSA", True, GOLD_ACCENT)
    surface.blit(title, title.get_rect(center=(width//2, height//7)))
    
    total = sum(box.get_value() for box in input_boxes.values())
    
    draw_y = height//2 - 150
    for p in PARTIES:
        pc = PARTY_COLORS.get(p, TEXT_PRIMARY)
        # Színes csík
        pygame.draw.rect(surface, pc, (width//2 - 220, draw_y + 12, 5, 25), border_radius=2)
        lbl = f['large'].render(p, True, TEXT_PRIMARY)
        surface.blit(lbl, (width//2 - 205, draw_y + 5))
        input_boxes[p].rect.y = draw_y
        input_boxes[p].draw(surface)
        pct = f['medium'].render("%", True, TEXT_SECONDARY)
        surface.blit(pct, (width//2 + 190, draw_y + 10))
        draw_y += 70
    
    # Összesen
    tc = COLOR_SUCCESS if total == 100 else COLOR_ERROR
    tot = f['medium'].render(f"ÖSSZESEN: {total} / 100%", True, tc)
    surface.blit(tot, tot.get_rect(center=(width//2, height//2 + 225)))
    
    # Gomb
    btn_start.draw(surface, disabled=(total != 100))
    
    hint = f['tiny'].render("Kattints a mezőkre az íráshoz  ·  [ ESC ] Vissza", True, TEXT_MUTED)
    surface.blit(hint, hint.get_rect(center=(width//2, height - 40)))
