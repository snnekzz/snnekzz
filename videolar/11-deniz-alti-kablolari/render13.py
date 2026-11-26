"""Video 11: Deniz altı internet kabloları. Haritanın Ardı teknikleri: renk=anlam altyazı, canlı sayaç, "?" simgesi,
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

LEAD = 0.05
FC, FP = "caveat.ttf", "playfair.ttf"
BLUE = (37, 99, 235); TURQ = (40, 205, 215); RIVER = (80, 170, 255); PINK = (240, 110, 190)
ORANGE = (255, 150, 40); GREEN = (110, 220, 130); KRED = (229, 36, 59)
LON0, LAT0D = 30.0, 39.0
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
TEX_DET = TEX_BIG
TB = tex_info(20, 52, 29, 49, TEX_BIG); TD = TB
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
K = [(0.0, 34.0, 38.8, 2300, 0, 0), (st("istanbul"), 33.5, 39.2, 2200, 8, 0), (en("istanbul"), 29.0, 39.0, 2300, 10, 0),
     (st("risk") - .4, 28.6, 36.0, 1400, 12, 0), (TOTAL, 28.6, 36.0, 1350, 14, 0)]
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
for k in ("türkiyenin",): ENT[k] = KRED
for k in ("kablo", "kablolardan", "kabloların", "kabloları", "kablolardan"): ENT[k] = (60, 220, 255)
for k in ("uydu",): ENT[k] = WHITE
for k in ("istanbuldan", "marmaris"): ENT[k] = KRED
for k in ("singapurdan", "fransaya"): ENT[k] = (110, 170, 255)
for k in ("hortumu", "bahçe"): ENT[k] = (110, 210, 110)
for k in ("koptuğunda", "yavaşlayabiliyor"): ENT[k] = KRED
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
# ---------- Deniz altı kabloları ----------
import render4 as _R4
_R4.CLOUDT = _R4.CLOUDT * 0.18          # bulutlar seyrek (kablolar net görünsün)
CYAN = (60, 220, 255); GLOW = (150, 245, 255)
SMW5 = [(103.8, 1.3), (95, 5.5), (80.2, 6.0), (72, 9.5), (60, 13.5), (51, 12.5), (45.2, 12.2), (42.0, 15.0), (38.5, 20.0), (34.8, 26.5), (32.6, 29.9),
        (32.3, 31.4), (29.5, 33.4), (28.4, 34.6), (25.0, 34.3), (19.5, 35.2), (15.0, 36.6), (11.5, 38.5), (8.0, 41.0), (5.9, 43.1)]
MARM_BR = [(28.4, 34.6), (28.3, 35.8), (28.27, 36.85)]
KAFOS = [[(29.05, 41.25), (28.9, 42.0), (28.2, 42.8), (27.92, 43.2)], [(29.05, 41.25), (29.4, 42.3), (29.1, 43.4), (28.65, 44.17)]]
MEDN = [[(28.97, 40.98), (27.6, 40.6), (26.6, 40.25), (26.0, 39.6), (25.2, 38.6), (24.2, 37.9), (22.0, 36.9), (20.0, 36.8)],
        [(25.2, 38.6), (27.0, 36.3), (30.5, 35.0), (33.0, 34.7)], [(30.5, 35.0), (33.5, 33.0), (34.8, 32.1)]]
def dens(path, n=20):
    out = []
    for (a0, b0), (a1, b1) in zip(path[:-1], path[1:]):
        for k in range(n): u = k / n; out.append((a0 + (a1 - a0) * u, b0 + (b1 - b0) * u))
    out.append(path[-1]); return out
def gproj(lon, lat, lon0, lat0, R):
    la, lo, la0, lo0 = math.radians(lat), math.radians(lon), math.radians(lat0), math.radians(lon0)
    x = math.cos(la) * math.sin(lo - lo0); y = math.cos(la0) * math.sin(la) - math.sin(la0) * math.cos(la) * math.cos(lo - lo0)
    z = math.sin(la0) * math.sin(la) + math.cos(la0) * math.cos(la) * math.cos(lo - lo0)
    return ((OW / 2 + x * R) * SS, (OH * .47 - y * R) * SS, z > 0)
def gline(d, path, lon0, lat0, R, a, pr=1.0, col=CYAN, w=7, pulses=0, t=0):
    pts = [gproj(lo, la, lon0, lat0, R) for lo, la in dens(path, 24)]
    n = max(2, int(len(pts) * pr))
    seg = []
    for x, y, v in pts[:n]:
        if v: seg.append((x, y))
        elif len(seg) > 1: d.line(seg, fill=A(col, a), width=w * SS, joint="curve"); seg = []
        else: seg = []
    if len(seg) > 1:
        d.line(seg, fill=A(col, a * .35), width=w * 3 * SS, joint="curve"); d.line(seg, fill=A(col, a), width=w * SS, joint="curve")
    for k in range(pulses):
        u = ((t * .35 + k / pulses) % 1) * pr; i = int(u * (len(pts) - 1)); x, y, v = pts[i]
        if v: d.ellipse((x - 11 * SS, y - 11 * SS, x + 11 * SS, y + 11 * SS), fill=A(WHITE, a))
def gpin(img, lon, lat, lon0, lat0, R, a, label, col=KRED, dx=0, dy=-110):
    x, y, v = gproj(lon, lat, lon0, lat0, R)
    if not v or a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay); r = 16 * SS
    d.ellipse((x - r, y - r, x + r, y + r), fill=A(col, a), outline=A(WHITE, a), width=4 * SS); img.alpha_composite(lay)
    ytag(img, x + dx * SS, y + dy * SS, label, a, 42, bg=col, fg=WHITE)
def globe_params(t):
    if t < st("question"):
        p = smooth(t / max(.1, st("question"))); return lerp(24, 30, p), lerp(30, 34, p), lerp(560, 820, p)
    if t < st("world"):
        p = smooth((t - st("marmaris") + .3) / 2.2); return lerp(30, 56, p), lerp(34, 22, p), lerp(820, 470, p)
    if t < st("cta"):
        return 56 + (t - st("world")) * 32, 12, 520
    p = smooth((t - st("cta")) / 1.5); return lerp(56 + (st("cta") - st("world")) * 32, 32, p) % 360, lerp(12, 30, p), lerp(520, 640, p)
def globe_layer(t):
    lon0, lat0, R = globe_params(t)
    img = globe(lon0, lat0, R, t).resize((W, H), Image.BICUBIC).convert("RGBA")
    lay = L(); d = ImageDraw.Draw(lay)
    # açılış: Akdeniz'de veri akışı
    a_i = vis(t, 0.0, st("question") - .2, .3, .4)
    if a_i > 0:
        gline(d, SMW5[9:], lon0, lat0, R, a_i, 1, CYAN, 6, 6, t); gline(d, MARM_BR, lon0, lat0, R, a_i, 1, CYAN, 6, 2, t)
    # Marmaris: Singapur → Fransa
    t_m = cue("marmaris", "kablo", "geçen")
    a_m = vis(t, st("marmaris") - .2, en("marmaris") + .5, .4, .5)
    if a_m > 0:
        pr = smooth((t - t_m) / 2.6)
        gline(d, SMW5, lon0, lat0, R, a_m, pr, CYAN, 7, 5 if pr >= 1 else 0, t)
        gline(d, MARM_BR, lon0, lat0, R, a_m, 1, YEL, 7)
    # 35+ tur: ekvatorda dönen ışık
    t_w = cue("world", "35", "otuz", "dolanırdık")
    a_w = vis(t, st("world") - .2, en("world") + .3, .4, .4)
    if a_w > 0:
        eq = [(lo, 0) for lo in range(-180, 181, 4)]
        gline(d, eq, lon0, lat0, R, a_w * .9, 1, YEL, 5)
        if t > t_w:
            laps = 35 * smooth((t - t_w) / 2.4); lo = (laps * 360) % 360 - 180
            for k in range(8):
                x, y, v = gproj(lo - k * 6, 0, lon0, lat0, R)
                if v: d.ellipse((x - (16 - k) * SS, y - (16 - k) * SS, x + (16 - k) * SS, y + (16 - k) * SS), fill=A(WHITE, a_w * (1 - k / 8)))
    img.alpha_composite(lay)
    if a_m > 0:
        gpin(img, 103.8, 1.3, lon0, lat0, R, a_m * vis(t, t_m, TOTAL, .3, .3), "SİNGAPUR", (60, 140, 255), 0, 90)
        gpin(img, 28.27, 36.85, lon0, lat0, R, a_m * vis(t, st("marmaris"), TOTAL, .3, .3), "MARMARİS", KRED, -40, -110)
        gpin(img, 5.9, 43.1, lon0, lat0, R, a_m * vis(t, t_m + 2.0, TOTAL, .3, .3), "FRANSA", (60, 140, 255), 0, -110)
        t_km = cue("marmaris", "20000", "yirmi", "kilometre")
        ytag(img, W / 2, 1520 * SS, f"{trnum(20000 * smooth((t - t_m) / 2.6))} km", a_m * vis(t, t_m, en("marmaris") + .4, .3, .4), 72, sc=pop(t, t_km))
    if a_w > 0:
        laps = int(35 * smooth((t - t_w) / 2.4)) if t > t_w else 0
        ytag(img, W / 2, 1450 * SS, f"{laps}+ TUR" if laps >= 35 else f"{laps} TUR", a_w * vis(t, t_w, en("world") + .3, .3, .4), 80, sc=pop(t, t_w))
        ytag(img, W / 2, 560 * SS, "1,4 MİLYON KM+ KABLO", a_w * vis(t, st("world") + .2, en("world") + .3, .3, .4), 50, bg=WHITE)
    return img

def flat_overlays(img, cam, fp, t):
    lay = L(); d = ImageDraw.Draw(lay)
    t_i = cue("istanbul", "istanbuldan", "kabloların")
    a_s = vis(t, t_i - .2, en("istanbul") + .3, .3, .4)
    if a_s > 0:
        for k, path in enumerate(KAFOS + MEDN):
            pts = ring_pts(cam, dens(path, 16))
            pp = partial(pts, smooth((t - t_i - k * .15) / 1.2))
            if len(pp) > 1:
                d.line(pp, fill=A(CYAN, a_s * .35), width=22 * SS, joint="curve"); d.line(pp, fill=A(CYAN, a_s), width=8 * SS, joint="curve")
            if len(pp) > 2:
                u = (t * .5 + k * .2) % 1; x, y = pp[int(u * (len(pp) - 1))]; d.ellipse((x - 10 * SS, y - 10 * SS, x + 10 * SS, y + 10 * SS), fill=A(WHITE, a_s))
    # risk: kablo kopar, bölge kararır
    t_r = cue("risk", "koptuğunda", "kablolardan")
    a_r = vis(t, st("risk") - .2, en("risk") + .3, .3, .4)
    if a_r > 0:
        for path in (SMW5[9:17], MARM_BR):
            pts = ring_pts(cam, dens(path, 16))
            if len(pts) > 1: d.line(pts, fill=A(CYAN, a_r), width=8 * SS, joint="curve")
        bp = pj(cam, 28.4, 34.6)
        if bp and t > t_r:
            g = pop(t, t_r); x, y = bp[0], bp[1]
            for k in range(10):
                an = k * .63; d.line([(x, y), (x + math.cos(an) * 70 * SS * g, y + math.sin(an) * 70 * SS * g)], fill=A(YEL, a_r), width=6 * SS)
            dark = smooth((t - t_r - .3) / 1.2)
            dl = Image.new("L", (W // 4, H // 4), 0); ImageDraw.Draw(dl).ellipse(((x - 900 * SS * dark) / 4, (y - 700 * SS * dark) / 4, (x + 900 * SS * dark) / 4, (y + 700 * SS * dark) / 4), fill=int(170 * a_r))
            img.paste((10, 10, 20), (0, 0), dl.filter(ImageFilter.GaussianBlur(30)).resize((W, H), Image.BILINEAR))
    img.alpha_composite(lay)
    if a_s > 0:
        q = pj(cam, 28.97, 41.01)
        if q: ytag(img, q[0], q[1] + 90 * SS, "İSTANBUL", a_s, 52, bg=KRED, fg=WHITE)
        for lab, lo, la in (("BULGARİSTAN", 27.0, 43.0), ("ROMANYA", 28.0, 44.5), ("YUNANİSTAN", 22.5, 38.8), ("KIBRIS · İSRAİL", 34.0, 33.6)):
            qq = pj(cam, lo, la)
            if qq: ytag(img, qq[0], qq[1], lab, a_s * sine_out((t - t_i - .8) / .4), 34, bg=WHITE)
    if a_r > 0 and t > t_r:
        ytag(img, W / 2, 620 * SS, "KOPMA = YAVAŞLAMA", a_r * sine_out((t - t_r - .2) / .3), 58, bg=KRED, fg=WHITE)
    qa = vis(t, cue("question", "nereden", "peki"), en("question") + .1, .3, .3)
    if qa > 0:
        q = pj(cam, 35, 39)
        if q: stamp_text(img, "?", (q[0], q[1] + math.sin(t * 5) * 8 * SS), FA, 260, fill=WHITE, stroke=BLACK, alpha=qa)
    a_tr = vis(t, st("question") - .2, en("question") + .1, .3, .4)
    if a_tr > 0: glow_outline(img, cam, CN["Turkey"], (255, 90, 90), a_tr, fp, 5)

def icons_twist(img, t):
    a = vis(t, st("twist") - .1, en("twist") + .2, .3, .4)
    if a <= 0: return
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 20, int(150 * a))))
    lay = L(); d = ImageDraw.Draw(lay)
    x, y = W * .28, 1050 * SS; s = SS * 1.2 * pop(t, st("twist"))   # uydu
    d.rectangle((x - 40 * s, y - 40 * s, x + 40 * s, y + 40 * s), fill=A((200, 205, 215), a), outline=A(BLACK, a), width=int(3 * s))
    for sg in (-1, 1): d.rectangle((min(x + sg * 50 * s, x + sg * 150 * s), y - 28 * s, max(x + sg * 50 * s, x + sg * 150 * s), y + 28 * s), fill=A((60, 110, 200), a), outline=A(BLACK, a), width=int(3 * s))
    t_k = cue("twist", "kablo")
    if t > t_k:
        for sg in (1, -1): d.line([(x - 120 * SS, y - 120 * SS * sg), (x + 120 * SS, y + 120 * SS * sg)], fill=A(KRED, a), width=18 * SS)
        x2 = W * .72; g = pop(t, t_k)                                       # kablo kesiti mini
        for r, c in ((90, (30, 30, 34)), (70, (160, 165, 175)), (45, (200, 140, 70)), (25, (20, 30, 40))):
            d.ellipse((x2 - r * SS * g, y - r * SS * g, x2 + r * SS * g, y + r * SS * g), fill=A(c, a))
        for k in range(6):
            an = k / 6 * 2 * math.pi; d.ellipse((x2 + math.cos(an) * 12 * SS * g - 5 * SS, y + math.sin(an) * 12 * SS * g - 5 * SS, x2 + math.cos(an) * 12 * SS * g + 5 * SS, y + math.sin(an) * 12 * SS * g + 5 * SS), fill=A(GLOW, a))
    img.alpha_composite(lay)
    ytag(img, W * .28, 1260 * SS, "UYDU", a, 44, bg=WHITE)
    if t > t_k: ytag(img, W * .72, 1260 * SS, "KABLO", a, 44, bg=CYAN)
    t_99 = cue("twist", "99", "doksan", "yüzde")
    a99 = vis(t, t_99, en("twist") + .2, .3, .4) * a
    if a99 > 0: stamp_text(img, f"%{int(round(99 * smooth((t - t_99) / 1.0)))}", (W / 2, 700 * SS), FA, 220, fill=YEL, stroke=BLACK, alpha=a99)

def hose_scene(img, t):
    a = vis(t, st("hose") - .2, en("hose") + .2, .5, .5)
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(0, H, 10):
        u = yy / H; d.rectangle((0, yy, W, yy + 10), fill=tuple(int(lerp(p, q, u)) for p, q in zip((20, 60, 110), (2, 8, 20))) + (255,))
    r0 = random.Random(4)
    for _ in range(80):
        x, y, r = r0.uniform(0, W), (r0.uniform(0, H) - t * 60 * SS) % H, r0.uniform(2, 6) * SS
        d.ellipse((x - r, y - r, x + r, y + r), fill=(200, 230, 255, 60))
    cx, cy = W * .29, 1100 * SS; g = smooth((t - st("hose") + .2) / .8)
    layers = [(300, (25, 25, 28), "polietilen"), (250, (120, 125, 135), "çelik teller"), (180, (190, 120, 60), "bakır"), (120, (40, 45, 60), "dolgu"), (60, (230, 240, 255), "fiber")]
    for r, c, _ in layers:
        d.ellipse((cx - r * SS * g * .7, cy - r * SS * g * .7, cx + r * SS * g * .7, cy + r * SS * g * .7), fill=c + (255,), outline=(0, 0, 0, 255), width=3 * SS)
    for k in range(28):
        an = k / 28 * 2 * math.pi; rr = 215 * SS * g * .7
        d.ellipse((cx + math.cos(an) * rr - 16 * SS * g * .7, cy + math.sin(an) * rr - 16 * SS * g * .7, cx + math.cos(an) * rr + 16 * SS * g * .7, cy + math.sin(an) * rr + 16 * SS * g * .7), fill=(170, 175, 185, 255))
    for k in range(8):
        an = k / 8 * 2 * math.pi
        d.ellipse((cx + math.cos(an) * 30 * SS * g * .7 - 9 * SS, cy + math.sin(an) * 30 * SS * g * .7 - 9 * SS, cx + math.cos(an) * 30 * SS * g * .7 + 9 * SS, cy + math.sin(an) * 30 * SS * g * .7 + 9 * SS), fill=GLOW + (255,))
    t_h = cue("hose", "hortumu", "bahçe")
    if t > t_h:
        hx, gg = W * .73, pop(t, t_h)
        d.ellipse((hx - 280 * SS * gg * .7, cy - 280 * SS * gg * .7, hx + 280 * SS * gg * .7, cy + 280 * SS * gg * .7), fill=(40, 170, 70, 255), outline=(10, 60, 20, 255), width=6 * SS)
        d.ellipse((hx - 215 * SS * gg * .7, cy - 215 * SS * gg * .7, hx + 215 * SS * gg * .7, cy + 215 * SS * gg * .7), fill=(10, 20, 30, 255))
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    ytag(img, cx, cy + 380 * SS, "DENİZ ALTI KABLOSU", a * g, 44, bg=CYAN)
    ytag(img, cx, cy - 380 * SS, "IŞIK = VERİ (fiber)", a * vis(t, st("hose") + .5, en("hose") + .2, .3, .4), 40, bg=WHITE)
    if t > t_h:
        ytag(img, W * .76, cy + 380 * SS, "BAHÇE HORTUMU", a, 44, bg=(40, 170, 70), fg=WHITE)
        hand(img, "neredeyse aynı!", W * .55, cy - 470 * SS, 84, a * sine_out((t - t_h - .3) / .4), YEL, -6)

def ui(img, t):
    brand.brand_card(img, t, "İNTERNET UYDUDAN", "GELMİYOR!", en("intro") - .1)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Uydu mu, kablo mu?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 86, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    gw = max(vis(t, -1, st("question") - .2, .1, .5), vis(t, st("marmaris") - .3, en("world") + .1, .5, .5), vis(t, st("cta") - .2, TOTAL + 1, .5, .1))
    img = None
    if gw < .999:
        cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g); flat_overlays(img, cam, fp, t)
    if gw > .001:
        gi = globe_layer(t); img = gi if img is None else Image.blend(img, gi, gw)
    icons_twist(img, t)
    hose_scene(img, t)
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
