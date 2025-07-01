import cv2
import face_recognition
import mediapipe as mp
import numpy as np
import os
import json
import pickle
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import messagebox
import speech_recognition as sr
import pyttsx3
from datetime import datetime, timedelta
import requests
import webbrowser
from PIL import Image, ImageTk
import random
import re
import urllib.parse
import subprocess
import takvim_db
import signal
try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import ctypes
except ImportError:
    AudioUtilities = None
    IAudioEndpointVolume = None
    CLSCTX_ALL = None
    ctypes = None
try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
except ImportError:
    Model = None
    KaldiRecognizer = None
    sd = None
import matplotlib.pyplot as plt

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Tüm argümanları ascii'ye çevir, yazılamayan karakterleri sil
        def to_ascii(a):
            return str(a).encode('ascii', errors='ignore').decode('ascii')
        print(*(to_ascii(a) for a in args), **kwargs)

class MainSystem:
    def __init__(self):
        # Sistem durumu
        self.system_active = False
        self.current_user = None
        self.face_verified = False
        self.hand_verified = False
        self.voice_active = False
        
        # Zaman sayaçları
        self.face_detection_start = None
        self.face_detection_threshold = 5.0  # 5 saniye
        
        # MediaPipe el tanıma
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
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
        
        # Veri dizinleri
        self.face_data_dir = "data/faces"
        self.hand_data_dir = "data/hands"
        self.models_dir = "models"
        
        # Yüz tanıma değişkenleri
        self.known_face_encodings = []
        self.known_face_names = []
        
        # El hareketi tanıma değişkenleri
        self.hand_gesture_model = None
        self.scaler = None
        
        # Komut eşleştirmeleri
        self.commands = {
            
            "sistem_kapat": ["sistem kapat", "sistemi kapat", "kapat", "kapat"],
            "nasilsin": ["nasılsın", "nasılsınız", "iyi misin", "nasıl gidiyor"],
            "hava_durumu": ["hava durumu", "hava nasıl", "yağmur yağacak mı"],
            "saat_kac": ["saat kaç", "saat", "zaman"],
            "tarih": ["tarih", "bugün günlerden ne", "hangi gün"],
            "muzik_cal": ["müzik çal", "müzik aç", "şarkı çal"],
            "ses_azalt": ["sesi azalt", "ses azalt", "kıs"],
            "ses_artir": ["sesi artır", "ses artır", "aç"],
            "parlaklik_azalt": ["parlaklığı azalt", "ekranı karart", "ışığı azalt", "ekranı kıs"],
            "parlaklik_artir": ["parlaklığı artır", "ekranı aydınlat", "ışığı artır", "ekranı aç"],
            "gorusuruz": ["görüşürüz", "görüşmek üzere", "hoşça kal"],
            "hoscakal": ["hoşçakal", "hoşça kal", "güle güle"],
            "tesekkurler": ["teşekkürler", "teşekkür ederim", "sağol"],
            "evet": ["evet", "tamam", "olur"],
            "hayir": ["hayır", "yok", "olmaz"],
            "quote": "Hayat bir gündür, o da bugündür."
        }
        
        # Kural tabanlı komutlar ve anahtar kelimeleri
        self.command_rules = {
            "kapanis": ["kapat", "görüşürüz", "bay bay", "hoşça kal", "çıkış"],
            "volume_up": ["sesi aç", "sesi yükselt", "ses ver"],
            "volume_down": ["sesi kıs", "sesi azalt", "sessize al"],
            "turn_on_light": ["parlaklığı aç", "parlaklığı artır", "ışığı aç"],
            "turn_off_light": ["parlaklığı kıs", "parlaklığı azalt", "ışığı kıs", "ekranı karart"],
            "saat_kac": ["saat"],
            "hava_durumu": ["hava durumu", "hava nasıl"],
            "muzik_cal": ["müzik çal", "şarkı aç"],
            "stop_music": ["müziği durdur", "şarkıyı kapat"],
            "ask_joke": ["şaka yap", "fıkra anlat"],
            "ask_quote": ["güzel söz", "anlamlı bir söz", "motive et"]
        }
        
        # Yanıtlar - Etiketler kurallar ve modelle tutarlı olmalı
        self.responses = {
            
            "how_are_you": ["Harikayım, sorduğunuz için teşekkürler!", "Çok iyiyim, umarım siz de iyisinizdir."],
            "assistant_status": ["Komutlarınızı dinliyorum.", "Sizin için buradayım."],
            "user_feeling_happy": ["Bunu duyduğuma çok sevindim!", "Harika! Enerjiniz bana da yansıdı."],
            "user_feeling_tired": ["Anlıyorum. Biraz dinlenmek iyi gelebilir."],
            "who_are_you": ["Ben bir yapay zeka asistanım.", "Adım yok, ama görevim size yardımcı olmak."],
            "thanks": ["Rica ederim!", "Yardımcı olabildiğime sevindim."],
            "greeting": ["Merhaba!", "Selam, nasıl yardımcı olabilirim?"],
            # Kural tabanlı yanıtlar
            "kapanis": ["Görüşmek üzere!", "Hoşça kalın, yine beklerim."],
            "volume_up": "Sesi artırıyorum.",
            "volume_down": "Sesi azaltıyorum.",
            "turn_on_light": "Parlaklığı artırıyorum.",
            "turn_off_light": "Parlaklığı azaltıyorum.",
            "saat_kac": lambda: f"Saat şu an {datetime.now().strftime('%H:%M')}",
            "hava_durumu": "Hemen kontrol ediyorum...",
            "muzik_cal": "Ne tür bir müzik istersiniz?",
            "stop_music": "Müzik durduruluyor.",
            "ask_joke": [
                "Adamın biri yarın öleceğim demiş. Yarmışlar, ölmüş.",
                "Geçen gün taksi çevirdim, hala dönüyor."
            ],
            "ask_quote": [
                "Başarının sırrı, başlangıç yapmaktır.",
                "Düşünmeden öğrenmek, zaman kaybetmektir."
            ]
        }
        
        # Komut sınıflandırma modeli ve vektörizeri yükle
        try:
            with open('voice_command_model.pkl', 'rb') as f:
                self.voice_command_model = pickle.load(f)
            with open('voice_vectorizer.pkl', 'rb') as f:
                self.voice_vectorizer = pickle.load(f)
        except Exception as e:
            print(f"Komut modeli yüklenemedi: {e}")
            self.voice_command_model = None
            self.voice_vectorizer = None
        
        # Vosk modeli yükle
        self.vosk_model = None
        if Model is not None:
            model_path = './vosk-model-small-tr-0.3'
            if os.path.exists(model_path):
                self.vosk_model = Model(model_path)
        
        # Modelleri yükle
        self.load_models()
    
    def load_models(self):
        """Eğitilmiş modelleri yükle"""
        print("Modeller yükleniyor...")
        
        # Yüz verilerini yükle
        self.load_face_data()
        
        # El hareketi modelini yükle
        self.load_hand_model()
        
        print("Modeller yüklendi!")
    
    def load_face_data(self):
        """Yüz verilerini yükle"""
        if not os.path.exists(self.face_data_dir):
            print("Yüz veri dizini bulunamadı!")
            return
        
        for person_name in os.listdir(self.face_data_dir):
            person_dir = os.path.join(self.face_data_dir, person_name)
            if os.path.isdir(person_dir):
                image_files = [f for f in os.listdir(person_dir) if f.endswith('.jpg')]
                
                for i, image_file in enumerate(image_files[:3]):  # İlk 3 fotoğrafı al
                    image_path = os.path.join(person_dir, image_file)
                    try:
                        image = face_recognition.load_image_file(image_path)
                        face_encodings = face_recognition.face_encodings(image)
                        
                        if face_encodings:
                            self.known_face_encodings.append(face_encodings[0])
                            self.known_face_names.append(person_name)
                            print(f"Yüz yüklendi: {person_name}")
                    except Exception as e:
                        print(f"Yüz yükleme hatası: {e}")
    
    def load_hand_model(self):
        """El hareketi modelini yükle"""
        model_path = os.path.join(self.models_dir, 'hand_gesture_model.pkl')
        scaler_path = os.path.join(self.models_dir, 'hand_scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            with open(model_path, 'rb') as f:
                self.hand_gesture_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            print("El hareketi modeli yüklendi")
        else:
            print("El hareketi modeli bulunamadı!")
    
    def recognize_face(self, frame):
        """Yüz tanıma"""
        if not self.known_face_encodings:
            return None, None
        
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
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
        
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for top, right, bottom, left in face_locations]
        
        return face_locations, face_names
    
    def recognize_hand_gesture(self, hand_landmarks):
        """El hareketi tanıma"""
        if self.hand_gesture_model is None or self.scaler is None:
            return None, None
        
        features = []
        for landmark in hand_landmarks.landmark:
            features.extend([landmark.x, landmark.y, landmark.z])
        
        features_scaled = self.scaler.transform([features])
        prediction = self.hand_gesture_model.predict(features_scaled)[0]
        probability = np.max(self.hand_gesture_model.predict_proba(features_scaled))
        
        return prediction, probability
    
    def check_person_gesture(self, person_name, gesture):
        """Kişiye özel el hareketi kontrolü"""
        person_gestures = {
            "ataturk": "A",
            "cemyilmaz": "B",
            "centralcee": "C",
            "esterexposite": "D",
            "lebronjames": "E",
            "ricardoquaresma": "F",
            "stephencurry": "G",
            "sude": "H",
            "travisscott": "I",
        }
        expected_gesture = person_gestures.get(person_name.lower(), "A")
        # Karşılaştırmayı büyük harfe çevirerek yap
        return (gesture or "").upper() == expected_gesture.upper()
    
    def speak(self, text):
        """Metni sesli olarak söyle"""
        import sys
        try:
            # Unicode karakterleri doğrudan yazdırmak için
            sys.stdout.buffer.write(f"Sistem: {text}\n".encode("utf-8", errors="replace"))
            sys.stdout.flush()
        except Exception:
            # Her ihtimale karşı
            print("Sistem: (Yazdırılamayan karakterler var)")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen_for_command(self):
        """Vosk ile çevrimdışı sesli komut dinle"""
        if self.vosk_model is None or KaldiRecognizer is None or sd is None:
            print("Vosk veya sounddevice yüklü değil!")
            return None
        samplerate = 16000
        duration = 5  # saniye
        print("Dinleniyor (Vosk)...")
        try:
            with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, dtype='int16', channels=1) as stream:
                rec = KaldiRecognizer(self.vosk_model, samplerate)
                print("Konuşun...")
                frames = b''
                for _ in range(int(samplerate / 8000 * duration)):
                    data = stream.read(8000)[0]
                    if rec.AcceptWaveform(bytes(data)):
                        break
                    frames += bytes(data)
                result = rec.FinalResult()
                import json as _json
                text = _json.loads(result).get('text', '').strip()
                # Türkçe karakter hatası olmasın diye güvenli print
                try:
                    safe_print(f"Kullanıcıdan gelen sesli komut (Vosk): {text}")
                except Exception:
                    safe_print("Kullanıcıdan gelen sesli komut (Vosk): (Yazdırılamayan karakterler var)")
                return text.lower() if text else None
        except Exception as e:
            print(f"Vosk ile dinleme hatası: {e}")
            return None
    
    def match_command(self, text):
        text = text.lower().strip()

        # 0. Kısa tek kelimelik komutlar
        if text in ["aç", "kapat", "kıs", "azalt", "artır", "yükselt", "parlaklık", "parlak", "şarkı", "müzik", "ses"]:
            # Tahmini en yakın komut
            if text in ["aç", "artır", "yükselt", "parlaklık", "parlak", "ses"]:
                return "turn_on_light"
            if text in ["kapat", "kıs", "azalt"]:
                return "turn_off_light"
            if text in ["şarkı", "müzik"]:
                return "muzik_cal"

        # 1. Önce spesifik aksiyon komutlarını kontrol et
        # Bu, "sesi kapat" gibi komutların "kapanis" olarak algılanmasını engeller.
        
        # Ses Komutları
        if "ses" in text:
            if any(word in text for word in ["aç", "yükselt", "artır"]):
                safe_print("[DEBUG] Kural eşleşti: ses aç -> volume_up")
                return "volume_up"
            if any(word in text for word in ["kıs", "azalt", "düşür", "kapat", "alçalt", "sessize al"]):
                safe_print("[DEBUG] Kural eşleşti: ses kıs -> volume_down")
                return "volume_down"
        
        # Parlaklık Komutları
        if any(w in text for w in ["parlak", "ekran", "ışık"]):
            if any(word in text for word in ["aç", "artır", "yükselt", "canlandır"]):
                safe_print("[DEBUG] Kural eşleşti: parlaklık artır -> turn_on_light")
                return "turn_on_light"
            if any(word in text for word in ["kıs", "azalt", "düşür", "karart", "loş", "kapat"]):
                safe_print("[DEBUG] Kural eşleşti: parlaklık azalt -> turn_off_light")
                return "turn_off_light"

        # Müzik/Şarkı Komutları
        if any(w in text for w in ["müzik", "şarkı"]):
            if any(word in text for word in ["aç", "çal", "oynat", "başlat"]):
                safe_print("[DEBUG] Kural eşleşti: müzik aç -> muzik_cal")
                return "muzik_cal"
            if any(word in text for word in ["durdur", "kapat", "bitir", "sustur"]):
                safe_print("[DEBUG] Kural eşleşti: müzik durdur -> stop_music")
                return "stop_music"

        # 2. Genel komutları ve en son kapanış komutunu kontrol et
        # Eğer yukarıdaki kurallardan hiçbiri eşleşmediyse buraya gelinir.
        
        # Hava Durumu
        if "hava durumu" in text or "hava nasıl" in text:
            safe_print("[DEBUG] Kural eşleşti: hava durumu -> hava_durumu")
            return "hava_durumu"
        
        # Saat
        if "saat" in text:
             safe_print("[DEBUG] Kural eşleşti: saat -> saat_kac")
             return "saat_kac"

        # Kapanış Komutları (En son kontrol ediliyor)
        # Komutun büyük oranda sadece kapanış kelimesi olmasını sağlıyoruz.
        if text in ["kapat", "görüşürüz", "bay bay", "hoşça kal", "çıkış"]:
            safe_print(f"[DEBUG] Kural eşleşti (net kapanış): {text} -> kapanis")
            # Takvim açıksa kapat
            try:
                import psutil
                takvim_kapandi = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['cmdline'] and 'takvim_gui.py' in ' '.join(proc.info['cmdline']):
                            proc.terminate()
                            takvim_kapandi = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                if takvim_kapandi:
                    self.speak("Takvim kapatıldı.")
            except Exception:
                pass
            return "kapanis"

        # Takvim açma komutu (esnek)
        if "takvim" in text and "aç" in text:
            subprocess.Popen(["python", "takvim_gui.py"])
            self.speak("Takvim açılıyor.")
            return "takvim_acildi"
        # Takvim kapatma komutu (esnek)
        if "takvim" in text and "kapat" in text:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'takvim_gui.py' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        self.speak("Takvim kapatıldı.")
                        return "takvim_kapatildi"
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self.speak("Açık takvim bulunamadı.")
            return "takvim_bulunamadi"
        # Görev/Toplantı ekle komutu
        if "ekle" in text or "görev ekle" in text:
            self.speak("Hangi türde görev eklemek istersiniz? (iş, toplantı)")
            while True:
                tur = self.listen_for_command()
                tur_norm = self.normalize_input(tur).replace('i̇', 'i').replace('İ', 'i').replace('ı', 'i').replace('ş', 's').replace('Ş', 's')
                tur_norm = tur_norm.strip().lower()
                if not tur_norm or tur_norm == "":
                    self.speak("Cevap alınamadı, lütfen tekrar söyleyin.")
                    continue
                if "iptal" in tur_norm:
                    self.speak("İşlem iptal edildi. Size başka nasıl yardımcı olabilirim?")
                    return "islem_iptal"
                if tur_norm in ["iş", "is", "i", "is", "ıs", "i", "iş"]:
                    title = "iş"
                    break
                elif "toplantı" in tur_norm or "toplanti" in tur_norm:
                    title = "toplantı"
                    break
                else:
                    self.speak("Lütfen sadece 'iş' veya 'toplantı' olarak belirtin.")
            tarih = self.tarih_sor()
            if isinstance(tarih, tuple) and tarih[0] == "komut_yonlendir":
                return self.match_command(tarih[1])
            if tarih is None:
                return "islem_iptal"
            # Tarih format düzeltme
            if '-' in tarih and not tarih.count('-') == 2:
                gun_str, ay_str = tarih.split('-')
                # Yıl sor
                while True:
                    self.speak("Hangi yıldan bahsediyoruz? (örn: bu yıl, seneye)")
                    yil_cevap = self.listen_for_command()
                    yil_cevap_norm = self.normalize_input(yil_cevap)
                    yil = self.get_year_from_text(yil_cevap_norm)
                    if yil and isinstance(yil, int):
                        break
                    self.speak("Yılı anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: bu yıl, seneye)")
                aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
                try:
                    ay_index = aylar.index(ay_str) + 1
                    tarih_db = f"{yil}-{ay_index:02d}-{int(gun_str):02d}"
                except Exception:
                    self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran 2024)")
                    return "islem_iptal"
            else:
                tarih_db = tarih
            while True:
                self.speak("Hangi saatte eklemek istersiniz? (örn: 14:00, 09:30)")
                saat_cevap = self.listen_for_command()
                saat = self.normalize_time(saat_cevap)
                if isinstance(saat, tuple) and saat[0] == "komut_yonlendir":
                    return self.match_command(saat[1])
                if not saat:
                    self.speak("Saati anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 14:00, 09:30)")
                    continue
                if hasattr(takvim_db, 'get_task_by_datetime'):
                    existing = takvim_db.get_task_by_datetime(tarih_db, saat, title)
                    if existing:
                        self.speak("Bu gün ve saatte başka bir planınız var. Lütfen başka bir saat veya gün söyleyin.")
                        continue
                break
            self.speak("Bir açıklama eklemek ister misiniz? (Yoksa boş bırakabilirsiniz)")
            desc = self.listen_for_command()
            if desc and "iptal" in desc.lower():
                self.speak("İşlem iptal edildi. Size başka nasıl yardımcı olabilirim?")
                return "islem_iptal"
            if not desc:
                desc = ""
            # UTF-8 karakter desteği için encode/decode
            title_utf8 = title.encode('utf-8', errors='replace').decode('utf-8')
            desc_utf8 = desc.encode('utf-8', errors='replace').decode('utf-8')
            safe_print(f"[DEBUG] Ekleme: title={title_utf8}, desc={desc_utf8}, tarih={tarih_db}, saat={saat}")
            takvim_db.add_task(title_utf8, desc_utf8, tarih_db, saat)
            safe_print(f"[DEBUG] Ekleme sonrası kontrol: get_task_by_datetime={takvim_db.get_task_by_datetime(tarih_db, saat, title_utf8)}")
            try:
                yil, ay, gun = map(int, tarih_db.split('-'))
                aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
                ay_str = aylar[ay-1]
                yil_str = self.int_to_turkce_yil(yil)
                tarih_str = f"{gun} {ay_str} {yil_str}"
            except Exception:
                tarih_str = tarih_db
            self.speak(f"'{title}' görevi, {tarih_str} {saat or ''} eklendi.")
            return "ekle_islemi_tamam"
        # Görev/Toplantı sil komutu
        if re.search(r"\bsil( |$|in|i|iyor|mek|mesini|ecek|di|miş)?", text):
            self.speak("Hangi günü ve ayı silmek istiyorsunuz? (örn: 5 Haziran)")
            gun_ay_cevap = self.listen_for_command()
            gun_ay_cevap_norm = self.normalize_input(gun_ay_cevap)
            ay = self.normalize_ay(gun_ay_cevap_norm)
            gun = self.turkce_sayi_to_int(gun_ay_cevap_norm)
            if not (gun and ay):
                self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran)")
                return "islem_iptal"
            while True:
                self.speak("Hangi yıldan bahsediyoruz? (örn: bu yıl, seneye)")
                yil_cevap = self.listen_for_command()
                yil_cevap_norm = self.normalize_input(yil_cevap)
                yil = self.get_year_from_text(yil_cevap_norm)
                if yil and isinstance(yil, int):
                    break
                self.speak("Yılı anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: bu yıl, seneye)")
            from datetime import datetime
            aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
            try:
                ay_index = aylar.index(ay) + 1
                tarih = datetime(yil, ay_index, gun).strftime("%Y-%m-%d")
            except:
                self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran 2024)")
                return "islem_iptal"
            self.speak("Hangi saatteki görevi silmek istiyorsunuz? (örn: 17:00)")
            saat_cevap = self.listen_for_command()
            saat = self.normalize_time(saat_cevap)
            safe_print(f"[DEBUG] Silme: tarih={tarih}, saat={saat}")
            if tarih and saat:
                task = takvim_db.get_task_by_datetime(tarih, saat)
            else:
                task = takvim_db.get_last_task()
            safe_print(f"[DEBUG] Silinecek task: {task}")
            if task:
                try:
                    yil, ay, gun = map(int, tarih.split('-'))
                    aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
                    ay_str = aylar[ay-1]
                    yil_str = self.int_to_turkce_yil(yil)
                    tarih_str = f"{gun} {ay_str} {yil_str}"
                except Exception:
                    tarih_str = tarih
                takvim_db.delete_task(task[0])
                safe_print(f"[DEBUG] Silme sonrası kontrol: get_task_by_datetime={takvim_db.get_task_by_datetime(tarih, saat)}")
                self.speak(f"'{task[1]}' görevi, {tarih_str} {saat} silindi.")
            else:
                self.speak("Böyle bir görev bulunamadı.")
            return "sil_islemi_tamam"
        # Görev/Toplantı tamamlandı komutu
        if "tamamlandı" in text:
            self.speak("Hangi günü ve ayı tamamlandı olarak işaretlemek istiyorsunuz? (örn: 5 Haziran)")
            gun_ay_cevap = self.listen_for_command()
            gun_ay_cevap_norm = self.normalize_input(gun_ay_cevap)
            ay = self.normalize_ay(gun_ay_cevap_norm)
            gun = self.turkce_sayi_to_int(gun_ay_cevap_norm)
            if not (gun and ay):
                self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran)")
                return "islem_iptal"
            while True:
                self.speak("Hangi yıldan bahsediyoruz? (örn: bu yıl, seneye)")
                yil_cevap = self.listen_for_command()
                yil_cevap_norm = self.normalize_input(yil_cevap)
                yil = self.get_year_from_text(yil_cevap_norm)
                if yil and isinstance(yil, int):
                    break
                self.speak("Yılı anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: bu yıl, seneye)")
            from datetime import datetime
            aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
            try:
                ay_index = aylar.index(ay) + 1
                tarih = datetime(yil, ay_index, gun).strftime("%Y-%m-%d")
            except:
                self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran 2024)")
                return "islem_iptal"
            self.speak("Hangi saatteki görevi tamamlandı olarak işaretlemek istiyorsunuz? (örn: 17:00)")
            saat_cevap = self.listen_for_command()
            saat = self.normalize_time(saat_cevap)
            safe_print(f"[DEBUG] Tamamlandı: tarih={tarih}, saat={saat}")
            if tarih and saat:
                task = takvim_db.get_task_by_datetime(tarih, saat)
            else:
                task = takvim_db.get_last_task()
            safe_print(f"[DEBUG] Tamamlanacak task: {task}")
            if task:
                try:
                    yil, ay, gun = map(int, tarih.split('-'))
                    aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
                    ay_str = aylar[ay-1]
                    yil_str = self.int_to_turkce_yil(yil)
                    tarih_str = f"{gun} {ay_str} {yil_str}"
                except Exception:
                    tarih_str = tarih
                takvim_db.mark_task_completed(task[0])
                safe_print(f"[DEBUG] Tamamlandı sonrası kontrol: get_task_by_datetime={takvim_db.get_task_by_datetime(tarih, saat)}")
                self.speak(f"'{task[1]}' görevi, {tarih_str} {saat} tamamlandı olarak işaretlendi.")
            else:
                self.speak("Böyle bir görev bulunamadı.")
            return "tamamlandi_islemi_tamam"

        # Bugün toplantı/iş/görev var mı? (esnek ve gelişmiş)
        if any(k in text for k in ["toplantı", "toplantım", "iş", "işim", "görev", "görevim"]) and \
           any(k in text for k in ["var mı", "bugün", "yarın", "pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar", "işlerim", "görevlerim", "ne var"]):
            date = self.get_date_from_text(text)
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            if any(k in text for k in ["toplantı", "toplantım"]):
                meetings = takvim_db.get_meetings_by_date(date)
                if meetings:
                    cevap = f"{date} tarihinde {len(meetings)} toplantınız var: "
                    for m in meetings:
                        cevap += f"{m[4] or ''} {m[1]}. "
                else:
                    cevap = "O gün için toplantınız yok."
                self.speak(cevap)
                return
            else:
                tasks = takvim_db.get_all_tasks_by_date(date)
                if tasks:
                    cevap = f"{date} için işleriniz: "
                    for t in tasks:
                        cevap += f"{t[4] or ''} {t[1]}. "
                else:
                    cevap = "O gün için kaydedilmiş bir işiniz yok."
                self.speak(cevap)
                return

        # Genel plan sorgusu ("planım ne" gibi)
        if any(k in text for k in ["planım ne", "planım", "plan ne", "planlarım"]):
            self.speak("Hangi tarihteki planınızı öğrenmek istiyorsunuz? (örn: 27 Haziran)")
            tarih_cevap = self.listen_for_command()
            tarih, _, _, _ = parse_task_command(tarih_cevap)
            if not tarih:
                self.speak("Tarihi anlayamadım. Lütfen tekrar deneyin.")
                return
            tasks = takvim_db.get_all_tasks_by_date(tarih)
            if tasks:
                cevap = f"{tarih} için planlarınız: "
                for t in tasks:
                    cevap += f"{t[4] or ''} {t[1]}. "
            else:
                cevap = f"{tarih} için kaydedilmiş bir planınız yok."
            self.speak(cevap)
            return

        # Belirli tarihli plan/görev/toplantı sorgusu
        tarihli_sorgu = re.search(r"(\d{1,2} [a-zA-ZçğıöşüÇĞİÖŞÜ]+)", text)
        if tarihli_sorgu and any(k in text for k in ["iş", "görev", "toplantı", "plan"]):
            tarih_str = tarihli_sorgu.group(1)
            try:
                tarih = datetime.strptime(tarih_str + f" {datetime.now().year}", "%d %B %Y").strftime("%Y-%m-%d")
            except:
                tarih = datetime.now().strftime("%Y-%m-%d")
            tasks = takvim_db.get_all_tasks_by_date(tarih)
            if tasks:
                cevap = f"{tarih} için planlarınız: "
                for t in tasks:
                    cevap += f"{t[4] or ''} {t[1]}. "
            else:
                cevap = f"{tarih} için kaydedilmiş bir planınız yok."
            self.speak(cevap)
            return

        # 3. Kural eşleşmezse modeli kullan (sohbet için)
        if self.voice_command_model and self.voice_vectorizer:
            try:
                text_vec = self.voice_vectorizer.transform([text])
                prediction = self.voice_command_model.predict(text_vec)[0]
                safe_print(f"[DEBUG] Model tahmini: {prediction}")
                return prediction
            except Exception as e:
                print(f"Model tahmin hatası: {e}")
                return None
        return None

    def get_response(self, command, extra=None):
        """Komuta uygun yanıtı al ve aksiyonu tetikle."""
        if not command or command in ["ekle_islemi_tamam", "sil_islemi_tamam", "tamamlandi_islemi_tamam", "islem_iptal", "takvim_acildi", "takvim_kapatildi", "takvim_bulunamadi"]:
            return ""
        if not command:
            return "Bu komutu anlayamadım."

        # Aksiyon gerektiren komutları burada ele al
        if command == "volume_up":
            return self.adjust_system_parameter("volume", 0.1)
        if command == "volume_down":
            return self.adjust_system_parameter("volume", -0.1)
        if command == "turn_on_light":
            return self.adjust_system_parameter("brightness", 10)
        if command == "turn_off_light":
            return self.adjust_system_parameter("brightness", -10)
        
        if command == "hava_durumu":
            try:
                API_KEY = "e439f45d9412b211b5b17c3cd0256d34"
                city = "Istanbul"
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&lang=tr&units=metric"
                r = requests.get(url, timeout=5)
                data = r.json()
                if r.status_code == 200:
                    weather = data['weather'][0]['description']
                    temp = data['main']['temp']
                    return f"Şu anda {city} için hava: {weather}, sıcaklık: {temp}°C."
                else:
                    return f"Hava durumu alınamadı: {data.get('message', 'Bilinmeyen hata')} (Kod: {r.status_code})"
            except Exception as e:
                return f"Hava durumu alınamadı, hata: {e}"

        if command == "muzik_cal":
            self.speak(self.responses[command])
            song_name = self.listen_for_command()
            if song_name:
                # Şarkı ismini doğrudan kullan, modele gönderme
                query = urllib.parse.quote(song_name)
                url = f"https://www.youtube.com/results?search_query={query}"
                try:
                    response = requests.get(url)
                    video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
                    if video_ids:
                        webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
                        return f"{song_name} açılıyor."
                    else:
                        return "Şarkı bulunamadı."
                except Exception as e:
                    return f"YouTube'da arama yapılamadı: {e}"
            else:
                return "Şarkı ismi algılanamadı."

        # Diğer komutlar için yanıtları `self.responses` sözlüğünden al
        response = self.responses.get(command)
        if response:
            if isinstance(response, list):
                return random.choice(response)
            elif callable(response):
                return response()
            else:
                return response

        return "Bu komutu tam olarak anlayamadım, tekrar eder misin?"

    def adjust_system_parameter(self, param_type, change):
        """Ses veya parlaklık ayarlarını yapar"""
        if param_type == "volume":
            if not all([AudioUtilities, IAudioEndpointVolume, CLSCTX_ALL]):
                return "Ses ayarı için gerekli modül bulunamadı."
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
                current = volume.GetMasterVolumeLevelScalar()
                new_volume = max(0.0, min(1.0, current + change))
                volume.SetMasterVolumeLevelScalar(new_volume, None)
                return "Ses seviyesi ayarlandı."
            except Exception as e:
                return f"Ses ayarlanamadı: {e}"
        elif param_type == "brightness":
            if not sbc:
                return "Parlaklık ayarı için gerekli modül bulunamadı."
            try:
                current = sbc.get_brightness(display=0)[0]
                new_brightness = max(0, min(100, current + change))
                sbc.set_brightness(new_brightness, display=0)
                return "Parlaklık ayarlandı."
            except Exception as e:
                return f"Parlaklık ayarlanamadı: {e}"
        return ""

    def start_voice_assistant(self):
        """Sesli asistanı başlat"""
        self.voice_active = True
        welcome_message = f"Hoş geldiniz {self.current_user}! Size nasıl yardımcı olabilirim?"
        self.speak(welcome_message)
        
        while self.voice_active:
            command_text = self.listen_for_command()
            if command_text:
                command_label = self.match_command(command_text)
                
                if command_label == "kapanis":
                    self.speak(random.choice(self.responses["kapanis"]))
                    self.voice_active = False
                    self.system_active = False
                    if self.root:
                        self.root.destroy()
                    break

                response = self.get_response(command_label)
                self.speak(response)

    def run_main_system(self):
        """Ana sistem döngüsü"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Kamera açılamadı!")
            return
        
        print("Ana sistem başlatıldı...")
        print("Çıkmak için 'q' tuşuna basın")
        
        while self.system_active:
            ret, frame = cap.read()
            if not ret:
                break

            # Yüz tanıma (sadece yüz doğrulanmadıysa)
            if not self.face_verified:
                face_locations, face_names = self.recognize_face(frame)
                # Yüz çerçevelerini çiz
                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    # Yüz tanıma sürecini başlat
                    if name != "Bilinmeyen":
                        if self.current_user != name:
                            self.current_user = name
                            self.face_detection_start = time.time()
                            self.face_verified = False
                            self.hand_verified = False
                        if self.face_detection_start:
                            elapsed_time = time.time() - self.face_detection_start
                            if elapsed_time >= self.face_detection_threshold:
                                self.face_verified = True
                                self.face_detection_start = None
                    else:
                        self.current_user = None
                        self.face_detection_start = None
                        self.face_verified = False
                        self.hand_verified = False
            # Yüz doğrulandıktan sonra yüz tanıma yapılmaz, sadece el hareketi beklenir

            # El hareketi tanıma (sadece yüz doğrulandıktan sonra)
            if self.face_verified and not self.hand_verified:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # El çizgilerini çiz
                        self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # El hareketini tanı
                        gesture, probability = self.recognize_hand_gesture(hand_landmarks)
                        
                        # Debug bilgisi - her zaman göster
                        cv2.putText(frame, f"Tespit: {gesture} ({probability:.2f})", 
                                  (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                        
                        if gesture and probability > 0.40:
                            expected_gesture = self.person_gestures.get(self.current_user.lower(), "A") if hasattr(self, 'person_gestures') else None
                            safe_print(f"DEBUG: Kullanıcı: {self.current_user}, Beklenen: {expected_gesture}, Tahmin: {gesture}, Güven: {probability:.2f}")
                            cv2.putText(frame, f"El Hareketi: {gesture} ({probability:.2f})", 
                                      (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                            # Kişiye özel el hareketi kontrolü
                            if self.check_person_gesture(self.current_user, gesture):
                                self.hand_verified = True
                                welcome_text = f"Hoş geldiniz {self.current_user}!"
                                cv2.putText(frame, welcome_text, (10, 220), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                self.speak(welcome_text)
                                if not self.voice_active:
                                    safe_print("DEBUG: Sesli asistan başlatılıyor!")
                                    threading.Thread(target=self.start_voice_assistant, daemon=True).start()
                else:
                    # El tespit edilmediğinde bilgi göster
                    cv2.putText(frame, "El Tespit Edilmedi", (10, 150), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Durum bilgilerini göster
            status_text = []
            if self.current_user:
                status_text.append(f"Kisi: {self.current_user}")
                if self.face_detection_start:
                    elapsed = time.time() - self.face_detection_start
                    remaining = max(0, self.face_detection_threshold - elapsed)
                    status_text.append(f"Yuz Dogrulama: {remaining:.1f}s")
                elif self.face_verified:
                    status_text.append("Yuz Dogrulandi (OK)")
                    if not self.hand_verified:
                        status_text.append("El Hareketi Bekleniyor...")
                    else:
                        status_text.append("El Hareketi Dogrulani ✓")
                        status_text.append("Sisteme Giris Basarili!")
                        if self.voice_active:
                            status_text.append("Sesli Asistan Aktif")
            
            # Durum bilgilerini ekrana yaz
            for i, text in enumerate(status_text):
                cv2.putText(frame, text, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Ana Sistem - Yuz ve El Hareketi Tanitma', frame)
            
            # --- YENİ: Eğer hem yüz hem el doğrulandıysa döngüyü bitir ---
            if self.face_verified and self.hand_verified:
                safe_print("Doğrulama tamamlandı, sesli asistana geçiliyor.")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def create_gui(self):
        self.theme = 'light'  # Varsayılan tema
        def apply_theme():
            if self.theme == 'light':
                bg_main = '#f5f5f5'  # Modern açık gri
                bg_header1 = '#1A237E'
                bg_header2 = '#3949AB'
                fg_title = '#FFD700'  # Altın sarısı vurgu
                fg_shadow = '#1A237E'
                fg_status = '#1A237E'
                bg_status = '#FFFFFF'
                bg_info = '#1A237E'
                fg_info = '#FFFFFF'
                btn_bg = '#FFD700'
                btn_fg = '#1A237E'
                btn_active = '#1A237E'
                btn_active_fg = '#FFD700'
            else:
                bg_main = '#23272A'
                bg_header1 = '#181818'
                bg_header2 = '#3949AB'
                fg_title = '#FFD700'
                fg_shadow = '#3949AB'
                fg_status = '#FFFFFF'
                bg_status = '#181818'
                bg_info = '#181818'
                fg_info = '#FFD700'
                btn_bg = '#FFD700'
                btn_fg = '#23272A'
                btn_active = '#3949AB'
                btn_active_fg = '#FFD700'
            self.root.configure(bg=bg_main)
            wave_canvas.configure(bg=bg_main)
            wave_canvas.delete('all')
            # Daha yumuşak dalga efekti
            wave_canvas.create_arc(-100, 20, 950, 220, start=0, extent=180, fill=bg_header1, outline='')
            wave_canvas.create_arc(-100, 40, 950, 240, start=0, extent=180, fill=bg_header2, outline='')
            title_shadow1.config(bg=bg_header1, fg=fg_shadow)
            title_shadow2.config(bg=bg_header1, fg=fg_shadow)
            title1.config(bg=bg_header1, fg=fg_title)
            title2.config(bg=bg_header1, fg=fg_title)
            subtitle.config(bg=bg_header2, fg=fg_title)
            if hasattr(self, 'icon_img'):
                icon_label.config(bg=bg_header1)
            if hasattr(self, 'avatar_img'):
                avatar_label.config(bg=bg_main)
            status_frame.config(bg=bg_status, highlightbackground=bg_header1)
            self.status_label.config(bg=bg_status, fg=fg_status)
            button_frame.config(bg=bg_main)
            style.configure('Modern.TButton', background=btn_bg, foreground=btn_fg, font=("Segoe UI", 15, "bold"), borderwidth=0, focusthickness=3, focuscolor=btn_active)
            style.map('Modern.TButton', background=[('active', btn_active)], foreground=[('active', btn_active_fg)])
            self.start_button.config(style='Modern.TButton')
            self.stop_button.config(style='Modern.TButton')
            self.exit_button.config(style='Modern.TButton')
            info_frame.config(bg=bg_info)
            info_label.config(bg=bg_info, fg=fg_info)
            if hasattr(self, 'info_icon_img'):
                info_icon_label.config(bg=bg_info)

        self.root = tk.Tk()
        self.root.title("Yüz Tanıma ve El Hareketleriyle Güvenlik Sistemi ve Akıllı Asistan")
        self.root.geometry("900x720")
        self.root.configure(bg='#f5f5f5')

        # Üstte dalga efekti (canvas)
        wave_canvas = tk.Canvas(self.root, width=900, height=120, bg='#f5f5f5', highlightthickness=0)
        wave_canvas.pack(fill='x')
        wave_canvas.create_arc(-100, 20, 950, 220, start=0, extent=180, fill='#1A237E', outline='')
        wave_canvas.create_arc(-100, 40, 950, 240, start=0, extent=180, fill='#3949AB', outline='')

        # Başlık ve ikon (iki satır, ortalanmış, modern)
        title_text1 = 'Yüz Tanıma ve El Hareketleriyle Güvenlik Sistemi'
        title_text2 = 've Akıllı Asistan'
        # İlk satır
        title_shadow1 = tk.Label(self.root, text=title_text1, font=('Segoe UI', 22, 'bold'), bg='#1A237E', fg='#3949AB', anchor='center', justify='center')
        title_shadow1.place(relx=0.5, y=38, anchor='n')
        title1 = tk.Label(self.root, text=title_text1, font=('Segoe UI', 22, 'bold'), bg='#1A237E', fg='#FFD700', anchor='center', justify='center')
        title1.place(relx=0.5, y=35, anchor='n')
        # İkinci satır (daha aşağıda)
        title_shadow2 = tk.Label(self.root, text=title_text2, font=('Segoe UI', 18, 'bold'), bg='#1A237E', fg='#3949AB', anchor='center', justify='center')
        title_shadow2.place(relx=0.5, y=78, anchor='n')
        title2 = tk.Label(self.root, text=title_text2, font=('Segoe UI', 18, 'bold'), bg='#1A237E', fg='#FFD700', anchor='center', justify='center')
        title2.place(relx=0.5, y=75, anchor='n')
        subtitle = tk.Label(self.root, text='Yüz ve El Hareketleriyle Güvenlik, Akıllı Asistan Deneyimi', font=('Segoe UI', 14, 'italic'), bg='#3949AB', fg='#FFD700', anchor='center', justify='center')
        subtitle.place(relx=0.5, y=110, anchor='n')

        # Kullanıcı avatarı (örnek görsel)
        try:
            avatar_img = Image.open('images/avatar.png').resize((60, 60))
            self.avatar_img = ImageTk.PhotoImage(avatar_img)
            avatar_label = tk.Label(self.root, image=self.avatar_img, bg='#f5f5f5', bd=0)
            avatar_label.place(x=800, y=30)
        except:
            pass

        # Tema değiştirici buton
        def toggle_theme():
            self.theme = 'dark' if self.theme == 'light' else 'light'
            apply_theme()
        theme_btn = tk.Button(self.root, text='🌙/☀️', font=('Segoe UI', 14, 'bold'), bg='#1A237E', fg='#FFD700', bd=0, relief='flat', command=toggle_theme, cursor='hand2', activebackground='#3949AB')
        theme_btn.place(x=840, y=20, width=38, height=38)

        # Durum göstergesi (renkli çerçeve ve animasyonlu çubuk)
        self.status_var = tk.StringVar(value="Sistem Hazır")
        status_frame = tk.Frame(self.root, bg="#FFFFFF", highlightbackground="#1A237E", highlightthickness=3, bd=0)
        status_frame.pack(pady=(140, 10))
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 18, "bold"), bg="#FFFFFF", fg="#1A237E", pady=10)
        self.status_label.pack()
        self.progress = ttk.Progressbar(status_frame, orient='horizontal', length=400, mode='indeterminate')
        self.progress.pack(pady=8)

        # Butonlar (büyük, yuvarlatılmış, modern)
        button_frame = tk.Frame(self.root, bg='#f5f5f5')
        button_frame.pack(pady=35)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TButton', font=("Segoe UI", 15, "bold"), borderwidth=0, focusthickness=3, focuscolor='#FFD700', padding=12, relief='flat')
        self.start_button = ttk.Button(button_frame, text="🚀 Sistemi Başlat", command=self.start_system, style='Modern.TButton')
        self.start_button.pack(side=tk.LEFT, padx=22)
        self.stop_button = ttk.Button(button_frame, text="⏹ Sistemi Durdur", command=self.stop_system, style='Modern.TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=22)
        self.exit_button = ttk.Button(button_frame, text="❌ Çıkış", command=self.exit_system, style='Modern.TButton', state=tk.NORMAL)
        self.exit_button.pack(side=tk.LEFT, padx=22)

        # Buton hover efekti
        def on_enter(e):
            e.widget.config(cursor="hand2")
        def on_leave(e):
            e.widget.config(cursor="arrow")
        for btn in [self.start_button, self.stop_button, self.exit_button]:
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Alt bilgi paneli (ikonlu ve paddingli)
        info_frame = tk.Frame(self.root, bg='#1A237E', bd=2, relief='ridge')
        info_frame.pack(side='bottom', fill='x', pady=18)
        try:
            info_icon = Image.open('images/assistant_icon.png').resize((28, 28))
            self.info_icon_img = ImageTk.PhotoImage(info_icon)
            info_icon_label = tk.Label(info_frame, image=self.info_icon_img, bg='#1A237E')
            info_icon_label.pack(side='left', padx=(18, 8), pady=8)
        except:
            pass
        info_text = "Yüz ve el hareketleriyle güvenli giriş, sesli komutlarla akıllı asistan deneyimi. Tüm verileriniz güvende!"
        info_label = tk.Label(info_frame, text=info_text, font=("Segoe UI", 13), bg='#1A237E', fg='#FFD700', pady=12)
        info_label.pack(side='left', padx=5)

        apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_system(self):
        """Sistemi başlat"""
        # Tüm state değişkenlerini sıfırla
        self.system_active = True
        self.voice_active = False
        self.face_verified = False
        self.hand_verified = False
        self.current_user = None
        self.face_detection_start = None
        self.status_var.set("Sistem Aktif")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_main_system, daemon=True).start()
    
    def stop_system(self):
        """Sistemi durdur"""
        self.system_active = False
        self.voice_active = False
        self.status_var.set("Sistem Durduruldu")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def exit_system(self):
        """Sistemden çıkış yap"""
        self.stop_system()
        self.root.destroy()
    
    def on_closing(self):
        """Pencere kapatılırken temizlik yap"""
        self.stop_system()
        self.root.destroy()
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        self.create_gui()
        self.root.mainloop()

    def saat_sor(self):
        while True:
            self.speak("Hangi saatte ekleyeyim? (örn: 14:00, 09:30, on iki)")
            saat_cevap = self.listen_for_command()
            saat_cevap_norm = self.normalize_input(saat_cevap)
            if not saat_cevap_norm:
                self.speak("Cevap alınamadı, lütfen tekrar söyleyin.")
                continue
            if "iptal et" in saat_cevap_norm:
                self.speak("İşlem iptal edildi. Size başka nasıl yardımcı olabilirim?")
                return "islem_iptal"
            if "saati tekrar sor" in saat_cevap_norm:
                continue
            ana_komut = self.match_command(saat_cevap_norm)
            if ana_komut:
                return ("komut_yonlendir", saat_cevap_norm)
            # Anahtar kelime ve sayı eşleştirmesi
            sayilar = {
                "bir": 1, "iki": 2, "uc": 3, "dort": 4, "bes": 5, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
                "on": 10, "on bir": 11, "on iki": 12, "on uc": 13, "on dort": 14, "on bes": 15, "on alti": 16, "on yedi": 17, "on sekiz": 18, "on dokuz": 19,
                "yirmi": 20, "yirmi bir": 21, "yirmi iki": 22, "yirmi uc": 23, "yirmi dort": 24
            }
            for kelime, rakam in sayilar.items():
                if kelime in saat_cevap_norm:
                    return f"{rakam:02d}:00"
            # Rakamlı formatı da destekle
            import re
            match = re.search(r"\b(\d{1,2})[:\.\, ]?(\d{2})?\b", saat_cevap_norm)
            if match:
                saat = int(match.group(1))
                dakika = int(match.group(2)) if match.group(2) else 0
                return f"{saat:02d}:{dakika:02d}"
            # Sonra model tahmini
            ana_komut = self.match_command(saat_cevap_norm)
            if ana_komut:
                return ("komut_yonlendir", saat_cevap_norm)
            self.speak("Saati anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 14:00, on iki)")

    def normalize_input(self, text):
        if not text:
            return ""
        text = text.lower().strip()
        text = text.replace('  ', ' ')
        # 'ekle' gibi fazlalıkları temizle
        text = text.replace(' ekle', '').replace('ekle ', '').replace('ekle', '')
        # 'iş' kelimesi için özel kontrol
        if text == 'iş' or text == 'is':
            return 'is'
        text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        # 'iki' varyasyonlarını normalize et
        for bozuk in [' i ', ' ik ', ' ki ', ' li ', ' iki̇ ', ' iki ', 'i̇ki', ' iki', 'iki ', 'i̇ki ']:
            text = text.replace(bozuk, ' iki ')
        # Başta veya sonda ise
        if text.startswith('i '):
            text = text.replace('i ', 'iki ', 1)
        if text.endswith(' i'):
            text = text[:-2] + ' iki'
        if text == 'i' or text == 'ik' or text == 'ki' or text == 'li' or text == 'iki̇':
            text = 'iki'
        return text

    def onay_al(self, metin):
        self.speak(f"Şunu mu söylediniz: {metin}? Evet veya hayır deyin.")
        cevap = self.listen_for_command()
        cevap = self.normalize_input(cevap)
        return cevap in ["evet", "tamam", "dogru", "doğru"]

    def turkce_yil_to_int_akilli(self, yil_str):
        # Tüm birleşik ve ayrı yazılmış varyasyonları destekle
        yil_str = yil_str.lower().replace("ikibin", "iki bin ").replace("binyirmi", "bin yirmi ")
        yil_str = yil_str.replace("binyirmi", "bin yirmi ").replace("binyirmi", "bin yirmi ")
        yil_str = yil_str.replace("yirmibes", "yirmi beş").replace("yirmialtı", "yirmi altı").replace("yirmiyedi", "yirmi yedi").replace("yirmisekiz", "yirmi sekiz").replace("yirmidokuz", "yirmi dokuz")
        yil_str = yil_str.replace("yirmibir", "yirmi bir").replace("yirmiiki", "yirmi iki").replace("yirmiüç", "yirmi üç").replace("yirmidört", "yirmi dört").replace("yirmibeş", "yirmi beş").replace("yirmialtı", "yirmi altı")
        yil_str = yil_str.replace("onbir", "on bir").replace("oniki", "on iki").replace("onüç", "on üç").replace("ondört", "on dört").replace("onbeş", "on beş").replace("onaltı", "on altı").replace("onyedi", "on yedi").replace("onsekiz", "on sekiz").replace("ondokuz", "on dokuz")
        yil_str = yil_str.replace("bin", " bin ").replace("yüz", " yüz ")
        yil_str = ' '.join(yil_str.split())
        sayilar = {"sıfır": 0, "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90, "yüz": 100, "bin": 1000}
        kelimeler = yil_str.split()
        toplam = 0
        temp = 0
        for kelime in kelimeler:
            if kelime in sayilar:
                deger = sayilar[kelime]
                if deger == 1000:
                    if temp == 0:
                        temp = 1
                    toplam += temp * 1000
                    temp = 0
                elif deger == 100:
                    if temp == 0:
                        temp = 1
                    temp *= 100
                else:
                    temp += deger
        toplam += temp
        return toplam if toplam > 0 else None

    def turkce_sayi_to_int(self, metin):
        metin = metin.lower().replace("-", " ").replace("  ", " ")
        import re
        rakam = re.findall(r"\b\d{1,4}\b", metin)
        if rakam:
            return int(rakam[0])
        birler = {"sıfır":0, "bir":1, "iki":2, "üç":3, "dört":4, "beş":5, "altı":6, "yedi":7, "sekiz":8, "dokuz":9}
        onlar = {"on":10, "yirmi":20, "otuz":30, "kırk":40, "elli":50, "altmış":60, "yetmiş":70, "seksen":80, "doksan":90}
        kelimeler = metin.split()
        toplam = 0
        i = 0
        while i < len(kelimeler):
            if kelimeler[i] in onlar:
                deger = onlar[kelimeler[i]]
                if i+1 < len(kelimeler) and kelimeler[i+1] in birler:
                    deger += birler[kelimeler[i+1]]
                    i += 1
                toplam += deger
            elif kelimeler[i] in birler:
                toplam += birler[kelimeler[i]]
            i += 1
        if 0 <= toplam <= 3000:
            return toplam
        return None

    def normalize_time(self, saat_str):
        if not saat_str:
            return None
        saat_str = saat_str.strip().lower().replace("-", " ").replace("  ", " ")
        import re
        # Gece yarısı
        if "gece yarısı" in saat_str:
            return "00:00"
        # Öğlen
        if "öğlen" in saat_str or "öğle" in saat_str:
            return "12:00"
        # Öğleden sonra
        if "öğleden sonra" in saat_str:
            match = re.search(r"(\d{1,2})", saat_str)
            if match:
                saat = int(match.group(1))
                if saat < 12:
                    saat += 12
                return f"{saat:02d}:00"
        # Türkçe sayı sözlüğü
        birler = {"sıfır":0, "bir":1, "iki":2, "üç":3, "dört":4, "beş":5, "altı":6, "yedi":7, "sekiz":8, "dokuz":9}
        onlar = {"on":10, "yirmi":20, "otuz":30, "kırk":40, "elli":50, "altmış":60, "yetmiş":70, "seksen":80, "doksan":90}
        # Tüm kelimeleri sayıya çevir
        def kelime_to_sayi(kelimeler):
            toplam = 0
            i = 0
            while i < len(kelimeler):
                kelime = kelimeler[i]
                # 'iki' varyasyonlarını normalize et
                if kelime in ['i', 'ik', 'ki', 'li', 'iki̇']:
                    kelime = 'iki'
                if kelime in onlar:
                    deger = onlar[kelime]
                    if i+1 < len(kelimeler):
                        sonraki = kelimeler[i+1]
                        if sonraki in ['i', 'ik', 'ki', 'li', 'iki̇']:
                            sonraki = 'iki'
                        if sonraki in birler:
                            deger += birler[sonraki]
                            i += 1
                    toplam += deger
                elif kelime in birler:
                    toplam += birler[kelime]
                i += 1
            return toplam
        # Rakamlı saat (örn: 14:30, 09:15, 7.45, 1700, 18 15)
        match = re.search(r"(\d{1,2})[:\.\,\s]?(\d{2})?", saat_str)
        if match:
            saat = int(match.group(1))
            dakika = int(match.group(2)) if match.group(2) else 0
            if 0 <= saat <= 23 and 0 <= dakika <= 59:
                return f"{saat:02d}:{dakika:02d}"
        # Türkçe kelimeyle saat (örn: 'on sekiz', 'on sekiz on beş', 'iki kırk dört')
        kelimeler = saat_str.split()
        # 'iki' varyasyonlarını normalize et
        kelimeler = ['iki' if k in ['i', 'ik', 'ki', 'li', 'iki̇'] else k for k in kelimeler]
        if len(kelimeler) == 1:
            # Tek kelime: 'dokuz', 'on', 'on sekiz' gibi
            saat = kelime_to_sayi(kelimeler)
            if 0 <= saat <= 23:
                return f"{saat:02d}:00"
        elif len(kelimeler) == 2:
            # İki kelime: 'sekiz on', 'on sekiz', 'on beş', 'yirmi sekiz' gibi
            saat = kelime_to_sayi([kelimeler[0]])
            dakika = kelime_to_sayi([kelimeler[1]])
            if 0 <= saat <= 23 and 0 <= dakika <= 59:
                return f"{saat:02d}:{dakika:02d}"
        elif len(kelimeler) == 3:
            # Üç kelime: 'iki kırk dört', 'on sekiz on', 'on sekiz beş' gibi
            saat = kelime_to_sayi([kelimeler[0]])
            dakika = kelime_to_sayi(kelimeler[1:])
            if 0 <= saat <= 23 and 0 <= dakika <= 59:
                return f"{saat:02d}:{dakika:02d}"
        # 'buçuk' desteği
        for saat_kelime in birler.keys() | onlar.keys():
            if saat_kelime in kelimeler and "buçuk" in kelimeler:
                saat = kelime_to_sayi([saat_kelime])
                return f"{saat:02d}:30"
        return None

    def int_to_turkce_yil(self, yil):
        # 2025 -> 'iki bin yirmi beş'
        birler = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
        onlar = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
        if yil < 1000 or yil > 2999:
            return str(yil)
        binlik = yil // 1000
        yuzluk = (yil % 1000) // 100
        onlarlik = (yil % 100) // 10
        birlik = yil % 10
        sonuc = ""
        if binlik:
            sonuc += birler[binlik] + " bin"
        if yuzluk:
            sonuc += " " + birler[yuzluk] + " yüz"
        if onlarlik or birlik:
            if sonuc:
                sonuc += " "
            sonuc += onlar[onlarlik]
            if birlik:
                sonuc += " " + birler[birlik]
        return sonuc.strip()

    def tarih_sor(self, islem="ekle"):
        from datetime import datetime
        aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
        if islem == "ekle":
            soru = "Hangi günü ve ayı eklemek istersiniz? (örn: 5 Haziran)"
        elif islem == "sil":
            soru = "Hangi günü ve ayı silmek istiyorsunuz? (örn: 5 Haziran)"
        elif islem == "tamamlandi":
            soru = "Hangi günü ve ayı tamamlandı olarak işaretlemek istiyorsunuz? (örn: 5 Haziran)"
        else:
            soru = "Hangi günü ve ayı belirtmek istersiniz? (örn: 5 Haziran)"
        while True:
            self.speak(soru)
            gun_ay_cevap = self.listen_for_command()
            gun_ay_cevap_norm = self.normalize_input(gun_ay_cevap)
            if not gun_ay_cevap_norm or gun_ay_cevap_norm.strip() == "":
                self.speak("Cevap alınamadı, lütfen tekrar söyleyin.")
                continue
            if "iptal et" in gun_ay_cevap_norm:
                self.speak("İşlem iptal edildi. Size başka nasıl yardımcı olabilirim?")
                return "islem_iptal"
            if "tarihi tekrar sor" in gun_ay_cevap_norm:
                continue
            gun_ay_cevap_norm = gun_ay_cevap_norm.replace(' ekle', '').replace('ekle ', '').replace('ekle', '')
            # Ay ve gün ayrıştırma
            ay = self.normalize_ay(gun_ay_cevap_norm)
            gun = self.turkce_sayi_to_int(gun_ay_cevap_norm)
            safe_print(f"[DEBUG] tarih_sor: gun_ay_cevap_norm={gun_ay_cevap_norm}, gun={gun}, ay={ay}")
            # Eğer hem ay hem gün varsa, model tahmini bypass
            if ay and gun:
                return f"{gun:02d}-{ay}"
            if ay and not gun:
                while True:
                    self.speak(f"Hangi günü {ay} ayı için belirtmek istersiniz? (örn: 5)")
                    gun_cevap = self.listen_for_command()
                    gun_cevap_norm = self.normalize_input(gun_cevap)
                    if not gun_cevap_norm or gun_cevap_norm.strip() == "":
                        self.speak("Cevap alınamadı, lütfen tekrar söyleyin.")
                        continue
                    gun = self.turkce_sayi_to_int(gun_cevap_norm)
                    safe_print(f"[DEBUG] tarih_sor: gun_cevap_norm={gun_cevap_norm}, gun={gun}, ay={ay}")
                    if gun:
                        return f"{gun:02d}-{ay}"
            if gun and not ay:
                while True:
                    self.speak("Hangi ayı belirtmek istersiniz? (örn: Haziran)")
                    ay_cevap = self.listen_for_command()
                    ay_cevap_norm = self.normalize_input(ay_cevap)
                    if not ay_cevap_norm or ay_cevap_norm.strip() == "":
                        self.speak("Cevap alınamadı, lütfen tekrar söyleyin.")
                        continue
                    ay = self.normalize_ay(ay_cevap_norm)
                    safe_print(f"[DEBUG] tarih_sor: ay_cevap_norm={ay_cevap_norm}, gun={gun}, ay={ay}")
                    if ay:
                        return f"{gun:02d}-{ay}"
            self.speak("Tarihi anlayamadım. Lütfen tekrar ve net bir şekilde söyleyin. (örn: 5 Haziran)")

    def normalize_ay(self, metin):
        # Ay isimlerini ve varyasyonlarını normalize eder
        aylar = {
            "ocak": ["ocak", "ocag", "ocagı"],
            "şubat": ["şubat", "subat", "şubatt", "subatt"],
            "mart": ["mart", "martt"],
            "nisan": ["nisan", "nisann"],
            "mayıs": ["mayıs", "mayis", "mayiss"],
            "haziran": ["haziran", "hazirann", "hazirannn"],
            "temmuz": ["temmuz", "temuz", "temmuzz"],
            "ağustos": ["ağustos", "agustos", "ağustoss", "agustoss"],
            "eylül": ["eylül", "eylul", "eylull", "eylüll"],
            "ekim": ["ekim", "ekimm"],
            "kasım": ["kasım", "kasim", "kasimm"],
            "aralık": ["aralık", "aralik", "aralikk"]
        }
        metin = metin.lower()
        for dogru, varyasyonlar in aylar.items():
            for v in varyasyonlar:
                if v in metin:
                    return dogru
        return None

    def get_year_from_text(self, yil_str):
        from datetime import datetime
        yil_str = (yil_str or "").lower().strip()
        now = datetime.now()
        import re
        # 'X yıl sonra' desteği (hem rakam hem Türkçe)
        match = re.search(r"(\d+) yıl sonra", yil_str)
        if match:
            return now.year + int(match.group(1))
        # Türkçe sayı ile 'yıl sonra'
        turkce_sayilar = {
            "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10
        }
        for kelime, rakam in turkce_sayilar.items():
            if f"{kelime} yıl sonra" in yil_str:
                return now.year + rakam
        # Rakamlı yıl
        match = re.search(r"\b(20\d{2})\b", yil_str)
        if match:
            return int(match.group(1))
        # Türkçe yıl
        turkce_yil = self.turkce_yil_to_int_akilli(yil_str)
        if turkce_yil and 1900 < turkce_yil < 2100:
            return turkce_yil
        # bu yıl, seneye, gelecek yıl, önümüzdeki yıl
        if "bu yil" in yil_str or "bu sene" in yil_str or "şu anki yil" in yil_str:
            return now.year
        if "seneye" in yil_str or "gelecek yil" in yil_str or "önümüzdeki yil" in yil_str or "gelecek sene" in yil_str or "önümüzdeki sene" in yil_str:
            return now.year + 1
        if "iki bin" in yil_str:
            turkce_yil = self.turkce_yil_to_int_akilli(yil_str)
            if turkce_yil and 1900 < turkce_yil < 2100:
                return turkce_yil
        return None

    def get_date_from_text(self, text):
        """Kullanıcıdan gelen metinden bugüne, yarına veya haftanın gününe göre tarih döndürür."""
        text = text.lower()
        today = datetime.now()
        if "bugün" in text:
            return today.strftime("%Y-%m-%d")
        elif "yarın" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            days = ["pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar"]
            for i, day in enumerate(days):
                if day in text:
                    today_idx = today.weekday()
                    target_idx = i
                    delta = (target_idx - today_idx + 7) % 7
                    if delta == 0:
                        delta = 7  # Aynı günse bir sonraki haftayı kasteder
                    target_date = today + timedelta(days=delta)
                    return target_date.strftime("%Y-%m-%d")
        return None

def parse_task_command(text):
    if not text:
        return None, None, None, ""
    # Türkçe sayıları rakama çevir
    turkce_sayilar = {
        "sıfır": "0", "bir": "1", "iki": "2", "üç": "3", "dört": "4", "beş": "5", "altı": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
        "on": "10", "on bir": "11", "on iki": "12", "on üç": "13", "on dört": "14", "on beş": "15", "on altı": "16", "on yedi": "17", "on sekiz": "18", "on dokuz": "19",
        "yirmi": "20", "yirmi bir": "21", "yirmi iki": "22", "yirmi üç": "23", "yirmi dört": "24", "yirmi beş": "25", "yirmi altı": "26", "yirmi yedi": "27", "yirmi sekiz": "28", "yirmi dokuz": "29", "otuz": "30", "otuz bir": "31"
    }
    aylar = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
    # Türkçe sayıları rakama çevir
    for kelime, rakam in sorted(turkce_sayilar.items(), key=lambda x: -len(x[0])):
        text = text.replace(kelime, rakam)
    # Ay adlarını küçük harfe çevir
    for ay in aylar:
        text = text.replace(ay.capitalize(), ay)
    # Tarih bul
    tarih_regex = r'(\d{1,2} [a-zA-ZçğıöşüÇĞİÖŞÜ]+)'
    saat_regex = r'(\d{1,2}[:\.\,\s]?\d{2})'
    tarih = None
    saat = None
    title = None
    desc = ""
    # Tarih bul
    import re
    tarih_match = re.search(tarih_regex, text)
    if tarih_match:
        tarih_str = tarih_match.group(1)
        try:
            tarih = datetime.strptime(tarih_str + f" {datetime.now().year}", "%d %B %Y").strftime("%Y-%m-%d")
        except:
            tarih = datetime.now().strftime("%Y-%m-%d")
    else:
        tarih = None
    # Saat bul
    saat_match = re.search(saat_regex, text)
    if saat_match:
        saat_raw = saat_match.group(1)
        # 1700 gibi yazılmışsa : ekle
        if len(saat_raw.replace(' ','')) == 4 and ':' not in saat_raw:
            saat = f"{saat_raw[:2]}:{saat_raw[-2:]}"
        else:
            saat = saat_raw.replace(' ',':').replace('.',':').replace(',',':')
    # Başlık türü bul
    if "toplantı" in text:
        title = "toplantı"
    elif "iş" in text:
        title = "iş"
    elif "görev" in text:
        title = "görev"
    else:
        title = None
    return tarih, saat, title, desc

if __name__ == "__main__":
    system = MainSystem()
    system.run() 