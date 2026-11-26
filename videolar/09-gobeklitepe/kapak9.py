"""Göbeklitepe kapakları (dikey 1080x1920 + yatay 1280x720). Arka plan: render11 'human' sahnesi (altyazısız)."""
import sys; sys.path.insert(0, "../kapak")
import render11 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/09-gobeklitepe/"
bg = M.frame(M.st("human") + 3.0).convert("RGBA")
v = bg.copy(); top_shade(v)
pillx(v, "GÖBEKLİTEPE · 11.500 YIL", 540, 120, 34, RED, WHITE)
text(v, "PİRAMİTLERDEN 7.000 YIL ÖNCE", 540, 250, 60, WHITE, 5)
text(v, "BUNLARI KİM DİKTİ?", 540, 420, 128, YEL, 10, rot=-3)
text(v, "yazı yok, tekerlek yok!", 540, 1760, 92, YEL, 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
yatay(bg, 560, "PİRAMİTLERDEN", "7.000 YIL ÖNCE!", "GÖBEKLİTEPE · ŞANLIURFA", RED, OUT + "kapak-yatay.jpg", s1=84, s2=92)
print("ok")
