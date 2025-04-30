import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class SqueezeMomentum:
    """
    5-minute TTM Squeeze; adds 'squeeze' flag when it fires.
    """

    def __init__(self, bus, conf):
        self.bus     = bus
        self.tickers = conf["tickers"]
        self.state   = {}                       # {sym: {"in": bool, "dir": str}}
        bus.register = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    def _dl(self, sym):
        end, start = datetime.utcnow(), datetime.utcnow() - timedelta(days=5)
        return yf.download(sym, start=start, end=end,
                           interval="5m", progress=False, threads=False)

    @staticmethod
    def _mom(src, n=12): return src.diff(n)

    async def run_tick(self):
        for sym in self.tickers:
            df = self._dl(sym)
            if df.empty or len(df) < 25:
                continue

            c, h, l = df["Close"], df["High"], df["Low"]
            mid = c.rolling(20).mean()
            bb_w = (mid + 2*c.rolling(20).std()) - (mid - 2*c.rolling(20).std())

            tr  = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
            kc_w = 1.5 * tr.rolling(20).mean()

            in_sq_now = (bb_w.iloc[-1] < kc_w.iloc[-1]).item()     # ← bool
            mom_now   = self._mom(c).iloc[-1].item()

            st = self.state.setdefault(sym, {"in": False, "dir": None})

            if in_sq_now:
                st["in"] = True
            elif st["in"]:                                 # exited squeeze
                price = c.iloc[-1].item()
                if mom_now > 0 and st["dir"] != "long":
                    self.bus.alert(f"📊 {sym} squeeze-fire LONG – {price:.2f}")
                    self.bus.register["score"](sym, "squeeze")
                    st["in"], st["dir"] = False, "long"
                elif mom_now < 0 and st["dir"] != "short":
                    self.bus.alert(f"📊 {sym} squeeze-fire SHORT – {price:.2f}")
                    self.bus.register["score"](sym, "squeeze")
                    st["in"], st["dir"] = False, "short"
