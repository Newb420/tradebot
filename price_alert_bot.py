import requests
import time
from datetime import datetime
import pytz

# Your TwelveData API key
API_KEY = "e14ad734262e45cca5efb0aed08a2175"

# Your Discord webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1366300950104510506/gAxTNC27dDLFnnWC7qwzmpEPlUyk81YLXWkq5Wx_wFXsntE8YBPp7bFoKsoyHHZbbf6X"

# Stock symbol to monitor
SYMBOL = "GME"

# Price thresholds
LOWER_ALERT = 27.00  # Alert if price drops below this
UPPER_ALERT = 28.00  # Alert if price rises above this

# Time between checks (in seconds) — 120 sec = 2 minutes
CHECK_INTERVAL = 120

def send_discord_alert(message):
    data = {
        "content": message
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
        print(f"Alert sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending alert: {e}")

def get_gme_price():
    url = f"https://api.twelvedata.com/price?symbol={SYMBOL}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def is_market_open():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    current_time = now.time()

    market_open = datetime.strptime("09:30", "%H:%M").time()
    market_close = datetime.strptime("16:00", "%H:%M").time()

    return market_open <= current_time <= market_close

if __name__ == "__main__":
    print("Starting TradeBot with market hours check...")
    while True:
        if is_market_open():
            price = get_gme_price()
            if price:
                print(f"Current {SYMBOL} price: ${price}")
                if price < LOWER_ALERT:
                    send_discord_alert(f"🚨 {SYMBOL} dropped below ${LOWER_ALERT}: Current Price ${price}")
                elif price > UPPER_ALERT:
                    send_discord_alert(f"🚀 {SYMBOL} broke above ${UPPER_ALERT}: Current Price ${price}")
        else:
            print("Market is closed — sleeping.")
        time.sleep(CHECK_INTERVAL)
