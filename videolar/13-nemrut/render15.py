"""Video 13: Nemrut – Van Gölü'nü bugünkü hâline getiren yanardağ ve kalderasındaki iki göl.
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
NEM = (42.245, 38.623)                       # kaldera merkezi (veriden; ~8,5 x 7 km)

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
# lav: Nemrut'tan batıya ~60 km (temsilî); eski çıkış: gölün güneybatısından batıya, Murat'a (temsilî)
LAV = dens(_chaikin([(42.18, 38.63), (42.05, 38.615), (41.92, 38.63), (41.80, 38.66), (41.66, 38.69), (41.52, 38.71)]), 3)
CIKIS = dens(_chaikin([(42.30, 38.52), (42.12, 38.56), (41.97, 38.60), (41.82, 38.66), (41.62, 38.73), (41.40, 38.78)]), 3)
CROSS = (41.88, 38.635)
RIM = [(NEM[0] + .049 * math.cos(u), NEM[1] + .032 * math.sin(u)) for u in np.linspace(0, 2 * math.pi, 90)]

# ---------- kamera ----------
def K_():
    return [(0.0, 42.85, 38.64, 300, 0, 0), (en("intro") - .3, 42.80, 38.64, 280, 6, 0), (st("lava") + .4, 41.95, 38.66, 175, 12, 0),
            (en("lava"), 41.95, 38.66, 168, 14, 0), (st("soda") + .3, 42.85, 38.62, 270, 4, 0), (en("soda"), 42.85, 38.62, 262, 5, 0),
            (st("question") + .5, 42.24, 38.635, 40, 18, 0), (st("caldera") + .6, 42.235, 38.632, 26, 36, 0), (en("caldera"), 42.235, 38.632, 25, 38, 8),
            (st("cold") + .5, 42.225, 38.628, 21, 32, 4), (st("hot") + .4, 42.244, 38.640, 13, 30, 0), (en("hot"), 42.244, 38.640, 12.5, 30, 0),
            (st("yinyang") + .6, 42.234, 38.632, 22, 0, 0), (en("yinyang"), 42.234, 38.632, 21, 0, 0),
            (st("active") + 1.0, 42.30, 38.66, 120, 22, 0), (st("cta"), 42.55, 38.66, 220, 16, 0), (TOTAL, 42.55, 38.66, 215, 16, 0)]
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
for k in ("van", "gölü", "gölünü", "gölün", "göl", "suyun", "suyu", "tatlı", "soğuk"): ENT[k] = LAKE
for k in ("lav", "nemrut", "dağından", "yanardağ", "yanardağın", "yanardağı", "aktif", "patlaması", "uyanır"): ENT[k] = LAVA
for k in ("sıcak", "ısınıyor"): ENT[k] = HOT
for k in ("soda", "sabun"): ENT[k] = WHITE
for k in ("kapattı",): ENT[k] = KRED
for k in ("yinyang",): ENT[k] = WHITE

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

def map_overlays(img, cam, t):
    # Van Gölü vurgusu
    a_v = max(vis(t, .1, en("intro") + .2, .5, .4), vis(t, st("soda"), en("soda") + .2, .4, .4))
    poly_glow(img, cam, VANP, LAKE, a_v, 5, .18)
    lay = L(); d = ImageDraw.Draw(lay)
    # eski çıkış (mavi, batıya akar) + lav
    t_l = cue("lava", "lav", "nemrut"); t_k = cue("lava", "kapattı", "çıkışını")
    pr = .45 * smooth((t - t_l) / max(.5, t_k - t_l)) if t < t_k else .45 + .55 * smooth((t - t_k) / 1.3)
    a_l = vis(t, st("lava") - .1, en("lava") + .2, .4, .4)
    if a_l > 0:
        cl = scr_line(cam, CIKIS)
        cut = scr_line(cam, [CROSS])[0] if scr_line(cam, [CROSS]) else None
        blocked = t > t_k
        n_ok = len(cl) if not blocked else int(len(cl) * .42)
        if n_ok > 1: d.line(cl[:n_ok], fill=A(LAKE, a_l * .35), width=int(34 * SS), joint="curve"); d.line(cl[:n_ok], fill=A(LAKE, a_l * .9), width=int(14 * SS), joint="curve")
        flow_particles(d, cl[:n_ok], t, a_l * (1 if not blocked else .5), LAKE, .2, 10, r=8)
        ll = scr_line(cam, LAV); pp = partial(ll, pr) if len(ll) > 1 else []
        if len(pp) > 1:
            d.line(pp, fill=A(LAVA, a_l * .3), width=int(60 * SS), joint="curve")
            d.line(pp, fill=A(LAVA, a_l * .8), width=int(30 * SS), joint="curve")
            d.line(pp, fill=A((255, 220, 120), a_l), width=int(10 * SS), joint="curve")
            x, y = pp[-1]; r = (26 + 6 * math.sin(t * 9)) * SS
            d.ellipse((x - r, y - r, x + r, y + r), fill=A((255, 230, 150), a_l))
        if blocked and cut:
            g = pop(t, t_k); x, y = cut; s = 60 * SS * g
            for sg in (1, -1): d.line([(x - s, y - s * sg), (x + s, y + s * sg)], fill=A(KRED, a_l), width=int(18 * SS))
    # buharlaşma + soda
    a_s = vis(t, st("soda") - .1, en("soda") + .2, .4, .4)
    if a_s > 0:
        q = pj(cam, 42.95, 38.64)
        if q:
            wisps(d, q[0], q[1], 420 * SS, t, a_s, n=26, h=420, seed=3)
            t_sd = cue("soda", "soda")
            if t > t_sd:
                rr = random.Random(9); g = smooth((t - t_sd) / 1.2)
                for _ in range(int(160 * g)):
                    lo, la = rr.uniform(42.45, 43.45), rr.uniform(38.45, 38.85)
                    if VANP.contains(Point(lo, la)):
                        p_ = pj(cam, lo, la)
                        if p_: s = rr.uniform(4, 8) * SS; d.rectangle((p_[0] - s, p_[1] - s, p_[0] + s, p_[1] + s), fill=A(WHITE, a_s * .85))
    # Ilıgöl buharı
    a_h = vis(t, st("hot") - .1, en("hot") + .2, .4, .4)
    if a_h > 0:
        q = pj(cam, *ILI.centroid.coords[0])
        if q: wisps(d, q[0], q[1], 90 * SS, t, a_h, (255, 240, 225), n=16, h=320, seed=5)
    # aktif: kızıl nabız
    a_a = vis(t, st("active") - .1, en("active") + .3, .4, .4)
    if a_a > 0:
        q = pj(cam, *NEM)
        if q:
            for k in range(3):
                ph = (t * .7 + k / 3) % 1; r = (40 + ph * 260) * SS
                d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), outline=A(LAVA, a_a * (1 - ph)), width=int(8 * SS))
            d.ellipse((q[0] - 34 * SS, q[1] - 34 * SS, q[0] + 34 * SS, q[1] + 34 * SS), fill=A(LAVA, a_a * (.6 + .4 * math.sin(t * 6))))
    img.alpha_composite(lay)
    # kaldera kenarı + cetvel
    a_c = vis(t, cue("caldera", "çukur", "kilometrelik", "yerinde"), en("caldera") + .2, .4, .4)
    if a_c > 0:
        poly_glow(img, cam, Polygon(RIM), YEL, a_c, 5)
        p0, p1 = pj(cam, NEM[0] - .049, NEM[1] - .045), pj(cam, NEM[0] + .049, NEM[1] - .045)
        if p0 and p1:
            dd = ImageDraw.Draw(img); g = smooth((t - cue("caldera", "kilometrelik", "yedi")) / .8)
            xe = lerp(p0[0], p1[0], g)
            p0 = (float(p0[0]), float(p0[1])); p1 = (float(p1[0]), float(p1[1])); xe = lerp(p0[0], p1[0], g)
            dd.line([p0, (xe, lerp(p0[1], p1[1], g))], fill=A(YEL, a_c), width=int(8 * SS))
            for p_ in (p0, (xe, lerp(p0[1], p1[1], g))): dd.line([(p_[0], p_[1] - 24 * SS), (p_[0], p_[1] + 24 * SS)], fill=A(YEL, a_c), width=int(8 * SS))
            ytag(img, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 80 * SS, f"~{int(round(7 * g))} KM", a_c * clamp01(g * 3), 56, bg=YEL)
    # göller
    a_m = max(vis(t, st("cold") - .1, en("cold") + .2, .4, .4), vis(t, st("yinyang"), en("yinyang") + .2, .4, .4))
    poly_glow(img, cam, MAIN, LAKE, a_m, 5, .12)
    a_i = max(vis(t, st("hot") - .1, en("hot") + .2, .4, .4), vis(t, st("yinyang"), en("yinyang") + .2, .4, .4))
    poly_glow(img, cam, ILI, HOT, a_i, 5, .25)
    # etiketler
    a_lb = max(vis(t, .3, en("intro") + .2, .5, .4), vis(t, st("soda"), en("soda") + .2, .4, .4))
    q = pj(cam, 42.97, 38.62)
    if q: ytag(img, q[0], q[1], "VAN GÖLÜ", a_lb, 56, bg=LAKE)
    a_n = max(vis(t, .8, en("lava") + .2, .4, .4), vis(t, st("question"), en("question") + .1, .4, .3), vis(t, st("active"), en("active") + .2, .4, .4))
    q = pj(cam, *NEM)
    if q:
        dd = ImageDraw.Draw(img)
        if a_n > 0:
            dd.polygon([(q[0], q[1] - 70 * SS), (q[0] - 46 * SS, q[1] + 10 * SS), (q[0] + 46 * SS, q[1] + 10 * SS)], fill=A(LAVA, a_n), outline=A(BLACK, a_n))
            ytag(img, q[0], q[1] - 130 * SS, "NEMRUT", a_n, 50, bg=LAVA, fg=WHITE)
    if a_l > 0:
        q = pj(cam, *LAV[len(LAV) * 2 // 3])
        if q and t > t_l: typetag(img, q[0], q[1] + 120 * SS, "LAV · 60 KM", t, t_l + .4, a_l, 50, bg=LAVA, fg=WHITE)
        q = pj(cam, *CROSS)
        if q and t > t_k: ytag(img, q[0], q[1] - 150 * SS, "ÇIKIŞ KAPANDI", a_l * sine_out((t - t_k) / .3), 52, bg=KRED, fg=WHITE)
        q = pj(cam, *CIKIS[-6])
        if q: ytag(img, q[0], q[1] + 110 * SS, "GÖLÜN ÇIKIŞI", a_l * (1 - smooth((t - t_k - .8) / .4)), 44, bg=LAKE)
    if a_s > 0:
        ytag(img, W / 2, 640 * SS, "BUHARLAŞMA ↑", a_s * vis(t, cue("soda", "buharlaştı"), en("soda") + .2, .3, .3), 50, bg=WHITE)
        t_sd = cue("soda", "soda")
        if t > t_sd: ytag(img, W / 2, 1500 * SS, "SODA GÖLDE KALDI", a_s * sine_out((t - t_sd) / .3), 52, bg=WHITE)
        t_sb = cue("soda", "sabun")
        if t > t_sb: hand(img, "sabun gibi su!", W / 2, 1700 * SS, 96, a_s * sine_out((t - t_sb) / .4), YEL, -6)
    qa = vis(t, cue("question", "peki", "tepesinde"), en("question") + .1, .3, .3)
    if qa > 0:
        q = pj(cam, *NEM)
        if q: stamp_text(img, "?", (q[0] + 260 * SS, q[1] - 200 * SS + math.sin(t * 5) * 8 * SS), FA, 260, fill=WHITE, stroke=BLACK, alpha=qa)
    if a_m > 0 and st("cold") - .2 < t < en("cold") + .3:
        q = pj(cam, *MAIN.centroid.coords[0])
        if q: ytag(img, q[0] - 120 * SS, q[1] - 40 * SS, "SOĞUK · TATLI", a_m, 50, bg=LAKE)
        t_d = cue("cold", "176", "yüz", "derinliğinde")
        if t > t_d - .2:          # derinlik çubuğu
            g = smooth((t - t_d + .2) / 1.2); dd = ImageDraw.Draw(img); x = W - 150 * SS; y0 = 820 * SS; y1 = y0 + 760 * SS * g
            dd.rectangle((x - 30 * SS, y0, x + 30 * SS, y1), fill=A((20, 60, 130), a_m), outline=A(WHITE, a_m), width=int(4 * SS))
            for k in range(1, 4):
                yy = y0 + 760 * SS * k / 4
                if yy < y1: dd.line([(x - 30 * SS, yy), (x + 30 * SS, yy)], fill=A(WHITE, a_m * .6), width=int(3 * SS))
            stamp_text(img, f"{int(round(176 * g))} m", (x - 20 * SS, y1 + 70 * SS), FA, 90, fill=YEL, stroke=BLACK, alpha=a_m)
    if a_i > 0 and st("hot") - .2 < t < en("hot") + .3:
        q = pj(cam, *ILI.centroid.coords[0])
        if q:
            ytag(img, q[0], q[1] + 150 * SS, "SICAK SULAR", a_i, 52, bg=HOT)
            hand(img, "yerin altından ısınıyor", W / 2, 1720 * SS, 84, a_i * sine_out((t - st("hot") - .4) / .4), YEL, -5)
    t_y = cue("yinyang", "yin", "yang", "gibi", offset=-.3)
    a_y = vis(t, t_y, en("yinyang") + .2, .3, .4)
    if a_y > 0:
        lay2 = L(); yinyang(ImageDraw.Draw(lay2), W * .78, 1560 * SS, 120 * SS * pop(t, t_y), a_y)
        img.alpha_composite(lay2); hand(img, "yin-yang!", W * .38, 1580 * SS, 110, a_y, YEL, -6)
    if a_a > 0:
        t_ak = cue("active", "aktif", "türkiyenin")
        if t > t_ak: ytag(img, W / 2, 1480 * SS, "TÜRKİYE'NİN EN AKTİF YANARDAĞI", a_a * sine_out((t - t_ak) / .3), 50, bg=LAVA, fg=WHITE)
        t_sp = cue("active", "patlaması", "son")
        if t > t_sp: hand(img, "son patlama: birkaç yüz yıl önce", W / 2, 1670 * SS, 90, a_a * sine_out((t - t_sp) / .4), YEL, -4)

def ui(img, t):
    brand.brand_card(img, t, "VAN GÖLÜ'NÜ", "BİR YANARDAĞ DEĞİŞTİRDİ!", en("intro") - .1)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Yeniden uyanır mı?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 92, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t)
    map_overlays(img, cam, t)
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
