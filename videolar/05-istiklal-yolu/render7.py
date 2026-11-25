"""Video 5: İstiklal Yolu – yeni teknikler: üst altyazı, marka kartı, el yazısı notlar, 'ya da' kartı,
yolculuk sayacı, serif yıllar, filigran, kar yağışı."""
import json, math, os, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, LineString, Point
import render as R
from render import stamp_text, pill, partial, vis, prog, back, eout, ease, FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys, tr_up
from render3 import A, L, RED, WHITE, YEL, BLACK, VIG, CLOUDS, clamp01
from render4 import globe, sample, EARTH, fractal, Cam, persp_coeffs
import brand

FC, FP = "caveat.ttf", "playfair.ttf"           # el yazısı, serif
LON0, LAT0D = 33.4, 40.9
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
C_TR = (227, 10, 23); BLUE = (37, 99, 235); GOLD = (255, 200, 80)

G = json.load(open("countries10_me.json"))
CN = {}
for f in G["features"]:
    g = shape(f["geometry"]).buffer(0).intersection(box(18, 30, 50, 48))
    if not g.is_empty: CN[f["properties"]["name"]] = g
TR = CN["Turkey"]
INEBOLU = (33.76, 41.975); KASTAMONU = (33.78, 41.38); ILGAZ = (33.64, 41.02); CANKIRI = (33.62, 40.60); ANKARA = (32.85, 39.93); ISTANBUL = (28.97, 41.01)
ROUTE = [INEBOLU, (33.80, 41.75), KASTAMONU, (33.70, 41.17), ILGAZ, (33.63, 40.85), CANKIRI, (33.35, 40.35), (33.08, 40.12), ANKARA]
SEA = [(36.8, 43.6), (35.6, 43.0), (34.5, 42.4), (33.95, 42.1), INEBOLU]

exec(open("maplib_src.py").read())   # build_tex, render_base, pj, raised, flag_pin, tag, curved_arrow, zoom_blur, typewriter ...
TEX_BIG = build_tex(24, 46, 34, 44, 4096, 3, "tex_big.png")
TEX_DET = build_tex(31.0, 36.0, 39.3, 42.6, 4096, 9, "tex_det.png")
TB = tex_info(24, 46, 34, 44, TEX_BIG); TD = tex_info(31.0, 36.0, 39.3, 42.6, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

# ---------- kamera ----------
def lerp(a, b, p): return a + (b - a) * p
T_GLOBE = 2.4
K = [
    (T_GLOBE - .3, 33.5, 40.0, 2400, 0, 0),
    (st("intro") + 4.2, 33.4, 40.6, 1300, 20, 0),
    (st("hook") + .5, 33.35, 40.95, 640, 24, 0),
    (st("sea") + .6, 31.2, 41.6, 1400, 20, 0),
    (st("route") + .6, 33.35, 40.95, 620, 28, 0),
    (st("kagni") + .6, 33.74, 41.55, 430, 38, 6),
    (st("ilgaz") + .6, 33.62, 41.02, 420, 40, -4),
    (st("days") + .6, 33.35, 40.95, 640, 26, 0),
    (st("women") + .6, 33.45, 40.85, 560, 30, 4),
    (st("serife") + .6, 33.6, 41.0, 420, 40, -2),
    (st("legacy") + .5, 33.33, 40.95, 650, 26, 0),
    (st("cta") + .6, 33.2, 40.9, 950, 22, 0),
    (TOTAL, 33.2, 40.9, 1050, 20, 0),
]
def cam_at(t):
    if t <= K[0][0]: a = b = K[0]; p = 0
    elif t >= K[-1][0]: a = b = K[-1]; p = 0
    else:
        for a, b in zip(K[:-1], K[1:]):
            if a[0] <= t <= b[0]: p = ease((t - a[0]) / (b[0] - a[0])); break
    lon, lat = lerp(a[1], b[1], p), lerp(a[2], b[2], p)
    D = math.exp(lerp(math.log(a[3]), math.log(b[3]), p)) * 1000
    x, y = ll2m(lon, lat)
    return Cam(x, y, D, math.radians(lerp(a[4], b[4], p)), math.radians(lerp(a[5], b[5], p) + 1.2 * math.sin(t * .2)))

# ---------- yolculuk ilerlemesi (0..1) ----------
def journey(t):
    p1 = lerp(0.0, 0.48, ease(prog(t, st("kagni") + .4, en("ilgaz") - st("kagni"))))
    p2 = lerp(0.0, 0.52, ease(prog(t, st("days") + .2, en("days") - st("days"))))
    return p1 + p2
def dense(path, n=16):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        for k in range(n): out.append((lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
    out.append(path[-1]); return out
DR = dense(ROUTE)

# ---------- yeni yardımcılar ----------
def hand(img, text, x, y, size, a, col=WHITE, rot=-6, sc=1.0):
    """el yazısı not"""
    if a <= .01 or sc <= .01: return
    f = font(FC, size * SS * sc); l, t_, r, b = f.getbbox(text, stroke_width=4 * SS)
    lay = Image.new("RGBA", (r - l + 40, b - t_ + 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20 - l, 20 - t_), text, font=f, fill=A(col, a), stroke_width=int(4 * SS), stroke_fill=(0, 0, 0, int(200 * a)))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def hand_arrow(img, p0, p1, a, prog_=1.0):
    curved_arrow(img, p0, p1, a, .35, prog_, col=WHITE, width=4)
def serif(img, text, x, y, size, a, col=GOLD, sc=1.0):
    if a <= .01 or sc <= .01: return
    stamp_text(img, text, (x, y), FP, size, fill=col, stroke=BLACK, alpha=a, scale=sc)
def ytag(img, x, y, text, a, sc=1.0, size=44, bg=YEL, fg=BLACK):
    if a <= .01 or sc <= .01: return
    f = font(FA, size * SS * sc); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 30 * SS * sc, b - t_ + 22 * SS * sc
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((14, 14, w + 14, h + 14), fill=(0, 0, 0, int(100 * a))); d.rectangle((8, 8, w + 8, h + 8), fill=A(bg, a))
    d.text((8 + w / 2, 8 + h / 2), text, font=f, fill=A(fg, a), anchor="mm")
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

def kagni(d, x, y, s, a, t, quilt=False, walk=True):
    s *= SS; wood = A((150, 105, 60), a); dark = A((70, 45, 25), a)
    d.ellipse((x - 150 * s, y + 18 * s, x + 90 * s, y + 40 * s), fill=(0, 0, 0, int(70 * a)))
    # öküz
    ox = x - 105 * s; step = math.sin(t * 6) * 8 * s if walk else 0
    for k, lx in enumerate((-30, -14, 14, 30)):
        dx = step if k % 2 == 0 else -step
        d.line([(ox + lx * s, y - 10 * s), (ox + lx * s + dx, y + 26 * s)], fill=A((90, 60, 35), a), width=int(7 * s))
    d.ellipse((ox - 46 * s, y - 42 * s, ox + 40 * s, y + 2 * s), fill=A((125, 85, 50), a), outline=dark, width=int(2 * s) + 1)
    d.ellipse((ox - 70 * s, y - 46 * s, ox - 38 * s, y - 18 * s), fill=A((115, 78, 45), a), outline=dark)
    d.arc((ox - 78 * s, y - 62 * s, ox - 54 * s, y - 38 * s), 180, 300, fill=A((230, 220, 200), a), width=int(4 * s))
    d.arc((ox - 56 * s, y - 62 * s, ox - 32 * s, y - 38 * s), 240, 360, fill=A((230, 220, 200), a), width=int(4 * s))
    # boyunduruk
    d.line([(ox + 30 * s, y - 30 * s), (x - 20 * s, y - 14 * s)], fill=dark, width=int(5 * s))
    # araba
    d.polygon([(x - 30 * s, y - 20 * s), (x + 90 * s, y - 20 * s), (x + 84 * s, y - 2 * s), (x - 24 * s, y - 2 * s)], fill=wood, outline=dark)
    for k in range(-20, 90, 22): d.line([(x + k * s, y - 20 * s), (x + k * s, y - 52 * s)], fill=dark, width=int(3 * s) + 1)
    d.line([(x - 26 * s, y - 52 * s), (x + 88 * s, y - 52 * s)], fill=dark, width=int(4 * s))
    if quilt:
        d.chord((x - 26 * s, y - 92 * s, x + 88 * s, y - 14 * s), 180, 360, fill=A((176, 40, 50), a), outline=dark)
        for k in range(6):
            cx = x - 14 * s + k * 18 * s; cy = y - 40 * s - 10 * s * math.sin(k)
            d.ellipse((cx - 4 * s, cy - 4 * s, cx + 4 * s, cy + 4 * s), fill=A((250, 210, 120), a))
    else:
        for row in range(2):
            for k in range(5):
                cx = x - 10 * s + k * 20 * s; cy = y - 30 * s - row * 18 * s
                d.rounded_rectangle((cx - 7 * s, cy - 8 * s, cx + 7 * s, cy + 8 * s), radius=int(5 * s), fill=A((150, 150, 140), a), outline=dark)
                d.polygon([(cx - 7 * s, cy - 8 * s), (cx + 7 * s, cy - 8 * s), (cx, cy - 18 * s)], fill=A((180, 140, 60), a))
    # tekerlek (dönen)
    cx, cy, r = x + 30 * s, y + 4 * s, 26 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=A((120, 80, 45), a), outline=dark, width=int(4 * s))
    for k in range(3):
        an = t * 3 + k * math.pi / 3
        d.line([(cx - math.cos(an) * r, cy - math.sin(an) * r), (cx + math.cos(an) * r, cy + math.sin(an) * r)], fill=dark, width=int(3 * s))
def woman(d, x, y, s, a, t, bend=0.0):
    s *= SS; step = math.sin(t * 6) * 6 * s
    d.line([(x - 6 * s, y), (x - 6 * s + step, y + 30 * s)], fill=A((60, 40, 30), a), width=int(5 * s))
    d.line([(x + 6 * s, y), (x + 6 * s - step, y + 30 * s)], fill=A((60, 40, 30), a), width=int(5 * s))
    d.polygon([(x - 16 * s, y + 4 * s), (x + 16 * s, y + 4 * s), (x + 9 * s, y - 38 * s), (x - 9 * s, y - 38 * s)], fill=A((110, 60, 70), a))
    hx = x + bend * 18 * s
    d.ellipse((hx - 10 * s, y - 60 * s, hx + 10 * s, y - 40 * s), fill=A((230, 200, 170), a))
    d.chord((hx - 14 * s, y - 66 * s, hx + 14 * s, y - 36 * s), 150, 390, fill=A((230, 220, 200), a))
def ship(d, x, y, s, a):
    s *= SS; o = A((30, 30, 35), a)
    d.polygon([(x - 80 * s, y), (x + 80 * s, y), (x + 64 * s, y + 24 * s), (x - 70 * s, y + 24 * s)], fill=A((60, 60, 70), a), outline=o)
    d.rectangle((x - 30 * s, y - 26 * s, x + 30 * s, y), fill=A((220, 215, 200), a), outline=o)
    d.rectangle((x + 4 * s, y - 56 * s, x + 18 * s, y - 26 * s), fill=A((180, 40, 40), a), outline=o)
    for k in range(3): d.ellipse((x + 8 * s + k * 6 * s, y - 80 * s - k * 12 * s, x + 26 * s + k * 9 * s, y - 64 * s - k * 12 * s), fill=(200, 200, 200, int(110 * a / (k + 1))))
def truck(d, x, y, s, a):
    s *= SS; c = A((90, 110, 80), a); o = A((30, 30, 30), a)
    d.rectangle((x - 70 * s, y - 50 * s, x + 20 * s, y), fill=c, outline=o, width=int(3 * s))
    d.polygon([(x + 20 * s, y - 36 * s), (x + 55 * s, y - 36 * s), (x + 70 * s, y - 14 * s), (x + 70 * s, y), (x + 20 * s, y)], fill=c, outline=o)
    for wx in (-45, 45): d.ellipse((x + wx * s - 15 * s, y - 10 * s, x + wx * s + 15 * s, y + 20 * s), fill=A((30, 30, 30), a))
def train(d, x, y, s, a):
    s *= SS; c = A((60, 60, 70), a); o = A((20, 20, 20), a)
    d.rectangle((x - 70 * s, y - 40 * s, x + 50 * s, y), fill=c, outline=o, width=int(3 * s))
    d.rectangle((x + 10 * s, y - 70 * s, x + 50 * s, y - 40 * s), fill=c, outline=o)
    d.rectangle((x - 60 * s, y - 62 * s, x - 44 * s, y - 40 * s), fill=c, outline=o)
    for wx in (-50, -15, 25): d.ellipse((x + wx * s - 13 * s, y - 6 * s, x + wx * s + 13 * s, y + 20 * s), fill=A((180, 40, 40), a), outline=o)
    for k in range(3): d.ellipse((x - 62 * s - k * 10 * s, y - 92 * s - k * 14 * s, x - 42 * s + k * 6 * s, y - 72 * s - k * 14 * s), fill=(210, 210, 210, int(120 * a / (k + 1))))
def vs_card(img, cx, cy, label, drawer, a, sc, crossed):
    if a <= .01 or sc <= .01: return
    w, h = int(330 * SS * sc), int(330 * SS * sc)
    lay = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((14, 16, w + 10, h + 12), radius=int(30 * SS * sc), fill=(0, 0, 0, int(100 * a)))
    d.rounded_rectangle((4, 4, w, h), radius=int(30 * SS * sc), fill=(20, 24, 32, int(235 * a)), outline=A(WHITE, a), width=int(5 * SS * sc))
    drawer(d, w / 2 + 4, h * .55, 1.6 * sc, a)
    d.text((w / 2 + 4, h * .84), label, font=font(FA, int(54 * SS * sc)), fill=A(WHITE, a), anchor="mm")
    if crossed > 0:
        k = crossed
        for sg in (1, -1):
            d.line([(w * .2, h * (.5 - .3 * sg * k)), (w * .2 + w * .6 * k, h * (.5 + .3 * sg * k))], fill=A((230, 40, 50), a), width=int(16 * SS * sc))
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

rnd = random.Random(11)
FLAKES = [(rnd.random(), rnd.random(), rnd.uniform(.5, 1.6), rnd.uniform(.4, 1.0)) for _ in range(260)]
def snow(img, t, a):
    if a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay)
    for fx, fy, sz, sp in FLAKES:
        x = (fx * W + math.sin(t * 1.3 + fy * 9) * 30 * SS) % W; y = ((fy + t * .09 * sp) % 1) * H
        r = sz * 4 * SS; d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(200 * a * sp)))
    img.alpha_composite(lay)

def brand_card(img, t):
    return brand.brand_card(img, t, "İNEBOLU'DAN ANKARA'YA", "BİR MERMİ KAÇ GÜNDE?", en("hook") + .2)
def _old_brand_card(img, t):
    a = vis(t, .2, en("hook") + .2, .35, .4)
    if a <= 0: return
    sc = .9 + .1 * back(prog(t, .2, .4))
    lay = Image.new("RGBA", (W, 360 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 900 * SS * sc, 230 * SS * sc; x0, y0 = W / 2 - w / 2, 180 * SS - h / 2
    d.rounded_rectangle((x0 + 10, y0 + 14, x0 + w + 10, y0 + h + 14), radius=int(38 * SS), fill=(0, 0, 0, 110))
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(38 * SS), fill=(14, 16, 22, 235))
    tw = font(F9, int(26 * SS * sc)).getlength("BİLİNMEYENİN PEŞİNDE")
    d.rounded_rectangle((W / 2 - tw / 2 - 20 * SS, y0 - 22 * SS, W / 2 + tw / 2 + 20 * SS, y0 + 22 * SS), radius=int(22 * SS), fill=A(RED, 1))
    d.text((W / 2, y0), "BİLİNMEYENİN PEŞİNDE", font=font(F9, int(26 * SS * sc)), fill=WHITE, anchor="mm")
    d.text((W / 2, y0 + h * .40), "İNEBOLU'DAN ANKARA'YA", font=font(FA, int(70 * SS * sc)), fill=WHITE, anchor="mm")
    d.text((W / 2, y0 + h * .76), "BİR MERMİ KAÇ GÜNDE?", font=font(FA, int(64 * SS * sc)), fill=YEL, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, 470 * SS))

def caption_top(img, t):
    """Haritanın Ardı tarzı: üstte küçük tek satır, söylenen kelime renkli kutuda"""
    c = next((c for c in R.CAPS if c["start"] <= t < c["end"]), None)
    if not c: return
    size = 48 * SS; f = font(F9, size); sp = f.getlength(" ")
    words = [tr_up(w) for w in c["words"]]
    cur = max(i for i, wt in enumerate(c["wt"]) if wt <= t)
    ws = [f.getlength(w) for w in words]; tw = sum(ws) + sp * (len(words) - 1)
    if tw > W * .9:
        size = size * W * .9 / tw; f = font(F9, size); sp = f.getlength(" "); ws = [f.getlength(w) for w in words]; tw = sum(ws) + sp * (len(words) - 1)
    pop = .9 + .1 * back(prog(t, c["start"], .12))
    lay = Image.new("RGBA", (W, int(size * 2.2)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x = W / 2 - tw / 2; y = size * 1.1
    for i, w in enumerate(words):
        if i == cur:
            d.rounded_rectangle((x - 12 * SS, y - size * .62, x + ws[i] + 12 * SS, y + size * .58), radius=int(10 * SS), fill=A(BLUE, 1))
            d.text((x, y), w, font=f, fill=WHITE, anchor="lm")
        else:
            d.text((x, y), w, font=f, fill=WHITE, anchor="lm", stroke_width=int(size / 9), stroke_fill=(0, 0, 0, 220))
        x += ws[i] + sp
    if pop < 1: lay = lay.resize((lay.width, lay.height))
    img.alpha_composite(lay, (0, int(330 * SS - size * 1.1)))

def watermark(img, t):
    return brand.watermark(img, t, TOTAL)
def _old_watermark(img, t):
    a = .55 * min(prog(t, .5, .5), 1)
    stamp_text(img, "@BilinmeyeninPesinde", (W / 2, 1820 * SS), F9, 26, fill=WHITE, stroke=BLACK, alpha=a)

# ---------- kare ----------
def frame(t):
    if t < T_GLOBE:
        p = ease(t / T_GLOBE)
        img = globe(lerp(10, 33, p), lerp(28, 40, p), math.exp(lerp(math.log(420), math.log(2300), ease(p ** 1.3))), t).resize((W, H), Image.BICUBIC).convert("RGBA")
        if t > T_GLOBE - .45:
            b, _ = render_base(cam_at(T_GLOBE - .3), t); img = Image.blend(img, b, clamp01((t - (T_GLOBE - .45)) / .45))
        cam = None
    else:
        cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
        overlays(img, cam, fp, t)
        img = zoom_blur(img, t)
    sn = vis(t, st("ilgaz") + .2, en("ilgaz") + .4, .6, .8) + vis(t, st("serife") - .2, en("serife") + .3, .6, .8)
    if sn > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (210, 225, 240, int(45 * min(1, sn)))))
    dark = vis(t, st("serife") - .2, en("serife") + .2, .8, .8)
    if dark > 0: img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 24, int(130 * dark))))
    snow(img, t, min(1, sn))
    ui(img, cam, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * (.14 + .35 * dark))))
    caption_top(img, t)
    watermark(img, t)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def overlays(img, cam, fp, t):
    a_tr = vis(t, T_GLOBE, st("hook") + .3, .5, .6)
    glow_outline(img, cam, TR, (255, 90, 90), a_tr * .8, fp, 5)
    raised(img, cam, TR, C_TR, a_tr, fp, lift=8, simplify=0.02, fill_a=.30)
    # İstanbul işgal
    a_i = vis(t, st("sea") + .3, en("sea") + .3, .3, .3)
    qi = pj(cam, *ISTANBUL)
    if qi and a_i > 0:
        lay = L(); d = ImageDraw.Draw(lay); r = (70 + 10 * math.sin(t * 5)) * SS
        d.ellipse((qi[0] - r, qi[1] - r, qi[0] + r, qi[1] + r), outline=A((255, 60, 60), a_i), width=6 * SS)
        img.alpha_composite(lay)
        hand(img, "İşgal altında!", qi[0] + 40 * SS, qi[1] - 150 * SS, 66, a_i, (255, 200, 200), -8, back(prog(t, st("sea") + .3, .35)))
    # gemi rotası
    a_s = vis(t, st("sea") + 1.2, en("route") + .3, .3, .4)
    if a_s > 0:
        pts = ring_pts(cam, dense(SEA, 10)); ps = eout(prog(t, st("sea") + 1.2, 2.2))
        lay = L(); d = ImageDraw.Draw(lay)
        if len(pts) > 1:
            R.dashed(d, partial(pts, ps), A(WHITE, a_s), 5 * SS, 16, 12)
            sx, sy = partial(pts, ps)[-1]; ship(d, sx, sy, 1.0, a_s)
        img.alpha_composite(lay)
        if ps > .4:
            sx, sy = partial(pts, ps)[-1]
            hand(img, "Gizlice...", sx + 150 * SS, sy - 120 * SS, 60, a_s, WHITE, -6)
    # rota (kağnı yolu)
    a_r = vis(t, st("route") + .2, TOTAL, .3, .3)
    if a_r > 0:
        pr = eout(prog(t, st("route") + .4, 2.4))
        pts = ring_pts(cam, DR)
        gold = vis(t, st("legacy"), TOTAL, .6, .3)
        col = tuple(int(lerp((255, 255, 255)[i], GOLD[i], gold)) for i in range(3))
        lay = L(); d = ImageDraw.Draw(lay)
        if len(pts) > 1:
            d.line(partial(pts, pr), fill=A((0, 0, 0), a_r * .5), width=int((16 + 10 * gold) * SS), joint="curve")
            d.line(partial(pts, pr), fill=A(col, a_r), width=int((7 + 5 * gold) * SS), joint="curve")
            if gold > 0: d.line(partial(pts, pr), fill=A(GOLD, a_r * gold * .35), width=40 * SS, joint="curve")
        img.alpha_composite(lay)
    # şehir iğneleri / etiketleri
    for nm, ll, t0 in (("İNEBOLU", INEBOLU, st("hook") + .2), ("ANKARA", ANKARA, st("hook") + .6), ("KASTAMONU", KASTAMONU, st("route") + .9),
                       ("ÇANKIRI", CANKIRI, st("route") + 1.6)):
        q = pj(cam, *ll)
        if q:
            a = vis(t, t0, TOTAL, .3, .3) * (1 - vis(t, st("serife") - .2, en("serife"), .3, .3))
            if a > 0:
                lay = L(); d = ImageDraw.Draw(lay); r = 12 * SS
                d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=A(RED, a), outline=A(WHITE, a), width=4 * SS)
                img.alpha_composite(lay)
                ytag(img, q[0] + (150 if nm != "ANKARA" else -120) * SS, q[1], nm, a, back(prog(t, t0, .35)), 40)
    # hook: soru işareti rotanın ortasında
    a_q = vis(t, st("hook") + .8, en("hook") + .2, .3, .3)
    qm = pj(cam, 33.6, 40.95)
    if qm and a_q > 0:
        stamp_text(img, "?", (qm[0], qm[1]), FA, 230, fill=YEL, alpha=a_q, scale=back(prog(t, st("hook") + .8, .4)), rot=8)
    # km notu
    a_k = vis(t, st("route") + 2.6, en("route") + .2, .3, .3)
    qk = pj(cam, 34.1, 40.9)
    if qk: hand(img, "≈ 330 km", qk[0], qk[1], 80, a_k, YEL, -10, back(prog(t, st("route") + 2.6, .35)))
    # Ilgaz etiketi
    qg = pj(cam, *ILGAZ)
    if qg:
        hand(img, "Ilgaz Dağları", qg[0] + 260 * SS, qg[1] + 120 * SS, 66, vis(t, st("ilgaz") + .4, en("ilgaz") + .2, .3, .3), WHITE, -6)
    # kağnı (yolculuk)
    a_c = vis(t, st("kagni") + .2, st("women") + .2, .4, .4)
    if a_c > 0:
        p = journey(t); ll = partial(DR, max(.001, p))[-1]; q = pj(cam, *ll)
        if q:
            lay = L(); d = ImageDraw.Draw(lay)
            s = 1.5 * 420000 / max(q[2], 250000)
            kagni(d, q[0], q[1], s, a_c, t)
            if t > st("women"): woman(d, q[0] - 210 * SS * s, q[1] + 6 * SS, s, a_c * vis(t, st("women"), 99, .4, .1), t)
            img.alpha_composite(lay)
            # sayaç
            days = 14 * p; km = 330 * p
            ytag(img, q[0], q[1] - 190 * SS * s, f"GÜN {min(14, int(days) + (1 if p > 0 else 0))}  •  {int(km)} KM", a_c, 1.0, 54, bg=WHITE)
        a_n = vis(t, st("kagni") + 3.2, en("kagni") + .3, .3, .3)
        if q: hand(img, "Günde ~20 km", q[0] + 60 * SS, q[1] + 150 * SS, 62, a_n, YEL, 4, back(prog(t, st("kagni") + 3.2, .35)))

def ui(img, cam, t):
    brand_card(img, t)
    a = vis(t, st("sea") + .4, en("sea") + .2, .3, .3)
    serif(img, "1920 – 1922", W / 2, 520 * SS, 110, a, GOLD, back(prog(t, st("sea") + .4, .4)))
    # ya da kartı
    a = vis(t, st("versus") - .1, en("versus") + .3, .3, .3)
    if a > 0:
        cr = eout(prog(t, st("versus") + 2.0, .5))
        vs_card(img, W * .27, 760 * SS, "KAMYON", truck, a, back(prog(t, st("versus"), .4)), cr)
        vs_card(img, W * .73, 760 * SS, "TREN", train, a, back(prog(t, st("versus") + .7, .4)), cr)
        hand(img, "ya da", W / 2, 760 * SS, 72, a * vis(t, st("versus") + .5, 99, .3, .1), YEL, -8)
    a = vis(t, st("kagni") + .1, st("kagni") + 1.7, .3, .4)
    if a > 0:
        vs_card(img, W / 2, 760 * SS, "KAĞNI ✓" if False else "KAĞNI", lambda d, x, y, s, al: kagni(d, x + 20 * SS, y, .9 * s / 1.6, al, t), a, back(prog(t, st("kagni") + .1, .4)), 0)
    # iki hafta
    a = vis(t, st("days") + .6, en("days") + .4, .3, .3)
    stamp_text(img, "≈ 2 HAFTA", (W / 2, 540 * SS), FA, 140, fill=YEL, alpha=a, scale=back(prog(t, st("days") + .6, .4)))
    # kadınlar ve çocuklar (ekran illüstrasyonu)
    a = vis(t, st("women") + .1, en("women") + .3, .5, .5)
    if a > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(90 * a))))
        kagni(d, W * .70, 1000 * SS, 2.4, a, t)
        woman(d, W * .12, 1010 * SS, 2.4, a, t)
        woman(d, W * .24, 1030 * SS, 1.6, a, t + .5)
        img.alpha_composite(lay)
    a = vis(t, st("women") + 1.6, en("women") + .2, .3, .3)
    hand(img, "Erkekler cephedeydi...", W / 2, 560 * SS, 74, a, WHITE, -5, back(prog(t, st("women") + 1.6, .35)))
    # Şerife Bacı sahnesi (ekran illüstrasyonu)
    a = vis(t, st("serife") + .2, en("serife") + .3, .6, .6)
    if a > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        kagni(d, W * .58, 980 * SS, 3.0, a, t, quilt=t > st("serife") + 2.2, walk=False)
        woman(d, W * .22, 990 * SS, 3.0, a, 0, bend=.6)
        img.alpha_composite(lay)
        serif(img, "Şerife Bacı", W / 2, 520 * SS, 96, a, (240, 225, 200), back(prog(t, st("serife") + .4, .45)))
        hand(img, "mermiler ıslanmasın diye...", W / 2, 1220 * SS, 64, a * vis(t, st("serife") + 2.2, 99, .4, .1), (255, 225, 190), -4)
    # İstiklal Yolu
    a = vis(t, st("legacy") + .3, en("legacy") + .8, .3, .4)
    serif(img, "İstiklal Yolu", W / 2, 540 * SS, 120, a, GOLD, back(prog(t, st("legacy") + .3, .45)))
    # kapanış
    a = vis(t, st("cta") + .3, TOTAL, .3, .3)
    if a > 0:
        hand(img, "Bugün arabayla: ? saat", W / 2, 560 * SS, 86, a, YEL, -6, back(prog(t, st("cta") + .3, .4)))
        pill(img, "YORUMLARA YAZ!", W / 2, 700 * SS, 58, alpha=vis(t, st("cta") + 1.2, TOTAL, .25, .3), scale=back(prog(t, st("cta") + 1.2, .35)))

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s7_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
