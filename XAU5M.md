# XAU 5M Scalper — manual

Built from `anotherone.txt`. A **new engine**, not a revision of
`xau_scalper.pine` or `scalper_pro.pine`. Nothing was carried across but UI
conventions: the palette, the dashboard table idiom, tooltip style, input
grouping, and the drawing-object pooling pattern. No trading logic was reused.

---

## 1. The strategy

Two trade types, nothing else:

- **HIGH-QUALITY REVERSAL** — price reaches a meaningful location, liquidity is
  swept, the move fails to continue, structure shifts, and a candle closes.
- **HIGH-MOMENTUM CONTINUATION** — an established trend, real displacement, a
  controlled pullback into value, and structure resuming.

Each is tracked as a **ten-step sequence**, not a boolean. Counting the steps is
what lets the dashboard say exactly what is confirmed and what is still needed,
and it is why the engine can say "7/10, still needed: structure shift" instead
of a bare no.

### The reversal sequence

| # | Step |
|---|---|
| 1 | meaningful location (4H / 1H / 15M / 5M S/R, demand, supply) |
| 2 | liquidity swept and still holding |
| 3 | failure to continue past the sweep extreme |
| 4 | rejection (wick or candle) |
| 5 | pressure weakening / absorption |
| 6 | important level reclaimed |
| 7 | structure shift — MSS, CHoCH, or a failed break |
| 8 | higher low (or lower high) forms |
| 9 | displacement |
| 10 | estimated delta and momentum agree |

### The continuation sequence

HTF trend · 15M structure · 5M structure · displacement · controlled pullback
(15–66% retrace) · pullback into value/support/Fib · weak counter-pressure · no
structure break against · higher low / lower high · structure resumes with
momentum.

**Regime changes the bar.** A mature range is where sweep reversals belong, so
the requirement is normal there; fading a trend costs an extra step. High
volatility raises the requirement for both. Compression and dead volatility
block everything.

---

## 2. Priority hierarchy

The brief's §43, enforced in code rather than described in comments:

```
1 HTF context   2 structure   3 location   4 liquidity   5 Wyckoff
6 price action  7 order-flow proxy   8 volume / delta
9 momentum     10 EMA / Bollinger   11 risk:reward
```

RSI, MACD, EMA and Bollinger cannot create a setup. They occupy 10, 3 and a
shared bucket in the score, and none of them appears in the sequence steps that
promote a setup through the state machine. An oscillator never overrules
structure.

---

## 3. BUY confirmation, exactly

All of these, in order:

1. Symbol is gold, chart is 5m, not in a news window, ATR above minimum, inside
   London or New York, regime not COMPRESSION or LOW VOLATILITY.
2. Sequence count ≥ the regime-adjusted requirement.
3. State machine has reached `WAITING_CONFIRMATION`, which needs a structure
   shift (MSS / CHoCH / BOS) — this is the line between a setup existing and a
   trade existing.
4. Higher timeframes not aligned against a continuation.
5. A reversal against a trend needs a Wyckoff event (Strict/Normal).
6. Not chasing — within `maxExtAtr` of EMA20. Otherwise the dashboard says
   **MISSED ENTRY — wait for a pullback**.
7. Target space exists, TP1 is not beyond opposing liquidity, R:R ≥ `minRR`.
8. Position size fits the account at the broker minimum lot.
9. Confluence ≥ `minScore`.
10. **On a LATER bar**, a bullish candle **closes** above the trigger level
    recorded when structure shifted.

`bar_index > stBar` is the whole of §38 in one expression: a setup can never
confirm itself on the bar that created it.

**SELL** is the exact mirror.

---

## 4. WATCH · WAIT · NO TRADE

- ⚪ **WATCH** — a sequence is building (state `WATCHING` or `SETUP`).
- 🟡 **WAIT FOR CONFIRMATION** — state `WAITING_CONFIRMATION`. The dashboard
  names the candle required and the price it must close beyond. **No trade yet.**
- ⚫ **NO TRADE** — conditions are wrong, not merely incomplete: dead
  volatility, compression, a news window, no target space, R:R too low, size
  unsuitable, or confluence below 65.

---

## 5. TP notification

Two distinct states, because an intrabar touch can be given back:

| When | Label |
|---|---|
| price reaches the TP area **intrabar** | `TP DEVELOPING — WAIT FOR CANDLE CLOSE` |
| the candle **closes** having reached it | `TP1 — TAKE PROFIT` |

The developing label is drawn **only on the live bar** and deleted each tick.
It is deliberately not written into history, because a historical label for an
intrabar condition is exactly the repainting §38 forbids.

After TP1, and only after it is genuinely reached, the engine suggests
**MOVE SL TO BREAKEVEN**. Not before — moving the stop early is how an ordinary
pullback stops out a good trade.

---

## 6. CANCEL vs TAKE PROFIT

§26 is the subtle one, and it is handled by check order:

1. **TP2 reached** → close, profit.
2. **TP1 reached** → `TP1 — TAKE PROFIT`, then break-even suggestion.
3. **Structural invalidation** → `CANCEL LONG / CANCEL SHORT — TRADE THESIS
   INVALID`, with the specific reason: `SUPPORT LOST`, `RESISTANCE RECLAIMED`,
   `structural stop taken`, or `structure broke against the position`.
4. **Time stop** → the setup stopped working.

A long rejecting at resistance is **take profit**, not a cancel. A long that
closes below the support the thesis depended on is a **cancel**. The difference
is whether price reached the objective or broke the structure — never whether
an indicator changed colour.

---

## 7. Confluence score

The brief's weights, and correlated evidence is not double-counted:

| Bucket | Points |
|---|---|
| HTF context | 15 |
| Market structure | 15 |
| Location / S&R / supply-demand (+ Fibonacci ≤ 2) | 10 |
| Liquidity | 10 |
| Wyckoff | 10 |
| Price action | 10 |
| Momentum — **RSI and MACD share this one bucket** | 10 |
| Volume / effort-result | 5 |
| Order-flow proxy / estimated delta | 5 |
| EMA | 3 |
| ATR / volatility | 2 |
| R:R + target space | 5 |

Anti-double-counting is structural, not a fudge factor: RSI and MACD share one
10-point bucket so two views of the same momentum cannot pay twice; EMA gets 3
regardless of how many of its lines agree; Fibonacci can earn at most 2, and
only where it coincides with a level that already mattered; and the delta
bucket scores **direction** while the volume bucket scores **effort vs result**,
so the same observation cannot be sold twice.

**Bands:** 90–100 A+ · 85–89 A · 75–84 WATCH · 65–74 WEAK · below 65 NO TRADE.

**A 90 means 90 points of confluence. It is not a 90% win rate.** The dashboard
shows a separate `HISTORY` row — the proportion of this script's own signals on
the loaded bars that reached TP1 before the stop — and it refuses to show a
percentage until 25 have resolved, because a rate from a handful of trades is
noise. Even then it is in-sample and describes loaded history, not the future.

---

## 8. Stop loss and targets

**Stop** sits beyond what invalidates the thesis — the swept extreme or spring
low for a reversal, the pullback's own higher low for a continuation — plus an
ATR buffer, floored at `slFloorAtr × ATR` and padded for spread. The floor
exists because gold noise on 5m routinely covers half an ATR.

**Targets** come from a ladder of real levels, in the brief's order: ranked S/R
zones, liquidity pools, previous-day extremes, 15M and 1H extremes, the Asian
range, the far edge of a live supply/demand zone, the value-area boundary, and
the Wyckoff range boundary. TP1 is the nearest beyond the spread minimum, TP2
the next, both placed just in front of the level.

The R:R is then **whatever the geometry produced**. Below `minRR` the trade is
rejected. A target sitting beyond the opposing liquidity pool is rejected too —
the path there is not clean. The stop is never moved to manufacture a ratio.

---

## 9. What is OBSERVED and what is INFERRED

| Module | Status |
|---|---|
| OHLC, volume, structure, S/R, liquidity levels, Wyckoff geometry, every indicator | **OBSERVABLE** |
| Estimated delta | **INFERRED** — labelled `EST. DELTA` with its source |
| Order flow / buying and selling pressure | **INFERRED** — labelled `[PROXY]` |
| Absorption | **INFERRED** — from volume, range and estimated delta |

**Estimated delta** signs each lower-timeframe bar's volume by whether that
intrabar closed up or down and sums them. On a 5m chart with 1m intrabars that
is five samples. It is a defensible estimate of net pressure. It is **not**
true bid/ask delta: it misreads a bar that reverses inside an intrabar, and
when the lower timeframe is unavailable (too far back in history, or a feed
without it) it falls back to signing the bar's own volume by where it closed in
its range. The dashboard says which method produced the number.

Pine cannot see the global XAUUSD order book, every institutional order, hidden
liquidity, OTC transactions, or true centralised spot-gold bid/ask volume.
Nothing in this script pretends otherwise.

---

## 10. Volume profile

A real session profile, not a fabrication. Each closed bar's volume is added to
a fixed-height price bin; the heaviest bin is the POC; the value area grows
outward from it, always taking the heavier neighbour, until it holds `vpVA`% of
the session's volume. Bin height is frozen at session start so bins stay
comparable when the range expands, and the map is cleared each day.

Limits worth knowing: it is a **session** profile, not a fixed-range or visible-
range one; it uses `hlc3` as each bar's price rather than distributing volume
across the bar's range; and on a feed without volume it is meaningless. POC,
VAH and VAL feed the location tests and the target ladder.

---

## 11. Non-repainting

| Check | Result |
|---|---|
| Signals on unclosed bars | none — every transition is gated on `barstate.isconfirmed` |
| Confirmation candle | must be a **later** bar (`bar_index > stBar`) |
| `request.security` | 6 calls, all `expr[1]` with `lookahead = barmerge.lookahead_off` |
| Historical labels moved after the fact | none; the only live-only drawing is the TP-developing marker, which is deleted and redrawn on the last bar and never written to history |
| Unconfirmed pivots treated as confirmed | no — `ta.pivothigh/pivotlow` with the lag accounted for |
| `ta.*` inside conditional branches | none (checked, including multi-line ternaries) |
| Drawing objects | pooled and capped: 70 labels, 24 lines, 4 reused boxes |
| Compiler tokens | ~85,200 of 100,256 |

**On `lookahead_off`:** the brief asks for it, and this uses it — but the `[1]`
is what actually makes it safe. `lookahead_off` on its own still lets the
developing HTF bar update intrabar, so history and real time would disagree.
`expr[1]` + `lookahead_off` returns the last **closed** bar of that timeframe
and is identical live and historically, at the cost of up to one HTF bar of
extra lag. That is the correct trade for a brief that says reliability over
pretty signals.

---

## 12. Known limitations

1. **Volume is tick volume** on retail XAUUSD feeds — price updates, not
   contracts. Everything downstream of volume is directional evidence, not
   measurement.
2. **Estimated delta is an estimate.** See §9.
3. **No news awareness.** Pine has no economic calendar. The dashboard reports
   `NEWS: UNVERIFIED` permanently; the blackout window is yours to set.
4. **Wyckoff phase is approximate** and returns `UNCERTAIN` often. That is the
   honest answer, not a defect.
5. **The cause-and-effect objective is a projection**, shown as context and
   never used to size a stop or a target.
6. **Pivot lag** — a confirmed pivot needs `pivIn`/`pivEx` bars after the fact.
   That is the price of not repainting.
7. **Lower-timeframe data has history limits.** Far enough back, the delta
   engine falls back to its cruder proxy. The dashboard says when.
8. **`HISTORY` is in-sample** and describes loaded bars only.
9. **Not backtested.** This is an indicator, not a strategy — it produces no
   Strategy Tester report. Its expectancy on XAUUSD is unknown until you run it
   forward on a demo account. Nothing here establishes that it is profitable,
   and nothing claims it.
10. **Spread is an assumption** you supply. Gold spreads widen violently around
    news and at rollover.
11. **One setup at a time**, by design.

---

## 13. Installing

1. TradingView → Pine Editor → **Open** → **New indicator**.
2. Clear the tab completely (`Ctrl+A`, `Delete`) — `Ctrl+F` for `//@version=6`
   should show **1 match**. Two scripts in one tab produces `CE10243`.
3. Paste `xau_5m_scalper.pine`, **Save**, **Add to chart**.
4. Open an **XAUUSD 5-minute** chart.
5. Gear icon → set **Your typical spread (pips)** to your broker's actual value
   before trusting any position size shown.

## 14. Configuring alerts

Right-click the chart → **Add alert** → Condition: **XAU 5M Scalper**.

- For the full formatted message, choose **Any alert() function call** and set
  **Once Per Bar Close**.
- For individual events, pick a named condition: `BUY confirmed`,
  `SELL confirmed`, `Wait for confirmation`, `Setup cancelled`, `TP1 hit`,
  `TP2 hit`, `Cancel trade`, `TP developing`, `Move SL to break-even`,
  `High confluence`, `Wyckoff spring / upthrust`, `Liquidity sweep`.

`Alert sensitivity` in the settings controls how much reaches you:
`Confirmed only` · `Confirmed + waiting` (default) · `Everything`.

Alerts fire on **state transitions**, never per bar, so the same setup cannot
spam you.

---

## 15. Recommended settings — XAUUSD 5M

Defaults are already tuned for this. What is worth changing:

| Input | Default | Note |
|---|---|---|
| Spread (pips) | 2.5 | **set this yourself** — everything downstream depends on it |
| Minimum confluence | 85 | 90 for A+ only, and expect very few |
| Confirmation strictness | Strict | Loose relaxes Wyckoff only, never the sequence |
| Sequence steps required | 7 of 10 | 8 makes it considerably rarer |
| Stop floor (× ATR) | 0.8 | lower and gold noise takes you out |
| Time stop | 36 bars | three hours on 5m |
| Risk per trade | 1.5% | on $60 that is $0.90 |
| Lower timeframe for delta | 1 | five samples per 5m bar |

Expect **a small number of signals per session, and many sessions with none.**
That is the intended behaviour: the brief asks for quality over frequency, and
an engine that refuses most of the day is doing its job.
