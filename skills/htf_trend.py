import yfinance as yf
from datetime import datetime, timedelta

class HTFTrend:
    """
    Adds 'htf' flag when both 1-hour and Daily 20-EMA trends
    align with the 5-minute trade direction.
    """

    def __init__(self, bus, conf):
        self.bus      = bus
        self.tickers  = conf["tickers"]
        bus.register  = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    # ── helper ──────────────────────────────────────────────
    def _aligned(self, sym, tf):
        end, start = datetime.utcnow(), datetime.utcnow() - timedelta(days=120)
        df = yf.download(sym, start=start, end=end,
                         interval=tf, progress=False, threads=False)
        if df.empty or len(df) < 25:
            return None
        price = df["Close"].iloc[-1].item()
        ema20 = df["Close"].ewm(span=20, adjust=False).mean().iloc[-1].item()
        return "long" if price > ema20 else "short"

    async def run_tick(self):
        for sym in self.tickers:
            h1  = self._aligned(sym, "60m")
            day = self._aligned(sym, "1d")
            if h1 and day and h1 == day:
                self.bus.register["score"](sym, "htf")
