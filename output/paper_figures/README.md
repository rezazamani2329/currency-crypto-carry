# Paper figures

Every figure in `paper/crowded_carry_paper.pdf`, numbered as in the paper. Rebuild with `python paper/make_paper_figures.py . paper/figures` (charts made from the CSV outputs) after running `run_all.py`. In the code and output folders the crypto strategy (Strategy B in the paper) is labelled C.

| File | Figure in the paper |
|---|---|
| `fig01_c_funding_by_coin.png` | Figure 1: Average funding rate by coin |
| `fig02_a_positions.png` | Figure 2: Strategy A: how often each currency is held |
| `fig03_a_cum.png` | Figure 3: Strategy A: growth of $1, carry and crowd-filtered carry (net of costs) |
| `fig04_a_lrv.png` | Figure 4: Strategy A and the Lustig–Roussanov–Verdelhan carry factor |
| `fig05_a_contrib.png` | Figure 5: Strategy A: profit and loss by currency |
| `fig06_a_crowding_drawdown.png` | Figure 6: Strategy A: the crowding measure and drawdowns |
| `fig07_a_2008.png` | Figure 7: The 2008 carry crash |
| `fig08_c_cum_annotated.png` | Figure 8: Strategy B: growth of $1 (net of costs, log scale) |
| `fig09_c_decomp_annotated.png` | Figure 9: Strategy B: cumulative funding received and price returns |
| `fig10_c_performance.png` | Figure 10: Strategy B: gross and net value, drawdown, and return components |
| `fig11_c_drawdown.png` | Figure 11: Strategy B: drawdown from the previous peak |
| `fig12_c_contrib.png` | Figure 12: Strategy B: total profit and loss by coin |
| `fig13_comb.png` | Figure 13: FX carry, crypto carry, and the 50/50 combination |
| `fig14_ac_rolling_corr.png` | Figure 14: Rolling correlation between FX carry and crypto carry |
| `fig15_robustness.png` | Figure 15: Robustness of both strategies to parameter choices |
