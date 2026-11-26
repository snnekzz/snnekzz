"""Video 12: İstanbul Boğazı – deniz aynı anda iki ters yöne akıyor.
Haritanın Ardı teknikleri: renk=anlam altyazı (açık mavi = Karadeniz suyu / yüzey, turuncu = tuzlu Akdeniz suyu / dip),
canlı akıntı parçacıkları, "?" simgesi, kesit animasyonu (yoğunluk akıntısı), canlı sayaç, ~1 sn'de bir görsel olay.
Kıyı çizgisi AWS terrarium z12 verisinden (ist_tex.py). Kesit ve deniz altı nehri güzergâhı temsilîdir."""
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
LIGHT = (120, 205, 245)        # Karadeniz suyu / yüzey akıntısı
SALT = (255, 150, 40)          # tuzlu Akdeniz suyu / dip akıntısı
DENSE = (28, 58, 128); LIGHTW = (92, 182, 228); NAVY = (8, 16, 32)
LON0, LAT0D = 30.0, 39.0
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
CN = {}                         # maplib_src beklentisi (bu videoda ülke poligonu kullanılmıyor)

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
import ist_tex
IB = ist_tex.B
TEX, _E = ist_tex.build()
TB = tex_info(*IB, TEX); TD = TB
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

# Boğaz orta hattı (güney → kuzey), veriden çıkarıldı + yumuşatıldı
_raw = json.load(open("bogaz_hat.json"))
_raw = [(28.985, 40.995)] + [p for p in _raw if p[1] > 41.02] + [(29.14, 41.235)]
def _smooth_line(pts, k=2):
    out = []
    for i in range(len(pts)):
        a, b = max(0, i - k), min(len(pts), i + k + 1)
        out.append((sum(p[0] for p in pts[a:b]) / (b - a), sum(p[1] for p in pts[a:b]) / (b - a)))
    return out
HAT = _smooth_line(_raw)
def dens(path, n=8):
    out = []
    for (a0, b0), (a1, b1) in zip(path[:-1], path[1:]):
        for k in range(n): u = k / n; out.append((a0 + (a1 - a0) * u, b0 + (b1 - b0) * u))
    out.append(path[-1]); return out
HATD = dens(HAT, 6)
# deniz altı nehri (temsilî güzergâh, Boğaz'ın Karadeniz çıkışından ~60 km kuzeye)
def _chaikin(p, n=3):
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]): q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        p = q + [p[-1]]
    return p
NEHIR = dens(_chaikin([(29.135, 41.228), (29.155, 41.28), (29.14, 41.34), (29.18, 41.41), (29.165, 41.48), (29.21, 41.55), (29.235, 41.63), (29.26, 41.70)]), 3)

# ---------- kamera ----------
def K_():
    t_n = cue("river", "nehir", "altmış", "dibinde")
    return [(0.0, 29.05, 41.10, 52, 0, 0), (st("twist"), 29.05, 41.11, 46, 14, 0), (en("question"), 29.06, 41.12, 50, 16, 0),
            (st("river") - .2, 29.10, 41.20, 60, 12, 0), (t_n, 29.18, 41.43, 105, 26, 0), (en("river"), 29.18, 41.45, 108, 28, 0),
            (st("cta"), 29.10, 41.25, 95, 18, 0), (TOTAL, 29.10, 41.25, 92, 18, 0)]
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

# renk = anlam: kelime → ekrandaki rengi
ENT = {}
for k in ("yüzeyde", "karadenizden", "karadenize", "nehirler", "yüzeydeki", "suyunu"): ENT[k] = LIGHT
for k in ("derinlerde", "ters", "tersi", "tuz", "tuzlu", "akdenizden", "marmaradan", "tabandan", "dibe", "ağır", "alt"): ENT[k] = SALT
for k in ("boğazında", "boğazda"): ENT[k] = WHITE
for k in ("nehir", "dibinde"): ENT[k] = SALT
for k in ("ren", "nehrinin"): ENT[k] = (110, 170, 255)
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

# ---------- harita katmanı ----------
def scr_line(cam, pts):
    out = []
    for lon, lat in pts:
        q = pj(cam, lon, lat)
        if q: out.append((q[0], q[1]))
    return out
def flow_particles(d, line, t, a, col, speed, n, rev=False, r=7, tail=10, phase=0.):
    """line boyunca akan parçacıklar (rev=True: sondan başa)"""
    if len(line) < 2 or a <= 0: return
    L_ = len(line) - 1
    for k in range(n):
        u = (k / n + t * speed + phase) % 1.0
        if rev: u = 1 - u
        i = u * L_; i0 = int(i); fr = i - i0
        if i0 >= L_: continue
        x = line[i0][0] + (line[i0 + 1][0] - line[i0][0]) * fr; y = line[i0][1] + (line[i0 + 1][1] - line[i0][1]) * fr
        j = max(0, min(L_, int(i + (tail if rev else -tail)))); tx, ty = line[j]
        edge = min(1, u * 8, (1 - u) * 8)
        d.line([(tx, ty), (x, y)], fill=A(col, a * .35 * edge), width=int(r * SS * .9))
        d.ellipse((x - r * SS, y - r * SS, x + r * SS, y + r * SS), fill=A(col, a * edge))
def offset_line(line, off):
    out = []
    for i in range(len(line)):
        a, b = line[max(0, i - 1)], line[min(len(line) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
        out.append((line[i][0] - dy / n * off, line[i][1] + dx / n * off))
    return out

def map_overlays(img, cam, t):
    lay = L(); d = ImageDraw.Draw(lay)
    line = scr_line(cam, HATD)
    # yüzey: güneye (hat güney→kuzey olduğu için rev=True)
    a_s = max(vis(t, .1, en("question") + .2, .5, .5), vis(t, st("cta"), TOTAL, .5, .3))
    flow_particles(d, line, t, a_s, LIGHT, .11, 22, rev=True, r=15, tail=14)
    # dip: kuzeye, turuncu, biraz yana kaydırılmış ve kesik çizgi
    t_d = cue("twist", "derinlerde", "ama")
    a_d = max(vis(t, t_d, en("question") + .2, .4, .5), vis(t, st("cta"), TOTAL, .5, .3))
    if a_d > 0:
        lo = offset_line(line, 12 * SS)
        d.line(lo, fill=A(SALT, a_d * .22), width=int(26 * SS), joint="curve")
        for i in range(0, len(lo) - 1, 3): d.line([lo[i], lo[min(len(lo) - 1, i + 2)]], fill=A(SALT, a_d * .6), width=int(8 * SS))
        flow_particles(d, lo, t, a_d, SALT, .09, 18, rev=False, r=13, tail=12, phase=.37)
    # deniz altı nehri
    t_n = cue("river", "girince", "durmuyor")
    a_n = vis(t, st("river") - .1, en("river") + .3, .5, .5)
    if a_n > 0:
        dark = Image.new("RGBA", (W, H), (4, 10, 30, int(120 * smooth((t - st("river")) / 1.0) * a_n)))
        img.alpha_composite(dark)
        rl = scr_line(cam, NEHIR); pr = smooth((t - t_n) / 2.6); pp = partial(rl, pr) if len(rl) > 1 else []
        if len(pp) > 1:
            d.line(pp, fill=A(SALT, a_n * .25), width=int(46 * SS), joint="curve")
            d.line(pp, fill=A(SALT, a_n * .55), width=int(24 * SS), joint="curve")
            d.line(pp, fill=A((255, 215, 150), a_n), width=int(9 * SS), joint="curve")
            flow_particles(d, pp, t, a_n * .9, (255, 240, 210), .16, 14, r=6)
    img.alpha_composite(lay)
    # yer etiketleri
    a_l = max(vis(t, .3, en("question") + .1, .5, .4), vis(t, st("river"), en("river") + .2, .5, .4))
    for text, lon, lat, bg in (("KARADENİZ", 29.26, 41.30, LIGHT), ("MARMARA", 28.93, 40.955, SALT)):
        q = pj(cam, lon, lat)
        if q and -200 * SS < q[1] < H + 200 * SS: ytag(img, q[0], min(max(q[1], 520 * SS), H - 260 * SS), text, a_l, 46, bg=bg)
    q = pj(cam, 29.06, 41.09)
    if q: hand(img, "İstanbul Boğazı", q[0] + 270 * SS, q[1] + 60 * SS, 76, vis(t, .6, en("intro") + .2, .5, .4), WHITE, 6)
    # twist etiketleri
    a_t = vis(t, st("twist"), en("question") + .1, .4, .4)
    if a_t > 0:
        q = pj(cam, 29.10, 41.15)
        if q: ytag(img, q[0] + 120 * SS, q[1], "YÜZEY ↓ GÜNEYE", a_t, 46, bg=LIGHT)
        if t > t_d:
            q = pj(cam, 29.0, 41.04)
            if q: ytag(img, q[0] - 60 * SS, q[1] + 160 * SS, "DİP ↑ KUZEYE", a_t * sine_out((t - t_d) / .3), 46, bg=SALT)
    # soru
    qa = vis(t, cue("question", "nasıl", "peki"), en("question") + .1, .3, .3)
    if qa > 0:
        q = pj(cam, 29.06, 41.10)
        if q: stamp_text(img, "?", (q[0] + 200 * SS, q[1] + math.sin(t * 5) * 8 * SS), FA, 260, fill=WHITE, stroke=BLACK, alpha=qa)
    # nehir etiketleri
    if a_n > 0 and t > t_n:
        q = pj(cam, *NEHIR[len(NEHIR) // 2])
        if q: typetag(img, q[0] + 300 * SS, q[1], "DENİZ ALTI NEHRİ", t, t_n + .2, a_n, 50, bg=SALT)
        km = 60 * smooth((t - t_n) / 2.6)
        stamp_text(img, f"{int(round(km))} KM", (W * .30, 1020 * SS), FA, 150, fill=YEL, stroke=BLACK, alpha=vis(t, t_n, en("river") - .2, .4, .2))
        q = pj(cam, 29.135, 41.228)
        if q: ytag(img, q[0] - 150 * SS, q[1] + 90 * SS, "BOĞAZ ÇIKIŞI", a_n, 36, bg=WHITE)

# ---------- kesit sahnesi (tuz → katmanlar → ağ) ----------
YS, YI = 900 * SS, 1210 * SS            # yüzey, ara yüz
def ybot(x): return 1640 * SS - 70 * SS * math.exp(-((x / W - .22) / .09) ** 2) + 12 * SS * math.sin(x / W * 9)
def chevron(d, x, y, s, a, col, right=True):
    k = 1 if right else -1
    d.line([(x - 14 * s * k, y - 16 * s), (x + 6 * s * k, y), (x - 14 * s * k, y + 16 * s)], fill=A(col, a), width=int(5 * s), joint="curve")
def boat(d, x, y, s, a):
    c = A((150, 92, 52), a); o = A((60, 35, 20), a)
    d.polygon([(x - 120 * s, y - 30 * s), (x + 120 * s, y - 30 * s), (x + 90 * s, y + 22 * s), (x - 95 * s, y + 22 * s)], fill=c, outline=o)
    d.rectangle((x - 30 * s, y - 90 * s, x + 40 * s, y - 30 * s), fill=A((235, 235, 230), a), outline=o, width=int(3 * s))
    d.line([(x + 70 * s, y - 30 * s), (x + 70 * s, y - 150 * s)], fill=o, width=int(5 * s))
def xsec(img, t):
    a = vis(t, st("salt") - .25, en("nets") + .2, .5, .5)
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(0, H, 10):                              # gökyüzü → gece mavisi
        u = yy / H; d.rectangle((0, yy, W, yy + 10), fill=tuple(int(lerp(p, q, u)) for p, q in zip((30, 44, 80), (6, 10, 22))) + (255,))
    xs = np.linspace(0, W, 80)
    bot = [(x, ybot(x)) for x in xs]
    d.polygon([(0, YS)] + [(W, YS)] + bot[::-1], fill=LIGHTW + (255,))
    # yoğun (tuzlu) su: önce sağ yarıda dikey, sonra altına kayıp katman olur
    t_l = cue("layers", "ağır", "tuzlu")
    p = smooth((t - t_l) / 2.4)
    xf = lerp(W * .5, -W * .15, p); ytop_r = lerp(YS, YI, p); nose = W * .13
    top = []
    for x in xs[::-1]:
        if x >= W * .5: y = ytop_r
        elif x >= xf:
            dd = (x - xf) / nose; y = lerp(ybot(x), ytop_r, 1 - (1 - min(1, dd)) ** 2)
        else: y = ybot(x)
        y += 6 * SS * math.sin(x / W * 14 + t * 2) * p
        top.append((x, min(y, ybot(x))))
    d.polygon(top + bot, fill=DENSE + (255,))
    base = lay; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)   # yarı saydam öğeler ayrı katmanda
    rr = random.Random(3)                                   # tuz taneleri
    for _ in range(140):
        x = rr.uniform(0, W); yb = ybot(x); ty = None
        for (tx_, tyy) in top:
            if abs(tx_ - x) < W / 80: ty = tyy; break
        if ty is None or ty >= yb - 10: continue
        y = rr.uniform(ty + 10 * SS, yb - 10 * SS); s = rr.uniform(3, 6) * SS
        d.rectangle((x - s, y - s, x + s, y + s), fill=(255, 255, 255, 120))
    base.alpha_composite(lay); lay = base; d = ImageDraw.Draw(lay)
    d.polygon(bot + [(W, H), (0, H)], fill=(70, 52, 34, 255))       # taban
    d.line(bot, fill=(40, 28, 18, 255), width=int(6 * SS))
    d.line([(0, YS), (W, YS)], fill=(200, 235, 255, 255), width=int(4 * SS))
    base = lay; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # nehirler (tuz sahnesi): Karadeniz'e tatlı su
    a_r = vis(t, cue("salt", "nehirler", "karadenize"), en("salt") + .2, .4, .4)
    if a_r > 0:
        for k, x0 in enumerate((W * .30, W * .37, W * .44)):
            pts = [(x0 + 20 * SS * math.sin((yy / SS) / 40 + t * 6 + k), yy) for yy in range(int(620 * SS), int(YS), int(12 * SS))]
            if len(pts) > 1: d.line(pts, fill=A((150, 225, 255), a_r), width=int(14 * SS), joint="curve")
    # akıntı okları (katmanlaşınca)
    a_f = clamp01((p - .55) / .3) * vis(t, st("layers"), en("nets") + .2, .3, .3)
    if a_f > 0:
        for row, (y, col, right, sp) in enumerate(((lerp(YS, YI, .5), WHITE, True, 140), (lerp(YI, 1560 * SS, .45), SALT, False, 110))):
            for k in range(7):
                ph = (t * sp * SS / W * 2.2 + k / 7) % 1
                x = (ph if right else 1 - ph) * W
                chevron(d, x, y, SS * 1.3, a_f * min(1, ph * 6, (1 - ph) * 6), col, right)
    # ağ sahnesi: tekne ağı dibe sarkıtıyor, akıntıya karşı sürükleniyor
    a_n = vis(t, st("nets") - .1, en("nets") + .2, .4, .4)
    t_net = cue("nets", "sarkıttığında", "derine")
    if a_n > 0:
        drift = smooth((t - t_net - .6) / 3.5); bx = lerp(W * .66, W * .40, drift); by = YS + 4 * SS * math.sin(t * 3)
        boat(d, bx, by, SS * 1.15, a_n)
        g = smooth((t - t_net) / 1.0); ny = lerp(YS + 20 * SS, YI + 180 * SS, g); lag = 70 * SS * drift + 40 * SS
        d.line([(bx - 80 * SS, by), (bx - 80 * SS - lag, ny)], fill=A((230, 230, 220), a_n), width=int(4 * SS))
        if g > .3:
            nx = bx - 80 * SS - lag; w_ = 140 * SS
            net = [(nx - w_ / 2, ny), (nx + w_ / 2, ny), (nx + w_ / 2 - 20 * SS, ny + 140 * SS * g), (nx - w_ / 2 - 30 * SS, ny + 150 * SS * g)]
            d.polygon(net, outline=A((240, 240, 230), a_n), fill=A((240, 240, 230), a_n * .15))
            for k in range(1, 6):
                u = k / 6; d.line([(lerp(net[0][0], net[1][0], u), ny), (lerp(net[3][0], net[2][0], u), ny + 145 * SS * g)], fill=A((240, 240, 230), a_n * .6), width=int(2 * SS))
    base.alpha_composite(lay); lay = base
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    # etiketler
    ytag(img, W * .14, YS - 90 * SS, "KARADENİZ", a, 44, bg=LIGHT)
    ytag(img, W * .86, YS - 90 * SS, "MARMARA", a, 44, bg=SALT)
    a_s = a * vis(t, st("salt") + .3, st("layers") + .8, .4, .4)
    ytag(img, W * .25, YS + 160 * SS, "AZ TUZLU", a_s, 50, bg=LIGHT)
    ytag(img, W * .75, YS + 160 * SS, "ÇOK TUZLU", a_s, 50, bg=SALT)
    if a_r > 0: ytag(img, W * .37, 580 * SS, "NEHİRLER", a * a_r, 40, bg=WHITE)
    a_h = a * vis(t, t_l + .3, en("layers") + .2, .3, .4)
    if a_h > 0: hand(img, "ağır su dibe çöker", W * .5, 1760 * SS, 84, a_h, YEL, -4)
    a_m = a * clamp01((p - .7) / .3) * vis(t, st("layers"), en("nets") + .2, .3, .3)
    if a_m > 0:
        d2 = ImageDraw.Draw(img); x = W - 70 * SS
        d2.line([(x, YS + 10 * SS), (x, YI)], fill=A(YEL, a_m), width=int(5 * SS))
        for yy in (YS + 10 * SS, YI): d2.line([(x - 20 * SS, yy), (x + 20 * SS, yy)], fill=A(YEL, a_m), width=int(5 * SS))
        ytag(img, x - 110 * SS, lerp(YS, YI, .5), "~25 m", a_m, 40, bg=YEL)
    if a_n > 0 and t > t_net + 1.0:
        hand(img, "akıntıya karşı!", W * .45, YS - 260 * SS, 92, a_n * sine_out((t - t_net - 1.0) / .4), YEL, -6)

# ---------- büyüklük sahnesi (sayaç + Ren karşılaştırması) ----------
def size_scene(img, t):
    a = vis(t, st("size") - .2, en("size") + .3, .4, .4)
    if a <= 0: return
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 24, int(205 * a))))
    v = 22000 * smooth((t - st("size")) / 1.4)
    stamp_text(img, trnum(v), (W / 2, 820 * SS), FA, 210, fill=YEL, stroke=BLACK, alpha=a * clamp01((t - st("size") + .05) / .25))
    stamp_text(img, "m³ / saniye", (W / 2, 1000 * SS), FA, 70, fill=WHITE, stroke=BLACK, alpha=a * clamp01((t - st("size") + .05) / .25))
    t_r = cue("size", "ren")
    a_b = a * vis(t, t_r - .1, en("size") + .3, .3, .4)
    if a_b > 0:
        d = ImageDraw.Draw(img); x0 = 140 * SS; unit = (W - 280 * SS) / 10
        d.rectangle((x0, 1250 * SS, x0 + unit * smooth((t - t_r) / .5), 1340 * SS), fill=A((110, 170, 255), a_b), outline=A(BLACK, a_b), width=int(4 * SS))
        ytag(img, x0 + 160 * SS, 1200 * SS, "REN NEHRİ", a_b, 40, bg=(110, 170, 255))
        g = smooth((t - t_r - .35) / .7)
        d.rectangle((x0, 1440 * SS, x0 + unit * 10 * g, 1530 * SS), fill=A(SALT, a_b), outline=A(BLACK, a_b), width=int(4 * SS))
        for k in range(1, 10):
            if unit * k < unit * 10 * g: d.line([(x0 + unit * k, 1440 * SS), (x0 + unit * k, 1530 * SS)], fill=A(BLACK, a_b * .5), width=int(3 * SS))
        ytag(img, x0 + 230 * SS, 1390 * SS, "DENİZ ALTI NEHRİ", a_b, 40, bg=SALT)
        t_10 = max(cue("size", "katı", offset=-.15), t_r + 1.05)
        if t > t_10: stamp_text(img, "10 KATI!", (W / 2, 1700 * SS), FA, 170, fill=YEL, stroke=BLACK, alpha=a_b * sine_out((t - t_10) / .3), scale=pop(t, t_10))

def ui(img, t):
    brand.brand_card(img, t, "BOĞAZ'DA DENİZ", "İKİ YÖNE AKIYOR!", en("intro") - .1)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Denizin dibinde ne var?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 86, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t)
    map_overlays(img, cam, t)
    xsec(img, t)
    size_scene(img, t)
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
