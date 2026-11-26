"""Gerilim müziği (drone + kalp atışı) + efektler, seslendirmeyle karışım -> mix.wav"""
import json, subprocess, wave, numpy as np

SR = 44100
T = json.load(open("timing.json")); S = {s["scene"]: s for s in T["segs"]}
st = lambda n: S[n]["start"]; en = lambda n: S[n]["end"]
TOT = T["total"]; N = int(TOT * SR) + SR
rng = np.random.default_rng(3)
t = np.arange(N) / SR

with wave.open("voice.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]

def nf(m): return 440 * 2 ** ((m - 69) / 12)
def env_lin(points):
    """[(zaman, değer)...] doğrusal zarf"""
    xs, ys = zip(*points); return np.interp(t, xs, ys).astype(np.float32)

# --- karanlık drone (D minör) ---
drone = (np.sin(2*np.pi*nf(38)*t) + 0.5*np.sin(2*np.pi*nf(45)*t*1.002) + 0.35*np.sin(2*np.pi*nf(50)*t*0.998)
         + 0.25*np.sin(2*np.pi*nf(53)*t)) * (0.7 + 0.3*np.sin(2*np.pi*0.13*t))
# filtrelenmiş gürültü "rüzgâr"
wn = rng.standard_normal(N).astype(np.float32); k = 400
wind = np.convolve(wn, np.ones(k)/k, mode="same") * 6
g_drone = env_lin([(0, 0), (1.5, .9), (st("y1880"), 1.0), (st("gone") - .3, 1.4), (st("gone"), 0), (en("gone") + .6, 0),
                   (st("zone") + .5, .8), (st("twist"), .9), (st("survive"), .5), (TOT, 0)])
music = 0.05 * drone * g_drone + 0.03 * wind * g_drone

# --- kalp atışı: y1880 -> gone arası hızlanarak ---
def heart(tt):
    lub = np.sin(2*np.pi*55*tt) * np.exp(-tt*28); return lub
hb_len = int(0.25*SR); hb = heart(np.arange(hb_len)/SR)
tcur = st("arrows") - 1.0
while tcur < st("gone") - 0.25:
    prog = (tcur - (st("arrows") - 1)) / max(1, (st("gone") - st("arrows") + 1))
    bpm = 62 + 48 * prog; gain = 0.35 + 0.45 * prog
    for off, g in ((0, 1.0), (0.22, 0.7)):
        i = int((tcur + off) * SR)
        if i + hb_len < N: music[i:i+hb_len] += 0.5 * gain * g * hb
    tcur += 60 / bpm

# --- ters köşe sonrası hüzünlü/umutlu pad (D majör'e çözülme) ---
pad_g = env_lin([(0, 0), (st("flu") - .5, 0), (st("flu") + 1.5, .7), (st("survive"), 1), (TOT - 1.5, .8), (TOT, 0)])
pad = sum(np.sin(2*np.pi*nf(n)*t) * (1 + 0.003*np.sin(2*np.pi*0.2*t)) for n in (50, 57, 62, 66)) / 4
music += 0.07 * pad * pad_g

# ducking
e = np.convolve(np.abs(voice), np.ones(int(.12*SR))/int(.12*SR), mode="same")
duck = np.convolve(np.where(e > .01, .55, 1.0), np.ones(int(.3*SR))/int(.3*SR), mode="same").astype(np.float32)
music *= duck

# --- efektler ---
sfx = np.zeros(N, np.float32)
def add(a, at, g):
    i = int(at * SR)
    if 0 <= i < N: n = min(len(a), N - i); sfx[i:i+n] += g * a[:n]
def whoosh(d=1.0):
    n = int(d*SR); x = rng.standard_normal(n).astype(np.float32); tt = np.arange(n)/SR
    out = np.zeros(n, np.float32); yv = 0.0; a = 0.02 + 0.3*np.sin(np.pi*tt/d)
    for i in range(n): yv += a[i]*(x[i]-yv); out[i] = yv
    return out * np.sin(np.pi*tt/d)**2 * 2.4
def fwip():   # ok sesi
    n = int(.28*SR); tt = np.arange(n)/SR; x = rng.standard_normal(n)
    return (np.diff(x, prepend=0) * np.exp(-((tt-.1)/.05)**2) * .6 + np.sin(2*np.pi*(1800-3000*tt)*tt)*np.exp(-tt*25)*.3)
def thump():
    tt = np.arange(int(.5*SR))/SR
    return np.sin(2*np.pi*(45 + 70*np.exp(-tt*18))*tt) * np.exp(-tt*7)
def boom():
    tt = np.arange(int(2.5*SR))/SR
    return (np.sin(2*np.pi*(32 + 50*np.exp(-tt*6))*tt) * np.exp(-tt*1.6) +
            0.25*np.convolve(rng.standard_normal(len(tt)), np.ones(200)/200, mode="same")*np.exp(-tt*2.5)*8)
def pop():
    tt = np.arange(int(.12*SR))/SR; return np.sin(2*np.pi*(700-2000*tt)*tt)*np.exp(-tt*35)

W1 = whoosh()
for at in (0.6, st("name") - .4, st("zone") - .3, st("cta") - .2):
    pass  # geçiş sesi kaldırıldı
for at in (st("y1880") + .3, st("y2004") + .3, st("y2006") + .3, st("y2018") + .3):
    add(thump(), at, .16)
for k in range(9):
    add(fwip(), st("arrows") + .5 + k * .38, .07)
for k in range(6):
    add(fwip(), st("y2004") + 1.2 + k * .3, .06)
add(boom(), en("y2018") + .35, .28)
for at in (st("name") + .2, st("unknown") + .4, st("unknown") + 1.2, st("zone") + 1.6, st("flu") + .8, st("cta") + 1.2):
    pass  # pop kaldırıldı

mix = voice + music + sfx
mix /= max(1.0, np.max(np.abs(mix)) / .95)
with wave.open("mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-ar", "48000", "mix.wav"], check=True)
print("ok", round(TOT, 2))
