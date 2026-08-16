# XAUUSD (gold) — settings, and an honest look at $60

**No, the system was not built for gold, and two things in it were wrong for
gold.** Both are now fixed. This page has the corrected numbers and the part you
need to hear about account size.

---

## What was broken

| Bug | Effect on XAUUSD |
|---|---|
| Pip size came from `syminfo.type == "forex"`. Most feeds report gold as `"cfd"`, some as `"forex"` | The pip resolved to **0.01** on some brokers and **0.10** on others — the same script behaved differently depending on where you loaded it |
| Contract size defaulted to **100,000 units**. One gold lot is **100 ounces** | Pip value came out ~100× too large, which made the maximum allowable stop **0.09 pips**. Every single signal would have been suppressed with "stop too wide". You would have seen a permanently silent indicator and no reason why |

Both are replaced by an explicit **Instrument** preset (auto-detects `XAU`/`GOLD`
in the ticker) and a panel row that prints the resolved pip size and dollar per
pip, so you can check it against your broker instead of trusting it.

---

## The gold numbers

| | Value |
|---|---|
| 1 pip | **0.10** (ten cents) |
| 1.00 lot | **100 ounces** |
| 0.01 lot (broker minimum) | **1 ounce** |
| Value of 1 pip at 0.01 lot | **$0.10** |
| A $1.00 move in gold | **10 pips** = $1.00 at 0.01 lot |

Convenient coincidence: at 0.01 lot, gold and EURUSD are both **$0.10 per pip**.
So the risk table is the same — but gold *moves* several times further, which is
the whole problem below.

> If your broker quotes the gold spread as "25" rather than "2.5", they define a
> pip as 0.01. Set **Instrument → Custom** with pip size `0.01`, units per lot
> `100`. The panel's $/pip row will confirm you got it right.

---

## Your $60 account on gold — the hard part

Risk 1.5% of $60 = **$0.90**. At $0.10 per pip that is a **maximum stop of 9
pips = a $0.90 move in gold.**

Now compare that to how far gold actually travels:

| Chart | Typical ATR | Stop the system would need | Fits in $0.90? |
|---|---|---|---|
| **1m** | $0.30 – $0.90 | ~$0.70 – $0.90 (7–9 pips) | **Just barely** |
| **5m** | $0.80 – $2.00 | ~$1.30 – $1.90 (13–19 pips) | **No** |
| 15m | $1.50 – $4.00 | $2.50+ (25+ pips) | No |

So on $60 trading gold at a 0.01 lot minimum:

- **1m is the only timeframe that fits**, and only in normal conditions. In a
  fast session the stop will exceed your budget and the panel will correctly
  refuse the trade.
- **5m will mostly show "stop 15.8 pips > 9.0 max for $60"** and produce no
  signals. That is the script working properly, not a fault.

**What account size does gold actually need?**

| Goal | Account at 1.5% risk |
|---|---|
| 1m gold, comfortably | **$90 – $120** |
| 5m gold | **$130 – $200** |
| 15m gold | $350+ |

You are roughly $30–60 short of trading 1m gold with any comfort, and well short
of 5m.

**Two other gold-specific problems on a small account:**

1. **Spread.** Gold runs 20–35 cents (2–3.5 pips) versus about 1 pip on EURUSD.
   Against a 9-pip stop you are paying **22–39% of your risk on entry**. EURUSD
   costs about 17%. Gold is roughly twice as expensive to scalp.
2. **Margin.** 0.01 lot is 1 ounce, so the notional is one gold price — call it
   $3,000-ish. At 1:100 leverage the margin is about $30, **half your account for
   a single trade.** At 1:500 it is about $6. Check your leverage: at 1:100 you
   can hold one position and you are near a margin call with two.

### The honest recommendation

If you want to keep trading gold, **build the account to about $120 before
scalping it**, on demo or with a much smaller live risk in the meantime. Gold's
minimum position is simply too large relative to its own noise for $60.

If you want to trade *now* with $60, **EURUSD is the better instrument** — same
$0.10 per pip at 0.01 lot, but roughly a third of gold's range and half its
spread, so a 9-pip stop is a normal stop instead of a tight one.

I am not going to tell you $60 on gold is workable because it is what you
already trade. The arithmetic says otherwise.

---

## Settings for XAUUSD

**Instrument**

| Input | Value |
|---|---|
| Instrument | `Auto detect` (verify the panel says `GOLD · pip 0.1 · $0.100/pip`) |
| Broker minimum lot | whatever your broker allows — check, some require 0.10 for gold |

**Risk**

| Input | Value |
|---|---|
| Account size | your real balance |
| Risk per trade | **1.5%** (1.0% while learning) |
| Spread (pips) | **2.5** — measure yours during London, not at 3am |
| Minimum TP1 = spread × | 3.0 |
| Stop floor (× ATR) | 0.6 |
| TP1 / cap TP2 | 1.0R / 3.0R |
| Time stop | 30 bars |

**Execution**

| Input | Value |
|---|---|
| Chart | **1m** (5m only once the account clears ~$130) |
| Minimum ATR (pips) | **3.0** — gold below 3 pips of ATR is dead and not worth the spread |
| Reject beyond × ATR from EMA9 | 1.2 |
| RSI do-not-chase | 75 |

**Sessions** — gold's real liquidity is the London/NY overlap.

| Input | Value |
|---|---|
| Killzone 1 (London) | `0700-1000` GMT |
| Killzone 2 (New York) | `1200-1600` GMT — widen from 1500 to catch the overlap |
| Timezone | GMT (adjust for DST twice a year) |

**Additionally, and the indicator cannot do this for you:** stand aside for the
five minutes either side of US data at **13:30 GMT** (CPI, NFP, PPI) and **19:00
GMT** (FOMC). Gold moves several dollars in seconds and the spread widens to
whatever the broker likes. A 9-pip stop does not survive that, and the fill you
get will not be the price you saw.

---

## Backtesting gold

In `scalper_pro_strategy.pine`, edit the declaration — these cannot be inputs:

```pine
default_qty_value = 1        // 1 ounce = 0.01 lot   (NOT 1000, that is forex)
commission_value  = 0.125    // 25 cent spread, per side: 1 x 0.25 / 2
```

Leaving the forex defaults in place will report a fantasy equity curve.

Then judge it on expectancy per trade after commission, not net profit — see
`STRATEGY.md` section H.
