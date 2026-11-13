# -*- coding: utf-8 -*-
# Границы блоков: поиск серых областей-заглушек, ширина контейнера
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'

def grey_spans_col(f, x, y0=0, y1=None, lo=200, hi=235):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    y1 = y1 or im.height
    spans, start = [], None
    for y in range(y0, y1):
        r, g, b = im.getpixel((x, y))
        is_grey = lo <= r <= hi and abs(r - g) < 6 and abs(g - b) < 6
        if is_grey and start is None:
            start = y
        elif not is_grey and start is not None:
            if y - start > 20:
                spans.append((start, y - 1, y - start))
            start = None
    print(f"{f[:20]:22s} x={x} серые span'ы: {spans}")

def grey_span_row(f, y, x0=0, x1=None):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    x1 = x1 or im.width
    xs = [x for x in range(x0, x1) if all(200 <= c <= 235 for c in im.getpixel((x, y)))]
    if xs:
        print(f"{f[:20]:22s} y={y} серый x: {xs[0]}..{xs[-1]} (w={xs[-1]-xs[0]+1})")

def blue_span_row(f, y):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    xs = [x for x in range(im.width) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150]
    if xs:
        print(f"{f[:20]:22s} y={y} синий x: {xs[0]}..{xs[-1]} (w={xs[-1]-xs[0]+1})")

def blue_span_col(f, x, y0, y1):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    ys = [y for y in range(y0, y1) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150]
    if ys:
        print(f"{f[:20]:22s} x={x} синий y: {ys[0]}..{ys[-1]} (h={ys[-1]-ys[0]+1})")

print('== Lost: карточка-заглушка')
grey_spans_col('Lost page.png', 240)
grey_span_row('Lost page.png', 420)
print('== Lost: кнопка сообщить')
blue_span_row('Lost page.png', 148)
blue_span_col('Lost page.png', 1000, 110, 200)
print('== Lost: поиск')
# рамка поиска — светло-серая линия
im = Image.open(os.path.join(d, 'Lost page.png')).convert('RGB')
ys = [y for y in range(200, 290) if im.getpixel((300, y))[0] < 240 and abs(im.getpixel((300, y))[0]-im.getpixel((300, y))[2]) < 8]
print('Lost: линии поиска y:', ys[:4], ys[-4:] if ys else '')
print('== Home: hero кнопки')
blue_span_row('Home page.png', 378)
blue_span_col('Home page.png', 512, 330, 430)
print('== Home: карточки')
# бежевая карточка
im = Image.open(os.path.join(d, 'Home page.png')).convert('RGB')
ys = [y for y in range(400, 900) if im.getpixel((235, y))[0] > 230 and im.getpixel((235, y))[2] < 245 and im.getpixel((235, y))[0]-im.getpixel((235, y))[2] > 4]
print('Home: бежевая карточка y:', ys[0], '..', ys[-1], 'h=', ys[-1]-ys[0]+1)
xs = [x for x in range(0, 640) if im.getpixel((x, 610))[0]-im.getpixel((x, 610))[2] > 4]
print('Home: бежевая карточка x:', xs[0], '..', xs[-1], 'w=', xs[-1]-xs[0]+1)
print('== Login: карточка формы')
im = Image.open(os.path.join(d, 'Login page.png')).convert('RGB')
ys = [y for y in range(200, 760) if im.getpixel((640, y)) == (255, 255, 255)]
print('Login: белая карточка y:', ys[0], '..', ys[-1])
xs = [x for x in range(400, 900) if im.getpixel((x, 300)) == (255, 255, 255)]
print('Login: белая карточка x:', xs[0], '..', xs[-1])
print('== Login: кнопка Войти')
blue_span_row('Login page.png', 554)
blue_span_col('Login page.png', 640, 500, 600)
print('== Login: инпут')
ys = [y for y in range(320, 390) if im.getpixel((640, y)) != (255, 255, 255) and sum(im.getpixel((640, y))) < 760]
print('Login: границы инпута y:', ys)
print('== Profile: сайдбар')
im = Image.open(os.path.join(d, 'Profile.png')).convert('RGB')
xs = [x for x in range(0, 640) if im.getpixel((x, 300)) == (255, 255, 255)]
print('Profile y=300 белый x:', xs[0], '..', xs[-1])
ys = [y for y in range(100, 700) if im.getpixel((210, y)) == (255, 255, 255)]
print('Profile x=210 белый y:', ys[0], '..', ys[-1])
print('== Header Home: логотип')
im = Image.open(os.path.join(d, 'Home page.png')).convert('RGB')
ys = [y for y in range(0, 80) if im.getpixel((91, y))[2] > 150 and im.getpixel((91, y))[0] < 150]
print('Home: логотип y:', ys[0], '..', ys[-1], 'h=', ys[-1]-ys[0]+1)
xs = [x for x in range(0, 300) if im.getpixel((x, 37))[2] > 150 and im.getpixel((x, 37))[0] < 150]
print('Home: логотип x:', xs[0], '..', xs[-1])
# граница шапки
ys = [y for y in range(60, 100) if sum(im.getpixel((640, y))) < 750]
print('Home: линия под шапкой y:', ys)
