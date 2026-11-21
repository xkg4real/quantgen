# mobile/ — Flet Android trial bundle (OS-P0-b, OS-A1)

- Owner decision D9 (2026-11-17, recommended part approved): mobile is **not** PySide6. The phone app is a
  reduced Flet companion app; Android first, on the owner's own phone. iOS waits for incorporation and the
  payments decision.
- Build input: `python tools/packaging/stage.py --profile mobile --output <new folder>` copies the Flet app
  without Qt (only the Qt-free `quantgen_desktop` text modules the Flet pages import; staging fails if one
  of them imports Qt) and uses `mobile/pyproject.toml` as its `pyproject.toml`.
- Build: `flet build apk` in the staged folder (GitHub `platform-build.yml`, manual run only). The APK is
  debug-signed for the owner's phone; no upload key and no store listing before incorporation.
- Unverified until the trial: which dependencies install on Android, APK size, first-start time, and that a
  Quant Lab result matches the desktop.
