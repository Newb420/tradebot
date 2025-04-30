import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class DailySqueeze:
    """
    Daily-chart TTM Squeeze; fires once per symbol when the squeeze releases.
    Adds 'htf' flag to the score engine (swing timeframe).
    """

    def __init__(self, bus, conf):
        self.bus     = bus
        self.tickers = conf["tickers"]
        self.state   = {}                      # {sym: in_squeeze_bool}
        bus.register = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s,t: None)

    def _dl(self, sym):
        end, start = datetime.utcnow(), datetime.utcnow() - timedelta(days=400)
        return yf.download(sym, start=start, end=end,
                           interval="1d", progress=False, threads=False)

    async def run_tick(self):
        for sym in self.tickers:
            df = self._dl(sym)
            if df.empty or len(df) < 40:
                continue

            c, h, l = df["Close"], df["High"], df["Low"]
            mid = c.rolling(20).mean()
            bb_w = (mid + 2*c.rolling(20).std()) - (mid - 2*c.rolling(20).std())

            tr   = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
            kc_w = 1.5 * tr.rolling(20).mean()

            in_sq_now = (bb_w.iloc[-1] < kc_w.iloc[-1]).item()

            if sym not in self.state:
                self.state[sym] = in_sq_now
                continue

            if in_sq_now:
                self.state[sym] = True
            elif self.state[sym]:                    # just released
                price = c.iloc[-1].item()
                self.bus.alert(f"📆 {sym} DAILY squeeze RELEASE – {price:.2f}")
                self.bus.register["score"](sym, "htf")
                self.state[sym] = False
