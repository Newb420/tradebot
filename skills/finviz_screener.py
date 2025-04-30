# skills/finviz_screener.py

import json, requests, pandas as pd, time
from pathlib import Path
from datetime import date
from io import StringIO
from requests.exceptions import HTTPError

# ─── CONFIG ──────────────────────────────────────────────────────────────
MIN_PRICE    = 5
MIN_VOLUME   = 1_000_000    # shares/day
MIN_SHORT    = 10           # % float short
MAX_SYMBOLS  = 150          # universe size
CACHE_PATH   = Path("finviz_cache.json")
USER_AGENT   = "Mozilla/5.0"
# ─────────────────────────────────────────────────────────────────────────

class FinvizScreener:
    """
    • Runs once at startup.
    • Loads tickers from cache if today's list exists.
    • Otherwise pulls up to MAX_SYMBOLS via page-fetches, caches result.
    • Flags 'finviz' on Earnings-This-Week or Insider-Buy.
    """

    def __init__(self, bus, conf):
        self.bus   = bus
        self.conf  = conf
        self._done = False
        bus.register = getattr(bus, "register", {})
        bus.register.setdefault("score", lambda s, t: None)

    def _load_cache(self):
        if not CACHE_PATH.exists():
            return None
        data = json.loads(CACHE_PATH.read_text())
        if data.get("date") == str(date.today()):
            return data.get("tickers", [])
        return None

    def _write_cache(self, tickers):
        CACHE_PATH.write_text(
            json.dumps({"date": str(date.today()), "tickers": tickers})
        )

    def _fetch_pages(self):
        """Fetch up to MAX_SYMBOLS from Finviz screener, throttled, table-guarded."""
        base = "https://finviz.com/screener.ashx?v=111"
        filters = (
            f"&f=sh_avgvol_o{int(MIN_VOLUME/1_000_000)}"
            f",sh_price_o{MIN_PRICE}"
            f",sh_short_o{MIN_SHORT}"
        )
        per_page = 20
        pages    = (MAX_SYMBOLS + per_page - 1) // per_page
        all_rows = []
        headers  = {"User-Agent": USER_AGENT}

        for page in range(pages):
            start = page * per_page + 1
            url   = f"{base}{filters}&r={start}"

            # back off on 429
            while True:
                r = requests.get(url, headers=headers, timeout=10)
                try:
                    r.raise_for_status()
                    break
                except HTTPError:
                    if r.status_code == 429:
                        time.sleep(5)
                        continue
                    else:
                        raise

            # parse only the table that contains 'Ticker'
            tables = pd.read_html(StringIO(r.text))
            df = next((t for t in tables if "Ticker" in t.columns), None)
            if df is not None:
                all_rows.append(df)
            else:
                print(f"[Finviz] warning: no Ticker column on page {page+1}")

            time.sleep(1)  # throttle

        full = pd.concat(all_rows, ignore_index=True)
        symbols = full["Ticker"].tolist()[:MAX_SYMBOLS]
        return symbols, full

    async def run_tick(self):
        if self._done:
            return
        self._done = True

        # 1) try cache
        cached = self._load_cache()
        if cached:
            self.conf["tickers"].clear()
            self.conf["tickers"].extend(cached)
            self.bus.alert(f"📋 Finviz universe loaded from cache ({len(cached)} tickers)")
            symbols, full_df = self._fetch_pages()
        else:
            # 2) fresh pull
            print(f"↻  Finviz screener pulling fresh ({MAX_SYMBOLS} symbols)…")
            symbols, full_df = self._fetch_pages()
            self.conf["tickers"].clear()
            self.conf["tickers"].extend(symbols)
            self._write_cache(symbols)
            self.bus.alert(f"📋 Finviz universe pulled ({len(symbols)} tickers)")

        # 3) catalyst tagging
        full_df = full_df.set_index("Ticker")
        for sym in self.conf["tickers"]:
            row = full_df.loc[sym]
            if row["Earnings"].startswith("This"):
                self.bus.register["score"](sym, "finviz")
            elif row["Insider Trans"].startswith("Buy"):
                self.bus.register["score"](sym, "finviz")
