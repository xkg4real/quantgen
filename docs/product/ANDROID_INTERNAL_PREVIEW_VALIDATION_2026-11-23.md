# Android internal preview

## Fixed Monte Carlo example

On the home screen, **Quant Lab · Monte Carlo → 예시 계산하기** runs the same GBM calculation used by
the desktop Quant Lab. It uses 30 synthetic closes with fixed weekday labels from April 1 to May 10,
2024. The last close is 105.25. The example simulates five trading sessions with zero log drift, 256
paths and seed 7. The button displays the median and the interval from the 5th to the 95th percentile.

| Host reference | Value shown |
| --- | ---: |
| 5th percentile | 101.01 |
| Median | 104.69 |
| 95th percentile | 108.95 |

The actual Flet 0.85.2 button was invoked twice in each of two fresh host processes using a test
page. All 15 recorded result fields, including the median by session, matched the native desktop
calculation on the same inputs. The home screen loaded before NumPy or the Monte Carlo engine.
The button completed the GBM example with SciPy, GARCH, provider modules and account settings excluded.

The eight mobile acceptance tests passed, including the missing-calculation-dependency message.
For the desktop regression check, the original and updated engines produced identical terminal prices,
percentile bands, sample paths, risk metrics and explanatory notes across five synthetic model/drift
combinations covering GBM, jump, bootstrap and GARCH-t. The mobile control exposes only the fixed GBM
example. Market data, charts and login are outside the preview.

To verify on Android, build the revision containing the button with the manual platform workflow below.
Record the APK size, signature and resolved dependencies, install it on the owner's phone, measure first
start, check layout and scrolling, then press **예시 계산하기** and compare the three displayed values.
The build, dependency installation on Android and phone result remain pending.

### Reading the internal build artifact

After an owner-approved Android build, download the Android artifact from the workflow run. Open
`apk-evidence.json` beside the APK. Match the filename, byte size and SHA-256 to the downloaded APK.
The signer certificate SHA-256 identifies the certificate that Android SDK verification observed.
The artifact name retains `debug` for compatibility. The receipt records the Flutter build mode as
`NOT_OBSERVED`. Identifying that mode requires separate evidence from the Flutter build.

The receipt's overall status covers APK integrity and signature verification. Its dependencies section
lists selected package versions observed in Flet's target staging directory, read from entries directly in
`build/site-packages` and from its Android ABI folders (`arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`), where
serious_python installs packages per ABI (`abi`, `abi_packages`). It flags missing evidence (a package not seen at all;
a package seen in some ABI folders but not in others, `abi_missing`, which makes the status `PARTIAL_METADATA`),
two versions in one place (`conflicting_versions`), ABIs that disagree (`abi_disagreements`) and a direct entry
whose version differs from the ABI folders (`direct_abi_disagreements`); the last three make it
`CONFLICTING_METADATA`. The per-ABI layout comes from
reading serious_python's packaging source; no real Flet build has confirmed it yet, so `nested_layout:
NO_ABI_FOLDERS` with empty package lists on a real run means the layout differs and the versions were not seen.
When verification fails, the job prints the receipt in the log and the tool prints its fixed error codes. Confirm these versions separately. On the phone, measure startup and run the example above.
Record the results alongside the build revision.

## Initial layout-only preview at PR #141

The following record describes the original preview through commit `693e7cbb`, before the calculation
button was added. The test and staging counts below apply to that revision.

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

### Validation performed

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

### Build and remaining evidence at the initial checkpoint

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
