from data.yahoo import get_headline

KEYWORDS = [
    "upgrade","downgrade","initiates","raises","cuts",
    "beats","misses","guidance","record","acquires",
    "acquisition","merger","offering","buyback","partnership",
    "contract","award","investment","bankruptcy","lawsuit"
]

class NewsFilter:
    """Ping only catalyst headlines (adds 'keyword' flag to score)."""

    def __init__(self, bus, conf):
        self.bus     = bus
        self.tickers = conf["tickers"]
        self.seen    = {}

    async def run_tick(self):
        for sym in self.tickers:
            hl = get_headline(sym)
            if hl and hl != self.seen.get(sym):
                self.seen[sym] = hl
                if any(k in hl.lower() for k in KEYWORDS):
                    self.bus.alert(f"📰🔔 {sym}: {hl}")
                    self.bus.register["score"](sym, "keyword")     # ← flag
