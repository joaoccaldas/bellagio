"""Luxor evidence: ESRI imagery tiles (z19) stitched into a local-frame square (Bellagio survey frame), OSM extract."""
import io, math, json, os, sys, time, urllib.request
from PIL import Image
LAT0, LON0 = 36.11298, -115.17643          # Bellagio core = Las Vegas city frame origin
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110574.0
UA = {'User-Agent': 'caldas-world-research/1.0 (joaoccaldas@gmail.com)'}
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
def geo(x, y): return LAT0 + y / KY, LON0 + x / KX
def txy(lat, lon, z):
    n = 2 ** z; return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
def fetch(u):
    for a in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()
        except Exception: time.sleep(1 + a)
def stitch(name, cx, cy, half, z, px):
    la0, lo0 = geo(cx - half, cy - half); la1, lo1 = geo(cx + half, cy + half)
    fx0, fy1 = txy(la0, lo0, z); fx1, fy0 = txy(la1, lo1, z)
    tx0, tx1, ty0, ty1 = int(fx0), int(fx1), int(fy0), int(fy1)
    m = Image.new('RGB', ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            b = fetch(f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}')
            if b: m.paste(Image.open(io.BytesIO(b)).convert('RGB'), ((tx - tx0) * 256, (ty - ty0) * 256))
    box = ((fx0 - tx0) * 256, (fy0 - ty0) * 256, (fx1 - tx0) * 256, (fy1 - ty0) * 256)
    img = m.crop(tuple(int(round(v)) for v in box)).resize((px, px), Image.LANCZOS)
    img.save(os.path.join(D, name + '.jpg'), quality=92)
    json.dump({'center': [cx, cy], 'half': half, 'px': px, 'mpp': 2 * half / px, 'z': z}, open(os.path.join(D, name + '.json'), 'w'))
    print(name, px, round(2 * half / px, 3), 'm/px')
if __name__ == '__main__':
    stitch('luxor_sat', 30.0, -1900.0, 380.0, 19, 2560)          # pyramid, towers, sphinx, pool, Strip frontage
    la0, lo0 = geo(-350, -2300); la1, lo1 = geo(420, -1500)
    b = fetch(f'https://api.openstreetmap.org/api/0.6/map?bbox={lo0},{la0},{lo1},{la1}')
    open(os.path.join(D, 'luxor.osm'), 'wb').write(b); print('osm', len(b))
