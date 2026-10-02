"""
01_download_data_strategyC.py
MFE 230GB Final Project - Strategy C: Crypto Carry (perpetual futures funding rates)

Downloads from Binance's public data archive (data.binance.vision), no API key:
  - USDT-margined perpetual futures funding rates (every 8h) -> daily sum
  - Daily perpetual futures klines (close price, quote volume)

Why the archive and not the live API: the Binance trading API blocks US IP
addresses, but the public bulk-data archive is static files.

Universe: large coins with perpetuals listed by ~2020-2021, INCLUDING coins that
were later delisted or renamed (LUNA, FTT, MATIC) to limit survivorship bias.
Months before a coin was listed (or after delisting) return HTTP 404 - that is
expected and cached so re-runs are fast.

Outputs (data/clean/):
  crypto_close_daily.csv          perpetual close price (USDT)
  crypto_quote_volume_daily.csv   daily traded volume in USDT (liquidity filter)
  crypto_funding_daily.csv        sum of funding rates paid per day (decimal)
                                  positive = longs pay shorts

Requirements: pip install pandas requests
Run from the project root:  python code/01_download_data_strategyC.py
"""

import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw/binance")
CLEAN = Path("data/clean")
for d in (RAW, CLEAN):
    d.mkdir(parents=True, exist_ok=True)

BASE = "https://data.binance.vision/data/futures/um/monthly"
HEADERS = {"User-Agent": "Mozilla/5.0 (MFE230GB course project)"}
START, END = "2020-01", "2026-08"   # monthly files; extend END as months complete

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "SOLUSDT",
    "LTCUSDT", "LINKUSDT", "AVAXUSDT",
    # delisted / renamed - kept to reduce survivorship bias
    "LUNAUSDT", "FTTUSDT",
    "USDCUSDT",  # stablecoin: sanity check only, excluded from the carry ranking
]

KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume",
              "ignore"]


def fetch(url: str, dest: Path):
    """Download once and cache. Empty file = cached 404 (not available)."""
    if dest.exists():
        return dest if dest.stat().st_size > 0 else None
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code == 404:
        dest.write_bytes(b"")
        return None
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def read_zip(path: Path) -> pd.DataFrame:
    """Read the CSV inside a Binance zip; older files have no header row."""
    with zipfile.ZipFile(path) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), header=None, low_memory=False)
    if pd.isna(pd.to_numeric(df.iloc[0, 0], errors="coerce")):
        df = df.iloc[1:]
    return df.apply(pd.to_numeric, errors="coerce")


def to_datetime_utc(ms: pd.Series) -> pd.Series:
    """Binance timestamps are milliseconds (some newer files use microseconds)."""
    unit = "us" if ms.dropna().iloc[0] > 1e14 else "ms"
    return pd.to_datetime(ms, unit=unit, utc=True)


def months():
    return [p.strftime("%Y-%m") for p in pd.period_range(START, END, freq="M")]


def download_symbol(sym: str):
    closes, vols, funding = [], [], []
    for m in months():
        # daily klines
        f = fetch(f"{BASE}/klines/{sym}/1d/{sym}-1d-{m}.zip",
                  RAW / "klines" / sym / f"{sym}-1d-{m}.zip")
        if f:
            k = read_zip(f).iloc[:, :len(KLINE_COLS)]
            k.columns = KLINE_COLS[:k.shape[1]]
            d = to_datetime_utc(k["open_time"]).dt.tz_localize(None).dt.normalize()
            closes.append(pd.Series(k["close"].values, index=d))
            vols.append(pd.Series(k["quote_volume"].values, index=d))
        # funding rates (first column = time, last column = rate)
        f = fetch(f"{BASE}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip",
                  RAW / "funding" / sym / f"{sym}-fundingRate-{m}.zip")
        if f:
            fr = read_zip(f)
            t = to_datetime_utc(fr.iloc[:, 0]).dt.tz_localize(None).dt.normalize()
            funding.append(pd.Series(fr.iloc[:, -1].values, index=t))

    def combine(parts, how):
        if not parts:
            return pd.Series(dtype=float)
        s = pd.concat(parts)
        return s.groupby(level=0).sum() if how == "sum" else s.groupby(level=0).last()

    return combine(closes, "last"), combine(vols, "last"), combine(funding, "sum")


def main():
    close, vol, fund = {}, {}, {}
    for i, sym in enumerate(SYMBOLS, 1):
        print(f"[{i}/{len(SYMBOLS)}] {sym} ...", end=" ", flush=True)
        c, v, f = download_symbol(sym)
        name = sym.replace("USDT", "")
        if c.empty:
            print("no data")
            continue
        close[name], vol[name], fund[name] = c, v, f
        print(f"{c.index.min():%Y-%m-%d} to {c.index.max():%Y-%m-%d}, "
              f"{len(c)} days, funding obs {len(f)}")

    for label, d in (("crypto_close_daily.csv", close),
                     ("crypto_quote_volume_daily.csv", vol),
                     ("crypto_funding_daily.csv", fund)):
        df = pd.DataFrame(d).sort_index()
        df.index.name = "date"
        df.to_csv(CLEAN / label)

    f = pd.DataFrame(fund)
    print("\n=== Sanity checks ===")
    print(f"Coins with data: {len(close)}")
    print("Average annualized funding rate (%), by coin:")
    print((100 * 365 * f.mean()).round(1).sort_values().to_string())
    print("\nDone. Clean files are in data/clean/")


if __name__ == "__main__":
    main()
