# -*- coding: utf-8 -*-
# Проверка горизонтальной прокрутки на всех ширинах 320–1920
import os, json
from playwright.sync_api import sync_playwright

SITE = r'C:\Users\User\Documents\lost_foubd\site'
WIDTHS = [320, 360, 390, 480, 576, 600, 768, 820, 992, 1024, 1200, 1280, 1440, 1920]
PAGES = ['index.html','home-after-login.html','lost.html','found.html','login.html','signup.html',
         'submit.html','notifications.html','profile.html','settings.html','contact.html','claim.html']

JS = """() => {
  const vw = window.innerWidth;
  const bad = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (cs.position === 'fixed') return;
    if (r.width > 0 && (r.right > vw + 0.5 || r.left < -0.5)) {
      bad.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || '',
        left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width)
      });
    }
  });
  return {
    vw,
    docScroll: document.documentElement.scrollWidth,
    bodyScroll: document.body.scrollWidth,
    overflow: document.documentElement.scrollWidth > vw,
    bad: bad.slice(0, 8)
  };
}"""

problems = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for page in PAGES:
        for w in WIDTHS:
            pg = b.new_page(viewport={'width': w, 'height': 900})
            pg.goto('file:///' + os.path.join(SITE, page).replace('\\', '/'))
            pg.wait_for_timeout(80)
            d = pg.evaluate(JS)
            if d['overflow'] or d['docScroll'] > w:
                problems.append((page, w, d['docScroll'], d['bad']))
                print(f'OVERFLOW {page:24s} w={w:4d} scroll={d["docScroll"]} bad={d["bad"]}')
            pg.close()
    b.close()

print('\nвсего проблем:', len(problems))
if not problems:
    print('Горизонтальной прокрутки нет ни на одной ширине.')