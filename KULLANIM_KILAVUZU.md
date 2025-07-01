# Yüz Tanıma ve El Hareketi Tanıma Sistemi - Kullanım Kılavuzu

## 🚀 Sistem Genel Bakış

Bu sistem, yüz tanıma, el hareketi tanıma ve sesli asistan özelliklerini birleştiren kapsamlı bir güvenlik sistemi içerir. Sistem şu şekilde çalışır:

1. **Yüz Tanıma**: Kamera açılır ve ekrandaki yüzü tanır
2. **5 Saniye Doğrulama**: Tanınan yüz 5 saniye boyunca doğrulanır
3. **El Hareketi Tanıma**: Yüz doğrulandıktan sonra el hareketi beklenir
4. **Sesli Asistan**: Giriş başarılı olduktan sonra sesli asistan devreye girer

## 📋 Gereksinimler

### Donanım Gereksinimleri
- Kamera (webcam)
- Mikrofon
- Hoparlör veya kulaklık

### Yazılım Gereksinimleri
- Python 3.8 veya üzeri
- Windows 10/11 (test edilmiş)

## 🔧 Kurulum

### 1. Python Kurulumu
Python'u [python.org](https://www.python.org/downloads/) adresinden indirin ve kurun.

### 2. Gerekli Kütüphaneleri Yükleme
Komut satırında proje dizinine gidin ve şu komutu çalıştırın:

```bash
pip install -r requirements.txt
```

### 3. Klasör Yapısı
Sistem otomatik olarak gerekli klasörleri oluşturacaktır:
```
proje/
├── data/
│   ├── faces/          # Yüz fotoğrafları
│   ├── hands/          # El hareketi verileri
│   └── voice/          # Sesli komutlar
├── models/             # Eğitilmiş modeller
└── [diğer dosyalar]
```

## 📚 Kullanım Adımları

### Adım 1: Yüz Veri Seti Oluşturma

1. **face_data_collection.py** dosyasını çalıştırın:
   ```bash
   python face_data_collection.py
   ```

2. Açılan arayüzde:
   - Kişi adını girin (örn: "ahmet")
   - "Veri Toplamayı Başlat" butonuna tıklayın
   - Kameraya bakın ve 's' tuşuna basarak fotoğraf çekin
   - En az 20-30 fotoğraf çekin
   - "Durdur" butonuna tıklayın

### Adım 2: El Hareketi Veri Seti Oluşturma

1. **hand_data_collection.py** dosyasını çalıştırın:
   ```bash
   python hand_data_collection.py
   ```

2. Açılan arayüzde:
   - Kişi adını girin (aynı kişi adı)
   - El hareketi türünü seçin (örn: "thumbs_up")
   - "Veri Toplamayı Başlat" butonuna tıklayın
   - El hareketini yapın ve 's' tuşuna basarak kaydedin
   - Her hareket için 50-100 örnek toplayın
   - Farklı hareketler için tekrarlayın

### Adım 3: Sesli Asistan Veri Seti Oluşturma (İsteğe Bağlı)

1. **voice_data_collection.py** dosyasını çalıştırın:
   ```bash
   python voice_data_collection.py
   ```

2. Açılan arayüzde:
   - Kişi adını girin
   - Komut türünü seçin veya özel komut girin
   - "Kayıt Başlat" butonuna tıklayın
   - Komutu sesli olarak söyleyin
   - Her komut için 10-20 kayıt yapın

### Adım 4: Ana Sistemi Çalıştırma

1. **main_system.py** dosyasını çalıştırın:
   ```bash
   python main_system.py
   ```

2. Açılan arayüzde:
   - "Sistemi Başlat" butonuna tıklayın
   - Kameraya bakın ve yüzünüzün tanınmasını bekleyin
   - 5 saniye boyunca yüzünüzü kamerada tutun
   - Yüz doğrulandıktan sonra el hareketinizi yapın
   - Sisteme giriş yapıldıktan sonra sesli asistan devreye girer

## 🎯 Sistem Çalışma Sırası

### 1. Yüz Tanıma Aşaması
- Kamera açılır
- Yüz tespit edilir ve yeşil çerçeve içine alınır
- Yüzün üstünde kişi adı görünür
- 5 saniye boyunca aynı yüz kamerada kalmalıdır

### 2. El Hareketi Aşaması
- Yüz doğrulandıktan sonra el hareketi beklenir
- El hareketi tespit edilir ve çizgilerle gösterilir
- Kişiye özel el hareketi yapılmalıdır
- Doğru hareket yapıldığında giriş başarılı olur

### 3. Sesli Asistan Aşaması
- "Hoş geldiniz [kişi adı]!" mesajı sesli olarak söylenir
- "Bu gün nasılsınız?" diyerek konuşma başlar
- Sesli komutlara yanıt verir
- "Görüşürüz" veya "Hoşçakal" denince sistem kapanır

## 🔧 Kişiye Özel Ayarlar

### El Hareketi Eşleştirmesi
Her kişi için farklı el hareketi tanımlanabilir. Bunun için `face_hand_recognition.py` dosyasındaki `person_gestures` sözlüğünü düzenleyin:

```python
person_gestures = {
    "ahmet": "thumbs_up",
    "ayse": "peace",
    "mehmet": "ok",
    # Yeni kişiler ekleyin
}
```

### Desteklenen El Hareketleri
- thumbs_up (başparmak yukarı)
- thumbs_down (başparmak aşağı)
- peace (barış işareti)
- ok (tamam işareti)
- fist (yumruk)
- open_hand (açık el)
- point (işaret etme)
- victory (zafer işareti)
- rock (taş)
- paper (kağıt)
- scissors (makas)

## 🎤 Sesli Asistan Komutları

### Temel Komutlar
- **"Sistem aç"** - Sistemi başlatır
- **"Sistem kapat"** - Sistemi kapatır
- **"Nasılsın"** - Asistanın durumunu sorar
- **"Saat kaç"** - Saati söyler
- **"Tarih"** - Tarihi söyler
- **"Teşekkürler"** - Teşekkür eder
- **"Görüşürüz"** - Sistemi kapatır

### Ek Komutlar
- **"Hava durumu"** - Hava durumu bilgisi (internet gerekli)
- **"Müzik çal"** - Müzik çalma (henüz aktif değil)
- **"Ses azalt/artır"** - Ses seviyesi kontrolü

## ⚠️ Sorun Giderme

### Yaygın Sorunlar

1. **Kamera açılmıyor**
   - Kameranın başka bir uygulama tarafından kullanılmadığından emin olun
   - Kamera izinlerini kontrol edin

2. **Yüz tanınmıyor**
   - Daha fazla yüz fotoğrafı ekleyin
   - Farklı açılardan fotoğraf çekin
   - İyi aydınlatma sağlayın

3. **El hareketi tanınmıyor**
   - Daha fazla el hareketi verisi toplayın
   - El hareketini net yapın
   - Kameraya yakın durun

4. **Sesli komut anlaşılmıyor**
   - Mikrofonun çalıştığından emin olun
   - Net ve yavaş konuşun
   - Gürültülü ortamlardan kaçının

### Hata Mesajları

- **"Yüz veri dizini bulunamadı"**: Önce yüz veri seti oluşturun
- **"El hareketi modeli bulunamadı"**: Önce el hareketi veri seti oluşturun
- **"Kamera açılamadı"**: Kamerayı kontrol edin

## 🔒 Güvenlik Notları

- Sistem sadece eğitildiği kişileri tanır
- El hareketi kişiye özeldir
- Sesli komutlar Türkçe olarak algılanır
- Sistem verileri yerel olarak saklanır

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. README.md dosyasını kontrol edin
2. Gerekli kütüphanelerin yüklü olduğundan emin olun
3. Kamera ve mikrofon izinlerini kontrol edin
4. Python sürümünüzün uyumlu olduğundan emin olun

## 🎉 Başarılı Kullanım İçin İpuçları

1. **İyi aydınlatma** kullanın
2. **Net el hareketleri** yapın
3. **Yavaş ve net konuşun**
4. **Düzenli veri toplama** yapın
5. **Sistemi düzenli olarak test edin**

---

**Not**: Bu sistem eğitim amaçlı geliştirilmiştir. Güvenlik uygulamalarında kullanmadan önce ek testler yapılması önerilir. 