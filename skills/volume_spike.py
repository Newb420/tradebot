import yfinance as yf
from datetime import datetime, timedelta

class VolumeSpike:
    """
    Alert when current 5-min volume ≥ 2 × 20-bar avg
    and candle body ≥ 0.3 %.
    Adds 'volume' flag to score engine.
    """

    def __init__(self, bus, conf):
        self.bus      = bus
        self.tickers  = conf["tickers"]
        self.span_min = 5
        self.cache    = {}
        bus.register  = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s,t: None)

    def _dl(self, sym):
        end   = datetime.utcnow()
        start = end - timedelta(days=2)
        return yf.download(sym, start=start, end=end,
                           interval=f"{self.span_min}m",
                           progress=False, threads=False)

    async def run_tick(self):
        for sym in self.tickers:
            df = self._dl(sym)
            if df.empty or len(df) < 25:
                continue

            vol_now  = df["Volume"].iloc[-1].item()
            vol_avg  = df["Volume"].tail(21).iloc[:-1].mean().item()

            # skip if avg vol is zero (pre/post-market)
            if vol_avg == 0:
                continue

            open_p  = df["Open"].iloc[-1].item()
            close_p = df["Close"].iloc[-1].item()
            body_pct = abs(close_p - open_p) / open_p if open_p else 0

            if vol_now >= 2 * vol_avg and body_pct >= 0.003:
                ts = df.index[-1]
                if ts != self.cache.get(sym):
                    self.bus.alert(
                        f"💥 {sym} vol-spike {vol_now/vol_avg:.1f}× "
                        f"(body {body_pct*100:.2f} %)"
                    )
                    self.bus.register["score"](sym, "volume")
                    self.cache[sym] = ts
