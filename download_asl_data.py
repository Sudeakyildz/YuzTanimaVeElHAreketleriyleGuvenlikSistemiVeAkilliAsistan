import os
import requests
import zipfile
import json
import numpy as np
from PIL import Image
import cv2
import mediapipe as mp
from tqdm import tqdm

def download_asl_dataset():
    """ASL alphabet veri setini indir"""
    print("ASL alphabet veri seti indiriliyor...")
    
    # ASL dataset URL (Kaggle'dan)
    url = "https://storage.googleapis.com/kaggle-datasets-images/12/19/asl-alphabet/asl-alphabet.zip"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open("asl-alphabet.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Veri seti indirildi!")
        
        # ZIP dosyasını çıkart
        with zipfile.ZipFile("asl-alphabet.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_asl")
        
        print("ZIP dosyası çıkartıldı!")
        
    except Exception as e:
        print(f"İndirme hatası: {e}")
        return False
    
    return True

def process_asl_images():
    """ASL görüntülerini işle ve el hareketi verilerine dönüştür"""
    print("ASL görüntüleri işleniyor...")
    
    # MediaPipe el tanıma
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.7
    )
    
    # El hareketi eşleştirmeleri (ASL harfleri -> bizim hareketlerimiz)
    asl_to_gesture = {
        'A': 'yumruk',                      # Kapalı yumruk
        'B': 'el_acik',                     # Beş parmak açık
        'C': 'pinch',                       # C şekli
        'D': 'isaret_parmagi_yukari',       # İşaret parmağı yukarı
        'E': 'yumruk_basparmak_icte',       # Yumruk, başparmak içte
        'F': 'ok_isareti',                  # Başparmak ve işaret O yapıyor
        'G': 'isaret_parmagi_yana',         # İşaret parmağı yana
        'H': 'iki_parmak_yana',             # İşaret ve orta parmak yana
        'I': 'serce_yukari',                # Sadece serçe yukarı
        'J': 'serce_yukari',                # Serçe yukarı, havada J çizer
        'K': 'iki_parmak_yukari',           # İşaret ve orta yukarı, başparmak yana
        'L': 'l_isareti',                   # L şekli
        'M': 'uc_parmak_icte',              # Üç parmak başparmak altında
        'N': 'iki_parmak_icte',             # İki parmak başparmak altında
        'O': 'o_isareti',                   # Parmaklar yuvarlak, O şekli
        'P': 'iki_parmak_asagi',            # İşaret ve orta parmak aşağı
        'Q': 'basparmak_asagi',             # Başparmak ve işaret aşağı
        'R': 'capraz_parmak',               # İşaret ve orta parmak çapraz
        'S': 'yumruk',                      # Kapalı yumruk
        'T': 'basparmak_isaret_arasi',      # Başparmak işaret arası
        'U': 'iki_parmak_yukari',           # İşaret ve orta yukarı
        'V': 'victory',                     # V şekli
        'W': 'uc_parmak_yukari',            # Üç parmak yukarı
        'X': 'kivrilmis_isaret',            # İşaret parmağı kıvrık
        'Y': 'basparmak_serce_yana',        # Başparmak ve serçe yana
        'Z': 'isaret_parmagi_z_ciziyor'     # İşaret parmağı havada Z çizer
    }
    
    # Kişi eşleştirmeleri (ASL harfleri -> kişilerimiz)
    asl_to_person = {
        'A': 'ataturk',
        'B': 'cemyilmaz', 
        'C': 'centralcee',
        'D': 'esterexposite',
        'E': 'lebronjames',
        'F': 'ricardoquaresma',
        'G': 'stephencurry',
        'H': 'sude',
        
    }
    
    # data/hands klasörünü oluştur
    if not os.path.exists("data/hands"):
        os.makedirs("data/hands")
    
    processed_count = 0
    
    # ASL klasörlerini tara
    asl_dir = "temp_asl/asl_alphabet_train"
    if os.path.exists(asl_dir):
        for letter in os.listdir(asl_dir):
            letter_dir = os.path.join(asl_dir, letter)
            if os.path.isdir(letter_dir) and letter in asl_to_gesture:
                
                gesture = asl_to_gesture[letter]
                person = asl_to_person[letter]
                
                # Kişi ve hareket klasörlerini oluştur
                person_dir = os.path.join("data/hands", person)
                gesture_dir = os.path.join(person_dir, gesture)
                
                if not os.path.exists(person_dir):
                    os.makedirs(person_dir)
                if not os.path.exists(gesture_dir):
                    os.makedirs(gesture_dir)
                
                # Görüntüleri işle
                image_files = [f for f in os.listdir(letter_dir) if f.endswith(('.jpg', '.png'))]
                
                for i, img_file in enumerate(tqdm(image_files[:10], desc=f"İşleniyor: {letter}")):  # Her harften 10 örnek
                    img_path = os.path.join(letter_dir, img_file)
                    
                    try:
                        # Görüntüyü yükle
                        image = cv2.imread(img_path)
                        if image is None:
                            continue
                        
                        # RGB'ye çevir
                        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        
                        # El tespit et
                        results = hands.process(rgb_image)
                        
                        if results.multi_hand_landmarks:
                            for hand_landmarks in results.multi_hand_landmarks:
                                # El özelliklerini çıkar
                                features = []
                                for landmark in hand_landmarks.landmark:
                                    features.extend([landmark.x, landmark.y, landmark.z])
                                
                                # JSON dosyası olarak kaydet
                                timestamp = f"asl_{letter}_{i:03d}"
                                filename = f"{person}_{gesture}_{timestamp}.json"
                                filepath = os.path.join(gesture_dir, filename)
                                
                                data = {
                                    "person": person,
                                    "gesture": gesture,
                                    "features": features,
                                    "timestamp": timestamp,
                                    "source": "asl_dataset"
                                }
                                
                                with open(filepath, 'w') as f:
                                    json.dump(data, f)
                                
                                processed_count += 1
                                break  # Sadece ilk eli al
                    
                    except Exception as e:
                        print(f"Hata: {img_path} - {e}")
                        continue
    
    hands.close()
    print(f"Toplam {processed_count} el hareketi verisi oluşturuldu!")
    return processed_count

def cleanup():
    """Geçici dosyaları temizle"""
    import shutil
    
    if os.path.exists("asl-alphabet.zip"):
        os.remove("asl-alphabet.zip")
    
    if os.path.exists("temp_asl"):
        shutil.rmtree("temp_asl")
    
    print("Geçici dosyalar temizlendi!")

if __name__ == "__main__":
    print("ASL Alphabet veri setinden el hareketi verileri oluşturuluyor...")
    
    # Veri setini indir
    if download_asl_dataset():
        # Görüntüleri işle
        count = process_asl_images()
        
        if count > 0:
            print(f"✅ Başarılı! {count} el hareketi verisi oluşturuldu.")
            print("Şimdi modeli eğitebilirsiniz: python face_hand_recognition.py")
        else:
            print("❌ Veri işleme başarısız!")
    
    # Temizlik
    cleanup() 