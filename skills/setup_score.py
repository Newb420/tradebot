class SetupScore:
    """
    Aggregates flags dropped via bus.register['score'].
    Fires an alert once when score ≥ THRESHOLD, then resets.
    """

    WEIGHTS = {
        "ema_vwap": 3,
        "volume"  : 2,
        "squeeze" : 3,
        "keyword" : 2,
        "htf"     : 2,   # higher-time-frame trend
        "mtf"     : 2,   # multi-TF momentum
        "flow"    : 2,   # options-flow sweep
        "finviz"  : 2    # Finviz catalyst
    }
    THRESHOLD = 7

    def __init__(self, bus, conf):
        self.bus   = bus
        self.flags = {sym: set() for sym in conf["tickers"]}
        bus.register = getattr(bus, "register", {})
        bus.register["score"] = self.flag

    def flag(self, sym, tag):
        if tag in self.WEIGHTS:
            self.flags[sym].add(tag)

    async def run_tick(self):
        for sym, tags in self.flags.items():
            score = sum(self.WEIGHTS[t] for t in tags)
            if score >= self.THRESHOLD:
                eta = (
                    "1-5 d"     if "htf" in tags else
                    "30-90 min" if "mtf" in tags else
                    "intraday"
                )
                self.bus.alert(
                    f"✅ {sym} setup-score {score}  "
                    f"[{', '.join(sorted(tags))}] | ETA {eta}"
                )
                self.flags[sym].clear()
