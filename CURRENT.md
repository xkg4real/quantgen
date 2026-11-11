---
status: checkpoint
reason: manual
from: claude
task: claude-resume-20261103
cycle: 2026-11-10
done_ids: ⑬-2/a4-a, ⑬-2/a4-b, ⑬-2/a4-c, ⑬-2/a4-d, ⑬-2/a2, ②-5/NEW-M6-14, ②-5/NEW-M6-15, ②-5/NEW-M6-22, ⑬-2/a4-b/2, ⑬-2/a4-c/2, ⑬-2/a4-d/2, ⑬-2/a4-e, ⑬-2/a3-type, ⑬-2/a3-rail, ⑬-2/a3-controls, ②-5/M4-N4, ②-5/M4-N7, ②-5/M4-N9, ②-5/N-M1-02/a, ②-5/NEW-M6-04, ②-5/NEW-M6-05, ②-5/NEW-M6-12, ②-5/NEW-M6-19, ⑬-2/a1, ⑬-2/a3-layout-reading, ⑫-1/display-owner-decision, ⑬-8/b2/b/2, ⑫-2/b/1, ⑨-3a/codec/1, ⑨-3a/store/1, ⑨-3a/keys/1, ⑨-3a/data-hash/1, ⑨-3a/source-digests/1, ⑬-2/compact-ui, ⑨-3a/series-digest/1, ⑨-3a/series-format/1, ⑨-3a/series-files/1, ⑨-1/2/a, ⑨-3a/fold/1, ⑨-4/2/a, ⑨-1/2/b, ⑨-1/2/c, ⑨-3a/series-files/2, ⑨-3a/fold/2, ⑨-4/2/b, ⑨-1/2/d, ⑤-2/b, ⑨-3a/series-files/3, ⑤-2/b/2, ⑥-1/prep, ⑤-2/d
next_ids: ⑤-2/e, ⑤-2/f, ⑨-1/2/d/2, ⑥-1, ⑥-2, ⑦-1, ⑦-2, ⑨-1/2/e, ⑨-4/2/c, ⑨-3a/recorder/1, ⑨-3a, ⑬-2/a3, ⑬-2/k, ⑩-1/b, ⑩-2/b, ⑫-2/b, ⑬-1/c
updated_at: 2026-11-11T17:06:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/provider-parity-spy-rerun-20261111
work_commit: fbe493d
uncommitted_changes: no
pr: none
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

바로 앞 Claude 안내는 승인 대기 묶음을 P2·P3·P4, A-1~3, B·C·D로 나열하고 "한 묶음을 전부 권장대로 하시려면 `P 전부 승인`처럼 답하시면 됩니다"였습니다. Claude는 이 답을 **다섯 묶음 모두 권장대로 승인**으로 받았고 소유자에게 그렇게 알렸습니다. 권장 문구 전체와 반영 내용은 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`의 마지막 절(브랜치 `claude/series-files-followup-20261111`, 커밋 `45af437`, push됨. PR은 #102 병합 뒤에 엽니다)에 있고, 초안 사본은 `scratchpad/rulings_1111_all.md`입니다.

- **P2:** 이 세션이 연구 브랜치에 커밋 가능. 범위는 Step 10 마감 기록·스펙·README·`docs/nautilus_bridge/runs/`로 한정. `tools/nautilus/**`, `tests/nautilus_*.py`, 러너, 표, `owner_confirmed`, `host_fingerprint`는 계속 금지.
- **P3:** Step 10 확인 뒤 Claude가 main을 연구 브랜치에 합쳐 충돌 해결 + 캐시 없는 전체 테스트. 그 전에는 합치지 않음(H-D5). main 병합 커밋은 소유자.
- **P4:** 주문 모듈, R3 실험실 화면 연결, LA-07 하네스 변경은 ⑦-2 병합 뒤. R3 기록기 본체는 진행.
- **A-1:** 생성기가 KRW=X(F16)를 뉴욕 17:00 외환 마감 기준으로 스탬프(⑨-1/2/e). **A-2는 미정**(파일 이름을 여쭌 질문). **A-3:** 현행.
- **B:** Q1 REJECT(잠정 표시), Q2 게이트와 같은 분산 값으로 판정·SE_null은 참고 줄, Q3 검정력 부족이면 이겨도 자료 부족, Q4 DM으로 판정·Clark–West 참고 줄, Q5 12항목 필수·Claude 초안·소유자 커밋·R-FAM/L-FAM 병기, Q7 60/40은 21거래일 리밸런싱·실제 거래분 비용. 다음 단위 ⑨-4/2/c(결과 조립).
- **C:** 0b 채택 방침만 기록. Q12 = 7개 파일(`core/quant/strategies.py`, `validate.py`, `history.py`, `gate_ledger.py`, `core/research/strategy_workflow.py`, `core/quant/optimize.py`, `core/quant/risk.py`). Q13·Q14·Q16·Q17·Q18 기본값. 화면은 네이티브만(UI-D1), Flet 작업(Q19 포함) 안 함, PC 화면은 시안 먼저 + UI 세션 이식과 ⑦-2 병합 뒤. Q22의 잘라내기 여부는 2026-12 말 전에 따로 질문. 다음 단위 ⑨-3a/recorder/1(화면 없음, 결정 9 조건: run_family 안에서 PNL_COMPUTED보다 낮은 PROGRESS를 쓰지 않음).
- **D:** 주문 한도 수치(1회 100만 원/5%, 하루 10건·300만 원/15%, 손실 중지 40만 원/2%, 종목 비중 20%/400만 원, 가격 이탈 3%·시세 15초·지정가만, 09:00~15:20, 모의 20거래일·30건 등)를 기본값으로 승인. **실거래는 켜지지 않음.** 순서: 안전 설계 문서 보고 → ⑦-2 병합 뒤 구현 → 모의투자 → 결과 보고 → 소유자의 실거래 전환 승인. D-14 법률 자문은 소유자가 의뢰.

### 소유자 판정: SPY-가, BTC-나 (2026-11-11 17:06 KST) — 가장 최신

소유자 답(2026-11-11 17:1x KST, 원문 두 줄):

> SPY-가-승인, BTC-나-승인
> 그리고 BTC-나 에 따라 문제의 원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요

Claude가 받은 뜻(소유자에게 그대로 알림):
- **SPY-가:** 도구의 fmp 수신을 여러 번 요청해 이어 받도록 고침(kis처럼 뒤로 넘기며 받기) → 새 고정 커밋·sha256(둘째 버전, 첫 버전 `5202482`·`f2fe72cd…0184`는 11-11 기록 실행 3건의 버전으로 남김) → 소유자가 fmp만 새 폴더에 다시 받고 SPY 대조를 한 번 더 → 이 판정이 스펙 10.5가 요구하는 "나중 실행 인정" 판정. 첫 실행(WITHHELD)과 요약은 그대로 둠.
- **BTC-나:** Pilot 2 전에 원인 확인. 가격이 아닌 통계(연도별 불일치 일수, 수준 차이의 99번째 백분위·최댓값)만 PC 밖으로 나가는 것을 허용. Claude가 소유자 PC용 읽기 전용 진단 스크립트 `tools/provider_parity/btc_diagnose.py`를 만듦(고정된 도구의 판독 함수만 사용, 연도보다 자세한 날짜·가격·일별 차이는 출력하지 않음).
- **둘째 줄("자동으로 해결 및 pilot 2 진행"):** 원인이 고정 파일·등록 표·코드 지문 아래 코드를 바꾸지 않고 설명되면, 불일치와 원인을 기록하고 BTC 관문을 이 판정으로 통과한 것으로 봄(다시 묻지 않음). 고정 파일·표·코드를 바꿔야 하는 원인이면 자동으로 하지 않고 보고 후 판정을 받음(`owner_confirmed`가 무효가 되므로). Pilot 2는 소유자 PC에서 소유자가 실행하며 Pilot 1의 hard 패리티 통과가 조건(러너 R-11).

진행(⑤-2/f): 워크플로가 도는 중. 워크트리 `scratchpad/pp2`, 브랜치 `claude/provider-parity-spy-rerun-20261111`(main `fbe493d`에서, push 전). 판정 원문과 선택지 표 원문은 `scratchpad/rulings_1111_spy_btc.md`에 모아 두었고 워크플로가 `OWNER_RULINGS_LOG.md` 새 절과 `results/RULINGS.md`에 옮깁니다. 산출물: (1) `fetch_fmp` 수정과 시험, (2) `btc_diagnose.py`와 시험 모듈 `tests/provider_parity_btc_diagnose_acceptance.py`, (3) 결정 기록·README·FACTS·새 안내서 `docs/product/PROVIDER_PARITY_RERUN_2026-11-11.md`(A: SPY 재수신·재대조, B: BTC 진단 실행), (4) 새 고정값 기록과 기준선. 그 뒤 독립 검증 3관점 → 수정.

워크플로가 끝난 뒤 순서: 결과 검토 → push → PR → CI(Runtime 약 30분) + 캐시 없는 전체 실행 → 병합 → **main을 실행 브랜치에 병합**(실행 브랜치 `claude/provider-parity-runs-20261111`은 소유자 커밋 `0b397f7`이 위에 있으므로 병합 커밋으로 올림, 소유자는 `pp_clone`에서 `git pull --ff-only`) → 소유자에게 새 안내서와 새 고정값 전달 → 소유자: SPY 재수신·재대조·push, BTC 진단 출력 붙여넣기 → Claude: SPY 둘째 요약 판독(PASS면 Pilot 1 관문 통과), BTC 진단 판독과 원인 기록 → 관문 판정을 `results/RULINGS.md`에 기록 → Pilot 1 안내(`docs/product/PILOT_OWNER_RUN_2026-11-11.md`). Pilot 1 전에 연구 클론의 추적되지 않는 폴더 `.agents/`·`quantgen/` 처리도 필요(소유자에게 폴더 안 이름 목록을 요청함).

### ⑤-2/d 완료: 소유자 PC 대조 결과와 판독 (2026-11-11 17:00 KST) — 가장 최신

소유자가 16:5x KST에 요약 3개를 실행 브랜치에 올렸습니다(`claude/provider-parity-runs-20261111` `0b397f7`, 9fc3817 위에 `results/PP-*/summary.json` 3개만 추가, 523줄). 세 요약 모두 도구 sha256 `f2fe72cd…0184`, 고정 파일 md5 일치. Claude는 `git show`로 summary.json만 읽었습니다.

| 시계열 | run_id | 기록 실행 | 읽은 내용 |
|---|---|---|---|
| DGS3MO(rf) | PP-20261111T075307Z-rf | **PASS** | treasury(독립): 공통 값 5,475개 중 허용치 초과 0, 최대 차이 1e-08 이하. 경고 1건: FRED에는 값이 있고 재무부에는 행이 없는 날 3일(2008-12-10, 12-18, 12-24). fred_now(같은 출처 재수신) 5,478개 초과 0. h15는 `not compared: fetch_failed` |
| SPY | PP-20261111T051909Z-spy | **WITHHELD** | 고정 파일 자체 검사 PASS(5,489행). fmp: 첫 날짜 2006-11-15, 기간 밖 494거래일(허용 5) → coverage WITHHELD. kis: 첫 날짜 2007-08-21, 기간 밖 684거래일 → WITHHELD. 두 짝 모두 수익률 비교 미실행. yahoo_now(같은 출처): 5,489일 공통, 허용치 초과 0일. 사유 `no independent or cross pair was evaluated in full` |
| BTC-USD | PP-20261111T075328Z-btc | **FAIL** | 고정 파일 자체 검사 PASS(4,392행, 빠진 날 0). coinbase(독립): coverage·calendar·day_boundary(lag 0) PASS, levels_and_returns FAIL: 2017년 이후 3,555일에서 수준 차이 중앙값 0.1% 이하지만 띠 밖(99번째 백분위 > 1.5% 또는 최댓값 > 5%, 요약은 구간만 적어 어느 쪽인지 모름), 일간 로그수익률 차이 2% 초과 43일(허용 20). bitstamp(독립): 같은 모양, 47일(허용 21). 2017년 전 구간은 띠 안. binance(진단)는 2017-08-17 시작이라 WITHHELD(판정에 영향 없음) |

**관문(스펙 10.5):** Pilot 1은 SPY·DGS3MO → DGS3MO는 통과, SPY는 소유자 판정 필요. Pilot 2는 BTC-USD → 소유자 판정 필요. 판정 문장은 원문 그대로 `results/RULINGS.md`(main과 실행 브랜치)와 `OWNER_RULINGS_LOG.md`에 적습니다. 판정 전에는 어느 파일럿도 시작하지 않습니다.

**소유자에게 물은 것(답 대기, `waiting_on: owner`):**
- SPY: 가(권장: fmp 수신을 기간을 나눠 받도록 도구 수정 → 새 고정값 → fmp만 재수신 → SPY 대조 한 번 더, 첫 실행은 기록 유지) / 나(증거 없이 진행) / 다(보류).
- BTC: 가(불일치를 기록하고 Pilot 2 진행) / 나(권장: Pilot 2 전에 원인 확인. 소유자 PC의 `detail.json`에서 가격이 아닌 통계, 곧 연도별 불일치 일수와 수준 차이의 99번째 백분위·최댓값만 읽어 채팅으로 보내는 것을 허용하는 판정이 함께 필요. Pilot 1에는 영향 없음) / 다(자료 교체, 비권장: 고정값·표·owner_confirmed가 무효가 되고 저장된 카드와 비교가 끊김).
- 읽은 뜻(미검증 추론): 두 거래소가 거의 같은 건수로 어긋나므로 고정 파일(Yahoo 집계가) 쪽이 거래소 종가와 약 1%의 날에 다르다는 쪽을 가리킵니다. 허용치(10.5.1)는 실제 자료로 맞춘 적이 없어 거짓 FAIL 비율은 모릅니다. 허용치를 결과를 본 뒤에 바꾸는 것은 권하지 않습니다.

### ⑥-1/prep 완료 (2026-11-11 15:12 KST) — 가장 최신

- [PR #104](https://github.com/xkg4real/quantgen/pull/104) 병합, main `fbe493d`(트리 = head `8023833`). Compliance 42970696999 성공(문서만이라 Runtime은 경로 필터 밖). 문서 3개가 main의 `docs/product/`에 있습니다: `PILOT_OWNER_RUN_2026-11-11.md`(소유자 실행표), `PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md`(판독 점검표·Step 10 마감 기록 틀·병합 뒤 정리), `STEP10_MERGE_REHEARSAL_2026-11-11.md`(리허설 기록과 충돌 풀이 방법, 부록에 수정 S1~S3 패치).
- 리허설 커밋의 캐시 없는 전체 실행(`a5f904a`): 987행 = 843 PASS, 137 NOT_RUN, 7 FAIL. main 트리 대비 92행 추가(nautilus 57 = 44 PASS + 13 NOT_RUN, bonds 33 = 28 PASS + 5 FAIL, macro 2 PASS), 제거 0, 변경 0. bonds 5 FAIL은 기록이 예고한 것(S1을 넣으면 통과, 모듈 단위로만 확인). 리허설 브랜치 `scratch/step10-rehearsal`은 로컬에만 있고 **push 금지**. Step 10 때 그날의 main과 연구 head로 다시 해야 합니다.
- **소유자에게 보고할 질문 26건**(문서 K절과 리허설 기록 5절, 아직 보고 안 함): 대조 실행이 정리되면 표로 묶어 보고합니다. 급한 것은 파일럿 1 전에 필요한 것(추적되지 않는 폴더 `.agents/`·`quantgen/` 처리)과 Step 10 병합 전에 필요한 것(합친 뒤 Windows 전체 검사 재실행 여부, 서명 문장 적용 한 줄, P3 병합에 S1~S3·기준선을 넣어도 되는지, Bonds 화면 선택 7건, 연구 브랜치 push 승인 방식)입니다.
- 열려 있는 PR 없음. 소유자 PC 대조 실행은 위 "소유자 PC 대조 실행 중간 결과" 절 그대로이고 답을 기다립니다(실행 브랜치는 아직 `9fc3817`, 요약 push 전).

### 소유자 PC 대조 실행 중간 결과 (2026-11-11 15:01 KST) — 가장 최신

소유자가 14:1x KST에 안내서 1~26단계의 화면을 채팅에 붙였습니다(요약 파일은 아직 push 전). 화면 줄에서 읽은 것:

- **수신 9번:** fmp OK(5,000행, 첫 날짜 2006-11-15), kis OK(4,810행, 첫 날짜 2007-08-21, `kis paging stopped at 2007-08-21 ... a page brought no new date`), yahoo_now OK(2004-11-01부터), treasury OK(2004-11-01부터), **h15 UNAVAILABLE fetch_failed**(`the response does not name the 3-month series`), fred_now OK, coinbase OK(2015-07-20부터), bitstamp OK(2014-08-17부터), binance OK(2017-08-17부터). 모두 마지막 날짜 2026-10-02, 주말 날짜 0.
- **SPY 기록 실행 = WITHHELD** (`PARITY spy WITHHELD exit=3`, run_id `PP-20261111T051909Z-spy`, 요약은 도구 클론의 `results/PP-20261111T051909Z-spy/summary.json`에 복사됨). 원인(도구 규칙으로 읽음, 요약으로 확인 전): SPY의 `edge_uncovered_max`는 5인데 fmp와 kis가 표 시작일 2004-12-01보다 2년 이상 늦게 시작 → 두 짝 모두 coverage WITHHELD, 수익률 비교 미실행 → 독립·교차 증거 0. yahoo_now는 vintage라 증거로 세지 않음. fmp는 한 요청이 5,000행에서 끊긴 것으로 보임(도구가 요청을 나누지 않음, FMP 문서로는 미확인). 안내서의 멈춤 지점 조건(첫 날짜, kis 문구)에 걸렸지만 소유자가 계속 진행했습니다.
- **rf:** 첫 대조는 h15 파일이 없어 `REFUSED`(실행 아님). 소유자에게 준 다시 실행 줄: 26단계에서 `--pair h15 ...` 대신 `--unavailable h15 fetch_failed`. 이어서 27(복사), 28(btc 대조), 29(복사), 30~34(add, status, commit, push, 연구 클론 status).
- **소유자에게 물은 것(답 대기):** SPY 선택지 가(권장: Claude가 fmp 수신을 기간을 나눠 받도록 고치고 새 고정값 기록 → 소유자가 fmp만 다시 받아 SPY 대조를 한 번 더, 첫 실행은 기록에 유지) / 나(독립 증거 없이 "기록하고 진행") / 다(보류). 승인양식 `SPY-가-승인` 등. 답은 원문 그대로 `results/RULINGS.md`와 `OWNER_RULINGS_LOG.md`에 적습니다. "가"면: main에서 새 브랜치, `tools/provider_parity/parity_check.py`의 `fetch_fmp`(528행 부근)를 날짜 구간으로 나눠 요청·병합·중복 제거하고 한 구간이 상한에 닿으면 알리도록 수정, h15 요청 형식(`H15_URL`, 식별자 `RIFLGFCM03_N.B`)도 조사, 시험·검토·CI → 새 커밋과 sha256을 README·안내서·`results/RULINGS.md`·결정 기록·FACTS에 기록 → 실행 브랜치에 반영(소유자 요약 push와 충돌하지 않게 main을 실행 브랜치에 병합) → 소유자 재수신·재대조. FMP가 2004~2006년 자료를 주는지는 미검증.
- **판독 방법:** 소유자 push 뒤 `git fetch origin claude/provider-parity-runs-20261111` → `git show origin/claude/provider-parity-runs-20261111:results/<run_id>/summary.json`만 읽습니다.
- **소유자 PC 상태(파일럿 전에 정리 필요):** 연구 클론은 `C:\Users\<사용자>\OneDrive\Desktop\QUANTGEN`. UI 브랜치 `claude/friendly-bardeen-r6xe8f`에 있던 것을 소유자가 연구 브랜치로 전환(로컬 `83ee469`, 원격 `8a8c247`보다 스펙 커밋 1개 뒤, 대조가 읽는 표·고정 파일은 동일). 추적되지 않는 폴더 `.agents/`와 `quantgen/`이 있어 러너가 R-01로 거부할 것 → 내용 확인 뒤 클론 밖으로 옮기는 줄을 안내해야 합니다(지우지 않음). 실행표 맨 위에 적어 둠.
- **⑥-1/prep:** 워크플로 완료. 브랜치 `claude/pilot-prep-20261111`(로컬, push 전): `b246b98`(문서 3개, 검증 지적 59건 반영), PC 상태 메모 커밋, main `83046c1` 병합 `e015178`, 기준선 갱신(미커밋). 리허설은 로컬 `scratch/step10-rehearsal`의 `c582f15`(main `9fc3817` 병합) + `a5f904a`(Bonds 화면 검토 수정 F1~F5), **push 금지**. `a5f904a`의 캐시 없는 전체 실행이 도는 중(`scratchpad/reh.json`, 비교 `reh_full.out`) → 기록 301행의 PENDING 줄을 채움 → 기준선 다시 → push → PR → Compliance CI → 병합 → 원장 `⑥-1/prep`. 문서가 모은 소유자 질문 26건(파일럿이 보류로 끝났을 때, 합친 뒤 Windows 전체 검사 재실행, 서명 문장 적용, push 승인, Bonds 화면 선택 7건 등)은 표로 정리해 소유자에게 보고해야 합니다(아직 안 함).

### PR #103 병합 (2026-11-11 13:53 KST) — 가장 최신

- [PR #103](https://github.com/xkg4real/quantgen/pull/103) 병합, main `83046c1`(트리 = head `4d3cc16`). Runtime 42958820518 6/6·Compliance 42958820509 성공, 캐시 없는 전체 실행 769/895(추가 0·제거 0·변경 0). 원장: ⑨-3a/series-files/3, ⑤-2/b/2. "전부승인" 결정 기록 절이 main에 들어갔습니다.
- **열려 있는 PR 없음.** 진행 중인 것은 ⑥-1/prep 워크플로(워크트리 `scratchpad/pilotprep`, 브랜치 `claude/pilot-prep-20261111`, 아직 push 없음)뿐입니다. 리허설 커밋은 로컬 `scratch/step10-rehearsal`의 `c582f15`(main `9fc3817`을 연구 head `8a8c247`에 합침, **push 금지**)이고 초안 3개가 `docs/product/`에 쓰였으며 독립 검증 중입니다. 다음: 검증 지적 반영 → 리허설 커밋의 캐시 없는 전체 실행으로 기록의 PENDING 줄 채움 → main `83046c1` 합침 → 기준선 → push → PR(문서만, Compliance CI) → 병합 → 원장 `⑥-1/prep`.
- ⑤-2/d는 소유자 PC 실행 대기(`waiting_on: owner`).
- 그다음 단위(승인됨, 미착수): ⑨-1/2/e + ⑨-1/2/d/2(같은 파일 `docs/macro_fixtures.py`), ⑨-4/2/c, ⑨-3a/recorder/1, 주문 모듈 안전 설계 문서.

### PR #103 (2026-11-11 13:22 KST) — 가장 최신

- [PR #103](https://github.com/xkg4real/quantgen/pull/103), 브랜치 `claude/series-files-followup-20261111`, head `4d3cc16`. 세 가지를 한 PR에 묶었습니다(compliance 파일 충돌을 한 번에 풀기 위해): ⑨-3a/series-files/3(`a45f216`, `63adcf8`), ⑤-2/b/2(`7161fa2` = 워크트리 `parity`의 `e3e5af0`을 옮긴 것, 시험만·도구 파일 불변), 결정 기록 "전부승인" 절(`45af437`). main `9fc3817`을 합쳤고(`80416a6`) 기준선을 다시 만들었습니다(`4d3cc16`).
- 확인: series-files 72·adoption 35·provider parity 114 통과, compliance 정합성 PASS, 도구 sha256 `f2fe72cd…0184` 그대로. 캐시 없는 전체 실행 `sf4`가 도는 중(`scratchpad/sf4.json`, 기준 `par2.json` 769/895).
- 남은 것: CI(Runtime 약 30분 + Compliance) → 병합(expectedHeadSha `4d3cc16…`, 트리 확인) → 원장 `--done` 두 줄(⑨-3a/series-files/3, ⑤-2/b/2) → Notion 두 페이지.
- ⑤-2/d: 소유자에게 실행 안내서를 파일로 전달했고 "시작해도 됩니다"를 알렸습니다.

### ⑤-2/b 완료와 소유자 실행 대기 (2026-11-11 12:22 KST) — 아래 "현재 상태" 절보다 새 내용입니다

- **⑤-2/b 완료:** [PR #102](https://github.com/xkg4real/quantgen/pull/102) 병합, main `9fc3817`(트리 = head `b92275f`). Runtime 42948682493 6/6·Compliance 42948682508 성공, 시험 114개, 캐시 없는 전체 실행 769/895(main `96cca1f`와 같음, 추가 0·제거 0·변경 0). 독립 검증 2관점: blocker·major 0건.
- **고정값(확정):** 도구 커밋 `5202482e3c24de871b8483608b8a03beb07abe1e`, `tools/provider_parity/parity_check.py`의 sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`. 실행 브랜치 `claude/provider-parity-runs-20261111`을 main `9fc3817`에서 만들어 push했고 `git branch -r --contains 5202482`로 확인했습니다.
- **소유자에게 "시작해도 됩니다"를 알렸습니다.** 안내서: main의 `docs/product/PROVIDER_PARITY_OWNER_RUN_2026-11-11.md`(PowerShell 34단계, 15~20분 추정). `waiting_on: owner`는 이 실행을 뜻합니다. 그동안 아래 다른 단위는 계속 진행합니다.
- **⑤-2/d (소유자 PC 실행):** 소유자가 수신 9번, 대조 3번을 돌리고 요약 `results/PP-.../summary.json`을 실행 브랜치에 push합니다. 채팅으로는 수신 마지막 두 줄씩 18줄, PARITY 3줄, 31단계 `git status --short`, 33단계 push 출력 마지막 두 줄을 보냅니다(안내서 5절).
- **⑤-2/e (판독과 관문):** `git fetch origin claude/provider-parity-runs-20261111` 뒤 `git show origin/claude/provider-parity-runs-20261111:results/<run_id>/summary.json`만 읽습니다(`detail.json`·CSV는 PC 밖으로 나오지 않음). 시계열별 첫 PASS·FAIL·WITHHELD가 기록 실행이고 REFUSED·ERROR는 실행이 아닙니다. 관문(스펙 10.5): SPY와 DGS3MO가 PASS이거나 PASS가 아닌 시계열마다 소유자 판정이 `results/RULINGS.md`에 원문으로 적혀 있으면 Pilot 1 가능, BTC-USD는 Pilot 2 전에 같은 규칙. PASS가 아니면 선택지 3개(불일치를 기록하고 진행 / 원인을 찾을 때까지 보류 / 자료 교체)를 정리해 드립니다. 자료 교체는 러너 고정값과 표가 바뀌어 `owner_confirmed`가 무효가 되고 Step 7A 일부를 다시 해야 합니다. Binance 짝은 이력이 2017-08부터라 WITHHELD가 예상됩니다(소유자 결정 대기 항목).
- **⑤-2/b/2 (후속, 시험만):** 검증에서 나온 minor 2건. (1) 수신 기간 거부 시험이 금리(rf)만 다룸 → spy(fmp)와 btc(coinbase)에 늦은 시작·이른 끝을 추가. (2) 공급사 파일의 빈 값·0 값 처리(`read_provider`의 keep_blanks)를 붙잡는 시험이 없음 → rf에 0.00 구간, spy에 빈 값 사례 추가. **도구 파일은 건드리지 않습니다**(고정값 유지). 워크플로의 수정 작업자가 워크트리 `scratchpad/parity`에서 작업 중이며, 끝나면 main에서 새 브랜치를 만들어 그 커밋을 옮기고 PR로 올립니다(시험 수가 바뀌면 README·안내서·FACTS의 "114"도 함께).

### 현재 상태 (2026-11-11 11:51 KST) — 이 절이 가장 최신입니다

- **중단과 재개:** 2026-11-11 07:37 KST 무렵 하위 작업자들이 "out of usage credits"로 멈췄습니다(PR #102 검증 2개, 파일럿 준비 워크플로 전체). 소유자가 11:4x KST에 "Try again"이라고 해서 재개했습니다. 다시 멈추면 아래 상태에서 이어받으면 됩니다.
- **⑤-2/b, [PR #102](https://github.com/xkg4real/quantgen/pull/102):** head `b92275f` push됨(11:50 KST). 커밋 3개: `5202482`(/code-review 지적 F1~F7 수정, 시험 114개), `74397da`(고정값 다시 기록), `b92275f`(compliance 기준선). **고정값이 바뀌었습니다:** 도구 커밋 `5202482e3c24de871b8483608b8a03beb07abe1e`, 도구 파일 sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`(위 P1 항목의 `49a3a67`·`d651795e…` 값은 병합 전에 교체됨, 실행 기록 없음). 다섯 곳(도구 README, 한국어 안내서, `results/RULINGS.md`, `OWNER_RULINGS_LOG.md` 마지막 절, FACTS 행)이 같은 값인지 확인함(`sha256sum tools/provider_parity/parity_check.py`).
  - 남은 것: 독립 검증 2관점(도구 동작, 고정값·기록)이 다시 도는 중 → 지적이 있으면 수정 후 고정값 재기록 → CI(Runtime 약 30분 + Compliance) → `b92275f` 캐시 없는 전체 실행(`scratchpad/par2.json`, 기준 `prep.json` 769/895) → 병합(expectedHeadSha, 트리 확인) → 실행 브랜치 생성(`git push origin origin/main:refs/heads/claude/provider-parity-runs-20261111`, `git branch -r --contains 5202482`) → 원장 `--done "⑤-2/b | ..."` → Notion → 소유자에게 "시작해도 됩니다".
- **⑨-3a/series-files/3:** 브랜치 `claude/series-files-followup-20261111` head `45af437` push됨, PR 없음. 커밋: `a45f216`·`63adcf8`(PR #100 /code-review 수정과 그 검증 수정), `89b751b`(기준선), `45af437`(결정 기록 "전부승인" 절). `89b751b` 캐시 없는 전체 실행 769/895, 기준 대비 추가 0·제거 0·변경 0. 다음: PR #102 병합 뒤 main을 합침(`docs/compliance/FACTS.md`는 양쪽 유지, `source-review.json`은 한쪽을 받고 `--refresh-baseline`, `OWNER_RULINGS_LOG.md` 끝은 P1 절 다음에 "전부승인" 절) → PR → CI → 병합 → 원장 → Notion.
- **⑥-1/prep (6·7번 준비, 소유자 우선 요청):** 워크플로가 도는 중. 워크트리 `scratchpad/pilotprep`(브랜치 `claude/pilot-prep-20261111`, main `96cca1f`에서, 아직 커밋·push 없음)와 `scratchpad/reh`(로컬 브랜치 `scratch/step10-rehearsal`, 연구 head `8a8c247`, **절대 push 금지**). 산출물 3개(모두 `docs/product/`): `PILOT_OWNER_RUN_2026-11-11.md`(소유자용 한국어 실행 순서표: 준비 점검 → Pilot 1 → Pilot 2 → Windows 전체 검사 → 병합 4줄), `PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md`(Claude·GPT용 판독 점검표와 Step 10 마감 기록 틀, 병합 뒤 정리 목록), `STEP10_MERGE_REHEARSAL_2026-11-11.md`(main을 연구 브랜치에 합치는 리허설 기록. 지금 충돌 5개: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, `qa/research_status.json`, `quantgen_desktop/bonds_portfolio_narrative.py`, `ui/bonds_page.py`, `ui/qcharts.py`). 워크플로가 끝나면: 리허설 커밋의 캐시 없는 전체 실행을 돌려 기록의 PENDING 줄을 채움 → main 합침 → 기준선 → push → PR(문서만이라 Compliance CI) → 병합 → 원장.
  - 이 워크플로가 다시 죽으면: 경로 조사 결과 `scratchpad/pilot_path_1111.json`(단계 S1~S13과 연구 브랜치 근거 줄)의 내용이 위 세 문서의 뼈대입니다. 연구 브랜치 근거: `docs/nautilus_bridge/RUNBOOK_windows.md`, 스펙 `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`(Step 8·9·10은 1631~1633행 부근, 10.3~10.5는 1656~1777행, 거부 코드 1263~1303행), `tools/nautilus/runner.py`. Pilot 1 명령: `python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot1_E1_spy.json --of-record`.
- **⑨-1/2/d/2 (PR #101 `/code-review high`, 병합 뒤 검토, 미수정 5건, 모두 `docs/macro_fixtures.py`):** (R1, 418행) `generate`가 out_dir을 쓴 뒤에 `freeze`가 md5를 비교해, 거부(FixtureChanged)되기 전에 동결 파일이 이미 덮어써짐 → 최종 쓰기 전에 manifest와 비교. (R2, 292행과 `tests/macro_m1_calendars.py` 405행) 긴 형식 F27이 종목별로 묶여 있으면 날짜 순서 위반으로 거부 → 종목별 순서 허용을 생성기와 판독기 양쪽에. (R3, 270·276행) 날짜 열을 첫 열로 가정, 날짜 파싱 오류에 파일·줄 없음. (R4, 358행) 최종 복사가 전부 아니면 전무가 아님. (R5, 350행) 결과표를 `read_text`로 읽어 CRLF가 LF로 바뀜(바이트 그대로 복사가 아님). ⑨-1/2/e(KRW=X 뉴욕 17:00 스탬프, A-1)와 같은 파일이라 같은 PR에서 고칩니다. 기준 자료 파일이 저장소에 없어 지금까지 결과에는 영향 없음.
- **아직 시작하지 않은 승인된 단위:** ⑨-1/2/e, ⑨-4/2/c(채택 결과 조립, B Q1~Q3), ⑨-3a/recorder/1(화면 없는 기록기 본체, Q12 7개 파일, 결정 9 조건), 주문 모듈 안전 설계 문서(문서만, 코드는 ⑦-2 병합 뒤), §10 남은 36개 묶음.
- 하위 작업자 지시문 규칙: 저장소 전체 `find`·`ls -R`·경로 없는 `git ls-files` 금지, 검색은 `git grep ... ':!docs/asset_expansion/cache'`만(소유자: "규칙은 꼭 지키자").

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
