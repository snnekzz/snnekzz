"""İstiklal Yolu: duygusal belgesel müziği, yumuşak geçiş sesleri, Ilgaz/Şerife'de rüzgâr.
Kurallar (stil rehberi): ses kesilmez; efektler konuşmada ×0.8; geçiş sesi konuşmanın ~6 dB altında, 140–1100 Hz."""
import json, subprocess, wave, numpy as np
from scipy.signal import butter, sosfilt
SR = 44100
T = json.load(open("timing.json")); S = {s["scene"]: s for s in T["segs"]}
st = lambda n: S[n]["start"]; en = lambda n: S[n]["end"]
TOT = T["total"]; N = int(TOT * SR) + SR; t = np.arange(N) / SR; rng = np.random.default_rng(7)
with wave.open("voice.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]
nf = lambda m: 440 * 2 ** ((m - 69) / 12)
env = lambda pts: np.interp(t, *zip(*pts)).astype(np.float32)
# D minör, yavaş ve duygusal
chords = [(50, 57, 62, 65), (46, 53, 58, 62), (48, 55, 60, 64), (45, 52, 57, 61)]   # Dm Bb C A
pad = np.zeros(N, np.float32); bar = 4.0
for i in range(int(TOT / bar) + 1):
    a, b = int(i * bar * SR), min(N, int((i + 1.2) * bar * SR)); tt = np.arange(b - a) / SR
    e = np.minimum(1, tt / 1.4) * np.minimum(1, ((b - a) / SR - tt) / 1.0).clip(0)
    pad[a:b] += sum(np.sin(2 * np.pi * nf(n) * tt) * (1 + .002 * np.sin(2 * np.pi * .3 * tt)) for n in chords[i % 4]) / 4 * e
# yavaş piyano benzeri notalar
mel = np.zeros(N, np.float32)
notes = [74, 72, 69, 70, 69, 65, 67, 69]
for i in range(int(TOT / 1.0)):
    j0 = int(i * 1.0 * SR); ln = min(N - j0, int(1.6 * SR))
    if ln <= 0: break
    tt = np.arange(ln) / SR; n = notes[i % len(notes)]
    mel[j0:j0 + ln] += (np.sin(2 * np.pi * nf(n) * tt) + .3 * np.sin(4 * np.pi * nf(n) * tt)) * np.exp(-tt * 2.8)
drone = np.sin(2 * np.pi * nf(38) * t) + .4 * np.sin(2 * np.pi * nf(45) * t)
g_pad = env([(0, 0), (2, .7), (st("serife"), .8), (en("serife"), 1.0), (st("legacy"), 1.0), (TOT - 1.2, .8), (TOT, 0)])
g_mel = env([(0, 0), (st("hook"), .4), (st("ilgaz"), .3), (st("women"), .6), (st("serife"), .9), (en("legacy"), .7), (TOT - 1, .4), (TOT, 0)])
g_dr = env([(0, 0), (2, .6), (st("ilgaz"), .9), (en("serife"), 1.0), (st("legacy"), .4), (TOT, 0)])
music = .05 * pad * g_pad + .035 * mel * g_mel + .04 * drone * g_dr
# rüzgâr (Ilgaz + Şerife)
wn = sosfilt(butter(2, [200, 900], "band", fs=SR, output="sos"), rng.standard_normal(N)).astype(np.float32)
wn /= np.max(np.abs(wn)) + 1e-9
gust = .6 + .4 * np.sin(2 * np.pi * .23 * t) * np.sin(2 * np.pi * .07 * t + 1)
g_w = env([(0, 0), (st("ilgaz") - .3, 0), (st("ilgaz") + .8, 1), (en("ilgaz") + .6, .2), (st("serife") - .3, .2), (st("serife") + 1, 1), (en("serife") + .6, 0), (TOT, 0)])
music += .09 * wn * gust * g_w
e_ = np.convolve(np.abs(voice), np.ones(int(.12 * SR)) / int(.12 * SR), mode="same")
music *= np.convolve(np.where(e_ > .01, .6, 1.0), np.ones(int(.3 * SR)) / int(.3 * SR), mode="same").astype(np.float32)
sfx = np.zeros(N, np.float32)
def add(a, at, g):
    i = int(at * SR)
    if 0 <= i < N: n = min(len(a), N - i); sfx[i:i + n] += g * a[:n]
def soft_swell(d=1.6):
    n = int(d * SR); x = sosfilt(butter(3, [140, 1100], "band", fs=SR, output="sos"), rng.standard_normal(n))
    x /= np.max(np.abs(x)) + 1e-9; tt = np.arange(n) / SR
    return (x * .8 + np.sin(2 * np.pi * (70 + 25 * tt / d) * tt) * .35) * np.sin(np.pi * tt / d) ** 3
def thump():
    tt = np.arange(int(.5 * SR)) / SR; return np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 8)
for sc in ("hook", "sea", "route", "versus", "kagni", "ilgaz", "days", "women", "serife", "legacy", "cta"):
    add(soft_swell(), st(sc) - .7, .30)
add(thump(), st("versus") + 2.0, .22)        # X işaretleri
add(thump(), st("days") + .6, .22)           # ≈ 2 HAFTA
sfx *= np.convolve(np.where(e_ > .01, .80, 1.0), np.ones(int(.2 * SR)) / int(.2 * SR), mode="same").astype(np.float32)
mix = voice + music + sfx; mix /= max(1.0, np.max(np.abs(mix)) / .95)
with wave.open("mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "mix.wav"], check=True)
sw = soft_swell() * .30 * .80
print("ok", round(TOT, 2), "| geçiş sesi", round(20 * np.log10(np.sqrt(np.mean(sw[int(.6 * SR):int(1.0 * SR)] ** 2)) + 1e-9), 1),
      "dB | konuşma", round(20 * np.log10(np.sqrt(np.mean(voice[voice != 0] ** 2)) + 1e-9), 1), "dB")
