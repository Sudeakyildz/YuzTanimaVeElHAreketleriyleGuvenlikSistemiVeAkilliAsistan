import os
import cv2
import mediapipe as mp
import json
from tqdm import tqdm

# Klasörler
ASL_DIR = 'asl_alphabet_train'
OUT_DIR = 'data/hands'

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1)

os.makedirs(OUT_DIR, exist_ok=True)

# Her harf klasörü için
for letter in tqdm(os.listdir(ASL_DIR)):
    letter_dir = os.path.join(ASL_DIR, letter)
    if not os.path.isdir(letter_dir):
        continue
    out_letter_dir = os.path.join(OUT_DIR, letter)
    os.makedirs(out_letter_dir, exist_ok=True)
    # Her resim için
    for img_name in os.listdir(letter_dir):
        if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        img_path = os.path.join(letter_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.extend([lm.x, lm.y, lm.z])
                # JSON olarak kaydet
                out_json = os.path.join(out_letter_dir, img_name.replace('.jpg', '.json').replace('.jpeg', '.json').replace('.png', '.json'))
                with open(out_json, 'w') as f:
                    json.dump({
                        'features': landmarks,
                        'gesture': letter
                    }, f)
                break # Sadece ilk el

hands.close()
print('ASL el landmark verileri çıkarıldı ve kaydedildi.') 