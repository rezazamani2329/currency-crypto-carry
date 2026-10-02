"""
06_build_web.py
MFE 230GB Final Project - build the self-contained interactive page web/index.html

Reads the result files in output/ (written by scripts 02, 04 and 05), recomputes
the Strategy C robustness variants for the interactive selector, and embeds
everything as JSON in a single HTML file. Charts use Plotly.js from cdnjs.

Run from the project root:  python code/06_build_web.py
"""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT_A = Path("output/strategyA")
OUT_C = Path("output/strategyC")
OUT_R = Path("output/risk")
WEB = Path("web")
WEB.mkdir(exist_ok=True)


def records(df, digits=3):
    """DataFrame -> {columns, rows} with rounded numbers, index flattened into columns."""
    df = df.reset_index()
    df.columns = ["" if str(c).startswith(("level_", "Unnamed")) or str(c) == "index" else str(c)
                  for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        row = []
        for v in r.values:
            if isinstance(v, (float, np.floating)):
                row.append(None if np.isnan(v) else round(float(v), digits))
            elif isinstance(v, (int, np.integer)):
                row.append(int(v))
            else:
                row.append(str(v))
        rows.append(row)
    return {"columns": list(df.columns), "rows": rows}


def series(s, digits=5):
    s = s.dropna()
    return {"x": [d.strftime("%Y-%m-%d") for d in s.index],
            "y": [round(float(v), digits) for v in s.values]}


def cum(r):
    return (1 + r.fillna(0)).cumprod()


def read_table(path, index_cols):
    return pd.read_csv(path, index_col=list(range(index_cols)))


def strategy_c_variants():
    """Weekly-sampled cumulative net/gross curves for each lookback x rebalance."""
    spec = importlib.util.spec_from_file_location("stratC", "code/04_backtest_strategyC.py")
    C = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(C)
    close, volume, funding = C.load()
    ret = close.pct_change(fill_method=None)
    tradable = close.notna() & volume.gt(0)
    out = {}
    for lb in (3, 7, 30):
        for rb in ("D", "W"):
            w = C.carry_weights(funding, tradable, lb, rb)
            b = C.backtest(w, ret, funding, C.TC_BP)
            key = f"{lb}{rb}"
            out[key] = {k: series(cum(b[k]).resample("W-SUN").last(), 4)
                        for k in ("gross", "net")}
    return out


def build_data():
    d = {}
    # ---- Strategy A ----
    a = pd.read_csv(OUT_A / "monthly_returns.csv", index_col=0, parse_dates=True)
    d["A_cum"] = {c: series(cum(a[c]), 4) for c in
                  ("Carry (gross)", "Carry (net)", "Crowd-filtered (gross)", "Crowd-filtered (net)")}
    d["A_crowd"] = series(a["crowding"], 3)
    d["A_perf"] = records(read_table(OUT_A / "performance_table.csv", 2))
    d["A_crowded"] = records(read_table(OUT_A / "crowded_vs_not.csv", 1))
    d["A_grid"] = records(pd.read_csv(OUT_A / "robustness_grid.csv").set_index("threshold"))
    # ---- risk ----
    d["A_lrv"] = records(read_table(OUT_R / "A_vs_LRV_HML.csv", 1))
    d["A_reg"] = records(read_table(OUT_R / "A_factor_regressions.csv", 2))
    d["A_worst"] = records(read_table(OUT_R / "A_worst_months.csv", 1), 2)
    d["C_coins"] = records(read_table(OUT_R / "C_coin_summary.csv", 1), 2)
    d["C_contrib"] = records(read_table(OUT_R / "C_contribution_by_coin.csv", 1), 1)
    d["C_control"] = records(read_table(OUT_R / "C_risk_control.csv", 2)
                             .drop(columns=["Start", "End"]))
    d["C_worst"] = records(read_table(OUT_R / "C_worst_weeks.csv", 1), 2)
    comb = pd.read_csv(OUT_R / "combined_monthly_returns.csv", index_col=0, parse_dates=True)
    d["comb_cum"] = {c: series(cum(comb[c]), 4) for c in comb.columns}
    d["comb_perf"] = records(read_table(OUT_R / "combined_portfolio.csv", 1))
    d["comb_corr"] = round(float(comb.iloc[:, 0].corr(comb.iloc[:, 1])), 3)
    lrv = pd.read_csv(OUT_R / "A_vs_LRV_HML.csv", index_col=0)
    d["lrv_corr"] = round(float(lrv["Correlation"].iloc[0]), 2)
    # ---- Strategy C ----
    c = pd.read_csv(OUT_C / "daily_returns.csv", index_col=0, parse_dates=True)
    d["C_cum"] = {"Crypto carry (gross)": series(cum(c["Crypto carry (gross)"]), 4),
                  "Crypto carry (net)": series(cum(c["Crypto carry (net)"]), 4)}
    d["C_decomp_cum"] = {"Funding component": series(100 * c["funding component"].cumsum(), 2),
                         "Price component": series(100 * c["price component"].cumsum(), 2)}
    d["C_perf"] = records(read_table(OUT_C / "performance_table.csv", 2))
    d["C_decomp"] = records(read_table(OUT_C / "return_decomposition.csv", 1), 2)
    d["C_grid"] = records(pd.read_csv(OUT_C / "robustness_grid.csv").set_index("lookback_days"), 2)
    d["C_variants"] = strategy_c_variants()
    return d


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crowded Carry</title>
<meta name="description" content="Crash risk in FX and crypto carry trades - MFE 230GB final project">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.0/plotly.min.js"></script>
<style>
:root {
  --bg: #fbfaf7; --surface: #ffffff; --text: #1d1d1f; --muted: #5f6368; --line: #e3e1db;
  --accent: #1f5fae; --accent2: #c2571a; --good: #2e7d4f; --bad: #b3261e; --grid: #ecebe6;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #15171a; --surface: #1d2024; --text: #e8e6e1; --muted: #a2a6ab; --line: #30343a;
    --accent: #7fb0ec; --accent2: #f0a46b; --good: #6cc391; --bad: #f08a80; --grid: #2a2e33;
  }
}
:root[data-theme="dark"] {
  --bg: #15171a; --surface: #1d2024; --text: #e8e6e1; --muted: #a2a6ab; --line: #30343a;
  --accent: #7fb0ec; --accent2: #f0a46b; --good: #6cc391; --bad: #f08a80; --grid: #2a2e33;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
header { border-bottom: 1px solid var(--line); background: var(--surface); }
.wrap { max-width: 980px; margin: 0 auto; padding: 0 16px; }
header .wrap { padding-top: 28px; padding-bottom: 22px; }
h1 { font-size: clamp(1.6rem, 4vw, 2.3rem); margin: 0 0 6px; letter-spacing: -0.01em; }
h2 { font-size: 1.45rem; margin: 48px 0 8px; padding-top: 8px; border-top: 1px solid var(--line); }
h3 { font-size: 1.08rem; margin: 28px 0 6px; }
p, li { color: var(--text); }
.sub { color: var(--muted); margin: 0; }
nav { position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); }
nav .wrap { display: flex; gap: 18px; overflow-x: auto; padding-top: 10px; padding-bottom: 10px; white-space: nowrap; }
nav a { color: var(--muted); text-decoration: none; font-size: 0.92rem; }
nav a:hover { color: var(--accent); }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 10px 0; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.seg button { background: var(--surface); color: var(--text); border: 0; padding: 6px 12px; font: inherit;
  font-size: 0.88rem; cursor: pointer; }
.seg button + button { border-left: 1px solid var(--line); }
.seg button.on { background: var(--accent); color: var(--bg); }
.label { font-size: 0.85rem; color: var(--muted); }
.chart { width: 100%; height: 380px; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
.chart.short { height: 260px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 16px 0; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }
.card .k { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.card .v { font-size: 1.5rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.card .n { font-size: 0.85rem; color: var(--muted); }
.tbl { overflow-x: auto; margin: 10px 0 4px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 10px; text-align: right; white-space: nowrap; border-bottom: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; background: var(--bg); position: sticky; top: 0; }
td:first-child, th:first-child, td.txt { text-align: left; }
tr:last-child td { border-bottom: 0; }
td.neg { color: var(--bad); }
.note { border-left: 3px solid var(--accent2); padding: 8px 14px; background: var(--surface); border-radius: 0 8px 8px 0; margin: 14px 0; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 720px) { .two { grid-template-columns: 1fr; } .chart { height: 320px; } }
code { background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 1px 5px; font-size: 0.88em; }
pre { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 12px; overflow-x: auto; }
footer { color: var(--muted); font-size: 0.85rem; padding: 40px 0 60px; }
.theme { margin-left: auto; }
</style>
</head>
<body>
<header><div class="wrap">
  <h1>Crowded Carry</h1>
  <p class="sub">Crash risk in FX and crypto carry trades &middot; MFE 230GB Currency Markets, final project</p>
</div></header>
<nav><div class="wrap">
  <a href="#idea">Idea</a><a href="#a">Strategy A: G10 FX</a><a href="#c">Strategy C: crypto</a>
  <a href="#combo">Combined</a><a href="#data">Data &amp; replication</a>
  <span class="theme seg"><button data-t="auto" class="on">Auto</button><button data-t="light">Light</button><button data-t="dark">Dark</button></span>
</div></nav>

<main class="wrap">
<section id="idea">
<h2>1. The idea</h2>
<p>A carry trade buys high-yielding assets and funds them with low-yielding ones. It earns a risk premium
on average, but the premium is compensation for <b>crash risk</b>: when many investors hold the same trade and
are forced to unwind at once, losses are sudden and large (Brunnermeier, Nagel &amp; Pedersen 2008).</p>
<p>We test this mechanism in two markets with the same economic structure but very different investors:</p>
<div class="cards">
  <div class="card"><div class="k">Strategy A &middot; developed markets</div>
    <div class="v">G10 FX carry</div>
    <div class="n">Signal: 3-month interest differential. Alternative data: CFTC speculative positioning as a crowding gauge.</div></div>
  <div class="card"><div class="k">Strategy C &middot; crypto</div>
    <div class="v">Funding carry</div>
    <div class="n">Signal: perpetual-futures funding rates, the crypto analogue of an interest differential. Shorts crowded-long coins.</div></div>
  <div class="card"><div class="k">Key check</div>
    <div class="v" id="kpi-corr">&ndash;</div>
    <div class="n">Correlation of our Strategy A with the Lustig-Roussanov-Verdelhan developed carry factor.</div></div>
</div>
</section>

<section id="a">
<h2>2. Strategy A: crowded G10 carry</h2>
<p><b>Rule.</b> At each month-end, rank JPY, EUR, GBP, CHF, CAD, AUD and NZD by their 3-month rate minus the US rate.
Go long the 2 highest and short the 2 lowest, equal weights, dollar-neutral. Returns include the interest differential
(covered interest parity). Costs: 3 bp per unit traded.</p>
<p><b>Crowding filter.</b> CFTC Commitments of Traders: net speculative position / open interest, z-scored over 36 months
and used only after its Friday release. Portfolio crowding = average z of the long leg minus that of the short leg.
When crowding &gt; 1, positions are cut to half. In-sample ends 2010; 2011 onward is out-of-sample.</p>
<div class="controls"><span class="label">Returns:</span>
  <span class="seg" id="a-gn"><button data-v="net" class="on">Net of costs</button><button data-v="gross">Gross</button></span></div>
<div id="a-cum" class="chart"></div>
<h3>Crowding signal</h3>
<div id="a-crowd" class="chart short"></div>
<h3>Performance</h3>
<div class="tbl" id="a-perf"></div>
<h3>Does crowding predict bad carry months?</h3>
<div class="tbl" id="a-crowded"></div>
<div class="note">Next-month carry averages 0.30% after uncrowded months but only 0.02% after crowded months, with more
negative skew. The filter lifts the out-of-sample Sharpe ratio (0.27 &rarr; 0.32 net) but does not avoid the 2008 crash,
which began from a non-crowded reading.</div>
<h3>Robustness: threshold &times; exposure when crowded</h3>
<div class="tbl" id="a-grid"></div>
<h3>Validation against the academic carry factor</h3>
<p>Our monthly net carry vs the developed-country HML portfolio of Lustig, Roussanov &amp; Verdelhan (course file
<code>CurrencyPortfolios.xls</code>), overlapping months:</p>
<div class="tbl" id="a-lrv"></div>
<h3>When does Strategy A lose money?</h3>
<p>Regression of monthly net carry on the dollar factor (RX, average excess return of all developed currencies)
and on innovations in aggregate equity volatility, with Newey-West t-statistics:</p>
<div class="tbl" id="a-reg"></div>
<div class="note">Carry loses when global volatility spikes (t &asymp; &minus;4): the textbook carry-crash exposure.
After controlling for the dollar factor and volatility, the alpha is not significant.</div>
<div class="two"><div><h3>Worst 10 months</h3><div class="tbl" id="a-worst"></div></div>
<div><h3>2008 crash</h3><p>July 2008 to March 2009: <b>&minus;20.5%</b> cumulative, with the worst month in October 2008
(&minus;12.0%) as funding currencies (JPY, CHF) rallied. The 2015 Swiss franc de-peg is also among the worst months.</p></div></div>
</section>

<section id="c">
<h2>3. Strategy C: crypto funding carry</h2>
<p><b>Rule.</b> Universe: 12 Binance USDT perpetuals, including LUNA and FTT, which collapsed, to avoid survivorship bias
(USDC is used only as a sanity check). A coin is tradable only on days with a price and positive volume.
Every Sunday, rank coins by their trailing 7-day average funding rate; <b>short the top third, long the bottom third</b>,
equal weights, dollar-neutral. Shorts receive positive funding. Costs: 5 bp per unit traded.
In-sample 2020&ndash;2023, out-of-sample 2024 onward.</p>
<h3>The coins</h3>
<div class="tbl" id="c-coins"></div>
<div class="controls"><span class="label">Returns:</span>
  <span class="seg" id="c-gn"><button data-v="net" class="on">Net of costs</button><button data-v="gross">Gross</button></span></div>
<div id="c-cum" class="chart"></div>
<h3>Where the return comes from</h3>
<div class="two"><div id="c-decomp" class="chart short"></div><div class="tbl" id="c-decomp-t"></div></div>
<div class="note">Funding income is positive (+8.6% a year), but in 2020&ndash;2023 the short leg (crowded longs such as
DOGE and XRP) rallied and wiped it out. The out-of-sample gain is mostly price, not funding.</div>
<h3>Performance</h3>
<div class="tbl" id="c-perf"></div>
<h3>Robustness: lookback &times; rebalancing</h3>
<div class="controls">
  <span class="label">Lookback:</span><span class="seg" id="c-lb"><button data-v="3">3 days</button><button data-v="7" class="on">7 days</button><button data-v="30">30 days</button></span>
  <span class="label">Rebalance:</span><span class="seg" id="c-rb"><button data-v="D">Daily</button><button data-v="W" class="on">Weekly</button></span>
</div>
<div id="c-var" class="chart short"></div>
<div class="tbl" id="c-grid"></div>
<div class="note">The pre-specified case (7 days, weekly) is close to the weakest. Shorter signals do better even after
costs, which suggests funding information decays within days. We report the pre-specified case as the main result.</div>
<h3>Risk: who causes the losses?</h3>
<p>Beta to BTC is essentially zero (&minus;0.02, t = &minus;0.75): the strategy is market-neutral. Its risk comes from
individual coins. Profit and loss by coin, in percentage points:</p>
<div id="c-contrib" class="chart short"></div>
<h3>Worst weeks and a pre-specified risk control</h3>
<p>Fixed before running it: cap each coin at 1/6 of its leg, and do not hold as a long any coin whose 7-day funding is below &minus;50% a year
(a &ldquo;distress&rdquo; filter).</p>
<div class="two"><div class="tbl" id="c-worst"></div><div class="tbl" id="c-control"></div></div>
<div class="note"><b>Honest result:</b> the control halves losses in the LUNA and FTX weeks, but mainly because the cap leaves
about half the capital unused, so the Sharpe ratio falls. LUNA's funding crossed &minus;50% only mid-week (10 May 2022),
after the weekly rebalance, and the filter also blocked the two biggest winners (BNB, SOL). In crypto, deeply negative
funding usually signals crowded <i>shorts</i>, whose forced covering pushes prices up, not distress. Crypto carry's crash
risk is the mirror image of FX: it ends up long whatever traders short hardest.</div>
</section>

<section id="combo">
<h2>4. Combined portfolio</h2>
<p>Each strategy is scaled to 10% volatility using only past volatility (36 months for A, 12 for C), then combined 50/50.</p>
<div id="comb-cum" class="chart"></div>
<div class="tbl" id="comb-perf"></div>
<div class="note">Correlation between A and C: <b id="comb-corr"></b>. FX and crypto carry crash at different times, so
combining them cuts volatility, although C was weak during the overlap.</div>
</section>

<section id="data">
<h2>5. Data &amp; replication</h2>
<div class="tbl"><table>
<tr><th>Data</th><th>Source</th><th>Series</th></tr>
<tr><td>FX spot</td><td class="txt">FRED (Fed H.10)</td><td class="txt">DEXJPUS, DEXUSEU, DEXUSUK, DEXSZUS, DEXCAUS, DEXUSAL, DEXUSNZ</td></tr>
<tr><td>3-month rates</td><td class="txt">OECD via FRED</td><td class="txt">IR3TIB01xxM156N</td></tr>
<tr><td>Positioning</td><td class="txt">CFTC Commitments of Traders</td><td class="txt">legacy futures-only, 1986&ndash;2026</td></tr>
<tr><td>Crypto prices &amp; funding</td><td class="txt">Binance public archive</td><td class="txt">data.binance.vision, USDT-M perpetuals</td></tr>
<tr><td>Carry factor check</td><td class="txt">Lustig, Roussanov &amp; Verdelhan</td><td class="txt">CurrencyPortfolios.xls (course file)</td></tr>
</table></div>
<pre>pip install -r requirements.txt
python run_all.py                  # downloads + all analysis + this page
SKIP_DOWNLOAD=1 python run_all.py  # use the committed data/clean snapshot</pre>
<p>FRED often blocks scripted downloads: save each series by hand as <code>data/raw/fred_&lt;ID&gt;.csv</code>.
All parameters were fixed before backtesting; the robustness grids report the alternatives.</p>
</section>
<footer>Generated by <code>code/06_build_web.py</code> from the files in <code>output/</code>. Built __BUILT__.</footer>
</main>

<script>
const D = __DATA__;
const $ = id => document.getElementById(id);
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

function table(id, t, opts = {}) {
  const el = $(id); if (!el) return;
  let h = "<table><tr>" + t.columns.map(c => `<th>${c}</th>`).join("") + "</tr>";
  for (const r of t.rows) {
    h += "<tr>" + r.map((v, i) => {
      if (v === null) return "<td>&ndash;</td>";
      if (typeof v === "number") {
        const d = (Number.isInteger(v) || Math.abs(v) >= 100) ? 0 : (opts.digits ?? 2);
        return `<td class="${v < 0 ? "neg" : ""}">${v.toLocaleString(undefined, {minimumFractionDigits: d, maximumFractionDigits: d})}</td>`;
      }
      return `<td class="txt">${v}</td>`;
    }).join("") + "</tr>";
  }
  el.innerHTML = h + "</table>";
}

function layout(extra = {}) {
  const text = css("--text"), grid = css("--grid"), muted = css("--muted");
  return Object.assign({
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: {color: text, size: 12, family: "-apple-system, Segoe UI, Roboto, sans-serif"},
    margin: {l: 52, r: 16, t: 30, b: 40}, hovermode: "x unified",
    legend: {orientation: "h", y: 1.12, x: 0, font: {color: muted}},
    xaxis: {gridcolor: grid, linecolor: grid, zeroline: false},
    yaxis: {gridcolor: grid, linecolor: grid, zeroline: false},
  }, extra);
}
const cfg = {displayModeBar: false, responsive: true};
const line = (s, name, color, extra = {}) => Object.assign({x: s.x, y: s.y, name, type: "scatter", mode: "lines",
  line: {color, width: 1.8}}, extra);
const vline = (x, label) => ({type: "line", x0: x, x1: x, yref: "paper", y0: 0, y1: 1,
  line: {color: css("--muted"), width: 1, dash: "dot"}});
const vlabel = (x, text) => ({x, yref: "paper", y: 1, text, showarrow: false, xanchor: "left",
  font: {size: 10, color: css("--muted")}});

let aMode = "net", cMode = "net", lb = "7", rb = "W";

function drawA() {
  const sfx = aMode === "net" ? "(net)" : "(gross)";
  Plotly.react("a-cum", [
    line(D.A_cum["Carry " + sfx], "Carry " + sfx, css("--accent")),
    line(D.A_cum["Crowd-filtered " + sfx], "Crowd-filtered " + sfx, css("--accent2")),
  ], layout({title: {text: "Growth of $1 (log scale)", font: {size: 13}}, yaxis: {type: "log", gridcolor: css("--grid")},
    shapes: [vline("2011-01-01")], annotations: [vlabel("2011-01-01", " out-of-sample →")]}), cfg);
  Plotly.react("a-crowd", [line(D.A_crowd, "Crowding", css("--text"), {line: {width: 1, color: css("--text")}})],
    layout({showlegend: false, margin: {l: 52, r: 16, t: 10, b: 30},
      shapes: [{type: "line", xref: "paper", x0: 0, x1: 1, y0: 1, y1: 1, line: {color: css("--bad"), dash: "dash", width: 1}}]}), cfg);
}

function drawC() {
  const k = cMode === "net" ? "Crypto carry (net)" : "Crypto carry (gross)";
  const ev = [["2020-03-12", "Covid"], ["2022-05-09", "LUNA"], ["2022-11-08", "FTX"]];
  Plotly.react("c-cum", [line(D.C_cum[k], k, css("--accent"))],
    layout({title: {text: "Growth of $1 (log scale)", font: {size: 13}}, yaxis: {type: "log", gridcolor: css("--grid")},
      shapes: [vline("2024-01-01"), ...ev.map(e => vline(e[0]))],
      annotations: [vlabel("2024-01-01", " out-of-sample →"), ...ev.map(e => vlabel(e[0], " " + e[1]))]}), cfg);
  Plotly.react("c-decomp", [
    line(D.C_decomp_cum["Funding component"], "Funding", css("--good")),
    line(D.C_decomp_cum["Price component"], "Price", css("--bad")),
  ], layout({title: {text: "Cumulative contribution (% pts)", font: {size: 13}}}), cfg);
}

function drawVar() {
  const v = D.C_variants[lb + rb];
  Plotly.react("c-var", [line(v[cMode], `${lb}-day, ${rb === "D" ? "daily" : "weekly"} (${cMode})`, css("--accent"))],
    layout({yaxis: {type: "log", gridcolor: css("--grid")}, margin: {l: 52, r: 16, t: 30, b: 30}}), cfg);
  document.querySelectorAll("#c-grid tr").forEach((tr, i) => {
    if (i === 0) return;
    const c = tr.children;
    tr.style.fontWeight = (c[0].textContent === lb && c[1].textContent === (rb === "D" ? "daily" : "weekly")) ? "700" : "";
  });
}

function drawStatic() {
  const t = D.C_contrib;
  const ci = t.columns.indexOf("total P&L (% pts)");
  Plotly.react("c-contrib", [{type: "bar", orientation: "h", y: t.rows.map(r => r[0]), x: t.rows.map(r => r[ci]),
    marker: {color: t.rows.map(r => r[ci] < 0 ? css("--bad") : css("--good"))}, hovertemplate: "%{y}: %{x:.1f} pts<extra></extra>"}],
    layout({hovermode: "closest", showlegend: false, margin: {l: 60, r: 16, t: 10, b: 30}}), cfg);
  const cols = [css("--accent"), css("--accent2"), css("--text")];
  Plotly.react("comb-cum", Object.keys(D.comb_cum).map((k, i) => line(D.comb_cum[k], k, cols[i],
    {line: {color: cols[i], width: k.startsWith("Combined") ? 2.6 : 1.4}})),
    layout({title: {text: "Growth of $1, each scaled to 10% volatility", font: {size: 13}}}), cfg);
}

function drawAll() { drawA(); drawC(); drawVar(); drawStatic(); }

function seg(id, cb) {
  $(id).querySelectorAll("button").forEach(b => b.addEventListener("click", () => {
    $(id).querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
    cb(b.dataset.v ?? b.dataset.t);
  }));
}
seg("a-gn", v => { aMode = v; drawA(); });
seg("c-gn", v => { cMode = v; drawC(); drawVar(); });
seg("c-lb", v => { lb = v; drawVar(); });
seg("c-rb", v => { rb = v; drawVar(); });
document.querySelectorAll(".theme button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".theme button").forEach(x => x.classList.toggle("on", x === b));
  if (b.dataset.t === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", b.dataset.t);
  drawAll();
}));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", drawAll);

$("kpi-corr").textContent = D.lrv_corr.toFixed(2);
$("comb-corr").textContent = D.comb_corr.toFixed(2);
table("a-perf", D.A_perf); table("a-crowded", D.A_crowded); table("a-grid", D.A_grid);
table("a-lrv", D.A_lrv); table("a-reg", D.A_reg, {digits: 3}); table("a-worst", D.A_worst);
table("c-coins", D.C_coins); table("c-perf", D.C_perf); table("c-decomp-t", D.C_decomp);
table("c-grid", D.C_grid); table("c-worst", D.C_worst); table("c-control", D.C_control);
table("comb-perf", D.comb_perf);
if (window.Plotly) drawAll();
else document.querySelectorAll(".chart").forEach(e => e.innerHTML =
  "<p style='padding:16px;color:var(--muted)'>Charts need an internet connection to load Plotly.js.</p>");
</script>
</body>
</html>
"""


def main():
    data = build_data()
    html = (HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
                .replace("__BUILT__", pd.Timestamp.today().strftime("%Y-%m-%d")))
    path = WEB / "index.html"
    path.write_text(html, encoding="utf-8")
    print(f"Wrote {path} ({path.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()


# ===== Questions this script answers and results =====
# What this builds: web/index.html, a single self-contained page (about 0.34 MB) with
# the idea, Strategy A (rule, cumulative returns, crowding signal, LRV check, risk
# regressions), Strategy C (coins, cumulative returns with Covid/LUNA/FTX marked,
# funding vs price, lookback x rebalance selector, risk control), the combined
# portfolio, and data/replication notes. Gross/net toggles and light/dark mode.
# It only reads output/ and recomputes the Strategy C robustness variants; it does not
# change any results. Charts need an internet connection to load Plotly.js.
