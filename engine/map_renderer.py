"""
Poligame — Térkép Renderelő Motor

Shapely GIS geometriával és Pygame rajzolással.
- GeoJSON betöltés (NVI 106 OEVK)
- Mercator-korrekció
- Megye összevonás
- Dinamikus zoom/pan kamera
- Screen culling optimalizáció
- OEVK/Megye nézetváltás zoom szint alapján
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
        """Beállítja az OEVK-k színeit a szimuláció eredményéből."""
        self.oevk_colors = colors_dict

    def _load(self, callback=None):
        with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        county_polygons = {}
        lon_ratio = math.cos(math.radians(47.16))  # Magyarország közepén
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
            
            minx, miny, maxx, maxy = geom.bounds
            self.min_lon = min(self.min_lon, minx)
            self.max_lon = max(self.max_lon, maxx)
            self.min_lat = min(self.min_lat, miny)
            self.max_lat = max(self.max_lat, maxy)

            self.oevks.append({"name": name, "county": county, "geom": geom})

            if county not in county_polygons:
                county_polygons[county] = []
            county_polygons[county].append(geom)

        for county, polys in county_polygons.items():
            self.counties[county] = {
                "name": county,
                "geom": unary_union(polys)
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

    # --- Kamera Kezelés ---

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.is_dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4:
                self._zoom(1.15, event.pos)
            elif event.button == 5:
                if self.scale > self.base_scale * 0.5:
                    self._zoom(1.0 / 1.15, event.pos)
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

    def _zoom(self, factor, pos):
        lon = (pos[0] - self.offset_x) / self.scale + self.min_lon
        lat = self.max_lat - (pos[1] - self.offset_y) / self.scale
        self.scale *= factor
        self.offset_x = pos[0] - (lon - self.min_lon) * self.scale
        self.offset_y = pos[1] - (self.max_lat - lat) * self.scale

    def _geo_to_screen(self, lon, lat):
        x = (lon - self.min_lon) * self.scale + self.offset_x
        y = (self.max_lat - lat) * self.scale + self.offset_y
        return x, y

    # --- Rajzolás ---

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

    def draw(self, surface, mouse_pos, show_oevk=False, sim_results=None):
        surface.fill((18, 22, 35))
        
        hovered_name = None
        hovered_data = None
        
        geo_x = (mouse_pos[0] - self.offset_x) / self.scale + self.min_lon
        geo_y = self.max_lat - (mouse_pos[1] - self.offset_y) / self.scale
        geo_mouse = Point(geo_x, geo_y)
        
        elements = self.oevks if show_oevk else list(self.counties.values())
        
        for elem in elements:
            geom = elem['geom']
            minx, miny, maxx, maxy = geom.bounds
            
            # Screen culling
            sl, sb = self._geo_to_screen(minx, miny)
            sr, st = self._geo_to_screen(maxx, maxy)
            if sr < 0 or sl > self.width or sb < 0 or st > self.height:
                continue
            
            # Hover check
            is_hovered = False
            if minx <= geo_x <= maxx and miny <= geo_y <= maxy:
                if geom.contains(geo_mouse):
                    is_hovered = True
            
            # Színezés
            if show_oevk:
                base_color = self.oevk_colors.get(elem['name'], DEFAULT_MAP_COLOR)
            else:
                county_name = elem['name']
                county_oevk_colors = [
                    self.oevk_colors.get(o['name'], DEFAULT_MAP_COLOR)
                    for o in self.oevks if o['county'] == county_name
                ]
                if county_oevk_colors:
                    base_color = Counter(county_oevk_colors).most_common(1)[0][0]
                else:
                    base_color = (40, 55, 50)
            
            if is_hovered:
                hovered_name = elem['name']
                if sim_results and elem['name'] in sim_results.get("oevk_pcts", {}):
                    hovered_data = sim_results["oevk_pcts"][elem['name']]
                fill = tuple(min(255, c + 35) for c in base_color)
            else:
                fill = base_color
            
            border = (180, 180, 180) if not show_oevk else (80, 80, 80)
            bw = 2 if not show_oevk else 1
            self._draw_geom(surface, geom, fill, border, bw)
        
        # Tooltip
        if hovered_name:
            self._draw_tooltip(surface, mouse_pos, hovered_name, hovered_data)

    def _draw_tooltip(self, surface, pos, name, data):
        lines = [name]
        if data:
            winner = max(data, key=data.get)
            lines.append(f"Győztes: {winner}")
            for p in sorted(data, key=data.get, reverse=True):
                lines.append(f"  {p}: {data[p]:.1f}%")
        
        max_w = max(self.font_small.size(l)[0] for l in lines) + 20
        h = len(lines) * 26 + 10
        
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
