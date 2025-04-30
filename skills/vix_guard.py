import yfinance as yf
from datetime import datetime, timedelta

THRESH   = 25        # risk-off trigger
SYMBOL   = "^VIX"    # CBOE Volatility Index
SPAN_MIN = 5

class VIXGuard:
    """Warns when VIX crosses above / below THRESH."""

    def __init__(self, bus, conf):
        self.bus   = bus
        self.state = None         # None | "risk" | "calm"

    def _dl(self):
        end, start = datetime.utcnow(), datetime.utcnow() - timedelta(days=2)
        return yf.download(SYMBOL, start=start, end=end,
                           interval=f"{SPAN_MIN}m",
                           progress=False, threads=False)

    async def run_tick(self):
        df = self._dl()
        if df.empty or "Close" not in df:
            return

        vix = df["Close"].iloc[-1].item()       # convert to plain float

        if vix >= THRESH and self.state != "risk":
            self.bus.alert(f"⚠️  Risk-OFF: VIX {vix:.2f} (>{THRESH})")
            self.state = "risk"
        elif vix < THRESH and self.state != "calm":
            self.bus.alert(f"✅ Risk back ON: VIX {vix:.2f} (<{THRESH})")
            self.state = "calm"
