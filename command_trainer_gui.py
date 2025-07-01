import tkinter as tk
from tkinter import messagebox, ttk
import csv
import subprocess
import os
import json
from PIL import Image, ImageTk

CSV_PATH = 'voice_commands.csv'
RESPONSES_PATH = 'command_responses.json'
TRAIN_SCRIPT = 'train_voice_command_model.py'

class ModernStyle(ttk.Style):
    def __init__(self):
        super().__init__()
        self.theme_use('clam')
        self.configure('TButton', font=('Segoe UI', 12, 'bold'), padding=10, relief='flat', background='#4F8EF7', foreground='white')
        self.map('TButton', background=[('active', '#356AC3')])
        self.configure('Card.TFrame', background='#ffffff', relief='raised', borderwidth=1)
        self.configure('TLabel', background='#f5f7fa', font=('Segoe UI', 11))
        self.configure('Header.TLabel', font=('Segoe UI', 22, 'bold'), background='#e3ebf7', foreground='#356AC3')
        self.configure('Desc.TLabel', font=('Segoe UI', 12), background='#e3ebf7', foreground='#222')
        self.configure('Treeview', font=('Segoe UI', 11), rowheight=32, fieldbackground='#f5f7fa', background='#f5f7fa')
        self.configure('Treeview.Heading', font=('Segoe UI', 12, 'bold'), background='#e3ebf7', foreground='#356AC3')

class CommandTrainerGUI:
    def __init__(self, root):
        ModernStyle()
        self.root = root
        self.root.title('Sesli Asistan Komut Eğitimi')
        self.root.geometry('820x820')
        self.root.configure(bg='#e3ebf7')

        # Başlık ve ikon
        header_frame = tk.Frame(root, bg='#e3ebf7')
        header_frame.pack(fill='x', pady=(0, 10))
        try:
            img = Image.open('images/assistant_icon.png').resize((60, 60))
            self.icon_img = ImageTk.PhotoImage(img)
            icon_label = tk.Label(header_frame, image=self.icon_img, bg='#e3ebf7')
            icon_label.pack(side='left', padx=(30, 10), pady=10)
        except:
            pass
        title = ttk.Label(header_frame, text='Sesli Asistan Komut Eğitimi', style='Header.TLabel')
        title.pack(side='left', pady=10)

        desc = ttk.Label(root, text='Yeni komutlar ekleyin, mevcutları düzenleyin veya silin. Modeli yeniden eğitmeyi unutmayın!', style='Desc.TLabel')
        desc.pack(pady=(0, 15))

        # Komut ekleme kutusu
        add_frame = ttk.Frame(root, style='Card.TFrame')
        add_frame.pack(fill='x', padx=30, pady=10, ipady=10)
        tk.Label(add_frame, text='Komut Cümlesi:', font=('Segoe UI', 11, 'bold'), bg='#ffffff').grid(row=0, column=0, sticky='e', pady=8, padx=8)
        self.sentence_entry = tk.Entry(add_frame, width=45, font=('Segoe UI', 11), bg='#f5f7fa', relief='flat', highlightthickness=1, highlightbackground='#4F8EF7')
        self.sentence_entry.grid(row=0, column=1, padx=8, pady=8)
        tk.Label(add_frame, text='Etiket:', font=('Segoe UI', 11, 'bold'), bg='#ffffff').grid(row=1, column=0, sticky='e', pady=8, padx=8)
        self.label_entry = tk.Entry(add_frame, width=25, font=('Segoe UI', 11), bg='#f5f7fa', relief='flat', highlightthickness=1, highlightbackground='#4F8EF7')
        self.label_entry.grid(row=1, column=1, padx=8, pady=8, sticky='w')
        tk.Label(add_frame, text='Cevap:', font=('Segoe UI', 11, 'bold'), bg='#ffffff').grid(row=2, column=0, sticky='e', pady=8, padx=8)
        self.response_entry = tk.Entry(add_frame, width=55, font=('Segoe UI', 11), bg='#f5f7fa', relief='flat', highlightthickness=1, highlightbackground='#4F8EF7')
        self.response_entry.grid(row=2, column=1, padx=8, pady=8)
        self.add_button = ttk.Button(add_frame, text='Komutu Ekle', command=self.add_command)
        self.add_button.grid(row=3, column=0, columnspan=2, pady=16)
        self.root.bind('<Return>', lambda event: self.add_command())

        # Komutları kart/kutu şeklinde listele
        list_frame = ttk.Frame(root, style='Card.TFrame')
        list_frame.pack(fill='both', expand=True, padx=30, pady=10)
        self.tree = ttk.Treeview(list_frame, columns=('sentence', 'label', 'response'), show='headings', height=12, style='Treeview')
        self.tree.heading('sentence', text='Komut Cümlesi')
        self.tree.heading('label', text='Etiket')
        self.tree.heading('response', text='Cevap')
        self.tree.column('sentence', width=270)
        self.tree.column('label', width=120)
        self.tree.column('response', width=270)
        self.tree.pack(fill='both', expand=True, side='left', padx=10, pady=10)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Sil ve Düzenle butonları
        btn_frame = tk.Frame(root, bg='#e3ebf7')
        btn_frame.pack(fill='x', padx=30, pady=(0, 10))
        self.delete_button = ttk.Button(btn_frame, text='Seçili Komutu Sil', command=self.delete_command)
        self.delete_button.pack(side='left', padx=8)
        self.edit_button = ttk.Button(btn_frame, text='Seçili Komutu Düzenle', command=self.edit_command)
        self.edit_button.pack(side='left', padx=8)

        # Model eğitme butonu
        self.train_button = ttk.Button(root, text='Modeli Yeniden Eğit', command=self.train_model)
        self.train_button.pack(fill='x', padx=30, pady=18)

        self.selected_item = None
        self.refresh_commands()

    def add_command(self):
        sentence = self.sentence_entry.get().strip()
        label = self.label_entry.get().strip()
        response = self.response_entry.get().strip()
        if not sentence or not label or not response:
            messagebox.showwarning('Eksik Bilgi', 'Lütfen komut, etiket ve cevap girin.')
            return
        if ',' in sentence or ',' in label:
            messagebox.showwarning('Hatalı Giriş', 'Virgül kullanmayınız.')
            return
        with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([sentence, label])
        responses = {}
        if os.path.exists(RESPONSES_PATH):
            with open(RESPONSES_PATH, 'r', encoding='utf-8') as f:
                try:
                    responses = json.load(f)
                except:
                    responses = {}
        responses[label] = response
        with open(RESPONSES_PATH, 'w', encoding='utf-8') as f:
            json.dump(responses, f, ensure_ascii=False, indent=2)
        self.sentence_entry.delete(0, tk.END)
        self.label_entry.delete(0, tk.END)
        self.response_entry.delete(0, tk.END)
        self.refresh_commands()
        messagebox.showinfo('Başarılı', 'Komut ve cevap başarıyla eklendi. Modeli yeniden eğitmeyi unutmayın!')

    def refresh_commands(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        responses = {}
        if os.path.exists(RESPONSES_PATH):
            with open(RESPONSES_PATH, 'r', encoding='utf-8') as f:
                try:
                    responses = json.load(f)
                except:
                    responses = {}
        if not os.path.exists(CSV_PATH):
            return
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    label = row[1]
                    response = responses.get(label, '')
                    self.tree.insert('', tk.END, values=(row[0], label, response))

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_item = selected[0]
        else:
            self.selected_item = None

    def delete_command(self):
        if not self.selected_item:
            messagebox.showwarning('Seçim Yok', 'Lütfen silmek için bir komut seçin.')
            return
        values = self.tree.item(self.selected_item, 'values')
        sentence, label, _ = values
        rows = []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(rows[0])
            for row in rows[1:]:
                if not (row[0] == sentence and row[1] == label):
                    writer.writerow(row)
        if os.path.exists(RESPONSES_PATH):
            with open(RESPONSES_PATH, 'r', encoding='utf-8') as f:
                try:
                    responses = json.load(f)
                except:
                    responses = {}
            if label in responses:
                del responses[label]
            with open(RESPONSES_PATH, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=2)
        self.refresh_commands()
        self.selected_item = None
        messagebox.showinfo('Başarılı', 'Komut başarıyla silindi.')

    def edit_command(self):
        if not self.selected_item:
            messagebox.showwarning('Seçim Yok', 'Lütfen düzenlemek için bir komut seçin.')
            return
        values = self.tree.item(self.selected_item, 'values')
        sentence, label, response = values
        self.sentence_entry.delete(0, tk.END)
        self.sentence_entry.insert(0, sentence)
        self.label_entry.delete(0, tk.END)
        self.label_entry.insert(0, label)
        self.response_entry.delete(0, tk.END)
        self.response_entry.insert(0, response)
        self.delete_command()

    def train_model(self):
        try:
            subprocess.run(['python', TRAIN_SCRIPT], check=True)
            messagebox.showinfo('Başarılı', 'Model başarıyla yeniden eğitildi!')
        except Exception as e:
            messagebox.showerror('Hata', f'Model eğitilemedi: {e}')

if __name__ == '__main__':
    root = tk.Tk()
    app = CommandTrainerGUI(root)
    root.mainloop() 