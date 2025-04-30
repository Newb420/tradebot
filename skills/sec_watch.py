import feedparser

FORM_KEYS = [
    "8-K","10-Q","10-K","S-1","S-3","424B","F-1",
    "144","S-8","FWP","FORM 4","SC 13","SHELF"
]

class SECWatch:
    """
    Poll SEC Atom feed; alert on first matching filing.
    Adds 'keyword' flag to score engine.
    """
    URL = ("https://www.sec.gov/cgi-bin/browse-edgar?"
           "action=getcompany&CIK={}&owner=include&count=10&output=atom")

    def __init__(self, bus, conf):
        self.bus     = bus
        self.tickers = conf["tickers"]
        self.seen    = {}
        bus.register = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    def _feed(self, sym):
        return feedparser.parse(self.URL.format(sym))

    async def run_tick(self):
        for sym in self.tickers:
            try:
                feed = self._feed(sym)
                if not feed.entries:
                    continue
                seen = self.seen.setdefault(sym, set())
                for entry in feed.entries[:3]:
                    if entry.id in seen:
                        continue
                    title = entry.title
                    if any(k.lower() in title.lower() for k in FORM_KEYS):
                        self.bus.alert(f"📄 {sym} SEC filing: {title}")
                        self.bus.register["score"](sym, "keyword")
                        seen.add(entry.id)
            except Exception as e:
                print(f"SEC feed error {sym}: {e}")
