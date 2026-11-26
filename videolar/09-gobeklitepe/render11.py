"""Video 9: Göbeklitepe – piramitlerden 7.000 yıl önce dikilen dev taşlar. Haritanın Ardı teknikleri: renk=anlam altyazı, canlı sayaç, "?" simgesi,
Türkiye'yi beyazlatma, odak dışını karartma, daktilo etiket, ~1 sn'de bir görsel olay. Zoom blur YOK, yumuşak süzülme."""
import json, math, os, random, re, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, Point
from shapely.ops import nearest_points
import render as R
from render import stamp_text, pill, partial, prog, FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys, tr_up
from render3 import A, L, RED, WHITE, YEL, BLACK, VIG, clamp01
from render4 import globe, sample, EARTH, fractal, Cam, persp_coeffs
import brand

# Koruma: yeni Pillow ters koordinatlı dikdörtgende hata veriyor → koordinatları sırala
from PIL import ImageDraw as _ID
if not getattr(_ID.ImageDraw, "_safe_rect", False):
    _orig_rect = _ID.ImageDraw.rectangle
    def _rect(self, xy, *a, **k):
        try:
            (x0, y0), (x1, y1) = (xy[0], xy[1]) if len(xy) == 2 else ((xy[0], xy[1]), (xy[2], xy[3]))
            xy = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        except Exception: pass
        return _orig_rect(self, xy, *a, **k)
    _ID.ImageDraw.rectangle = _rect; _ID.ImageDraw._safe_rect = True


LEAD = 0.05
FC, FP = "caveat.ttf", "playfair.ttf"
BLUE = (37, 99, 235); TURQ = (40, 205, 215); RIVER = (80, 170, 255); PINK = (240, 110, 190)
ORANGE = (255, 150, 40); GREEN = (110, 220, 130); KRED = (229, 36, 59)
LON0, LAT0D = 38.9, 37.2
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
BB = box(18, 27, 54, 51)
CN = {}
for f in json.load(open("countries50.json"))["features"]:
    g = shape(f["geometry"]).buffer(0)
    if g.intersects(BB): CN[f["properties"].get("name") or f["properties"].get("NAME")] = g.intersection(BB)
CN["Turkey"] = shape([f for f in json.load(open("countries10_tr.json"))["features"] if f["properties"]["name"] == "Turkey"][0]["geometry"]).buffer(0)
VAN = shape(json.load(open("van.json"))["geometry"]).buffer(0)
VC = VAN.centroid; VCX, VCY = VC.x, VC.y

# ---------- yumuşak zamanlama ----------
def smooth(x): x = clamp01(x); return x * x * x * (x * (6 * x - 15) + 10)
def sine_out(x): x = clamp01(x); return math.sin(x * math.pi / 2)
def vis(t, t0, t1, fi=.45, fo=.45):
    if t < t0 or t > t1 + fo: return 0.
    return min(sine_out((t - t0) / fi), 1 - smooth((t - t1) / fo))
def rise(t, t0, d=.5): return (1 - sine_out((t - t0) / d)) * 40 * SS
def pop(t, t0, d=.35):
    x = clamp01((t - t0) / d); c1 = 1.70158; c3 = c1 + 1
    return 0 if x <= 0 else 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
WORDS = json.load(open("words.json"))
def _n(w): return re.sub(r"[^\wçğıöşü]", "", w.replace("İ", "i").replace("I", "ı").lower())
def cue(scene, *needles, offset=0.0):
    t0, t1 = st(scene) - .3, en(scene) + .3
    for w in WORDS:
        tw = w["s"] + LEAD
        if t0 <= tw <= t1 and any(_n(nd) in _n(w["w"]) for nd in needles): return tw + offset
    return st(scene) + offset

exec(open("maplib_src.py").read())
def lake_paint(img, lon0, lon1, lat0, lat1):
    """dokuya gölleri boya (uydu dokusu gölü bulanık gösteriyor)"""
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1); mpp = (x1 - x0) / img.width
    def tp(lon, lat): x, y = ll2m(lon, lat); return ((x - x0) / mpp, (y1 - y) / mpp)
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).polygon([tp(*c) for c in VAN.exterior.coords], fill=255)
    edge = Image.fromarray(np.clip(np.asarray(m, np.float32) - np.asarray(m.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(10)), np.float32), 0, 255).astype(np.uint8))
    img = img.copy(); img.paste((28, 92, 140), (0, 0), m); img.paste((70, 160, 180), (0, 0), edge.point(lambda v: int(v * .8)))
    return img
def relief_tex(bounds, npx, seed, z, name, exag):
    """uydu rengi + AWS yükseklik verisinden rölyef gölgesi (bulanık uydu dokusuna keskin dağlar)"""
    f = name + "_r.png"
    if os.path.exists(f): return Image.open(f).convert("RGB")
    import dem as DM
    base = build_tex(*bounds, npx, seed, name + ".png")
    d = DM.DEM(*bounds, z, "../geo/dem")
    img, _ = DM.relief(base, d, *bounds, ll2m, exag=exag)
    img.save(f); return img
TEX_BIG = lake_paint(relief_tex((20, 52, 29, 49), 4096, 3, 7, "t7_big2", 3.0), 20, 52, 29, 49)
TEX_DET = relief_tex((37.6, 40.2, 36.2, 38.3), 4096, 7, 10, "t9_urfa", 1.6)
TB = tex_info(20, 52, 29, 49, TEX_BIG); TD = tex_info(37.6, 40.2, 36.2, 38.3, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
K = [(0.0, 35.5, 39.0, 2500, 0, 0), (cue("intro", "şanlıurfada", "şanlıurfa") - .3, 35.8, 38.9, 2400, 0, 0),
     (en("intro") - .1, 38.92, 37.20, 140, 30, 0), (en("question"), 38.92, 37.19, 110, 36, 0),
     (st("site"), 38.92, 37.19, 100, 38, 0), (st("cta"), 38.92, 37.20, 160, 26, 0), (TOTAL, 38.92, 37.21, 200, 22, 0)]
def cam_at(t):
    if t <= K[0][0]: a = b = K[0]; p = 0
    elif t >= K[-1][0]: a = b = K[-1]; p = 0
    else:
        for a, b in zip(K[:-1], K[1:]):
            if a[0] <= t <= b[0]: p = smooth((t - a[0]) / max(.01, b[0] - a[0])); break
    lon, lat = lerp(a[1], b[1], p), lerp(a[2], b[2], p)
    D = math.exp(lerp(math.log(a[3]), math.log(b[3]), p)) * 1000
    x, y = ll2m(lon, lat)
    return Cam(x, y, D, math.radians(lerp(a[4], b[4], p)), math.radians(lerp(a[5], b[5], p) + 1.0 * math.sin(t * .18)))

# ---------- metin yardımcıları ----------
def hand(img, text, x, y, size, a, col=WHITE, rot=-6):
    if a <= .01: return
    f = font(FC, size * SS); l, t_, r, b = f.getbbox(text, stroke_width=4 * SS)
    lay = Image.new("RGBA", (r - l + 40, b - t_ + 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20 - l, 20 - t_), text, font=f, fill=A(col, a), stroke_width=int(4 * SS), stroke_fill=(0, 0, 0, int(200 * a)))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def big(img, text, x, y, size, a, col=YEL, sc=1.):
    if a > .01: stamp_text(img, text, (x, y), FA, size, fill=col, stroke=BLACK, alpha=a, scale=sc)
def ytag(img, x, y, text, a, size=44, bg=YEL, fg=BLACK, sc=1.):
    if a <= .01 or sc <= .01: return
    f = font(FA, size * SS * sc); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 30 * SS * sc, b - t_ + 22 * SS * sc
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((14, 14, w + 14, h + 14), fill=(0, 0, 0, int(100 * a))); d.rectangle((8, 8, w + 8, h + 8), fill=A(bg, a))
    d.text((8 + w / 2, 8 + h / 2), text, font=f, fill=A(fg, a), anchor="mm")
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def typetag(img, x, y, text, t, t0, a, size=50, bg=ORANGE, fg=WHITE):
    """daktilo etiket: harf harf yazılır"""
    n = int(clamp01((t - t0) / (.06 * len(text))) * len(text) + .999)
    if n > 0: ytag(img, x, y, text[:n], a, size, bg, fg)
def trnum(v): return f"{int(round(v)):,}".replace(",", ".")

# renk = anlam (Haritanın Ardı): kelime → haritadaki rengi
ENT = {}
for k in ("şanlıurfada", "şanlıurfa"): ENT[k] = ORANGE
for k in ("göbeklitepe", "taşlar", "taşları", "dikilitaşlar", "dikilitaş", "tapınak"): ENT[k] = (255, 200, 80)
for k in ("yazısı", "tekerleği", "tarlası"): ENT[k] = KRED
for k in ("tarım",): ENT[k] = (110, 210, 110)
for k in ("tilki", "yaban", "domuzu", "akrep", "akbaba"): ENT[k] = ORANGE
for k in ("piramitlerden",): ENT[k] = WHITE
def caption_top(img, t):
    c = next((c for c in R.CAPS if c["start"] <= t < c["end"]), None)
    if not c: return
    size = 48 * SS; f = font(F9, size); sp = f.getlength(" ")
    words = [tr_up(w) for w in c["words"]]
    cur = max(i for i, wt in enumerate(c["wt"]) if wt <= t)
    ws = [f.getlength(w) for w in words]; tw = sum(ws) + sp * (len(words) - 1)
    if tw > W * .9:
        size *= W * .9 / tw; f = font(F9, size); sp = f.getlength(" "); ws = [f.getlength(w) for w in words]; tw = sum(ws) + sp * (len(words) - 1)
    a = sine_out((t - c["start"]) / .15)
    lay = Image.new("RGBA", (W, int(size * 2.2)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x = W / 2 - tw / 2; y = size * 1.1
    for i, w in enumerate(words):
        ec = ENT.get(_n(c["words"][i]).replace("²", "²"))
        if ec is None and re.sub(r"[^\d]", "", c["words"][i]): ec = YEL
        if i == cur:
            bg = ec or BLUE; fg = BLACK if sum(bg) > 500 else WHITE
            d.rounded_rectangle((x - 12 * SS, y - size * .62, x + ws[i] + 12 * SS, y + size * .58), radius=int(10 * SS), fill=bg + (255,))
            d.text((x, y), w, font=f, fill=fg, anchor="lm")
        else:
            d.text((x, y), w, font=f, fill=(ec or WHITE), anchor="lm", stroke_width=int(size / 9), stroke_fill=(0, 0, 0, 220))
        x += ws[i] + sp
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, int(330 * SS - size * 1.1)))

# ---------- çizim yardımcıları ----------
def fish(d, x, y, s, a, col=(205, 215, 225), fin=ORANGE, flip=False, rot=0.0):
    """inci kefali: gümüş gövde, turuncu yüzgeç"""
    s *= SS; m = -1 if flip else 1; cr, sr = math.cos(rot), math.sin(rot)
    T = lambda px, py: (x + (m * px * cr - py * sr) * s, y + (m * px * sr + py * cr) * s)
    body = [T(60 * math.cos(u), 22 * math.sin(u)) for u in np.linspace(0, 2 * math.pi, 28)]
    d.polygon([T(-52, 0), T(-86, -26), T(-80, 0), T(-86, 26)], fill=A(fin, a))
    d.polygon([T(-5, -18), T(15, -36), T(25, -18)], fill=A(fin, a))
    d.polygon(body, fill=A(col, a), outline=A((60, 70, 80), a))
    d.line([T(-40, 2), T(50, 2)], fill=A((150, 160, 175), a), width=max(1, int(3 * s / SS)))
    ex_, ey_ = T(42, -4); er = 4.5 * s
    d.ellipse((ex_ - er, ey_ - er, ex_ + er, ey_ + er), fill=A((20, 20, 24), a))
def xmark(d, x, y, r, a, col=KRED, w=14):
    for s in (1, -1): d.line([(x - r, y - r * s), (x + r, y + r * s)], fill=A(col, a), width=int(w * SS))
def qmark(img, x, y, size, a, t):
    if a <= .01: return
    bob = math.sin(t * 5) * 8 * SS
    stamp_text(img, "?", (x, y + bob), FA, size, fill=WHITE, stroke=BLACK, alpha=a, scale=pop(t, 0) if False else 1)
# ---------- Göbeklitepe ----------
GT = (38.922, 37.223)
STONE = (214, 194, 158); STONE_D = (150, 128, 96); RELIEF = (240, 226, 196); GOLD2 = (255, 200, 80)
def pinmark(img, cam, lon, lat, a, col=KRED):
    q = pj(cam, lon, lat)
    if not q or a <= .01: return None
    lay = L(); d = ImageDraw.Draw(lay); x, y = q[0], q[1] - (1 - sine_out(a)) * 40 * SS; r = 24 * SS
    d.polygon([(x - r * .8, y - r * 1.6), (x + r * .8, y - r * 1.6), (x, y)], fill=A(col, a))
    d.ellipse((x - r, y - r * 2.6, x + r, y - r * .6), fill=A(col, a), outline=A(WHITE, a), width=4 * SS)
    d.ellipse((x - r * .38, y - r * 1.98, x + r * .38, y - r * 1.22), fill=A(WHITE, a))
    img.alpha_composite(lay); return (x, y)
def swap_cards(img, t, t0, t_sw, a):
    if a <= .01: return
    p = smooth((t - t_sw) / .9) if t > t_sw else 0
    for k, (txt, col) in enumerate((("TARIM", (90, 190, 90)), ("TAPINAK", GOLD2))):
        x0, x1 = (W * .27, W * .73) if k == 0 else (W * .73, W * .27)
        x = lerp(x0, x1, p); y = 1150 * SS - math.sin(p * math.pi) * (180 if k == 0 else -180) * SS
        ytag(img, x, y, txt, a * sine_out((t - t0 - k * .25) / .3), 80, bg=col, fg=BLACK if k else WHITE, sc=pop(t, t0 + k * .25))
    if t > t0 + .5:
        lay = L(); d = ImageDraw.Draw(lay); aa = a * (1 - math.sin(p * math.pi)) * sine_out((t - t0 - .5) / .3)
        d.line([(W * .43, 1150 * SS), (W * .57, 1150 * SS)], fill=A(WHITE, aa), width=12 * SS)
        d.polygon([(W * .58, 1150 * SS), (W * .55, 1125 * SS), (W * .55, 1175 * SS)], fill=A(WHITE, aa)); img.alpha_composite(lay)
def icon(d, kind, x, y, s, a):
    s *= SS; c = A(WHITE, a); o = A(BLACK, a)
    if kind == "scroll":
        d.rectangle((x - 60 * s, y - 75 * s, x + 60 * s, y + 75 * s), fill=A((240, 225, 190), a), outline=o, width=int(4 * s))
        for k in range(5): d.line([(x - 40 * s, y - 45 * s + k * 22 * s), (x + 40 * s, y - 45 * s + k * 22 * s)], fill=A((120, 100, 70), a), width=int(5 * s))
        for yy in (-75, 75): d.ellipse((x - 70 * s, y + yy * s - 12 * s, x + 70 * s, y + yy * s + 12 * s), fill=A((220, 200, 160), a), outline=o, width=int(3 * s))
    elif kind == "wheel":
        d.ellipse((x - 75 * s, y - 75 * s, x + 75 * s, y + 75 * s), outline=A((200, 150, 90), a), width=int(16 * s))
        for k in range(8):
            an = k * math.pi / 4; d.line([(x, y), (x + 68 * s * math.cos(an), y + 68 * s * math.sin(an))], fill=A((200, 150, 90), a), width=int(8 * s))
        d.ellipse((x - 16 * s, y - 16 * s, x + 16 * s, y + 16 * s), fill=A((150, 100, 50), a))
    elif kind == "wheat":
        d.line([(x, y + 85 * s), (x, y - 70 * s)], fill=A((220, 180, 70), a), width=int(8 * s))
        for k in range(5):
            yy = y - 60 * s + k * 26 * s
            for sg in (-1, 1): d.ellipse((x + sg * 8 * s - 14 * s, yy - 20 * s, x + sg * 8 * s + 14 * s, yy + 6 * s), fill=A((240, 200, 80), a))
def xmark(d, x, y, r, a, col=KRED, w=14):
    for s in (1, -1): d.line([(x - r, y - r * s), (x + r, y + r * s)], fill=A(col, a), width=int(w * SS))
# --- illüstrasyon sahnesi ---
GROUND = 1500 * SS
PXM = 900 * SS / 5.5
PX = W * .42
SHAFT_W, TOP_W, TOP_H = 1.25 * PXM, 2.5 * PXM, 1.1 * PXM
def sky(d, h, c0=(40, 50, 95), c1=(250, 160, 90)):
    for yy in range(0, int(h), 8):
        u = yy / max(1, h); d.rectangle((0, yy, W, yy + 8), fill=tuple(int(lerp(p, q, u)) for p, q in zip(c0, c1)) + (255,))
def t_pillar(d, x, ground, hm, a, grow=1.0, scale=1.0):
    pxm = PXM * scale; h = hm * pxm * grow
    sw, tw, th = SHAFT_W * scale, TOP_W * scale, TOP_H * scale
    top = ground - h
    if top + th >= ground: return   # taş henüz yerden çıkmadı (yükselme animasyonunun ilk anı)
    d.rectangle((x - sw / 2, top + th * .9, x + sw / 2, ground), fill=A(STONE, a), outline=A(STONE_D, a), width=max(2, int(4 * SS * scale)))
    d.rectangle((x - tw / 2, top, x + tw / 2, top + th), fill=A(STONE, a), outline=A(STONE_D, a), width=max(2, int(4 * SS * scale)))
    d.rectangle((x + sw / 2 - 6, top + th, x + sw / 2, ground), fill=A(STONE_D, a * .6))
def relief(d, kind, x, y, s, a):
    s *= SS; c = A(RELIEF, a); o = A(STONE_D, a); w = max(2, int(3 * s))
    if kind == "fox":
        d.ellipse((x - 60 * s, y - 22 * s, x + 40 * s, y + 22 * s), fill=c, outline=o, width=w)
        d.polygon([(x + 30 * s, y - 20 * s), (x + 80 * s, y - 5 * s), (x + 35 * s, y + 15 * s)], fill=c, outline=o)
        d.polygon([(x + 38 * s, y - 18 * s), (x + 44 * s, y - 44 * s), (x + 54 * s, y - 14 * s)], fill=c, outline=o)
        d.polygon([(x - 55 * s, y - 5 * s), (x - 110 * s, y + 20 * s), (x - 60 * s, y + 15 * s)], fill=c, outline=o)
        for lx in (-40, -20, 10, 25): d.line([(x + lx * s, y + 18 * s), (x + lx * s, y + 50 * s)], fill=o, width=int(6 * s))
    elif kind == "boar":
        d.ellipse((x - 70 * s, y - 35 * s, x + 50 * s, y + 30 * s), fill=c, outline=o, width=w)
        d.polygon([(x + 40 * s, y - 25 * s), (x + 90 * s, y), (x + 40 * s, y + 20 * s)], fill=c, outline=o)
        d.line([(x + 70 * s, y + 5 * s), (x + 85 * s, y - 18 * s)], fill=A(WHITE, a), width=int(5 * s))
        for k in range(6): d.line([(x - 50 * s + k * 16 * s, y - 34 * s), (x - 46 * s + k * 16 * s, y - 50 * s)], fill=o, width=int(4 * s))
        for lx in (-50, -30, 15, 32): d.line([(x + lx * s, y + 25 * s), (x + lx * s, y + 55 * s)], fill=o, width=int(7 * s))
    elif kind == "scorpion":
        for k in range(4): d.ellipse((x - 22 * s, y - 20 * s + k * 22 * s, x + 22 * s, y + 4 * s + k * 22 * s), fill=c, outline=o, width=w)
        pts = [(x + 60 * s * math.sin(u) * (1 - u / 5), y + 70 * s - 80 * s * u / 3.5) for u in np.linspace(0, 3.5, 12)]
        d.line(pts, fill=c, width=int(14 * s), joint="curve"); d.polygon([pts[-1], (pts[-1][0] - 18 * s, pts[-1][1] + 8 * s), (pts[-1][0] - 6 * s, pts[-1][1] - 20 * s)], fill=o)
        for sg in (-1, 1):
            d.line([(x, y - 10 * s), (x + sg * 50 * s, y - 50 * s)], fill=c, width=int(10 * s))
            d.ellipse((x + sg * 50 * s - 16 * s, y - 70 * s, x + sg * 50 * s + 16 * s, y - 40 * s), fill=c, outline=o, width=w)
            for k in range(3): d.line([(x, y + k * 20 * s), (x + sg * 55 * s, y + 10 * s + k * 26 * s)], fill=o, width=int(4 * s))
    elif kind == "vulture":
        d.polygon([(x, y), (x - 110 * s, y - 40 * s), (x - 90 * s, y - 10 * s), (x - 120 * s, y + 5 * s), (x - 30 * s, y + 20 * s), (x, y + 60 * s),
                   (x + 30 * s, y + 20 * s), (x + 120 * s, y + 5 * s), (x + 90 * s, y - 10 * s), (x + 110 * s, y - 40 * s)], fill=c, outline=o)
        d.ellipse((x - 14 * s, y - 34 * s, x + 14 * s, y - 6 * s), fill=c, outline=o, width=w)
def human(d, x, ground, a, scale=1.0):
    h = 1.75 * PXM * scale; c = A((25, 25, 35), a)
    d.ellipse((x - h * .07, ground - h, x + h * .07, ground - h * .86), fill=c)
    d.rounded_rectangle((x - h * .11, ground - h * .85, x + h * .11, ground - h * .45), radius=int(h * .05), fill=c)
    d.rectangle((x - h * .09, ground - h * .46, x - h * .015, ground), fill=c); d.rectangle((x + h * .015, ground - h * .46, x + h * .09, ground), fill=c)
def gt_scene(img, t, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sky(d, GROUND)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sun).ellipse((W * .62, GROUND - 520 * SS, W * .62 + 300 * SS, GROUND - 220 * SS), fill=(255, 210, 140, 200))
    lay.alpha_composite(sun.filter(ImageFilter.GaussianBlur(40))); d = ImageDraw.Draw(lay)
    hill = [(0, GROUND - 60 * SS)] + [(W * u, GROUND - (60 + 180 * math.sin(u * math.pi) ** 1.5) * SS) for u in np.linspace(0, 1, 30)] + [(W, H), (0, H)]
    d.polygon(hill, fill=(120, 92, 62, 255))
    d.rectangle((0, GROUND, W, H), fill=(104, 80, 54, 255))
    rr = random.Random(2)
    for _ in range(140):
        sx, sy = rr.uniform(0, W), rr.uniform(GROUND, H); r_ = rr.uniform(4, 12) * SS
        d.ellipse((sx - r_, sy - r_ * .5, sx + r_, sy + r_ * .5), fill=(84, 64, 44, 255))
    t_site, t_pil = st("site"), cue("pillars", "dikilitaşlar", "ortadaki")
    # uzak çember (site sahnesi): küçük T taşları halka hâlinde yükselir
    a_ring = vis(t, t_site - .3, t_pil + .2, .4, .5)
    if a_ring > 0:
        for k in range(12):
            an = k / 12 * 2 * math.pi; x = W / 2 + math.cos(an) * W * .33; y = GROUND - 120 * SS + math.sin(an) * 110 * SS
            g = smooth((t - t_site - k * .06) / .8)
            if g > 0: t_pillar(d, x, y, 3.5 + (k % 3) * .4, a_ring, g, .28)
        for x in (W * .45, W * .55): t_pillar(d, x, GROUND - 100 * SS, 5.5, a_ring, smooth((t - t_site - .5) / .9), .32)
    # büyük merkez dikilitaş
    a_big = vis(t, t_pil - .2, en("human") + .3, .5, .5)
    if a_big > 0:
        g = smooth((t - t_pil + .2) / 1.0)
        t_pillar(d, PX, GROUND, 5.5, a_big, g)
        human(d, W * .80, GROUND, a_big * sine_out((t - t_pil - .4) / .4))
        for kind, word, xx, yy, s in (("vulture", "akbaba", PX, GROUND - 5.5 * PXM + TOP_H * .5, 1.5), ("fox", "tilki", PX, GROUND - 3.9 * PXM, 1.0),
                                      ("boar", "domuzu", PX, GROUND - 2.6 * PXM, 1.0), ("scorpion", "akrep", PX, GROUND - 1.25 * PXM, .9)):
            tw_ = cue("animals", word)
            if t > tw_ - .05: relief(d, kind, xx, yy, s * pop(t, tw_ - .05), a_big)
        t_arm = cue("human", "kollar", "taşlarda")
        if t > t_arm:
            pa = smooth((t - t_arm) / .8); top = GROUND - 5.5 * PXM + TOP_H
            for sg in (-1, 1):
                x0 = PX + sg * SHAFT_W * .42
                pts = [(x0, top + 40 * SS), (x0, top + (40 + 420 * pa) * SS)]
                d.line(pts, fill=A(STONE_D, a_big), width=14 * SS)
                if pa > .6:
                    yy = top + 460 * SS; d.line([(x0, yy), (PX + sg * 14 * SS, yy + 30 * SS)], fill=A(STONE_D, a_big), width=14 * SS)
                    for f in range(5): d.line([(PX + sg * (14 + f * 10) * SS, yy + 30 * SS), (PX + sg * (14 + f * 10) * SS, yy + 66 * SS)], fill=A(STONE_D, a_big * clamp01((pa - .6) / .4)), width=6 * SS)
            if t > cue("human", "eller") + .2: d.line([(PX - SHAFT_W / 2, top + 560 * SS), (PX + SHAFT_W / 2, top + 560 * SS)], fill=A(STONE_D, a_big), width=10 * SS)
    # kazılan kısım çok küçük: üstten görünüş + 200 dikilitaş
    a_m = vis(t, st("more") - .2, en("more") + .4, .5, .5)
    if a_m > 0:
        top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
        dt.rectangle((0, 0, W, H), fill=(118, 96, 66, int(255 * a_m)))
        dt.ellipse((W * .06, 520 * SS, W * .94, 1640 * SS), fill=(140, 112, 76, int(255 * a_m)), outline=(90, 70, 46, int(255 * a_m)), width=6 * SS)
        ex0, ey0, ex1, ey1 = W * .40, 880 * SS, W * .58, 1060 * SS
        dt.rectangle((ex0, ey0, ex1, ey1), fill=(215, 195, 160, int(255 * a_m)), outline=(255, 255, 255, int(255 * a_m)), width=5 * SS)
        for cx_, cy_ in ((ex0 + 60 * SS, ey0 + 60 * SS), (ex1 - 60 * SS, ey0 + 70 * SS), (ex0 + 90 * SS, ey1 - 50 * SS)):
            for k in range(8):
                an = k / 8 * 2 * math.pi; dt.rectangle((cx_ + math.cos(an) * 34 * SS - 5 * SS, cy_ + math.sin(an) * 34 * SS - 5 * SS, cx_ + math.cos(an) * 34 * SS + 5 * SS, cy_ + math.sin(an) * 34 * SS + 5 * SS), fill=(110, 90, 60, int(255 * a_m)))
        t_200 = cue("more", "200", "iki", "dikilitaş")
        n = int(200 * smooth((t - t_200) / 1.6)) if t > t_200 else 0
        r1 = random.Random(8); dots = []
        for c in range(20):
            while True:
                cx_, cy_ = r1.uniform(W * .14, W * .86), r1.uniform(600 * SS, 1560 * SS)
                if ((cx_ - W / 2) / (W * .40)) ** 2 + ((cy_ - 1080 * SS) / (500 * SS)) ** 2 < 1 and not (ex0 - 80 * SS < cx_ < ex1 + 80 * SS and ey0 - 80 * SS < cy_ < ey1 + 80 * SS): break
            for k in range(10):
                an = k / 10 * 2 * math.pi; dots.append((cx_ + math.cos(an) * 40 * SS, cy_ + math.sin(an) * 40 * SS))
        for x_, y_ in dots[:n]:
            dt.ellipse((x_ - 8 * SS, y_ - 8 * SS, x_ + 8 * SS, y_ + 8 * SS), fill=(255, 210, 90, int(230 * a_m)))
        lay.alpha_composite(top)
        d = ImageDraw.Draw(lay)
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    # metin katmanı
    t_115 = cue("site", "11500", "yaklaşık", "bin")
    ytag(img, W / 2, 620 * SS, f"{trnum(11500 * smooth((t - t_115) / 1.2))} YIL", a * vis(t, t_115, en("site") + .2, .3, .4), 70, sc=pop(t, t_115))
    stamp_text(img, "GÖBEKLİTEPE", (W / 2, 470 * SS + rise(t, st("site"))), FA, 96, fill=GOLD2, stroke=BLACK, alpha=a * vis(t, st("site"), en("site") + .2, .4, .4))
    t_55 = cue("pillars", "55", "beş", "metreye")
    a55 = a * vis(t, t_55 - .1, en("pillars") + .4, .3, .4)
    if a55 > 0:
        g = smooth((t - t_55) / 1.0); xr = PX - TOP_W / 2 - 70 * SS
        lay2 = L(); d2 = ImageDraw.Draw(lay2); ytop = GROUND - 5.5 * PXM * g
        d2.line([(xr, GROUND), (xr, ytop)], fill=A(YEL, a55), width=8 * SS)
        for m in range(0, int(5.5 * g) + 1): d2.line([(xr - 22 * SS, GROUND - m * PXM), (xr, GROUND - m * PXM)], fill=A(YEL, a55), width=5 * SS)
        img.alpha_composite(lay2)
        ytag(img, xr - 10 * SS, ytop - 70 * SS, f"{5.5 * g:.1f} m".replace(".", ","), a55, 56)
    ytag(img, W * .78, 760 * SS, "TONLARCA", a * vis(t, cue("pillars", "tonlarca"), en("pillars") + .3, .3, .4), 60, bg=WHITE, sc=pop(t, cue("pillars", "tonlarca")))
    ytag(img, W * .80, 1560 * SS, "İNSAN 1,75 m", a * vis(t, t_pil + .5, en("pillars") + .3, .3, .4), 36, bg=WHITE)
    hand(img, "dev insan figürü?", W * .72, 760 * SS, 76, a * vis(t, cue("human", "insan", "figürleri"), en("human") + .2, .4, .4), YEL, -6)
    a_o = a * vis(t, st("order") - .1, en("order") + .2, .4, .4)
    if a_o > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 18, int(190 * a_o))))
        swap_cards(img, t, st("order") + .1, cue("order", "tersine", "sırayı"), a_o)
        hand(img, "belki de tersi!", W / 2, 1450 * SS, 86, a_o * vis(t, cue("order", "tersine") + .6, en("order") + .2, .4, .4), YEL, -5)
    if a_m > 0:
        n = int(200 * smooth((t - cue("more", "200", "iki", "dikilitaş")) / 1.6)) if t > cue("more", "200", "iki", "dikilitaş") else 0
        ytag(img, W / 2, 470 * SS, f"{n} DİKİLİTAŞ", a * a_m * vis(t, cue("more", "200", "iki", "dikilitaş"), en("more") + .3, .3, .4), 64)
        ytag(img, W * .49, 1130 * SS, "KAZILAN KISIM", a * a_m * vis(t, cue("more", "kazılan"), en("more") + .3, .3, .4), 40, bg=WHITE)

def overlays(img, cam, fp, t):
    a_tr = vis(t, 0.0, cue("intro", "şanlıurfada", "şanlıurfa") + .2, .25, .6)
    if a_tr > 0: fill_geom(img, cam, CN["Turkey"], (250, 250, 250), .75 * a_tr, fp, outline=WHITE, ow=4 * SS)
    glow_outline(img, cam, CN["Turkey"], (255, 90, 90), vis(t, 0, en("intro"), .3, .6) * .7, fp, 4)
    p = pinmark(img, cam, *GT, max(vis(t, cue("intro", "şanlıurfada", "şanlıurfa"), st("twist") - .2, .4, .3), vis(t, st("question") - .2, TOTAL, .4, .4)))
    if p:
        ytag(img, p[0], p[1] + 80 * SS, "ŞANLIURFA", vis(t, st("question") - .1, en("question") + .2, .3, .4), 48, bg=ORANGE, fg=WHITE)
        qa = vis(t, cue("question", "kim", "peki"), en("question") + .1, .3, .3)
        if qa > 0: stamp_text(img, "?", (p[0], p[1] - 260 * SS + math.sin(t * 5) * 8 * SS), FA, 240, fill=WHITE, stroke=BLACK, alpha=qa)

def timeline(img, t, a):
    if a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay); y = 1420 * SS; x0, x1 = 110 * SS, W - 110 * SS
    d.rounded_rectangle((x0 - 50 * SS, y - 170 * SS, x1 + 50 * SS, y + 120 * SS), radius=int(30 * SS), fill=A((10, 14, 24), a * .82))
    d.line([(x0, y), (x1, y)], fill=A(WHITE, a), width=6 * SS)
    xp = x0 + (x1 - x0) * (9600 - 2560) / (9600 + 2026)
    g = smooth((t - .3) / 1.5)
    d.line([(x0, y), (lerp(x0, xp, g), y)], fill=A(GOLD2, a), width=18 * SS)
    for x, lab, col in ((x0, "GÖBEKLİTEPE", GOLD2), (xp, "PİRAMİTLER", WHITE), (x1, "BUGÜN", WHITE)):
        d.ellipse((x - 14 * SS, y - 14 * SS, x + 14 * SS, y + 14 * SS), fill=A(col, a), outline=A(BLACK, a), width=3 * SS)
    img.alpha_composite(lay)
    for x, lab, yr in ((x0, "GÖBEKLİTEPE", "MÖ 9600"), (xp, "PİRAMİTLER", "MÖ 2560"), (x1, "BUGÜN", "2026")):
        ytag(img, x + (60 * SS if x == x0 else -40 * SS if x == x1 else 0), y + 70 * SS, yr, a, 30, bg=WHITE)
        stamp_text(img, lab, (x + (90 * SS if x == x0 else -60 * SS if x == x1 else 0), y - 60 * SS), FA, 40, fill=WHITE, stroke=BLACK, alpha=a)
    ytag(img, lerp(x0, xp, .5), y - 125 * SS, f"{trnum(7000 * g)} YIL", a * clamp01((t - .5) / .4), 50, sc=1)

def ui(img, t):
    brand.brand_card(img, t, "7.000 YIL ÖNCE,", "DEV TAŞLAR!", en("intro") - .2)
    timeline(img, t, vis(t, .2, en("intro") + .1, .4, .4))
    t_tw = st("twist")
    a = vis(t, t_tw - .1, en("twist") + .2, .3, .4)
    if a > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 18, int(170 * a))))
        lay = L(); d = ImageDraw.Draw(lay)
        for k, (kind, word, lab) in enumerate((("scroll", "yazısı", "YAZI"), ("wheel", "tekerleği", "TEKERLEK"), ("wheat", "tarlası", "TARIM"))):
            tw_ = cue("twist", word); x = W * (.2 + .3 * k); y = 1150 * SS
            if t > tw_ - .15:
                icon(d, kind, x, y, 1.3 * pop(t, tw_ - .15), a)
                if t > tw_ + .25: xmark(d, x, y, 110 * SS * pop(t, tw_ + .25), a, w=16)
        img.alpha_composite(lay)
        for k, (word, lab) in enumerate((("yazısı", "YAZI"), ("tekerleği", "TEKERLEK"), ("tarlası", "TARIM"))):
            if t > cue("twist", word) - .15: ytag(img, W * (.2 + .3 * k), 1380 * SS, lab, a, 40, bg=WHITE)
        hand(img, "hiçbiri yoktu!", W / 2, 1560 * SS, 84, vis(t, cue("twist", "tarlası") + .4, en("twist") + .2, .4, .4), YEL, -5)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Taşları kim dikti?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 86, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
    overlays(img, cam, fp, t)
    sc = vis(t, st("site") - .3, en("more") + .3, .7, .7)
    if sc > 0: gt_scene(img, t, sc)
    ui(img, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * .16)))
    caption_top(img, t)
    brand.watermark(img, t, TOTAL)
    fade = min(prog(t, 0, .15), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]: frame(float(tt)).save(f"v_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
