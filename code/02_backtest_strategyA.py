"""
02_backtest_strategyA.py
MFE 230GB Final Project - Strategy A: Crowded G10 Carry

Hypothesis (stated before testing):
  Carry trades earn a risk premium but crash when crowded positions unwind
  (Brunnermeier, Nagel & Pedersen 2008). When speculators are heavily long the
  high-rate currencies and short the low-rate currencies (CFTC data), the trade
  is crowded and crash risk is elevated -> scale exposure down.

Strategy:
  - Universe: JPY, EUR, GBP, CHF, CAD, AUD, NZD, all vs USD (monthly)
  - Baseline carry: at each month-end, long the N_LEG highest-rate currencies,
    short the N_LEG lowest-rate currencies, equal weights (dollar-neutral)
  - Crowding signal: z-score of CFTC net speculative positioning (rolling window),
    portfolio crowding = avg z of long leg - avg z of short leg
  - Filtered carry: scale positions to CROWDED_SCALE when crowding > CROWD_THRESHOLD

Inputs:  data/clean/ files produced by 01_download_data_strategyA.py
Outputs: output/strategyA/ (performance tables, monthly returns, figures)

Requirements: pip install pandas numpy matplotlib
Run from the project root:  python code/02_backtest_strategyA.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CLEAN = Path("data/clean")
OUT = Path("output/strategyA")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# PRE-SPECIFIED PARAMETERS (fixed before looking at results - do not tune on the
# test period; robustness grid below reports alternatives transparently)
# ---------------------------------------------------------------------------
CCYS = ["JPY", "EUR", "GBP", "CHF", "CAD", "AUD", "NZD"]
N_LEG = 2                 # currencies in each leg
Z_WINDOW = 36             # months for crowding z-score
Z_MIN = 24                # minimum months before z-score is defined
CROWD_THRESHOLD = 1.0     # crowding above this = "crowded"
CROWDED_SCALE = 0.5       # exposure when crowded (1.0 = no filter)
CFTC_RELEASE_LAG_DAYS = 3 # Tuesday positions are published Friday
TC_BP = 3.0               # one-way transaction cost, basis points per unit traded
IN_SAMPLE_END = "2010-12-31"
MONTH_END = "ME"          # change to "M" if pandas < 2.2


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load():
    spot = pd.read_csv(CLEAN / "fx_spot_monthly_usd_per_fcu.csv",
                       index_col=0, parse_dates=True)[CCYS]
    rates = pd.read_csv(CLEAN / "rates_3m_monthly.csv",
                        index_col=0, parse_dates=True)
    weekly = pd.read_csv(CLEAN / "cftc_net_spec_weekly.csv",
                         index_col=0, parse_dates=True)[CCYS]
    idx = spot.index.intersection(rates.index)
    return spot.loc[idx], rates.loc[idx], weekly


def excess_returns(spot, rates):
    """Monthly excess return of holding each foreign currency vs USD.
    rx_t = (1 + i_k,t-1/1200) * S_t / S_t-1 - (1 + i_US,t-1/1200)
    (forward-implied carry via covered interest parity)."""
    gross_foreign = (1 + rates[CCYS].shift(1) / 1200) * spot / spot.shift(1)
    gross_usd = 1 + rates["USD"].shift(1) / 1200
    return gross_foreign.sub(gross_usd, axis=0)


def carry_weights(rate_diff, tradable):
    """Long top N_LEG, short bottom N_LEG by interest differential vs USD."""
    w = pd.DataFrame(0.0, index=rate_diff.index, columns=rate_diff.columns)
    for t, row in rate_diff.iterrows():
        r = row[tradable.loc[t]].dropna()
        if len(r) < 2 * N_LEG:
            continue
        ranked = r.sort_values()
        w.loc[t, ranked.index[-N_LEG:]] = 1.0 / N_LEG
        w.loc[t, ranked.index[:N_LEG]] = -1.0 / N_LEG
    return w


def crowding_signal(weekly, w, index):
    """Portfolio crowding = sum_k w_k * z_k  (avg z of longs - avg z of shorts)."""
    released = weekly.copy()
    released.index = released.index + pd.Timedelta(days=CFTC_RELEASE_LAG_DAYS)
    pos = released.resample(MONTH_END).last().reindex(index).ffill(limit=1)
    roll = pos.rolling(Z_WINDOW, min_periods=Z_MIN)
    z = (pos - roll.mean()) / roll.std()
    crowd = (w * z).sum(axis=1, min_count=1)
    # if any position lacks a z-score, treat signal as unavailable
    missing = ((w != 0) & z.isna()).any(axis=1)
    crowd[missing] = np.nan
    return crowd, z


def backtest(w, rx, tc_bp):
    """Weights formed at end of t earn rx at t+1; costs charged on turnover."""
    gross = (w.shift(1) * rx).sum(axis=1, min_count=1)
    turnover = w.diff().abs().sum(axis=1)
    net = gross - turnover.shift(1) * tc_bp / 1e4
    first = w.abs().sum(axis=1).gt(0).idxmax()
    keep = gross.index > first
    return gross[keep], net[keep], turnover[keep]


# ---------------------------------------------------------------------------
# Performance statistics
# ---------------------------------------------------------------------------
def perf(r, turnover=None):
    r = r.dropna()
    if len(r) < 12:
        return pd.Series(dtype=float)
    mean, vol = r.mean() * 12, r.std() * np.sqrt(12)
    cum = (1 + r).cumprod()
    dd = cum / cum.cummax() - 1
    out = {
        "Start": r.index[0].strftime("%Y-%m"),
        "End": r.index[-1].strftime("%Y-%m"),
        "Months": len(r),
        "Ann. mean (%)": 100 * mean,
        "Ann. vol (%)": 100 * vol,
        "Sharpe": mean / vol if vol > 0 else np.nan,
        "Max drawdown (%)": 100 * dd.min(),
        "Skewness": r.skew(),
        "Worst month (%)": 100 * r.min(),
        "Hit rate (%)": 100 * (r > 0).mean(),
    }
    if turnover is not None:
        out["Ann. turnover (x)"] = turnover.reindex(r.index).mean() * 12
    return pd.Series(out)


def split_table(series_dict, turnover_dict):
    rows = {}
    periods = {"Full": (None, None),
               "In-sample": (None, IN_SAMPLE_END),
               "Out-of-sample": (pd.Timestamp(IN_SAMPLE_END) + pd.Timedelta(days=1), None)}
    for name, r in series_dict.items():
        for pname, (a, b) in periods.items():
            rows[(name, pname)] = perf(r.loc[a:b], turnover_dict.get(name))
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    spot, rates, weekly = load()
    rx = excess_returns(spot, rates)
    rate_diff = rates[CCYS].sub(rates["USD"], axis=0)
    tradable = spot.notna() & rates[CCYS].notna()

    w_carry = carry_weights(rate_diff, tradable)
    crowd, z = crowding_signal(weekly, w_carry, spot.index)
    scale = pd.Series(np.where(crowd > CROWD_THRESHOLD, CROWDED_SCALE, 1.0),
                      index=crowd.index)
    w_filt = w_carry.mul(scale, axis=0)

    g_c, n_c, to_c = backtest(w_carry, rx, TC_BP)
    g_f, n_f, to_f = backtest(w_filt, rx, TC_BP)

    # align both strategies to the period where the crowding signal exists
    start = crowd.first_valid_index()
    series = {"Carry (gross)": g_c.loc[start:], "Carry (net)": n_c.loc[start:],
              "Crowd-filtered (gross)": g_f.loc[start:], "Crowd-filtered (net)": n_f.loc[start:]}
    turns = {"Carry (gross)": to_c, "Carry (net)": to_c,
             "Crowd-filtered (gross)": to_f, "Crowd-filtered (net)": to_f}

    table = split_table(series, turns)
    table.to_csv(OUT / "performance_table.csv")
    pd.set_option("display.width", 200)
    print("\n=== PERFORMANCE ===")
    print(table.round(2).to_string())

    # save monthly returns for later risk analysis / HTML page
    monthly = pd.DataFrame(series)
    monthly["crowding"] = crowd
    monthly["scale"] = scale
    monthly.to_csv(OUT / "monthly_returns.csv")
    w_carry.to_csv(OUT / "weights_carry.csv")

    # crash analysis: carry returns in crowded vs uncrowded months
    nxt = n_c.loc[start:]
    state = (crowd.shift(1) > CROWD_THRESHOLD).reindex(nxt.index)
    crash = pd.DataFrame({
        "Months": nxt.groupby(state).size(),
        "Next-month carry mean (%)": 100 * nxt.groupby(state).mean(),
        "Next-month carry vol (%)": 100 * nxt.groupby(state).std(),
        "Next-month skewness": nxt.groupby(state).skew(),
        "Share of worst-10% months (%)": 100 * (nxt < nxt.quantile(0.1)).groupby(state).mean(),
    }).rename(index={False: "Not crowded", True: "Crowded"})
    crash.to_csv(OUT / "crowded_vs_not.csv")
    print("\n=== CARRY RETURNS AFTER CROWDED vs NOT-CROWDED MONTHS (net) ===")
    print(crash.round(2).to_string())

    # robustness grid (reported transparently, NOT used to pick parameters)
    grid = []
    for thr in (0.5, 1.0, 1.5):
        for sc in (0.0, 0.5):
            wf = w_carry.mul(np.where(crowd > thr, sc, 1.0), axis=0)
            _, n, _ = backtest(wf, rx, TC_BP)
            n = n.loc[start:]
            oos = n.loc[pd.Timestamp(IN_SAMPLE_END) + pd.Timedelta(days=1):]
            grid.append({"threshold": thr, "crowded_scale": sc,
                         "Sharpe full": perf(n)["Sharpe"],
                         "Sharpe OOS": perf(oos)["Sharpe"],
                         "MaxDD full (%)": perf(n)["Max drawdown (%)"]})
    grid = pd.DataFrame(grid)
    grid.to_csv(OUT / "robustness_grid.csv", index=False)
    print("\n=== ROBUSTNESS GRID (net) ===")
    print(grid.round(2).to_string(index=False))

    # ---------------- figures ----------------
    fig, ax = plt.subplots(3, 1, figsize=(11, 11), sharex=True,
                           gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
    for name in ("Carry (net)", "Crowd-filtered (net)"):
        ax[0].plot((1 + series[name]).cumprod(), label=name)
    ax[0].set_yscale("log")
    ax[0].axvline(pd.Timestamp(IN_SAMPLE_END), color="grey", ls="--", lw=1)
    ax[0].text(pd.Timestamp(IN_SAMPLE_END), ax[0].get_ylim()[1], " out-of-sample →",
               va="top", fontsize=9, color="grey")
    ax[0].set_title("Strategy A: G10 carry vs crowding-filtered carry (net of costs, log scale)")
    ax[0].legend()

    for name in ("Carry (net)", "Crowd-filtered (net)"):
        cum = (1 + series[name]).cumprod()
        ax[1].plot(100 * (cum / cum.cummax() - 1), label=name)
    ax[1].set_ylabel("Drawdown (%)")

    ax[2].plot(crowd.loc[start:], color="black", lw=1)
    ax[2].axhline(CROWD_THRESHOLD, color="red", ls="--", lw=1)
    ax[2].fill_between(crowd.loc[start:].index, crowd.loc[start:].min(), crowd.loc[start:].max(),
                       where=(crowd.loc[start:] > CROWD_THRESHOLD), color="red", alpha=0.1)
    ax[2].set_ylabel("Crowding")
    fig.tight_layout()
    fig.savefig(OUT / "strategyA_performance.png", dpi=150)
    print(f"\nSaved tables and figure to {OUT}/")


if __name__ == "__main__":
    main()


# ===== Questions this script answers and results =====
# Results from the 2026-10-02 run (output/strategyA/), net of 3 bp costs:
# - Does G10 carry make money? Yes, modestly. 1999-05 to 2026-08: 3.27% a year, 8.9% vol,
#     Sharpe 0.37, max drawdown -37%, worst month -12.0% (Oct 2008), skew -0.49.
#     In-sample (to 2010) Sharpe 0.47; out-of-sample (2011+) Sharpe 0.27.
# - Does the crowding filter help? Full sample: Sharpe 0.38 vs 0.37 (no real change).
#     Out-of-sample: Sharpe 0.32 vs 0.27, skew -0.02 vs -0.10, max drawdown -14.4% vs -15.5%,
#     at the cost of higher turnover (about 2.0x vs 1.2x a year).
# - Is carry worse after crowded months? Next-month carry averages 0.02% after the 33 crowded
#     months (of 247 with a signal) vs 0.30% after non-crowded months; skew -0.71 vs -0.46.
# - Robust? Full-sample Sharpe 0.35-0.38 and out-of-sample 0.30-0.39 across thresholds
#     0.5/1.0/1.5 and crowded exposure 0/0.5.
# - Holdings: NZD long in 80% of months, AUD 63%; CHF short 48%, CAD 42%, JPY 25%, EUR 20%.
# Limitations: sample starts 1999; few crowded months; the 2008 crash began from a
# non-crowded reading, so the filter did not avoid the largest drawdown.
