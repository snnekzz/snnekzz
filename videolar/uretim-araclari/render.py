"""Mısır sınırları – 9:16 harita animasyonu renderer."""
import json, math, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import shape, box, Polygon, LineString, MultiPolygon

SS = 2                      # süper örnekleme
OW, OH = 1080, 1920
W, H = OW * SS, OH * SS
FPS = 30
LAT0 = math.cos(math.radians(25))

T = json.load(open("timing.json"))
SEG = {s["scene"]: s for s in T["segs"]}
TOTAL = T["total"]
def st(n): return SEG[n]["start"]
def en(n): return SEG[n]["end"]

# ---------- renkler ----------
OCEAN1, OCEAN2 = (22, 52, 84), (12, 30, 52)
GRAT = (34, 68, 104)
LAND = (236, 226, 204)
BORDER = (140, 120, 95)
YEL = (255, 210, 63)
WHITE = (255, 255, 255)
BLACK = (15, 15, 18)
SAND = (226, 190, 128)

FA, F9, F7 = "anton.ttf", "mont900.ttf", "mont700.ttf"
_fc = {}
def font(p, size):
    k = (p, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, max(4, int(size)))
    return _fc[k]

def tr_up(s): return s.replace("i", "İ").replace("ı", "I").upper()

# ---------- easing ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return 4*x*x*x if x < .5 else 1 - (-2*x+2)**3/2
def eout(x): x = clamp(x); return 1 - (1-x)**3
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3*(x-1)**3 + c1*(x-1)**2
def prog(t, t0, d): return clamp((t - t0) / d)
def vis(t, t0, t1, fi=.25, fo=.25):
    """t0'da belirir, t1'de kaybolur -> alfa"""
    if t < t0 or t > t1 + fo: return 0.
    return min(eout((t - t0) / fi), 1 - clamp((t - t1) / fo))

# ---------- veri ----------
G = json.load(open("countries50.json"))
REG = box(-20, -5, 60, 45)
CN = {}
for f in G["features"]:
    if not f.get("geometry"): continue
    g = shape(f["geometry"])
    if g.intersects(REG): CN[f["properties"]["name"]] = g
EG, SD, LY = CN["Egypt"], CN["Sudan"], CN["Libya"]
EGSD = EG.union(SD)

def polys(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]

BIRTAWIL = Polygon([(33.17, 22.0), (34.08, 22.0), (33.95, 21.80), (33.56, 21.72), (33.37, 21.84)])
HALAIB = Polygon([(34.08, 22.0), (35.6, 23.15), (37.6, 23.15), (37.6, 22.0)]).intersection(EGSD)
ADMIN = LineString([(31.2, 22.0), (33.17, 22.0), (33.37, 21.84), (33.56, 21.72), (33.95, 21.80),
                    (34.08, 22.0), (35.6, 23.15)])
NILE = [(31.33, 21.6), (31.45, 22.0), (31.7, 22.5), (32.3, 22.95), (32.6, 23.4), (32.88, 23.97),
        (32.94, 24.47), (32.87, 24.98), (32.55, 25.3), (32.64, 25.7), (32.72, 26.16), (32.24, 26.05),
        (31.69, 26.56), (31.18, 27.18), (30.75, 28.1), (30.95, 28.6), (31.1, 29.07), (31.23, 29.6),
        (31.24, 30.05)]
ROSETTA = [(31.24, 30.05), (31.0, 30.5), (30.7, 31.0), (30.42, 31.46)]
DAMIETTA = [(31.24, 30.05), (31.3, 30.5), (31.55, 31.0), (31.82, 31.42)]
DELTA = Polygon([(31.24, 30.05), (30.35, 31.45), (30.9, 31.55), (31.4, 31.55), (31.9, 31.45)])

# ---------- kamera ----------
CAMS = {  # (lon, lat, px/derece @1080)
    "wide": (31.0, 25.0, 30),
    "egypt": (30.6, 26.9, 86),
    "south": (31.0, 24.0, 92),
    "west": (27.6, 26.6, 92),
    "egypt2": (30.6, 26.9, 88),
    "bt": (34.85, 22.2, 300),
    "end": (34.6, 22.25, 230),
}
KEYS = [  # (zaman, hedef, süre)
    (0.5, "egypt", 2.3),
    (st("south") - .25, "south", 1.1),
    (st("west") - .25, "west", 1.1),
    (st("both") - .2, "egypt2", 1.0),
    (st("zoom_bt") - .3, "bt", 1.5),
    (st("cta") - .2, "end", 1.2),
]
def camera(t):
    cur = CAMS["wide"]
    for k, name, d in KEYS:
        tgt = CAMS[name]
        if t <= k: break
        p = ease((t - k) / d)
        # zoom'u logaritmik enterpole et
        s = math.exp(math.log(cur[2]) + (math.log(tgt[2]) - math.log(cur[2])) * p)
        cur = (cur[0] + (tgt[0]-cur[0])*p, cur[1] + (tgt[1]-cur[1])*p, s)
    # hafif "nefes" hareketi
    cur = (cur[0], cur[1], cur[2] * (1 + 0.012 * math.sin(t * 0.6)))
    return cur

class Proj:
    def __init__(s, cam):
        s.cx, s.cy, sc = cam; s.s = sc * SS
    def xy(s, lon, lat):
        return (W/2 + (lon - s.cx) * s.s * LAT0, H/2 - (lat - s.cy) * s.s)
    def arr(s, coords):
        a = np.asarray(coords, dtype=np.float64)
        x = W/2 + (a[:, 0] - s.cx) * s.s * LAT0
        y = H/2 - (a[:, 1] - s.cy) * s.s
        return list(zip(x.tolist(), y.tolist()))
    def view(s):
        dx = W/2 / (s.s*LAT0) * 1.1; dy = H/2 / s.s * 1.1
        return box(s.cx-dx, s.cy-dy, s.cx+dx, s.cy+dy)

# ---------- statik katmanlar ----------
def make_ocean():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W/2)/W)**2 + ((y - H*0.45)/H)**2) * 1.6
    d = np.clip(d, 0, 1)[..., None]
    c = np.array(OCEAN1) * (1-d) + np.array(OCEAN2) * d
    return Image.fromarray(c.astype(np.uint8), "RGB")
OCEAN = make_ocean()

def make_dunes():
    im = Image.new("RGBA", (W, H), SAND + (255,))
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for row in range(0, H, 46*SS):
        ph = rnd.random() * 6; amp = rnd.uniform(6, 14) * SS
        pts = [(x, row + amp*math.sin(x/(70*SS) + ph) + 8*SS*math.sin(x/(23*SS))) for x in range(0, W+20, 12)]
        d.line(pts, fill=(196, 156, 96, 255), width=3*SS)
    return im
DUNES = make_dunes()

def stamp_text(img, text, xy, fp, size, fill=WHITE, stroke=BLACK, sw=None, alpha=1., anchor="mm", scale=1., rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    size = size * SS * scale
    f = font(fp, size)
    sw = int((sw if sw is not None else max(2, size/(9*SS))) * SS) if sw is not None else int(max(2, size/9))
    l, t_, r, b = f.getbbox(text, stroke_width=sw)
    pad = 4
    lay = Image.new("RGBA", (r - l + pad*2, b - t_ + pad*2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - l, pad - t_), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha)); lay.putalpha(a)
    x, y = xy
    lw, lh = lay.size
    if anchor == "mm": ox, oy = x - lw/2, y - lh/2
    elif anchor == "lm": ox, oy = x, y - lh/2
    else: ox, oy = x - lw, y - lh/2
    img.alpha_composite(lay, (int(ox), int(oy)))

def pill(img, text, cx, cy, size, bg=YEL, fg=BLACK, alpha=1., scale=1.):
    if alpha <= .01 or scale <= .01: return
    f = font(FA, size*SS*scale)
    l, t_, r, b = f.getbbox(text)
    w, h = r - l + 50*SS*scale, b - t_ + 30*SS*scale
    lay = Image.new("RGBA", (int(w)+8, int(h)+8), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((4, 4, w+4, h+4), radius=int(h/2), fill=bg + (255,), outline=BLACK, width=int(4*SS*scale)+1)
    d.text((4 + w/2, 4 + h/2), text, font=f, fill=fg, anchor="mm")
    if alpha < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v*alpha)))
    img.alpha_composite(lay, (int(cx - lay.width/2), int(cy - lay.height/2)))
    return lay.width

# ---------- bayraklar ----------
def flag_img(kind, w, h):
    w, h = max(2, int(w)), max(2, int(h))
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    if kind == "egypt":
        d.rectangle((0, 0, w, h/3), fill=(206, 17, 38)); d.rectangle((0, h/3, w, 2*h/3), fill=WHITE)
        d.rectangle((0, 2*h/3, w, h), fill=BLACK)
    elif kind == "sudan":
        d.rectangle((0, 0, w, h/3), fill=(210, 16, 52)); d.rectangle((0, h/3, w, 2*h/3), fill=WHITE)
        d.rectangle((0, 2*h/3, w, h), fill=BLACK)
        d.polygon([(0, 0), (min(w, h)*0.75, h/2), (0, h)], fill=(0, 114, 41))
    elif kind == "libya":
        d.rectangle((0, 0, w, h/4), fill=(231, 0, 19)); d.rectangle((0, h/4, w, 3*h/4), fill=BLACK)
        d.rectangle((0, 3*h/4, w, h), fill=(35, 158, 70))
        r = h*0.14; cx, cy = w/2 - r*0.2, h/2
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=WHITE)
        d.ellipse((cx-r*0.78+r*0.28, cy-r*0.8, cx+r*0.8+r*0.28, cy+r*0.8), fill=BLACK)
        star(d, cx + r*1.05, cy, r*0.42, WHITE)
    elif kind == "uk":
        d.rectangle((0, 0, w, h), fill=(1, 33, 105))
        lw = h*0.2
        d.line([(0, 0), (w, h)], fill=WHITE, width=int(lw)); d.line([(0, h), (w, 0)], fill=WHITE, width=int(lw))
        d.line([(0, 0), (w, h)], fill=(200, 16, 46), width=int(lw*0.4)); d.line([(0, h), (w, 0)], fill=(200, 16, 46), width=int(lw*0.4))
        d.rectangle((w/2 - h/6, 0, w/2 + h/6, h), fill=WHITE); d.rectangle((0, h/2 - h/6, w, h/2 + h/6), fill=WHITE)
        d.rectangle((w/2 - h/10, 0, w/2 + h/10, h), fill=(200, 16, 46)); d.rectangle((0, h/2 - h/10, w, h/2 + h/10), fill=(200, 16, 46))
    elif kind == "italy":
        d.rectangle((0, 0, w/3, h), fill=(0, 146, 70)); d.rectangle((w/3, 0, 2*w/3, h), fill=WHITE)
        d.rectangle((2*w/3, 0, w, h), fill=(206, 43, 55))
    return im

def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi/2 + i*math.pi/5; rr = r if i % 2 == 0 else r*0.42
        pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
    d.polygon(pts, fill=fill)

def card(img, kind, cx, cy, w, alpha=1., scale=1., label=None):
    if alpha <= .01 or scale <= .01: return
    w = w*SS*scale; h = w*2/3
    fl = flag_img(kind, w, h).convert("RGBA")
    m = Image.new("L", fl.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, fl.width-1, fl.height-1), radius=int(h*0.12), fill=int(255*alpha))
    fl.putalpha(m)
    bw = int(6*SS*scale)
    bg = Image.new("RGBA", (fl.width + bw*2, fl.height + bw*2), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle((0, 0, bg.width-1, bg.height-1), radius=int(h*0.12)+bw, fill=(255, 255, 255, int(255*alpha)))
    bg.alpha_composite(fl, (bw, bw))
    img.alpha_composite(bg, (int(cx - bg.width/2), int(cy - bg.height/2)))
    if label: stamp_text(img, label, (cx, cy + bg.height/2 + 40*SS*scale), FA, 46*scale, alpha=alpha)

# ---------- çizim yardımcıları ----------
def poly_mask(P, g, mask=None, fill=255):
    if mask is None: mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for p in polys(g):
        pts = P.arr(p.exterior.coords)
        if len(pts) > 2: d.polygon(pts, fill=fill)
        for h in p.interiors:
            d.polygon(P.arr(h.coords), fill=0)
    return mask

def bbox_screen(P, g):
    x0, y0, x1, y1 = g.bounds
    a = P.xy(x0, y1); b = P.xy(x1, y0)
    return (max(0, a[0]), max(0, a[1]), min(W, b[0]), min(H, b[1]))

def flag_fill(img, P, g, kind, alpha):
    if alpha <= .01: return
    x0, y0, x1, y1 = bbox_screen(P, g)
    if x1 - x0 < 4 or y1 - y0 < 4: return
    fl = flag_img(kind, x1 - x0, y1 - y0)
    m = poly_mask(P, g, fill=int(255*alpha*0.92))
    lay = Image.new("RGB", (W, H)); lay.paste(fl, (int(x0), int(y0)))
    img.paste(lay, (0, 0), m)

def partial(pts, p):
    """polyline'ın ilk p oranı"""
    if p >= 1: return pts
    if p <= 0 or len(pts) < 2: return pts[:1]
    L = [math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1)]
    tot = sum(L) * p; out = [pts[0]]
    for i, l in enumerate(L):
        if tot >= l: out.append(pts[i+1]); tot -= l
        else:
            f = tot / l if l else 0
            out.append((pts[i][0] + (pts[i+1][0]-pts[i][0])*f, pts[i][1] + (pts[i+1][1]-pts[i][1])*f)); break
    return out

def densify(coords, n=40):
    out = []
    for a, b in zip(coords[:-1], coords[1:]):
        for k in range(n): out.append((a[0] + (b[0]-a[0])*k/n, a[1] + (b[1]-a[1])*k/n))
    out.append(coords[-1]); return out

def glow_line(img, pts, color, width, alpha=1., glow=True):
    if alpha <= .01 or len(pts) < 2: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if glow:
        d.line(pts, fill=color + (int(90*alpha),), width=int(width*3.2), joint="curve")
    d.line(pts, fill=BLACK + (int(255*alpha),), width=int(width*1.6), joint="curve")
    d.line(pts, fill=color + (int(255*alpha),), width=int(width), joint="curve")
    img.alpha_composite(lay)

def dashed(d, pts, color, width, dash=26, gap=18):
    dash *= SS; gap *= SS
    on, acc = True, 0
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.dist(a, b)
        if L == 0: continue
        pos = 0
        while pos < L:
            seg = (dash if on else gap) - acc
            nxt = min(L, pos + seg)
            if on:
                d.line([(a[0]+(b[0]-a[0])*pos/L, a[1]+(b[1]-a[1])*pos/L),
                        (a[0]+(b[0]-a[0])*nxt/L, a[1]+(b[1]-a[1])*nxt/L)], fill=color, width=width)
            acc += nxt - pos
            if acc >= (dash if on else gap) - 1e-6: on = not on; acc = 0
            pos = nxt

def ruler(img, p0, p1, f, side, alpha=1.):
    """p0->p1 doğrusu boyunca f konumunda kayan cetvel"""
    if alpha <= .01: return
    ang = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy*side, ux*side
    cx = p0[0] + (p1[0]-p0[0])*f; cy = p0[1] + (p1[1]-p0[1])*f
    L, Wd, off = 420*SS, 74*SS, 14*SS
    def P(a, b): return (cx + ux*a + nx*(off+b), cy + uy*a + ny*(off+b))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([P(-L/2, 0), P(L/2, 0), P(L/2, Wd), P(-L/2, Wd)], fill=(250, 214, 80, int(225*alpha)), outline=(60, 45, 10, int(255*alpha)))
    for k in range(0, 43):
        a = -L/2 + 10*SS + k*(L-20*SS)/42
        tl = (30 if k % 10 == 0 else 20 if k % 5 == 0 else 11) * SS
        d.line([P(a, 0), P(a, tl)], fill=(60, 45, 10, int(255*alpha)), width=2*SS)
    img.alpha_composite(lay)

def arrow(d, a, b, color, width):
    d.line([a, b], fill=color, width=width)
    ang = math.atan2(b[1]-a[1], b[0]-a[0]); s = width*3.2
    d.polygon([b, (b[0]-s*math.cos(ang-0.45), b[1]-s*math.sin(ang-0.45)),
               (b[0]-s*math.cos(ang+0.45), b[1]-s*math.sin(ang+0.45))], fill=color)

# ---------- altyazı ----------
def build_captions():
    caps = []
    for s in T["segs"]:
        words = s["cap"].split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or len(" ".join(cur)) > 17 or w[-1] in ",.?!:":
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        if len(chunks) > 1 and len(chunks[-1]) == 1 and len(chunks[-2]) <= 3 and not chunks[-2][-1][-1] in ".?!":
            last = chunks.pop(); chunks[-1] = chunks[-1] + last
        wts = [len(w) + 2.5 for w in words]
        dur = s["end"] - s["start"]; tsum = sum(wts)
        t = s["start"]; wi = 0
        for ch in chunks:
            wt = []
            for w in ch:
                ex = s.get("tts_word_starts")
                if ex and len(ex) == len(words):   # ElevenLabs kelime zamanlaması
                    t = ex[wi]
                wt.append(t); t += dur * wts[wi] / tsum; wi += 1
            caps.append({"words": ch, "wt": wt, "start": wt[0], "end": t})
    for i in range(len(caps) - 1):
        caps[i]["end"] = min(caps[i+1]["start"], caps[i]["end"] + 0.35)
    return caps
CAPS = build_captions()

def draw_caption(img, t):
    c = next((c for c in CAPS if c["start"] <= t < c["end"]), None)
    if not c: return
    pop = 0.86 + 0.14 * back((t - c["start"]) / 0.12)
    size = 82 * SS * pop
    f = font(F9, size)
    words = [tr_up(w) for w in c["words"]]
    sw = int(size / 8)
    sp = f.getlength(" ")
    lines, cur = [], []
    for w in words:
        if cur and sum(f.getlength(x) for x in cur + [w]) + sp*len(cur) > W*0.86:
            lines.append(cur); cur = []
        cur.append(w)
    lines.append(cur)
    widest = max(sum(f.getlength(x) for x in ln) + sp*(len(ln)-1) for ln in lines)
    if widest > W*0.9:
        size = size * W*0.9 / widest; f = font(F9, size); sw = int(size/8); sp = f.getlength(" ")
    cy = 1455 * SS - (len(lines)-1) * size * 0.6
    idx = 0
    cur_i = max(i for i, wt in enumerate(c["wt"]) if wt <= t)
    lay = Image.new("RGBA", (W, int(size*1.2*len(lines) + size*0.8)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for li, line in enumerate(lines):
        tw = sum(f.getlength(w) for w in line) + sp*(len(line)-1)
        x = W/2 - tw/2; y = size*0.7 + li*size*1.2
        for w in line:
            col = YEL if idx == cur_i else WHITE
            d.text((x, y), w, font=f, fill=col, stroke_width=sw, stroke_fill=BLACK, anchor="lm")
            x += f.getlength(w) + sp; idx += 1
    img.alpha_composite(lay, (0, int(cy - size*0.7)))

def draw_header(img, t):
    a = vis(t, 0.15, en("nomans") + 0.3, .3, .4)
    if a <= 0: return
    sc = 0.9 + 0.1*back(prog(t, 0.15, .35))
    lay = Image.new("RGBA", (W, 260*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 880*SS*sc, 190*SS*sc
    x0, y0 = W/2 - w/2, 130*SS - h/2
    d.rounded_rectangle((x0, y0, x0+w, y0+h), radius=int(34*SS), fill=(15, 15, 18, 235), outline=YEL + (255,), width=5*SS)
    d.text((W/2, y0 + h*0.31), "MISIR'IN SINIRLARI", font=font(FA, 70*SS*sc), fill=WHITE, anchor="mm")
    d.text((W/2, y0 + h*0.71), "NEDEN DÜMDÜZ?", font=font(FA, 76*SS*sc), fill=YEL, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v*a)))
    img.alpha_composite(lay, (0, 150*SS))

# ---------- kare ----------
LINE22 = [(24.978, 22.0), (36.87, 22.0)]
LINE25 = [(25.0, 22.0), (25.0, 31.49)]

def frame(t):
    cam = camera(t); P = Proj(cam); V = P.view()
    img = OCEAN.copy()
    d = ImageDraw.Draw(img)
    # graticule (1°)
    lo0, la0, lo1, la1 = V.bounds
    step = 1 if cam[2] > 60 else 5
    for lo in range(int(lo0) - 1, int(lo1) + 2):
        if lo % step == 0: d.line([P.xy(lo, la0), P.xy(lo, la1)], fill=GRAT, width=SS)
    for la in range(int(la0) - 1, int(la1) + 2):
        if la % step == 0: d.line([P.xy(lo0, la), P.xy(lo1, la)], fill=GRAT, width=SS)
    # ülkeler
    vis_c = [(n, g) for n, g in CN.items() if g.intersects(V)]
    for n, g in vis_c:
        for p in polys(g):
            pts = P.arr(p.exterior.coords)
            if len(pts) > 2: d.polygon(pts, fill=LAND)
    img = img.convert("RGBA")

    # çöl dokusu
    a_des = vis(t, st("desert"), st("zoom_bt") - .2, .6, .6)
    if a_des > 0:
        m = Image.new("L", (W, H), 0)
        for n, g in vis_c:
            if n in ("Egypt", "Libya", "Sudan", "Chad", "Saudi Arabia", "S. Sudan"):
                poly_mask(P, g, m, fill=int(235*a_des))
        img.paste(DUNES, (0, 0), m)

    # bayraklar
    egA = min(eout(prog(t, 0.9, 1.2)), 1 - eout(prog(t, st("desert"), .6)))
    flag_fill(img, P, EG, "egypt", egA)
    sdA = min(eout(prog(t, st("south"), .8)), 1 - eout(prog(t, st("desert"), .6)))
    flag_fill(img, P, SD, "sudan", sdA)
    lyA = min(eout(prog(t, st("west"), .8)), 1 - eout(prog(t, st("desert"), .6)))
    flag_fill(img, P, LY, "libya", lyA)
    # yakın plan tonları
    btA = eout(prog(t, st("zoom_bt"), .8))
    if btA > 0:
        img.paste((240, 205, 200), (0, 0), poly_mask(P, EG, fill=int(150*btA)))
        img.paste((200, 228, 200), (0, 0), poly_mask(P, SD, fill=int(150*btA)))

    # sınır çizgileri
    d = ImageDraw.Draw(img)
    bw = max(2, int(2.2*SS * min(1.6, cam[2]/80)))
    for n, g in vis_c:
        for p in polys(g):
            d.line(P.arr(p.exterior.coords), fill=BORDER, width=bw, joint="curve")

    # Nil
    a_nile = vis(t, st("nile"), st("zoom_bt"), .4, .5)
    if a_nile > 0:
        pn = eout(prog(t, st("nile"), 1.4))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.polygon(P.arr(DELTA.exterior.coords), fill=(110, 170, 70, int(200*a_nile*pn)))
        main = P.arr(densify(NILE, 8))
        dl.line(partial(main, pn), fill=(110, 170, 70, int(170*a_nile)), width=int(30*SS), joint="curve")
        dl.line(partial(main, pn), fill=(40, 120, 220, int(255*a_nile)), width=int(8*SS), joint="curve")
        if pn > .9:
            for br in (ROSETTA, DAMIETTA):
                dl.line(P.arr(br), fill=(40, 120, 220, int(255*a_nile)), width=int(6*SS), joint="curve")
        img.alpha_composite(lay)
        # nüfus noktaları
        rnd = random.Random(7); dd = ImageDraw.Draw(img)
        pd = prog(t, st("nile") + 1.0, 2.0)
        allp = NILE + DELTA.exterior.coords[:]
        for k in range(160):
            if k/160 > pd: break
            if k < 70:
                lo, la = DELTA.centroid.x + rnd.uniform(-0.6, 0.6), DELTA.centroid.y + rnd.uniform(-0.45, 0.6)
                if not DELTA.buffer(0.05).contains(shape({"type": "Point", "coordinates": (lo, la)})): continue
            else:
                i = rnd.randrange(len(NILE)-1); f_ = rnd.random()
                a, b = NILE[i], NILE[i+1]
                lo = a[0] + (b[0]-a[0])*f_ + rnd.uniform(-.12, .12); la = a[1] + (b[1]-a[1])*f_ + rnd.uniform(-.1, .1)
            x, y = P.xy(lo, la); r = 4*SS
            dd.ellipse((x-r, y-r, x+r, y+r), fill=(30, 30, 30))

    # 22. enlem / 25. boylam
    p22 = P.arr(densify(LINE22, 4)); p25 = P.arr(densify(LINE25, 4))
    lw = 9*SS
    a_lines = 1 - eout(prog(t, st("zoom_bt"), .6))
    f22 = ease(prog(t, st("ruler") + .05, 1.05))
    f25 = ease(prog(t, st("ruler") + 1.15, 1.0))
    pulse22 = 1 + 0.5*max(0, math.sin((t - st("south"))*6)) if st("south") < t < en("south_len") else 1
    pulse25 = 1 + 0.5*max(0, math.sin((t - st("west"))*6)) if st("west") < t < en("west_line") else 1
    if f22 > 0:
        # paralel boyunca kesikli çizgi
        a_par = vis(t, st("south"), en("south_len"), .4, .4) * a_lines
        if a_par > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dashed(ImageDraw.Draw(lay), [P.xy(lo0, 22), P.xy(lo1, 22)], (255, 255, 255, int(200*a_par)), 3*SS)
            img.alpha_composite(lay)
        glow_line(img, partial(p22, f22), YEL, lw*pulse22, a_lines)
    if f25 > 0:
        a_mer = vis(t, st("west"), en("west_line"), .4, .4) * a_lines
        if a_mer > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dashed(ImageDraw.Draw(lay), [P.xy(25, la1), P.xy(25, la0)], (255, 255, 255, int(200*a_mer)), 3*SS)
            img.alpha_composite(lay)
        glow_line(img, partial(p25, f25), YEL, lw*pulse25, a_lines)
    # cetveller
    r1 = vis(t, st("ruler"), st("ruler") + 1.15, .2, .25)
    ruler(img, p22[0], p22[-1], f22, 1, r1)
    r2 = vis(t, st("ruler") + 1.1, en("ruler") + .1, .2, .3)
    ruler(img, p25[0], p25[-1], f25, 1, r2)
    r3 = vis(t, st("ruler2") + .3, en("ruler2"), .2, .3)
    if r3 > 0:
        ruler(img, p25[-1], p25[0], ease(prog(t, st("ruler2") + .3, 2.4)), -1, r3)

    # uzunluk ölçüsü
    a_len = vis(t, st("south_len") + .1, en("south_len") + .3, .3, .3)
    if a_len > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        y = p22[0][1] - 70*SS; x0, x1 = p22[0][0], p22[-1][0]
        pe = eout(prog(t, st("south_len") + .1, .8)); xm = (x0+x1)/2
        c = (255, 255, 255, int(255*a_len))
        arrow(dl, (xm, y), (xm - (xm-x0)*pe, y), c, 5*SS); arrow(dl, (xm, y), (xm + (x1-xm)*pe, y), c, 5*SS)
        img.alpha_composite(lay)
        pill(img, "1.276 KM", xm, y - 70*SS, 54, alpha=a_len, scale=back(prog(t, st("south_len") + .3, .35)))

    # 1902 idari çizgisi
    a_adm = vis(t, st("line1902"), TOTAL, .3, .3)
    if a_adm > 0:
        pa = eout(prog(t, st("line1902") + .2, 1.6))
        seg_ = ADMIN.intersection(EGSD.buffer(0.01))
        lines = [seg_] if seg_.geom_type == "LineString" else list(getattr(seg_, "geoms", []))
        pts = P.arr(densify(list(ADMIN.coords), 20))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dashed(dl, partial(pts, pa), (255, 255, 255, int(255*a_adm)), 7*SS, 22, 14)
        img.alpha_composite(lay)
        # 22. enlem burada da (yakın planda)
        glow_line(img, P.arr(densify([(31.2, 22.0), (36.87, 22.0)], 10)), YEL, 7*SS, a_adm*0.9, glow=False)

    # Halayib
    a_h = vis(t, st("halaib"), TOTAL, .4, .3)
    if a_h > 0:
        m = poly_mask(P, HALAIB, fill=int(255*a_h*0.75))
        x0, y0, x1, y1 = bbox_screen(P, HALAIB)
        stripes = Image.new("RGB", (W, H), (206, 17, 38)); ds = ImageDraw.Draw(stripes)
        for k in range(-H, W + H, 60*SS):
            ds.polygon([(k, 0), (k + 30*SS, 0), (k + 30*SS - H, H), (k - H, H)], fill=(0, 114, 41))
        img.paste(stripes, (0, 0), m)
        glow_line(img, P.arr(HALAIB.exterior.coords), WHITE, 4*SS, a_h, glow=False)
    # Bir Tavil
    a_b = vis(t, st("birtawil"), TOTAL, .3, .3)
    if a_b > 0:
        pul = 0.55 + 0.35*(0.5 + 0.5*math.sin(t*5))
        img.paste(WHITE, (0, 0), poly_mask(P, BIRTAWIL, fill=int(255*a_b*pul)))
        glow_line(img, P.arr(BIRTAWIL.exterior.coords), YEL, 5*SS, a_b, glow=True)

    # ---- etiketler ----
    sc_lab = min(1.0, cam[2] / 86)
    def lab(text, lon, lat, size, alpha=1, col=WHITE, scale=1., stroke=BLACK, rot=0):
        if alpha <= 0: return
        stamp_text(img, text, P.xy(lon, lat), FA, size, fill=col, stroke=stroke, alpha=alpha, scale=scale, rot=rot)
    a_names = vis(t, 0.9, st("zoom_bt") - .3, .4, .4)
    lab("MISIR", 29.6, 26.3, 92*max(.55, sc_lab), a_names, scale=back(prog(t, 0.9, .5)))
    lab("LİBYA", 23.0, 27.6, 70*max(.55, sc_lab), a_names * (1 if t > st("west") - .5 else .75), col=WHITE if t > st("west") else (120, 100, 75), stroke=BLACK if t > st("west") else (245, 238, 222))
    lab("SUDAN", 30.0, 20.4, 70*max(.55, sc_lab), a_names * (1 if t > st("south") - .5 else .75), col=WHITE if t > st("south") else (120, 100, 75), stroke=BLACK if t > st("south") else (245, 238, 222))
    lab("AKDENİZ", 28.5, 32.6, 46*max(.6, sc_lab), a_names, col=(150, 190, 230), stroke=OCEAN2)
    lab("KIZILDENİZ", 36.0, 25.0, 40*max(.6, sc_lab), a_names, col=(150, 190, 230), stroke=OCEAN2, rot=-58)
    # enlem / boylam etiketleri
    a = vis(t, st("south") + .2, en("south_len"), .3, .3)
    lab("22° KUZEY ENLEMİ", 28.6, 22.45, 52, a, col=YEL, scale=back(prog(t, st("south") + .2, .4)))
    a = vis(t, st("west") + .2, en("west_line"), .3, .3)
    lab("25° DOĞU BOYLAMI", 24.55, 26.8, 52, a, col=YEL, scale=back(prog(t, st("west") + .2, .4)), rot=90)
    # çöl / Nil
    a = vis(t, st("desert") + .3, en("ruler2"), .3, .4)
    lab("SAHRA ÇÖLÜ", 27.4, 25.2, 66, a, col=WHITE, scale=back(prog(t, st("desert") + .3, .4)))
    a = vis(t, st("nile") + .4, en("ruler2"), .3, .4)
    lab("NİL", 33.3, 27.3, 64, a, col=(120, 190, 255), scale=back(prog(t, st("nile") + .4, .4)))
    a = vis(t, st("nile") + 1.6, en("nile") + .3, .3, .3)
    pill_xy = P.xy(33.9, 29.0)
    pill(img, "NÜFUSUN %95'İ", pill_xy[0], pill_xy[1], 50, alpha=a, scale=back(prog(t, st("nile") + 1.6, .35)))
    # yakın plan
    zb = vis(t, st("zoom_bt") + .6, TOTAL, .4, .3)
    lab("MISIR", 34.3, 22.85, 70, zb * (1 - vis(t, st("halaib"), TOTAL, .3, .3) * .3))
    lab("SUDAN", 35.7, 21.55, 70, zb)
    lab("KIZILDENİZ", 36.55, 22.6, 42, zb, col=(150, 190, 230), stroke=OCEAN2, rot=-50)
    a = vis(t, st("line1902") + .5, st("halaib"), .3, .3)
    pill(img, "1902 ÇİZGİSİ", *P.xy(32.4, 21.7), 46, bg=WHITE, alpha=a, scale=back(prog(t, st("line1902") + .5, .35)))
    a = vis(t, st("halaib") + .2, TOTAL, .3, .3)
    lab("HALAYİB ÜÇGENİ", 35.45, 22.38, 50, a, scale=back(prog(t, st("halaib") + .2, .4)))
    lab("20.580 KM²", 35.45, 22.18, 36, a, col=YEL)
    a = vis(t, st("birtawil") + .1, TOTAL, .3, .3)
    lab("BİR TAVİL", 33.62, 21.58, 50, a, scale=back(prog(t, st("birtawil") + .1, .4)))
    lab("2.060 KM²", 33.62, 21.43, 36, a, col=YEL)
    # neden: Halayib 10 kat büyük + kıyı
    a = vis(t, st("why_bt") + .6, en("why_bt") + .2, .3, .3)
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        pa_ = eout(prog(t, st("why_bt") + .6, .6))
        A = P.xy(33.75, 21.9); B = P.xy(34.9, 22.55)
        arrow(dl, A, (A[0] + (B[0]-A[0])*pa_, A[1] + (B[1]-A[1])*pa_), (255, 255, 255, int(255*a)), 7*SS)
        img.alpha_composite(lay)
        pill(img, "10 KAT BÜYÜK + DENİZ KIYISI", W/2, 560*SS, 44, alpha=a, scale=back(prog(t, st("why_bt") + 1.0, .35)))
    # sahipsiz damgası
    a = vis(t, st("nomans") + .4, st("cta") + .2, .2, .3)
    if a > 0:
        s = 1.6 - 0.6*eout(prog(t, st("nomans") + .4, .25))
        x, y = P.xy(33.62, 21.86)
        f = font(FA, 64*SS*s); tw = f.getlength("SAHİPSİZ!")
        lay = Image.new("RGBA", (int(tw + 60*SS*s), int(130*SS*s)), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle((4, 4, lay.width-5, lay.height-5), radius=int(14*SS), outline=(225, 30, 40, int(255*a)), width=int(8*SS*s))
        dl.text((lay.width/2, lay.height/2), "SAHİPSİZ!", font=f, fill=(225, 30, 40, int(255*a)), anchor="mm")
        lay = lay.rotate(12, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(lay, (int(x - lay.width/2), int(y - lay.height/2 - 150*SS)))

    # sömürgeci kartları
    a = vis(t, st("colonial") + .5, en("colonial") + .1, .25, .3)
    card(img, "uk", W*0.30, 640*SS, 300, a, back(prog(t, st("colonial") + .5, .4)), "İNGİLTERE")
    a2 = vis(t, st("colonial") + .9, en("colonial") + .1, .25, .3)
    card(img, "italy", W*0.70, 640*SS, 300, a2, back(prog(t, st("colonial") + .9, .4)), "İTALYA")
    # yıl rozetleri
    for yr, kind, t0, t1 in (("1899", "uk", st("south") + .4, en("south_len")),
                             ("1925", "italy", st("west") + .4, en("west_line"))):
        a = vis(t, t0, t1, .25, .3)
        if a > 0:
            sc = back(prog(t, t0, .35))
            pill(img, yr, W/2 - 90*SS, 545*SS, 72, alpha=a, scale=sc)
            card(img, kind, W/2 + 110*SS, 545*SS, 150, a, sc)
    # 1902 rozeti
    a = vis(t, st("line1902") + .2, en("line1902") + .2, .25, .3)
    pill(img, "1902", W/2, 545*SS, 72, bg=WHITE, alpha=a, scale=back(prog(t, st("line1902") + .2, .35)))
    # neden? büyük soru işareti
    a = vis(t, st("why") - .05, en("why") + .15, .15, .25)
    stamp_text(img, "?", (W/2, 800*SS), FA, 330, fill=YEL, alpha=a, scale=back(prog(t, st("why") - .05, .35)), rot=-8 * math.sin(t*4))
    a = vis(t, st("both") + 1.6, en("both") + .1, .2, .25)
    stamp_text(img, "?", (W*0.78, 760*SS), FA, 240, fill=YEL, alpha=a, scale=back(prog(t, st("both") + 1.6, .35)), rot=10)
    # CTA
    a = vis(t, st("cta") + .3, TOTAL, .3, .3)
    if a > 0:
        stamp_text(img, "?", P.xy(33.62, 22.45), FA, 200, fill=YEL, alpha=a, scale=back(prog(t, st("cta") + .3, .4)) * (1 + .05*math.sin(t*6)))
        sc = back(prog(t, st("cta") + 1.3, .35))
        pill(img, "YORUMLARA YAZ!", W/2, 600*SS, 64, bg=YEL, alpha=vis(t, st("cta") + 1.3, TOTAL, .25, .3), scale=sc)
        a3 = vis(t, st("cta") + 1.3, TOTAL, .25, .3)
        if a3 > 0:
            bob = 12*SS*math.sin(t*7)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            cx, cy = W/2, 680*SS + bob
            dl.polygon([(cx - 30*SS, cy), (cx + 30*SS, cy), (cx, cy + 36*SS)], fill=YEL + (int(255*a3),), outline=BLACK + (255,))
            img.alpha_composite(lay)

    draw_header(img, t)
    draw_caption(img, t)
    # başta / sonda hafif karartma
    fade = min(prog(t, 0, .35), 1 - prog(t, TOTAL - .5, .5))
    out = img.convert("RGB").resize((OW, OH), Image.LANCZOS)
    if fade < 1:
        out = Image.blend(Image.new("RGB", (OW, OH)), out, fade)
    return out

def render_chunk(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f"still_{float(tt):05.1f}.png")
    else:
        i0, i1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        render_chunk(i0, i1, out)
