---
status: taken
reason: manual
from: gpt
task: owner-product-workflow-20261029
cycle: 2026-10-27
done_ids: none
next_ids: ⑫-3, ⑬-1, ⑬-2, ⑨-2, ⑩-1, ⑩-2, ⑪-1
updated_at: 2026-10-30T13:37:20+09:00
stale_after_hours: 3
waiting_on: none
work_branch: gpt/pyqt6-desktop-20261030
work_commit: f466c4b87747f4387bf3268c494eed026fad3206
uncommitted_changes: yes
pr: https://github.com/xkg4real/quantgen/pull/16
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: unknown
session: codex
execution_id: 1a2e45b4-a6df-43f8-a011-c332797c7b02
handoff_id: 2026-10-27/owner-product-workflow-20261029/a45bca0b6c73178729d1c3d21a0cd7bbbb15bd75
---

# Owner-directed product work — ownership notice

The owner directly requested continuation: native PyQt6 desktop application, retained Flet browser application, shared calculation core, approved A/F1 design. This manual task resumes the owner's checkpoint; it is not an automatic stale takeover. Work starts from the latest integrated product main (PR #15), preserving earlier handoff records and automatic weekly eligibility. The design-only public-site HTML artifact is validated and delivered privately; the owner will upload it and explicitly excluded live website deployment from this task. Native Qt first-slice source is pushed in draft PR #16 with local fixture/installed-wheel checks passed; full screen migration remains in progress. No research approval fields, frozen work, protected stores, orders, TRADEGEN or shared environment settings may change. Consolidated Claude delivery remains deferred until completion or the owner-requested usage/runtime checkpoint.

## Current verified checkpoint

Draft PR #16 contains native Home/Markets/Bonds/Monte Carlo/portfolio/session export. Commit f466c4b87747f4387bf3268c494eed026fad3206 passed runtime packaging CI 41003116686 on Ubuntu Python 3.12 and Windows Python 3.12/3.14. Rates and FX adapters/native panes are now being implemented locally; those additions are not yet pushed or verified. Full desktop parity is incomplete; Flet remains unchanged. The historical report below is superseded for PR-F, Home integration and UI PR/merge authorization; consolidated reconciliation will replace it at this task's handoff.

# Historical prior report

## 0. 한 줄 요약
The owner requested a progress/decision report and intends to continue through Codex
while Claude is unavailable. The report is delivered privately. This is a reporting
checkpoint, not completion of every inherited task and not a claim that all remaining
work needs approval. **PR-F packaging/CI is unfinished and is the next unblocked task.**

## 1. 목표와 최신 요청
Continue unblocked Claude handoff work, explain approval-dependent items, prepare
the selected A/F1 UI for actual use, and reconcile completed/remaining work with the
roadmap/project notes. Latest clarification: the owner views a local Flet server on
their PC, not an already deployed app. They asked for completed work, unfinished work,
recommendations and next steps in a document.

## 2. 근거
Read these at work_commit:
- docs/nautilus_bridge/CONTINUATION_STATUS_2026-10-29.md
- docs/nautilus_bridge/REMAINING_WORK_2026-10-29.md and original 2026-10-27 roadmap
- docs/nautilus_bridge/HANDOFF_MANUAL_2026-10-29.md
- docs/nautilus_bridge/O2_O15_DECISION_FORM_2026-10-29.md
- docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-Q-explainer_2026-10-29.md
- docs/nautilus_bridge/PT04_VALIDATION_2026-10-29.md
- docs/nautilus_bridge/drafts/PR_B_IDENTITY_DESIGN_2026-10-29.md
Read latest LEDGER in full before deciding a new ID is unfinished.

## 3. 판단 기록
The earlier return ended too soon: PT-04, PR-B design and PR-F were available work.
This continuation completed the first two. PR-F was inspected, not implemented;
do not mislabel it as approval-blocked. The private report distinguishes inherited
Claude test history from Codex's own focused checks.

Project notes contained stale calendar-unsigned and R1–R5 pending wording. Latest
GitHub ledger/decision records already complete those older items. Notes were read
but not modified. The report is not a formal external Nautilus review or approval.

## 4. 추가 완료
- ②-5/c: 7db616c6d5ccbe82e8d64df04d83cf1d3127e86e.
  Partial FRED curves withhold unavailable long-end metrics and refuse prices
  outside observed coverage, including fitted/shocked curves. 6 new tests plus
  existing FICC 57 and Bonds 33 PASS (96 total). Complete/synthetic baseline unchanged.
- ⑫-2/a: 00d32eb11559bc32e36a879933719392baf575ca.
  PR-B identity design and 17 alias cases; 3 characterization tests PASS.
  BTCUSD/EURUSD/UNKNOWN defects reproduced. Frozen resolver NOT_IMPLEMENTED.
- 45e2d3ecff14f9273d6e97bfc1b6b1c0bd0a5c1a records status and next steps.

Earlier completed sub-items remain in LEDGER: ①-2/4/a, ⑫-0, ⑫-1/a,
⑫-1/a/2, ⑬-2/a. Do not repeat them. The current branch already contains
e1271a7 UI, the calendar patch and status cherry-picks, plus Claude's work.

## 5. UI 적용의 정확한 상태
UI-only main candidate: gpt/ui-apply-main-20261029 /
e46f81fca513ca39983d31ac5131e5f6e67b0543, based on main 950f25e.
15 UI/status fixture tests and status provenance check PASS. It excludes Claude's
Nautilus, PT-04 and calendar-loader changes. See docs/UI_APPLY_2026-10-29.md there.

Automatic approval review rejected creating its public PR: the retained no-PR/
no-merge instruction was not clearly revoked by the later UI request. No PR number
exists; no main push/merge occurred. Do not bypass the rejection via another tool.
Owner must clarify UI-only PR creation/merge if they want that integration.

The owner's running PC needs a checkout update and app restart. Cloud localhost
does not reach the PC. No remote PC action or public hosting was performed.
Home counts/market values/recent runs/distributions remain honestly unconnected.
Actual Flet layouts were rendered earlier with inert engine fixtures, not live data.

## 6. 다음 작업과 완료 조건
1. **⑫-3 PR-F now:** fix dependency/module/resource packaging in excluded-path copy;
   verify clean install includes statsmodels, tools.status, assets/fonts/calendar/
   recorded-status resources. Add minimal CI; report real Linux/Windows runs separately.
   No extra research approval is required. Do not claim Windows/CI success from definitions.
2. UI integration only after clear PR/merge authorization; preserve PC local edits.
3. ⑫-2 actual resolver: owner 12.8/K-f/frozen-harness scope first. Keep cost-table
   values, gates and past results intact. Use prepared alias matrix.
4. ⑨-3a: rev2/10.2 A answers; shadow first, comparison and validation before ⑨-3d.
5. ④-2/O8/O11 then ④-3, Windows/egress/host evidence, provider parity,
   SPY pilot then conditional BTC. Do not create the actual E1 ledger here.
6. ⑬-1/⑬-2: provenance-preserving read-only adapters for connected Home;
   no protected store traversal, fabricated values or implicit new ledger.

## 7. 保護範囲 / 하지 말 것
.env, four protected caches, actual ledgers, frozen research/preregistration/holdout:
do not read or modify. No order-path, TRADEGEN, shared environment/security or owner
approval-field changes. Do not manually edit AUTO_STATE. No public raw transcripts,
private report or private source links. Full suite was not run in this continuation.

## 8. 남은 사용자 결정
Nautilus O2–O15 (especially O8 review route, O11 E1 initialization);
PR-B 12.8/K-f/frozen-harness scope; R3 rev2/10.2 A; UI-only PR/merge scope;
②-5 §10 classification, BS-21, future model/data/public-distribution decisions.
Existing migration approval, O1 and R1–R5 are not requested again.
waiting_on owner here means the requested report has been delivered and a next
direct task is awaited; it does not make PR-F dependent on owner research approval.

## 9. Codex / Claude 재개 지시
The owner may continue in this Codex conversation immediately with a direct request.
Claim latest CURRENT using exact SHA + unique execution ID and remote read-back.
Branch from work_branch/work_commit; compare latest LEDGER before editing.
Read CONTINUATION_STATUS and the latest roadmap; start PR-F unless the owner selects
another task. Do not redo old IDs, reapply UI cherry-picks or merge the Nautilus PR
as part of UI. Old returned-cycle automatic eligibility remains next Thursday
2026-11-05 00:00 KST; this manual continuation does not reset completed IDs.
