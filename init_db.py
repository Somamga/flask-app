import sqlite3

conn = sqlite3.connect('data.db')
c = conn.cursor()

# 名前保存用のテーブル（検索・一覧表示に使う）
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        image_filename TEXT
    )
''')

# ログイン用のテーブル（ログイン機能で使ってたやつ）
c.execute('''
    CREATE TABLE IF NOT EXISTS login_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
