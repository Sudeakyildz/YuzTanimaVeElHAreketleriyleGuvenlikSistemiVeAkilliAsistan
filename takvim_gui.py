import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

# --- Veritabanı Fonksiyonları ---
def init_db():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_task(title, description, date, time):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (title, description, date, time, completed)
        VALUES (?, ?, ?, ?, 0)
    ''', (title, description, date, time))
    conn.commit()
    conn.close()

def get_tasks_by_date(date):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE date=?', (date,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def mark_task_completed(task_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('UPDATE tasks SET completed=1 WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

# --- GUI Fonksiyonları ---
def show_tasks_for_date(selected_date):
    tasks = get_tasks_by_date(selected_date)
    tasks_list.delete(0, tk.END)
    for t in tasks:
        status = "✓" if t[5] else "✗"
        tasks_list.insert(tk.END, f"{status} {t[3]} {t[4] or ''} - {t[1]}: {t[2] or ''}")

def on_date_select(event):
    selected_date = cal.get_date()
    show_tasks_for_date(selected_date)

def add_task_gui():
    def save_task():
        title = entry_title.get()
        desc = entry_desc.get()
        date = cal.get_date()
        time = entry_time.get()
        if title:
            add_task(title, desc, date, time)
            show_tasks_for_date(date)
            add_win.destroy()
        else:
            messagebox.showwarning("Uyarı", "Başlık boş olamaz!")
    add_win = tk.Toplevel(root)
    add_win.title("Görev Ekle")
    tk.Label(add_win, text="Başlık:").pack()
    entry_title = tk.Entry(add_win)
    entry_title.pack()
    tk.Label(add_win, text="Açıklama:").pack()
    entry_desc = tk.Entry(add_win)
    entry_desc.pack()
    tk.Label(add_win, text="Saat (HH:MM):").pack()
    entry_time = tk.Entry(add_win)
    entry_time.pack()
    tk.Button(add_win, text="Kaydet", command=save_task).pack()

def mark_selected_task_completed():
    selected = tasks_list.curselection()
    if not selected:
        return
    idx = selected[0]
    selected_date = cal.get_date()
    tasks = get_tasks_by_date(selected_date)
    task_id = tasks[idx][0]
    mark_task_completed(task_id)
    show_tasks_for_date(selected_date)

def delete_selected_task():
    selected = tasks_list.curselection()
    if not selected:
        return
    idx = selected[0]
    selected_date = cal.get_date()
    tasks = get_tasks_by_date(selected_date)
    task_id = tasks[idx][0]
    delete_task(task_id)
    show_tasks_for_date(selected_date)

# --- Ana Program ---
init_db()
root = tk.Tk()
root.title("Takvim ve Görev Yöneticisi")

cal = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd', locale='tr_TR')
cal.pack(pady=10)
cal.bind("<<CalendarSelected>>", on_date_select)

tasks_list = tk.Listbox(root, width=80)
tasks_list.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Görev Ekle", command=add_task_gui).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Tamamlandı Olarak İşaretle", command=mark_selected_task_completed).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Görevi Sil", command=delete_selected_task).pack(side=tk.LEFT, padx=5)

show_tasks_for_date(datetime.now().strftime("%Y-%m-%d"))
root.mainloop() 