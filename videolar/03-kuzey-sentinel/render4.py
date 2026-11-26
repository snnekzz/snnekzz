"""Video 3 – gerçekçi / 3D sürüm: uydu dokulu küre -> uydu haritası -> eğik kameralı 3D ada."""
import json, math, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from shapely.geometry import shape, box, Polygon, Point
import render as R
R.LAT0 = math.cos(math.radians(11.5))
import render2 as R2
from render import (stamp_text, pill, card, partial, vis, prog, back, eout, ease, FA, W, H, SS, OW, OH, FPS,
                    TOTAL, st, en, font, polys)
from render3 import (ISL, CX, CY, CPOLY, boat, heli, kayak, virus, xmark, shield, header, typewriter, timeline,
                     clamp01, A, L, RED, WHITE, YEL, BLACK, VIG, CLOUDS)

TEX = "../tex/"
EARTH = np.asarray(Image.open(TEX + "2_no_clouds_4k.jpg").convert("RGB"), dtype=np.float32)
CLOUDT = np.asarray(Image.open(TEX + "fair_clouds_4k.png").convert("L"), dtype=np.float32) / 255
STARS = Image.open(TEX + "galaxy_starfield.png").convert("RGB")
TH, TW = EARTH.shape[:2]
LAT0 = math.cos(math.radians(11.5))
M_PER_DEG = 111320.0

def sample(img, lon, lat, order=1):
    """eşdikdörtgen dokudan (lon,lat) dizileriyle örnekleme"""
    x = ((lon + 180) % 360) / 360 * TW - 0.5; y = (90 - lat) / 180 * TH - 0.5
    if img.ndim == 2:
        return ndimage.map_coordinates(img, [y, x], order=order, mode="wrap")
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=order, mode="wrap") for c in range(3)], -1)

# ---------------- 1) KÜRE ----------------
STARBG = STARS.resize((OW * 2, OH)).crop((0, 0, OW, OH))
STARBG = Image.blend(Image.new("RGB", (OW, OH), (2, 4, 10)), STARBG, 0.55)
SUN = np.array([-0.55, 0.45, 0.70]); SUN /= np.linalg.norm(SUN)
def globe(lon0, lat0, Rpx, t):
    out = np.asarray(STARBG, dtype=np.float32).copy()
    cy0 = OH * 0.47
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    x = (xx - OW / 2) / Rpx; y = -(yy - cy0) / Rpx
    r2 = x * x + y * y; inside = r2 < 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    xi, yi, zi = x[inside], y[inside], z[inside]
    lat = np.arcsin(np.clip(yi * math.cos(la0) + zi * math.sin(la0), -1, 1))
    lon = lo0 + np.arctan2(xi, zi * math.cos(la0) - yi * math.sin(la0))
    latd, lond = np.degrees(lat), np.degrees(lon)
    col = sample(EARTH, lond, latd)
    cl = sample(CLOUDT, lond - t * 1.5, latd) * clamp01(1 - (Rpx - 700) / 1400)
    shade = np.clip(xi * SUN[0] + yi * SUN[1] + zi * SUN[2], 0, 1) * 0.85 + 0.25
    col = col * (1 - cl[:, None] * 0.85) + 255 * cl[:, None] * 0.85
    col *= shade[:, None]
    rim = (1 - zi) ** 3
    col = col * (1 - rim[:, None] * 0.5) + np.array([90, 150, 255]) * rim[:, None] * 0.5
    out[inside] = col
    # atmosfer parıltısı
    rr = np.sqrt(r2); halo = np.clip(1 - (rr - 1) / 0.06, 0, 1) * (rr >= 1)
    out += halo[..., None] * np.array([70, 130, 255]) * 0.8
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

# ---------------- 2) UYDU HARİTASI (düz) ----------------
LANDPOLY = [(n, p, b) for n, p, b in CPOLY]
rng = np.random.default_rng(4)
def fractal(n, octaves=6, seed=0, k0=2, gain=0.55):
    r = np.random.default_rng(seed); acc = np.zeros((n, n), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        k = 2 ** (o + k0)
        g = r.standard_normal((k, k)).astype(np.float32)
        acc += amp * np.asarray(Image.fromarray(g).resize((n, n), Image.BICUBIC)); tot += amp; amp *= gain
    acc /= tot; return (acc - acc.min()) / (acc.max() - acc.min())
DETAIL = fractal(1024, 7, 1)
def satmap(lon0, lat0, s, t):
    """s: px/derece (1080 genişlikte)"""
    xs = lon0 + (np.arange(OW) - OW / 2) / (s * LAT0)
    ys = lat0 - (np.arange(OH) - OH * 0.47) / s
    LON, LAT = np.meshgrid(xs, ys)
    col = sample(EARTH, LON, LAT)
    m = Image.new("L", (OW, OH), 0); d = ImageDraw.Draw(m)
    vb = (xs[0], ys[-1], xs[-1], ys[0])
    for n, p, b in LANDPOLY:
        if b[2] < vb[0] or b[0] > vb[2] or b[3] < vb[1] or b[1] > vb[3]: continue
        pts = [(OW / 2 + (x - lon0) * s * LAT0, OH * 0.47 - (y - lat0) * s) for x, y in p.exterior.coords]
        if len(pts) > 2: d.polygon(pts, fill=255)
    land = np.asarray(m, dtype=np.float32) / 255
    blur_r = max(2, 0.06 * s)
    shallow = np.asarray(m.filter(ImageFilter.GaussianBlur(blur_r)), dtype=np.float32) / 255
    # detay dokusu (ölçekle kayan)
    sc = max(1, int(1024 / max(1, s / 8)))
    det = np.asarray(Image.fromarray((DETAIL * 255).astype(np.uint8)).resize((OW, OH), Image.BICUBIC), dtype=np.float32) / 255
    deep = np.array([10, 38, 78], np.float32); sh = np.array([30, 140, 160], np.float32)
    ocean = deep * (1 - shallow[..., None] * 0.9) + sh * shallow[..., None] * 0.9
    ocean *= (0.92 + 0.12 * det[..., None])
    landc = col * (0.80 + 0.4 * det[..., None])
    landc = np.where((landc.sum(-1, keepdims=True) < 60), np.array([40, 70, 40], np.float32), landc)
    out = ocean * (1 - land[..., None]) + landc * land[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

# ---------------- 3) 3D ADA ----------------
N = 3072; LM = 36000.0; MPP = LM / N            # doku: 36 km kare, ~11.7 m/piksel
def w2t(xm, ym): return (N / 2 + xm / MPP, N / 2 - ym / MPP)
def ll2m(lon, lat): return ((lon - CX) * M_PER_DEG * LAT0, (lat - CY) * M_PER_DEG)
ISLM = Polygon([ll2m(x, y) for x, y in ISL.exterior.coords])
def build_texture():
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).polygon([w2t(x, y) for x, y in ISLM.exterior.coords], fill=255)
    mask = np.asarray(m) > 127
    di = ndimage.distance_transform_edt(mask) * MPP
    do = ndimage.distance_transform_edt(~mask) * MPP
    n1 = fractal(N, 6, 11, k0=4, gain=0.6); n2 = fractal(N, 8, 12); n3 = fractal(N, 7, 13, k0=5, gain=0.65)
    sd = di - do + (n1 - 0.5) * 520           # doğal, girintili kıyı çizgisi
    crown = ndimage.gaussian_filter(np.random.default_rng(21).random((N, N)).astype(np.float32), 1.3)
    crown = (crown - crown.mean()) / crown.std()
    land = sd > 0
    ridge = 1 - np.abs(fractal(N, 7, 14, k0=3) * 2 - 1)
    h = np.where(land, (1 - np.exp(-np.clip(sd, 0, None) / 500)) * (40 + 120 * n2 + 70 * ridge ** 2) + 12 * n3 + 1.5 * crown, 0).astype(np.float32)
    gy, gx = np.gradient(h, MPP)
    nx, ny, nz = -gx * 7, gy * 7, np.ones_like(h)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nl, ny / nl, nz / nl
    Ld = np.array([-0.6, 0.5, 0.62]); Ld /= np.linalg.norm(Ld)
    shade = np.clip(nx * Ld[0] + ny * Ld[1] + nz * Ld[2], 0, 1)
    forest1 = np.array([28, 78, 34], np.float32); forest2 = np.array([66, 112, 46], np.float32)
    fmix = np.clip(n3 * 1.3 - 0.15 + (h / 160) * 0.3, 0, 1)[..., None]
    canopy = forest1 * (1 - fmix) + forest2 * fmix
    canopy *= (0.45 + 0.85 * shade[..., None]) * (1 + 0.16 * crown[..., None]) * (0.9 + 0.2 * n3[..., None])
    beach = np.array([226, 210, 168], np.float32) * (0.85 + 0.25 * shade[..., None])
    bw = np.clip((60 + 40 * n1 - sd) / 30, 0, 1)[..., None] * land[..., None]
    landc = canopy * (1 - bw) + beach * bw
    depth = np.clip(-sd, 0, None)
    deep = np.array([8, 40, 82], np.float32); mid = np.array([18, 95, 135], np.float32)
    shal = np.array([60, 190, 190], np.float32)
    a1 = np.clip(1 - depth / 380, 0, 1)[..., None]; a2 = np.clip(1 - depth / 1500, 0, 1)[..., None]
    water = deep * (1 - a2) + mid * a2
    water = water * (1 - a1) + shal * a1
    reef = np.exp(-((depth - 420 - 160 * n2) / 90) ** 2)[..., None] * 0.35
    water = water * (1 - reef) + np.array([120, 210, 200]) * reef
    wv = ndimage.gaussian_filter(np.random.default_rng(31).random((N, N)).astype(np.float32), [0.8, 3.0])
    water *= (0.9 + 0.2 * n3[..., None]) * (0.94 + 0.12 * wv[..., None])
    rgb = np.where(land[..., None], landc, water)
    alpha = np.where(land, 0, 255).astype(np.uint8)          # su maskesi
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(Image.fromarray(alpha))
    return img, sd
import os
if os.path.exists("island_tex.png"):
    TEX3D = Image.open("island_tex.png").convert("RGBA")
else:
    TEX3D, _sd = build_texture(); TEX3D.save("island_tex.png")
TEXRGB = TEX3D.convert("RGB") if False else Image.fromarray(np.asarray(TEX3D)[..., :3].copy())
TEXW = TEX3D.getchannel("A")
COAST = ISLM.buffer(60).simplify(20)

FOVY = math.radians(42)
class Cam:
    def __init__(s, tx, ty, D, pitch, yaw, w=W, h=H):
        s.w, s.h = w, h
        f = np.array([math.sin(yaw), math.cos(yaw), 0.0])
        s.T = np.array([tx, ty, 0.0])
        s.C = s.T - f * D * math.sin(pitch) + np.array([0, 0, D * math.cos(pitch)])
        fw = s.T - s.C; s.fw = fw / np.linalg.norm(fw)
        up0 = np.array([0, 0, 1.0]) if pitch > 0.01 else np.array([math.sin(yaw), math.cos(yaw), 0])
        r = np.cross(s.fw, up0); s.r = r / np.linalg.norm(r); s.u = np.cross(s.r, s.fw)
        s.ty = math.tan(FOVY / 2); s.tx = s.ty * w / h
    def ground(s, px, py):
        u = (px / s.w * 2 - 1) * s.tx; v = (1 - py / s.h * 2) * s.ty
        d = s.fw + s.r * u + s.u * v
        if d[2] >= -1e-6: return None
        k = -s.C[2] / d[2]; g = s.C + d * k; return g[0], g[1]
    def proj(s, x, y, z=0.0):
        p = np.array([x, y, z]) - s.C; dz = p @ s.fw
        if dz <= 1: return None
        u = (p @ s.r) / dz / s.tx; v = (p @ s.u) / dz / s.ty
        return ((u + 1) / 2 * s.w, (1 - v) / 2 * s.h, dz)
def persp_coeffs(src, dst):
    """dst(çıktı) -> src(doku) eşlemesi için PIL PERSPECTIVE katsayıları"""
    Am = []; bv = []
    for (x, y), (X, Y) in zip(dst, src):
        Am.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); bv.append(X)
        Am.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); bv.append(Y)
    return np.linalg.solve(np.array(Am, float), np.array(bv, float)).tolist()
HAZE = np.linspace(1, 0, H, dtype=np.float32) ** 2.2
def render3d(cam, t):
    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    src = [w2t(*cam.ground(x, y)) for x, y in corners]
    co = persp_coeffs(src, corners)
    rgb = TEXRGB.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC, fillcolor=(8, 40, 82))
    water = TEXW.transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR, fillcolor=255)
    # su parıltıları (ekran uzayında kayan)
    off = int(t * 25 * SS) % 512
    gl = GLINT.crop((0, off, W, off + H))
    rgb.paste((255, 255, 255), (0, 0), Image.fromarray((np.asarray(gl, np.float32) * np.asarray(water, np.float32) / 255).astype(np.uint8)))
    # mesafe sisi
    hz = (HAZE * 120 * (cam_pitch_factor(cam))).astype(np.uint8)
    rgb.paste((150, 175, 200), (0, 0), Image.fromarray(np.repeat(hz[:, None], W, 1)))
    return rgb.convert("RGBA")
def cam_pitch_factor(cam): return clamp01((math.degrees(math.acos(-cam.fw[2])) - 10) / 40)
gn = np.random.default_rng(9).random((H + 512, W)).astype(np.float32)
GLINT = Image.fromarray((np.clip((gn - 0.985) / 0.015, 0, 1) * 90).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))

# ---------------- zaman çizelgesi / kamera ----------------
T_GLOBE_END = 2.7
T_SAT_END = st("name") + 0.6
def lerp(a, b, p): return a + (b - a) * p
def stage_globe(t):
    p = ease(t / T_GLOBE_END)
    lon = lerp(30, 89, p); lat = lerp(5, 14, p)
    Rpx = math.exp(lerp(math.log(430), math.log(60 * 180 / math.pi), ease(p ** 1.4)))
    return lon, lat, Rpx
def stage_sat(t):
    p = clamp01((t - T_GLOBE_END) / (T_SAT_END - T_GLOBE_END))
    q = ease(p)
    lon = lerp(89, CX, q); lat = lerp(14, CY, q)
    s = math.exp(lerp(math.log(60), math.log(2600), ease(p) ** 1.6))
    return lon, lat, s
D0 = 20000 / math.tan(math.atan(math.tan(FOVY / 2) * W / H))   # düz -> 3D eşleşmesi (~40 km genişlik)
K3 = [  # (zaman, tx, ty, D, pitch°, yaw°)
    (T_SAT_END, 0, 0, D0, 0, 0),
    (st("tribe") - .2, 0, -500, 30000, 48, 8),
    (st("y1880") - .3, -2200, -1200, 36000, 52, 14),
    (st("arrows") + 1, -800, -900, 33000, 50, 22),
    (st("y2004") + .5, 900, -300, 38000, 52, 30),
    (st("y2006") + .5, -1200, -500, 35000, 50, 38),
    (st("y2018") + .5, 1500, -1800, 36000, 52, 46),
    (st("gone"), 500, -800, 30000, 55, 50),
    (st("zone") + .3, 0, -3500, 78000, 46, 58),
    (st("flu") - .1, 0, -600, 33000, 50, 66),
    (st("survive") + .5, 0, -500, 30000, 46, 74),
    (st("cta") + .4, 0, -2500, 70000, 38, 82),
    (TOTAL, 0, -3000, 85000, 34, 86),
]
def cam3d(t):
    for a, b in zip(K3[:-1], K3[1:]):
        if a[0] <= t <= b[0]:
            p = ease((t - a[0]) / max(1e-3, b[0] - a[0])); break
    else:
        a = b = K3[-1] if t > K3[-1][0] else K3[0]; p = 0
    v = [lerp(a[i], b[i], p) for i in range(1, 6)]
    v[2] = math.exp(lerp(math.log(a[3]), math.log(b[3]), p))
    return Cam(v[0], v[1], v[2], math.radians(v[3]), math.radians(v[4]))
SHAKES = [(st("y1880") + .3, .3, 6), (st("y2004") + .3, .3, 6), (st("y2006") + .3, .3, 6),
          (st("y2018") + .3, .3, 6), (en("y2018") + .35, 1.0, 22)]
def shake(t):
    dx = dy = 0
    for t0, d, a in SHAKES:
        if t0 <= t < t0 + d:
            k = a * SS * (1 - (t - t0) / d); dx += k * math.sin(t * 91); dy += k * math.cos(t * 73)
    return dx, dy

# ---------------- 3D sahne üstü nesneler ----------------
def P3(cam, x, y, z=0): return cam.proj(x, y, z)
def wpath(cam, pts, z=0):
    out = [P3(cam, x, y, z) for x, y in pts]; return [(q[0], q[1]) for q in out if q]
def boat3d(dl, cam, x, y, heading, a, col=(140, 95, 55), scale=1.0, wake=True, t=0):
    q = P3(cam, x, y)
    if not q: return None
    s = 50000 / q[2] * scale
    if wake:
        for side in (-1, 1):
            pts = [(x - math.sin(heading) * k * 60 + side * math.cos(heading) * k * 18,
                    y - math.cos(heading) * k * 60 - side * math.sin(heading) * k * 18) for k in range(0, 12)]
            dl.line(wpath(cam, pts), fill=A((235, 245, 255), a * .55), width=max(2, int(4 * SS * s / 2)))
    sq = P3(cam, x + 25, y - 25)
    if sq: dl.ellipse((sq[0] - 60 * s * SS / 2, sq[1] - 10 * s * SS / 2, sq[0] + 60 * s * SS / 2, sq[1] + 10 * s * SS / 2), fill=(0, 0, 0, int(70 * a)))
    boat(dl, q[0], q[1], s, a, col)
    return q
def projectile3d(dl, cam, p0, p1, p, a, hmax=180):
    if p <= 0 or p >= 1: return
    def pos(qq):
        x = lerp(p0[0], p1[0], qq); y = lerp(p0[1], p1[1], qq)
        z = lerp(p0[2], p1[2], qq) + hmax * 4 * qq * (1 - qq); return P3(cam, x, y, z)
    pts = [pos(max(0, p - k * 0.025)) for k in range(6)]
    pts = [q for q in pts if q]
    if len(pts) < 2: return
    hd, tl = pts[0], pts[-1]
    w = max(3, int(5 * SS * 40000 / hd[2]))
    dl.line([(q[0], q[1]) for q in pts], fill=A((235, 225, 200), a), width=w)
    ang = math.atan2(hd[1] - pts[1][1], hd[0] - pts[1][0]); s = w * 3.2
    dl.polygon([(hd[0] + math.cos(ang) * s, hd[1] + math.sin(ang) * s), (hd[0] + math.cos(ang + 2.5) * s * .7, hd[1] + math.sin(ang + 2.5) * s * .7),
                (hd[0] + math.cos(ang - 2.5) * s * .7, hd[1] + math.sin(ang - 2.5) * s * .7)], fill=A((210, 210, 215), a))

def coast_point(ang):
    """ada merkezinden ang yönündeki kıyı noktası (m)"""
    far = (math.cos(ang) * 8000, math.sin(ang) * 8000)
    from shapely.geometry import LineString
    inter = ISLM.exterior.intersection(LineString([(0, 0), far]))
    if inter.is_empty: return (0, 0)
    g = inter if inter.geom_type == "Point" else list(inter.geoms)[0]
    return (g.x, g.y)

def overlays3d(img, cam, t):
    lay = L(); dl = ImageDraw.Draw(lay)
    # kıyı köpüğü / dalga halkaları
    for k in range(4):
        ph = ((t * 0.3) + k / 4) % 1
        ring = COAST.buffer(30 + ph * 420).exterior.coords
        dl.line(wpath(cam, ring), fill=(240, 250, 255, int(70 * (1 - ph))), width=max(2, int(3 * SS)))
    # tehlike nabzı
    a_p = vis(t, st("name") + .4, en("y2018"), .4, .5)
    if a_p > 0:
        for k in range(2):
            ph = ((t * .55) + k * .5) % 1; rr = 4200 + ph * 2600
            circ = [(math.cos(i / 48 * 6.283) * rr, math.sin(i / 48 * 6.283) * rr) for i in range(49)]
            dl.line(wpath(cam, circ), fill=A(RED, a_p * (1 - ph) * .7), width=5 * SS)
    # yasak bölge
    a_z = vis(t, st("zone") + .6, st("flu") - .3, .3, .6)
    if a_z > 0:
        RZ = 9260; pz = eout(prog(t, st("zone") + .6, 1.4)); n = 96
        fillp = wpath(cam, [(math.cos(i / n * 6.283) * RZ, math.sin(i / n * 6.283) * RZ) for i in range(n + 1)])
        if len(fillp) > 3: dl.polygon(fillp, fill=A(RED, .10 * a_z))
        for k in range(int(n * pz)):
            if k % 2: continue
            a0 = k / n * 6.283 + t * .12; a1 = a0 + 6.283 / n
            seg = wpath(cam, [(math.cos(a0) * RZ, math.sin(a0) * RZ), (math.cos(a1) * RZ, math.sin(a1) * RZ)])
            if len(seg) == 2: dl.line(seg, fill=A(RED, a_z), width=7 * SS)
        sw = t * 1.4
        sector = [(0, 0)] + [(math.cos(sw - k * .02) * RZ, math.sin(sw - k * .02) * RZ) for k in range(20)]
        sp = wpath(cam, sector)
        if len(sp) > 2: dl.polygon(sp, fill=A(RED, .22 * a_z))
        for k, an in enumerate((.5, 2.4, 4.0)):
            boat3d(dl, cam, math.cos(an) * (RZ + 900), math.sin(an) * (RZ + 900), an + math.pi, vis(t, st("zone") + 2.0, st("flu") - .4, .3, .5),
                   (90, 110, 140), 1.2, wake=False)
    img.alpha_composite(lay); lay = L(); dl = ImageDraw.Draw(lay)
    # 1880: tekne gelip geri döner
    a = vis(t, st("y1880") + .2, en("y1880") + .2, .3, .4)
    if a > 0:
        p = prog(t, st("y1880") + .2, en("y1880") - st("y1880")); q = math.sin(min(1, p) * math.pi)
        bx, by = -7600 + q * 3600, -2600 + q * 900
        heading = math.atan2(3600, 900) if p < .5 else math.atan2(-3600, -900)
        qq = boat3d(dl, cam, bx, by, heading, a, scale=1.5, t=t)
        if qq: img.alpha_composite(lay); lay = L(); dl = ImageDraw.Draw(lay); card(img, "uk", qq[0], qq[1] - 200 * SS * 40000 / qq[2], 140, a)
    # ok yağmuru
    if st("arrows") < t < en("arrows") + .8:
        for k in range(16):
            t0 = st("arrows") + .4 + k * .25; an = k * 2.399
            cpx, cpy = coast_point(an)
            projectile3d(dl, cam, (cpx, cpy, 5), (cpx + math.cos(an) * 2600, cpy + math.sin(an) * 2600, 0), (t - t0) / 1.0, 1, 380)
    # 2004: helikopter
    a = vis(t, st("y2004") + .2, en("y2004") + .3, .3, .4)
    if a > 0:
        p = prog(t, st("y2004") + .2, en("y2004") - st("y2004"))
        app = eout(min(1, p / .45)); ret = ease(max(0, (p - .7) / .3))
        hx = 7000 - app * 3600 + ret * 5000; hy = 4000 - app * 1800 + ret * 2500; hz = 420
        sh = P3(cam, hx, hy, 0); hq = P3(cam, hx, hy, hz)
        if sh and hq:
            s = 55000 / hq[2]
            dl.ellipse((sh[0] - 90 * s * SS / 2, sh[1] - 22 * s * SS / 2, sh[0] + 90 * s * SS / 2, sh[1] + 22 * s * SS / 2), fill=(0, 0, 0, int(80 * a)))
            heli(dl, hq[0], hq[1], s, a, t)
            for k in range(6):
                t0 = st("y2004") + 1.2 + k * .3; cpx, cpy = coast_point(math.atan2(hy, hx))
                projectile3d(dl, cam, (cpx, cpy, 5), (hx + (k - 3) * 40, hy, hz), (t - t0) / .8, 1, 160)
    # 2006: sürüklenen balıkçı teknesi
    a = vis(t, st("y2006") + .2, en("y2006") + .3, .3, .4)
    if a > 0:
        p = eout(prog(t, st("y2006") + .2, 2.4))
        cpx, cpy = coast_point(math.radians(150))
        bx, by = lerp(cpx - 3800, cpx - 250, p), lerp(cpy + 1600, cpy + 120, p)
        qq = boat3d(dl, cam, bx, by, math.atan2(3550, -1480), a, (120, 120, 130), 1.2, t=t)
        img.alpha_composite(lay); lay = L(); dl = ImageDraw.Draw(lay)
        if qq and t > st("y2006") + 2.5:
            xmark(img, qq[0], qq[1] - 60 * SS, 60 * back(prog(t, st("y2006") + 2.5, .3)), a)
    # 2018: kano rotası
    a = vis(t, st("y2018") + .2, en("gone") + .2, .3, .5)
    if a > 0:
        cpx, cpy = coast_point(math.radians(-40))
        pts = [(lerp(cpx + 5200, cpx + 80, k / 40), lerp(cpy - 4200, cpy - 60, k / 40) + math.sin(k / 5) * 150) for k in range(41)]
        pr = eout(prog(t, st("y2018") + .4, en("y2018") - st("y2018") - .2))
        sp = wpath(cam, partial(pts, pr))
        if len(sp) > 1:
            R.dashed(dl, sp, A(WHITE, a), 5 * SS, 14, 12)
            q = P3(cam, *partial(pts, pr)[-1])
            if q: kayak(dl, q[0], q[1], 55000 / q[2], a * (1 - prog(t, en("y2018") + .3, .5)))
    # virüsler
    a = vis(t, st("flu") + .3, en("flu") + .3, .4, .5)
    if a > 0:
        for k in range(6):
            an = k * 1.047 + .4; p = eout(prog(t, st("flu") + .3 + k * .22, 3.0)); dd = 7500 - p * 4300
            q = P3(cam, math.cos(an) * dd, math.sin(an) * dd, 500 + 150 * math.sin(t * 2 + k))
            if q: virus(dl, q[0], q[1], 24 * 40000 / q[2] * (1 + .08 * math.sin(t * 5 + k)), a, t + k)
    # kalkan
    a = vis(t, st("survive") + .2, st("cta") + .2, .5, .5)
    if a > 0:
        q = P3(cam, 0, 0, 1800)
        if q: shield(dl, q[0], q[1], 1300 * 9000 / q[2] / SS * (0.92 + 0.08 * back(prog(t, st("survive") + .2, .6))), a)
    img.alpha_composite(lay)
    # ekran etiketleri (adaya göre)
    q = P3(cam, 0, 0, 0)
    if q:
        cx, cy = q[0], q[1]
        a = vis(t, st("unknown") + .3, en("unknown") + .2, .3, .3)
        pill(img, "NÜFUS: ?", cx - 260 * SS, cy - 300 * SS, 54, bg=YEL, alpha=a, scale=back(prog(t, st("unknown") + .3, .35)))
        a = vis(t, st("unknown") + 1.1, en("unknown") + .2, .3, .3)
        pill(img, "DİL: ?", cx + 260 * SS, cy + 120 * SS, 54, bg=YEL, alpha=a, scale=back(prog(t, st("unknown") + 1.1, .35)))

# ---------------- kare ----------------
def frame(t):
    if t < T_GLOBE_END:
        lon, lat, Rpx = stage_globe(t)
        base = globe(lon, lat, Rpx, t).resize((W, H), Image.BICUBIC).convert("RGBA")
        sat_s = Rpx * math.pi / 180
        if t > T_GLOBE_END - .35:   # düz haritaya yumuşak geçiş
            f = (t - (T_GLOBE_END - .35)) / .35
            s2 = satmap(lon, lat, sat_s, t).resize((W, H), Image.BICUBIC).convert("RGBA")
            base = Image.blend(base, s2, f)
        img = base; mode = "globe"; s_now = sat_s; c_ll = (lon, lat)
    elif t < T_SAT_END:
        lon, lat, s = stage_sat(t)
        img = satmap(lon, lat, s, t).resize((W, H), Image.BICUBIC).convert("RGBA"); mode = "sat"; s_now = s; c_ll = (lon, lat)
        f = clamp01((t - (T_SAT_END - .45)) / .45)
        if f > 0:
            img = Image.blend(img, render3d(cam3d(T_SAT_END), t), f)
    else:
        cam = cam3d(t); img = render3d(cam, t); overlays3d(img, cam, t); mode = "3d"
    # bulutlar (3D sahnede ince sis)
    a_cl = .07 if mode == "3d" else (.18 if mode == "sat" else 0)
    if a_cl:
        off = int((t * 40 * SS) % W); cl = CLOUDS.crop((off, 0, off + W, H)).point(lambda v: int(v * a_cl))
        img.paste((240, 244, 250), (0, 0), cl)
    # etiketler (küre/uydu)
    if mode in ("globe", "sat"):
        def lab(text, lon, lat, size, a, col=(235, 240, 245)):
            if a <= 0: return
            if mode == "sat":
                x = W / 2 + (lon - c_ll[0]) * s_now * LAT0 * SS; y = H * .47 - (lat - c_ll[1]) * s_now * SS
            else:
                x = W / 2 + (lon - c_ll[0]) * s_now * math.cos(math.radians(lat)) * SS; y = H * .47 - (lat - c_ll[1]) * s_now * SS
            stamp_text(img, text, (x, y), FA, size, fill=col, stroke=BLACK, alpha=a)
        lab("HİNDİSTAN", 78.5, 21.5, 70, clamp01((s_now - 12) / 10) * clamp01(1 - (s_now - 80) / 60))
        lab("BENGAL KÖRFEZİ", 88.5, 15.5, 46, clamp01((s_now - 25) / 15) * clamp01(1 - (s_now - 150) / 100), (170, 205, 240))
        lab("ANDAMAN ADALARI", 93.9, 12.6, 50, clamp01((s_now - 120) / 60) * clamp01(1 - (s_now - 700) / 400))
        a_ns = clamp01((s_now - 150) / 80) * clamp01(1 - (s_now - 1500) / 600)
        if a_ns > 0:
            x = W / 2 + (CX - c_ll[0]) * s_now * LAT0 * SS; y = H * .47 - (CY - c_ll[1]) * s_now * SS
            rr = (16 + 5 * math.sin(t * 6)) * SS
            ImageDraw.Draw(img).ellipse((x - rr, y - rr, x + rr, y + rr), outline=RED, width=5 * SS)
            stamp_text(img, "KUZEY SENTİNEL", (x - 40 * SS, y + 60 * SS), FA, 42, fill=RED, stroke=BLACK, alpha=a_ns)
    typewriter(img, t, "KUZEY SENTİNEL", st("name") + .1, 560, 120)
    a = vis(t, st("tribe") + .3, en("tribe") + .2, .3, .3)
    pill(img, "DIŞ DÜNYAYLA TEMAS: YOK", W / 2, 1250 * SS, 52, bg=WHITE, fg=BLACK, alpha=a, scale=back(prog(t, st("tribe") + .3, .35)))
    a = vis(t, st("y1880") + 2.6, en("y1880") + .2, .3, .3)
    pill(img, "6 KİŞİ KAÇIRILDI", W / 2, 1250 * SS, 52, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("y1880") + 2.6, .35)))
    a = vis(t, st("y2006") + 2.6, en("y2006") + .2, .3, .3)
    pill(img, "2 BALIKÇI", W / 2, 1250 * SS, 52, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("y2006") + 2.6, .35)))
    a = vis(t, st("zone") + 1.6, st("flu") - .4, .3, .4)
    pill(img, "9 KM YASAK BÖLGE", W / 2, 470 * SS, 58, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("zone") + 1.6, .35)))
    a = vis(t, st("flu") + .8, en("flu") + .2, .3, .3)
    pill(img, "BAĞIŞIKLIK YOK", W / 2, 470 * SS, 58, bg=WHITE, fg=RED, alpha=a, scale=back(prog(t, st("flu") + .8, .35)))
    a = vis(t, st("survive") + .6, st("cta") + .1, .3, .3)
    pill(img, "HAYATTA KALMA MÜCADELESİ", W / 2, 470 * SS, 50, bg=YEL, alpha=a, scale=back(prog(t, st("survive") + .6, .35)))
    timeline(img, t)
    header(img, t)
    a3 = vis(t, st("cta") + 1.2, TOTAL, .25, .3)
    pill(img, "YORUMLARA YAZ!", W / 2, 560 * SS, 64, alpha=a3, scale=back(prog(t, st("cta") + 1.2, .35)))
    # sinematik
    dark = .35 + .5 * vis(t, en("y2018") + .2, st("zone") + .3, .4, .9)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * dark)))
    if t >= en("y2018") + .35:
        fl = 1 - clamp01((t - (en("y2018") + .35)) / .5)
        if fl > 0: img.alpha_composite(Image.new("RGBA", (W, H), A(RED, fl * .4)))
    warm = eout(prog(t, st("survive"), 1.2))
    if warm > 0: img.alpha_composite(Image.new("RGBA", (W, H), (255, 170, 80, int(34 * warm))))
    R2.caption(img, t)
    sx, sy = shake(t)
    if sx or sy: img = img.transform(img.size, Image.AFFINE, (1, 0, -sx, 0, 1, -sy), resample=Image.BILINEAR)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .6, .6))
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
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s4_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
