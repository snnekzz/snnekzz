import math
from PIL import Image, ImageDraw, ImageFont
import render4 as M
from render4 import Cam, render3d, wpath, projectile3d, coast_point, P3, L, A, RED, WHITE, YEL, BLACK, W, H, SS, OW, OH, VIG
OUT = "/home/user/snnekzz/videolar/03-kuzey-sentinel/"
t = 10.0
cam = Cam(0, -900, 29000, math.radians(50), math.radians(12))
img = render3d(cam, t)
lay = L(); dl = ImageDraw.Draw(lay)
for k in range(4):                                   # kıyı köpüğü
    ring = M.COAST.buffer(30 + k * 110).exterior.coords
    dl.line(wpath(cam, ring), fill=(240, 250, 255, int(70 * (1 - k / 4))), width=3 * SS)
for rr, al in ((4400, .9), (5600, .6), (6800, .35)):  # tehlike halkaları
    circ = [(math.cos(i / 64 * 6.283) * rr, math.sin(i / 64 * 6.283) * rr) for i in range(65)]
    dl.line(wpath(cam, circ), fill=A(RED, al), width=7 * SS)
for k in range(10):                                  # uçuşan oklar
    an = k * 0.628 + 0.2; cpx, cpy = coast_point(an)
    projectile3d(dl, cam, (cpx, cpy, 5), (cpx + math.cos(an) * 3200, cpy + math.sin(an) * 3200, 0), 0.45 + 0.04 * (k % 3), 1, 420)
img.alpha_composite(lay)
img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * .55)))
# üst/alt karartma
for y0, y1, top in ((0, 1500, True), (H - 1300, H, False)):
    g = Image.new("L", (1, y1 - y0))
    for y in range(y1 - y0):
        f = (1 - y / (y1 - y0)) if top else (y / (y1 - y0))
        g.putpixel((0, y), int(210 * f ** 1.5))
    img.paste((0, 0, 0), (0, y0), g.resize((W, y1 - y0)))
def txt(im, xy, s, size, fill, sw, rot=0):
    f = ImageFont.truetype("anton.ttf", int(size * SS))
    l, tt, r, b = f.getbbox(s, stroke_width=sw * SS)
    t_ = Image.new("RGBA", (r - l + 40, b - tt + 40), (0, 0, 0, 0))
    ImageDraw.Draw(t_).text((20 - l, 20 - tt), s, font=f, fill=fill, stroke_width=sw * SS, stroke_fill=BLACK)
    if rot: t_ = t_.rotate(rot, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(t_, (int(xy[0] - t_.width / 2), int(xy[1] - t_.height / 2)))
txt(img, (W / 2, 210 * SS), "KİMSENİN", 150, WHITE, 9)
txt(img, (W / 2, 390 * SS), "GİREMEDİĞİ ADA", 160, RED, 11, rot=-2)
M.pill(img, "YAKLAŞANA OK ATIYORLAR", W / 2, 1620 * SS, 70, bg=WHITE, fg=RED)
v = img.convert("RGB").resize((OW, OH), Image.LANCZOS); v.save(OUT + "kapak-dikey.jpg", quality=93)
# yatay
cam2 = Cam(0, -600, 24000, math.radians(48), math.radians(12), w=1280 * 2, h=720 * 2)
M_W, M_H = M.W, M.H
hz = Image.new("RGB", (1280, 720), (8, 20, 40))
crop = v.crop((0, 450, 1080, 1530)).resize((720, 720), Image.LANCZOS)
hz.paste(crop, (0, 0))
fd = Image.linear_gradient("L").rotate(90).resize((260, 720))
hz.paste((8, 14, 26), (460, 0, 720, 720), fd); hz.paste((8, 14, 26), (720, 0, 1280, 720))
hz = hz.convert("RGBA")
def txt2(s, xy, size, fill, sw):
    f = ImageFont.truetype("anton.ttf", size); d = ImageDraw.Draw(hz)
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=BLACK)
txt2("KİMSENİN", (985, 230), 120, WHITE, 7); txt2("GİREMEDİĞİ", (985, 370), 120, RED, 7); txt2("ADA", (985, 510), 140, RED, 8)
hz.convert("RGB").save(OUT + "kapak-yatay.jpg", quality=93)
print("ok")
