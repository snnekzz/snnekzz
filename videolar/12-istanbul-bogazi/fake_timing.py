"""Ses yokken test zamanlaması: Emrullah ~5,6 hece/sn. words.json + timing.json + sessiz voice.wav üretir.
Gerçek ses gelince words.py + build_timing_words.py ile değiştirilir."""
import json, re, wave, numpy as np
from script import SEGMENTS
RATE, LEAD, TAIL, SR = 5.6, 0.05, 1.8, 44100
syl = lambda w: max(1, len(re.findall("[aeıioöuüAEIİOÖUÜ]", w)))
t = 0.0; words = []; segs = []
for si, (nar, cap, scene, _) in enumerate(SEGMENTS):
    nw = nar.split(); cw = cap.split(); s0 = t; ws = []
    for w in nw:
        d = syl(w) / RATE; words.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)}); ws.append(t); t += d
        if w[-1] in ".?!:": t += .32
        elif w[-1] == ",": t += .14
    # altyazı kelimeleri (sayılar farklı yazılabilir) → seslendirme süresine orantılı dağıt
    cst = [s0 + (t - s0) * k / len(cw) for k in range(len(cw))]
    segs.append({"i": si, "scene": scene, "cap": cap, "start": round(s0 + LEAD, 3), "end": round(t - .2 + LEAD, 3), "tts_word_starts": [round(x + LEAD, 3) for x in cst]})
total = t + LEAD + TAIL
json.dump(words, open("words.json", "w"), ensure_ascii=False, indent=0)
json.dump({"total": total, "sr": SR, "segs": segs}, open("timing.json", "w"), ensure_ascii=False, indent=1)
with wave.open("voice.wav", "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(np.zeros(int(total * SR), np.int16).tobytes())
for s in segs: print(f'{s["start"]:6.2f}-{s["end"]:6.2f} {s["scene"]}')
print("toplam", round(total, 2))
