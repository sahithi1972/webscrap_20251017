import sqlite3

def init_db():
    conn = sqlite3.connect("crypto.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS crypto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(name, price):
    conn = sqlite3.connect("crypto.db")
    c = conn.cursor()
    c.execute("INSERT INTO crypto (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()

def fetch_data():
    conn = sqlite3.connect("crypto.db")
    c = conn.cursor()
    c.execute("SELECT name, price, last_updated FROM crypto ORDER BY last_updated DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return rows
