
from data.yahoo import get_headline

class NewsWatch:
    def __init__(self, bus, conf):
        self.bus = bus
        self.tickers = conf.get("tickers", [])
        self.seen = {}

    async def run_tick(self):
        for sym in self.tickers:
            hl = get_headline(sym)
            if hl and hl != self.seen.get(sym):
                self.seen[sym] = hl
                self.bus.alert(f"📰 {sym}: {hl}")
