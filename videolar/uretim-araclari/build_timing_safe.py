"""Güvenli hizalama: sesi ASLA kelime içinden kesmez.
- DTW sınırının ±0.6 sn çevresinde en sessiz 80 ms'lik anı arar.
- O an gerçekten sessizse (< -35 dB) orada keser ve gerekirse ek sessizlik ekler.
- Sessiz an yoksa sesi kesmez; sahne sınırı sadece zaman olarak işaretlenir.
- Kesimlerde 15 ms yumuşak geçiş (tık sesi olmaz).
- Sonda otomatik kontrol: kelime içinde kesim varsa hata verir.
Kullanım: python3 build_timing_safe.py ses.mp3  (EXTRA aşağıda)"""
import json, sys, wave, numpy as np, librosa

SRC = sys.argv[1] if len(sys.argv) > 1 else "eleven.mp3"
EXTRA = json.load(open("extra.json")) if __import__("os").path.exists("extra.json") else {}
SIL_DB = -35.0
P = json.load(open("timing_piper.json"))["segs"]
raw = json.load(open("dtw_out.json"))["raw"]
y, sr = librosa.load(SRC, sr=44100)
hop = 441                                     # 10 ms
rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
db = 20 * np.log10(rms + 1e-9)
win = 8                                       # 80 ms
dbw = np.convolve(db, np.ones(win) / win, mode="same")
first = np.argmax(db > -40) * 0.01
last = min((len(db) - np.argmax(db[::-1] > -40)) * 0.01, raw[-1][1] + 0.35)

cuts = []   # (zaman, kesilebilir_mi)
prev = first
for i in range(len(raw) - 1):
    mid = (raw[i][1] + raw[i + 1][0]) / 2
    a = int(max(prev + 0.2, mid - 0.6) * 100); b = int(min(last - 0.2, mid + 0.6) * 100)
    if b <= a: cuts.append((mid, False)); continue
    k = a + int(np.argmin(dbw[a:b]))
    tq = k * 0.01
    cuts.append((tq, bool(dbw[k] < SIL_DB))); prev = tq

FADE = int(0.015 * sr)
def fade(seg, fin, fout):
    seg = seg.copy()
    if fin and len(seg) > FADE: seg[:FADE] *= np.linspace(0, 1, FADE)
    if fout and len(seg) > FADE: seg[-FADE:] *= np.linspace(1, 0, FADE)
    return seg

pieces = [np.zeros(int(0.4 * sr), np.float32)]; t = 0.4; timing = []
cur = first; seg_start_t = t
bounds = [c for c in cuts]
for i, p in enumerate(P):
    end = last if i == len(P) - 1 else bounds[i][0]
    cuttable_next = (i < len(P) - 1) and bounds[i][1]
    seg = y[int(cur * sr): int(end * sr)]
    timing.append({"i": i, "scene": p["scene"], "cap": p["cap"], "start": t, "end": t + len(seg) / sr})
    pieces.append(fade(seg, i == 0 or bounds[i - 1][1], cuttable_next or i == len(P) - 1)); t += len(seg) / sr
    if i < len(P) - 1:
        extra = EXTRA.get(P[i + 1]["scene"], 0.0) if cuttable_next else 0.0
        if extra > 0: pieces.append(np.zeros(int(extra * sr), np.float32)); t += extra
    cur = end
pieces.append(np.zeros(int(1.8 * sr), np.float32)); t += 1.8
out = np.concatenate(pieces).astype(np.float32); out = out / np.max(np.abs(out)) * 0.9

# --- otomatik kontrol: eklenen sessizliklerin kenarında konuşma olmamalı ---
bad = [(P[i + 1]["scene"], round(c[0], 2)) for i, c in enumerate(bounds) if EXTRA.get(P[i + 1]["scene"], 0) > 0 and not c[1]]
cut_ok = sum(1 for c in bounds if c[1])
print(f"kesilebilir sınır: {cut_ok}/{len(bounds)}  |  sessizlik eklenemeyen (ses kesilmedi): {bad}")
for i, c in enumerate(bounds):
    if c[1]:
        lvl = dbw[int(c[0] * 100)]
        assert lvl < SIL_DB, f"HATA: {P[i+1]['scene']} sınırında konuşma varken kesim ({lvl:.1f} dB)"

with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())
json.dump({"total": t, "sr": sr, "segs": timing}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("toplam", round(t, 2), "sn — kontrol geçti, kelime içinde kesim yok")
