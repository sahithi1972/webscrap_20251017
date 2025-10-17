# ...existing code...
import os
import re
import time
import logging
import secrets
from flask import Flask, jsonify, send_from_directory, request, Response
from werkzeug.security import generate_password_hash, check_password_hash
from bs4 import BeautifulSoup
import requests

# serve frontend files (index.html, style.css, script.js) from ../frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""  # serve static files at root so /style.css, /script.js work
)

DATA = []
LAST_FETCH = 0
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0.0.0 Safari/537.36"
}
IMDB_TOP_URL = "https://www.imdb.com/chart/top/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- simple demo authentication (in-memory) ---
USERS = {
    # change password here if needed
    "admin": generate_password_hash("secret123")
}
SESSIONS = {}  # token -> username

def require_token(req):
    auth = req.headers.get("Authorization", "")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        user = SESSIONS.get(token)
        if user:
            return user
    return None

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"message": "username and password required"}), 400
    pw_hash = USERS.get(username)
    if not pw_hash or not check_password_hash(pw_hash, password):
        return jsonify({"message": "invalid credentials"}), 401
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = username
    logger.info("User %s logged in (token=%s)", username, token)
    return jsonify({"token": token, "user": username})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    user = require_token(request)
    if not user:
        return jsonify({"status": "ok"}), 200
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1].strip()
    SESSIONS.pop(token, None)
    logger.info("User %s logged out (token=%s)", user, token)
    return jsonify({"status": "logged_out"})

@app.route("/api/auth/check")
def api_auth_check():
    user = require_token(request)
    if not user:
        return jsonify({"message":"unauthenticated"}), 401
    return jsonify({"user": user})

def fetch_imdb_data(force=False, timeout=10):
    """
    Fetch Top 250 from IMDb and populate DATA.
    - Caches results for 10 minutes unless force=True.
    - Extracts imdb_id and imdb link where available.
    """
    global DATA, LAST_FETCH
    if not force and (time.time() - LAST_FETCH) < 600 and DATA:
        return DATA

    try:
        resp = requests.get(IMDB_TOP_URL, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch IMDb page: %s", e)
        return DATA

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tbody.lister-list tr")
    parsed = []
    id_re = re.compile(r"/title/(tt\d+)/")
    for row in rows:
        title_col = row.find("td", class_="titleColumn")
        if not title_col:
            continue

        # rank (e.g., "1.")
        rank_text = title_col.get_text(" ", strip=True).split()[0]
        try:
            place = int(rank_text.strip('.'))
        except Exception:
            place = None

        a = title_col.find("a")
        movie_title = a.get_text(strip=True) if a else ""
        href = a.attrs.get("href", "") if a and a.has_attr("href") else ""
        imdb_id = None
        match = id_re.search(href)
        if match:
            imdb_id = match.group(1)
        imdb_link = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None

        year_tag = title_col.find("span", class_="secondaryInfo")
        year = year_tag.get_text(strip=True).strip("()") if year_tag else ""

        star_cast = a.attrs.get("title", "") if a and a.has_attr("title") else ""

        rating_col = row.find("td", class_="ratingColumn imdbRating")
        rating = None
        if rating_col:
            strong = rating_col.find("strong")
            if strong and strong.get_text(strip=True):
                try:
                    rating = round(float(strong.get_text(strip=True)), 1)
                except Exception:
                    rating = None

        parsed.append({
            "place": place,
            "movie_title": movie_title,
            "rating": rating,
            "year": year,
            "star_cast": star_cast,
            "imdb_id": imdb_id,
            "link": imdb_link
        })

    DATA = parsed
    LAST_FETCH = time.time()
    logger.info("Fetched %d movies from IMDb", len(DATA))
    return DATA

# Serve login page at /login.html (fallback to index.html if login.html missing)
@app.route("/login.html")
def serve_login():
    login_path = os.path.join(FRONTEND_DIR, "login.html")
    if os.path.exists(login_path):
        return send_from_directory(FRONTEND_DIR, "login.html")
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"error":"login page not found"}), 404

# Dashboard entrypoint at /
@app.route("/")
def index():
    # prefer a dedicated dashboard file if present
    dash_path = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(dash_path):
        return send_from_directory(FRONTEND_DIR, "dashboard.html")

    # if there's an index.html that is clearly a dashboard (heuristic),
    # serve it. Otherwise, generate a minimal dashboard page that loads
    # the frontend assets (style.css + script.js).
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        # Heuristic: if index.html contains 'login-form' treat it as login -> redirect to /login.html
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                txt = f.read(4096)
                if "login-form" in txt or "login-page" in txt or "Sign in" in txt:
                    # serve login at /login.html and redirect here to that path so client sees consistent URL
                    return send_from_directory(FRONTEND_DIR, "index.html")
        except Exception:
            pass
        # fallback serve index.html
        return send_from_directory(FRONTEND_DIR, "index.html")

    # If no frontend files exist, return a minimal generated dashboard page
    generated = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IMDb Top 10 — Dashboard</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="topbar">
  <div class="brand"><h1>IMDb Top 10</h1></div>
  <div class="actions">
    <button id="refresh-btn" class="btn">Refresh</button>
    <button id="logout-btn" class="btn btn-ghost">Logout</button>
  </div>
</header>
<main class="container">
  <section id="status" class="status hidden"></section>
  <section id="movies-container" class="grid"></section>
  <div id="empty" class="empty hidden">No movies available.</div>
</main>
<footer class="footer"><small>Data fetched from IMDb</small></footer>
<script src="/script.js"></script>
</body>
</html>"""
    return Response(generated, mimetype="text/html")

@app.route("/update", methods=["GET"])
def update_data():
    # require token to trigger update
    user = require_token(request)
    if not user:
        return jsonify({"message": "unauthenticated"}), 401
    fetch_imdb_data(force=True)
    return jsonify({"status": "updated", "count": len(DATA)})

@app.route("/api/movies")
def api_movies():
    # require authenticated token
    user = require_token(request)
    if not user:
        return jsonify({"message":"unauthenticated"}), 401
    if not DATA:
        fetch_imdb_data()
    # return top N (dashboard will slice to top 10)
    return jsonify({"count": len(DATA), "movies": DATA})

if __name__ == "__main__":
    try:
        fetch_imdb_data()
    except Exception:
        logger.exception("Initial fetch failed (continuing to run)")
    # run on localhost only for development
    app.run(debug=True, host="127.0.0.1", port=5000)
# ...existing code...