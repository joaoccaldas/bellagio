"""Footprints the world builds for 30 October 2022.

Reads the current OpenStreetMap extract and replaces anything that was not
there, or not yet finished, on that day. city.py extrudes whatever
built_footprints() returns. No Blender import, so the check can run it directly.
"""
import json, os

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, '..', 'data')

# Official Horseshoe name was 15 Dec 2022. On 30 Oct the resort was still Bally's.
# Review-Journal, 13 Dec 2022: rebrand launches 15 Dec 2022.
RENAME = (
    ('Horseshoe Las Vegas', "Bally's Las Vegas"),
)


def _rename(name):
    for old, new in RENAME:
        if name.startswith(old):
            return new + name[len(old):]
    # "Horseshoe/Paris Las Vegas" is the same resort, still Bally's on this date.
    if 'horseshoe' in name.lower() and 'las vegas' in name.lower():
        return name.replace('Horseshoe', "Bally's").replace('horseshoe', "Bally's")
    # The Cromwell kept that name until the Vanderpump rebrand in 2026.
    if name.lower().startswith('the vanderpump'):
        return 'The Cromwell'
    return name


def _drop(name):
    n = name.lower()
    if n == 'sphere' or n.startswith('sphere '):
        return True  # exterior still under construction; opened September 2023
    if 'hard rock' in n or 'guitar tower' in n:
        return True  # the Mirage was still open; Hard Rock bought it in December 2022
    if 'grand prix' in n or 'formula 1' in n or 'formula one' in n or n.startswith('f1 '):
        return True  # no street circuit yet; first race November 2023
    if n == 'new las vegas stadium':
        return True  # the ballpark on the Tropicana site did not exist; the hotel was still open
    return False


def _inside(x, y, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            c = not c
        j = i
    return c


# Towers that were open on 30 Oct 2022 but whose OSM outline is only the low podium.
MIN_HEIGHT = {
    'New York New York Hotel and Casino': 161.2,
    'Hotel MGM Grand Las Vegas': 89.3,  # 293 ft, 30 floors, Skyscraper Center
    'Caesars Palace': 88.0,
    'Aria Resort & Casino': 182.9,
    'Excalibur Hotel': 79.5,
    'Excalibur Hotel & Casino': 79.5,
    'Mandalay Bay': 146.0,
    'Mandalay Bay Resort & Casino': 146.0,
    'Delano Las Vegas': 145.0,
    'Treasure Island Hotel and Casino': 112.0,
    'Circus Circus Las Vegas': 90.0,
    'Resorts World Las Vegas': 145.0,
    'Flamingo Las Vegas': 85.0,
    'Paris Las Vegas': 15.8,  # podium (hotel tower is Le Boulevard At Paris, 112m)
    'The Cromwell': 45.0,
    "Harrah's Showroom": 60.0,
    'The LINQ Hotel + Experience': 63.0,
    'Stratosphere Tower': 350.0,
    'The Strat': 350.0,
    'T-Mobile Arena': 36.0,
    'Vdara': 176.0,
    'Planet Hollywood Resort and Casino': 122.0,
}


def _lift(item):
    name = item.get('name') or ''
    floor = MIN_HEIGHT.get(name)
    if not floor:
        nlow = name.lower()
        for k, v in MIN_HEIGHT.items():
            if k.lower() in nlow or nlow in k.lower():
                floor = v
                break
    item = dict(item)
    if floor and item['h'] < floor:
        item['h'] = floor
        item['src'] = 'published'

    nlow = name.lower()
    if any(g in nlow for g in ('mandalay', 'mirage', 'wynn', 'encore')):
        item['k'] = 'gold'
    elif 'excalibur' in nlow:
        item['k'] = 'castle'
    elif any(b in nlow for b in ('caesar', 'augustus', 'octavius', 'forum shops', 'colosseum', 'tropicana')):
        item['k'] = 'block'
    elif any(g in nlow for g in ('aria', 'cosmopolitan', 'new york', 'mgm grand', 'planet hollywood', 'resorts world', 'strat')):
        item['k'] = 'glass'
    return item


def built_footprints(buildings_path=None, standing_path=None):
    """The list city.massing extrudes. Each item has name, h, k, c, r."""
    buildings_path = buildings_path or os.path.join(DATA, 'city_buildings.json')
    standing_path = standing_path or os.path.join(DATA, 'standing_2022_10_30.json')
    raw = json.load(open(buildings_path))
    standing = json.load(open(standing_path)) if os.path.exists(standing_path) else []
    rings = [p['r'] for p in standing]
    out = []
    for b in raw:
        name = b.get('name') or ''
        if _drop(name):
            continue
        cx, cy = b['c']
        if any(_inside(cx, cy, ring) for ring in rings):
            continue  # 2026 construction sitting on a 2022 resort footprint
        item = dict(b)
        item['name'] = _rename(name)
        out.append(_lift(item))
    out.extend(standing)
    return out
