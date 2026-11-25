"""Ağrı Dağı kapakları (dikey 1080x1920 + yatay 1280x720). Arka plan: render10 soru sahnesi (altyazısız)."""
import render10 as M
from PIL import Image, ImageDraw, ImageFont, ImageFilter
M.caption_top = lambda *a: None; M.brand.watermark = lambda *a, **k: None; M.ui = lambda *a: None
OUT = "/home/user/snnekzz/videolar/08-agri-dagi/"
bg = M.frame(M.cue("question", "nasıl", "dağ") + .6).convert("RGBA")
YEL, WHITE, RED, BLACK = (255, 214, 0), (255, 255, 255), (229, 36, 59), (0, 0, 0)
def text(img, s, cx, cy, size, fill, sw, rot=0, font="anton.ttf"):
    f = ImageFont.truetype(font, int(size)); l, t, r, b = f.getbbox(s, stroke_width=sw)
    lay = Image.new("RGBA", (r - l + 60, b - t + 60), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((30 - l, 30 - t), s, font=f, fill=fill, stroke_width=sw, stroke_fill=BLACK)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * .6)))
    x, y = int(cx - lay.width / 2), int(cy - lay.height / 2)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * .06)), (x + int(size * .04), y + int(size * .06))); img.alpha_composite(lay, (x, y))
def pillx(img, s, cx, cy, size, bg_, fg):
    f = ImageFont.truetype("mont900.ttf", size); l, t, r, b = f.getbbox(s); w, h = r - l + size * 1.1, b - t + size * .75
    d = ImageDraw.Draw(img); d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=bg_, outline=BLACK, width=max(2, int(size * .08)))
    d.text((cx, cy), s, font=f, fill=fg, anchor="mm")
v = bg.copy()
top = Image.new("RGBA", v.size, (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
for y in range(0, 700): dt.line([(0, y), (1080, y)], fill=(0, 0, 0, int(190 * (1 - y / 700) ** 1.4)))
v.alpha_composite(top)
pillx(v, "AĞRI DAĞI · 1932", 540, 120, 34, RED, WHITE)
text(v, "BU DAĞ NASIL TÜRKİYE'NİN OLDU?", 540, 250, 62, WHITE, 5)
text(v, "TOPRAK TAKASI!", 540, 420, 150, YEL, 11, rot=-3)
text(v, "yamaçları İran'daydı", 540, 1560, 100, YEL, 4, rot=-6, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
# yatay: dikey sahneden orta kesit + sağda yazı
hz = Image.new("RGBA", (1280, 720), (8, 14, 26, 255))
crop = bg.crop((0, 640, 1080, 1720)).resize((720, 720), Image.LANCZOS); hz.paste(crop, (0, 0))
g = Image.linear_gradient("L").rotate(90).resize((300, 720)); hz.paste((8, 14, 26), (420, 0, 720, 720), g)
text(hz, "İKİ ÜLKE,", 975, 210, 120, WHITE, 7); text(hz, "BİR DAĞ!", 975, 380, 150, YEL, 8, rot=-3)
pillx(hz, "AĞRI DAĞI · 1932", 975, 560, 32, RED, WHITE)
hz.convert("RGB").save(OUT + "kapak-yatay.jpg", quality=93)
print("ok")
