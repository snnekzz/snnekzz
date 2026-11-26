"""İstanbul Boğazı kapakları. Dikey: twist sahnesi (yüzey + dip akıntısı haritada). Yatay: kesit (katmanlar + tekne)."""
import sys; sys.path.insert(0, "../kapak")
import render14 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/12-istanbul-bogazi/"
bg = M.frame(M.cue("twist", "derinlerde", "ama") + 1.2).convert("RGBA")
v = bg.copy(); top_shade(v, 760, 210)
pillx(v, "İSTANBUL BOĞAZI", 540, 120, 34, RED, WHITE)
text(v, "DENİZ AYNI ANDA", 540, 250, 66, WHITE, 5)
text(v, "İKİ YÖNE AKIYOR!", 540, 420, 128, YEL, 10, rot=-3)
bottom_shade(v)
text(v, "dipte ters akıntı!", 540, 1800, 92, (255, 150, 40), 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
bx = M.frame(M.cue("nets", "akıntıya", "karşı") + .3).convert("RGBA")
yatay(bx, 620, "BOĞAZ'DA DENİZ", "İKİ YÖNE!", "İSTANBUL BOĞAZI", RED, OUT + "kapak-yatay.jpg", s1=86, s2=150)
print("ok")
