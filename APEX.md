# XAUUSD Apex Scalper — manual

Sixth engine, separate file. No trading logic shared with the other five.

---

## 1. The money module — read this first

This is the part you asked for, and it is the part that decides whether a trade
is sane for your account. Settings group **01 ACCOUNT & RISK**.

### How much you risk — pick one

| Mode | You set | The engine works out |
|---|---|---|
| **Percent of balance** | balance + a % | the lot size |
| **Fixed dollars** | balance + a cash amount | the lot size |
| **Fixed lot size** | the lot | what that actually risks in dollars |

### What you want to make — pick one

| Mode | You set |
|---|---|
| **Risk:Reward ratio** | 1 : X (e.g. 1:2) |
| **Dollar target** | a cash amount (e.g. $2.00) |
| **Structure only** | nothing — take whatever the levels offer |

### What it gives you back

```
Lot size          0.02 lot
You are risking   $0.90 of $60.00   (1.5%)
Your target       1:2 → 4413.60     ✓ TP2 reaches it
Take profit 1     4410.50   1:1.56   ≈ $1.40
Take profit 2     4415.00   1:2.88   ≈ $2.59
```

Three things worth understanding:

**Lots are rounded DOWN to your broker's step.** Rounding up would risk more
than you said. If rounding moves your risk, the panel tells you: *"you asked
for $0.90, the lot step moved it"*.

**Targets are never moved to hit your goal.** They come from real levels. What
the engine does is tell you whether those levels can *reach* your goal — and if
they cannot, it refuses the trade with *"the real levels cannot reach your
1:2 target — skip it"*. Moving a target to flatter a ratio is how a plan stops
being a plan.

**If the smallest lot your broker allows already risks more than you set, that
is a hard refusal**, not a warning. On a $60 account with 0.01 minimum lot, a
stop wider than about 9 pips already risks more than 1.5%. The panel says so in
dollars.

---

## 2. What the main panel tells you

Plain English, because you need to know what to *do*:

```
XAUUSD SCALPER            🟢 BUY
What to do                Buy now — this candle has closed.
Setup                     Liquidity Sweep Reversal
Buy zone                  4405.00 – 4405.40
Entry                     4405.20
Stop loss                 4401.80   (34 pips)
Take profit 1             4410.50   1:1.56   ≈ $1.40
Take profit 2             4415.00   1:2.88   ≈ $2.59
Lot size                  0.02 lot
You are risking           $0.90 of $60.00   (1.5%)
Your target               1:2 → 4413.60   ✓ TP2 reaches it
Expected direction        UP · 15 min: upward, toward 4410.50
                          30 min: continuing to 4415.00 if 4410.50 breaks and holds
Confidence                91/100 — A+ exceptional
Why                       ✓ bigger picture agrees
                          ✓ price is at a level that matters
                          ✓ yesterday's low was swept and held
                          ✓ price reacted at the zone
                          ✓ structure turned up
                          ✓ a hammer confirmed it
                          ✓ the reward is worth the risk
Get out if                price closes beyond 4401.80
```

When there is no trade it says why in one line. When something is forming it
says what it is waiting for, what the entry *would* be, and what would cancel
it. The technical detail lives in a separate **Advanced** panel you can switch
off.

---

## 3. The 15 / 30 minute scenario engine

Not a prediction — a projection of how far gold typically travels in that time
*at the current volatility*, capped by the next real level in the way.

Distance scales with the **square root** of time, not linearly, because that is
how volatility actually accumulates. A linear multiple badly overstates the
30-minute move and would put targets where price rarely gets.

Every scenario comes with the alternative: *"a close below 4401.80 kills the
bullish idea and opens 4398.40"*. A path with no stated failure case is not
analysis.

---

## 4. How a trade is found

Context → location → liquidity → structure → Wyckoff → flow → momentum →
room → risk → a closed confirmation candle. In that order, and any one of them
can stop it.

- **Reversal** — price at a level that matters, liquidity swept and *held*, the
  move failing to continue, structure turning back. Fading a **trend** costs an
  extra piece of evidence (a Wyckoff event or a reclaim); fading a **range
  edge** does not, because the edge has already proved itself.
- **Continuation** — the trend, a real displacement leg, a controlled 15–66%
  pullback with weak counter-pressure, a higher low, and structure resuming.

Both need a **closed** candle on a bar *later* than the one that set up the
wait. That is the anti-repaint guarantee.

**Hard refusals** that no score can override: the middle of a range with
nothing to react against, 1H and 15M conflicting, a failed or accepted zone,
price already run too far (*MISSED ENTRY — WAIT FOR PULLBACK*), no room to the
target, R:R below your minimum, a lot size your account cannot carry, or the
levels being unable to reach your goal.

---

## 5. Score vs win rate — two different numbers

**CONFLUENCE 0–100** is how much independent evidence agrees right now.
90+ A+ · 85–89 A · 80–84 B+ · 75–79 B · 65–74 C · under 65 no trade.
**A 91 does not mean a 91% chance of winning.** It means the technical picture
is unusually consistent.

**VALIDATION** is a separate panel showing what actually happened to this
script's signals on the bars loaded: win rate, average R, profit factor, worst
losing run, split by reversal/continuation and by A+ grade. It refuses to show
a percentage until 25 trades have resolved, because a rate from a handful of
trades is noise.

That record is honest about its limits, stated in the panel itself: *in-sample,
loaded bars only, no slippage, no spread variation, no partial fills, not a
forecast.* An indicator cannot produce a broker statement.

---

## 6. On "research to make this high-probability"

Worth being straight with you. I searched, and what searching for a
"high-win-rate XAUUSD strategy" returns is marketing — signal sellers, course
funnels, and backtests with the losing period cropped out. There is no public,
verifiable edge to look up. Anyone who tells you otherwise is selling something.

What research *did* buy, and it was worth it, is API correctness — the thing
that has actually been breaking these scripts:

- **All `request.*()` tuples in a script share a 127-element cap.** This one
  uses 35.
- **`lookahead_on` with `[1]` is the canonical non-repainting idiom**, which is
  what this uses.
- Nested requests are permitted in v6 and inherit the parent's context — which
  corrected an overstated claim in `DIVINE.md`, now fixed.

Where the edge actually has to come from is selectivity: refusing the middle of
ranges, refusing conflicted timeframes, refusing trades your account cannot
size, and refusing targets the market is not offering. That is what this is
built to do, and it is why it will say WAIT most of the time.

**Nothing here establishes that this is profitable, and nothing claims it.**
Forward-test it on a demo account before risking money.

---

## 7. Known limitations

1. **Volume is tick volume** on retail XAUUSD feeds — price updates, not
   contracts. Everything downstream is directional evidence, not measurement.
2. **Estimated delta is inferred** from 1-minute intrabar closes, with a
   close-position fallback. It is not bid/ask tape; Pine has none.
3. **No news data.** `HIGH IMPACT NEWS MODE` is a manual toggle with a window
   you set. Pine has no economic calendar.
4. **Volume Profile is not implemented here** and is not faked. The target
   ladder uses real swing, session and previous-day levels instead.
5. **Pivot lag** — confirmed pivots need `pivIn`/`pivEx` bars. The cost of not
   repainting.
6. **The scenario engine is a projection**, not a forecast, and assumes
   volatility persists over the next 15–30 minutes. It often will not.
7. **Validation is in-sample** and indicator-based. See §5.
8. **Spread is an assumption you supply** and every dollar figure depends on
   it. Gold spreads widen violently around news and at rollover.
9. **Not backtested as a strategy.** This is an indicator — no Strategy Tester
   report.

---

## 8. Installing

Pine Editor → **Open** → **New indicator** → clear the tab (`Ctrl+F` for
`//@version=6` should show **1 match**) → paste → Save → Add to chart. Use a
**1M–5M** XAUUSD chart.

Then, before anything else, set group **01**: your balance, how you want to
risk, how you want to target, and **your broker's real spread**. Every dollar
figure on the panel depends on that spread being right.

Alerts fire on state transitions, never per bar: `BUY confirmed`,
`SELL confirmed`, `Setup found`, `Wait for confirmation`, `TP1 — take profit`,
`TP2 — take profit`, `TP developing`, `Cancel trade`, `Move SL to break-even`,
`Setup cancelled`, `Missed entry`, `Volatility warning`. For the full formatted
message use **Any alert() function call** with **Once Per Bar Close**.
