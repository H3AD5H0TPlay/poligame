"""
Poligame — Térkép Renderelő Motor

Shapely GIS geometriával és Pygame rajzolással.
- GeoJSON betöltés (NVI 106 OEVK)
- Mercator-korrekció
- Megye összevonás
- Dinamikus zoom/pan kamera
- Screen culling optimalizáció
- Tooltip a hovered területhez
"""

import json
import math
import pygame
from collections import Counter
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely.affinity import scale as shapely_scale

from engine.constants import (
    PARTY_COLORS, DEFAULT_MAP_COLOR, GEOJSON_PATH
)


class MapRenderer:
    def __init__(self, width, height, loading_callback=None):
        self.width = width
        self.height = height
        
        self.oevks = []
        self.counties = {}
        self.min_lon, self.max_lon = 999, -999
        self.min_lat, self.max_lat = 999, -999
        
        # Kamera
        self.offset_x, self.offset_y = 0, 0
        self.scale = 1.0
        self.base_scale = 1.0
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Szimuláció színek
        self.oevk_colors = {}
        self._county_colors = {}  # Cache: megye többségi szín
        
        self._hover_name = None
        self._hover_data = None
        self._selected_name = None
        self._selected_data = None
        self._selected_center = None
        self._last_geo_mouse = None
        self._drag_moved = False
        
        # O(1) hover gyorsítás és 0-lag renderelés: Cache felszínek
        self._id_surface = pygame.Surface((width, height))
        self._id_surface.set_colorkey(None) # Nincs alpha
        self._map_surface = pygame.Surface((width, height))
        self._view_dirty = True
        self._last_view_mode = None
        
        # Betűtípusok (lazily cached)
        self._font_tiny = None
        self._font_small = None
        
        self._load(loading_callback)
        self._center()
    
    @property
    def font_tiny(self):
        if self._font_tiny is None:
            self._font_tiny = pygame.font.SysFont("Segoe UI", 18)
        return self._font_tiny
    
    @property
    def font_small(self):
        if self._font_small is None:
            self._font_small = pygame.font.SysFont("Segoe UI", 24)
        return self._font_small

    def set_colors(self, colors_dict):
        """Beállítja az OEVK-k színeit. Pre-computálja a megye színeket is."""
        self.oevk_colors = colors_dict
        self._compute_county_colors()

    def _compute_county_colors(self):
        """A megye többségi színét előre kiszámítja (nem kell frame-enként)."""
        self._county_colors = {}
        for county_name in self.counties:
            county_oevk_colors = [
                self.oevk_colors.get(o['name'], DEFAULT_MAP_COLOR)
                for o in self.oevks if o['county'] == county_name
            ]
            if county_oevk_colors:
                self._county_colors[county_name] = Counter(county_oevk_colors).most_common(1)[0][0]
            else:
                self._county_colors[county_name] = (40, 55, 50)

    def _load(self, callback=None):
        with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        county_polygons = {}
        lon_ratio = math.cos(math.radians(47.16))
        total = len(data['features'])

        for idx, feature in enumerate(data['features']):
            if callback and idx % 10 == 0:
                callback(f"OEVK betöltése ({idx+1}/{total})...", 0.2 + 0.6 * idx / total)
            
            geom = shape(feature['geometry'])
            geom = make_valid(geom).buffer(0)
            geom = geom.simplify(0.0005, preserve_topology=True)
            geom = shapely_scale(geom, xfact=lon_ratio, yfact=1.0, origin=(0, 0))

            name = feature['properties']['name']
            county = name.rsplit(' ', 1)[0]
            
            bounds = geom.bounds
            self.min_lon = min(self.min_lon, bounds[0])
            self.max_lon = max(self.max_lon, bounds[2])
            self.min_lat = min(self.min_lat, bounds[1])
            self.max_lat = max(self.max_lat, bounds[3])

            self.oevks.append({
                "name": name,
                "county": county,
                "geom": geom,
                "bounds": bounds,
            })

            if county not in county_polygons:
                county_polygons[county] = []
            county_polygons[county].append(geom)

        for county, polys in county_polygons.items():
            merged = unary_union(polys)
            self.counties[county] = {
                "name": county,
                "geom": merged,
                "bounds": merged.bounds,
            }

    def _center(self):
        map_w = self.max_lon - self.min_lon
        map_h = self.max_lat - self.min_lat
        if map_w == 0 or map_h == 0:
            return
        sx = (self.width * 0.9) / map_w
        sy = (self.height * 0.9) / map_h
        self.base_scale = min(sx, sy)
        self.scale = self.base_scale
        cx = (self.min_lon + self.max_lon) / 2
        cy = (self.min_lat + self.max_lat) / 2
        self.offset_x = self.width / 2 - (cx - self.min_lon) * self.scale
        self.offset_y = self.height / 2 - (self.max_lat - cy) * self.scale

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.is_dragging = True
                self._drag_moved = False
                self.last_mouse_pos = event.pos
            elif event.button == 4:
                self._zoom(1.15, event.pos)
            elif event.button == 5:
                if self.scale > self.base_scale * 0.5:
                    self._zoom(1.0 / 1.15, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
                if not self._drag_moved:
                    # Sima kattintás: kiválasztjuk a hoverelt elemet
                    self._selected_name = self._hover_name
                    self._selected_data = self._hover_data
                    if self._hover_name:
                        elements = self.oevks if self._last_view_mode else list(self.counties.values())
                        for e in elements:
                            if e['name'] == self._hover_name:
                                self._selected_center = e['geom'].centroid
                                break
                    else:
                        self._selected_center = None
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._drag_moved = True
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.offset_x += dx
                self.offset_y += dy
                self.last_mouse_pos = event.pos
                # Panningnél NINCS _view_dirty redraw! Tiszta blittelés történik offsettel.

    def _zoom(self, factor, pos):
        lon = (pos[0] - self.offset_x) / self.scale + self.min_lon
        lat = self.max_lat - (pos[1] - self.offset_y) / self.scale
        self.scale *= factor
        self.offset_x = pos[0] - (lon - self.min_lon) * self.scale
        self.offset_y = pos[1] - (self.max_lat - lat) * self.scale
        self._view_dirty = True

    def _geo_to_screen(self, lon, lat):
        x = (lon - self.min_lon) * self.scale + self.offset_x
        y = (self.max_lat - lat) * self.scale + self.offset_y
        return x, y

    def _draw_geom(self, surface, geom, fill, border, bw):
        s, ox, oy = self.scale, self.offset_x, self.offset_y
        mlon, mlat = self.min_lon, self.max_lat
        
        def draw_poly(poly):
            coords = [((x - mlon) * s + ox, (mlat - y) * s + oy) 
                      for x, y in poly.exterior.coords]
            if len(coords) > 2:
                pygame.draw.polygon(surface, fill, coords)
                pygame.draw.lines(surface, border, True, coords, bw)
        
        if geom.geom_type == 'Polygon':
            draw_poly(geom)
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                draw_poly(poly)

    def _redraw_cache_surfaces(self, show_oevk):
        """Kirajzolja a statikus térképet és a láthatatlan ID felszínt PONTOSAN az offszetek nélkül."""
        
        map_w_px = int((self.max_lon - self.min_lon) * self.scale) + 100
        map_h_px = int((self.max_lat - self.min_lat) * self.scale) + 100
        
        if map_w_px > 6000 or map_h_px > 6000:
            return  # Failsafe extrém zoom memória limit
            
        self._id_surface = pygame.Surface((map_w_px, map_h_px))
        self._id_surface.set_colorkey(None)
        self._id_surface.fill((0, 0, 0))
        
        self._map_surface = pygame.Surface((map_w_px, map_h_px))
        self._map_surface.fill((18, 22, 35))
        self._map_surface.set_colorkey((18, 22, 35))
        
        elements = self.oevks if show_oevk else list(self.counties.values())
        s = self.scale
        mlon, mlat = self.min_lon, self.max_lat
        
        for idx, elem in enumerate(elements):
            idx_color = (idx + 1, 0, 0)
            geom = elem['geom']
            name = elem['name']
            
            if show_oevk:
                base_color = self.oevk_colors.get(name, DEFAULT_MAP_COLOR)
            else:
                base_color = self._county_colors.get(name, (40, 55, 50))
            
            border = (180, 180, 180) if not show_oevk else (80, 80, 80)
            bw = 2 if not show_oevk else 1
            
            def draw_poly(poly):
                coords = [((x - mlon) * s, (mlat - y) * s) 
                          for x, y in poly.exterior.coords]
                if len(coords) > 2:
                    pygame.draw.polygon(self._id_surface, idx_color, coords)
                    pygame.draw.polygon(self._map_surface, base_color, coords)
                    pygame.draw.lines(self._map_surface, border, True, coords, bw)
            
            if geom.geom_type == 'Polygon':
                draw_poly(geom)
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    draw_poly(poly)

    def _update_hover(self, mouse_pos, show_oevk, sim_results):
        """Pixel-tökéletes hover, figyelembe véve a pannelséget."""
        self._hover_name = None
        self._hover_data = None
        
        # Átszámítjuk az egér pozícióját aszerint, ahová a felszínt is blit-eljük
        idx_x = int(mouse_pos[0] - self.offset_x)
        idx_y = int(mouse_pos[1] - self.offset_y)
        
        if not (0 <= idx_x < self._id_surface.get_width() and 0 <= idx_y < self._id_surface.get_height()):
            return
            
        color = self._id_surface.get_at((idx_x, idx_y))
        idx = color[0] - 1
        
        elements = self.oevks if show_oevk else list(self.counties.values())
        if 0 <= idx < len(elements):
            name = elements[idx]['name']
            self._hover_name = name
            if sim_results:
                target_dict = sim_results.get("oevk_pcts", {}) if show_oevk else sim_results.get("county_pcts", {})
                if name in target_dict:
                    self._hover_data = target_dict[name]

    def draw(self, surface, mouse_pos, show_oevk=False, sim_results=None):
        if self._view_dirty or show_oevk != self._last_view_mode:
            self._redraw_cache_surfaces(show_oevk)
            self._view_dirty = False
            self._last_view_mode = show_oevk
            
        surface.fill((18, 22, 35))
        
        # O(1) háttér renderelés eltolással (így drag esetén nem kell frissíteni!)
        surface.blit(self._map_surface, (self.offset_x, self.offset_y))
        
        # Hover frissítése
        self._update_hover(mouse_pos, show_oevk, sim_results)
        
        elements = self.oevks if show_oevk else list(self.counties.values())
        
        # O(1) redraw ONLY the single hovered polygon with a glow effect
        if self._hover_name:
            for elem in elements:
                if elem['name'] == self._hover_name:
                    name = elem['name']
                    if show_oevk:
                        base_color = self.oevk_colors.get(name, DEFAULT_MAP_COLOR)
                    else:
                        base_color = self._county_colors.get(name, (40, 55, 50))
                    
                    fill = tuple(min(255, c + 35) for c in base_color)
                    border = (180, 180, 180) if not show_oevk else (80, 80, 80)
                    bw = 2 if not show_oevk else 1
                    
                    def draw_glow(poly):
                        # A glow renderelése a surface-re megy (pozícionálással)
                        coords = [((x - self.min_lon) * self.scale + self.offset_x, 
                                   (self.max_lat - y) * self.scale + self.offset_y) 
                                  for x, y in poly.exterior.coords]
                        if len(coords) > 2:
                            pygame.draw.polygon(surface, fill, coords)
                            pygame.draw.lines(surface, border, True, coords, bw)
                    
                    if elem['geom'].geom_type == 'Polygon':
                        draw_glow(elem['geom'])
                    elif elem['geom'].geom_type == 'MultiPolygon':
                        for poly in elem['geom'].geoms:
                            draw_glow(poly)
                    break
        
        # Kiválasztott elem infó panelje (ha kattintott), a Vármegye / OEVK földrajzi közepén!
        if self._selected_name and self._selected_center:
            cx, cy = self._geo_to_screen(self._selected_center.x, self._selected_center.y)
            self._draw_tooltip(surface, (cx, cy), self._selected_name, self._selected_data)

    def _draw_tooltip(self, surface, pos, name, data):
        lines = [name]
        if data:
            winner = max(data, key=data.get)
            lines.append(f"Győztes: {winner}")
            for p in sorted(data, key=data.get, reverse=True):
                lines.append(f"  {p}: {data[p]:.1f}%")
        
        max_w = max(self.font_small.size(l)[0] for l in lines) + 20
        h = len(lines) * 26 + 10
        
        # Tooltip a kattintás pozíciója felett
        tx = min(pos[0] + 15, self.width - max_w - 10)
        ty = max(pos[1] - h - 10, 10)
        
        tip = pygame.Surface((max_w, h), pygame.SRCALPHA)
        tip.fill((10, 10, 20, 230))
        pygame.draw.rect(tip, (200, 170, 60), (0, 0, max_w, h), 1, border_radius=4)
        
        for i, line in enumerate(lines):
            color = (255, 230, 100) if i == 0 else (220, 220, 220)
            txt = self.font_tiny.render(line, True, color)
            tip.blit(txt, (10, 5 + i * 26))
        
        surface.blit(tip, (tx, ty))
