import sys
import os
import json
import math
import pygame
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely.affinity import scale as shapely_scale

# Ablak alaphelyzetbe (0,0) ugrasztása (kizárólag egyszer történik a betöltéskor)
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

pygame.init()
pygame.display.set_caption("Poligame - Map")

# Képernyőfelbontás lekérdezése
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)

font_splash = pygame.font.SysFont("Segoe UI", 28, bold=True)
font_large = pygame.font.SysFont("Segoe UI", 48, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 24)

# --- PYINSTALLER BOOTLOADER SPLASH SCREEN BEZÁRÁSA ---
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# --- SPLASH KÉPERNYŐ RAJZOLÁSA ---
screen.fill((20, 20, 30))
text_surf = font_splash.render("Térképadatok és Geometria Inicializálása (OEVK, Megyék)...", True, (255, 200, 50))
screen.blit(text_surf, text_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))
pygame.display.flip()
pygame.event.pump()

# --- TÉRKÉP OSZTÁLY (GIS ADATOK ÉS KAMERA) ---
class MapRenderer:
    def __init__(self, geojson_path):
        self.oevks = []
        self.counties = {}
        self.min_lon, self.max_lon = 999, -999
        self.min_lat, self.max_lat = 999, -999
        
        self.offset_x, self.offset_y = 0, 0
        self.scale = 1.0
        self.base_scale = 1.0
        
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)

        self.load_data(geojson_path)
        self.center_map()

    def load_data(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print("Nem találtam a data/oevk.json fájlt:", e)
            return

        county_polygons = {}

        HUNGARY_CENTER_LAT = 47.16 
        lon_ratio = math.cos(math.radians(HUNGARY_CENTER_LAT))

        for feature in data['features']:
            geom = shape(feature['geometry'])
            geom = make_valid(geom).buffer(0) 
            geom = geom.simplify(0.0005, preserve_topology=True) 
            geom = shapely_scale(geom, xfact=lon_ratio, yfact=1.0, origin=(0, 0))

            name = feature['properties']['name']
            county_name = name.rsplit(' ', 1)[0]
            
            minx, miny, maxx, maxy = geom.bounds
            self.min_lon = min(self.min_lon, minx)
            self.max_lon = max(self.max_lon, maxx)
            self.min_lat = min(self.min_lat, miny)
            self.max_lat = max(self.max_lat, maxy)

            self.oevks.append({
                "name": name,
                "county": county_name,
                "geom": geom
            })

            if county_name not in county_polygons:
                county_polygons[county_name] = []
            county_polygons[county_name].append(geom)

        for county_name, polys in county_polygons.items():
            merged_geom = unary_union(polys)
            self.counties[county_name] = {
                "name": county_name,
                "geom": merged_geom
            }

    def center_map(self):
        map_w = self.max_lon - self.min_lon
        map_h = self.max_lat - self.min_lat
        if map_w == 0 or map_h == 0: return

        scale_x = (WIDTH * 0.9) / map_w
        scale_y = (HEIGHT * 0.9) / map_h
        self.base_scale = min(scale_x, scale_y)
        self.scale = self.base_scale

        map_c_lon = (self.min_lon + self.max_lon) / 2
        map_c_lat = (self.min_lat + self.max_lat) / 2
        
        self.offset_x = (WIDTH / 2) - ((map_c_lon - self.min_lon) * self.scale)
        self.offset_y = (HEIGHT / 2) - ((self.max_lat - map_c_lat) * self.scale)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                self.is_dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4:
                self._zoom(1.2, event.pos)
            elif event.button == 5:
                if self.scale > self.base_scale * 0.5:
                    self._zoom(1.0 / 1.2, event.pos)
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.offset_x += dx
                self.offset_y += dy
                self.last_mouse_pos = event.pos

    def _zoom(self, factor, mouse_pos):
        mouse_lon = (mouse_pos[0] - self.offset_x) / self.scale + self.min_lon
        mouse_lat = self.max_lat - (mouse_pos[1] - self.offset_y) / self.scale
        
        self.scale *= factor
        
        new_x = (mouse_lon - self.min_lon) * self.scale
        new_y = (self.max_lat - mouse_lat) * self.scale
        
        self.offset_x = mouse_pos[0] - new_x
        self.offset_y = mouse_pos[1] - new_y

    def geo_to_screen(self, lon, lat):
        x = (lon - self.min_lon) * self.scale + self.offset_x
        y = (self.max_lat - lat) * self.scale + self.offset_y
        return (x, y)

    def draw_polygon(self, surface, geom, fill_color, border_color, border_width):
        s = self.scale
        ox = self.offset_x
        oy = self.offset_y
        mlon = self.min_lon
        mlat = self.max_lat
        
        if geom.geom_type == 'Polygon':
            coords = [((x - mlon) * s + ox, (mlat - y) * s + oy) for x, y in geom.exterior.coords]
            if len(coords) > 2:
                pygame.draw.polygon(surface, fill_color, coords)
                pygame.draw.lines(surface, border_color, True, coords, border_width)
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                coords = [((x - mlon) * s + ox, (mlat - y) * s + oy) for x, y in poly.exterior.coords]
                if len(coords) > 2:
                    pygame.draw.polygon(surface, fill_color, coords)
                    pygame.draw.lines(surface, border_color, True, coords, border_width)

    def draw(self, surface, mouse_pos):
        surface.fill((25, 30, 45))
        hovered_name = None
        geo_x = (mouse_pos[0] - self.offset_x) / self.scale + self.min_lon
        geo_y = self.max_lat - (mouse_pos[1] - self.offset_y) / self.scale
        geo_mouse = Point(geo_x, geo_y)
        
        show_oevk = self.scale > (self.base_scale * 2.5)
        element_list = self.oevks if show_oevk else self.counties.values()
        
        for elem in element_list:
            geom = elem['geom']
            minx, miny, maxx, maxy = geom.bounds
            
            screen_left, screen_bottom = self.geo_to_screen(minx, miny)
            screen_right, screen_top = self.geo_to_screen(maxx, maxy)
            
            if screen_right < 0 or screen_left > WIDTH or screen_bottom < 0 or screen_top > HEIGHT:
                continue 
            
            is_hovered = False
            if minx <= geo_x <= maxx and miny <= geo_y <= maxy:
                if geom.contains(geo_mouse):
                    is_hovered = True

            if is_hovered:
                hovered_name = elem['name']
                fill_color = (60, 110, 80) if not show_oevk else (120, 150, 70) 
            else:
                fill_color = (40, 60, 50) if not show_oevk else (50, 80, 60)
            
            border_color = (150, 150, 150) if not show_oevk else (100, 100, 100)
            border_w = 2 if not show_oevk else 1
            
            self.draw_polygon(surface, geom, fill_color, border_color, border_w)

        if hovered_name:
            infobox = font_small.render(hovered_name, True, (255, 255, 255))
            ib_rect = infobox.get_rect(midbottom=(mouse_pos[0], mouse_pos[1] - 15))
            bg_rect = ib_rect.copy()
            bg_rect.inflate_ip(10, 10)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=4)
            surface.blit(infobox, ib_rect)

map_engine = MapRenderer("data/oevk.json")


# --- UI GOMBOK, INPUTBOXOK ÉS ÁLLAPOTGÉP ---
STATE_MENU = 0
STATE_PARTY_SELECT = 1
STATE_SCENARIO_SELECT = 2
STATE_CUSTOM_SETUP = 3
STATE_MAP = 4

current_state = STATE_MENU
selected_party = None
custom_percentages = {}

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        
    def draw(self, surface):
        color = (70, 180, 230) if self.is_hovered else (50, 150, 200)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        txt_surf = font_large.render(self.text, True, (255,255,255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.txt_surface = font_large.render(text, True, self.color)
        self.active = False
        self.cursor_visible = False
        self.timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                if self.text == "0": # Töröljük a 0-t fókuszba kerüléskor!
                    self.text = ""
            else:
                self.active = False
                if self.text == "": # Tegyük vissza a 0-t, ha üresen hagyták!
                    self.text = "0"
            self.color = self.color_active if self.active else self.color_inactive
            self.txt_surface = font_large.render(self.text, True, self.color)
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != pygame.K_RETURN:
                if event.unicode.isnumeric() and len(self.text) < 3:
                    self.text += event.unicode
            self.txt_surface = font_large.render(self.text, True, self.color)

    def draw(self, screen):
        # Doboz háttér
        pygame.draw.rect(screen, (30, 30, 40), self.rect)
        # Keret (szín cserélődik, ha fókuszban van)
        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)
        # Szöveg renderelés középen
        screen.blit(self.txt_surface, self.txt_surface.get_rect(center=self.rect.center))

    def get_value(self):
        try:
            return int(self.text)
        except ValueError:
            return 0

def main():
    global current_state, selected_party, custom_percentages
    clock = pygame.time.Clock()
    
    # 1. Menü Gombok
    btn_play = Button(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 60, "Játék")
    btn_exit = Button(WIDTH//2 - 150, HEIGHT//2 + 40, 300, 60, "Kilépés")
    
    # 2. Pártválasztás
    parties = ["Tisza", "Fidesz", "Mi Hazánk", "MKKP", "DK"]
    party_buttons = []
    start_y = HEIGHT//2 - 150
    for i, p in enumerate(parties):
        party_buttons.append(Button(WIDTH//2 - 150, start_y + i * 70, 300, 50, p))
        
    # 3. Szcenárió gombok
    btn_scenario_lore = Button(WIDTH//2 - 250, HEIGHT//2 - 80, 500, 60, "Történelmi felállás (Hamarosan)")
    btn_scenario_custom = Button(WIDTH//2 - 250, HEIGHT//2 + 40, 500, 60, "Egyéni szimuláció")
    
    # 4. Egyéni szimuláció TextBoxok
    input_boxes = {}
    box_y = HEIGHT//2 - 150
    for p in parties:
        input_boxes[p] = InputBox(WIDTH//2 + 50, box_y, 100, 50, '0')
        box_y += 70
        
    btn_start_custom = Button(WIDTH//2 - 150, HEIGHT//2 + 280, 300, 60, "Tovább a Térképre")
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # - MENU ÁLLAPOT -
            if current_state == STATE_MENU:
                btn_play.is_hovered = btn_play.rect.collidepoint(mouse_pos)
                btn_exit.is_hovered = btn_exit.rect.collidepoint(mouse_pos)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play.is_hovered:
                        current_state = STATE_PARTY_SELECT # Átugrunk a pártválasztóba
                    if btn_exit.is_hovered:
                        pygame.quit()
                        sys.exit()
            
            # - PÁRTVÁLASZTÓ ÁLLAPOT -
            elif current_state == STATE_PARTY_SELECT:
                for p_btn in party_buttons:
                    p_btn.is_hovered = p_btn.rect.collidepoint(mouse_pos)
                    
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for p_btn in party_buttons:
                        if p_btn.is_hovered:
                            selected_party = p_btn.text
                            current_state = STATE_SCENARIO_SELECT # Jövünk a Szenárióba
                            break
                            
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
            
            # - SZCENÁRIÓ VÁLASZTÓ ÁLLAPOT -
            elif current_state == STATE_SCENARIO_SELECT:
                btn_scenario_lore.is_hovered = False # Nem lehet kattintani (Hamarosan)
                btn_scenario_custom.is_hovered = btn_scenario_custom.rect.collidepoint(mouse_pos)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_scenario_custom.is_hovered:
                        current_state = STATE_CUSTOM_SETUP
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_PARTY_SELECT
                    
            # - EGYÉNI SZÁZALÉK INPUT ÁLLAPOT -
            elif current_state == STATE_CUSTOM_SETUP:
                # Esemény továbbítása a text boxoknak
                for box in input_boxes.values():
                    box.handle_event(event)
                    
                total = sum(b.get_value() for b in input_boxes.values())
                btn_start_custom.is_hovered = btn_start_custom.rect.collidepoint(mouse_pos) if total == 100 else False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_start_custom.is_hovered and total == 100:
                        # Ha fixen 100, akkor mentsük és indítsuk
                        for p, box in input_boxes.items():
                            custom_percentages[p] = box.get_value()
                        current_state = STATE_MAP
                        
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_SCENARIO_SELECT
                    
            # - TÉRKÉP ÁLLAPOT -
            elif current_state == STATE_MAP:
                map_engine.handle_event(event)
                
                # ESC visszadob a menübe innen is
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
                    
        # --- RENDERELÉSI SZAKASZ ---
        if current_state == STATE_MENU:
            screen.fill((30, 30, 40))
            title_surf = font_large.render("POLIGAME", True, (200, 200, 200))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//4)))
            btn_play.draw(screen)
            btn_exit.draw(screen)
            
        elif current_state == STATE_PARTY_SELECT:
            screen.fill((30, 30, 40))
            title_surf = font_large.render("VÁLASSZ PÁRTOT", True, (220, 220, 100))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//6)))
            
            for p_btn in party_buttons:
                p_btn.draw(screen)
            
            help_surf = font_small.render("[ ESC ] Vissza", True, (150, 150, 150))
            screen.blit(help_surf, help_surf.get_rect(center=(WIDTH//2, HEIGHT - 50)))
            
        elif current_state == STATE_SCENARIO_SELECT:
            screen.fill((30, 30, 40))
            title_surf = font_large.render("VÁLASSZ SZCENÁRIÓT", True, (100, 200, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//4)))
            
            btn_scenario_lore.draw(screen) # Alapból inactive rajz, de a Button így is szép
            # Szürke override a "Lore" gombra (mivel Disabled)
            pygame.draw.rect(screen, (80, 80, 80), btn_scenario_lore.rect, border_radius=8)
            txt_surf = font_large.render(btn_scenario_lore.text, True, (150,150,150))
            screen.blit(txt_surf, txt_surf.get_rect(center=btn_scenario_lore.rect.center))
            
            btn_scenario_custom.draw(screen)
            
            help_surf = font_small.render("[ ESC ] Vissza", True, (150, 150, 150))
            screen.blit(help_surf, help_surf.get_rect(center=(WIDTH//2, HEIGHT - 50)))
            
        elif current_state == STATE_CUSTOM_SETUP:
            screen.fill((30, 30, 40))
            title_surf = font_large.render("EGYÉNI TÁMOGATOTTSÁG (% BEÁLLÍTÁSA)", True, (220, 220, 100))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//6)))
            
            total = sum(b.get_value() for b in input_boxes.values())
            
            draw_y = HEIGHT//2 - 150
            for p in parties:
                lbl_surf = font_large.render(p, True, (255, 255, 255))
                screen.blit(lbl_surf, (WIDTH//2 - 200, draw_y))
                input_boxes[p].rect.y = draw_y
                input_boxes[p].draw(screen)
                
                pct_surf = font_large.render("%", True, (200, 200, 200))
                screen.blit(pct_surf, (WIDTH//2 + 160, draw_y))
                draw_y += 70
                
            color_total = (50, 255, 50) if total == 100 else (255, 80, 80)
            tot_surf = font_large.render(f"ÖSSZESEN: {total} / 100%", True, color_total)
            screen.blit(tot_surf, tot_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 215)))
            
            if total == 100:
                btn_start_custom.draw(screen)
            else:
                pygame.draw.rect(screen, (80, 80, 80), btn_start_custom.rect, border_radius=8)
                txt_surf = font_large.render(btn_start_custom.text, True, (150,150,150))
                screen.blit(txt_surf, txt_surf.get_rect(center=btn_start_custom.rect.center))

            help_surf = font_small.render("Kattints a számokra az átíráshoz.  |  [ ESC ] Vissza", True, (150, 150, 150))
            screen.blit(help_surf, help_surf.get_rect(center=(WIDTH//2, HEIGHT - 50)))
            
        elif current_state == STATE_MAP:
            map_engine.draw(screen, mouse_pos)
            
            # Bal alsó sötétített háttér panel
            panel_w, panel_h = 350, 280
            
            # Alfa-csatornás transzparencia fekete hatter
            s_panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            s_panel.fill((0, 0, 0, 200))
            screen.blit(s_panel, (20, HEIGHT - panel_h - 20))
            
            y_cursor = HEIGHT - panel_h - 5
            
            if selected_party:
                party_surf = font_small.render(f"Irányított párt: {selected_party}", True, (255, 230, 100))
                screen.blit(party_surf, (35, y_cursor))
                y_cursor += 40
                
            pygame.draw.line(screen, (100, 100, 100), (35, y_cursor), (35 + panel_w - 30, y_cursor))
            y_cursor += 15
            
            # Táblázatos UI az Országos Támogatottságról a sötét panelen
            title_tamu = font_small.render("Országos Bázis (Egyéni):", True, (255, 255, 255))
            screen.blit(title_tamu, (35, y_cursor))
            y_cursor += 35
            
            # Sorban kiírva a mentett adatok:
            for p, pct in custom_percentages.items():
                p_surf = font_small.render(f"{p}", True, (200, 200, 200))
                v_surf = font_small.render(f"{pct}%", True, (50, 200, 255))
                screen.blit(p_surf, (35, y_cursor))
                screen.blit(v_surf, (35 + panel_w - 100, y_cursor))
                y_cursor += 25
            
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
