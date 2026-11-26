"""Bilinmeyenin Peşinde – profesyonel logo sistemi (vektör).
İşaret: KONUM İĞNESİ + ANAHTAR DELİĞİ (harita + sır). Anahtar deliğinden altın bir ışık sızar.
Çıktılar: logo.svg + isaret.svg (vektör), profil-fotografi.png (1600 px, yuvarlak), isaret.png (filigran),
          youtube-banner.png (2560x1440), kimlik-sayfasi.png
Çalıştırma: python3 logo_pro.py   (Playwright/Chromium ile render eder)"""
import math, os, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))

# --- geometri (viewBox 1000) ---
CX, CY, R, TIP = 500, 440, 205, 800
d = TIP - CY; a = math.asin(R / d); th = math.pi / 2 - a
LX, RX, TY = CX - R * math.sin(th), CX + R * math.sin(th), CY + R * math.cos(th)
PIN = f"M {CX} {TIP} L {LX:.1f} {TY:.1f} A {R} {R} 0 1 1 {RX:.1f} {TY:.1f} Z"
KC, KR = (CX, CY - 22), 66
SLOT = f"M {CX-26} {CY+20} L {CX+26} {CY+20} L {CX+46} {CY+150} L {CX-46} {CY+150} Z"
def sparkle(cx, cy, s, k=.16):
    i = s * k
    return (f"M {cx} {cy-s} C {cx+i} {cy-i} {cx+i} {cy-i} {cx+s} {cy} C {cx+i} {cy+i} {cx+i} {cy+i} {cx} {cy+s} "
            f"C {cx-i} {cy+i} {cx-i} {cy+i} {cx-s} {cy} C {cx-i} {cy-i} {cx-i} {cy-i} {cx} {cy-s} Z")

THEMES = {
    # ad: (zemin iç, zemin dış, iğne üst, iğne alt, ışık, halka rengi, halka opaklık)
    "gece":   ("#1B2A4A", "#060A14", "#FF4A5C", "#C3102C", "#FFC94A", "#FFFFFF", .055),
}

def svg(theme, size=1000, bg=True):
    b0, b1, p0, p1, li, rc, ro = THEMES[theme]
    rings = "".join(f'<circle cx="500" cy="500" r="{r}" fill="none" stroke="{rc}" stroke-opacity="{ro*(1.25 - i*.22):.3f}" stroke-width="2"/>'
                    for i, r in enumerate((250, 330, 410)))
    ticks = "".join(f'<line x1="{500+math.cos(t)*402:.1f}" y1="{500+math.sin(t)*402:.1f}" x2="{500+math.cos(t)*418:.1f}" y2="{500+math.sin(t)*418:.1f}" stroke="{rc}" stroke-opacity="{ro*2.2:.3f}" stroke-width="3"/>'
                    for t in [k * math.pi / 12 for k in range(24)])
    cross = (f'<line x1="500" y1="70" x2="500" y2="150" stroke="{rc}" stroke-opacity="{ro*2.5:.3f}" stroke-width="2"/>'
             f'<line x1="500" y1="850" x2="500" y2="930" stroke="{rc}" stroke-opacity="{ro*2.5:.3f}" stroke-width="2"/>'
             f'<line x1="70" y1="500" x2="150" y2="500" stroke="{rc}" stroke-opacity="{ro*2.5:.3f}" stroke-width="2"/>'
             f'<line x1="850" y1="500" x2="930" y2="500" stroke="{rc}" stroke-opacity="{ro*2.5:.3f}" stroke-width="2"/>')
    back = f'''<rect width="1000" height="1000" fill="url(#bg)"/>
  <g>{rings}{ticks}{cross}</g>
  <circle cx="500" cy="440" r="330" fill="url(#halo)"/>
  <rect width="1000" height="1000" filter="url(#grain)" opacity=".07"/>''' if bg else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="{size}" height="{size}">
<defs>
  <radialGradient id="bg" cx="50%" cy="42%" r="70%"><stop offset="0" stop-color="{b0}"/><stop offset="1" stop-color="{b1}"/></radialGradient>
  <radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{p0}" stop-opacity=".22"/><stop offset="1" stop-color="{p0}" stop-opacity="0"/></radialGradient>
  <linearGradient id="pin" x1="0.2" y1="0" x2="0.8" y2="1"><stop offset="0" stop-color="{p0}"/><stop offset="1" stop-color="{p1}"/></linearGradient>
  <radialGradient id="light" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{li}" stop-opacity=".95"/><stop offset=".45" stop-color="{li}" stop-opacity=".35"/><stop offset="1" stop-color="{li}" stop-opacity="0"/></radialGradient>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
  <filter id="drop" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000" flood-opacity=".38"/></filter>
  <mask id="key"><rect width="1000" height="1000" fill="#fff"/>
    <circle cx="{KC[0]}" cy="{KC[1]}" r="{KR}" fill="#000"/>
    <path d="{SLOT}" fill="#000" stroke="#000" stroke-width="14" stroke-linejoin="round"/></mask>
  <clipPath id="keyclip"><circle cx="{KC[0]}" cy="{KC[1]}" r="{KR}"/><path d="{SLOT}"/></clipPath>
</defs>
{back}
  <g transform="translate(500 520) scale(1.1) translate(-500 -520)">
  <ellipse cx="500" cy="842" rx="92" ry="15" fill="#000" opacity=".35" filter="url(#soft)"/>
  <g filter="url(#drop)">
    <path d="{PIN}" fill="url(#pin)" stroke="url(#pin)" stroke-width="10" stroke-linejoin="round" mask="url(#key)"/>
  </g>
  <path d="M {CX-R+38} {CY-40} A {R-38} {R-38} 0 0 1 {CX-40} {CY-R+38}" fill="none" stroke="#fff" stroke-opacity=".32" stroke-width="9" stroke-linecap="round"/>
  <g clip-path="url(#keyclip)"><circle cx="{KC[0]}" cy="{KC[1]+30}" r="150" fill="url(#light)"/></g>
  <circle cx="{KC[0]}" cy="{KC[1]}" r="120" fill="url(#light)" opacity=".35"/>
  <path d="{sparkle(KC[0], KC[1], 40)}" fill="{li}"/>
  <path d="{sparkle(KC[0], KC[1], 40)}" fill="#fff" opacity=".55" transform="translate({KC[0]} {KC[1]}) scale(.45) translate({-KC[0]} {-KC[1]})"/>
  </g>
</svg>'''


open(f"{HERE}/logo.svg", "w").write(svg("gece"))
open(f"{HERE}/isaret.svg", "w").write(svg("gece", bg=False))

import re, itertools
_uid = itertools.count()
def uniq(x):   # aynı sayfada birden çok SVG: id çakışmasın
    n = next(_uid); return re.sub(r'(id="|url\(#)(\w+)', lambda m: f"{m.group(1)}{m.group(2)}{n}", x)
FONT = f"""@font-face{{font-family:M9;src:url(file://{HERE}/mont900.ttf)}}@font-face{{font-family:M7;src:url(file://{HERE}/mont700.ttf)}}"""
def page(body, w, h, css=""):
    return f"<html><head><style>{FONT}*{{margin:0;padding:0;box-sizing:border-box}}html,body{{background:transparent}}body{{width:{w}px;height:{h}px;overflow:hidden}}{css}</style></head><body>{body}</body></html>"
def circ(s): return f'<div style="width:{s}px;height:{s}px;border-radius:50%;overflow:hidden;flex:none">{uniq(svg("gece", s))}</div>'
jobs = []
def job(name, html, w, h, transparent=False):
    p = f"{HERE}/_{name}.html"; open(p, "w").write(page(html, w, h)); jobs.append((p, f"{HERE}/{name}.png", w, h, transparent))

job("profil-fotografi", svg("gece", 1600), 1600, 1600)
job("isaret", uniq(svg("gece", 512, bg=False)), 512, 512, True)

# --- YouTube banner 2560x1440 (güvenli alan: x 507–2053, y 508–931; her şey bunun içinde) ---
grid = "".join(f'<circle cx="685" cy="720" r="{r}" fill="none" stroke="#fff" stroke-opacity="{.07 - i*.008:.3f}" stroke-width="2"/>' for i, r in enumerate(range(260, 1500, 150)))
grid += "".join(f'<line x1="{685+math.cos(t)*300:.0f}" y1="{720+math.sin(t)*300:.0f}" x2="{685+math.cos(t)*2600:.0f}" y2="{720+math.sin(t)*2600:.0f}" stroke="#fff" stroke-opacity=".035" stroke-width="2"/>' for t in [k * math.pi / 8 for k in range(16)])
dots = "".join(f'<circle cx="{(k*397)%2560}" cy="{(k*233)%1440}" r="{1+(k%3)*.8}" fill="#fff" opacity="{.15+(k%5)*.08:.2f}"/>' for k in range(160))
banner = f"""<div style="position:relative;width:2560px;height:1440px;background:radial-gradient(ellipse at 27% 50%,#1B2A4A 0%,#0A1222 45%,#05080F 100%);font-family:M7;color:#fff">
<svg width="2560" height="1440" style="position:absolute;inset:0"><defs><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="2"/><feColorMatrix type="saturate" values="0"/></filter>
<radialGradient id="h" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#E5243B" stop-opacity=".28"/><stop offset="1" stop-color="#E5243B" stop-opacity="0"/></radialGradient></defs>
{grid}{dots}<circle cx="685" cy="720" r="420" fill="url(#h)"/><rect width="2560" height="1440" filter="url(#g)" opacity=".06"/></svg>
<div style="position:absolute;left:520px;top:555px;width:330px;height:330px">{uniq(svg("gece", 330, bg=False))}</div>
<div style="position:absolute;left:870px;top:578px">
  <div style="font-family:M7;font-size:26px;letter-spacing:9px;color:#FFC94A">HARİTA · TARİH · GİZEM</div>
  <div style="font-family:M9;font-size:84px;line-height:1;margin-top:14px;white-space:nowrap">BİLİNMEYENİN <span style="color:#E5243B">PEŞİNDE</span></div>
  <div style="font-size:31px;color:#AEB7C9;margin-top:22px">Tarihin, haritaların ve dünyanın bilinmeyen hikâyeleri</div>
  <div style="display:inline-block;margin-top:26px;padding:10px 26px;border-radius:40px;background:#E5243B;font-family:M9;font-size:26px;letter-spacing:2px">HER HAFTA YENİ SHORTS</div>
</div></div>"""
job("youtube-banner", banner, 2560, 1440)

# --- kimlik sayfası ---
sw = [("#0A1222", "Gece Mavisi"), ("#E5243B", "Keşif Kırmızısı"), ("#FFC94A", "Bilinmeyen Altını"), ("#FBF7F0", "Parşömen")]
body = f"""
<div style="display:flex;height:100%;background:#0A1222;color:#fff;font-family:M7">
  <div style="width:1000px;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 45%,#1B2A4A,#060A14)">{circ(720)}</div>
  <div style="flex:1;padding:110px 90px 0 70px">
    <div style="font-size:22px;letter-spacing:8px;color:#FFC94A">MARKA KİMLİĞİ · 2026</div>
    <div style="font-family:M9;font-size:92px;line-height:.98;margin-top:34px;letter-spacing:1px">BİLİNMEYENİN<br><span style="color:#E5243B">PEŞİNDE</span></div>
    <div style="font-size:26px;color:#AEB7C9;margin-top:26px;line-height:1.45">Tarihin, haritaların ve dünyanın<br>bilinmeyen hikâyeleri.</div>
    <div style="height:2px;background:#ffffff1a;margin:56px 0 40px"></div>
    <div style="font-size:18px;letter-spacing:5px;color:#7F8AA3">İŞARET · Konum iğnesi + anahtar deliği: haritadaki sır</div>
    <div style="display:flex;gap:30px;margin-top:34px;align-items:flex-end">{circ(170)}{circ(110)}{circ(70)}{circ(44)}{circ(28)}</div>
    <div style="display:flex;gap:22px;margin-top:56px">
      {"".join(f'<div><div style="width:150px;height:84px;border-radius:14px;background:{c};border:1px solid #ffffff22"></div><div style="font-size:17px;margin-top:12px">{n}</div><div style="font-size:15px;color:#7F8AA3;margin-top:4px">{c}</div></div>' for c, n in sw)}
    </div>
  </div>
</div>"""
job("kimlik-sayfasi", body, 1920, 1080)

js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();
for(const [f,o,w,h,tr] of {json.dumps(jobs)}){{const p=await b.newPage({{viewport:{{width:w,height:h}},deviceScaleFactor:1}});
await p.goto('file://'+f);await p.waitForTimeout(400);await p.screenshot({{path:o,omitBackground:tr}});await p.close();}}await b.close();}})();"""
open(f"{HERE}/_r.js", "w").write(js)
subprocess.run(["node", f"{HERE}/_r.js"], check=True)
for f in os.listdir(HERE):
    if f.startswith("_"): os.remove(f"{HERE}/{f}")
# profil fotoğrafı: yuvarlak, köşeler şeffaf
from PIL import Image, ImageDraw
im = Image.open(f"{HERE}/profil-fotografi.png").convert("RGBA"); s = im.width
m = Image.new("L", (s * 2, s * 2)); ImageDraw.Draw(m).ellipse((0, 0, s * 2, s * 2), fill=255)
out = Image.new("RGBA", (s, s)); out.paste(im, (0, 0), m.resize((s, s), Image.LANCZOS)); out.save(f"{HERE}/profil-fotografi.png")
# filigran için işareti üretim araçlarına kopyala
import shutil; shutil.copy(f"{HERE}/isaret.png", os.path.join(HERE, "..", "..", "uretim-araclari", "isaret.png"))
print("ok")
