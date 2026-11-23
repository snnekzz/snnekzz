"""Telifsiz fon müziği + efektler üretir, seslendirmeyle karıştırır -> mix.wav"""
import json, subprocess, wave, numpy as np

SR = 44100
T = json.load(open("timing.json"))
S = {s["scene"]: s for s in T["segs"]}
st = lambda n: S[n]["start"]
TOT = T["total"]
N = int(TOT * SR) + SR
rng = np.random.default_rng(1)

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "voice.wav", "-ar", str(SR), "-ac", "1", "voice44.wav"], check=True)
with wave.open("voice44.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.zeros(N, np.float32); voice[:len(v)] = v[:N]

def note(f): return 440 * 2 ** ((f - 69) / 12)
t_all = np.arange(N) / SR

# ---- müzik ----
bpm = 100; beat = 60 / bpm; bar = beat * 4
prog = [[62, 65, 69], [58, 62, 65], [53, 57, 60], [60, 64, 67]]   # Dm Bb F C
music = np.zeros(N, np.float32)
nb = int(TOT / bar) + 2
for b in range(nb):
    ch = prog[b % 4]; t0 = b * bar
    i0 = int(t0 * SR); L = int(bar * SR * 1.15); i1 = min(N, i0 + L)
    if i0 >= N: break
    tt = np.arange(i1 - i0) / SR
    env = np.minimum(1, tt / 0.5) * np.exp(-tt * 0.35) * np.minimum(1, (L / SR - tt) / 0.3).clip(0)
    pad = sum(np.sin(2*np.pi*note(n-12)*tt) + 0.3*np.sin(2*np.pi*note(n)*tt*1.003) for n in ch)
    music[i0:i1] += 0.05 * env * pad
    # bas
    bt = np.arange(min(N - i0, int(bar * SR))) / SR
    music[i0:i0+len(bt)] += 0.10 * np.sin(2*np.pi*note(ch[0]-24)*bt) * np.exp(-bt*1.2)
    # arpej (sekizlik)
    for k in range(8):
        ts = t0 + k * beat / 2; j0 = int(ts * SR)
        if j0 >= N: break
        n_ = ch[[0, 1, 2, 1, 2, 0, 1, 2][k]] + 12
        ln = min(N - j0, int(0.45 * SR)); tt = np.arange(ln) / SR
        pl = (np.sin(2*np.pi*note(n_)*tt) + 0.25*np.sin(4*np.pi*note(n_)*tt)) * np.exp(-tt * 9)
        music[j0:j0+ln] += 0.035 * pl
    # hafif vuruş + hi-hat
    for k in range(4):
        ts = t0 + k * beat; j0 = int(ts * SR)
        if j0 >= N: break
        ln = min(N - j0, int(0.25 * SR)); tt = np.arange(ln) / SR
        if k in (0, 2):
            kick = np.sin(2*np.pi*(50 + 90*np.exp(-tt*30))*tt) * np.exp(-tt*14)
            music[j0:j0+ln] += 0.16 * kick
        j1 = int((ts + beat/2) * SR)
        if j1 < N:
            ln2 = min(N - j1, int(0.05*SR)); hh = rng.standard_normal(ln2) * np.exp(-np.arange(ln2)/SR*80)
            hh = np.diff(hh, prepend=0)
            music[j1:j1+ln2] += 0.025 * hh
# müzik giriş / çıkış
music *= np.clip(t_all / 1.0, 0, 1) * np.clip((TOT - t_all) / 1.8, 0, 1)

# ---- ducking ----
env = np.abs(voice)
k = int(0.12 * SR); env = np.convolve(env, np.ones(k)/k, mode="same")
duck = np.where(env > 0.01, 0.45, 1.0).astype(np.float32)
k2 = int(0.25 * SR); duck = np.convolve(duck, np.ones(k2)/k2, mode="same")
music *= duck

# ---- efektler ----
sfx = np.zeros(N, np.float32)
def add(arr, t, g):
    i = int(t * SR)
    if i >= N: return
    ln = min(len(arr), N - i); sfx[i:i+ln] += g * arr[:ln]
def whoosh(d=0.9):
    n = int(d*SR); x = rng.standard_normal(n).astype(np.float32)
    tt = np.arange(n)/SR; out = np.zeros(n, np.float32); y = 0
    a = 0.02 + 0.25*np.sin(np.pi*tt/d)       # sweep eden alçak geçiren
    for i in range(n): y += a[i]*(x[i]-y); out[i] = y
    return out * np.sin(np.pi*tt/d)**2 * 2.2
def pop():
    tt = np.arange(int(0.12*SR))/SR
    return np.sin(2*np.pi*(900 - 2500*tt)*tt) * np.exp(-tt*35)
def ding():
    tt = np.arange(int(0.9*SR))/SR
    return (np.sin(2*np.pi*1320*tt) + 0.5*np.sin(2*np.pi*1980*tt)) * np.exp(-tt*5)
def thud():
    tt = np.arange(int(0.35*SR))/SR
    return np.sin(2*np.pi*(60 + 120*np.exp(-tt*25))*tt) * np.exp(-tt*10) + 0.3*rng.standard_normal(len(tt))*np.exp(-tt*40)
def tick():
    tt = np.arange(int(0.02*SR))/SR
    return rng.standard_normal(len(tt)) * np.exp(-tt*300)

W = whoosh()
for t in [0.5, st("south") - .25, st("west") - .25, st("both") - .2, st("zoom_bt") - .3, st("cta") - .2]:
    add(W, t, 0.30)
for t in [st("why") - .05, st("colonial") + .5, st("colonial") + .9, st("south") + .2, st("south_len") + .3,
          st("west") + .2, st("desert") + .3, st("nile") + .4, st("nile") + 1.6, st("line1902") + .5,
          st("halaib") + .2, st("birtawil") + .1, st("why_bt") + 1.0, st("cta") + 1.3, 0.9]:
    add(pop(), t, 0.35)
for t in [st("south") + .4, st("west") + .4, st("line1902") + .2]:
    add(ding(), t, 0.18)
add(thud(), st("nomans") + .45, 0.6)
for base, dur in [(st("ruler"), 2.2), (st("ruler2") + .3, 2.4)]:
    for k in range(int(dur / 0.07)):
        add(tick(), base + k*0.07, 0.12)

mix = voice * 1.0 + music * 1.0 + sfx
mix = mix / max(1.0, np.max(np.abs(mix)) / 0.95)
st_ = np.stack([mix, mix], 1)
with wave.open("mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st_ * 32767).astype(np.int16).tobytes())
with wave.open("music_only.wav", "wb") as w:
    m = music + sfx; m = m / np.max(np.abs(m)) * 0.9
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((m * 32767).astype(np.int16).tobytes())
# YouTube için -14 LUFS'a normalize
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-ar", "48000", "mix.wav"], check=True)
print("ok", TOT)
