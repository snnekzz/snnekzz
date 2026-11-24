"""Kaliningrad: belgesel gerilim müziği, geçiş sesi YOK, çok kısık efektler."""
import json, subprocess, wave, numpy as np
SR = 44100
T = json.load(open("timing.json")); S = {s["scene"]: s for s in T["segs"]}
st = lambda n: S[n]["start"]; en = lambda n: S[n]["end"]
TOT = T["total"]; N = int(TOT * SR) + SR; t = np.arange(N) / SR; rng = np.random.default_rng(5)
with wave.open("voice.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]
nf = lambda m: 440 * 2 ** ((m - 69) / 12)
env = lambda pts: np.interp(t, *zip(*pts)).astype(np.float32)
# A minör drone + yavaş yaylı pad
drone = (np.sin(2*np.pi*nf(33)*t) + .5*np.sin(2*np.pi*nf(40)*t*1.002) + .3*np.sin(2*np.pi*nf(45)*t)) * (0.75 + .25*np.sin(2*np.pi*.11*t))
chords = [(57, 60, 64), (53, 57, 60), (55, 59, 62), (52, 55, 59)]   # Am F G Em
pad = np.zeros(N, np.float32); bar = 4.2
for i in range(int(TOT / bar) + 1):
    a, b = int(i * bar * SR), min(N, int((i + 1.15) * bar * SR)); tt = np.arange(b - a) / SR
    e = np.minimum(1, tt / 1.2) * np.minimum(1, ((b - a) / SR - tt) / 1.0).clip(0)
    pad[a:b] += sum(np.sin(2*np.pi*nf(n)*tt) for n in chords[i % 4]) / 3 * e
g_d = env([(0, 0), (1.5, .8), (st("siege"), 1.1), (st("operation"), 1.4), (en("rescue"), 1.2), (st("today"), .7), (TOT, 0)])
g_p = env([(0, 0), (2, .5), (st("who"), .7), (st("siege"), .2), (en("rescue"), .2), (st("today"), .7), (TOT - 1, .6), (TOT, 0)])
music = .045 * drone * g_d + .05 * pad * g_p
# yavaş nabız (koridor bölümünde)
pulse_len = int(.3 * SR); pl = np.sin(2*np.pi*50*np.arange(pulse_len)/SR) * np.exp(-np.arange(pulse_len)/SR*20)
tc = st("siege") + .5
while tc < en("rescue"):
    i = int(tc * SR)
    if i + pulse_len < N: music[i:i+pulse_len] += .18 * pl
    tc += 0.75
e_ = np.convolve(np.abs(voice), np.ones(int(.12*SR))/int(.12*SR), mode="same")
music *= np.convolve(np.where(e_ > .01, .55, 1.0), np.ones(int(.3*SR))/int(.3*SR), mode="same").astype(np.float32)
sfx = np.zeros(N, np.float32)
def add(a, at, g):
    i = int(at * SR)
    if 0 <= i < N: n = min(len(a), N - i); sfx[i:i+n] += g * a[:n]
def thump():
    tt = np.arange(int(.5*SR))/SR; return np.sin(2*np.pi*(45 + 60*np.exp(-tt*18))*tt) * np.exp(-tt*8)
def stampsnd():
    tt = np.arange(int(.15*SR))/SR; return (np.sin(2*np.pi*120*tt) + .3*rng.standard_normal(len(tt))) * np.exp(-tt*40)
def boom():
    tt = np.arange(int(2.2*SR))/SR; return np.sin(2*np.pi*(32 + 45*np.exp(-tt*6))*tt) * np.exp(-tt*1.8)
for at in (st("y1921") + .2, st("y1973") + .2, st("operation") + .2):
    add(thump(), at, .14)
add(boom(), st("operation") + .05, .20)
# yumuşak geçiş: tizleri kesilmiş, yavaş yükselip alçalan hava sesi (kulak tırmalamaz)
from scipy.signal import butter, sosfilt
def soft_swell(d=1.6):
    n = int(d * SR); x = rng.standard_normal(n)
    x = sosfilt(butter(4, 380, "low", fs=SR, output="sos"), x)
    x /= np.max(np.abs(x)) + 1e-9
    tt = np.arange(n) / SR
    e = np.sin(np.pi * tt / d) ** 3                      # yumuşak giriş/çıkış
    low = np.sin(2 * np.pi * (70 + 25 * tt / d) * tt) * 0.35
    return (x * 0.8 + low) * e
for sc in ("name", "who", "y1921", "y1973", "size", "operation", "today", "cta"):
    add(soft_swell(), st(sc) - .9, .06)
mix = voice + music + sfx; mix /= max(1.0, np.max(np.abs(mix)) / .95)
with wave.open("mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "mix.wav"], check=True)
print("ok", round(TOT, 2))
