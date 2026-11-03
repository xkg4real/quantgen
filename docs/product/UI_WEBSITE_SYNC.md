# UI changes → website workspace

The owner requested on 2026-10-31:

> UI 개선이 되는 즉시 변동 내역을 "웹사이트 작업공간(AWS)"로 보내서 웹사이트에도 반영이 되어야 하는 부분이 즉시 반영될 수 있게 수정해주세요.

Source: **QUANTGEN UI 개선**. Destination: **웹사이트 작업공간(AWS)**.
This is an agent workflow with a durable change queue, not a running notification
service. It supplements the existing main-session handoff without taking its
ownership or replacing its research ledger.

## On every completed UI improvement

1. In the same work session, create or update one record per source PR at
   `docs/product/ui_website_updates/PR-<number>.json`. Include the problem and
   resulting behavior, changed files, source commit/PR, tests and limitations.
2. Classify website impact: shared/browser change, native-only source change,
   or review required. Name the corresponding browser surfaces and concrete
   follow-up. Do not copy PyQt-only drawing code into a browser implementation.
3. Locate the destination chat by its exact title with supported chat tools.
   Send the record/link and a concise action request immediately after UI
   verification. Update it with the merge commit when available; retain the same
   record ID on retries. An already delivered, unchanged record is not resent.
4. Record a successful messaging-tool receipt before changing `delivery.status`
   from `queued` to `sent`. A receiving-chat acknowledgement is separate evidence.
   If messaging is unavailable, preserve `queued`, record the reason and report
   that delivery is blocked in the owner's completion update. Never modify chat
   databases or use undocumented endpoints to imitate a sent message.
5. The website workspace checks each item against its actual website source.
   Apply relevant UI/copy/asset changes promptly within the authorized website
   scope, verify affected pages and record its commit, checks and URL. Mark an
   item `not_applicable` only with a reason. Keep code application and deployment
   separate; neither a merged native PR nor a sent message proves deployment.

Report delivery, website application and deployment as separate observed states.
Records must not contain credentials, AWS login codes, account data, protected
research content or private chat transcripts. The workflow needs no new AWS
credentials, environment changes or duplicate monitoring schedule.

## Current handoff: PR #36

[`ui_website_updates/PR-36.json`](ui_website_updates/PR-36.json) contains the
merged native chart fix and browser review request. Native fixes address clipped
large-price ticks, overlapping legends and clipped footers.

The retained Flet browser uses Matplotlib images in `ui/qcharts.py`, including
`bbox_inches="tight"`, rather than `quantgen_desktop/charts.py`. That source
difference is evidence for a separate browser check; it is not proof that a live
website passed. No website URL or implementation was established by reading the
destination chat, which currently records AWS Toolkit setup.

At setup, the available chat tools can list/read/wait for chats but cannot send
messages or wake the destination. PR #36 is therefore **queued, not sent**. Its
website review, application and deployment remain unverified. Resume dispatch
when the supported chat messaging tool is available.
