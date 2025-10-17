import requests
from bs4 import BeautifulSoup

def fetch_data():
    url = "https://example.com/news"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    headlines = [h.text for h in soup.select(".headline")]
    # Return a list of headlines
    return headlines
