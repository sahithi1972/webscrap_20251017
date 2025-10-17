from flask import Flask, render_template
from database import init_db, fetch_data
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_crypto

app = Flask(__name__)
init_db()

# Schedule scraper every 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_crypto, trigger="interval", minutes=10)
scheduler.start()

@app.route('/')
def index():
    data = fetch_data()
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
