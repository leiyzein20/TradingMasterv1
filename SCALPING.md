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

---

# Update: signal table, sizing, Fibonacci, and where the oscillators went

## "I'm not seeing SBS / SSS"

They are in the script — they were just being filtered out, and nothing told you
why. The panel now has a **`Waiting on`** row that names the *first* gate
blocking a signal right now, e.g.:

- `HTF bias not aligned (60 + 1D)` — 1H and 1D disagree, so no trade either way
- `outside killzone` — you are testing outside London/NY hours
- `no pullback into value` — in trend but price has not come back to the EMA band
- `too extended (2.31 ATR from EMA)` — the move already ran
- `momentum only 1/3` — MACD/Stoch/RSI do not agree yet
- `TP1 only 1.4 pips, need 3.0` — **the most likely one on a 1m chart**
- `score gate` — everything passed but the score is under your threshold

That last one deserves attention. On a 1m FX chart ATR is often 1.5–2 pips, so a
1R target can be smaller than the minimum pip filter and **no signal will ever
fire**. That is the filter doing its job — a 1.4-pip target does not survive the
spread — but it means 1m is the wrong timeframe for a small account. Move to 5m,
or lower `Minimum TP1 distance (pips)` if you genuinely have a sub-1-pip spread.

To see signals sooner while learning, relax in this order: **Strong signal
minimum score** → **Max extension** → **Require BOTH bias timeframes** →
**Killzones**. Give up the killzone filter last.

## The detail table instead of hovering

**Settings → Colours & Legend → Signal detail table position.** The full
breakdown of the most recent SBS/SSS now renders as a table (default: middle
right) — direction, score, how many bars ago, trigger pattern, entry, stop in
price *and* pips, TP1/TP2, the time stop, and the complete reason list.

It also shows the position sizing: your risk budget in dollars, the lot size,
the actual dollar risk, and what TP1/TP2 pay at that size.

One limitation worth stating: Pine has **no chart click event**. A script cannot
know which label you clicked. So the table always shows the *latest* signal.
Older signals still carry their full tooltip on the label — hover, or
long-press on mobile.

Set the position to `Off` if you would rather only use tooltips.

## Position sizing for a small account

New **Account & Position Size** group: account size, risk %, contract size,
broker minimum lot and lot step. Every signal is then costed in real money, and
the table turns **red with a warning** when your broker's minimum lot forces
more risk than your budget allows — which on a $50 account happens as soon as
the stop is wider than about 10 pips.

Full arithmetic and the settings for $50: **[`ACCOUNT_50.md`](ACCOUNT_50.md).**

## Fibonacci

Added as a **location filter**, not decoration. The script takes the last
confirmed swing leg and computes:

- the **0.5 line** — the discount/premium divider. Below it on an up leg is
  discount (where you want to buy); above it is premium (where you want to sell).
- the **golden pocket**, 0.618–0.705 — where reactions cluster.

Longs now require price to be in discount or the golden pocket; shorts require
premium or the golden pocket. It is a hard gate on SBS/SSS and a scored check in
the confluence engine, and the panel shows the current zone in the **`Fib zone`**
row. Turn it off with `Check: Fibonacci discount / premium`.

Only those two levels are drawn. The 0.382/0.786 lines were left out on purpose —
they add lines without changing a decision.

## BOS / CHoCH clutter

Three fixes:

- Break lines are now **bounded**: each spans the swing it broke plus a short
  tail, instead of `extend.right` running to the edge of the chart forever. That
  was what turned the chart into a grid. Turn it off with `Keep BOS / CHoCH lines
  short` if you prefer the old behaviour.
- Only the **2 most recent** breaks are kept (`BOS / CHoCH marks kept on chart`).
- The **supply/demand proxy plots were removed entirely.** They were only
  `low ± ATR` on bars that happened to touch a level, so they rendered as
  disconnected dashes rather than zones — pure clutter. Zone work is done
  properly by the FVG boxes and the S/R steplines.

## Where RSI and MACD are

They are **not chart lines and cannot be**. RSI and Stochastic live on a 0–100
scale, MACD on a zero-centred one. On a EURUSD price axis around 1.08 they would
all be a flat line pinned to the bottom of the screen. That is why the main
indicator reports them as **numbers in the panel**.

To see the actual curves, add the companion script:

**[`candlestick_master_oscillators.pine`](candlestick_master_oscillators.pine)**

Add it to the same chart and it opens in its own pane underneath. It uses the
same settings and the same colours as the main indicator, so the two always
agree. Pick what to display with the **Show** input:

- `RSI + Stochastic` — both share the 0–100 scale, so they fit in one pane
- `MACD` — needs its own scale, so give it a second copy of the script

It also draws your **do-not-chase levels** (RSI 78 / 22 by default) and has a
momentum table showing the same 2-of-3 count the main panel reports, so when the
main indicator says `momentum only 1/3` you can see exactly which one is missing.
