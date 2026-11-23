import wave, json, sys, numpy as np
from piper import PiperVoice, SynthesisConfig
from script import SEGMENTS

M = "../dl/vits-piper-tr_TR-fahrettin-medium/tr_TR-fahrettin-medium.onnx"
LS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.92
voice = PiperVoice.load(M, config_path=M + ".json")
cfg = SynthesisConfig(length_scale=LS, noise_scale=0.6, noise_w_scale=0.7)

SR = None
parts, timing, t = [], [], 0.0
for i, (tts, cap, scene, gap) in enumerate(SEGMENTS):
    fn = f"seg{i:02d}.wav"
    with wave.open(fn, "wb") as w:
        voice.synthesize_wav(tts, w, syn_config=cfg)
    with wave.open(fn) as w:
        SR = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    # baştaki/sondaki sessizliği kırp
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.08 * SR)]
    if i == 0:
        gap = 0.4
    parts.append(np.zeros(int(gap * SR), np.float32)); t += gap
    timing.append({"i": i, "scene": scene, "cap": cap, "start": t, "end": t + len(a) / SR})
    parts.append(a); t += len(a) / SR
parts.append(np.zeros(int(1.6 * SR), np.float32)); t += 1.6
v = np.concatenate(parts)
v = v / np.max(np.abs(v)) * 0.9
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((v * 32767).astype(np.int16).tobytes())
json.dump({"total": t, "sr": SR, "segs": timing}, open("timing.json", "w"), ensure_ascii=False, indent=1)
print("total", round(t, 2), "s")
for s in timing:
    print(f'{s["start"]:6.2f}-{s["end"]:6.2f} {s["scene"]}')
