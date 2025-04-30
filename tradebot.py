import json, asyncio, csv
from pathlib import Path
from core.dispatcher import Dispatcher

# ─── skills ─────────────────────────────────────────────────────────────
from skills import price_band, news_watch, news_filter
import skills.momentum_signals  as momentum_signals
import skills.aligned_momentum  as aligned_momentum
import skills.volume_spike      as volume_spike
import skills.squeeze_momentum  as squeeze_momentum
import skills.daily_squeeze     as daily_squeeze
import skills.htf_trend         as htf_trend
import skills.vix_guard         as vix_guard
import skills.sec_watch         as sec_watch
import skills.tradier_flow      as tradier_flow
import skills.finviz_screener   as finviz_screener
import skills.setup_score       as setup_score

# ─── config & dispatcher ────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
conf = json.load(open(ROOT / "config.json"))
bus  = Dispatcher(conf["webhook"])

# ─── alert logging ───────────────────────────────────────────────────────
log_f = open(ROOT / "alerts_log.csv", "a", newline="")
log_w = csv.writer(log_f)
# write header if empty
if log_f.tell() == 0:
    log_w.writerow(["timestamp_utc", "alert"])
_old_alert = bus.alert
def _logged_alert(msg: str):
    ts = asyncio.get_event_loop().time()  # high-resolution clock, or use datetime.utcnow()
    from datetime import datetime
    log_w.writerow([datetime.utcnow().isoformat(), msg])
    log_f.flush()
    _old_alert(msg)

bus.alert = _logged_alert

# ─── assemble skills ─────────────────────────────────────────────────────
skills = [
    finviz_screener.FinvizScreener(bus, conf),  # universe first
    price_band.PriceBand(bus, conf),
    news_watch.NewsWatch(bus, conf),
    news_filter.NewsFilter(bus, conf),
    momentum_signals.MomentumSignals(bus, conf),
    aligned_momentum.AlignedMomentum(bus, conf),
    volume_spike.VolumeSpike(bus, conf),
    squeeze_momentum.SqueezeMomentum(bus, conf),
    daily_squeeze.DailySqueeze(bus, conf),
    htf_trend.HTFTrend(bus, conf),
    vix_guard.VIXGuard(bus, conf),
    sec_watch.SECWatch(bus, conf),
    tradier_flow.TradierFlow(bus, conf),
    setup_score.SetupScore(bus, conf)
]

# ─── main loop (24×7) ────────────────────────────────────────────────────
async def main():
    interval = conf.get("scan_interval", 60)
    while True:
        await asyncio.gather(*(s.run_tick() for s in skills))
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔌  TradeBot stopped by user. Bye!")
