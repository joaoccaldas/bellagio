"""Procedural albedo textures for interior floors (baked into the lightmaps; not shipped)."""
import numpy as np
from PIL import Image
import os
DATA = os.path.join(os.path.dirname(__file__), '..', 'data')


def _grid(w, h, W, H):
    x = (np.arange(w) + .5) / w * W
    y = (np.arange(h) + .5) / h * H
    return np.meshgrid(x, y)


def lobby_floor(W=44.0, H=24.0, res=2048):
    """Cream marble field, dark-green / terracotta border bands, radiating medallion under the Chihuly."""
    w, h = res, int(res * H / W)
    X, Y = _grid(w, h, W, H)
    rng = np.random.default_rng(3)
    # marble veining
    n = np.zeros_like(X)
    for k, a in ((1.3, .5), (3.1, .25), (7.7, .12), (17.0, .06)):
        ph = rng.random(4) * 10
        n += a * np.sin(X * k * .7 + Y * k * .3 + 3 * np.sin(Y * k * .21 + ph[0]) + ph[1])
    vein = np.exp(-np.abs(np.sin(n * 2.2)) * 18)
    base = np.stack([.86 - .05 * vein, .80 - .06 * vein, .70 - .07 * vein], -1)
    img = base.copy()
    # 1.2 m tile joints
    jx = np.abs(((X / 1.2) % 1) - .5) > .493
    jy = np.abs(((Y / 1.2) % 1) - .5) > .493
    img[jx | jy] *= .82
    # border bands
    d = np.minimum.reduce([X, W - X, Y, H - Y])
    band = (d > .6) & (d < 1.0)
    img[band] = [.10, .22, .15]
    band2 = (d > 1.1) & (d < 1.3)
    img[band2] = [.55, .22, .12]
    # medallion (radiating star + rings) centred where the Chihuly hangs
    cx, cy = W / 2, H / 2
    r = np.hypot(X - cx, Y - cy)
    a = np.arctan2(Y - cy, X - cx)
    ring = (np.abs(r - 3.6) < .18) | (np.abs(r - 5.4) < .12) | (np.abs(r - 1.2) < .1)
    star = (r < 3.5) & (np.abs(np.cos(a * 8)) ** 6 * 3.4 > r * .9)
    img[star] = [.60, .30, .15]
    img[(r < 3.5) & ~star & (np.cos(a * 16) > .6) & (r > 1.3)] = [.18, .30, .22]
    img[ring] = [.08, .08, .07]
    return img


def scroll_floor(W=42.0, H=32.0, res=2048):
    """Conservatory: cream marble with black scroll / spiral mosaic lines (as photographed)."""
    w, h = res, int(res * H / W)
    X, Y = _grid(w, h, W, H)
    img = np.ones((h, w, 3)) * np.array([.84, .79, .70])
    rng = np.random.default_rng(9)
    n = np.sin(X * .9 + 2 * np.sin(Y * .7)) + .5 * np.sin(Y * 2.3 + 1.7 * np.sin(X * 1.9))
    img *= (1 - .05 * np.exp(-np.abs(np.sin(n * 3)) * 12))[..., None]
    # blended spiral phase field: each centre contributes a spiral phase, weighted by a gaussian;
    # contour lines of the blend coil into spirals at centres and flow as vines between them
    cx = []
    for gx in np.arange(1.5, W, 3.3):
        for gy in np.arange(1.5, H, 3.3):
            cx.append((gx + rng.uniform(-.9, .9), gy + rng.uniform(-.9, .9), rng.choice([-1, 1]), rng.uniform(.7, 1.3)))
    num = np.zeros_like(X)
    den = np.zeros_like(X) + 1e-6
    for gx, gy, sgn, sc in cx:
        dx, dy = X - gx, Y - gy
        r = np.hypot(dx, dy)
        th = np.arctan2(dy, dx) * sgn
        wgt = np.exp(-(r / (1.1 * sc)) ** 2 * 2.2)
        num += wgt * (r / (.36 * sc) - th / (2 * np.pi))
        den += wgt
    ph = num / den
    line = (np.abs((ph % 1) - .5) < .055) & (den > .02)
    # secondary fine scroll where weights are weak (the flowing vine lines)
    line |= (den < .02) & (np.abs(((Y + .5 * np.sin(X * 1.2)) / 1.6) % 1 - .5) < .02)
    img[line] = [.06, .06, .06]
    return img


def save(name, img):
    Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)).save(os.path.join(DATA, name), quality=93)


if __name__ == '__main__':
    save('floor_lobby.jpg', lobby_floor())
    save('floor_conservatory.jpg', scroll_floor())
    print('ok')


def parquet(W=8.0, res=1024):
    """Herringbone oak, 0.6 x 0.09 m boards (tileable, W metres per tile)."""
    X, Y = _grid(res, res, W, W)
    bw, bl = .09, .54
    u = (X + Y) / np.sqrt(2)
    v = (X - Y) / np.sqrt(2)
    col = np.floor(u / bl)
    k = np.where(col % 2 == 0, (v + col * bw) / bw, (v - col * bw) / bw)
    board = np.floor(k) + col * 1000
    rng = np.random.default_rng(1)
    tone = (np.sin(board * 12.9898) * 43758.5453) % 1
    grain = .5 + .5 * np.sin(u * 180 + 3 * np.sin(v * 40 + board))
    base = np.stack([.42 + .10 * tone, .25 + .06 * tone, .12 + .03 * tone], -1) * (.9 + .1 * grain[..., None])
    edge = (np.abs((k % 1) - .5) > .47) | (np.abs(((u / bl) % 1) - .5) > .485)
    base[edge] *= .6
    return base


def checker(W=4.0, res=1024, tile=.8):
    X, Y = _grid(res, res, W, W)
    c = ((np.floor(X / tile) + np.floor(Y / tile)) % 2).astype(bool)
    n = np.sin(X * 3.1 + 2 * np.sin(Y * 2.3)) * .5 + .5
    vein = np.exp(-np.abs(np.sin((X * .8 + Y * .5 + n * 2) * 4)) * 14)
    white = np.stack([.88 - .1 * vein, .87 - .1 * vein, .84 - .1 * vein], -1)
    black = np.stack([.03 + .12 * vein, .03 + .12 * vein, .035 + .12 * vein], -1)
    img = np.where(c[..., None], black, white)
    j = (np.abs((X / tile) % 1 - .5) > .495) | (np.abs((Y / tile) % 1 - .5) > .495)
    img[j] = .45
    return img


def travertine(W=6.0, res=1024):
    X, Y = _grid(res, res, W, W)
    n = np.zeros_like(X)
    for f, a in ((1.1, .5), (4.3, .25), (13.0, .12), (37.0, .07)):
        n += a * np.sin(Y * f * 3 + 1.3 * np.sin(X * f * .7))
    pits = (np.sin(X * 71 + np.sin(Y * 53) * 5) * np.sin(Y * 67) > .96)
    img = np.stack([.80 + .05 * n, .72 + .05 * n, .60 + .05 * n], -1)
    img[pits] *= .7
    j = (np.abs((X / 1.2) % 1 - .5) > .496) | (np.abs((Y / .6) % 1 - .5) > .492)
    img[j] *= .85
    return img


def fresco(res=1024):
    """Sky fresco for the salon vault: fbm cumulus (blurred multi-octave noise), warm horizon, gilded rim."""
    from PIL import ImageFilter
    rng = np.random.default_rng(4)
    acc = np.zeros((res, res))
    for octv, amp in ((8, .55), (16, .25), (32, .12), (64, .06), (128, .03)):
        n = rng.random((octv, octv))
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((res, res), Image.BICUBIC).filter(ImageFilter.GaussianBlur(res / octv / 3))
        acc += amp * (np.asarray(im) / 255.0)
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    cloud = np.clip((acc - .52) * 3.2, 0, 1) ** .8
    X, Y = _grid(res, res, 1.0, 1.0)
    r = np.hypot(X - .5, Y - .5) * 2
    sky = np.stack([.22 + .35 * r ** 2, .40 + .28 * r ** 2, .78 - .08 * r ** 2], -1)       # deeper blue at zenith, warm toward edges
    shade = np.clip(acc - .6, 0, 1)[..., None] * .6
    img = sky * (1 - cloud[..., None]) + (np.array([.98, .94, .86]) - shade * np.array([.3, .3, .25])) * cloud[..., None]
    rim = np.minimum.reduce([X, 1 - X, Y, 1 - Y])
    img[rim < .025] = [.78, .60, .28]
    img[(rim > .03) & (rim < .036)] = [.62, .45, .18]
    return img


def book_spines(res=512):
    """Library shelves: rows of spines in leather tones with gilt bands."""
    h, w = res, res
    img = np.zeros((h, w, 3))
    rng = np.random.default_rng(12)
    rows = 6
    for r in range(rows):
        y0, y1 = int(r * h / rows), int((r + 1) * h / rows)
        x = 0
        while x < w:
            bw = rng.integers(6, 16)
            hh = int((y1 - y0) * rng.uniform(.72, .95))
            c = rng.choice([[.35, .06, .04], [.07, .15, .08], [.06, .08, .22], [.30, .20, .10], [.45, .38, .25], [.12, .05, .03]])
            img[y1 - hh:y1 - 4, x:x + bw - 1] = np.array(c) * rng.uniform(.8, 1.2)
            img[y1 - hh + 8:y1 - hh + 10, x:x + bw - 1] = [.75, .58, .25]
            x += bw
        img[y1 - 4:y1] = [.18, .09, .04]
    return img


if __name__ == '__main__' or True:
    pass


def make_penthouse_textures():
    save('ph_parquet.jpg', parquet())
    save('ph_checker.jpg', checker())
    save('ph_travertine.jpg', travertine())
    save('ph_fresco.jpg', fresco())
    save('ph_books.jpg', book_spines())
