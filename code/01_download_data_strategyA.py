"""
01_download_data_strategyA.py
MFE 230GB Final Project - Strategy A: Crowded G10 Carry

Downloads all raw data for Strategy A (no API keys needed):
  1. FX spot rates          - FRED (Federal Reserve H.10), daily -> month-end
  2. 3-month interbank rates - OECD via FRED, monthly
  3. Speculator positioning  - CFTC Commitments of Traders, legacy futures-only, weekly

Outputs (data/clean/):
  fx_spot_monthly_usd_per_fcu.csv   USD per 1 unit of foreign currency (up = foreign ccy appreciates)
  rates_3m_monthly.csv              annualized 3-month rates, percent
  cftc_net_spec_weekly.csv          (noncommercial long - short) / open interest
  cftc_net_spec_monthly.csv         same, last observation of each month

Pre-1999 EUR is spliced with the Deutsche mark (fixed rate 1.95583 DEM/EUR).

Requirements: pip install pandas requests
Run from the project root:  python code/01_download_data_strategyA.py
"""

import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
CLEAN = Path("data/clean")
for d in (RAW, CLEAN):
    d.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (MFE230GB course project)"}
MONTH_END = "ME"  # change to "M" if your pandas version is older than 2.2
DEM_PER_EUR = 1.95583

# ---------------------------------------------------------------------------
# 1. FX spot rates (FRED)
# value = (FRED series id, True if quoted as foreign currency per USD -> invert)
# ---------------------------------------------------------------------------
FX_SERIES = {
    "JPY": ("DEXJPUS", True),
    "EUR": ("DEXUSEU", False),
    "GBP": ("DEXUSUK", False),
    "CHF": ("DEXSZUS", True),
    "CAD": ("DEXCAUS", True),
    "AUD": ("DEXUSAL", False),
    "NZD": ("DEXUSNZ", False),
    "DEM": ("DEXGEUS", True),  # pre-euro splice
}

# 3-month interbank rates (OECD Main Economic Indicators, via FRED)
RATE_SERIES = {
    "USD": "IR3TIB01USM156N",
    "JPY": "IR3TIB01JPM156N",
    "EUR": "IR3TIB01EZM156N",
    "GBP": "IR3TIB01GBM156N",
    "CHF": "IR3TIB01CHM156N",
    "CAD": "IR3TIB01CAM156N",
    "AUD": "IR3TIB01AUM156N",
    "NZD": "IR3TIB01NZM156N",
    "DEM": "IR3TIB01DEM156N",  # pre-euro splice
}


def fred_series(series_id: str) -> pd.Series:
    """Download one FRED series as a float Series indexed by date; cache raw copy."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url, na_values=".")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")[series_id].astype(float)
    s.to_csv(RAW / f"fred_{series_id}.csv")
    return s


def build_fx() -> pd.DataFrame:
    print("Downloading FX spot rates from FRED...")
    spot = {}
    for ccy, (sid, invert) in FX_SERIES.items():
        s = fred_series(sid)
        spot[ccy] = 1.0 / s if invert else s  # -> USD per foreign currency unit
    spot = pd.DataFrame(spot).resample(MONTH_END).last()
    spot["EUR"] = spot["EUR"].combine_first(spot["DEM"] * DEM_PER_EUR)
    spot = spot.drop(columns="DEM")
    spot.index.name = "date"
    spot.to_csv(CLEAN / "fx_spot_monthly_usd_per_fcu.csv")
    return spot


def build_rates() -> pd.DataFrame:
    print("Downloading 3-month interest rates from FRED...")
    rates = pd.DataFrame({ccy: fred_series(sid) for ccy, sid in RATE_SERIES.items()})
    rates = rates.resample(MONTH_END).last()
    rates["EUR"] = rates["EUR"].combine_first(rates["DEM"])
    rates = rates.drop(columns="DEM")
    rates.index.name = "date"
    rates.to_csv(CLEAN / "rates_3m_monthly.csv")
    return rates


# ---------------------------------------------------------------------------
# 2. CFTC Commitments of Traders (legacy, futures only)
# ---------------------------------------------------------------------------
CFTC_URLS = ["https://www.cftc.gov/files/dea/history/deacot1986_2016.zip"] + [
    f"https://www.cftc.gov/files/dea/history/deacot{y}.zip" for y in range(2017, 2027)
]

# Contract name prefixes (CME). Futures are quoted vs USD, so "long" = long foreign ccy.
CFTC_NAMES = {
    "JPY": ["JAPANESE YEN"],
    "EUR": ["EURO FX"],
    "GBP": ["BRITISH POUND"],
    "CHF": ["SWISS FRANC"],
    "CAD": ["CANADIAN DOLLAR"],
    "AUD": ["AUSTRALIAN DOLLAR"],
    "NZD": ["NEW ZEALAND DOLLAR", "NZ DOLLAR"],
    "DEM": ["DEUTSCHE MARK"],  # pre-euro splice
}

CFTC_COLS = {
    "Market and Exchange Names": "market",
    "As of Date in Form YYYY-MM-DD": "date",
    "Open Interest (All)": "oi",
    "Noncommercial Positions-Long (All)": "nc_long",
    "Noncommercial Positions-Short (All)": "nc_short",
}


def download_cftc() -> pd.DataFrame:
    print("Downloading CFTC Commitments of Traders files...")
    frames = []
    for url in CFTC_URLS:
        fname = RAW / Path(url).name
        if not fname.exists():
            r = requests.get(url, headers=HEADERS, timeout=180)
            if r.status_code != 200:
                print(f"  skipped {url} (HTTP {r.status_code})")
                continue
            fname.write_bytes(r.content)
        with zipfile.ZipFile(fname) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = df.columns.str.strip()
        frames.append(df[list(CFTC_COLS)].rename(columns=CFTC_COLS))
        print(f"  loaded {fname.name}: {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)


def match_currency(market: str):
    """Map a CFTC market name to a currency code; exclude crosses and mini contracts."""
    parts = str(market).upper().split(" - ")
    name = parts[0].strip()
    exchange = parts[1] if len(parts) > 1 else ""
    if "CHICAGO MERCANTILE" not in exchange:
        return None
    if any(bad in name for bad in ("/", "XRATE", "MINI")):
        return None
    for ccy, prefixes in CFTC_NAMES.items():
        if any(name.startswith(p) for p in prefixes):
            return ccy
    return None


def build_positioning() -> pd.DataFrame:
    cot = download_cftc()
    cot["ccy"] = cot["market"].map(match_currency)
    cot = cot.dropna(subset=["ccy"]).copy()

    print("\nMatched CFTC contracts - CHECK that these are the right ones:")
    for ccy, names in cot.groupby("ccy")["market"].unique().items():
        print(f"  {ccy}: {sorted(set(names))}")

    cot["date"] = pd.to_datetime(cot["date"])
    for c in ("oi", "nc_long", "nc_short"):
        cot[c] = pd.to_numeric(cot[c], errors="coerce")
    cot = cot.drop_duplicates(subset=["date", "market"])

    wk = cot.groupby(["date", "ccy"])[["oi", "nc_long", "nc_short"]].sum()
    wk["net_spec"] = (wk["nc_long"] - wk["nc_short"]) / wk["oi"]
    net = wk["net_spec"].unstack("ccy").sort_index()
    if "DEM" in net:
        net["EUR"] = net["EUR"].combine_first(net["DEM"])
        net = net.drop(columns="DEM")

    net.index.name = "date"
    net.to_csv(CLEAN / "cftc_net_spec_weekly.csv")
    monthly = net.resample(MONTH_END).last()
    monthly.to_csv(CLEAN / "cftc_net_spec_monthly.csv")
    return monthly


def summarize(name: str, df: pd.DataFrame) -> None:
    print(f"\n=== {name} ===")
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            print(f"  {col}: NO DATA")
        else:
            print(f"  {col}: {s.index.min():%Y-%m} to {s.index.max():%Y-%m}, "
                  f"{len(s)} obs, last = {s.iloc[-1]:.4f}")


if __name__ == "__main__":
    spot = build_fx()
    rates = build_rates()
    net = build_positioning()
    summarize("FX spot (USD per FCU, month-end)", spot)
    summarize("3-month rates (% p.a.)", rates)
    summarize("CFTC net speculative positioning (share of OI)", net)
    print("\nDone. Clean files are in data/clean/")
