import sqlite3

def get_db():
    conn = sqlite3.connect('scraped_data.db')
    return conn

def insert_headlines(headlines):
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS news (headline TEXT)')
    for h in headlines:
        c.execute('INSERT INTO news (headline) VALUES (?)', (h,))
    conn.commit()
    conn.close()
