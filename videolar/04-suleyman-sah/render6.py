"""Video 4: Süleyman Şah Türbesi – uydu + eski harita, gece operasyonu, Haritalogy teknikleri."""
import json, math, os, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, LineString, Point
from shapely.ops import unary_union
import render as R
import render2 as R2
from render import stamp_text, pill, card, partial, vis, prog, back, eout, ease, FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys
from render3 import A, L, RED, WHITE, YEL, BLACK, VIG, CLOUDS, clamp01
from render4 import globe, sample, EARTH, fractal, Cam, persp_coeffs

LON0, LAT0D = 38.0, 36.5
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
C_TR = (227, 10, 23); C_SY = (200, 190, 160)

G = json.load(open("countries10_me.json"))
CN = {}
for f in G["features"]:
    g = shape(f["geometry"]).buffer(0).intersection(box(18, 24, 56, 48))
    if not g.is_empty: CN[f["properties"]["name"]] = g
TR, SY = CN["Turkey"], CN["Syria"]
CABER = (38.43, 35.89); KARAKOZAK = (38.09, 36.65); ESME = (38.19, 36.826); KOBANI = (38.36, 36.86)
LAKE = Polygon([(38.10, 36.10), (38.20, 36.06), (38.33, 35.99), (38.46, 35.93), (38.58, 35.88), (38.55, 35.84), (38.40, 35.86), (38.27, 35.93), (38.15, 36.00), (38.08, 36.06)])
FIRAT = [(37.97, 37.15), (38.00, 36.95), (38.01, 36.83), (38.06, 36.73), (38.09, 36.65), (38.13, 36.52), (38.18, 36.38), (38.15, 36.25), (38.12, 36.10), (38.24, 36.03), (38.40, 35.95), (38.56, 35.87), (38.78, 35.90), (39.01, 35.95)]
ROUTE_IN = [(38.36, 36.90), (38.37, 36.82), (38.30, 36.74), (38.18, 36.68), (38.09, 36.65)]
ROUTE_OUT = [(38.09, 36.65), (38.13, 36.72), (38.17, 36.78), (38.19, 36.826)]
BORDER_PT = (38.22, 36.832)

exec(open("maplib_src.py").read())   # build_tex, render_base, pj, raised, flag_pin, tag, curved_arrow, zoom_blur ...

# eski kâğıt harita dokusu (uydu dokusundan)
def paper_of(img, fname):
    if os.path.exists(fname): return Image.open(fname).convert("RGB")
    g = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    p = ImageOps.colorize(g, black=(110, 85, 55), mid=(205, 182, 140), white=(242, 230, 198))
    n = np.asarray(Image.fromarray((fractal(1024, 7, 77, k0=5) * 255).astype(np.uint8)).resize(p.size, Image.BICUBIC), np.float32) / 255
    a = np.asarray(p, np.float32) * (0.9 + 0.16 * n[..., None])
    p = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    p.save(fname); return p
TEX_BIG = build_tex(26, 46, 30, 42, 4096, 3, "tex_big.png")
TEX_DET = build_tex(36.6, 40.4, 35.3, 37.5, 4096, 7, "tex_det.png")
PAP_BIG = paper_of(TEX_BIG, "pap_big.png"); PAP_DET = paper_of(TEX_DET, "pap_det.png")
TB = tex_info(26, 46, 30, 42, TEX_BIG); TD = tex_info(36.6, 40.4, 35.3, 37.5, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0
_base = render_base
def base_mix(cam, t):
    f = vis(t, st("who") - .3, en("flag") + .2, .7, .7)       # eski harita bölümü
    if f <= 0: return _base(cam, t)
    TB["img"], TD["img"] = PAP_BIG, PAP_DET
    p, g = _base(cam, t)
    TB["img"], TD["img"] = TEX_BIG, TEX_DET
    if f >= 1: return p, g
    s, _ = _base(cam, t)
    return Image.blend(s, p, f), g

# ---------- kamera ----------
def lerp(a, b, p): return a + (b - a) * p
T_GLOBE = 2.4
K = [
    (T_GLOBE - .3, 36.0, 38.0, 2600, 0, 0),
    (st("intro") + 3.2, 37.6, 37.7, 1500, 22, 0),
    (st("name") + .3, 38.19, 36.78, 220, 40, 0),
    (st("who") + .6, 38.30, 36.40, 720, 26, 0),
    (st("river") + 1.0, 38.30, 36.25, 620, 28, 0),
    (st("y1921") + .5, 38.40, 35.98, 380, 34, 0),
    (en("flag"), 38.42, 35.96, 330, 38, 6),
    (st("y1973") + .8, 38.26, 36.30, 560, 28, 0),
    (st("size") + .4, 38.10, 36.66, 240, 42, 0),
    (st("siege") + .4, 38.10, 36.66, 170, 48, -6),
    (st("operation") + .5, 38.22, 36.76, 280, 44, -8),
    (en("rescue"), 38.17, 36.76, 250, 44, -4),
    (st("today") + .6, 38.19, 36.86, 160, 46, 0),
    (st("cta") + .5, 37.4, 37.4, 1300, 26, 0),
    (TOTAL, 37.3, 37.5, 1500, 24, 0),
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
    return Cam(x, y, D, math.radians(lerp(a[4], b[4], p)), math.radians(lerp(a[5], b[5], p) + 1.5 * math.sin(t * .2)))

# ---------- yeni ikonlar ----------
def tr_flag(w, h, wave=0.0, t=0.0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h), fill=(227, 10, 23, 255))
    r = h * .25; cx, cy = w * .38, h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE); r2 = r * .8
    d.ellipse((cx - r2 + r * .25, cy - r2, cx + r2 + r * .25, cy + r2), fill=(227, 10, 23))
    sx, sr = cx + r * 1.05, r * .42
    pts = [(sx + (sr if i % 2 == 0 else sr * .4) * math.cos(-math.pi / 2 + i * math.pi / 5), cy + (sr if i % 2 == 0 else sr * .4) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=WHITE)
    if wave:
        a = np.asarray(im); out = np.zeros_like(a)
        for x in range(w):
            dy = int(wave * h * .08 * math.sin(x / w * 6 + t * 6) * (x / w))
            out[:, x] = np.roll(a[:, x], dy, axis=0)
        im = Image.fromarray(out)
    return im
_flag_orig = flag_draw
def flag_draw2(kind, w, h):
    if kind == "turkey": return tr_flag(w, h).convert("RGB")
    if kind == "france":
        im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
        for i, c in enumerate([(0, 85, 164), (255, 255, 255), (239, 65, 53)]): d.rectangle((i * w / 3, 0, (i + 1) * w / 3, h), fill=c)
        return im
    return _flag_orig(kind, w, h)
flag_draw = flag_draw2
def tomb(d, x, y, s, a):
    s *= SS; st_ = A((236, 222, 190), a); o = A((70, 55, 40), a)
    d.rectangle((x - 60 * s, y - 30 * s, x + 60 * s, y + 20 * s), fill=st_, outline=o, width=int(3 * s) + 1)
    d.polygon([(x - 46 * s, y - 30 * s), (x + 46 * s, y - 30 * s), (x + 38 * s, y - 62 * s), (x - 38 * s, y - 62 * s)], fill=st_, outline=o)
    d.pieslice((x - 40 * s, y - 104 * s, x + 40 * s, y - 22 * s), 180, 360, fill=A((70, 120, 110), a), outline=o, width=int(3 * s) + 1)
    d.line([(x, y - 64 * s), (x, y - 86 * s)], fill=A((220, 190, 90), a), width=int(4 * s) + 1)
    d.ellipse((x - 7 * s, y - 98 * s, x + 7 * s, y - 84 * s), outline=A((220, 190, 90), a), width=int(3 * s) + 1)
    d.rectangle((x - 12 * s, y - 8 * s, x + 12 * s, y + 20 * s), fill=A((90, 70, 50), a))
def flag_pole(img, x, y, s, a, t, rise=1.0):
    if a <= .01: return
    s *= SS; h = 170 * s
    lay = L(); d = ImageDraw.Draw(lay)
    d.line([(x, y), (x, y - h)], fill=A((230, 230, 230), a), width=int(5 * s) + 1)
    img.alpha_composite(lay)
    fw, fh = int(100 * s), int(66 * s)
    fl = tr_flag(fw, fh, wave=1.0, t=t)
    if a < 1: fl.putalpha(fl.getchannel("A").point(lambda v: int(v * a)))
    fy = y - h + (1 - rise) * (h - fh)
    img.alpha_composite(fl, (int(x + 3 * s), int(fy)))
def tank(d, x, y, s, a, light=False, face=1):
    s *= SS; c = A((86, 96, 70), a); o = A((30, 34, 26), a)
    if light:
        d.polygon([(x + face * 50 * s, y - 6 * s), (x + face * 200 * s, y - 40 * s), (x + face * 200 * s, y + 30 * s)], fill=(255, 240, 180, int(60 * a)))
    d.rounded_rectangle((x - 52 * s, y - 4 * s, x + 52 * s, y + 18 * s), radius=int(9 * s), fill=A((40, 44, 36), a), outline=o)
    d.polygon([(x - 48 * s, y - 4 * s), (x + 48 * s, y - 4 * s), (x + 40 * s, y - 20 * s), (x - 44 * s, y - 20 * s)], fill=c, outline=o)
    d.rounded_rectangle((x - 22 * s, y - 34 * s, x + 18 * s, y - 18 * s), radius=int(6 * s), fill=c, outline=o)
    d.line([(x + face * 14 * s, y - 27 * s), (x + face * 64 * s, y - 30 * s)], fill=o, width=int(5 * s) + 1)
    for k in range(-40, 50, 16):
        d.ellipse((x + k * s - 6 * s, y + 2 * s, x + k * s + 6 * s, y + 14 * s), fill=A((70, 72, 66), a))
def soldier(d, x, y, s, a, col=(86, 104, 70)):
    s *= SS; c = A(col, a)
    d.pieslice((x - 9 * s, y - 40 * s, x + 9 * s, y - 24 * s), 180, 360, fill=A((60, 74, 50), a))
    d.ellipse((x - 7 * s, y - 34 * s, x + 7 * s, y - 20 * s), fill=A((230, 200, 170), a))
    d.rounded_rectangle((x - 10 * s, y - 20 * s, x + 10 * s, y + 6 * s), radius=int(5 * s), fill=c)
def scroll_card(img, cx, cy, a, sc):
    if a <= .01 or sc <= .01: return
    s = SS * sc; w, h = 470 * s, 170 * s
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((10, 10, w, h), radius=int(20 * s), fill=(243, 232, 200, int(245 * a)), outline=(110, 85, 50, int(255 * a)), width=int(4 * s))
    for yy in (10, h): d.ellipse((0, yy - 14 * s, 26 * s, yy + 14 * s), fill=(200, 180, 140, int(255 * a)))
    d.text((w / 2 + 5, 62 * s), "ANKARA ANTLAŞMASI", font=font(FA, 46 * s), fill=(60, 40, 20, int(255 * a)), anchor="mm")
    d.text((w / 2 + 5, 118 * s), "Türkiye • Fransa • 1921", font=font(F9, 26 * s), fill=(120, 90, 55, int(255 * a)), anchor="mm")
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))
def flag_card(img, kind, cx, cy, w, a, sc):
    if a <= .01 or sc <= .01: return
    w = int(w * SS * sc); h = int(w * 2 / 3)
    fl = flag_draw2(kind, w, h).convert("RGBA")
    m = Image.new("L", fl.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(h * .12), fill=int(255 * a)); fl.putalpha(m)
    bw = int(6 * SS * sc); bg = Image.new("RGBA", (w + 2 * bw + 12, h + 2 * bw + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(bg)
    d.rounded_rectangle((10, 14, w + 2 * bw + 8, h + 2 * bw + 12), radius=int(h * .12) + bw, fill=(0, 0, 0, int(90 * a)))
    d.rounded_rectangle((0, 0, w + 2 * bw, h + 2 * bw), radius=int(h * .12) + bw, fill=(255, 255, 255, int(255 * a)))
    bg.alpha_composite(fl, (bw, bw))
    img.alpha_composite(bg, (int(cx - bg.width / 2), int(cy - bg.height / 2)))
def ytag(img, x, y, text, a, sc=1.0, size=48, bg=YEL, fg=BLACK):
    """Haritalogy tarzı sarı etiket kutusu"""
    if a <= .01 or sc <= .01: return
    f = font(FA, size * SS * sc); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 30 * SS * sc, b - t_ + 22 * SS * sc
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((14, 14, w + 14, h + 14), fill=(0, 0, 0, int(100 * a)))
    d.rectangle((8, 8, w + 8, h + 8), fill=A(bg, a))
    d.text((8 + w / 2, 8 + h / 2), text, font=f, fill=A(fg, a), anchor="mm")
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def family_tree(img, t, t0, a):
    if a <= .01: return
    names = ["SÜLEYMAN ŞAH", "ERTUĞRUL GAZİ", "OSMAN GAZİ"]
    y = 1180 * SS; xs = [W * .2, W * .5, W * .8]
    lay = L(); d = ImageDraw.Draw(lay)
    for i in range(2):
        p = eout(prog(t, t0 + .5 + i * .6, .4))
        if p > 0: R.arrow(d, (xs[i] + 70 * SS, y), (xs[i] + 70 * SS + (xs[i + 1] - xs[i] - 140 * SS) * p, y), A(WHITE, a), 6 * SS)
    img.alpha_composite(lay)
    for i, n in enumerate(names):
        sc = back(prog(t, t0 + i * .6, .35))
        if sc <= .01: continue
        r = 46 * SS * sc
        lay = L(); d = ImageDraw.Draw(lay)
        d.ellipse((xs[i] - r, y - r, xs[i] + r, y + r), fill=A(YEL if i == 0 else WHITE, a), outline=A(BLACK, a), width=4 * SS)
        d.text((xs[i], y), str(i + 1), font=font(FA, 56 * SS * sc), fill=A(BLACK, a), anchor="mm")
        img.alpha_composite(lay)
        ytag(img, xs[i], y + 90 * SS, n, a, sc * .8, 40, bg=YEL if i == 0 else WHITE)
def pitch_card(img, t, t0, a):
    if a <= .01: return
    s = SS; cx, cy = W / 2, 560 * SS
    sc = back(prog(t, t0, .4)); w, h = 860 * s * sc, 400 * s * sc
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((10, 10, w, h), radius=int(26 * s), fill=(20, 24, 30, int(225 * a)), outline=A(WHITE, a), width=int(4 * s))
    # futbol sahası (105x68)
    px, py, pw, ph = 50 * s * sc, 90 * s * sc, 330 * s * sc, 214 * s * sc
    d.rectangle((px, py, px + pw, py + ph), fill=A((60, 150, 70), a), outline=A(WHITE, a), width=int(3 * s))
    d.line([(px + pw / 2, py), (px + pw / 2, py + ph)], fill=A(WHITE, a), width=int(3 * s))
    d.ellipse((px + pw / 2 - 30 * s * sc, py + ph / 2 - 30 * s * sc, px + pw / 2 + 30 * s * sc, py + ph / 2 + 30 * s * sc), outline=A(WHITE, a), width=int(3 * s))
    d.text((px + pw / 2, py - 40 * s * sc), "FUTBOL SAHASI", font=font(FA, 36 * s * sc), fill=A(WHITE, a), anchor="mm")
    d.text((px + pw / 2, py + ph + 40 * s * sc), "7.140 m²", font=font(FA, 40 * s * sc), fill=A((180, 230, 180), a), anchor="mm")
    # türbe arazisi (~8.797 m², aynı ölçek)
    side = math.sqrt(8797 / 7140 * pw * ph) * pw / pw
    tx, ty = w - 60 * s * sc - side, py + ph / 2 - side / 2
    gp = eout(prog(t, t0 + .8, .6))
    d.rectangle((tx, ty, tx + side, ty + side), fill=A((227, 10, 23), a * .75 * gp), outline=A(WHITE, a * gp), width=int(4 * s))
    d.text((tx + side / 2, py - 40 * s * sc), "TÜRBE ARAZİSİ", font=font(FA, 36 * s * sc), fill=A(WHITE, a * gp), anchor="mm")
    d.text((tx + side / 2, py + ph + 40 * s * sc), "≈ 8.800 m²", font=font(FA, 40 * s * sc), fill=A((255, 170, 170), a * gp), anchor="mm")
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))
def magnifier(img, t, t0, a):
    """Eşme: türbe ile sınır arası 200 m – şematik büyüteç"""
    if a <= .01: return
    sc = back(prog(t, t0, .45)); r = int(250 * SS * sc)
    if r < 10: return
    lay = Image.new("RGBA", (2 * r + 40, 2 * r + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); c = r + 20
    inner = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); di = ImageDraw.Draw(inner)
    di.rectangle((0, 0, 2 * r, r * .62), fill=(214, 190, 150, 255))          # Türkiye (üst)
    di.rectangle((0, r * .62, 2 * r, 2 * r), fill=(196, 176, 140, 255))      # Suriye (alt)
    for k in range(0, 2 * r, int(22 * SS * sc)):
        di.line([(k, r * .62 - 4), (k + 12 * SS * sc, r * .62 - 4)], fill=(150, 30, 30, 255), width=int(5 * SS * sc))
    di.text((r, r * .30), "TÜRKİYE", font=font(FA, 46 * SS * sc), fill=(120, 20, 20, 255), anchor="mm")
    di.text((r, r * 1.75), "SURİYE", font=font(FA, 40 * SS * sc), fill=(90, 80, 60, 255), anchor="mm")
    tomb(di, r * .75, r * 1.42, .9 * sc, 1)
    pm = eout(prog(t, t0 + .8, .6))
    ax, y0, y1 = r * 1.25, r * 1.40, r * .66
    if pm > 0:
        R.arrow(di, (ax, (y0 + y1) / 2), (ax, (y0 + y1) / 2 - (y0 - y1) / 2 * pm), (20, 20, 20, 255), int(6 * SS * sc))
        R.arrow(di, (ax, (y0 + y1) / 2), (ax, (y0 + y1) / 2 + (y0 - y1) / 2 * pm), (20, 20, 20, 255), int(6 * SS * sc))
    m = Image.new("L", inner.size, 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=int(255 * a)); inner.putalpha(m)
    d.ellipse((c - r + 8, c - r + 16, c + r + 8, c + r + 16), fill=(0, 0, 0, int(110 * a)))
    lay.alpha_composite(inner, (20, 20))
    d.ellipse((c - r, c - r, c + r, c + r), outline=A(WHITE, a), width=int(12 * SS * sc))
    x, y = W * .72, 640 * SS
    img.alpha_composite(lay, (int(x - c), int(y - c)))
    if pm > .5: ytag(img, x + r * 0.25 + 60 * SS, y - 20 * SS, "200 M", a, sc, 52)

def header(img, t):
    a = vis(t, .15, en("name") + .1, .3, .4)
    if a <= 0: return
    sc = .9 + .1 * back(prog(t, .15, .35))
    lay = Image.new("RGBA", (W, 260 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 860 * SS * sc, 180 * SS * sc; x0, y0 = W / 2 - w / 2, 130 * SS - h / 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(36 * SS), fill=(0, 0, 0, 210), outline=A(C_TR, 1), width=4 * SS)
    d.text((W / 2, y0 + h * .31), "TÜRKİYE'NİN", font=font(FA, 64 * SS * sc), fill=WHITE, anchor="mm")
    d.text((W / 2, y0 + h * .71), "SINIR DIŞINDAKİ TOPRAĞI", font=font(FA, 70 * SS * sc), fill=(255, 80, 80), anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, 150 * SS))

# ---------- kare ----------
def frame(t):
    if t < T_GLOBE:
        p = ease(t / T_GLOBE)
        lon, lat = lerp(5, 36, p), lerp(25, 38, p)
        Rpx = math.exp(lerp(math.log(420), math.log(2000), ease(p ** 1.3)))
        img = globe(lon, lat, Rpx, t).resize((W, H), Image.BICUBIC).convert("RGBA")
        if t > T_GLOBE - .45:
            b, _ = base_mix(cam_at(T_GLOBE - .3), t)
            img = Image.blend(img, b, clamp01((t - (T_GLOBE - .45)) / .45))
        cam = None
    else:
        cam = cam_at(t); img, g = base_mix(cam, t); fp = footprint(g)
        overlays(img, cam, fp, t)
        img = zoom_blur(img, t)
    # gece modu (operasyon)
    night = vis(t, st("siege") + .5, en("rescue") + .2, .8, .8)
    if night > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 16, 44, int(150 * night))))
        if cam is not None: night_lights(img, cam, t, night)
    ui(img, cam, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * (.14 + .35 * night))))
    R2.caption(img, t)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def dense(path, n=14):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        for k in range(n): out.append((lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
    out.append(path[-1]); return out
DIN, DOUT = dense(ROUTE_IN), dense(ROUTE_OUT)

def convoy(img, cam, t, path, t0, dur, a, face=1, light=True, n=5):
    lay = L(); d = ImageDraw.Draw(lay)
    pts = ring_pts(cam, path)
    p = eout(prog(t, t0, dur))
    if len(pts) > 1:
        R.dashed(d, partial(pts, p), A((255, 230, 150), a), 5 * SS, 16, 12)
    for k in range(n):
        pk = clamp01(p - k * 0.05)
        if pk <= 0: continue
        ll = partial(path, pk)[-1]; q = pj(cam, *ll)
        if q: tank(d, q[0], q[1], 330000 / max(q[2], 90000) * (1 - k * .05), a, light, face)
    img.alpha_composite(lay)

def night_lights(img, cam, t, a):
    # Kobani ve sınır boyunca hafif ışıklar
    lay = L(); d = ImageDraw.Draw(lay); rnd = random.Random(4)
    for k in range(40):
        lon, lat = 38.0 + rnd.random() * .7, 36.83 + rnd.random() * .25
        q = pj(cam, lon, lat)
        if q:
            r = (3 + 2 * rnd.random()) * SS; fl = .6 + .4 * math.sin(t * 3 + k)
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=(255, 220, 140, int(160 * a * fl)))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))

def overlays(img, cam, fp, t):
    pul = .5 + .5 * math.sin(t * 5)
    # Türkiye: neon parıltılı, yükseltilmiş
    a_tr = vis(t, T_GLOBE, st("who") - .2, .5, .5) + vis(t, st("today"), TOTAL, .6, .3)
    a_tr = min(1, a_tr)
    glow_outline(img, cam, TR, (255, 90, 90), a_tr * .8, fp, 5)
    fa_tr = .70 if t < st("today") else .40
    raised(img, cam, TR, C_TR, a_tr, fp, lift=8 if t < st("today") else 4, simplify=0.02, fill_a=fa_tr)
    a_sy = vis(t, T_GLOBE + .3, st("who") - .2, .5, .5)
    raised(img, cam, SY, C_SY, a_sy * .9, fp, lift=4, simplify=0.02, fill_a=.35)
    # Fırat nehri
    a_r = vis(t, st("river") - .2, en("y1973") + .3, .4, .5)
    if a_r > 0:
        pts = ring_pts(cam, dense(FIRAT, 8))
        lay = L(); d = ImageDraw.Draw(lay)
        pr = eout(prog(t, st("river") - .2, 1.6))
        if len(pts) > 1:
            d.line(partial(pts, pr), fill=A((40, 120, 230), a_r * .5), width=22 * SS, joint="curve")
            d.line(partial(pts, pr), fill=A((90, 170, 255), a_r), width=8 * SS, joint="curve")
        img.alpha_composite(lay)
        lab(img, cam, "FIRAT", 38.62, 36.3, 54, a_r, (140, 200, 255), rot=-70)
    # baraj gölü yükselir
    a_l = vis(t, st("y1973") + .3, en("size") + .3, .4, .5)
    if a_l > 0:
        g = eout(prog(t, st("y1973") + .4, 2.0))
        c = LAKE.centroid
        from shapely import affinity
        lk = affinity.scale(LAKE, xfact=max(.05, g), yfact=max(.05, g), origin=c)
        glow_outline(img, cam, lk, (120, 200, 255), a_l, fp, 4)
        fill_geom(img, cam, lk, (40, 120, 220), .85 * a_l, fp, simplify=0.001)
        if g > .6: lab(img, cam, "BARAJ GÖLÜ", 38.4, 35.80, 46, a_l, (170, 220, 255))
    # türbe ikonu (konum: Caber -> Karakozak -> Eşme)
    if st("y1973") + 1.4 < t < en("rescue") + .5 or t < st("y1973") + 1.4:
        if t < st("y1973") + 1.4: loc = CABER
        elif t < st("y1973") + 3.2:
            u = ease(prog(t, st("y1973") + 1.4, 1.8)); loc = (lerp(CABER[0], KARAKOZAK[0], u), lerp(CABER[1], KARAKOZAK[1], u))
        else: loc = KARAKOZAK
    else:
        loc = ESME if t > st("today") - .2 else KARAKOZAK
    if t > en("rescue") - 1.2 and t < st("today"):
        u = ease(prog(t, en("rescue") - 1.2, 1.4)); loc = (lerp(KARAKOZAK[0], ESME[0], u), lerp(KARAKOZAK[1], ESME[1], u))
    a_t = vis(t, st("name") + .1, TOTAL - .3, .4, .3) * (1 - vis(t, st("cta") + .4, TOTAL, .4, .1))
    q = pj(cam, *loc)
    if q and a_t > 0:
        lay = L(); tomb(ImageDraw.Draw(lay), q[0], q[1] - 6 * SS, 1.1 * back(prog(t, st("name") + .1, .45)), a_t); img.alpha_composite(lay)
        # bayrak
        a_f = vis(t, st("flag") + .1, TOTAL, .3, .3)
        if a_f > 0:
            flag_pole(img, q[0] + 70 * SS, q[1] + 10 * SS, 1.0, a_t * a_f, t, eout(prog(t, st("flag") + .1, 1.0)))
            if st("flag") < t < en("flag") + .3:
                lay = L(); d = ImageDraw.Draw(lay)
                for k in range(3): soldier(d, q[0] - 110 * SS + k * 40 * SS, q[1] + 20 * SS, 1.4, vis(t, st("flag") + .3 + k * .2, en("flag") + .3, .3, .3))
                img.alpha_composite(lay)
    # 1973: kuzeye taşıma oku
    a_m = vis(t, st("y1973") + 1.2, en("y1973") + .3, .3, .3)
    if a_m > 0:
        p0, p1 = pj(cam, *CABER), pj(cam, *KARAKOZAK)
        if p0 and p1: curved_arrow(img, (p0[0], p0[1]), (p1[0], p1[1] + 40 * SS), a_m, .25, eout(prog(t, st("y1973") + 1.2, 1.6)))
    # kuşatma
    a_s = vis(t, st("siege") + .2, st("operation") + 1.0, .4, .5)
    if a_s > 0 and q:
        lay = L(); d = ImageDraw.Draw(lay)
        close = eout(prog(t, st("siege") + .4, 3.5))
        for k in range(3):
            rr = (520 - 220 * close + k * 60) * SS * (1 + .03 * math.sin(t * 6 + k))
            d.ellipse((q[0] - rr, q[1] - rr * .62, q[0] + rr, q[1] + rr * .62), outline=A((255, 50, 50), a_s * (.9 - k * .25)), width=6 * SS)
        for k in range(10):
            an = k / 10 * 6.283 + .3; rr = (640 - 260 * close) * SS
            sx, sy = q[0] + math.cos(an) * rr, q[1] + math.sin(an) * rr * .62
            R.arrow(d, (sx, sy), (sx - math.cos(an) * 90 * SS, sy - math.sin(an) * 56 * SS), A((255, 60, 60), a_s), 8 * SS)
        for k in range(12):
            soldier(d, q[0] - 150 * SS + (k % 6) * 60 * SS, q[1] + 70 * SS + (k // 6) * 60 * SS, 1.3, a_s * vis(t, st("siege") + 1.0 + k * .05, 99, .2, .1))
        img.alpha_composite(lay)
    # operasyon konvoyu
    a_o = vis(t, st("operation") + .8, en("rescue") + .2, .4, .4)
    if a_o > 0:
        convoy(img, cam, t, DIN, st("operation") + 1.0, en("operation") - st("operation") - 1.0, a_o, face=-1)
        if t > st("rescue") - .2:
            convoy(img, cam, t, DOUT, st("rescue"), en("rescue") - st("rescue"), a_o, face=1, n=3)
        # sınır çizgisi vurgusu
        bl = TR.boundary.intersection(SY.boundary).intersection(box(37.6, 36.6, 38.9, 37.1))
        if not bl.is_empty:
            lay = L(); d = ImageDraw.Draw(lay)
            for ln in (list(bl.geoms) if hasattr(bl, "geoms") else [bl]):
                if ln.geom_type == "LineString":
                    pts = ring_pts(cam, list(ln.coords))
                    if len(pts) > 1: d.line(pts, fill=A((255, 80, 80), a_o * (.6 + .4 * pul)), width=6 * SS)
            img.alpha_composite(lay)
    # bayrak iğneleri
    qk = pj(cam, *KOBANI)
    a_tag = vis(t, st("operation") + .8, en("operation"), .3, .3)
    if qk: tag(img, qk[0] + 160 * SS, qk[1] - 120 * SS, "TÜRKİYE SINIRI", a_tag, back(prog(t, st("operation") + .8, .4)), size=44)
    q1 = pj(cam, 37.2, 38.6); a_p = vis(t, T_GLOBE + .2, st("name") - .2, .3, .3)
    if q1: flag_pin(img, q1[0], q1[1], "turkey", a_p, back(prog(t, T_GLOBE + .2, .4)))
    # etiketler
    a_n = vis(t, T_GLOBE + .2, st("name") - .1, .3, .3)
    lab(img, cam, "TÜRKİYE", 35.5, 38.9, 76, a_n, WHITE)
    lab(img, cam, "SURİYE", 38.4, 35.2, 64, a_n, (240, 230, 200))
    q2 = pj(cam, *ESME)
    if q2: ytag(img, q2[0], q2[1] + 90 * SS, "EŞME", vis(t, st("today") + .4, st("cta"), .3, .3), back(prog(t, st("today") + .4, .35)), 46)
    q3 = pj(cam, *CABER)
    if q3: ytag(img, q3[0] + 170 * SS, q3[1] + 40 * SS, "CABER KALESİ", vis(t, st("y1921") + .3, en("flag"), .3, .3), back(prog(t, st("y1921") + .3, .35)), 40)
    q4 = pj(cam, *KARAKOZAK)
    if q4: ytag(img, q4[0] + 180 * SS, q4[1] + 30 * SS, "KARAKOZAK", vis(t, st("y1973") + 2.8, en("size"), .3, .3), back(prog(t, st("y1973") + 2.8, .35)), 40)

def ui(img, cam, t):
    header(img, t)
    q = pj(cam, *ESME) if cam is not None else None
    if q: tag(img, W / 2, 560 * SS, "SÜLEYMAN ŞAH TÜRBESİ", vis(t, st("name") + .2, en("name") + .4, .3, .3), back(prog(t, st("name") + .2, .4)), size=60)
    family_tree(img, t, st("who") + .3, vis(t, st("who") + .2, en("who") + .2, .3, .3))
    a = vis(t, st("y1921") + .2, en("y1921") + .2, .3, .3)
    if a > 0:
        stamp_text(img, "1921", (W / 2, 520 * SS), FA, 150, fill=YEL, alpha=a, scale=back(prog(t, st("y1921") + .2, .4)))
        flag_card(img, "turkey", W * .30, 1110 * SS, 190, a, back(prog(t, st("y1921") + .8, .4)))
        flag_card(img, "france", W * .70, 1110 * SS, 190, a, back(prog(t, st("y1921") + 1.0, .4)))
        scroll_card(img, W / 2, 1290 * SS, a, back(prog(t, st("y1921") + 1.6, .4)))
    a = vis(t, st("y1973") + .2, en("y1973") + .1, .3, .3)
    if a > 0: stamp_text(img, "1973", (W / 2, 520 * SS), FA, 150, fill=YEL, alpha=a, scale=back(prog(t, st("y1973") + .2, .4)))
    pitch_card(img, t, st("size") + .2, vis(t, st("size") + .2, en("size") + .3, .3, .3))
    a = vis(t, st("siege") + 1.2, en("siege") + .2, .3, .3)
    ytag(img, W / 2, 560 * SS, "≈ 40 ASKER", a, back(prog(t, st("siege") + 1.2, .35)), 64)
    a = vis(t, st("operation") + .2, en("operation") + .1, .3, .3)
    if a > 0:
        ytag(img, W / 2, 470 * SS, "21 ŞUBAT 2015", a, back(prog(t, st("operation") + .2, .35)), 62)
        ytag(img, W * .30, 600 * SS, "≈ 600 ASKER", a, back(prog(t, st("operation") + 2.2, .35)), 46, bg=WHITE)
        ytag(img, W * .70, 600 * SS, "≈ 100 ZIRHLI ARAÇ", a, back(prog(t, st("operation") + 3.0, .35)), 46, bg=WHITE)
    magnifier(img, t, st("today") + 1.2, vis(t, st("today") + 1.2, en("today") + .3, .3, .3))
    a = vis(t, st("cta") + .3, TOTAL, .3, .3)
    if a > 0:
        lay = Image.new("RGBA", (W, 420 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        sc = back(prog(t, st("cta") + .3, .4))
        for i, (tx, col) in enumerate((("SENCE ESKİ YERİNE", WHITE), ("DÖNEBİLİR Mİ?", YEL))):
            d.text((W / 2, (110 + i * 120) * SS), tx, font=font(FA, int(108 * SS * sc)), fill=A(col, a), anchor="mm", stroke_width=8 * SS, stroke_fill=(0, 0, 0, int(230 * a)))
        img.alpha_composite(lay, (0, 260 * SS))
        pill(img, "YORUMLARA YAZ!", W / 2, 760 * SS, 60, alpha=vis(t, st("cta") + 1.0, TOTAL, .25, .3), scale=back(prog(t, st("cta") + 1.0, .35)))

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s6_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
