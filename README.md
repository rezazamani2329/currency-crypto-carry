# Crowded Carry: Crash Risk in FX and Crypto Carry Trades

MFE 230GB Currency Markets, Final Project
Authors: [Name 1], [Name 2]

## Economic idea
Carry trades earn a risk premium but are exposed to crashes when crowded
positions unwind. We test this mechanism in two markets:

| | Strategy A: G10 FX | Strategy C: Crypto |
|---|---|---|
| Universe | JPY, EUR, GBP, CHF, CAD, AUD, NZD vs USD | Large-cap USDT perpetual futures |
| Carry signal | 3-month interest rate differential | Perpetual futures funding rate |
| Alternative data | CFTC speculative positioning (crowding) | [to be filled in] |
| Frequency | Monthly | [to be filled in] |

## Key results
[Table and figure links to be added]

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
| FX spot rates | FRED (Fed H.10) | DEXJPUS, DEXUSEU, DEXUSUK, DEXSZUS, DEXCAUS, DEXUSAL, DEXUSNZ, DEXGEUS | YYYY-MM-DD |
| 3-month rates | OECD via FRED | IR3TIB01xxM156N | YYYY-MM-DD |
| Positioning | CFTC Commitments of Traders (legacy, futures only) | cftc.gov historical compressed files | YYYY-MM-DD |
| Crypto funding and prices | Binance public data archive | data.binance.vision (futures/um) | YYYY-MM-DD |

## Methodology notes
- Trading rules and parameters fixed before backtesting; out-of-sample period
  is 2011 onward for Strategy A.
- CFTC positions (as of Tuesday) are used only after their Friday release.
- Delisted coins kept in the crypto universe to limit survivorship bias.

## AI use
See `ai_log.md`, as required by the course.
