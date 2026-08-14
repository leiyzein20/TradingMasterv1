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
