# Video 12: İstanbul Boğazı – TASLAK (seslendirme bekliyor, 26.11.2026)

## Seslendirme metni (ElevenLabs'e aynen)
`elevenlabs_metin.txt` (814 karakter ≈ 45 sn; Emrullah, eleven_v4, tek versiyon)

## Sahneler
intro, twist, question, salt, layers, nets, river, size, cta
- Harita: İstanbul dokusu `ist_tex.py` (AWS terrarium z12 → kıyı çizgisi veriden; bu bölgede batimetri yok → kıyıdan uzaklığa göre temsilî derinlik rengi). Boğaz orta hattı `bogaz_hat.json` (veriden otomatik).
- Kesit: tuzlu su önce sağ yarıda, "ağır" kelimesinde altına kayıp katman olur (yoğunluk akıntısı). Ağ sahnesinde tekne yüzey akıntısına karşı sürüklenir.
- Nehir: Karadeniz çıkışından ~60 km kuzeye temsilî güzergâh + canlı km sayacı. Büyüklük: 22.000 sayaç + Ren 1 / nehir 10 birim çubuk.
- Renk = anlam: açık mavi = Karadeniz suyu / yüzey, turuncu = tuzlu Akdeniz suyu / dip.

## Test
`fake_timing.py` ile ses olmadan (5,6 hece/sn) zamanlama üretilip tüm sahneler kare kare kontrol edildi.

## Bitirme adımları (ses gelince)
eleven_orig.mp3 → EQ (voice_eq.txt) → eleven.mp3 → words.py → build_timing_words.py → make_audio14.py → render14.py 4 parça → birleştir → stamp_metadata → kapak12.py → paylaşım.
Çalışma klasörüne ek olarak: ist_tex.py, bogaz_hat.json (+ ../geo/dem önbelleği; yoksa ilk açılışta indirilir).

## Doğrulama
Bkz. `paylasim-bilgileri.md` → Bilgi kaynakları. Mutlak ifade kontrolü: "aynı anda iki ters yöne" (genel rejim; meteorolojik koşullarda zaman zaman tek yönlü olabilir → açıklamada sorun yok, videoda genel durum anlatılıyor).
