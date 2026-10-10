"""Extra figures for the paper. Run from the repo root: python paper/make_paper_figures.py . paper/figures"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
NAVY, AMBER, SLATE, RED, GREEN = "#14213D", "#E39B17", "#5C677D", "#B83227", "#2E7D4F"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#B8BEC9")
    ax.tick_params(colors=SLATE, labelsize=10)
    ax.grid(axis="y", color="#E4E7EC", lw=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.tight_layout(); fig.savefig(OUT / f"{name}.png", dpi=200, facecolor="white"); plt.close(fig)


def dd(r):
    w = (1 + r.fillna(0)).cumprod()
    return (w / w.cummax() - 1) * 100


a = pd.read_csv(REPO / "output/strategyA/monthly_returns.csv", index_col=0, parse_dates=True)

# 1. crowding signal and drawdowns
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 6.0), sharex=True, gridspec_kw={"height_ratios": [1, 1]})
crowd = a["crowding"]
crowded = crowd > 1
ax1.plot(crowd, color=NAVY, lw=1.1)
ax1.axhline(1, color=RED, ls="--", lw=1)
ax1.fill_between(crowd.index, crowd.min() - 0.2, crowd.max() + 0.2, where=crowded, color=RED, alpha=0.12, lw=0)
ax1.set_ylabel("Crowding measure", color=SLATE)
ax1.text(crowd.index[3], 1.15, "threshold = 1", color=RED, fontsize=9)
style(ax1)
ax2.plot(dd(a["Carry (net)"]), color=NAVY, lw=1.4, label="Carry (net)")
ax2.plot(dd(a["Crowd-filtered (net)"]), color=AMBER, lw=1.4, label="Crowd-filtered (net)")
ax2.set_ylabel("Drawdown (%)", color=SLATE)
ax2.legend(frameon=False, fontsize=10, loc="lower left")
style(ax2)
save(fig, "a_crowding_drawdown")

# 2. portfolio composition
w = pd.read_csv(REPO / "output/strategyA/weights_carry.csv", index_col=0, parse_dates=True).loc["1999-05":"2026-08"]
w = w[(w != 0).any(axis=1)]
longs = (w > 0).mean() * 100; shorts = (w < 0).mean() * 100
order = (longs - shorts).sort_values().index
fig, ax = plt.subplots(figsize=(7.0, 3.8))
y = np.arange(len(order))
ax.barh(y, longs[order], color=GREEN, label="Long (high rate)")
ax.barh(y, -shorts[order], color=RED, label="Short (low rate)")
for i, c in enumerate(order):
    if longs[c] > 3: ax.text(longs[c] + 1, i, f"{longs[c]:.0f}%", va="center", fontsize=9, color=SLATE)
    if shorts[c] > 3: ax.text(-shorts[c] - 1, i, f"{shorts[c]:.0f}%", va="center", ha="right", fontsize=9, color=SLATE)
ax.set_yticks(y); ax.set_yticklabels(order)
ax.axvline(0, color="#B8BEC9", lw=0.8)
ax.set_xlim(-115, 115)
ax.set_xticks([-100, -50, 0, 50, 100]); ax.set_xticklabels(["100", "50", "0", "50", "100"])
ax.set_xlabel("Share of months in the portfolio (%)", color=SLATE)
ax.legend(frameon=False, fontsize=9, loc="lower right")
style(ax); ax.grid(axis="y", visible=False); ax.grid(axis="x", color="#E4E7EC", lw=0.8)
save(fig, "a_positions")

# 3. funding by coin
cs = pd.read_csv(REPO / "output/strategyC/coin_summary.csv", index_col=0).drop(index="USDC", errors="ignore")
cs = cs.sort_values("avg_funding_ann_%")
fig, ax = plt.subplots(figsize=(7.0, 4.0))
ax.barh(cs.index, cs["avg_funding_ann_%"], color=[RED if v < 0 else NAVY for v in cs["avg_funding_ann_%"]])
for i, (v, p) in enumerate(zip(cs["avg_funding_ann_%"], cs["pos_funding_days_%"])):
    ax.text(max(v, 0) + 0.4, i, f"{v:.1f}%  ({p:.0f}% of days > 0)", va="center", fontsize=8.5, color=SLATE)
ax.axvline(0, color="#B8BEC9", lw=0.8)
ax.set_xlabel("Average funding rate (% a year)", color=SLATE)
ax.set_xlim(cs["avg_funding_ann_%"].min() - 2, cs["avg_funding_ann_%"].max() + 14)
style(ax); ax.grid(axis="y", visible=False); ax.grid(axis="x", color="#E4E7EC", lw=0.8)
save(fig, "c_funding_by_coin")

# 4. crypto drawdown
cd = pd.read_csv(REPO / "output/strategyC/daily_returns.csv", index_col=0, parse_dates=True)
r = cd["Crypto carry (net)"].dropna()
fig, ax = plt.subplots(figsize=(8.2, 3.6))
d = dd(r)
ax.fill_between(d.index, d, 0, color=NAVY, alpha=0.85, lw=0)
for day, lab in (("2021-04-15", "DOGE/XRP rally"), ("2022-05-09", "LUNA"), ("2022-11-08", "FTX")):
    ax.axvline(pd.Timestamp(day), color=RED, ls=":", lw=1)
    ax.text(pd.Timestamp(day), 2, " " + lab, color=RED, fontsize=9, va="bottom")
ax.axvline(pd.Timestamp("2024-01-01"), color=SLATE, ls=":", lw=1)
ax.text(pd.Timestamp("2024-01-20"), -70, "out-of-sample", color=SLATE, fontsize=9)
ax.set_ylabel("Drawdown (%)", color=SLATE); ax.set_ylim(-75, 8)
style(ax)
save(fig, "c_drawdown")

# 5. rolling correlation of A and C
ca = a["Carry (net)"]
cm = (1 + r).resample("ME").prod() - 1
both = pd.concat([ca, cm], axis=1, keys=["A", "C"]).dropna()
rc = both["A"].rolling(24).corr(both["C"]).dropna()
fig, ax = plt.subplots(figsize=(8.2, 3.4))
ax.plot(rc, color=NAVY, lw=1.6)
ax.axhline(both.corr().iloc[0, 1], color=AMBER, ls="--", lw=1.2)
ax.text(rc.index[1], 0.55, f"full-sample correlation {both.corr().iloc[0, 1]:.2f}", color=AMBER, fontsize=9)
ax.axhline(0, color="#B8BEC9", lw=0.8)
ax.set_ylabel("24-month correlation", color=SLATE); ax.set_ylim(-1, 1)
style(ax)
save(fig, "ac_rolling_corr")
# print(len(both), both.corr().iloc[0, 1], rc.min(), rc.max())
# print(longs.round(0).to_dict(), shorts.round(0).to_dict(), len(w))

# 6. Strategy A P&L by currency, split into interest carry and spot moves
import importlib.util
spec = importlib.util.spec_from_file_location("sa", REPO / "code/02_backtest_strategyA.py")
sa = importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
spot, rates, _ = sa.load()
rx = sa.excess_returns(spot, rates)
ir = (rates[sa.CCYS].shift(1).sub(rates["USD"].shift(1), axis=0)) / 1200
wa = pd.read_csv(REPO / "output/strategyA/weights_carry.csv", index_col=0, parse_dates=True)[sa.CCYS]
wl = wa.shift(1).reindex(rx.index)
per = slice("1999-05", "2026-08")
tot = (wl * rx).loc[per].sum() * 100
intr = (wl * ir).loc[per].sum() * 100
fxm = tot - intr
order = tot.sort_values().index
fig, ax = plt.subplots(figsize=(7.0, 3.8))
y = np.arange(len(order)); h = 0.38
ax.barh(y + h / 2, intr[order], h, color=NAVY, label="Interest carry")
ax.barh(y - h / 2, fxm[order], h, color=AMBER, label="Spot moves")
ax.scatter(tot[order], y, color=RED, zorder=3, s=22, label="Total")
ax.set_yticks(y); ax.set_yticklabels(order)
ax.axvline(0, color="#B8BEC9", lw=0.8)
ax.set_xlabel("Total P&L contribution, gross (% pts)", color=SLATE)
ax.legend(frameon=False, fontsize=9, loc="lower right")
style(ax); ax.grid(axis="y", visible=False); ax.grid(axis="x", color="#E4E7EC", lw=0.8)
save(fig, "a_contrib")
# print(pd.DataFrame({"interest": intr, "spot": fxm, "total": tot}).round(1).sort_values("total"))
# print("sum", tot.sum().round(1), (a["Carry (gross)"].loc[per].sum() * 100).round(1))

# 7. robustness grids for A and C
ga = pd.read_csv(REPO / "output/strategyA/robustness_grid.csv")
gc = pd.read_csv(REPO / "output/strategyC/robustness_grid.csv")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.9))
la = [f"{t:g}\n{s:.0%}" for t, s in zip(ga["threshold"], ga["crowded_scale"])]
x = np.arange(len(ga)); h = 0.38
ax1.bar(x - h / 2, ga["Sharpe full"], h, color=NAVY, label="Full sample")
ax1.bar(x + h / 2, ga["Sharpe OOS"], h, color=AMBER, label="Out-of-sample")
ax1.axhline(0.37, color=NAVY, ls=":", lw=1); ax1.axhline(0.27, color=AMBER, ls=":", lw=1)
ax1.set_xticks(x); ax1.set_xticklabels([t + "*" if i == 3 else t for i, t in enumerate(la)], fontsize=8.5)
ax1.set_xlabel("Threshold / exposure when crowded", color=SLATE)
ax1.set_ylabel("Net Sharpe ratio", color=SLATE); ax1.set_title("A. Crowding filter (FX)", color=NAVY, fontsize=11)
ax1.set_ylim(0, 0.5); ax1.legend(frameon=False, fontsize=8.5, loc="upper left")
style(ax1)
lc = [f"{d}d\n{r}" for d, r in zip(gc["lookback_days"], gc["rebalance"])]
x = np.arange(len(gc))
ax2.bar(x - h / 2, gc["Sharpe net"], h, color=NAVY, label="Full sample")
ax2.bar(x + h / 2, gc["Sharpe OOS net"], h, color=AMBER, label="Out-of-sample")
ax2.set_xticks(x); ax2.set_xticklabels([t + "*" if i == 3 else t for i, t in enumerate(lc)], fontsize=8.5)
ax2.set_xlabel("Funding lookback / rebalancing", color=SLATE)
ax2.set_title("B. Crypto funding carry", color=NAVY, fontsize=11)
ax2.set_ylim(0, 1.4); style(ax2)
save(fig, "robustness")

# 8. combined portfolio (A and B at 10% vol) and Strategy B performance panel (paper labels: crypto = Strategy B)
cm = pd.read_csv(REPO / "output/risk/combined_monthly_returns.csv", index_col=0, parse_dates=True)
fig, ax = plt.subplots(figsize=(8.2, 4.4))
ax.plot((1 + cm["A (10% vol)"]).cumprod(), color=NAVY, lw=1.6, label="A (10% vol)")
ax.plot((1 + cm["C (10% vol)"]).cumprod(), color=SLATE, lw=1.6, label="B (10% vol)")
ax.plot((1 + cm["Combined 50/50"]).cumprod(), color=AMBER, lw=2.6, label="Combined 50/50")
ax.set_ylabel("Growth of $1", color=SLATE); ax.legend(frameon=False, fontsize=10, loc="upper left")
style(ax); save(fig, "comb")

bt = pd.read_csv(REPO / "output/strategyC/daily_returns.csv", index_col=0, parse_dates=True).dropna(subset=["Crypto carry (net)"])
fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
ax[0].plot((1 + bt["Crypto carry (gross)"]).cumprod(), color=NAVY, lw=1.2, label="Strategy B (gross)")
ax[0].plot((1 + bt["Crypto carry (net)"]).cumprod(), color=AMBER, lw=1.2, label="Strategy B (net)")
ax[0].set_yscale("log"); ax[0].set_yticks([0.6, 0.8, 1.0, 1.5, 2.0]); ax[0].set_yticklabels(["0.6", "0.8", "1.0", "1.5", "2.0"]); ax[0].minorticks_off(); ax[0].axvline(pd.Timestamp("2024-01-01"), color=SLATE, ls="--", lw=1)
ax[0].text(pd.Timestamp("2024-01-20"), 0.62, "out-of-sample", color=SLATE, fontsize=9)
ax[0].set_ylabel("Growth of $1 (log)", color=SLATE); ax[0].legend(frameon=False, fontsize=10, loc="upper right")
ax[1].plot(dd(bt["Crypto carry (net)"]), color=AMBER, lw=1.2); ax[1].set_ylabel("Drawdown (%)", color=SLATE)
ax[2].plot(100 * bt["funding component"].cumsum(), color=GREEN, lw=1.4, label="Funding component")
ax[2].plot(100 * bt["price component"].cumsum(), color=RED, lw=1.2, label="Price component")
ax[2].set_ylabel("Cumulative (%)", color=SLATE); ax[2].legend(frameon=False, fontsize=10, loc="lower left")
for a_ in ax: style(a_)
save(fig, "c_performance")
