"""Sade sürüm: düz renkler, her an tek fikir."""
import math, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
from render import (Proj, camera, CN, EG, SD, LY, EGSD, polys, BIRTAWIL, HALAIB, ADMIN, NILE, ROSETTA,
                    DAMIETTA, DELTA, stamp_text, pill, card, poly_mask, partial, densify, dashed,
                    ruler, arrow, st, en, vis, prog, back, eout, ease, FA, F9, W, H, SS, OW, OH, FPS,
                    TOTAL, LINE22, LINE25, CAPS, tr_up, font, flag_img)

SEA1, SEA2 = (178, 210, 232), (150, 188, 218)
LAND = (244, 238, 224)
BORDER = (196, 184, 160)
EGC = (243, 162, 84)       # Mısır
SDC = (138, 196, 150)      # Sudan
LYC = (186, 168, 220)      # Libya
SANDC = (232, 205, 148)
RED = (214, 40, 57)
DARK = (35, 35, 42)
WHITE = (255, 255, 255)
YEL = (255, 210, 63)
BLACK = (15, 15, 18)
SEA_TXT = (70, 110, 150)

def make_sea():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    c = np.array(SEA1) * (1 - y) + np.array(SEA2) * y
    return Image.fromarray(np.broadcast_to(c, (H, W, 3)).astype(np.uint8), "RGB")
SEA = make_sea()

def mix(a, b, f): return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

def fill(img, P, g, color, alpha):
    if alpha <= .01: return
    img.paste(color, (0, 0), poly_mask(P, g, fill=int(255 * alpha)))

def line(img, pts, color, width, alpha=1.):
    if alpha <= .01 or len(pts) < 2: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line(pts, fill=WHITE + (int(255*alpha),), width=int(width * 1.8), joint="curve")
    d.line(pts, fill=color + (int(255*alpha),), width=int(width), joint="curve")
    img.alpha_composite(lay)

def lab(img, P, text, lon, lat, size, alpha=1., scale=1., col=DARK, stroke=WHITE, rot=0):
    stamp_text(img, text, P.xy(lon, lat), FA, size, fill=col, stroke=stroke, alpha=alpha, scale=scale, rot=rot)

def caption(img, t):
    c = next((c for c in CAPS if c["start"] <= t < c["end"]), None)
    if not c: return
    pop = 0.88 + 0.12 * back((t - c["start"]) / 0.12)
    size = 74 * SS * pop; f = font(F9, size); sw = int(size / 7.5); sp = f.getlength(" ")
    words = [tr_up(w) for w in c["words"]]
    lines, cur = [], []
    for w in words:
        if cur and sum(f.getlength(x) for x in cur + [w]) + sp * len(cur) > W * 0.84:
            lines.append(cur); cur = []
        cur.append(w)
    lines.append(cur)
    widest = max(sum(f.getlength(x) for x in ln) + sp * (len(ln) - 1) for ln in lines)
    if widest > W * 0.9:
        size *= W * 0.9 / widest; f = font(F9, size); sw = int(size / 7.5); sp = f.getlength(" ")
    cur_i = max(i for i, wt in enumerate(c["wt"]) if wt <= t)
    lay = Image.new("RGBA", (W, int(size * 1.2 * len(lines) + size)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    idx = 0
    for li, ln in enumerate(lines):
        tw = sum(f.getlength(w) for w in ln) + sp * (len(ln) - 1); x = W/2 - tw/2; y = size * 0.7 + li * size * 1.2
        for w in ln:
            d.text((x, y), w, font=f, fill=YEL if idx == cur_i else WHITE, stroke_width=sw, stroke_fill=BLACK, anchor="lm")
            x += f.getlength(w) + sp; idx += 1
    img.alpha_composite(lay, (0, int(1460 * SS - (len(lines) - 1) * size * 0.6 - size * 0.7)))

def header(img, t):
    a = vis(t, 0.15, en("why") + 0.1, .3, .4)
    if a <= 0: return
    sc = 0.9 + 0.1 * back(prog(t, 0.15, .35))
    lay = Image.new("RGBA", (W, 260 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 860 * SS * sc, 180 * SS * sc; x0, y0 = W/2 - w/2, 130 * SS - h/2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(36 * SS), fill=(20, 20, 24, 235))
    d.text((W/2, y0 + h * 0.31), "MISIR'IN SINIRLARI", font=font(FA, 66 * SS * sc), fill=WHITE, anchor="mm")
    d.text((W/2, y0 + h * 0.71), "NEDEN DÜMDÜZ?", font=font(FA, 74 * SS * sc), fill=YEL, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, 150 * SS))

def frame(t):
    cam = camera(t); P = Proj(cam); V = P.view()
    img = SEA.copy(); d = ImageDraw.Draw(img)
    vis_c = [(n, g) for n, g in CN.items() if g.intersects(V)]
    for n, g in vis_c:
        for p in polys(g):
            pts = P.arr(p.exterior.coords)
            if len(pts) > 2: d.polygon(pts, fill=LAND)
    img = img.convert("RGBA")

    # ---- ülke renkleri (video boyunca sabit) ----
    desert = vis(t, st("desert"), st("zoom_bt") - .2, .6, .6)
    egA = eout(prog(t, 0.8, 1.0))
    fill(img, P, EG, mix(EGC, SANDC, desert), egA)
    sdA = eout(prog(t, st("south"), .7))
    fill(img, P, SD, mix(SDC, SANDC, desert), sdA)
    lyA = eout(prog(t, st("west"), .7))
    fill(img, P, LY, mix(LYC, SANDC, desert), lyA)

    d = ImageDraw.Draw(img)
    bw = max(2, int(2 * SS * min(1.5, cam[2] / 80)))
    for n, g in vis_c:
        for p in polys(g):
            d.line(P.arr(p.exterior.coords), fill=BORDER, width=bw, joint="curve")

    # ---- Nil ----
    a_nile = vis(t, st("nile"), st("zoom_bt"), .4, .5)
    if a_nile > 0:
        pn = eout(prog(t, st("nile"), 1.4))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.polygon(P.arr(DELTA.exterior.coords), fill=(120, 180, 90, int(220 * a_nile * pn)))
        main = P.arr(densify(NILE, 8))
        dl.line(partial(main, pn), fill=(120, 180, 90, int(200 * a_nile)), width=int(34 * SS), joint="curve")
        dl.line(partial(main, pn), fill=(40, 115, 210, int(255 * a_nile)), width=int(9 * SS), joint="curve")
        if pn > .9:
            for br in (ROSETTA, DAMIETTA):
                dl.line(P.arr(br), fill=(40, 115, 210, int(255 * a_nile)), width=int(7 * SS), joint="curve")
        img.alpha_composite(lay)

    # ---- düz çizgiler ----
    p22 = P.arr(densify(LINE22, 4)); p25 = P.arr(densify(LINE25, 4))
    lo0, la0, lo1, la1 = V.bounds
    lines_a = 1 - eout(prog(t, st("zoom_bt"), .6))
    f22 = ease(prog(t, st("ruler") + .05, 1.0)); f25 = ease(prog(t, st("ruler") + 1.1, 1.0))
    pul = lambda s, e: 1 + 0.45 * max(0, math.sin((t - st(s)) * 6)) if st(s) < t < en(e) else 1
    a_par = vis(t, st("south"), en("south_len"), .4, .4) * lines_a
    a_mer = vis(t, st("west"), en("west_line"), .4, .4) * lines_a
    if a_par > 0 or a_mer > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        if a_par > 0: dashed(dl, [P.xy(lo0, 22), P.xy(lo1, 22)], RED + (int(160 * a_par),), 3 * SS)
        if a_mer > 0: dashed(dl, [P.xy(25, la1), P.xy(25, la0)], RED + (int(160 * a_mer),), 3 * SS)
        img.alpha_composite(lay)
    if f22 > 0: line(img, partial(p22, f22), RED, 8 * SS * pul("south", "south_len"), lines_a)
    if f25 > 0: line(img, partial(p25, f25), RED, 8 * SS * pul("west", "west_line"), lines_a)
    ruler(img, p22[0], p22[-1], f22, 1, vis(t, st("ruler"), st("ruler") + 1.1, .2, .25))
    ruler(img, p25[0], p25[-1], f25, 1, vis(t, st("ruler") + 1.05, en("ruler") + .1, .2, .3))
    r3 = vis(t, st("ruler2") + .3, en("ruler2"), .2, .3)
    if r3 > 0: ruler(img, p25[-1], p25[0], ease(prog(t, st("ruler2") + .3, 2.4)), -1, r3)

    # uzunluk
    a_len = vis(t, st("south_len") + .1, en("south_len") + .3, .3, .3)
    if a_len > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        y = p22[0][1] - 60 * SS; x0, x1 = p22[0][0], p22[-1][0]; xm = (x0 + x1) / 2
        pe = eout(prog(t, st("south_len") + .1, .8)); c = DARK + (int(255 * a_len),)
        arrow(dl, (xm, y), (xm - (xm - x0) * pe, y), c, 5 * SS); arrow(dl, (xm, y), (xm + (x1 - xm) * pe, y), c, 5 * SS)
        img.alpha_composite(lay)
        pill(img, "1.276 KM", xm, y - 66 * SS, 54, bg=WHITE, alpha=a_len, scale=back(prog(t, st("south_len") + .3, .35)))

    # ---- yakın plan: 1902 / Halayib / Bir Tavil ----
    a_adm = vis(t, st("line1902"), TOTAL, .3, .3)
    if a_adm > 0:
        line(img, P.arr(densify([(31.2, 22.0), (36.87, 22.0)], 10)), RED, 6 * SS, a_adm * .9)
        pts = P.arr(densify(list(ADMIN.coords), 20))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dashed(ImageDraw.Draw(lay), partial(pts, eout(prog(t, st("line1902") + .2, 1.6))), DARK + (int(255 * a_adm),), 7 * SS, 22, 14)
        img.alpha_composite(lay)
    a_h = vis(t, st("halaib"), TOTAL, .4, .3)
    if a_h > 0:
        m = poly_mask(P, HALAIB, fill=int(255 * a_h))
        stripes = Image.new("RGB", (W, H), EGC); ds = ImageDraw.Draw(stripes)
        for k in range(-H, W + H, 64 * SS):
            ds.polygon([(k, 0), (k + 32 * SS, 0), (k + 32 * SS - H, H), (k - H, H)], fill=SDC)
        img.paste(stripes, (0, 0), m)
        line(img, P.arr(HALAIB.exterior.coords), DARK, 3 * SS, a_h)
    a_b = vis(t, st("birtawil"), TOTAL, .3, .3)
    if a_b > 0:
        pulse = 0.75 + 0.25 * math.sin(t * 5)
        fill(img, P, BIRTAWIL, WHITE, a_b * pulse)
        line(img, P.arr(BIRTAWIL.exterior.coords), DARK, 4 * SS, a_b)

    # ---- etiketler ----
    sc = max(.6, min(1.0, cam[2] / 86))
    names = vis(t, 0.9, st("zoom_bt") - .3, .4, .4)
    lab(img, P, "MISIR", 29.7, 26.4, 96 * sc, names, back(prog(t, 0.9, .5)))
    lab(img, P, "SUDAN", 32.6, 21.05, 74 * sc, names * eout(prog(t, st("south"), .5)))
    lab(img, P, "LİBYA", 23.0, 27.6, 74 * sc, names * eout(prog(t, st("west"), .5)))
    lab(img, P, "AKDENİZ", 28.5, 32.6, 44 * sc, names, col=SEA_TXT, stroke=SEA1)
    lab(img, P, "KIZILDENİZ", 36.0, 25.0, 40 * sc, names, col=SEA_TXT, stroke=SEA1, rot=-58)
    a = vis(t, st("south") + .2, en("south_len"), .3, .3)
    lab(img, P, "22. ENLEM", 27.3, 21.62, 54, a, back(prog(t, st("south") + .2, .4)), col=RED)
    a = vis(t, st("west") + .2, en("west_line"), .3, .3)
    lab(img, P, "25. BOYLAM", 24.55, 26.8, 54, a, back(prog(t, st("west") + .2, .4)), col=RED, rot=90)
    a = vis(t, st("desert") + .3, en("desert") + .2, .3, .4)
    lab(img, P, "ÇÖL", 28.0, 24.8, 110, a, back(prog(t, st("desert") + .3, .4)), col=(150, 105, 40))
    a = vis(t, st("nile") + .5, en("ruler2"), .3, .4)
    lab(img, P, "NİL", 33.3, 27.3, 64, a, back(prog(t, st("nile") + .5, .4)), col=(40, 115, 210))
    a = vis(t, st("nile") + 1.5, en("nile") + .3, .3, .3)
    px, py = P.xy(32.9, 29.4)
    pill(img, "NÜFUSUN %95'İ", px, py, 50, bg=WHITE, alpha=a, scale=back(prog(t, st("nile") + 1.5, .35)))
    zb = vis(t, st("zoom_bt") + .6, TOTAL, .4, .3)
    lab(img, P, "MISIR", 34.0, 22.9, 76, zb)
    lab(img, P, "SUDAN", 35.6, 21.5, 76, zb)
    a = vis(t, st("line1902") + .2, en("line1902") + .2, .25, .3)
    pill(img, "1902", W/2, 560 * SS, 72, bg=WHITE, alpha=a, scale=back(prog(t, st("line1902") + .2, .35)))
    a = vis(t, st("halaib") + .2, TOTAL, .3, .3)
    lab(img, P, "HALAYİB", 35.45, 22.42, 58, a, back(prog(t, st("halaib") + .2, .4)))
    lab(img, P, "İKİSİ DE İSTİYOR", 35.45, 22.2, 34, a * vis(t, st("halaib") + .2, st("cta"), .3, .3))
    a = vis(t, st("birtawil") + .1, TOTAL, .3, .3)
    lab(img, P, "BİR TAVİL", 33.62, 21.56, 58, a, back(prog(t, st("birtawil") + .1, .4)))
    lab(img, P, "KİMSE İSTEMİYOR", 33.62, 21.38, 34, a * vis(t, st("birtawil") + .1, st("cta"), .3, .3), col=RED)
    a = vis(t, st("why_bt") + .8, en("why_bt") + .2, .3, .3)
    pill(img, "10 KAT BÜYÜK + DENİZ KIYISI", W/2, 560 * SS, 44, bg=WHITE, alpha=a, scale=back(prog(t, st("why_bt") + .8, .35)))
    a = vis(t, st("nomans") + .4, st("cta") + .2, .2, .3)
    if a > 0:
        s = 1.6 - 0.6 * eout(prog(t, st("nomans") + .4, .25)); x, y = P.xy(33.62, 21.9)
        f = font(FA, 64 * SS * s); tw = f.getlength("SAHİPSİZ!")
        lay = Image.new("RGBA", (int(tw + 60 * SS * s), int(130 * SS * s)), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle((4, 4, lay.width - 5, lay.height - 5), radius=int(14 * SS), outline=RED + (int(255 * a),), width=int(8 * SS * s))
        dl.text((lay.width / 2, lay.height / 2), "SAHİPSİZ!", font=f, fill=RED + (int(255 * a),), anchor="mm")
        lay = lay.rotate(10, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2 - 150 * SS)))

    # kartlar / rozetler
    a = vis(t, st("colonial") + .5, en("colonial") + .1, .25, .3)
    card(img, "uk", W * .30, 640 * SS, 300, a, back(prog(t, st("colonial") + .5, .4)), "İNGİLTERE")
    a = vis(t, st("colonial") + .9, en("colonial") + .1, .25, .3)
    card(img, "italy", W * .70, 640 * SS, 300, a, back(prog(t, st("colonial") + .9, .4)), "İTALYA")
    for yr, kind, t0, t1 in (("1899", "uk", st("south") + .4, en("south_len")), ("1925", "italy", st("west") + .4, en("west_line"))):
        a = vis(t, t0, t1, .25, .3)
        if a > 0:
            s = back(prog(t, t0, .35))
            pill(img, yr, W/2 - 90 * SS, 560 * SS, 72, bg=WHITE, alpha=a, scale=s)
            card(img, kind, W/2 + 110 * SS, 560 * SS, 150, a, s)
    a = vis(t, st("why") - .05, en("why") + .2, .15, .25)
    stamp_text(img, "?", (W/2, 820 * SS), FA, 330, fill=YEL, alpha=a, scale=back(prog(t, st("why") - .05, .35)), rot=-8 * math.sin(t * 4))
    a = vis(t, st("cta") + .3, TOTAL, .3, .3)
    if a > 0:
        stamp_text(img, "?", P.xy(33.62, 22.45), FA, 200, fill=YEL, alpha=a, scale=back(prog(t, st("cta") + .3, .4)) * (1 + .05 * math.sin(t * 6)))
        a3 = vis(t, st("cta") + 1.2, TOTAL, .25, .3)
        pill(img, "YORUMLARA YAZ!", W/2, 600 * SS, 64, alpha=a3, scale=back(prog(t, st("cta") + 1.2, .35)))
        if a3 > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            cx, cy = W/2, 680 * SS + 12 * SS * math.sin(t * 7)
            dl.polygon([(cx - 30 * SS, cy), (cx + 30 * SS, cy), (cx, cy + 36 * SS)], fill=YEL + (int(255 * a3),), outline=BLACK + (255,))
            img.alpha_composite(lay)

    header(img, t)
    caption(img, t)
    fade = min(prog(t, 0, .3), 1 - prog(t, TOTAL - .5, .5))
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
        for tt in sys.argv[2:]: frame(float(tt)).save(f"s2_{float(tt):05.1f}.png")
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
