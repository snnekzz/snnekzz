"""Bilinmeyenin Peşinde – ortak marka öğeleri. Her videoda kullan:
    from brand import brand_card, watermark
    brand_card(img, t, "İNEBOLU'DAN ANKARA'YA", "BİR MERMİ KAÇ GÜNDE?", t_end)
    watermark(img, t, TOTAL)
Kanvas: 2160x3840 (SS=2) RGBA. Fontlar: anton.ttf, mont900.ttf, mont700.ttf çalışma klasöründe."""
import math
from PIL import Image, ImageDraw, ImageFont

SS = 2; W, H = 1080 * SS, 1920 * SS
RED = (227, 30, 45); YEL = (255, 210, 63); WHITE = (255, 255, 255)
HANDLE = "@BilinmeyeninPesinde"
_fc = {}
def _f(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, max(4, int(s)))
    return _fc[k]
def _clamp(x): return max(0.0, min(1.0, x))
def _back(x):
    x = _clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def _vis(t, t0, t1, fi=.35, fo=.4):
    if t < t0 or t > t1 + fo: return 0.
    return min(1 - (1 - _clamp((t - t0) / fi)) ** 3, 1 - _clamp((t - t1) / fo))

def brand_card(img, t, line1, line2, t_end, y_center=650):
    """Açılış başlık kartı: kırmızı BİLİNMEYENİN PEŞİNDE etiketi + beyaz/sarı iki satır başlık."""
    a = _vis(t, .2, t_end)
    if a <= 0: return
    sc = .9 + .1 * _back((t - .2) / .4)
    lay = Image.new("RGBA", (W, 360 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w, h = 900 * SS * sc, 230 * SS * sc; x0, y0 = W / 2 - w / 2, 180 * SS - h / 2
    d.rounded_rectangle((x0 + 10, y0 + 14, x0 + w + 10, y0 + h + 14), radius=int(38 * SS), fill=(0, 0, 0, 110))
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(38 * SS), fill=(14, 16, 22, 235))
    tf = _f("mont900.ttf", 26 * SS * sc); tw = tf.getlength("BİLİNMEYENİN PEŞİNDE")
    d.rounded_rectangle((W / 2 - tw / 2 - 20 * SS, y0 - 22 * SS, W / 2 + tw / 2 + 20 * SS, y0 + 22 * SS), radius=int(22 * SS), fill=RED)
    d.text((W / 2, y0), "BİLİNMEYENİN PEŞİNDE", font=tf, fill=WHITE, anchor="mm")
    for txt, yy, col, size in ((line1, .40, WHITE, 70), (line2, .76, YEL, 64)):
        f = _f("anton.ttf", size * SS * sc)
        if f.getlength(txt) > w * .92: f = _f("anton.ttf", size * SS * sc * w * .92 / f.getlength(txt))
        d.text((W / 2, y0 + h * yy), txt, font=f, fill=col, anchor="mm")
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay, (0, int((y_center - 180) * SS)))

import os
_ISARET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isaret.png")
_lc = {}
def _logo(size):
    """kanal işareti (konum iğnesi + anahtar deliği, kanal/logo/isaret.png). Yoksa eski çizim."""
    if os.path.exists(_ISARET):
        if size not in _lc:
            im = Image.open(_ISARET).convert("RGBA"); im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
            h = int(size * 1.25); _lc[size] = im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)
        return _lc[size]
    return _logo_eski(size)
def _logo_eski(size):
    s = size; im = Image.new("RGBA", (int(s * 1.3), int(s * 1.3)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = s * .42; cx = cy = s * .5
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(40, 110, 200, 255), outline=WHITE, width=max(2, int(s * .07)))
    d.arc((cx - r * .5, cy - r, cx + r * .5, cy + r), 0, 360, fill=(255, 255, 255, 160), width=max(1, int(s * .03)))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 255, 255, 160), width=max(1, int(s * .03)))
    d.line([(cx + r * .72, cy + r * .72), (cx + r * 1.45, cy + r * 1.45)], fill=WHITE, width=max(3, int(s * .13)))
    return im

# filigranın gezindiği güvenli noktalar (Shorts arayüzünün kapatmadığı yerler)
SPOTS = [(.50, .945), (.24, .62), (.76, .40), (.50, .945), (.74, .70), (.27, .36)]
def watermark(img, t, total, period=7.0, alpha=.50):
    """Gezinen filigran: logo + kanal adı; birkaç saniyede bir yumuşakça yer değiştirir."""
    k = int(t // period); u = (t % period) / period
    fade = min(_clamp(u / .08), _clamp((1 - u) / .08))            # geçişte yumuşak sön/yan
    fade *= _clamp(t / .6) * _clamp((total - t) / .4)
    if fade <= .01: return
    sx, sy = SPOTS[k % len(SPOTS)]
    f = _f("mont700.ttf", 26 * SS); tw = f.getlength(HANDLE); lg = _logo(30 * SS)
    lay = Image.new("RGBA", (int(tw + lg.width + 30 * SS), int(lg.height + 10 * SS)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lay.alpha_composite(lg, (0, 0))
    d.text((lg.width + 6 * SS, lay.height / 2), HANDLE, font=f, fill=WHITE, anchor="lm", stroke_width=3 * SS, stroke_fill=(0, 0, 0, 200))
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha * fade)))
    x = sx * W - lay.width / 2; y = sy * H - lay.height / 2
    img.alpha_composite(lay, (int(x), int(y)))

def stamp_metadata(mp4_in, mp4_out, title):
    """Dosya künyesine telif bilgisi (yeniden kodlama yok)."""
    import subprocess, datetime
    y = datetime.date.today().year
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4_in, "-c", "copy",
                    "-metadata", f"title={title}", "-metadata", "artist=Bilinmeyenin Peşinde",
                    "-metadata", f"copyright=© {y} Bilinmeyenin Peşinde – tüm hakları saklıdır",
                    "-metadata", f"comment=Orijinal içerik: YouTube {HANDLE}. İzinsiz kopyalanamaz.",
                    "-movflags", "+faststart", mp4_out], check=True)
