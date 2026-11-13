# -*- coding: utf-8 -*-
# Сравнение вертикальных метрик: референс vs мой скриншот
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'
s = r'C:\Users\User\Documents\lost_foubd\site\compare\r1\shots'

def rows(path, box, thresh=150, label=''):
    im = Image.open(path).convert('L').crop(box)
    w, h = im.size
    dark = [y for y in range(h) if min(im.getpixel((x, y)) for x in range(0, w, 2)) < thresh]
    if not dark:
        print(f'{label:34s} box={box} нет')
        return
    spans, start, prev = [], dark[0], dark[0]
    for y in dark[1:]:
        if y - prev > 2:
            spans.append((start, prev)); start = y
        prev = y
    spans.append((start, prev))
    print(f'{label:34s} ' + ' '.join(f'{a}-{b}(h{b-a+1})' for a, b in spans))

def blue_col(path, x, y0, y1, label=''):
    im = Image.open(path).convert('RGB')
    ys = [y for y in range(y0, min(y1, im.height)) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150]
    if ys:
        print(f'{label:34s} синий y {ys[0]}..{ys[-1]} (h={ys[-1]-ys[0]+1})')

print('--- Hero title (box 380,90,900,240) REF / SHOT')
rows(os.path.join(d, 'Home page.png'), (380, 90, 900, 240), label='REF title')
rows(os.path.join(s, 'index_d.png'), (380, 90, 900, 260), label='SHOT title')
print('--- Hero subtitle')
rows(os.path.join(d, 'Home page.png'), (300, 240, 980, 330), 200, 'REF subtitle')
rows(os.path.join(s, 'index_d.png'), (300, 240, 980, 340), 200, 'SHOT subtitle')
print('--- Hero primary button')
blue_col(os.path.join(d, 'Home page.png'), 512, 300, 500, 'REF btn')
blue_col(os.path.join(s, 'index_d.png'), 512, 300, 560, 'SHOT btn')
print('--- Cards (beige) top/bottom')
def beige_col(path, x, y0, y1, label):
    im = Image.open(path).convert('RGB')
    ys = [y for y in range(y0, min(y1, im.height)) if im.getpixel((x, y))[0] > 225 and im.getpixel((x, y))[2] < 246 and im.getpixel((x, y))[0] - im.getpixel((x, y))[2] > 3]
    if ys:
        print(f'{label:34s} беж y {ys[0]}..{ys[-1]} (h={ys[-1]-ys[0]+1})')
beige_col(os.path.join(d, 'Home page.png'), 235, 400, 900, 'REF cards')
beige_col(os.path.join(s, 'index_d.png'), 235, 400, 1000, 'SHOT cards')
print('--- Footer text')
rows(os.path.join(d, 'Home page.png'), (57, 900, 400, 985), 200, 'REF footer')
rows(os.path.join(s, 'index_d.png'), (57, 900, 400, 1048), 200, 'SHOT footer')
print('--- Login: title, card, button')
rows(os.path.join(d, 'Login page.png'), (450, 150, 830, 240), label='REF login title')
rows(os.path.join(s, 'login_d.png'), (450, 150, 830, 260), label='SHOT login title')
blue_col(os.path.join(d, 'Login page.png'), 640, 480, 620, 'REF login btn')
blue_col(os.path.join(s, 'login_d.png'), 640, 480, 680, 'SHOT login btn')
print('--- Lost: h1, search, image')
rows(os.path.join(d, 'Lost page.png'), (55, 110, 220, 190), label='REF lost h1')
rows(os.path.join(s, 'lost_d.png'), (55, 110, 220, 190), label='SHOT lost h1')
def grey_col(path, x, y0, y1, label):
    im = Image.open(path).convert('RGB')
    ys = [y for y in range(y0, min(y1, im.height)) if 200 <= im.getpixel((x, y))[0] <= 235 and abs(im.getpixel((x, y))[0] - im.getpixel((x, y))[2]) < 6]
    if ys:
        print(f'{label:34s} серый y {ys[0]}..{ys[-1]} (h={ys[-1]-ys[0]+1})')
grey_col(os.path.join(d, 'Lost page.png'), 240, 280, 600, 'REF img')
grey_col(os.path.join(s, 'lost_d.png'), 240, 280, 600, 'SHOT img')
print('--- Notifications: h1, items')
rows(os.path.join(d, 'Notification page.png'), (250, 140, 500, 210), label='REF notif h1')
rows(os.path.join(s, 'notifications_d.png'), (250, 140, 500, 230), label='SHOT notif h1')
print('--- Profile: avatar, name')
blue_col(os.path.join(d, 'Profile.png'), 210, 130, 260, 'REF avatar')
blue_col(os.path.join(s, 'profile_d.png'), 210, 130, 260, 'SHOT avatar')
