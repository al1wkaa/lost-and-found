# -*- coding: utf-8 -*-
# Мобильные измерения (390px)
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'

def col(f, x, y0, y1, test, label):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    ys = [y for y in range(y0, min(y1, im.height)) if test(im.getpixel((x, y)))]
    if ys:
        print(f"{f[:22]:24s} x={x} {label}: y {ys[0]}..{ys[-1]} (h={ys[-1]-ys[0]+1})")

def row(f, y, x0, x1, test, label):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    xs = [x for x in range(x0, min(x1, im.width)) if test(im.getpixel((x, y)))]
    if xs:
        print(f"{f[:22]:24s} y={y} {label}: x {xs[0]}..{xs[-1]} (w={xs[-1]-xs[0]+1})")

blue = lambda c: c[2] > 200 and c[0] < 150
grey = lambda c: 200 <= c[0] <= 235 and abs(c[0]-c[2]) < 6
beige = lambda c: c[0] > 235 and c[2] < 247 and c[0]-c[2] > 3

# Home Mobile
col('Home — Mobile.png', 195, 400, 500, blue, 'кнопка Подать')
col('Home — Mobile.png', 195, 0, 80, blue, 'логотип')
row('Home — Mobile.png', 447, 0, 390, blue, 'кнопка Подать')
col('Home — Mobile.png', 60, 560, 1000, beige, 'карточка беж')
row('Home — Mobile.png', 700, 0, 390, beige, 'карточка беж')
col('Home — Mobile.png', 60, 140, 200, lambda c: sum(c) < 200, 'титул h1 тёмный')
col('Home — Mobile.png', 195, 495, 545, blue, 'кнопка поиск (рамка)')
# Lost Mobile
col('Lost Items — Mobile.png', 195, 420, 760, grey, 'картинка-заглушка')
row('Lost Items — Mobile.png', 600, 0, 390, grey, 'картинка-заглушка')
col('Lost Items — Mobile.png', 195, 250, 320, blue, 'кнопка Сообщить')
col('Lost Items — Mobile.png', 30, 140, 220, lambda c: sum(c) < 200, 'h1 Пропажи')
# Signup Mobile
col('Signup — Mobile.png', 195, 180, 260, lambda c: sum(c) < 220, 'титул')
# Footer mobile Home
col('Home — Mobile.png', 30, 1430, 1518, lambda c: sum(c) < 740, 'футер текст')
# header border mobile
im = Image.open(os.path.join(d, 'Lost Items — Mobile.png')).convert('RGB')
ys = [y for y in range(140, 190) if sum(im.getpixel((195, y))) < 750]
print('Lost Mobile: линия под меню y:', ys)
ys2 = [y for y in range(60, 80) if sum(im.getpixel((195, y))) < 755]
print('Lost Mobile: линия под шапкой y:', ys2)
