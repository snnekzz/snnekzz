"""DTW sınırlarını duraklamalara oturtur, kritik anlara ek sessizlik ekler."""
import json, wave, numpy as np, librosa
P = json.load(open("timing_piper.json"))["segs"]
d = json.load(open("dtw_out.json")); raw = d["raw"]; pauses = d["pauses"]
EXTRA = {"who": 0.1, "y1921": 0.15, "y1973": 0.15, "siege": 0.3, "operation": 0.45, "today": 0.2, "cta": 0.2}
y, sr = librosa.load("eleven.mp3", sr=44100)
r = librosa.feature.rms(y=y, frame_length=441, hop_length=441)[0]
db = 20*np.log10(r+1e-9)
first = np.argmax(db > -40) * 0.01
last = (len(r) - np.argmax(db[::-1] > -40)) * 0.01
cuts = []   # her sınırın (konuşma bitişi, sonraki başlangıç) – sıralı ve yakın olmalı
prev = first
for i in range(len(raw)-1):
    mid = (raw[i][1] + raw[i+1][0]) / 2
    cand = [q for q in pauses if q[0] > prev + 0.3 and (q[0] - 0.4 <= mid <= q[1] + 0.4)]
    if cand:
        p = min(cand, key=lambda q: 0 if q[0] <= mid <= q[1] else min(abs(q[0]-mid), abs(q[1]-mid)))
    else:
        p = (mid - 0.02, mid + 0.02)
    cuts.append(p); prev = p[1]
pieces, timing, t = [], [], 0.0
lead = 0.4
pieces.append(np.zeros(int(lead*sr))); t = lead
for i, p in enumerate(P):
    s = first if i == 0 else cuts[i-1][1]
    e = last if i == len(P)-1 else cuts[i][0]
    if i > 0:
        gap = (cuts[i-1][1] - cuts[i-1][0]) + EXTRA.get(p["scene"], 0)
        pieces.append(np.zeros(int(gap*sr))); t += gap
    seg = y[int(s*sr): int(e*sr)]
    timing.append({"i": i, "scene": p["scene"], "cap": p["cap"], "start": t, "end": t + len(seg)/sr})
    pieces.append(seg); t += len(seg)/sr
pieces.append(np.zeros(int(1.8*sr))); t += 1.8
a = np.concatenate(pieces).astype(np.float32); a = a/np.max(np.abs(a))*0.9
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a*32767).astype(np.int16).tobytes())
json.dump({"total": t, "sr": sr, "segs": timing}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("total", round(t, 2))
for o in timing: print(f'{o["start"]:6.2f}-{o["end"]:6.2f} {o["scene"]}')
