# Trading a $50 account — the numbers

You asked how many pips and how many dollars to put on a trade. Here is the
arithmetic, and then the honest part.

## The one calculation that decides everything

On a standard FX pair quoted in USD:

| Lot size | Value of 1 pip |
|---|---|
| 1.00 (standard) | $10.00 |
| 0.10 (mini) | $1.00 |
| **0.01 (micro — the usual broker minimum)** | **$0.10** |
| 0.001 (nano — only some brokers) | $0.01 |

Your risk on a trade is **stop distance in pips × pip value**.

At 0.01 lots, every pip is 10 cents. So:

| Stop distance | Loss at 0.01 lot | % of a $50 account |
|---|---|---|
| 5 pips | $0.50 | 1.0% |
| **10 pips** | **$1.00** | **2.0%** |
| 15 pips | $1.50 | 3.0% |
| 20 pips | $2.00 | 4.0% |
| 50 pips | $5.00 | 10% |

## Your numbers

- **Risk per trade: $0.50 to $1.00** (1–2% of $50). Never more.
- **Lot size: 0.01** — you have no choice; it is almost certainly your broker's
  minimum.
- **Maximum stop: 10 pips.** This is the hard constraint. At 0.01 lots a stop
  wider than 10 pips risks more than 2% of your account, and you cannot size
  down any further.
- **Target: 10–20 pips** (1R–2R against a 10-pip stop).
- **A winning trade makes you $1–$2.** That is the real scale of a $50 account.

The indicator now does this for you. Every SBS/SSS signal shows the stop in
pips, the lot size, the actual dollar risk, and what TP1 and TP2 pay — and it
turns the row **red with a warning** when the broker minimum forces more risk
than your budget. Set your real numbers in **Settings → Account & Position
Size**.

The panel also has a **Size now** row showing what the current setup would cost
you before any signal fires.

## Why the 10-pip stop limit changes how you trade

A 10-pip maximum stop rules some things out, and you should know which:

- **1-minute charts are hard, not easy.** A 1m stop is often 2–4 pips. If your
  broker's EURUSD spread is 1.5 pips, you are paying ~40% of your stop distance
  in spread on every single trade. The maths is brutal even with a good signal.
- **5-minute charts fit better.** Stops land around 6–12 pips, so the spread is
  15–25% of the risk instead of 40%. That is why the guide recommends starting
  on 5m rather than 1m.
- **Trade the tightest-spread pair your broker offers**, normally EURUSD. On a
  small account the spread is the largest single cost you control.
- **News spikes will hit a 10-pip stop for reasons unrelated to your setup.**
  The killzone filter helps; avoiding the first minutes after high-impact news
  helps more.

## The honest part

$50 is below the size at which trading returns matter, and I would be doing you
a disservice not to say so:

- At 2% risk, a **good** month of scalping might return 10–20%. On $50 that is
  **$5–$10**. Realistically, most beginners lose their first account regardless
  of the indicator.
- The spread is a fixed cost that does not shrink with your account. On $50 it
  is proportionally enormous.
- **You cannot recover a $50 account by risking more.** Raising risk to 10% per
  trade turns a normal 5-loss streak into a wiped account. This is the single
  most common way new traders lose everything, and it is the exact thing a small
  account tempts you into.

What $50 **is** genuinely good for: learning execution with real emotions
attached, at a size where the tuition is cheap. Treat it as the cost of
learning, not as capital. Trade it for a few months, keep a written record of
every trade and why you took it, and judge yourself on whether you followed your
plan — not on the $3.

Before adding money, prove to yourself on **at least 100 logged trades** that
you are profitable after spread. If you are not, more capital just loses faster.

## Settings that match a $50 account

In **Account & Position Size**:

| Input | Set to |
|---|---|
| Account size ($) | 50 |
| Risk per trade (%) | 2 (drop to 1 while learning) |
| Units per 1.00 lot | 100000 for FX; 1 for most CFDs/crypto |
| Broker minimum lot | whatever your broker actually allows — check this |
| Lot step | usually 0.01 |

In **Professional Engine** and **Scalping Engine**:

| Input | Set to | Why |
|---|---|---|
| Chart timeframe | **5m** | keeps the stop 6–12 pips |
| Scalp ATR stop floor | 0.8 | tight enough for a 10-pip cap |
| Scalp TP1 / TP2 R | 1.0 / 2.0 | realistic inside 30 minutes |
| Minimum TP1 distance (pips) | your spread × 3 | if EURUSD spread is 1.5, set 4.5 |
| Risk per trade | 1–2% | $0.50–$1.00 |

One caveat on the sizing maths: it assumes the **quote currency is your account
currency**, which is true for EURUSD, GBPUSD, AUDUSD on a USD account. On a
cross like EURGBP the pip value differs and you should verify with your broker's
own calculator.
