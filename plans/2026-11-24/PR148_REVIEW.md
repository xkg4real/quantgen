# PR #148 (프로젝트 스킬 6개 + quant-analyst) 메인 독립 검토 결과

작성: 메인 세션 QUANTGEN/MAIN, 2026-11-24 19:2x KST. 대상: `claude/quant-skills-20261123` @ `462f7df` (24파일). 방법: 워크플로 wf_3a7ca4ae-206 — 검토 2관점(외부 스킬 내용의 안전성, 저장소 규칙 일치) + 지적마다 반박 검증 1회. 반박 검증 28건 중 26건 완료 시점 기준(반박된 것 5건은 뺌). 큰 참고 문서 6개는 줄 단위로 읽지 않고 패턴 검색으로 봄.

**판정: 지금 상태로는 병합하지 않음.** 아래 "막는 것"과 "주요"를 고친 뒤 다시 확인하면 병합. 이 PR을 만든 세션(소유자 PC의 "Claude Code skills and subagents setup")이 이 문서를 읽고 고치거나, 소유자가 메인에게 고치라고 하면 메인이 같은 브랜치에 커밋을 더한다.

## 막는 것 (1)

| # | 파일 | 문제 | 고칠 방법 |
|---|---|---|---|
| B1 | `.claude/THIRD_PARTY_NOTICES.md` 7행, `.claude/skills/nautilus-trader/references/` 6개 파일(약 829KB, PR 24.4k줄 중 20.9k줄) | 참고 문서 6개는 HyperFrequency의 저작물이 아니라 NautilusTrader 공식 문서(nautilustrader.io)를 긁어 온 것이다(각 쪽 머리에 그 URL이 있음). 저작권자는 Nautech Systems인데 고지는 "HyperFrequency, MIT (README; no LICENSE file upstream)"로 적혀 있다. 공개 저장소에 잘못된 라이선스로 재배포하게 된다. | 가장 간단한 길: `references/` 디렉터리를 지우고 SKILL.md가 설치된 1.231.0 소스(이미 "긁은 v1.222.0 문서보다 우선"이라고 적혀 있음)와 공식 문서 URL을 가리키게 한다. 남기려면 Nautech Systems의 실제 라이선스를 확인해 고지를 바로잡고 소유자 판단을 받는다. |

## 주요 (4)

| # | 파일 | 문제 | 고칠 방법 |
|---|---|---|---|
| M1 | `skills/nautilus-trader/SKILL.md:8`, `skills/strategy-workflow/SKILL.md:8`, `skills/tearsheet-generator/SKILL.md:8` | front matter의 `allowed-tools: Read, Write, Edit, Bash, Glob(, Grep)`는 스킬이 켜져 있는 동안 그 도구들을 승인 없이 쓰게 한다. 참고·방법론 스킬인데 Bash·Write·Edit 전체가 승인 없이 풀린다. PR의 CLAUDE.md 절이 Nautilus·백테스트·전략 작업마다 이 스킬들을 읽게 하므로 영향이 넓다. | 세 파일에서 `allowed-tools` 줄을 지운다(쓰지 않는 `version:` 키도 함께). |
| M2 | `.claude/agents/quant-analyst.md:19` 부근 | 이 PR은 "Session pipeline" 절이 없던 옛 main에서 만들어졌다. 서브에이전트가 CLAUDE.md의 인계 규칙을 그대로 따르면 `push_handoff.py`, `git push`, `--done`을 직접 할 수 있다. 지금 규칙은 하부 세션도 원장을 직접 쓰지 않는다. | "너는 서브에이전트다: `tools/handoff/push_handoff.py`, `git push`, `--done`을 실행하지 않는다. ID·커밋·명령·검사 결과를 부른 세션에 돌려준다"를 더한다. 스킬 경로(`.claude/skills/nautilus-portfolio-bridge/SKILL.md`)도 적는다(이 에이전트에는 Skill 도구가 없음). |
| M3 | `THIRD_PARTY_NOTICES.md:17` | HyperFrequency/skills@7532af7에는 LICENSE 파일이 없고 README의 문구뿐이다. 스킬 3개(nautilus-trader, strategy-workflow, tearsheet-generator)가 여기서 왔다. | 소유자 결정 사항으로 올린다: 받아들일지, 원저자에게 LICENSE를 요청할지, 세 스킬을 QUANTGEN 글로 다시 쓸지. 답을 고지 파일에 적는다. |
| M4 | `THIRD_PARTY_NOTICES.md:3` | "Each copied file states its own changes at its top"이 사실과 다르다(머리 주석이 없는 복사 파일이 여럿). | 해당 파일에 두 줄 머리(출처 저장소@커밋, 라이선스, 바꾼 것)를 넣거나 문장을 사실대로 고친다. |

## 작은 것 (같은 커밋에서 함께 권장)

- `tearsheet-generator/references/html_templates.md`: 조건 없이 들어가는 "Nautilus Verified" 배지(58~64행)와 그 CSS, 예시 수치가 자리표시 대신 그대로 박힌 곳(+45.2%, Sharpe 2.45, 18.75x 등), 원저자 상표가 남은 꼬리말(701행 "QuantusMaximus ... strategy_tearsheet.py") → 배지 삭제, 수치는 `{{...}}`로, 꼬리말은 중립 문구로.
- `tearsheet-generator/commands/verify-mae-lev.md`, `verify-backtest.md`: 같은 거래의 MAE로 레버리지·손절을 정해 Nautilus를 다시 돌리고 "PASSED"를 적는 원본 절차가 그대로다. QUANTGEN에서는 등록 안 된 표본 내 조정 시도다 → 파일 머리에 "QUANTGEN에서는 분석만, Nautilus 실행은 `tools/nautilus/runner.py`로만, 새 설정은 원장에 먼저 등록" 주석을 넣거나 파일을 뺀다.
- `tearsheet-generator/tearsheet_helpers.py:115`: MAE 자료가 없으면 최대 레버리지 50배와 위험 "LOW"를 돌려준다(빈 입력으로 재현) → 자료 없음이면 권고를 내지 않게 고치고 고지에 변경을 적는다. 고지는 "unchanged"라고 하지만 줄바꿈이 CRLF로 바뀌어 있다.
- `nautilus-trader/references/getting_started.md`: 원격 자료를 내려받는 예시(213행 `urlretrieve`, 고정되지 않은 main 브랜치) → B1에서 디렉터리를 지우면 함께 해결.
- `nautilus-trader/references/concepts.md:984`: 거래소 어댑터 import 예시가 하나 남아 있다(QUANTGEN 금지 접두어) → B1과 함께 해결.
- `nautilus-portfolio-bridge/SKILL.md`: `.env`를 열지 말라는 문장이 없다(52행이 `.env` 키를 언급) → "`.env`와 `~/.nextgen`은 열거나 출력하지 않는다, 변수 이름만"을 규칙에 더한다. 28행의 시범 실행 상태가 낡았다(두 시범 모두 2026-11-13 기록 실행, 10단계 2026-11-17 종료). 54·70행의 "requirements·pyproject·config.py는 바꾸지 않는다"는 다리 작업에만 해당한다고 범위를 적는다.
- `agents/quant-analyst.md`: 마지막 문장("...generate consistent alpha...")과 고빈도·실행 최적화 목록이 연구·모의 전용 범위와 어긋난다 → "실패나 WITHHELD도 유효한 결과이며, 관문을 통과시키려고 설정을 조정하지 않는다"로 바꾸고 목록을 지운다.
- `portfolio-optimizer/SKILL.md:14`: 소유자 거주 국가를 적은 구절은 필요 없다 → 범위 이유만 남긴다.
- 긁어 온 문서 6개에 폭 없는 공백 문자(U+200B) 378개 → B1과 함께 해결.
- `tearsheet-generator/references/index.md:21`: `sys.path.insert(0, ".claude/skills/...")`로 가져오라는 안내 → 파일 하나를 절대 경로로 불러오거나 별도 프로세스로 실행하라고 고친다. 이 파이썬 파일은 저장소의 어떤 검사 범위에도 들지 않으므로 sha256을 고지에 적는다.

## 확인했고 문제가 없던 것

- 24개 파일에 모델을 겨냥한 지시문(프롬프트 주입 문구), 숨은 지시가 든 주석, 양방향 제어 문자는 없다.
- 설치·원격 실행 명령(curl, wget, pip install, npx, git clone 등)은 없다. API 키·비밀키·지갑 문자열도 없다.
- `tearsheet_helpers.py`(469줄)에는 subprocess, requests, urllib, socket, eval/exec, pickle, 출력 경로 밖 쓰기가 없다.
- CLAUDE.md에 더한 13줄은 인계 규칙을 뒤집지 않는다(순서: 명세 → 다리 스킬 → 일반 스킬). 병합 트리에서 compliance `--check`는 PASS다(`.claude/`는 추적 범위 밖).
- 스킬 이름은 기존 `quantgen-paper`와 겹치지 않는다.

## 병합 전 다시 볼 것

1. `git diff --stat origin/main...HEAD -- . ':!docs/asset_expansion/cache'`에 `references/`가 없고(B1을 삭제로 풀 때) `allowed-tools`가 0건(`grep -rn "allowed-tools" .claude/skills` → 없음).
2. `THIRD_PARTY_NOTICES.md`의 출처·라이선스 표가 남은 파일과 맞음.
3. CLAUDE.md 절은 "Session pipeline" 절 아래로 옮기는 것을 권함(지금은 인계 규칙보다 위).
