# Video 13: Nemrut – TAMAMLANDI (26.11.2026)

Van Gölü videosunun (en çok tutan) devamı: gölün sodalı/çıkışsız olmasının sebebi Nemrut'un lav seti.

## Seslendirme
`elevenlabs_metin.txt` (908 karakter), Emrullah, eleven_v4, tek versiyon (Starter hesabı, 821 kredi, 50,1 sn).

## Sahneler
intro, lava, soda, question, caldera, cold, hot, yinyang, active, cta
- Dokular `nem_tex.py`: geniş Van bölgesi z10 (`vanr_tex.png`, BV 40,9–44,3 / 37,55–39,75), kaldera z13 (`nem_tex.png`). Göller veriden: düz yüzey + rakım (ana göl ~2.248 m, Ilıgöl ~2.253 m, Van ~1.648 m). Göl kıyı poligonları `nem_goller.json` (scikit-image find_contours).
- Lav, "kapattı" kelimesinde eski çıkışı keser (X + ÇIKIŞ KAPANDI). Buharlaşma bulutları + soda kristalleri. Kaldera halkası veriden ölçülmüş merkez/eksen (42,245 / 38,623; ~8,5 × 7 km) + canlı km cetveli. Derinlik çubuğu 0→176 m. Ilıgöl buharı. Yin-yang simgesi. Aktif: kızıl nabız halkaları.
- Renk = anlam: mavi = göl suyu, kırmızı/turuncu = lav/yanardağ/sıcak, beyaz = soda.

## Çalışma klasörü ek dosyaları
nem_tex.py, nem_goller.json, (+ ../geo/dem önbelleği; yoksa ilk açılışta indirilir), scikit-image.

## Tamamlandı (26.11.2026)
- `nemrut-shorts.mp4` (51,9 sn), −14,5 LUFS, TP −1,9 dBTP (ln2.py −2,2).
- Senkron (bitmiş videonun sesi Whisper ile): ortalama −3 ms, 150 ms üstü sapma yok.
- Düzeltme: soru sahnesinde (19–21 sn) görüş alanı detay dokusunun dışına taşıp bulanık geniş dokuya düşüyordu → kamera D 40→30, eğim 18→8; yalnızca 390–780. kareler yeniden render edildi.
- Kapaklar: kapak-dikey.jpg (kaldera + yin-yang), kapak-yatay.jpg (lav seti) – kapak13.py.
