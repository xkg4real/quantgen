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
- The home screen uses the QUANTGEN palette and QG Interface font. Under **Quant Lab · Monte Carlo**, tap
  **예시 계산하기** to simulate five sessions from 30 fixed synthetic closing prices. The example uses the
  desktop geometric Brownian motion (GBM) calculation with zero log drift, 256 paths and seed 7. The
  numerical modules load on the tap. Market data, charts and account login are outside this preview.
- On the host, the button displayed a median of **104.69** and a middle 90% range of **101.01–108.95**
  from a starting price of 105.25. Use these values when checking the same button on the owner's phone.
  The earlier layout-only preview and both sets of host results are recorded in
  [Android preview validation](../docs/product/ANDROID_INTERNAL_PREVIEW_VALIDATION_2026-11-23.md).
- Build: `flet build apk` in the staged folder (GitHub `platform-build.yml`, manual run only). The trial is
  intended to use debug signing for the owner's phone; no APK/signature/device evidence exists yet. Debug
  signing does not establish Flutter debug build mode. No upload key or store listing before incorporation.
- Record the APK size, signature and installed dependencies, then measure first start and check layout,
  scrolling and the calculation on the owner's phone. The host result supplies the reference for the
  device comparison. Actual APK and phone evidence are pending.
