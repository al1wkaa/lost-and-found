# -*- coding: utf-8 -*-
# Замер ключевых блоков текущей вёрстки в браузере
import os, sys, json
from playwright.sync_api import sync_playwright

SITE = r'C:\Users\User\Documents\lost_foubd\site'
PAGES = sys.argv[1:] or ['index.html', 'lost.html', 'login.html', 'submit.html', 'profile.html']

JS = """() => {
  const pick = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y + window.scrollY), w: Math.round(r.width), h: Math.round(r.height)};
  };
  return {
    viewport: window.innerWidth,
    docScroll: document.documentElement.scrollWidth,
    bodyScroll: document.body.scrollWidth,
    container: pick('.container'),
    header: pick('.header__inner'),
    heroTitle: pick('.hero__title'),
    heroBtn: pick('.hero__actions .btn'),
    cards: [...document.querySelectorAll('.grid--3 > *')].map(el => {
      const r = el.getBoundingClientRect();
      return {x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height)};
    }),
    cardImg: pick('.placeholder--card'),
    pageHead: pick('.page-head'),
    search: pick('.search'),
    authCard: pick('.auth-card'),
    submitCard: pick('.submit-card'),
    profileSide: pick('.profile-side'),
    profileContent: pick('.profile-content'),
    settingsNav: pick('.settings-nav'),
    settingsPanel: pick('.settings-panel'),
    claimCard: pick('.claim-card'),
    footer: pick('.footer__inner')
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for page_name in PAGES:
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        pg.goto('file:///' + os.path.join(SITE, page_name).replace('\\', '/'))
        pg.wait_for_timeout(120)
        data = pg.evaluate(JS)
        print('==', page_name)
        print(json.dumps(data, ensure_ascii=False, indent=1))
        pg.close()
    b.close()