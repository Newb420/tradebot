import requests
from bs4 import BeautifulSoup
import time

# ─── user settings ──────────────────────────────────────────────────────
WEBHOOK_URL   = "https://discord.com/api/webhooks/1366300950104510506/gAxTNC27dDLFnnWC7qwzmpEPlUyk81YLXWkq5Wx_wFXsntE8YBPp7bFoKsoyHHZbbf6X"
SYMBOL        = "GME"

LOWER_ALERT   = 27.00   # send alert if price drops below
UPPER_ALERT   = 28.00   # send alert if price rises above
CHECK_INTERVAL = 60     # seconds between checks
# ────────────────────────────────────────────────────────────────────────

last_headline = None      # dedupe headline alerts

def send_discord_alert(msg: str):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=8).raise_for_status()
        print("Alert sent:", msg)
    except Exception as e:
        print("Discord error:", e)

def get_price_from_yahoo(sym: str):
    try:
        url = f"https://finance.yahoo.com/quote/{sym}"
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).text
        tag  = BeautifulSoup(html, "lxml").find("fin-streamer", {"data-field": "regularMarketPrice"})
        if tag:
            price = float(tag.text.replace(",", ""))
            # ── sanity filter ── ignore bogus pre/post-market glitches
            if 0.50 < price < 500:
                return price
    except Exception as e:
        print("Price fetch error:", e)
    return None

def get_latest_headline(sym: str):
    try:
        url  = f"https://finance.yahoo.com/quote/{sym}?p={sym}"
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).text
        tag  = BeautifulSoup(html, "lxml").find("h3", {"class": "Mb(5px)"})
        if tag:
            return tag.text.strip()
    except Exception as e:
        print("Headline fetch error:", e)
    return None

# ─── main loop ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Starting Yahoo Scanner Bot for {SYMBOL} …")
    while True:
        price = get_price_from_yahoo(SYMBOL)
        if price is not None:
            print(f"Current {SYMBOL} price: ${price}")
            if price < LOWER_ALERT:
                send_discord_alert(f"🚨 {SYMBOL} dropped below ${LOWER_ALERT}: now ${price}")
            elif price > UPPER_ALERT:
                send_discord_alert(f"🚀 {SYMBOL} broke above ${UPPER_ALERT}: now ${price}")

        headline = get_latest_headline(SYMBOL)
        if headline and headline != last_headline:
            send_discord_alert(f"📰 {SYMBOL} headline: {headline}")
            last_headline = headline

        time.sleep(CHECK_INTERVAL)
