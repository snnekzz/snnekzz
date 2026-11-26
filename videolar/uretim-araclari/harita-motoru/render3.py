"""Video 3: Kuzey Sentinel – gerilimli, çeşitli animasyonlu renderer."""
import json, math, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, box, Polygon, Point
import render as R
R.LAT0 = math.cos(math.radians(11.5))
import render2 as R2
from render import (Proj, stamp_text, pill, card, partial, densify, dashed, vis, prog, back, eout, ease,
                    FA, F9, W, H, SS, OW, OH, FPS, TOTAL, st, en, font, polys)

# ---------- renkler ----------
SEA1, SEA2 = (14, 30, 52), (5, 12, 26)
LAND = (52, 60, 70); LAND_HI = (66, 76, 88); BORDER = (82, 92, 104)
JUNGLE = (40, 118, 66); JUNGLE_D = (26, 86, 46); BEACH = (214, 196, 150)
RED = (230, 57, 70); WHITE = (255, 255, 255); YEL = (255, 210, 63); BLACK = (10, 10, 14)
LABEL = (200, 210, 222); SEA_TXT = (90, 130, 175)

# ---------- veri ----------
G = json.load(open("countries10_asia.json"))
CPOLY = []   # (isim, polygon, bounds)
for f in G["features"]:
    g = shape(f["geometry"]).buffer(0).intersection(box(55, -12, 125, 40))
    for p in polys(g):
        CPOLY.append((f["properties"]["name"], p, p.bounds))
ISL = max((p for n, p, b in CPOLY if n == "India" and p.intersects(box(92.0, 11.4, 92.4, 11.7))), key=lambda p: p.area)
def chaikin(c, it=3):
    c = list(c)
    for _ in range(it):
        out = []
        for a, b in zip(c[:-1], c[1:]):
            out += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
        out.append(out[0]); c = out
    return c
ISL = Polygon(chaikin(ISL.exterior.coords))
CX, CY = ISL.centroid.x, ISL.centroid.y
BEACHP = ISL.buffer(0.0013)
rnd = random.Random(5)
TREES = []
x0, y0, x1, y1 = ISL.bounds
while len(TREES) < 260:
    p = (rnd.uniform(x0, x1), rnd.uniform(y0, y1))
    if ISL.buffer(-0.0015).contains(Point(p)): TREES.append((p, rnd.uniform(0.6, 1.4)))
ZONE_R = 9 / 111.0   # 9 km (derece)

# ---------- kamera ----------
CAMS = {"wide": (82, 17, 13), "bay": (91.0, 13.5, 50), "andaman": (92.75, 11.9, 230),
        "island": (CX, CY, 7000), "island2": (CX - 0.004, CY, 5000), "zone": (CX, CY, 3900),
        "island3": (CX, CY, 6200), "end": (92.75, 11.9, 240)}
KEYS = [(0.35, "bay", 2.0), (2.45, "andaman", 1.9), (st("name") - .4, "island", 1.4),
        (st("y1880") - .2, "island2", 1.0), (st("zone") - .3, "zone", 1.5), (st("flu") - .2, "island3", 1.0),
        (st("cta") - .2, "end", 1.6)]
SHAKES = [(st("y1880") + .3, .35, 8), (st("y2004") + .3, .35, 8), (st("y2006") + .3, .35, 8),
          (st("y2018") + .3, .35, 8), (en("y2018") + .35, 1.0, 26)]
def camera(t):
    cur = CAMS["wide"]
    for k, nm, d in KEYS:
        if t <= k: break
        tg = CAMS[nm]; p = ease((t - k) / d)
        s = math.exp(math.log(cur[2]) + (math.log(tg[2]) - math.log(cur[2])) * p)
        cur = (cur[0] + (tg[0]-cur[0])*p, cur[1] + (tg[1]-cur[1])*p, s)
    return (cur[0], cur[1], cur[2] * (1 + 0.015 * math.sin(t * 0.5)))
def shake(t):
    dx = dy = 0
    for t0, d, a in SHAKES:
        if t0 <= t < t0 + d:
            k = a * SS * (1 - (t - t0) / d)
            dx += k * math.sin(t * 91); dy += k * math.cos(t * 73)
    return dx, dy

# ---------- statik katmanlar ----------
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
SEA = Image.fromarray(np.broadcast_to(np.array(SEA1)*(1-yy) + np.array(SEA2)*yy, (H, W, 3)).astype(np.uint8), "RGB")
gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = Image.fromarray((np.clip(np.sqrt(((gx-W/2)/(W*.62))**2 + ((gy-H*.46)/(H*.6))**2), 0, 1)**2.2 * 255).astype(np.uint8), "L")
del gx, gy
def make_clouds(seed):
    im = Image.new("L", (W*2, H), 0); d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(26):
        x, y, s = r.uniform(0, W*2), r.uniform(0, H), r.uniform(120, 380)*SS
        for _ in range(5):
            ox, oy = r.uniform(-s, s), r.uniform(-s*.4, s*.4); rr = s * r.uniform(.4, .8)
            d.ellipse((x+ox-rr, y+oy-rr*.6, x+ox+rr, y+oy+rr*.6), fill=r.randint(120, 200))
    return im.filter(ImageFilter.GaussianBlur(40*SS))
CLOUDS = make_clouds(2)

# ---------- ikonlar ----------
def L(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def A(c, a): return c + (int(255*max(0, min(1, a))),)
def boat(d, x, y, s, a, col=(150, 100, 60)):
    s *= SS
    d.polygon([(x-60*s, y), (x+60*s, y), (x+42*s, y+22*s), (x-42*s, y+22*s)], fill=A(col, a), outline=A(BLACK, a))
    d.line([(x, y), (x, y-70*s)], fill=A((230, 230, 230), a), width=int(4*s)+1)
    d.polygon([(x+3*s, y-68*s), (x+3*s, y-8*s), (x+48*s, y-12*s)], fill=A((240, 240, 235), a))
def heli(d, x, y, s, a, t):
    s *= SS; c = A((70, 78, 88), a)
    d.ellipse((x-50*s, y-26*s, x+40*s, y+24*s), fill=c, outline=A(BLACK, a), width=int(3*s)+1)
    d.ellipse((x+8*s, y-18*s, x+34*s, y+6*s), fill=A((150, 200, 230), a))
    d.line([(x-45*s, y-2*s), (x-120*s, y-12*s)], fill=c, width=int(10*s))
    d.line([(x-120*s, y-30*s), (x-120*s, y+8*s)], fill=c, width=int(5*s))
    d.line([(x-40*s, y+38*s), (x+40*s, y+38*s)], fill=c, width=int(5*s))
    rl = 110*s*abs(math.cos(t*30))
    d.line([(x-rl, y-34*s), (x+rl, y-34*s)], fill=A((30, 30, 30), a), width=int(6*s)+1)
    d.line([(x, y-26*s), (x, y-34*s)], fill=c, width=int(5*s))
def kayak(d, x, y, s, a):
    s *= SS
    d.ellipse((x-46*s, y-8*s, x+46*s, y+8*s), fill=A((230, 120, 40), a), outline=A(BLACK, a))
    d.ellipse((x-9*s, y-26*s, x+9*s, y-8*s), fill=A((240, 220, 190), a))
def projectile(d, p0, p1, p, a, arc=0.25):
    if p <= 0 or p >= 1: return
    def pos(q):
        x = p0[0] + (p1[0]-p0[0])*q; y = p0[1] + (p1[1]-p0[1])*q
        L_ = math.dist(p0, p1); return (x, y - arc*L_*4*q*(1-q))
    h, tl = pos(p), pos(max(0, p-0.12))
    ang = math.atan2(h[1]-tl[1], h[0]-tl[0]); s = 26*SS
    d.line([tl, h], fill=A((235, 225, 200), a), width=6*SS)
    d.polygon([(h[0]+math.cos(ang)*s, h[1]+math.sin(ang)*s), (h[0]+math.cos(ang+2.5)*s*.8, h[1]+math.sin(ang+2.5)*s*.8),
               (h[0]+math.cos(ang-2.5)*s*.8, h[1]+math.sin(ang-2.5)*s*.8)], fill=A((200, 200, 205), a))
    for k in (2.7, -2.7):
        d.line([tl, (tl[0]+math.cos(ang+k)*s, tl[1]+math.sin(ang+k)*s)], fill=A(RED, a), width=3*SS)
def virus(d, x, y, r, a, t):
    r *= SS
    for k in range(10):
        an = k*math.pi/5 + t*0.8
        ex, ey = x + math.cos(an)*r*1.45, y + math.sin(an)*r*1.45
        d.line([(x+math.cos(an)*r, y+math.sin(an)*r), (ex, ey)], fill=A((200, 50, 70), a), width=int(r*.18))
        d.ellipse((ex-r*.2, ey-r*.2, ex+r*.2, ey+r*.2), fill=A((240, 90, 100), a))
    d.ellipse((x-r, y-r, x+r, y+r), fill=A((215, 60, 80), a), outline=A((120, 20, 30), a), width=int(r*.12))
def xmark(img, x, y, size, a):
    if a <= 0: return
    lay = L(); d = ImageDraw.Draw(lay); s = size*SS
    for sg in (1, -1):
        d.line([(x-s, y-s*sg), (x+s, y+s*sg)], fill=A(BLACK, a), width=int(s*.42))
        d.line([(x-s, y-s*sg), (x+s, y+s*sg)], fill=A(RED, a), width=int(s*.28))
    img.alpha_composite(lay)
def shield(d, x, y, s, a):
    s *= SS
    pts = [(x, y-s), (x+s*.85, y-s*.65), (x+s*.75, y+s*.25), (x, y+s), (x-s*.75, y+s*.25), (x-s*.85, y-s*.65)]
    d.polygon(pts, fill=A((255, 196, 80), a*.35), outline=A((255, 214, 120), a), width=int(10*SS))

# ---------- metin öğeleri ----------
def header(img, t):
    a = vis(t, .15, en("name") + .1, .3, .4)
    if a <= 0: return
    sc = .9 + .1*back(prog(t, .15, .35))
    lay = Image.new("RGBA", (W, 260*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 820*SS*sc, 180*SS*sc; x0, y0 = W/2-w/2, 130*SS-h/2
    d.rounded_rectangle((x0, y0, x0+w, y0+h), radius=int(36*SS), fill=(0, 0, 0, 215), outline=A(RED, 1), width=4*SS)
    d.text((W/2, y0+h*.31), "KİMSENİN", font=font(FA, 64*SS*sc), fill=WHITE, anchor="mm")
    d.text((W/2, y0+h*.71), "GİREMEDİĞİ ADA", font=font(FA, 76*SS*sc), fill=RED, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v*a)))
    img.alpha_composite(lay, (0, 150*SS))

def typewriter(img, t, text, t0, y, size, col=WHITE):
    a = vis(t, t0, en("tribe") - .3, .1, .4)
    if a <= 0: return
    n = int(len(text) * clamp01((t - t0) / 0.9)) if t < t0 + 0.9 else len(text)
    shown = text[:max(1, n)]
    jitter = (random.Random(int(t*30)).uniform(-4, 4)*SS) if t < t0 + 1.0 else 0
    stamp_text(img, shown, (W/2 + jitter, y*SS), FA, size, fill=col, alpha=a)
    if t > t0 + 0.9:
        f = font(FA, size*SS); tw = f.getlength(text); u = eout(prog(t, t0 + .9, .4))
        lay = L(); d = ImageDraw.Draw(lay)
        d.line([(W/2 - tw/2*u, (y + size*.62)*SS), (W/2 + tw/2*u, (y + size*.62)*SS)], fill=A(RED, a), width=8*SS)
        img.alpha_composite(lay)
def clamp01(x): return max(0., min(1., x))

YEARS = [("1880", "y1880"), ("2004", "y2004"), ("2006", "y2006"), ("2018", "y2018")]
def timeline(img, t):
    a = vis(t, st("y1880") - .2, en("gone") - .2, .4, .4)
    if a <= 0: return
    lay = L(); d = ImageDraw.Draw(lay)
    xs = [190*SS + i*(700*SS)/3 for i in range(4)]; y = 300*SS
    d.line([(xs[0], y), (xs[-1], y)], fill=A((120, 130, 145), a), width=6*SS)
    cur = max([i for i, (_, sc) in enumerate(YEARS) if t >= st(sc)] or [-1])
    if cur >= 0:
        nxt = xs[min(cur+1, 3)]; p = eout(prog(t, st(YEARS[cur][1]), .6))
        d.line([(xs[0], y), (xs[cur], y)], fill=A(RED, a), width=8*SS)
    for i, (yr, sc) in enumerate(YEARS):
        on = i <= cur
        r = (20 if i == cur else 13)*SS * (1 + .25*max(0, math.sin((t - st(sc))*6)) if i == cur and t < st(sc)+1 else 1)
        d.ellipse((xs[i]-r, y-r, xs[i]+r, y+r), fill=A(RED if on else (90, 98, 110), a), outline=A(WHITE, a), width=3*SS)
        d.text((xs[i], y + 52*SS), yr, font=font(FA, (54 if i == cur else 40)*SS), fill=A(WHITE if on else (150, 158, 170), a), anchor="mm")
    img.alpha_composite(lay)

# ---------- kare ----------
def frame(t):
    cam = camera(t); P = Proj(cam); V = P.view(); vb = V.bounds
    sx, sy = shake(t)
    img = SEA.copy(); d = ImageDraw.Draw(img)
    for n, p, b in CPOLY:
        if b[2] < vb[0] or b[0] > vb[2] or b[3] < vb[1] or b[1] > vb[3]: continue
        if p.equals(ISL) or (n == "India" and p.intersects(box(92.1, 11.45, 92.4, 11.7))): continue
        pts = P.arr(p.exterior.coords)
        if len(pts) > 2:
            d.polygon(pts, fill=LAND_HI if n == "India" else LAND, outline=BORDER)
    img = img.convert("RGBA")
    zoomed = cam[2] > 1500

    # dalga halkaları
    if cam[2] > 900:
        lay = L(); dl = ImageDraw.Draw(lay)
        for k in range(5):
            ph = ((t * 0.35) + k / 5) % 1
            ring = ISL.buffer(0.0015 + ph * 0.010)
            dl.line(P.arr(ring.exterior.coords), fill=(120, 170, 220, int(90 * (1 - ph))), width=3*SS)
        img.alpha_composite(lay)
    # yasak bölge
    a_z = vis(t, st("zone") + .6, st("flu") - .3, .3, .6)
    if a_z > 0:
        lay = L(); dl = ImageDraw.Draw(lay)
        cx, cy = P.xy(CX, CY); rp = ZONE_R * P.s
        dl.ellipse((cx-rp, cy-rp, cx+rp, cy+rp), fill=A(RED, .10*a_z))
        pz = eout(prog(t, st("zone") + .6, 1.4)); n = 64
        for k in range(int(n * pz)):
            if k % 2: continue
            a0 = k * 2*math.pi/n + t*0.15; a1 = a0 + 2*math.pi/n
            dl.arc((cx-rp, cy-rp, cx+rp, cy+rp), math.degrees(a0), math.degrees(a1), fill=A(RED, a_z), width=7*SS)
        sw = t * 1.6
        for k in range(18):
            aa = sw - k*0.035
            dl.line([(cx, cy), (cx + math.cos(aa)*rp, cy + math.sin(aa)*rp)], fill=A(RED, a_z*0.35*(1-k/18)), width=4*SS)
        img.alpha_composite(lay)
    # ada
    d = ImageDraw.Draw(img)
    d.polygon(P.arr(BEACHP.exterior.coords), fill=BEACH)
    warm = eout(prog(t, st("survive"), 1.2))
    jcol = tuple(int(JUNGLE[i] + (np.array((96, 150, 70))[i] - JUNGLE[i]) * warm) for i in range(3))
    d.polygon(P.arr(ISL.exterior.coords), fill=jcol)
    if cam[2] > 1200:
        for (lo, la), s in TREES:
            x, y = P.xy(lo, la); r = s * cam[2] * 0.0011 * SS / 2
            d.ellipse((x-r, y-r, x+r, y+r), fill=JUNGLE_D)
    # tehlike nabzı
    a_pulse = vis(t, st("name"), en("y2018"), .3, .5)
    if a_pulse > 0 and zoomed:
        lay = L(); dl = ImageDraw.Draw(lay)
        cx, cy = P.xy(CX, CY)
        for k in range(2):
            ph = ((t * .7) + k * .5) % 1; rr = (0.03 + ph * 0.03) * P.s
            dl.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), outline=A(RED, a_pulse*(1-ph)*.8), width=6*SS)
        img.alpha_composite(lay)
    # bulutlar (geniş planlarda)
    a_cl = clamp01(1 - (cam[2] - 20) / 200) * .55
    if a_cl > 0.01:
        off = int((t * 60 * SS) % W)
        cl = CLOUDS.crop((off, 0, off + W, H)).point(lambda v: int(v * a_cl))
        img.paste((235, 240, 248), (0, 0), cl)

    # ---- olay animasyonları (ada merkezine göre ekran koordinatları) ----
    cx, cy = P.xy(CX, CY); IR = 0.033 * P.s   # ada yarıçapı ~
    lay = L(); dl = ImageDraw.Draw(lay)
    # 1880: tekne gelir, geri döner
    a = vis(t, st("y1880") + .2, en("y1880") + .2, .3, .4)
    if a > 0:
        p = prog(t, st("y1880") + .2, en("y1880") - st("y1880"))
        q = math.sin(min(1, p) * math.pi)    # git-gel
        bx = cx - IR*3.2 + q * IR*1.9; by = cy + IR*0.9 + 6*SS*math.sin(t*3)
        boat(dl, bx, by, 2.0, a)
        card(img, "uk", bx, by - 230*SS, 150, a)
    # ok yağmuru
    if st("arrows") < t < en("arrows") + .8:
        for k in range(14):
            t0 = st("arrows") + .4 + k * .27; p = (t - t0) / .9
            an = k * 2.399; d0 = IR*.6; d1 = IR*2.6
            projectile(dl, (cx + math.cos(an)*d0, cy + math.sin(an)*d0), (cx + math.cos(an)*d1, cy + math.sin(an)*d1), p, 1, .12)
    # 2004: helikopter + oklar
    a = vis(t, st("y2004") + .2, en("y2004") + .3, .3, .4)
    if a > 0:
        p = prog(t, st("y2004") + .2, en("y2004") - st("y2004"))
        app = eout(min(1, p / .45)); ret = ease(max(0, (p - .7) / .3))
        hx = cx + IR*3.0 - app*IR*1.6 + ret*IR*2.2; hy = cy - IR*2.6 + app*IR*1.1 - ret*IR*1.4
        heli(dl, hx, hy, 1.9, a, t)
        for k in range(6):
            t0 = st("y2004") + 1.2 + k*.3; pp = (t - t0) / .7
            projectile(dl, (cx + IR*.3, cy - IR*.2), (hx + (k-3)*12*SS, hy + 20*SS), pp, 1, .15)
    # 2006: sürüklenen balıkçı teknesi + X
    a = vis(t, st("y2006") + .2, en("y2006") + .3, .3, .4)
    if a > 0:
        p = eout(prog(t, st("y2006") + .2, 2.2))
        bx = cx - IR*2.8 + p*IR*1.5; by = cy - IR*1.6 + p*IR*.9 + 5*SS*math.sin(t*2.5)
        boat(dl, bx, by, 1.7, a, (120, 120, 130)); img.alpha_composite(lay); lay = L(); dl = ImageDraw.Draw(lay)
        xmark(img, bx, by - 50*SS, 64 * back(prog(t, st("y2006") + 2.4, .3)), a * (t > st("y2006") + 2.4))
    # 2018: kano rotası
    a = vis(t, st("y2018") + .2, en("gone") + .2, .3, .5)
    if a > 0:
        p0 = (cx + IR*2.6, cy + IR*2.4); p1 = (cx + IR*.75, cy + IR*.55)
        pts = [(p0[0] + (p1[0]-p0[0])*k/40, p0[1] + (p1[1]-p0[1])*k/40 + math.sin(k/6)*12*SS) for k in range(41)]
        pr = eout(prog(t, st("y2018") + .4, en("y2018") - st("y2018") - .2))
        dashed(dl, partial(pts, pr), A(WHITE, a), 5*SS, 14, 12)
        kp = partial(pts, pr)[-1]
        kayak(dl, kp[0], kp[1], 1.7, a * (1 - prog(t, en("y2018") + .3, .5)))
    # yasak bölgede bekleyen gemiler
    a = vis(t, st("zone") + 2.0, st("flu") - .4, .3, .5)
    if a > 0:
        rp = ZONE_R * P.s
        for k, an in enumerate((-.6, 2.3, 3.9)):
            bx, by = cx + math.cos(an)*(rp + 90*SS), cy + math.sin(an)*(rp + 90*SS) + 4*SS*math.sin(t*2 + k)
            boat(dl, bx, by, 1.1, a, (90, 110, 140))
    # virüsler
    a = vis(t, st("flu") + .3, en("flu") + .3, .4, .5)
    if a > 0:
        for k in range(5):
            an = k * 1.257 + .4; p = eout(prog(t, st("flu") + .3 + k*.25, 3.0))
            dd = IR*(3.2 - p*1.9)
            virus(dl, cx + math.cos(an)*dd, cy + math.sin(an)*dd, 38*(1 + .08*math.sin(t*5 + k)), a, t + k)
    # kalkan
    a = vis(t, st("survive") + .2, st("cta") + .2, .5, .5)
    if a > 0:
        shield(dl, cx, cy, IR*1.45/SS*(0.92 + 0.08*back(prog(t, st("survive") + .2, .6))), a)
    img.alpha_composite(lay)

    # ---- etiketler ----
    def lab(text, lon, lat, size, a, col=LABEL, sc=1., rot=0):
        if a > 0: stamp_text(img, text, P.xy(lon, lat), FA, size, fill=col, stroke=BLACK, alpha=a, scale=sc, rot=rot)
    wide = clamp01(1 - (cam[2] - 30) / 60)
    lab("HİNDİSTAN", 78.5, 21.0, 70, wide * vis(t, .2, 99, .4, .3))
    lab("BENGAL KÖRFEZİ", 88.5, 15.6, 46, clamp01(1 - abs(math.log(cam[2]/45))) * vis(t, .4, 99, .4, .3), SEA_TXT)
    a_and = clamp01(1 - abs(math.log(cam[2] / 230)) * 1.5)
    lab("ANDAMAN ADALARI", 93.75, 12.55, 50, a_and, WHITE)
    if a_and > .2:
        x, y = P.xy(CX, CY); rr = (14 + 4*math.sin(t*6))*SS
        ImageDraw.Draw(img).ellipse((x-rr, y-rr, x+rr, y+rr), outline=RED, width=5*SS)
        lab("KUZEY SENTİNEL", CX - 0.15, CY - 0.28, 40, a_and, RED)
    typewriter(img, t, "KUZEY SENTİNEL", st("name") + .1, 560, 120)
    if zoomed:
        a = vis(t, st("tribe") + .3, en("tribe") + .2, .3, .3)
        pill(img, "DIŞ DÜNYAYLA TEMAS: YOK", W/2, 1250*SS, 52, bg=WHITE, fg=BLACK, alpha=a, scale=back(prog(t, st("tribe") + .3, .35)))
        a = vis(t, st("unknown") + .3, en("unknown") + .2, .3, .3)
        pill(img, "NÜFUS: ?", cx - IR*1.6, cy - IR*1.5, 54, bg=YEL, alpha=a, scale=back(prog(t, st("unknown") + .3, .35)))
        a = vis(t, st("unknown") + 1.1, en("unknown") + .2, .3, .3)
        pill(img, "DİL: ?", cx + IR*1.6, cy + IR*1.5, 54, bg=YEL, alpha=a, scale=back(prog(t, st("unknown") + 1.1, .35)))
        a = vis(t, st("y1880") + 2.6, en("y1880") + .2, .3, .3)
        pill(img, "6 KİŞİ KAÇIRILDI", W/2, 1250*SS, 52, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("y1880") + 2.6, .35)))
        a = vis(t, st("y2006") + 2.5, en("y2006") + .2, .3, .3)
        pill(img, "2 BALIKÇI", W/2, 1250*SS, 52, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("y2006") + 2.5, .35)))
        a = vis(t, st("zone") + 1.6, st("flu") - .4, .3, .4)
        pill(img, "9 KM YASAK BÖLGE", W/2, 470*SS, 58, bg=RED, fg=WHITE, alpha=a, scale=back(prog(t, st("zone") + 1.6, .35)))
        a = vis(t, st("flu") + .8, en("flu") + .2, .3, .3)
        pill(img, "BAĞIŞIKLIK YOK", W/2, 470*SS, 58, bg=WHITE, fg=RED, alpha=a, scale=back(prog(t, st("flu") + .8, .35)))
        a = vis(t, st("survive") + .6, st("cta") + .1, .3, .3)
        pill(img, "HAYATTA KALMA MÜCADELESİ", W/2, 470*SS, 50, bg=YEL, alpha=a, scale=back(prog(t, st("survive") + .6, .35)))
    timeline(img, t)
    header(img, t)
    a3 = vis(t, st("cta") + 1.2, TOTAL, .25, .3)
    pill(img, "YORUMLARA YAZ!", W/2, 560*SS, 64, alpha=a3, scale=back(prog(t, st("cta") + 1.2, .35)))

    # ---- sinematik katmanlar ----
    dark = .45 + .45 * vis(t, en("y2018") + .2, st("zone") + .3, .4, .9)
    img.paste((0, 0, 0), (0, 0), VIG.point(lambda v: int(v * dark)))
    fl = 1 - clamp01((t - (en("y2018") + .35)) / .5) if t >= en("y2018") + .35 else 0
    if fl > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), A(RED, fl * .45)))
    if warm > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 170, 80, int(30 * warm))))
    R2.caption(img, t)
    if sx or sy:
        img = img.transform(img.size, Image.AFFINE, (1, 0, -sx, 0, 1, -sy), resample=Image.BILINEAR)
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
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s3_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
