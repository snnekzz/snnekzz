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
- Seslendirme: ElevenLabs, aynı ses, Eleven Multilingual v2, Stability %40.
- **Geçiş sesleri sadece yumuşak ve kısık:** tizleri kesilmiş "nefes" sesi. Whoosh/pop gibi keskin sesler YOK.
- Efektler konuşmanın çok altında; kritik anda kısa sessizlik + alçak "boom".
- Müzik: telifsiz, kodla üretilen drone/pad; konuşma sırasında otomatik kısılır.
- Ses seviyesi: -14 LUFS (YouTube standardı).

## ❌ Yapılan hatalar (tekrarlama)
- Piper TTS → yabancı aksanlı Türkçe. Kullanma.
- Tam ekran bayrak dolguları → karışık görüntü.
- Yüksek geçiş efektleri → kulak tırmalıyor.
- Düz, karikatür harita → amatör görünüm.
- Ekrandan taşan altyazılar → satır kaydırma her zaman açık.
- Kanal adı önerirken sadece kullanıcı adını kontrol etmek → aynı isimli kanal da aranmalı.

## 📝 İş akışı
1. Senaryo (`script.py`): seslendirme metni (sayılar yazıyla) + ekran altyazısı (rakamlarla).
2. ElevenLabs'ta seslendirme → MP3.
3. DTW ile cümle hizalama (`dtw.py`, `build_timing3.py`), kritik anlara ek sessizlik.
4. Müzik/efekt (`make_audio*.py`).
5. Render (4 paralel parça) → birleştirme.
6. Kapak (dikey 1080×1920 + yatay 1280×720) + paylaşım metinleri.
