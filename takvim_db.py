import sqlite3
from datetime import datetime

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

def get_last_task():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('SELECT * FROM tasks ORDER BY id DESC LIMIT 1')
    task = c.fetchone()
    conn.close()
    return task

def get_meetings_by_date(date):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE date=? AND title LIKE ?", (date, '%toplantı%'))
    meetings = c.fetchall()
    conn.close()
    return meetings

def get_all_tasks_by_date(date):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE date=?", (date,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def get_task_by_datetime(date, time, title=None):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    if title:
        c.execute("SELECT * FROM tasks WHERE date=? AND time=? AND title LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1", (date, time, f"%{title}%"))
    else:
        c.execute("SELECT * FROM tasks WHERE date=? AND time=? ORDER BY id DESC LIMIT 1", (date, time))
    task = c.fetchone()
    conn.close()
    return task 