# --- render5.py'den otomatik alınan ortak parçalar ---
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
def tex_info(lon0, lon1, lat0, lat1, img):
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1)
    return dict(img=img, x0=x0, y1=y1, mpp=(x1 - x0) / img.width, box=(x0, y0, x1, y1))
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

def typewriter(img, t, text, t0, t1, y, size, col=WHITE):
    a = vis(t, t0, t1, .1, .4)
    if a <= 0: return
    n = len(text) if t > t0 + .9 else max(1, int(len(text) * clamp01((t - t0) / .9)))
    stamp_text(img, text[:n], (W / 2, y * SS), FA, size, fill=col, alpha=a)
    if t > t0 + .9:
        tw = font(FA, size * SS).getlength(text); u = eout(prog(t, t0 + .9, .4))
        lay = L(); ImageDraw.Draw(lay).line([(W / 2 - tw / 2 * u, (y + size * .62) * SS), (W / 2 + tw / 2 * u, (y + size * .62) * SS)], fill=A(RED, a), width=8 * SS)
        img.alpha_composite(lay)
