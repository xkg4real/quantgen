# Android internal preview — startup boundary

Base: `dec979a7fae65d5f749e12193fad3d0a9ce8ddf3`.
Branch: `gpt/android-commercial-preview-20261123`.

The initial mobile dependency list excludes SciPy and Matplotlib, but the desktop Flet entry eagerly
imports pages that require them. The mobile stage now uses a separate lightweight entry and records both
`mobile/main.py -> main.py` and `mobile/pyproject.toml -> pyproject.toml` in its manifest. Desktop entry,
calculation code, dependency declarations, data routes, and order/engine policies are unchanged.

This entry is an internal layout/scrolling preview using the existing QUANTGEN palette and QG Interface
font. Market data/charts, Quant Lab Monte Carlo, and login are explicitly unavailable. Constructing these
controls does not establish APK startup, accessibility, Android dependency support, commercial rights,
desktop feature parity, or a commercial launch. No data-provider/account/research/engine modules are
imported by the mobile entry.

## Validation performed

- Pinned Flet 0.85.2: 8 new mobile entry/staging tests and 3 existing packaging tests passed.
- Independent guarded confirmation: the same 11 methods passed, with no errors, failures, or skips;
  network, environment/credential access, heavy imports, source writes, and server startup were blocked.
- Actual mobile staging produced 399 allowlisted inputs. All selected bytes matched the verified source;
  compared with the original mobile stage, only the target `main.py` bytes changed. Both replacements are
  explicitly recorded rather than attributed to the desktop entry.
- Independent final-source check covered 474 selected public files; 469 original inputs, desktop main,
  core/data, source HEAD/index, and original stage were preserved.
- Earlier guard diagnostics are retained separately: one bootstrap stopped before collection; later
  attempts passed the tests but failed aggregate guards on interpreter cache/archive probes. They do not
  replace the final clean guarded result and are not erased as successful attempts.

Reproduce host checks with the declared Flet version, in an isolated environment:

```sh
python -B -m unittest tests.mobile_startup_acceptance tests.packaging_policy_acceptance -v
python -B tools/packaging/stage.py --profile mobile --output /absolute/new/trial-folder
```

Tests create synthetic temporary Git repositories. The real-control test constructs a FakePage only;
it does not run Flet's application server. Hosts without Flet skip that method; such a run is not the
11-method confirmation recorded above. The runtime workflow explicitly runs the new test module and
also triggers on edits to it.

## Build and remaining evidence

The task-private Flet/CLI 0.85.2, JDK 17.0.13, Android SDK manager 12.0, Android 35r2, build-tools 34.0.0,
and platform-tools 37.0.3 were installed and verified by eight component commands. Required Flutter
3.41.7 is not installed: its official SDK and the mobile wheel host returned CONNECT 403 under the
existing cloud policy. The policy was not changed or bypassed. Component checks are not an APK build.

The existing `platform-build.yml` can build an internal Android artifact by manual dispatch on this
branch. For Android only: `android=true`, `windows=false`, `macos=false`, `font_probe=false` and the
existing `qt_binding=PyQt6` input. This change does not add automatic build triggers or release tags.
The trial intends debug signing; neither the actual signature nor Flutter build mode is proven here.

Still required: an actual APK and dependency-resolution record, artifact size/signature inspection,
owner-phone install/startup/layout/scrolling evidence, accessibility checks, a supported Quant Lab
calculation path and desktop-result comparison, and account/commercial-release requirements. OS-A1
and the overall Android product remain open. No upload key, store submission, PG activation, real
provider/model call, order, ledger execution, or website deployment was performed.
