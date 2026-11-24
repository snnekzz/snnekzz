import math
from PIL import Image, ImageDraw, ImageFont
S = 1600   # 2x, sonra 800'e küçült
SEA = (120, 170, 210); SEA_D = (40, 80, 130); LAND = (244, 238, 224)
EGC = (243, 162, 84); RED = (214, 40, 57); YEL = (255, 210, 63); DARK = (25, 30, 40); WHITE = (255, 255, 255)
FA = "anton.ttf"
OUT = "/home/user/snnekzz/videolar/kanal/"

def save(im, name):
    im.resize((800, 800), Image.LANCZOS).save(OUT + name)

# 1) MERİDYEN: küre + kırmızı meridyen
im = Image.new("RGB", (S, S), SEA_D); d = ImageDraw.Draw(im)
c, r = S/2, S*0.36
d.ellipse((c-r, c-r, c+r, c+r), fill=SEA)
# kara parçaları (soyut)
for poly in [[(-.55,-.55),(-.1,-.7),(.15,-.45),(.05,-.15),(-.35,-.05),(-.6,-.25)],
             [(.05,-.05),(.45,-.2),(.62,.15),(.35,.55),(.05,.4),(-.05,.15)],
             [(-.62,.2),(-.3,.15),(-.2,.45),(-.45,.62)]]:
    d.polygon([(c+x*r, c+y*r) for x, y in poly], fill=LAND)
d.polygon([(c+.05*r, c-.05*r), (c+.33*r, c-.13*r), (c+.33*r, c+.25*r), (c+.05*r, c+.25*r)], fill=EGC)
for k in (-.5, .5):
    w = r*abs(k)*1.0
    d.ellipse((c-w, c-r, c+w, c+r), outline=WHITE, width=10)
for y in (-.5, 0, .5):
    hw = r*math.sqrt(1-y*y)
    d.line([(c-hw, c+y*r), (c+hw, c+y*r)], fill=WHITE, width=10)
d.line([(c, c-r-60), (c, c+r+60)], fill=WHITE, width=58)
d.line([(c, c-r-60), (c, c+r+60)], fill=RED, width=34)
d.ellipse((c-r, c-r, c+r, c+r), outline=WHITE, width=22)
save(im, "profil-meridyen.png")

# 2) NEDEN HARİTA: katlanmış harita + soru işareti
im = Image.new("RGB", (S, S), SEA_D); d = ImageDraw.Draw(im)
x0, y0, w, h = S*0.2, S*0.3, S*0.6, S*0.42
pw = w/3
for i in range(3):
    dy = -40 if i % 2 == 0 else 40
    col = LAND if i != 1 else (230, 222, 205)
    d.polygon([(x0+i*pw, y0+(0 if i%2==0 else 40)), (x0+(i+1)*pw, y0+(40 if i%2==0 else 0)),
               (x0+(i+1)*pw, y0+h+(40 if i%2==0 else 0)), (x0+i*pw, y0+h+(0 if i%2==0 else 40))], fill=col)
# haritada turuncu ülke + kırmızı düz sınır
d.polygon([(x0+pw*0.7, y0+h*0.25), (x0+pw*1.9, y0+h*0.25+20), (x0+pw*2.1, y0+h*0.7), (x0+pw*0.7, y0+h*0.72)], fill=EGC)
d.line([(x0+pw*0.7, y0+h*0.72), (x0+pw*2.2, y0+h*0.72)], fill=RED, width=22)
d.line([(x0+pw*0.7, y0+h*0.22), (x0+pw*0.7, y0+h*0.75)], fill=RED, width=22)
f = ImageFont.truetype(FA, 760)
d.text((S*0.66, S*0.36), "?", font=f, fill=YEL, anchor="mm", stroke_width=34, stroke_fill=DARK)
save(im, "profil-nedenharita.png")

# 3) SINIR HİKÂYELERİ: cetvel ile çizilen kırmızı sınır
im = Image.new("RGB", (S, S), (245, 240, 228)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, S, S*0.5), fill=EGC)
d.rectangle((0, S*0.5, S, S), fill=(138, 196, 150))
d.line([(0, S*0.5), (S, S*0.5)], fill=WHITE, width=70)
d.line([(0, S*0.5), (S, S*0.5)], fill=RED, width=40)
rx, ry, rl, rw = S*0.12, S*0.53, S*0.76, S*0.13
d.rounded_rectangle((rx, ry, rx+rl, ry+rw), radius=20, fill=YEL, outline=DARK, width=12)
for k in range(31):
    x = rx + 30 + k*(rl-60)/30; tl = rw*(0.55 if k % 5 == 0 else 0.3)
    d.line([(x, ry), (x, ry+tl)], fill=DARK, width=8)
f = ImageFont.truetype(FA, 330)
d.text((S/2, S*0.27), "SINIR", font=f, fill=WHITE, anchor="mm", stroke_width=16, stroke_fill=DARK)
d.text((S/2, S*0.82), "HİKÂYELERİ", font=ImageFont.truetype(FA, 200), fill=WHITE, anchor="mm", stroke_width=12, stroke_fill=DARK)
save(im, "profil-sinirhikayeleri.png")

# Önizleme: yuvarlak kırpılmış (YouTube'da görüneceği gibi)
names = ["profil-meridyen.png", "profil-nedenharita.png", "profil-sinirhikayeleri.png"]
labels = ["MERİDYEN\n@Meridyen", "NEDEN HARİTA\n@NedenHarita", "SINIR HİKÂYELERİ\n@SinirHikayeleri"]
pv = Image.new("RGB", (1500, 640), (250, 250, 250)); dp = ImageDraw.Draw(pv)
for i, (n, l) in enumerate(zip(names, labels)):
    a = Image.open(OUT + n).resize((400, 400), Image.LANCZOS)
    m = Image.new("L", (400, 400), 0); ImageDraw.Draw(m).ellipse((0, 0, 399, 399), fill=255)
    pv.paste(a, (50 + i*500, 50), m)
    small = a.resize((88, 88)); ms = m.resize((88, 88))
    pv.paste(small, (206 + i*500, 470), ms)
    dp.multiline_text((250 + i*500, 590), l, font=ImageFont.truetype("mont700.ttf", 28), fill=DARK, anchor="mm", align="center")
pv.save(OUT + "onizleme.png")
print("ok")
