# -*- coding: utf-8 -*-
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'

def bands(f, label, maxrows=26):
    im = Image.open(os.path.join(D, f)).convert('RGB')
    w, h = im.size
    rows = []
    for y in range(h):
        dark = sum(1 for x in range(0, w, 2) if sum(im.getpixel((x, y))) < 450)
        blue = sum(1 for x in range(0, w, 2) if im.getpixel((x, y))[2] > 200 and im.getpixel((x, y))[0] < 150)
        rows.append((dark, blue))
    def spans(pred):
        out, s = [], None
        for y, (d, b) in enumerate(rows):
            if pred(d, b) and s is None: s = y
            elif not pred(d, b) and s is not None:
                if y - s >= 2: out.append((s, y - 1))
                s = None
        if s is not None: out.append((s, h - 1))
        return out
    print('==', label, im.size)
    print(' dark:', spans(lambda d, b: d > 2)[:maxrows])
    print(' blue:', spans(lambda d, b: b > 2)[:maxrows])

for f, label in [
    ('Report Item — Mobile.png', 'Submit mobile'),
    ('Claim Item — Mobile.png', 'Claim mobile'),
    ('Notifications — Mobile.png', 'Notif mobile'),
    ('Settings — Mobile.png', 'Settings mobile'),
    ('Contact — Mobile.png', 'Contact mobile'),
    ('Signup — Mobile.png', 'Signup mobile'),
    ('Found Items — Mobile.png', 'Found mobile'),
]:
    bands(f, label)