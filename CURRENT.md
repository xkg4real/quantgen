---
status: checkpoint
reason: manual
from: claude
task: claude-resume-20261103
cycle: 2026-11-10
done_ids: ⑬-2/a4-a, ⑬-2/a4-b, ⑬-2/a4-c, ⑬-2/a4-d, ⑬-2/a2, ②-5/NEW-M6-14, ②-5/NEW-M6-15, ②-5/NEW-M6-22, ⑬-2/a4-b/2, ⑬-2/a4-c/2, ⑬-2/a4-d/2, ⑬-2/a4-e, ⑬-2/a3-type, ⑬-2/a3-rail, ⑬-2/a3-controls, ②-5/M4-N4, ②-5/M4-N7, ②-5/M4-N9, ②-5/N-M1-02/a, ②-5/NEW-M6-04, ②-5/NEW-M6-05, ②-5/NEW-M6-12, ②-5/NEW-M6-19, ⑬-2/a1, ⑬-2/a3-layout-reading, ⑫-1/display-owner-decision, ⑬-8/b2/b/2, ⑫-2/b/1, ⑨-3a/codec/1, ⑨-3a/store/1, ⑨-3a/keys/1, ⑨-3a/data-hash/1, ⑨-3a/source-digests/1, ⑬-2/compact-ui, ⑨-3a/series-digest/1, ⑨-3a/series-format/1, ⑨-3a/series-files/1, ⑨-1/2/a, ⑨-3a/fold/1, ⑨-4/2/a, ⑨-1/2/b, ⑨-1/2/c, ⑨-3a/series-files/2, ⑨-3a/fold/2, ⑨-4/2/b, ⑨-1/2/d
next_ids: ⑤-2/b, ⑨-3a/series-files/3, ⑥-1, ⑥-2, ⑦-1, ⑦-2, ⑨-1/2/e, ⑨-4/2/c, ⑨-3a/recorder/1, ⑨-3a, ⑬-2/a3, ⑬-2/k, ⑩-1/b, ⑩-2/b, ⑫-2/b, ⑬-1/c
updated_at: 2026-11-11T07:25:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/provider-parity-tool-20261111
work_commit: ba8b400
uncommitted_changes: no
pr: 102
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-17T17:00:00+09:00
session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
---

# 인수인계: Claude 재개 (2026-11-10) — GPT 반환 확인, PR89 CI 실패 수정부터

## 0. 한 줄 요약

GPT가 2026-11-07 00:45에 `returned`로 돌려준 작업을 Claude가 다시 맡았습니다(2026-11-10 17:09 KST 확인).
- 가장 먼저 할 일: main에 병합된 PR #89(글꼴·UI 압축)의 Runtime CI 실패를 고칩니다. 그 뒤 PR #87 → #88 병합, ⑨-3a/series-files/1 구현 순서입니다.
- 이전 이력(GPT 113KB CURRENT, 2026-11-06·07 주간 인계)은 `handoff` 브랜치의 `archive/`와 `WEEKLY_HANDOFF_2026-11-0{6,7}_*.md`에 있습니다.

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로, 2026-11-10 Claude Code 채팅):**
  > 위 마크다운 파일들과 노션의 1107 날짜로 되어있는 업무 기록들을 참고해서 남은 일들을 실행해주세요. 이때, UI관련해서는 일단 위 task에서의 작업으로만 진행해주시고, 추후 다른 UI/UX 업데이트를 다른 세션에서 결과 보고를 할때 해당 부분 반영해서 진행해주세요
  >
  > /openshell-cli /karpathy-skills /find-skills 등과 같은 스킬들을 적극적으로 활용해주시고, 노션의 "Remaining work", 그리고 노션의 1107 날짜로 되어있는 부분들에 대해서 background task나 명시되어 있는 부분들이 마무리 될 때마다 취소선 그어주세요.
- "위 마크다운 파일들" = `QUANTGEN_UI_HANDOFF_20261107.md`(= handoff 브랜치 `UI_SESSION_CURRENT.md`의 이전 중간기록), `WEEKLY_HANDOFF_2026-11-06_2041_FINAL.md`.
- "UI는 위 task로만" = 2026-11-07 글꼴·밀도 개선(PR #89)의 남은 일만. 다른 UI/UX 변경은 다른 세션 보고가 오면 반영.
- Notion 대상: "REMAINING WORK"(4065c916fe0c80d2af08c0e7f68817fa), "1107 QUANTGEN : 업무 기록 및 남은 일"(40f5c916fe0c80179ed0c75b3292542a). 완료될 때마다 취소선.
- 완료 조건: 아래 6절 각 ID가 PR → CI(Windows 3.11/3.12/3.14·Ubuntu 3.12·구문·Compliance) 성공 → 병합 → LEDGER → Notion 두 페이지 취소선까지 끝나면 그 ID는 끝.

## 2. 근거

| 종류 | 위치 | 쓰는 부분 |
|---|---|---|
| GPT 반환 문서 | `git show origin/handoff:CURRENT.md`(2026-11-07 00:45 returned), `WEEKLY_HANDOFF_2026-11-07_4bf1f03c.md` | PR87/88 상태, series-files 중단 지점 |
| UI 세션 문서 | `git show origin/handoff:UI_SESSION_CURRENT.md` | PR89 병합 `6a09d3f`, Runtime 42245900881 진행 중이었음 |
| Notion | 위 두 페이지 | 남은 일, 취소선 대상 |
| PR89 CI | Runtime 42245900881 | installed 4개 작업 실패(아래 4절) |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안 |
|---|---|---|
| PR89 CI 실패를 가장 먼저 고침 | main의 head 시험이 실패 상태라, PR87/88에 main을 합치면 같은 실패를 물려받음 | PR87/88 먼저: CI가 같은 이유로 빨갛게 됨 |
| 같은 task 이름(`claude-resume-20261103`)을 이어 씀, cycle만 2026-11-10 | GPT가 같은 task로 돌려줬고 소유자 작업 순서가 이어짐 | 새 task 이름: 원장·이력 추적이 끊김 |
| `⑬-2/compact-ui`를 2026-11-07 글꼴·밀도 개선의 원장 ID로 씀 | PR89에는 원장 행이 없음. CI가 초록이 된 뒤에 기록 | — |

## 4. 진행 상황 (이번에 확인한 것)

- [x] `--show`: status returned, from gpt, work_commit `e7ed793`(= PR88 head), next_ids 확인.
- [x] 원장 128행, 마지막 `⑨-3a/source-digests/1`(PR86, `cd4019c`). main 기록에 PR75~86 병합과 PR89 병합 `6a09d3f`, `9d1eacd`가 있음.
- [x] PR87(`ea90521`, series-digest), PR88(`e7ed793`, series-format): 열림, `mergeable_state: dirty`(main이 움직여 충돌). GPT 보고는 두 head 모두 CI 성공.
- [x] **PR89 Runtime 42245900881 = 실패.** installed (ubuntu 3.12, windows 3.11/3.12/3.14) 4개 모두 `tests.desktop_a3_layout_acceptance` 의 `test_mc_larger_combo_fonts_reflow_and_keep_field_order_and_evidence` 1건 실패: `AssertionError: 2 != 3` (window 1360, en, form_width 696, Ubuntu control min 236, Windows 308). 나머지 19개 OK. 구문·Compliance는 성공. PR89는 이 결과가 나오기 전에 병합됨.
- [x] Notion 1107 페이지 읽음.
- [x] ⑬-2/compact-ui 원인: PR89가 모든 compact 입력폼을 고정 696px(3×224+간격)로 제한. 18px 콤보에서 열 최소폭 236(Linux)/308(Windows) → 3열 불가 → 넓은 창에서도 2열. 수정: `form_layout.py`에서 224px를 상한이 아니라 기준으로(실제 최소폭이 요구하는 폭까지만 넓힘). A3 시험 그대로, 새 회귀 시험 추가. 로컬 CI 동등 데스크톱 9개 명령 647개 통과(Linux), 독립 검토 2명 승인, 컴플라이언스 PASS. 커밋 `05db49f`, 웹 기록 `30bca10`.
- [x] ⑬-2/compact-ui PR #90 병합 `19a7375`(트리 = head `30bca10`). Runtime 42790177998 6/6(Windows 3.12는 첫 시도에서 15단계 KIS·관심종목 시험이 30분 제한에 걸려 취소, 재실행 1회 통과; 직전 head `05db49f`의 Runtime 42790128647 6/6), Compliance 42790178270 성공.
- [x] ⑨-3a/series-digest/1 PR #87 병합 `9042f3e`(트리 = head `2f231cb`), Runtime 42799417249 6/6·Compliance 42799417582 성공.
- [x] ⑨-3a/series-format/1 PR #88 병합 `d1346ff`(트리 = head `f3f56c3`), Runtime 42799673404 6/6·Compliance 성공.
- [x] ⑨-3a/series-files/1 PR #91 병합 `ed8df4a`(트리 = head `93408c3`), Runtime 42799788975 6/6(Windows 3.11/3.12/3.14 포함)·Compliance 성공.
- [x] 범위 조사(읽기 전용 워크플로, 3개 + 비판): 소유자 확인 없이 시작 가능한 단위는 ⑨-1/2/a(LA-01, 가치 최고), ⑨-3a/fold/1, ⑨-1/2/b(LA-02 1부, 재범위), ⑨-4/2/a(채택 모듈, 잠정). 결과: 스크래치 `scope_results.json`.
- [x] ⑨-1/2/a LA-01 PR #94 병합 `be26c24`. Compliance 성공, 캐시 없는 사본 전체 실행 747/873(main 기준 746/872 + 새 시험 1, 다른 행 변화 없음, FAIL 2는 기존 환경 탓, acceptance_results md5 불변).
- [x] PR #94 병합 뒤 #93·#95·#96이 main과 FACTS.md·source-review.json에서 충돌. 순서대로 이어 병합했습니다(main → fold → adoption → LA-02, 뒤 브랜치가 앞 브랜치를 모두 포함하므로 차례로 병합하면 새 충돌 없음).
  - fold `claude/run-registry-fold-20261110` = `239123a`(main `be26c24` 포함).
  - adoption `claude/adoption-strategy-checks-20261110` = `f92a35b`(fold 포함). runtime-smoke.yml 충돌은 두 쪽의 새 시험 모듈(run_registry_fold_acceptance, adoption_strategy_rules_acceptance)을 R3 unittest 단계와 paths 필터에 모두 남겨 해결. 기준선 재생성, consistency PASS. fold·adoption·series-files 시험 124개 통과.
  - LA-02 `claude/lookahead-la02-part1-20261110` = `8e88814`(adoption 포함). 그 전 병합 `f43ce06`은 adoption의 옛 head `7282c73`을 가져와 main·fold가 빠져 있었음. 기준선 재생성, consistency PASS.
- [x] LA-02 1부 단독 전체 실행(`2d87256`, 캐시 없는 사본): 753/879, main `ed8df4a` 기준 746/872 대비 새 시험 7개 PASS만 추가, 바뀐 행 0, FAIL 2는 기존 환경 탓(macro_m8 dry_run 로컬 캐시, papers 프로세스 트리), acceptance_results md5 불변.
- [x] 세 PR을 합친 `8e88814`의 캐시 없는 전체 실행: 754/880, main `ed8df4a` 기준 746/872 대비 새 시험 8개(LA-02 7, LA-01 1) PASS만 추가, 바뀐 행 0, FAIL 2는 기존 환경 탓, acceptance_results md5 불변.
- [x] ⑨-3a/fold/1 PR #93 병합 `2d6b796`(트리 = head `239123a`). Runtime 42823727729 6/6(Windows 3.12 첫 시도는 17단계 시작 40초 뒤 30분 제한으로 취소, 1~16단계 통과; 재실행 1회 통과), Compliance 42823727852 성공.
- [x] ⑨-4/2/a PR #95 병합 `d97fdff`(트리 = head `f92a35b`). Runtime 42824126370 6/6, Compliance 42824126418 성공.
- [x] ⑨-1/2/b PR #96 병합 `b0d2862`(트리 = head `8e88814`). Runtime 42824252097 6/6, Compliance 42824252061 성공.
- [ ] ⑨-1/2/c LA-02 2부 워크플로 실행 중(워크트리 `la02c`, 브랜치 `claude/lookahead-la02-part2-20261110`, `8e88814`에서). 4그룹: m1_pit(G-POST-01·T-PRINT-01 F13·G-STALE-01·T-MISS-01), m1_fixtures G-POST + m1_calendars T-CLOSE-02, m2_risk(T-VT-01·T-LABEL-01), m3 T-B5-01 + m8_forward G-REF-01. 제외: T-FIX-01(저장소 밖 자료), T-REGIME-01(ACQUISITION 행 없음), I-05(LA-30 자료). PR은 #96 병합 뒤 main 기준으로 엽니다.
- [x] 소유자 승인 2026-11-10 ("전부 승인합니노.") 원문 기록 + 누출 감사 보고서(L-1)·채택 기준 문서(초안 표시 해제)를 main에 반영: PR #92 병합 `f4e034d`(트리 = head `85fad1b`, Compliance 성공). 승인 범위: I-05용 LA-07 하네스 변경, 채택 기준 main 반영, R3 실험실 UI(네이티브 Qt 포함), 696ee3c 사후 승인. 미결: 'ledger N_raw' 뜻(두 해석 중 미선택), 설계 0b(P-01)·Q12 파일 목록.
- (이전) 소유자 질문 대기(작업은 막지 않음): I-05/LA-07 동결 하네스 변경 여부, 새 시험 test_ids(macro_registry.csv) 허용 여부, ⑨-4 Q1~Q7(특히 채택 기준 문서 main 반영 Q6, ledger N_raw 의미), R3 Lab UI 작업 허용(소유자가 UI 범위를 PR89로 제한), 설계 0b(P-01), Q12 파일 목록, ⑨-3c 동결 지시, series-files no-clobber 질문.
- 참고(소유자 보고 필요): 커밋 696ee3c(10-30, GPT)가 동결 하네스 core/quant/strategies.py를 수정했는데 결정 기록에 해당 항목이 없음. 이번 작업은 막지 않음.

## 5. 중단 지점

소유자가 2026-11-11 02:4x KST에 결정 14건에 답했습니다(원문):

> 1-승인, 2-승인, 3-승인, 4-승인, 5-승인, 6-승인, 7-권장대로 요청, 8-승인, 9-현행유지, 10-승인, 11-정리보고요청, 12-함께, 13-수치제시, 14-보류
>
> 그리고 Remaining Work에서 6. 실제파일럿 이랑 7. 마감/병합 부분은 도대체 언제 완료될까요? 얘네만 지금 한번도 손에 못댄 채 있는데, 빨리빨리 얘네도 처리해야합니다.

결정표 전문과 각 답을 어떻게 받았는지는 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` 마지막 절(브랜치 `claude/owner-rulings-20261111`, 커밋 `275ec93`, push됨)에 있습니다. 6·7번이 멈춘 원인: 선행 단계 ⑤-2 공급사 대조 도구가 `777fc5b`(11-05 미완성본, `origin/claude/provider-parity-5-2`)에서 멈춰 있었고 연구 브랜치는 `8a8c247` 이후 변화가 없습니다. Step 7A 세션(session_016uB1jgeiPdP8gPkAez3Wrx)은 11-05 이후 쉬는 상태입니다. 도구는 `tools/provider_parity/`(main 계열)라 연구 브랜치를 건드리지 않고 이 세션에서 완성합니다.

진행 (2026-11-11 04:55 KST):

- [x] 결정 7·8·9·10: [PR #100](https://github.com/xkg4real/quantgen/pull/100) 병합 `1a8b29f`(트리 = head `e4b0772`). Runtime 42883511339 6/6·Compliance 42883511196 성공. 캐시 없는 전체 실행: main `7ddb568` 763/889, `e4b0772` 763/889, 바뀐 행 0(FAIL 2 기존 환경). 결정 기록 원문도 이 PR로 main에 들어감.
- [ ] PR #100 `/code-review high` 9건 → 수정 워크플로 ws08qnsb0(워크트리 `rul`, 로컬 커밋, push 전): F1 임시 파일을 결과 확정까지 유지, F4 기존 대상 fsync, F7 공식 기준 단일 출처, F8 REPLACE_ 이름 변경, F9 재시도 Windows 한정, F3·F5 문서. 미수용 2건: fold flag(결정 9), "owner ruling 7" 문구. 끝나면 main에서 새 브랜치로 옮겨 후속 PR(⑨-3a/series-files/3).
- [ ] ⑤-2/b: 워크플로 wpjte04dg 완료 → [PR #102](https://github.com/xkg4real/quantgen/pull/102), head `ba8b400`(도구 완성 `49a3a67` + P1 고정 기록). 시험 110개, 한국어 실행 안내서 `docs/product/PROVIDER_PARITY_OWNER_RUN_2026-11-11.md`(PowerShell 34단계). 시험이 임시 폴더를 남기던 문제 수정(159개 → 0개). CI와 `49a3a67`의 캐시 없는 전체 실행(scratchpad `parity`, `m1_compare.py <S> prep parity`) 대기.
  - **소유자 결정 P1 (2026-11-11 06:3x KST, 원문):** "1번으로 승인하겠노" = 도구 버전을 main 쪽에 고정. 도구 커밋 `49a3a67b246d020381b27067103d1a7ba4795f9e`, 도구 파일 sha256 `d651795e4b4776d096601a43989c7f45c375ae120b75a64179432f469d2daca1`. 기록: `OWNER_RULINGS_LOG.md` 마지막 절, `results/RULINGS.md`, 도구 README, 한국어 안내서.
  - **병합 직후 할 일:** main에서 실행 브랜치 `claude/provider-parity-runs-20261111`을 만들어 push(`git push origin origin/main:refs/heads/claude/provider-parity-runs-20261111`), `git branch -r --contains 49a3a67`로 확인 → 소유자에게 안내서와 "시작해도 됩니다" 전달 → 원장 `--done "⑤-2/b | ..."` → Notion.
  - 소유자 PC 실행 뒤: 마지막 두 줄씩 18줄 + PARITY 3줄을 받아 판독. PASS가 아니면 선택지 정리 → 판정을 `results/RULINGS.md`에 원문 기록.
- [x] ⑨-1/2/d 결정 1~6: [PR #101](https://github.com/xkg4real/quantgen/pull/101) 병합 `96cca1f`(트리 = head `30f009d`). Compliance 42899220664 성공(Runtime 경로 필터 밖), 캐시 없는 전체 실행 769/895 = main 763/889 + 새 시험 6개 PASS, 바뀐 행 0. 미완: KRWX(F16)는 FX 시계가 없어 생성기가 거부(소유자 질문 A-1), G-REF-01 기록 파일 위치·형식(A-2), 1995-04 이전 가격제한폭 빈 값(A-3). `MANIFEST.csv`의 ACQUISITION md5 한 칸을 총괄 세션이 갱신(README 규칙). 달력 서명 요청 목록: `docs/product/CALENDAR_SIGNING_REQUEST_2026-11-11.md`. `/code-review`는 병합 뒤 실행해 후속 PR에 묶음.
- [x] 소유자 보고(03:5x KST): 파일럿·마감 경로와 일정 추정(도구 병합 뒤 4~6일, 현실적으로 1~2주), 결정 요청 P1~P4(도구 고정 위치, 연구 브랜치 담당, 병합 충돌 처리, 병합 전 main 보류 항목), B-Q1~Q5·Q7(채택 기준), C(0b, Q12, Qt, Q22, 확인용 6건), D-1~14(M-12 수치안). 상세본 `scratchpad/OWNER_REPORT_2026-11-11.md`(소유자에게 파일 전달). 원자료: `scratchpad/pilot_path_1111.json`, `scratchpad/reports_1111.json`. 답 대기 중이나 작업은 계속.
- 참고: Windows CI 작업이 30분 제한에 근접(PR #100에서 3.11 30:00, 3.12 30:19). 제한 상향(30→45분)을 다음 PR에서 제안.
- 규칙 위반 보고(소유자에게 알림): 하위 작업자가 보호 캐시 폴더를 이름으로 두 번 훑음(git 색인 조회, find). 파일을 열지는 않음. 이후 지시문에 제외 방법을 명시.

### 소유자 결정 "전부승인" (2026-11-11 07:1x KST, 원문 그대로)

> 전부승인

바로 앞 Claude 안내는 승인 대기 묶음을 P2·P3·P4, A-1~3, B·C·D로 나열하고 "한 묶음을 전부 권장대로 하시려면 `P 전부 승인`처럼 답하시면 됩니다"였습니다. Claude는 이 답을 **다섯 묶음 모두 권장대로 승인**으로 받았고 소유자에게 그렇게 알렸습니다. 권장 문구 전체와 반영 내용은 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`의 마지막 절(브랜치 `claude/series-files-followup-20261111`, 로컬 커밋, PR #102 병합 뒤 push)에 있고, 초안 사본은 `scratchpad/rulings_1111_all.md`입니다.

- **P2:** 이 세션이 연구 브랜치에 커밋 가능. 범위는 Step 10 마감 기록·스펙·README·`docs/nautilus_bridge/runs/`로 한정. `tools/nautilus/**`, `tests/nautilus_*.py`, 러너, 표, `owner_confirmed`, `host_fingerprint`는 계속 금지.
- **P3:** Step 10 확인 뒤 Claude가 main을 연구 브랜치에 합쳐 충돌 해결 + 캐시 없는 전체 테스트. 그 전에는 합치지 않음(H-D5). main 병합 커밋은 소유자.
- **P4:** 주문 모듈, R3 실험실 화면 연결, LA-07 하네스 변경은 ⑦-2 병합 뒤. R3 기록기 본체는 진행.
- **A-1:** 생성기가 KRW=X(F16)를 뉴욕 17:00 외환 마감 기준으로 스탬프(⑨-1/2/e). **A-2는 미정**(파일 이름을 여쭌 질문). **A-3:** 현행.
- **B:** Q1 REJECT(잠정 표시), Q2 게이트와 같은 분산 값으로 판정·SE_null은 참고 줄, Q3 검정력 부족이면 이겨도 자료 부족, Q4 DM으로 판정·Clark–West 참고 줄, Q5 12항목 필수·Claude 초안·소유자 커밋·R-FAM/L-FAM 병기, Q7 60/40은 21거래일 리밸런싱·실제 거래분 비용. 다음 단위 ⑨-4/2/c(결과 조립).
- **C:** 0b 채택 방침만 기록. Q12 = 7개 파일(`core/quant/strategies.py`, `validate.py`, `history.py`, `gate_ledger.py`, `core/research/strategy_workflow.py`, `core/quant/optimize.py`, `core/quant/risk.py`). Q13·Q14·Q16·Q17·Q18 기본값. 화면은 네이티브만(UI-D1), Flet 작업(Q19 포함) 안 함, PC 화면은 시안 먼저 + UI 세션 이식과 ⑦-2 병합 뒤. Q22의 잘라내기 여부는 2026-12 말 전에 따로 질문. 다음 단위 ⑨-3a/recorder/1(화면 없음, 결정 9 조건: run_family 안에서 PNL_COMPUTED보다 낮은 PROGRESS를 쓰지 않음).
- **D:** 주문 한도 수치(1회 100만 원/5%, 하루 10건·300만 원/15%, 손실 중지 40만 원/2%, 종목 비중 20%/400만 원, 가격 이탈 3%·시세 15초·지정가만, 09:00~15:20, 모의 20거래일·30건 등)를 기본값으로 승인. **실거래는 켜지지 않음.** 순서: 안전 설계 문서 보고 → ⑦-2 병합 뒤 구현 → 모의투자 → 결과 보고 → 소유자의 실거래 전환 승인. D-14 법률 자문은 소유자가 의뢰.

## 6. 다음 할 일 (순서대로)

1. 각 워크플로 결과를 검토(`git log origin/main..HEAD`, 검토 지적과 수정 대조) → push → PR → `/code-review` → CI + 캐시 없는 전체 실행(`scratchpad/full_commit313.sh <name> <commit>`, `m1_compare.py`로 `la02d` 대비; 끝나면 `full_<name>` 삭제) → 병합(expectedHeadSha, 트리 확인) → 원장 `--done` → Notion 두 페이지 취소선. FACTS.md·source-review.json이 서로 겹치므로 rulings → prep → parity 순으로 이어 병합(`scratchpad/merge_chain.py`). 다른 세션의 UI PR #98도 같은 파일을 고칩니다.
2. 소유자에게 보고: (가) ⑤-2 PC 실행 안내서와 파일럿·마감 일정, (나) ⑨-4 Q표, (다) 설계 0b·Q12, (라) M-12 수치안(확인 전 주문 기능 시작 금지), (마) 달력 서명 요청 목록.
3. 소유자 PC 실행 결과가 오면: ⑤-2 대조 판정 → ⑥-1 Pilot 1(SPY) → ⑥-2 Pilot 2(BTC) → ⑦-1 Step 10 → ⑦-2 main 병합(소유자 --no-ff). 파일럿과 Step 10은 연구 브랜치·소유자 PC 작업입니다.
4. 결정 9(현행 유지)의 조건: 기록기 단위는 `run_family` 안에서 PNL_COMPUTED보다 낮은 PROGRESS를 쓰지 않습니다. 결정 14: N-M1-02/b 보류 유지.

## 7. 주의사항

- **화면(UI) 작업 기준 (소유자 결정 UI-D1~D4, 2026-11-11):** UI 기준 앱은 네이티브 PyQt(`quantgen_desktop/`) 하나입니다. 화면을 건드리기 전에 handoff 브랜치의 `AGENTS.md` 6절과 `UI_SESSION_CURRENT.md` 맨 위(소유자 원문, 금지 사항)를 반드시 읽으십시오. next_ids의 ⑬-2/a3·⑬-2/k와 R3 실험실 화면 연결(C 묶음)은 화면 작업이므로 이 기준을 따릅니다. 지금 UI 세션(session_016uB1jf8m3p5GW1qzQVJe7k, 브랜치 `claude/friendly-bardeen-r6xe8f`, LEDGER ⑬-2/owner-14-native 진행 중)이 `quantgen_desktop/`의 Strategy Lab·도구 화면·글꼴을 고치고 있으니, 그 파일들은 `UI_SESSION_CURRENT.md`의 진행 항목을 확인하기 전에는 시작하지 않습니다.
- UI 세션의 다음 compliance 갱신은 `docs/compliance/FACTS.md`, 08/13/14/19, `source-review.json`, `.github/workflows/runtime-smoke.yml`을 고칩니다. PR #102와 겹치므로 나중에 병합하는 쪽이 main을 합치고 기준선을 다시 만듭니다.
- `.env`, `docs/asset_expansion/cache/`(열기·검색·해시 금지), `~/.nextgen` 원장, 동결 하네스, 연구 브랜치·`tools/nautilus/**` 는 건드리지 않습니다. `tests/run_all.py`는 캐시 없는 사본에서만.
- 실제 Anthropic API 호출 없음. Vercel 상태 무시·댓글 없음. 웹사이트 HTML 수정·업로드 없음.
- TRADEGEN(별도 저장소)의 1107 페이지는 이 세션 범위 밖입니다(소유자 확인 필요).

## 9. 이어받는 에이전트에게

`status: checkpoint`인 동안 이어받지 않습니다.

## 10. 확인

```
python3 tools/handoff/push_handoff.py --show   # 기대: checkpoint, from claude, cycle 2026-11-10
```
