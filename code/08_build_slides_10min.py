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

import matplotlib.pyplot as plt
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


def notes(slide, minutes, bullets, extra=()):
    """Speaker notes: a time cue, one bullet per line, then optional background to use if asked."""
    lines = [f"[about {minutes}]"] + [f"• {b}" for b in list(bullets) + list(extra)] if bullets else []
    slide.notes_slide.notes_text_frame.text = "\n".join(lines)
    return minutes, bullets, list(extra)


CURRENCIES = ("Japanese yen (JPY), euro (EUR), British pound (GBP), Swiss franc (CHF), Canadian dollar (CAD), "
              "Australian dollar (AUD) and New Zealand dollar (NZD), each against the US dollar.")
COIN_NAMES = ("Bitcoin (BTC), Ethereum (ETH), BNB, XRP, Cardano (ADA), Dogecoin (DOGE), Solana (SOL), Litecoin (LTC), "
              "Chainlink (LINK), Avalanche (AVAX), Terra (LUNA) and FTX Token (FTT).")


def takeaways(slide, x, y, w, h, items, size=14):
    """A tinted box headed 'Takeaways' with one full-sentence bullet per item."""
    box(slide, x, y, w, h)
    text(slide, x + 0.25, y + 0.18, w - 0.5, 0.4, "Takeaways", size=16, bold=True, color=NAVY)
    text(slide, x + 0.25, y + 0.65, w - 0.5, h - 0.8, [(t, {"bullet": True}) for t in items], size=size, space_after=8)


def perf_box(slide, x, y, w, h, heading, cells):
    """A tinted box with a heading and one column per metric: big value over a small label."""
    box(slide, x, y, w, h)
    text(slide, x + 0.25, y + 0.1, w - 0.5, 0.35, heading, size=13, bold=True, color=NAVY)
    cw = (w - 0.5) / len(cells)
    for i, (label, value, color) in enumerate(cells):
        text(slide, x + 0.25 + i * cw, y + 0.42, cw - 0.1, 0.45, value, size=20, font=HEAD, bold=True, color=color)
        text(slide, x + 0.25 + i * cw, y + 0.88, cw - 0.1, 0.3, label, size=11, color=SLATE)


def share(path, start=None):
    """Share of trading periods each asset was held long and short."""
    w = pd.read_csv(path, index_col=0, parse_dates=True).loc[start:]
    w = w[(w != 0).any(axis=1)]
    return (100 * (w > 0).mean()).round().astype(int), (100 * (w < 0).mean()).round().astype(int)


def cum_chart():
    """Slide 7 chart: growth of $1 in Strategy C, as in the 16-slide deck, plus a band for
    the Dogecoin and XRP rally while we were short them (April to May 2021)."""
    cd = pd.read_csv(OUT_C / "daily_returns.csv", index_col=0, parse_dates=True)
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    s = deck.cum(cd["Crypto carry (net)"])
    ax.axvspan(pd.Timestamp("2021-04-01"), pd.Timestamp("2021-05-31"), color="#" + deck.RED, alpha=0.10, lw=0)
    ax.text(pd.Timestamp("2021-04-01"), s.max() * 1.05, " Dogecoin, XRP\n rally (short)", color="#" + deck.RED,
            fontsize=9, va="bottom")
    ax.plot(s, color="#" + NAVY, lw=1.5)
    ax.set_yscale("log")
    for d, lab in (("2020-03-12", "Covid"), ("2022-05-09", "LUNA\n(Terra)"), ("2022-11-08", "FTX")):
        ax.axvline(pd.Timestamp(d), color="#" + deck.RED, lw=1, ls=":")
        ax.text(pd.Timestamp(d), s.max() * 1.05, " " + lab, color="#" + deck.RED, fontsize=10, va="bottom")
    ax.axvline(pd.Timestamp("2024-01-01"), color="#" + SLATE, ls=":", lw=1)
    ax.text(pd.Timestamp("2024-02-01"), s.min(), "out-of-sample", color="#" + SLATE, fontsize=9, va="bottom")
    ax.set_ylabel("Growth of $1 (net, log)", color="#" + SLATE)
    ax.yaxis.set_major_formatter(deck.matplotlib.ticker.FormatStrFormatter("%.1f"))
    ax.yaxis.set_minor_formatter(deck.matplotlib.ticker.FormatStrFormatter("%.1f"))
    deck.style(ax)
    return deck.save(fig, "c_cum_marked")


def decomp_chart():
    """Slide 8 chart: cumulative funding and price components of Strategy C, with the two
    episodes the notes discuss marked: the Dogecoin and XRP rally while we were short them
    (April to May 2021) and the FTX crash, when the long FTT position collected extreme
    negative funding (10-14 Nov 2022)."""
    cd = pd.read_csv(OUT_C / "daily_returns.csv", index_col=0, parse_dates=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.axvspan(pd.Timestamp("2021-04-01"), pd.Timestamp("2021-05-31"), color="#" + deck.RED, alpha=0.10, lw=0)
    ax.axvline(pd.Timestamp("2022-11-10"), color="#" + deck.GREEN, lw=1, ls=":")
    ax.plot(100 * cd["funding component"].cumsum(), color="#" + deck.GREEN, lw=1.8, label="Funding received")
    ax.plot(100 * cd["price component"].cumsum(), color="#" + deck.RED, lw=1.8, label="Price moves")
    ax.axhline(0, color="#B8BEC9", lw=0.8)
    ax.text(pd.Timestamp("2021-06-10"), 70, "Dogecoin, XRP\nrally while\nwe were short",
            color="#" + deck.RED, fontsize=8.5, va="top")
    ax.text(pd.Timestamp("2022-11-25"), 70, "FTX crash: our long\nFTX Token collects\nextreme funding",
            color="#" + deck.GREEN, fontsize=8.5, va="top")
    ax.set_ylim(top=75)
    ax.set_ylabel("Cumulative (% pts)", color="#" + SLATE)
    ax.legend(frameon=False, fontsize=10, loc="lower left")
    deck.style(ax)
    return deck.save(fig, "c_decomp_marked")


def build():
    # charts go to a temporary folder so the images of the 16-slide deck stay unchanged
    deck.IMG = Path(tempfile.mkdtemp())
    ch = deck.make_charts()
    ch["c_decomp"] = decomp_chart()
    ch["c_cum"] = cum_chart()

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
    grid_c = pd.read_csv(OUT_C / "robustness_grid.csv")
    a_long, a_short = share(OUT_A / "weights_carry.csv", a_net.index[0])

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
        "Our project asks one question: do carry trades crash when they are crowded?",
        "We test it in two markets with the same economics: G10 currencies and crypto.",
        "Strategy A is carry in seven G10 currencies against the US dollar, with a crowding filter built from CFTC data.",
        "Strategy C is funding carry in twelve crypto perpetual futures on Binance, including the coins that collapsed, Terra and FTX Token.",
    ])))

    # 2 idea + hypotheses -----------------------------------------------------
    s = new()
    title(s, "Carry pays because it crashes", "Our question: do carry trades crash when they are crowded?")
    text(s, 0.6, 1.85, 5.6, 5.4, [
        ("We test it in two markets with the same economics: G10 currencies and crypto.", {"bullet": True}),
        ("Strategy A is carry in seven G10 currencies against the US dollar, with a crowding filter "
         "built from CFTC data.", {"bullet": True}),
        ("Strategy C is funding carry in twelve crypto perpetual futures on Binance, including the coins "
         "that collapsed, Terra and FTX Token.", {"bullet": True}),
        ("Why carry crashes", {"bold": True, "color": NAVY}),
        ("Carry borrows the low-yield asset and holds the high-yield one. UIP says this earns nothing, "
         "but in the data it earns a premium, with rare large crashes.", {"bullet": True}),
        ("Crashes are worst when the trade is crowded and everyone unwinds at once "
         "(Brunnermeier, Nagel & Pedersen 2008).", {"bullet": True}),
        ("Hypotheses, fixed before testing", {"bold": True, "color": NAVY}),
        ("A: carry earns a premium, crowded months are followed by weaker carry, and it loses in volatility spikes.",
         {"bullet": True}),
        ("C: funding carry earns a premium with little BTC exposure, and its crashes are coin-specific.",
         {"bullet": True}),
    ], size=14, space_after=7)
    for i, (k, v1, v2) in enumerate([
            ("", "A: G10 FX", "C: Crypto"),
            ("Carry signal", "3-month rate differential", "Perpetual funding rate"),
            ("Crowding data", "CFTC speculator positions", "Funding = leveraged demand"),
            ("Universe", "7 currencies vs USD", "12 coins (listed below)"),
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
    text(s, 6.5, 5.75, 6.3, 1.5, [
        ("Currencies: " + CURRENCIES, {"size": 11}),
        ("Coins: " + COIN_NAMES, {"size": 11}),
    ], color=SLATE, space_after=6)
    script.append(("Carry pays because it crashes", *notes(s, "1:00", [
        "Carry means borrowing in a low-yield asset and holding a high-yield one.",
        "Uncovered interest parity says this should earn nothing, but in the data it earns a premium.",
        "The catch is crash risk: carry goes up the stairs and down the elevator.",
        "Brunnermeier, Nagel and Pedersen show crashes are worst when speculators are crowded into the trade.",
        "In FX the yield is the interest-rate differential, and we measure crowding with CFTC speculator positions.",
        "Our FX universe is the yen, euro, British pound, Swiss franc, Canadian dollar, Australian dollar and New Zealand dollar, all against the US dollar.",
        "In crypto the yield is the perpetual funding rate, which also measures leveraged demand.",
        "Our coins are Bitcoin, Ethereum, BNB, XRP, Cardano, Dogecoin, Solana, Litecoin, Chainlink, Avalanche, Terra and FTX Token.",
        "We wrote the hypotheses and all parameters down before running any backtest.",
    ], [
        "Uncovered interest parity (UIP) says a high-rate currency should fall by exactly the rate gap, so carry would earn zero; in practice high-rate currencies tend not to fall that much, which is the forward premium puzzle.",
        "'Up the stairs and down the elevator' means carry earns small steady gains most of the time and then loses a lot in a few weeks, so its returns have negative skew.",
        "Crowding matters because when many speculators hold the same trade, a shock forces them all to unwind together, which makes the crash larger.",
        "Hypothesis A says three things: carry earns a premium, crowded months are followed by weaker carry, and carry loses when volatility spikes.",
        "Hypothesis C says crypto funding carry earns a premium with little exposure to Bitcoin, and that its crashes come from single coins.",
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
        ("All parameters were fixed before the first backtest.", {"bullet": True}),
        ("The out-of-sample period starts in 2011 for A and in 2024 for C.", {"bullet": True}),
        ("Costs are 3 bp per unit traded in FX and 5 bp in crypto.", {"bullet": True}),
        ("There is no look-ahead: weights set at t earn the return of t+1, and CFTC data are used only after their Friday release.", {"bullet": True}),
        ("There is no survivorship bias, because Terra (LUNA) and FTX Token (FTT) stay in the sample.", {"bullet": True}),
        ("Robustness grids are reported, but they were never used for tuning.", {"bullet": True}),
    ], size=15, space_after=10)
    text(s, 0.6, 4.75, 6.6, 1.9, [
        ("Data fix: before Aug 2000 CFTC lists the same currency futures under "
         "'International Monetary Market'. Matching both names extended positioning back to 1986.",
         {"size": 13, "color": SLATE}),
    ])
    script.append(("Data and methodology", *notes(s, "0:50", [
        "All data are public: FRED for FX and rates, CFTC for positions, Binance for crypto.",
        "One data fix worth mentioning: before 2000 the CFTC lists currency futures under a different exchange name; matching both names gave us positioning back to 1986.",
        "Every parameter was fixed in advance, and our out-of-sample period starts in 2011 for FX and in 2024 for crypto.",
        "Returns are net of costs, there is no look-ahead, and we keep the two coins that died, Terra (LUNA) and FTX Token (FTT).",
    ], [
        "Out-of-sample means the later years that we did not look at while designing the strategy; if a rule still works there, it is less likely to be a result of data mining.",
        "Look-ahead bias means using information that was not public at the time of the trade; we avoid it because weights set at t earn the return of t+1, and CFTC positions measured on Tuesday are used only after their Friday release.",
        "Survivorship bias means testing only on assets that still exist today; we avoid it by keeping Terra and FTX Token, which together cost the crypto strategy about 100 percentage points of P&L.",
        "A basis point (bp) is 0.01%, so a cost of 3 bp means we lose 0.03% of every dollar we trade.",
        "The Lustig–Roussanov–Verdelhan (LRV) factor is the published academic carry factor, built by buying high-rate and selling low-rate currency portfolios; we use it only to check our own carry series.",
    ])))

    # 4 strategy A rule --------------------------------------------------------
    s = new()
    title(s, "Strategy A: crowding-filtered G10 carry",
          "Yen, euro, pound, Swiss franc, Canadian, Australian and New Zealand dollar vs USD, monthly")
    numbered(s, 0.6, 2.05, 7.4, [
        ("Carry portfolio", "At each month-end we buy the 2 highest-rate currencies and sell the 2 lowest, "
                            "with equal weights and no net dollar bet."),
        ("Crowding signal", "Each currency's CFTC net speculative position over open interest is z-scored over 36 months."),
        ("Portfolio crowding", "It is the average z of the long leg minus the average z of the short leg."),
        ("Filter", "If crowding is above 1, all positions are cut to half for the next month."),
    ], gap=1.2)
    stat(s, 8.6, 2.05, 4.1, f"{int(cv.loc['Crowded', 'Months'])}",
         f"crowded months out of {int(cv['Months'].sum())}, 1999–2026")
    box(s, 8.6, 3.85, 4.1, 2.2)
    text(s, 8.85, 4.03, 3.6, 2.5, [
        ("Who we usually hold", {"size": 16, "bold": True, "color": NAVY}),
        (f"Long: New Zealand dollar ({a_long['NZD']}% of months) and Australian dollar ({a_long['AUD']}%).", {"bullet": True}),
        (f"Short: Swiss franc ({a_short['CHF']}%), Japanese yen ({a_short['JPY']}%) and euro ({a_short['EUR']}%).", {"bullet": True}),
    ], size=13, space_after=8)
    script.append(("Strategy A rule", *notes(s, "1:00", [
        "Each month we rank the seven currencies by their three-month interest rate.",
        "We buy the two highest and sell the two lowest, so the portfolio has no net dollar bet.",
        f"In practice we are almost always long the New Zealand and Australian dollars and short the Swiss franc, often with the yen or the euro.",
        "For crowding we take speculators' net futures position and z-score it over 36 months.",
        "Crowding is high when speculators are unusually long what we hold and short what we sell.",
        f"When this score is above one standard deviation, we halve the position, which happened in {int(cv.loc['Crowded', 'Months'])} months.",
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
    ab = lambda c, f: f"{A('Carry (net)', 'Full', c):{f}}% / {A('Crowd-filtered (net)', 'Full', c):{f}}%"
    perf_box(s, 0.6, 5.85, 7.8, 1.3, "Full sample 1999–2026, net of costs: carry / crowd-filtered", [
        ("Net return a year", ab("Ann. mean (%)", ".1f"), NAVY),
        ("Volatility a year", ab("Ann. vol (%)", ".1f"), NAVY),
        ("Max drawdown", ab("Max drawdown (%)", ".0f"), RED),
    ])
    script.append(("Strategy A results", *notes(s, "1:20", [
        f"Plain carry earns about {A('Carry (net)', 'Full', 'Ann. mean (%)'):.1f}% a year after costs with {A('Carry (net)', 'Full', 'Ann. vol (%)'):.1f}% volatility, a net Sharpe of {A('Carry (net)', 'Full'):.2f}.",
        f"Our carry has a {lrv['Correlation'].iloc[0]:.2f} correlation with the published Lustig–Roussanov–Verdelhan factor, which validates the code and data.",
        f"After crowded months, next-month carry averages only {cv.loc['Crowded', 'Next-month carry mean (%)']:.2f}% versus {cv.loc['Not crowded', 'Next-month carry mean (%)']:.2f}% otherwise, with more negative skew.",
        f"Out of sample the filter lifts the Sharpe from {A('Carry (net)', 'Out-of-sample'):.2f} to {A('Crowd-filtered (net)', 'Out-of-sample'):.2f}, and every variant in our robustness grid also beats {A('Carry (net)', 'Out-of-sample'):.2f}.",
        f"But it did not avoid 2008: the crash started from a non-crowded reading, so the max drawdown is {A('Carry (net)', 'Full', 'Max drawdown (%)'):.0f}% either way.",
        f"One caveat is that there are only {int(cv.loc['Crowded', 'Months'])} crowded months, so the effect is not precisely estimated.",
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
        "To see when it loses, we regress monthly carry on the dollar factor and on equity-volatility shocks.",
        f"The volatility beta is {reg.loc[(m, 'dVol (LRV)'), 'coef']:.2f} with a t-stat of {reg.loc[(m, 'dVol (LRV)'), 'NW t-stat']:.1f}: carry loses when volatility jumps.",
        f"Once we control for these factors the alpha is not significant, so carry is pay for risk, not a free lunch.",
        f"From July 2008 to March 2009 the strategy lost {abs(crash08):.1f}% as the funding currencies, the Japanese yen and the Swiss franc, rallied against the Australian and New Zealand dollars.",
    ])))

    # 7 strategy C rule + results -------------------------------------------------
    s = new()
    title(s, "Strategy C: crypto funding carry",
          "Binance perpetuals on BTC, ETH, BNB, XRP, ADA, DOGE, SOL, LTC, LINK, AVAX, LUNA (Terra), FTT; weekly, 2020–2026")
    picture(s, ch["c_cum"], 0.5, 1.75, w=7.6)
    text(s, 8.5, 1.8, 4.3, 2.3, [
        ("Funding is paid every 8 hours, and positive funding means longs pay shorts.", {"bullet": True}),
        ("Each Sunday we short the third of coins with the highest 7-day funding and buy the lowest third.", {"bullet": True}),
        ("The book is dollar-neutral and pays 5 bp per trade.", {"bullet": True}),
    ], size=14, space_after=8)
    stat(s, 8.5, 4.15, 2.05, f"{C('Full'):.2f}", "Net Sharpe, full", h=1.3)
    stat(s, 10.7, 4.15, 2.05, f"{C('Out-of-sample'):.2f}", "Net Sharpe, 2024–26", h=1.3)
    stat(s, 8.5, 5.6, 4.25, f"{cw['Base'].iloc[0]:.0f}%", "Worst week: LUNA (Terra) collapse, May 2022",
         color=RED, h=1.3)
    cb_ = lambda c, f: f"{C('Full', c):{f}}% / {C('Out-of-sample', c):{f}}%"
    perf_box(s, 0.6, 5.95, 7.6, 1.3, "Net of costs: full sample 2020–2026 / since 2024", [
        ("Net return a year", cb_("Ann. mean (%)", ".1f"), NAVY),
        ("Volatility a year", cb_("Ann. vol (%)", ".0f"), NAVY),
        ("Max drawdown", cb_("Max drawdown (%)", ".0f"), RED),
    ])
    script.append(("Strategy C", *notes(s, "1:20", [
        "Crypto perpetual futures have their own interest rate, the funding rate, paid every 8 hours between longs and shorts.",
        "High funding means many leveraged longs, so it is both a carry signal and a crowding signal.",
        "Each Sunday we short the third of coins with the highest funding and buy the third with the lowest.",
        "The twelve coins are Bitcoin, Ethereum, BNB, XRP, Cardano, Dogecoin, Solana, Litecoin, Chainlink, Avalanche, Terra and FTX Token.",
        "We keep Terra (LUNA) and FTX Token (FTT), which both collapsed in 2022, to avoid survivorship bias.",
        f"Net Sharpe is {C('Full'):.2f} over the full sample: {C('In-sample'):.2f} in 2020 to 2023 and {C('Out-of-sample'):.2f} since 2024.",
        f"After costs it earns {C('Full', 'Ann. mean (%)'):.1f}% a year with {C('Full', 'Ann. vol (%)'):.0f}% volatility, and its maximum drawdown is {C('Full', 'Max drawdown (%)'):.0f}%, much deeper than FX carry.",
        f"The worst week was the Terra (LUNA) collapse in May 2022, {cw['Base'].iloc[0]:.1f}%: traders were shorting Terra, its funding turned negative, and so our rule held it long.",
    ], [
        "A perpetual future has no expiry date, so the exchange uses the funding payment to keep its price close to the spot price.",
        "For example, if funding is +0.01% every 8 hours, longs pay shorts about 0.03% a day, which is roughly 11% a year.",
        "So shorting a coin with high funding earns that payment, just as selling a low-rate currency and buying a high-rate one earns the interest gap in FX.",
        "The book is dollar-neutral, which means the long and short sides have the same size, so a move of the whole crypto market should roughly cancel out.",
        "The out-of-sample Sharpe since 2024 is strong, but it comes from less than three years of data, so we treat it with caution.",
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
    text(s, 0.6, 5.75, 5.9, 1.3,
         f"Total P&L by coin, % pts: Solana +{contrib['SOL']:.0f}, BNB +{contrib['BNB']:.0f}, Avalanche +{contrib['AVAX']:.0f}; "
         f"Terra {contrib['LUNA']:.0f}, XRP {contrib['XRP']:.0f}, Dogecoin {contrib['DOGE']:.0f}, FTX Token {contrib['FTT']:.0f}.",
         size=12, color=SLATE)
    text(s, 0.6, 6.45, 5.9, 0.8,
         f"Robustness: all {len(grid_c)} lookback and rebalancing settings have a positive out-of-sample Sharpe "
         f"({grid_c['Sharpe OOS net'].min():.2f} to {grid_c['Sharpe OOS net'].max():.2f}); our pre-set choice is in the bottom half.",
         size=12, bold=True, color=NAVY)
    takeaways(s, 6.9, 3.5, 5.9, 3.65, [
        f"Funding income is steady at about {dec.loc['Full', 'Funding carry (% p.a.)']:.1f}% a year, but price moves decide the result.",
        f"The strategy has no market exposure, since its beta to Bitcoin is {beta.loc[('Base', 'BTC return'), 'coef']:.2f}.",
        f"Its losses come from single coins: Terra lost {abs(contrib['LUNA']):.0f} points, XRP {abs(contrib['XRP']):.0f} and Dogecoin {abs(contrib['DOGE']):.0f}.",
        f"Our pre-set risk control lowered the Sharpe from {ctl.loc[('Base', 'Full'), 'Sharpe']:.2f} to {ctl.loc[('Risk-controlled', 'Full'), 'Sharpe']:.2f}, so it did not help.",
        "Deeply negative funding signals crowded shorts, not a cheap coin.",
    ], size=13)
    script.append(("Strategy C drivers", *notes(s, "1:10", [
        f"We split the return into funding and price. Funding adds about {dec.loc['Full', 'Funding carry (% p.a.)']:.1f}% a year, steadily.",
        "But price moves dominate: in 2020 to 2023 the coins we shorted, like Dogecoin and XRP, kept rallying and wiped out the funding.",
        "Since 2024 most of the gain came from price, so we read the strong out-of-sample number with caution.",
        f"The beta to Bitcoin is about zero, so the strategy has no market exposure.",
        f"Its losses come from single coins: Terra alone cost {abs(contrib['LUNA']):.0f} percentage points, XRP {abs(contrib['XRP']):.0f} and Dogecoin {abs(contrib['DOGE']):.0f}, while Solana and BNB were the biggest winners.",
        f"A risk control we fixed in advance made things worse and lowered the Sharpe to {ctl.loc[('Risk-controlled', 'Full'), 'Sharpe']:.2f}: the cap halved exposure and the filter missed the timing of Terra's collapse.",
        "Our takeaway is that crypto carry crashes in the mirror image of FX: it ends up long whatever traders short hardest.",
        f"As a robustness check we tried {len(grid_c)} lookback and rebalancing settings; all have a positive out-of-sample Sharpe, and the setting we fixed in advance is in the bottom half, so we did not pick the best one after the fact.",
    ], [
        f"The table adds up: over the full sample, funding of {dec.loc['Full', 'Funding carry (% p.a.)']:+.1f}%, price of {dec.loc['Full', 'Price component (% p.a.)']:+.1f}% and costs of {dec.loc['Full', 'Costs (% p.a.)']:+.1f}% give a net return of {dec.loc['Full', 'Net total (% p.a.)']:+.1f}% a year.",
        f"In 2020 to 2023 funding paid {dec.loc['In-sample', 'Funding carry (% p.a.)']:.1f}% a year, but price moves took away {abs(dec.loc['In-sample', 'Price component (% p.a.)']):.1f}%, so the strategy lost money.",
        f"Since 2024 funding paid only {dec.loc['Out-of-sample', 'Funding carry (% p.a.)']:.1f}%, and price moves added {dec.loc['Out-of-sample', 'Price component (% p.a.)']:.1f}%, which is luck rather than carry.",
        "The risk control capped each coin at one sixth of its side of the book and refused to buy coins with 7-day funding below minus 50% a year.",
        "It failed because the cap left part of the book in cash and halved the funding income, and on the Sunday before Terra collapsed its 7-day funding was only about minus 20% a year, so the filter did not remove it.",
    ])))

    # 9 combined ------------------------------------------------------------------
    s = new()
    title(s, "Combining FX and crypto carry", "Each scaled to 10% vol with lagged volatility, 50/50, 2021–2026")
    picture(s, ch["comb"], 0.5, 1.75, w=6.6)
    table(s, 0.6, 5.4, 6.4, [
        ["", "Sharpe", "Vol (%)", "Max DD (%)", "Worst month (%)"],
        *[[k.split(" (")[0], f"{comb.loc[k, 'Sharpe']:.2f}", f"{comb.loc[k, 'Ann. vol (%)']:.1f}",
           f"{comb.loc[k, 'Max drawdown (%)']:.0f}", f"{comb.loc[k, 'Worst month (%)']:.1f}"] for k in comb.index],
    ], col_w=[1.6, 0.9, 0.9, 1.3, 1.7], size=12, row_h=0.34)
    cb = "Combined 50/50"
    stat(s, 7.5, 1.8, 5.25, f"{corr:.2f}", "Correlation between A and C, monthly, 2021–2026", h=1.4)
    takeaways(s, 7.5, 3.4, 5.25, 3.75, [
        "FX carry and crypto carry are almost uncorrelated, so they crash at different times.",
        f"The 50/50 mix has {comb.loc[cb, 'Ann. vol (%)']:.1f}% volatility, compared with about 9% for each strategy alone.",
        f"Its worst month is {comb.loc[cb, 'Worst month (%)']:.1f}%, smaller than for FX ({comb.loc['A (10% vol)', 'Worst month (%)']:.1f}%) or crypto ({comb.loc['C (10% vol)', 'Worst month (%)']:.1f}%).",
        f"The mix does not beat FX alone on Sharpe ({comb.loc[cb, 'Sharpe']:.2f} vs {comb.loc['A (10% vol)', 'Sharpe']:.2f}), because crypto carry was weak in this window.",
    ], size=13)
    script.append(("Combined portfolio", *notes(s, "0:50", [
        "Finally, we scale both strategies to 10% volatility and combine them 50/50.",
        f"Their correlation is only {corr:.2f}: FX and crypto carry crash at different times.",
        f"The mix has {comb.loc[cb, 'Ann. vol (%)']:.1f}% volatility and a Sharpe of {comb.loc[cb, 'Sharpe']:.2f}, and its worst month, {comb.loc[cb, 'Worst month (%)']:.1f}%, is smaller than either part's.",
        "It does not beat FX alone on Sharpe, because crypto carry was weak in this window.",
        "Our takeaway is that the benefit of combining them is lower risk, not a higher return.",
    ], [
        "We scale each strategy to 10% volatility so that neither one dominates the mix just because it is more volatile; crypto carry is about three times as volatile as FX carry before scaling.",
        "The scaling uses past volatility only, so there is no look-ahead in the combined portfolio.",
        "A correlation of 0.11 is close to zero, which means a bad month in one strategy says very little about the other.",
        "The window starts in 2021 because that is when both strategies have enough history for the volatility estimate.",
        "With only 67 months of overlap, these combined numbers are indicative rather than precise.",
    ])))

    # 10 conclusions --------------------------------------------------------------
    s = new(dark=True)
    title(s, "Conclusions and limitations", dark=True)
    text(s, 0.6, 1.45, 7.4, 0.5, "Hypotheses: verdict and evidence", size=18, bold=True, color=AMBER)
    verdicts = [
        ["Hypothesis", "Verdict", "Evidence"],
        ["A1: G10 carry earns a premium", "Supported",
         f"Net Sharpe {A('Carry (net)', 'Full'):.2f}; {lrv['Correlation'].iloc[0]:.2f} correlation with LRV"],
        ["A2: crowding predicts weaker carry", "Leaning yes",
         f"{cv.loc['Crowded', 'Next-month carry mean (%)']:.2f}% vs {cv.loc['Not crowded', 'Next-month carry mean (%)']:.2f}% next month; "
         f"OOS Sharpe {A('Carry (net)', 'Out-of-sample'):.2f} → {A('Crowd-filtered (net)', 'Out-of-sample'):.2f}; missed 2008"],
        ["A3: carry loses in volatility spikes", "Supported",
         f"Vol beta {reg.loc[(m, 'dVol (LRV)'), 'coef']:.2f} (t = {reg.loc[(m, 'dVol (LRV)'), 'NW t-stat']:.1f}); alpha not significant"],
        ["C1: funding carry earns a premium", "Mixed",
         f"Funding +{dec.loc['Full', 'Funding carry (% p.a.)']:.1f}% a year, but net Sharpe {C('Full'):.2f}; price moves dominate"],
        ["C2: no BTC exposure; coin-specific crashes", "Supported",
         f"BTC beta ≈ 0; Terra {contrib['LUNA']:.0f} pts; worst week {cw['Base'].iloc[0]:.0f}%"],
        ["Pre-set risk control helps", "Not supported",
         f"Sharpe {ctl.loc[('Base', 'Full'), 'Sharpe']:.2f} → {ctl.loc[('Risk-controlled', 'Full'), 'Sharpe']:.2f}"],
        ["FX and crypto carry diversify", "Supported",
         f"Correlation {corr:.2f}; vol {comb.loc['Combined 50/50', 'Ann. vol (%)']:.1f}% vs about 9%"],
    ]
    vt = table(s, 0.6, 2.0, 7.6, verdicts, col_w=[2.75, 1.25, 3.6], size=11, row_h=0.5, left=True)
    tone = {"Supported": "2E7D4F", "Leaning yes": "B7700C", "Mixed": "B7700C", "Not supported": RED}
    for r in range(1, len(verdicts)):
        run = vt.cell(r, 1).text_frame.paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = deck.rgb(tone[verdicts[r][1]])
    text(s, 8.6, 1.45, 4.2, 0.5, "What is new", size=18, bold=True, color=AMBER)
    text(s, 8.6, 1.95, 4.2, 2.2, [
        ("We use CFTC speculator positioning as a crowding filter on G10 carry.", {"bullet": True}),
        ("We treat crypto funding as the crypto interest-rate gap and as a crowding signal, and test it with the coins that died.", {"bullet": True}),
    ], size=13, color=WHITE, space_after=8)
    text(s, 8.6, 4.15, 4.2, 0.5, "Limitations", size=18, bold=True, color=AMBER)
    text(s, 8.6, 4.65, 4.2, 2.6, [
        ("The crypto history is short (2020–2026) and covers only 12 coins.", {"bullet": True}),
        (f"There are only {int(cv.loc['Crowded', 'Months'])} crowded FX months, and the 2008 crash was not flagged.", {"bullet": True}),
        ("Costs are simple estimates, and we ignore funding-rate caps, borrow limits and exchange risk.", {"bullet": True}),
    ], size=13, color=WHITE, space_after=8)
    script.append(("Conclusions", *notes(s, "1:00", [
        "The table sums up our hypotheses: four are supported, crowding in FX leans yes, crypto funding carry is mixed, and our pre-set risk control did not work.",
        "In both markets, carry looks like compensation for crash risk.",
        "In FX, crowding measured from CFTC positions is a cheap and modestly useful warning sign.",
        "In crypto, sorting on funding alone exposes you to single-coin collapses like Terra and FTX Token.",
        "Because the two crash at different times, they diversify each other.",
        "What is new in our work is using CFTC positioning as a crowding filter on carry, and treating crypto funding as both the crypto interest-rate gap and a crowding signal, tested with the coins that died.",
        "The main limitations are a short crypto sample, few crowded FX months, and simple cost estimates.",
    ])))

    path = SLIDES / "presentation_10min.pptx"
    prs.save(path)

    md = ["# Speaker notes: 10-minute presentation", "",
          "Read alongside `slides/presentation_10min.pptx`. The same notes are in each slide's notes pane.", ""]
    for i, (name, minutes, bullets, extra) in enumerate(script, 1):
        md += [f"## Slide {i}. {name} (about {minutes})", ""] + ([f"- {b}" for b in bullets + extra] or ["No speaking on this slide."]) + [""]
    (SLIDES / "speaker_notes_10min.md").write_text("\n".join(md))
    total = sum(int(t.split(":")[0]) * 60 + int(t.split(":")[1]) for _, t, _, _ in script)
    print(f"Wrote {path} ({len(prs.slides)} slides, about {total // 60}:{total % 60:02d} of speaking time)")


if __name__ == "__main__":
    build()


# ===== Questions this script answers and results =====
# What this builds: slides/presentation_10min.pptx, a 10-slide version of the deck for a
# 10-minute talk: title, idea and hypotheses, data and methodology, Strategy A rule,
# results (with the LRV check) and risk, Strategy C rule and results, its drivers and
# risk control, combined portfolio, conclusions. Every slide has bullet speaker notes with
# a time cue (about 9:30 in total); slides/speaker_notes_10min.md has the same notes.
