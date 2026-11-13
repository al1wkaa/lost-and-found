# -*- coding: utf-8 -*-
# Живые метрики после этапа 6 (ширины как у референсов)
import os, json
from playwright.sync_api import sync_playwright

SITE = r'C:\Users\User\Documents\lost_foubd\site'
CASES = [
    ('index.html', 1280, ['.hero__title','.hero__subtitle','.hero__actions','.hero__actions .btn','.features','.feature-card','.footer']),
    ('home-after-login.html', 1280, ['.hero__title','.hero__actions','.feature-card']),
    ('lost.html', 1280, ['.page-head','.h1','.toolbar','.search','.chips','.placeholder--card','.item-card__title','.grid--3 > *']),
    ('found.html', 1280, ['.page-head','.placeholder--card','.grid--3 > *']),
    ('login.html', 1271, ['.auth-head__title','.auth-head__subtitle','.auth-card','.auth-card .btn--block']),
    ('signup.html', 1271, ['.auth-head__title','.auth-card','.auth-card .btn--block']),
    ('submit.html', 1271, ['.h1','.page-sub','.submit-card','.submit-card__toggle']),
    ('claim.html', 1271, ['.h1','.claim-card','.claim-contacts','.claim-body','.placeholder--claim']),
    ('notifications.html', 1271, ['.h1','.panel--filters','.notif']),
    ('settings.html', 1271, ['.h1','.settings-layout','.settings-nav','.settings-panel']),
    ('profile.html', 1271, ['.profile-layout','.profile-side','.profile-content','.listing-row']),
    ('contact.html', 1271, ['.h1','.contact-card','.contact-card--form']),
]

JS_TPL = """(sels) => {
  const out = {};
  for (const sel of sels) {
    const el = document.querySelector(sel);
    if (!el) { out[sel] = null; continue; }
    const r = el.getBoundingClientRect();
    out[sel] = {x:Math.round(r.x), y:Math.round(r.y+scrollY), w:Math.round(r.width), h:Math.round(r.height)};
  }
  const b = document.querySelector('.header');
  out['HEADER'] = b ? Math.round(b.getBoundingClientRect().height) : null;
  return out;
}"""

with sync_playwright() as p:
    br = p.chromium.launch()
    for page, w, sels in CASES:
        pg = br.new_page(viewport={'width': w, 'height': 900})
        pg.goto('file:///' + os.path.join(SITE, page).replace('\\','/'))
        pg.wait_for_timeout(100)
        d = pg.evaluate(JS_TPL, sels)
        print('==', page, 'w=', w)
        print(json.dumps(d, ensure_ascii=False))
        pg.close()
    br.close()