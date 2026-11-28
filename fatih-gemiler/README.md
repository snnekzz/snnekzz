# Gemiler Karadan Yürüyor (1453) — Bilinmeyenin Peşinde

Fatih Sultan Mehmed'in 22 Nisan 1453'te gemileri Galata tepesi üzerinden Haliç'e indirmesini anlatan
~39 saniyelik dikey (9:16) 3D kısa video. Sahne, karakterler, kamera ve render tamamen **Three.js** ile kodlandı.

## Yapı
- `src/core.js` — renderer, kamera, post-processing (bloom, renk düzenleme, vinyet, film greni), geometri yardımcıları
- `src/world.js` — gökyüzü/ışık (gün batımı · gece · şafak), arazi, yansımalı deniz, bitki örtüsü, surlar, Galata, zincir, kızaklar, meşaleler
- `src/actors.js` — detaylı kadırgalar (latin yelken, kürekler, tente, fener), eklemli insanlar, öküzler, Fatih ve atı, halatlar, su sıçraması
- `src/shots.js` — 16 çekimlik kurgu; kesmeler anlatımın kelime zamanlarına (`audio/words.json`) bağlı
- `src/main.js` — zaman çizelgesi, kelime kelime vurgulu altyazı, etiketler, başlık ve kapanış kartı
- `render.cjs` — Playwright ile kare kare JPEG çıktısı
- `mix.sh` — ses miksi (anlatım EQ + kompresör, müzik ducking, efektler, -14 LUFS)

## Ses
- Anlatım: ElevenLabs "Emrullah" (`DpEiQMnL9WxMsymCsjPY`), `eleven_v4`, metnin başında `[energetic, fast-paced documentary narration]`
- EQ: 250 Hz −4 dB, 450 Hz −2 dB (kutu tınısı), 3.5 kHz +2.5 dB, 8 kHz raf +3 dB; hız ayarı yok
- Müzik: Magic Hour (enstrümantal, mehter esintili); efektler: ElevenLabs Sound Effects
- Seviye: −14 LUFS, true peak −1 dB

## Çalıştırma
```bash
npm install
node render.cjs --out frames --pr 0.75          # kareler (taslak için --pr 0.5, tek kare için --stills 5,13)
./mix.sh 39.25                                   # audio/mix.wav + mix.m4a
ffmpeg -framerate 30 -i frames/f_%05d.jpg -i audio/mix.wav -vf scale=1080:1920:flags=lanczos \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart video.mp4
```
Anlatım değişirse: yeni sesi `audio/emrullah_a.mp3`, kelime zamanlarını `audio/words.json` olarak koyun; kurgu otomatik uyar.

## Tarihsel notlar
- Gemi sayısı kaynaklarda 67–72 arası ("yetmiş kadar"). Güzergahın tam yeri tartışmalı; Beşiktaş → Kasımpaşa rotası sadeleştirilmiş haritayla gösterilir.
- Kritovulos ve Barbaro yağlanmış kızakları, öküzleri, açık yelkenleri ve kürekçilerin karada kürek çekmesini anlatır.
