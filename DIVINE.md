# Divine XAUUSD Scalper — manual

Fifth engine, separate file. No trading logic shared with the other four —
only UI conventions and Pine techniques.

---

## 1. How six engines fit in one script

The brief asks for six genuinely independent timeframe engines. The honest way
to build that is **one engine function run six times**, not six copies of the
same code:

```pine
tfEngine() => ... complete analysis ...

[c1, s1, l1, ...] = request.security(sym, "60", tfEngine(), lookahead_off)
[c2, s2, l2, ...] = request.security(sym, "30", tfEngine(), lookahead_off)
... six in total
```

Every `var` inside `tfEngine()` becomes **separate persistent state per call
site**. The 1H instance tracks its own pivots, its own swing highs, its own
Wyckoff range, its own POI, its own delta — from 1H bars. The 5M instance does
the same from 5M bars. They never see each other. This is not 1H analysis
copied down; it is the same *method* applied six times to six different series,
which is what the brief actually asks for.

Writing it out six times would be six times the source for identical behaviour
and would blow the compiler token budget for nothing.

**Why it fits:** Pine allows 40 `request.security` calls. This uses 13 (six
engines, the daily levels, and the intrabar delta). Each engine packs its
boolean findings into integers so one call carries everything:

```pine
structB = (hh?1:0) + (hl?2:0) + (lh?4:0) + ... + (mssDn?512:0)
```

and the main script unpacks with `bit(v, B_MSSDN)`. Same information, a
fraction of the call budget.

---

## 2. What each engine computes, independently

Structure at two resolutions (internal swings and external swings, kept
separate so a small fluctuation cannot fake a major BOS) · HH/HL/LH/LL · BOS ·
CHoCH · MSS · failed break and failed breakdown · displacement · compression ·
expansion · trend classified in 7 states from structure, slope, displacement
and swing progression — never from an EMA crossover alone · market regime
(normal / compression / expansion / transition / exhaustion / extreme
volatility) · S/R from external swings · supply and demand at displacement
origins with freshness · liquidity pools, equal highs and lows, sweeps that
hold · a POI with quality scored 0–100 · mitigation in 7 states · a Wyckoff
range with Spring, Upthrust, tests, SOS/SOW, LPS/LPSY and phases A–E ·
effort-vs-result · estimated delta with divergence · RSI, MACD, EMA and
Bollinger · ATR · Fibonacci anchored to the external leg · and its own 0–100
score.

The dashboard shows all six rows so their independence is **visible**, not just
claimed — hover any timeframe's name cell for that engine's own ATR, regime and
score.

---

## 3. The MTF confluence layer

The six results are **not overwritten**. They stay intact and are compared:

| TF | Role | Weight |
|---|---|---|
| 1H | major context — who has the structural advantage | 22 |
| 30M | is the 1H thesis supported or weakening | 16 |
| 15M | directional bias now | 20 |
| **5M** | **where the setup lives** | 24 |
| 3M | is the 5M setup behaving correctly | 10 |
| 1M | has the trigger appeared | 8 |

Alignment is also **counted**, not inferred from the weighted average:
`minAlign` engines must actually agree.

---

## 4. The workflow, and why 1M cannot invent a trade

```
1H context → 30M confirm → 15M bias → 5M SETUP → 3M confirm → 1M trigger → CLOSE
```

State machine: `IDLE → SETUP DEVELOPING → WAIT FOR 1M CONFIRMATION → ACTIVE`.

The first transition requires a **5M setup**. With no 5M setup there is no
state 1, so no 3M confirmation and no 1M trigger can produce anything. The 1M
engine is an execution engine by construction.

A 5M setup means, on the 5M engine's own bars: a POI of sufficient quality,
**mitigated** (rejected or retested — not accepted, not failed), liquidity
swept and still holding, and a structure shift. Continuation is classified
separately and needs the trend and a controlled return instead of a sweep.

The final entry needs `bar_index > stBar` — the confirmation candle is always a
**later, closed** bar than the one that put the setup into waiting.

---

## 5. Take profit vs cancellation

Different events, checked in that order.

- **TP developing** (intrabar) → `TP DEVELOPING — WAIT FOR CANDLE CLOSE`, drawn
  only on the live bar, never written into history.
- **TP confirmed** (on close) → `TP — TAKE PROFIT WHEN THIS CANDLE CLOSES`,
  once per level.
- **Cancellation** → `CANCEL LONG / CANCEL SHORT — TRADE THESIS INVALID`, with
  the reason: protected level broken, structural stop taken, 5M thesis
  invalidated, or strong opposing displacement.

The protected level carries a noise buffer, so a one-tick poke through it is
not treated as invalidation. Break-even is suggested only after TP1 is reached
**and** 5M structure has not broken against the trade.

---

## 6. Scoring

Two separate scores, as the brief requires. Each timeframe scores itself 0–100
from its own evidence. The MTF score is built from context, alignment, the 5M
setup, POI quality, mitigation, liquidity, Wyckoff, flow, 3M confirmation, 1M
trigger, volatility and geometry.

Correlated evidence shares a bucket: the order-flow proxy and estimated delta
come from the same observation, so they score once; the six per-timeframe
scores already contain their own momentum and volume, so those are not re-added
at the MTF level.

**90–100 A+ · 85–89 A · 75–84 B watch · 65–74 weak · below 65 no trade.**

A 90 means exceptional technical agreement. **It is not a 90% win probability.**
The `HISTORY` row is a separate number — this script's own signals on the
loaded bars that reached TP1 before the stop — and it refuses to show a
percentage below 25 resolved trades.

---

## 7. Observable vs inferred

| | |
|---|---|
| **OBSERVABLE** | OHLC, TradingView volume, time, ATR, RSI, MACD, EMA, Bollinger, and every structure, level, zone and Wyckoff event computed from them |
| **INFERRED** | buying and selling pressure, absorption, estimated delta, footprint-style imbalance |

Inferred readings are worded as such: *"consistent with possible buying
absorption"*, never *"institutions are buying"*. The dashboard column is
labelled `EST. DELTA [inferred]` and the order-flow readout `[PROXY]`.

**Estimated delta** on the chart timeframe signs each 1-minute intrabar's
volume by that intrabar's own close, via `request.security_lower_tf`. The six
nested engines use the close-position proxy instead.

*Correction:* an earlier version of this note said `request.security_lower_tf`
**cannot** be nested inside `request.security`. That was wrong — Pine v6 permits
nested requests, and a nested call inherits the outer call's context. The real
reasons the engines use the proxy are cost (six nested intrabar requests on top
of six engines) and the 127-element cap that all `request.*()` tuples share.
The dashboard says which method produced the number.

Pine cannot see the global XAUUSD order book, hidden liquidity, OTC flow or
true bid/ask volume. Nothing here pretends otherwise.

---

## 8. Anti-repainting

| Check | Result |
|---|---|
| HTF reads | `expr[1]` with `lookahead_off` on every value the engines return |
| Why the `[1]` matters | `lookahead_off` alone still lets a forming HTF bar update intrabar; the `[1]` returns the last **closed** bar of that timeframe |
| Timeframes below the chart | **excluded**, not faked — requesting them would leak information from inside the current bar, so those engines report `n/a` and drop out of the alignment count |
| Pivots | confirmed pivots only, their lag accounted for |
| Final entry | requires `barstate.isconfirmed` **and** a bar later than the trigger |
| Historical labels | never moved; the only live-only drawing is the TP-developing notice, deleted and redrawn on the last bar |
| `ta.*` in ternary branches | none — checked including multi-line ternaries |
| Security calls | 13 of the 40 allowed |
| Tokens | ~78,300 of 100,256 |

---

## 9. Known limitations

1. **Volume is tick volume** on retail XAUUSD feeds — price updates, not
   contracts.
2. **Estimated delta is an estimate**, and the nested engines use the cruder of
   the two available methods. See §7.
3. **No news data.** Pine has no economic calendar. `HIGH IMPACT NEWS MODE` is
   a manual toggle with a window you set; the dashboard otherwise reads
   `NEWS: UNVERIFIED`.
4. **Volume Profile is not implemented here.** A per-timeframe POC/VAH/VAL
   would need a price-binned map per engine, and a map cannot be maintained
   inside a function called through `request.security`. Rather than fabricate
   it, it is left out — the target ladder uses real swing, session and
   previous-day levels instead. (`xau_5m_scalper.pine` has a genuine
   session volume profile, on the chart timeframe only.)
5. **Wyckoff phases are approximate** and often report nothing. That is the
   honest answer.
6. **Pivot lag** — `pivIn`/`pivEx` bars. The cost of not repainting.
7. **Six nested engines are computationally heavy.** If TradingView reports a
   calculation-time error, raise the pivot lengths or disable a module.
8. **`HISTORY` is in-sample** and describes loaded bars only.
9. **Not backtested.** This is an indicator, not a strategy. Its expectancy on
   XAUUSD is unknown until you forward-test it. Nothing here establishes that
   it is profitable and nothing claims it.
10. **Spread is an assumption you supply.**

---

## 10. Installing and alerts

Pine Editor → **Open** → **New indicator** → clear the tab (`Ctrl+F` for
`//@version=6` should show **1 match**) → paste → Save → Add to chart.

Use a **1M–5M** XAUUSD chart: this is the execution layer and the higher
timeframes come from the engines. Set **Your typical spread (pips)** to your
broker's real value before trusting any size shown.

Alerts fire on state transitions, never per bar: `BUY confirmed`,
`SELL confirmed`, `5M setup developing`, `Wait for 1M confirmation`,
`TP1 — take profit`, `TP2 — take profit`, `TP developing`, `Cancel trade`,
`Move SL to break-even`, `Setup cancelled`, `Missed entry`,
`Extreme volatility`. For the full formatted message use **Any alert() function
call** with **Once Per Bar Close**.

Expect very few signals. Six engines have to agree, a 5M setup has to exist,
3M has to confirm, 1M has to trigger, and a candle has to close. Most of the
time the correct output is WAIT.
