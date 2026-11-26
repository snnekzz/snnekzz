"""Video 10: Derinkuyu – yerin 85 m altındaki şehir. Haritanın Ardı teknikleri: renk=anlam altyazı, canlı sayaç, "?" simgesi,
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
LON0, LAT0D = 34.74, 38.4
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
TEX_DET = relief_tex((33.6, 35.9, 37.5, 39.3), 4096, 8, 10, "t10_kapadokya", 1.6)
TB = tex_info(20, 52, 29, 49, TEX_BIG); TD = tex_info(33.6, 35.9, 37.5, 39.3, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
K = [(0.0, 34.0, 39.0, 2500, 0, 0), (cue("intro", "nevşehirde") - .3, 34.2, 38.95, 2400, 0, 0),
     (en("intro") - .1, 34.74, 38.36, 120, 30, 0), (st("kaymakli") - .2, 34.745, 38.36, 120, 30, 0),
     (st("kaymakli") + .9, 34.745, 38.41, 75, 34, 0), (st("cta"), 34.74, 38.40, 160, 26, 0), (TOTAL, 34.74, 38.40, 200, 22, 0)]
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
for k in ("nevşehirde",): ENT[k] = ORANGE
for k in ("derinkuyu", "şehre", "şehir", "şehrin", "şehri"): ENT[k] = (255, 200, 80)
for k in ("tünel", "tünelle"): ENT[k] = (200, 160, 110)
for k in ("kaymaklıya",): ENT[k] = (110, 170, 255)
for k in ("düşman",): ENT[k] = KRED
for k in ("ahırlar", "kuyular", "şarap", "mahzenleri", "kiliseler"): ENT[k] = (235, 205, 150)
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
# ---------- Derinkuyu ----------
DK = (34.734, 38.374); KAYM = (34.751, 38.461)
ROCK = (196, 168, 128); ROCK_D = (150, 122, 88); CHAMBER = (60, 42, 30); LIT = (255, 190, 100)
def pinmark(img, cam, lon, lat, a, col=KRED):
    q = pj(cam, lon, lat)
    if not q or a <= .01: return None
    lay = L(); d = ImageDraw.Draw(lay); x, y = q[0], q[1] - (1 - sine_out(a)) * 40 * SS; r = 24 * SS
    d.polygon([(x - r * .8, y - r * 1.6), (x + r * .8, y - r * 1.6), (x, y)], fill=A(col, a))
    d.ellipse((x - r, y - r * 2.6, x + r, y - r * .6), fill=A(col, a), outline=A(WHITE, a), width=4 * SS)
    d.ellipse((x - r * .38, y - r * 1.98, x + r * .38, y - r * 1.22), fill=A(WHITE, a))
    img.alpha_composite(lay); return (x, y)
def xmark(d, x, y, r, a, col=KRED, w=14):
    for s in (1, -1): d.line([(x - r, y - r * s), (x + r, y + r * s)], fill=A(col, a), width=int(w * SS))
SURF = 640 * SS; BOT = 1760 * SS; PXM = (BOT - SURF) / 85.0
rnd = random.Random(11)
LEVELS = []   # (y, x0, x1) – oda katları
for k in range(10):
    y = SURF + (6 + k * 8.2) * PXM; x0 = W * rnd.uniform(.10, .30); x1 = W * rnd.uniform(.55, .78)
    LEVELS.append((y, x0, x1))
SHAFT_X = W * .44
ROOMS = [("AHIR", 2, .22), ("KUYU", 4, .66), ("ŞARAP MAHZENİ", 6, .30), ("KİLİSE", 8, .62)]
def section12(img, t, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(0, int(SURF), 8):
        u = yy / SURF; d.rectangle((0, yy, W, yy + 8), fill=tuple(int(lerp(p, q, u)) for p, q in zip((70, 120, 190), (190, 215, 235))) + (255,))
    for yy in range(int(SURF), H, 10):
        u = (yy - SURF) / (H - SURF); d.rectangle((0, yy, W, yy + 10), fill=tuple(int(lerp(p, q, u)) for p, q in zip(ROCK, (110, 86, 60))) + (255,))
    r0 = random.Random(3)
    for _ in range(260):
        sx, sy, rr = r0.uniform(0, W), r0.uniform(SURF, H), r0.uniform(3, 10) * SS
        d.ellipse((sx - rr, sy - rr * .6, sx + rr, sy + rr * .6), fill=(ROCK_D[0], ROCK_D[1], ROCK_D[2], 180))
    # peri bacaları + ev (yüzey)
    for x, h in ((W * .08, 160), (W * .17, 220), (W * .88, 190), (W * .95, 140)):
        d.polygon([(x - 50 * SS, SURF), (x - 22 * SS, SURF - h * SS), (x + 22 * SS, SURF - h * SS), (x + 50 * SS, SURF)], fill=(205, 180, 140, 255))
        d.ellipse((x - 34 * SS, SURF - (h + 40) * SS, x + 34 * SS, SURF - (h - 10) * SS), fill=(150, 120, 90, 255))
    hx = SHAFT_X; d.rectangle((hx - 120 * SS, SURF - 190 * SS, hx + 120 * SS, SURF), fill=(225, 205, 170, 255), outline=(120, 95, 70, 255), width=4 * SS)
    d.polygon([(hx - 145 * SS, SURF - 190 * SS), (hx, SURF - 290 * SS), (hx + 145 * SS, SURF - 190 * SS)], fill=(170, 80, 60, 255))
    d.rectangle((hx - 30 * SS, SURF - 110 * SS, hx + 30 * SS, SURF), fill=(90, 60, 40, 255))
    # duvar yıkılır → tünel aşağı iner
    t_w = cue("intro", "yıktı", "duvarı"); t_t = cue("tunnel", "tünel", "arkasında")
    if t > t_w:
        g = smooth((t - t_w) / .6)
        for k in range(6):
            ang = k * 1.1; d.line([(hx + 90 * SS, SURF - 60 * SS), (hx + (90 + 50 * math.cos(ang) * g) * SS, SURF - (60 + 50 * math.sin(ang) * g) * SS)], fill=(60, 40, 30, 255), width=4 * SS)
    gt = smooth((t - t_t + .3) / 1.4)
    if gt > 0:
        pts = [(hx + 90 * SS, SURF - 40 * SS), (hx + 60 * SS, SURF + 40 * SS), (hx - 20 * SS, SURF + 70 * SS), (SHAFT_X, LEVELS[0][0])]
        pp = partial(pts, gt); d.line(pp, fill=(30, 20, 14, 255), width=34 * SS, joint="curve")
    # şehir: katlar sırayla açılır (aydınlanır)
    t_c = cue("city", "şehre", "koca")
    nlv = len(LEVELS) * smooth((t - t_c) / 1.8) if t > t_c else 0
    t_more = cue("more", "kısmını", "bugün")
    for k, (y, x0, x1) in enumerate(LEVELS):
        if k >= nlv: break
        dark = smooth((t - t_more - .3) / .8) * (1 if k >= 3 else 0)
        col = tuple(int(lerp(c1, c0, .65 * dark)) for c0, c1 in zip((20, 14, 10), (75, 52, 36)))
        d.rounded_rectangle((x0, y - 34 * SS, x1, y + 34 * SS), radius=int(30 * SS), fill=col + (255,), outline=(40, 26, 18, 255), width=3 * SS)
        for j in range(3):   # oda içi lamba ışığı
            lx = lerp(x0, x1, (j + .5) / 3)
            d.ellipse((lx - 10 * SS, y - 10 * SS, lx + 10 * SS, y + 10 * SS), fill=LIT + (int(220 * (1 - dark)),))
        if k > 0:            # kat arası rampa
            py = LEVELS[k - 1][0]; d.line([(lerp(LEVELS[k - 1][1], LEVELS[k - 1][2], .8), py + 30 * SS), (lerp(x0, x1, .2), y - 30 * SS)], fill=col + (255,), width=26 * SS)
    if nlv > 0:              # havalandırma bacası
        d.rectangle((W * .86 - 9 * SS, SURF, W * .86 + 9 * SS, LEVELS[min(len(LEVELS) - 1, int(nlv))][0]), fill=(40, 28, 20, 255))
    # insanlar
    t_p = cue("people", "20000", "yirmi", "kişinin")
    np_ = int(160 * smooth((t - t_p) / 1.6)) if t > t_p else 0
    r1 = random.Random(5)
    for i in range(np_):
        k = r1.randrange(len(LEVELS)); y, x0, x1 = LEVELS[k]; x = r1.uniform(x0 + 30 * SS, x1 - 30 * SS)
        c = (255, 255, 255) if r1.random() > .25 else (240, 210, 150)
        d.ellipse((x - 6 * SS, y - 16 * SS, x + 6 * SS, y - 4 * SS), fill=c + (255,)); d.rectangle((x - 5 * SS, y - 4 * SS, x + 5 * SS, y + 16 * SS), fill=c + (255,))
    # taş kapılar: girişte yuvarlanır, sonra katlar sırayla kapanır
    t_d = cue("doors", "yuvarlak", "taşlarla", "girişler")
    if t > t_d - .2:
        g = smooth((t - t_d + .2) / .9); y = LEVELS[0][0]; x = lerp(SHAFT_X + 220 * SS, SHAFT_X + 20 * SS, g); r = 48 * SS
        d.ellipse((x - r, y - r, x + r, y + r), fill=(170, 150, 120, 255), outline=(90, 70, 50, 255), width=5 * SS)
        d.ellipse((x - 12 * SS, y - 12 * SS, x + 12 * SS, y + 12 * SS), fill=(90, 70, 50, 255))
        an = -g * 4; d.line([(x, y), (x + r * .8 * math.cos(an), y + r * .8 * math.sin(an))], fill=(90, 70, 50, 255), width=4 * SS)
    t_l = cue("levels", "kat", "ayrı")
    if t > t_l:
        for k, (y, x0, x1) in enumerate(LEVELS[1:], 1):
            g = smooth((t - t_l - k * .12) / .4)
            if g > 0:
                x = lerp(x0, x0 + 40 * SS, g); r = 30 * SS
                d.ellipse((x - r, y - r, x + r, y + r), fill=(170, 150, 120, 255), outline=(90, 70, 50, 255), width=4 * SS)
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    # metinler
    stamp_text(img, "1963", (W * .74, 470 * SS + rise(t, st("intro") + .4)), FP, 130, fill=(255, 200, 80), stroke=BLACK, alpha=a * vis(t, st("intro") + .4, en("tunnel"), .4, .4))
    stamp_text(img, "?", (SHAFT_X, LEVELS[0][0] + 40 * SS + math.sin(t * 5) * 8 * SS), FA, 200, fill=WHITE, stroke=BLACK, alpha=a * vis(t, cue("question", "nereye", "peki"), en("question") + .1, .3, .3))
    stamp_text(img, "DERİNKUYU", (W / 2, 520 * SS + rise(t, cue("city", "derinkuyu"))), FA, 100, fill=(255, 200, 80), stroke=BLACK, alpha=a * vis(t, cue("city", "derinkuyu"), en("city") + .3, .4, .4))
    t_85 = cue("depth", "85", "seksen", "metre")
    a85 = a * vis(t, t_85 - .1, en("depth") + .4, .3, .4)
    if a85 > 0:
        g = smooth((t - t_85) / 1.1); xr = W * .06
        lay2 = L(); d2 = ImageDraw.Draw(lay2); yb = SURF + 85 * PXM * g
        d2.line([(xr, SURF), (xr, yb)], fill=A(YEL, a85), width=8 * SS)
        for m in range(0, int(85 * g) + 1, 10): d2.line([(xr, SURF + m * PXM), (xr + 22 * SS, SURF + m * PXM)], fill=A(YEL, a85), width=5 * SS)
        t_28 = cue("depth", "28", "yirmi", "katlı")
        if t > t_28:          # 28 katlı bina hayaleti (aşağı doğru)
            g2 = smooth((t - t_28) / 1.0); bx0, bx1 = W * .80, W * .94
            for f in range(int(28 * g2)):
                y0 = SURF + f * 85 * PXM / 28; d2.rectangle((bx0, y0, bx1, y0 + 85 * PXM / 28 - 3 * SS), outline=A(WHITE, a85 * .8), width=2 * SS, fill=A((255, 255, 255), a85 * .12))
        img.alpha_composite(lay2)
        ytag(img, xr + 120 * SS, yb + 10 * SS, f"{int(round(85 * g))} m", a85, 54)
        if t > t_28: ytag(img, W * .87, SURF - 60 * SS, f"{int(28 * smooth((t - t_28) / 1.0))} KAT", a85, 48, bg=WHITE)
    a_p = a * vis(t, t_p, en("people") + .3, .3, .4)
    if a_p > 0: ytag(img, W / 2, 560 * SS, f"{trnum(20000 * smooth((t - t_p) / 1.6))} KİŞİ", a_p, 64, sc=pop(t, t_p))
    for lab, k, fx in ROOMS:
        tw_ = cue("rooms", lab.split()[0].lower()[:5])
        ar = a * vis(t, tw_ - .1, en("rooms") + .3, .25, .4)
        if ar > 0: ytag(img, W * fx, LEVELS[k][0] - 70 * SS, lab, ar, 40, bg=WHITE, sc=pop(t, tw_ - .1))
    ytag(img, SHAFT_X + 200 * SS, LEVELS[0][0] - 110 * SS, "YARIM TON", a * vis(t, cue("doors", "yarım", "ton"), en("doors") + .2, .3, .4), 46, sc=pop(t, cue("doors", "yarım", "ton")))
    hand(img, "her kat kilitlenir", W / 2, 1830 * SS, 76, a * vis(t, t_l, en("levels") + .2, .4, .4), YEL, -4)
    if t > t_more:
        ytag(img, W * .5, LEVELS[1][0] - 70 * SS, "ZİYARETE AÇIK", a * vis(t, t_more, en("more") + .3, .3, .4), 40, bg=GREEN)
        ytag(img, W * .5, LEVELS[7][0] - 70 * SS, "KAPALI / KARANLIK", a * vis(t, t_more + .4, en("more") + .3, .3, .4), 40, bg=(60, 60, 70), fg=WHITE)

def overlays(img, cam, fp, t):
    a_tr = vis(t, 0.0, cue("intro", "nevşehirde") + .2, .25, .6)
    if a_tr > 0: fill_geom(img, cam, CN["Turkey"], (250, 250, 250), .75 * a_tr, fp, outline=WHITE, ow=4 * SS)
    glow_outline(img, cam, CN["Turkey"], (255, 90, 90), vis(t, 0, en("intro"), .3, .6) * .7, fp, 4)
    p = pinmark(img, cam, *DK, vis(t, cue("intro", "nevşehirde"), TOTAL, .4, .4))
    if p: ytag(img, p[0], p[1] + 80 * SS, "NEVŞEHİR · DERİNKUYU", vis(t, cue("intro", "nevşehirde") + .2, st("tunnel"), .3, .4), 44, bg=ORANGE, fg=WHITE)
    t_k = cue("kaymakli", "kaymaklıya", "tünelle")
    a_k = vis(t, t_k - .2, en("kaymakli") + .4, .3, .4)
    if a_k > 0:
        q = pinmark(img, cam, *KAYM, a_k, (60, 140, 255)); p0 = pj(cam, *DK)
        if q and p0:
            lay = L(); d = ImageDraw.Draw(lay); pr = smooth((t - t_k) / 1.2)
            e = (p0[0] + (q[0] - p0[0]) * pr, p0[1] + (q[1] - p0[1]) * pr)
            R.dashed(d, [p0[:2], e], A(YEL, a_k), 10 * SS, 26 * SS, 16 * SS); img.alpha_composite(lay)
            ytag(img, q[0], q[1] - 160 * SS, "KAYMAKLI", a_k, 48, bg=(60, 140, 255), fg=WHITE)
            hand(img, "yerin altından tünel", (p0[0] + q[0]) / 2 + 180 * SS, (p0[1] + q[1]) / 2, 70, a_k * sine_out((t - t_k - .6) / .4), YEL, -6)

def ui(img, t):
    brand.brand_card(img, t, "BİR DUVAR YIKILDI,", "ALTINDAN ŞEHİR ÇIKTI!", en("intro") - .1)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Neden bu kadar derin?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 86, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
    overlays(img, cam, fp, t)
    sc = max(vis(t, st("tunnel") - .3, st("kaymakli") - .1, .7, .6), vis(t, st("more") - .2, en("more") + .3, .6, .6))
    if sc > 0: section12(img, t, sc)
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
