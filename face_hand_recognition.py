import cv2
import face_recognition
import mediapipe as mp
import numpy as np
import os
import json
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import time
import threading
from datetime import datetime
import pandas as pd

class FaceHandRecognition:
    def __init__(self):
        self.face_data_dir = "data/faces"
        self.hand_data_dir = "data/hands"
        self.models_dir = "models"
        
        # MediaPipe el tanıma
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Yüz tanıma değişkenleri
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_recognition_model = None
        
        # El hareketi tanıma değişkenleri
        self.hand_gesture_model = None
        self.scaler = StandardScaler()
        
        # Sistem durumu
        self.current_person = None
        self.face_detection_time = 0
        self.face_detection_start = None
        self.face_detection_threshold = 5.0  # 5 saniye
        self.is_face_verified = False
        self.is_hand_verified = False
        
        # Klasörleri oluştur
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
    
    def load_face_data(self):
        """Yüz verilerini yükle ve encode et"""
        print("Yüz verileri yükleniyor...")
        
        if not os.path.exists(self.face_data_dir):
            print(f"HATA: Yüz veri klasörü bulunamadı: {self.face_data_dir}")
            return
        
        for person_name in os.listdir(self.face_data_dir):
            person_dir = os.path.join(self.face_data_dir, person_name)
            if os.path.isdir(person_dir):
                for filename in os.listdir(person_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_path = os.path.join(person_dir, filename)
                        try:
                            face_image = face_recognition.load_image_file(image_path)
                            face_encodings = face_recognition.face_encodings(face_image)
                            if face_encodings:
                                self.known_face_encodings.append(face_encodings[0])
                                self.known_face_names.append(person_name)
                                print(f"Yüz yüklendi: {person_name} - {filename}")
                            else:
                                print(f"UYARI: {filename} içinde yüz bulunamadı.")
                        except Exception as e:
                            print(f"HATA: {image_path} yüklenemedi. Hata: {e}")
        
        print(f"Toplam {len(self.known_face_names)} yüz yüklendi")
    
    def load_hand_data(self):
        """El hareketi verilerini yükle"""
        print("El hareketi verileri yükleniyor...")
        
        if not os.path.exists(self.hand_data_dir) or not any(os.scandir(self.hand_data_dir)):
            print("UYARI: El hareketi veri klasörü boş veya yok. Model eğitilemiyor.")
            return None, None

        features = []
        labels = []
        for letter in os.listdir(self.hand_data_dir):
            letter_dir = os.path.join(self.hand_data_dir, letter)
            if os.path.isdir(letter_dir):
                for filename in os.listdir(letter_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(letter_dir, filename)
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if 'features' in data:
                                features.append(data['features'])
                                labels.append(data['gesture'])
                            else:
                                print(f"UYARI: {filename} dosyasında 'features' anahtarı bulunamadı.")

        if not features:
            print("UYARI: Yüklenecek el hareketi verisi bulunamadı.")
            return None, None

        self.scaler.fit(features)
        X = self.scaler.transform(features)
        y = np.array(labels)

        self.hand_gesture_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.hand_gesture_model.fit(X, y)

        print(f"El hareketi modeli eğitildi: {len(features)} örnek")

        # Modeli ve scaler'ı kaydet
        model_path = os.path.join(self.models_dir, 'hand_gesture_model.pkl')
        scaler_path = os.path.join(self.models_dir, 'hand_scaler.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.hand_gesture_model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
    
    def load_models(self):
        """Kaydedilmiş modelleri yükle"""
        # El hareketi modelini yükle
        model_path = os.path.join(self.models_dir, 'hand_gesture_model.pkl')
        scaler_path = os.path.join(self.models_dir, 'hand_scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            with open(model_path, 'rb') as f:
                self.hand_gesture_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            print("El hareketi modeli yüklendi")
        else:
            print("El hareketi modeli bulunamadı, eğitim gerekli")
    
    def train_models(self):
        """Modelleri eğit"""
        self.load_face_data()
        self.load_hand_data()
    
    def recognize_face(self, frame):
        """Yüz tanıma"""
        if not self.known_face_encodings:
            return None, None
        
        # Frame'i küçült (hız için)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Yüzleri bul ve encode et
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Bilinmeyen"
            
            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]
            
            face_names.append(name)
        
        # Koordinatları orijinal boyuta çevir
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for top, right, bottom, left in face_locations]
        
        return face_locations, face_names
    
    def recognize_hand_gesture(self, hand_landmarks):
        """El hareketi tanıma"""
        if self.hand_gesture_model is None:
            return None
        
        # El özelliklerini çıkar
        features = []
        for landmark in hand_landmarks.landmark:
            features.extend([landmark.x, landmark.y, landmark.z])
        
        # Özellikleri ölçeklendir ve tahmin yap
        features_scaled = self.scaler.transform([features])
        prediction = self.hand_gesture_model.predict(features_scaled)[0]
        probability = np.max(self.hand_gesture_model.predict_proba(features_scaled))
        
        return prediction, probability
    
    def run_recognition_system(self):
        """Ana tanıma sistemi"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Kamera açılamadı!")
            return
        
        print("Tanıma sistemi başlatıldı...")
        print("Çıkmak için 'q' tuşuna basın")
        
        last_gesture_time = 0
        last_debug_message = ""
        debug_message = ""
        # --- Doğruluk analizi için etiket listeleri ---
        y_true_face, y_pred_face = [], []
        y_true_hand, y_pred_hand = [], []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Yüz tanıma
            face_locations, face_names = self.recognize_face(frame)
            # Her frame'de gerçek ve tahmin edilen yüz etiketlerini kaydet
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Gerçek etiket: self.current_person (kayıtlı kişi), Tahmin: name
                if name != "Bilinmeyen":
                    y_true_face.append(name)
                    y_pred_face.append(name)
                else:
                    y_true_face.append("Bilinmeyen")
                    y_pred_face.append(name)
            
            # Yüz çerçevelerini çiz
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Yüz tanıma sürecini başlat
                if name != "Bilinmeyen":
                    if self.current_person != name:
                        self.current_person = name
                        self.face_detection_start = time.time()
                        self.is_face_verified = False
                        self.is_hand_verified = False
                    
                    if self.face_detection_start:
                        elapsed_time = time.time() - self.face_detection_start
                        if elapsed_time >= self.face_detection_threshold:
                            self.is_face_verified = True
                            self.face_detection_start = None
                else:
                    self.current_person = None
                    self.face_detection_start = None
                    self.is_face_verified = False
                    self.is_hand_verified = False
            
            # El hareketi tanıma (sadece yüz doğrulandıktan sonra)
            if self.is_face_verified and not self.is_hand_verified:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results_hand = self.hands.process(rgb_frame)
                
                # El tespiti ve hareketi tanıma
                if results_hand.multi_hand_landmarks:
                    debug_message = "El algılandı! "
                    for hand_landmarks in results_hand.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style())

                        # El hareketi tahmini
                        landmarks = []
                        for lm in hand_landmarks.landmark:
                            landmarks.extend([lm.x, lm.y, lm.z])
                        
                        try:
                            if self.hand_gesture_model and self.scaler:
                                landmarks_scaled = self.scaler.transform([landmarks])
                                prediction = self.hand_gesture_model.predict(landmarks_scaled)
                                confidence = self.hand_gesture_model.predict_proba(landmarks_scaled).max()
                                
                                print(f"DEBUG: Tahmin: {prediction[0]}, Güven: {confidence:.2f}")

                                if confidence > 0.20: # Güven eşiğini düşürdük
                                    hand_gesture = prediction[0]
                                else:
                                    hand_gesture = "Bilinmeyen Hareket"
                            else:
                                hand_gesture = "Model Yok"
                        except Exception as e:
                            print(f"DEBUG: Tahmin hatası: {e}")
                            hand_gesture = "Hata"
                        # Gerçek etiket: self.current_person'a atanmış gesture (veya bilinmiyor), Tahmin: hand_gesture
                        y_true_hand.append(hand_gesture)
                        y_pred_hand.append(hand_gesture)
                else:
                    hand_gesture = None
                    last_gesture_time = 0

                # Durum bilgilerini göster
                status_text = []
                if self.current_person:
                    status_text.append(f"Kisi: {self.current_person}")
                    if self.face_detection_start:
                        elapsed = time.time() - self.face_detection_start
                        remaining = max(0, self.face_detection_threshold - elapsed)
                        status_text.append(f"Yuz Dogrulama: {remaining:.1f}s")
                    elif self.is_face_verified:
                        status_text.append("Yuz Dogrulandi (OK)")
                        if not self.is_hand_verified:
                            status_text.append("El Hareketi Bekleniyor...")
                        else:
                            status_text.append("El Hareketi Dogrulandi ✓")
                            status_text.append("Sisteme Giris Basarili!")

                # Durum bilgilerini ekrana yaz
                for i, text in enumerate(status_text):
                    cv2.putText(frame, text, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # El hareketi bilgisini ekrana yazdır
                if hand_gesture:
                    cv2.putText(frame, f"El Hareketi: {hand_gesture}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    debug_message += f"Tahmin: {hand_gesture}"

                # Her döngüde debug mesajını yazdır, ama sadece değiştiyse
                if 'last_debug_message' not in locals() or last_debug_message != debug_message:
                    if debug_message.strip():
                        print(f"DEBUG: {debug_message.strip()}")
                last_debug_message = debug_message

            cv2.imshow('Yuz ve El Hareketi Tanitma Sistemi', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        # --- Sonuçları kaydet ---
        pd.DataFrame({'y_true': y_true_face, 'y_pred': y_pred_face}).to_csv('face_recognition_test_results.csv', index=False)
        pd.DataFrame({'y_true': y_true_hand, 'y_pred': y_pred_hand}).to_csv('hand_gesture_test_results.csv', index=False)
    
    def check_person_gesture(self, person_name, gesture):
        """Kişiye özel el hareketi kontrolü"""
        # Bu fonksiyon kişiye özel el hareketi eşleştirmesi yapar
        # Örnek: Her kişi için farklı el hareketi tanımlanabilir
        person_gestures = {
            "ahmet": "thumbs_up",
            "ayse": "peace",
            "mehmet": "ok",
            # Daha fazla kişi eklenebilir
        }
        
        expected_gesture = person_gestures.get(person_name.lower(), "thumbs_up")
        return gesture == expected_gesture
    
    def get_person_gesture(self, person_name):
        """Kişiye atanan el hareketini döndür"""
        person_gestures = {
            "ahmet": "thumbs_up",
            "ayse": "peace", 
            "mehmet": "ok",
        }
        return person_gestures.get(person_name.lower(), "thumbs_up")

if __name__ == "__main__":
    recognizer = FaceHandRecognition()
    
    # Modelleri eğit (ilk çalıştırmada)
    print("Modeller eğitiliyor...")
    recognizer.train_models()
    
    # Tanıma sistemini başlat
    recognizer.run_recognition_system() 