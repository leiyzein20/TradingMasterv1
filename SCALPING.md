# Scalping guide (1–30 minute holds)

## The strategy the indicator now implements

For holds of 1–30 minutes, the template with the most surviving edge is
**higher-timeframe bias + lower-timeframe pullback continuation**. It is what you
were already doing manually by checking 1H and 1D first. Written out:

1. **Direction is decided on 1H and 1D, never on the entry chart.** On a 1m chart
   there is not enough information to know which way anything is going. Your job
   on the 1m is *timing*, not direction.
2. **Wait for a pullback into value.** Value = the EMA 9/21 band, VWAP, a
   qualified Fair Value Gap, or a support/resistance level. Entering mid-range,
   between levels, is where scalping money disappears.
3. **Do not enter extended.** If price is already far from the fast EMA, the move
   has happened. This is the single most expensive scalping mistake, so the
   indicator measures it (`extension from fast EMA` in ATR) and refuses signals
   past your threshold.
4. **Require a trigger candle.** A candlestick pattern from the engine, or a
   decisive momentum candle (body ≥ 50% of range, close in the leading third,
   back on the right side of the fast EMA).
5. **Require momentum agreement**, at least 2 of 3: MACD, Stochastic, RSI.
6. **Only trade the killzones.** London 07:00–10:00 and New York 12:00–15:00 GMT.
   Scalping spot FX during the Asian range or the rollover means paying spread
   into thin liquidity, and no amount of indicator accuracy fixes that.
7. **Structure must not be against you.** If the last break of structure on the
   entry chart went the other way, stand down until it flips back.
8. **The target must clear the spread.** A 2-pip target on a 1.5-pip spread is a
   losing strategy at any win rate. The `Minimum TP1 distance (pips)` filter
   rejects those setups outright.

That is exactly what SBS / SSS now require — all of it, or no signal.

### Why not the other popular scalping approaches

- **Pure mean-reversion at Bollinger extremes** works in ranges and gets
  destroyed in trends. The indicator uses the bands for *regime* (squeeze vs
  expansion) and *location*, not as a standalone signal.
- **Pure breakout scalping** on 1m is mostly false breaks; retail spreads eat
  the rest. The structure engine reports BOS/CHoCH as context, and you still
  need a pullback to enter.
- **Indicator-stacking** (RSI + MACD + Stochastic all agreeing) feels like
  confluence but is four views of one thing. That is why they now share a single
  capped 16-point momentum budget in the score instead of adding up.

## Recommended settings for your style

| Setting | Value | Why |
|---|---|---|
| Chart timeframe | **1m or 5m** (5m for 5–30 min holds, 1m for seconds–3 min) | matches your hold time |
| Scalp mode | **ON** | unlocks Must/Important patterns on 1–15m charts |
| HTF 1 / 2 / 3 | **15 / 60 / 1D** | 1H + 1D are the bias, 15m is fast confirmation |
| Require BOTH bias timeframes | **ON** | your own 1H + 1D workflow, enforced |
| Fast / Mid EMA | **9 / 21** | standard scalping pullback band |
| Max extension from fast EMA | **1.5 ATR** (tighten to 1.0 if you want fewer, cleaner entries) | anti-chasing |
| Killzones | **ON**, 0700–1000 and 1200–1500 GMT | shift for DST; set the timezone input to your broker's |
| Scalp ATR stop floor | **0.8** | tighter than the swing default of 1.2 |
| TP1 / TP2 R | **1.0 / 2.0** | scalps rarely reach 3R inside 30 minutes |
| Minimum TP1 pips | **your spread × 3** (start at 3) | viability filter |
| Max hold (bars) | **30** | your stated maximum; also how far the SL/TP lines extend |
| Signal cooldown | **5 bars** | stops one condition firing five bars in a row |
| Strong signal minimum score | **78** (raise to 85 for fewer, higher-grade signals) | selectivity dial |

If you want signals to appear more often, in this order: lower **Strong signal
minimum score** → raise **Max extension** → turn off **Require BOTH bias
timeframes** → turn off **Killzones**. Each step trades quality for quantity;
the killzone filter is the last one you should give up.

## Reading the chart

**SBS ▲ / SSS ▼** — a green up-triangle below the candle, or a red down-triangle
above it, plus a label reading e.g. `SBS 86%`. Hover the label (long-press on
mobile) and you get:

- every check that passed or failed, with the actual numbers
- which pattern triggered it and that pattern's reference reliability
- entry, stop loss (in price *and* pips), TP1, TP2, and the time stop
- the management plan

The lines drawn to the right of a signal, extending `Max hold` bars forward:

| Line | Meaning |
|---|---|
| grey solid | entry (the signal candle's close) |
| **red dashed** | stop loss |
| **green dashed** | TP1 |
| green dotted | TP2 |

### What the percentage is and is not

The number on the label is a **confluence score**: how much of the model agreed,
weighted by family. It is **not** a win rate and not a probability that the trade
wins. An 86% SBS means "almost everything this model looks at lines up here", not
"86% of these win". The same applies to the per-pattern reliability figures — those
come from the candlestick literature, not from a backtest of your symbol.

Backtest it on your pairs and sessions before sizing up. Use the TradingView bar
replay on 1m for a few hundred signals; that is the only number that matters.

## Which line is which

There is a **colour legend at the bottom right** of the chart listing every drawn
object with its colour swatch, and each row has a tooltip explaining what it is.

| | Line | Colour / style |
|---|---|---|
| ① | Bollinger upper/lower | thin blue, faint fill between |
| ② | Bollinger basis | orange **dots** |
| ③ | Fast EMA 9 | yellow, thick |
| ④ | Mid EMA 21 | magenta, thick |
| ⑤ | Slow EMA 50 | grey, thick |
| ⑥ | VWAP | cyan, thickest |
| ⑦ | Support | green **stepped** |
| ⑧ | Resistance | red **stepped** |

**BOS vs CHoCH** — these were the confusing ones, and they now look different on
purpose:

- **BOS ▲ / BOS ▼** — *solid* line, bright green / bright red. "Break of
  Structure": the trend that was already running pushed through a swing point.
  This is **continuation**.
- **CHoCH ▲ / CHoCH ▼** — *dashed* line, lime / orange. "Change of Character":
  the **first** break in the opposite direction after the previous structure.
  This is the **trend-flip warning**, and it is the more important of the two.

The old script printed `BOS+` / `CHOCH+` in the same colour, which is why you
couldn't tell them apart. Both labels now carry a tooltip spelling out the
difference.

### RSI, MACD and Stochastic

These are not chart lines and never were. They are oscillators on a 0–100 (or
zero-centred) scale — plotting them on a price axis would be meaningless, so the
indicator shows them as **live numbers in the panel at the top right** instead.
The legend's last row says this too.

If you want to see the actual curves, add TradingView's own RSI and MACD as
separate panes below the chart. Say the word and I'll write a companion
oscillator pane script that colours them to match this one and marks the same SBS
/ SSS bars.

## Alerts

Two new streams: **"SBS - Strong Buy Signal"** and **"SSS - Strong Sell
Signal"**. There is also a dynamic `alert()` carrying the score, entry, SL, TP1
and TP2 in the message — for that one create the alert with **"Any alert()
function call"**.

All signals evaluate on the **bar close**, so nothing repaints. On a 1m chart that
means you act at the close of the signal candle.

## Honest limitations

- **The indicator cannot see your spread or slippage.** The pip filter is a
  proxy. On a 1m chart with a wide-spread broker, the arithmetic may not work no
  matter how good the signal is.
- **Sub-minute holds ("seconds") are below what this can help with.** The
  fastest thing here is a 1m bar close. Anything faster is order-flow and
  execution, not indicators.
- **Killzone times are fixed clock times** and do not auto-adjust for DST. Check
  them twice a year, or set the timezone input to your broker's server time.
- **Nothing here guarantees profitability.** It enforces a disciplined,
  widely-used process and refuses low-quality setups. Position sizing, risk per
  trade, and not revenge-trading are still entirely on you — and for a scalper
  they matter more than the entry signal does.
