# CMS first-period coupon disclosure

M4-N11 concerns the meaning of a displayed rate, not the note's pricing rule.
The CMS report's existing `coupon` field contains the first period's projected
coupon at an annualized decimal rate. Later coupon projections can differ along
the forward curve. The previous generic “Coupon / year” label and “The coupon
is … a year” explanation could be read as a fixed rate for the whole note.

Flet and PyQt6 now label this quantity **First-period expected coupon · p.a.**
(Korean: **첫 기간 예상 쿠폰 · 연율**). Both narrative languages identify the
first period and refer to the existing period-by-period schedule in the CMS
coupon leg. The first rate alone does not establish a fixed coupon for all
periods or guarantee payment; equal floor and cap can still produce equal
coupons in every period. No new average statistic is introduced.

Flet's AI payload retains the original `coupon` value and adds
`coupon_interpretation` metadata. The native report and commentary payload
carry the same interpretation as a separate section: first-period scope,
annual-decimal units, the existing forward-curve projection without CMS
convexity adjustment, and a reference to the CMS coupon-leg schedule.

The compatibility field, price, margin, Greeks, leg values/details, payoff grid,
hedges and model notes are unchanged. Reverse-convertible coupon and DCD
simple-yield labels keep their existing meanings. Saved historical reports and
external narratives are not rewritten. Language changes affect only the view;
new report exports retain their canonical English evidence.

Verification uses only constructed curves and injected UI/AI boundaries:

```text
python -B -m unittest tests.cms_coupon_disclosure_acceptance \
  tests.desktop_authored_prose_language_acceptance.AuthoredProseLanguageTests.test_structuring_all_products_and_warnings_keep_number_tokens \
  tests.desktop_acceptance.AnalysisAdapterTests.test_structuring_terms_optional_coupon_and_futures_hedge_match_existing_core -v
```

The focused suite covers an independent discount-factor/par-rate oracle,
nonflat/flat/inverted curves, annual/half-year payments, zero coupons, floor/cap
binding and equal floor/cap, Flet and native labels, both narrative languages,
AI/export interpretation, unchanged inputs and non-CMS product regressions.
Independent comparison to base `efd9b0c` preserves all 24 synthetic product
reports exactly (456 top-level field comparisons), including a stub period and
RC/DCD/PPN cases. The numerical-pricer source itself is unchanged.

These checks do not constitute live-market, manual Windows, public-release or
research-gate validation. Other CMS model limitations and study decisions stay
outside this display correction.
