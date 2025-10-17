from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User preferences
    default_stock = db.Column(db.String(10), default='AAPL')
    default_city = db.Column(db.String(50), default='New York')
    default_news_category = db.Column(db.String(20), default='technology')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.String(10))
    conditions = db.Column(db.String(50))
    humidity = db.Column(db.String(10))
    wind = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class StockData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    price = db.Column(db.String(20))
    change = db.Column(db.String(20))
    market_cap = db.Column(db.String(20))
    volume = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class NewsData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    headline = db.Column(db.String(200))
    source = db.Column(db.String(50))
    summary = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)