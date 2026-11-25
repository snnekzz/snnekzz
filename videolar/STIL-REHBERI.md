# Bilinmeyenin Peşinde – Video Stil Rehberi

Her yeni videoda bu listeyi uygula. Kaynak: kendi deneyimlerimiz + Haritalogy kanalının incelenmesi.

## ✅ Görsel stil
- **Canlı uydu haritası:** parlak, doygun renkler (mavi okyanus, yeşil-kahverengi kara). Koyu/sisli harita kullanma.
- **Yükseltilmiş ülkeler:** vurgulanan ülke = canlı tek renk + **kalın beyaz kenar** + **altında gölge** (haritadan kalkmış gibi).
- **Ülke renkleri video boyunca sabit** (ör. Rusya kırmızı, Litvanya yeşil, Polonya lila).
- **Yuvarlak bayrak iğneleri** şehirlerin / ülkelerin üstünde.
- **Kırmızı isim etiketi** (beyaz kenarlı, hafif eğik) ana yer adı için.
- **Kavisli beyaz oklar** göç / hareket / bağlantı için.
- **Büyük gölgeli yıl sayıları** ve üstte zaman çizelgesi.
- **3D his:** dönen dünya küresiyle giriş, eğik drone kamera, ışık-gölge.
- **Hızlı yakınlaşmalarda zoom bulanıklığı** (hafif; yazıyı okunmaz yapmasın).

## ✅ Sade anlatım
- **Her an ekranda tek bir fikir.** Aynı anda en fazla 1 ana animasyon + 1 etiket.
- Etiketler **altyazıyla çakışmamalı** (altyazı alanı: ekranın ~%75'i hizası).
- Başlık kutusu sadece ilk 5–6 saniye.

## ✅ Ses
- Seslendirme: ElevenLabs, **Emrullah** (profesyonel Türkçe ses, `DpEiQMnL9WxMsymCsjPY`), model eleven_v4. Yenikapı'dan itibaren tüm videolarda bu ses.
- **Geçiş sesleri sadece yumuşak ve kısık:** tizleri kesilmiş "nefes" sesi. Whoosh/pop gibi keskin sesler YOK.
- Efektler konuşmanın çok altında; kritik anda kısa sessizlik + alçak "boom".
- Müzik: telifsiz, kodla üretilen drone/pad; konuşma sırasında otomatik kısılır.
- Ses seviyesi: -14 LUFS (YouTube standardı).

## ❌ Yapılan hatalar (tekrarlama)
- **Tahmini hizalama (DTW + karakter oranı):** hızlandırılmış seste altyazı ve sahneler sesle kaydı. Çözüm: Whisper ile ölçülmüş kelime zamanları.
- **Efektleri konuşma altında fazla kısmak (%65):** efektler ve geçiş sesi duyulmaz oldu. Doğru ayar: konuşma sırasında efektler ×0.8; yumuşak geçiş sesi konuşmanın ~6 dB altında, 140–1100 Hz bant.
- **Sesi kelime içinden kesmek** (Süleyman Şah, hızlandırılmış ses): sessizlik eklerken duraklama bulunamayınca ses kesildi → kesik kesik ses. Çözüm: `build_timing_safe.py` + efektleri konuşma altında otomatik kısma (`sfx_duck`).
- Ses hızlandırıldıktan sonra hizalamayı eski araçla yapmak → duraklamalar kısalır, mutlaka güvenli araç.
- Piper TTS → yabancı aksanlı Türkçe. Kullanma.
- Tam ekran bayrak dolguları → karışık görüntü.
- Yüksek geçiş efektleri → kulak tırmalıyor.
- Düz, karikatür harita → amatör görünüm.
- Ekrandan taşan altyazılar → satır kaydırma her zaman açık.
- Kanal adı önerirken sadece kullanıcı adını kontrol etmek → aynı isimli kanal da aranmalı.

## 📝 İş akışı
1. Senaryo (`script.py`): seslendirme metni (sayılar yazıyla) + ekran altyazısı (rakamlarla).
2. ElevenLabs'ta seslendirme → MP3.
3. **Hizalama = ölçüm:** `words.py` (Whisper, kelime zaman damgaları) → `build_timing_words.py`. Ses HİÇ kesilmez, sahne ve altyazılar söylenen kelimeye milisaniye hassasiyetle bağlanır. DTW/`build_timing3`/`build_timing_safe` KULLANMA.
4. Müzik/efekt (`make_audio*.py`).
5. Render (4 paralel parça) → birleştirme.
6. Kapak (dikey 1080×1920 + yatay 1280×720) + paylaşım metinleri.

## 🆕 Haritalogy analizinden eklenecekler
Ayrıntılar: `HARITALOGY-TEKNIKLERI.md`
- Türkiye ile boyut kıyaslaması ("≈2x Türkiye") – uygun her videoda
- Neon parıltılı ülke vurgusu (beyaz kenar + dış parıltı)
- Tarihî bölümlerde eski kâğıt harita zemini
- Sarı küçük etiket kutuları, ok zincirli yıllar (1912 → 1935), numaralı daireler
- Kapanış sorusu ekranda büyük yazıyla
- Kesit / boyut kıyası diyagramları

## 🆕 "Haritanın Ardı" analizinden eklenecekler
Ayrıntılar: `HARITANIN-ARDI-TEKNIKLERI.md`
- Altyazı: ekranın üstünde, küçük, tek satır; anahtar kelime renkli kutuda (harita ortada temiz kalsın)
- Marka açılış kartı (her videoda aynı tasarım)
- El yazısı kısa notlar + ok
- "Ya da" karşılaştırma kartları
- Yolculuk sayaçları (gün/saat/km)
- Yıllar serif yazıyla; kanal filigranı alt ortada
- Başlıkta somut şaşırtıcı sayı; Türkiye/Osmanlı + yolculuk konuları en çok izleniyor

## 🆕 Haritanın Ardı hareketli analizinden (25.11.2026) – ZORUNLU
Ayrıntılar: `HARITANIN-ARDI-TEKNIKLERI.md` bölüm 2
- **Renk = anlam:** altyazıdaki ülke/yer adı, haritada boyandığı renkte kutuda; sayılar SARI kutuda; diğer vurgular mavi.
- **Kanca:** gerçek+sayı → "Ama…" → "Peki neden…?" → "Cevap …" (ilk 7 sn). Kart: 4 kelimelik zıtlık ("İKİ KITA, SIFIR KÖPRÜ").
- **Ses 0,0 sn'de başlar**; hedef ~2,3 kelime/sn, cümle arası ~0,4 sn.
- **Görsel olay sıklığı:** her 1–1,5 sn'de yeni bir şey (boyama, iğne, sayaç, etiket, kamera hareketi).
- Canlı ölçüm sayacı, "?" simgesi, şerit + şerit boyunca kayan etiket, kıtayı beyazlatma, odak dışını karartma, daktilo etiket, kıyas uçuşu.
- Konuda Türkiye bağlantısı olmalı (yabancı konular onlarda da düşük izleniyor).

## 🎙️ Doğal ses kuralları (her videoda aynı tempo, AI havası yok)
**Tempo – otomatik:** `auto_tempo.py ham.mp3 eleven.mp3` → Whisper ile ölçer, **5,9 hece/sn** hedefine getirir.
- Sınır 0,95x–1,05x (fazlası yapay duyulur; Emrullah doğal olarak ~4,4 hece/sn, sakin anlatım – zorla hızlandırma); %2'den küçük farkta dokunmaz.
- Esnetme **rubberband** (formant korumalı). `atempo` ve göz kararı hızlandırma YASAK.
- Ölçülen geçmiş: Kaliningrad 5,29 · Sentinel 5,37 · Süleyman 5,70→6,36 (fazla) · İstiklal 6,02→6,54 (fazla). Hepsi hedefle 5,8–6,05'e iner.

**Senaryo yazımı (AI havasını en çok bu belirler):**
- Gereksiz virgül koyma: "örttü, ve", "Adı, Kaliningrad" gibi yerler yapay duraklama yaratır. Virgül sadece doğal nefes yerine.
- Kısa cümleler; her cümlede tek fikir. Uzun cümleyi ikiye böl.
- Konuşma dili bağlaçları: "Peki", "Üstelik", "Yani", "Ama asıl ilginç olan…".
- Sayılar yazıyla (seslendirme), rakamla (altyazı).
- Soru cümleleri gerçekten soru gibi kurulsun ("…mı?" ile bitsin).

**Ses işleme:** Kesme/sessizlik ekleme yok; -14 LUFS.
- **Emrullah EQ (zorunlu):** ham çıktı boğuk/odada gibi ("banyo yankısı") geliyor → `uretim-araclari/voice_eq_emrullah.txt` zincirini uygula: 350 Hz kutu tınısı −4 dB, 3,2 kHz +2,5 dB, 6 kHz üstü +5 dB, hafif kapı (aralardaki oda kuyruğunu kısar).
- **Emrullah'ta hız esnetme YOK** (rubberband oyuk tını ekliyor). Doğal temposu ~4,4 hece/sn; senaryoyu kısa tut (~650 karakter ≈ 53 sn).
- Geçiş sesi kazancı .15 (aktif konuşmanın ~5,5 dB altı).
**ElevenLabs:** Emrullah sesi, eleven_v4, tek versiyon (~680 kredi / video).

## 🏷️ Marka ve koruma (HER videoda zorunlu)
Modül: `uretim-araclari/brand.py`
- **Açılış kartı:** `brand_card(img, t, "SATIR 1", "SATIR 2 (sarı)", t_end)` – kırmızı "BİLİNMEYENİN PEŞİNDE" etiketi + iki satır başlık (İstiklal Yolu'ndaki tasarım). İlk 5–8 saniye.
- **Gezinen filigran:** `watermark(img, t, TOTAL)` – kanal işareti (`uretim-araclari/isaret.png`) + @BilinmeyeninPesinde, 7 sn'de bir yumuşakça yer değiştirir (kırpması/silmesi zor).
- **Logo sistemi:** `kanal/logo/` – işaret = konum iğnesi + anahtar deliği. Renkler: Gece Mavisi #0A1222, Keşif Kırmızısı #E5243B, Bilinmeyen Altını #FFC94A, Parşömen #FBF7F0. Font: Montserrat 900/700. Profil fotoğrafı, YouTube banner'ı, kimlik sayfası `logo_pro.py` ile üretilir.
- **Dosya künyesi:** `stamp_metadata(giris, cikis, başlık)` – telif bilgisi MP4'e gömülür.
- Kaynak dosyalar (senaryo, kod, ham ses) GitHub'da tarih damgalı → sahiplik kanıtı.
