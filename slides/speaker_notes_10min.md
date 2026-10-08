# Speaker notes: 10-minute presentation

Read alongside `slides/presentation_10min.pptx`. The same notes are in each slide's notes pane.

## Slide 1. Title (about 0:20)

- Good morning. Our project asks one question: do carry trades crash when they are crowded?
- We test it in two markets with the same economics: G10 currencies and crypto.
- Strategy A is G10 FX carry with a crowding filter; Strategy C is crypto funding carry.

## Slide 2. Carry pays because it crashes (about 1:00)

- Carry means borrowing in a low-yield asset and holding a high-yield one.
- Uncovered interest parity says this should earn nothing, but in the data it earns a premium.
- The catch is crash risk: carry goes up the stairs and down the elevator.
- Brunnermeier, Nagel and Pedersen show crashes are worst when speculators are crowded into the trade.
- In FX the yield is the interest differential and we measure crowding with CFTC positions.
- In crypto the yield is the perpetual funding rate, which itself measures leveraged demand.
- We wrote the hypotheses and all parameters down before running any backtest.

## Slide 3. Data and methodology (about 0:50)

- All data are public: FRED for FX and rates, CFTC for positions, Binance for crypto.
- One data fix worth mentioning: before 2000 the CFTC lists currency futures under a different exchange name; matching both names gave us positioning back to 1986.
- Every parameter was fixed in advance, and we hold out an out-of-sample period: 2011 on for FX, 2024 on for crypto.
- Returns are net of costs, there is no look-ahead, and we keep the coins that died, LUNA and FTT.

## Slide 4. Strategy A rule (about 0:50)

- Each month we rank seven currencies by their interest rate against the dollar.
- We buy the two highest and sell the two lowest, so the portfolio has no net dollar bet.
- For crowding we take speculators' net futures position and z-score it over 36 months.
- Crowding is high when speculators are unusually long what we hold and short what we sell.
- Above one, we halve the position. This happened in 33 months.

## Slide 5. Strategy A results (about 1:20)

- Plain carry earns about 3.3% a year after costs, a net Sharpe of 0.37.
- Our carry has a 0.82 correlation with the published Lustig–Roussanov–Verdelhan factor, which validates the code and data.
- After crowded months, next-month carry averages only 0.02% versus 0.30% otherwise, with more negative skew.
- Out of sample the filter lifts the Sharpe from 0.27 to 0.32, and every variant in our robustness grid also beats 0.27.
- But it did not avoid 2008: the crash started from a non-crowded reading, so the max drawdown is -37% either way.
- Caveat: only 33 crowded months, so the effect is not precisely estimated.

## Slide 6. Strategy A risk (about 0:50)

- When does it lose? We regress monthly carry on the dollar factor and on equity-volatility shocks.
- The volatility beta is -1.55 with a t-stat of -3.7: carry loses when volatility jumps.
- Once we control for these factors the alpha is not significant, so carry is pay for risk, not a free lunch.
- From July 2008 to March 2009 the strategy lost 20.5% as the funding currencies, yen and Swiss franc, rallied.

## Slide 7. Strategy C (about 1:20)

- Crypto perpetual futures have their own interest rate, the funding rate, paid every 8 hours between longs and shorts.
- High funding means many leveraged longs, so it is both a carry signal and a crowding signal.
- Each Sunday we short the third of coins with the highest funding and buy the third with the lowest.
- We keep LUNA and FTT, which collapsed in 2022, to avoid survivorship bias.
- Net Sharpe is 0.14 over the full sample: -0.07 in 2020 to 2023 and 0.81 since 2024.
- The worst week was the LUNA collapse, -27.3%: traders were shorting LUNA, its funding turned negative, so our rule held it long.

## Slide 8. Strategy C drivers (about 1:10)

- We split the return into funding and price. Funding adds about 8.5% a year, steadily.
- But price moves dominate: in 2020 to 2023 the coins we shorted, like DOGE and XRP, kept rallying and wiped out the funding.
- Since 2024 most of the gain came from price, so we read the strong out-of-sample number with caution.
- The strategy has no market exposure; its losses come from single coins, LUNA alone -87 percentage points.
- A risk control we fixed in advance made things worse, Sharpe -0.16: the cap halved exposure and the filter missed LUNA's timing.
- So crypto carry crashes in the mirror image of FX: it ends up long whatever traders short hardest.

## Slide 9. Combined portfolio (about 0:50)

- Finally, we scale both strategies to 10% volatility and combine them 50/50.
- Their correlation is only 0.11: FX and crypto carry crash at different times.
- The mix has 7.0% volatility and a Sharpe of 0.51, with a smaller worst month than either part.
- It does not beat FX alone on Sharpe because crypto carry was weak in this window, but the diversification is clear.

## Slide 10. Conclusions (about 1:00)

- To conclude: in both markets carry looks like compensation for crash risk.
- In FX, crowding measured from CFTC positions is a cheap and modestly useful warning sign.
- In crypto, sorting on funding alone exposes you to single-coin collapses like LUNA and FTX.
- Because the two crash at different times, they diversify each other.
- Main limitations: a short crypto sample, few crowded FX months, and simple cost estimates.
- Thank you, we are happy to take questions.
