# -*- coding: utf-8 -*-
# Списки чипов в мобильных референсах
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def spans(vals, pred, off=0):
    out, s = [], None
    for i, v in enumerate(vals):
        if pred(v) and s is None: s = i
        elif not pred(v) and s is not None:
            out.append((s + off, i - 1 + off)); s = None
    if s is not None: out.append((s + off, len(vals) - 1 + off))
    return out

def row_scan(f, y, label):
    im = Image.open(os.path.join(D, f)).convert('RGB')
    w = im.width
    print('==', label, 'y=', y)
    # фон чипа #f8fafc (248,250,252) или серый #f3f4f6
    chip = [x for x in range(w) if all(240 <= c <= 252 for c in im.getpixel((x, y)))]
    print(' светлый фон x:', spans(chip, lambda v: True))
    # текст: тёмные пиксели
    dark = [x for x in range(w) if sum(im.getpixel((x, y))) < 450]
    print(' текст x:', spans(dark, lambda v: True))
    # синие пиксели
    blue = [x for x in range(w) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150]
    print(' синий x:', spans(blue, lambda v: True))

for f, ys, label in [
    ('Lost Items — Mobile.png', [400, 410, 417, 425, 435], 'Lost chips'),
    ('Notifications — Mobile.png', [300, 310, 320, 330], 'Notif chips'),
]:
    for y in ys:
        row_scan(f, y, label)

# Вертикальные границы панели фильтров уведомлений
im = Image.open(os.path.join(D, 'Notifications — Mobile.png')).convert('RGB')
for y in range(240, 360, 1):
    if im.getpixel((10, y)) != (249, 249, 249):
        pass
print('Notif panel bg x=10:', [(y, im.getpixel((10, y))) for y in range(250, 350, 10)])