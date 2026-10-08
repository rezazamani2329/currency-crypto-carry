"""
08_build_slides_10min.py
MFE 230GB Final Project - build the 10-minute version of the deck:
slides/presentation_10min.pptx (10 slides) with bullet speaker notes and a time cue
on every slide, plus slides/speaker_notes_10min.md with the same notes for reading.

It reuses the chart and slide helpers of 07_build_slides.py, and every number is read
from output/, so it always matches the latest results.

Requirements: pip install pandas matplotlib python-pptx
Run from the project root:  python code/08_build_slides_10min.py
"""

import importlib.util
import tempfile
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

_spec = importlib.util.spec_from_file_location("deck", Path(__file__).with_name("07_build_slides.py"))
deck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deck)
from_deck = ("NAVY", "AMBER", "SLATE", "WHITE", "TINT", "RED", "HEAD", "W", "H",
             "bg", "text", "box", "title", "stat", "numbered", "picture", "table")
globals().update({k: getattr(deck, k) for k in from_deck})

OUT_A, OUT_C, OUT_R = deck.OUT_A, deck.OUT_C, deck.OUT_R
SLIDES = Path("slides")


def notes(slide, minutes, bullets):
    """Speaker notes: a time cue, then one bullet per line."""
    slide.notes_slide.notes_text_frame.text = "\n".join([f"[about {minutes}]"] + [f"• {b}" for b in bullets])
    return minutes, bullets


def build():
    # charts go to a temporary folder so the images of the 16-slide deck stay unchanged
    deck.IMG = Path(tempfile.mkdtemp())
    ch = deck.make_charts()

    pa = pd.read_csv(OUT_A / "performance_table.csv", index_col=[0, 1])
    pc = pd.read_csv(OUT_C / "performance_table.csv", index_col=[0, 1])
    cv = pd.read_csv(OUT_A / "crowded_vs_not.csv", index_col=0)
    reg = pd.read_csv(OUT_R / "A_factor_regressions.csv", index_col=[0, 1])
    lrv = pd.read_csv(OUT_R / "A_vs_LRV_HML.csv", index_col=0)
    dec = pd.read_csv(OUT_C / "return_decomposition.csv", index_col=0)
    ctl = pd.read_csv(OUT_R / "C_risk_control.csv", index_col=[0, 1])
    cw = pd.read_csv(OUT_R / "C_worst_weeks.csv", index_col=0)
    comb = pd.read_csv(OUT_R / "combined_portfolio.csv", index_col=0)
    cm = pd.read_csv(OUT_R / "combined_monthly_returns.csv", index_col=0)
    a_net = pd.read_csv(OUT_A / "monthly_returns.csv", index_col=0, parse_dates=True)["Carry (net)"]
    crash08 = 100 * ((1 + a_net.loc["2008-07":"2009-03"]).prod() - 1)
    beta = pd.read_csv(OUT_R / "C_beta_btc.csv", index_col=[0, 1])
    contrib = pd.read_csv(OUT_R / "C_contribution_by_coin.csv", index_col=0)["total P&L (% pts)"]

    A = lambda k, p, c="Sharpe": pa.loc[(k, p), c]
    C = lambda p, c="Sharpe": pc.loc[("Crypto carry (net)", p), c]
    m = "RX (dollar) + dVol (LRV)"
    corr = cm.iloc[:, 0].corr(cm.iloc[:, 1])
    script = []

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    blank = prs.slide_layouts[6]

    def new(dark=False):
        s = prs.slides.add_slide(blank)
        bg(s, NAVY if dark else WHITE)
        return s

    # 1 title ---------------------------------------------------------------
    s = new(dark=True)
    text(s, 0.8, 1.45, 11.8, 1.0, "Crowded Carry in G10 FX and Crypto", size=46, font=HEAD, bold=True, color=WHITE)
    text(s, 0.8, 2.6, 11.5, 0.7, "Crash risk in FX and crypto carry trades", size=24, color="C9D1E0")
    text(s, 0.8, 4.3, 5.5, 0.4, "STUDENTS", size=12, bold=True, color="8E9AB5")
    text(s, 0.8, 4.7, 5.8, 0.5, "Reza Zamani  ·  Paraj Goyal", size=20, color=AMBER, bold=True)
    text(s, 7.0, 4.3, 5.5, 0.4, "PROFESSOR", size=12, bold=True, color="8E9AB5")
    text(s, 7.0, 4.7, 5.5, 0.5, "Amir Kermani", size=20, color=WHITE, bold=True)
    text(s, 0.8, 6.0, 11.5, 0.5, "Currency Markets (MFE 230GB)  ·  Final project  ·  October 2026",
         size=15, color="C9D1E0")
    script.append(("Title", *notes(s, "0:20", [
        "Good morning. Our project asks one question: do carry trades crash when they are crowded?",
        "We test it in two markets with the same economics: G10 currencies and crypto.",
        "Strategy A is G10 FX carry with a crowding filter; Strategy C is crypto funding carry.",
    ])))

    # 2 idea + hypotheses -----------------------------------------------------
    s = new()
    title(s, "Carry pays because it crashes", "Same economic mechanism, two very different markets")
    text(s, 0.6, 2.0, 5.6, 4.6, [
        ("Carry: borrow the low-yield asset, hold the high-yield one.", {"bullet": True}),
        ("UIP says this earns nothing; in the data it earns a premium, with rare large crashes.", {"bullet": True}),
        ("Crashes are worst when the trade is crowded and everyone unwinds at once "
         "(Brunnermeier, Nagel & Pedersen 2008).", {"bullet": True}),
        ("Hypotheses, fixed before testing:", {"bold": True, "color": NAVY}),
        ("A: carry earns a premium; crowded months are followed by weaker carry; it loses in volatility spikes.",
         {"bullet": True, "size": 15}),
        ("C: funding carry earns a premium with little BTC exposure; its crashes are coin-specific.",
         {"bullet": True, "size": 15}),
    ], size=17, space_after=12)
    for i, (k, v1, v2) in enumerate([
            ("", "A: G10 FX", "C: Crypto"),
            ("Carry signal", "3-month rate differential", "Perpetual funding rate"),
            ("Crowding data", "CFTC speculator positions", "Funding = leveraged demand"),
            ("Universe", "7 currencies vs USD", "12 coins incl. LUNA, FTT"),
            ("Frequency", "Monthly, 1999–2026", "Weekly, 2020–2026")]):
        yy = 2.0 + i * 0.78
        if i == 0:
            text(s, 8.55, yy, 2.0, 0.5, v1, size=16, bold=True, color=NAVY)
            text(s, 10.65, yy, 2.1, 0.5, v2, size=16, bold=True, color="B7700C")
            continue
        box(s, 6.5, yy - 0.12, 6.25, 0.66)
        text(s, 6.7, yy, 1.8, 0.5, k, size=13, bold=True, color=SLATE)
        text(s, 8.55, yy, 2.0, 0.5, v1, size=13)
        text(s, 10.65, yy, 2.0, 0.5, v2, size=13)
    script.append(("Carry pays because it crashes", *notes(s, "1:00", [
        "Carry means borrowing in a low-yield asset and holding a high-yield one.",
        "Uncovered interest parity says this should earn nothing, but in the data it earns a premium.",
        "The catch is crash risk: carry goes up the stairs and down the elevator.",
        "Brunnermeier, Nagel and Pedersen show crashes are worst when speculators are crowded into the trade.",
        "In FX the yield is the interest differential and we measure crowding with CFTC positions.",
        "In crypto the yield is the perpetual funding rate, which itself measures leveraged demand.",
        "We wrote the hypotheses and all parameters down before running any backtest.",
    ])))

    # 3 data + methodology ------------------------------------------------------
    s = new()
    title(s, "Data and methodology", "Public data; a research design chosen to keep the tests honest")
    table(s, 0.6, 1.9, 6.6, [
        ["Data", "Source", "Coverage"],
        ["FX spot, 7 currencies", "FRED (Fed H.10)", "1999–2026"],
        ["3-month rates", "OECD via FRED", "1999–2026"],
        ["Speculator positions", "CFTC Commitments of Traders", "1986–2026"],
        ["Crypto price, volume, funding", "Binance public archive", "2020–2026"],
        ["Carry factor (validation)", "Lustig–Roussanov–Verdelhan", "1983–2021"],
    ], col_w=[2.5, 2.6, 1.5], size=12, row_h=0.42, left=True)
    text(s, 7.6, 1.9, 5.2, 4.8, [
        ("Parameters fixed before the first backtest", {"bullet": True}),
        ("Out-of-sample: A from 2011, C from 2024", {"bullet": True}),
        ("Costs: 3 bp per unit traded in FX, 5 bp in crypto", {"bullet": True}),
        ("No look-ahead: weights at t earn t+1; CFTC used after its Friday release", {"bullet": True}),
        ("No survivorship bias: LUNA and FTT kept", {"bullet": True}),
        ("Robustness grids reported, never used for tuning", {"bullet": True}),
    ], size=16, space_after=12)
    text(s, 0.6, 4.75, 6.6, 1.9, [
        ("Data fix: before Aug 2000 CFTC lists the same currency futures under "
         "'International Monetary Market'. Matching both names extended positioning back to 1986.",
         {"size": 13, "color": SLATE}),
    ])
    script.append(("Data and methodology", *notes(s, "0:50", [
        "All data are public: FRED for FX and rates, CFTC for positions, Binance for crypto.",
        "One data fix worth mentioning: before 2000 the CFTC lists currency futures under a different exchange name; matching both names gave us positioning back to 1986.",
        "Every parameter was fixed in advance, and we hold out an out-of-sample period: 2011 on for FX, 2024 on for crypto.",
        "Returns are net of costs, there is no look-ahead, and we keep the coins that died, LUNA and FTT.",
    ])))

    # 4 strategy A rule --------------------------------------------------------
    s = new()
    title(s, "Strategy A: crowding-filtered G10 carry", "JPY, EUR, GBP, CHF, CAD, AUD, NZD vs USD, monthly")
    numbered(s, 0.6, 2.05, 7.4, [
        ("Carry portfolio", "Each month-end: long the 2 highest-rate currencies, short the 2 lowest. "
                            "Equal weights, dollar-neutral."),
        ("Crowding signal", "CFTC net speculative position / open interest, as a 36-month z-score."),
        ("Portfolio crowding", "Average z of the long leg minus average z of the short leg."),
        ("Filter", "If crowding > 1, cut all positions to half for the next month."),
    ], gap=1.2)
    stat(s, 8.6, 2.05, 4.1, f"{int(cv.loc['Crowded', 'Months'])}",
         f"crowded months out of {int(cv['Months'].sum())}, 1999–2026")
    stat(s, 8.6, 3.85, 4.1, "1 SD", "Threshold for 'crowded': one standard deviation above normal positioning")
    script.append(("Strategy A rule", *notes(s, "0:50", [
        "Each month we rank seven currencies by their interest rate against the dollar.",
        "We buy the two highest and sell the two lowest, so the portfolio has no net dollar bet.",
        "For crowding we take speculators' net futures position and z-score it over 36 months.",
        "Crowding is high when speculators are unusually long what we hold and short what we sell.",
        f"Above one, we halve the position. This happened in {int(cv.loc['Crowded', 'Months'])} months.",
    ])))

    # 5 A results + validation ---------------------------------------------------
    s = new()
    title(s, "Crowding filter helps out of sample, not in 2008")
    picture(s, ch["a_cum"], 0.5, 1.45, w=7.9)
    stat(s, 8.75, 1.4, 4.0, f"{A('Carry (net)', 'Out-of-sample'):.2f} → {A('Crowd-filtered (net)', 'Out-of-sample'):.2f}",
         "Out-of-sample Sharpe, net: carry vs crowd-filtered (2011–2026)", h=1.45)
    stat(s, 8.75, 3.0, 4.0, f"{cv.loc['Not crowded', 'Next-month carry mean (%)']:.2f}% vs "
                            f"{cv.loc['Crowded', 'Next-month carry mean (%)']:.2f}%",
         "Next-month carry after non-crowded vs crowded months", h=1.45)
    stat(s, 8.75, 4.6, 4.0, f"{lrv['Correlation'].iloc[0]:.2f}",
         "Correlation with the academic LRV carry factor (1999–2021)", h=1.45)
    text(s, 0.6, 5.95, 7.8, 0.9,
         f"Full sample, net: Sharpe {A('Carry (net)', 'Full'):.2f} carry, {A('Crowd-filtered (net)', 'Full'):.2f} filtered; "
         f"max drawdown {A('Carry (net)', 'Full', 'Max drawdown (%)'):.0f}% either way.", size=14, color=SLATE)
    script.append(("Strategy A results", *notes(s, "1:20", [
        f"Plain carry earns about {A('Carry (net)', 'Full', 'Ann. mean (%)'):.1f}% a year after costs, a net Sharpe of {A('Carry (net)', 'Full'):.2f}.",
        f"Our carry has a {lrv['Correlation'].iloc[0]:.2f} correlation with the published Lustig–Roussanov–Verdelhan factor, which validates the code and data.",
        f"After crowded months, next-month carry averages only {cv.loc['Crowded', 'Next-month carry mean (%)']:.2f}% versus {cv.loc['Not crowded', 'Next-month carry mean (%)']:.2f}% otherwise, with more negative skew.",
        f"Out of sample the filter lifts the Sharpe from {A('Carry (net)', 'Out-of-sample'):.2f} to {A('Crowd-filtered (net)', 'Out-of-sample'):.2f}, and every variant in our robustness grid also beats {A('Carry (net)', 'Out-of-sample'):.2f}.",
        f"But it did not avoid 2008: the crash started from a non-crowded reading, so the max drawdown is {A('Carry (net)', 'Full', 'Max drawdown (%)'):.0f}% either way.",
        f"Caveat: only {int(cv.loc['Crowded', 'Months'])} crowded months, so the effect is not precisely estimated.",
    ])))

    # 6 A risk --------------------------------------------------------------------
    s = new()
    title(s, "Strategy A loses when volatility spikes", "Monthly net carry on risk factors, Newey-West t-stats, 1999–2021")
    stat(s, 0.6, 1.95, 3.0, f"{reg.loc[(m, 'dVol (LRV)'), 'coef']:.2f}",
         f"Beta to equity-volatility changes (t = {reg.loc[(m, 'dVol (LRV)'), 'NW t-stat']:.1f})", color=RED)
    stat(s, 3.85, 1.95, 3.0, f"{reg.loc[(m, 'RX (dollar)'), 'coef']:.2f}",
         f"Beta to the dollar factor (t = {reg.loc[(m, 'RX (dollar)'), 'NW t-stat']:.1f})")
    stat(s, 0.6, 3.75, 3.0, f"{100 * reg.loc[(m, 'const'), 'coef']:.2f}%",
         f"Monthly alpha (t = {reg.loc[(m, 'const'), 'NW t-stat']:.1f}): not significant")
    stat(s, 3.85, 3.75, 3.0, f"{reg.loc[(m, 'R2'), 'coef']:.2f}", "R² of the two-factor model")
    text(s, 0.6, 5.65, 6.3, 1.2, "Worst months: Oct 2008, Aug 2007, May 2000, Jan 2009, and the Jan 2015 Swiss franc de-peg.",
         size=14, color=SLATE)
    text(s, 7.4, 1.95, 5.3, 0.4, f"The 2008 carry crash: {crash08:.1f}% (Jul 2008 – Mar 2009)",
         size=16, bold=True, color=NAVY)
    picture(s, ch["a_2008"], 7.3, 2.45, w=5.5)
    script.append(("Strategy A risk", *notes(s, "0:50", [
        f"When does it lose? We regress monthly carry on the dollar factor and on equity-volatility shocks.",
        f"The volatility beta is {reg.loc[(m, 'dVol (LRV)'), 'coef']:.2f} with a t-stat of {reg.loc[(m, 'dVol (LRV)'), 'NW t-stat']:.1f}: carry loses when volatility jumps.",
        f"Once we control for these factors the alpha is not significant, so carry is pay for risk, not a free lunch.",
        f"From July 2008 to March 2009 the strategy lost {abs(crash08):.1f}% as the funding currencies, yen and Swiss franc, rallied.",
    ])))

    # 7 strategy C rule + results -------------------------------------------------
    s = new()
    title(s, "Strategy C: crypto funding carry", "12 Binance perpetuals incl. LUNA and FTT, weekly, 2020–2026")
    picture(s, ch["c_cum"], 0.5, 1.75, w=7.6)
    text(s, 8.5, 1.8, 4.3, 2.3, [
        ("Funding is paid every 8 hours; positive funding means longs pay shorts.", {"bullet": True}),
        ("Each Sunday: short the third of coins with the highest 7-day funding, long the lowest third.", {"bullet": True}),
        ("Dollar-neutral, 5 bp costs.", {"bullet": True}),
    ], size=14, space_after=8)
    stat(s, 8.5, 4.15, 2.05, f"{C('Full'):.2f}", "Net Sharpe, full", h=1.3)
    stat(s, 10.7, 4.15, 2.05, f"{C('Out-of-sample'):.2f}", "Net Sharpe, 2024–26", h=1.3)
    stat(s, 8.5, 5.6, 4.25, f"{cw['Base'].iloc[0]:.0f}%", "Worst week: LUNA collapse, May 2022",
         color=RED, h=1.3)
    script.append(("Strategy C", *notes(s, "1:20", [
        "Crypto perpetual futures have their own interest rate, the funding rate, paid every 8 hours between longs and shorts.",
        "High funding means many leveraged longs, so it is both a carry signal and a crowding signal.",
        "Each Sunday we short the third of coins with the highest funding and buy the third with the lowest.",
        "We keep LUNA and FTT, which collapsed in 2022, to avoid survivorship bias.",
        f"Net Sharpe is {C('Full'):.2f} over the full sample: {C('In-sample'):.2f} in 2020 to 2023 and {C('Out-of-sample'):.2f} since 2024.",
        f"The worst week was the LUNA collapse, {cw['Base'].iloc[0]:.1f}%: traders were shorting LUNA, its funding turned negative, so our rule held it long.",
    ])))

    # 8 C drivers + risk control --------------------------------------------------
    s = new()
    title(s, "Funding is earned, but price moves dominate", "Where the return comes from, and what drives the losses")
    picture(s, ch["c_decomp"], 0.5, 1.75, w=6.0)
    rows = [["% per year", "Funding", "Price", "Net"]]
    for p in ("Full", "In-sample", "Out-of-sample"):
        rows.append([p, f"{dec.loc[p, 'Funding carry (% p.a.)']:+.1f}",
                     f"{dec.loc[p, 'Price component (% p.a.)']:+.1f}", f"{dec.loc[p, 'Net total (% p.a.)']:+.1f}"])
    table(s, 6.9, 1.85, 5.9, rows, col_w=[2.3, 1.2, 1.2, 1.2], size=13)
    text(s, 6.9, 3.55, 5.9, 3.4, [
        (f"Beta to BTC ≈ {beta.loc[('Base', 'BTC return'), 'coef']:.2f} (t = {beta.loc[('Base', 'BTC return'), 'NW t-stat']:.2f}): market-neutral.",
         {"bullet": True}),
        (f"Losses are coin-specific: LUNA {contrib['LUNA']:.0f}, XRP {contrib['XRP']:.0f}, DOGE {contrib['DOGE']:.0f} % pts.",
         {"bullet": True}),
        (f"Pre-set risk control (1/6 cap, no longs below −50% funding): Sharpe {ctl.loc[('Base', 'Full'), 'Sharpe']:.2f} → "
         f"{ctl.loc[('Risk-controlled', 'Full'), 'Sharpe']:.2f}. It did not help.", {"bullet": True}),
        ("Lesson: deeply negative funding means crowded shorts, not distress.", {"bullet": True, "bold": True, "color": NAVY}),
    ], size=14, space_after=10)
    script.append(("Strategy C drivers", *notes(s, "1:10", [
        f"We split the return into funding and price. Funding adds about {dec.loc['Full', 'Funding carry (% p.a.)']:.1f}% a year, steadily.",
        f"But price moves dominate: in 2020 to 2023 the coins we shorted, like DOGE and XRP, kept rallying and wiped out the funding.",
        f"Since 2024 most of the gain came from price, so we read the strong out-of-sample number with caution.",
        f"The strategy has no market exposure; its losses come from single coins, LUNA alone {contrib['LUNA']:.0f} percentage points.",
        f"A risk control we fixed in advance made things worse, Sharpe {ctl.loc[('Risk-controlled', 'Full'), 'Sharpe']:.2f}: the cap halved exposure and the filter missed LUNA's timing.",
        "So crypto carry crashes in the mirror image of FX: it ends up long whatever traders short hardest.",
    ])))

    # 9 combined ------------------------------------------------------------------
    s = new()
    title(s, "Combining FX and crypto carry", "Each scaled to 10% vol with lagged volatility, 50/50, 2021–2026")
    picture(s, ch["comb"], 0.5, 1.85, w=7.8)
    stat(s, 8.75, 1.95, 4.0, f"{corr:.2f}", "Correlation between A and C")
    table(s, 8.75, 3.75, 4.0, [
        ["", "Sharpe", "Vol (%)", "MaxDD (%)"],
        *[[k.split(" (")[0], f"{comb.loc[k, 'Sharpe']:.2f}", f"{comb.loc[k, 'Ann. vol (%)']:.1f}",
           f"{comb.loc[k, 'Max drawdown (%)']:.0f}"] for k in comb.index],
    ], col_w=[1.3, 0.8, 0.8, 1.1], size=12)
    cb = "Combined 50/50"
    script.append(("Combined portfolio", *notes(s, "0:50", [
        f"Finally, we scale both strategies to 10% volatility and combine them 50/50.",
        f"Their correlation is only {corr:.2f}: FX and crypto carry crash at different times.",
        f"The mix has {comb.loc[cb, 'Ann. vol (%)']:.1f}% volatility and a Sharpe of {comb.loc[cb, 'Sharpe']:.2f}, with a smaller worst month than either part.",
        "It does not beat FX alone on Sharpe because crypto carry was weak in this window, but the diversification is clear.",
    ])))

    # 10 conclusions --------------------------------------------------------------
    s = new(dark=True)
    title(s, "Conclusions and limitations", dark=True)
    text(s, 0.6, 1.7, 5.9, 0.5, "What we found", size=20, bold=True, color=AMBER)
    text(s, 0.6, 2.3, 5.9, 4.5, [
        (f"FX carry reproduces the academic factor (corr {lrv['Correlation'].iloc[0]:.2f}) and is exposed to volatility shocks.", {"bullet": True}),
        ("Crowding predicts weaker carry and modestly improves the out-of-sample Sharpe.", {"bullet": True}),
        ("Crypto funding carry is market-neutral, but its crashes are coin-specific: it ends up long what traders short hardest.", {"bullet": True}),
        (f"FX and crypto carry are nearly uncorrelated ({corr:.2f}).", {"bullet": True}),
    ], size=15, color=WHITE, space_after=12)
    text(s, 7.0, 1.7, 5.7, 0.5, "Limitations", size=20, bold=True, color=AMBER)
    text(s, 7.0, 2.3, 5.7, 4.5, [
        ("Short crypto history (2020–2026) and only 12 coins.", {"bullet": True}),
        (f"Few crowded FX months ({int(cv.loc['Crowded', 'Months'])}); the 2008 crash was not flagged.", {"bullet": True}),
        ("Crypto results depend on lookback and rebalancing frequency.", {"bullet": True}),
        ("Costs are simple estimates; no funding-rate caps, borrow limits or exchange risk.", {"bullet": True}),
    ], size=15, color=WHITE, space_after=12)
    script.append(("Conclusions", *notes(s, "1:00", [
        "To conclude: in both markets carry looks like compensation for crash risk.",
        "In FX, crowding measured from CFTC positions is a cheap and modestly useful warning sign.",
        "In crypto, sorting on funding alone exposes you to single-coin collapses like LUNA and FTX.",
        "Because the two crash at different times, they diversify each other.",
        "Main limitations: a short crypto sample, few crowded FX months, and simple cost estimates.",
        "Thank you, we are happy to take questions.",
    ])))

    path = SLIDES / "presentation_10min.pptx"
    prs.save(path)

    md = ["# Speaker notes: 10-minute presentation", "",
          "Read alongside `slides/presentation_10min.pptx`. The same notes are in each slide's notes pane.", ""]
    for i, (name, minutes, bullets) in enumerate(script, 1):
        md += [f"## Slide {i}. {name} (about {minutes})", ""] + [f"- {b}" for b in bullets] + [""]
    (SLIDES / "speaker_notes_10min.md").write_text("\n".join(md))
    total = sum(int(t.split(":")[0]) * 60 + int(t.split(":")[1]) for _, t, _ in script)
    print(f"Wrote {path} ({len(prs.slides)} slides, about {total // 60}:{total % 60:02d} of speaking time)")


if __name__ == "__main__":
    build()


# ===== Questions this script answers and results =====
# What this builds: slides/presentation_10min.pptx, a 10-slide version of the deck for a
# 10-minute talk: title, idea and hypotheses, data and methodology, Strategy A rule,
# results (with the LRV check) and risk, Strategy C rule and results, its drivers and
# risk control, combined portfolio, conclusions. Every slide has bullet speaker notes with
# a time cue (about 9:30 in total); slides/speaker_notes_10min.md has the same notes.
