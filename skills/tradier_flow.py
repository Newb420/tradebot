import requests, asyncio

MIN_PREMIUM = 50_000        # $50k filter

LIVE_URL     = "https://api.tradier.com/v1/markets/events"
SANDBOX_URL  = "https://sandbox.tradier.com/v1/markets/events"

HEADERS = {
    "Accept":        "application/json",
    "Authorization": "Bearer {token}"
}

def _premium(trd):           # helper
    return trd["price"] * trd["quantity"] * 100

class TradierFlow:
    """
    Polls Tradier option-trade events once per run_tick.
    Fires 🐳 alert when a single trade ≥ MIN_PREMIUM, tags 'flow'.
    """

    def __init__(self, bus, conf):
        self.bus      = bus
        self.key      = conf["tradier_key"]
        self.url      = LIVE_URL if conf.get("tradier_live") else SANDBOX_URL
        self.tickers  = [s.upper() for s in conf["tickers"]]
        self.last_id  = {}
        bus.register  = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    async def run_tick(self):
        hdrs = {k: v.format(token=self.key) for k, v in HEADERS.items()}
        for sym in self.tickers:
            try:
                params = {"symbols": sym, "types": "trade"}
                r = requests.get(self.url, headers=hdrs, params=params, timeout=8)
                if r.status_code != 200:
                    continue
                trades = r.json().get("events", {}).get("trade", [])
                if not trades:
                    continue

                t = trades[0]                       # most recent
                if t["id"] == self.last_id.get(sym):
                    continue
                self.last_id[sym] = t["id"]

                prem = _premium(t)
                if prem < MIN_PREMIUM:
                    continue

                side   = "CALL" if t["option_type"] == "call" else "PUT"
                strike = t["strike"]; exp = t["expiration_date"]; qty = t["quantity"]
                self.bus.alert(f"🐳 {sym} {side} {strike} {exp} – ${prem/1_000:.1f}k ({qty}c)")
                self.bus.register["score"](sym, "flow")

            except Exception as e:
                print(f"Tradier flow error {sym}: {e}")
            await asyncio.sleep(0)        # yield to event loop
