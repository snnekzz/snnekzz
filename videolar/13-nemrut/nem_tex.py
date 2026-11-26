"""Nemrut kalderası dokusu: AWS terrarium z13 yükseklik → volkanik rölyef; göller veriden (düz yüzey + rakım):
ana krater gölü ~2248 m, Ilıgöl ~2253 m, Van Gölü ~1648 m."""
import math, os, numpy as np
from PIL import Image
from scipy import ndimage
import dem as DM
B = (41.95, 42.50, 38.48, 38.80)
LON0, LAT0D = 30.0, 39.0
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def comp_at(mask, lon, lat, LON, LAT):
    lab, n = ndimage.label(mask)
    iy, ix = np.unravel_index(np.argmin((LON - lon) ** 2 + (LAT - lat) ** 2), LON.shape)
    k = lab[iy, ix]
    if k == 0:   # en yakın bileşen
        d = ndimage.distance_transform_edt(lab == 0, return_indices=True)[1]; k = lab[d[0][iy, ix], d[1][iy, ix]]
    return lab == k
BV = (40.90, 44.30, 37.55, 39.75)          # Van bölgesi (geniş görünümler)
def build(npx=3072, fname="nem_tex.png", b=None, z=13):
    b = b or B; mname = fname.replace(".png", "_masks.npz")
    if os.path.exists(fname): return Image.open(fname).convert("RGB"), np.load(mname)
    lon0, lon1, lat0, lat1 = b
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1); mpp = (x1 - x0) / npx; hpx = int((y1 - y0) / mpp)
    X, Y = np.meshgrid(np.linspace(x0, x1, npx), np.linspace(y1, y0, hpx))
    LON = LON0 + X / KX; LAT = LAT0D + Y / KY
    E = DM.DEM(lon0, lon1, lat0, lat1, z, "../geo/dem").sample(LON, LAT).astype(np.float32)
    g = np.hypot(*np.gradient(E))
    flat = ndimage.binary_opening(g < 0.12, iterations=2)
    main = comp_at(flat & (E > 2243) & (E < 2252), 42.215, 38.625, LON, LAT)
    ili = comp_at(flat & (E > 2249) & (E < 2258), 42.246, 38.643, LON, LAT)
    ili = ndimage.binary_dilation(ili, iterations=2) & ~main
    if b != B:                                # geniş doku: Ilıgöl seçilemez; ana göl makul boyutta değilse yok say
        ili = np.zeros_like(ili)
        if main.sum() > 0.005 * main.size: main = np.zeros_like(main)
    van = flat & (E > 1640) & (E < 1655); van = ndimage.binary_opening(van, iterations=3)
    lab, n = ndimage.label(van); sz = ndimage.sum(van, lab, range(1, n + 1)); van = np.isin(lab, 1 + np.where(sz > 0.02 * van.sum())[0])
    Es = ndimage.gaussian_filter(E, 2.2)
    gy, gx = np.gradient(Es * 1.6, mpp)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy); az, alt = math.radians(315), math.radians(38)
    shade = np.clip(np.cos(math.pi / 2 - alt) * np.cos(slope) + np.sin(math.pi / 2 - alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    ks = [1600, 1900, 2200, 2500, 2800, 3000]
    cs = np.array([(150, 150, 98), (142, 136, 92), (138, 118, 88), (122, 102, 84), (96, 86, 82), (110, 104, 100)], np.float32)
    lc = np.stack([np.interp(Es, ks, cs[:, c]) for c in range(3)], -1)
    rng = np.random.default_rng(5); n_ = ndimage.gaussian_filter(rng.standard_normal(E.shape).astype(np.float32), 4); n_ /= n_.std() + 1e-6
    lc *= (0.95 + 0.05 * n_[..., None]); lc = lc * (0.5 + 0.8 * shade[..., None])
    out = lc.copy()
    def paint(mask, deep, edge):
        dist = ndimage.distance_transform_edt(mask) * mpp
        u = np.clip(dist / (400 if mpp < 40 else 1500), 0, 1)[..., None]
        col = np.array(edge, np.float32) * (1 - u) + np.array(deep, np.float32) * u
        out[mask] = col[mask]
    paint(van, (24, 78, 140), (70, 150, 180)); paint(main, (20, 60, 130), (60, 140, 190)); paint(ili, (60, 160, 150), (120, 200, 170))
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); img.save(fname)
    np.savez_compressed(mname, main=main, ili=ili, van=van)
    return img, np.load(mname)
if __name__ == "__main__":
    img, m = build(); print(img.size, m["main"].sum(), m["ili"].sum(), m["van"].sum())
    img.resize((img.width // 3, img.height // 3)).save("/tmp/is/nem_tex_prev.jpg")
    img, m = build(3072, "vanr_tex.png", BV, 10); print(img.size, m["van"].sum())
    img.resize((img.width // 3, img.height // 3)).save("/tmp/is/vanr_tex_prev.jpg")
