"""Orthophoto -> ground albedo. Lifts cast shadows (they would double with rendered shadows).
Outputs data/ground_core.jpg (456 m) and data/ground_wide.jpg (760 m)."""
import numpy as np
from PIL import Image, ImageFilter
import os
here = os.path.join(os.path.dirname(__file__), '..', 'data')


def lift(src, dst, blur):
    im = Image.open(f'{here}/{src}').convert('RGB')
    a = np.asarray(im).astype(np.float32) / 255
    lin = a ** 2.2
    L = lin.mean(-1)
    Lb = np.asarray(Image.fromarray((np.clip(L, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
    ref = np.asarray(Image.fromarray((np.clip(L, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur * 6))).astype(np.float32) / 255
    sh = np.clip((ref * .55 - Lb) / (ref * .45 + 1e-3), 0, 1)          # 1 where darker than surroundings
    gain = 1 + sh * np.clip(ref / (Lb + 1e-3) - 1, 0, 3.5)
    out = np.clip(lin * gain[..., None], 0, 1)
    out = out ** (1 / 2.2)
    Image.fromarray((out * 255).astype(np.uint8)).save(f'{here}/{dst}', quality=92)


lift('hi_core.jpg', 'ground_core.jpg', 6)
lift('sat.jpg', 'ground_wide.jpg', 4)
print('ok')
