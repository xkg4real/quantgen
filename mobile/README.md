# mobile/ — Flet Android trial bundle (OS-P0-b, OS-A1)

- Owner decision D9 (2026-11-17, recommended part approved): mobile is **not** PySide6. The phone app is a
  reduced Flet companion app; Android first, on the owner's own phone. iOS waits for incorporation and the
  payments decision.
- Build input: `python tools/packaging/stage.py --profile mobile --output <new folder>` copies the Flet runtime
  without Qt (only the Qt-free `quantgen_desktop` text modules the Flet pages import; staging fails if one
  of them imports Qt). It replaces the desktop entry with `mobile/main.py` and uses `mobile/pyproject.toml`
  as its `pyproject.toml`. Both source-to-destination replacements appear in `STAGE_MANIFEST.json`; the
  original desktop entry is not claimed as a staged input. Explicit replacement files must be regular files;
  they may be untracked in a local trial, so the manifest is not proof that every input is committed.
- Current entry: a lightweight internal preview using the existing QUANTGEN palette and QG Interface font.
  It allows checking the shell layout and scrolling. Market data/charts, Quant Lab (Monte Carlo), and real
  login are explicitly unavailable; startup does not import the research/engine/provider/credential modules,
  access caches or accounts, or run calculations. The desktop entry remains unchanged. This avoids its eager
  SciPy/Matplotlib imports, which are excluded from the initial mobile dependency list.
- Build: `flet build apk` in the staged folder (GitHub `platform-build.yml`, manual run only). The trial is
  intended to use debug signing for the owner's phone; no APK/signature/device evidence exists yet. Debug
  signing does not establish Flutter debug build mode. No upload key or store listing before incorporation.
- Unverified until the trial: which dependencies install on Android, APK size, first-start time, and actual
  phone layout/scrolling. Quant Lab Monte Carlo parity with desktop remains unverified and is not supplied by
  this shell; it needs a separately supported calculation/dependency path. No store release or commercial
  launch is claimed by an internal APK or a control-construction test.
