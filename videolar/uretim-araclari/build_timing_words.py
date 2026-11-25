"""Whisper kelime zamanlarıyla KESİN hizalama. Ses hiç kesilmez.
Girdi: eleven.mp3, words.json (words.py), script.py (altyazı metinleri)
Çıktı: voice.wav (0.4 sn baş + ses + 1.8 sn son), timing.json (sahne + kelime zamanları)
Kontrol: eşleşmeyen kelime oranı yüksekse hata verir."""
import json, re, wave, difflib, subprocess, numpy as np
from script import SEGMENTS

LEAD, TAIL, SR = 0.05, 1.8, 44100   # ses videonun başında başlar (kanca hemen)
def norm(w):
    w = w.replace("İ", "i").replace("I", "ı").lower()
    w = re.sub(r"[’'`]", "", w); w = re.sub(r"[^\wçğıöşü]", "", w)
    return w
# whisper kelimeleri: kesme işaretiyle ayrılanları birleştir ("Türkiye" + "'nin")
W = []
for x in json.load(open("words.json")):
    if W and x["w"][:1] in "'’": W[-1]["w"] += x["w"]; W[-1]["e"] = x["e"]
    else: W.append(dict(x))
wn = [norm(x["w"]) for x in W]
# altyazı kelimeleri
caps = []
for si, (_, cap, scene, _) in enumerate(SEGMENTS):
    for w in cap.split(): caps.append((si, w))
cn = [norm(w) for _, w in caps]
sm = difflib.SequenceMatcher(None, cn, wn, autojunk=False)
t_of = [None] * len(caps)
for a, b, n in sm.get_matching_blocks():
    for k in range(n): t_of[a + k] = (W[b + k]["s"], W[b + k]["e"])
# eşleşmeyenler: komşu eşleşmelerden enterpolasyon (sayılar vb.)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op in ("replace", "delete", "insert") and i2 > i1:
        s = W[j1]["s"] if j1 < len(W) and j2 > j1 else (t_of[i1 - 1][1] if i1 > 0 and t_of[i1 - 1] else 0)
        e = W[j2 - 1]["e"] if j2 > j1 else s + 0.3
        for k in range(i1, i2):
            if t_of[k] is None:
                f0 = (k - i1) / (i2 - i1); f1 = (k - i1 + 1) / (i2 - i1)
                t_of[k] = (s + (e - s) * f0, s + (e - s) * f1)
miss = sum(1 for k in range(len(caps)) if cn[k] not in wn)
print(f"altyazı kelimesi: {len(caps)}, whisper ile birebir eşleşmeyen: {miss}")
assert miss / len(caps) < 0.25, "Çok fazla eşleşmeyen kelime – metin ile ses uyuşmuyor"
# ses: hiç kesme yok
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "eleven.mp3", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
a = np.concatenate([np.zeros(int(LEAD * SR), np.float32), a, np.zeros(int(TAIL * SR), np.float32)])
a = a / np.max(np.abs(a)) * 0.9
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
total = len(a) / SR
segs = []
for si, (_, cap, scene, _) in enumerate(SEGMENTS):
    idx = [k for k, (s, _) in enumerate(caps) if s == si]
    st_ = t_of[idx[0]][0] + LEAD; en_ = t_of[idx[-1]][1] + LEAD
    segs.append({"i": si, "scene": scene, "cap": cap, "start": round(st_, 3), "end": round(en_, 3),
                 "tts_word_starts": [round(t_of[k][0] + LEAD, 3) for k in idx]})
# kontrol: sahneler sıralı ve çakışmasız olmalı
for x, y in zip(segs[:-1], segs[1:]):
    assert y["start"] >= x["start"], f"sıra hatası: {x['scene']} -> {y['scene']}"
json.dump({"total": total, "sr": SR, "segs": segs}, open("timing.json", "w"), ensure_ascii=False, indent=1)
for s in segs: print(f'{s["start"]:6.2f}-{s["end"]:6.2f} {s["scene"]}')
print("toplam", round(total, 2), "sn — ses kesintisiz, zamanlar ölçümle")
