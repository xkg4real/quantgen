# Pilot 1 readout and BTC-라 owner ruling — 2026-11-13

로드맵 ⑥-1/readout. 이미 push된 소유자 PC 실행 결과의 판독 기록이며 새 파일럿·등록·재채점은 수행하지 않았다. 판독은 2026-11-13 16:58:56 KST, BTC-라 승인 수신은 같은 날 후속 대화이며 17:58 KST에 기록했다.

## 1. 판독 결론

소유자 PC에서 생성한 Pilot 1(E1-SPY) 실행은 CARD_WRITTEN으로 끝났습니다. 실행 종료는 2026-11-13 00:31:56 KST입니다. 12개 설정 × 비용 1배·2배 = 24건의 hard parity 검사가 모두 통과했습니다. 두 엔진의 판정은 REJECT로 일치합니다. 사전 예상과 같은 전략 기각이며 브리지 실행 실패가 아닙니다.

- 일별 수익률 상관 최저: 0.9999996240319662 (기준 0.9999 이상).
- Sharpe 차이 최댓값: 0.0006384421130428697 (기준 0.01 이하).
- 실행 오류, 보류 사유, 패리티 실패, 경고, 파일 쓰기 실패, 정리 잔류: 없음.
- 시행 수: 격자 12 / E1 12 / 미국 시장 12 / U 24 / 합계 36.
- 기존 E1 등록 12개를 재사용했고 새로 추가된 등록은 0개입니다. 등록 전후 해시가 같고 24개 child 모두 등록 후 해시를 되돌려 줍니다.
- P11 진단: 38개 origin 중 2개에서 두 엔진의 독립 설정 선택이 다릅니다. 문서 1.2.2의 진단 전용 항목으로, 통과 여부를 바꾸는 실패나 경고로 재분류하지 않습니다.
- 선택 비교에 사용된 공통 규칙: IS 756 / OOS 126 / embargo 21, 38 origins.
- 카드 MD5: dd4e580addeea60359cdd0442f1e9932, run.json에 적힌 값과 일치.
- 카드 SHA256: 56301f4f60e3bff3f6de3e12605825ed3b8784d931141cc760f49515558b428c.
- 실제 PC에서 재실행한 것이 아니라 이미 push된 결과를 판독한 것입니다.

## 2. 체크리스트 1.2.1 대조

| 항목 | 확인 결과 |
|---|---|
| 1. 소유자 콘솔 마지막 줄 | CURRENT와 LEDGER가 STATUS CARD_WRITTEN exit=0을 기록. 이 세션에서 PC 콘솔을 직접 보지는 않음 |
| 2. 결과 파일 경로 | run.json 및 카드가 존재. fallback 파일 없음 |
| 3. 폴더 구성 | 원격 디렉터리에 run.json, NB_E1_trend_spy.json 두 파일만 확인 |
| 4. schema/mode/pilot/stub | nautilus-bridge-run/2 / of-record / E1-SPY / false |
| 5. 상태 | CARD_WRITTEN |
| 6. git 기준 | clean=true, offending=[], anchor_problem=null. 실행 head 8a8c2475…에서 현재 연구 head a2ac79b…까지 결과 파일 2개를 추가한 1커밋뿐 |
| 7. 코드·표 지문 | 판독 문서 기준과 일치: code f995600b…; table d76d2d73… |
| 8. 입력 정보 | 2004-12-01~2026-09-25, 5,489 sessions, rounding_changed=true. 기록의 prices/rf MD5가 체크리스트와 일치. 보호 원본 파일은 읽거나 해시하지 않음 |
| 9. provenance | P0a=true, P0b=true |
| 10. 비용 | 50bp, floor 50bp, stress 2 |
| 11. egress | 기록상 probe.blocked=true |
| 12. 등록 | family E1, col 0~11, 등록 전후 12행, 새 추가 0 |
| 13. child | 고유 (col,stress) 24개; 모두 returncode 0; invalid/timeout 0; 등록 후 해시 echo 24/24 |
| 14. parity | hard_pass=true, P13 24/24 통과 |
| 15. 실패·경고 | failed=[], warnings=[]; P1~P10 실패 없음 |
| 16. 시행 수 | 12/12/12/U24/36, n_trials=family_n_raw+U |
| 17. 판정 | QUANTGEN REJECT / Nautilus REJECT |
| 18. 일치 | gate.agree.ok=true |
| 19. 참조 | gate.reference=null |
| 20. 선택 | origins 38; P11 독립 선택 차이 2회(진단) |
| 21. 보류 사유 | 없음 |
| 22. 카드 지문 | UTF-8 원격 카드 10,032 bytes의 MD5가 실행 기록과 일치 |
| 23. 카드 내용 | ID/판정/run ID/claim_label/등록 config IDs/row MD5/ledger hash 일치 |
| 24. 예외 | 이전 run 없음, supersedes/rerun_reason/error null, record_write_failures/cleanup_leftovers 빈 배열 |

## 3. 완료 범위와 남은 해석

Step 8 실행 증거는 확인됐고, 소유자가 결과 폴더를 연구 브랜치에 올린 것도 확인했습니다. 판독 문서 1.2.5가 이미 지적한 두 문구상의 쟁점은 Step 10 기록에 그대로 넘깁니다.

1. 선택 origin/chosen 전체 목록은 카드가 아닌 run.json의 gate.selection에 있습니다. 카드에는 고정 설명·마지막 선택·walk-forward 요약이 있습니다.
2. child별 manifest/hash 전체는 카드가 아닌 run.json에 있습니다. 카드에는 registration row MD5와 ledger hash가 있습니다.

이를 새로 해결됐다고 선언하거나 스펙·판정 기준을 바꾸지 않았습니다. ⑥ 부모, Pilot 2, Step 10, 연구 main 병합, 법률·라이선스·실거래 승인은 미완료입니다.

## 4. 공급사 대조

SPY 둘째 요약 PP-20261112T073747Z-spy를 직접 확인했습니다.

- 전체 outcome PASS.
- fmp 독립 대조: 공통 5,489일, 허용치 초과 0일.
- yahoo_now: PASS.
- KIS 보조 대조: coverage WITHHELD. 전체 PASS를 KIS까지 모두 통과한 것으로 표현하지 않습니다.
- 요약 SHA256 4ad6c537fa5649a2f5d0ba069fd88a0d8e1a4398ca23308defcc017b118b3c02: Claude 인계/LEDGER의 값과 일치.
- DGS3MO PASS는 이번에 재판독하지 않았으며 Claude 인계의 기존 완료 기록으로만 인용합니다.

BTC 진단은 CURRENT/LEDGER에 보존된 합계를 판독 규칙과 대조했습니다. 원본 PC 진단 출력은 이 세션에서 받지 않았습니다.
both 20, coinbase_only 9, bitstamp_only 9, edge 14/12, unpaired 0/6, venues agree 20.
case 3: 43−9=34>20, 47−9=38>21이므로 성립하지 않음.
case 4: agree=20이 허용치 20/21 모두를 초과하지 않으므로 성립하지 않음.
따라서 case 5, 원인 미확인. 이 진단 결과 자체로는 기존 BTC-나의 자동 진행 조건(case 3)이 충족되지 않는다. 이후 2026-11-13 소유자가 “그러면 라 옵션으로 가겠습니다”라고 직접 선택하여 BTC-라를 승인했다. 원인 미확인과 원래 FAIL을 유지하고 불일치를 마감 기록·자료 접근 이력에 적는 조건으로 Pilot 2 진행을 허용한 별도 판정이다.

## 5. 소유자 결정과 다음 단계

소유자 원문: “그러면 라 옵션으로 가겠습니다”. 직전 비교표와 Pilot 2 설명의 라 옵션(BTC-라)을 지칭한다.

Pilot 1의 parity.hard_pass는 true이고 BTC-USD 관문은 이 명시적 진행 판정으로 충족되었다. 기존 BTC 공급사 대조 outcome은 FAIL이며 원인은 미확인이다. 소유자는 실행표 D의 A1~A10 준비 조건을 다시 확인한 뒤 Windows PC에서 Pilot 2를 실행할 수 있다. 원래 C3 5설정·비용 10/20bp·원장 등록·재실행 규칙을 유지하며, 실행 승인 이후에도 러너 거부 조건과 기존 Windows/마감/병합 조건은 그대로다. 이 문서는 Pilot 2 실행 완료, 데이터 정확성, 전략 수익성, 연구 브랜치 후속 커밋 승인(결정 11) 또는 최종 main 병합 승인을 새로 부여하지 않는다.

## 6. 데이터 접근과 미완료 범위

GPT는 원격 run.json·카드·SPY/BTC summary와 인계 문서의 집계만 읽었다. 원문 체결·가격 배열은 복사하지 않았으며 보호 캐시·.env·실제 원장·소유자 PC에 접근하지 않았다. 실행 결과 판독과 카드/요약 지문 대조를 Step 10 자료 접근 이력에 포함할 것. 새 실행·등록·재채점 0회. Pilot 2, Windows 전체 검사, Step 10, 최종 연구 병합은 미완료다. GPT/Gemini 선택 spec 공개·추가 심사는 NOT_PERFORMED로 유지한다.

## 7. 원격 근거

- [CURRENT](https://github.com/xkg4real/quantgen/blob/7e2d40d5cfc6b2c641d77c51920de205f8792ba2/CURRENT.md)
- [판독 절차](https://github.com/xkg4real/quantgen/blob/9e00bf326acbfd512d6479026946358967dfc078/docs/product/PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md)
- [Pilot run](https://github.com/xkg4real/quantgen/blob/a2ac79b04bf2e31055c7bc486cb9cffb3727f2c4/docs/nautilus_bridge/runs/NB-20261112T153028389916Z-d76d2d73/run.json)
- [결과 카드](https://github.com/xkg4real/quantgen/blob/a2ac79b04bf2e31055c7bc486cb9cffb3727f2c4/docs/nautilus_bridge/runs/NB-20261112T153028389916Z-d76d2d73/NB_E1_trend_spy.json)
- [SPY summary](https://github.com/xkg4real/quantgen/blob/77d2647857325d9a2809f6d8ba0c730097d6ffaf/results/PP-20261112T073747Z-spy/summary.json)
- [Notion REMAINING WORK](https://app.notion.com/p/4065c916fe0c80d2af08c0e7f68817fa)
