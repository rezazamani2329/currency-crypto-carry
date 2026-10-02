"""
04_backtest_strategyC.py
MFE 230GB Final Project - Strategy C: Crypto Carry (perpetual futures funding)

Hypothesis (stated before testing):
  Perpetual futures funding rates are the crypto analogue of the interest
  differential in FX carry. Coins with high funding are crowded longs (leveraged
  retail demand); shorting them collects the funding, while longing the
  low-funding coins hedges the common crypto market factor. As in FX, the trade
  should earn a premium but suffer crashes when crowded positions unwind.

Strategy:
  - Universe: 12 USDT-margined perpetuals (incl. delisted LUNA, FTT);
    USDC is a stablecoin sanity check and is NOT traded
  - A coin is tradable on a day only if it has a close price and quote volume > 0
    (drops LUNA after 2022-05-13 and FTT after 2022-11-14)
  - Signal: trailing LOOKBACK-day average daily funding, using data up to t-1
  - Every REBALANCE period: short the top third by funding, long the bottom
    third, equal weights, dollar-neutral (each leg 0.5 gross)
  - Daily P&L per coin = side * price return - side * funding paid that day
    (a short perp RECEIVES positive funding)

Inputs:  data/clean/crypto_*_daily.csv from 03_download_data_strategyC.py,
         output/strategyA/monthly_returns.csv (for the correlation check)
Outputs: output/strategyC/ (performance tables, daily returns, figures)

Requirements: pip install pandas numpy matplotlib
Run from the project root:  python code/04_backtest_strategyC.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CLEAN = Path("data/clean")
OUT = Path("output/strategyC")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# PRE-SPECIFIED PARAMETERS (fixed before looking at results - do not tune on the
# test period; robustness grid below reports alternatives transparently)
# ---------------------------------------------------------------------------
COINS = ["BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "LTC", "LINK", "AVAX",
         "LUNA", "FTT"]          # USDC deliberately excluded
LOOKBACK = 7                     # days of funding in the signal
REBALANCE = "W"                  # "W" = weekly (Sunday close), "D" = daily
LEG_FRACTION = 1 / 3             # top / bottom third
MIN_COINS = 6                    # need at least this many tradable coins to trade
TC_BP = 5.0                      # cost in basis points per unit of turnover
IN_SAMPLE_END = "2023-12-31"
DAYS_PER_YEAR = 365
# days missing from Binance's archive for some coins - the only days we forward-fill
ARCHIVE_GAPS = pd.to_datetime(["2022-02-26", "2022-02-27", "2022-02-28",
                               "2022-04-01", "2022-04-02"])


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load():
    def read(name):
        df = pd.read_csv(CLEAN / name, index_col=0, parse_dates=True)
        return df.reindex(columns=COINS)
    close = read("crypto_close_daily.csv")
    volume = read("crypto_quote_volume_daily.csv")
    funding = read("crypto_funding_daily.csv")
    days = pd.date_range(min(close.index.min(), funding.index.min()),
                         max(close.index.max(), funding.index.max()), freq="D")
    close, volume, funding = (x.reindex(days) for x in (close, volume, funding))
    # forward-fill price and volume only on the archive-gap days
    gap = close.index.isin(ARCHIVE_GAPS)
    close.loc[gap] = close.ffill().loc[gap]
    volume.loc[gap] = volume.ffill().loc[gap]
    return close, volume, funding


# ---------------------------------------------------------------------------
# Portfolio construction
# ---------------------------------------------------------------------------
def carry_weights(funding, tradable, lookback, rebalance):
    """Target weights decided at the end of day t (signal uses funding up to t),
    held over day t+1. Short top third by funding, long bottom third."""
    signal = funding.rolling(lookback, min_periods=lookback).mean()
    if rebalance == "D":
        rebal_days = signal.index
    else:
        rebal_days = signal.resample("W-SUN").last().index.intersection(signal.index)
    target = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    for t in rebal_days:
        s = signal.loc[t][tradable.loc[t]].dropna()
        row = pd.Series(0.0, index=signal.columns)
        if len(s) >= MIN_COINS:
            k = max(1, int(len(s) * LEG_FRACTION))
            ranked = s.sort_values()
            row[ranked.index[:k]] = 0.5 / k     # long low funding
            row[ranked.index[-k:]] = -0.5 / k   # short high funding
        target.loc[t] = row
    w = target.ffill().fillna(0.0)
    # a coin that stops trading between rebalances is closed out (no re-weighting)
    return w.where(tradable, 0.0)


def backtest(w, ret, funding, tc_bp):
    """Weights at end of t earn day t+1's price return and pay t+1's funding."""
    held = w.shift(1)
    price = (held * ret.fillna(0)).sum(axis=1)
    carry = -(held * funding.fillna(0)).sum(axis=1)
    gross = price + carry
    turnover = w.diff().abs().sum(axis=1)
    turnover.iloc[0] = w.iloc[0].abs().sum()
    net = gross - turnover.shift(1) * tc_bp / 1e4
    first = w.abs().sum(axis=1).gt(0).idxmax()
    keep = gross.index > first
    return {"gross": gross[keep], "net": net[keep], "turnover": turnover[keep],
            "price": price[keep], "carry": carry[keep]}


# ---------------------------------------------------------------------------
# Performance statistics
# ---------------------------------------------------------------------------
def perf(r, turnover=None):
    r = r.dropna()
    if len(r) < 30:
        return pd.Series(dtype=float)
    mean, vol = r.mean() * DAYS_PER_YEAR, r.std() * np.sqrt(DAYS_PER_YEAR)
    cum = (1 + r).cumprod()
    dd = cum / cum.cummax() - 1
    weekly = (1 + r).resample("W-SUN").prod() - 1
    out = {
        "Start": r.index[0].strftime("%Y-%m-%d"),
        "End": r.index[-1].strftime("%Y-%m-%d"),
        "Days": len(r),
        "Ann. mean (%)": 100 * mean,
        "Ann. vol (%)": 100 * vol,
        "Sharpe": mean / vol if vol > 0 else np.nan,
        "Max drawdown (%)": 100 * dd.min(),
        "Skewness (weekly)": weekly.skew(),
        "Worst week (%)": 100 * weekly.min(),
        "Hit rate days (%)": 100 * (r > 0).mean(),
    }
    if turnover is not None:
        out["Ann. turnover (x)"] = turnover.reindex(r.index).mean() * DAYS_PER_YEAR
    return pd.Series(out)


def periods():
    return {"Full": (None, None),
            "In-sample": (None, IN_SAMPLE_END),
            "Out-of-sample": (pd.Timestamp(IN_SAMPLE_END) + pd.Timedelta(days=1), None)}


def split_table(series_dict, turnover):
    rows = {}
    for name, r in series_dict.items():
        for pname, (a, b) in periods().items():
            rows[(name, pname)] = perf(r.loc[a:b], turnover)
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    close, volume, funding = load()
    ret = close.pct_change(fill_method=None)
    tradable = close.notna() & volume.gt(0)

    w = carry_weights(funding, tradable, LOOKBACK, REBALANCE)
    bt = backtest(w, ret, funding, TC_BP)
    series = {"Crypto carry (gross)": bt["gross"], "Crypto carry (net)": bt["net"]}

    table = split_table(series, bt["turnover"])
    table.to_csv(OUT / "performance_table.csv")
    pd.set_option("display.width", 250)
    print("=== PERFORMANCE (annualised with 365 days) ===")
    print(table.to_string())

    daily = pd.DataFrame({**series, "price component": bt["price"],
                          "funding component": bt["carry"], "turnover": bt["turnover"],
                          "n_long": (w > 0).sum(axis=1), "n_short": (w < 0).sum(axis=1)})
    daily.to_csv(OUT / "daily_returns.csv")
    w.to_csv(OUT / "weights.csv")

    # ---------------- return decomposition ----------------
    rows = {}
    for pname, (a, b) in periods().items():
        rows[pname] = {
            "Funding carry (% p.a.)": 100 * bt["carry"].loc[a:b].mean() * DAYS_PER_YEAR,
            "Price component (% p.a.)": 100 * bt["price"].loc[a:b].mean() * DAYS_PER_YEAR,
            "Costs (% p.a.)": 100 * (bt["net"] - bt["gross"]).loc[a:b].mean() * DAYS_PER_YEAR,
            "Net total (% p.a.)": 100 * bt["net"].loc[a:b].mean() * DAYS_PER_YEAR,
        }
    decomp = pd.DataFrame(rows).T
    decomp.to_csv(OUT / "return_decomposition.csv")
    print("\n=== RETURN DECOMPOSITION (arithmetic, % p.a.) ===")
    print(decomp.round(2).to_string())

    # ---------------- worst weeks ----------------
    wk = pd.DataFrame({
        "net (%)": (1 + bt["net"]).resample("W-SUN").prod() - 1,
        "funding (%)": bt["carry"].resample("W-SUN").sum(),
        "price (%)": bt["price"].resample("W-SUN").sum(),
    }) * 100
    worst = wk.nsmallest(5, "net (%)")
    worst.index = worst.index.strftime("week ending %Y-%m-%d")
    worst.to_csv(OUT / "worst_weeks.csv")
    print("\n=== WORST 5 WEEKS (net) ===")
    print(worst.round(2).to_string())

    events = {"COVID crash (Mar 2020)": ("2020-03-08", "2020-03-22"),
              "LUNA collapse (May 2022)": ("2022-05-05", "2022-05-15"),
              "FTX collapse (Nov 2022)": ("2022-11-06", "2022-11-16")}
    print("\n=== EVENT WINDOWS (net cumulative %, positions held) ===")
    for name, (a, b) in events.items():
        r = bt["net"].loc[a:b]
        pos = w.shift(1).loc[a:b]
        held = {c: ("long" if pos[c].max() > 0 else "short") for c in pos.columns
                if pos[c].abs().max() > 0 and c in ("LUNA", "FTT", "BTC", "SOL")}
        txt = f"{100 * ((1 + r).prod() - 1):.2f}" if len(r) else "not traded"
        print(f"  {name}: {txt}   {held}")

    # ---------------- correlation with Strategy A ----------------
    a_path = Path("output/strategyA/monthly_returns.csv")
    if a_path.exists():
        a = pd.read_csv(a_path, index_col=0, parse_dates=True)["Carry (net)"]
        c_m = (1 + bt["net"]).resample("ME").prod() - 1
        both = pd.concat([c_m.rename("C"), a.rename("A")], axis=1, sort=True).dropna()
        print(f"\n=== CORRELATION with Strategy A monthly net carry ===\n"
              f"  {both.index[0]:%Y-%m} to {both.index[-1]:%Y-%m}, {len(both)} months: "
              f"corr = {both.corr().iloc[0, 1]:.3f}")
    else:
        print("\n(Strategy A monthly returns not found - run 02_backtest_strategyA.py first)")

    # ---------------- robustness grid ----------------
    grid = []
    for lb in (3, 7, 30):
        for rb in ("D", "W"):
            wg = carry_weights(funding, tradable, lb, rb)
            b = backtest(wg, ret, funding, TC_BP)
            n = b["net"]
            oos = n.loc[pd.Timestamp(IN_SAMPLE_END) + pd.Timedelta(days=1):]
            grid.append({"lookback_days": lb, "rebalance": {"D": "daily", "W": "weekly"}[rb],
                         "Sharpe gross": perf(b["gross"])["Sharpe"],
                         "Sharpe net": perf(n)["Sharpe"],
                         "Sharpe OOS net": perf(oos)["Sharpe"],
                         "Ann. mean net (%)": perf(n)["Ann. mean (%)"],
                         "MaxDD (%)": perf(n)["Max drawdown (%)"],
                         "Ann. turnover (x)": perf(n, b["turnover"])["Ann. turnover (x)"]})
    grid = pd.DataFrame(grid)
    grid.to_csv(OUT / "robustness_grid.csv", index=False)
    print("\n=== ROBUSTNESS GRID ===")
    print(grid.round(2).to_string(index=False))

    # ---------------- figures ----------------
    fig, ax = plt.subplots(3, 1, figsize=(11, 11), sharex=True,
                           gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
    for name, r in series.items():
        ax[0].plot((1 + r).cumprod(), label=name)
    ax[0].set_yscale("log")
    ax[0].axvline(pd.Timestamp(IN_SAMPLE_END), color="grey", ls="--", lw=1)
    ax[0].text(pd.Timestamp(IN_SAMPLE_END), ax[0].get_ylim()[1], " out-of-sample →",
               va="top", fontsize=9, color="grey")
    ax[0].set_title("Strategy C: crypto funding carry (short high funding, long low funding)")
    ax[0].legend()

    cum = (1 + bt["net"]).cumprod()
    ax[1].plot(100 * (cum / cum.cummax() - 1), color="C1")
    ax[1].set_ylabel("Drawdown (%)")

    ax[2].plot(100 * bt["carry"].cumsum(), label="funding component")
    ax[2].plot(100 * bt["price"].cumsum(), label="price component")
    ax[2].set_ylabel("Cumulative (%)")
    ax[2].legend()
    fig.tight_layout()
    fig.savefig(OUT / "strategyC_performance.png", dpi=150)
    print(f"\nSaved tables and figure to {OUT}/")


if __name__ == "__main__":
    main()
