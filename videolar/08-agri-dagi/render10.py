"""Video 8: Ağrı Dağı – 1932 Türkiye–İran toprak takası. Haritanın Ardı teknikleri: renk=anlam altyazı, canlı sayaç, "?" simgesi,
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
LON0, LAT0D = 44.35, 39.4
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
TEX_DET = relief_tex((43.4, 46.0, 38.1, 40.3), 4096, 6, 10, "t8_agri", 1.5)
TB = tex_info(20, 52, 29, 49, TEX_BIG); TD = tex_info(43.4, 46.0, 38.1, 40.3, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def lerp(a, b, p): return a + (b - a) * p
K = [(0.0, 36.5, 39.2, 2500, 0, 0), (cue("intro", "yanındaki", "hemen"), 37.0, 39.2, 2400, 0, 0),
     (en("intro") - .2, 44.36, 39.62, 120, 30, 0), (en("question"), 44.38, 39.61, 95, 36, 0),
     (st("border") + .3, 44.39, 39.60, 80, 40, 0), (en("crisis"), 44.37, 39.60, 78, 42, 0),
     (st("gain"), 44.40, 39.60, 85, 36, 0), (st("give") + .2, 44.40, 39.62, 90, 34, 0),
     (st("give") + 1.4, 44.33, 39.0, 280, 22, 0), (en("give") + .1, 44.33, 39.0, 290, 22, 0),
     (st("myth") + 1.0, 44.86, 39.60, 85, 30, 0), (en("kars"), 44.86, 39.60, 78, 32, 0),
     (st("cta") + .4, 44.45, 39.55, 300, 20, 0), (TOTAL, 44.45, 39.55, 340, 18, 0)]
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
for k in ("türkiyenin", "türkiyeye", "türk"): ENT[k] = KRED
for k in ("iran", "irana", "irandaki", "kotur"): ENT[k] = GREEN
for k in ("küçük", "ağrının", "ağrı", "dağının", "dağın"): ENT[k] = ORANGE
for k in ("nahçıvan",): ENT[k] = (110, 170, 255)
for k in ("takasta", "takası", "takasla", "1932de", "1921den"): ENT[k] = YEL
for k in ("kriz",): ENT[k] = KRED

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
# ---------- Ağrı geometrisi ----------
AGRI = (44.298, 39.702); KUCUK = (44.405, 39.652)
BORDER_NOW = [(44.567, 39.767), (44.459, 39.655), (44.451, 39.626), (44.412, 39.544), (44.415, 39.505), (44.405, 39.452)]
BORDER_OLD = [(44.405, 39.452), (44.372, 39.55), (44.362, 39.615), (44.388, 39.668), (44.45, 39.73), (44.567, 39.767)]
STRIP = Polygon(BORDER_OLD + BORDER_NOW[::-1][1:-1]).buffer(0)          # takasla Türkiye'ye geçen şerit (temsili)
KOTUR_NOW = [(44.297, 38.601), (44.293, 38.563), (44.3, 38.512), (44.3, 38.493), (44.286, 38.455), (44.286, 38.443), (44.289, 38.417)]
KOTUR = Polygon(KOTUR_NOW + [(44.36, 38.42), (44.405, 38.47), (44.385, 38.555), (44.335, 38.61)]).buffer(0)   # İran'a geçen alan (temsili)
KOTUR_C = (44.35, 38.51)
NAKH = CN.get("Azerbaijan", Polygon()).intersection(box(44.7, 38.8, 46.3, 39.9))
NAKH_BORDER = CN["Turkey"].boundary.intersection(NAKH.buffer(.03))
IRAN = CN.get("Iran", Polygon())
def dens(path, n=30):
    out = []
    for (a0, b0), (a1, b1) in zip(path[:-1], path[1:]):
        for k in range(n): u = k / n; out.append((a0 + (a1 - a0) * u, b0 + (b1 - b0) * u))
    out.append(path[-1]); return out
def focus_dim(img, cam, geom, a, buf=0.12):
    if a <= .01: return
    m = Image.new("L", (W // 4, H // 4), int(150 * a)); dm = ImageDraw.Draw(m)
    for p in polys(geom.buffer(buf).simplify(.01)):
        pts = ring_pts(cam, p.exterior.coords)
        if len(pts) > 2: dm.polygon([(x / 4, y / 4) for x, y in pts], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    img.paste((6, 10, 20), (0, 0), m)
def pinmark(img, cam, lon, lat, a, col=KRED, t=0):
    q = pj(cam, lon, lat)
    if not q or a <= .01: return None
    lay = L(); d = ImageDraw.Draw(lay); x, y = q[0], q[1] - (1 - sine_out(a)) * 40 * SS; r = 22 * SS
    d.polygon([(x - r * .8, y - r * 1.6), (x + r * .8, y - r * 1.6), (x, y)], fill=A(col, a))
    d.ellipse((x - r, y - r * 2.6, x + r, y - r * .6), fill=A(col, a), outline=A(WHITE, a), width=4 * SS)
    d.ellipse((x - r * .38, y - r * 1.98, x + r * .38, y - r * 1.22), fill=A(WHITE, a))
    img.alpha_composite(lay); return (x, y)
def swap_icon(img, x, y, s, a, t, col=YEL):
    if a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay); r = 90 * SS * s; rot = t * 1.4
    for k in range(2):
        a0 = rot + k * math.pi
        pts = [(x + r * math.cos(a0 + u), y + r * math.sin(a0 + u)) for u in np.linspace(.25, 2.6, 24)]
        d.line(pts, fill=A(BLACK, a), width=int(26 * SS * s), joint="curve"); d.line(pts, fill=A(col, a), width=int(16 * SS * s), joint="curve")
        e = a0 + 2.75; tx, ty = x + r * math.cos(e), y + r * math.sin(e); bx, by = math.cos(e + math.pi / 2), math.sin(e + math.pi / 2)
        d.polygon([(tx + bx * 34 * SS * s, ty + by * 34 * SS * s), (tx + math.cos(e) * 30 * SS * s, ty + math.sin(e) * 30 * SS * s),
                   (tx - math.cos(e) * 30 * SS * s, ty - math.sin(e) * 30 * SS * s)], fill=A(col, a))
    img.alpha_composite(lay)
def treaty_card(img, t, t0, a):
    if a <= .01: return
    lay = L(); d = ImageDraw.Draw(lay); s = SS * (.85 + .15 * pop(t, t0)); x, y = W / 2, 1150 * SS - rise(t, t0, .6)
    w, h = 300 * s, 380 * s
    d.rectangle((x - w + 14 * SS, y - h + 18 * SS, x + w + 14 * SS, y + h + 18 * SS), fill=A((0, 0, 0), a * .4))
    d.rectangle((x - w, y - h, x + w, y + h), fill=A((246, 236, 212), a), outline=A((120, 90, 50), a), width=5 * SS)
    for k in range(9):
        yy = y - h + (110 + k * 52) * s; d.line([(x - w + 50 * s, yy), (x + w - (50 + (k % 3) * 60) * s, yy)], fill=A((150, 130, 100), a), width=int(7 * s))
    d.ellipse((x + w - 170 * s, y + h - 170 * s, x + w - 40 * s, y + h - 40 * s), fill=A(KRED, a), outline=A((120, 10, 20), a), width=4 * SS)
    img.alpha_composite(lay)
    stamp_text(img, "TAHRAN", (x, y - h + 60 * s), FP, 54 * SS / SS, fill=(90, 60, 30), stroke=(246, 236, 212), alpha=a)

def overlays(img, cam, fp, t):
    a_tr = vis(t, 0.0, cue("intro", "yanındaki", "hemen") + .1, .25, .6)
    if a_tr > 0: fill_geom(img, cam, CN["Turkey"], (250, 250, 250), .75 * a_tr, fp, outline=WHITE, ow=4 * SS)
    # ülke tonları: Türkiye kırmızımsı, İran yeşilimsi (renk = anlam)
    a_c = vis(t, cue("intro", "dağın") - .3, TOTAL, .6, .3)
    fill_geom(img, cam, IRAN, (40, 170, 90), .22 * a_c, fp)
    glow_outline(img, cam, IRAN, (80, 220, 120), .5 * a_c, fp, 3)
    a_nk = max(vis(t, st("myth") - .2, en("kars") + .3, .5, .5), .5 * a_c)
    fill_geom(img, cam, NAKH, (60, 140, 255), .3 * a_nk, fp)
    # odak dışını karartma
    fd = max(vis(t, en("intro") - .5, st("treaty") - .2, .6, .4), vis(t, st("gain") - .2, en("gain") + .3, .5, .4))
    focus_dim(img, cam, STRIP, fd * .9, .15)
    # şerit: önce İran (yeşil), takastan sonra Türkiye (kırmızı)
    t_g = cue("gain", "geçti", "türkiyeye")
    turn = smooth((t - t_g + .3) / .8)
    a_s = vis(t, cue("intro", "yamaçları") - .1, TOTAL, .5, .3)
    if a_s > 0:
        col = tuple(int(lerp(c0, c1, turn)) for c0, c1 in zip((50, 200, 100), (229, 36, 59)))
        fill_geom(img, cam, STRIP, col, a_s * (.55 + .12 * math.sin(t * 3)), fp, simplify=.001, outline=WHITE, ow=3 * SS)
    # eski sınır (kesikli) → takastan sonra söner; bugünkü sınır (düz)
    t_b = cue("border", "eskiden", "sınır")
    a_ob = vis(t, t_b - .1, t_g + .4, .3, .6)
    if a_ob > 0:
        pts = ring_pts(cam, dens(BORDER_OLD, 20)); lay = L(); d = ImageDraw.Draw(lay)
        pp = partial(pts, smooth((t - t_b) / 1.1))
        if len(pp) > 1: R.dashed(d, pp, A(WHITE, a_ob), 8 * SS, 26 * SS, 16 * SS)
        img.alpha_composite(lay)
    a_nb = vis(t, t_g, TOTAL, .5, .3)
    if a_nb > 0:
        pts = ring_pts(cam, dens(BORDER_NOW, 20)); lay = L(); d = ImageDraw.Draw(lay)
        pp = partial(pts, smooth((t - t_g) / .9))
        if len(pp) > 1:
            d.line(pp, fill=A(BLACK, a_nb * .6), width=14 * SS, joint="curve"); d.line(pp, fill=A(YEL, a_nb), width=7 * SS, joint="curve")
        img.alpha_composite(lay)
    # dağ iğneleri + yükseklik sayaçları (sesle söylenmiyor, ekranda)
    pa = pinmark(img, cam, *AGRI, vis(t, .9, en("border"), .4, .5))
    if pa: ytag(img, pa[0] - 60 * SS, pa[1] - 190 * SS, f"AĞRI · {trnum(5137 * smooth((t - .9) / 1.2))} m", vis(t, 1.0, en("question") + .2, .3, .4), 52)
    pk = pinmark(img, cam, *KUCUK, vis(t, 2.0, en("border"), .4, .5), (255, 150, 40))
    if pk: ytag(img, pk[0] + 40 * SS, pk[1] + 110 * SS, f"KÜÇÜK AĞRI · {trnum(3896 * smooth((t - 2.0) / 1.2))} m", vis(t, 2.1, en("question") + .2, .3, .4), 52, bg=ORANGE, fg=WHITE)
    qs = pj(cam, *STRIP.centroid.coords[0])
    if qs:
        sx, sy = qs[0], qs[1]
        stamp_text(img, "İRAN", (min(sx + 40 * SS, W - 200 * SS), sy + 330 * SS), FA, 70, fill=(110, 235, 140), stroke=BLACK, alpha=vis(t, cue("intro", "iran") - .1, cue("question", "peki") , .3, .4))
        qa = vis(t, cue("question", "nasıl", "dağ"), en("question") + .1, .3, .3)
        if qa > 0: stamp_text(img, "?", (sx, sy - 80 * SS + math.sin(t * 5) * 8 * SS), FA, 220, fill=WHITE, stroke=BLACK, alpha=qa)
        # isyancılar (beyaz) sınırı geçip İran yamacına kaçar; ardından asker (kırmızı ok)
        t_r = cue("rebels", "isyancılar", "isyanda")
        a_r = vis(t, t_r - .1, en("crisis") + .3, .3, .5)
        if a_r > 0:
            lay = L(); d = ImageDraw.Draw(lay)
            for k in range(6):
                u = clamp01((t - t_r - k * .15) / 1.6); x0, y0 = sx - (330 - k * 12) * SS, sy + (k - 2.5) * 46 * SS
                x1 = sx + 30 * SS; xx = lerp(x0, x1, smooth(u))
                d.ellipse((xx - 13 * SS, y0 - 13 * SS, xx + 13 * SS, y0 + 13 * SS), fill=A(WHITE, a_r), outline=A(BLACK, a_r), width=3 * SS)
            img.alpha_composite(lay)
            hand(img, "isyancılar", sx - 260 * SS, sy - 230 * SS, 72, vis(t, t_r, en("rebels") + .2, .4, .4), WHITE, -5)
        t_c = cue("crisis", "askeri", "türk")
        a_c2 = vis(t, t_c - .1, en("crisis") + .3, .3, .5)
        if a_c2 > 0:
            p0 = (sx - 420 * SS, sy + 40 * SS); p1 = (sx + 10 * SS, sy + 20 * SS)
            curved_arrow(img, p0, p1, a_c2, .2, smooth((t - t_c) / 1.0), KRED, 14)
            t_k = cue("crisis", "kriz")
            if t > t_k: stamp_text(img, "KRİZ!", (sx, sy - 260 * SS), FA, 150, fill=KRED, stroke=WHITE, alpha=a_c2, scale=pop(t, t_k), rot=-8)
        if t > t_g - .2:
            ytag(img, sx - 30 * SS, sy - 250 * SS, "TÜRKİYE'YE", vis(t, t_g, en("gain") + .3, .3, .4), 52, bg=KRED, fg=WHITE, sc=pop(t, t_g))
    # Kotur: İran'a geçen alan
    t_k2 = cue("give", "karşılığında", "iran")
    a_k = vis(t, t_k2, TOTAL, .5, .3)
    if a_k > 0:
        fill_geom(img, cam, KOTUR, (50, 200, 100), a_k * (.6 + .12 * math.sin(t * 3)), fp, simplify=.001, outline=WHITE, ow=3 * SS)
        qk = pj(cam, *KOTUR_C)
        if qk:
            ytag(img, qk[0] + 150 * SS, qk[1] - 120 * SS, "İRAN'A", vis(t, t_k2 + .2, en("give") + .3, .3, .4), 52, bg=(40, 170, 90), fg=WHITE, sc=pop(t, t_k2 + .2))
            typetag(img, qk[0] - 120 * SS, qk[1] + 100 * SS, "KOTUR", t, cue("give", "kotur") , vis(t, cue("give", "kotur"), en("give") + .3, .3, .4), 48, bg=WHITE, fg=BLACK)
            qs2 = pj(cam, *STRIP.centroid.coords[0])
            if qs2 and t > t_k2 + .4:
                a_sw = vis(t, t_k2 + .4, en("give") + .2, .3, .4)
                curved_arrow(img, (qs2[0] - 30 * SS, qs2[1] + 40 * SS), (qk[0] - 30 * SS, qk[1] - 40 * SS), a_sw, .3, smooth((t - t_k2 - .4) / .8), (110, 235, 140), 9)
                curved_arrow(img, (qk[0] + 30 * SS, qk[1] - 40 * SS), (qs2[0] + 30 * SS, qs2[1] + 40 * SS), a_sw, .3, smooth((t - t_k2 - .6) / .8), KRED, 9)
    # Nahçıvan sınırı (1921'den beri)
    a_n = vis(t, st("myth") + .2, en("kars") + .3, .4, .5)
    if a_n > 0 and not NAKH_BORDER.is_empty:
        lay = L(); d = ImageDraw.Draw(lay)
        for g in getattr(NAKH_BORDER, "geoms", [NAKH_BORDER]):
            if g.geom_type != "LineString": continue
            pts = ring_pts(cam, g.coords)
            if len(pts) > 1:
                d.line(pts, fill=A(YEL, a_n * (.35 + .2 * math.sin(t * 5))), width=60 * SS, joint="curve"); d.line(pts, fill=A(YEL, a_n), width=14 * SS, joint="curve")
        img.alpha_composite(lay)
        qn = pj(cam, 44.98, 39.56)
        if qn: stamp_text(img, "NAHÇIVAN", (qn[0], qn[1]), FA, 64, fill=(140, 190, 255), stroke=BLACK, alpha=a_n)
        t_y = cue("myth", "yanlış")
        if t > t_y: stamp_text(img, "YANLIŞ!", (W * .5, 1250 * SS), FA, 130, fill=KRED, stroke=WHITE, alpha=vis(t, t_y, en("myth") + .1, .3, .3), scale=pop(t, t_y), rot=-8)
        hand(img, "takastan önce de vardı", W / 2, 1450 * SS, 74, vis(t, cue("kars", "1921", "beri"), en("kars") + .3, .4, .4), YEL, -5)

def ui(img, t):
    brand.brand_card(img, t, "İKİ ÜLKE,", "BİR DAĞ!", en("intro") - .3)
    t_a = cue("answer", "takasta", "cevap")
    a = vis(t, t_a, en("answer") + .2, .3, .4)
    if a > 0:
        swap_icon(img, W / 2, 1150 * SS, 1.3 * pop(t, t_a), a, t)
        ytag(img, W / 2, 1420 * SS, "TAKAS", a, 64, sc=pop(t, t_a + .1))
    t_t = cue("treaty", "çözüm", "1932")
    a = vis(t, t_t, en("treaty") + .2, .4, .4)
    if a > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (6, 10, 20, int(150 * a))))
        stamp_text(img, "1932", (W / 2, 640 * SS + rise(t, t_t)), FP, 170, fill=(255, 200, 80), stroke=BLACK, alpha=a)
        treaty_card(img, t, cue("treaty", "tahran"), vis(t, cue("treaty", "tahran") - .1, en("treaty") + .2, .3, .4))
        ytag(img, W / 2, 1650 * SS, "TOPRAK TAKASI", vis(t, cue("treaty", "toprak", "takası"), en("treaty") + .2, .3, .4), 60, sc=pop(t, cue("treaty", "toprak", "takası")))
    t_k = cue("kars", "1921", "sınır")
    a = vis(t, t_k, en("kars") + .2, .4, .4)
    if a > 0: stamp_text(img, "1921", (W / 2, 640 * SS + rise(t, t_k)), FP, 160, fill=(255, 200, 80), stroke=BLACK, alpha=a)
    if a > 0: ytag(img, W / 2, 800 * SS, "MOSKOVA + KARS ANTLAŞMALARI", a, 38, bg=WHITE)
    a = vis(t, st("cta") + .3, TOTAL, .5, .3)
    if a > 0:
        hand(img, "Takası kim kazandı?", W / 2, 620 * SS - rise(t, st("cta") + .3) / 2, 86, a, YEL, -6)
        pill(img, "YORUMLARA YAZ!", W / 2, 1460 * SS, 58, alpha=vis(t, cue("cta", "yorumlara"), TOTAL, .4, .3), scale=1)

def frame(t):
    cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
    overlays(img, cam, fp, t)
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
