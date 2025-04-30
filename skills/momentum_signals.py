import yfinance as yf
from datetime import datetime, timedelta

def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

class MomentumSignals:
    """
    5-minute momentum:
      • 9-EMA vs 21-EMA cross
      • price above / below VWAP
      • volume ≥ 2 × 20-bar avg
    Adds 'ema_vwap' flag for the score engine.
    """

    def __init__(self, bus, conf):
        self.bus      = bus
        self.tickers  = conf["tickers"]
        self.sent     = {}
        self.span_min = 5

        # ensure score hook exists
        bus.register = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    # ── helper ──────────────────────────────────────────────
    def _dl(self, sym):
        end   = datetime.utcnow()
        start = end - timedelta(days=2)
        return yf.download(sym, start=start, end=end,
                           interval=f"{self.span_min}m",
                           progress=False, threads=False)

    # ── main tick ───────────────────────────────────────────
    async def run_tick(self):
        for sym in self.tickers:
            df = self._dl(sym)
            if df.empty or len(df) < 25:
                continue

            c = df["Close"]; v = df["Volume"]
            ema9  = _ema(c, 9)
            ema21 = _ema(c, 21)
            vwap  = (v * (df["High"] + df["Low"] + c) / 3).cumsum() / v.cumsum()

            # pandas 2.2 scalar -> bool with .item()
            cross_up = (
                (ema9.iloc[-1] > ema21.iloc[-1]).item() and
                (ema9.shift(1).iloc[-1] <= ema21.shift(1).iloc[-1]).item()
            )
            cross_down = (
                (ema9.iloc[-1] < ema21.iloc[-1]).item() and
                (ema9.shift(1).iloc[-1] >= ema21.shift(1).iloc[-1]).item()
            )

            over_vwap  = (c.iloc[-1] > vwap.iloc[-1]).item()
            vol_spike  = v.iloc[-1] >= 2 * v.tail(21).iloc[:-1].mean()

            st = self.sent.setdefault(sym, {"bull": False, "bear": False})

            if cross_up and over_vwap and vol_spike and not st["bull"]:
                price = c.iloc[-1]
                self.bus.alert(f"🟢 {sym} momentum setup – {price:.2f}")
                self.bus.register["score"](sym, "ema_vwap")
                st.update(bull=True, bear=False)

            if cross_down and (not over_vwap) and vol_spike and not st["bear"]:
                price = c.iloc[-1]
                self.bus.alert(f"🔴 {sym} momentum setup – {price:.2f}")
                self.bus.register["score"](sym, "ema_vwap")
                st.update(bear=True, bull=False)
