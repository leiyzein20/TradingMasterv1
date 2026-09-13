# XAU Scalper — architecture

Built from `Read_Instruction_Master_Scalping.txt`. This is a **new engine**, not
a revision of `scalper_pro.pine`. The only things carried across from the older
work are UI conventions: the colour palette, the dashboard table idiom, tooltip
style, input grouping, and the non-repainting `request.security` form. No
trading logic was reused (§ instruction file, lines 34–40).

---

## STEP 1 — The one structural decision

The instruction file is explicit twice:

> *"Indicators must CONFIRM each other, not vote independently."* (§3)
> *"Do not create RSI signal + MACD signal + EMA signal + Wyckoff signal and
> simply count them. Instead, determine whether they tell a coherent story."* (§50)

That rules out a scoring model where each component adds points to a total.
Counting is exactly what produces a 78/100 built from four things that
contradict each other.

So the engine is a **chain**, not a tally:

```
          ┌─────────────────────────────────────────────┐
          │  A thesis is PROPOSED, then walked down a    │
          │  chain. Any layer may kill it. The score is  │
          │  computed LAST, and only for a thesis that   │
          │  already survived the whole chain.           │
          └─────────────────────────────────────────────┘
```

A layer answers one of three things about the thesis in front of it:

| | Meaning |
|---|---|
| **SUPPORTS** | this layer's evidence points the same way |
| **SILENT** | this layer has nothing to say — *not* agreement |
| **CONTRADICTS** | this layer's evidence points the other way |

And the rule that makes it a chain rather than a vote:

> **A contradiction at a higher priority kills a thesis supported only by
> lower-priority layers.** An oscillator never overrules market structure.

Priority is the instruction file's own hierarchy (§57):

```
1 market structure      6 Wyckoff
2 HTF context           7 volume / effort-result
3 location              8 momentum
4 liquidity             9 EMA
5 price action         10 Bollinger / Fibonacci
```

Layers 1–6 are **structural**. A contradiction there ends the thesis. Layers
7–10 are **corroborating**: a contradiction costs points and can downgrade a
BUY to WAIT, but cannot by itself create a trade or destroy one.

---

## STEP 2 — How the modules talk to each other

```
                     ┌──────────────┐
   15M CONTEXT ─────▶│              │  regime, trend, major swings,
   (§4 context)      │   CONTEXT    │  ranges, HTF S/R, Wyckoff range
                     └──────┬───────┘
                            │ passes: bias, regime, range, levels
                            ▼
                     ┌──────────────┐
   3M SETUP ────────▶│    SETUP     │  BOS/CHoCH/MSS, sweeps, Wyckoff
   (§4 setup)        │              │  events, pullback, displacement
                     └──────┬───────┘
                            │ passes: a THESIS — direction + type
                            │         (REVERSAL or CONTINUATION)
                            ▼
                     ┌──────────────┐
                     │  COHERENCE   │  walks the §57 chain
                     │    CHAIN     │  → SUPPORTS / SILENT / CONTRADICTS
                     └──────┬───────┘
                            │ survives, or dies with a stated reason
                            ▼
                     ┌──────────────┐
                     │  RISK / R:R  │  SL from invalidation, TP from real
                     │              │  levels, reject if geometry fails
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
   1M EXECUTION ────▶│ CONFIRMATION │  state machine; a CLOSED candle
   (§4 execution)    │ STATE MACHINE│  promotes SETUP → CONFIRMED
                     └──────┬───────┘
                            ▼
                       FINAL DECISION
        🟢 BUY · 🔴 SELL · 🟡 WAIT FOR CONFIRMATION · ⚪ WAIT · ⚫ NO TRADE
```

Nothing skips a stage. The 1M chart cannot promote anything that the 15M
context stage refused to pass down (§4, line 202).

---

## The state machine (§41)

A setup is an object with a life, not a per-bar boolean. This is what stops
the same setup alerting on every candle, and what lets a setup be *cancelled*
rather than quietly disappearing (§40).

```
  IDLE
   │  location reached + liquidity event
   ▼
  WATCHING ──────────────┐
   │  rejection +        │
   │  effort/result      │  new extreme, or timeout
   ▼                     │
  SETUP ─────────────────┤
   │  structure shift    │
   │  (MSS/BOS on 3M)    │
   ▼                     │
  WAITING CONFIRMATION ──┤  confirmation candle closes the WRONG way,
   │  confirmation       │  or the sweep low/high is taken out on a close
   │  candle CLOSES      │
   ▼                     ▼
  CONFIRMED ───────▶  INVALIDATED ──▶ RESET ──▶ IDLE
   │
   ▼
  ACTIVE ──▶ TP1 / TP2 / SL / TIME ──▶ RESET ──▶ IDLE
```

Each transition fires exactly one alert. `INVALIDATED` is a first-class
outcome and is announced, because a stale signal left on screen is worse than
no signal.

---

## Score vs win rate (§2)

Two different numbers, kept apart on purpose and labelled differently on the
dashboard:

- **CONFLUENCE nn/100** — how much independent evidence agrees *right now*.
  It is not a probability. 92/100 does not mean 92% of these win.
- **HISTORY n=X** — the actual TP1-before-SL rate of signals this script
  produced on the bars currently loaded. Below the minimum sample it reports
  `insufficient sample`, because a rate computed from nine trades is noise.

The history figure is also in-sample and forward-looking only in the weakest
sense — it is what happened on the loaded chart, not a prediction. It is shown
because the instruction file asks for the distinction to exist, not because it
should be trusted as an edge.

---

## What Pine genuinely cannot do (§49)

Stated here so the terminology in the dashboard is not mistaken for data the
script does not have:

| Term used | What it actually is |
|---|---|
| "absorption" | volume expansion with a small range and a close back into the range — an *inference* from price and volume |
| "liquidity" | prices where stops are likely to rest: equal highs/lows, session and prior-day extremes |
| "effort vs result" | relative volume compared with realised range |
| volume | whatever the broker feed supplies — on XAUUSD this is normally **tick volume**, not centralised spot-gold volume |

There is no order book, no institutional positioning, no hidden liquidity and
no future information anywhere in this script.

---

## Non-repainting (§28, §48)

Every higher-timeframe read uses:

```pine
request.security(syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on)
```

This looks like it violates "do not use lookahead", so it needs saying
plainly: `expr[1]` + `lookahead_on` is the **correct non-repainting form**. It
returns the last *closed* higher-timeframe bar and is identical in history and
in real time. The dangerous form is `lookahead_on` *without* the `[1]`, which
hands you the in-progress bar and repaints. Omitting lookahead entirely also
repaints, because the developing HTF bar updates on every chart tick.

Every signal additionally requires `barstate.isconfirmed`, so nothing is
emitted from a bar that is still forming.
