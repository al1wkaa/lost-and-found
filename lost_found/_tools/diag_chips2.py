# -*- coding: utf-8 -*-
import os
from PIL import Image

D = r'C:\Users\User\Documents\lost_foubd\references'
for f, ys in [('Lost Items — Mobile.png', [396, 400, 417, 435, 439]),
              ('Notifications — Mobile.png', [300, 310, 330, 340])]:
    im = Image.open(os.path.join(D, f)).convert('RGB')
    print('==', f)
    for y in ys:
        vals = [(x, im.getpixel((x, y))) for x in range(0, 390, 10)]
        print(' y=', y, vals)