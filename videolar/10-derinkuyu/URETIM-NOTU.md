# Video 10: Derinkuyu – TAMAMLANDI (26.11.2026)

## Doğrulanan bilgiler
- 1963: bir adam evini tadil ederken duvarı yıktı, tünel buldu (tavuk anlatısı kullanılmadı). 1969'da ziyarete açıldı.
- Derinlik ~85 m (≈ 28 katlı bina), en az 18 seviye; sadece bir kısmı ziyarete açık.
- Kapasite tahmini: hayvanlarıyla ~20.000 kişi ("tahmin ediliyor").
- Yarım tonluk yuvarlak taş kapılar, katlar ayrı ayrı kapatılabiliyordu.
- Kaymaklı'ya tünel bağlantısı var; uzunluk kaynaklarda net değil → rakam verilmedi.
- Kesit çizimi temsilidir.

## Bitirme adımları
EQ → words.py → build_timing_words.py → make_audio (sahneler: tunnel, question, city, depth, people, rooms, doors, levels, kaymakli, more, cta) → render12.py → kapak + paylaşım.

## Yeni keşif kontrolü (26.11.2026)
- 2014'te bulunan Nevşehir Kale yeraltı şehrinin Derinkuyu'dan büyük olabileceği tahmin ediliyor → videoda "en büyük" denmiyor, sorun yok.
- 85 m / 18 seviye / 20.000 kişi kaynaklarda tutarlı; ziyarete 8 seviye açık → "sadece bir kısmı" doğru.

## Tamamlandı (26.11.2026)
- Ses: Emrullah, eleven_v4, tek versiyon (kullanıcının ikinci ElevenLabs hesabında web arayüzünden üretildi, mp3 olarak yüklendi) → EQ (voice_eq.txt) → `derinkuyu-shorts.mp4`.
- Ses seviyesi: iki geçişli loudnorm → ~−14 LUFS, TP ≤ −1,1 dBTP (make_audio artık iki geçişli).
- Altyazı-ses senkronu (bitmiş videonun sesi Whisper ile yeniden ölçüldü): ortalama sapma +8 ms, 150 ms üstü sapma yok.
- Kapaklar: `kapak-dikey.jpg` (1080x1920), `kapak-yatay.jpg` (1280x720) – betik `kapak10.py` (+ harita-motoru/kapak_ortak.py).
- Paylaşım metinleri: `paylasim-bilgileri.md`.
