"""Seslendirmeyi kanalın standart hızına getirir (her videoda aynı, doğal tempo).
Kullanım: python3 auto_tempo.py giris.mp3 cikis.mp3 [whisper_python]
- Hız ölçümü: Whisper kelime zamanlarıyla hece/sn (Türkçe: ünlü sayısı), duraklar dahil genel tempo.
- Hedef: 5.9 hece/sn. Değişim sınırı: 0.92x – 1.10x (fazlası yapay duyulur).
- Esnetme: ffmpeg rubberband (formant korumalı, yüksek kalite) – atempo KULLANMA.
- Değişim %2'den küçükse dokunmaz."""
import json, subprocess, sys, os

TARGET, LO, HI = 5.9, 0.92, 1.10
VOW = set("aeıioöuüAEIİOÖUÜâîû")
src, dst = sys.argv[1], sys.argv[2]
py = sys.argv[3] if len(sys.argv) > 3 else "python3"
here = os.path.dirname(os.path.abspath(__file__))

def measure(path):
    subprocess.run([py, os.path.join(here, "words.py"), path, "small"], check=True, capture_output=True,
                   env={**os.environ, "HF_HUB_DISABLE_XET": "1"})
    W = json.load(open("words.json"))
    syl = sum(sum(c in VOW for c in w["w"]) for w in W)
    return syl / (W[-1]["e"] - W[0]["s"])

rate = measure(src)
f = max(LO, min(HI, TARGET / rate))
if abs(f - 1) < 0.02:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "44100", "-b:a", "192k", dst], check=True); f = 1.0
else:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af",
                    f"rubberband=tempo={f:.4f}:pitchq=quality:formant=preserved:transients=smooth:window=standard",
                    "-ar", "44100", "-b:a", "192k", dst], check=True)
new = measure(dst)    # words.json artık çıkış dosyasının zamanlarını içerir (hizalama için hazır)
print(f"ölçülen tempo {rate:.2f} → katsayı {f:.3f} → yeni tempo {new:.2f} hece/sn (hedef {TARGET})")
