# Harita Shorts üretim araçları

Bu klasördeki kodlar "Mısır'ın Sınırları Neden Dümdüz?" videosunu baştan sona üretti:
seslendirme (Piper TTS, Türkçe "fahrettin" sesi), harita animasyonu (Natural Earth verisi),
telifsiz fon müziği ve efektler (kodla sentezleniyor), altyazılar.

| Dosya | Görevi |
|---|---|
| `script.py` | Senaryo: seslendirme metni, ekran altyazısı, sahne adı |
| `make_voice.py` | Her cümleyi seslendirir, `voice.wav` ve `timing.json` üretir |
| `make_audio.py` | Müzik + efekt üretir, sesle karıştırır, -14 LUFS'a normalize eder |
| `render.py` | 1080x1920 30fps harita animasyonu (sahneler `timing.json`'a göre zamanlanır) |

Gerekenler: `pip install piper-tts matplotlib shapely numpy pillow soundfile`, ffmpeg,
`npm i world-atlas@2.0.2 topojson-client @expo-google-fonts/anton @expo-google-fonts/montserrat`
ve `vits-piper-tr_TR-fahrettin-medium` ses modeli (k2-fsa/sherpa-onnx GitHub sürümlerinde).
