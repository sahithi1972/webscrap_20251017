import requests
from bs4 import BeautifulSoup
from database import insert_data

def scrape_crypto():
    url = "https://www.coingecko.com/en"  # Public crypto data website
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get first 5 crypto names and prices
    coins = soup.select("tbody tr")[:5]
    
    for coin in coins:
        name = coin.select_one(".tw-hidden lg:tw-flex font-bold tw-items-center tw-justify-between").text.strip() if coin.select_one(".tw-hidden lg:tw-flex font-bold tw-items-center tw-justify-between") else coin.select_one("td .coin-name").text.strip()
        price = coin.select_one(".td-price .no-wrap").text.strip()
        insert_data(name, price)
    print("Crypto data updated!")
