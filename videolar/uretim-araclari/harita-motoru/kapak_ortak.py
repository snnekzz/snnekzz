"""Ortak kapak yardımcıları (kapak8.py ile aynı stil)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
YEL, WHITE, RED, BLACK, CYAN = (255, 214, 0), (255, 255, 255), (229, 36, 59), (0, 0, 0), (60, 210, 255)
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
def top_shade(v, h=700, k=190):
    top = Image.new("RGBA", v.size, (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
    for y in range(0, h): dt.line([(0, y), (v.width, y)], fill=(0, 0, 0, int(k * (1 - y / h) ** 1.4)))
    v.alpha_composite(top)
def bottom_shade(v, h=500, k=170):
    lay = Image.new("RGBA", v.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(h): d.line([(0, v.height - 1 - y), (v.width, v.height - 1 - y)], fill=(0, 0, 0, int(k * (1 - y / h) ** 1.4)))
    v.alpha_composite(lay)
def mute(M):
    M.caption_top = lambda *a: None; M.brand.watermark = lambda *a, **k: None; M.ui = lambda *a: None
def yatay(bg, crop_y0, l1, l2, pill, pill_bg, out, l2col=YEL, s1=110, s2=140):
    hz = Image.new("RGBA", (1280, 720), (8, 14, 26, 255))
    crop = bg.crop((0, crop_y0, 1080, crop_y0 + 1080)).resize((720, 720), Image.LANCZOS); hz.paste(crop, (0, 0))
    g = Image.linear_gradient("L").rotate(90).resize((300, 720)); hz.paste((8, 14, 26), (420, 0, 720, 720), g)
    text(hz, l1, 975, 210, s1, WHITE, 7); text(hz, l2, 975, 380, s2, l2col, 8, rot=-3)
    pillx(hz, pill, 975, 560, 30, pill_bg, WHITE)
    hz.convert("RGB").save(out, quality=93)
