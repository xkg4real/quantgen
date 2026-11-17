"""Model adoption layer on top of the existing gate (roadmap item ⑨-4/2, owner ruling M-21).

The rules come from `docs/nautilus_bridge/MODEL_ADOPTION_CRITERIA_DRAFT_2026-11-04.md` (owner-approved on
2026-11-10, merged to main in PR #92) as decided in rulings M-1 to M-22
(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`). The package sits outside the Nautilus `code_sha256` scope and
outside `core.quant.gate_package.HARNESS_SOURCES`: it calls the gate's functions and never edits them.

Units so far:
- `strategy_rules` (⑨-4/2/a): the strategy comparison lines S-2, S-3, S-4 and S-7, the borderline zones and the
  2027-01-01 holdout guard, as pure functions with no outcome label.

Nothing is imported here, so importing the package loads no numerical code.
"""
