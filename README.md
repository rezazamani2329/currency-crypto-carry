# Crowded Carry: Crash Risk in FX and Crypto Carry Trades

MFE 230GB Currency Markets, Final Project
Authors: Reza Zamani and [partner]

## Economic idea
Carry trades earn a risk premium but are exposed to crashes when crowded
positions unwind. We test this mechanism in two markets:

| | Strategy A: G10 FX | Strategy C: Crypto |
|---|---|---|
| Universe | JPY, EUR, GBP, CHF, CAD, AUD, NZD vs USD | 12 Binance USDT perpetuals incl. delisted LUNA, FTT (USDC as sanity check only) |
| Carry signal | 3-month interest rate differential | Perpetual futures funding rate |
| Alternative data | CFTC speculative positioning (crowding) | Perpetual-futures funding rates (leveraged-demand / positioning data) |
| Frequency | Monthly | Daily P&L, weekly rebalancing |

## Key results
Net of transaction costs. Full tables in `output/`; interactive page in `web/index.html`.

| | Sample | Ann. mean | Ann. vol | Sharpe | Max DD |
|---|---|---|---|---|---|
| A: G10 carry | 1999-05 to 2026-08 | 3.3% | 8.9% | 0.37 | -37% |
| A: crowd-filtered | 1999-05 to 2026-08 | 3.2% | 8.5% | 0.38 | -37% |
| A: carry, out-of-sample | 2011-01 to 2026-08 | 2.0% | 7.5% | 0.27 | -15% |
| A: crowd-filtered, out-of-sample | 2011-01 to 2026-08 | 2.3% | 7.2% | 0.32 | -14% |
| C: crypto funding carry | 2020-02 to 2026-08 | 4.1% | 29.9% | 0.14 | -67% |
| C: out-of-sample | 2024-01 to 2026-08 | 13.9% | 17.2% | 0.81 | -13% |
| A + C, 50/50 at 10% vol each | 2021-02 to 2026-08 | 3.6% | 7.0% | 0.51 | -11% |

- Strategy A correlates 0.82 with the Lustig-Roussanov-Verdelhan developed carry
  factor (course file), and loses when equity volatility rises (NW t = -4.3).
- After crowded months, next-month carry averages 0.02% vs 0.30% otherwise.
- Strategy C has no BTC beta (t = -0.75); losses are concentrated in coins that
  collapsed (LUNA -87, XRP -58, DOGE -44 % pts). The pre-specified risk control
  (per-coin cap + negative-funding filter) did not improve the Sharpe ratio.
- Correlation between A and C: 0.11.

## Reproducing the results
```bash
pip install -r requirements.txt
python run_all.py                  # full pipeline incl. downloads
SKIP_DOWNLOAD=1 python run_all.py  # use the committed data snapshot
```

Notes on data access:
- **FRED files must be downloaded by hand.** FRED's website often drops
  scripted requests. Save each series from fred.stlouisfed.org (Download → CSV)
  as `data/raw/fred_<SERIES_ID>.csv` (e.g. `data/raw/fred_IR3TIB01USM156N.csv`);
  the download script reads these cached files first. Setting `FRED_API_KEY`
  (free key from fredaccount.stlouisfed.org) uses the official API instead.
- **`SKIP_DOWNLOAD=1`** skips all downloads and runs the analysis on the
  committed `data/clean/` snapshot, so results reproduce without network access.
- `code/05_risk_analysis.py` uses the course file `CurrencyPortfolios.xls`
  (Lustig-Roussanov-Verdelhan portfolios) placed in `data/raw/`; the sections
  that need it are skipped if it is absent. A hand-saved `data/raw/fred_VIXCLS.csv`
  is used if present.

## Repository structure
```
code/          numbered scripts, run in order (see run_all.py)
data/raw/      downloaded files (not committed; re-created by scripts)
data/clean/    processed data snapshot used for all results (committed)
output/        tables and figures
web/           interactive HTML page
slides/        presentation
ai_log.md      documentation of AI-assisted work
```

## Data sources
| Data | Source | Series / location | Downloaded |
|---|---|---|---|
| FX spot rates | FRED (Fed H.10) | DEXJPUS, DEXUSEU, DEXUSUK, DEXSZUS, DEXCAUS, DEXUSAL, DEXUSNZ (DEXGEUS optional) | 2026-10-02 |
| 3-month rates | OECD via FRED | IR3TIB01xxM156N (saved by hand) | 2026-10-02 |
| Positioning | CFTC Commitments of Traders (legacy, futures only) | cftc.gov historical compressed files, 1986-2026 | 2026-10-02 |
| Crypto funding and prices | Binance public data archive | data.binance.vision (futures/um), 2020-01 to 2026-08 | 2026-10-02 |

## Methodology notes
- Trading rules and parameters fixed before backtesting; out-of-sample period
  is 2011 onward for Strategy A.
- CFTC positions (as of Tuesday) are used only after their Friday release.
- Delisted coins kept in the crypto universe to limit survivorship bias.

## AI use
See `ai_log.md`, as required by the course.
