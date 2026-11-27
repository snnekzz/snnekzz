# Profesyonel Shorts Kontrol Listesi (her videoda zorunlu)

Bu liste STIL-REHBERI.md'nin üstündedir: her video yayından önce buradaki maddelerden geçer.
Dayanak: kendi Analytics verimiz (Mısır elde tutma grafiği: kayıp ilk 30 sn'de, sonra düz plato) + Shorts
üreticilerinin yaygın olarak kullandığı teknikler. "✔" = üretim hattımızda otomatik/standart.

## 1. Konu seçimi (senaryodan önce)
- [ ] **Tek cümlelik çelişki** var mı? ("En büyük gölde neredeyse hiç balık yok", "Deniz iki yöne akıyor").
- [ ] **Çözülmemiş gizem / "nasıl olur?"** hissi. Türkiye bağlantısı artı puan, zorunlu değil (1977 Sinyali ve Mary Celeste Türkiye'siz 1,2 B aldı).
- [ ] **Somut, şaşırtıcı bir sayı** (7.000 yıl, 85 m, Ren'in 10 katı).
- [ ] **Sonda bir "yok artık" anı** saklanabiliyor mu?
- [ ] **Seri içinde mi?** ("Türkiye'nin Gizemli Suları" vb.) – abone olmak için sebep verir.
- [ ] **Güncel bağ:** Haberde/gündemde olan bir konuysa 24–48 saat içinde çık.
- [ ] Doğrulama + "yeni keşif / son yıllar" araması + mutlak ifade kontrolü ("tek, sadece, hiç") ✔

## 2. Kanca (0–3 sn) – en kritik bölüm
- [ ] **İlk kelime 0,05 sn'de** (sessiz giriş, logo, selam YOK) ✔
- [ ] **İlk cümle = en şaşırtıcı gerçek + sayı.** Bağlam sonra gelir.
- [ ] Kanca türlerinden biri seçildi:
  - **Çelişki:** "Türkiye'nin en büyük gölünde neredeyse hiç balık yok."
  - **Soru:** "Mısır'ın sınırları neden cetvelle çizilmiş gibi?"
  - **Sen-hitabı:** "Şu an izlediğin bu video denizin dibinden geçerek geldi."
  - **Yasak / tehlike:** "Bu adaya gidersen geri dönemezsin."
  - **Ölçek şoku:** "Bu kablo Singapur'dan Fransa'ya uzanıyor."
- [ ] **İlk karede görsel olay** (soru işareti, sayaç, parlayan sınır) – boş harita ile açılmaz.
- [ ] **Kapak = ilk kare = ilk cümle** aynı soruyu sorar (görsel-sözel tutarlılık).
- [ ] İlk 3 sn'de konu adı ekranda (izleyici neyi izlediğini anlar).

## 3. Elde tutma (3 sn → son)
- [ ] **Açık döngü (open loop):** İlk 5 sn'de bir soru aç ("Peki neden?"), cevabı en az 10 sn sonra ver.
- [ ] **Orta noktada yeniden kanca:** Videonun ~yarısında ikinci merak cümlesi ("Asıl şaşırtıcı olan şu…", "Ama hikâye burada bitmiyor").
- [ ] **Her ~1–1,5 sn'de bir görsel değişim** (kamera hareketi, etiket, sayaç, kesit, ok) – donuk kare yok ✔
- [ ] **Desen kırıcı (pattern interrupt):** En az 2 kez sahne türü değişsin (harita → kesit → sayaç → harita).
- [ ] **Ölü an yok:** 2 sn'den uzun "hiçbir şey olmayan" an kalmaz (Boğaz'da 31–34 sn düzeltildi).
- [ ] **Kelime kelime altyazı + renk = anlam** (anahtar kelime haritadaki rengiyle) ✔
- [ ] **Somut karşılaştırma:** soyut sayıyı tanıdık şeye bağla ("28 katlı bina", "bahçe hortumu", "Ren'in 10 katı").
- [ ] **Süre 40–50 sn**, seslendirme ~700–800 karakter. 60 sn'yi geçme.
- [ ] Animasyon tetikleri: cue() kelime içinde arar → 2 harfli iğne ("en", "on") kullanma; tetik kelimesinin sahnede tek geçtiğini kontrol et.
- [ ] Gereksiz cümle avı: her cümle ya bilgi ya merak eklemeli; ikisini de eklemeyen cümle silinir.

## 4. Kapanış ve döngü
- [ ] **"Yok artık" anı sondan bir önceki cümlede** (en güçlü bilgi en sonda).
- [ ] **CTA tek cümle ve soru biçiminde** ("Sence … mi, … mi? Yorumlara yaz!") – iki seçenekli sorular daha çok yorum alır.
- [ ] **Döngü sonu (loop):** Son cümle/son kare videonun başına bağlanır; izleyici fark etmeden başa döner (tekrar izleme oranı ↑). Örnek: son kare = ilk kare, ya da son cümle ilk cümleyi tamamlar.
- [ ] Kapanış ≤ 3 sn; sondaki "yorumlara yaz" kartından sonra uzatma yok.
- [ ] Seri videolarında son cümlede bir sonraki bölüme işaret ("Serinin devamında: Karadeniz'in dibindeki ölü bölge").

## 5. Ses
- [ ] Emrullah, eleven_v4, tek versiyon, `[energetic, fast-paced documentary narration]` ✔
- [ ] EQ (voice_eq.txt), iki geçişli −14 LUFS, TP ≤ −1,5 dBTP (AAC sonrası; `ln2.py … -2.2`) ✔
- [ ] Kritik anda kısa vurgu ("thud") + yumuşak geçiş sesleri, konuşmanın ~6 dB altında ✔
- [ ] Tempo esnetme yok; hız senaryo kısaltılarak ayarlanır ✔

## 6. Kapak ve başlık
- [ ] **Kapak:** en fazla 3–5 kelime büyük yazı + tek soru/çelişki; üstte kırmızı konu etiketi; altta el yazısı ipucu ✔
- [ ] Kapak yazısı telefonda küçük boyutta okunabiliyor mu (kapak ~%30 küçültülüp kontrol edilir).
- [ ] **Başlık:** merak + somut sayı + konu adı, ≤ 60 karakter görünür kısım; sonunda tek emoji + #shorts.
- [ ] Başlıkta ana arama kelimesi (Nemrut, Van Gölü, İstanbul Boğazı) ilk 40 karakterde.
- [ ] 2 alternatif başlık hazır; 48 saatte izlemeyi seçenler < %60 ise başlık değiştirilir.

## 7. Yayın
- [ ] **Haftada 2 video, sabit günler, 19:00.**
- [ ] Yapay zeka bildirimi: **Evet** (yapay ses kullanıyoruz).
- [ ] Açıklama: ilk satır = kanca cümlesi; maddeler emoji ile; kaynak notu; 5–6 hashtag.
- [ ] **İlgili video** bağlantısı: konu olarak en yakın eski videomuz (Nemrut → Van Gölü).
- [ ] **Sabit yorum:** soru + "en iyi yorumu sabitleyeceğim" ✔
- [ ] İlk 1 saatte gelen yorumlara cevap (algoritma etkileşimi ilk saatlerde ölçer).
- [ ] Eski popüler videoya yeni videoyu öneren bir yorum (Van'a "cevabı Nemrut'ta").
- [ ] Videolar oynatma listesine eklenir (seri adıyla).

## 8. Ölçüm (yayından 48 saat sonra)
- [ ] İzlemeyi seçenler (viewed vs swiped away): hedef ≥ %70; < %60 → kanca/kapak/başlık zayıf.
- [ ] Ortalama izleme yüzdesi: hedef ≥ %80 (Mısır: %63,4); grafikte en sert düşüş saniyesi not edilir.
- [ ] Abone kazanımı / 1.000 izlenme (şu an ~2) not edilir.
- [ ] Sonuç YOL-HARITASI.md → Ölçüm kayıtları tablosuna yazılır; en iyi konunun devamı hemen planlanır.
