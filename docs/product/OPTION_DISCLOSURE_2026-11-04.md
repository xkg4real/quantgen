# Option board: what the box, hedge mean and MFIV are (§10 M4-N4, M4-N7, M4-N9)

The owner decided on 2026-11-03 not to recover GPT's private options work. Claude
redid these three §10 items from scratch on product main `c1a4e97`. Each item went
through two steps:

- an analyst reproduced it on synthetic boards;
- a separate reviewer tried to refute the reproduction and the proposed fix.

The fixes below include the reviewers' corrections. `core/ficc/equity_deriv.py`
is unchanged.

## M4-N7: the GBM hedge mean is zero by construction

The product runs `hedge_pnl_simulation` with σ_true = σ_h. The default GBM engine
passes no `sigma_true`, drift or cost, so the expected hedge P&L is exactly 0 and
the break-even vol equals σ_h up to noise. The Flet tile coloured the sign of that
noise green or red, and the narrative said the hedge "earns" it.

On the synthetic board, seeds 1–20 gave 11 green and 9 red tiles. A 100,000-path run
gave +0.08 bp (SE 0.12 bp).

| Surface | Change |
| --- | --- |
| `snapshot` | Records `hedge_scope` from the arguments it actually passed: `ZERO_BY_CONSTRUCTION` for GBM, `MODEL_RESULT` for GARCH-t. |
| Readers | Claim nothing when `hedge_scope` is absent. A σ_true ≠ σ_h simulation is never labelled. |
| Flet tile | Neutral `text` token under GBM. Tooltips say the sign is Monte Carlo noise and the break-even equals σ_h by construction. A notice states it. |
| Narratives (EN/KO) | "has a simulated mean P&L of" in place of "earns … on average". Under GBM they add the disclosure. |
| AI payload `hedge` | Adds `expected_mean_status`, `expected_mean_pnl_bp` and `scope`. |
| Native pane | A localized disclosure line and a `hedge_scope` export section. |

GARCH-t keeps its coloured sign: there the mean is a model result. On the synthetic
board it is +6.9 bp with z ≈ 9.

## M4-N9: MFIV comes from a finite strike strip

`mfiv()` sums only the quoted strikes. KIS boards are fetched at spot ±10%
(at most 160 series), and the omitted wings bias the variance downward.
`mfiv()` already returned `k_min`/`k_max`, but every surface dropped them.

| Surface | Change |
| --- | --- |
| `mfiv_strip(s)` | Computed on the fly. Returns the range as forward moneyness and as approximate ATM-vol standard deviations, which overstate the put wing's coverage on a skewed board. |
| Narratives (EN/KO) | State the range and the downward bias with the same numbers. |
| Native pane | Adds a `Model-free IV strike range · % of forward` row and an `mfiv_strip` export section. |
| Flet | MFIV tooltip and a `MFIV strike range` tile. |
| AI payload | Adds `mfiv_strip`. The Flet AI receives only the payload, so this key is how it learns of the truncation. |

The register's ±10% comparison (−0.07/−1.74/−1.27 vp) used a 91-strike board that
starts at 1012.5, outside the KIS filter. With the 90-strike KIS ±10% filter the
figures are −0.07/−1.80/−1.31 vp. The register itself is not edited here.

## M4-N4: an adjacent-strike box is a quote check, not a funding rate

The box uses the strikes on either side of F, 2.5 points apart. At T = 20 days, 0.01
point of box price moves the implied rate by about 731 bp. On KIS a box was priced
when any quote on the board was two-sided, so its four "mids" could be last prints.

| Surface | Change |
| --- | --- |
| Validation | `box_check` prices the box only when all four legs have two-sided quotes. Otherwise it is `NOT_RUN` and names the missing legs. This is the only change to when a value appears. |
| Values | `ED.box_rate`, the strike choice and the shown rate are unchanged when it is priced. |
| Disclosure | Sensitivity in bp per 0.01 point, and the rate at the quoted asks (bought) and bids (sold). On the synthetic board it ranges from −224.92% bought to +263.96% sold. |
| Labels | "Box rate · adjacent strikes, mid quotes" (Native) and "Box rate (quote check)" (Flet). |
| Narratives | Say "quote-quality check, not a funding-rate estimate". They no longer state the box as "a KRW funding rate" or give its bp gap to CD. |
| AI payload | Adds `box_check`; `box_rate` is kept. |

Widening the box to about 100 points would cut the sensitivity about 40 times. It
changes the shown number, so it is a model change left to the owner.

## Valid inputs are unchanged

Old main and this branch were run on the synthetic board for GBM and GARCH-t at 100
and 3,000 paths. Across all four cases the following are identical:

- the `pnl`, `realised_vol` and `gamma_term` arrays (by sha256);
- every simulation scalar;
- `box` and `mfiv`;
- every existing payload value.

Only `box_check`, `mfiv_strip` and three `hedge` keys are added.

## Not changed

- `core/ficc/equity_deriv.py` and `docs/asset_expansion_study.py`.
- The stored study cards, gates, ledgers and the registers.
- The GARCH-t sign colouring (a separate limitation).
- The `horizon_days=1` validation gap.
- Real KIS boards and the Windows screen are NOT_RUN.

## Checks

`tests/option_disclosure_acceptance.py` has 11 tests (offline). Run it with
`python -m unittest tests.option_disclosure_acceptance -v`. These existing suites
still pass:

- quote coverage, Native and Flet;
- authored-prose language parity;
- market diagnostics language;
- desktop market;
- AI payload;
- the `equity_deriv` and `ui/derivatives_page` self-checks.
