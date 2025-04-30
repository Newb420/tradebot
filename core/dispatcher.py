
import requests, datetime

class Dispatcher:
    def __init__(self, webhook):
        self.webhook = webhook

    def alert(self, msg: str):
        stamp = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{stamp}] {msg}")
        try:
            requests.post(self.webhook, json={"content": msg}, timeout=8)
        except Exception as e:
            print("Discord webhook error:", e)
