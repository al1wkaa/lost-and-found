# -*- coding: utf-8 -*-
# Уточнение цветов текста: самый частый тёмный цвет в области
import os
from collections import Counter
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'

def region(f, box, thresh=140, n=3):
    im = Image.open(os.path.join(d, f)).convert('RGB').crop(box)
    cnt = Counter(p for p in im.getdata() if sum(p) / 3 < thresh)
    tops = cnt.most_common(n)
    out = ' '.join('#%02x%02x%02x(%d)' % (c[0][0], c[0][1], c[0][2], c[1]) for c in tops)
    print(f"{f[:22]:24s} {str(box):24s} {out}")

# Home: заголовок, подзаголовок, подпись, футер
region('Home page.png', (450, 150, 830, 215))          # hero title
region('Home page.png', (310, 245, 970, 300), 180)     # hero subtitle
region('Home page.png', (135, 690, 360, 715))          # card title
region('Home page.png', (108, 740, 378, 800), 180)     # card desc
region('Home page.png', (57, 950, 330, 972), 180)      # footer text
region('Home page.png', (780, 948, 1215, 972), 180)    # footer links
region('Home page.png', (555, 26, 910, 50), 180)       # nav links
region('Home page.png', (140, 28, 245, 48), 180)       # logo text
region('Home page.png', (411, 360, 613, 398), 250)     # primary btn (все цвета)
region('Home page.png', (630, 352, 860, 405), 250)     # secondary btn
region('Home page.png', (995, 18, 1223, 58), 250)      # Войти + Регистрация
# Lost page
region('Lost page.png', (57, 128, 205, 170))           # h1 Пропажи
region('Lost page.png', (95, 230, 560, 260), 180)      # placeholder
region('Lost page.png', (626, 224, 1210, 266), 250)    # chips
region('Lost page.png', (74, 530, 400, 555))           # card title
region('Lost page.png', (337, 528, 410, 548), 180)     # card date
region('Lost page.png', (74, 562, 210, 582), 200)      # card location
region('Lost page.png', (140, 636, 350, 658))          # link
region('Lost page.png', (730, 26, 1100, 50), 250)      # nav active color
# Found badges
region('Found page.png', (76, 626, 220, 654), 250)     # green badge
region('Found page.png', (467, 626, 615, 654), 250)    # orange badge
# Profile
region('Profile.png', (40, 480, 120, 520), 250)        # page bg рядом
region('Profile.png', (132, 248, 292, 275))            # name
region('Profile.png', (112, 278, 310, 298), 180)       # email
region('Profile.png', (520, 280, 600, 300))            # status потеряно
region('Profile.png', (520, 636, 600, 656))            # найдено
region('Profile.png', (1090, 392, 1192, 416), 250)     # Активно badge
# Notifications
region('Notification page.png', (258, 155, 470, 190))  # h1
region('Notification page.png', (888, 152, 1013, 176), 180)  # прочитать все
# Claim
region('claim item page.png', (233, 95, 455, 135))     # h1
region('claim item page.png', (649, 520, 1002, 540), 200)  # label
# Contact
region('Contact page.png', (259, 128, 672, 168))       # h1
