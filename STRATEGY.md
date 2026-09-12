# Scalper Pro — design document

Answers sections A–H of your brief. The code follows this document exactly; if
they ever disagree, the code is wrong.

---

## A. The strategy I selected, and why

**HTF-aligned liquidity-sweep and pullback continuation, confirmed by market
structure.**

For a 1–5 minute holding period there are only a handful of entry models that
survive retail spreads. The system detects exactly these and nothing else, in
this priority order:

| Setup | What it is | Why it works on 1–5m |
|---|---|---|
| **SWEEP-REV** (best) | Price wicks through a known liquidity level (prior swing low, previous-day low, session low), closes back inside, *then* structure shifts | Stops sit under obvious lows. When they are run and price immediately reclaims, the move away is fast — which is exactly what a seconds-to-minutes hold needs. Staged: nothing is entered until the shift and a trigger candle |
| **EXH-REV** | Enough independent exhaustion readings stack up, *then* structure shifts | Same three-stage lifecycle. The evidence is counted, never predicted |
| **CONTINUATION** | HTF trend + a real displacement leg + a controlled pullback into value or demand + a higher low + resumption | The strictest trend setup: it requires the drive to have actually happened and the pullback to have stayed shallow and weak |
| **BREAK–RETEST** | Structure breaks, price returns to the broken level and holds | Gives a defined invalidation and a measured target |
| **PULLBACK** | In an established HTF trend, price returns to value (EMA 9/20 band or VWAP) and rejects | The highest-frequency setup, and the weakest — it rarely clears the score threshold on its own |

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
1D    MACRO TREND     close vs EMA20/50, prior day H/L
 4H   SWING CONTEXT   close vs EMA20/50, 20-bar swing H/L
 1H   DIRECTION       EMA20/50, RSI regime
        │             → three votes become ONE reading: bullish, bearish,
        │               mixed, and whether all three agree ("strong").
        ▼
15M   INTRADAY        structure, 12-bar liquidity pools
 5M   SETUP           swing structure, liquidity pools, S/R
        │             → decides WHERE a trade is allowed to happen.
        ▼
3M/1M EXECUTION       trigger candle, momentum, volume
                      → decides WHEN, and sets entry / stop / target.
```

A 1m trigger cannot create a long against a **strong** higher-timeframe bear
reading. "Strong" means 1D, 4H and 1H all agree — that is the only state that
carries an outright veto, and it exists because the most expensive beginner
mistake is fading a trend on an oscillator.

The single exception is a fully staged counter-trend reversal: it needs the
reversal to have reached stage 3, a swept higher-timeframe level, the required
exhaustion evidence, *and* the structure, liquidity and Wyckoff layers all
voting for it. Anything less stays blocked. Turn `Allow counter-trend
reversals` off and even that is gone.

Chart timeframe 1m–5m is enforced; above 15m the script tells you it is the
wrong tool rather than pretending.

---

## B2. The nine layers, and why they can cancel each other

This is the part that makes the script reject trades instead of rationalising
them. Nine layers each vote `-1 / 0 / +1` from their **own** evidence:

| # | Layer | Reads | Decisive? |
|---|---|---|---|
| L1 | HTF context | 1D + 4H + 1H agreement | ✅ |
| L2 | Structure | BOS / CHoCH / MSS, HH-HL vs LH-LL | ✅ |
| L3 | Liquidity | a pool swept and reclaimed | ✅ |
| L4 | Wyckoff | spring / upthrust / SOS / SOW / absorption | ✅ |
| L5 | Supply–demand | reaction at a displacement-origin zone | ✅ |
| L6 | Momentum | RSI + MACD + Bollinger — **one vote between them** | — |
| L7 | Price action | trigger candle closed *at a location* | — |
| L8 | Trend / EMA | 20-50-200 alignment and slope | — |
| L9 | Volume | effort vs result | — |

Three rules follow from this:

1. **Abstaining is not agreement.** A layer with no reading votes 0. Volume on
   a feed without volume data abstains rather than quietly counting as
   confirmation.
2. **Conflict cancels.** If `maxConflict` (default 2) of the five *decisive*
   layers point the other way, the output is ⚫ NO TRADE regardless of score,
   and the panel names which layers disagreed. A 78/100 with three decisive
   layers against is not a trade.
3. **Correlated indicators share a vote.** RSI, MACD and Bollinger are all
   smoothed transforms of the same close series. They get one vote and one
   10-point bucket between them, so three agreeing oscillators cannot
   impersonate three independent confirmations. EMA is a derivative of price
   and is capped at 5.

There is also a floor: at least `minDecisive` (default 2) of the five decisive
layers must back the direction. A candle plus a momentum reading is never
enough on its own.

---

## C. Indicators used — and what I removed

### Kept

| Component | Role | Why it earns its place |
|---|---|---|
| **Market structure** (pivots, BOS, CHoCH, HH/HL/LH/LL) | Backbone | The only component that describes *what price is doing* rather than a smoothed derivative of it. Zero lag beyond pivot confirmation |
| **HTF bias 1D + 4H + 1H** | Veto + priority | The single largest filter on trade quality. Costs nothing in lag because it is context, not trigger. The three become one reading, and only unanimous agreement ("strong") carries an outright veto |
| **Liquidity levels** (5M swings, prior-day H/L, session H/L) | Location + the sweep setup | Where stops actually sit. This is what a sweep sweeps |
| **VWAP** | Value reference | The intraday line institutions actually reference. Anchored, so it does not lag like a moving average |
| **EMA 9 / 20 / 50 / 200** | Pullback band + trend | 9/20 defines "value" for a pullback; 50/200 give slower context at a glance |
| **ATR** | Stops, targets, volatility regime | Never a signal. It sizes everything |
| **Relative volume** | Confirmation of sweeps and breaks | A sweep on no volume is noise. Note: FX volume is tick volume |
| **RSI(14)** | Momentum family member + divergence + anti-chase | See §G below for how it is used — *not* as overbought/oversold |
| **MACD(12,26,9)** | Momentum family member | Re-added by request. It is **capped**, not trusted: it shares one vote and one 10-point bucket with RSI and Bollinger, and its histogram *direction* is the reading used, because the crossover itself arrives late at this speed. It can confirm a thesis; it can never create one |
| **Bollinger bands + bandwidth** | Regime, momentum family member, exhaustion | Squeeze vs expansion decides which setups are allowed. A band touch is never a trigger |
| **Wyckoff engine** | Reversal quality | Spring / upthrust / test / SOS / SOW / absorption, each requiring an established range, a level with ≥2 prior reactions, a close-based rejection and effort-vs-result behaviour |
| **Supply / demand zones** | Location | The origin of a displacement move — the price the aggressor had to pay. Fresh zones score higher than tested ones |
| **Asian range** | Liquidity | Not traded. Tracked because its high and low are what London runs |
| **Candlestick trigger** (5 forms) | Execution timing | Engulfing, rejection wick, drive candle — the ones that actually mark a turn on a 1m chart |

### Removed, with reasons

| Removed | Why |
|---|---|
| **Stochastic** | Measures the same thing as RSI. Keeping both is one opinion counted twice |
| **ADX** | A double-smoothed 14-period average. On 1m it identifies a trend roughly when the trend ends. Regime detection now uses Bollinger bandwidth percentile + EMA alignment + structure, all of which respond faster |
| **45 candlestick patterns** | Ladder Bottom, Concealing Baby Swallow, Tri-Star and friends are daily-chart formations. On a 1m chart they are coincidences. Five execution-relevant candle forms remain |
| **Fibonacci retracement levels** (as drawn lines) | The useful part — *how deep is this pullback* — is measured directly instead: the CONTINUATION setup requires the retrace to sit between 15% and `maxRetrace` (default 66%) of the displacement leg, which is the 0.382–0.618 band by another name. Drawing the levels added lines without changing a decision, so they are computed, not plotted |

The 45-pattern script still exists as `candlestick_master_pro.pine` if you want
it for higher timeframes. It is a different tool for a different job, and it is
what was pushing the old script into Pine's compiler limits.

---

## D. Entry rules — exact

### Hard requirements (all must be true, or the output is NO TRADE)

1. Chart timeframe ≤ 15m.
2. **Volatility is tradable**: ATR ≥ `Minimum ATR (pips)`. A dead market cannot pay the spread.
3. **Not inside a news blackout window** (if one is configured — see the addendum on news).
4. **Target clears cost**: TP1 distance ≥ `Spread (pips)` × `Minimum TP1 / spread ratio`. Otherwise: `🚫 NO TRADE — TARGET TOO SMALL`.
5. **R:R to TP2 ≥ `minRR`** (default 1.5). If the geometry does not produce it, the trade is rejected — the stop is *not* tightened to manufacture a ratio.
6. **Stop fits the account**: required stop ≤ the maximum stop your risk budget allows at the broker's minimum lot (see §F). Otherwise: `⚫ NO TRADE: POSITION SIZE / RISK NOT SUITABLE FOR ACCOUNT`.
7. **A setup exists**: staged reversal, CONTINUATION, BREAK–RETEST or PULLBACK.
8. **≥ `minAgree` of 9 layers agree** (default 5).
9. **≥ `minDecisive` of the 5 decisive layers agree** (default 2).
10. **No layer conflict**: fewer than `maxConflict` decisive layers point the other way.
11. **No strong-HTF veto**, unless the counter-trend reversal exception is met in full.
12. Regime is not `DEAD` or `SQUEEZE`, and if `Session filter` is on, price is inside a killzone.
13. Score ≥ `Minimum tradable score` (default 75).

### Score bands

| Score | Output |
|---|---|
| 85–100 | 🟢/🔴 **A+ setup** |
| 75–84 | 🟢/🔴 tradable |
| 65–74 | 🟡 **WAIT** — watch only, no entry |
| < 65 | ⚫ **NO TRADE** |

Every bar resolves to exactly one of 🟢 BUY · 🔴 SELL · 🟡 WAIT · ⚫ NO TRADE.
WAIT means something is forming. NO TRADE means the conditions themselves are
wrong and waiting will not fix them.

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

---

## Addendum — why reversals are scored differently

The first version of the scorer gave 43 of its 100 points to the higher
timeframes *agreeing* with the trade direction. That is right for a
continuation setup and completely wrong for a reversal, which by definition
disagrees with the recent direction.

The arithmetic for a counter-trend bullish reversal was:

| | earned | possible |
|---|---|---|
| 1D bias | 0 | 15 |
| 1H bias | 0 | 20 |
| 5M bias | 0 | 8 |
| everything else | 56 | 57 |
| **total** | **56** | threshold **70** |

A reversal against the higher timeframes could not reach the threshold at any
level of evidence. The result was a setup that reached CONFIRM and stayed
there permanently — the indicator saying "waiting for a trigger" forever.

**The fix:** reversals use a different profile for the same points. Instead of
asking "does the higher timeframe agree", it asks "is the higher timeframe
*stretched the other way*" — which is the fuel for a reversal, not an argument
against it.

| Points | Continuation earns it when… | Reversal earns it when… |
|---|---|---|
| 1D (15) | 1D agrees | 1D agrees (15), or disagrees but the sweep took a **daily level** (11), else 4 |
| 1H (20) | 1H agrees | 1H agrees (20), or 1H RSI is exhausted the other way (16), else 5 |
| 5M (8) | price on the right side of the 5M mean | 8 if it agrees, 5 if not — being the far side of the mean is normal at a turn |
| VWAP (3) | price on the right side | price **stretched ≥ 1 ATR** from VWAP |

A fully-evidenced counter-trend reversal that swept a daily level now scores
around 90. One with no daily level and no 1H exhaustion scores about 73 — it
can still fire, but only with everything else perfect.

**The hard veto changed too.** Trading against *both* higher timeframes was
flatly blocked. It is now allowed for exactly one case, which is the exception
the brief asked for: a staged reversal that reached ENTRY, carries at least the
configured evidence count, **and** swept an actual previous-day level. Anything
less stays blocked, and the panel says what is missing:

```
both HTFs against — needs a daily-level sweep with 4/6 evidence (have 3, daily no)
```

**Two other changes came out of the same investigation:**

- The structure-shift level was the last *major* confirmed swing. After a long
  push that can be far away, so by the time it broke, the entry was too distant
  from the swept extreme and the stop no longer fitted the account. It now uses
  the **nearer** of the major swing and the 5-bar high/low, which confirms
  sooner and keeps the stop affordable.
- **Reversal stop** gained a mode. The swept extreme is the structurally correct
  invalidation, but on a $60 account it is frequently wider than the risk budget
  allows — which silently produced no signals. `Auto` uses the swept extreme
  when it fits and falls back to the 3-bar swing when it does not, so you get a
  tradable stop or an explicit refusal, never silence.

---

## Addendum — news, and what the script genuinely cannot know

Pine Script has no access to an economic calendar. It cannot know when CPI,
NFP, FOMC or a Powell speech is scheduled, and any indicator that claims to
filter news on TradingView without an external data feed is either using a
hard-coded list that goes stale or is not doing it at all.

So the panel always reports:

```
NEWS STATUS: UNVERIFIED
```

and the only real filter offered is one you set yourself: a session window in
the `News blackout` input group. Inside it, every signal is suppressed and the
panel shows `⛔ NEWS BLACKOUT`. Set it on the day you know a release is coming;
leave it off otherwise. That is the honest limit of what this can do.

---

## Addendum — how targets are chosen

The brief's rule is *"never choose TP merely because it gives a nice-looking
risk/reward ratio"*, and the implementation follows it literally.

A ladder of real levels is built on each side of price:

- liquidity high / low (5M swing pools)
- previous day high / low
- 4H swing high / low
- 15M high / low
- Asian session high / low
- the far edge of the live supply or demand zone

TP1 is the **nearest** of those beyond the spread minimum; TP2 is the **next**
one out. Both are placed just in front of the level, not on it — the queue at
an obvious level is long and the last tick into it is the one that does not
fill. TP3 exists only as a capped runner at `maxR`.

The resulting R:R is then whatever the geometry actually produced. If it comes
out below `minRR`, the trade is **rejected**. The stop is never moved closer to
improve the ratio, because a stop placed to flatter a number is not an
invalidation level any more.

When no level can be found on that side, the R-multiple fallback is used and
the panel's R:R row shows what you are really being offered.

---

## Addendum — the Wyckoff layer's guardrails

The failure mode of every Wyckoff indicator is labelling a spring on any wick
that pokes below support. Four conditions are required here, all mechanical,
and missing any one produces no vote at all:

1. **An established range.** Height between 1.5× and `wyMaxRange`× ATR over the
   lookback. A 20-ATR "range" is a trend, and Wyckoff logic does not apply.
2. **A level that has been respected.** At least `wyTouch` *distinct* prior
   approaches — counted as entries into the zone, so ten consecutive bars
   parked on the low count as one reaction, not ten.
3. **Rejection on the close.** Price penetrated the level and closed back
   inside on the same bar.
4. **Effort vs result.** Either a rejection wick at least as long as the body,
   or volume expansion that produced almost no range — the signature of the
   other side absorbing the aggression.

A test of the spring, a sign of strength, and absorption at the extreme are
scored separately and score differently. `sos`/`sow` score highest because they
are the only ones that confirm the range was actually left.

---

## What this document does not claim

Nothing here is a statement about profitability, and no win rate is claimed or
implied anywhere in the script or these notes. The score is a measure of how
much independent evidence agrees — it is not a probability of the trade
working. Technical analysis produces probabilities, never certainty.

The only way to find out whether this has positive expectancy on XAUUSD is to
measure it: forward-test on a demo account, log every signal including the ones
you skipped, and judge it on expectancy over a sample, not on the last trade.
