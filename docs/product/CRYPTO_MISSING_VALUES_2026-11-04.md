# Crypto: a missing value stays missing (§10 NEW-M6-14, NEW-M6-15, NEW-M6-22)

The owner's 2026-11-03 decision: the GPT private Crypto work is not recovered; Claude
redoes the §10 items from scratch. This change is that rework. It reads the model
register (`MODEL_LIMITS_REGISTER_2026-10-28.md`, entries 132 M6-01 and 142 M6-11, on
research commit `2da6469`) and the current code on product main `c1a4e97`.

## Which limitation each ID names

The queue marks all three IDs `mapping_needs_disambiguation`. The register lists them
only in the "related errors" cell, so the mapping is resolved by elimination: every
other limitation of the same model already carries its own error ID.

- **NEW-M6-15 (M6-01 kimchi premium and 1-year z).** The only M6-01 limitation without
  another ID: when z cannot be computed (fewer than 91 observations), `last_z` became
  0.0 and the screens showed `+0.00`. A flat window gave z = 0 as well. Unambiguous.
- **NEW-M6-14 and NEW-M6-22 (M6-11 provider-derived values).** M6-11 has four
  limitations without another ID:
  - (a) a coin with no KRW market or no current price was valued at 0, and the total
    still read as the whole account;
  - (b) one unknown market could make the whole price request fail, so the whole
    holdings card became an error;
  - (c) a missing index price gave a 0% perpetual premium, and a missing mark price
    gave −100%;
  - (d) the average buy price had no currency unit.

  Two IDs over four limitations stays ambiguous. This change corrects all four, so
  each ID is covered whichever pairing is meant. The other M6-11 limitations already
  have their own IDs: SFV-01 (open interest fetched but unused) and NEW-M6-18
  (holdings in the AI payload, implemented earlier). Neither is part of this change.

## What changed

| Where | Before | After |
| --- | --- | --- |
| `data/crypto/crypto_client.py` premium index | missing index → 0.0 %, missing mark → −100 %, missing next funding time → 1970-01-01 | `premium_pct`, `mark`, `index`, `next_funding_time` are `None` when missing |
| Upbit daily candles | a day without a close (or open/high/low) became 0.0 (premium −100 %) | the day is left out and not counted, so paging continues to the requested number of usable days (also D12-03) |
| Upbit ticker | a missing price, change or 24-hour value became 0.0 | `None` |
| Binance funding rate in the premium index | missing → 0.0, read by the AI as a 0 % rate | `None` |
| `core/crypto/analytics.py` `kimchi_premium` | z = 0 for a flat window; `last_z` 0.0 when not computed; zero or missing prices entered the premium | z and `last_z` are NaN when undefined; days without a usable Upbit or Binance price are left out, and an unusable FX fixing is skipped so the previous one carries forward |
| `core/research/crypto_workflow.py` | `tick.get(coin, 0.0)`; one batch ticker request | `value_holdings` sets `krw_value=None` without a price (a zero quantity is worth 0); `krw_prices` asks each market alone only when Upbit rejects the list (HTTP 400/404), while a timeout, rate limit or server error stays a failed read; `holdings_summary` returns the valued total, the unvalued coins and `complete` |
| Narratives (English, Korean) | "+0.0 standard deviations" | "z unavailable: fewer than 91 observations or no variation in the window" / "z는 계산할 수 없습니다 …" |
| AI payload | `kimchi.z` 0.0; `premium_index.premium_pct` 0.0 or −100 | `null` |
| Flet Crypto page | `+0.00`, `+0.000%`, total of valued and zero-valued coins | `n/a` with a tooltip; total marked "partial, excludes …"; row value "n/a (no KRW price)"; cost basis with its unit, non-KRW prices to 8 significant digits |
| Native Crypto pane | z 0.0000; KRW value 0.0000 | `—`; a note naming unvalued coins (English and Korean), exported as a named holdings section so, like the holdings table, it never enters AI commentary (NEW-M6-18); cost basis with its unit |

Provider parsing and the analytics share one definition of a usable number (`core/crypto/values.py`).

For valid inputs nothing changes. On 40 synthetic random histories (95–800 days,
weekday-only FX), the old and new `kimchi_premium` gave identical dates, premium and
z arrays and identical summary values. The only numbers that differ are the
undefined cases above. A flat window is treated as having no variation when its
standard deviation is below 1e-10 of its largest absolute value. Without this
tolerance, float rounding of a constant window gave z ≈ ±1.

## Not changed

- Historical study cards and the frozen asset-expansion study are not regenerated.
  `docs/asset_expansion_study.py` would now print `nan` instead of `+0.00` in the same
  undefined case; it is not edited.
- The other M6-01 limitations keep their own IDs and are not claimed here: FX age
  (V01-01), synthetic FX labelled LIVE (D03-01, D03-08), USDT basis (DF-06), today's
  incomplete bar (DF-03), page-wide failure when Binance futures fail (SFV-01) and speed
  (P01-09).
- Real Upbit and Binance replies are not used. How Upbit answers a list with an
  unknown market is unverified. The per-market retry covers both a whole-list
  rejection and a partial answer.

## Checks

`tests/crypto_missing_values_acceptance.py` (11 tests, offline, sockets refused):

- provider parsing of missing mark/index/close/price;
- the ticker fallback, and no per-coin retry on an outage;
- holdings valuation and summary;
- z for a short and a flat history, and unchanged z for a varying one;
- left-out zero/NaN rows;
- English/Korean narratives and payload;
- the native pane's cells and note.

Run with the development dependencies:

```sh
python -m unittest tests.crypto_missing_values_acceptance -v
```
