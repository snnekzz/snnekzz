import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import render2 as R
R.caption = lambda img, t: None
R.header = lambda img, t: None
OUT = "/home/user/snnekzz/videolar/01-misir-sinirlari/"
base = R.frame(30.0).convert("RGBA")
W, H = base.size
P = R.Proj(R.camera(30.0))
def sp(lo, la): x, y = P.xy(lo, la); return (x/2, y/2)
d = ImageDraw.Draw(base)
for a, b in ((sp(25.0, 22.0), sp(36.87, 22.0)), (sp(25.0, 22.0), sp(25.0, 31.49))):
    d.line([a, b], fill=(255, 255, 255), width=30); d.line([a, b], fill=(214, 40, 57), width=18)
clean = base.copy()
FA = "anton.ttf"; YEL = (255, 210, 63); BLK = (15, 15, 18); RED = (214, 40, 57); WHITE = (255, 255, 255)

def txt(img, xy, s, size, fill, sw=10, rot=0):
    f = ImageFont.truetype(FA, size)
    l, t, r, b = f.getbbox(s, stroke_width=sw)
    lay = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((10 - l, 10 - t), s, font=f, fill=fill, stroke_width=sw, stroke_fill=BLK)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(xy[0] - lay.width / 2), int(xy[1] - lay.height / 2)))

# üst karartma şeridi
grad = Image.new("L", (1, 700))
for y in range(700): grad.putpixel((0, y), int(215 * (1 - y / 700) ** 1.4))
base.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, 700), 0)] * 3 + [grad.resize((W, 700))]), (0, 0))
txt(base, (W / 2, 190), "MISIR'IN SINIRLARI", 128, WHITE, 9)
txt(base, (W / 2, 360), "NEDEN DÜMDÜZ?", 168, YEL, 12, rot=-3)

# cetvel 22. enlem üzerinde
(x0, y0), (x1, _) = sp(25.0, 22.0), sp(36.87, 22.0)
rl, rw = 520, 72; rx = (x0 + x1) / 2 - rl / 2; ry = y0 - 16 - rw
d = ImageDraw.Draw(base)
d.rounded_rectangle((rx, ry, rx + rl, ry + rw), radius=10, fill=(250, 214, 80), outline=(60, 45, 10), width=4)
for k in range(41):
    xx = rx + 12 + k * (rl - 24) / 40; tl = 30 if k % 10 == 0 else 20 if k % 5 == 0 else 11
    d.line([(xx, ry + rw), (xx, ry + rw - tl)], fill=(60, 45, 10), width=3)

# alt şerit: merak sorusu
grad2 = Image.new("L", (1, 520))
for y in range(520): grad2.putpixel((0, y), int(225 * (y / 520) ** 1.3))
base.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, 520), 0)] * 3 + [grad2.resize((W, 520))]), (0, H - 520))
f = ImageFont.truetype(FA, 74)
pw, ph = f.getlength("KİMSENİN İSTEMEDİĞİ TOPRAK") + 80, 120
d = ImageDraw.Draw(base)
d.rounded_rectangle((W / 2 - pw / 2, 1640, W / 2 + pw / 2, 1640 + ph), radius=60, fill=WHITE, outline=BLK, width=6)
d.text((W / 2, 1640 + ph / 2), "KİMSENİN İSTEMEDİĞİ TOPRAK", font=f, fill=RED, anchor="mm")
txt(base, (W * 0.70, 860), "?", 260, YEL, 14, rot=12)
v = base.convert("RGB"); v.save(OUT + "kapak-dikey.jpg", quality=93)

# yatay 1280x720: harita solda, yazı sağda
hz = Image.new("RGB", (1280, 720), (24, 30, 44))
crop = clean.convert("RGB").crop((0, 420, 1080, 1500)).resize((720, 720), Image.LANCZOS)
hz.paste(crop, (0, 0))
fade = Image.new("L", (260, 720))
for x in range(260): 
    for y in range(0, 720, 720): pass
fd = Image.linear_gradient("L").rotate(90).resize((260, 720))
hz.paste((24, 30, 44), (460, 0, 720, 720), fd)
hz = hz.convert("RGBA")
txt(hz, (980, 210), "MISIR'IN", 120, WHITE, 8)
txt(hz, (980, 340), "SINIRLARI", 120, WHITE, 8)
txt(hz, (985, 500), "NEDEN", 130, YEL, 9, rot=-3)
txt(hz, (985, 625), "DÜMDÜZ?", 130, YEL, 9, rot=-3)
hz.convert("RGB").save(OUT + "kapak-yatay.jpg", quality=93)
print("ok")
