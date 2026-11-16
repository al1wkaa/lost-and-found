# -*- coding: utf-8 -*-
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def runs(vals, pred, off=0):
    out, s = [], None
    for i, v in enumerate(vals):
        if pred(v) and s is None: s = i
        elif not pred(v) and s is not None:
            out.append((s + off, i - 1 + off)); s = None
    if s is not None: out.append((s + off, len(vals) - 1 + off))
    return out

im = Image.open(os.path.join(D, 'Notifications — Mobile.png')).convert('RGB')
for y in [280, 285, 291, 295, 300, 305, 310, 315]:
    row = [im.getpixel((x, y)) for x in range(390)]
    chip = [x for x, c in enumerate(row) if 240 <= c[0] <= 246 and abs(c[0]-c[2]) < 3]
    dark = [x for x, c in enumerate(row) if sum(c) < 450]
    print('y=', y, 'chip-bg x:', runs(chip, lambda v: True), 'dark:', runs(dark, lambda v: True))

# Lost: точные границы трёх чипов
im2 = Image.open(os.path.join(D, 'Lost Items — Mobile.png')).convert('RGB')
for y in [400, 417]:
    row = [im2.getpixel((x, y)) for x in range(390)]
    grey = [x for x, c in enumerate(row) if 246 <= c[0] <= 250 and 248 <= c[1] <= 252 and 250 <= c[2] <= 254]
    print('Lost y=', y, 'chip #f8fafc:', runs(grey, lambda v: True))