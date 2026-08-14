# Candlestick Master Pro

A TradingView **Pine Script v6** indicator: 45 candlestick patterns wired into a
multi-factor confluence engine (market structure, support/resistance, Fair Value
Gaps, Bollinger regime, RSI, MACD, Stochastic, VWAP, ADX, volume and
higher-timeframe bias).

**Script:** [`candlestick_master_pro.pine`](candlestick_master_pro.pine)
**Debug/change log:** [`DEBUG_LOG.md`](DEBUG_LOG.md)

Works on the TradingView free plan. It is an **analysis** indicator: it draws
labels and reference levels, it never sends broker orders.

## Install

1. Open any chart on tradingview.com.
2. Open the **Pine Editor** panel at the bottom.
3. Delete the default code, paste the whole contents of `candlestick_master_pro.pine`.
4. **Add to chart**, then open the gear icon to configure.

## How a signal is produced

A label only appears when all of these pass, in this order:

1. **Pattern geometry** — strict OHLC/anatomy rules, never candle colour. All
   size thresholds are ATR(14)-relative, so "long body" adapts to any pair and
   any timeframe.
2. **Required prior trend** — a bullish reversal needs a prior downtrend, a
   bearish reversal needs a prior uptrend, continuation patterns need the
   matching ongoing trend. The trend is EMA(20)/EMA(50) plus slope, and with
   *Require swing structure to agree* on it must also not contradict the
   confirmed swing structure.
3. **Timeframe gate** — each pattern carries its ideal timeframe list
   (e.g. Hammer = `60,240,1D`) and is only evaluated on those charts. A pattern
   with three ideal timeframes appears on all three. "Ignore timeframe filter"
   exists for testing.
4. **Category / tier / structure filters** — your settings.
5. **Confluence score** — see below.

The label text is only the abbreviation (HAM, BEC, MS…) to keep the chart clean.
Hover it on desktop, or press-and-hold on mobile, for the full dynamic
checklist: every ✓/✗ is the actual computed state on that bar.

### Confluence scoring (family-weighted)

Naively adding "+5 for RSI, +5 for MACD, +5 for Stochastic, +5 for VWAP" lets
four views of the *same* momentum outvote location and structure. Scores here are
grouped into families with fixed weights instead:

| Family | Weight | Checks inside |
|---|---|---|
| Pattern quality | 22 | valid geometry + the pattern's reference reliability |
| Location | 18 | S/R touch count, qualified FVG, Bollinger position, room to TP1 |
| Trend | 16 | HTF alignment, 20 EMA side, ADX direction |
| Momentum | 16 | RSI, MACD, Stochastic, VWAP (shared budget) |
| Structure | 14 | BOS / CHOCH, structural direction agreement |
| Volume | 8 | volume vs SMA(20) × multiplier |
| Regime | 6 | not chop, expansion or trending |

A family pays its full weight only when every **enabled** check inside it
passes. Checks you disable, or that are unavailable on the symbol (no volume,
VWAP off an intraday chart, ADX still warming up), are removed from the
denominator instead of counting as failures — so turning a check off never
silently caps your score.

`Score = 100 × earned / available`, then thresholds: **Strong** ≥ 80,
**Good** ≥ 65, and a setup is only marked trade-ready at ≥ *Minimum trade score*
with the chop filter satisfied.

### Lifecycle

Every pattern is tracked after detection:

| State | Meaning |
|---|---|
| `DETECTED - AWAITING CONFIRMATION` | geometry valid, waiting for the next close beyond the pattern high (bullish) / low (bearish) |
| `CONFIRMED ✓` | the confirmation close happened |
| `FAILED ✗` | price closed through the invalidation level first — label dims |
| `EXPIRED` | no resolution inside the confirmation window — label dims |
| `NEUTRAL` | indecision pattern, informational only |

## Filtering

- **Category** — bullish reversal / bearish reversal / continuation / indecision.
  For bullish only: untick everything except "Bullish reversal patterns".
- **Priority tier** — Must / Important / Rare (Rare off by default).
- **Structure** — single / double / triple & multi candle.
- **Per pattern** — every one of the 45 has its own checkbox.
- **Show only confirmed patterns** — hides a pattern until it confirms.

## Alerts

Four `alertcondition` streams (Strong Buy, Strong Sell, Bullish BOS/CHOCH,
Bearish BOS/CHOCH), plus a dynamic `alert()` on every trade-ready pattern —
for that one, create the alert with **"Any alert() function call"**.

## Pattern coverage

**Single candle (01–12):** Hammer (HAM), Hanging Man (HGM), Inverted Hammer (IH),
Shooting Star (SST), Bullish Marubozu (BUM), Bearish Marubozu (BEM), Spinning Top
(SPT), Standard Doji (DOJ), Long-Legged Doji (LLD), Dragonfly Doji (DFD),
Gravestone Doji (GSD), Four Price Doji (FPD).

**Double candle (13–23, 25):** Bullish Engulfing (BEC), Bearish Engulfing (BRE),
Bullish Harami (BUH), Bearish Harami (BEH), Harami Cross (HC), Piercing Line
(PL), Dark Cloud Cover (DCC), Tweezer Bottom (TWB), Tweezer Top (TWT), Matching
Low (ML), Matching High (MH), Kicking (KCK).

**Triple & multi (24, 26–45):** Stick Sandwich (SSW), Morning Star (MS), Evening
Star (ES), Morning Doji Star (MDS), Evening Doji Star (EDS), Three White Soldiers
(TWS), Three Black Crows (TBC), Three Inside Up/Down (TIU/TID), Three Outside
Up/Down (TOU/TOD), Rising/Falling Three Methods (RTM/FTM), Breakaway (BWY),
Ladder Bottom (LDB), Concealing Baby Swallow (CBS), Unique Three River (UTR),
Tri-Star (TS), Advance Block (AB), Deliberation (DEL), Ladder Top (LDT).

## Things worth knowing

- **No repainting of signals.** Detection runs under `barstate.isconfirmed`, and
  higher-timeframe values use the `[1]` + `lookahead_on` idiom, which returns the
  last *closed* HTF bar and behaves identically live and on history. The
  top-right dashboard is the one deliberate exception: it shows the live,
  still-forming bar.
- **Forex volume is tick volume** on TradingView, not traded volume. Where
  volume is missing entirely the volume check drops out of the score.
- **VWAP is session-anchored and intraday only.** It is computed manually rather
  than with `ta.vwap`, which errors on symbols that carry no volume.
- **Previous-day levels are only used below the daily timeframe**, because
  pulling a lower timeframe into a higher chart would leak future data.
- **The reliability percentage is reference material** from the candlestick
  literature, not a measured win rate for your symbol. Backtest before trading.

## Disclaimer

Educational and analytical tool. Not financial advice. Trading involves
substantial risk of loss — do your own research and manage your own risk.
