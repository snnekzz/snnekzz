"""Video 7: Van Gölü – tek balık türü. Haritanın Ardı teknikleri: renk=anlam altyazı, canlı sayaç, "?" simgesi,
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
LON0, LAT0D = 43.0, 38.65
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
TEX_DET = lake_paint(relief_tex((41.4, 44.6, 37.6, 39.8), 4096, 5, 10, "t7_van", 1.6), 41.4, 44.6, 37.6, 39.8)
TB = tex_info(20, 52, 29, 49, TEX_BIG); TD = tex_info(41.4, 44.6, 37.6, 39.8, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
K = [(0.0, 35.2, 39.0, 2500, 0, 0), (cue("intro", "gölünde") + .1, 35.4, 39.0, 2400, 0, 0),
     (en("intro") + .2, 43.0, 38.62, 330, 18, 0), (en("size"), 43.0, 38.60, 270, 26, 0),
     (st("answer") + .2, 43.0, 38.58, 240, 38, 0), (st("outlet") + .1, 42.85, 38.64, 300, 28, 0),
     (st("evap") + .3, 43.08, 38.74, 330, 30, 0), (st("soap") + .2, 43.0, 38.62, 250, 36, 0),
     (st("fish"), 43.0, 38.62, 250, 36, 0), (st("migrate") + .2, 43.35, 38.86, 280, 30, 0),
     (en("migrate") + .3, 43.35, 38.84, 250, 34, 0), (st("cta") - .1, 43.0, 38.64, 300, 24, 0), (TOTAL, 43.0, 38.66, 380, 18, 0)]
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
for k in ("türkiyenin", "türkiye"): ENT[k] = KRED
for k in ("gölünde", "göl", "van", "gölünün", "gölün"): ENT[k] = TURQ
for k in ("nehirlerin", "nehirlere"): ENT[k] = RIVER
for k in ("sodası", "sabunsu", "sabunsuz"): ENT[k] = PINK
for k in ("inci", "kefali"): ENT[k] = ORANGE
for k in ("bakterilerin", "kuleler"): ENT[k] = GREEN
for k in ("tek", "3700", "km²", "km", "40", "13", "binlercesi"): ENT[k] = YEL
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
            bg = ec or BLUE; fg = BLACK if bg == YEL else WHITE
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
def lake_screen(cam):
    return [p for p in ring_pts(cam, VAN.simplify(.004).exterior.coords)]
def focus_dim(img, cam, a, buf=0.35):
    """odak dışını karartma (gölün çevresi aydınlık)"""
    if a <= .01: return
    m = Image.new("L", (W // 4, H // 4), int(150 * a)); dm = ImageDraw.Draw(m)
    g = VAN.buffer(buf).simplify(.01)
    pts = ring_pts(cam, g.exterior.coords)
    if len(pts) > 2: dm.polygon([(x / 4, y / 4) for x, y in pts], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    img.paste((6, 10, 20), (0, 0), m)
rnd = random.Random(7)
def rand_in_lake(n, seed):
    r = random.Random(seed); out = []
    x0, y0, x1, y1 = VAN.bounds
    while len(out) < n:
        p = (r.uniform(x0, x1), r.uniform(y0, y1))
        if VAN.buffer(-.03).contains(Point(p)): out.append(p)
    return out
VAPOR = rand_in_lake(16, 1); SODA = rand_in_lake(140, 2); BUBBLES = rand_in_lake(30, 3)
def snap(path):
    p = Point(path[-1]); q = nearest_points(VAN.exterior, p)[0]
    return path[:-1] + [(q.x, q.y)]
RIVERS = [snap(p) for p in (
    [(44.10, 39.32), (43.95, 39.20), (43.82, 39.10), (43.72, 39.03), (43.62, 38.99)],
    [(43.05, 39.48), (43.18, 39.32), (43.27, 39.17), (43.33, 39.06), (43.36, 39.00)],
    [(43.95, 38.72), (43.78, 38.63), (43.60, 38.58), (43.45, 38.55), (43.33, 38.52)],
    [(43.62, 38.12), (43.45, 38.20), (43.28, 38.27), (43.12, 38.33)],
    [(42.55, 39.25), (42.65, 39.12), (42.74, 39.00), (42.80, 38.90)])]
def dens(path, n=60):
    out = []
    for (a0, b0), (a1, b1) in zip(path[:-1], path[1:]):
        for k in range(n): u = k / n; out.append((a0 + (a1 - a0) * u, b0 + (b1 - b0) * u))
    out.append(path[-1]); return out
RIV_D = [dens(p, 30) for p in RIVERS]

def overlays(img, cam, fp, t):
    # Türkiye beyaz (konumuz bu ülke)
    a_tr = vis(t, 0.0, cue("intro", "gölünde") + .2, .3, .6)
    if a_tr > 0: fill_geom(img, cam, CN["Turkey"], (250, 250, 250), .78 * a_tr, fp, outline=WHITE, ow=4 * SS)
    glow_outline(img, cam, CN["Turkey"], (255, 90, 90), vis(t, 0, en("intro"), .3, .6) * .8, fp, 4)
    # odak dışı karartma
    fd = max(vis(t, en("intro") - .2, st("fish") - .1, .7, .4), vis(t, st("migrate") - .2, en("migrate") + .2, .5, .5) * .8,
             vis(t, st("cta"), TOTAL, .6, .3) * .7)
    focus_dim(img, cam, fd)
    # göl: turkuaz + parıltı (sodayla sütlü)
    a_l = vis(t, cue("intro", "gölünde") - .1, TOTAL, .6, .3)
    milky = smooth((t - cue("evap", "sodası", "kalıyor")) / 1.5)
    col = tuple(int(lerp(c0, c1, milky)) for c0, c1 in zip(TURQ, (150, 225, 215)))
    pulse = .55 + .12 * math.sin(t * 3)
    fill_geom(img, cam, VAN, col, a_l * pulse * .85, fp, simplify=.003)
    glow_outline(img, cam, VAN, (180, 255, 255), a_l * (.6 + .4 * vis(t, st("size"), en("size"), .4, .5)), fp, 4)
    q = pj(cam, VCX, VCY)
    if not q: return
    cx, cy = q[0], q[1]
    # sayaç: 0 → 3.700 km²
    t_n = cue("size", "3700", "kilometre", "tam")
    a_n = vis(t, t_n - .1, en("size") + .4, .3, .4)
    if a_n > 0:
        v = 3700 * smooth((t - t_n) / 1.1)
        ytag(img, cx, cy - 330 * SS - rise(t, t_n) / 2, f"{trnum(v)} km²", a_n, 64, sc=.85 + .15 * pop(t, t_n))
    hand(img, "Türkiye'nin en büyük gölü", cx, cy + 300 * SS, 70, vis(t, cue("size", "kocaman"), en("size") + .2, .4, .4), WHITE, -5)
    # diğer balıklar gelir, dönemez → "?"
    t_q = cue("question", "diğer", "balıklar")
    a_q = vis(t, t_q, en("question") + .3, .4, .4)
    if a_q > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, (sx, sy, fl) in enumerate(((-.45, -.18, False), (.45, .05, True), (-.42, .22, False))):
            u = smooth((t - t_q - k * .15) / 1.4); xx = cx + sx * W * (1 - .55 * u); yy = cy + sy * W
            fish(d, xx, yy, 1.1, a_q * (1 - .6 * smooth((t - cue("question", "yaşayamıyor")) / .6)), (150, 160, 170), (120, 130, 140), fl)
            if t > cue("question", "yaşayamıyor"): xmark(d, xx, yy, 40 * SS, a_q * sine_out((t - cue("question", "yaşayamıyor") - k * .1) / .3), w=10)
        img.alpha_composite(lay)
    qmark(img, cx, cy - 40 * SS, 230, vis(t, cue("question", "neden"), en("answer") + .1, .3, .4), t)
    # cevap suyun içinde: dalga halkaları
    t_a = st("answer")
    if t_a - .1 < t < en("answer") + 1.0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k in range(4):
            u = ((t - t_a) * .7 + k / 4) % 1; r = (60 + 380 * u) * SS
            d.ellipse((cx - r, cy - r * .45, cx + r, cy + r * .45), outline=A(WHITE, (1 - u) * .7 * vis(t, t_a, en("answer") + .6, .3, .4)), width=5 * SS)
        img.alpha_composite(lay)
    # çıkış yok: batıya kesik ok + kırmızı X
    t_o = cue("outlet", "çıkışı", "hiçbir")
    a_o = vis(t, t_o - .2, en("outlet") + .5, .3, .4)
    if a_o > 0:
        p0 = pj(cam, 42.33, 38.52); p1 = pj(cam, 41.75, 38.70)
        if p0 and p1:
            p0, p1 = p0[:2], p1[:2]
            lay = L(); d = ImageDraw.Draw(lay); pr = smooth((t - t_o + .2) / .7)
            ex, ey = p0[0] + (p1[0] - p0[0]) * pr, p0[1] + (p1[1] - p0[1]) * pr
            R.dashed(d, [p0, (ex, ey)], A(WHITE, a_o), 9 * SS, 30 * SS, 20 * SS)
            if t > cue("outlet", "yok"): xmark(d, ex, ey, 46 * SS, a_o * pop(t, cue("outlet", "yok")))
            img.alpha_composite(lay)
            if t > cue("outlet", "yok"): ytag(img, ex + 40 * SS, ey - 120 * SS, "ÇIKIŞ YOK", a_o, 52, bg=KRED, fg=WHITE, sc=pop(t, cue("outlet", "yok") + .1))
    # nehirler akar
    t_r = cue("evap", "nehirlerin")
    a_r = vis(t, t_r - .1, en("migrate") + .4, .3, .5)
    if a_r > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, rp in enumerate(RIV_D):
            pts = ring_pts(cam, rp)
            if len(pts) < 2: continue
            pr = smooth((t - t_r - k * .12) / 1.0)
            pp = partial(pts, pr)
            if len(pp) > 1:
                d.line(pp, fill=A((10, 40, 90), a_r * .6), width=16 * SS, joint="curve")
                d.line(pp, fill=A(RIVER, a_r), width=8 * SS, joint="curve")
            if pr >= 1 and t < st("migrate"):           # akış yönünde parıltılar
                for j in range(3):
                    u = ((t * .45 + j / 3 + k * .17) % 1); i = int(u * (len(pts) - 1)); x_, y_ = pts[i]
                    d.ellipse((x_ - 7 * SS, y_ - 7 * SS, x_ + 7 * SS, y_ + 7 * SS), fill=A(WHITE, a_r * .9))
        img.alpha_composite(lay)
    # buharlaşma
    t_v = cue("evap", "buharlaşıyor")
    a_v = vis(t, t_v - .1, en("evap") + .3, .3, .5)
    if a_v > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, (lo, la) in enumerate(VAPOR):
            p = pj(cam, lo, la)
            if not p: continue
            u = ((t - t_v) * .55 + k * .137) % 1
            for j in range(6):
                yy = p[1] - (u * 260 + j * 16) * SS; xx = p[0] + math.sin(u * 7 + j * .8 + k) * 16 * SS
                d.ellipse((xx - 5 * SS, yy - 5 * SS, xx + 5 * SS, yy + 5 * SS), fill=A(WHITE, a_v * (1 - u) * .55))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
        ytag(img, cx - 260 * SS, cy - 300 * SS, "BUHARLAŞIR", a_v * vis(t, t_v, en("evap") - .6, .3, .3), 42, bg=WHITE)
    # soda birikir
    t_s = cue("evap", "sodası")
    a_s = vis(t, t_s - .1, en("soap") + .3, .3, .5)
    if a_s > 0:
        lay = L(); d = ImageDraw.Draw(lay); n = int(len(SODA) * smooth((t - t_s) / 1.6))
        for lo, la in SODA[:n]:
            p = pj(cam, lo, la)
            if p: d.ellipse((p[0] - 6 * SS, p[1] - 6 * SS, p[0] + 6 * SS, p[1] + 6 * SS), fill=A((255, 225, 240), a_s * .85))
        img.alpha_composite(lay)
        ytag(img, cx + 240 * SS, cy - 280 * SS, "SODA", a_s * vis(t, t_s, en("evap") + .2, .3, .3), 52, bg=PINK, fg=WHITE, sc=pop(t, t_s))
    # sabunsu: köpük baloncukları
    t_b = cue("soap", "sabunsu")
    a_b = vis(t, t_b - .1, en("soap") + .2, .3, .4)
    if a_b > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, (lo, la) in enumerate(BUBBLES):
            p = pj(cam, lo, la)
            if not p: continue
            u = ((t - t_b) * .5 + k * .093) % 1; r = (10 + 22 * (k % 4) / 3) * SS
            yy = p[1] - u * 200 * SS
            d.ellipse((p[0] - r, yy - r, p[0] + r, yy + r), outline=A(WHITE, a_b * (1 - u)), width=3 * SS)
            d.ellipse((p[0] - r * .45, yy - r * .55, p[0] - r * .15, yy - r * .25), fill=A(WHITE, a_b * (1 - u) * .8))
        img.alpha_composite(lay)
    # kefaller nehre tırmanır
    t_m = cue("migrate", "bahar", "her")
    a_m = vis(t, t_m, en("migrate") + .3, .4, .5)
    if a_m > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, rp in enumerate(RIV_D):
            pts = ring_pts(cam, rp)
            if len(pts) < 3: continue
            for j in range(7):
                u = ((t - t_m) * .22 + j / 7 + k * .11) % 1
                i = int((1 - u) * (len(pts) - 2)); (x0, y0), (x1, y1) = pts[i + 1], pts[i]
                ang = math.atan2(y1 - y0, x1 - x0)
                fish(d, x0, y0, .32, a_m * min(1, u * 6, (1 - u) * 6), rot=ang)
        img.alpha_composite(lay)
        ytag(img, W * .28, 560 * SS - rise(t, t_m) / 2, "HER BAHAR", a_m, 46, bg=GREEN)
        t_k = cue("migrate", "binlercesi")
        ytag(img, W * .70, 560 * SS, "BİNLERCE", vis(t, t_k, en("migrate") + .2, .3, .4), 46, sc=pop(t, t_k))
        hand(img, "akıntıya karşı!", W * .5, 1350 * SS, 80, vis(t, cue("migrate", "akıntıya"), en("migrate") + .2, .4, .4), YEL, -5)

def fish_scene(img, t):
    a = vis(t, st("fish") - .2, en("spawn") + .1, .5, .5)
    if a <= 0: return
    img.alpha_composite(Image.new("RGBA", (W, H), (6, 14, 26, int(175 * a))))
    lay = L(); d = ImageDraw.Draw(lay)
    t_f = cue("fish", "inci", "kefali")
    sc = 4.2 * (.8 + .2 * sine_out((t - t_f + .3) / .5))
    fish(d, W / 2 + (1 - sine_out((t - t_f + .3) / .6)) * 300 * SS + math.sin(t * 2) * 10 * SS, 1000 * SS + math.sin(t * 3) * 14 * SS, sc, a * sine_out((t - t_f + .3) / .4), rot=math.sin(t * 2.2) * .05)
    t_e = cue("spawn", "yumurtasını")
    a_e = vis(t, t_e, en("spawn") + .1, .3, .4)
    if a_e > 0:
        r0 = random.Random(5)
        for k in range(14):
            ex, ey = W * .5 + r0.uniform(-120, 120) * SS, 1420 * SS + r0.uniform(-50, 50) * SS; rr = r0.uniform(16, 24) * SS * pop(t, t_e + k * .02)
            d.ellipse((ex - rr, ey - rr, ex + rr, ey + rr), fill=A((255, 175, 70), a_e), outline=A((150, 80, 20), a_e), width=2 * SS)
        if t > cue("spawn", "bırakamıyor", "burada"): xmark(d, W * .5, 1420 * SS, 150 * SS, a_e * pop(t, cue("spawn", "bırakamıyor", "burada")), w=18)
    img.alpha_composite(lay)
    typetag(img, W / 2, 1260 * SS, "İNCİ KEFALİ", t, t_f + .1, vis(t, t_f, en("fish") + .2, .3, .4), 62)
    hand(img, "tek dayanıklı tür", W / 2, 700 * SS, 76, vis(t, cue("fish", "dayanabiliyor"), en("fish") + .1, .4, .4), YEL, -5)
    hand(img, "yumurta burada olmaz", W / 2, 1640 * SS, 70, vis(t, cue("spawn", "bırakamıyor", "burada"), en("spawn") + .1, .4, .4), WHITE, -4)

def laundry(img, t):
    t_c = cue("soap", "çamaşırlar")
    a = vis(t, t_c - .1, en("soap") + .2, .4, .4)
    if a <= 0: return
    lay = L(); d = ImageDraw.Draw(lay); y0 = 1260 * SS - rise(t, t_c, .6)
    d.line([(W * .12, y0), (W * .88, y0 + 20 * SS)], fill=A(WHITE, a), width=5 * SS)
    for k, (fx, c) in enumerate(((.25, (240, 240, 245)), (.45, (120, 180, 255)), (.65, (255, 210, 120)), (.80, (240, 240, 245)))):
        x = W * fx; y = y0 + 20 * SS * fx + 6 * SS; s = SS * 1.15 * pop(t, t_c + k * .1); sw = math.sin(t * 2 + k) * 4 * SS
        d.polygon([(x - 70 * s + sw, y), (x + 70 * s + sw, y), (x + 100 * s + sw, y + 40 * s), (x + 70 * s + sw, y + 60 * s), (x + 60 * s + sw, y + 170 * s),
                   (x - 60 * s + sw, y + 170 * s), (x - 70 * s + sw, y + 60 * s), (x - 100 * s + sw, y + 40 * s)], fill=A(c, a), outline=A((30, 30, 40), a))
        d.rectangle((x - 6 * s + sw, y - 14 * s, x + 6 * s + sw, y + 10 * s), fill=A((200, 160, 90), a))
    img.alpha_composite(lay)
    hand(img, "sabunsuz yıkanırdı!", W / 2, 1640 * SS, 80, vis(t, cue("soap", "sabunsuz"), en("soap") + .2, .4, .4), YEL, -5)

# ---------- göl dibi kesiti ----------
SURF, BOT = 470 * SS, 1650 * SS
PXM = (BOT - 760 * SS) / 40.0                                # px / metre
TOWERS = [(.13, 22, 1), (.31, 40, 2), (.47, 17, 3), (.90, 27, 4)]
def tower(d, x, h, a, seed, grow):
    r = random.Random(seed); top = BOT - h * PXM * grow; y = BOT
    while y > top:
        w = (70 + r.uniform(-14, 18)) * SS * (1 - .35 * (BOT - y) / max(1, h * PXM)); hh = r.uniform(50, 90) * SS
        c = int(r.uniform(-12, 12))
        d.ellipse((x - w + r.uniform(-8, 8) * SS, y - hh, x + w + r.uniform(-8, 8) * SS, y + hh * .2), fill=A((150 + c, 158 + c, 130 + c), a), outline=A((90, 100, 80), a))
        y -= hh * .55
def section9(img, t, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    off = (1 - sine_out(clamp01((t - st("deeper") + .2) / .9))) * 500 * SS
    sky = np.linspace(0, 1, int(SURF));
    for i, (c0, c1) in enumerate((((40, 70, 120), (150, 190, 220)),)): pass
    for yy in range(0, int(SURF + off), 8):
        u = yy / max(1, SURF + off); c = tuple(int(lerp(p, q, u)) for p, q in zip((30, 55, 100), (160, 200, 225)))
        d.rectangle((0, yy, W, yy + 8), fill=c + (255,))
    mt = [(0, SURF + off - 120 * SS), (W * .2, SURF + off - 260 * SS), (W * .38, SURF + off - 150 * SS), (W * .6, SURF + off - 420 * SS),
          (W * .78, SURF + off - 200 * SS), (W, SURF + off - 280 * SS), (W, SURF + off), (0, SURF + off)]
    d.polygon(mt, fill=(70, 80, 96, 255))
    for yy in range(int(SURF + off), H, 10):
        u = clamp01((yy - SURF - off) / (BOT - SURF)); c = tuple(int(lerp(p, q, u)) for p, q in zip((60, 185, 200), (12, 52, 80)))
        d.rectangle((0, yy, W, yy + 10), fill=c + (255,))
    if BOT + off < H: d.rectangle((0, BOT + off, W, H), fill=(54, 50, 44, 255))
    r0 = random.Random(9)
    for _ in range(160):
        sx, sy = r0.uniform(0, W), r0.uniform(BOT + off, max(H, BOT + off + 1)); rr = r0.uniform(4, 14) * SS
        d.ellipse((sx - rr, sy - rr * .5, sx + rr, sy + rr * .5), fill=(40, 36, 32, 255))
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(rays)
    for k in range(5):
        x = W * (.15 + .18 * k) + math.sin(t * .6 + k) * 30 * SS
        dr.polygon([(x - 30 * SS, SURF + off), (x + 30 * SS, SURF + off), (x + 220 * SS, BOT + off), (x + 60 * SS, BOT + off)], fill=(255, 255, 255, 22))
    lay.alpha_composite(rays.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(lay)
    # yüzen kefaller
    for k in range(5):
        u = ((t * .05 + k * .23) % 1)
        fish(d, W * (1.1 - 1.2 * u), SURF + off + (150 + k * 120) * SS, .7, 1, flip=True)
    ob = Image.new("RGBA", (W, H), (0, 0, 0, 0)); do = ImageDraw.Draw(ob)
    t_b = cue("towers", "bakterilerin")
    t_g = cue("towers", "ördüğü")
    for k, (fx, h, seed) in enumerate(TOWERS):
        g = smooth((t - t_g - k * .15) / 1.4)
        if g > 0: tower(do, W * fx, h, 1, seed, g)
    if t > t_b:                                           # parlayan bakteriler
        r1 = random.Random(4)
        for k in range(90):
            fx, h, _ = TOWERS[k % 4]; bx = W * fx + r1.uniform(-110, 110) * SS; by = BOT - r1.uniform(0, h) * PXM * .9 + math.sin(t * 2 + k) * 6 * SS
            al = vis(t, t_b + r1.uniform(0, .6), en("building") + 1, .3, .4) * .9
            do.ellipse((bx - 6 * SS, by - 6 * SS, bx + 6 * SS, by + 6 * SS), fill=A(GREEN, al))
    lay.alpha_composite(ob, (0, int(off)))
    d = ImageDraw.Draw(lay)
    # ölçü cetveli: 0 → 40 m
    t_40 = cue("towers", "40", "kırk", "metrelik")
    a40 = vis(t, t_40 - .1, en("building") + .6, .3, .4)
    if a40 > 0:
        g = smooth((t - t_40) / 1.0); xr = W * .31 + 160 * SS; ytop = BOT - 40 * PXM * g + off
        d.line([(xr, BOT + off), (xr, ytop)], fill=A(YEL, a40), width=8 * SS)
        for m in range(0, int(40 * g) + 1, 5):
            yy = BOT + off - m * PXM; d.line([(xr - 22 * SS, yy), (xr, yy)], fill=A(YEL, a40), width=5 * SS)
        d.line([(xr - 40 * SS, ytop), (xr + 40 * SS, ytop)], fill=A(YEL, a40), width=8 * SS)
    # 13 katlı bina
    t_13 = cue("building", "13", "on", "katlı")
    a13 = vis(t, t_13 - .2, TOTAL, .4, .4)
    if a13 > 0:
        bx0, bx1 = W * .60, W * .78; fl_h = 40 * PXM / 13; rise_ = (1 - sine_out((t - t_13 + .2) / .6)) * 200 * SS
        d.rectangle((bx0, BOT + off - 40 * PXM + rise_, bx1, BOT + off), fill=A((205, 212, 222), a13), outline=A((40, 50, 70), a13), width=4 * SS)
        lit = int(13 * smooth((t - t_13) / 1.1))
        for f_ in range(13):
            yy = BOT + off - (f_ + 1) * fl_h + rise_
            d.line([(bx0, yy), (bx1, yy)], fill=A((120, 130, 150), a13), width=3 * SS)
            for wx in range(4):
                x0 = bx0 + (18 + wx * ((bx1 - bx0 - 36) / 4)) * 1; ww = (bx1 - bx0 - 36) / 4 - 16 * SS
                d.rectangle((x0, yy + fl_h * .25, x0 + ww, yy + fl_h * .7), fill=A(YEL if f_ < lit else (90, 105, 130), a13))
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)
    if a40 > 0:
        g = smooth((t - t_40) / 1.0)
        ytag(img, W * .31 + 160 * SS, BOT + off - 40 * PXM * g - 80 * SS, f"{int(round(40 * g))} m", a * a40, 60)
    if a13 > 0:
        lit = int(13 * smooth((t - t_13) / 1.1))
        ytag(img, W * .69, BOT + off - 40 * PXM - 120 * SS, f"{lit} KAT", a * a13, 58, sc=pop(t, t_13))
    hand(img, "bakteriler ördü", W * .72, 600 * SS, 70, a * vis(t, t_b, en("towers") - .2, .4, .4), GREEN, -5)
    hand(img, "gölün dibinde", W * .5, 900 * SS, 80, a * vis(t, cue("deeper", "dibinde"), en("deeper") + .1, .4, .4), WHITE, -4)

# ---------- kare ----------
def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
    overlays(img, cam, fp, t)
    laundry(img, t)
    fish_scene(img, t)
    sec = vis(t, st("deeper") - .2, en("building") + .4, .9, .8)
    if sec > 0: section9(img, t, sec)
    ui(img, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * .16)))
    caption_top(img, t)
    brand.watermark(img, t, TOTAL)
    fade = min(prog(t, 0, .15), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def ui(img, t):
    brand.brand_card(img, t, "DEV GÖL,", "TEK BALIK!", en("intro") - .1)
    t_1 = cue("intro", "tek")
    a = vis(t, t_1, en("intro") + .1, .3, .4)
    if a > 0:
        lay = L(); fish(ImageDraw.Draw(lay), W * .42, 1180 * SS, 2.0 * pop(t, t_1), a); img.alpha_composite(lay)
        big(img, "1", W * .66, 1180 * SS, 230, a, YEL, sc=pop(t, t_1))
        ytag(img, W * .62, 1400 * SS, "TÜR", a, 50)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Başka hangi sırrı var?", W / 2, 600 * SS - rise(t, st("cta") + .3) / 2, 84, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara") , TOTAL, .4, .3), scale=1)

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
