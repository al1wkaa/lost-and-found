# -*- coding: utf-8 -*-
# Мобильные метрики (390 px)
import os, json
from playwright.sync_api import sync_playwright

SITE = r'C:\Users\User\Documents\lost_foubd\site'
CASES = [
    ('index.html', ['.header','.brand__logo','.nav','.header__actions','.hero','.hero__title','.hero__subtitle','.hero__actions','.hero__actions .btn','.features','.feature-card','.footer__inner']),
    ('lost.html', ['.header','.h1','.page-head .btn','.toolbar','.search','.chips','.placeholder--card','.item-card__title']),
    ('login.html', ['.header','.auth-head__title','.auth-head__subtitle','.auth-card','.auth-card .btn--block']),
    ('signup.html', ['.header','.auth-head__title','.auth-card','.auth-card .btn--block']),
    ('submit.html', ['.header','.h1','.page-sub','.submit-card','.submit-card__toggle .btn']),
    ('claim.html', ['.h1','.claim-card','.claim-contacts','.claim-actions .btn']),
    ('notifications.html', ['.header','.h1','.panel--filters','.notif']),
    ('profile.html', ['.header','.profile-side','.profile-side__avatar','.profile-content','.listing-row']),
    ('settings.html', ['.header','.h1','.settings-nav','.settings-panel']),
    ('contact.html', ['.header','.h1','.contact-card']),
    ('found.html', ['.header','.h1','.page-head .btn','.placeholder--card']),
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
    for page, sels in CASES:
        pg = br.new_page(viewport={'width': 390, 'height': 900})
        pg.goto('file:///' + os.path.join(SITE, page).replace('\\','/'))
        pg.wait_for_timeout(100)
        d = pg.evaluate(JS_TPL, sels)
        print('==', page)
        print(json.dumps(d, ensure_ascii=False))
        pg.close()
    br.close()