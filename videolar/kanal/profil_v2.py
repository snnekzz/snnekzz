"""Profil fotoğrafı – 3 sade alternatif (küçük daire boyutunda da okunur).
Çalıştırma (fontlar + ../tex dokusu olan klasörde): python3 profil_v2.py
A) Büyüteçli dünya  B) Soru işaretli konum iğnesi  C) Pusula + halka yazı"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
S = 1600
RED, YEL, WHITE, NAVY = (226, 32, 44), (255, 204, 0), (255, 255, 255), (10, 18, 40)
F = lambda n, s: ImageFont.truetype(n, int(s))
EARTH = np.asarray(Image.open("../tex/2_no_clouds_4k.jpg").convert("RGB"), np.float32)
TH, TW = EARTH.shape[:2]

def radial(c0, c1, power=1.4):
    yy, xx = np.mgrid[0:S, 0:S] / S - .5
    r = np.clip(np.sqrt(xx ** 2 + yy ** 2) / .7, 0, 1) ** power
    a = np.array(c0, np.float32) * (1 - r[..., None]) + np.array(c1, np.float32) * r[..., None]
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")

def globe(R, lon0, lat0):
    """ortografik dünya, ışık sol üstten, atmosfer parıltısı"""
    n = 2 * R; yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x = (xx - R + .5) / R; y = -(yy - R + .5) / R; rr = x * x + y * y; m = rr <= 1
    z = np.sqrt(np.clip(1 - rr, 0, 1)); la0, lo0 = math.radians(lat0), math.radians(lon0)
    lat = np.arcsin(np.clip(y * math.cos(la0) + z * math.sin(la0), -1, 1))
    lon = lo0 + np.arctan2(x, z * math.cos(la0) - y * math.sin(la0))
    px = ((np.degrees(lon) + 180) % 360) / 360 * TW; py = (90 - np.degrees(lat)) / 180 * TH
    col = np.stack([ndimage.map_coordinates(EARTH[..., c], [py, px], order=1, mode="wrap") for c in range(3)], -1)
    col = np.clip((col - 128) * 1.25 + 128 + 8, 0, 255)                      # canlı renk
    L = np.clip(.25 + .95 * (-.55 * x + .5 * y + .67 * z), .12, 1.15)        # ışık
    col = col * L[..., None]
    rim = np.clip((rr - .75) / .25, 0, 1) ** 2                                  # atmosfer kenarı
    col = col * (1 - rim[..., None] * .5) + np.array([90, 170, 255]) * rim[..., None] * .5
    a = np.where(m, 255, 0).astype(np.uint8)
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA"); im.putalpha(Image.fromarray(a))
    return im

def stars(img, n, seed=3):
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(1, 3.2)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(rng.uniform(80, 230))))

def glow(img, shape_fn, color, blur):
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0)); shape_fn(ImageDraw.Draw(g), color)
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))

def pin(d, cx, cy, r, fill, outline=None, ow=0):
    """konum iğnesi: başı (cx,cy) merkezli r yarıçaplı, ucu aşağıda"""
    tip = cy + r * 2.25
    a = math.asin(r / (tip - cy))
    pts = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(-math.pi / 2 + a - math.pi / 2 + math.pi / 2 - a, 0, 1)]
    left = (cx - r * math.cos(a), cy + r * math.sin(a)); right = (cx + r * math.cos(a), cy + r * math.sin(a))
    if outline:
        d.polygon([(left[0] - ow, left[1]), (right[0] + ow, right[1]), (cx, tip + ow * 1.6)], fill=outline)
        d.ellipse((cx - r - ow, cy - r - ow, cx + r + ow, cy + r + ow), fill=outline)
    d.polygon([left, right, (cx, tip)], fill=fill)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)

def ctext(img, s, cx, cy, size, fill, font="anton.ttf", sw=0, sc=(0, 0, 0)):
    ImageDraw.Draw(img).text((cx, cy), s, font=F(font, size), fill=fill, anchor="mm", stroke_width=sw, stroke_fill=sc)

def ring_text(img, s, cx, cy, R, size, fill, font="mont900.ttf", start=-90, spread=None, inside=False):
    f = F(font, size); widths = [f.getlength(ch) for ch in s]; tot = sum(widths) + size * .08 * (len(s) - 1)
    ang = math.degrees(tot / R) if spread is None else spread
    sg = -1 if inside else 1                     # altta yazı ters yönde ilerler (soldan sağa okunsun)
    a = start - sg * ang / 2
    for ch, w in zip(s, widths):
        da = sg * math.degrees((w + size * .08) / R); mid = a + sg * math.degrees(w / 2 / R)
        t = Image.new("RGBA", (int(size * 1.6), int(size * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((t.width / 2, t.height / 2), ch, font=f, fill=fill, anchor="mm")
        rot = -(mid + 90) if not inside else -(mid - 90)
        t = t.rotate(rot, resample=Image.BICUBIC)
        x = cx + R * math.cos(math.radians(mid)); y = cy + R * math.sin(math.radians(mid))
        img.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2))); a += da

def circle_mask(img):
    m = Image.new("L", (S * 2, S * 2), 0); ImageDraw.Draw(m).ellipse((0, 0, S * 2, S * 2), fill=255)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0)); out.paste(img, (0, 0), m.resize((S, S), Image.LANCZOS)); return out

# ---------- A: Büyüteçli dünya ----------
img = radial((22, 40, 82), (4, 8, 20)); stars(img, 260)
cx, cy, R = 690, 690, 430
glow(img, lambda d, c: d.ellipse((cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30), fill=c), (70, 150, 255, 150), 60)
# sap
hx0, hy0 = cx + (R + 40) * .707, cy + (R + 40) * .707; hx1, hy1 = 1300, 1300
hl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dh = ImageDraw.Draw(hl)
dh.line([(hx0, hy0), (hx1, hy1)], fill=(20, 20, 26), width=150)
dh.line([(hx0 + 30, hy0 + 30), (hx1, hy1)], fill=RED, width=124)
dh.ellipse((hx1 - 62, hy1 - 62, hx1 + 62, hy1 + 62), fill=RED)
dh.line([(hx0 + 60, hy0 + 40), (hx1 - 20, hy1 - 40)], fill=(255, 120, 120), width=18)   # parlama
img.alpha_composite(hl)
img.alpha_composite(globe(R, 33, 30), (cx - R, cy - R))
d = ImageDraw.Draw(img)
d.ellipse((cx - R - 52, cy - R - 52, cx + R + 52, cy + R + 52), outline=(20, 20, 26), width=26)
d.ellipse((cx - R - 44, cy - R - 44, cx + R + 44, cy + R + 44), outline=(235, 238, 245), width=50)
d.arc((cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30), 200, 250, fill=WHITE, width=14)
lens = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(lens).ellipse((cx - R * .85, cy - R * .9, cx - R * .1, cy - R * .35), fill=(255, 255, 255, 40))
img.alpha_composite(lens.filter(ImageFilter.GaussianBlur(30)))
d = ImageDraw.Draw(img)
pin(d, cx + 10, cy - 170, 120, RED, outline=(255, 255, 255), ow=14)
ctext(img, "?", cx + 10, cy - 172, 170, WHITE)
circle_mask(img).save(OUT + "profil-A-buyutec.png")

# ---------- B: Soru işaretli iğne, kırmızı zemin ----------
img = radial((240, 50, 58), (120, 8, 18), 1.2)
d = ImageDraw.Draw(img)
for k in range(-6, 7):                      # meridyen/paralel çizgileri (harita hissi)
    w = abs(k) / 6
    d.ellipse((S / 2 - S * .62 * (1 - w ** 2) ** .5 if abs(k) < 6 else S / 2 - 2, -40, S / 2 + S * .62 * (1 - w ** 2) ** .5 if abs(k) < 6 else S / 2 + 2, S + 40), outline=(255, 255, 255, 34), width=5)
for k in range(1, 8): y = k * S / 8; d.line([(0, y), (S, y)], fill=(255, 255, 255, 30), width=5)
glow(img, lambda dd, c: pin(dd, S / 2, 620, 330, c), (0, 0, 0, 170), 50)
d = ImageDraw.Draw(img)
pin(d, S / 2, 600, 330, WHITE)
ctext(img, "?", S / 2, 590, 470, RED)
d.ellipse((S / 2 - 170, 1390, S / 2 + 170, 1450), fill=(0, 0, 0, 70))
circle_mask(img).save(OUT + "profil-B-igne.png")

# ---------- C: Pusula + halka yazı ----------
img = radial((24, 34, 60), (6, 9, 18)); stars(img, 120, 9)
c = S / 2; d = ImageDraw.Draw(img)
d.ellipse((60, 60, S - 60, S - 60), outline=RED, width=34)
d.ellipse((330, 330, S - 330, S - 330), outline=(255, 255, 255, 90), width=8)
for k in range(72):
    a = math.radians(k * 5); r0 = 452 if k % 2 == 0 else 470
    d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + 490 * math.cos(a), c + 490 * math.sin(a))], fill=(255, 255, 255, 120), width=5)
ring_text(img, "BİLİNMEYENİN", c, c, 600, 118, WHITE, start=-90)
ring_text(img, "PEŞİNDE", c, c, 645, 118, YEL, start=90, inside=True)
for k in (-1, 1): d.ellipse((c + k * 610 - 18, c - 18, c + k * 610 + 18, c + 18), fill=RED)
star = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ds = ImageDraw.Draw(star)
def ray(a, L, w, col, half):
    a = math.radians(a); p = (c + L * math.cos(a), c + L * math.sin(a))
    q = (c + w * math.cos(a + (math.pi / 2 if half else -math.pi / 2)), c + w * math.sin(a + (math.pi / 2 if half else -math.pi / 2)))
    ds.polygon([(c, c), p, q], fill=col)
for k in range(4):
    a = -90 + 45 + k * 90; ray(a, 250, 50, (180, 186, 200), 1); ray(a, 250, 50, (120, 126, 140), 0)
for k in range(4):
    a = -90 + k * 90; L = 430 if k == 0 else 400
    hi = RED if k == 0 else (245, 247, 252); lo = (160, 14, 26) if k == 0 else (170, 176, 190)
    ray(a, L, 80, hi, 1); ray(a, L, 80, lo, 0)
glow(img, lambda dd, col: dd.ellipse((c - 300, c - 300, c + 300, c + 300), fill=col), (255, 60, 70, 60), 80)
img.alpha_composite(star)
d = ImageDraw.Draw(img); d.ellipse((c - 46, c - 46, c + 46, c + 46), fill=YEL, outline=(20, 20, 26), width=10)
ctext(img, "?", c, c - 2, 70, (20, 20, 26))
circle_mask(img).save(OUT + "profil-C-pusula.png")
print("ok")
