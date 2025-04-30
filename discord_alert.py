import requests

# Your Discord webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1366300950104510506/gAxTNC27dDLFnnWC7qwzmpEPlUyk81YLXWkq5Wx_wFXsntE8YBPp7bFoKsoyHHZbbf6X"

# Function to send a Discord alert
def send_discord_alert(message):
    data = {
        "content": message
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Alert sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending alert: {e}")

# Example alert
if __name__ == "__main__":
    send_discord_alert("[TRADEBOT TEST] Example alert from TradeBot 🚨")
