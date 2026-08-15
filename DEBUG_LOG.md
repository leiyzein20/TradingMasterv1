# Debug & improvement log

Everything below was found in the original `Candlestick Master Pro` draft and
fixed in [`candlestick_master_pro.pine`](candlestick_master_pro.pine).

## 1. Compile-blocking

| # | Problem | Fix |
|---|---|---|
| 1 | `str.tostring(=======confidence)` in the dashboard — a leftover merge-conflict marker. This alone stopped the script from compiling. | Removed. The panel now shows a real live score. |
| 2 | Even without the marker, `confidence` did not exist at that point: it is local to `fire()`, so the dashboard could never read it. | Score computation was extracted into `confluenceScore()`, which the dashboard calls directly. |
| 3 | `int latestPatternBar = … : na` — `na` in an `int` ternary. | Uses `-1` as the sentinel. |
| 3a | `SHORT_TITLE_TOO_LONG` — `shorttitle` was `"CandleMasterPro"` (15 chars); the limit is 10. | Now `"CandlePro"` (9). |
| 3b | `CE10205 The if statement is too long` — all 45 detections were nested inside one `if barstate.isconfirmed` body (~445 lines), exceeding Pine's per-`if`-body size limit. | The wrapper is gone: `confirmed = barstate.isconfirmed` is hoisted and each detection is its own flat `if confirmed and <shape> and <trend>`, so every `if` body is a single `fire()` call. Behaviour is identical — a nested `if A` inside `if B` is exactly `if B and A`. The BOS/CHOCH drawing block was split into two flat blocks for the same reason, the dashboard's locals were hoisted to global scope, and the tooltip suffix moved into `readinessText()`. The largest remaining `if` body is 35 lines. |

## 2. Wrong results (silent, worse than a compile error)

| # | Problem | Fix |
|---|---|---|
| 4 | **ADX was invalid.** `plusDI = trur > 0 ? 100.0 * ta.rma(plusDM, adxLen) / trur : 0.0` put `ta.rma` inside a ternary branch. A `ta.*` function only advances its internal state on bars where it is actually evaluated, so the smoothing was corrupted — and ADX feeds the trend filter, the regime label and the FVG quality gate. | `ta.rma` is hoisted to unconditional globals (`plusDMSm`, `minusDMSm`). |
| 5 | Same hazard in `stochBullCross = ta.crossover(…) or ta.crossover(…)`. | Each cross hoisted into its own variable. |
| 6 | **Ladder Bottom used the wrong wick.** The reference requires candle 4 to have an *upper* shadow (a failed rebound); the code tested `loW[1]`, a lower shadow. It was detecting the opposite structure. | Now `upW[1] >= body[1] * 0.30`. |
| 7 | **`ta.vwap` can raise a runtime error** on symbols with no volume, and it is meaningless on daily+ charts, where it still scored points. | Session VWAP is computed manually from `hlc3 × nz(volume)` with a daily reset, and `vwapAvailable` is gated to intraday. |
| 8 | **Previous-day S/R leaked future data** on daily and weekly charts: requesting `"1D"` with `lookahead_on` from a higher timeframe. | Guarded by `useDailyLevels` (chart timeframe below 1D). |
| 9 | **BOS was a state, not an event.** `bullBOS = close > lastSwingHigh` stayed true for as long as price held above the swing, so "break of structure" scored on every bar of a trend. `ta.crossover` on a level that jumps between pivots is also unreliable. | A proper structure engine: each swing is armed once, consumed on the break, and `structDir` records the resulting bias. CHOCH is now a break that reverses `structDir`, instead of being inferred from the EMA trend one bar earlier. |
| 10 | **Stochastic ignored its own inputs.** `stochOS`/`stochOB` existed but the crosses were hardcoded to 20/80/50. Raw `%K` was used with no smoothing. | `%K` is smoothed and compared against `%D`; the configured levels are used. |
| 11 | **Marubozu could essentially never fire.** The default `maruWickTicks = 0` demanded exactly `open = low` and `close = high`, so `body >= rng * 0.95` was dead code. | Tolerance is `max(range × 5%, N ticks)`, default 2 ticks, both configurable. |
| 12 | **RSI divergence had no time bound**, so two pivots hundreds of bars apart could pair into a phantom divergence. | Added `divMaxSpan` (default 60 bars) between the paired pivots. |
| 13 | **HTF alignment needed 2 of 3 even when fewer than 2 HTFs existed.** On an H4 chart with HTFs 60/240/1D, only 1D is usable, so `htfBullAlign` could never be true and every signal silently lost those points. | The requirement scales with `htfActive`, and the checks drop out of the score entirely when no HTF is usable. |
| 14 | Only **one FVG per side** was tracked; each new gap silently erased the previous one, and the zone was drawn with `plot` + `fill` rather than boxes (`max_boxes_count` was declared but unused). | A `Fvg` user-defined type in an array, up to *N* zones per side as boxes that extend right and retire on full fill or expiry. |
| 15 | `fvgBullSRFar` and `fvgBearSRFar` were **identical expressions**, and "room" for both directions used absolute distance — so a resistance price had already broken still counted as a wall above it. | One shared `fvgSRFar`, plus directional `distResAbove` / `distSupBelow` that only count levels actually ahead of price. |

## 3. Scoring design

| # | Problem | Fix |
|---|---|---|
| 16 | The score added RSI + MACD + Stochastic + VWAP + EMA + ADX + BB + HTF as if they were independent evidence. They are largely four or five views of the same momentum, so momentum could outvote location and structure — the opposite of how the patterns are supposed to be validated. | Family weighting with fixed budgets (pattern 22, location 18, trend 16, momentum 16, structure 14, volume 8, regime 6). Correlated oscillators now share one capped 16-point budget. |
| 17 | Disabling a check reduced `maxScore`, but unavailable data (no volume, warming-up ADX) still counted as a failure in some paths. | Unavailable and disabled checks are removed from the denominator consistently. |
| 18 | Every pattern started from the same base regardless of quality; the per-pattern reliability from the reference material was only decorative text. | The literature reliability (50–78%) now scales the pattern family, and the "★ High/Good/Fair/Low" grade is derived from it rather than hand-typed per call. |
| 19 | Nothing checked whether the target was reachable. A setup pointing straight into resistance scored the same as one with open space. | New **room to TP1** check: the first opposing level must be at least `rr1 × R` away. |
| 20 | Stops sat exactly on the pattern extreme. | `slBufferATR` (default 0.15 ATR) beyond the extreme, still floored at `atrSLMult × ATR`. |

## 4. Pattern definitions tightened against the reference

- **Hammer / Inverted Hammer** — the dominant shadow must now also be ≥ 55% of
  the range, not just ≥ 2× the body. Without that, a small-bodied candle with two
  medium wicks qualified as a pin bar.
- **Engulfing (BEC/BRE)** — candle 1 must have a real body (engulfing a doji is
  not an engulfing), and candle 2 must exceed it by 10% and be ≥ 0.40 ATR.
- **Spinning Top** — added a shadow-balance rule and restored the noise floor, so
  a pin bar is no longer classified as indecision. (It is the only "all
  timeframes" pattern, so it was the biggest source of label spam.)
- **Dragonfly / Gravestone** — opposite shadow tightened from 15% to 10% of range.
- **Four Price Doji** — also requires the range to be tiny versus ATR, not just
  versus ticks.
- **Morning / Evening Star** — candle 3 must now be a real body (≥ 0.5 ATR); a
  doji "recovery" candle no longer counts.
- **Tweezers, Matching High/Low, Stick Sandwich** — candle 1 must have a real
  body, so two adjacent doji-like bars no longer trigger them.
- **Matching Low** — added the reference's "does not open materially lower" rule.
- **Tri-Star** — required a true gap on *both* sides of the middle doji, which
  effectively never happens on spot FX. Now requires the middle doji to be at the
  extreme, with a gap treated as a bonus rather than a precondition.
- **Deliberation** — "opens inside candle 2's body" now tests `open` itself rather
  than `min(open, close)`.
- **Advance Block** — candle 1 must have a meaningful body.
- **Trend gate** — with `strictTrend` on (default), the required prior trend must
  also not contradict the confirmed swing structure.

## 5. Robustness / Pine-specific hazards removed

- `openInsidePrevBody(int off)` indexed history with a **variable offset**
  (`open[off]`), which Pine cannot always size a lookback buffer for. Replaced
  with the two explicit expressions actually needed.
- The FVG cap originally removed an array element **while iterating forward** with
  a loop bound captured before the removal — an out-of-bounds runtime error
  waiting to happen. The index is now resolved first, and the retirement pass
  iterates downwards.
- `confluence()` no longer reads any `[1]` history internally. All
  previous-bar comparisons (`rsiRising`, `stochRising`, `macdHist` deltas) are
  precomputed as globals, so a conditionally-called function can never see stale
  history.
- Multi-line `if` conditions were rewritten as named booleans; continuation lines
  are all indented by a non-multiple of 4, as Pine requires.
- Redundant `array.set()` after mutating a UDT field removed (instances are
  references), and dead variables (`gapUp`, `gapDown`, `bodyGapDown`, duplicated
  `dispBody`/`dispBodyPct`) deleted.

## 6. Additions

- Live **two-sided** confluence read (bull vs bear) on the dashboard, plus the
  last pattern's score, structural bias and S/R touch counts.
- Dynamic `alert()` on trade-ready patterns, carrying abbreviation, direction,
  score, symbol and timeframe.
- BOS/CHOCH labels now render on both sides with correct `+`/`-` suffixes; the
  original could only ever print `CHOCH+` and `BOS` regardless of direction.
- `confWindow`, `fvgMaxZones`, `divMaxSpan`, `slBufferATR`, `maruWickPct`,
  `strictTrend`, `stochSmoothK`, `stochSmoothD` exposed as inputs.

## Not changed on purpose

- **Detection stays on confirmed bars.** Nothing was moved to intra-bar
  evaluation to make signals appear "earlier" — that would repaint.
- **The reliability percentages are still reference figures** from the source
  material. They are not measured win rates and are not presented as such
  anywhere in the tooltips.
- **No order execution.** Entry/SL/TP remain analytical reference levels.

## 7. CE10295 — "the main body of the script is too long"

Pine caps how much code the **global scope** may hold. The script had grown to
roughly 1460 code lines in the main body; ~680 of them were moved into functions,
which is the fix TradingView's own error message recommends. Nothing changed
semantically — each extracted function is called unconditionally on every bar, so
history references inside them advance exactly as before.

| Moved into a function | Was | Now |
|---|---|---|
| The 45 pattern detections | 355 lines of `if … fire(…)` in the main body | `detectSingleCandle()`, `detectDoubleCandle()`, `detectTripleCandle()`, `detectMultiCandle()` — four calls |
| Dashboard cells | 74 | `drawDashboard()` |
| Legend rows | 33 | `drawLegend()` |
| Pattern lifecycle loop | 30 | `updateLifecycle()` |
| FVG retirement loop | 14 | `retireFvgs()` |
| FVG interaction scan | 15 | `scanFvgs()`, returning a 4-tuple |
| Same-bar pattern scan | 25 | `scanPattern(dir)`, returning a 4-tuple, called once per direction |
| 18 multi-line shape definitions | 100 | one `fn…()` wrapper each |
| BOS / CHoCH drawing | 32 | `drawBreak(dir, level, isChoch)` |

Main body: **1463 → 783 code lines.** Of what remains, 225 lines are `input.*`
calls, which have to stay in the global scope.

Two details worth recording, because they constrain how this refactor can be done:

- **A Pine function cannot reassign a global variable.** The BOS/CHoCH drawing
  used `var line lastBullBreakLine` and reassigned it, so it could not simply be
  wrapped. It now pushes into `var array<line> structLines` instead — *mutating*
  an object is allowed where reassigning a variable is not. That also gained a
  feature: `structKeep` controls how many recent breaks stay on the chart.
- **Blocks that produced several globals return tuples instead**
  (`scanFvgs`, `scanPattern`), for the same reason.

## 8. CE10235 — incompatible if/else branch types (`Fvg; void`)

`array.remove()` **returns the element it removed**. In the FVG retirement loop
it was the last statement of the `if` branch, so that branch had the type `Fvg`
while the `else` branch ended on a void `box.set_right()`:

```pine
if filled or expired
    if not na(f.bx)
        box.delete(f.bx)
    array.remove(fvgs, i)        // <- branch type: Fvg
else
    if not na(f.bx)
        box.set_right(f.bx, ...) // <- branch type: void
```

Rewritten as three separate `if`s with no `else`, so no two branches are ever
compared. A bare `if` whose last statement returns a value is fine — the error
only fires when an explicit `else` exists and the branches disagree, which is why
`if array.size(supLevels) > 20 / array.shift(supLevels)` elsewhere is legal.

`registerFvg` had the same shape without an `else`. It was reordered anyway
(capture the element, remove it, then delete its box) so the branch ends void.
The order matters for a second reason: the box id has to be read *before* the
element leaves the array.

## 9. CE10117 — compiled code contains too many tokens (108,925 / 100,256)

A hard ceiling on the whole script, not just the global scope, so this needed
real volume reduction rather than relocation. Measured the token distribution
per section first, then cut the largest contributors:

| Change | Est. tokens saved |
|---|---|
| **Rolling extremes `hi2…hi6` / `lo2…lo6`** precomputed once, replacing nested `math.max(high, math.max(math.max(high[1], high[2]), …))` at 45 call sites | ~8,600 |
| `confluenceText()` rebuilt around a `chk(ok, name)` helper instead of a bespoke sentence for every state of every indicator | ~2,000 |
| Dropped `trendTxt`, `sltp`, `tfHuman` from `fire()` — the trend is implied by the gate, the SL/TP prose is superseded by the computed levels, and the ideal-TF text duplicated `tfList` | ~1,900 |
| `scalpReasons()` and `signalTooltip()` rebuilt on the same helper; the tooltip now defers detail to the signal table | ~1,600 |
| Panel trimmed from 21 rows to 13 — the RSI/MACD/ADX/Volume/Bollinger number rows moved to the companion oscillator pane | ~1,300 |
| 30 niche inputs became constants (all 12 colours, 8 FVG tuning knobs, Fib pocket bounds, lot step, and others) | ~1,200 |
| Signal detail table 16 rows → 13, legend 16 → 15 | ~700 |

Result: **108,925 → ~92,000 tokens**, about 8% under the limit.

The `hi2…lo6` change is the interesting one — it was pure repetition. Forty-odd
copies of a five-call nested expression cost more than every input in the script
combined, and collapsing them changed no behaviour at all.

Nothing was removed from the pattern set: all 45 patterns, their geometry, the
per-pattern toggles and the lifecycle tracking are intact. What went is
duplicated prose and configuration nobody needs to touch.

One follow-on bug from this pass, caught before shipping: moving `confluenceText`
introduced the `chk()` helper *after* `scalpReasons()`, which also uses it —
a forward reference. `chk()` now sits above both.
