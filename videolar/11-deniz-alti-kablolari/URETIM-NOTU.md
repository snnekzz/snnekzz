# Video 11: Deniz altı internet kabloları – TAMAMLANDI (26.11.2026)
Kaynak fikir: Sinan Dündoğan'ın "okyanus tabanına internet kabloları" videosu (396 bin) → harita + Türkiye köprüsü.

## Doğrulanan bilgiler
- Deniz altı kabloları uluslararası internet trafiğinin ~%99'unu taşır (ITU; TeleGeography kesin hesabın zor olduğunu not eder → "yaklaşık").
- Toplam uzunluk (26.11.2026 doğrulaması): eski 1,1 milyon km rakamı eskimiş. ITU 2025: ~1,7 milyon km (ICPC); TeleGeography 2025: ~1,48 milyon km → Dünya çevresi (40.075 km) ile 37–42 tur → videoda "35 kezden fazla" / "1,4 MİLYON KM+".
- Derin deniz kablosu ≈ bahçe hortumu kalınlığı (WEF).
- Türkiye: MedNautilus İstanbul'a iner (Yunanistan, İtalya, İsrail, Kıbrıs); KAFOS Karadeniz'de Türkiye–Bulgaristan–Romanya (iniş noktası İstanbul/İğneada kaynaklarda farklı → videoda sadece "Karadeniz").
- SEA-ME-WE 5: Singapur → Fransa (Toulon), ~20.000 km, Türkiye iniş noktası Marmaris (Türk Telekom).
- Haritadaki kablo güzergâhları temsilidir.

## Bitirme
EQ → words.py → build_timing_words.py → make_audio (sahneler: twist, question, istanbul, marmaris, hose, world, risk, cta) → render13.py → kapak + paylaşım.

## Tamamlandı (26.11.2026)
- Ses: Emrullah, eleven_v4, tek versiyon (kullanıcının ikinci ElevenLabs hesabında web arayüzünden üretildi, mp3 olarak yüklendi) → EQ (voice_eq.txt) → `deniz-alti-kablolari-shorts.mp4`.
- Ses seviyesi: iki geçişli loudnorm → ~−14 LUFS, TP ≤ −1,1 dBTP (make_audio artık iki geçişli).
- Altyazı-ses senkronu (bitmiş videonun sesi Whisper ile yeniden ölçüldü): ortalama sapma −1 ms, 150 ms üstü sapma yok.
- Kapaklar: `kapak-dikey.jpg` (1080x1920), `kapak-yatay.jpg` (1280x720) – betik `kapak11.py` (+ harita-motoru/kapak_ortak.py).
- Paylaşım metinleri: `paylasim-bilgileri.md`.
- Düzeltme: Romanya/Bulgaristan etiketleri üst altyazıyla çakışıyor ve kenarda kesiliyordu → ekran içine ve altyazı bandının altına sınırlandı.
