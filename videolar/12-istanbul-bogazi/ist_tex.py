"""İstanbul Boğazı dokusu: AWS terrarium (z12) yükseklik + deniz derinliği → kara rölyef, deniz derinlik rengi.
Kıyı çizgisi doğrudan veriden (E>0) – Natural Earth Boğaz için çok kaba."""
import math, os, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
import dem as DM
B = (28.55, 29.75, 40.78, 41.78)          # lon0, lon1, lat0, lat1
LON0, LAT0D = 30.0, 39.0
KX = 111320 * math.cos(math.radians(LAT0D)); KY = 111320.0
def ll2m(lon, lat): return ((lon - LON0) * KX, (lat - LAT0D) * KY)
def build(npx=3072, fname="ist_tex.png"):
    if os.path.exists(fname): return Image.open(fname).convert("RGB"), np.load("ist_E.npy")
    lon0, lon1, lat0, lat1 = B
    x0, y0 = ll2m(lon0, lat0); x1, y1 = ll2m(lon1, lat1); mpp = (x1 - x0) / npx; hpx = int((y1 - y0) / mpp)
    X, Y = np.meshgrid(np.linspace(x0, x1, npx), np.linspace(y1, y0, hpx))
    LON = LON0 + X / KX; LAT = LAT0D + Y / KY
    d = DM.DEM(lon0, lon1, lat0, lat1, 12, "../geo/dem")
    E = d.sample(LON, LAT).astype(np.float32)
    land = ndimage.binary_opening(E > 0.5, iterations=1)
    # kara: alçak yeşil-zeytin, yükseldikçe açık; rölyef gölgesi
    Es = ndimage.gaussian_filter(np.maximum(E, 0), 1.0)
    gy, gx = np.gradient(Es * 2.2, mpp)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy); az, alt = math.radians(315), math.radians(40)
    shade = np.clip(np.cos(math.pi / 2 - alt) * np.cos(slope) + np.sin(math.pi / 2 - alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    ks = [0, 60, 150, 300, 500]; cs = np.array([(150, 160, 112), (128, 150, 92), (112, 138, 80), (140, 140, 100), (165, 160, 130)], np.float32)
    lc = np.stack([np.interp(Es, ks, cs[:, c]) for c in range(3)], -1)
    pass
    rng = np.random.default_rng(7); n = ndimage.gaussian_filter(rng.standard_normal(E.shape).astype(np.float32), 6); n /= n.std() + 1e-6
    lc *= (0.95 + 0.05 * n[..., None]); lc = lc * (0.55 + 0.75 * shade[..., None])
    # deniz: sığ turkuaz → derin lacivert
    # bu bölgede batimetri yok (E≈sabit) → kıyıdan uzaklığa göre temsilî derinlik
    dist = ndimage.distance_transform_edt(~land) * mpp / 1000.0          # km
    dep = np.clip(dist * 9.0, 0, 400) + 1.5 * n
    sk = [0, 15, 60, 120, 400]; sc = np.array([(92, 178, 205), (60, 150, 196), (34, 104, 168), (24, 80, 148), (14, 52, 112)], np.float32)
    oc = np.stack([np.interp(dep, sk, sc[:, c]) for c in range(3)], -1)
    coast = ndimage.gaussian_filter(land.astype(np.float32), 2.0)
    oc = oc * (1 - .25 * coast[..., None]) + np.array([150, 215, 230], np.float32) * .25 * coast[..., None]
    out = np.where(land[..., None], lc, oc)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); img.save(fname); np.save("ist_E.npy", E)
    return img, E
if __name__ == "__main__":
    img, E = build(); print(img.size, E.min(), E.max())
    img.resize((img.width // 4, img.height // 4)).save("/tmp/is/ist_prev.jpg")
