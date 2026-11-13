# -*- coding: utf-8 -*-
# Скриншоты страниц и сравнение с референсами (бок о бок)
import os, sys, glob
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

ROOT = r'C:\Users\User\Documents\lost_foubd'
REFS = os.path.join(ROOT, 'references')
SITE = os.path.join(ROOT, 'site')
ROUND = sys.argv[1] if len(sys.argv) > 1 else 'r1'
OUT = os.path.join(SITE, 'compare', ROUND)
os.makedirs(os.path.join(OUT, 'shots'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'side'), exist_ok=True)

# (файл референса, страница, ширина)
PAIRS = [
    ('Home page.png', 'index.html', 1280),
    ('Home page ( after login ).png', 'home-after-login.html', 1280),
    ('Login page.png', 'login.html', 1271),
    ('Signup page.png', 'signup.html', 1271),
    ('Lost page.png', 'lost.html', 1280),
    ('Found page.png', 'found.html', 1280),
    ('claim item page.png', 'claim.html', 1271),
    ('Submit page.png', 'submit.html', 1271),
    ('Notification page.png', 'notifications.html', 1271),
    ('Profile.png', 'profile.html', 1271),
    ('Setting page.png', 'settings.html', 1271),
    ('Contact page.png', 'contact.html', 1271),
    ('Home — Mobile.png', 'index.html', 390),
    ('Home After Login — Mobile.png', 'home-after-login.html', 390),
    ('Login — Mobile.png', 'login.html', 390),
    ('Signup — Mobile.png', 'signup.html', 390),
    ('Lost Items — Mobile.png', 'lost.html', 390),
    ('Found Items — Mobile.png', 'found.html', 390),
    ('Claim Item — Mobile.png', 'claim.html', 390),
    ('Report Item — Mobile.png', 'submit.html', 390),
    ('Notifications — Mobile.png', 'notifications.html', 390),
    ('Profile — Mobile.png', 'profile.html', 390),
    ('Settings — Mobile.png', 'settings.html', 390),
    ('Contact — Mobile.png', 'contact.html', 390),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for ref, page, width in PAIRS:
        b = browser.new_page(viewport={'width': width, 'height': 900})
        b.goto('file:///' + os.path.join(SITE, page).replace('\\', '/'))
        b.wait_for_timeout(150)
        shot_path = os.path.join(OUT, 'shots', page.replace('.html', '') + ('_m' if width == 390 else '_d') + '.png')
        b.screenshot(path=shot_path, full_page=True)
        b.close()

        ref_path = glob.glob(os.path.join(REFS, glob.escape(ref)))
        if not ref_path:
            print('нет референса:', ref)
            continue
        ref_im = Image.open(ref_path[0]).convert('RGB')
        shot_im = Image.open(shot_path).convert('RGB')

        # приведение к одной ширине
        w = 640
        r2 = ref_im.resize((w, int(ref_im.height * w / ref_im.width)))
        s2 = shot_im.resize((w, int(shot_im.height * w / shot_im.width)))
        h = max(r2.height, s2.height)
        canvas = Image.new('RGB', (w * 2 + 12, h), (255, 255, 255))
        canvas.paste(r2, (0, 0))
        canvas.paste(s2, (w + 12, 0))
        d = ImageDraw.Draw(canvas)
        d.text((4, 2), 'REF', fill=(200, 30, 30))
        d.text((w + 16, 2), 'SHOT', fill=(30, 120, 30))
        name = page.replace('.html', '') + ('_m' if width == 390 else '_d') + '.png'
        canvas.save(os.path.join(OUT, 'side', name))
        print(f'{page:26s} w={width}  ref={ref_im.size}  shot={shot_im.size}')
    browser.close()
print('готово:', OUT)
