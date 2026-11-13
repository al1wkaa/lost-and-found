# -*- coding: utf-8 -*-
# Выборка цветов пикселей из референсов
import os
from PIL import Image

d = r'C:\Users\User\Documents\lost_foubd\references'

def px(f, pts):
    im = Image.open(os.path.join(d, f)).convert('RGB')
    for name, (x, y) in pts:
        r, g, b = im.getpixel((x, y))
        print(f"{f[:22]:24s} {name:22s} #{r:02x}{g:02x}{b:02x}")

px('Home page.png', [
    ('page_bg_hero', (100, 200)), ('header_bg', (700, 37)), ('logo_text', (160, 37)),
    ('nav_link', (587, 37)), ('btn_primary', (512, 378)), ('btn_primary_text', (470, 377)),
    ('btn_secondary_text', (760, 378)), ('card_bg', (235, 610)), ('card_title', (200, 702)),
    ('card_desc', (160, 745)), ('footer_text', (60, 959)), ('footer_link', (850, 958)),
    ('hero_title_dark', (640, 183)), ('hero_sub', (400, 261)),
])
px('Home page ( after login ).png', [
    ('nav_link_active', (585, 37)), ('card_bg', (235, 610)), ('card_title2', (200, 702)),
])
px('Login page.png', [
    ('page_bg', (100, 300)), ('card_bg', (636, 270)), ('subtitle', (530, 227)),
    ('label', (500, 312)), ('input_bg', (636, 349)), ('input_border', (491, 349)),
    ('input_placeholder', (520, 349)), ('btn_primary', (636, 554)),
    ('forgot_link', (720, 500)), ('or_text', (636, 617)), ('google_btn_bg', (636, 679)),
    ('google_btn_border', (491, 679)), ('bottom_link', (697, 768)),
])
px('Lost page.png', [
    ('page_bg', (100, 200)), ('search_border', (85, 244)), ('chip_bg', (755, 244)),
    ('chip_text', (780, 243)), ('chip_active_bg', (677, 244)), ('card_title', (90, 542)),
    ('card_date', (376, 538)), ('card_loc', (100, 572)), ('card_desc', (100, 599)),
    ('card_link', (240, 646)), ('page_top', (640, 110)),
])
px('Found page.png', [
    ('badge_green_bg', (148, 640)), ('badge_green_text', (105, 640)),
    ('badge_orange_bg', (541, 640)), ('badge_orange_text', (495, 640)),
    ('btn_claim_bg', (244, 690)), ('btn_claim_text', (240, 689)),
])
px('Profile.png', [
    ('page_bg', (640, 650)), ('sidebar_bg', (210, 410)), ('avatar_bg', (210, 194)),
    ('name', (180, 263)), ('stat_num', (120, 334)), ('stat_label', (130, 356)),
    ('tab_active_bg', (210, 412)), ('tab_inactive', (155, 458)), ('list_card_bg', (810, 262)),
    ('status_poterjano', (575, 291)), ('status_naydeno', (560, 646)),
    ('badge_aktivno_bg', (1155, 262)), ('date_right', (1140, 233)),
])
px('Notification page.png', [
    ('page_bg', (640, 110)), ('card_bg', (640, 250)), ('unread_border', (260, 387)),
    ('n_title', (400, 368)), ('n_text', (400, 397)), ('n_time', (960, 364)),
    ('filter_active_bg', (374, 262)), ('filter_inactive_bg', (548, 263)),
    ('mark_read', (947, 162)), ('subtitle', (400, 185)),
])
px('Contact page.png', [
    ('page_bg', (640, 110)), ('card1_bg', (636, 308)), ('thumb_bg', (353, 313)),
    ('copy_btn_text', (910, 550)), ('readonly_bg', (558, 550)),
    ('readonly_text', (410, 550)), ('page_h1', (300, 146)),
])
px('Setting page.png', [
    ('page_bg', (640, 110)), ('card_bg', (775, 500)), ('sidebar_bg', (279, 410)),
    ('side_active_bg', (279, 263)), ('side_inactive', (230, 312)),
    ('avatar_bg', (494, 344)), ('save_btn', (538, 734)),
])
px('claim item page.png', [
    ('page_bg', (640, 50)), ('card_bg', (636, 780)), ('inner_bg', (636, 345)),
    ('inner_label', (330, 282)), ('inner_value', (320, 310)), ('email_link', (390, 382)),
    ('upload_btn_bg', (443, 859)), ('cancel_btn_text', (786, 1324)),
    ('photo_bg', (443, 664)),
])
