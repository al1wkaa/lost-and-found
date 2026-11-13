# -*- coding: utf-8 -*-
# Вертикальная структура мобильных референсов: полосы текста/синего
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def bands(f, label):
    im = Image.open(os.path.join(D, f)).convert('RGB')
    w, h = im.size
    print('==', label, im.size)
    rows = []
    for y in range(h):
        dark = sum(1 for x in range(0, w, 2) if sum(im.getpixel((x, y))) < 450)
        blue = sum(1 for x in range(0, w, 2) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150)
        rows.append((dark, blue))
    # полосы, где есть тёмные пиксели
    spans, s = [], None
    for y, (d, b) in enumerate(rows):
        if d > 2 and s is None:
            s = y
        elif d <= 2 and s is not None:
            if y - s >= 2:
                spans.append((s, y - 1))
            s = None
    if s is not None:
        spans.append((s, h - 1))
    print(' тёмные полосы:', spans[:30])
    # синие полосы
    bspans, s = [], None
    for y, (d, b) in enumerate(rows):
        if b > 2 and s is None:
            s = y
        elif b <= 2 and s is not None:
            if y - s >= 2:
                bspans.append((s, y - 1))
            s = None
    if s is not None:
        bspans.append((s, h - 1))
    print(' синие полосы:', bspans[:30])

bands('Home — Mobile.png', 'Home mobile')
bands('Lost Items — Mobile.png', 'Lost mobile')
bands('Profile — Mobile.png', 'Profile mobile')
bands('Login — Mobile.png', 'Login mobile')