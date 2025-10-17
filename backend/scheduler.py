from apscheduler.schedulers.background import BackgroundScheduler
from scraper import fetch_data
from database import insert_headlines

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: insert_headlines(fetch_data()), 'interval', minutes=60)  # every hour
scheduler.start()
