"""ElevenLabs ile Türkçe seslendirme. Kullanım: python3 make_voice_eleven.py <voice_id> [model]
Anahtar ortamın ağ ayarlarından otomatik eklenir (xi-api-key). voice.wav + timing.json üretir
(make_voice.py ile aynı biçim, ayrıca kelime zamanlamaları)."""
import base64, json, subprocess, sys, urllib.request, wave
import numpy as np
from script import SEGMENTS

VOICE = sys.argv[1]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "eleven_multilingual_v2"
SR = 44100
KEY = "proxy-injected"   # gerçek anahtarı ağ proxy'si ekler

def tts(text, prev, nxt):
    body = {"text": text, "model_id": MODEL, "language_code": "tr",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25, "use_speaker_boost": True}}
    if MODEL != "eleven_v3":
        body["previous_text"] = prev; body["next_text"] = nxt
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=pcm_44100",
        data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    pcm = np.frombuffer(base64.b64decode(r["audio_base64"]), np.int16).astype(np.float32) / 32768
    return pcm, r.get("alignment") or {}

parts, timing, t = [], [], 0.0
for i, (txt, cap, scene, gap) in enumerate(SEGMENTS):
    prev = SEGMENTS[i-1][0] if i else ""
    nxt = SEGMENTS[i+1][0] if i + 1 < len(SEGMENTS) else ""
    a, al = tts(txt, prev, nxt)
    idx = np.where(np.abs(a) > 0.01)[0]
    s0 = max(0, idx[0] - int(0.03*SR)); a = a[s0: idx[-1] + int(0.08*SR)]
    if i == 0: gap = 0.4
    parts.append(np.zeros(int(gap*SR), np.float32)); t += gap
    # kelime başlangıçları (seslendirme metnindeki kelimeler)
    words, ws = [], []
    chars = al.get("characters", []); starts = al.get("character_start_times_seconds", [])
    cur = ""
    for ch, cs in zip(chars, starts):
        if ch.isspace():
            if cur: words.append(cur); cur = ""
            continue
        if not cur: ws.append(t + max(0, cs - s0/SR))
        cur += ch
    if cur: words.append(cur)
    timing.append({"i": i, "scene": scene, "cap": cap, "start": t, "end": t + len(a)/SR,
                   "tts_words": words, "tts_word_starts": ws})
    parts.append(a); t += len(a)/SR
    print(f"{i:02d} {len(a)/SR:5.2f}s {scene}")
parts.append(np.zeros(int(1.6*SR), np.float32)); t += 1.6
v = np.concatenate(parts); v = v / np.max(np.abs(v)) * 0.9
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((v*32767).astype(np.int16).tobytes())
json.dump({"total": t, "sr": SR, "segs": timing}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("toplam", round(t, 2), "sn")
