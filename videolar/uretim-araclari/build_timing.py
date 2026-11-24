import json, subprocess, wave, numpy as np, librosa
P = json.load(open("timing_piper.json"))["segs"]
d = json.load(open("dtw_out.json")); raw = d["raw"]; pauses = d["pauses"]
y, sr = librosa.load("eleven.mp3", sr=44100)
r = librosa.feature.rms(y=y, frame_length=441, hop_length=441)[0]
first = np.argmax(20*np.log10(r+1e-9) > -40) * 0.01
last = (len(r) - np.argmax(20*np.log10(r[::-1]+1e-9) > -40)) * 0.01
bounds = []
for i in range(len(raw)-1):
    mid = (raw[i][1] + raw[i+1][0]) / 2
    p = min(pauses, key=lambda q: 0 if q[0] <= mid <= q[1] else min(abs(q[0]-mid), abs(q[1]-mid)))
    bounds.append(p)
segs = []
for i in range(len(raw)):
    s = first if i == 0 else bounds[i-1][1]
    e = last if i == len(raw)-1 else bounds[i][0]
    segs.append([s, e])
lead = 0.4; off = lead - first
a = y[max(0, int((first-0.02)*sr)): int((last+0.15)*sr)]
a = np.concatenate([np.zeros(int((lead-0.02)*sr)), a, np.zeros(int(1.5*sr))]).astype(np.float32)
a = a / np.max(np.abs(a)) * 0.9
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a*32767).astype(np.int16).tobytes())
total = len(a)/sr
out = [{"i": i, "scene": p["scene"], "cap": p["cap"], "start": s+off, "end": e+off} for i, ((s, e), p) in enumerate(zip(segs, P))]
json.dump({"total": total, "sr": sr, "segs": out}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2))
for o in out: print(f'{o["start"]:6.2f}-{o["end"]:6.2f} {o["scene"]}')
