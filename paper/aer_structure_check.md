# Our paper compared with recent AER articles, and benchmarks for Tables 8 and 12

**Reference article:** Einav, Klopack and Mahoney (2025), "Selling Subscriptions," *American Economic Review* 115(5): 1650–1671. This is an empirical paper, read from the authors' posted published PDF (https://web.stanford.edu/~leinav/pubs/AER2025.pdf).

**Second check:** Fujiwara and Matsuyama (2024), *AER* 114(11). This is a theory paper. It was used only to confirm the title page, headings and references format.

## Where we already match

| Element | AER (Einav et al. 2025) | Our paper |
|---|---|---|
| Section numbers | I., II., III. | Same |
| Subsection numbers | A., B., C. | Same |
| Literature review | Inside the introduction, no separate section | Same |
| Author footnote | "Einav: Stanford University and NBER (email: ...)" | Same form |
| Table captions | "Table 1—Parameter Estimates by ..." | Same |
| Figure captions | "Figure 1. Aggregating Retention Rates" | Same |
| Robustness | A subsection of the results section ("E. Robustness and Heterogeneity") | Same ("VD. Robustness") |
| Conclusion | Last numbered section ("IV. Conclusions") | Same ("VII. Conclusion") |
| References | After the conclusion | Same |
| Appendix | Supplemental appendix after the references | Same |

## Where we differ

| # | Element | AER | Our paper | Suggested change |
|---|---|---|---|---|
| 1 | Introduction heading | None. The text starts right after the abstract and is not numbered. | "I. Introduction" | Remove the heading, so Hypotheses becomes I and Data becomes II |
| 2 | Abstract | Unlabeled paragraph | "Abstract" heading | Remove the heading |
| 3 | JEL codes | At the end of the abstract: "(JEL D12, D18, L81, L88)" | Separate "JEL classification:" line | Move into the abstract in AER form |
| 4 | Keywords | None printed (given only on the AEA website) | Five keywords | Remove from the PDF |
| 5 | Sub-subsection headings | Unnumbered, run-in: "Robustness.—" | Numbered, run-in: "1. Carry Earns a Premium ... (H-A1).—" | Drop the numbers |
| 6 | Table and figure notes | Start with "Notes:" | Start directly with "This table ..." | Add "Notes:" before each note |
| 7 | "Go to" line | Separate footnote (†) on the title | Inside the author footnote | Move to its own † footnote on the title |
| 8 | Date on title page | None (published version) | "October 2026" | Keep; working papers carry a date |

Points 1–7 change only formatting, not content. Point 8 is normal for a paper that is not yet published.

## Content differences that are acceptable

- **Hypotheses section:** AER papers rarely have a separate "Hypotheses" section. It is still acceptable, and it suits a pre-specified test design.
- **Literature table (Table 1) and the summary-of-evidence table (Table 15):** these are uncommon in AER but are not against its style.
- **Separate Discussion section:** Einav et al. go straight to the conclusions. Many AER empirical papers do include a discussion section.

**Status:** items 1–7 were applied on October 10, 2026. The sections are now: (unnumbered introduction), I Hypotheses, II Data, III Methodology, IV Results, V Discussion, VI Conclusion, and Appendix A.

## Section counts in five recent AER papers (checked October 10, 2026)

| Paper | Type | Sections after the unheaded introduction |
|---|---|---|
| Einav, Klopack and Mahoney (2025), "Selling Subscriptions," 115(5) | Empirical, short (22 pages) | 4: Data and Sample Construction; Descriptive Evidence; Quantifying the Impact on Revenues; Conclusions |
| Antolin-Diaz and Surico (2025), "The Long-Run Effects of Government Spending," 115(7) | Empirical | 6: Empirical Framework; Effects of Military Spending; Assessing Inference (robustness); Inspecting the Mechanism; What Drives the Long-Run Effects; Conclusion |
| Doraszelski, Seim, Sinkinson and Wang (2025), "Ownership Concentration and Strategic Supply Reduction," 115(3) | Empirical with a model | 8: Institutional Setting; Model; Data Sources; Descriptive Evidence; Reservation Values and Simulation; Main Results; Auction Design; Conclusion |
| Kekre and Lenel (2024), "The Flight to Safety and International Risk Sharing," 114(6) | Quantitative theory | 6 |
| Gaubert, Kline, Vergara and Yagan (2025), "Place-Based Redistribution," 115(10) | Theory with calibration | 8 or more |

Common features across all five:
- The introduction has no heading.
- Related literature sits inside the introduction, sometimes as a run-in "Related Literature" paragraph.
- A framework or model section, when there is one, comes before the data.
- Robustness is a subsection or a section near the end.

The number of sections ranges from 4 to 8, and ours has 6, which is typical.

## Benchmarks for Table 8 (low R²) and Table 12 (near-zero Bitcoin beta)

These numbers were read from the papers on October 10, 2026. They are cited in Sections IVA and IVB of the paper.

### Table 8: R² of carry regressions

| Paper | Regression | R² | Slope |
|---|---|---|---|
| Our paper, Table 8 | Monthly Strategy A on dollar factor and volatility innovations | 0.10–0.18 | Volatility −1.55 (t = −3.7); alpha t = 1.7 |
| Brunnermeier, Nagel and Pedersen (NBER WP 14473, Table 7) | Weekly carry (3 long / 3 short) on change in VIX | 0.05 | −0.94 (t ≈ −3.8) |
| Same paper, Table 7 | Weekly carry on change in TED spread | 0.01 | −1.21 (SE 0.84) |
| Lustig, Roussanov and Verdelhan (RFS 2011, Table 4) | Monthly carry portfolios on HML and RX | 0.75–0.94 | Fit driven by RX and HML themselves |
| Menkhoff, Sarno, Schmeling and Schrimpf (JF 2012, Table II) | Monthly carry portfolios on DOL and global FX volatility | 0.67–0.83 | Fit mainly from DOL |

R² is high only when the dollar factor or the carry factor is a regressor. Volatility alone explains little, as in our results. Our counterpart to the high-R² case is the 0.82 correlation with the LRV carry factor.

### Table 12: market beta of long-short strategies

| Paper | Strategy | Market beta | Interpretation |
|---|---|---|---|
| Our paper, Table 12 | Crypto funding carry on Bitcoin, daily | −0.018 (t = −0.78), 95% CI [−0.064, 0.028] | Precisely estimated zero |
| Liu, Tsyvinski and Wu (2019 working-paper version of JF 2022, Table 8) | Weekly crypto 3-week momentum long-short on crypto market | 0.101 (t = 0.78), R² = 0.002 | "not significantly exposed to the coin market returns" |
| Frazzini and Pedersen (JFE 2014, Table III) | Betting-against-beta factor, monthly | Realized beta −0.06 | Market neutral by construction |
| Christin et al. (2023); Borri et al. (2025) | Crypto carry | Not reported | Only means and Sharpe ratios |

Caveats:
- The Brunnermeier et al. t-statistics are coefficient divided by standard error.
- The Lustig et al. rows come from a partly garbled PDF extraction.
- The full text of Schmeling, Schrimpf and Todorov could not be read.

Sources:
- https://www.nber.org/papers/w14473.pdf
- https://www.johnhcochrane.com/s/Lustig_Roussanov_Verdelhan_common_risk_currency.pdf
- https://openaccess.city.ac.uk/id/eprint/3391/1/CTVOL_R3_v4_paper.pdf
- https://cowles.yale.edu/sites/default/files/2022-10/LiuTsyvinskiWu2019%20COMMON%20RISK%20FACTORS.pdf
- https://www.johnhcochrane.com/s/BettingAgainstBeta.pdf
