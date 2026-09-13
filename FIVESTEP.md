# XAU 5-Step — manual

Built from the five-step framework brief. A **fourth, separate engine**. No
trading logic is shared with `xau_5m_scalper.pine`, `xau_scalper.pine` or
`scalper_pro.pine` — only UI conventions and Pine techniques.

---

## What makes this one different

The previous engine counted a ten-step sequence: steps could be satisfied in
any order and the total decided whether to act. **This one is a pipeline.** The
five steps are states, each enterable only from the one before it:

```
IDLE → BIAS → POI IDENTIFIED → WAITING FOR MITIGATION → MITIGATED →
WAITING FOR LIQUIDITY SWEEP → LIQUIDITY SWEPT → WAITING FOR MSS →
WAITING FOR CONFIRMATION CANDLE → ACTIVE → TP / CANCELLED → RESET
```

That ordering is the brief's "do not skip steps" rule expressed as code rather
than as a comment:

- a liquidity sweep with **no mitigated POI** never reaches `LIQUIDITY SWEPT`
- an MSS with **no sweep** never reaches `WAITING FOR MSS`
- a confirmation candle with **no MSS** is ignored entirely
- no confluence score can move the pipeline forward a single state

The score exists only to **rank setups that already passed all five steps**.

---

## Step 1 — trend direction

1H for major context, 15M for intraday structure, 5M for execution. The
brief's primary rule is enforced: **when 1H and 15M disagree, the output is
WAIT**, and `Require 1H and 15M to agree` is on by default. The regime read
distinguishes trending, weak, range, transition and conflicting-timeframes.

5M structure is tracked at two resolutions — external (the swing skeleton) and
internal (the detail inside it) — because a reversal breaks internal structure
long before external structure turns. Trend strength and exhaustion are both
reported.

## Step 2 — liquidity and points of interest

POIs are marked **before** any entry is considered, as objects with a life:

```pine
type Poi
    float top / bot      int bar        int dir
    string kind          int quality    int state
    float deepest        int touches
```

Sources: displacement origins (demand/supply), confirmed external swings,
previous-day extremes, equal highs and lows.

**Quality (1–6)** counts how many *independent* things overlap the zone —
previous-day level, 1H extreme, 15M extreme, session level, Wyckoff range
boundary, Fibonacci. A zone that is only a swing low is a swing low. A zone
that is a swing low, yesterday's low, the range floor and the 0.618 is a point
of interest. `minQuality` gates which are tradable.

Zones merge by proximity rather than accumulating — marking the same price ten
times is not ten points of interest.

**On language:** the dashboard says *likely* sell-side liquidity and *potential
stop cluster*, never "the stops are at". Pine sees price and volume. It does
not see anyone's orders.

## Step 3 — mitigation

Approaching a POI is not mitigation. The engine distinguishes all seven
interactions the brief names:

| Reading | Meaning |
|---|---|
| first touch | price reached the zone for the first time |
| retest | a later touch after leaving |
| deeper mitigation | penetrated further than before, still holding |
| rejection | touched and closed back out with a wick |
| **acceptance** | closed *inside* the zone for `acceptBars` bars |
| penetration | closed beyond the far edge |
| **failed** | the zone is no longer valid |

Acceptance is the important one: price **sitting** in a zone rather than being
pushed out of it means the zone is being absorbed, not defended. That kills the
POI and resets the pipeline — which is the brief's "a POI is not automatically
valid simply because it was previously respected".

## Step 4 — the liquidity sweep entry model

The sweep is the trigger, and it only counts *after* a mitigated POI. A sweep
is: through the level, then **closed back inside**. A close beyond it is a
break, which is the opposite.

Then, in order: the sweep must be **rejected rather than extended** → structure
must shift (MSS/CHoCH) → a **later** candle must close in the direction.

`bar_index > mssBar` is the whole of the non-repainting requirement for
entries: the confirmation candle can never be the bar that produced the MSS.

**Reversal vs continuation** is classified, not blurred: a setup against the
prevailing 5M trend is a REVERSAL, one aligned with it is a CONTINUATION.

## Step 5 — protected level, stop and targets

This is the part most worth understanding.

> **The sweep extreme is only a CANDIDATE protected level.**

It becomes *the* protected low/high — and therefore the stop — only after the
market has actually rejected the liquidity area **and** structure has shifted.
The first wick is not protection. The dashboard shows the distinction
explicitly: `4123.40 · candidate only` versus `4123.40 ✓ confirmed`, and a
setup cannot confirm while it is still a candidate.

**Stop**: beyond the protected level, plus an ATR buffer, floored at
`slFloorAtr × ATR` and padded for spread.

**Targets**: a ladder of real opposing levels in the brief's priority order —
liquidity pools, major swings, 15M and 1H extremes, session extremes,
previous-day extremes, the Wyckoff range boundary. TP1 is the nearest beyond
the spread minimum, TP2 the next.

The R:R is then **whatever the geometry produced**. Below `minRR` the setup is
rejected. The stop is never moved closer to manufacture a ratio.

---

## Confluence score

Weighted by the Step 4A hierarchy — context and structure outrank order flow,
which outranks momentum, which outranks EMA:

| | Weight |
|---|---|
| 1H context | 12 |
| 15M structure | 12 |
| POI quality | 12 |
| Liquidity location | 8 |
| Liquidity sweep | 10 |
| MSS | 10 |
| Displacement | 8 |
| Wyckoff | 6 |
| Volume / effort-result | 5 |
| Order-flow proxy **+** estimated delta (one bucket) | 6 |
| RSI **+** MACD (one bucket) | 5 |
| EMA | 2 |
| R:R + target space | 4 |

Correlated evidence shares a bucket: the footprint proxy and estimated delta
come from the same lower-timeframe data, and RSI and MACD are both momentum.
Counting them separately would be selling the same observation twice.

**90+ A+ · 85–89 A · 75–84 watch · 65–74 weak · below 65 no trade.**

A 90 means 90 points of confluence. **It is not a 90% win rate.** The `HISTORY`
row is a separate number — the share of this script's own signals on the loaded
bars that reached TP1 before the stop — and it refuses to show a percentage
until 25 have resolved.

---

## Take profit vs cancellation

Different events, checked in that order:

- **TP developing** (intrabar) → `TP DEVELOPING — WAIT FOR CANDLE CLOSE`,
  drawn only on the live bar and never written into history, because an
  intrabar touch is not a fact until the candle closes.
- **TP confirmed** (on close) → `TP — TAKE PROFIT WHEN THIS CANDLE CLOSES`,
  once per level.
- **Cancellation** → `CANCEL LONG / CANCEL SHORT — TRADE THESIS INVALID`, with
  the reason: *protected low broken*, *protected high broken*, *structural stop
  taken*, or *bearish MSS against the long*.

A trade pulling back is not a cancellation. An indicator changing colour is
not a cancellation. **The protected level breaking is**, because that level is
the entire basis of the trade.

Break-even is suggested only once TP1 is genuinely reached.

---

## Known limitations

1. **Volume is tick volume** on retail XAUUSD feeds — price updates, not
   contracts. Everything downstream is directional evidence, not measurement.
2. **Estimated delta is inferred**, from lower-timeframe closes, with a
   close-position fallback when intrabar data is unavailable. It is not tape.
3. **No news awareness.** Pine has no economic calendar.
4. **Pivot lag** — confirmed pivots need `pivIn`/`pivEx` bars. That is the cost
   of not repainting.
5. **A very strong bar can advance several states at once.** Each state is
   still evaluated and required; they are not skipped. Only the final
   confirmation is forced onto a later bar, which is where it matters.
6. **POI quality is a count of overlaps**, not a measure of how well a zone has
   held in the past.
7. **`HISTORY` is in-sample** and describes loaded bars only.
8. **Not backtested.** This is an indicator, not a strategy. Its expectancy on
   XAUUSD is unknown until you forward-test it. Nothing here establishes that
   it is profitable and nothing claims it.
9. **Spread is an assumption you supply.**

---

## Installing and alerts

Pine Editor → **Open** → **New indicator** → clear the tab (`Ctrl+F` for
`//@version=6` should show **1 match**) → paste → Save → Add to chart. Open an
**XAUUSD 5-minute** chart, then set **Your typical spread (pips)** to your
broker's real value before trusting any size shown.

Alerts fire on **state transitions**, never per bar: `BUY confirmed`,
`SELL confirmed`, `Wait for confirmation`, `POI mitigated`, `Liquidity swept`,
`TP1 — take profit`, `TP2 — take profit`, `TP developing`, `Cancel trade`,
`Move SL to break-even`, `Setup cancelled`. For the full formatted message use
**Any alert() function call** with **Once Per Bar Close**.

Expect **few signals**. The pipeline requires five things to happen in order,
and most days they do not.
