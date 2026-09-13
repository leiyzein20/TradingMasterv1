# XAU Scalper — manual

Companion to [`ARCHITECTURE.md`](ARCHITECTURE.md), which covers the design and
how the modules talk to each other. This covers what the thing actually does
and what it cannot do.

---

## 1. Signal logic in one paragraph

A **thesis** is proposed only where the methodology allows one: a meaningful
location plus a liquidity event (reversal), or an established trend with a real
displacement leg and a controlled pullback into it (continuation). The thesis
is then walked down the priority chain. Layers 1–6 are structural and any one
of them contradicting ends it. Layers 7–10 corroborate and can only cost
points. If the chain survives, the score is computed and the hard blockers are
checked. Only then does the state machine allow a *closed* confirmation candle
to promote the setup to a signal.

Nothing skips a stage, and the score is never consulted before the chain.

---

## 2. BUY conditions

Every one of these, in order:

| | Condition |
|---|---|
| 1 | Chart ≤ 15m, symbol is gold, not in a news blackout, ATR above the minimum, inside London or New York, regime not `Transition` or `Range (compressed)` |
| 2 | **Thesis proposed** — reversal: at support/demand (or the range low in a clean range) **and** sell-side liquidity was swept or a bearish BOS failed. Continuation: 15M bullish, trending regime, recent bullish displacement, 15–66% retrace, weak counter-selling, a higher low, not chasing |
| 3 | **Chain intact** — no contradiction in layers 1–6 and at least `minStruct` of them confirming |
| 4 | **Reversal against a trend** additionally needs a validated Wyckoff event (Strict/Normal) |
| 5 | Location layer confirms, structure layer confirms |
| 6 | Not chasing (< `maxExtAtr` from EMA20) |
| 7 | Stop is at least `stopFloorAtr` × ATR — wide enough to survive normal gold noise |
| 8 | TP1 is further away than spread × `minTpSpread` |
| 9 | R:R to TP2 ≥ `minRR` |
| 10 | Position size fits the account at the broker minimum lot |
| 11 | Confluence ≥ `minScore` |
| 12 | State machine is at `WAITING CONFIRMATION`, and on a **later** bar a bullish candle **closes** above the trigger level with the chain still intact |
| 13 | Cooldown elapsed |

**SELL** is the exact mirror. There is no asymmetry anywhere in the code.

---

## 3. WAIT vs NO TRADE

Two different statements, and mixing them up is what makes indicators useless.

- 🟡 **WAIT FOR CONFIRMATION** — a setup exists and is at stage `WAITING
  CONFIRMATION`. The dashboard says exactly what the confirmation candle has to
  do, and at what price. **There is no trade yet.**
- ⚪ **WAIT** — a thesis is forming (`WATCHING` or `SETUP`), or the evidence is
  merely incomplete. Something may develop.
- ⚫ **NO TRADE** — the conditions themselves are wrong: dead volatility, a news
  window, a squeeze, layers in conflict, no target space, or a score below 65.
  Waiting will not fix these; they have to change.

The dashboard's `WHY` row always names the single thing currently stopping the
trade, in the order it was checked.

---

## 4. The confirmation candle

This is the part the instruction file calls critical, so it is worth being
precise about.

```pine
canConfirm = confirmed and stState == 3 and bar_index > stBar and ...
```

Three things matter in that line:

- `confirmed` is `barstate.isconfirmed` — the bar has closed.
- `bar_index > stBar` — the confirmation candle is a **different, later** candle
  than the one that shifted structure. A setup cannot confirm itself on the bar
  it was created.
- the close must be beyond `stTrigger`, the level recorded when structure
  shifted — not merely green, and not merely higher than the open.

If it closes the other way, or `confirmWin` bars pass without one, the setup is
`INVALIDATED` and says so out loud. A stale signal left on the screen is worse
than no signal.

---

## 5. The confluence score

Computed **last**, only for a thesis that already survived the chain. Weights
are the instruction file's:

| Bucket | Full | Silent |
|---|---|---|
| HTF context | 15 | 6 |
| Market structure | 15 | 5 |
| Location + secondary confluence | 7 + 3 | 2 + 1 |
| Liquidity | 10 | 2 |
| Wyckoff | 10 | **4** |
| Price action | 10 | 3 |
| Momentum (RSI **and** MACD together) | 10 | 4 |
| Volume / effort-result | 5 | 2 |
| EMA | 5 | 2 |
| Volatility / ATR | 5 | — |
| R:R + target space | 5 | — |

Two deliberate choices:

**Wyckoff silence scores 4, not 0.** No Wyckoff reading is not a reading
against. A Wyckoff *contradiction* already killed the thesis upstream, so by the
time scoring happens, silence genuinely means "nothing to say".

**Anti-double-counting is structural, not a fudge factor.** RSI and MACD share a
single verdict inside `verdict(8, …)`, so two views of the same momentum cannot
be counted twice. EMA gets one 5-point bucket regardless of how many of its
lines agree. Fibonacci can only ever earn 3 points, and only when it coincides
with a level that already mattered.

**Bands:** 90+ A+ · 85–89 A · 75–84 watch · 65–74 weak · below 65 no trade.
The default `minScore` is 85.

---

## 6. Score is not a win rate

The dashboard shows two separate rows and they are never combined:

```
CONFLUENCE   92/100   ·   A+  extreme confluence
HISTORY      insufficient sample — 11 closed of 13 fired, need 30
```

`CONFLUENCE` is how much independent evidence agrees right now. **92/100 does
not mean 92% of these win.** It is not a probability of anything.

`HISTORY` is the proportion of this script's own signals, on the bars currently
loaded, where TP1 was reached before the stop. Below `minSample` it refuses to
show a percentage, because a rate computed from nine trades is noise. Even
above it, the figure is in-sample and describes loaded history, not the future.

---

## 7. Stop loss and targets

**Stop** sits beyond the price that invalidates the thesis:

- reversal → beyond the swept extreme or the spring low
- continuation → beyond the higher low / lower high the pullback made

then floored at `stopFloorAtr` × ATR and padded by 1.5 × spread. The floor
exists because a stop tighter than ordinary XAUUSD noise is not a stop.

**Targets** come from a ladder of real levels: ranked S/R, liquidity pools,
previous-day extremes, 15M extremes, the Asian range, the far edge of a live
zone, and the Wyckoff range boundary. TP1 is the nearest one beyond the spread
minimum; TP2 is the next. Both sit *just in front of* the level, because the
queue at an obvious price is long. TP3 uses the Wyckoff cause-and-effect
objective when one exists.

The R:R is then **whatever the geometry produced**. If it is below `minRR` the
trade is rejected. The stop is never moved to manufacture a ratio — a stop
placed to flatter a number has stopped being an invalidation level.

---

## 8. Alerts

Nine conditions, all fired on **state transitions** rather than per bar, which
is what the state machine is for:

BUY confirmed · SELL confirmed · Wait for confirmation · Setup invalidated ·
TP1 · TP2 · Stop hit · High confluence (90+) detected · Wyckoff spring/upthrust

`Alert sensitivity` controls which reach you: `Confirmed only` (default),
`Confirmed + waiting`, or `Everything`. Set the TradingView alert to **Once Per
Bar Close**.

---

## 9. Repainting and lookahead audit

| Check | Result |
|---|---|
| Signals on unconfirmed bars | None. Every transition is gated on `barstate.isconfirmed` |
| `request.security` form | `expr[1]` + `lookahead_on` — returns the last **closed** HTF bar, identical live and historically |
| HTF calls | 3 (15M, 3M, 1D) |
| Future references | None. No negative offsets, no `security` without `[1]` |
| Pivots | `ta.pivothigh/pivotlow` are confirmed pivots; every use accounts for the `pivLen` lag |
| `ta.*` in conditional branches | None — the audit checks for this specifically, and caught one during the build |
| Drawing objects | Capped: 80 labels, 20 lines, 2 boxes reused rather than recreated |
| Compiler tokens | ~74,500 of 100,256 |

**On `lookahead_on`:** the instruction file says do not use lookahead, and that
deserves a direct answer rather than silence. `expr[1]` with `lookahead_on` is
the *correct non-repainting idiom*. It returns the previous, fully closed
higher-timeframe bar. The repainting form is `lookahead_on` **without** the
`[1]`, which hands you the in-progress bar. Omitting lookahead entirely also
repaints, because the developing HTF bar updates on every chart tick. The
intent of §28 — signals must not change after close — is met.

---

## 10. Known limitations

Stated plainly, because the alternative is you discovering them with money on.

1. **Volume is tick volume.** On XAUUSD from a retail feed, "volume" counts
   price updates, not contracts. Effort-vs-result readings are therefore
   directional evidence, not measurements. On a feed with no volume at all the
   volume layer abstains rather than guessing.
2. **No news awareness.** Pine has no economic calendar. The dashboard says
   `NEWS: UNVERIFIED` permanently and the only filter is a window you type in.
3. **"Absorption", "liquidity", "institutional" are inferences** from price,
   range and volume. There is no order book anywhere in this.
4. **Wyckoff phase classification is approximate.** It returns `UNCERTAIN`
   often, and that is the honest answer rather than a defect.
5. **The cause-and-effect objective is a projection**, an approximation of
   point-and-figure counting. It is never used to size a stop or a TP1/TP2.
6. **Pivot lag.** A confirmed pivot needs `pivLen` bars after the fact. This is
   the price of not repainting.
7. **In-sample history.** The `HISTORY` row describes loaded bars only.
8. **Not backtested here.** This is an indicator, not a strategy — it produces
   no TradingView Strategy Tester report. Until you run it forward on a demo
   account, its expectancy on XAUUSD is unknown. Nothing in this repository
   establishes that it is profitable, and nothing claims it.
9. **Spread and slippage are assumptions.** The `spreadPips` input is yours to
   set correctly. Gold spreads widen violently around news and at rollover.
10. **One trade at a time**, by design for a small account.

---

## 11. Recommended settings — XAUUSD 1M / 3M / 15M

The defaults are already tuned for this. What is worth changing:

| Input | 1M chart | 3M chart | Why |
|---|---|---|---|
| Context / Setup TF | 15 / 3 | 15 / 5 | keep roughly a 5× step between layers |
| Swing pivot length | 3 | 3 | |
| Major pivot length | 6 | 5 | |
| Minimum confluence | 85 | 85 | 90 if you want A+ only, and expect very few |
| Confirmation strictness | Strict | Strict | Loose only relaxes the Wyckoff requirement, never the chain |
| Spread (pips) | **set this yourself** | | 2.0–3.5 typical; wrong here means every size is wrong |
| Stop floor (× ATR) | 0.7 | 0.7 | lower and gold noise takes you out |
| Time stop (bars) | 40 | 25 | roughly 40 min either way |
| Risk per trade | 1.5% | 1.5% | on $60 that is $0.90 |

**Check the Size row on the dashboard against your broker before trading.** The
engine assumes 1 lot = 100 oz and 1 pip = $10/lot. If your broker differs, every
size shown is wrong.

A realistic expectation at these settings: **a small number of signals per
session, and many sessions with none.** That is the intended behaviour. The
instruction file asks for quality over frequency, and an engine that produces
two setups a day and refuses the rest is doing its job.
