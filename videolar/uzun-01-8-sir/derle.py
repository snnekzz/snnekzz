"""Uzun video: Haritaların Bilinmeyen 8 Sırrı – 8 Shorts'tan 16:9 derleme (yeni seslendirme gerekmez).
Düzen: solda dikey video (bulanık arka plan), sağda bölüm paneli; bölüm arası kart + müzikal geçiş; giriş ve 20 sn bitiş ekranı."""
import os, json, subprocess, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V = "/home/user/snnekzz/videolar/"
FONT = "/home/user/snnekzz/videolar/kanal/logo/"
OUT = V + "uzun-01-8-sir/"
os.makedirs(OUT, exist_ok=True); os.makedirs("seg", exist_ok=True)
W, H, FPS, SR = 1920, 1080, 30, 48000
NAVY, RED, GOLD, WHITE, MUTED = (10, 18, 34), (229, 36, 59), (255, 201, 74), (255, 255, 255), (150, 160, 180)
F9 = lambda s: ImageFont.truetype(FONT + "mont900.ttf", s); F7 = lambda s: ImageFont.truetype(FONT + "mont700.ttf", s)
ISARET = Image.open(V + "uretim-araclari/isaret.png").convert("RGBA")
CH = [  # (klasör, dosya, kesim sn, başlık)
    ("06-yenikapi", "yenikapi-shorts.mp4", 47.3, "İstanbul'un altından çıkan 37 gemi"),
    ("07-van-golu", "van-golu-shorts.mp4", 38.2, "Tek balıklı dev göl: Van Gölü"),
    ("01-misir-sinirlari", "misir-sinirlari-shorts.mp4", 64.9, "Mısır'ın cetvelle çizilmiş sınırları"),
    ("08-agri-dagi", "agri-dagi-shorts.mp4", 36.3, "Ağrı Dağı ve 1932 toprak takası"),
    ("04-suleyman-sah", "suleyman-sah-shorts.mp4", 51.7, "Suriye'deki Türk toprağı: Süleyman Şah"),
    ("05-istiklal-yolu", "istiklal-yolu-shorts.mp4", 51.9, "İnebolu'dan Ankara'ya bir mermi"),
    ("02-kaliningrad", "kaliningrad-shorts.mp4", 58.6, "Avrupa'nın ortasındaki Rusya: Kaliningrad"),
    ("03-kuzey-sentinel", "kuzey-sentinel-shorts.mp4", 57.8, "Kimsenin giremediği ada: Kuzey Sentinel"),
]

def tr_up(s): return s.replace("i", "İ").replace("ı", "I").upper()
def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def isaret(size):
    im = ISARET.crop(ISARET.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)

def bg_grad():
    y, x = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    r = np.clip(np.sqrt((x - .3) ** 2 + (y - .5) ** 2) / .9, 0, 1)
    a = np.array((27, 42, 74), np.float32) * (1 - r[..., None]) + np.array((5, 8, 15), np.float32) * r[..., None]
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")

def panel(i):
    """sağ panel (şeffaf PNG): bölüm no, başlık, ilerleme listesi, işaret"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = 860
    d.rounded_rectangle((x0 - 40, 70, W - 60, H - 70), radius=36, fill=(8, 12, 22, 200))
    d.text((x0, 120), "HARİTALARIN BİLİNMEYEN 8 SIRRI", font=F7(26), fill=GOLD)
    d.text((x0, 170), f"{i + 1:02d}", font=F9(150), fill=RED)
    y = 360
    for ln in wrap(tr_up(CH[i][3]), F9(54), W - 60 - 40 - x0):
        d.text((x0, y), ln, font=F9(54), fill=WHITE); y += 66
    y = max(y + 40, 560)
    for k, c in enumerate(CH):
        col = WHITE if k == i else MUTED; f = F9(26) if k == i else F7(24)
        if k == i: d.rounded_rectangle((x0 - 14, y - 6, W - 100, y + 36), radius=10, fill=(229, 36, 59, 230))
        d.text((x0, y), f"{k + 1:02d}  {c[3]}", font=f, fill=col); y += 46
    m = isaret(70); im.alpha_composite(m, (W - 100 - m.width, H - 70 - 30 - m.height))
    d.text((x0, H - 150), "@BilinmeyeninPesinde", font=F7(26), fill=MUTED)
    return im

def card(i):
    im = bg_grad(); d = ImageDraw.Draw(im)
    d.text((W / 2, 330), f"{i + 1:02d}", font=F9(220), fill=RED, anchor="mm")
    y = 520
    for ln in wrap(tr_up(CH[i][3]), F9(72), 1500):
        d.text((W / 2, y), ln, font=F9(72), fill=WHITE, anchor="mm"); y += 88
    d.text((W / 2, 860), "HARİTALARIN BİLİNMEYEN 8 SIRRI", font=F7(30), fill=GOLD, anchor="mm")
    return im.convert("RGB")

def intro():
    im = bg_grad(); d = ImageDraw.Draw(im)
    m = isaret(360); im.alpha_composite(m, (int(W / 2 - m.width / 2), 90))
    d.text((W / 2, 560), "HARİTALARIN", font=F9(110), fill=WHITE, anchor="mm")
    d.text((W / 2, 690), "BİLİNMEYEN 8 SIRRI", font=F9(110), fill=RED, anchor="mm")
    d.text((W / 2, 820), "Sınırlar, kayıp gemiler, yasak adalar ve gizli takaslar", font=F7(38), fill=MUTED, anchor="mm")
    d.text((W / 2, 930), "BİLİNMEYENİN PEŞİNDE", font=F9(34), fill=GOLD, anchor="mm")
    return im.convert("RGB")

def outro():
    im = bg_grad(); d = ImageDraw.Draw(im)
    m = isaret(200); im.alpha_composite(m, (int(W / 2 - m.width / 2), 70))
    d.text((W / 2, 330), "BİR SONRAKİ SIRDA GÖRÜŞÜRÜZ", font=F9(64), fill=WHITE, anchor="mm")
    d.text((W / 2, 400), "Abone ol – her hafta yeni bir sır", font=F7(36), fill=GOLD, anchor="mm")
    for x in (W * .28, W * .72):      # YouTube bitiş ekranı öğeleri için boş çerçeveler
        d.rounded_rectangle((x - 300, 520, x + 300, 860), radius=24, outline=(60, 75, 105), width=4)
    return im.convert("RGB")

# ---------- müzik / geçiş sesi ----------
nf = lambda m: 440 * 2 ** ((m - 69) / 12)
def swell(d=1.6, root=52):
    t = np.arange(int(d * SR)) / SR
    ch = sum(np.sin(2 * np.pi * nf(root + iv) * t) for iv in (0, 7, 12, 16)) / 4
    e = np.sin(np.pi * t / d) ** 2
    bell = np.zeros_like(t); b0 = int(d * .5 * SR); bt = t[b0:] - t[b0]
    bell[b0:] = np.sin(2 * np.pi * nf(root + 24) * bt) * np.exp(-bt * 4) * .3
    return (ch * e * .35 + bell).astype(np.float32)
def pad(d, root=50):
    t = np.arange(int(d * SR)) / SR; chords = [(0, 7, 12, 15), (-4, 3, 8, 12), (-2, 5, 10, 14), (-5, 2, 7, 10)]
    out = np.zeros_like(t)
    for k in range(int(d / 3.2) + 1):
        a, b = int(k * 3.2 * SR), min(len(t), int((k + 1.25) * 3.2 * SR)); tt = t[a:b] - t[a]
        e = np.minimum(1, tt / 1.0) * np.clip(((b - a) / SR - tt) / 1.0, 0, 1)
        out[a:b] += sum(np.sin(2 * np.pi * nf(root + iv) * tt) for iv in chords[k % 4]) / 4 * e
    fade = np.minimum(1, t / 1.0) * np.minimum(1, (d - t) / 1.5)
    return (out * fade * .22).astype(np.float32)
def wav(path, x):
    x = np.clip(x, -1, 1); s = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(s.tobytes())

def still_seg(img, dur, audio, out):
    img.save("seg/_s.png"); wav("seg/_s.wav", audio)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", "seg/_s.png", "-i", "seg/_s.wav", "-t", f"{dur}",
                    "-vf", f"zoompan=z='1+0.0006*on':d={int(dur * FPS)}:s={W}x{H}:fps={FPS},format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", out], check=True)

segs = []
still_seg(intro(), 5.0, pad(5.0) + np.pad(swell(2.0), (int(2.6 * SR), int(.4 * SR)))[:int(5 * SR)], "seg/00_intro.mp4"); segs.append(("intro", "seg/00_intro.mp4"))
for i, (fold, fn, cut, title) in enumerate(CH):
    still_seg(card(i), 1.6, swell(1.6, [52, 55, 50, 57][i % 4]), f"seg/{i + 1:02d}a.mp4"); segs.append(("card", f"seg/{i + 1:02d}a.mp4"))
    panel(i).save("seg/_p.png")
    fc = (f"[0:v]split[a][b];[a]scale={W}:-2,crop={W}:{H},boxblur=28:2,eq=brightness=-0.28:saturation=1.1[bg];"
          f"[b]scale=-2:{H}[fg];[bg][fg]overlay=170:0[v1];[v1][1:v]overlay=0:0,format=yuv420p[v];"
          f"[0:a]afade=t=out:st={cut - .5:.2f}:d=0.5,aresample={SR},aformat=channel_layouts=stereo[au]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", f"{cut}", "-i", V + fold + "/" + fn, "-i", "seg/_p.png",
                    "-filter_complex", fc, "-map", "[v]", "-map", "[au]", "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", f"seg/{i + 1:02d}b.mp4"], check=True)
    segs.append((title, f"seg/{i + 1:02d}b.mp4"))
still_seg(outro(), 20.0, pad(20.0, 48), "seg/99_outro.mp4"); segs.append(("outro", "seg/99_outro.mp4"))

open("seg/list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for _, p in segs))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "seg/list.txt", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "seg/tmp.mp4"], check=True)
# bölüm zaman damgaları (açıklama için)
t, stamps = 0.0, []
for kind, p in segs:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    if kind == "card": stamps.append(t)
    t += dur
names = [c[3] for c in CH]
lines = ["0:00 Giriş"] + [f"{int(s // 60)}:{int(s % 60):02d} {n}" for s, n in zip(stamps, names)] + [f"{int((t - 20) // 60)}:{int((t - 20) % 60):02d} Kapanış"]
open(OUT + "bolumler.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines)); print("toplam", round(t, 1))
