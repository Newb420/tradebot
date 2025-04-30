import yfinance as yf
from datetime import datetime, timedelta

def _ema(s, span):
    return s.ewm(span=span, adjust=False).mean()

def _momentum(sym, tf):
    """
    Return 'long', 'short', or None for the timeframe.
    """
    end   = datetime.utcnow()
    start = end - timedelta(days=3)
    df = yf.download(sym, start=start, end=end,
                     interval=tf, progress=False, threads=False)
    if df.empty or len(df) < 25:
        return None

    c = df["Close"]; v = df["Volume"]
    ema9  = _ema(c, 9)
    ema21 = _ema(c, 21)
    vwap  = (v * (df["High"] + df["Low"] + c) / 3).cumsum() / v.cumsum()

    # convert comparisons to plain bools with .item()
    above_ema = (ema9.iloc[-1] > ema21.iloc[-1]).item()
    below_ema = (ema9.iloc[-1] < ema21.iloc[-1]).item()
    above_vwap = (c.iloc[-1] > vwap.iloc[-1]).item()
    below_vwap = (c.iloc[-1] < vwap.iloc[-1]).item()

    if above_ema and above_vwap:
        return "long"
    if below_ema and below_vwap:
        return "short"
    return None

class AlignedMomentum:
    """
    Adds 'mtf' flag when BOTH 15-minute and 60-minute momentum agree.
    """

    def __init__(self, bus, conf):
        self.bus      = bus
        self.tickers  = conf["tickers"]
        bus.register  = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    async def run_tick(self):
        for sym in self.tickers:
            m15 = _momentum(sym, "15m")
            h1  = _momentum(sym, "60m")
            if m15 and h1 and m15 == h1:
                self.bus.register["score"](sym, "mtf")
