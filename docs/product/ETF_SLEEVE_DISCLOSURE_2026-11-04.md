# ETF sleeves: undefined Sharpe and the sleeve conventions (§10 NEW-M6-04, NEW-M6-05)

Claude redid these two §10 items from scratch on product main `a32106b`. Each item went
through two steps:

- an analyst reproduced it on synthetic and injected histories;
- a separate reviewer tried to refute the reproduction and the proposed fix.

The fixes below include the reviewers' corrections, and a second round of corrections from three
code reviewers (listed under "Review round 2" below). Both are disclosure, validation or
unavailable-state changes. `core/quant/strategies.py` (a frozen harness file) is unchanged, and
no number changes for a sleeve whose daily P&L varies. Both items live in one new module,
`core/research/sleeve_disclosure.py`.

## Which limitation each ID is

Both IDs come from model #144 (M6-13, the ETF sleeve summary) in
`docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md` at commit `659898b`.

**NEW-M6-04: unambiguous.** It is the only limitation of #144 marked [결함]: when the trend switch
never holds the fund, its P&L is the cash rate on every session and the Sharpe shows about 1e16.
Register line 137 ends "노출이 없는 구간은 … Sharpe가 1e16 단위로 폭주한다(P01-11). ETF 화면의 무추세
모의에서는 6.8%가 그렇다(NEW-M6-04)." The known-errors register row (`KNOWN_ERRORS_REGISTER_2026-10-28.md:1788`)
says the ID appears only in the related-errors cell; line 137 shows otherwise. The registers are
official records and are not edited here.

**NEW-M6-05: probable, not unambiguous.** No register sentence prints NEW-M6-05. The probable reading
is the warm-up and full-window Sharpe limitation of #144 (the first 210 sessions are cash; "invested"
counts only after them, while the Sharpe covers the whole window), together with the undisclosed
fixed 3% cash half of the distributions limitation. The evidence:

- The verification cell cites one script for exactly two findings, "1e16과 워밍업 편향", and NEW-M6-04
  is the 1e16 half.
- Register line 95 writes a defect that has two numbers as "X = Y". Entry 144 lists NEW-M6-05 and K-e
  separately, so NEW-M6-05 is probably not K-e.
- Line 137 covers the fixed 3% cash and the gross Sharpe but cites only NEW-M6-04 (weak evidence).

The other readings are still possible:

- GPT's own description of NEW-M6-05 ("daily constant-weight rebalancing versus buy-and-hold")
  describes the K-e assumption.
- The family-verdict limitation (the verdict tiles show the family card, not this fund) has no ID.
- The gross, not excess-of-cash, Sharpe sits next to FC-14 only by inference.

The §10 queue type ("Model assumption or convention") was written by GPT, so it is not independent
evidence. The conventions text therefore states every one of these: the warm-up, the fixed cash
assumption, the Sharpe basis, the invested-share window, K-e (as a disclosure only; K-e's code fix
stays held for R3) and the family cards. It is correct under every reading. The owner can choose the
reading; nothing in the code depends on it.

## Reproduction (synthetic and injected inputs, offline)

| Case | Before | Now |
| --- | --- | --- |
| Constant cash P&L, 505 closes | numpy sd 5.43e-20, Sharpe 3.4826467946423224e16 | n/a |
| Constant cash P&L, 547 closes | sd exactly 0, Sharpe 0.00 | n/a |
| Register seed-2 walk, 505 closes, 069500 (3 bp) and SPY (50 bp) | trend 3.4826467946423224e16 | trend n/a; vol target −0.7151 / −0.7516 and buy-and-hold −0.8407 unchanged |
| Flat price at 100.0, 505 closes | trend and vol target 3.48e16, buy-and-hold 0.00 | all three n/a, one note naming all three |
| Flat price at 100.37, 505 closes | trend 20.80, vol target 3.48e16, buy-and-hold 0.00 | trend 20.80 unchanged; vol target and buy-and-hold n/a |
| Shipped Synthetic demo, 251340, 400 sessions | trend 4.642314207434303e16; Flet tile "46423142074343032.00" | trend n/a; vol target −0.64, buy-and-hold −0.73 unchanged |
| One NaN close | every Sharpe 0.00 | every Sharpe n/a, "non-finite values" |

- The exact sample variance of a constant cash P&L is 0 (checked with `Fraction` arithmetic), while its
  mean is positive (0.03 a year). Its Sharpe is therefore a positive number over 0: undefined, but not
  0/0. Only a P&L that is 0 throughout, such as buy-and-hold on a flat price, is 0/0. Of the lengths
  301–2520 closes, 21 give an sd of exactly 0 (the first is 547) and showed 0.00; the rest showed about
  1e16, which comes from the rounding residue of the sd (5.43e-20 at 505 closes), not from the data.
- A flat price is not always "all three n/a". Buy-and-hold never varies on it, and neither does the vol
  target (its realised vol is 0, so it stays in cash). The trend switch stays in cash only when its
  210-session average equals the price exactly, as at 100.0 (and at 0.1 over 505 closes). At many other
  levels, float rounding of that average puts the switch in the fund on some rows, so its P&L moves
  between 0 and the cash rate and its Sharpe is defined: 20.80 at 100.37, 57% invested. That number is
  the same as before; the test pins it.
- On 400 register walks (505 closes, 19%/yr, no drift), 27 never hold the fund. In 3 of them the switch
  turns on only on the final row, which is never held. Every cash-only P&L has a relative sd at most
  5.43e-20, and every P&L that held the fund at least 1.84e-3.
- 251340 / 400 is the only undefined Sharpe among 27 synthetic code and length combinations
  (069500, SPY, QQQ, 122630, 252670, 114800, 233740, 251340, DEMO × 400, 504, 1000).
- On the default screen (504 closes = 503 daily returns), the trend sleeve's first 210 daily returns
  (42%) and the vol target's first 23 are cash. On 373 of 373 register walks that held the fund, the
  full-window sd was below the post-warm-up sd.

## The tolerance rule (NEW-M6-04)

`sleeve_summary(pnl)` returns `S.summary(pnl)` with every number unchanged, plus `sharpe_status`:

- `COMPUTED`: the P&L has at least two finite values and `std(ddof=1) > 1e-10 × max(1, max|p|)`.
  `sharpe` is the identical `S.summary` value.
- `NOT_DEFINED_NO_VARIATION`: otherwise. `sharpe` is `None`.
- `NOT_DEFINED_NON_FINITE`: the P&L contains NaN or infinity. `sharpe` is `None`.

This is a numerical tolerance, not an exact zero test: a P&L whose relative sd is at or below 1e-10
counts as no variation. A P&L with a real but tiny variation at or below that level also becomes
n/a; the test pins one (300 sessions at the cash rate plus one at +1e-12). On the register walks
above, the margin is more than 7 orders of magnitude on each side (5.43e-20 and 1.84e-3 against
1e-10), and the rule agrees with an exact max − min == 0 test on every trend P&L. The crypto z score uses the same 1e-10 rule
(`core/crypto/analytics.py:98`).

## What each surface shows

| Surface | NEW-M6-04 | NEW-M6-05 |
| --- | --- | --- |
| `etf_workflow.analyze` | `sleeve_summary` for the three sleeves | The literals are named once (`SLEEVE_TREND_LOOKBACK` 210, `SLEEVE_VOL_WINDOW` 22, `SLEEVE_CASH_RATE` 0.03, rf = cash / 252). The same variables go to the strategy calls and to `sleeves.conventions`. After the study cards are loaded, `with_loaded_cards` records whether each family card was among them (`trend_card_loaded`, `vol_target_card_loaded`). |
| EN narrative | "Sharpe n/a" in place of the number, then a note after "Price basis for these sleeve numbers: …" | The conventions sentence after the note (or after the price basis when there is no note) |
| KO narrative | "계산 불가" and the Korean note, in the same places | `conventions_korean`, in the same place |
| Flet tiles | "n/a" with a tooltip saying why | A defined Sharpe tile carries the conventions as its tooltip (it had none) |
| Flet notice | — | A notice under the sleeve row with the conventions text |
| Flet AI payload | `sharpe: null` and `sharpe_status` | `sleeves.conventions` (no private field name, so the AI filter keeps it) |
| Native table | "—" (already shown by `fmt(None)`; no change) | — |
| Native text | A localized en/ko note after the "bp per side" line | A localized en/ko conventions text, then a `sleeve_conventions` report section |
| Native export and AI commentary | They carry the sections (the note and the conventions text, plus the section). They never carried the sleeve dicts, so `sharpe_status` reaches only the Flet AI payload and `MarketOutput.data`. | Same |

Narrative order: the existing sleeve sentences unchanged (the Sharpe sentence, "These are in-sample
descriptive numbers…", the verdicts and the price basis), then the NEW-M6-04 note (only when a Sharpe
is not defined), then the conventions. The note comes after the price basis, not straight after the
Sharpe numbers, so that "These are…" / "이는 표본 내 기술통계입니다" still refers to the numbers and not to
the note.

The conventions text (default screen, Flet, where the study cards are loaded):

> Sleeve conventions: the trend switch first decides after 210 sessions (the length of its 10-month
> moving average), so the first 210 of these 503 daily returns (42%) are a warm-up held in cash, and the
> vol target's first 23 likewise. Cash earns a fixed 3% a year (assumption: 3% / 252 per session), not an
> observed rate, the same for every currency. Each Sharpe is the mean daily return × 252 over its
> standard deviation × √252 on the whole window, warm-up included. It uses raw returns, not returns in
> excess of the cash rate, and the trend switch and vol target returns are after their per-side trading
> cost; buy-and-hold has no warm-up, no cash and no cost. The warm-up replaces the fund's return with the
> fixed cash return on those sessions and lowers the measured volatility, so the comparison with
> buy-and-hold is not like-for-like. The invested share averages the trend weight from the end of the
> warm-up to the last close, including the last close's weight, which is never held. A vol-target weight
> below 1 is reset to that weight every session at no cost. The study verdicts are those of the family
> cards (S_E1_trend_krx and S_E2_voltarget_kodex200), not a test of this fund.

The Native app loads no study card (`execute_etf` without `study_cards`, so the verdicts read "not
run"). There the last sentence is instead: "The family study cards (S_E1_trend_krx and
S_E2_voltarget_kodex200) were not loaded here, so no study verdict is shown for them (not run); a
card's verdict covers the rule family, not this fund." If only one card is loaded, each card gets its
own sentence.

The Sharpe is not called "gross": in this codebase "gross" means before costs, and the trend and
vol-target P&L is after the 3 or 50 bp per-side cost (`strategies.simulate` subtracts it). The Korean
text likewise avoids "총수익", which the LETF text in the same narrative uses for total return with
distributions; it says "현금 금리를 빼지 않은 수익률 기준" and "편도 거래 비용을 뺀 값". The record's
`sharpe_basis` is `RAW_RETURN_NOT_EXCESS_OF_CASH_AFTER_SLEEVE_COST`.

The counts are daily returns, so they do not clash with "Over 504 sessions" in the premium sentence.
The text describes the mechanism and claims no direction of bias, because the direction depends on
the data:

- On a path with steady upward drift, the warm-up lowers the trend Sharpe: 0.73 on the page against
  0.79 after the warm-up.
- On the register's driftless walks that held the fund, it raises the median: 0.11 against −0.04 over
  373 walks.

The Korean-locale HTML export keeps these dynamic notes in English, as the existing decay and LETF
disclosures do: `localized_html` translates only catalog strings and keeps unknown text raw. No catalog
pairs were added. The test reads both notes from the `ko_KR` report.html.

## Valid inputs are unchanged

- `tests/etf_sleeve_disclosure_acceptance.py` keeps a verbatim copy of the `a32106b` sleeve recipe and
  of the `a32106b` `narrative` and `etf_korean`.
- On 120 register walks × 2 costs:
  - every existing key of every sleeve is bit-identical, in the same order;
  - `equity_trend`, `equity_bh`, `cost_bps` and `exposure_trend` are identical;
  - only `sharpe_status` and `conventions` are added.
- More than 200 of those cases have all three Sharpes defined. For each of them, removing the
  conventions sentence gives the old EN and KO narratives exactly.
- The same check holds for 8 shipped fixtures: the ETF premium fixture, LETF 233740,
  069500/504, SPY/504, QQQ/1000, 122630/504, 252670/400 and DEMO/400.
- A scratch probe loaded the `a32106b` modules themselves. Over 400 walks × 2 codes it found
  2,360 sleeves COMPUTED with identical values and 40 undefined, and 760 narratives identical
  after the sentence was removed.

## Not changed, and still open

- `core/quant/strategies.py`, `validate.py`, the study, the cards, the gates and the registers.
- P01-11, the same 0/0 cause in `validate._col_sharpe` (gate and DSR territory, on the R3 path).
- `core/ficc/vol_products.py` also uses `summary`; a book that never trades gives 0.0 there. How that
  screen shows it is unverified.
- MF-02: the costs stay hard-coded at 3 bp (KRX) and 50 bp.
- The off-by-one in "invested": it includes the final, never-held row (seed 0: 0.1424 against 0.1429
  over the held rows). It is disclosed, not fixed, because fixing it would change a number.
- One 3% cash rate for KRW and USD funds. It is disclosed ("the same for every currency"), not changed.
- The Korean-locale export notes stay in English.
- Optional maths additions, for the owner to decide: a like-for-like pair (trend and buy-and-hold
  Sharpe after the warm-up) and the vol target's mean held weight.
- Native AI commentary refuses reports over 180,000 bytes (`quantgen_desktop/commentary.py`). The note,
  the conventions text (in its own line and in the narrative) and the `sleeve_conventions` section add
  about 3.4 KB to the ETF report, so that limit is now reached about 48 sessions earlier. Measured on
  the synthetic 069500 Native report: `a32106b` accepts up to 2,554 sessions and refuses from 2,555;
  now it accepts up to 2,506 and refuses from 2,507 ("Report is too large for commentary; choose a
  smaller calculation"). The refusal is the existing explicit message; the exact limit for real data
  depends on the series and is unverified. The default screen (504 sessions) is about 39.6 KB.
- Observed, outside these items: on the synthetic LETF index, GARCH-t ν is `inf`, so
  `json.dumps(wf.payload(...), allow_nan=False)` fails for those funds. The export's `plain()` writes it
  as null. The new test checks strict JSON for the sleeves only, for that reason.

- Observed in the tests, outside these items: in one process, a second `ResearchWindow` built after the
  first was really deleted (`deleteLater` plus a posted `DeferredDelete`) fails in
  `quantgen_desktop/wheel_guard.py` ("wrapped C/C++ object of type _WheelGuard has been deleted"). The
  two Native tests therefore share one window. The product opens one window, so this is not reached in
  normal use (unverified beyond that).

## Review round 2

Three code reviewers read commit `acc736c`. Every finding was reproduced before it was fixed:

- The cash-only Sharpe was called 0/0, and the on-screen note said "not a large positive Sharpe".
  Its mean is positive, so the ratio is a positive number over 0. The note now says "the standard
  deviation is 0 and the ratio is undefined; a figure of 0 or a very large number here would be float
  rounding, not a result", and the comments say the same.
- "Flat price: all three n/a" holds at 100.0, not at every level (see the reproduction section).
- The verdict clause named the card ids next to "not run" verdicts on the Native screen, which loads
  no card. It now says the cards were not loaded.
- "Gross" read as "before costs", and "총수익" as total return with distributions (see above).
- The n/a note sat between the Sharpe sentence and "These are in-sample descriptive numbers" / "이는
  표본 내 기술통계입니다", so "These" and "이는" pointed at the note. It now follows the price basis.
- Korean wording: "변동성 목표도 처음 23개가 같습니다" (ambiguous) is now "변동성 목표도 처음 23개는 현금으로
  보유한 준비 구간입니다", and "210거래일(10개월 평균)" is now "210거래일(10개월 이동평균 기간)".
- Test gaps: a test now checks the Native conventions text and section for a valid input (the
  mutation "show them only with a note" fails it), and the Flet tests check the banner under the sleeve
  row itself, not only the tile tooltips (removing the banner fails them).
- The commentary size limit is disclosed above.

## Records left to the main session

The SECTION10 queue entry and counts, the SECTION10 triage, `docs/compliance/FACTS.md`,
`docs/compliance/source-review.json` (`etf_workflow.py`, `market_narrative_language.py`,
`market_tools.py`, `ui/etf_page.py`, plus the new module and test), `.github/workflows/runtime-smoke.yml`
(paths and a unittest line) and the website update record.

## Unverified

- Real KIS, FMP or Yahoo data, and Windows.
- How the Flet and Qt widgets look on screen. The tests check control values, tooltips, table cells
  and report sections only.
- How the Flet AI path (`core/quant/insights.py`) serialises the pre-existing `nu = inf`.
- The exact procedure for refreshing `source-review.json`.

## Checks

`tests/etf_sleeve_disclosure_acceptance.py` has 17 tests and runs offline. Run it with
`python -B -m unittest tests.etf_sleeve_disclosure_acceptance -v`. These existing suites still pass:

- desktop market and markets watchlist;
- authored-prose language parity;
- market diagnostics language and desktop language;
- AR(1) decay, Native and Flet;
- the LETF disclosure, assumptions, index, AI payload and I/O guard suites, Native and Flet;
- `expansion_acceptance` (20 checks, run through its `tests()` list, including the `strategies` self-check);
- the `ui/etf_page.py` self-check.
