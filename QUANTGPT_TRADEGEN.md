# QUANTGPT_TRADEGEN — QuantGPT 출력 인터페이스 (TRADEGEN 공유용)

- 판: v0.1 초안 (2026-11-24). 작성: QUANTGEN 메인 세션. 구현 담당: 하부 세션 QUANTGPT (quantgen 브랜치 `claude/quantgpt-q0-20261124`, 디렉터리 `qgpt/`).
- 근거: 소유자 지시 2026-11-24 "QuantGPT에 대한 내용을 TRADEGEN 세션에도 공유하여 진행해주세요", TRADEGEN 오케스트레이션 세션("QUANTGEN/TRADEGEN model split")의 요청(같은 날).
- 이 저장소는 공개 상태라 **인터페이스만** 적는다. 설계 명세서 본문, 모델 후보, 세부 일정, 가중치는 적지 않는다(소유자 결정 2026-11-24: 명세서는 공개하지 않음).
- 구현 전 초안이다. 필드가 바뀌면 판 번호를 올리고 아래 "바뀐 내역"에 적는다. TRADEGEN 쪽 소비 계약 문서(xkg4real/tradegen의 문서 PR)가 올라오면 맞춰 고친다.

## 1. 먼저 알아 둘 것: QuantGPT는 방향·확률 예측값을 내지 않는다

| 구분 | 내용 |
|---|---|
| QuantGPT가 내는 것 | 앱 계산 결과의 해설, 자연어 전략의 카드 변환, 근거 기반 질의 응답, 연구 가설 초안, 실험·원장 요약, 뉴스 기사의 유형 판단 |
| QuantGPT가 내지 않는 것 | 가격 방향·수익률 예측값, 매수·매도 확률, 주문·주문 초안·주문 버튼 값, 호가 조정값, 자동 실행 신호 |

- 그래서 BR-26(호가 괴리 Y 조정)과 OQ9(매수 우위)의 **후보 모형으로 바로 쓸 수 있는 수치 출력은 지금 설계에 없다.**
- 수치 신호에 가까운 것은 QuantGPT가 아니라 DIDM 쪽 설계다. DIDM은 뉴스·공시 판단을 충격으로 바꿔 위험 덮개(노출을 줄이는 방향)로 내보내는 연구 계획이고, Stage 0~5 관문을 통과한 뒤에만 동결된 산출물을 읽기 전용으로 내보낸다. 단독 알파는 NO-GO로 사전 등록돼 있다(`docs/didm/PREREG_V0.md`). 아직 어느 관문도 돌리지 않았다.
- QuantGPT에 "거시 사건 분석"(자산별 방향·기간·대안 시나리오를 담는 구조화 출력, owner 모드 전용, 행동·주문 필드 없음) 작업 유형을 더할지는 **소유자 결정 대기**다. 더해져도 그 `direction` 값은 보정된 확률이 아니라 정성 판단이고, 검증 전에는 관찰·모의 기록에만 쓴다.
- TRADEGEN이 방향·확률 모형을 필요로 하면, 그것은 QuantGPT 출력 필드가 아니라 TRADEGEN의 사전 등록 연구(`research_lab`)에서 QuantGPT·DIDM 출력을 **입력 특성**으로 쓰는 별도 모형으로 설계하는 것이 지금 구조에 맞다.

## 2. 출력 이름과 형식

모든 출력은 봉투(envelope) 하나의 형식이다. JSON(UTF-8), 봉투 1개 = 객체 1개, 묶음은 JSON Lines.

| 필드 | 뜻 |
|---|---|
| `envelope_version` | `qgpt-env-v1` |
| `task` | 작업 유형 코드 (아래 표) |
| `mode` | `tool`(QUANTGEN 공개 앱) 또는 `owner`(TRADEGEN) |
| `status` | `ok` / `abstain`(근거 부족·검사 실패로 답하지 않음) / `blocked`(정책 필터에 걸림, tool 모드) / `error`. 받는 쪽은 `ok`일 때만 본문을 쓴다 |
| `body` | 작업 유형별 본문 |
| `numbers[]` | 본문에 나온 숫자와, 그 숫자가 입력 자료에 있었는지(`found_in_payload`) |
| `citations[]` | 근거 `source_id`, 그 근거의 `as_of`. 추가 예정: `verification`(VERIFIED / UNVERIFIED / STALE), `expires_at` |
| `policy` | 정책 필터 위반 목록과 규칙 판 |
| `model` | `id`, `adapter`, `prompt_version`. 추가 예정: `decoding{temperature, seed, max_new_tokens}`, `rag_index_version` |
| `label_ko` | AI가 만든 글이라는 고지 문구 |
| `latency_ms`, `request_sha256` | 지연 시간, 요청 해시 |

| 작업 유형 | 내용 | TRADEGEN에서 |
|---|---|---|
| `T-RESEARCH` | 연구 가설 초안 | `research_lab` 사전 등록 파일로만 저장. 자동 실행 없음. 실행마다 시도 1회로 원장에 기록 |
| `T-REPORT` | 원장·실험 결과 요약(한국어·영어) | 사용 |
| `T-EXPLAIN` | 호스트가 계산한 보고서 JSON의 해설 | 사용 |
| `T-NEWS` | 기사 → 유형 판단 | 별도 어댑터·평가셋·관문. 레코드 형식은 `didm-score-v0` |
| `T-CARD`, `T-QA`, `T-PORT` | 전략 카드 변환, 개념 질의, 포트폴리오 진단 해설 | 필요하면 사용 |

## 3. 시각과 기간

- `as_of`: 근거가 **쓸 수 있게 된 시각**이다(수신 시각 기준). 요청의 `as_of`보다 늦은 근거는 검색 결과에서 빠진다. 발행 시각(`published_at`)은 따로 보관한다. 날짜만 있는 공시 자료에는 +1 거래일을 적용한다.
- 예측 기간(horizon): 지금 출력에는 없다(예측값을 내지 않으므로). 1절의 거시 사건 분석 유형이 승인되면 `assets[].horizon`으로만 들어간다.
- 정정 기사는 앞 기사를 대체하는 연결(`supersedes`)로 표시할 예정이다.

## 4. 값의 정의

- 확신 점수(0~1): 모델이 스스로 낸 값이다. **보정 전에는 확률이 아니다.** 보정 전후의 보정 오차(ECE)를 함께 보고할 예정이며, TRADEGEN은 보정 전 값을 확률로 쓰지 않는다.
- `T-NEWS`의 유형: `didm-score-v0`의 유형 14개와 `none`(quantgen main `core/didm/llm/schema.py`, `SCHEMA_VERSION = "didm-score-v0"`). 모델은 판단 부분만 내고, 참신성·원출처 묶음·신뢰 상태·시장 확인·수신 시각은 DIDM 쪽이 채워 레코드를 조립한다(DIDM-2에서 계약을 정하는 중).
- 방향(direction)·확률: 1절 참고. 지금은 정의된 출력이 없다.

## 5. 모델 이름·버전과 스냅샷 해시

- 모델은 `model.id`(기반 모델과 양자화), `model.adapter`(미세조정 어댑터), `model.prompt_version`으로 식별한다. 셋 중 하나라도 바뀌면 다른 모델로 본다(새 카드, 새 시도 수).
- 시도 원장: 시도 1회 = 목적함수 + 데이터 버전 + 하이퍼파라미터 + 시드 + 모델 버전. 덧붙이기 전용이며 DSR 계산에 시도 수가 들어간다.
- `request_sha256`: 요청(작업 유형, 모드, 입력, `as_of`, 프롬프트 판)을 정규화한 JSON의 sha256. 정규화 규칙은 QGPT-02 구현 뒤 이 문서에 적는다.
- 모델 파일: git에 넣지 않는다. 매니페스트(sha256, 크기, 라이선스)로만 식별한다.
- 같은 입력·같은 모델·같은 디코딩 설정으로 다시 돌렸을 때 결과가 같은지(재생)를 시험하고, 다르면 차이를 보고한다.

## 6. 생성 주기와 일정

- 생성 주기: 요청이 있을 때만(버튼·명령). QuantGPT가 스스로 주기적으로 돌거나 결과를 밀어 넣지 않는다.
- 일정: 2026-11-24 기반 작업(계약, 검사, 시도 원장) 착수. TRADEGEN 통합(다리 모듈, owner 화면 해설 버튼, import 경계 시험)은 평가 기준선 관문 뒤, 소유자 승인 뒤다. 날짜는 공개 문서에 적지 않는다(필요하면 세션 메시지나 소유자에게).

## 7. 경계 (양쪽이 지킬 것)

- `quantgpt` 패키지와 TRADEGEN의 다리 모듈은 `execution`, `execution_accounts`, `execution_control`, `execution_launch`, `execution_network`, `execution_orders`를 import하지 않고, 그 패키지들도 `quantgpt`를 import하지 않는다. AST로 저장소 전체를 검사하는 시험을 둔다.
- QuantGPT에는 브로커 키·계좌·보유 정보를 주지 않는다. 도구 목록에 주문·계좌·키 함수가 없다.
- QuantGPT 출력은 연구 입력으로만 쓴다(TRADEGEN 쪽 순서: 오프라인 재생 → 사전 등록 기준 전향 검증 → 소유자 서명). 실거래 결과를 QuantGPT·DIDM 학습에 되먹이지 않는다.
- TRADEGEN 코드 변경은 TRADEGEN 세션과 소유자 승인으로만 한다. QUANTGEN 쪽 세션은 tradegen 저장소에 push하지 않는다.

## 8. TRADEGEN 쪽에 묻는 것 (소비 계약 문서에 답해 주면 됨)

1. QuantGPT가 건드리면 안 되는 경로·파일·원장.
2. `research_lab` 사전 등록 형식(파일 위치, 필수 필드, 해시·서명 규칙)과, 시도 원장이 목적함수·데이터 버전·하이퍼파라미터·시드를 담을 수 있는지.
3. BR-26·OQ9에 넣으려는 입력의 모양(값의 범위, 갱신 주기, `as_of` 지연 허용, 결측 처리). 1절 때문에 QuantGPT 출력을 그대로는 쓸 수 없으니, 어떤 특성이 필요한지.
4. Python·CI 판, 공개 저장소에서 비공개 의존성을 받을 수 있는지.

## 바뀐 내역

| 판 | 날짜 | 내용 |
|---|---|---|
| v0.1 | 2026-11-24 | 첫 초안 |
