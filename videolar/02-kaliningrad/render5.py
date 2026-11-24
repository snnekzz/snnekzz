"""Video 2: Kaliningrad – gerçekçi uydu görünümü, 3D eğik kamera, yaratıcı animasyonlar."""
import json, math, os, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
import render as R
import render2 as R2
from render import stamp_text, pill, card, partial, vis, prog, back, eout, ease, FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys
from render3 import A, L, RED, WHITE, YEL, BLACK, VIG, CLOUDS, boat, clamp01
from render4 import globe, sample, EARTH, fractal, Cam, persp_coeffs, GLINT

# ---------- dünya <-> yerel metre ----------
LON0, LAT0D = 22.0, 54.5
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def m2ll(x, y): return (LON0 + x / KX, LAT0D + y / KY)

# ---------- renkler ----------
C_RU = (220, 50, 60); C_LT = (80, 175, 95); C_PL = (175, 150, 235); C_BY = (150, 175, 200)
C_DE = (70, 70, 82); C_USSR = (200, 30, 40); C_NATO = (60, 120, 230)

# ---------- veri ----------
G = json.load(open("countries10_eu.json"))
REG = box(5, 44, 46, 66)
CN = {}
for f in G["features"]:
    g = shape(f["geometry"]).buffer(0).intersection(REG)
    if not g.is_empty: CN[f["properties"]["name"]] = g
RU = CN["Russia"]
KAL = max((p for p in polys(RU) if p.bounds[2] < 23.5 and p.bounds[1] > 54), key=lambda p: p.area)
RU_MAIN = unary_union([p for p in polys(RU) if p.bounds[0] > 26])
PL, LT, BY, LV, EE, UA, DE = CN["Poland"], CN["Lithuania"], CN["Belarus"], CN["Latvia"], CN["Estonia"], CN["Ukraine"], CN["Germany"]
EP_SOUTH = Polygon([(19.25, 54.42), (22.9, 54.42), (22.95, 54.15), (22.75, 53.75), (22.2, 53.45), (21.0, 53.25),
                    (20.2, 53.15), (19.6, 53.3), (19.3, 53.7), (19.15, 54.1)]).intersection(PL)
EPRUSSIA = unary_union([KAL, EP_SOUTH])
USSR = unary_union([RU_MAIN, KAL, BY, LT, LV, EE, UA]).intersection(box(5, 44, 46, 66))
KCITY = (20.51, 54.71); BALTIYSK = (19.91, 54.65)
TRI_KAL = (22.79, 54.36); TRI_BY = (23.50, 53.91)       # Suwałki koridorunun uçları
GAP_LINE = LT.boundary.intersection(PL.boundary)
ROUTE = [(32.05, 54.78), (30.4, 54.5), (28.6, 54.2), (27.56, 53.9), (26.6, 54.3), (25.28, 54.69), (23.9, 54.9),
         (22.6, 54.65), (21.4, 54.7), (20.51, 54.71)]
CROSS = [((31.75, 54.65), "BELARUS"), ((25.75, 54.48), "LİTVANYA"), ((22.7, 54.66), "KALİNİNGRAD")]

# ---------- uydu dokuları ----------
def build_tex(lon0, lon1, lat0, lat1, npx, seed, fname):
    if os.path.exists(fname): return Image.open(fname).convert("RGB")
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1)
    wpx = npx; hpx = int(npx * (y1 - y0) / (x1 - x0)); mpp = (x1 - x0) / wpx
    xs = np.linspace(x0, x1, wpx); ys = np.linspace(y1, y0, hpx)
    X, Y = np.meshgrid(xs, ys); LON = LON0 + X / KX; LAT = LAT0D + Y / KY
    col = sample(EARTH, LON, LAT).astype(np.float32)
    m = Image.new("L", (wpx, hpx), 0); dm = ImageDraw.Draw(m)
    def tp(lon, lat):
        x, y = ll2m(lon, lat); return ((x - x0) / mpp, (y1 - y) / mpp)
    for n, g in CN.items():
        for p in polys(g):
            dm.polygon([tp(*c) for c in p.exterior.coords], fill=255)
    land = np.asarray(m, np.float32) / 255
    shallow = np.asarray(m.filter(ImageFilter.GaussianBlur(max(3, 9000 / mpp))), np.float32) / 255
    n1 = fractal(min(wpx, 2048), 8, seed, k0=3); n1 = np.asarray(Image.fromarray(n1).resize((wpx, hpx), Image.BICUBIC))
    n2 = fractal(min(wpx, 2048), 6, seed + 1, k0=6, gain=0.7); n2 = np.asarray(Image.fromarray(n2).resize((wpx, hpx), Image.BICUBIC))
    fields = np.floor(n2 * 7) / 7
    deep = np.array([22, 78, 150], np.float32); sh = np.array([70, 160, 205], np.float32)
    ocean = deep * (1 - shallow[..., None] * .75) + sh * shallow[..., None] * .75
    ocean *= (0.93 + 0.1 * n1[..., None])
    lc = col * (0.78 + 0.35 * n1[..., None]) * (0.9 + 0.2 * fields[..., None])
    lc = lc * 0.9 + np.array([60, 95, 40]) * 0.1
    mu = lc.mean(-1, keepdims=True); lc = (mu + (lc - mu) * 1.45) * 1.12
    out = ocean * (1 - land[..., None]) + lc * land[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    # ülke sınırları (kıyılar hariç)
    bl = Image.new("L", (wpx, hpx), 0); db = ImageDraw.Draw(bl)
    for n, g in CN.items():
        for p in polys(g):
            db.line([tp(*c) for c in p.exterior.coords], fill=255, width=max(2, int(wpx / 2000)))
    er = Image.fromarray((ndimage.binary_erosion(land > .5, iterations=3) * 255).astype(np.uint8))
    bl = Image.fromarray((np.asarray(bl, np.float32) * np.asarray(er, np.float32) / 255 * 0.55).astype(np.uint8))
    img.paste((245, 245, 245), (0, 0), bl)
    img.save(fname); return img
TEX_BIG = build_tex(6, 42, 46, 64, 4096, 3, "tex_big.png")
TEX_DET = build_tex(18.0, 26.5, 52.6, 56.2, 4096, 7, "tex_det.png")
def tex_info(lon0, lon1, lat0, lat1, img):
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1)
    return dict(img=img, x0=x0, y1=y1, mpp=(x1 - x0) / img.width, box=(x0, y0, x1, y1))
TB = tex_info(6, 42, 46, 64, TEX_BIG); TD = tex_info(18.0, 26.5, 52.6, 56.2, TEX_DET)
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.0

def render_base(cam, t):
    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    g = [cam.ground(x, y) for x, y in corners]
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    use = TD if (min(xs) > TD["box"][0] and max(xs) < TD["box"][2] and min(ys) > TD["box"][1] and max(ys) < TD["box"][3]) else TB
    src = [((x - use["x0"]) / use["mpp"], (use["y1"] - y) / use["mpp"]) for x, y in g]
    img = use["img"].transform((W, H), Image.PERSPECTIVE, persp_coeffs(src, corners), Image.BICUBIC, fillcolor=(22, 78, 150))
    pf = clamp01((math.degrees(math.acos(-cam.fw[2])) - 8) / 45)
    hz = (HAZE * 70 * pf).astype(np.uint8)
    img.paste((200, 220, 240), (0, 0), Image.fromarray(np.repeat(hz[:, None], W, 1)))
    return img.convert("RGBA"), g

# ---------- kamera ----------
def lerp(a, b, p): return a + (b - a) * p
T_GLOBE = 2.6
K = [  # (zaman, lon, lat, D km, pitch°, yaw°)
    (T_GLOBE - .3, 24.0, 55.6, 3600, 0, 0),
    (st("intro") + 3.2, 26.5, 55.0, 2900, 22, 0),
    (st("name") + .2, 21.2, 54.6, 700, 35, 0),
    (st("route"), 26.2, 54.4, 2700, 18, 0),
    (st("why") + .5, 26.0, 54.4, 2600, 20, 2),
    (st("konigsberg") + .3, 21.0, 54.15, 900, 30, 0),
    (st("split2") + 2, 21.0, 54.05, 850, 34, 4),
    (st("rename") + 1, 20.9, 54.6, 520, 34, 4),
    (st("ussr") + .3, 28.0, 55.0, 3300, 20, 0),
    (st("collapse") + 3, 28.0, 55.0, 3400, 24, 0),
    (st("cut") + .3, 23.0, 54.9, 1350, 30, 0),
    (st("fleet") + .4, 19.74, 54.70, 150, 48, 0),
    (st("gap") + 1.4, 23.15, 54.05, 300, 52, -12),
    (st("gapname") + .5, 23.15, 54.1, 260, 54, -2),
    (st("cta") + .6, 22.4, 54.5, 1100, 32, 4),
    (TOTAL, 22.4, 54.55, 1300, 30, 6),
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
    return Cam(x, y, D, math.radians(lerp(a[4], b[4], p)), math.radians(lerp(a[5], b[5], p) + 2 * math.sin(t * .2)))

# ---------- projeksiyon yardımcıları ----------
def pj(cam, lon, lat, z=0.0):
    x, y = ll2m(lon, lat); return cam.proj(x, y, z)
def footprint(gpts):
    poly = Polygon([m2ll(x, y) for x, y in gpts]).buffer(0.3)
    return poly
def ring_pts(cam, coords, dx=0, dy=0):
    out = []
    for lon, lat in coords:
        q = pj(cam, lon, lat)
        if q: out.append((q[0] + dx, q[1] + dy))
    return out
def fill_geom(img, cam, geom, color, alpha, fp, dx=0, dy=0, outline=None, ow=0, simplify=0.01):
    if alpha <= .01 or geom.is_empty: return
    g = geom.intersection(fp)
    if g.is_empty: return
    g = g.simplify(simplify)
    lay = L(); d = ImageDraw.Draw(lay)
    for p in polys(g):
        pts = ring_pts(cam, p.exterior.coords, dx, dy)
        if len(pts) > 2:
            d.polygon(pts, fill=A(color, alpha))
            if outline: d.line(pts + [pts[0]], fill=A(outline, min(1, alpha * 2.2)), width=ow, joint="curve")
    img.alpha_composite(lay)
def glow_outline(img, cam, geom, color, a, fp, width=5):
    if a <= .01: return
    g = geom.intersection(fp).simplify(0.005)
    lay = L(); d = ImageDraw.Draw(lay)
    for p in polys(g):
        pts = ring_pts(cam, p.exterior.coords)
        if len(pts) > 2:
            d.line(pts + [pts[0]], fill=A(color, a * .35), width=width * 4 * SS, joint="curve")
            d.line(pts + [pts[0]], fill=A(color, a), width=width * SS, joint="curve")
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.5)))
def lab(img, cam, text, lon, lat, size, a, col=WHITE, sc=1., rot=0):
    if a <= .01: return
    q = pj(cam, lon, lat)
    if q: stamp_text(img, text, (q[0], q[1]), FA, size, fill=col, stroke=BLACK, alpha=a, scale=sc, rot=rot)


# ---------- Haritalogy tarzı yardımcılar ----------
def raised(img, cam, geom, color, a, fp, lift=9, simplify=0.01, dx=0, dy=0, outline=WHITE, fill_a=.88):
    """beyaz kenarlı, gölgeli, haritadan 'kalkmış' ülke"""
    if a <= .01 or geom.is_empty: return
    g = geom.intersection(fp)
    if g.is_empty: return
    g = g.simplify(simplify)
    rings = [ring_pts(cam, p.exterior.coords, dx, dy) for p in polys(g)]
    rings = [r for r in rings if len(r) > 2]
    if not rings: return
    sh = Image.new("L", (W // 4, H // 4), 0); ds = ImageDraw.Draw(sh)
    for r in rings: ds.polygon([((x + 6 * SS) / 4, (y + 12 * SS) / 4) for x, y in r], fill=int(150 * a))
    sh = sh.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    img.paste((0, 0, 0), (0, 0), sh)
    lay = L(); d = ImageDraw.Draw(lay); up = lift * SS * a
    for r in rings:
        rr = [(x, y - up) for x, y in r]
        d.polygon(rr, fill=A(color, fill_a * a))
        d.line(rr + [rr[0]], fill=A(outline, a), width=5 * SS, joint="curve")
    img.alpha_composite(lay)
def flag_draw(kind, w, h):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    if kind == "russia": cols = [(255, 255, 255), (0, 57, 166), (213, 43, 30)]
    elif kind == "lithuania": cols = [(253, 185, 19), (0, 106, 68), (193, 39, 45)]
    elif kind == "poland": cols = [(255, 255, 255), (220, 20, 60)]
    elif kind == "germany": cols = [(0, 0, 0), (221, 0, 0), (255, 206, 0)]
    elif kind == "belarus": cols = [(200, 49, 58), (200, 49, 58), (0, 140, 70)]
    else: cols = [(200, 200, 200)]
    n = len(cols)
    for i, c in enumerate(cols): d.rectangle((0, i * h / n, w, (i + 1) * h / n), fill=c)
    if kind == "belarus": d.rectangle((0, 0, w * .16, h), fill=(255, 255, 255)); d.rectangle((w * .04, 0, w * .12, h), fill=(200, 49, 58))
    return im
def flag_pin(img, x, y, kind, a, sc=1.0):
    if a <= .01 or sc <= .01: return
    r = int(46 * SS * sc)
    lay = Image.new("RGBA", (r * 2 + 40, r * 3 + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = r + 20, r + 20
    d.ellipse((cx - r + 6, cy - r + 14, cx + r + 6, cy + r + 14), fill=(0, 0, 0, int(90 * a)))
    d.polygon([(cx - r * .45, cy + r * .7), (cx + r * .45, cy + r * .7), (cx, cy + r * 1.55)], fill=A(WHITE, a))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=A(WHITE, a))
    fl = flag_draw(kind, 2 * r - 12, 2 * r - 12).convert("RGBA")
    m = Image.new("L", fl.size, 0); ImageDraw.Draw(m).ellipse((0, 0, fl.width - 1, fl.height - 1), fill=int(255 * a)); fl.putalpha(m)
    lay.alpha_composite(fl, (cx - r + 6, cy - r + 6))
    img.alpha_composite(lay, (int(x - cx), int(y - cy - r * 1.55)))
def tag(img, x, y, text, a, sc=1.0, bg=RED, rot=-4, size=64):
    if a <= .01 or sc <= .01: return
    f = font(FA, size * SS * sc); l, t_, r, b = f.getbbox(text)
    w, h = r - l + 50 * SS * sc, b - t_ + 34 * SS * sc
    lay = Image.new("RGBA", (int(w) + 40, int(h) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((26, 30, w + 26, h + 30), radius=int(18 * SS * sc), fill=(0, 0, 0, int(110 * a)))
    d.rounded_rectangle((20, 20, w + 20, h + 20), radius=int(18 * SS * sc), fill=A(bg, a), outline=A(WHITE, a), width=int(6 * SS * sc))
    d.text((20 + w / 2, 20 + h / 2), text, font=f, fill=A(WHITE, a), anchor="mm")
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def curved_arrow(img, p0, p1, a, bend=.25, prog_=1.0, col=WHITE, width=6):
    if a <= .01 or prog_ <= 0: return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0])
    c = (mx + nx * bend, my + ny * bend)
    pts = [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])
           for u in np.linspace(0, prog_, 40)]
    lay = L(); d = ImageDraw.Draw(lay)
    d.line(pts, fill=A((0, 0, 0), a * .4), width=(width + 4) * SS, joint="curve")
    d.line(pts, fill=A(col, a), width=width * SS, joint="curve")
    h, q = pts[-1], pts[-3]; ang = math.atan2(h[1] - q[1], h[0] - q[0]); s = width * 4 * SS
    d.polygon([(h[0] + math.cos(ang) * s, h[1] + math.sin(ang) * s), (h[0] + math.cos(ang + 2.4) * s, h[1] + math.sin(ang + 2.4) * s),
               (h[0] + math.cos(ang - 2.4) * s, h[1] + math.sin(ang - 2.4) * s)], fill=A(col, a))
    img.alpha_composite(lay)
def cam_D(t):
    c = cam_at(t); return float(np.linalg.norm(c.C - c.T))
def zoom_blur(img, t):
    if t < T_GLOBE + .05: return img
    sp = abs(math.log(cam_D(t + .04)) - math.log(cam_D(t - .04))) / .08
    k = clamp01((sp - .7) / 2.0)
    if k < .05: return img
    sm = img.convert("RGB").resize((OW, OH), Image.BILINEAR)
    acc = np.asarray(sm, np.float32); n = 1
    for i in range(1, 6):
        f = 1 + .012 * i * k
        z = sm.resize((int(OW * f), int(OH * f)), Image.BILINEAR)
        ox, oy = (z.width - OW) // 2, (z.height - OH) // 2
        acc += np.asarray(z.crop((ox, oy, ox + OW, oy + OH)), np.float32); n += 1
    out = Image.fromarray((acc / n).astype(np.uint8)).resize((W, H), Image.BILINEAR).convert("RGBA")
    return Image.blend(img, out, min(.75, k * 1.0))

# ---------- yaratıcı ikonlar ----------
def car(d, x, y, s, a, ang):
    s *= SS
    def rp(px, py):
        return (x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang))
    body = [rp(-34 * s, -15 * s), rp(34 * s, -15 * s), rp(38 * s, 15 * s), rp(-38 * s, 15 * s)]
    d.polygon([(px + 6 * s, py + 8 * s) for px, py in body], fill=(0, 0, 0, int(90 * a)))
    d.polygon(body, fill=A((240, 240, 240), a), outline=A(BLACK, a))
    d.polygon([rp(-14 * s, -12 * s), rp(16 * s, -12 * s), rp(16 * s, 12 * s), rp(-14 * s, 12 * s)], fill=A((60, 90, 130), a))
    for px in (-24, 24):
        for py in (-17, 17):
            cx, cy = rp(px * s, py * s); d.ellipse((cx - 5 * s, cy - 3 * s, cx + 5 * s, cy + 3 * s), fill=A(BLACK, a))
def stamp(img, x, y, text, a, sc, rot):
    if a <= .01 or sc <= .01: return
    s = SS * sc
    f = font(FA, 40 * s); tw = f.getlength(text)
    r = max(tw / 2 + 30 * s, 90 * s)
    lay = Image.new("RGBA", (int(r * 2 + 20), int(r * 2 + 20)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    c = lay.width / 2; ink = (200, 30, 45, int(230 * a))
    d.ellipse((10, 10, lay.width - 10, lay.height - 10), outline=ink, width=int(7 * s))
    d.ellipse((24 * s, 24 * s, lay.width - 24 * s, lay.height - 24 * s), outline=ink, width=int(3 * s))
    d.text((c, c - 8 * s), text, font=f, fill=ink, anchor="mm")
    d.text((c, c + 34 * s), "GEÇİŞ", font=font(F9, 22 * s), fill=ink, anchor="mm")
    lay = lay.rotate(rot, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))
def castle(d, x, y, s, a):
    s *= SS; c = A((235, 225, 205), a); o = A((60, 50, 40), a)
    d.rectangle((x - 60 * s, y - 40 * s, x + 60 * s, y + 30 * s), fill=c, outline=o, width=int(3 * s))
    for tx in (-60, 40):
        d.rectangle((x + tx * s, y - 85 * s, x + (tx + 20) * s, y + 30 * s), fill=c, outline=o, width=int(3 * s))
        d.polygon([(x + (tx - 4) * s, y - 85 * s), (x + (tx + 24) * s, y - 85 * s), (x + (tx + 10) * s, y - 115 * s)], fill=A((170, 60, 50), a), outline=o)
    for k in range(-50, 50, 20):
        d.rectangle((x + k * s, y - 52 * s, x + (k + 10) * s, y - 40 * s), fill=c, outline=o)
    d.rectangle((x - 12 * s, y - 2 * s, x + 12 * s, y + 30 * s), fill=A((70, 50, 35), a))
def warship(d, x, y, s, a):
    s *= SS; hull = A((95, 105, 115), a); o = A((30, 35, 40), a)
    d.polygon([(x - 90 * s, y), (x + 100 * s, y), (x + 80 * s, y + 20 * s), (x - 80 * s, y + 20 * s)], fill=hull, outline=o)
    d.rectangle((x - 30 * s, y - 28 * s, x + 25 * s, y), fill=hull, outline=o)
    d.rectangle((x - 15 * s, y - 50 * s, x + 8 * s, y - 28 * s), fill=hull, outline=o)
    d.line([(x - 4 * s, y - 50 * s), (x - 4 * s, y - 75 * s)], fill=o, width=int(3 * s) + 1)
    d.line([(x + 40 * s, y - 8 * s), (x + 75 * s, y - 14 * s)], fill=o, width=int(5 * s))
    d.rectangle((x + 32 * s, y - 14 * s, x + 50 * s, y), fill=hull, outline=o)
    for k in range(3):
        d.line([(x - 90 * s - k * 30 * s, y + 20 * s + k * 6 * s), (x - 60 * s - k * 30 * s, y + 18 * s + k * 6 * s)],
               fill=(235, 245, 255, int(120 * a / (k + 1))), width=int(3 * s))
def person(d, x, y, s, a):
    s *= SS; c = A((245, 240, 230), a)
    d.ellipse((x - 7 * s, y - 34 * s, x + 7 * s, y - 20 * s), fill=c)
    d.rounded_rectangle((x - 10 * s, y - 18 * s, x + 10 * s, y + 8 * s), radius=int(6 * s), fill=c)
def kant_card(img, cx, cy, a, sc):
    if a <= .01 or sc <= .01: return
    s = SS * sc; w, h = 520 * s, 230 * s
    lay = Image.new("RGBA", (int(w) + 10, int(h) + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((5, 5, w, h), radius=int(26 * s), fill=(250, 246, 236, int(240 * a)), outline=(40, 35, 30, int(255 * a)), width=int(4 * s))
    hx, hy = 110 * s, 115 * s
    d.ellipse((hx - 48 * s, hy - 72 * s, hx + 48 * s, hy + 18 * s), fill=(70, 60, 55, int(255 * a)))
    d.pieslice((hx - 80 * s, hy + 10 * s, hx + 80 * s, hy + 150 * s), 180, 360, fill=(70, 60, 55, int(255 * a)))
    d.text((210 * s, 85 * s), "IMMANUEL KANT", font=font(FA, 52 * s), fill=(30, 25, 20, int(255 * a)), anchor="lm")
    d.text((210 * s, 150 * s), "Filozof • Königsberg, 1724", font=font(F9, 26 * s), fill=(110, 90, 70, int(255 * a)), anchor="lm")
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

YEARS = [("1255", "konigsberg"), ("1945", "split"), ("1991", "collapse"), ("BUGÜN", "fleet")]
def timeline(img, t):
    a = vis(t, st("konigsberg") - .2, en("gap") - .5, .4, .4)
    if a <= 0: return
    lay = L(); d = ImageDraw.Draw(lay); xs = [190 * SS + i * 700 * SS / 3 for i in range(4)]; y = 300 * SS
    d.line([(xs[0], y), (xs[-1], y)], fill=A((150, 158, 170), a), width=6 * SS)
    cur = max([i for i, (_, sc) in enumerate(YEARS) if t >= st(sc)] or [0])
    d.line([(xs[0], y), (xs[cur], y)], fill=A(RED, a), width=8 * SS)
    for i, (yr, sc) in enumerate(YEARS):
        on = i <= cur; r = (20 if i == cur else 13) * SS
        d.ellipse((xs[i] - r, y - r, xs[i] + r, y + r), fill=A(RED if on else (100, 108, 120), a), outline=A(WHITE, a), width=3 * SS)
        d.text((xs[i], y + 52 * SS), yr, font=font(FA, (52 if i == cur else 38) * SS), fill=A(WHITE if on else (170, 178, 190), a), anchor="mm",
               stroke_width=3 * SS, stroke_fill=(0, 0, 0, int(200 * a)))
    img.alpha_composite(lay)
def header(img, t):
    a = vis(t, .15, en("name") + .1, .3, .4)
    if a <= 0: return
    sc = .9 + .1 * back(prog(t, .15, .35))
    lay = Image.new("RGBA", (W, 260 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 820 * SS * sc, 180 * SS * sc; x0, y0 = W / 2 - w / 2, 130 * SS - h / 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(36 * SS), fill=(0, 0, 0, 210), outline=A(RED, 1), width=4 * SS)
    d.text((W / 2, y0 + h * .31), "RUSYA'NIN", font=font(FA, 64 * SS * sc), fill=WHITE, anchor="mm")
    d.text((W / 2, y0 + h * .71), "KOPUK TOPRAĞI", font=font(FA, 76 * SS * sc), fill=RED, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, 150 * SS))
def typewriter(img, t, text, t0, t1, y, size, col=WHITE):
    a = vis(t, t0, t1, .1, .4)
    if a <= 0: return
    n = len(text) if t > t0 + .9 else max(1, int(len(text) * clamp01((t - t0) / .9)))
    stamp_text(img, text[:n], (W / 2, y * SS), FA, size, fill=col, alpha=a)
    if t > t0 + .9:
        tw = font(FA, size * SS).getlength(text); u = eout(prog(t, t0 + .9, .4))
        lay = L(); ImageDraw.Draw(lay).line([(W / 2 - tw / 2 * u, (y + size * .62) * SS), (W / 2 + tw / 2 * u, (y + size * .62) * SS)], fill=A(RED, a), width=8 * SS)
        img.alpha_composite(lay)

# ---------- kare ----------
def frame(t):
    if t < T_GLOBE:
        p = ease(t / T_GLOBE)
        lon, lat = lerp(-5, 24, p), lerp(32, 55.6, p)
        Rpx = math.exp(lerp(math.log(420), math.log(2200), ease(p ** 1.3)))
        img = globe(lon, lat, Rpx, t).resize((W, H), Image.BICUBIC).convert("RGBA")
        if t > T_GLOBE - .45:
            cam = cam_at(T_GLOBE - .3); b, _ = render_base(cam, t)
            img = Image.blend(img, b, clamp01((t - (T_GLOBE - .45)) / .45))
        cam = None; fp = None
    else:
        cam = cam_at(t); img, g = render_base(cam, t); fp = footprint(g)
    if cam is not None:
        overlays(img, cam, fp, t)
        img = zoom_blur(img, t)
    # bulut/sis
    a_cl = .06 if cam is not None else 0
    if a_cl:
        off = int((t * 40 * SS) % W); img.paste((240, 244, 250), (0, 0), CLOUDS.crop((off, 0, off + W, H)).point(lambda v: int(v * a_cl)))
    ui(img, cam, t)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * (.14 + .3 * vis(t, st("cut"), en("cut") + .3, .4, .6)))))
    R2.caption(img, t)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .6, .6))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1: out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def overlays(img, cam, fp, t):
    # --- Rusya ana kara + Kaliningrad (giriş, isim, rota) ---
    a_ru = vis(t, T_GLOBE, st("konigsberg") - .3, .5, .5)
    raised(img, cam, RU_MAIN, C_RU, a_ru, fp, lift=8, simplify=0.05, fill_a=.80)
    pul = .5 + .5 * math.sin(t * 5)
    a_k = vis(t, st("intro") + 1.6, st("konigsberg") - .3, .4, .5)
    glow_outline(img, cam, KAL, (255, 120, 120), a_k * (.4 + .4 * pul), fp)
    raised(img, cam, KAL, C_RU, a_k, fp, lift=10 + 4 * pul)
    # --- rota: Rusya -> Belarus -> Litvanya -> Kaliningrad ---
    a_r = vis(t, st("route") + .2, en("why") + .2, .3, .5)
    if a_r > 0:
        raised(img, cam, BY, C_BY, a_r, fp, lift=6, fill_a=.75)
        raised(img, cam, LT, C_LT, a_r, fp, lift=6, fill_a=.80)
        pr = ease(prog(t, st("route") + .4, en("route") - st("route") - .4))
        dense = []
        for a_, b_ in zip(ROUTE[:-1], ROUTE[1:]):
            for k in range(12): dense.append((lerp(a_[0], b_[0], k / 12), lerp(a_[1], b_[1], k / 12)))
        dense.append(ROUTE[-1])
        part = partial(dense, pr)
        pts = ring_pts(cam, part)
        lay = L(); d = ImageDraw.Draw(lay)
        if len(pts) > 1:
            d.line(pts, fill=A((20, 20, 25), a_r), width=14 * SS, joint="curve")
            R.dashed(d, pts, A(YEL, a_r), 6 * SS, 18, 14)
            q2 = part[-2] if len(part) > 1 else part[-1]
            p1 = pj(cam, *part[-1]); p0 = pj(cam, *q2)
            if p1 and p0:
                car(d, p1[0], p1[1], 1.25, a_r, math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
        img.alpha_composite(lay)
        for k, ((lon, lat), name) in enumerate(CROSS):
            # aracın sınırı geçtiği an
            idx = min(range(len(dense)), key=lambda i: (dense[i][0] - lon) ** 2 + (dense[i][1] - lat) ** 2)
            tc = st("route") + .4 + (idx / len(dense)) * (en("route") - st("route") - .4)
            if t > tc:
                q = pj(cam, lon, lat)
                if q: stamp(img, q[0], q[1] + (-110 if k % 2 == 0 else 110) * SS, name, a_r, .78 * back(prog(t, tc, .3)) * (1.4 - .4 * eout(prog(t, tc, .25))), [-12, 9, -6][k])
    # --- Doğu Prusya / Königsberg ---
    a_ep = vis(t, st("konigsberg") + .2, st("split") + .2, .5, .3)
    raised(img, cam, EPRUSSIA, C_DE, a_ep, fp, lift=8, fill_a=.75)
    a_c = vis(t, st("konigsberg") + .5, st("rename") + .1, .4, .4)
    if a_c > 0:
        q = pj(cam, *KCITY)
        if q:
            lay = L(); castle(ImageDraw.Draw(lay), q[0], q[1] - 40 * SS, 1.15 * back(prog(t, st("konigsberg") + .5, .45)), a_c)
            img.alpha_composite(lay)
    # --- bölünme ---
    a_s = vis(t, st("split") + .1, en("rename") + .3, .3, .4)
    if a_s > 0:
        cutp = eout(prog(t, st("split") + .6, 1.6))
        sep = eout(prog(t, st("split2") + .1, .7)) * (1 - eout(prog(t, st("split2") + 2.0, .8))) * 34 * SS
        colN = tuple(int(lerp(C_DE[i], C_RU[i], eout(prog(t, st("split2") + 1.2, .6)))) for i in range(3))
        colS = tuple(int(lerp(C_DE[i], C_PL[i], eout(prog(t, st("split2") + .2, .6)))) for i in range(3))
        raised(img, cam, KAL, colN, a_s, fp, lift=8, dy=-sep, fill_a=.82)
        raised(img, cam, EP_SOUTH, colS, a_s, fp, lift=8, dy=sep, fill_a=.82)
        # kesik çizgisi + makas
        cl = [(19.2 + k * (3.75 / 40), 54.38 + 0.03 * math.sin(k)) for k in range(41)]
        pts = ring_pts(cam, partial(cl, cutp))
        if len(pts) > 1 and t < en("split") + .6:
            lay = L(); d = ImageDraw.Draw(lay); R.dashed(d, pts, A(WHITE, a_s), 6 * SS, 16, 12)
            x, y = pts[-1]; s = 26 * SS; ang = t * 18
            for sg in (1, -1):
                d.line([(x, y), (x - 44 * SS, y + sg * (14 + 10 * math.sin(ang)) * SS)], fill=A((220, 220, 230), a_s), width=6 * SS)
                d.ellipse((x - 64 * SS, y + sg * (14 + 10 * math.sin(ang)) * SS - 12 * SS, x - 40 * SS, y + sg * (14 + 10 * math.sin(ang)) * SS + 12 * SS), outline=A(RED, a_s), width=5 * SS)
            img.alpha_composite(lay)
        a2 = vis(t, st("split2") + .3, en("split2") + .3, .3, .3)
        lab(img, cam, "POLONYA", 21.0, 53.75, 54, a2, C_PL)
        a3 = vis(t, st("split2") + 1.3, en("split2") + .3, .3, .3)
        lab(img, cam, "SSCB", 21.0, 54.95, 54, a3, (255, 140, 140))
    # --- isim değişimi + göç ---
    a_n = vis(t, st("rename") + .1, en("rename") + .2, .3, .3)
    if a_n > 0:
        q = pj(cam, *KCITY)
        if q:
            stamp_text(img, "KÖNIGSBERG", (q[0], q[1] - 150 * SS), FA, 66, fill=WHITE, stroke=BLACK, alpha=a_n * (1 - eout(prog(t, st("rename") + 1.15, .3))))
            sp = eout(prog(t, st("rename") + .5, .7))
            if sp > 0 and t < st("rename") + 1.45:
                f = font(FA, 62 * SS); tw = f.getlength("KÖNIGSBERG")
                lay = L(); ImageDraw.Draw(lay).line([(q[0] - tw / 2, q[1] - 148 * SS), (q[0] - tw / 2 + tw * sp, q[1] - 148 * SS)], fill=A(RED, a_n * (1 - eout(prog(t, st("rename") + 1.15, .3)))), width=9 * SS)
                img.alpha_composite(lay)
            if t > st("rename") + 1.5:
                txt = "KALİNİNGRAD"; n = max(1, int(len(txt) * clamp01((t - st("rename") - 1.5) / .6)))
                stamp_text(img, txt[:n], (q[0], q[1] - 150 * SS), FA, 72, fill=(255, 150, 150), stroke=BLACK, alpha=a_n)
            # batıya göç eden insanlar
            lay = L(); d = ImageDraw.Draw(lay)
            for k in range(9):
                pp = prog(t, st("rename") + 1.6 + k * .12, 1.6)
                if 0 < pp < 1:
                    x = q[0] - pp * 520 * SS - (k % 3) * 30 * SS; y = q[1] + (k // 3 - 1) * 46 * SS - 40 * SS
                    person(d, x, y, 1.1, (1 - pp) * a_n)
            img.alpha_composite(lay)
    # --- SSCB bloğu ve dağılma ---
    a_u = vis(t, st("ussr") + .2, en("collapse") + .4, .5, .4)
    if a_u > 0:
        crack = eout(prog(t, st("collapse") + .6, .6)); expl = eout(prog(t, st("collapse") + 1.2, 1.0))
        if crack < 1 and expl == 0:
            raised(img, cam, USSR, C_USSR, a_u, fp, lift=8, simplify=0.05, fill_a=.78)
        cen = pj(cam, 30, 55)
        parts = [(RU_MAIN, C_RU), (KAL, C_RU), (BY, C_BY), (LT, C_LT), (LV, (200, 120, 130)), (EE, (110, 150, 210)), (UA, (230, 200, 80))]
        if crack > 0:
            for geom, col in parts:
                c = geom.intersection(fp).centroid if not geom.intersection(fp).is_empty else None
                if c is None or c.is_empty: continue
                q = pj(cam, c.x, c.y)
                if not q or not cen: continue
                vx, vy = q[0] - cen[0], q[1] - cen[1]; nrm = math.hypot(vx, vy) + 1e-6
                off = expl * (1 - eout(prog(t, en("collapse") - .6, .8))) * 46 * SS
                colm = tuple(int(lerp(C_USSR[i], col[i], expl)) for i in range(3))
                raised(img, cam, geom, colm, a_u, fp, lift=8 + 10 * expl, dx=vx / nrm * off, dy=vy / nrm * off, simplify=0.05, fill_a=.80)
            if expl < .5:   # çatlak çizgileri
                lay = L(); d = ImageDraw.Draw(lay); rnd = random.Random(3)
                for geom in (BY, LT, LV, EE, UA):
                    for p in polys(geom.intersection(fp).simplify(0.08)):
                        pts = ring_pts(cam, p.exterior.coords)
                        if len(pts) > 2:
                            jag = [(x + rnd.uniform(-6, 6) * SS, y + rnd.uniform(-6, 6) * SS) for x, y in pts]
                            d.line(jag, fill=A(WHITE, crack * (1 - expl * 2)), width=4 * SS)
                img.alpha_composite(lay)
        a_l = vis(t, st("ussr") + .6, st("collapse") + .8, .3, .3)
        lab(img, cam, "SOVYETLER BİRLİĞİ", 30.0, 56.2, 64, a_l, (255, 170, 170))
        a_lt = vis(t, st("collapse") + 1.6, en("collapse") + .2, .3, .3)
        lab(img, cam, "LİTVANYA", 24.0, 55.35, 56, a_lt, (170, 240, 170), sc=back(prog(t, st("collapse") + 1.6, .4)))
    # --- kopuk Kaliningrad ---
    a_ct = vis(t, st("cut") - .1, st("fleet") + .2, .4, .4)
    if a_ct > 0:
        raised(img, cam, LT, C_LT, a_ct, fp, lift=5, fill_a=.70)
        raised(img, cam, BY, C_BY, a_ct, fp, lift=5, fill_a=.65)
        glow_outline(img, cam, KAL, (255, 110, 110), a_ct * (.5 + .4 * pul), fp, 6)
        raised(img, cam, KAL, C_RU, a_ct, fp, lift=12 + 5 * pul)
        q = pj(cam, 21.2, 54.75); rr = (210 + 20 * math.sin(t * 3)) * SS
        if q and t < en("cut") + .6:
            lay = L(); d = ImageDraw.Draw(lay); n = 40
            for k in range(0, n, 2):
                a0 = k / n * 360 + t * 20
                d.arc((q[0] - rr, q[1] - rr * .7, q[0] + rr, q[1] + rr * .7), a0, a0 + 360 / n, fill=A(WHITE, a_ct * .9), width=5 * SS)
            img.alpha_composite(lay)
    # --- Baltık Filosu ---
    a_f = vis(t, st("fleet") + .3, en("fleet") + .4, .4, .4)
    if a_f > 0:
        lay = L(); d = ImageDraw.Draw(lay)
        for k, (lon, lat) in enumerate([(19.72, 54.68), (19.80, 54.79), (19.62, 54.83)]):
            q = pj(cam, lon + .02 * math.sin(t * .4 + k), lat)
            if q: warship(d, q[0], q[1], 220000 / q[2] * back(prog(t, st("fleet") + .3 + k * .2, .4)), a_f)
        img.alpha_composite(lay)
        q = pj(cam, *BALTIYSK)
        if q:
            pill(img, "BALTIK FİLOSU", q[0] + 60 * SS, q[1] - 260 * SS, 54, bg=WHITE, fg=BLACK, alpha=a_f, scale=back(prog(t, st("fleet") + .8, .35)))
    # --- Suwałki koridoru ---
    a_g = vis(t, st("gap") + .3, TOTAL, .5, .4)
    if a_g > 0:
        raised(img, cam, PL, C_PL, a_g, fp, lift=5, fill_a=.55, simplify=0.004)
        raised(img, cam, LT, C_LT, a_g, fp, lift=5, fill_a=.55, simplify=0.004)
        raised(img, cam, KAL, C_RU, a_g, fp, lift=9, fill_a=.80, simplify=0.004)
        raised(img, cam, BY, C_BY, a_g, fp, lift=9, fill_a=.80, simplify=0.004)
        # parlayan koridor bandı
        corr = LineString([TRI_KAL, (23.2, 54.16), TRI_BY]).buffer(0.10)
        pc = .55 + .45 * math.sin(t * 4)
        fill_geom(img, cam, corr, (255, 220, 80), (.25 + .25 * pc) * a_g * eout(prog(t, st("gap") + 1.2, .8)), fp, simplify=0.002)
        glow_outline(img, cam, corr, (255, 220, 80), a_g * eout(prog(t, st("gap") + 1.2, .8)) * pc, fp, 4)
        # ölçü çizgisi
        pm = eout(prog(t, st("gap") + 2.4, .8))
        p0 = pj(cam, *TRI_KAL); p1 = pj(cam, *TRI_BY)
        if p0 and p1 and pm > 0:
            lay = L(); d = ImageDraw.Draw(lay); xm, ym = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            ex0 = (lerp(xm, p0[0], pm), lerp(ym, p0[1], pm)); ex1 = (lerp(xm, p1[0], pm), lerp(ym, p1[1], pm))
            R.arrow(d, (xm, ym), ex0, A(WHITE, a_g), 6 * SS); R.arrow(d, (xm, ym), ex1, A(WHITE, a_g), 6 * SS)
            img.alpha_composite(lay)
            pill(img, "65 KM", xm + 150 * SS, ym, 60, bg=YEL, alpha=a_g * pm, scale=back(prog(t, st("gap") + 2.6, .35)))
        # sıkıştıran oklar
        pa = vis(t, st("gap") + 3.6, en("gapname") + .3, .4, .4)
        if pa > 0:
            lay = L(); d = ImageDraw.Draw(lay)
            for src, dst in (((21.6, 54.75), (22.75, 54.42)), ((24.6, 53.4), (23.55, 53.85))):
                a0 = pj(cam, *src); a1 = pj(cam, *dst)
                if a0 and a1:
                    k = .85 + .15 * math.sin(t * 6); a1 = (lerp(a0[0], a1[0], k), lerp(a0[1], a1[1], k))
                    R.arrow(d, (a0[0], a0[1]), a1, A(RED, pa), 14 * SS)
            img.alpha_composite(lay)
        lab(img, cam, "KALİNİNGRAD", 21.4, 54.98, 50, a_g, (255, 160, 160))
        lab(img, cam, "BELARUS", 24.9, 53.55, 50, a_g, (210, 225, 240))
        lab(img, cam, "POLONYA", 21.9, 53.75, 50, a_g, (215, 200, 255))
        lab(img, cam, "LİTVANYA", 23.9, 54.85, 50, a_g, (180, 245, 180))
        na = vis(t, st("gap") + 4.5, TOTAL, .3, .3)
        lab(img, cam, "NATO", 22.2, 53.55, 40, na, (140, 190, 255)); lab(img, cam, "NATO", 24.1, 54.6, 40, na, (140, 190, 255))
    # --- Haritalogy tarzı iğneler / etiketler ---
    qk = pj(cam, *KCITY)
    a_pin = vis(t, st("name") - .1, st("konigsberg") - .2, .3, .3)
    if qk: flag_pin(img, qk[0], qk[1], "russia", a_pin, back(prog(t, st("name") - .1, .4)))
    a_rp = vis(t, st("route") + .2, en("why") + .1, .3, .3)
    for kind, ll, d0 in (("belarus", (27.56, 53.9), .3), ("lithuania", (25.28, 54.69), .5)):
        q = pj(cam, *ll)
        if q: flag_pin(img, q[0], q[1], kind, a_rp, .8 * back(prog(t, st("route") + d0, .4)))
    a_gp = vis(t, st("gap") + .8, TOTAL, .3, .3)
    for kind, ll, d0 in (("russia", (21.0, 54.62), .8), ("belarus", (24.6, 53.8), 1.0), ("poland", (22.4, 53.95), 1.2), ("lithuania", (23.7, 54.6), 1.4)):
        q = pj(cam, *ll)
        if q: flag_pin(img, q[0], q[1], kind, a_gp, .75 * back(prog(t, st("gap") + d0, .4)))
    # göç: Königsberg'den batıya kavisli ok
    a_m = vis(t, st("rename") + 1.6, en("rename") + .2, .3, .3)
    if qk and a_m > 0:
        curved_arrow(img, (qk[0] - 30 * SS, qk[1] + 40 * SS), (qk[0] - 520 * SS, qk[1] + 120 * SS), a_m, .3, eout(prog(t, st("rename") + 1.6, .8)))
    # --- genel etiketler ---
    a_n = vis(t, T_GLOBE + .2, st("route") + 1, .4, .4)
    lab(img, cam, "RUSYA", 31.0, 55.9, 76, a_n * .95, (255, 170, 170))
    q = pj(cam, 21.0, 55.15); a_t = vis(t, st("name") - .2, st("route") + 1, .3, .4)
    if q: tag(img, q[0], q[1], "KALİNİNGRAD", a_t, back(prog(t, st("name") - .2, .4)), size=56)
    lab(img, cam, "BALTIK DENİZİ", 19.8, 56.4, 46, vis(t, T_GLOBE + .2, st("why"), .4, .4), (170, 205, 240))
    a_lb = vis(t, st("route") + .5, en("why") + .1, .3, .3)
    lab(img, cam, "BELARUS", 28.0, 53.3, 52, a_lb, (210, 225, 240)); lab(img, cam, "LİTVANYA", 24.0, 55.5, 52, a_lb, (180, 245, 180))

def ui(img, cam, t):
    header(img, t)
    typewriter(img, t, "KALİNİNGRAD", st("name") + .05, en("name") + .6, 560, 120)
    a = vis(t, st("konigsberg") + .5, en("konigsberg") + .1, .3, .3)
    if a > 0:   # yıl sayacı
        yr = int(lerp(1255, 1945, ease(prog(t, st("konigsberg") + .7, en("konigsberg") - st("konigsberg") - 1))))
        stamp_text(img, str(yr), (W / 2, 1130 * SS), FA, 150, fill=YEL, alpha=a)
        stamp_text(img, "KÖNIGSBERG", (W / 2, 1270 * SS), FA, 60, fill=WHITE, alpha=a)
    a = vis(t, st("kant") + .1, en("kant") + .3, .3, .3)
    kant_card(img, W / 2, 1180 * SS, a, back(prog(t, st("kant") + .1, .4)))
    a = vis(t, st("collapse") + .3, en("collapse") + .2, .3, .3)
    if a > 0:
        stamp_text(img, "1991", (W / 2, 560 * SS), FA, 170, fill=YEL, alpha=a, scale=back(prog(t, st("collapse") + .3, .4)))
    timeline(img, t)
    typewriter(img, t, "SUWAŁKI KORİDORU", st("gapname") - .05, TOTAL, 560, 104)
    a3 = vis(t, st("cta") + 1.2, TOTAL, .25, .3)
    pill(img, "YORUMLARA YAZ!", W / 2, 760 * SS, 64, alpha=a3, scale=back(prog(t, st("cta") + 1.2, .35)))

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s5_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
