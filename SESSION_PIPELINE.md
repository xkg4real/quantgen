# SESSION_PIPELINE — 메인·하부 세션 연결 규칙 (상시 지침)

version: 1.1
updated_at: 2026-11-24T18:45:00+09:00 (1.0은 2026-11-19T23:20:00+09:00)
coordinator: 메인 세션 QUANTGEN/MAIN (session_01H6RrzMUzF8vwK8xkX977mB)
함께 보는 파일: `WORKBOARD.md`(전체 업무 체크리스트, 장기 기억), `MERGE_QUEUE.md`(main 병합 순서), `CURRENT.md`(인계), 각 세션의 `*_SESSION_CURRENT.md`

이 문서는 소유자 지시(아래 0절 원문)를 모든 QUANTGEN Claude 세션이 매번 따르는 상시 지침으로 옮긴 것이다. 세션을 시작하거나 재개할 때, 그리고 작업 하나를 끝낼 때마다 이 문서와 `WORKBOARD.md`를 다시 읽는다. 저장소 `CLAUDE.md`의 인계 규칙과 기존 소유자 판정(OWNER_RULINGS_LOG)이 이 문서보다 우선한다.

## 0. 소유자 지시 원문 (2026-11-19, 메인 세션)

> 다음의 글을 현재 프로젝트 내 메모리, 혹은 claude.md처럼 이 세션에서 항상 작동하는 지침으로 인식하고, 이에 맞게 (1) 현재 진행된/진행되고 있는/진행되야할 일을 분석하고, (2) 아래의 파이프라인을 구축하여 당장 다음의 task(ex. background task 이후 해야할 일)을 자동으로 진행해주세요.
>
> 1. 클로드 내 QUANTGEN 메인세션과 하부세션 간 연결 유기화
> - 메인세션:
> ---> 하부 세션간 작업이 마무리되면 그 다음 그 세션이 해야할 작업, 혹은 다른 세션에서 진행할 작업을 바로 mapping해서 전달
> ---> 세션 자체적으로 서브세션을 위한 가이드라인/프롬프트 생성 및 전달, 전체 업무 마무리를 위한 업무처리 구조도(체크리스트)를 .md파일 등으로 장기 메모리로 가지고 있을 것
> ---> 각 작업이 하나하나씩 마무리되면 위에서 언급한 .md파일에서 하나하나씩 완료처리(체크표시 등)할 것.
> ---> 모든 개발이 마무리 된 다음 각 앱의 최종본을 가상환경에서 테스트하고 파일을 주는 역할 수행
>
> - 서브세션:
> ---> 할당된 작업이 마무리되면 바로바로 메인세션에 보고할 것.
> ---> 새롭게 들어온 작업이 들어오면 즉시 착수할 것.
>
> - 두 types of 세션 공통
> ---> 만약 사용자가 24시간 내에 수동으로 진행/서명/작업해야되는 항목이 그 작업 관련 main+sub 세션 전체를 통틀어서 5개가 되면 클로드 앱 푸쉬 알림으로 알릴 것.

## 0-1. 소유자 지시 원문 (2026-11-24, 메인 세션)

> 지피티가 마지막으로 Github Repository에 남긴 인계를 읽고, 세션별로 업무를 배분하여 마저 진행해주세요. 이 역시 지난주와 마찬가지로 24시간 이내 처리해야할 일을 앱 푸쉬 알림으로 전송해주세요.
>
> 위 작업과 더불어, 다음 요청사항을 참고하여 Task를 새롭게 구분/생성/진행하도록 진행해주세요.
>
> 1. 기존의 OS확장, Payment, Data Sourcing과 더불어 DIDM 개발, 그리고 아래에서 설명할 자체 LLM에 대한 세션도 하부 세션에 분리하여 추가해주세요.
>
> 1. 자체 LLM에 대한 개발을 착수할 것. 이때, 자체 LLM의 설계와 관련된 파일은 첨부된 .md 파일 및 Notion의 Autonomous Macro Intelligence Engine을 참고해주세요. 이때, 이와 유사한 구조를 가진 qlib에 대한 문서도 첨부하였으니 참고하시길 바랍니다.
> 2. 위 자체 LLM 개발에 대한 하위 session의 이름은 코드명 QuantGPT로 설정해주시고, 개발에 대한 reference 차 Notion의 Econ493 - 인공지능기반경제분석 -> 신경망과 딥러닝 페이지를 참고해주세요. 참고로 원본 내용은 econ.korea.ac.kr/~chirokhan/econ493/tut 에 있습니다.
> 3. QuantGPT에 대한 내용을 TRADEGEN 세션에도 공유하여 진행해주세요.
> 4. Claude Code skills and subagents 세션에서 적용한 skill 들을 참고 및 다음 /find-skills에 대한 claude code cli 명령을 참고하여 해당 스킬을 적용 및 이를 통해 relevant 한 skill들을 찾아서 능동적으로 적용해주세요. 만약 못찾으면 /reload-skills  적용 후 스킬 적용해주세요.
> 5. Claude.md에 있는 가이드라인을 준수하여 진행해주세요.

같은 날 이어진 말(원문): "그리고 무엇보다 Remaining work에 있는 작업들이 빨리 끝나도록 진행 부탁드립니다" / "GPT 인계를 읽고 이어서 진행하라" / "우선순위라기 보다 같이 병행하는걸 잊지 말라는 얘기였습니다".

같은 날 소유자 결정(메인의 질문에 고른 답, 2026-11-24 18:2x KST): QuantGPT 코드 위치 = "공개 quantgen에서 시작" / 명세서 v1.0 사본을 공개 저장소에 올릴지 = "공개하지 않음 (Recommended)" / TRADEGEN 전달 = "TRADEGEN_GITHUB 다시 열기 (Recommended)".

읽는 법: 새 세션(DIDM 개발, QuantGPT) 작업과 REMAINING WORK의 남은 일은 **함께 병행**한다. 하나를 위해 다른 하나를 미루지 않는다.

## 1. 세션 지도

| 세션 | 종류 | ID | 연락 방법 |
|---|---|---|---|
| QUANTGEN/MAIN | 메인(조정) | session_01H6RrzMUzF8vwK8xkX977mB | 하부 세션은 send_message로 이 ID에 보고 |
| PAYMENTS_ACCOUNT_KEYS | 하부 | session_016uB1jfZfzo935a4uucyT2S | 메인이 send_message |
| OS_EXPANSION | 하부 | session_016uB1jgXiwx42FSUU5ANwM7 | 메인이 send_message |
| DATA_SOURCE (전 DATA_SOURCE_DIDM) | 하부 | session_016uB1jiXnUcWg99JHtRek9T | 메인이 send_message. 2026-11-24부터 데이터 수집·공급사만 (DS-*) |
| DIDM_DEV | 하부 (2026-11-24 생성) | session_016uB1jj8iv57xVbx6EbLLwq | 메인이 send_message. DIDM 모형·평가 (DIDM-*). 인계 문서 `DIDM_SESSION_CURRENT.md` |
| QUANTGPT | 하부 (2026-11-24 생성) | session_016uB1jfyCrLC5oipyVVMyCe | 메인이 send_message. 자체 LLM 시스템, 코드명 QuantGPT (QGPT-*). 인계 문서 `QUANTGPT_SESSION_CURRENT.md`. 코드는 quantgen 브랜치 `claude/quantgpt-q0-20261124`의 `qgpt/` |
| TRADEGEN_GITHUB | 별도 (소유자 PC에서 도는 세션, 실거래 앱) | session_019s6Fyn2GetszXS83ZaV6W9 | QuantGPT 내용 공유만. 클라우드 세션의 메시지는 소유자의 신뢰 확인 뒤에만 닿음(메인 세션은 2026-11-24 거절됨 → QUANTGPT 세션이 시도, 안 되면 소유자가 붙여 넣음). 코드 변경 지시는 하지 않음(통합 PR은 소유자 승인) |
| UI/UX | 별도(메인이 만들지 않음) | — | **소유자를 거쳐서만** (소유자 판정 D6, MERGE_QUEUE 규칙). 메인은 붙여 넣을 글을 만들어 소유자에게 줌 |
| WEBSITE/AWS | 별도 | — | **소유자를 거쳐서만**. 메인은 붙여 넣을 글을 만들어 소유자에게 줌 |
| GPT(Codex) | 인계 상대 | handoff 브랜치 | `CLAUDE.md` 인계 규칙 |

새 하부 세션이 생기면 메인이 이 표에 한 줄을 더한다. 2026-11-24 기준 하부 세션은 5개(PAYMENTS_ACCOUNT_KEYS, OS_EXPANSION, DATA_SOURCE, DIDM_DEV, QUANTGPT)다. DATA_SOURCE와 DIDM_DEV의 파일 경계는 `WORKBOARD.md` 맨 위 블록에 있다.

## 2. 메인 세션의 일

1. **완료 보고를 받으면 바로 다음 일을 보낸다.** 하부 세션의 완료 보고(3절 형식)가 오면, 같은 차례(턴)에서:
   1. 보고 내용을 git·PR·CI로 확인한다(보고만 보고 완료 처리하지 않음).
   2. `WORKBOARD.md`의 해당 줄을 `[x]`로 바꾸고 근거(커밋, PR, 원장 행)를 적는다. 로드맵 ID면 `push_handoff.py --done`으로 원장에도 적는다.
   3. `WORKBOARD.md`와 `MERGE_QUEUE.md`에서 그 세션의 다음 일, 또는 그 결과로 풀린 다른 세션의 일을 찾는다.
   4. 4절 양식으로 지시문을 만들어 그 세션에 send_message로 보낸다. 소유자 손이 필요한 일이면 5절 목록에 올린다.
   5. `WORKBOARD.md`를 handoff 브랜치에 push한다.
2. **가이드라인·프롬프트를 만든다.** 하부 세션에 줄 지시문, UI/웹사이트 세션에 소유자가 붙여 넣을 글을 메인이 만든다. 지시문에는 목표, 근거 파일, 완료 조건(명령과 기대 결과), 금지 사항, 보고 형식을 넣는다.
3. **체크리스트를 장기 기억으로 유지한다.** `WORKBOARD.md`가 전체 업무 구조도다. 작업이 끝날 때마다 한 줄씩 완료 처리하고, 새 일이 생기면 한 줄씩 더한다. Notion은 REMAINING WORK 한 페이지에만 반영한다(소유자 지시 2026-11-07).
4. **병합.** main 병합은 `MERGE_QUEUE.md` 순서대로 한 번에 하나, 메인이 독립 검토 뒤 CI 녹색이면 merge commit으로 한다.
5. **마지막 단계.** 모든 개발이 끝나면 각 앱의 최종본(데스크톱 설치본 OS별, 웹, 그 밖에 `WORKBOARD.md` 5절의 목록)을 가상환경에서 설치·실행 시험하고, 결과와 파일을 소유자에게 준다.
6. **정기 점검.** 메인 세션에는 3시간마다 도는 예약 작업이 있다(2026-11-20 인계 때 꺼 두었고 2026-11-24 다시 켬, 하부 세션 5곳). 하부 세션 상태, 열린 PR, 5절의 소유자 작업 수를 다시 세고, 할 일이 있으면 처리한다. 바뀐 것이 없으면 아무에게도 알리지 않는다.

## 3. 하부 세션의 일

1. **끝나면 바로 보고한다.** 할당된 일(또는 그 안의 한 단계)이 끝나면 같은 차례에 메인 세션(session_01H6RrzMUzF8vwK8xkX977mB)에 send_message로 보고한다. 형식:

   ```
   [<세션 이름> → 메인] 완료: <WORKBOARD ID> <한 줄 요약>
   - 브랜치/커밋/PR: ...
   - 확인한 검사와 결과: ...
   - 남은 것/다음 제안: ...
   - 소유자 손이 필요한 일: <없음 | 무엇, 언제까지(24시간 안인지)>
   ```
2. **새 일이 오면 바로 시작한다.** 메인의 지시문을 받으면 그 차례에 착수한다. 앞 일과 겹치거나 소유자 판정과 어긋나면 착수 전에 메인에 한 줄로 묻는다.
3. **소유자 손이 필요한 일**이 생기면 그 즉시 메인에 보고한다(5절에서 셈).
4. main 병합은 MERGE_QUEUE에 "병합: <세션>"이 적힌 뒤에만 PR을 연다. 자기 `*_SESSION_CURRENT.md`를 마일스톤마다 갱신한다.

## 4. 메인 → 하부 지시문 양식

```
[메인 → <세션 이름>] 다음 일: <WORKBOARD ID> <제목>
- 목표: ...
- 근거 파일: ...
- 완료 조건: <명령> → <기대 결과>
- 하지 말 것: <해당 금지 사항>
- 끝나면: SESSION_PIPELINE 3절 형식으로 메인에 보고
```

## 5. 소유자 수동 작업과 푸시 알림 (두 종류 세션 공통)

- **무엇을 세나:** 소유자가 손으로 해야 하는 일(실행, 서명, 승인, 키 발급·등록, 다른 세션에 글 전달, AWS·웹 콘솔 작업, 결정) 중 아직 안 끝난 것. 지금 어떤 세션을 막고 있거나 기한이 24시간 안이면 "24시간 안" 항목이다.
- **어디에 적나:** `WORKBOARD.md` 3절 표 하나에 모든 세션의 항목을 모은다. 하부 세션은 항목이 생기면 메인에 보고하고, 메인이 표에 적는다(같은 항목을 두 번 세지 않도록 표가 하나뿐).
- **언제 알리나:** "24시간 안" 항목이 메인·하부 전체에서 **5개가 되는 순간** 클로드 앱 푸시 알림을 보낸다. 5개 이상인 채로 계속되면 새 항목이 더해질 때 다시 보내되 6시간에 한 번을 넘기지 않는다. 보낸 시각과 항목 ID를 표 아래 `push_log`에 적어 중복을 막는다.
- **누가 보내나:** 메인이 센다(정기 점검과 보고를 받을 때마다). 메인이 응답하지 않는 동안(예: 사용량 소진으로 인계 상태) 하부 세션이 표를 읽어 5개를 확인하면 그 세션이 보내고 `push_log`에 적는다.
- **알림 문구:** 200자 안, 한 줄. 예: `QUANTGEN: 오늘 직접 하실 일 5건 — DIDM 키 3개, UI 7쪽 실행 확인, 웹 세션 글 전달 (WORKBOARD 3절)`

## 6. 바뀌지 않는 규칙 (요약)

- UI/UX·웹사이트 세션은 소유자를 거쳐서만. 그 세션의 브랜치·인계 파일은 아무도 고치지 않는다.
- main 병합은 한 번에 하나. Vercel 상태는 무시한다.
- `owner_confirmed`, `host_fingerprint`는 Claude가 쓰지 않는다. 원장(~/.nextgen)과 보호 캐시 경로는 열지 않는다. `.env`는 열지 않는다. API 키·비밀값은 출력하거나 요구하지 않는다.
- 확인하지 못한 것은 "미검증"이라고 쓴다.

## 7. 스킬 (2026-11-24 추가)

- 프로젝트 스킬은 저장소 `.claude/skills/`, 서브에이전트는 `.claude/agents/`에 둔다. 첫 묶음은 PR #148(`claude/quant-skills-20261123` @ `462f7df`): `nautilus-portfolio-bridge`(QUANTGEN 규칙, 우선), `nautilus-trader`, `nautilus-authoring`, `strategy-workflow`, `tearsheet-generator`, `portfolio-optimizer`, 서브에이전트 `quant-analyst`. 병합 전에는 그 브랜치에서 읽는다.
- 각 하부 세션은 일에 맞는 스킬을 먼저 읽는다. 지시문에 세션별 목록을 적는다(예: QUANTGPT는 `claude-api`, `skill-creator`, `code-review`, `security-review`; DIDM_DEV는 `data:statistical-analysis`, `backtest-expert`).
- 외부 스킬은 그대로 설치하지 않는다. PR #148처럼 출처·커밋·라이선스·뺀 내용을 `.claude/THIRD_PARTY_NOTICES.md`에 적고, 원격 실행·유료 작업·실거래·키 관련 지시를 뺀 뒤 메인 검토를 거쳐 넣는다.
- 스킬 검색 사이트 skills.sh(`/find-skills`가 쓰는 `npx skills find`)는 클라우드 환경의 네트워크 규칙에 막혀 있다(2026-11-24 확인, 허용은 소유자 승인 사항). `/reload-skills`는 터미널 전용 명령이다. 그동안은 공개 스킬 저장소를 직접 읽어 후보를 찾는다(QuantGPT 후보: huggingface/skills의 `trl-training`, `huggingface-llm-trainer`, `huggingface-community-evals`, `hf-mem`, `hf-cli`).

