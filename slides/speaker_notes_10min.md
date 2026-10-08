# Speaker notes: 10-minute presentation

Read alongside `slides/presentation_10min.pptx`. The same notes are in each slide's notes pane.

## Slide 1. Title (about 0:20)

- Good morning. Our project asks one question: do carry trades crash when they are crowded?
- We test it in two markets with the same economics: G10 currencies and crypto.
- Strategy A is carry in seven G10 currencies against the US dollar, with a crowding filter built from CFTC data.
- Strategy C is funding carry in twelve crypto perpetual futures on Binance, including the coins that collapsed, Terra and FTX Token.

## Slide 2. Carry pays because it crashes (about 1:00)

- Carry means borrowing in a low-yield asset and holding a high-yield one.
- Uncovered interest parity says this should earn nothing, but in the data it earns a premium.
- The catch is crash risk: carry goes up the stairs and down the elevator.
- Brunnermeier, Nagel and Pedersen show crashes are worst when speculators are crowded into the trade.
- In FX the yield is the interest-rate differential, and we measure crowding with CFTC speculator positions.
- Our FX universe is the yen, euro, British pound, Swiss franc, Canadian dollar, Australian dollar and New Zealand dollar, all against the US dollar.
- In crypto the yield is the perpetual funding rate, which also measures leveraged demand.
- Our coins are Bitcoin, Ethereum, BNB, XRP, Cardano, Dogecoin, Solana, Litecoin, Chainlink, Avalanche, Terra and FTX Token.
- We wrote the hypotheses and all parameters down before running any backtest.

## Slide 3. Data and methodology (about 0:50)

- All data are public: FRED for FX and rates, CFTC for positions, Binance for crypto.
- One data fix worth mentioning: before 2000 the CFTC lists currency futures under a different exchange name; matching both names gave us positioning back to 1986.
- Every parameter was fixed in advance, and our out-of-sample period starts in 2011 for FX and in 2024 for crypto.
- Returns are net of costs, there is no look-ahead, and we keep the two coins that died, Terra (LUNA) and FTX Token (FTT).

## Slide 4. Strategy A rule (about 1:00)

- Each month we rank the seven currencies by their three-month interest rate.
- We buy the two highest and sell the two lowest, so the portfolio has no net dollar bet.
- In practice we are almost always long the New Zealand and Australian dollars and short the Swiss franc, often with the yen or the euro.
- For crowding we take speculators' net futures position and z-score it over 36 months.
- Crowding is high when speculators are unusually long what we hold and short what we sell.
- When this score is above one standard deviation, we halve the position, which happened in 33 months.

## Slide 5. Strategy A results (about 1:20)

- Plain carry earns about 3.3% a year after costs, a net Sharpe of 0.37.
- Our carry has a 0.82 correlation with the published Lustig–Roussanov–Verdelhan factor, which validates the code and data.
- After crowded months, next-month carry averages only 0.02% versus 0.30% otherwise, with more negative skew.
- Out of sample the filter lifts the Sharpe from 0.27 to 0.32, and every variant in our robustness grid also beats 0.27.
- But it did not avoid 2008: the crash started from a non-crowded reading, so the max drawdown is -37% either way.
- One caveat is that there are only 33 crowded months, so the effect is not precisely estimated.

## Slide 6. Strategy A risk (about 0:50)

- To see when it loses, we regress monthly carry on the dollar factor and on equity-volatility shocks.
- The volatility beta is -1.55 with a t-stat of -3.7: carry loses when volatility jumps.
- Once we control for these factors the alpha is not significant, so carry is pay for risk, not a free lunch.
- From July 2008 to March 2009 the strategy lost 20.5% as the funding currencies, the Japanese yen and the Swiss franc, rallied against the Australian and New Zealand dollars.

## Slide 7. Strategy C (about 1:20)

- Crypto perpetual futures have their own interest rate, the funding rate, paid every 8 hours between longs and shorts.
- High funding means many leveraged longs, so it is both a carry signal and a crowding signal.
- Each Sunday we short the third of coins with the highest funding and buy the third with the lowest.
- The twelve coins are Bitcoin, Ethereum, BNB, XRP, Cardano, Dogecoin, Solana, Litecoin, Chainlink, Avalanche, Terra and FTX Token.
- We keep Terra (LUNA) and FTX Token (FTT), which both collapsed in 2022, to avoid survivorship bias.
- Net Sharpe is 0.14 over the full sample: -0.07 in 2020 to 2023 and 0.81 since 2024.
- The worst week was the Terra (LUNA) collapse in May 2022, -27.3%: traders were shorting Terra, its funding turned negative, and so our rule held it long.

## Slide 8. Strategy C drivers (about 1:10)

- We split the return into funding and price. Funding adds about 8.5% a year, steadily.
- But price moves dominate: in 2020 to 2023 the coins we shorted, like Dogecoin and XRP, kept rallying and wiped out the funding.
- Since 2024 most of the gain came from price, so we read the strong out-of-sample number with caution.
- The beta to Bitcoin is about zero, so the strategy has no market exposure.
- Its losses come from single coins: Terra alone cost 87 percentage points, XRP 58 and Dogecoin 43, while Solana and BNB were the biggest winners.
- A risk control we fixed in advance made things worse and lowered the Sharpe to -0.16: the cap halved exposure and the filter missed the timing of Terra's collapse.
- Our takeaway is that crypto carry crashes in the mirror image of FX: it ends up long whatever traders short hardest.

## Slide 9. Combined portfolio (about 0:50)

- Finally, we scale both strategies to 10% volatility and combine them 50/50.
- Their correlation is only 0.11: FX and crypto carry crash at different times.
- The mix has 7.0% volatility and a Sharpe of 0.51, and its worst month, -5.9%, is smaller than either part's.
- It does not beat FX alone on Sharpe, because crypto carry was weak in this window.
- Our takeaway is that the benefit of combining them is lower risk, not a higher return.

## Slide 10. Conclusions (about 1:00)

- To conclude: in both markets carry looks like compensation for crash risk.
- In FX, crowding measured from CFTC positions is a cheap and modestly useful warning sign.
- In crypto, sorting on funding alone exposes you to single-coin collapses like Terra and FTX Token.
- Because the two crash at different times, they diversify each other.
- The main limitations are a short crypto sample, few crowded FX months, and simple cost estimates.
- Thank you, we are happy to take questions.
