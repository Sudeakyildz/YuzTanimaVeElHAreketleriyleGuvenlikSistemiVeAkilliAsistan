import speech_recognition as sr
import pyttsx3
import os
import json
import wave
import pyaudio
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time

class VoiceDataCollector:
    def __init__(self):
        self.data_dir = "data/voice"
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.record_seconds = 3
        
        # Ses tanıma ve sentezleme
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        
        # Türkçe ses ayarları
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'turkish' in voice.name.lower() or 'türkçe' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.setProperty('rate', 150)
        
        # Kayıt durumu
        self.is_recording = False
        self.current_command = ""
        self.current_person = ""
        self.recording_count = 0
        self.max_recordings = 20
        
        # Sesli komut türleri
        self.command_types = [
            "sistem_ac", "sistem_kapat", "nasilsin", "hava_durumu", 
            "saat_kac", "tarih", "muzik_cal", "ses_azalt", "ses_artir",
            "gorusuruz", "hoscakal", "tesekkurler", "evet", "hayir"
        ]
        
        # Klasörleri oluştur
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_gui(self):
        """Kullanıcı arayüzü oluştur"""
        self.root = tk.Tk()
        self.root.title("Sesli Asistan Veri Seti Oluşturucu")
        self.root.geometry("600x500")
        
        # Ana başlık
        title_label = tk.Label(self.root, text="Sesli Asistan Veri Seti Oluşturucu", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Kişi adı girişi
        person_frame = tk.Frame(self.root)
        person_frame.pack(pady=10)
        
        tk.Label(person_frame, text="Kişi Adı:").pack(side=tk.LEFT)
        self.person_entry = tk.Entry(person_frame, width=20)
        self.person_entry.pack(side=tk.LEFT, padx=5)
        
        # Komut seçimi
        command_frame = tk.Frame(self.root)
        command_frame.pack(pady=10)
        
        tk.Label(command_frame, text="Sesli Komut:").pack(side=tk.LEFT)
        self.command_var = tk.StringVar()
        self.command_combo = ttk.Combobox(command_frame, textvariable=self.command_var, 
                                        values=self.command_types, width=20)
        self.command_combo.pack(side=tk.LEFT, padx=5)
        self.command_combo.set("sistem_ac")
        
        # Özel komut girişi
        custom_frame = tk.Frame(self.root)
        custom_frame.pack(pady=5)
        
        tk.Label(custom_frame, text="Özel Komut:").pack(side=tk.LEFT)
        self.custom_command_entry = tk.Entry(custom_frame, width=30)
        self.custom_command_entry.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.record_button = tk.Button(button_frame, text="Kayıt Başlat", 
                                     command=self.start_recording, bg="green", fg="white")
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Kayıt Durdur", 
                                   command=self.stop_recording, bg="red", fg="white", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.test_button = tk.Button(button_frame, text="Test Et", 
                                   command=self.test_recognition, bg="blue", fg="white")
        self.test_button.pack(side=tk.LEFT, padx=5)
        
        # Durum bilgisi
        self.status_label = tk.Label(self.root, text="Hazır", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # İlerleme çubuğu
        self.progress_label = tk.Label(self.root, text="0 / " + str(self.max_recordings))
        self.progress_label.pack()
        
        # Kayıt listesi
        list_frame = tk.Frame(self.root)
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        tk.Label(list_frame, text="Kaydedilen Komutlar:").pack()
        
        self.recordings_listbox = tk.Listbox(list_frame, height=8)
        self.recordings_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Çıkış butonu
        exit_button = tk.Button(self.root, text="Çıkış", command=self.root.quit, bg="gray", fg="white")
        exit_button.pack(pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_recording(self):
        """Ses kaydını başlat"""
        person = self.person_entry.get().strip()
        command = self.command_var.get()
        custom_command = self.custom_command_entry.get().strip()
        
        if not person:
            messagebox.showerror("Hata", "Lütfen kişi adını girin!")
            return
        
        if custom_command:
            command = custom_command
        
        if not command:
            messagebox.showerror("Hata", "Lütfen komut seçin veya özel komut girin!")
            return
        
        self.current_person = person
        self.current_command = command
        self.is_recording = True
        
        # Klasörleri oluştur
        person_dir = os.path.join(self.data_dir, person)
        command_dir = os.path.join(person_dir, command)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        if not os.path.exists(command_dir):
            os.makedirs(command_dir)
        
        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Kayıt başladı: {command}")
        
        # Kayıt işlemini ayrı thread'de başlat
        threading.Thread(target=self.record_audio, daemon=True).start()
    
    def stop_recording(self):
        """Ses kaydını durdur"""
        self.is_recording = False
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Kayıt durduruldu")
    
    def record_audio(self):
        """Ses kaydı yap"""
        audio = pyaudio.PyAudio()
        
        stream = audio.open(format=self.audio_format,
                          channels=self.channels,
                          rate=self.rate,
                          input=True,
                          frames_per_buffer=self.chunk)
        
        frames = []
        
        # Geri sayım
        for i in range(3, 0, -1):
            self.root.after(0, lambda i=i: self.status_label.config(text=f"Kayıt başlıyor... {i}"))
            time.sleep(1)
        
        self.root.after(0, lambda: self.status_label.config(text="Kayıt yapılıyor..."))
        
        # Ses kaydı
        for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
            if not self.is_recording:
                break
            data = stream.read(self.chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        if self.is_recording and frames:
            # Ses dosyasını kaydet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{self.current_person}_{self.current_command}_{timestamp}.wav"
            filepath = os.path.join(self.data_dir, self.current_person, self.current_command, filename)
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            # Metadata kaydet
            metadata = {
                "person": self.current_person,
                "command": self.current_command,
                "filename": filename,
                "timestamp": timestamp,
                "duration": self.record_seconds,
                "sample_rate": self.rate,
                "channels": self.channels
            }
            
            metadata_path = filepath.replace('.wav', '.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.recording_count += 1
            self.root.after(0, self.update_progress)
            self.root.after(0, lambda: self.recordings_listbox.insert(0, f"{self.current_command} - {filename}"))
            
            print(f"Ses kaydedildi: {filename}")
            
            # Başarı mesajı
            self.root.after(0, lambda: messagebox.showinfo("Başarılı", f"Kayıt tamamlandı: {filename}"))
        
        self.root.after(0, lambda: self.status_label.config(text="Hazır"))
    
    def test_recognition(self):
        """Ses tanıma testi"""
        self.status_label.config(text="Ses tanıma testi başladı...")
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                self.status_label.config(text="Konuşun...")
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                self.status_label.config(text="Ses işleniyor...")
                
                # Google Speech Recognition kullan
                try:
                    text = self.recognizer.recognize_google(audio, language='tr-TR')
                    self.status_label.config(text=f"Tanınan: {text}")
                    
                    # Sesli geri bildirim
                    self.engine.say(f"Tanınan metin: {text}")
                    self.engine.runAndWait()
                    
                except sr.UnknownValueError:
                    self.status_label.config(text="Ses anlaşılamadı")
                    self.engine.say("Ses anlaşılamadı")
                    self.engine.runAndWait()
                    
                except sr.RequestError as e:
                    self.status_label.config(text=f"API hatası: {e}")
                    self.engine.say("API hatası oluştu")
                    self.engine.runAndWait()
                    
        except Exception as e:
            self.status_label.config(text=f"Test hatası: {e}")
    
    def update_progress(self):
        """İlerleme durumunu güncelle"""
        self.progress_label.config(text=f"{self.recording_count} / {self.max_recordings}")
    
    def on_closing(self):
        """Pencere kapatılırken temizlik yap"""
        self.stop_recording()
        self.root.destroy()
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        self.create_gui()
        self.root.mainloop()

if __name__ == "__main__":
    collector = VoiceDataCollector()
    collector.run() 