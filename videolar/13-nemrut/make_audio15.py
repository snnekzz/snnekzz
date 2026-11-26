"""Nemrut (video 13): gizemli belgesel müziği + MÜZİKAL yumuşak geçişler (gürültü yok).
Geçiş = yavaş yükselen yumuşak akor (sinüs, alçak geçiren) + çok hafif çan. Konuşmanın ~6 dB altında."""
import json, subprocess, wave, numpy as np
from scipy.signal import butter, sosfilt
SR = 44100
T = json.load(open("timing.json")); S = {s["scene"]: s for s in T["segs"]}
st = lambda n: S[n]["start"]; en = lambda n: S[n]["end"]
TOT = T["total"]; N = int(TOT * SR) + SR; t = np.arange(N) / SR
with wave.open("voice.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]
nf = lambda m: 440 * 2 ** ((m - 69) / 12)
env = lambda pts: np.interp(t, *zip(*pts)).astype(np.float32)
# E minör, gizemli; yavaş arpej + pad
chords = [(52, 59, 64, 67), (48, 55, 60, 64), (50, 57, 62, 66), (47, 54, 59, 62)]   # Em C D Bm
pad = np.zeros(N, np.float32); arp = np.zeros(N, np.float32); bar = 3.6
for i in range(int(TOT / bar) + 1):
    a, b = int(i * bar * SR), min(N, int((i + 1.2) * bar * SR)); tt = np.arange(b - a) / SR
    e = np.minimum(1, tt / 1.2) * np.minimum(1, ((b - a) / SR - tt) / 1.0).clip(0)
    pad[a:b] += sum(np.sin(2 * np.pi * nf(n) * tt) for n in chords[i % 4]) / 4 * e
    for k in range(8):
        j0 = int((i * bar + k * bar / 8) * SR); ln = min(N - j0, int(.9 * SR))
        if ln <= 0: continue
        n = chords[i % 4][[0, 1, 2, 3, 2, 1, 2, 3][k]] + 12; tt2 = np.arange(ln) / SR
        arp[j0:j0 + ln] += np.sin(2 * np.pi * nf(n) * tt2) * np.exp(-tt2 * 5)
low = sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), arp).astype(np.float32)
g_pad = env([(0, 0), (.4, .8), (st("question"), 1.0), (en("active"), 1.1), (st("cta"), .8), (TOT - 1, .7), (TOT, 0)])
g_arp = env([(0, 0), (.6, .5), (st("question"), .8), (st("question"), .3), (st("hot"), .7), (TOT - 1, .5), (TOT, 0)])
music = .05 * pad * g_pad + .03 * low * g_arp
e_ = np.convolve(np.abs(voice), np.ones(int(.12 * SR)) / int(.12 * SR), mode="same")
music *= np.convolve(np.where(e_ > .01, .6, 1.0), np.ones(int(.3 * SR)) / int(.3 * SR), mode="same").astype(np.float32)
sfx = np.zeros(N, np.float32)
def add(a, at, g):
    i = int(at * SR)
    if 0 <= i < N: n = min(len(a), N - i); sfx[i:i + n] += g * a[:n]
def soft_swell(root=52, d=1.8):
    """müzikal geçiş: yükselen yumuşak akor (alçak geçiren), sonunda hafif çan"""
    n = int(d * SR); tt = np.arange(n) / SR
    ch = sum(np.sin(2 * np.pi * nf(root + iv) * tt) for iv in (0, 7, 12, 16)) / 4
    ch = sosfilt(butter(2, 1400, "low", fs=SR, output="sos"), ch)
    e = (np.sin(np.pi * tt / d) ** 2) * np.minimum(1, tt / (d * .6))
    bell = np.zeros(n); b0 = int(d * .55 * SR); bt = np.arange(n - b0) / SR
    bell[b0:] = (np.sin(2 * np.pi * nf(root + 24) * bt) + .4 * np.sin(2 * np.pi * nf(root + 31) * bt)) * np.exp(-bt * 4) * .35
    return (ch * e + bell).astype(np.float32)
W_ = json.load(open("words.json"))
cue_kriz = next((w["s"] + .05 for w in W_ if "kapattı" in w["w"].lower()), st("lava") + 3)
def thud():
    tt = np.arange(int(.6 * SR)) / SR; return np.sin(2 * np.pi * (48 + 50 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 7)
roots = [52, 55, 50, 57, 52, 48, 55, 52, 50, 57]
for k, sc in enumerate(("lava", "soda", "question", "caldera", "cold", "hot", "yinyang", "active", "cta")):
    add(soft_swell(roots[k % len(roots)]), st(sc) - .9, .15)
add(thud(), cue_kriz, .18)                  # "kapattı": çıkış kapandı
add(thud(), st("caldera") + .1, .18)         # kaldera
sfx *= np.convolve(np.where(e_ > .01, .8, 1.0), np.ones(int(.2 * SR)) / int(.2 * SR), mode="same").astype(np.float32)
mix = voice + music + sfx; mix /= max(1.0, np.max(np.abs(mix)) / .95)
with wave.open("mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
# iki geçişli loudnorm (tek geçiş hedefin ~1,5 dB altında kalıyordu)
_f = "loudnorm=I=-14:TP=-1.5:LRA=11"
_o = subprocess.run(["ffmpeg", "-hide_banner", "-i", "mix_raw.wav", "-af", _f + ":print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
_m = json.loads(_o[_o.rindex("{"):_o.rindex("}") + 1])
_f += f":measured_I={_m['input_i']}:measured_TP={_m['input_tp']}:measured_LRA={_m['input_lra']}:measured_thresh={_m['input_thresh']}:offset={_m['target_offset']}:linear=true"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", _f, "-ar", "48000", "mix.wav"], check=True)
sw = soft_swell() * .15 * .8
print("ok", round(TOT, 2), "| geçiş", round(20 * np.log10(np.sqrt(np.mean(sw[int(.6 * SR):int(1.2 * SR)] ** 2)) + 1e-9), 1), "dB | konuşma",
      round(20 * np.log10(np.sqrt(np.mean(voice[voice != 0] ** 2)) + 1e-9), 1), "dB")
