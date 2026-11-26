"""Whisper ile kelime zaman damgaları -> words.json"""
import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small", device="cpu", compute_type="int8")
import subprocess, numpy as np
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", sys.argv[1], "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
segs, info = m.transcribe(audio, language="tr", word_timestamps=True, beam_size=5, vad_filter=False)
words = []
for s in segs:
    for w in s.words: words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
json.dump(words, open("words.json", "w"), ensure_ascii=False, indent=0)
print(len(words), "kelime"); print(" ".join(w["w"] for w in words))
