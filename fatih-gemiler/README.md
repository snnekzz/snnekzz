# Gemiler Karadan Yürüyor (1453)

Fatih Sultan Mehmed'in 22 Nisan 1453'te gemileri Galata tepesi üzerinden Haliç'e indirmesini anlatan
45 saniyelik dikey (9:16) 3D kısa video. Sahne, kamera ve render tamamen **Three.js** ile kodlandı;
anlatım sesi yapay zeka (ElevenLabs) ile üretildi.

## Çalıştırma

```bash
npm install
# Önizleme (sesli): bir sunucu açıp tarayıcıda index.html'i açın
npx http-server .   # veya: python3 -m http.server
# Kare kare render (Playwright + Chromium gerekir)
node render.cjs --out frames --pr 1
# Ses ile birleştirip MP4 yapma
ffmpeg -framerate 30 -i frames/f_%05d.jpg -i audio/anlatim.mp3 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest gemiler.mp4
```

Hızlı taslak için `--pr 0.5`, belirli anlar için `--stills 5,13,27` kullanın.

## Dosyalar
- `main.js` — sahne: arazi, deniz, gemiler, insanlar, öküzler, zincir, 11 çekim, etiketler, altyazılar
- `render.cjs` — Playwright ile kareleri JPEG olarak kaydeder
- `audio/anlatim.mp3` — anlatım sesi

## Tarihsel notlar
- Gemi sayısı kaynaklarda 67–72 arasında geçer ("yetmiş kadar").
- Güzergahın tam yeri (Tophane mi, Beşiktaş/Dolmabahçe mi) tartışmalıdır; videoda yaygın kabul gören
  Beşiktaş → Kasımpaşa rotası basitleştirilmiş bir haritayla gösterilir.
- Kritovulos ve Barbaro gibi çağdaş kaynaklar yağlanmış kızakları, öküzleri, açık yelkenleri ve
  gemilerdeki kürekçilerin karada kürek çekmesini anlatır.
