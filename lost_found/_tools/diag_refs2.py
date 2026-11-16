# -*- coding: utf-8 -*-
# Точные вертикальные срезы референсов
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def runs(vals, pred):
    out, s = [], None
    for i, v in enumerate(vals):
        if pred(v) and s is None:
            s = i
        elif not pred(v) and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(vals) - 1))
    return out

def scan(f, x, y0, y1, label):
    im = Image.open(os.path.join(D, f)).convert('RGB')
    print('==', label, f)
    for y in range(y0, min(y1, im.height), 1):
        pass
    white = [im.getpixel((x, y)) for y in range(y0, min(y1, im.height))]
    rr = [(a + y0, b + y0) for a, b in runs(white, lambda c: min(c) >= 250)]
    print(' белые полосы:', [r for r in rr if r[1] - r[0] > 3])

def dark(f, box, label, thresh=150):
    im = Image.open(os.path.join(D, f)).convert('L').crop(box)
    w, h = im.size
    rows = [y for y in range(h) if min(im.getpixel((x, y)) for x in range(0, w, 2)) < thresh]
    rr = [(a + box[1], b + box[1]) for a, b in runs(rows, lambda v: True)]
    print(f'{label:16s}', rr)

scan('Login page.png', 635, 100, 800, 'Login center')
scan('Signup page.png', 635, 100, 800, 'Signup center')
scan('Submit page.png', 635, 100, 1000, 'Submit center')
scan('claim item page.png', 635, 60, 1400, 'Claim center')
scan('Setting page.png', 635, 100, 800, 'Settings center')
scan('Notification page.png', 635, 100, 900, 'Notif center')

dark('Login page.png', (400, 100, 900, 280), 'Login top text')
dark('Signup page.png', (400, 100, 900, 280), 'Signup top text')
dark('Submit page.png', (150, 90, 1150, 240), 'Submit top text')
dark('claim item page.png', (150, 60, 1150, 240), 'Claim top text')