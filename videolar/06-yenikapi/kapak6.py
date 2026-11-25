"""Yenikapı kapakları: dikey 1080x1920 + yatay 1280x720.
Çalıştırma: fontların (anton.ttf, caveat.ttf, mont900.ttf) bulunduğu klasörde  python3 kapak6.py
Sahne: üstte gün batımında İstanbul silüeti + kazı kulesi, altta çamurda yatan Bizans gemileri, dikey kazı kuyusu ve ışık."""
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
YEL, WHITE, BLACK, RED = (255, 214, 0), (255, 255, 255), (0, 0, 0), (225, 30, 45)
F = lambda n, s: ImageFont.truetype(n, int(s))

def grad(w, h, stops):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        p = y / (h - 1)
        for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
            if p <= p1:
                k = (p - p0) / max(1e-6, p1 - p0); g.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))); break
    return g.resize((w, h))

def ship(d, x, y, s, rot, col=(110, 74, 42), out=(38, 24, 14)):
    pts = [(-120, -10), (-100, 20), (-40, 34), (40, 34), (100, 20), (124, -14), (90, 0), (-90, 0)]
    cr, sr = math.cos(rot), math.sin(rot)
    T = lambda px, py: (x + (px * cr - py * sr) * s, y + (px * sr + py * cr) * s)
    d.polygon([T(*p) for p in pts], fill=col, outline=out, width=max(1, int(3 * s)))
    for k in range(-80, 100, 22): d.line([T(k, 2), T(k, 30)], fill=out, width=max(1, int(4 * s)))
    d.line([T(-110, 4), T(110, 4)], fill=(150, 108, 66), width=max(1, int(3 * s)))      # güverte ışığı
    d.line([T(-10, 0), T(-14, -80)], fill=out, width=max(2, int(7 * s)))                  # kırık direk

def amphora(d, x, y, s, rot=0):
    c, o = (196, 112, 70), (90, 48, 28)
    d.ellipse((x - 14 * s, y - 20 * s, x + 14 * s, y + 18 * s), fill=c, outline=o, width=max(1, int(2 * s)))
    d.rectangle((x - 5 * s, y - 34 * s, x + 5 * s, y - 18 * s), fill=c, outline=o)
    d.polygon([(x - 6 * s, y + 16 * s), (x + 6 * s, y + 16 * s), (x, y + 30 * s)], fill=c, outline=o)

def text(img, s, cx, cy, size, fill, sw, rot=0, font="anton.ttf", shadow=True):
    f = F(font, size); l, t, r, b = f.getbbox(s, stroke_width=sw)
    lay = Image.new("RGBA", (r - l + 60, b - t + 60), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((30 - l, 30 - t), s, font=f, fill=fill, stroke_width=sw, stroke_fill=BLACK)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    x, y = int(cx - lay.width / 2), int(cy - lay.height / 2)
    if shadow:
        sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * .6)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * .06)), (x + int(size * .04), y + int(size * .06)))
    img.alpha_composite(lay, (x, y))

def pill(img, s, cx, cy, size, bg, fg):
    f = F("mont900.ttf", size); l, t, r, b = f.getbbox(s); w, h = r - l + size * 1.1, b - t + size * .75
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=bg, outline=BLACK, width=max(2, int(size * .08)))
    d.text((cx, cy), s, font=f, fill=fg, anchor="mm")

def scene(W, H, surf, shaft_x, rng, big_ships):
    """surf: yüzey çizgisi y; big_ships: [(x, y, ölçek, açı)]"""
    img = Image.new("RGBA", (W, H))
    img.paste(grad(W, surf, [(0, (18, 30, 70)), (.6, (120, 70, 110)), (1, (250, 150, 80))]), (0, 0))
    d = ImageDraw.Draw(img)
    u = H / 1920 if H > W else H / 720 * .55
    # güneş
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sun).ellipse((W * .66, surf - 210 * u, W * .66 + 260 * u, surf + 50 * u), fill=(255, 200, 120, 200))
    img.alpha_composite(sun.filter(ImageFilter.GaussianBlur(30 * u)))
    # İstanbul silüeti (camiler, minareler)
    sil = (28, 22, 40)
    x = 0
    while x < W:
        bw = rng.randint(40, 90) * u; bh = rng.randint(30, 90) * u
        d.rectangle((x, surf - bh, x + bw, surf), fill=sil); x += bw
    for cx, r in ((W * .30, 120 * u), (W * .70, 95 * u)):
        d.rectangle((cx - r * 1.2, surf - r * 1.1, cx + r * 1.2, surf), fill=sil)
        d.pieslice((cx - r, surf - r * 2.0, cx + r, surf - r * .1), 180, 360, fill=sil)
        for k in (-1, 1):
            mx = cx + k * r * 1.55
            d.rectangle((mx - 9 * u, surf - r * 3.0, mx + 9 * u, surf), fill=sil)
            d.polygon([(mx - 11 * u, surf - r * 3.0), (mx + 11 * u, surf - r * 3.0), (mx, surf - r * 3.5)], fill=sil)
    # kazı kulesi (vinç)
    d.line([(shaft_x - 60 * u, surf), (shaft_x - 60 * u, surf - 260 * u)], fill=(255, 170, 0), width=int(10 * u))
    d.line([(shaft_x - 60 * u, surf - 250 * u), (shaft_x + 200 * u, surf - 250 * u)], fill=(255, 170, 0), width=int(9 * u))
    d.line([(shaft_x + 120 * u, surf - 250 * u), (shaft_x + 120 * u, surf + 120 * u)], fill=(60, 60, 60), width=int(3 * u))
    # toprak katmanları
    layers = [(0, 60, (128, 92, 60)), (60, 130, (104, 74, 48)), (130, 210, (86, 62, 42)), (210, 9999, None)]
    for a, b, c in layers:
        y0, y1 = surf + a * u, min(H, surf + b * u)
        if c: d.rectangle((0, y0, W, y1), fill=c); d.line([(0, y0), (W, y0)], fill=(40, 28, 18), width=int(3 * u))
    mud0 = int(surf + 210 * u)
    img.paste(grad(W, H - mud0, [(0, (70, 82, 92)), (.5, (44, 54, 64)), (1, (20, 24, 30))]), (0, mud0))
    d = ImageDraw.Draw(img)
    d.line([(0, mud0), (W, mud0)], fill=(30, 22, 16), width=int(4 * u))
    for _ in range(int(W * H / 9000)):                      # taşlar / çakıl
        sx, sy, r = rng.uniform(0, W), rng.uniform(surf, H), rng.uniform(3, 12) * u
        d.ellipse((sx - r, sy - r * .6, sx + r, sy + r * .6), fill=(30, 24, 20, 255) if sy < mud0 else (32, 40, 48))
    # kazı kuyusu
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    ds.polygon([(shaft_x - 80 * u, surf), (shaft_x + 80 * u, surf), (shaft_x + 150 * u, H), (shaft_x - 150 * u, H)], fill=(0, 0, 0, 70))
    img.alpha_composite(sh)
    # küçük uzak gemiler
    d = ImageDraw.Draw(img)
    for _ in range(26):
        ship(d, rng.uniform(0, W), rng.uniform(mud0 + 60 * u, H - 40 * u), rng.uniform(.35, .75) * u, rng.uniform(-.35, .35),
             col=(78, 60, 44), out=(30, 22, 16))
    # ışık (kazı lambası)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(gl)
    for x, y, s, r in big_ships:
        dg.ellipse((x - 330 * s, y - 200 * s, x + 330 * s, y + 200 * s), fill=(255, 200, 130, 38))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(50 * u)))
    d = ImageDraw.Draw(img)
    for x, y, s, r in big_ships:
        ship(d, x, y, s, r)
    return img, mud0, u

# ---------- DİKEY ----------
W, H = 1080, 1920
rng = random.Random(7)
img, mud0, u = scene(W, H, 600, 540, rng, [(250, 1520, 1.55, -.18), (820, 1640, 1.7, .14), (540, 1810, 1.25, -.05)])
d = ImageDraw.Draw(img)
for k in range(4): amphora(d, 170 + k * 44, 1470 + k * 7, 1.15)        # güvertede yük
for k in range(4): amphora(d, 740 + k * 48, 1590 - k * 6, 1.25)
# üst karartma (yazı okunurluğu)
top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); top.putalpha(grad(W, H, [(0, (170,) * 3), (.2, (60,) * 3), (.3, (0,) * 3), (1, (0,) * 3)]).convert("L"))
img.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), Image.new("RGBA", (W, H), (0, 0, 0, 0)), top.getchannel("A")))
pill(img, "BİLİNMEYENİN PEŞİNDE", W / 2, 90, 30, RED, WHITE)
text(img, "İSTANBUL'DA METRO KAZARKEN", W / 2, 200, 74, WHITE, 5)
text(img, "37", W / 2, 1000, 420, YEL, 16)
text(img, "GEMİ ÇIKTI!", W / 2, 1290, 170, WHITE, 10, rot=-3)
text(img, "1.500 yıllık!", 300, 1420, 92, YEL, 4, rot=-8, font="caveat.ttf")
text(img, "@BilinmeyeninPesinde", W / 2, 1880, 30, (230, 230, 230), 2, font="mont900.ttf")
img.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
img.convert("RGB").save(OUT + "kapak.jpg", quality=93)

# ---------- YATAY ----------
W, H = 1280, 720
rng = random.Random(11)
img, mud0, u = scene(W, H, 230, 330, rng, [(190, 520, 1.05, -.15), (470, 640, 1.15, .12)])
d = ImageDraw.Draw(img)
for k in range(4): amphora(d, 120 + k * 36, 455 + k * 5, .95)
text(img, '1.500 yıllık!', 330, 400, 60, YEL, 3, rot=-8, font='caveat.ttf')
dark = Image.new("L", (W, H))
dark.putdata([int(235 * min(1, max(0, (x / W - .48) / .2))) for y in range(H) for x in range(W)])
img.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (8, 12, 20, 255)), Image.new("RGBA", (W, H), (0, 0, 0, 0)), dark))
text(img, "METRO KAZARKEN", 950, 150, 64, WHITE, 4)
text(img, "37 GEMİ", 950, 330, 190, YEL, 9)
text(img, "ÇIKTI!", 950, 520, 130, WHITE, 7, rot=-3)
pill(img, "İSTANBUL'UN ALTINDA", 950, 655, 26, RED, WHITE)
img.convert("RGB").save(OUT + "kapak-yatay.jpg", quality=93)
print("ok")
