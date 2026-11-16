# -*- coding: utf-8 -*-
# Диагностика размеров референсов и текущей вёрстки
import os, glob
from PIL import Image

REFS = r'C:\Users\User\Documents\lost_foubd\references'
for f in sorted(glob.glob(os.path.join(REFS, '*.png'))):
    im = Image.open(f)
    print(f'{os.path.basename(f):36s} {im.size}')

print('\n-- Lost page: серые пиксели по строкам --')
im = Image.open(os.path.join(REFS, 'Lost page.png')).convert('RGB')
for y in (300, 320, 330, 420, 500, 520):
    xs = [x for x in range(im.width) if 200 <= im.getpixel((x, y))[0] <= 235 and abs(im.getpixel((x, y))[0] - im.getpixel((x, y))[2]) < 6]
    if xs:
        # непрерывные диапазоны
        spans, start, prev = [], xs[0], xs[0]
        for x in xs[1:]:
            if x - prev > 1:
                spans.append((start, prev)); start = x
            prev = x
        spans.append((start, prev))
        print(f'y={y}: ' + ' '.join(f'{a}-{b}' for a, b in spans))