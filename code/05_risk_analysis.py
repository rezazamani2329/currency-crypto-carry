"""
05_risk_analysis.py
MFE 230GB Final Project - Risk analysis for Strategy A (G10 carry) and
Strategy C (crypto funding carry), plus the combined portfolio.

Sections:
  1. Strategy A vs the Lustig-Roussanov-Verdelhan developed-country carry
     portfolios (course file CurrencyPortfolios.xls): data/code validation
  2. Strategy A risk: exposure to volatility shocks and the dollar factor
     (Newey-West t-stats), worst months, the 2008 carry crash
  3. Strategy C risk: beta to BTC, worst weeks, loss contribution by coin,
     per-coin summary, and ONE pre-specified risk control
  4. Combined A + C portfolio (each scaled to 10% vol, 50/50)

Inputs:  output/strategyA/monthly_returns.csv (02_backtest_strategyA.py)
         data/clean/crypto_*_daily.csv       (03_download_data_strategyC.py)
         data/raw/CurrencyPortfolios.xls     (course file, optional - sections
                                              that need it are skipped if absent)
         data/raw/fred_VIXCLS.csv            (optional, saved by hand from FRED)
Outputs: output/risk/

Requirements: pip install pandas numpy matplotlib statsmodels xlrd
Run from the project root:  python code/05_risk_analysis.py
"""

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

RAW = Path("data/raw")
OUT = Path("output/risk")
OUT.mkdir(parents=True, exist_ok=True)
XLS = RAW / "CurrencyPortfolios.xls"
VIX = RAW / "fred_VIXCLS.csv"

# ---------------------------------------------------------------------------
# PRE-SPECIFIED PARAMETERS
# ---------------------------------------------------------------------------
NW_LAGS_MONTHLY = 3
NW_LAGS_DAILY = 7
# Strategy C risk control, fixed before running it (reported next to the base case):
CAP_PER_COIN = 1 / 6         # max weight of one coin as a share of its leg (0.5)
DISTRESS_FUNDING = -0.50     # exclude from the long leg if 7-day funding < -50% p.a.
TARGET_VOL = 0.10            # combined portfolio: each strategy scaled to 10% vol
VOL_WINDOW_A = 36            # months of trailing vol for Strategy A
VOL_WINDOW_C = 12            # months of trailing vol for Strategy C
MONTH_END = "ME"

pd.set_option("display.width", 250)


def load_strategy_c():
    """Reuse load/backtest/perf from 04_backtest_strategyC.py (file name starts with a digit)."""
    spec = importlib.util.spec_from_file_location("stratC", "code/04_backtest_strategyC.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def monthly_perf(r):
    r = r.dropna()
    mean, vol = r.mean() * 12, r.std() * np.sqrt(12)
    cum = (1 + r).cumprod()
    return pd.Series({
        "Start": r.index[0].strftime("%Y-%m"), "End": r.index[-1].strftime("%Y-%m"),
        "Months": len(r), "Ann. mean (%)": 100 * mean, "Ann. vol (%)": 100 * vol,
        "Sharpe": mean / vol, "Max drawdown (%)": 100 * (cum / cum.cummax() - 1).min(),
        "Skewness": r.skew(), "Worst month (%)": 100 * r.min()})


def nw_ols(y, X, lags):
    X = sm.add_constant(X)
    df = pd.concat([y, X], axis=1, sort=True).dropna()
    res = sm.OLS(df.iloc[:, 0], df.iloc[:, 1:]).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    out = pd.DataFrame({"coef": res.params, "NW t-stat": res.tvalues})
    out.loc["R2", "coef"] = res.rsquared
    out.loc["N", "coef"] = len(df)
    return out


def read_lrv(sheet):
    d = pd.read_excel(XLS, sheet_name=sheet, header=0)
    d = d.rename(columns={d.columns[0]: "date"}).dropna(subset=["date"])
    d["date"] = pd.to_datetime(d["date"]) + pd.offsets.MonthEnd(0)
    return d.set_index("date")


# ---------------------------------------------------------------------------
# 1 + 2. Strategy A
# ---------------------------------------------------------------------------
def strategy_a():
    a = pd.read_csv("output/strategyA/monthly_returns.csv", index_col=0, parse_dates=True)
    carry = a["Carry (net)"].rename("Strategy A carry (net)")

    factors = pd.DataFrame(index=carry.index)
    if XLS.exists():
        net = read_lrv("Developed currencies (net)")
        gross = read_lrv("Developed currencies")
        hml = net.filter(like="HML").iloc[:, 0].rename("LRV developed HML (net)")
        factors["RX (dollar)"] = net.filter(like="RX").iloc[:, 0]
        # equity-vol column block sits to the right of the gross sheet: level, then change
        vcols = list(gross.columns)
        i = next(k for k, c in enumerate(vcols) if "Volatility" in str(c))
        factors["dVol (LRV)"] = gross.iloc[:, i + 1]

        both = pd.concat([carry, hml], axis=1, sort=True).dropna()
        comp = pd.DataFrame({c: monthly_perf(both[c]) for c in both.columns}).T
        comp["Correlation"] = both.corr().iloc[0, 1]
        comp.to_csv(OUT / "A_vs_LRV_HML.csv")
        print("=== 1. STRATEGY A vs LUSTIG-ROUSSANOV-VERDELHAN DEVELOPED HML (net) ===")
        print(comp.round(3).to_string())
    else:
        print("=== 1. skipped: data/raw/CurrencyPortfolios.xls not found ===")

    if VIX.exists():
        v = pd.read_csv(VIX, index_col=0, parse_dates=True, na_values=".").iloc[:, 0]
        factors["dVIX"] = v.resample(MONTH_END).last().diff() / 100

    print("\n=== 2. STRATEGY A RISK EXPOSURES (monthly net carry, Newey-West t-stats) ===")
    regs = {}
    for cols in (["RX (dollar)"], ["dVol (LRV)"], ["RX (dollar)", "dVol (LRV)"], ["dVIX"]):
        if all(c in factors and factors[c].notna().any() for c in cols):
            regs[" + ".join(cols)] = nw_ols(carry, factors[cols], NW_LAGS_MONTHLY)
    if regs:
        reg = pd.concat(regs, names=["model", "term"])
        reg.to_csv(OUT / "A_factor_regressions.csv")
        print(reg.round(3).to_string())

    worst = (100 * carry.nsmallest(10)).rename("net return (%)").to_frame()
    worst.index = worst.index.strftime("%Y-%m")
    worst.to_csv(OUT / "A_worst_months.csv")
    print("\n=== STRATEGY A WORST 10 MONTHS ===")
    print(worst.round(2).to_string())

    crisis = carry.loc["2008-07":"2009-03"]
    print("\n=== STRATEGY A IN THE 2008 CARRY CRASH (Jul 2008 - Mar 2009) ===")
    print("  " + ", ".join(f"{d:%Y-%m}: {100 * r:.1f}%" for d, r in crisis.items()))
    print(f"  cumulative: {100 * ((1 + crisis).prod() - 1):.1f}%")
    return carry


# ---------------------------------------------------------------------------
# 3. Strategy C
# ---------------------------------------------------------------------------
def coin_summary(close, volume, funding):
    """Per-coin descriptive table; funding/returns only over days the coin traded."""
    ret = close.pct_change(fill_method=None)
    rows = {}
    for c in close.columns:
        live = close[c].notna() & volume[c].gt(0)
        if not live.any():
            continue
        last = live[live].index.max()
        p = close[c].loc[:last].dropna()
        r = ret[c].loc[p.index].dropna()
        f = funding[c].loc[:last].dropna()
        yrs = (p.index[-1] - p.index[0]).days / 365
        rows[c] = {
            "first": p.index[0].date(), "last traded": last.date(), "days": len(p),
            "data after last trade (days)": int(close[c].loc[last:].notna().sum() - 1),
            "avg funding (% p.a.)": 100 * f.mean() * 365,
            "positive funding days (%)": 100 * (f > 0).mean(),
            "ann. return (%)": 100 * ((p.iloc[-1] / p.iloc[0]) ** (1 / yrs) - 1),
            "ann. vol (%)": 100 * r.std() * np.sqrt(365),
            "max drawdown (%)": 100 * (p / p.cummax() - 1).min(),
            "worst day (%)": 100 * r.min(), "worst day": r.idxmin().date(),
            "avg volume ($M)": volume[c].loc[:last].mean() / 1e6,
            "corr with BTC": r.corr(ret["BTC"].loc[r.index]),
        }
    return pd.DataFrame(rows).T


def controlled_weights(C, funding, tradable):
    """Pre-specified control: base rule, but (i) coins whose 7-day funding is below
    DISTRESS_FUNDING are not eligible for the long leg, (ii) each coin is capped at
    CAP_PER_COIN of its leg; the capped remainder is left in cash (no re-levering)."""
    signal = funding.rolling(C.LOOKBACK, min_periods=C.LOOKBACK).mean()
    rebal = signal.resample("W-SUN").last().index.intersection(signal.index)
    target = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    cap = 0.5 * CAP_PER_COIN
    for t in rebal:
        s = signal.loc[t][tradable.loc[t]].dropna()
        row = pd.Series(0.0, index=signal.columns)
        if len(s) >= C.MIN_COINS:
            k = max(1, int(len(s) * C.LEG_FRACTION))
            shorts = s.sort_values().index[-k:]
            ok_long = s[(s * 365 >= DISTRESS_FUNDING) & ~s.index.isin(shorts)]
            longs = ok_long.sort_values().index[:k]
            if len(longs):
                row[longs] = min(0.5 / len(longs), cap)
            row[shorts] = -min(0.5 / k, cap)
        target.loc[t] = row
    return target.ffill().fillna(0.0).where(tradable, 0.0)


def strategy_c(C):
    close, volume, funding = C.load()
    ret = close.pct_change(fill_method=None)
    tradable = close.notna() & volume.gt(0)

    summ = coin_summary(close, volume, funding)
    summ.to_csv(OUT / "C_coin_summary.csv")
    usdc = Path("data/clean/crypto_close_daily.csv")
    if usdc.exists():
        u = pd.read_csv(usdc, index_col=0, parse_dates=True).get("USDC")
        if u is not None:
            print(f"\n(USDC sanity check: price range {u.min():.4f} to {u.max():.4f})")

    w_base = C.carry_weights(funding, tradable, C.LOOKBACK, C.REBALANCE)
    w_ctrl = controlled_weights(C, funding, tradable)
    base = C.backtest(w_base, ret, funding, C.TC_BP)
    ctrl = C.backtest(w_ctrl, ret, funding, C.TC_BP)

    # --- beta to BTC ---
    btc = ret["BTC"].rename("BTC return")
    beta = pd.concat({"Base": nw_ols(base["net"], btc, NW_LAGS_DAILY),
                      "Risk-controlled": nw_ols(ctrl["net"], btc, NW_LAGS_DAILY)},
                     names=["strategy", "term"])
    beta.to_csv(OUT / "C_beta_btc.csv")
    print("\n=== 3. STRATEGY C BETA TO BTC (daily net returns, Newey-West t-stats) ===")
    print(beta.round(4).to_string())
    down = btc < btc.quantile(0.05)
    print(f"  on BTC's worst 5% days: base avg {100 * base['net'][down].mean():.2f}%, "
          f"BTC avg {100 * btc[down].mean():.2f}%")

    # --- loss contribution by coin ---
    held = w_base.shift(1)
    pnl = held * ret.fillna(0) - held * funding.fillna(0)
    contrib = pd.DataFrame({
        "total P&L (% pts)": 100 * pnl.sum(),
        "price (% pts)": 100 * (held * ret.fillna(0)).sum(),
        "funding (% pts)": 100 * -(held * funding.fillna(0)).sum(),
        "days long": (held > 0).sum(), "days short": (held < 0).sum(),
        "worst day (% pts)": 100 * pnl.min(),
    }).sort_values("total P&L (% pts)")
    contrib.to_csv(OUT / "C_contribution_by_coin.csv")
    print("\n=== STRATEGY C P&L CONTRIBUTION BY COIN (base, sum of daily % pts) ===")
    print(contrib.round(1).to_string())

    # --- worst weeks, base vs control ---
    wk = pd.DataFrame({n: (1 + b["net"]).resample("W-SUN").prod() - 1
                       for n, b in (("Base", base), ("Risk-controlled", ctrl))}) * 100
    worst = wk.nsmallest(5, "Base")
    worst.index = worst.index.strftime("week ending %Y-%m-%d")
    worst.to_csv(OUT / "C_worst_weeks.csv")
    print("\n=== STRATEGY C WORST 5 WEEKS (net %, base vs risk-controlled) ===")
    print(worst.round(2).to_string())

    # --- control vs base ---
    rows = {}
    for name, b in (("Base", base), ("Risk-controlled", ctrl)):
        for pname, (s, e) in C.periods().items():
            rows[(name, pname)] = C.perf(b["net"].loc[s:e], b["turnover"])
    tab = pd.DataFrame(rows).T
    tab["Avg gross exposure"] = [ (w_base if n == "Base" else w_ctrl).abs().sum(axis=1)
                                  .loc[base["net"].index].loc[s:e].mean()
                                  for (n, p) in tab.index
                                  for s, e in [C.periods()[p]] ]
    tab.to_csv(OUT / "C_risk_control.csv")
    print(f"\n=== STRATEGY C PRE-SPECIFIED RISK CONTROL (net) ===\n"
          f"  cap {CAP_PER_COIN:.3f} of a leg per coin; no longs with 7-day funding < "
          f"{100 * DISTRESS_FUNDING:.0f}% p.a.")
    print(tab.drop(columns=["Start", "End"]).round(2).to_string())
    flagged = (funding.rolling(C.LOOKBACK).mean() * 365 < DISTRESS_FUNDING).sum()
    print("  coin-days flagged as distressed: " + ", ".join(f"{c} {n}" for c, n in flagged.items() if n))
    return base, ctrl


# ---------------------------------------------------------------------------
# 4. Combined portfolio
# ---------------------------------------------------------------------------
def combined(carry_a, c_daily):
    c_m = ((1 + c_daily).resample(MONTH_END).prod() - 1).rename("Strategy C carry (net)")
    df = pd.concat([carry_a, c_m], axis=1, sort=True)

    def scale(r, window):
        vol = r.rolling(window, min_periods=window).std().shift(1) * np.sqrt(12)
        return (TARGET_VOL / vol) * r

    a_s = scale(df.iloc[:, 0].dropna(), VOL_WINDOW_A).rename("A (10% vol)")
    c_s = scale(df.iloc[:, 1].dropna(), VOL_WINDOW_C).rename("C (10% vol)")
    both = pd.concat([a_s, c_s], axis=1, sort=True).dropna()
    both["Combined 50/50"] = both.mean(axis=1)
    tab = pd.DataFrame({c: monthly_perf(both[c]) for c in both.columns}).T
    tab.to_csv(OUT / "combined_portfolio.csv")
    both.to_csv(OUT / "combined_monthly_returns.csv")
    print("\n=== 4. COMBINED PORTFOLIO (each leg scaled to 10% vol with lagged vol, 50/50) ===")
    print(tab.round(2).to_string())
    print(f"  correlation A vs C (scaled, overlap): {both.iloc[:, 0].corr(both.iloc[:, 1]):.3f}")

    fig, ax = plt.subplots(figsize=(10, 5))
    for c in both.columns:
        ax.plot((1 + both[c]).cumprod(), label=c, lw=2 if "Combined" in c else 1)
    ax.set_title("Strategy A, Strategy C and the 50/50 combination (net, vol-scaled)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "combined_portfolio.png", dpi=150)


def main():
    C = load_strategy_c()
    carry_a = strategy_a()
    base, ctrl = strategy_c(C)
    combined(carry_a, base["net"])
    print(f"\nSaved tables and figure to {OUT}/")


if __name__ == "__main__":
    main()
