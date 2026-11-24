"""Klonlanmış sesle (Chatterbox Multilingual) seslendirme -> voice.wav + timing.json"""
import json, wave, sys, time, numpy as np, torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from script import SEGMENTS
torch.manual_seed(7)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu"); SR = m.sr
parts, timing, t = [], [], 0.0
for i, (tts, cap, scene, gap) in enumerate(SEGMENTS):
    t0 = time.time()
    w = m.generate(tts, language_id="tr", audio_prompt_path="ref.wav", exaggeration=0.6, cfg_weight=0.45, temperature=0.75)
    a = w.squeeze().numpy().astype(np.float32)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - int(0.03*SR)): idx[-1] + int(0.1*SR)]
    if i == 0: gap = 0.5
    parts.append(np.zeros(int(gap*SR), np.float32)); t += gap
    timing.append({"i": i, "scene": scene, "cap": cap, "start": t, "end": t + len(a)/SR})
    parts.append(a); t += len(a)/SR
    print(f"{i:02d} {scene:9s} {len(a)/SR:5.2f}s  ({time.time()-t0:.0f}s)", flush=True)
parts.append(np.zeros(int(1.8*SR), np.float32)); t += 1.8
v = np.concatenate(parts); v = v / np.max(np.abs(v)) * 0.9
with wave.open("voice.wav", "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((v*32767).astype(np.int16).tobytes())
json.dump({"total": t, "sr": SR, "segs": timing}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("toplam", round(t, 2))
