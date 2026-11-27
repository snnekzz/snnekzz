# Video 9: Göbeklitepe – TAMAMLANDI (26.11.2026)


## Seslendirme metni (ElevenLabs'e aynen)
[energetic, fast-paced documentary narration] + narration.txt

## Bitirme adımları (ses gelince ~30 dk)
1. eleven_orig.mp3 indir → EQ (`uretim-araclari/voice_eq_emrullah.txt`) → eleven.mp3
2. words.py → build_timing_words.py (LEAD 0.05)
3. make_audio (make_audio10 tabanı, sahne adları: twist, question, site, pillars, animals, human, order, more, cta)
4. render11.py 4 parça → birleştir → stamp_metadata
5. Kapak + paylaşım metinleri

## Doğrulanan bilgiler
- Yaş: ~11.500 yıl (MÖ ~9600); Büyük Piramit MÖ ~2560 → ~7.000 yıl fark.
- Merkez dikilitaşlar ~5,5 m (18 ft); ağırlık kaynaklarda 8–16 ton → "tonlarca".
- Kabartmalar: tilki, yaban domuzu, akrep, akbaba; bazı dikilitaşlarda kol/el/kemer kabartması (insan figürü yorumu).
- 1994 Klaus Schmidt; 2018 UNESCO Dünya Mirası.
- "Önce tapınak sonra tarım" Schmidt'in yorumu; bugünkü kazı ekibi yerleşim olarak yorumluyor → videoda "olabilir".
- Jeofizik taramalar: en az 200 dikilitaş daha toprağın altında.
- Kesit/sahne çizimleri temsilidir.

## Yeni keşif kontrolü (26.11.2026)
- Eylül 2025: duvara gömülü gerçek boyutlu insan heykeli bulundu (Bakan Ersoy). Ekim 2025: yer altı taramaları höyüğün doğu/güneyinde dörtgen konut izleri gösterdi. 2026: kazı ilk kez kuzey kesimde.
- Etkisi: "önce tapınak" yorumu tartışmalı → metindeki "olabilir" ifadesi korunuyor. "ne tarlası" doğru (yabani tahıl işlendi, evcil tarım yok).
- "en az iki yüz dikilitaş" jeofizik tahmin; mutlak ifade yok.

## Tamamlandı (26.11.2026)
- Ses: Emrullah, eleven_v4, tek versiyon (kullanıcının ikinci ElevenLabs hesabında web arayüzünden üretildi, mp3 olarak yüklendi) → EQ (voice_eq.txt) → `gobeklitepe-shorts.mp4`.
- Ses seviyesi: iki geçişli loudnorm → ~−14 LUFS, TP ≤ −1,1 dBTP (make_audio artık iki geçişli).
- Altyazı-ses senkronu (bitmiş videonun sesi Whisper ile yeniden ölçüldü): ortalama sapma +4 ms, 150 ms üstü sapma yok.
- Kapaklar: `kapak-dikey.jpg` (1080x1920), `kapak-yatay.jpg` (1280x720) – betik `kapak9.py` (+ harita-motoru/kapak_ortak.py).
- Paylaşım metinleri: `paylasim-bilgileri.md`.
- Düzeltmeler: (1) Yeni Pillow'da taş yükselme anında ters dikdörtgen hatası → korumalı. (2) "PİRAMİTLERDEN" vurgu kutusu beyaz-üstüne-beyazdı (görünmüyordu) → açık renkli kutularda siyah yazı (sum(bg) > 500, 10/11 ile aynı kural).
