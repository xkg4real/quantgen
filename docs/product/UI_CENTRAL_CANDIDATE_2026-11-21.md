# Central UI integration candidate — 2026-11-21

This work-in-progress branch preserves Claude UI `414eceb90ce42e67113f9cc592229f3f36f37c83` together with main `f065ec92dbce1e1b34e4adb0b6dbed724305a2f4`. It is not a merged release or a replacement for the owner PC acceptance gate.

The merge retains main's number formatting, restores the approved compact Korean/English portfolio empty-state instructions, and preserves both sides of the FACTS history. The redesigned System presence list obtains its existing presence-only loaders through `core.gateway.status_loaders()` in the original KRX/FICC/crypto/quant display order. It still returns only id, label, ready, setting names and note. No key values or probe results are invented.

Bounded Linux validation: 14 distinct selected UI cases passed across the recorded runs, with initial fixture/selector mistakes and the corrected portfolio regression retained in the evidence. The System bridge passes the unchanged 13-case gateway boundary suite (22 files/44 existing sites) and four selected presence/bilingual cases; independent before/after function checks pass three cases. These groups overlap and are not an entire UI-suite pass. Seven routes have Korean wide and English narrow offscreen captures using synthetic inputs. They do not establish Windows, DPI or live-provider results.

`docs/compliance/source-review.json` deliberately preserves the main baseline at this checkpoint. It is stale for the integrated UI and must be reviewed and refreshed on the final dependency tree. There is no source/document-consistency PASS claim for this candidate. The original Qt binding and the approved eight top-level pages/nine market categories remain unchanged.

Before a UI PR or merge: incorporate the latest ordered OS-F2 → DS-H → DS/DIDM → KEY-5/a prerequisites, complete the final source/document review and required CI, record the UI PR website impact, and obtain the existing seven-page owner PC confirmation. The later PySide6 switch still requires its OS go. Full KEY-5 routing and the DS-H home adapter remain distinct unfinished work. Website delivery, application and deployment are unverified.
