
from data.yahoo import get_price

class PriceBand:
    def __init__(self, bus, conf):
        self.bus = bus
        self.bands = conf.get("bands", {})
        self.cache = {}

    async def run_tick(self):
        for sym, band in self.bands.items():
            price = get_price(sym)
            if price is None:
                continue
            lo, hi = band.get("lower"), band.get("upper")
            if lo and price < lo and self.cache.get(sym) != "low":
                self.bus.alert(f"🔻 {sym} < {lo}: now ${price}")
                self.cache[sym] = "low"
            elif hi and price > hi and self.cache.get(sym) != "high":
                self.bus.alert(f"🔺 {sym} > {hi}: now ${price}")
                self.cache[sym] = "high"
