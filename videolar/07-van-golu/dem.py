"""AWS açık yükseklik karoları (terrarium) → yükseklik örnekleyici + uydu dokusuna rölyef gölgesi.
Kaynak: s3.amazonaws.com/elevation-tiles-prod (açık veri, Mapzen/Tilezen)."""
import math, os, io, subprocess
import numpy as np
from PIL import Image
from scipy import ndimage

def _tile_xy(lon, lat, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

class DEM:
    def __init__(self, lon0, lon1, lat0, lat1, z, cache):
        self.z = z
        x0, y0 = _tile_xy(lon0, lat1, z); x1, y1 = _tile_xy(lon1, lat0, z)
        self.tx0, self.ty0 = int(x0), int(y0); tx1, ty1 = int(x1), int(y1)
        os.makedirs(cache, exist_ok=True)
        rows = []
        for ty in range(self.ty0, ty1 + 1):
            row = []
            for tx in range(self.tx0, tx1 + 1):
                f = f"{cache}/{z}_{tx}_{ty}.png"
                if not os.path.exists(f):
                    subprocess.run(["curl", "-s", "-o", f, f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png"], check=True)
                a = np.asarray(Image.open(f).convert("RGB"), np.float32)
                row.append(a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768)
            rows.append(np.concatenate(row, 1))
        self.E = np.concatenate(rows, 0)

    def sample(self, LON, LAT):
        n = 2 ** self.z
        X = (LON + 180) / 360 * n * 256 - self.tx0 * 256
        lr = np.radians(LAT)
        Y = (1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / np.pi) / 2 * n * 256 - self.ty0 * 256
        return ndimage.map_coordinates(self.E, [Y, X], order=1, mode="nearest")

HYPSO = [(-100, (70, 120, 60)), (600, (92, 128, 62)), (1400, (138, 140, 86)), (2200, (150, 122, 88)),
         (3000, (130, 110, 96)), (3600, (205, 200, 195)), (4200, (250, 250, 252))]
def hypso(E):
    out = np.zeros(E.shape + (3,), np.float32)
    ks = [k for k, _ in HYPSO]; cs = np.array([c for _, c in HYPSO], np.float32)
    for ch in range(3): out[..., ch] = np.interp(E, ks, cs[:, ch])
    return out

def relief(img, dem, lon0, lon1, lat0, lat1, ll2m_fn, exag=2.0, tint=.35):
    """img: build_tex çıktısı (aynı sınırlar). Döndürür: rölyef gölgeli + yükseklik renkli doku."""
    w, h = img.size
    x0, y0 = ll2m_fn(lon0, lat0); x1, y1 = ll2m_fn(lon1, lat1); mpp = (x1 - x0) / w
    xs = np.linspace(x0, x1, w); ys = np.linspace(y1, y0, h)
    X, Y = np.meshgrid(xs, ys)
    # ters dönüşüm: yerel metrik → lon/lat (ll2m doğrusal)
    ax = (ll2m_fn(lon0 + 1, lat0)[0] - x0); ay = (ll2m_fn(lon0, lat0 + 1)[1] - y0)
    LON = lon0 + (X - x0) / ax; LAT = lat0 + (Y - y0) / ay
    E = dem.sample(LON, LAT).astype(np.float32)
    land = E > 5
    gy, gx = np.gradient(ndimage.gaussian_filter(E, 0.8) * exag, mpp)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(42)
    shade = np.cos(math.pi / 2 - alt) * np.cos(slope) + np.sin(math.pi / 2 - alt) * np.sin(slope) * np.cos(az - aspect)
    shade = np.clip(shade, 0, 1)
    base = np.asarray(img, np.float32)
    col = base * (1 - tint) + hypso(E) * tint
    lit = col * (0.42 + 0.85 * shade[..., None])
    out = np.where(land[..., None], lit, base)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), E
