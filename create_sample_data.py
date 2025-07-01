import os
import json
import numpy as np
from datetime import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

def create_sample_hand_data():
    """Örnek el hareketi verileri oluştur"""
    print("Örnek el hareketi verileri oluşturuluyor...")
    
    # Kişi-hareket eşleştirmeleri (ASL harflerinin gerçek el işaretlerine göre)
    person_gestures = {
        "ataturk": "yumruk",                    # A - Yumruk (kapalı el)
        "cemyilmaz": "el_acik",                 # B - El açık (beş parmak açık)
        "centralcee": "pinch",                  # C - C şekli (başparmak ve işaret yuvarlak)
        "esterexposite": "isaret_parmagi_yukari", # D - İşaret parmağı yukarı
        "lebronjames": "yumruk_basparmak_icte", # E - Yumruk, başparmak içte
        "ricardoquaresma": "ok_isareti",        # F - OK işareti (başparmak ve işaret O)
        "stephencurry": "isaret_parmagi_yana",  # G - İşaret parmağı yana
        "sude": "iki_parmak_yana",              # H - İki parmak yana (işaret ve orta)
        
    }
    
    # Her hareket için gerçekçi özellik vektörleri (21 landmark * 3 koordinat = 63 değer)
    gesture_features = {
        "yumruk": [
            # Başparmak (0-3)
            0.1, 0.2, 0.0,  # 0: Başparmak tabanı
            0.15, 0.25, 0.0,  # 1: Başparmak 1. eklem
            0.2, 0.3, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.35, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - kapalı
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.15, 0.0, # 5: İşaret 1. eklem
            0.4, 0.1, 0.0,   # 6: İşaret 2. eklem
            0.45, 0.05, 0.0, # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "el_acik": [
            # Başparmak (0-3) - açık
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.15, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.1, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.05, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - açık
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.1, 0.0,  # 5: İşaret 1. eklem
            0.4, 0.05, 0.0,  # 6: İşaret 2. eklem
            0.45, 0.0, 0.0,  # 7: İşaret ucu
            # Orta parmak (8-11) - açık
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.1, 0.0,  # 9: Orta 1. eklem
            0.5, 0.05, 0.0,  # 10: Orta 2. eklem
            0.55, 0.0, 0.0,  # 11: Orta ucu
            # Yüzük parmağı (12-15) - açık
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.1, 0.0,  # 13: Yüzük 1. eklem
            0.6, 0.05, 0.0,  # 14: Yüzük 2. eklem
            0.65, 0.0, 0.0,  # 15: Yüzük ucu
            # Serçe (16-19) - açık
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.1, 0.0,  # 17: Serçe 1. eklem
            0.7, 0.05, 0.0,  # 18: Serçe 2. eklem
            0.75, 0.0, 0.0,  # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "iki_parmak_yana": [
            # Başparmak (0-3) - kapalı
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.25, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.3, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.35, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - açık
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.1, 0.0,  # 5: İşaret 1. eklem
            0.4, 0.05, 0.0,  # 6: İşaret 2. eklem
            0.45, 0.0, 0.0,  # 7: İşaret ucu
            # Orta parmak (8-11) - açık
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.1, 0.0,  # 9: Orta 1. eklem
            0.5, 0.05, 0.0,  # 10: Orta 2. eklem
            0.55, 0.0, 0.0,  # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "isaret_parmagi_yukari": [
            # Başparmak (0-3) - kapalı
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.25, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.3, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.35, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - yukarı
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.1, 0.0,  # 5: İşaret 1. eklem
            0.4, 0.0, 0.0,   # 6: İşaret 2. eklem
            0.45, -0.1, 0.0, # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "ok_isareti": [
            # Başparmak (0-3) - açık
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.15, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.1, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.05, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - açık
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.1, 0.0,  # 5: İşaret 1. eklem
            0.4, 0.05, 0.0,  # 6: İşaret 2. eklem
            0.45, 0.0, 0.0,  # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "pinch": [
            # Başparmak (0-3) - açık
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.15, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.1, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.05, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - açık
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.1, 0.0,  # 5: İşaret 1. eklem
            0.4, 0.05, 0.0,  # 6: İşaret 2. eklem
            0.45, 0.0, 0.0,  # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "yumruk_basparmak_icte": [
            # Başparmak (0-3) - içte
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.12, 0.25, 0.0, # 1: Başparmak 1. eklem
            0.14, 0.3, 0.0,  # 2: Başparmak 2. eklem
            0.16, 0.35, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - kapalı
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.35, 0.15, 0.0, # 5: İşaret 1. eklem
            0.4, 0.1, 0.0,   # 6: İşaret 2. eklem
            0.45, 0.05, 0.0, # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ],
        
        "isaret_parmagi_yana": [
            # Başparmak (0-3) - kapalı
            0.1, 0.2, 0.0,   # 0: Başparmak tabanı
            0.15, 0.25, 0.0, # 1: Başparmak 1. eklem
            0.2, 0.3, 0.0,   # 2: Başparmak 2. eklem
            0.25, 0.35, 0.0, # 3: Başparmak ucu
            # İşaret parmağı (4-7) - yana
            0.3, 0.2, 0.0,   # 4: İşaret tabanı
            0.4, 0.15, 0.0,  # 5: İşaret 1. eklem
            0.5, 0.1, 0.0,   # 6: İşaret 2. eklem
            0.6, 0.05, 0.0,  # 7: İşaret ucu
            # Orta parmak (8-11) - kapalı
            0.4, 0.2, 0.0,   # 8: Orta tabanı
            0.45, 0.15, 0.0, # 9: Orta 1. eklem
            0.5, 0.1, 0.0,   # 10: Orta 2. eklem
            0.55, 0.05, 0.0, # 11: Orta ucu
            # Yüzük parmağı (12-15) - kapalı
            0.5, 0.2, 0.0,   # 12: Yüzük tabanı
            0.55, 0.15, 0.0, # 13: Yüzük 1. eklem
            0.6, 0.1, 0.0,   # 14: Yüzük 2. eklem
            0.65, 0.05, 0.0, # 15: Yüzük ucu
            # Serçe (16-19) - kapalı
            0.6, 0.2, 0.0,   # 16: Serçe tabanı
            0.65, 0.15, 0.0, # 17: Serçe 1. eklem
            0.7, 0.1, 0.0,   # 18: Serçe 2. eklem
            0.75, 0.05, 0.0, # 19: Serçe ucu
            # El tabanı (20)
            0.2, 0.3, 0.0    # 20: El tabanı
        ]
        
        
    }
    
    # data/hands klasörünü oluştur
    if not os.path.exists("data/hands"):
        os.makedirs("data/hands")
    
    total_count = 0
    
    for person, gesture in person_gestures.items():
        print(f"Oluşturuluyor: {person} - {gesture}")
        
        # Kişi ve hareket klasörlerini oluştur
        person_dir = os.path.join("data/hands", person)
        gesture_dir = os.path.join(person_dir, gesture)
        
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        if not os.path.exists(gesture_dir):
            os.makedirs(gesture_dir)
        
        # Her kişi için 15 örnek oluştur
        base_features = gesture_features[gesture]
        
        for i in range(15):
            # Özellikleri biraz değiştir (gerçekçilik için)
            features = []
            for j, val in enumerate(base_features):
                # %10 rastgele değişim
                noise = np.random.normal(0, 0.01)
                features.append(val + noise)
            
            # JSON dosyası oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{person}_{gesture}_{timestamp}_{i:02d}.json"
            filepath = os.path.join(gesture_dir, filename)
            
            data = {
                "person": person,
                "gesture": gesture,
                "features": features,
                "timestamp": timestamp,
                "sample_id": i
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f)
            
            total_count += 1
    
    print(f"✅ Başarılı! {total_count} el hareketi verisi oluşturuldu.")
    print("Her kişi için 15 örnek oluşturuldu.")
    print("Şimdi modeli eğitebilirsiniz: python face_hand_recognition.py")
    
    return total_count

if __name__ == "__main__":
    create_sample_hand_data() 