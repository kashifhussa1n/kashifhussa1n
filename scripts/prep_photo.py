"""Prepare Kashif's white-background Memoji for monochrome ASCII.

Adapted from Avi Vashishta's preprocessing: isolate/crop the subject, smooth
texture, stretch subject tones and enhance dark ridges before white compositing.
The supplied image already has a white background, so no AI cutout is needed.
Usage: python scripts/prep_photo.py [source-photo.jpg] [source-prepped.png]
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'source-photo.jpg'
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'source-prepped.png'
im = Image.open(src).convert('RGBA')
white = Image.new('RGBA', im.size, 'white')
white.alpha_composite(im)
gray = white.convert('L')
a = np.array(gray)
ys, xs = np.where(a < 230)
if not len(xs):
    raise ValueError('No portrait subject found')
box = (int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1)
gray = gray.crop(box)
smooth = gray.filter(ImageFilter.MedianFilter(3))
a = np.array(smooth, dtype=np.float32)
subject = a < 235
lo, hi = np.percentile(a[subject], [2, 92])
tone = np.clip((a-lo) / max(hi-lo, 1), 0, 1)
fine = np.array(smooth.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32)
coarse = np.array(smooth.filter(ImageFilter.GaussianBlur(6)), dtype=np.float32)
ridge = np.clip((coarse-fine)/40, 0, 1)
result = np.clip(tone - .60*ridge, 0, 1)*255
result[a >= 245] = 255
art = Image.fromarray(result.astype(np.uint8))
side = max(art.size) + 60
canvas = Image.new('L', (side, side), 255)
canvas.paste(art, ((side-art.width)//2, (side-art.height)//2))
canvas.save(out)
print(f'Prepared {src.name}: {canvas.size}, subject box {box}')

