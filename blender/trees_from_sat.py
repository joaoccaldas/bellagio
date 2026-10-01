"""Detect tree canopies in the satellite frame -> data/trees.json  [x, y, canopy_radius] metres.

Vegetation mask (G dominant, not lake teal) -> 1 m grid density -> local maxima >= 4.5 m apart.
Evidence: data/hi_core.jpg (ESRI World Imagery, 0.2227 m/px)."""
import json, sys, os
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import survey as S
from geo_2d import inside
here = os.path.join(os.path.dirname(__file__), '..', 'data')
img = Image.open(f'{here}/hi_core.jpg').convert('RGB')
im = np.asarray(img).astype(np.int16)
R, G, B = im[..., 0], im[..., 1], im[..., 2]
L = im.sum(-1).astype(np.float32) / 3
from scipy.ndimage import uniform_filter
var = uniform_filter(L * L, 7) - uniform_filter(L, 7) ** 2
tex = np.sqrt(np.clip(var, 0, None))
veg = ((G > R + 3) & (G > B + 6) & (R < 130) & (tex > 7)).astype(np.uint8) * 255
veg = np.asarray(Image.fromarray(veg).filter(ImageFilter.MedianFilter(5))) > 127
# resample to ~1 m cells (4.49 px)
k = 4
h, w = veg.shape[0] // k, veg.shape[1] // k
d = veg[:h * k, :w * k].reshape(h, k, w, k).mean(axis=(1, 3))
ds = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
mx = np.asarray(Image.fromarray((ds * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))).astype(np.float32) / 255
peaks = np.argwhere((ds >= mx - 1e-3) & (ds > .22))
def near_edge(poly, p, d):
    import math
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        vx, vy = x2 - x1, y2 - y1
        t = max(0, min(1, ((p[0] - x1) * vx + (p[1] - y1) * vy) / (vx * vx + vy * vy + 1e-9)))
        if math.hypot(x1 + vx * t - p[0], y1 + vy * t - p[1]) < d:
            return True
    return False
BUILDINGS = [S.THEATER, S.PARKING, S.CONSERVATORY, S.PORTE] + [S.PL([(a, b), (c, b), (c, d), (a, d)]) for a, b, c, d, *_ in S.VILLAGE]
BUILDINGS += [S.PL([(155, 195), (520, 195), (520, 660), (155, 660)]), S.PL([(800, 250), (985, 250), (985, 1250), (800, 1250)])]
def near_line(pts, p, d):
    return near_edge(list(pts) + list(reversed(pts)), p, d)
LINES = [(S.WING_N, 13), (S.WING_S, 13), (S.WING_W, 14), (S.SPA, 15)]
out = []
for py, px in peaks:
    ox, oy = (px + .5) * k, (py + .5) * k           # original px
    x, y = S.P(ox / 1.024, oy / 1.024)
    if inside(S.LAKE, (x, y)) or near_edge(S.LAKE, (x, y), 3.0):
        continue
    if any(inside(p, (x, y)) for p in BUILDINGS):
        continue
    if any(near_line(line, (x, y), hw) for line, hw in LINES) or abs(x - S.STRIP_X) < S.STRIP_W / 2:
        continue
    if any((x - a) ** 2 + (y - b) ** 2 < 4.5 ** 2 for a, b, _ in out[-40:]):
        continue
    out.append((round(x, 1), round(y, 1), round(2.0 + 3.5 * float(ds[py, px]), 1)))
print('trees', len(out))
json.dump(out, open(f'{here}/trees.json', 'w'))
# overlay for evidence
ov = img.copy().resize((1024, 1024))
from PIL import ImageDraw
dr = ImageDraw.Draw(ov)
for x, y, r in out:
    dx, dy = x / S.MPP + S.CX, S.CY - y / S.MPP
    ox, oy = dx * 1.024 / 2, dy * 1.024 / 2
    dr.ellipse((ox - 3, oy - 3, ox + 3, oy + 3), outline=(255, 0, 255))
ov.save(f'{here}/trees_overlay.jpg')
