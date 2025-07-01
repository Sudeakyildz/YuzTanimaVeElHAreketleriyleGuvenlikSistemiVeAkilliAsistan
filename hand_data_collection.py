import cv2
import mediapipe as mp
import numpy as np
import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class HandDataCollector:
    def __init__(self):
        self.data_dir = "data/hands"
        self.cap = None
        self.is_collecting = False
        self.current_gesture = ""
        self.gesture_count = 0
        self.max_gestures = 10
        
        # MediaPipe el tanıma
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # El hareketi türleri
        self.gesture_types = [
            "basparmak_yukari", "yumruk", "isaret_parmagi_yukari", "victory", 
            "el_acik", "yumruk_basparmak_icte", "rock_isareti", "ok_isareti", "pinch"
        ]
        
        # Klasörleri oluştur
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_gui(self):
        """Kullanıcı arayüzü oluştur"""
        self.root = tk.Tk()
        self.root.title("El Hareketi Veri Seti Oluşturucu")
        self.root.geometry("500x400")
        
        # Ana başlık
        title_label = tk.Label(self.root, text="El Hareketi Veri Seti Oluşturucu", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Hareket seçimi
        gesture_frame = tk.Frame(self.root)
        gesture_frame.pack(pady=10)
        
        tk.Label(gesture_frame, text="El Hareketi:").pack(side=tk.LEFT)
        self.gesture_var = tk.StringVar()
        self.gesture_combo = ttk.Combobox(gesture_frame, textvariable=self.gesture_var, 
                                        values=self.gesture_types, width=15)
        self.gesture_combo.pack(side=tk.LEFT, padx=5)
        self.gesture_combo.set("basparmak_yukari")
        
        # Kişi adı girişi
        person_frame = tk.Frame(self.root)
        person_frame.pack(pady=10)
        
        tk.Label(person_frame, text="Kişi Adı:").pack(side=tk.LEFT)
        self.person_entry = tk.Entry(person_frame, width=20)
        self.person_entry.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame, text="Veri Toplamayı Başlat", 
                                    command=self.start_collection, bg="green", fg="white")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Durdur", 
                                   command=self.stop_collection, bg="red", fg="white", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Durum bilgisi
        self.status_label = tk.Label(self.root, text="Hazır", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # İlerleme çubuğu
        self.progress_label = tk.Label(self.root, text="0 / " + str(self.max_gestures))
        self.progress_label.pack()
        
        # Otomatik kaydetme seçeneği
        self.auto_save_var = tk.BooleanVar()
        self.auto_save_check = tk.Checkbutton(self.root, text="Otomatik Kaydet (Her 2 saniyede)", 
                                            variable=self.auto_save_var)
        self.auto_save_check.pack(pady=5)
        
        # Çıkış butonu
        exit_button = tk.Button(self.root, text="Çıkış", command=self.root.quit, bg="gray", fg="white")
        exit_button.pack(pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_collection(self):
        """Veri toplamayı başlat"""
        gesture = self.gesture_var.get()
        person = self.person_entry.get().strip()
        
        if not gesture or not person:
            messagebox.showerror("Hata", "Lütfen el hareketi ve kişi adını seçin!")
            return
        
        self.current_gesture = gesture
        self.current_person = person
        self.gesture_count = 0
        self.is_collecting = True
        
        # Klasörleri oluştur
        person_dir = os.path.join(self.data_dir, person)
        gesture_dir = os.path.join(person_dir, gesture)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        if not os.path.exists(gesture_dir):
            os.makedirs(gesture_dir)
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"{person} için {gesture} hareketi toplanıyor...")
        
        # Kamerayı ayrı thread'de başlat
        threading.Thread(target=self.camera_loop, daemon=True).start()
    
    def stop_collection(self):
        """Veri toplamayı durdur"""
        self.is_collecting = False
        if self.cap:
            self.cap.release()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Veri toplama durduruldu")
        self.progress_label.config(text="0 / " + str(self.max_gestures))
    
    def extract_hand_features(self, hand_landmarks):
        """El landmark'larından özellik çıkar"""
        features = []
        for landmark in hand_landmarks.landmark:
            features.extend([landmark.x, landmark.y, landmark.z])
        return features
    
    def camera_loop(self):
        """Kamera döngüsü"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Hata", "Kamera açılamadı!")
            return
        
        last_save_time = 0
        
        while self.is_collecting and self.gesture_count < self.max_gestures:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # BGR'den RGB'ye çevir
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # El çizgilerini çiz
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # El özelliklerini çıkar
                    features = self.extract_hand_features(hand_landmarks)
                    
                    # Kaydetme koşulları
                    current_time = cv2.getTickCount() / cv2.getTickFrequency()
                    should_save = False
                    
                    if self.auto_save_var.get():
                        # Otomatik kaydetme (her 2 saniyede)
                        if current_time - last_save_time > 2.0:
                            should_save = True
                            last_save_time = current_time
                    else:
                        # Manuel kaydetme (s tuşu)
                        if cv2.waitKey(1) & 0xFF == ord('s'):
                            should_save = True
                    
                    if should_save and self.gesture_count < self.max_gestures:
                        # Veriyi kaydet
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"{self.current_person}_{self.current_gesture}_{timestamp}.json"
                        filepath = os.path.join(self.data_dir, self.current_person, 
                                              self.current_gesture, filename)
                        
                        # Özellikleri JSON olarak kaydet
                        data = {
                            "person": self.current_person,
                            "gesture": self.current_gesture,
                            "features": features,
                            "timestamp": timestamp
                        }
                        
                        with open(filepath, 'w') as f:
                            json.dump(data, f)
                        
                        self.gesture_count += 1
                        self.root.after(0, self.update_progress)
                        print(f"El hareketi kaydedildi: {filename}")
            
            # Bilgileri ekrana yaz
            cv2.putText(frame, f"Kişi: {self.current_person}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Hareket: {self.current_gesture}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Kaydedilen: {self.gesture_count}/{self.max_gestures}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if not self.auto_save_var.get():
                cv2.putText(frame, "Kaydetmek için 's' tuşuna basın", (10, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow('El Hareketi Veri Toplama', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        
        if self.gesture_count >= self.max_gestures:
            self.root.after(0, lambda: messagebox.showinfo("Tamamlandı", 
                f"{self.current_person} için {self.current_gesture} hareketinden {self.gesture_count} örnek kaydedildi!"))
    
    def update_progress(self):
        """İlerleme durumunu güncelle"""
        self.progress_label.config(text=f"{self.gesture_count} / {self.max_gestures}")
    
    def on_closing(self):
        """Pencere kapatılırken temizlik yap"""
        self.stop_collection()
        self.root.destroy()
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        self.create_gui()
        self.root.mainloop()

if __name__ == "__main__":
    collector = HandDataCollector()
    collector.run() 