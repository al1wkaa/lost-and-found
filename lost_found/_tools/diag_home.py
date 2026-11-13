# -*- coding: utf-8 -*-
# Подробные метрики首页
import os, json
from playwright.sync_api import sync_playwright

SITE = r'C:\Users\User\Documents\lost_foubd\site'
JS = """() => {
  const box = (sel) => { const el = document.querySelector(sel); if (!el) return null; const r = el.getBoundingClientRect(); return {x:Math.round(r.x), y:Math.round(r.y+scrollY), w:Math.round(r.width), h:Math.round(r.height), bottom:Math.round(r.bottom+scrollY)}; };
  return {
    header: box('.header'),
    hero: box('.hero'),
    title: box('.hero__title'),
    subtitle: box('.hero__subtitle'),
    actions: box('.hero__actions'),
    btn1: box('.hero__actions .btn'),
    features: box('.features'),
    card: box('.feature-card'),
    footer: box('.footer'),
    main: box('main')
  };
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width':1280,'height':900})
    pg.goto('file:///' + os.path.join(SITE,'index.html').replace('\\','/'))
    pg.wait_for_timeout(100)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1))
    b.close()