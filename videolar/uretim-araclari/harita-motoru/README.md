# Harita motoru – yeni oturumda kurulum

Bu klasör Shorts render altyapısının tamamıdır (render9–12'nin bağımlılıkları).

## Kurulum (yeni oturum)
```bash
W=/tmp/is && mkdir -p $W/tex && cd $W
cp -r /home/user/snnekzz/videolar/uretim-araclari/harita-motoru/* .
cp tex/* $W/tex/              # render4.py dokuyu ../tex/ altında arar → çalışma klasörünü $W/calis yap:
mkdir -p calis && cp *.py *.json *.ttf *.png *.txt calis/ && cd calis
# video dosyalarını kopyala (ör. Göbeklitepe):
cp /home/user/snnekzz/videolar/09-gobeklitepe/{script.py,render11.py} .
```
- Whisper: `python3 -m venv wvenv && wvenv/bin/pip install faster-whisper` → `wvenv/bin/python words.py eleven.mp3 small`
- Rölyef dokuları ilk çalıştırmada AWS açık yükseklik verisinden üretilir (`../geo/dem` önbelleği).
- `t7_big2_r.png` yoksa render11/12 ilk açılışta üretir (birkaç dakika).

## Bitirme akışı (ses gelince)
1. ElevenLabs: Emrullah (`DpEiQMnL9WxMsymCsjPY`), model eleven_v4, metin = `elevenlabs_metin.txt` (başında [energetic, fast-paced documentary narration]).
2. `ffmpeg -i eleven_orig.mp3 -af "$(cat voice_eq.txt)" eleven.mp3`
3. `words.py` → `build_timing_words.py`
4. make_audio10.py'yi kopyalayıp sahne adlarını script.py'ye göre değiştir → mix.wav
5. render 4 parça → concat → `brand.stamp_metadata`
6. Kapak (kapak7.py örneği) + paylasim-bilgileri.md
