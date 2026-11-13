# -*- coding: utf-8 -*-
# Р“СЂР°РЅРёС†С‹ Р±РµР»С‹С… РєР°СЂС‚РѕС‡РµРє Рё Р·Р°РіРѕР»РѕРІРєРѕРІ РЅР° СЂРµС„РµСЂРµРЅСЃР°С…
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def white_box(f, y0, y1, x0=0, x1=None, label=''):
    im = Image.open(os.path.join(D, f)).convert('RGB')
    x1 = x1 or im.width
    # РёС‰РµРј СЃР°РјСѓСЋ С€РёСЂРѕРєСѓСЋ РЅРµРїСЂРµСЂС‹РІРЅСѓСЋ Р±РµР»СѓСЋ РїРѕР»РѕСЃСѓ РїРѕ x РЅР° СЃРµСЂРµРґРёРЅРµ
    best = None
    for y in range(y0, min(y1, im.height)):
        xs = [x for x in range(x0, x1) if im.getpixel((x, y)) == (255, 255, 255)]
        if not xs:
            continue
        spans, s, p = [], xs[0], xs[0]
        for x in xs[1:]:
            if x - p > 1:
                spans.append((s, p)); s = x
            p = x
        spans.append((s, p))
        for a, b in spans:
            if b - a > 200 and (best is None or b - a > best[2] - best[1]):
                best = (y, a, b)
    if best:
        y, a, b = best
        # РІРµСЂС‚РёРєР°Р»СЊРЅС‹Рµ РіСЂР°РЅРёС†С‹ РєР°СЂС‚РѕС‡РєРё РїРѕ x=(a+b)//2
        x = (a + b) // 2
        ys = [yy for yy in range(max(0, y0 - 200), min(im.height, y1 + 400))
              if im.getpixel((x, yy)) == (255, 255, 255)]
        print(f'{label:22s} x {a}..{b} (w={b-a+1}) yв‰€{y}; С†РµРЅС‚СЂ x={x}')
        return (a, b, x)
    print(f'{label:22s} РЅРµ РЅР°Р№РґРµРЅРѕ')

def dark_rows(f, box, label):
    im = Image.open(os.path.join(D, f)).convert('L').crop(box)
    w, h = im.size
    rows = [y for y in range(h) if min(im.getpixel((x, y)) for x in range(0, w, 2)) < 150]
    if rows:
        print(f'{label:22s} y {rows[0]+box[1]}..{rows[-1]+box[1]}')

white_box('Signup page.png', 200, 800, 300, 1000, 'Signup card')
white_box('Submit page.png', 180, 900, 150, 1150, 'Submit card')
white_box('Claim Item page.png' if os.path.exists(os.path.join(D,'Claim Item page.png')) else 'claim item page.png', 120, 1300, 100, 1200, 'Claim card')
white_box('Setting page.png', 120, 800, 100, 1200, 'Settings panel')
white_box('Contact page.png', 120, 800, 100, 1200, 'Contact card')
white_box('Profile.png', 100, 800, 0, 700, 'Profile side')
white_box('Notification page.png', 100, 900, 150, 1150, 'Notif list')

dark_rows('Login page.png', (400, 120, 900, 280), 'Login title')
dark_rows('Submit page.png', (150, 100, 1150, 240), 'Submit h1')
dark_rows('Claim Item page.png' if os.path.exists(os.path.join(D,'Claim Item page.png')) else 'claim item page.png', (100, 80, 1200, 240), 'Claim h1')
dark_rows('Setting page.png', (150, 80, 1150, 200), 'Settings h1')
dark_rows('Profile.png', (60, 80, 700, 200), 'Profile name')
dark_rows('Notification page.png', (200, 80, 1100, 200), 'Notif h1')
