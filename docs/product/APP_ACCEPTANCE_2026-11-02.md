# Application runtime acceptance — 2026-11-02

The Windows product remains PyQt6 and the browser product remains Flet. This
change fixes startup when a persisted locale is a non-string value: the existing
English fallback keeps the settings screen usable, and selecting a supported
locale repairs the preference through the existing QSettings path.

## Reproducible automated checks

`tests.flet_runtime_acceptance` constructs all 19 real Flet routes with temporary,
disarmed state, an inert startup hook and blocked provider calls. It exercises
English/light/1440px and Korean/dark/390px navigation. It does not launch the live
Flet browser client or prove visual accessibility.

`tests.desktop_startup_acceptance` covers malformed locale types and a temporary
QSettings repair/restart cycle. The installed-wheel `tools/packaging/smoke_desktop.py`
runs outside the source checkout and checks the six native workspaces, a real
worker with injected synthetic prices, locale/theme switching, preference repair,
and JSON/ZIP export roundtrips. The canonical run keeps `verdict=NOT_RUN` and
synthetic provenance. Network and protected paths are blocked.

`tests.desktop_responsive_tools_acceptance` reproduces switching away from a
large result, returning to Macro and resizing Signals from wide to narrow and
back in both languages. The selected Markets/Risk tab determines its own size;
inactive tools no longer force horizontal clipping or stretch Macro input
labels. ChartStudy measures wrapped commentary at its actual available width.
Local offscreen captures cover ETF, Signals, Structuring and Macro in English
and Korean at 1440px and 1000px. These are renderer checks, not physical-device
or assistive-technology acceptance.

The runtime workflow repeats the bounded checks on its declared Windows and
Ubuntu matrix. A green job now retains only its allowlisted, verified wheel for
seven days under **Actions → Runtime packaging smoke → Artifacts → QUANTGEN-wheel**.
Use the artifact whose commit matches the reviewed PR/main revision. A workflow
being configured is not proof that a particular run passed; inspect that run.

After extracting the wheel on Windows, install it in an isolated Python virtual
environment with `python -m pip install ".\quantgen-<version>-py3-none-any.whl[desktop]"`
using the actual downloaded filename, then run `quantgen-desktop`. This is a wheel
installation path, not a signed standalone Windows installer. Installing package
dependencies may require internet access. Existing provider keys are not bundled.

## Limits

Local evidence used Linux and isolated synthetic inputs. Windows CI is an
automated runner check; actual user-device installation, display scaling,
taskbar pin/cache, native file dialogs, keyboard/screen-reader acceptance and
real Claude/provider requests remain separate observations. No Step7A approval,
official ledger record, Nautilus pilot, live trade, policy approval or external
product release follows from these checks.
