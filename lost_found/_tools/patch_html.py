# -*- coding: utf-8 -*-
# Точечные правки HTML: логотип, favicon, ARIA, обязательные поля
import os, re, glob

SITE = r'C:\Users\User\Documents\lost_foubd\site'
files = sorted(glob.glob(os.path.join(SITE, '*.html')))

LOGO_RE = re.compile(r'<svg class="brand__logo"[\s\S]*?</svg>')
LOGO = '<img class="brand__logo" src="assets/logo.svg" width="60" height="60" alt="">'

for path in files:
    with open(path, encoding='utf-8') as f:
        html = f.read()
    orig = html

    # Логотип — внешний SVG
    html = LOGO_RE.sub(LOGO, html)

    # Favicon
    vp = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    if 'rel="icon"' not in html:
        html = html.replace(vp, vp + '\n  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">')

    # Чипы: aria-pressed
    html = html.replace('<button class="chip chip--active" type="button">',
                        '<button class="chip chip--active" type="button" aria-pressed="true">')
    html = html.replace('<button class="chip chip--flat chip--active" type="button">',
                        '<button class="chip chip--flat chip--active" type="button" aria-pressed="true">')
    html = html.replace('<button class="chip" type="button">',
                        '<button class="chip" type="button" aria-pressed="false">')
    html = html.replace('<button class="chip chip--flat" type="button">',
                        '<button class="chip chip--flat" type="button" aria-pressed="false">')

    # Переключатель типа объявления
    html = html.replace('<button class="btn btn--primary" type="button" data-toggle>',
                        '<button class="btn btn--primary" type="button" data-toggle aria-pressed="true">')
    html = html.replace('<button class="btn btn--secondary" type="button" data-toggle>',
                        '<button class="btn btn--secondary" type="button" data-toggle aria-pressed="false">')

    # Обязательные поля (novalidate отключает нативную подсказку, required нужен для AT и JS)
    required_map = {
        'login-email': 'email', 'login-password': 'password',
        'signup-name': 'text', 'signup-email': 'email',
        'signup-password': 'password', 'signup-password2': 'password',
        'item-title': 'text', 'item-place': 'text', 'item-date': 'text',
        'item-contact': 'text',
        'claim-name': 'text', 'claim-email': 'email', 'claim-phone': 'tel',
    }
    for id_, typ in required_map.items():
        # добавляем required перед закрывающей >
        pat = re.compile(r'(<input\b[^>]*\bid="' + re.escape(id_) + r'"[^>]*?)(/?)>')
        def add_req(m):
            tag = m.group(1)
            if 'required' in tag:
                return m.group(0)
            return tag + ' required' + m.group(2) + '>'
        html = pat.sub(add_req, html, count=1)

    # select и textarea
    html = html.replace('<select class="select" id="item-category" name="category">',
                        '<select class="select" id="item-category" name="category" required>')
    html = html.replace('<textarea class="textarea" id="item-desc" name="description"></textarea>',
                        '<textarea class="textarea" id="item-desc" name="description" required></textarea>')
    html = html.replace('<textarea class="textarea" id="claim-desc" name="description"></textarea>',
                        '<textarea class="textarea" id="claim-desc" name="description" required></textarea>')

    # Чекбокс условий
    html = html.replace('<input class="check__box" type="checkbox" name="terms">',
                        '<input class="check__box" type="checkbox" name="terms" required>')

    # Неиспользуемый data-атрибут
    html = html.replace(' data-notif="unread"', '')

    if html != orig:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(html)
        print('обновлён:', os.path.basename(path))
    else:
        print('без изменений:', os.path.basename(path))