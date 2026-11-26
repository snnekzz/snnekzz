"""Deniz altı kabloları kapakları (dikey 1080x1920 + yatay 1280x720). Arka plan: render13 'istanbul' sahnesi (altyazısız)."""
import sys; sys.path.insert(0, "../kapak")
import render13 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/11-deniz-alti-kablolari/"
bg = M.frame(M.st("istanbul") + 3.2).convert("RGBA")
v = bg.copy(); off = 150   # harita aşağı kaydırılır: ülke etiketleri başlığın altında kalsın
v.paste(bg.crop((0, 0, 1080, 1920 - off)), (0, off)); v.paste(bg.crop((0, 0, 1080, off)).transpose(Image.FLIP_TOP_BOTTOM), (0, 0))
top_shade(v, 860, 230)
pillx(v, "DENİZ ALTI KABLOLARI", 540, 120, 34, RED, WHITE)
text(v, "TÜRKİYE'NİN İNTERNETİ", 540, 250, 64, WHITE, 5)
text(v, "DENİZİN DİBİNDEN!", 540, 420, 124, YEL, 10, rot=-3)
bottom_shade(v)
text(v, "uydu değil, kablo!", 430, 1850, 86, CYAN, 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-yatay.jpg".replace("yatay", "dikey"), quality=93)
yatay(bg, 380, "UYDU DEĞİL,", "KABLO!", "TÜRKİYE'NİN İNTERNETİ", RED, OUT + "kapak-yatay.jpg", s2=160)
print("ok")
