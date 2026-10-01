"""out/ (Blender) -> web/dist/assets (WebP lightmaps, GLB, HDR, manifest)."""
import os, shutil, json, sys
from PIL import Image, ImageFilter
root = os.path.dirname(os.path.abspath(__file__))
src, dst = os.path.join(root, os.environ.get('SRC', 'out')), os.path.join(root, 'web', 'dist', 'assets')
os.makedirs(dst, exist_ok=True)
q = int(os.environ.get('WEBP_Q', 82))
tot = 0
for f in sorted(os.listdir(src)):
    p = os.path.join(src, f)
    if f.startswith('lm_') and f.endswith('.png'):
        o = os.path.join(dst, f[:-4] + '.webp')
        Image.open(p).convert('RGB').filter(ImageFilter.MedianFilter(3)).save(o, 'WEBP', quality=q, method=6)   # kill bake fireflies
    elif f.endswith(('.glb', '.hdr', '.json', '.jpg')):
        o = os.path.join(dst, f); shutil.copy(p, o)
    else:
        continue
    sz = os.path.getsize(o); tot += sz
    print(f'{os.path.basename(o):32s} {sz/1e6:6.2f} MB')
print(f'TOTAL {tot/1e6:.1f} MB')
