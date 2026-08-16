# Scalper Pro — design document

Answers sections A–H of your brief. The code follows this document exactly; if
they ever disagree, the code is wrong.

---

## A. The strategy I selected, and why

**HTF-aligned liquidity-sweep and pullback continuation, confirmed by market
structure.**

For a 1–5 minute holding period there are only three entry models that survive
retail spreads. The system detects exactly these three and nothing else:

| Setup | What it is | Why it works on 1–5m |
|---|---|---|
| **SWEEP** (best) | Price wicks through a known liquidity level (prior swing low, previous-day low, session low) and closes back inside | Stops sit under obvious lows. When they are run and price immediately reclaims, the move away is fast — which is exactly what a seconds-to-minutes hold needs |
| **PULLBACK** | In an established HTF trend, price returns to value (EMA 9/20 band or VWAP) and rejects | The highest-frequency setup. Entry is close to the invalidation point, so the stop is small — the only way a $60 account can size properly |
| **BREAK–RETEST** | Structure breaks, price returns to the broken level and holds | Gives a defined invalidation and a measured target |

Everything else was rejected for a stated reason:

- **Raw breakout entries** — on 1m most breaks fail, and you pay the spread at the
  worst price. Breakouts are only traded here on the *retest*.
- **Mean reversion at Bollinger extremes** — profitable in a range, fatal in a
  trend. Bollinger is used to *identify* the regime, never as a trigger.
- **Indicator-cross entries** (MACD cross, RSI cross) — these are derivatives of
  price that arrive after the move. On a 3-minute hold, a lagging trigger is the
  whole loss.

The ordering principle throughout: **structure and location decide *whether* to
trade; momentum only decides *when*.**

---

## B. Timeframe architecture

```
1D    MACRO BIAS      close vs EMA20/50, prior day H/L
        │             → veto layer. Never generates entries.
        ▼
1H    DIRECTION       EMA20/50 + slope, RSI regime
        │             → decides whether longs or shorts have priority.
        ▼
5M    SETUP           swing structure, liquidity pools, S/R
        │             → decides WHERE a trade is allowed to happen.
        ▼
1–3M  EXECUTION       trigger candle, momentum, volume
                      → decides WHEN, and sets entry / stop / target.
```

Each layer can only ever *restrict* the layer below it. A 1m trigger cannot
create a long if 1H and 1D both point down — that is the countertrend gambling
you asked me to prevent.

The one exception is a **sweep reversal against 1H but with 1D**, which is
permitted at a reduced score, because a stop-run into daily support is a
legitimate scalp. Sweeps against *both* higher timeframes are rejected outright.

Chart timeframe 1m–5m is enforced; above 15m the script tells you it is the
wrong tool rather than pretending.

---

## C. Indicators used — and what I removed

### Kept

| Component | Role | Why it earns its place |
|---|---|---|
| **Market structure** (pivots, BOS, CHoCH, HH/HL/LH/LL) | Backbone | The only component that describes *what price is doing* rather than a smoothed derivative of it. Zero lag beyond pivot confirmation |
| **HTF bias 1D + 1H** | Veto + priority | The single largest filter on trade quality. Costs nothing in lag because it is context, not trigger |
| **Liquidity levels** (5M swings, prior-day H/L, session H/L) | Location + the sweep setup | Where stops actually sit. This is what a sweep sweeps |
| **VWAP** | Value reference | The intraday line institutions actually reference. Anchored, so it does not lag like a moving average |
| **EMA 9 / 20 / 50 / 200** | Pullback band + trend | 9/20 defines "value" for a pullback; 50/200 give slower context at a glance |
| **ATR** | Stops, targets, volatility regime | Never a signal. It sizes everything |
| **Relative volume** | Confirmation of sweeps and breaks | A sweep on no volume is noise. Note: FX volume is tick volume |
| **RSI(9)** | Momentum filter + divergence + anti-chase | See §G below for how it is used — *not* as overbought/oversold |
| **Bollinger bandwidth** | Regime only | Squeeze vs expansion decides which setups are allowed. Bands are not a trigger |
| **Candlestick trigger** (5 forms) | Execution timing | Engulfing, rejection wick, inside-bar break — the ones that actually mark a turn on a 1m chart |

### Removed, with reasons

| Removed | Why |
|---|---|
| **MACD** | You asked me to evaluate whether it is too slow. It is. MACD(12,26,9) on a 1m chart has an effective lookback near 26 minutes and its signal line adds nine more. For a 3-minute hold it confirms after the trade should already be closed. It is also a derivative of two EMAs the system already plots — it adds lag, not information. **Removed entirely.** |
| **Stochastic** | Measures the same thing as RSI. Keeping both is one opinion counted twice |
| **ADX** | A double-smoothed 14-period average. On 1m it identifies a trend roughly when the trend ends. Regime detection now uses Bollinger bandwidth percentile + EMA alignment + structure, all of which respond faster |
| **45 candlestick patterns** | Ladder Bottom, Concealing Baby Swallow, Tri-Star and friends are daily-chart formations. On a 1m chart they are coincidences. Five execution-relevant candle forms remain |
| **Fibonacci retracement levels** | The useful part — "am I buying in the lower half of the leg" — is already answered by the pullback-into-value test. Drawing the levels added lines without changing a decision |

The 45-pattern script still exists as `candlestick_master_pro.pine` if you want
it for higher timeframes. It is a different tool for a different job, and it is
what was pushing the old script into Pine's compiler limits.

---

## D. Entry rules — exact

### Hard requirements (all must be true, or the output is NO TRADE)

1. Chart timeframe ≤ 15m.
2. **Volatility is tradable**: ATR ≥ `Minimum ATR (pips)`. A dead market cannot pay the spread.
3. **Target clears cost**: TP1 distance ≥ `Spread (pips)` × `Minimum TP1 / spread ratio`.
4. **Stop fits the account**: required stop ≤ the maximum stop your risk budget allows at the broker's minimum lot (see §F). If it does not fit, the signal is suppressed and the panel says so.
5. **A setup exists**: SWEEP, PULLBACK or BREAK–RETEST was detected.
6. **Not both higher timeframes against the trade.**
7. Regime is not `DEAD`, and if `Session filter` is on, price is inside a killzone.
8. Score ≥ `Long / Short threshold`.

### LONG

```
1D bias bullish or neutral                          [required unless SWEEP]
1H bias bullish, or neutral with bullish structure  [required unless SWEEP]
        ↓
Chart structure: structDir ≥ 0 (no live bearish BOS against us)
        ↓
ONE of:
   SWEEP        low < liquidityLow AND close > liquidityLow
                (wick through, close back above)
   PULLBACK     trend up AND low tagged the EMA9/20 band or VWAP
                AND not extended (< maxExt ATR from EMA9)
   BREAK-RETEST bullish BOS within lookback AND price returned to the
                broken level AND held it
        ↓
Trigger candle: bullish engulf, rejection wick, or a decisive close
   (body ≥ 50% of range, close in the top third)
        ↓
Momentum: RSI rising AND RSI < chase guard  (not already exhausted)
        ↓
Score ≥ threshold  →  LONG or STRONG LONG
```

### SHORT

The exact mirror. Every level, every comparison, inverted.

---

## E. Exit rules — exact

### Stop loss

Structure first, volatility as a floor:

| Setup | Stop |
|---|---|
| SWEEP | beyond the sweep wick |
| PULLBACK | beyond the pullback swing extreme |
| BREAK–RETEST | beyond the retested level |

then `stop = max(structural distance, ATR × Stop ATR floor) + buffer`,
where the buffer is `spread × 1.5` so you are not stopped by the quote itself.

Hard rejection if the resulting stop exceeds what the account can size.

### Take profit

- **TP1 = 1R** (configurable), *or* the nearest opposing structure if that is
  closer — whichever comes first, provided it still clears the spread test.
  Take roughly half off here and **move the stop to break-even.**
- **TP2** = the next liquidity pool (the 5M swing in the trade's direction),
  capped at `Max R multiple` so it stays realistic for a 1–5 minute hold.
- **Time stop**: exit at `Maximum hold (bars)` regardless. A scalp that stops
  moving is a losing scalp holding your margin hostage.
- **Trailing**: after TP1, trail behind the EMA9. The panel marks the trade
  state (`RUNNING` → `TP1 HIT — BE` → closed).

---

## F. Risk framework for a $60 account

At **0.01 lots** (almost certainly your broker's minimum) on a USD-quoted pair,
**1 pip = $0.10**.

| Rule | Value | Reason |
|---|---|---|
| Risk per trade | **1.5%** = **$0.90** | 2% is the usual ceiling; below $100 a smaller number buys you more attempts |
| **Maximum stop** | **9 pips** | $0.90 ÷ $0.10 per pip. This is the hard constraint — you cannot size below 0.01 lots |
| Max daily loss | **4.5%** = $2.70 = **3 losing trades** | Then stop for the day. Not "one more to get it back" |
| Max consecutive losses | **3** | Stop, review the log, come back next session |
| Max trades per day | **5** | Spread cost scales with trade count; edge does not |
| Minimum R:R | **1:1 after spread** | Below this, the spread makes the arithmetic unwinnable |
| Leverage | Irrelevant to risk | Leverage sets your *margin*, not your risk. Your risk is stop × lot size. Higher leverage only lets you open a position you cannot afford to lose |

**Position sizing:** `lots = riskDollars ÷ (stopPips × pipValuePerLot)`, rounded
*down* to the lot step, floored at the broker minimum. When the floor forces
more risk than the budget, the panel says **TOO BIG — SKIP** and the signal is
suppressed. That happens on this account whenever the stop exceeds ~9 pips, and
it is the single most useful thing the script does for you.

**Spread is your dominant cost.** With a 1.5-pip spread and a 9-pip stop you
give away 17% of your risk on entry. Over 5 trades a day, 20 days a month, at
0.01 lots, the spread alone costs about **$15 a month — 25% of your account.**
That is why the trade-count cap and the minimum-target filter exist.

**Why overtrading is fatal here specifically:** your edge per trade is small and
uncertain; your cost per trade is fixed and certain. Doubling trade count
doubles the certain cost and does nothing reliable to the uncertain edge.

**And plainly: I am not claiming this makes $60 profitable.** A good month might
return 10–20%, which is $6–$12, and most beginners lose their first account
regardless of tooling. Treat the $60 as tuition. The value is learning execution
with real emotions attached at a size where being wrong is cheap.

---

## G. How repainting is prevented

Five specific mechanisms:

1. **Every signal is gated on `barstate.isconfirmed`.** Nothing is emitted from a
   forming bar, so a signal that appears can never disappear.

2. **Higher-timeframe values use the `[1]` + `lookahead_on` idiom:**
   ```pine
   request.security(syminfo.tickerid, "60", close[1], lookahead = barmerge.lookahead_on)
   ```
   This is deliberately *not* the naive `request.security(sym, tf, close)`, which
   delivers the in-progress HTF bar and repaints. Asking for the previous
   completed HTF bar with lookahead on returns the same value historically and in
   real time. It is one HTF bar stale by construction — that is the price of not
   repainting, and it is the correct trade.

3. **Structure uses confirmed pivots only.** `ta.pivothigh(high, n, n)` is only
   reported `n` bars after the fact. The delay is real and acknowledged; the
   alternative (a "live" pivot) is a value that changes after you have acted on it.

4. **A broken swing is consumed.** Each swing can be broken exactly once, so a
   BOS is a discrete event on one bar rather than a condition that keeps
   re-evaluating true and re-drawing.

5. **No `varip`, no `lookahead_on` without an offset, no future bar indices in
   any condition.** Drawings extend forward, but no *decision* reads forward.

**How to verify it yourself** rather than taking my word: note the signals on a
live chart, then refresh the page. Any signal that moves or vanishes is
repainting. Also compare bar-replay results against the live chart — they must
match exactly.

---

## H. How to test this properly

Use the **strategy version** (`scalper_pro_strategy.pine`), not the indicator.
Labels on a chart always look good in hindsight; a strategy tester does not
flatter you.

**Configure the tester honestly:**

- Commission: your actual spread, as `commission_type = cash_per_contract`
- Slippage: 1–2 ticks minimum
- Order size: the fixed lot you will really trade
- Initial capital: $60

**Metrics that matter, in order:**

1. **Expectancy per trade** = (Win% × AvgWin) − (Loss% × AvgLoss). If this is not
   positive *after* spread, nothing else matters.
2. **Profit factor** — above 1.3 is a real edge; above 2.0 on 1m data usually
   means a bug or curve fitting.
3. **Maximum drawdown** in R, not dollars. More than 10R of drawdown is
   untradeable on $60.
4. **Trade count** — under ~100 trades, results are noise. You need 200+.
5. **Longest losing streak** — this is what actually makes people quit. If it is
   8, ask yourself honestly whether you would have kept going.
6. **Win rate** last. A 40% win rate at 2R beats a 70% win rate at 0.5R.

**Test across regimes separately**, not as one blended number: a trending month,
a ranging month, and a high-volatility news period. A system that only works in
one regime is a regime bet, not a system.

**Avoiding curve fitting:** the script deliberately has few tunable numbers, and
the defaults are conventional values (EMA 9/20/50/200, RSI 9, ATR 14), not
optimized ones. If you optimize parameters until the backtest looks good, you
have fitted the past. Change one parameter, and if results collapse, the edge was
never there. Validate on a symbol and a date range you did not tune on.

---

## Signal classification

| Score | Output | Meaning |
|---|---|---|
| ≥ 85 | 🟢 **STRONG LONG** / 🔴 **STRONG SHORT** | Every layer agrees, premium location |
| 70–84 | 🟢 LONG / 🔴 SHORT | Tradable, one or two checks missing |
| 55–69 | ⚪ WEAK — shown, not signalled | Watch only |
| < 55 | ⚪ **WAIT / NO TRADE** | Includes every case where a hard requirement failed |

Thresholds are inputs. The bands are deliberately wider than the 0–39/40–59/…
scheme in your brief because the hard-requirement gate already removes most
low-quality cases before scoring — a setup that reaches the scorer is not
starting from zero.

**The score is confluence quality, not a win probability.** An 88 means the model
agrees with itself, not that 88% of these win. Only your own backtest produces
that number.
