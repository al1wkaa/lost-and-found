# -*- coding: utf-8 -*-
# Измерение высоты текста (кап-высота) по тёмным строкам
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'

def rows(f, box, thresh=150):
    im = Image.open(os.path.join(d, f)).convert('L').crop(box)
    w, h = im.size
    dark_rows = []
    for y in range(h):
        row = [im.getpixel((x, y)) for x in range(w)]
        if min(row) < thresh:
            dark_rows.append(y)
    if dark_rows:
        # интервалы непрерывных строк
        spans, start, prev = [], dark_rows[0], dark_rows[0]
        for y in dark_rows[1:]:
            if y - prev > 2:
                spans.append((start, prev)); start = y
            prev = y
        spans.append((start, prev))
        print(f"{f[:22]:24s} box={box} spans(cap-height): {[(a, b, b - a + 1) for a, b in spans]}")
    else:
        print(f"{f[:22]:24s} box={box} нет тёмных пикселей")

rows('Home page.png', (452, 140, 830, 225))        # hero title Lost & Found
rows('Home page.png', (555, 25, 625, 55), 200)     # nav Главная
rows('Lost page.png', (57, 125, 210, 175))         # h1 Пропажи
rows('Lost page.png', (975, 135, 1195, 168), 250)  # кнопка синяя (белый текст не виден)
rows('Home page.png', (136, 690, 355, 718))        # card title
rows('Home page.png', (108, 740, 378, 765), 180)   # card desc line 1
rows('Login page.png', (459, 165, 813, 215))       # С возвращением!
rows('Login page.png', (490, 300, 630, 325), 200)  # label
rows('Login page.png', (507, 338, 620, 362), 220)  # placeholder
rows('Login page.png', (700, 490, 775, 512))       # Забыли пароль?
rows('Profile.png', (132, 248, 292, 275))          # имя
rows('Profile.png', (417, 155, 597, 180))          # Ваши объявления
rows('Profile.png', (529, 222, 632, 246))          # MacBook Pro
rows('Notification page.png', (258, 155, 470, 190))# Уведомления
rows('Notification page.png', (343, 358, 535, 380))# заголовок увед.
rows('Contact page.png', (427, 254, 592, 280))     # Золотое кольцо
rows('Submit page.png', (259, 125, 562, 165))      # Подать объявление
rows('Submit page.png', (398, 278, 575, 296), 250) # нет — синий текст
rows('Home page.png', (740, 948, 905, 972), 180)   # Конфиденциальность
rows('claim item page.png', (293, 228, 512, 255))  # Контакты нашедшего
