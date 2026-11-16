# -*- coding: utf-8 -*-
# Кропы для детального осмотра
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'
out = r'C:\Users\User\Documents\lost_foubd\_tools\crops'
os.makedirs(out, exist_ok=True)

crops = [
    ('Found page.png', (60, 510, 620, 730), 'found_card1_2.png', 2),
    ('Home page.png', (0, 0, 1280, 80), 'header.png', 1.6),
    ('Home page.png', (400, 340, 880, 415), 'hero_buttons.png', 2),
    ('Notification page.png', (259, 230, 1020, 440), 'notif_cards.png', 1.6),
    ('Login page.png', (459, 260, 813, 580), 'login_form.png', 1.6),
    ('Profile.png', (59, 128, 361, 555), 'profile_sidebar.png', 2),
    ('Contact page.png', (259, 225, 1013, 400), 'contact_card.png', 1.6),
    ('Home — Mobile.png', (0, 0, 390, 230), 'mobile_home_top.png', 2),
    ('Lost — check nav', None, None, None),
]
for f, box, name, scale in crops:
    if box is None:
        continue
    im = Image.open(os.path.join(d, f)).convert('RGB').crop(box)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    im.save(os.path.join(out, name))
    print(name, im.size)
