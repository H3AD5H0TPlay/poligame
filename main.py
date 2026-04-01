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
# Mivel beállítottuk, hogy a .exe kicsomagolása alatt is már legyen egy képkocka, 
# amint elérjük a Pygame-et szoftveresen be kell zárni azt az ablakot.
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
        
        # Panning állapot
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

        # Közép-Szélesség kiszámítása az eltorzult (nyomott) magyar térkép javításához (Mercator hatás)
        # Magyarország kb. 47 fok szélességen van, 1 lon fok egyenlő cos(47) lat fokkal.
        HUNGARY_CENTER_LAT = 47.16 
        lon_ratio = math.cos(math.radians(HUNGARY_CENTER_LAT))

        # OEVK adatok feldolgozása
        for feature in data['features']:
            geom = shape(feature['geometry'])
            geom = make_valid(geom).buffer(0) # Topológiai hibák ("TopologyException") javítása
            
            # 1. OPTIMALIZÁCIÓ (LAG) - Geometriai részletesség butítása (100 méteres pontosságra), vizuálisan észrevehetetlen, de 90%-kal kevesebb számítás!
            geom = geom.simplify(0.0005, preserve_topology=True) 
            
            # 2. OPTIMALIZÁCIÓ (NYOMOTT KÉP) - A szélességi/hosszúsági arányok fixálása
            geom = shapely_scale(geom, xfact=lon_ratio, yfact=1.0, origin=(0, 0))

            name = feature['properties']['name']
            
            # Formátum: "MegyeNév Szám" -> pl. "Zala 01" vagy "Borsod-Abaúj-Zemplén 04"
            county_name = name.rsplit(' ', 1)[0]
            
            # Határok kinyerése a centering-hez
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

            # Csoportosítás egybeolvasztáshoz (Megyék)
            if county_name not in county_polygons:
                county_polygons[county_name] = []
            county_polygons[county_name].append(geom)

        # Shapely összeolvasztja a kerületeket megyévé a térkép alapján
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

        # Kezdetben 90%-át kitölti a képernyőnek az egybefüggő térkép
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
            if event.button == 1: # Bal klikk húzáshoz
                self.is_dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4: # Görgő fel (Zoom In)
                self._zoom(1.2, event.pos)
            elif event.button == 5: # Görgő le (Zoom Out)
                if self.scale > self.base_scale * 0.5: # Ne lehessen túlzottan kizoomolni
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
        # Zoomolás az egér pozíciója körül (szabályos GIS kamera logika)
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
        # OPTIMALIZÁCIÓ: Ciklusokon belüli függvényhívás (`geo_to_screen`) megölte a teljesítményt (LAG).
        # Helyette a számítást egyenesen beépítjük egy lokális villámgyors Python C-optimalizált list comprehensionbe!
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
        # Térkép háttere (pl. sötétkék "víz")
        surface.fill((25, 30, 45))

        hovered_name = None
        # Földrajzi pozíció az egér alatt (Point-in-Polygon teszthez)
        geo_x = (mouse_pos[0] - self.offset_x) / self.scale + self.min_lon
        geo_y = self.max_lat - (mouse_pos[1] - self.offset_y) / self.scale
        geo_mouse = Point(geo_x, geo_y)
        
        # ZOOM_THRESHOLD: 2.5-szeres nagyítás felett már OEVK-k, alatta puszta Megyék
        show_oevk = self.scale > (self.base_scale * 2.5)

        element_list = self.oevks if show_oevk else self.counties.values()
        
        for elem in element_list:
            geom = elem['geom']
            minx, miny, maxx, maxy = geom.bounds
            
            # --- 3. OPTIMALIZÁCIÓ (OEVK LAG): SCREEN CULLING (Megjelenítés elrejtése a képernyőn kívül) ---
            # Ha felzoomolunk, csak a látható OEVK-kat számítjuk ki és rajzoljuk le! Ami kiment a képből, kidobjuk erre a képkockára.
            screen_left, screen_bottom = self.geo_to_screen(minx, miny)
            screen_right, screen_top = self.geo_to_screen(maxx, maxy)
            
            # (Y tengely fordítva van földrajzilag és a Pygame-ben, ezért a top/bottom ellenőrzés trükkös)
            if screen_right < 0 or screen_left > WIDTH or screen_bottom < 0 or screen_top > HEIGHT:
                continue # Egyszerűen átugorjuk a kirajzolást (Ez adja vissza a sima 60 FPS-t bezoomoláskor!)
            
            is_hovered = False
            
            # Csak akkor végzünk pontos shapely elemzést, ha az egerünk a négyzetes (Bounding box) határon belül van (Optimalizáció!)
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

        # UI sáv kirajzolása a Hover infóhoz
        if hovered_name:
            # Követi az egeret
            infobox = font_small.render(hovered_name, True, (255, 255, 255))
            ib_rect = infobox.get_rect(midbottom=(mouse_pos[0], mouse_pos[1] - 15))
            
            # Sötét háttér a szövegnek
            bg_rect = ib_rect.copy()
            bg_rect.inflate_ip(10, 10)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=4)
            surface.blit(infobox, ib_rect)

# Adatok betöltése
map_engine = MapRenderer("data/oevk.json")


# --- UI GOMBOK ÉS ÁLLAPOTGÉP ---
STATE_MENU = 0
STATE_MAP = 1
current_state = STATE_MENU

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

def main():
    global current_state
    clock = pygame.time.Clock()
    
    btn_play = Button(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 60, "Játék")
    btn_exit = Button(WIDTH//2 - 150, HEIGHT//2 + 40, 300, 60, "Kilépés")
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if current_state == STATE_MENU:
                btn_play.is_hovered = btn_play.rect.collidepoint(mouse_pos)
                btn_exit.is_hovered = btn_exit.rect.collidepoint(mouse_pos)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play.is_hovered:
                        current_state = STATE_MAP # Térkép betöltése!
                    if btn_exit.is_hovered:
                        pygame.quit()
                        sys.exit()
                        
            elif current_state == STATE_MAP:
                # Főleg pannelést (bal klikk) és zoomolást (görgő) kezel
                map_engine.handle_event(event)
                
                # ESC visszadob a menübe
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
                        
        # Renderelés állapotfüggően
        if current_state == STATE_MENU:
            screen.fill((30, 30, 40))
            title_surf = font_large.render("POLIGAME", True, (200, 200, 200))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//4)))
            btn_play.draw(screen)
            btn_exit.draw(screen)
            
        elif current_state == STATE_MAP:
            map_engine.draw(screen, mouse_pos)
            
            # Súgó a jobb felső sarokban
            help_surf = font_small.render("[ ESC ] Vissza a menübe | [ Bal Klikk ] Kamera húzása | [ Görgő ] Nagyítás / OEVK-k megtekintése", True, (200, 200, 200))
            screen.blit(help_surf, (20, 20))
            
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
