# -*- coding: utf-8 -*-
# Расчёт контраста (WCAG) для пар цветов

def lum(hex):
    h = hex.lstrip('#')
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)

pairs = [
    ('#94a3b8', '#ffffff', 'text-3 на белом'),
    ('#64748b', '#ffffff', 'text-2 на белом'),
    ('#64748b', '#f3eded', 'text-2 на бежевом'),
    ('#64748b', '#d7d0d0', 'text-2 на серой карточке'),
    ('#475569', '#d7d0d0', 'slate-600 на серой карточке'),
    ('#475569', '#f3eded', 'slate-600 на бежевом'),
    ('#5b6b7f', '#ffffff', 'вариант text-3'),
    ('#a6a6a6', '#ffffff', 'placeholder на белом'),
    ('#6b7280', '#ffffff', 'placeholder-500 на белом'),
    ('#6b7280', '#fafafa', 'placeholder-500 на #fafafa'),
    ('#9a9a9a', '#dddddd', 'thumb-text на #ddd'),
    ('#595959', '#dddddd', 'thumb-text тёмный'),
    ('#666666', '#ffffff', 'grey-text'),
    ('#666666', '#f8fafc', 'grey-text на chip-bg'),
    ('#374151', '#f3f4f6', 'grey-text-2 на chip-bg-2'),
    ('#3b82f6', '#ffffff', 'синий на белом'),
    ('#2563eb', '#ffffff', 'blue-600 на белом'),
    ('#ffffff', '#3b82f6', 'белый на синем'),
    ('#ffffff', '#2563eb', 'белый на blue-600'),
    ('#3b82f6', '#dbeafe', 'синий на голубом'),
    ('#2563eb', '#dbeafe', 'blue-600 на голубом'),
    ('#1d4ed8', '#dbeafe', 'blue-700 на голубом'),
    ('#d97706', '#fef3c7', 'оранжевый на оранжевом'),
    ('#b45309', '#fef3c7', 'amber-700 на оранжевом'),
    ('#16a34a', '#dcfce7', 'зелёный на зелёном'),
    ('#15803d', '#dcfce7', 'green-700 на зелёном'),
    ('#166534', '#dcfce7', 'green-800 на зелёном'),
    ('#16a34a', '#ffffff', 'зелёный на белом'),
    ('#15803d', '#ffffff', 'green-700 на белом'),
    ('#ef4444', '#ffffff', 'красный на белом'),
    ('#dc2626', '#ffffff', 'red-600 на белом'),
    ('#9f9f9f', '#ffffff', 'divider'),
    ('#6b7280', '#ffffff', 'divider 500'),
    ('#797979', '#ffffff', 'profile email'),
    ('#737373', '#ffffff', 'profile email 737'),
    ('#64748b', '#f8fafc', 'chip на chip-bg'),
    ('#64748b', '#f9f9f9', 'text-2 на soft'),
    ('#64748b', '#fbfcfd', 'text-2 на hero'),
    ('#ffffff', '#dc2626', 'белый на red-600'),
    ('#ffffff', '#b45309', 'белый на amber-700'),
]
for a, b, label in pairs:
    r = ratio(a, b)
    mark = 'OK' if r >= 4.5 else ('AA-large' if r >= 3 else 'FAIL')
    print(f'{label:34s} {a} / {b}: {r:5}  {mark}')