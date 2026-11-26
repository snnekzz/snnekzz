"""Derinkuyu kapakları (dikey 1080x1920 + yatay 1280x720). Arka plan: render12 'rooms' sahnesi (altyazısız)."""
import sys; sys.path.insert(0, "../kapak")
import render12 as M
from kapak_ortak import *
mute(M); OUT = "/home/user/snnekzz/videolar/10-derinkuyu/"
bg = M.frame(M.st("rooms") + 2.0).convert("RGBA")
v = bg.copy(); top_shade(v, 760, 210)
pillx(v, "DERİNKUYU · 85 METRE", 540, 120, 34, RED, WHITE)
text(v, "DUVARI YIKTI, ARKASINDAN", 540, 250, 62, WHITE, 5)
text(v, "ŞEHİR ÇIKTI!", 540, 420, 150, YEL, 11, rot=-3)
bottom_shade(v)
text(v, "28 katlı bina derinliği", 540, 1835, 80, YEL, 4, rot=-5, font="caveat.ttf")
v.convert("RGB").save(OUT + "kapak-dikey.jpg", quality=93)
yatay(bg, 160, "YERİN ALTINDA", "ŞEHİR!", "DERİNKUYU · NEVŞEHİR", RED, OUT + "kapak-yatay.jpg", s1=88, s2=160)
print("ok")
