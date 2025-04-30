# data/yahoo.py
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_price(symbol: str):
    """
    Scrape Yahoo Finance and return a *sane* price:
    • Ignore if price < $0.50 or > $500.
    • Return None on any error.
    """
    try:
        html = requests.get(
            f"https://finance.yahoo.com/quote/{symbol}",
            headers=HEADERS, timeout=8
        ).text
        tag = BeautifulSoup(html, "lxml").find(
            "fin-streamer", {"data-field": "regularMarketPrice"}
        )
        if tag:
            price = float(tag.text.replace(",", ""))
            if 0.50 < price < 500:          # sanity guard
                return price
    except Exception as e:
        print("Yahoo price error:", e)
    return None

def get_headline(symbol: str):
    """Return latest Yahoo headline or None."""
    try:
        html = requests.get(
            f"https://finance.yahoo.com/quote/{symbol}?p={symbol}",
            headers=HEADERS, timeout=8
        ).text
        tag = BeautifulSoup(html, "lxml").find("h3", {"class": "Mb(5px)"})
        return tag.text.strip() if tag else None
    except Exception as e:
        print("Yahoo headline error:", e)
        return None
