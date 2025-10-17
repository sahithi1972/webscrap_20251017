from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import hashlib
import os
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dashboard-secret-key-2023'

# Database setup
def init_db():
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            default_stock TEXT DEFAULT 'AAPL',
            default_city TEXT DEFAULT 'New York',
            default_news_category TEXT DEFAULT 'technology',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Weather data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            city TEXT,
            temperature TEXT,
            conditions TEXT,
            humidity TEXT,
            wind TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Stock data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            price TEXT,
            change TEXT,
            market_cap TEXT,
            volume TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # News data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            headline TEXT,
            source TEXT,
            summary TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Mock data generators
def get_weather_data(city):
    return {
        'temperature': f'{random.randint(60, 90)}°F',
        'conditions': random.choice(['Sunny', 'Partly Cloudy', 'Cloudy', 'Rainy']),
        'humidity': f'{random.randint(40, 80)}%',
        'wind': f'{random.randint(5, 20)} mph'
    }

def get_stock_data(symbol):
    base_prices = {'AAPL': 182.63, 'GOOGL': 138.21, 'MSFT': 330.80, 'TSLA': 248.50}
    base_price = base_prices.get(symbol, 100 + random.random() * 200)
    change = round(random.uniform(-5, 5), 2)
    change_class = 'positive' if change >= 0 else 'negative'
    return {
        'price': f'${base_price + change:.2f}',
        'change': f'{change:+.2f}',
        'change_class': change_class,
        'market_cap': f'{random.randint(100, 600)}B',
        'volume': f'{random.randint(5, 50)}M'
    }

def get_news_data(category):
    headlines = {
        'technology': [
            "AI Breakthrough Revolutionizes Industry",
            "New Smartphone Launch Breaks Records",
            "Cybersecurity Firm Discovers Vulnerability"
        ],
        'business': [
            "Market Reaches New All-Time High",
            "Startup Secures Record Funding",
            "Economic Forecast Shows Growth"
        ],
        'sports': [
            "Underdog Team Wins Championship",
            "Star Athlete Signs Record Contract",
            "International Tournament Kicks Off"
        ],
        'entertainment': [
            "Blockbuster Film Breaks Box Office Records",
            "Award Show Delivers Surprising Winners",
            "Streaming Service Announces Original Content"
        ]
    }
    return {
        'headline': random.choice(headlines.get(category, headlines['technology'])),
        'source': random.choice(['Reuters', 'Bloomberg', 'Associated Press']),
        'summary': f'Latest news in {category} category with important updates.',
        'published': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('dashboard.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?', 
                 (username, hash_password(password)))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['default_stock'] = user[4]
            session['default_city'] = user[5]
            session['default_news_category'] = user[6]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('dashboard.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            return render_template('register.html', error='Username or email already exists')
        
        # Create new user
        c.execute('''
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        ''', (username, email, hash_password(password)))
        
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        # Auto login after registration
        session['user_id'] = user_id
        session['username'] = username
        session['default_stock'] = 'AAPL'
        session['default_city'] = 'New York'
        session['default_news_category'] = 'technology'
        
        return redirect('/dashboard')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         default_stock=session.get('default_stock', 'AAPL'),
                         default_city=session.get('default_city', 'New York'),
                         default_news_category=session.get('default_news_category', 'technology'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# API Routes
@app.route('/api/weather', methods=['POST'])
def api_weather():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    city = request.json.get('city', session.get('default_city', 'New York'))
    weather_data = get_weather_data(city)
    
    # Save to database
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO weather_data (user_id, city, temperature, conditions, humidity, wind)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], city, weather_data['temperature'], weather_data['conditions'], 
          weather_data['humidity'], weather_data['wind']))
    conn.commit()
    conn.close()
    
    # Update session
    session['default_city'] = city
    
    return jsonify(weather_data)

@app.route('/api/stocks', methods=['POST'])
def api_stocks():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    symbol = request.json.get('symbol', session.get('default_stock', 'AAPL')).upper()
    stock_data = get_stock_data(symbol)
    
    # Save to database
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO stock_data (user_id, symbol, price, change, market_cap, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], symbol, stock_data['price'], stock_data['change'], 
          stock_data['market_cap'], stock_data['volume']))
    conn.commit()
    conn.close()
    
    # Update session
    session['default_stock'] = symbol
    
    return jsonify(stock_data)

@app.route('/api/news', methods=['POST'])
def api_news():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    category = request.json.get('category', session.get('default_news_category', 'technology'))
    news_data = get_news_data(category)
    
    # Save to database
    conn = sqlite3.connect('dashboard.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO news_data (user_id, category, headline, source, summary)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], category, news_data['headline'], news_data['source'], 
          news_data['summary']))
    conn.commit()
    conn.close()
    
    # Update session
    session['default_news_category'] = category
    
    return jsonify(news_data)

# Initialize database
init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)