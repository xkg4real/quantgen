# Repository agent instructions

Read `CLAUDE.md` for the existing research handoff and ownership rules. The UI
website follow-up below does not transfer another session's active task or
change research gates, data rights, or deployment configuration.

## UI base app (owner decision UI-D1..D4, 2026-11-11)

The owner decided that every agent (Claude, GPT) builds the UI on **one app: the native PyQt
app** (`quantgen_desktop/`, `python -m quantgen_desktop`, `Start-QUANTGEN-Desktop.cmd`). Fix
screen issues there, even when the owner's screenshot shows the Flet app (`main.py`, `ui/*.py`),
which is kept but is not the base for new UI work. The owner's 14 issues of 2026-11-10 follow
Claude's fixes (PR #98) ported to native; the rest of the native UI keeps GPT's PR #89 compact
layout helpers; font: `assets/fonts/qg-interface*.otf` (Pretendard-derived) with the tracking and weights of owner
decision UI-D6 (`quantgen_desktop/typography.py`). Before any UI
work, read the owner-decision block at the top of `UI_SESSION_CURRENT.md` and the `⑬-2/` rows of
`LEDGER.md` on the `handoff` branch, so two agents never change different apps or the same screen.

## UI changes and website follow-up

The owner's 2026-10-31 instruction requires reporting UI changes to the owner
and immediately passing their website impact to **웹사이트 작업공간(AWS)**.
After implementing and verifying a UI improvement, follow
[`docs/product/UI_WEBSITE_SYNC.md`](docs/product/UI_WEBSITE_SYNC.md) in the same
work session. This includes native UI, Flet/browser UI, branding and UI copy.

Record the change, commit/PR, verification and browser applicability under
`docs/product/ui_website_updates/`. Use the supported chat messaging tool to send
the handoff to the exact destination chat when available. If the tool is absent
or delivery fails, retain a queued record and tell the owner; a committed file
is not a delivered chat message. Do not claim website application or deployment
without the receiving workspace's evidence.
