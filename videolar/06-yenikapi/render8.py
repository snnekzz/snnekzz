"""Video 6: Yenikapı – Marmaray kazısı. Yumuşak geçişler (zoom blur yok, süzülerek gelen öğeler),
kelime tetiklemeli animasyonlar, kazı kesiti + yıl sayacı."""
import json, math, os, random, re, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import shape, box, Polygon
import render as R
from render import stamp_text, pill, partial, prog, FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys, tr_up
from render3 import A, L, RED, WHITE, YEL, BLACK, VIG, clamp01
from render4 import globe, sample, EARTH, fractal, Cam, persp_coeffs
import brand

FC, FP = "caveat.ttf", "playfair.ttf"
BLUE = (37, 99, 235); GOLD = (255, 200, 80)
LON0, LAT0D = 28.97, 41.01
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)
G = json.load(open("countries10_tr.json"))
CN = {f["properties"]["name"]: shape(f["geometry"]).buffer(0).intersection(box(20, 34, 46, 44)) for f in G["features"]}
YENIKAPI = (28.951, 41.004)
MARMARAY = [(28.92, 40.99), (28.951, 41.004), (28.977, 41.015), (29.0, 41.022), (29.015, 41.026), (29.03, 41.0)]

# ---------- yumuşak zamanlama yardımcıları ----------
def smooth(x): x = clamp01(x); return x * x * x * (x * (6 * x - 15) + 10)       # smootherstep
def sine_out(x): x = clamp01(x); return math.sin(x * math.pi / 2)
def vis(t, t0, t1, fi=.45, fo=.45):
    if t < t0 or t > t1 + fo: return 0.
    return min(sine_out((t - t0) / fi), 1 - smooth((t - t1) / fo))
def rise(t, t0, d=.5): return (1 - sine_out((t - t0) / d)) * 40 * SS      # süzülerek yükselme ofseti
# ---------- kelime tetikleyici ----------
WORDS = json.load(open("words.json")) if os.path.exists("words.json") else []
def _n(w): return re.sub(r"[^\wçğıöşü]", "", w.replace("İ", "i").replace("I", "ı").lower())
def cue(scene, *needles, offset=0.0):
    """sahne içinde ilk eşleşen kelimenin söylendiği an (Whisper); yoksa sahne başı"""
    t0, t1 = st(scene) - .3, en(scene) + .3
    for w in WORDS:
        tw = w["s"] + 0.4
        if t0 <= tw <= t1 and any(_n(nd) in _n(w["w"]) for nd in needles): return tw + offset
    return st(scene) + offset

exec(open("maplib_src.py").read())
TEX_BIG = build_tex(20, 40, 34, 46, 4096, 3, "tex_big.png")
TEX_DET = build_tex(28.2, 29.8, 40.6, 41.5, 4096, 5, "tex_det.png")
TB = tex_info(20, 40, 34, 46, TEX_BIG); TD = tex_info(28.2, 29.8, 40.6, 41.5, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
T_GLOBE = 2.2
K = [(T_GLOBE - .3, 29.0, 41.0, 1600, 0, 0), (st("intro") + 3.3, 28.98, 41.02, 120, 30, 0),
     (st("dig") + .5, 28.97, 41.01, 60, 38, 0), (st("harbor") - .2, 28.951, 41.004, 22, 50, 0),
     (st("delay") - .3, 28.975, 41.012, 70, 34, 0), (st("cta") + .6, 28.98, 41.02, 140, 28, 0), (TOTAL, 28.98, 41.02, 160, 26, 0)]
def cam_at(t):
    if t <= K[0][0]: a = b = K[0]; p = 0
    elif t >= K[-1][0]: a = b = K[-1]; p = 0
    else:
        for a, b in zip(K[:-1], K[1:]):
            if a[0] <= t <= b[0]:
                p = smooth((t - a[0]) / (b[0] - a[0])); break
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
def serif(img, text, x, y, size, a, col=GOLD):
    if a > .01: stamp_text(img, text, (x, y), FP, size, fill=col, stroke=BLACK, alpha=a)
def big(img, text, x, y, size, a, col=YEL):
    if a > .01: stamp_text(img, text, (x, y), FA, size, fill=col, stroke=BLACK, alpha=a)
def ytag(img, x, y, text, a, size=44, bg=YEL, fg=BLACK):
    if a <= .01: return
    f = font(FA, size * SS); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 30 * SS, b - t_ + 22 * SS
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((14, 14, w + 14, h + 14), fill=(0, 0, 0, int(100 * a))); d.rectangle((8, 8, w + 8, h + 8), fill=A(bg, a))
    d.text((8 + w / 2, 8 + h / 2), text, font=f, fill=A(fg, a), anchor="mm")
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
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
        if i == cur:
            d.rounded_rectangle((x - 12 * SS, y - size * .62, x + ws[i] + 12 * SS, y + size * .58), radius=int(10 * SS), fill=BLUE + (255,))
            d.text((x, y), w, font=f, fill=WHITE, anchor="lm")
        else:
            d.text((x, y), w, font=f, fill=WHITE, anchor="lm", stroke_width=int(size / 9), stroke_fill=(0, 0, 0, 220))
        x += ws[i] + sp
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, int(330 * SS - size * 1.1)))

# ---------- kazı kesiti (ekran illüstrasyonu) ----------
LAYERS = [  # (üst derinlik, alt derinlik, renk, ad) – derinlik birimi: ekran pikseli (SS)
    (0, 900, None, "şehir"), (900, 960, (60, 60, 64), "asfalt"), (960, 2300, (122, 92, 62), "toprak"),
    (2300, 4200, (70, 78, 82), "liman çamuru"), (4200, 6000, (138, 96, 66), "kil"), (6000, 8000, (80, 70, 64), "kaya")]
rnd = random.Random(3)
STONES = [(rnd.uniform(0, W), rnd.uniform(960, 8000), rnd.uniform(6, 22)) for _ in range(420)]
SHIPS = [(rnd.uniform(.10, .90) * W, rnd.uniform(2450, 4150), rnd.uniform(.40, .75), rnd.uniform(-.25, .25)) for _ in range(37)]
SHIPS.sort(key=lambda s: s[1])
STEPS = [(W * .30 + k * 70 * SS, 5200 - k * 30 + (k % 2) * 60, k % 2) for k in range(9)]
def depth_at(t):
    """kesitte görüş penceresinin üst derinliği (yumuşak iniş)"""
    keys = [(st("harbor") - .1, 0), (st("harbor") + 1.6, 1700), (cue("ships", "37", "otuz") + .2, 2100),
            (st("deeper") + .2, 2400), (cue("footprints", "ayak", "izleri") - .4, 4300), (en("footprints"), 4400)]
    if t <= keys[0][0]: return keys[0][1]
    for (t0, d0), (t1, d1) in zip(keys[:-1], keys[1:]):
        if t <= t1: return lerp(d0, d1, smooth((t - t0) / max(.01, t1 - t0)))
    return keys[-1][1]
def year_at(depth):
    pts = [(0, 2004), (900, 1900), (1700, 1453), (2600, 600), (3600, 400), (4300, -6000)]
    for (d0, y0), (d1, y1) in zip(pts[:-1], pts[1:]):
        if depth <= d1: return lerp(y0, y1, (depth - d0) / (d1 - d0))
    return -6000
def byz_ship(d, x, y, s, a, rot=0.0):
    s *= SS; c = A((96, 66, 40), a); o = A((40, 26, 16), a)
    pts = [(-120, -10), (-100, 20), (-40, 34), (40, 34), (100, 20), (124, -14), (90, 0), (-90, 0)]
    cr, sr = math.cos(rot), math.sin(rot)
    P = [(x + (px * cr - py * sr) * s, y + (px * sr + py * cr) * s) for px, py in pts]
    d.polygon(P, fill=c, outline=o)
    for k in range(-80, 100, 26):
        p0 = (x + (k * cr - 2 * sr) * s, y + (k * sr + 2 * cr) * s); p1 = (x + (k * cr - 30 * sr) * s, y + (k * sr + 30 * cr) * s)
        d.line([p0, p1], fill=o, width=max(1, int(3 * s)))
    m0 = (x + (-10 * cr + 0 * sr) * s, y + (-10 * sr - 0 * cr) * s); m1 = (x + (-10 * cr + 70 * sr) * s, y + (-10 * sr - 70 * cr) * s)
    d.line([m0, m1], fill=o, width=max(1, int(5 * s)))
def amphora(d, x, y, s, a):
    s *= SS; c = A((190, 110, 70), a); o = A((90, 50, 30), a)
    d.ellipse((x - 14 * s, y - 20 * s, x + 14 * s, y + 18 * s), fill=c, outline=o)
    d.rectangle((x - 5 * s, y - 34 * s, x + 5 * s, y - 18 * s), fill=c, outline=o)
    d.polygon([(x - 6 * s, y + 16 * s), (x + 6 * s, y + 16 * s), (x, y + 30 * s)], fill=c, outline=o)
def foot(d, x, y, s, a, left):
    s *= SS; c = A((40, 28, 22), a); m = -1 if left else 1
    d.ellipse((x - 16 * s, y - 34 * s, x + 16 * s, y + 30 * s), fill=c)
    for k, (dx, dy, r) in enumerate([(-12, -46, 7), (-3, -50, 6), (6, -49, 5.5), (13, -45, 5), (18, -39, 4.5)]):
        d.ellipse((x + m * dx * s - r * s, y + dy * s - r * s, x + m * dx * s + r * s, y + dy * s + r * s), fill=c)
def section(img, t, a):
    top = depth_at(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for d0, d1, col, name in LAYERS:
        y0, y1 = d0 - top + 600 * SS, d1 - top + 600 * SS
        if y1 < 0 or y0 > H: continue
        if col is None:
            d.rectangle((0, y0, W, y1), fill=(150, 185, 215, 255))
            for k in range(14):    # şehir silüeti
                bx = k * W / 14; bh = (120 + (k * 53) % 260) * SS
                d.rectangle((bx + 6 * SS, y1 - bh, bx + W / 14 - 6 * SS, y1), fill=(70, 80, 98, 255))
            d.ellipse((W * .6, y1 - 420 * SS, W * .6 + 140 * SS, y1 - 280 * SS), fill=(70, 80, 98, 255))   # kubbe
            d.rectangle((W * .6 + 60 * SS, y1 - 520 * SS, W * .6 + 76 * SS, y1 - 340 * SS), fill=(70, 80, 98, 255))
        else:
            d.rectangle((0, y0, W, y1), fill=col + (255,))
            d.line([(0, y0), (W, y0)], fill=(30, 22, 16, 160), width=3 * SS)
    sl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sl)
    for sx, sy, r in STONES:
        y = sy - top + 600 * SS
        if 0 <= y <= H: ds.ellipse((sx - r * SS / 2, y - r * SS / 3, sx + r * SS / 2, y + r * SS / 3), fill=(40, 32, 26, 90))
    lay.alpha_composite(sl); d = ImageDraw.Draw(lay)
    # kazı çukuru (kepçe ile açılan yol)
    pit = 600 * SS - top
    pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pl).polygon([(W * .42, max(0, pit + 900)), (W * .58, max(0, pit + 900)), (W * .60, H), (W * .40, H)], fill=(0, 0, 0, 55))
    lay.alpha_composite(pl); d = ImageDraw.Draw(lay)
    # gemiler (kelimeyle birer birer)
    t_sh = cue("ships", "37", "otuz", "batık")
    n_sh = int(37 * smooth((t - t_sh) / 2.2)) if t > t_sh else 0
    for k in range(n_sh):
        x, dy, s, rot = SHIPS[k]; y = dy - top + 600 * SS
        if -200 < y < H + 200: byz_ship(d, x, y, s, a * min(1, (t - t_sh - k * 2.2 / 37) / .3 + .2), rot)
    # amforalar (yük)
    t_cg = cue("cargo", "yükü", "yük")
    if t > t_cg:
        x, dy, s, rot = SHIPS[min(5, len(SHIPS) - 1)]
        for k in range(5):
            amphora(d, x - 60 * SS + k * 30 * SS * s, dy - top + 600 * SS - 30 * SS, 1.2, a * sine_out((t - t_cg - k * .12) / .4))
    # ayak izleri (yürüyerek)
    t_fp = cue("footprints", "ayak", "izleri")
    for k, (x, dy, left) in enumerate(STEPS):
        ak = sine_out((t - t_fp - k * .22) / .35) if t > t_fp else 0
        if ak > 0: foot(d, x, dy - top + 600 * SS, 1.3, a * ak, left)
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    # derinlik/yıl sayacı (sağ kenar)
    yr = year_at(top + 900)
    label = f"{int(round(yr))}" if yr > 0 else f"MÖ {int(round(-yr))}"
    ytag(img, W * .80, 820 * SS, label, a, 58, bg=WHITE)
    ytag(img, W * .80, 900 * SS, "YIL", a, 30, bg=YEL)
    # etiketler
    if st("harbor") + 1.5 < t < en("cargo") + .3:
        serif(img, "Theodosius Limanı", W / 2, 560 * SS, 90, a * vis(t, cue("harbor", "theodosius", "liman") - .1, en("cargo"), .5, .4), (240, 225, 200))
    big(img, f"{n_sh}", W / 2, 1180 * SS, 180, a * vis(t, t_sh, en("cargo") - .5, .4, .5))
    hand(img, "batık gemi", W / 2 + 230 * SS, 1250 * SS, 70, a * vis(t, t_sh + .3, en("cargo") - .5, .4, .5), WHITE, -8)
    hand(img, "1.500 yıllık!", W * .30, 760 * SS, 76, a * vis(t, cue("cargo", "1500", "bin", "yıllık"), en("cargo") + .2, .4, .4), YEL, -8)
    hand(img, "daha derin...", W / 2, 640 * SS, 84, a * vis(t, st("deeper") + .1, en("deeper") + .2, .4, .4), WHITE, -5)
    hand(img, "8.000 yıllık ayak izleri", W / 2, 640 * SS, 72, a * vis(t, t_fp + .4, en("footprints") + .3, .4, .4), YEL, -5)

# ---------- tarih çubuğu (İstanbul'un tarihi uzuyor) ----------
def history_bar(img, t, a):
    if a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay)
    x0, x1, y = 120 * SS, W - 120 * SS, 1000 * SS
    grow = smooth((t - cue("older", "binlerce", "eski") ) / 1.4)
    full = x1 - x0; old_len = full * .14
    d.rounded_rectangle((x1 - old_len - (full - old_len) * grow, y - 26 * SS, x1, y + 26 * SS), radius=int(26 * SS), fill=A(GOLD, a))
    d.rounded_rectangle((x1 - old_len, y - 26 * SS, x1, y + 26 * SS), radius=int(26 * SS), fill=A((90, 160, 255), a))
    img.alpha_composite(lay)
    ytag(img, x1 - old_len / 2, y - 90 * SS, "BİLİNEN: ~2.700 YIL", a * (1 - .4 * grow), 34, bg=WHITE)
    if grow > .3: ytag(img, x0 + 180 * SS, y + 100 * SS, "YENİ: 8.000+ YIL", a * clamp01((grow - .3) / .3), 40)
    if grow > .6: hand(img, "+5.000 yıl!", W / 2, y - 220 * SS, 96, a * clamp01((grow - .6) / .3), YEL, -6)

# ---------- kare ----------
def frame(t):
    if t < T_GLOBE:
        p = smooth(t / T_GLOBE)
        img = globe(lerp(10, 29, p), lerp(30, 41, p), math.exp(lerp(math.log(420), math.log(2300), smooth(p))), t).resize((W, H), Image.BICUBIC).convert("RGBA")
        if t > T_GLOBE - .5:
            b, _ = render_base(cam_at(T_GLOBE - .3), t); img = Image.blend(img, b, smooth((t - (T_GLOBE - .5)) / .5))
        cam = None
    else:
        cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
        overlays(img, cam, fp, t)
    sec = vis(t, st("harbor") - .2, en("footprints") + .1, .9, .9)       # kesite yumuşak geçiş
    if sec > 0: section(img, t, sec)
    hb = vis(t, st("older") - .1, en("older") + .2, .6, .6)
    if hb > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 12, 20, int(170 * hb))))
        history_bar(img, t, hb)
    ui(img, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * .16)))
    caption_top(img, t)
    brand.watermark(img, t, TOTAL)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def overlays(img, cam, fp, t):
    a_tr = vis(t, T_GLOBE, st("dig") - .2, .6, .7)
    glow_outline(img, cam, CN["Turkey"], (255, 90, 90), a_tr * .7, fp, 5)
    a_m = vis(t, cue("dig", "marmaray") - .1, TOTAL, .5, .4)
    if a_m > 0:
        pts = ring_pts(cam, MARMARAY); pr = smooth((t - cue("dig", "marmaray")) / 1.6)
        lay = L(); d = ImageDraw.Draw(lay)
        if len(pts) > 1:
            d.line(partial(pts, pr), fill=A((0, 0, 0), a_m * .5), width=18 * SS, joint="curve")
            d.line(partial(pts, pr), fill=A((235, 40, 50), a_m), width=9 * SS, joint="curve")
        img.alpha_composite(lay)
    q = pj(cam, *YENIKAPI)
    if q:
        a_y = vis(t, cue("dig", "yenikapı") - .1, TOTAL, .5, .4)
        if a_y > 0:
            lay = L(); d = ImageDraw.Draw(lay); r = (16 + 4 * math.sin(t * 4)) * SS
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=A(RED, a_y), outline=A(WHITE, a_y), width=5 * SS)
            img.alpha_composite(lay)
            ytag(img, q[0] + 170 * SS, q[1] - rise(t, cue("dig", "yenikapı")) / 2, "YENİKAPI", a_y, 46)
        qm = pj(cam, 28.99, 41.03)
        if qm: ytag(img, qm[0] + 120 * SS, qm[1] - 140 * SS, "MARMARAY", vis(t, cue("dig", "marmaray") + .4, st("harbor") - .3, .5, .4), 40, bg=(235, 40, 50), fg=WHITE)
    a_i = vis(t, T_GLOBE + .3, st("dig") - .2, .6, .5)
    qi = pj(cam, 28.98, 41.08)
    if qi: big(img, "İSTANBUL", qi[0], max(qi[1], 1000 * SS) - rise(t, T_GLOBE + .3), 70, a_i, WHITE)

def ui(img, t):
    brand.brand_card(img, t, "İSTANBUL'UN ALTINDAN", "37 GEMİ ÇIKTI!", en("really") + .2)
    a = vis(t, cue("really", "gerçek"), en("really") + .2, .4, .4)
    if a > 0:
        lay = L(); byz_ship(ImageDraw.Draw(lay), W / 2, 1250 * SS - rise(t, cue("really", "gerçek"), .6), 2.4, a, -.05); img.alpha_composite(lay)
    a = vis(t, cue("dig", "2004", "iki"), en("dig") + .1, .5, .4)
    serif(img, "2004", W / 2, 560 * SS + rise(t, cue("dig", "2004", "iki")), 150, a)
    a = vis(t, cue("delay", "marmaray"), en("delay") + .3, .5, .4)
    if a > 0:
        serif(img, "2009", W * .30, 600 * SS, 120, a * (1 - .5 * smooth((t - cue("delay", "yıllarca", "ertelendi")) / .6)), (200, 200, 200))
        if t > cue("delay", "yıllarca", "ertelendi"):
            lay = L(); d = ImageDraw.Draw(lay)
            d.line([(W * .18, 600 * SS), (W * .42, 600 * SS)], fill=A(RED, a), width=10 * SS); img.alpha_composite(lay)
            serif(img, "2013", W * .70, 600 * SS + rise(t, cue("delay", "yıllarca", "ertelendi")), 140, a)
            hand(img, "açılış ertelendi", W / 2, 760 * SS, 72, a * sine_out((t - cue("delay", "yıllarca", "ertelendi")) / .5), YEL, -6)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Altında daha neler var?", W / 2, 560 * SS - rise(t, st("cta") + .3) / 2, 84, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 700 * SS, 58, alpha=vis(t, st("cta") + 1.0, TOTAL, .5, .3), scale=1)

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s8_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
