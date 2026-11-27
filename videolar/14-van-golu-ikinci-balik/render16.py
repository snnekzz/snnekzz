"""Video 14: Van Gölü'ndeki ikinci balık – sodalı gölde, 40 m'lik mikrobiyalit kulelerinde yaşayan tatlı su çöpçü balığı.
Haritanın Ardı teknikleri: renk=anlam altyazı (mavi = göl suyu, kırmızı/turuncu = lav, yanardağ, sıcak), "?" simgesi,
canlı sayaç, ~1 sn'de bir görsel olay, kalderaya 3B süzülme. Arazi ve göller AWS terrarium verisinden (nem_tex.py):
geniş görünüm z10 (vanr_tex), kaldera z13 (nem_tex). Lav ve eski çıkış güzergâhı temsilîdir."""
import json, math, os, random, re, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, Point
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
FC = "caveat.ttf"
BLUE = (37, 99, 235); KRED = (229, 36, 59); ORANGE = (255, 150, 40); GREEN = (110, 220, 130)
LAKE = (110, 195, 255); LAVA = (255, 95, 30); HOT = (255, 150, 40); TEAL = (120, 220, 190)
LON0, LAT0D = 30.0, 39.0
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
CN = {}

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
def lerp(a, b, p): return a + (b - a) * p

exec(open("maplib_src.py").read())
import nem_tex as NT
TEX_D, _ = NT.build(3072, "nem_tex.png", NT.B, 13)
TEX_B, _ = NT.build(3072, "vanr_tex.png", NT.BV, 10)
TD = tex_info(*NT.B, TEX_D); TB = tex_info(*NT.BV, TEX_B)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0
GL = json.load(open("nem_goller.json"))
MAIN = Polygon(GL["main"][0]); ILI = Polygon(GL["ili"][0]); VANP = Polygon(GL["van"][0])
def _chaikin(p, n=3):
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]): q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        p = q + [p[-1]]
    return p
def dens(path, n=6):
    out = []
    for (a0, b0), (a1, b1) in zip(path[:-1], path[1:]):
        for k in range(n): u = k / n; out.append((a0 + (a1 - a0) * u, b0 + (b1 - b0) * u))
    out.append(path[-1]); return out

# ---------- Van balık videosu: sabitler ----------
YELF = (250, 205, 40); SPOT = (30, 25, 20); WATER1 = (24, 92, 120); WATER2 = (6, 26, 44); TOWER = (196, 178, 140); TOWER_D = (120, 104, 78)
GEVAS = (43.10, 38.33)                      # balıkların toplandığı körfez (Gevaş yakını)
VANC = (42.95, 38.64)
DERE = [dens(_chaikin(p), 3) for p in (
    [(43.62, 39.22), (43.52, 39.10), (43.40, 39.00), (43.33, 38.97)],      # kuzeydoğu (Erciş tarafı)
    [(43.95, 38.80), (43.80, 38.72), (43.65, 38.66), (43.52, 38.62)],      # doğu
    [(43.30, 38.05), (43.22, 38.15), (43.15, 38.26), (43.12, 38.31)],      # güney (Gevaş)
    [(42.62, 39.10), (42.66, 38.98), (42.74, 38.86), (42.80, 38.80)],      # kuzeybatı
)]

def K_():
    t_g = cue("divers", "jandarma", "dalgıçları")
    return [(0.0, 42.95, 38.64, 270, 0, 0), (en("intro") - .2, 42.95, 38.64, 262, 4, 0), (t_g + .9, 43.10, 38.36, 85, 18, 0),
            (st("question"), 43.10, 38.36, 80, 18, 0), (st("fresh") + .3, 43.10, 38.66, 280, 8, 0), (en("fresh"), 43.10, 38.66, 270, 10, 0),
            (st("isolate") + .3, 42.98, 38.64, 270, 6, 0), (en("isolate"), 42.98, 38.64, 262, 8, 0),
            (st("cta") + .4, 42.80, 38.64, 285, 2, 0), (TOTAL - .8, 42.95, 38.64, 270, 0, 0), (TOTAL, 42.95, 38.64, 270, 0, 0)]
K = K_()
def cam_at(t):
    if t <= K[0][0]: a = b = K[0]; p = 0
    elif t >= K[-1][0]: a = b = K[-1]; p = 0
    else:
        for a, b in zip(K[:-1], K[1:]):
            if a[0] <= t <= b[0]: p = smooth((t - a[0]) / max(.01, b[0] - a[0])); break
    lon, lat = lerp(a[1], b[1], p), lerp(a[2], b[2], p)
    D = math.exp(lerp(math.log(a[3]), math.log(b[3]), p)) * 1000
    x, y = ll2m(lon, lat)
    return Cam(x, y, D, math.radians(lerp(a[4], b[4], p)), math.radians(lerp(a[5], b[5], p) + 0.8 * math.sin(t * .18)))

# ---------- metin yardımcıları ----------
def hand(img, text, x, y, size, a, col=WHITE, rot=-6):
    if a <= .01: return
    f = font(FC, size * SS); l, t_, r, b = f.getbbox(text, stroke_width=4 * SS)
    lay = Image.new("RGBA", (r - l + 40, b - t_ + 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20 - l, 20 - t_), text, font=f, fill=A(col, a), stroke_width=int(4 * SS), stroke_fill=(0, 0, 0, int(200 * a)))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def ytag(img, x, y, text, a, size=44, bg=YEL, fg=BLACK, sc=1.):
    if a <= .01 or sc <= .01: return
    f = font(FA, size * SS * sc); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 30 * SS * sc, b - t_ + 22 * SS * sc
    x = min(max(x, w / 2 + 30 * SS), W - w / 2 - 30 * SS)          # ekran içinde kalsın
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((14, 14, w + 14, h + 14), fill=(0, 0, 0, int(100 * a))); d.rectangle((8, 8, w + 8, h + 8), fill=A(bg, a))
    d.text((8 + w / 2, 8 + h / 2), text, font=f, fill=A(fg, a), anchor="mm")
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def typetag(img, x, y, text, t, t0, a, size=50, bg=ORANGE, fg=BLACK):
    n = int(clamp01((t - t0) / (.06 * len(text))) * len(text) + .999)
    if n > 0: ytag(img, x, y, text[:n], a, size, bg, fg)
def trnum(v): return f"{int(round(v)):,}".replace(",", ".")



ENT = {}
for k in ("van", "gölü", "gölünde", "gölde", "gölün", "gölünün", "gölle", "göl", "suyu", "suyun", "tatlı", "derelerde", "derelerden"): ENT[k] = LAKE
for k in ("yanılmışız",): ENT[k] = KRED
for k in ("sarı", "benekli", "balık", "balığı", "balıklar"): ENT[k] = YELF
for k in ("sodalı",): ENT[k] = WHITE
for k in ("kulelerin", "kuleler", "kulelerde", "mikrobiyalitler"): ENT[k] = TOWER
for k in ("tehlike", "nesli", "koptu"): ENT[k] = KRED
for k in ("nemrut",): ENT[k] = LAVA

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
        ec = ENT.get(_n(c["words"][i]))
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


def scr_line(cam, pts):
    out = []
    for lon, lat in pts:
        q = pj(cam, lon, lat)
        if q: out.append((float(q[0]), float(q[1])))
    return out
def flow_particles(d, line, t, a, col, speed, n, r=7, tail=8, phase=0.):
    if len(line) < 2 or a <= 0: return
    L_ = len(line) - 1
    for k in range(n):
        u = (k / n + t * speed + phase) % 1.0
        i = u * L_; i0 = int(i); fr = i - i0
        if i0 >= L_: continue
        x = line[i0][0] + (line[i0 + 1][0] - line[i0][0]) * fr; y = line[i0][1] + (line[i0 + 1][1] - line[i0][1]) * fr
        j = max(0, int(i - tail)); tx, ty = line[j]; edge = min(1, u * 8, (1 - u) * 8)
        d.line([(tx, ty), (x, y)], fill=A(col, a * .35 * edge), width=int(r * SS * .9))
        d.ellipse((x - r * SS, y - r * SS, x + r * SS, y + r * SS), fill=A(col, a * edge))
def poly_glow(img, cam, poly, col, a, width=5, fill_a=0.):
    if a <= .01: return
    pts = scr_line(cam, list(poly.exterior.coords))
    if len(pts) < 3: return
    lay = L(); d = ImageDraw.Draw(lay)
    if fill_a > 0: d.polygon(pts, fill=A(col, a * fill_a))
    d.line(pts + [pts[0]], fill=A(col, a * .35), width=width * 4 * SS, joint="curve")
    d.line(pts + [pts[0]], fill=A(col, a), width=width * SS, joint="curve")
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.5)))
def wisps(d, cx, cy, spread, t, a, col=(235, 245, 255), n=14, h=260, seed=1):
    rr = random.Random(seed)
    for k in range(n):
        x0 = cx + rr.uniform(-spread, spread); ph = (t * .35 + rr.random()) % 1
        y = cy - ph * h * SS; x = x0 + math.sin(ph * 6 + k) * 18 * SS; r = (10 + ph * 26) * SS
        d.ellipse((x - r, y - r, x + r, y + r), fill=A(col, a * .55 * math.sin(ph * math.pi)))
def yinyang(d, x, y, r, a):
    d.ellipse((x - r, y - r, x + r, y + r), fill=A(WHITE, a), outline=A(BLACK, a), width=int(4 * SS))
    d.pieslice((x - r, y - r, x + r, y + r), 90, 270, fill=A((20, 60, 130), a))
    d.ellipse((x - r / 2, y - r, x + r / 2, y), fill=A((20, 60, 130), a)); d.ellipse((x - r / 2, y, x + r / 2, y + r), fill=A(WHITE, a))
    d.ellipse((x - r / 8, y - r / 2 - r / 8, x + r / 8, y - r / 2 + r / 8), fill=A(WHITE, a))
    d.ellipse((x - r / 8, y + r / 2 - r / 8, x + r / 8, y + r / 2 + r / 8), fill=A((20, 60, 130), a))
    d.ellipse((x - r, y - r, x + r, y + r), outline=A(BLACK, a), width=int(4 * SS))


# ---------- çizim yardımcıları ----------
def kefal(d, x, y, s, a, flip=False):
    """inci kefali: gümüş gövde, turuncu yüzgeç (eski videodaki balık)"""
    s *= SS; m = -1 if flip else 1
    T = lambda px, py: (x + m * px * s, y + py * s)
    d.polygon([T(-52, 0), T(-86, -26), T(-80, 0), T(-86, 26)], fill=A(ORANGE, a))
    d.polygon([T(-5, -18), T(15, -36), T(25, -18)], fill=A(ORANGE, a))
    d.polygon([T(60 * math.cos(u), 22 * math.sin(u)) for u in np.linspace(0, 2 * math.pi, 28)], fill=A((205, 215, 225), a), outline=A((60, 70, 80), a))
    ex, ey = T(42, -4); d.ellipse((ex - 4.5 * s, ey - 4.5 * s, ex + 4.5 * s, ey + 4.5 * s), fill=A((20, 20, 24), a))
def copcu(d, x, y, s, a, flip=False, wig=0.0):
    """çöpçü balığı (Oxynoemacheilus): ince uzun sarı gövde, siyah benekler, bıyıklar"""
    s *= SS; m = -1 if flip else 1
    def T(px, py): return (x + m * px * s, y + (py + math.sin(px / 25 + wig) * 3) * s)
    d.polygon([T(-58, 0), T(-84, -16), T(-80, 0), T(-84, 16)], fill=A((215, 165, 30), a))
    body = [T(62 * math.cos(u), 13 * math.sin(u) * (1.15 if math.cos(u) > 0 else .85)) for u in np.linspace(0, 2 * math.pi, 32)]
    d.polygon(body, fill=A(YELF, a), outline=A((90, 70, 20), a))
    d.polygon([T(-8, -11), T(8, -22), T(18, -11)], fill=A((215, 165, 30), a))
    rr = random.Random(11)
    for _ in range(9):
        px, py = rr.uniform(-45, 40), rr.uniform(-7, 7); q = T(px, py); r = rr.uniform(2.2, 4) * s
        d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=A(SPOT, a))
    ex, ey = T(46, -3); d.ellipse((ex - 3 * s, ey - 3 * s, ex + 3 * s, ey + 3 * s), fill=A((15, 15, 15), a))
    for k in (-1, 1): d.line([T(60, 4), T(72, 4 + 7 * k)], fill=A((90, 70, 20), a), width=max(1, int(2 * s)))
def bubbles(d, t, a, n=40, seed=2, x0=0, x1=None):
    rr = random.Random(seed); x1 = x1 or W
    for k in range(n):
        x = rr.uniform(x0, x1); ph = (t * rr.uniform(.12, .25) + rr.random()) % 1; y = H * (1 - ph); r = rr.uniform(3, 9) * SS
        d.ellipse((x - r, y - r, x + r, y + r), outline=A((200, 235, 255), a * .6), width=int(2 * SS))
def diver(d, x, y, s, a, t):
    s *= SS; c = A((15, 20, 28), a)
    d.ellipse((x - 26 * s, y - 26 * s, x + 26 * s, y + 26 * s), fill=c)                       # baş
    d.rounded_rectangle((x - 14 * s, y - 10 * s, x + 20 * s, y + 8 * s), radius=int(6 * s), fill=A((90, 170, 200), a))   # maske
    d.polygon([(x - 20 * s, y + 20 * s), (x - 190 * s, y + 70 * s), (x - 200 * s, y + 40 * s), (x - 30 * s, y - 5 * s)], fill=c)   # gövde
    d.rounded_rectangle((x - 150 * s, y - 10 * s, x - 70 * s, y + 18 * s), radius=int(10 * s), fill=A((200, 200, 60), a))       # tüp
    k = math.sin(t * 4) * 18 * s
    for dy in (55, 75): d.polygon([(x - 190 * s, y + dy * s), (x - 290 * s, y + dy * s + k), (x - 285 * s, y + dy * s + 30 * s + k)], fill=c)
def water_bg(d, a=1.0, t=0.0):
    for yy in range(0, H, 10):
        u = yy / H; d.rectangle((0, yy, W, yy + 10), fill=tuple(int(lerp(p, q, u)) for p, q in zip(WATER1, WATER2)) + (int(255 * a),))
def rays(d, t, a=1.0):
    for k in range(5):                                          # ışık huzmeleri (ayrı katmanda çizilmeli)
        x = W * (.15 + .18 * k) + math.sin(t * .6 + k) * 40 * SS
        d.polygon([(x - 30 * SS, 0), (x + 30 * SS, 0), (x + 160 * SS, H * .75), (x - 60 * SS, H * .75)], fill=(160, 220, 240, int(22 * a)))
GROUND = 1650 * SS
def tower(d, x, base, h, w, a, seed=0):
    rr = random.Random(seed); pts_l, pts_r = [], []
    for k in range(13):
        u = k / 12; y = base - h * u; ww = w * (1 - .55 * u) * (1 + .12 * math.sin(u * 9 + seed))
        pts_l.append((x - ww / 2 + rr.uniform(-6, 6) * SS, y)); pts_r.append((x + ww / 2 + rr.uniform(-6, 6) * SS, y))
    d.polygon(pts_l + pts_r[::-1], fill=A(TOWER, a), outline=A(TOWER_D, a))
    for k in range(1, 12):                                       # katmanlı doku
        u = k / 12; y = base - h * u
        d.line([(pts_l[k][0] + 6 * SS, y), (pts_r[k][0] - 6 * SS, y)], fill=A(TOWER_D, a * .45), width=int(2 * SS))
    return pts_l, pts_r

# ---------- harita katmanı ----------
def map_overlays(img, cam, t):
    a_v = max(vis(t, .1, en("intro") + .2, .5, .4), vis(t, st("fresh"), en("fresh") + .2, .4, .4), vis(t, st("cta"), TOTAL, .4, .2))
    poly_glow(img, cam, VANP, LAKE, a_v, 5, .14)
    lay = L(); d = ImageDraw.Draw(lay)
    # dereler + derelerde yüzen çöpçü balıkları
    a_f = vis(t, st("fresh") - .1, en("fresh") + .2, .4, .4)
    t_iso = cue("isolate", "çekilince", "göl")
    a_i = vis(t, st("isolate") - .1, en("isolate") + .2, .4, .4)
    cut = smooth((t - t_iso) / 1.2) if a_i > 0 else 0
    for k, p in enumerate(DERE):
        a_d = max(a_f, a_i)
        if a_d <= 0: continue
        ln = scr_line(cam, p)
        if len(ln) < 2: continue
        n_ok = len(ln) if a_i <= 0 else max(2, int(len(ln) * (1 - .45 * cut)))
        d.line(ln[:n_ok], fill=A(LAKE, a_d * .35), width=int(26 * SS), joint="curve"); d.line(ln[:n_ok], fill=A(LAKE, a_d), width=int(10 * SS), joint="curve")
        flow_particles(d, ln[:n_ok], t, a_d * .9, (220, 245, 255), .25, 6, r=6, phase=k * .2)
        if a_f > 0 and t > cue("fresh", "derelerde", "dökülen"):
            u = (t * .18 + k * .27) % 1; i = int(u * (len(ln) - 2)); x, y = ln[i]; x2, y2 = ln[i + 1]
            copcu(d, x, y, .9, a_f, flip=(x2 < x))
    # göl çekilmesi: içte küçülen göl
    if a_i > 0 and cut > 0:
        from shapely import affinity
        sp = affinity.scale(VANP, 1 - .22 * cut, 1 - .22 * cut, origin="centroid")
        pts = scr_line(cam, list(sp.exterior.coords))
        if len(pts) > 2:
            dl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dl)
            full = scr_line(cam, list(VANP.exterior.coords))
            dd.polygon(full, fill=(150, 130, 90, int(150 * a_i * cut))); dd.polygon(pts, fill=(40, 110, 170, int(255 * a_i)))
            img.alpha_composite(dl)
    img.alpha_composite(lay)
    # etiketler
    a_lb = max(vis(t, .3, en("intro") + .2, .5, .4), vis(t, st("fresh"), en("fresh") + .2, .4, .4))
    q = pj(cam, *VANC)
    if q and a_lb > 0: ytag(img, q[0], q[1] - 40 * SS, "VAN GÖLÜ", a_lb, 54, bg=LAKE)
    if a_f > 0 and t > cue("fresh", "tatlı"): ytag(img, W / 2, 1480 * SS, "TATLI SU BALIĞI", a_f * sine_out((t - cue("fresh", "tatlı")) / .3), 56, bg=YELF)
    if a_f > 0 and t > cue("fresh", "derelerde", "dökülen"): hand(img, "derelerden göle", W / 2, 1640 * SS, 84, a_f, WHITE, -5)
    if a_i > 0 and cut > .5:
        ytag(img, W / 2, 1480 * SS, "BAĞLANTI KOPTU", a_i * sine_out((t - t_iso - .6) / .3), 56, bg=KRED, fg=WHITE)
        hand(img, "kulelerde kaldılar", W / 2, 1640 * SS, 88, a_i * sine_out((t - t_iso - 1.0) / .4), YEL, -5)
    # Gevaş iğnesi (dalgıç sahnesine geçiş)
    t_g = cue("divers", "jandarma", "dalgıçları")
    a_g = vis(t, t_g - .1, t_g + 1.6, .3, .3)
    if a_g > 0:
        q = pj(cam, *GEVAS)
        if q:
            dd = ImageDraw.Draw(img); r = (20 + 40 * ((t * 1.5) % 1)) * SS
            dd.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), outline=A(YELF, a_g * (1 - (t * 1.5) % 1)), width=int(6 * SS))
            dd.ellipse((q[0] - 16 * SS, q[1] - 16 * SS, q[0] + 16 * SS, q[1] + 16 * SS), fill=A(KRED, a_g), outline=A(WHITE, a_g), width=int(4 * SS))
            ytag(img, q[0], q[1] - 110 * SS, "GEVAŞ AÇIKLARI · ~13 m", a_g, 46, bg=WHITE)

# ---------- açılış kartı: "TEK BALIK!" → çizilir ----------
def old_claim(img, t):
    a = vis(t, .15, en("intro") + .15, .3, .3)
    if a <= 0: return
    cx, cy = W / 2, 1230 * SS
    lay = L(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((cx - 360 * SS, cy - 230 * SS, cx + 360 * SS, cy + 230 * SS), radius=int(30 * SS), fill=(10, 16, 30, int(215 * a)), outline=A(WHITE, a * .5), width=int(3 * SS))
    kefal(d, cx, cy + 60 * SS, 2.2, a)
    img.alpha_composite(lay)
    stamp_text(img, "TEK BALIK!", (cx, cy - 120 * SS), FA, 120, fill=YEL, stroke=BLACK, alpha=a)
    t_y = cue("intro", "yanılmışız")
    if t > t_y:
        g = pop(t, t_y); d2 = ImageDraw.Draw(img)
        for s_ in (1, -1): d2.line([(cx - 330 * SS * g, cy - 200 * SS * s_ * g), (cx + 330 * SS * g, cy + 200 * SS * s_ * g)], fill=A(KRED, a), width=int(22 * SS))
        stamp_text(img, "YANILMIŞIZ!", (cx, cy + 300 * SS), FA, 110, fill=WHITE, stroke=KRED, alpha=a * sine_out((t - t_y) / .25), scale=pop(t, t_y))

# ---------- su altı paneli: dalgıç, soru, kuleler, kaynak, tehlike ----------
def underwater(img, t):
    t_g = cue("divers", "jandarma", "dalgıçları")
    a1 = vis(t, t_g + 1.3, en("question") + .1, .45, .45)
    a2 = vis(t, st("towers") - .2, en("spring") + .1, .45, .45)
    a3 = vis(t, st("danger") - .2, en("danger") + .2, .4, .4)
    a = max(a1, a2, a3)
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    water_bg(d, 1.0, t)
    d.polygon([(0, GROUND)] + [(x, GROUND + 18 * SS * math.sin(x / W * 11)) for x in np.linspace(0, W, 40)] + [(W, H), (0, H)], fill=(52, 44, 34, 255))
    base = lay; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rays(d, t); base.alpha_composite(lay); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    bubbles(d, t, 1.0)
    if a1 > 0:                                                    # dalgıç + balık
        diver(d, W * .78, 820 * SS, 1.2, a1, t)
        t_b = cue("divers", "beş", "5", "santimetre")
        g = smooth((t - t_g - 1.6) / .8); fx = lerp(W * .35, W * .45, g); fy = 1180 * SS + math.sin(t * 2) * 15 * SS
        copcu(d, fx, fy, 4.2 * g + .01, a1 * g, wig=t * 6)
        if t > t_b:                                              # cetvel 5–6 cm
            dd = d; y = fy + 140 * SS; x0, x1 = fx - 260 * SS, fx + 300 * SS
            dd.line([(x0, y), (x1, y)], fill=A(WHITE, a1), width=int(6 * SS))
            for k in range(7): xx = lerp(x0, x1, k / 6); dd.line([(xx, y - 18 * SS), (xx, y + 18 * SS)], fill=A(WHITE, a1), width=int(4 * SS))
    if a2 > 0:                                                    # kuleler
        t_t = cue("towers", "kırk", "40", "metreye")
        grow = smooth((t - st("towers") + .1) / 1.6)
        tw = [(W * .22, 760, 300, 1), (W * .52, 1120, 380, 2), (W * .82, 640, 260, 3)]
        tops = []
        for x, h, w, sd in tw:
            pl, pr = tower(d, x, GROUND, h * SS * grow, w * SS, a2, sd); tops.append((x, GROUND - h * SS * grow))
        for k in range(10):                                       # kulenin çevresinde çöpçü balıkları
            ph = t * .35 + k * .628; x = tops[1][0] + math.cos(ph) * (180 + 25 * (k % 3)) * SS; y = tops[1][1] + 260 * SS + math.sin(ph * 1.3) * 160 * SS + k * 30 * SS
            copcu(d, x, y, .9, a2 * grow, flip=math.sin(ph) > 0, wig=t * 6 + k)
        if t > st("spring") - .1:                                  # yeraltı suyu kulenin içinden yükselir
            a_s = a2 * vis(t, st("spring") - .1, en("spring") + .1, .3, .3); x = tops[1][0]
            for k in range(14):
                ph = (t * .5 + k / 14) % 1; y = GROUND + 120 * SS - ph * (GROUND + 120 * SS - tops[1][1]); r = 10 * SS
                d.ellipse((x - r + math.sin(ph * 12) * 20 * SS, y - r, x + r + math.sin(ph * 12) * 20 * SS, y + r), fill=A((170, 235, 255), a_s * (1 - ph * .6)))
            for k in range(-2, 3):
                xx = x + k * 70 * SS; d.line([(xx, GROUND + 140 * SS), (xx, GROUND + 20 * SS)], fill=A((170, 235, 255), a_s * .8), width=int(8 * SS))
                d.polygon([(xx - 18 * SS, GROUND + 40 * SS), (xx + 18 * SS, GROUND + 40 * SS), (xx, GROUND + 5 * SS)], fill=A((170, 235, 255), a_s * .8))
    if a3 > 0:
        copcu(d, W / 2, 1150 * SS, 4.5, a3, wig=t * 4)
    base.alpha_composite(lay); lay = base
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    # metin katmanı
    if a1 > 0:
        ytag(img, W * .3, 700 * SS, "JANDARMA SU ALTI TİMİ · 2018", a1 * vis(t, t_g + 1.4, en("divers"), .3, .3), 40, bg=WHITE)
        t_b = cue("divers", "beş", "5", "santimetre")
        if t > t_b: stamp_text(img, "5–6 cm", (W * .45, 1450 * SS), FA, 110, fill=YEL, stroke=BLACK, alpha=a1 * vis(t, t_b, en("divers") + .1, .25, .3))
        t_sb = cue("divers", "sarı", "benekli")
        if t > t_sb: hand(img, "sarı, siyah benekli", W * .45, 980 * SS, 86, a1 * vis(t, t_sb, en("divers") + .1, .3, .3), YELF, -5)
        qa = vis(t, cue("question", "peki", "nasıl"), en("question") + .1, .3, .3) * a1
        if qa > 0:
            stamp_text(img, "?", (W * .72, 1250 * SS + math.sin(t * 5) * 10 * SS), FA, 300, fill=WHITE, stroke=BLACK, alpha=qa)
            ytag(img, W / 2, 1520 * SS, "SODALI SU · pH 9,7+", qa, 52, bg=WHITE)
    if a2 > 0:
        t_t = cue("towers", "kırk", "40", "metreye")
        if t > t_t - .1:
            x = W * .52 + 260 * SS; g = smooth((t - t_t + .1) / .8); y0 = GROUND; y1 = GROUND - 1120 * SS * g
            d2 = ImageDraw.Draw(img); d2.line([(x, y0), (x, y1)], fill=A(YEL, a2), width=int(8 * SS))
            for yy in (y0, y1): d2.line([(x - 24 * SS, yy), (x + 24 * SS, yy)], fill=A(YEL, a2), width=int(8 * SS))
            stamp_text(img, f"{int(round(40 * g))} m", (x + 10 * SS, y1 - 70 * SS), FA, 100, fill=YEL, stroke=BLACK, alpha=a2)
            hand(img, "≈ 13 katlı bina", W * .30, 640 * SS, 80, a2 * vis(t, t_t + .5, en("towers") + .1, .3, .3), WHITE, -5)
        t_m = cue("towers", "mikrobiyalitler", "bilinen", "en")
        if t > t_m: ytag(img, W / 2, 1500 * SS, "BİLİNEN EN BÜYÜK MİKROBİYALİTLER", a2 * vis(t, t_m, en("towers") + .1, .3, .3), 46, bg=TOWER)
        a_s = a2 * vis(t, st("spring") - .1, en("spring") + .1, .3, .3)
        if a_s > 0:
            ytag(img, W * .52, GROUND + 100 * SS, "YERALTI SUYU ↑", a_s, 48, bg=(170, 235, 255))
            ytag(img, W * .25, 560 * SS, "SODALI GÖL SUYU", a_s, 46, bg=WHITE)
    if a3 > 0:
        t_d = cue("danger", "tehlike", "nesli")
        stamp_text(img, "NESLİ TEHLİKEDE", (W / 2, 1480 * SS), FA, 120, fill=WHITE, stroke=KRED, alpha=a3 * sine_out((t - t_d + .1) / .3), scale=pop(t, t_d - .1), )
        ytag(img, W / 2, 1650 * SS, "IUCN: TEHLİKEDE (EN)", a3 * vis(t, t_d + .4, en("danger") + .2, .3, .3), 40, bg=WHITE)

def ui(img, t):
    brand.brand_card(img, t, "VAN GÖLÜ'NDE", "İKİNCİ BALIK!", en("intro") - .1)
    a = vis(t, st("cta") + .2, TOTAL, .5, .3)
    if a > 0:
        t_n = cue("cta", "nemrut")
        q_ok = vis(t, t_n - .1, cue("cta", "sence") + .3, .3, .3)
        if q_ok > 0: ytag(img, W / 2, 1480 * SS, "DEVAMI: NEMRUT", q_ok, 60, bg=LAVA, fg=WHITE)
        t_s = cue("cta", "sence", "üçüncü")
        hand(img, "Üçüncü balık var mı?", W / 2, 620 * SS, 90, vis(t, t_s, TOTAL, .4, .3), YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1480 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t)
    map_overlays(img, cam, t)
    old_claim(img, t)
    underwater(img, t)
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
