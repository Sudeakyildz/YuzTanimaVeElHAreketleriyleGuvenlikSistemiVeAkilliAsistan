# Yüz Tanıma ve El Hareketi Tanıma Sistemi

Bu proje, yüz tanıma, el hareketi tanıma ve sesli asistan özelliklerini birleştiren kapsamlı bir güvenlik sistemi içerir.

## Özellikler

1. **Yüz Tanıma Sistemi**
   - Yüz veri seti oluşturma
   - Gerçek zamanlı yüz tanıma
   - 5 saniye doğrulama süreci

2. **El Hareketi Tanıma Sistemi**
   - El hareketi veri seti oluşturma
   - MediaPipe ile el hareketi algılama
   - Özel el hareketi tanıma

3. **Sesli Asistan**
   - Sesli komut algılama
   - Metin-ses dönüşümü
   - Doğal dil işleme

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

1. `python face_data_collection.py` - Yüz veri seti oluşturma
2. `python hand_data_collection.py` - El hareketi veri seti oluşturma
3. `python voice_data_collection.py` - Sesli asistan veri seti oluşturma
4. `python main_system.py` - Ana sistem çalıştırma

## Proje Yapısı

```
├── face_data_collection.py      # Yüz veri toplama
├── hand_data_collection.py      # El hareketi veri toplama
├── voice_data_collection.py     # Sesli asistan veri toplama
├── face_hand_recognition.py     # Yüz ve el hareketi tanıma
├── main_system.py               # Ana sistem
├── voice_assistant.py           # Sesli asistan
├── data/                        # Veri setleri
│   ├── faces/                   # Yüz fotoğrafları
│   ├── hands/                   # El hareketi verileri
│   └── voice/                   # Sesli komutlar
└── models/                      # Eğitilmiş modeller
``` 