"""
Poligame — Konstansok és Globális Konfiguráció

Minden szín, pártadat, méret és verzió itt van definiálva.
Egyetlen forrás az igazságra (Single Source of Truth).
"""

import sys
import os

# ============================================================================
#  VERZIÓ
# ============================================================================
VERSION = "0.2.0-alpha"
GAME_TITLE = "Poligame"
GAME_SUBTITLE = "Magyar Belpolitikai Stratégiai Szimulátor"

# ============================================================================
#  ÚTVONALAK
# ============================================================================
def get_base_path():
    """Visszaadja a projekt gyökérkönyvtárát, PyInstaller frozen exe-ből is."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_PATH = get_base_path()
DATA_DIR = os.path.join(BASE_PATH, "data")
GEOJSON_PATH = os.path.join(DATA_DIR, "oevk.json")
ELECTION_DATA_PATH = os.path.join(DATA_DIR, "2024_ep.json")

# ============================================================================
#  PÁRTOK
# ============================================================================
PARTIES = ["Tisza", "Fidesz", "Mi Hazánk", "MKKP", "DK"]

PARTY_COLORS = {
    "Fidesz":    (255, 140, 0),
    "Tisza":     (0, 160, 60),
    "Mi Hazánk": (50, 50, 50),
    "MKKP":      (200, 30, 30),
    "DK":        (30, 80, 200),
}

DEFAULT_MAP_COLOR = (60, 80, 70)

# ============================================================================
#  UI SZÍNEK (HoI IV stílus)
# ============================================================================
BG_DARK      = (15, 18, 28)
BG_PANEL     = (10, 14, 24)
GOLD_ACCENT  = (200, 170, 60)
TEXT_PRIMARY  = (230, 230, 240)
TEXT_SECONDARY = (120, 120, 140)
TEXT_MUTED    = (80, 80, 100)
BORDER_LIGHT = (80, 80, 100)
BORDER_DARK  = (50, 50, 70)

COLOR_SUCCESS = (80, 230, 80)
COLOR_ERROR   = (230, 80, 80)

# ============================================================================
#  VÁLASZTÁSI RENDSZER PARAMÉTEREK
# ============================================================================
TOTAL_MANDATES = 199
OEVK_COUNT = 106
LIST_MANDATES = 92        # 199 - 106 = 93 (a nemzetiségit külön adjuk)
PARLIAMENT_THRESHOLD = 5  # 5%-os bejutási küszöb

# Határon túli levélszavazatok becslése (21K módszertan)
MAIL_VOTES = {
    "Fidesz":    250000,
    "Tisza":     50000,
    "Mi Hazánk": 5000,
    "DK":        1000,
    "MKKP":      1000,
}

# Becsült hazai szavazók (relatív számításhoz)
TOTAL_DOMESTIC_VOTERS = 5_000_000
OEVK_AVG_VOTERS = TOTAL_DOMESTIC_VOTERS / OEVK_COUNT

# +1 nemzetiségi mandátum (eddigi gyakorlat szerint Fidesz)
NATIONALITY_MANDATE_PARTY = "Fidesz"
