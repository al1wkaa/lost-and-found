# -*- coding: utf-8 -*-
# Точные строки текста: сравнение референса и текущего скриншота
import os, sys
from PIL import Image

def spans(rows):
    out = []
    if not rows:
        return out
    s = p = rows[0]
    for y in rows[1:]:
        if y - p > 2:
            out.append((s, p)); s = y
        p = y
    out.append((s, p))
    return out

def dark_rows(path, box, thresh=150):
    im = Image.open(path).convert('L').crop(box)
    w, h = im.size
    rows = [y for y in range(h) if min(im.getpixel((x, y)) for x in range(0, w, 2)) < thresh]
    return [(a + box[1], b + box[1]) for a, b in spans(rows)]

def white_rows(path, x, y0, y1):
    im = Image.open(path).convert('RGB')
    rows = [y for y in range(y0, min(y1, im.height)) if im.getpixel((x, y)) == (255, 255, 255)]
    return spans(rows)

D = r'C:\Users\User\Documents\lost_foubd\references'
S = r'C:\Users\User\Documents\lost_foubd\site\compare\r1\shots'

pairs = [
    ('Login page.png', 'login_d.png', (300, 60, 1000, 760), 'Login'),
    ('Signup page.png', 'signup_d.png', (300, 60, 1000, 900), 'Signup'),
    ('Submit page.png', 'submit_d.png', (150, 60, 1150, 300), 'Submit'),
    ('claim item page.png', 'claim_d.png', (150, 60, 1150, 300), 'Claim'),
    ('Setting page.png', 'settings_d.png', (150, 60, 1150, 300), 'Settings'),
    ('Notification page.png', 'notifications_d.png', (200, 60, 1100, 300), 'Notif'),
    ('Lost page.png', 'lost_d.png', (40, 60, 1240, 320), 'Lost'),
    ('Home page.png', 'index_d.png', (300, 60, 1000, 420), 'Home'),
]
for ref, shot, box, label in pairs:
    rp = os.path.join(D, ref)
    sp = os.path.join(S, shot)
    print('==', label)
    print('  REF  dark:', dark_rows(rp, box))
    print('  SHOT dark:', dark_rows(sp, box))
    print('  REF  white x=635:', white_rows(rp, 635, box[1], box[3]))
    print('  SHOT white x=635:', white_rows(sp, 635, box[1], box[3]))