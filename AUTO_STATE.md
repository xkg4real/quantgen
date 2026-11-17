---
kind: auto_snapshot
reason: periodic
created_at: 2026-11-17T18:09:19+09:00
source_branch: claude/friendly-bardeen-r6xe8f
source_head: e01e152
upstream: origin/claude/friendly-bardeen-r6xe8f
patch_base: 7402a43
unpushed_commits: 38
uncommitted_files: 17
patch: AUTO_STATE.patch (`git apply AUTO_STATE.patch` on patch_base)
usage_pct: unknown
usage_resets_at: unknown
session: c958d211-15cf-56b3-aa1e-f5e530ec719f
snapshot_key: none
current_md_updated_at: 2026-11-14T03:07:32+09:00
current_md_status: returned
---

# 자동 스냅샷 (모델 없이 생성)

스크립트가 git 상태만 보고 만든 파일입니다. 작업의 목표, 근거, 다음 할 일은 `CURRENT.md`에 있습니다.
`CURRENT.md`의 `updated_at`이 이 파일의 `created_at`보다 오래됐다면, 그 사이에 바뀐 것은 아래 git 상태로
확인하세요.

## 최근 커밋

```
e01e152 Merge pull request #120 from xkg4real/gpt/ui-interaction-delivery-20261114
cedf910 docs: record native UI delivery and queued website follow-up
51d7ffb Merge pull request #119 from xkg4real/gpt/market-menu-click-20261114
b8d5ac8 fix(ui): repair market clicks and refine research chart interactions
73ed4bf Merge pull request #118 from xkg4real/gpt/chart-ui-delivery-20261113
d6f1217 Record merged chart tools and Windows launch instructions
3db656c Merge pull request #117 from xkg4real/gpt/chart-risk-reward-20261113
3951195 Add draggable chart risk reward and conditional indicator guidance
1006b5e Merge pull request #115 from xkg4real/gpt/ui-market-navigation-guide-20261113
d743695 Merge PR115 UI with current main documentation
eba94f0 Merge pull request #116 from xkg4real/gpt/order-safety-design-20261113
b323121 docs: record consistency review for order safety design draft
e710428 docs: draft approved M-12 order safety boundaries and evidence gates
5d98193 Dispose market fixtures before progressive history checks
8f69c73 Keep stock chart pinned after nested market layout changes
```

## 푸시되지 않은 커밋

```
e01e152 Merge pull request #120 from xkg4real/gpt/ui-interaction-delivery-20261114
cedf910 docs: record native UI delivery and queued website follow-up
51d7ffb Merge pull request #119 from xkg4real/gpt/market-menu-click-20261114
b8d5ac8 fix(ui): repair market clicks and refine research chart interactions
73ed4bf Merge pull request #118 from xkg4real/gpt/chart-ui-delivery-20261113
d6f1217 Record merged chart tools and Windows launch instructions
3db656c Merge pull request #117 from xkg4real/gpt/chart-risk-reward-20261113
3951195 Add draggable chart risk reward and conditional indicator guidance
1006b5e Merge pull request #115 from xkg4real/gpt/ui-market-navigation-guide-20261113
d743695 Merge PR115 UI with current main documentation
eba94f0 Merge pull request #116 from xkg4real/gpt/order-safety-design-20261113
b323121 docs: record consistency review for order safety design draft
e710428 docs: draft approved M-12 order safety boundaries and evidence gates
5d98193 Dispose market fixtures before progressive history checks
8f69c73 Keep stock chart pinned after nested market layout changes
795165c Merge pull request #114 from xkg4real/gpt/pilot-readout-btc-ra-20261113
043b2cd Avoid native icon event re-entry during Windows window teardown
5ddb2a6 Show arriving quotes after an earlier empty market response
aeb7577 Keep market menu callers compatible and cancel pending hover on close
684b226 Improve market navigation, first quotes, full indicator guide and Windows branding
661c6b8 docs: reference full readout provenance from ruling log
a90c90b Record BTC-ra owner ruling and verified Pilot 1 readout
7e05673 Merge pull request #113 from xkg4real/gpt/ui-pr112-completion-record-20261113
48dfb9c Record merged UI release and verified completion handoff
d01ec73 Merge pull request #112 from xkg4real/gpt/ui-d11-d15-20261113
c45adc8 Dispose chart test windows and isolate long rendering suites
4ab349f Cancel initial-page scroll when its window is destroyed
b658cde Complete progressive charts and guided research workspaces
30c5546 Checkpoint progressive charts and guided research UI for visual review
f74c63c Fix wrapped analysis categories clipped at narrow widths
5b7f7dd Preserve negative signs and Korean text in searchable chart PDFs
5572e78 Verify report format selection and queue UI handoff for AWS
d46ca5e Continue Claude UI handoff: market menus, US Q-SCORE, chart reports and daily ranks
96a9965 Merge remote-tracking branch 'origin/main' into gpt/ui-d11-d15-20261113
9e00bf3 Merge pull request #111 from xkg4real/claude/adoption-outcome-20261112
73be590 Merge main 0786200 (PR #109, native app UI decisions) into the adoption outcome branch
351db88 ⑨-4/2/c verifier round: B-Q1 after a gate REVISE, lines checked before use, S-5/S-6/D-4 marked unchecked
5f08973 ⑨-4/2/c: strategy outcome assembly under the owner's answers B-Q1, B-Q2, B-Q3
```

## 커밋되지 않은 변경

```
M .github/workflows/runtime-smoke.yml
 M core/education/catalog.py
 M core/education/reading_cues.py
 M docs/compliance/12-claims.md
 M docs/compliance/FACTS.md
 M quantgen_desktop/app.py
 M quantgen_desktop/indicator_guide.py
 M quantgen_desktop/indicator_picker.py
 M quantgen_desktop/market_summary.py
 M quantgen_desktop/owner_ui_language/stock.py
 M quantgen_desktop/stock_detail_style.py
 M tests/desktop_home_markets_shell_acceptance.py
?? core/education/outlook.py
?? quantgen_desktop/market_hub.py
?? tests/desktop_indicator_scroll_acceptance.py
?? tests/desktop_market_hub_acceptance.py
?? tests/indicator_outlook_acceptance.py
```

`patch_base` 이후 바뀐 파일 (푸시 안 된 커밋 포함):

```
.github/workflows/runtime-smoke.yml                |  24 +-
 core/adoption/strategy_rules.py                    | 366 ++++++++++-
 core/education/catalog.py                          | 236 +++++++
 core/education/indicators.py                       |   5 +
 core/education/reading_cues.py                     |  70 ++
 core/education/signal_context.py                   | 119 ++++
 core/market/detail_model.py                        |  15 +-
 core/market/detail_svg.py                          |  19 +-
 core/market/presentation.py                        |   6 +-
 core/market/qscore_rankings.py                     |  52 ++
 core/market/rankings.py                            |  14 +-
 core/market/risk_reward.py                         |  39 ++
 core/market/routing.py                             |  25 +-
 core/market/screen.py                              |   4 +
 core/market/stock_report.py                        | 511 +++++++++++++++
 core/research/qscore.py                            |  42 +-
 data/kis_workspace.py                              |  42 +-
 docs/compliance/01-privacy-policy.md               |  29 +
 docs/compliance/02-terms-of-service.md             |  29 +
 docs/compliance/03-refund-policy.md                |  29 +
 docs/compliance/04-cookie-policy.md                |  29 +
 docs/compliance/05-cookie-consent.md               |  29 +
 docs/compliance/06-form-consent.md                 |  29 +
 docs/compliance/07-data-minimization.md            |  29 +
 docs/compliance/08-third-parties.md                |  29 +
 docs/compliance/09-dark-patterns.md                |  29 +
 docs/compliance/10-pricing.md                      |  29 +
 docs/compliance/11-testimonials.md                 |  29 +
 docs/compliance/12-claims.md                       |  35 +
 docs/compliance/13-alternative-text.md             |  29 +
 docs/compliance/14-contrast.md                     |  29 +
 docs/compliance/15-keyboard.md                     |  29 +
 docs/compliance/16-business-information.md         |  29 +
 docs/compliance/17-children.md                     |  29 +
 docs/compliance/18-marketing-email.md              |  29 +
 docs/compliance/19-licenses.md                     |  29 +
 docs/compliance/20-deletion.md                     |  29 +
 docs/compliance/FACTS.md                           | 146 ++++-
 docs/compliance/source-review.json                 | 361 ++++++-----
 docs/nautilus_bridge/OWNER_RULINGS_LOG.md          |  56 ++
 .../product/ADOPTION_STRATEGY_CHECKS_2026-11-10.md | 245 ++++++-
 docs/product/CHART_RISK_REWARD_2026-11-13.md       |  62 ++
 docs/product/ORDER_SAFETY_DESIGN_2026-11-13.md     | 169 +++++
 docs/product/UI_D11_D15_2026-11-13.md              |  49 ++
 docs/product/UI_INTERACTION_POLISH_2026-11-14.md   |  59 ++
 docs/product/UI_MARKET_GUIDE_2026-11-13.md         |  61 ++
 docs/product/ui_website_updates/PR-112.json        |  44 ++
 docs/product/ui_website_updates/PR-115.json        |  55 ++
 docs/product/ui_website_updates/PR-117.json        |  46 ++
 docs/product/ui_website_updates/PR-119.json        |  51 ++
 quantgen_desktop/app.py                            | 301 ++++++---
 quantgen_desktop/bonds.py                          |   9 +
 quantgen_desktop/choice_cards.py                   |  99 +++
 quantgen_desktop/indicator_guide.py                | 327 +++++-----
 quantgen_desktop/indicator_picker.py               | 257 +++++++-
 quantgen_desktop/localization.py                   |  11 +-
 quantgen_desktop/market_chart.py                   |  78 ++-
 quantgen_desktop/market_destinations.py            | 164 +++++
 quantgen_desktop/market_menu.py                    | 253 ++++++++
 quantgen_desktop/market_rankings.py                | 118 +++-
 quantgen_desktop/market_summary.py                 |  11 +-
 quantgen_desktop/owner_ui_language/__init__.py     |   2 +-
 quantgen_desktop/owner_ui_language/report.py       |  38 ++
 quantgen_desktop/owner_ui_language/stock.py        | 106 +++
 quantgen_desktop/paper.py                          |   3 +-
 quantgen_desktop/portfolio.py                      |   5 +
 quantgen_desktop/rail_menu.py                      | 227 ++++---
 quantgen_desktop/ranking_scores.py                 |  48 ++
 quantgen_desktop/research_style.py                 |  45 ++
 quantgen_desktop/risk_reward.py                    | 464 ++++++++++++++
 quantgen_desktop/shell_rail.py                     | 104 +--
 quantgen_desktop/stock_detail.py                   | 211 +++++-
 quantgen_desktop/stock_detail_side.py              |  12 +-
 quantgen_desktop/stock_detail_style.py             |  50 +-
 quantgen_desktop/stock_qscore.py                   | 658 +++++++++++++++++++
 quantgen_desktop/stock_report.py                   | 209 ++++++
 quantgen_desktop/tools.py                          |  24 +-
 quantgen_desktop/typography.py                     |  26 +-
 quantgen_desktop/windows_branding.py               |  63 ++
 quantgen_desktop/workspace_guide.py                | 131 ++++
 results/RULINGS.md                                 |  56 ++
 tests/adoption_strategy_rules_acceptance.py        | 399 +++++++++++-
 tests/desktop_compact_ui_acceptance.py             |   4 +-
 tests/desktop_home_live_acceptance.py              |  18 +-
 tests/desktop_home_markets_markets_acceptance.py   |  10 +-
 tests/desktop_home_markets_shell_acceptance.py     | 708 +++++----------------
 tests/desktop_indicator_guide_acceptance.py        | 107 ++--
 tests/desktop_market_chart_acceptance.py           |   4 +-
 tests/desktop_market_first_paint_acceptance.py     |  76 +++
 tests/desktop_market_layout_acceptance.py          |  24 +-
 tests/desktop_market_tabs_acceptance.py            |   7 +-
 tests/desktop_markets_watchlist_acceptance.py      |   5 +-
 tests/desktop_risk_reward_acceptance.py            | 222 +++++++
 tests/desktop_stock_detail_acceptance.py           |  27 +-
 tests/desktop_windows_branding_acceptance.py       |  54 ++
 tests/desktop_workflow_guidance_acceptance.py      |  89 +++
 tests/desktop_workspace_readability_acceptance.py  |  53 ++
 tests/indicator_catalog_acceptance.py              |  60 ++
 tests/indicator_signal_context_acceptance.py       |  87 +++
 tests/market_progressive_acceptance.py             | 103 +++
 tests/market_rankings_acceptance.py                |   2 +-
 tests/qscore_acceptance.py                         |   4 +-
 tests/qt_fixture_cleanup.py                        |  19 +
 tests/ui_followup_acceptance.py                    | 166 +++++
 104 files changed, 8566 insertions(+), 1371 deletions(-)
```

전체 diff: AUTO_STATE.patch (`git apply AUTO_STATE.patch` on patch_base)

추적되지 않는 파일은 비밀 값이 있을 수 있어 이름만 적습니다:

```
core/education/outlook.py
quantgen_desktop/market_hub.py
tests/desktop_indicator_scroll_acceptance.py
tests/desktop_market_hub_acceptance.py
tests/indicator_outlook_acceptance.py
```
