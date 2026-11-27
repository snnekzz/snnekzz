"""Van Gölü ikinci balık kapakları. Dikey: kuleler + balıklar (su altı). Yatay: açılıştaki 'TEK BALIK' kartı çizili."""
import sys; sys.path.insert(0, "../kapak")
import render16 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/14-van-golu-ikinci-balik/"
bg = M.frame(M.cue("towers", "mikrobiyalitler", "bilinen") + .2).convert("RGBA")
v = bg.copy(); top_shade(v, 760, 210)
pillx(v, "VAN GÖLÜ", 540, 120, 34, RED, WHITE)
text(v, "TEK BALIK DEMİŞTİK…", 540, 250, 66, WHITE, 5)
text(v, "YANILMIŞIZ!", 540, 420, 150, YEL, 11, rot=-3)
bottom_shade(v)
text(v, "40 m'lik kulelerde saklanıyor", 540, 1800, 76, (250, 205, 40), 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
bx = M.frame(M.cue("intro", "yanılmışız") + .6).convert("RGBA")
yatay(bx, 700, "VAN GÖLÜ'NDE", "2. BALIK!", "TEK BALIK DEĞİLMİŞ", RED, OUT + "kapak-yatay.jpg", s1=96, s2=150)
print("ok")
