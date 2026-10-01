"""Valley imagery, Strip imagery, and OSM building footprints in the Bellagio survey frame.

Origin is the Bellagio core (survey.py): +X east, +Y north, metres.
Imagery is ESRI World Imagery. Buildings are OpenStreetMap (ODbL).
"""
import io, json, math, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

LAT0, LON0 = 36.11298, -115.17643
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574.0
UA = {'User-Agent': 'caldas-world-research/1.0 (joaoccaldas@gmail.com)'}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(ROOT, 'data')
os.makedirs(DATA, exist_ok=True)


def geo(x, y):
    return LAT0 + y / KY, LON0 + x / KX


def local(lat, lon):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def txy(lat, lon, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def fetch(url, timeout=50):
    for a in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:
            time.sleep(0.4 + a * 0.6)
    return None


def stitch(name, x0, y0, sx, sy, z, px_w):
    """Rectangle [x0, x0+sx] x [y0, y0+sy] in survey metres, north-up JPEG."""
    la0, lo0 = geo(x0, y0)
    la1, lo1 = geo(x0 + sx, y0 + sy)
    fx0, fy1 = txy(la0, lo0, z)
    fx1, fy0 = txy(la1, lo1, z)
    tx0, tx1, ty0, ty1 = int(math.floor(fx0)), int(math.floor(fx1)), int(math.floor(fy0)), int(math.floor(fy1))
    tw, th = tx1 - tx0 + 1, ty1 - ty0 + 1
    print(f'{name} tiles {tw}x{th} z{z}', flush=True)
    canvas = Image.new('RGB', (tw * 256, th * 256), (40, 36, 30))
    jobs = [(tx, ty) for tx in range(tx0, tx1 + 1) for ty in range(ty0, ty1 + 1)]
    fail = 0

    def one(job):
        tx, ty = job
        url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}'
        return tx, ty, fetch(url)

    with ThreadPoolExecutor(max_workers=12) as ex:
        for tx, ty, b in ex.map(one, jobs):
            if not b:
                fail += 1
                continue
            try:
                canvas.paste(Image.open(io.BytesIO(b)).convert('RGB'), ((tx - tx0) * 256, (ty - ty0) * 256))
            except Exception:
                fail += 1
    box = ((fx0 - tx0) * 256, (fy0 - ty0) * 256, (fx1 - tx0) * 256, (fy1 - ty0) * 256)
    px_h = max(2, int(round(px_w * sy / sx)))
    img = canvas.crop(tuple(int(round(v)) for v in box)).resize((px_w, px_h), Image.LANCZOS)
    img.save(os.path.join(DATA, name + '.jpg'), quality=86)
    meta = {'x0': x0, 'y0': y0, 'sx': sx, 'sy': sy, 'px': [px_w, px_h], 'z': z, 'failed_tiles': fail}
    json.dump(meta, open(os.path.join(DATA, name + '.json'), 'w'), indent=1)
    print(name, img.size, 'failed', fail, flush=True)
    return meta


def ring_of(geom):
    pts = []
    for p in geom:
        pts.append(local(p['lat'], p['lon']))
    if len(pts) >= 2 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1.0:
        pts = pts[:-1]
    return pts


def clean(pts, maxn=20):
    out = []
    for x, y in pts:
        if not out or math.hypot(x - out[-1][0], y - out[-1][1]) >= 1.4:
            out.append((round(x, 2), round(y, 2)))
    if len(out) > maxn:
        step = len(out) / maxn
        out = [out[int(i * step)] for i in range(maxn)]
    return out


def area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) * 0.5


GLASS_NAMES = ('mandalay', 'delano', 'aria', 'vdara', 'cosmopolitan', 'waldorf', 'veer', 'mandarin',
               'trump', 'fontainebleau', 'resorts world', 'encore', 'wynn', 'palazzo', 'venetian',
               'mirage', 'park mgm', 'new york', 'nyny', 'planet hollywood', 'horseshoe', 'paris las',
               'bally', 'caesars', 'flamingo', 'linq', 'harrah', 'cromwell', 'sahara', 'circus',
               'stratosphere', 'the strat', 'treasure island', 'ti ', 'mgm grand', 'signature',
               'marriott', 'hilton', 'four seasons')


def kind_of(name, h, levels):
    n = (name or '').lower()
    if 'excalibur' in n:
        return 'castle'
    if h >= 70 or (levels or 0) >= 20 or any(k in n for k in GLASS_NAMES):
        return 'glass'
    return 'block'


def height_of(tags, a):
    h = tags.get('height') or tags.get('building:height')
    levels = tags.get('building:levels')
    try:
        if h:
            return float(str(h).split()[0]), int(float(levels)) if levels else None
    except ValueError:
        pass
    try:
        if levels:
            return float(levels) * 3.15, int(float(levels))
    except ValueError:
        pass
    if a > 20000:
        return 16.0, None
    if a > 5000:
        return 12.0, None
    if a > 800:
        return 8.0, None
    return 5.5, None


def buildings():
    boxes = [(36.085, -115.200, 36.150, -115.155), (36.158, -115.152, 36.182, -115.132)]
    parts = []
    for s, w, n, e in boxes:
        q = f'[out:json][timeout:180];way["building"]({s},{w},{n},{e});out tags geom;'
        url = 'https://overpass-api.de/api/interpreter?data=' + urllib.parse.quote(q)
        print('overpass', s, n, flush=True)
        raw = fetch(url, timeout=180)
        if not raw:
            print('overpass failed', s)
            continue
        parts.append(json.loads(raw))
    seen = set()
    out = []
    for doc in parts:
        for el in doc.get('elements', []):
            geom = el.get('geometry')
            if not geom or len(geom) < 4:
                continue
            tags = el.get('tags') or {}
            if tags.get('building') in ('roof', 'bridge'):
                continue
            pts = clean(ring_of(geom))
            if len(pts) < 3:
                continue
            a = area(pts)
            if a < 70 or a > 400000:
                continue
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            key = (round(cx / 3), round(cy / 3), round(a / 20))
            if key in seen:
                continue
            seen.add(key)
            h, levels = height_of(tags, a)
            h = max(3.0, min(h, 360.0))
            name = tags.get('name') or tags.get('brand') or ''
            out.append({'name': name, 'h': round(h, 1), 'k': kind_of(name, h, levels),
                        'a': round(a), 'c': [round(cx, 1), round(cy, 1)], 'r': pts,
                        'src': 'height' if tags.get('height') else ('levels' if tags.get('building:levels') else 'inferred')})
    out.sort(key=lambda b: -b['a'])
    json.dump(out, open(os.path.join(DATA, 'city_buildings.json'), 'w'))
    named = [b for b in out if b['name']]
    print('buildings', len(out), 'named', len(named), flush=True)
    for b in sorted(named, key=lambda b: -b['h'])[:40]:
        print(f"  {b['h']:6.0f}m {b['k']:7} {b['name'][:40]:40} ({b['c'][0]:7.0f},{b['c'][1]:7.0f}) {b['src']}")
    return out


if __name__ == '__main__':
    # 6 km valley plate under everything outside the Bellagio orthophoto, and a sharper Strip corridor
    # from south of Mandalay Bay to the Stratosphere, plus downtown.
    stitch('city_valley', -3000, -3000, 6000, 6000, 15, 1400)
    stitch('city_strip', -700, -2700, 1600, 4700, 17, 1200)
    buildings()
