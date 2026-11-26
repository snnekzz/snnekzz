"""Nemrut kapakları. Dikey: kaldera (iki göl, yin-yang). Yatay: lav seti sahnesi."""
import sys; sys.path.insert(0, "../kapak")
import render15 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/13-nemrut/"
bg = M.frame(M.en("yinyang") - .2).convert("RGBA")
v = bg.copy(); top_shade(v, 760, 210)
pillx(v, "NEMRUT · BİTLİS", 540, 120, 34, RED, WHITE)
text(v, "YANARDAĞIN TEPESİNDE", 540, 250, 64, WHITE, 5)
text(v, "İKİ GÖL VAR!", 540, 420, 150, YEL, 11, rot=-3)
bottom_shade(v)
text(v, "biri soğuk, biri sıcak", 540, 1800, 88, (255, 150, 40), 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
bx = M.frame(M.cue("lava", "kapattı") + .8).convert("RGBA")
yatay(bx, 420, "VAN GÖLÜ'NÜ", "YANARDAĞ DEĞİŞTİRDİ!", "NEMRUT · VAN GÖLÜ", RED, OUT + "kapak-yatay.jpg", s1=90, s2=64)
print("ok")
