import math
from PIL import Image, ImageDraw
import render7 as M
from render7 import W, H, SS, OW, OH, L, A, WHITE, YEL, RED, BLACK, VIG
import brand
OUT = "/home/user/snnekzz/videolar/05-istiklal-yolu/"
cam = M.Cam(*M.ll2m(33.35, 40.80), 700000, math.radians(22), math.radians(0))
img, g = M.render_base(cam, 30.0); fp = M.footprint(g)
pts = M.ring_pts(cam, M.DR)
lay = L(); d = ImageDraw.Draw(lay)
d.line(pts, fill=(0, 0, 0, 140), width=26 * SS, joint="curve"); d.line(pts, fill=A(M.GOLD, 1), width=12 * SS, joint="curve")
d.line(pts, fill=A(M.GOLD, .35), width=50 * SS, joint="curve")
img.alpha_composite(lay)
for nm, ll, dx in (("İNEBOLU", M.INEBOLU, 170), ("KASTAMONU", M.KASTAMONU, 190), ("ÇANKIRI", M.CANKIRI, 160), ("ANKARA", M.ANKARA, -150)):
    q = M.pj(cam, *ll)
    if q:
        lay = L(); dd = ImageDraw.Draw(lay); r = 16 * SS
        dd.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=RED, outline=WHITE, width=5 * SS); img.alpha_composite(lay)
        M.ytag(img, q[0] + dx * SS, q[1], nm, 1, 1.15, 46)
img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * .35)))
# üst karartma + marka kartı (büyük)
gr = Image.linear_gradient("L").resize((W, 1400)).transpose(Image.FLIP_TOP_BOTTOM).point(lambda v: int(v * .8))
img.paste((0, 0, 0), (0, 0), gr)
brand.brand_card(img, 5.0, "İNEBOLU'DAN ANKARA'YA", "BİR MERMİ KAÇ GÜNDE?", 99, y_center=330)
M.hand(img, "330 km • 2 hafta", W * .30, 1130 * SS, 92, 1, YEL, -10)
# alt: büyük kağnı + kadın
gb = Image.linear_gradient("L").resize((W, 1300)).point(lambda v: int(v * .75))
img.paste((0, 0, 0), (0, H - 1300), gb)
lay = L(); dd = ImageDraw.Draw(lay)
M.kagni(dd, W * .70, 1540 * SS, 2.9, 1, 1.0)
M.woman(dd, W * .09, 1552 * SS, 2.6, 1, .5)
img.alpha_composite(lay)
M.serif(img, "İstiklal Yolu", W / 2, 1745 * SS, 118, 1, M.GOLD)
brand.watermark(img, 38.0, 60)
v = img.convert("RGB").resize((OW, OH), Image.LANCZOS); v.save(OUT + "kapak-dikey.jpg", quality=93)
hz = Image.new("RGB", (1280, 720), (12, 16, 24)); hz.paste(v.crop((0, 600, 1080, 1680)).resize((720, 720), Image.LANCZOS), (0, 0))
fd = Image.linear_gradient("L").rotate(90).resize((260, 720)); hz.paste((12, 16, 24), (460, 0, 720, 720), fd); hz.paste((12, 16, 24), (720, 0, 1280, 720))
from PIL import ImageFont
d2 = ImageDraw.Draw(hz)
for txt, y, col, sz in (("İNEBOLU'DAN", 170, (255, 255, 255), 96), ("ANKARA'YA", 290, (255, 255, 255), 96), ("KAÇ GÜNDE?", 430, (255, 210, 63), 104)):
    d2.text((990, y), txt, font=ImageFont.truetype("anton.ttf", sz), fill=col, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
d2.text((990, 570), "İstiklal Yolu", font=ImageFont.truetype("playfair.ttf", 64), fill=(255, 200, 80), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
hz.save(OUT + "kapak-yatay.jpg", quality=93)
print("ok")
