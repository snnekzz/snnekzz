"""Profil fotoğrafı – 3 alternatif daha (D, E, F). profil_v2.py'deki yardımcıları kullanır.
Çalıştırma (fontlar + ../tex olan klasörde): python3 profil_v3.py
D) Eski hazine haritası + kırmızı X  E) Anahtar deliğinden dünya  F) Yıldızlardan soru işareti + kâşif"""
import os, math, random
_here = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_here, "profil_v2.py")).read().split("# ---------- A")[0])
OUT = _here + "/"

# ---------- D: Hazine haritası ----------
rng = random.Random(5)
img = radial((238, 214, 168), (150, 108, 62), 1.6)
noise = Image.effect_noise((S, S), 40).convert("L").filter(ImageFilter.GaussianBlur(2))
img = Image.composite(img, Image.new("RGBA", (S, S), (120, 84, 44, 255)), noise.point(lambda v: 255 - int(max(0, v - 100) * .5)))
d = ImageDraw.Draw(img)
INK = (70, 44, 24)
# kıyı / ada şekli
pts = []
for k in range(120):
    a = k / 120 * 2 * math.pi; r = 520 + 60 * math.sin(3 * a) + 40 * math.sin(7 * a + 1) + 25 * math.sin(13 * a)
    pts.append((S / 2 + r * math.cos(a) * 1.05, S / 2 + 40 + r * math.sin(a) * .85))
for k in range(4, 0, -1):    # kıyı dalga çizgileri
    d.polygon([(S / 2 + (x - S / 2) * (1 + k * .045), S / 2 + 40 + (y - S / 2 - 40) * (1 + k * .055)) for x, y in pts], outline=(110, 80, 50, 120))
d.polygon(pts, fill=(214, 186, 132), outline=INK, width=10)
for _ in range(9):           # dağlar
    x, y = rng.uniform(450, 1100), rng.uniform(520, 760)
    d.polygon([(x - 50, y + 35), (x, y - 50), (x + 50, y + 35)], outline=INK, width=8)
for _ in range(10):          # ağaçlar
    x, y = rng.uniform(420, 1150), rng.uniform(900, 1150)
    d.ellipse((x - 22, y - 30, x + 22, y + 10), outline=INK, width=6); d.line([(x, y + 10), (x, y + 32)], fill=INK, width=6)
# kesik çizgili rota
route = [(330, 1250), (430, 1120), (560, 1050), (640, 900), (800, 860), (930, 960), (1040, 880), (1120, 760)]
for (x0, y0), (x1, y1) in zip(route[:-1], route[1:]):
    n = int(math.hypot(x1 - x0, y1 - y0) / 44)
    for i in range(n):
        if i % 2 == 0: d.line([(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n), (x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (i + 1) / n)], fill=RED, width=20)
X, Y = 1150, 700
for s in (1, -1): d.line([(X - 95, Y - 95 * s), (X + 95, Y + 95 * s)], fill=(60, 20, 18), width=62)
for s in (1, -1): d.line([(X - 90, Y - 90 * s), (X + 90, Y + 90 * s)], fill=RED, width=46)
# pusula (sol üst)
cx, cy = 440, 420
d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), outline=INK, width=8)
for k in range(4):
    a = math.radians(k * 90 - 90)
    for sg, col in ((1, INK), (-1, (150, 110, 70))):
        d.polygon([(cx, cy), (cx + 150 * math.cos(a), cy + 150 * math.sin(a)), (cx + 30 * math.cos(a + sg * math.pi / 2), cy + 30 * math.sin(a + sg * math.pi / 2))], fill=col)
ctext(img, "N", cx, cy - 195, 70, INK, font="playfair.ttf")
# yanık kenar
v = Image.new("L", (S, S), 0); ImageDraw.Draw(v).ellipse((60, 60, S - 60, S - 60), fill=255)
img = Image.composite(img, Image.new("RGBA", (S, S), (60, 34, 14, 255)), v.filter(ImageFilter.GaussianBlur(70)))
circle_mask(img).save(OUT + "profil-D-hazine.png")

# ---------- E: Anahtar deliğinden dünya ----------
img = radial((30, 28, 34), (6, 6, 8), 1.3)
wd = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dw = ImageDraw.Draw(wd)
for k in range(0, S, 90):    # ahşap kapı dokusu (çok hafif)
    dw.line([(k, 0), (k + 20, S)], fill=(255, 255, 255, 12), width=3)
img.alpha_composite(wd)
key = Image.new("L", (S, S), 0); dk = ImageDraw.Draw(key)
cx, cy, r = S / 2, 640, 300
dk.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
dk.polygon([(cx - 150, cy + 150), (cx + 150, cy + 150), (cx + 260, 1360), (cx - 260, 1360)], fill=255)
# dışa parıltı
gl = Image.new("RGBA", (S, S), (255, 200, 110, 0)); gl.putalpha(key.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * .9)))
img.alpha_composite(gl)
inside = radial((12, 26, 60), (2, 4, 14)); stars(inside, 260, 4)
gb = globe(560, 30, 28); inside.alpha_composite(gb, (int(cx - 560), 560))
img.paste(inside, (0, 0), key)
# metal plaka kenarı
edge = key.filter(ImageFilter.MaxFilter(25)); ring = Image.new("RGBA", (S, S), (200, 160, 80, 255))
m = Image.fromarray(np.clip(np.asarray(edge, np.int16) - np.asarray(key, np.int16), 0, 255).astype(np.uint8))
img.paste(ring, (0, 0), m)
circle_mask(img).save(OUT + "profil-E-anahtar.png")

# ---------- F: Yıldızlardan soru işareti + kâşif ----------
img = radial((30, 52, 110), (4, 8, 24), 1.1); stars(img, 380, 21)
d = ImageDraw.Draw(img)
# soru işareti takımyıldızı
Q = [(610, 520), (680, 380), (820, 320), (960, 360), (1020, 480), (960, 600), (840, 680), (800, 800), (800, 900)]
glow(img, lambda dd, c: [dd.line([a, b], fill=c, width=24) for a, b in zip(Q[:-1], Q[1:])], (120, 180, 255, 160), 22)
d = ImageDraw.Draw(img)
for a, b in zip(Q[:-1], Q[1:]): d.line([a, b], fill=(200, 225, 255, 210), width=7)
for x, y in Q:
    glow(img, lambda dd, c, x=x, y=y: dd.ellipse((x - 30, y - 30, x + 30, y + 30), fill=c), (255, 255, 255, 200), 14)
    ImageDraw.Draw(img).ellipse((x - 14, y - 14, x + 14, y + 14), fill=WHITE)
X, Y = 800, 1035
glow(img, lambda dd, c: dd.ellipse((X - 60, Y - 60, X + 60, Y + 60), fill=c), (255, 70, 80, 255), 26)
ImageDraw.Draw(img).ellipse((X - 30, Y - 30, X + 30, Y + 30), fill=(255, 90, 90))
# ufuk: dağ silüeti + kâşif
d = ImageDraw.Draw(img)
glow(img, lambda dd, c: dd.rectangle((0, 1180, S, 1320), fill=c), (255, 120, 70, 120), 60)
d = ImageDraw.Draw(img)
mt = [(0, 1300), (180, 1200), (330, 1260), (520, 1150), (700, 1260), (820, 1220), (1000, 1300), (1180, 1180), (1380, 1250), (1600, 1190), (1600, 1600), (0, 1600)]
d.polygon(mt, fill=(8, 10, 18))
d.polygon([(560, 1600), (700, 1330), (800, 1300), (930, 1340), (1060, 1600)], fill=(4, 5, 10))
ex, ey = 800, 1300          # kâşif silüeti (sırt çantalı)
d.ellipse((ex - 16, ey - 150, ex + 16, ey - 118), fill=(4, 5, 10))
d.polygon([(ex - 24, ey - 116), (ex + 24, ey - 116), (ex + 28, ey - 50), (ex - 28, ey - 50)], fill=(4, 5, 10))
d.rounded_rectangle((ex - 48, ey - 112, ex - 16, ey - 56), 8, fill=(4, 5, 10))
d.polygon([(ex - 26, ey - 52), (ex - 4, ey - 52), (ex - 12, ey), (ex - 30, ey)], fill=(4, 5, 10))
d.polygon([(ex + 4, ey - 52), (ex + 26, ey - 52), (ex + 32, ey), (ex + 14, ey)], fill=(4, 5, 10))
d.line([(ex + 22, ey - 108), (ex + 50, ey - 160)], fill=(4, 5, 10), width=12)      # yukarıyı gösteren kol
circle_mask(img).save(OUT + "profil-F-yildiz.png")
print("ok")
