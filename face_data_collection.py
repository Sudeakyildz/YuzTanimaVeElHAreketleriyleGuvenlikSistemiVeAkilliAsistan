import cv2
import os
import face_recognition
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading

class FaceDataCollector:
    def __init__(self):
        self.data_dir = "data/faces"
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.cap = None
        self.is_collecting = False
        self.current_person = ""
        self.face_count = 0
        self.max_faces = 10
        
        # Klasörleri oluştur
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_gui(self):
        """Kullanıcı arayüzü oluştur"""
        self.root = tk.Tk()
        self.root.title("Yüz Veri Seti Oluşturucu")
        self.root.geometry("400x300")
        
        # Ana başlık
        title_label = tk.Label(self.root, text="Yüz Veri Seti Oluşturucu", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Kişi adı girişi
        name_frame = tk.Frame(self.root)
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="Kişi Adı:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(name_frame, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        
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
        self.progress_label = tk.Label(self.root, text="0 / " + str(self.max_faces))
        self.progress_label.pack()
        
        # Çıkış butonu
        exit_button = tk.Button(self.root, text="Çıkış", command=self.root.quit, bg="gray", fg="white")
        exit_button.pack(pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_collection(self):
        """Veri toplamayı başlat"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Hata", "Lütfen kişi adını girin!")
            return
        
        self.current_person = name
        self.face_count = 0
        self.is_collecting = True
        
        # Kişi klasörünü oluştur
        person_dir = os.path.join(self.data_dir, name)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"{name} için veri toplama başladı...")
        
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
        self.progress_label.config(text="0 / " + str(self.max_faces))
    
    def camera_loop(self):
        """Kamera döngüsü"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Hata", "Kamera açılamadı!")
            return
        
        while self.is_collecting and self.face_count < self.max_faces:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Gri tonlamaya çevir
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Yüzleri tespit et
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Yüz çerçevesi çiz
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Yüz bölgesini al
                face_roi = gray[y:y+h, x:x+w]
                
                # Her 10 frame'de bir yüz kaydet
                if self.face_count < self.max_faces and cv2.waitKey(1) & 0xFF == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{self.current_person}_{timestamp}.jpg"
                    filepath = os.path.join(self.data_dir, self.current_person, filename)
                    
                    # Yüzü kaydet
                    cv2.imwrite(filepath, face_roi)
                    self.face_count += 1
                    
                    # GUI'yi güncelle
                    self.root.after(0, self.update_progress)
                    
                    print(f"Yüz kaydedildi: {filename}")
            
            # Bilgileri ekrana yaz
            cv2.putText(frame, f"Kişi: {self.current_person}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Kaydedilen: {self.face_count}/{self.max_faces}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Kaydetmek için 's' tuşuna basın", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow('Yüz Veri Toplama', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        
        if self.face_count >= self.max_faces:
            self.root.after(0, lambda: messagebox.showinfo("Tamamlandı", 
                f"{self.current_person} için {self.face_count} yüz fotoğrafı kaydedildi!"))
    
    def update_progress(self):
        """İlerleme durumunu güncelle"""
        self.progress_label.config(text=f"{self.face_count} / {self.max_faces}")
    
    def on_closing(self):
        """Pencere kapatılırken temizlik yap"""
        self.stop_collection()
        self.root.destroy()
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        self.create_gui()
        self.root.mainloop()

if __name__ == "__main__":
    collector = FaceDataCollector()
    collector.run() 