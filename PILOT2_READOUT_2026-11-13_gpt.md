# Pilot 2 판독과 Step 10 다음 작업 — 2026-11-13

판독 시각: 2026-11-13T21:40:07+09:00
작성: GPT · execution_id: 42710822-a1b3-4677-9377-ed644d5aca21

## 결론과 완료 범위

**소유자 PC의 D2~D11 최종 상태는 정상 완료이며 Pilot 2는 PASS다.**
사용자가 제공한 콘솔과 연구 브랜치의 실제 두 파일을 대조했다.
⑥-2(소유자 실행·결과 push)와 ⑥-2/readout(이번 판독)을 완료로 기록한다.
다음은 소유자 PC의 **E절 Windows 전체 검사**다. ⑦-1 Step 10 전체 및 ⑦-2 main 병합은 미완료다.

- 실행 ID: `NB-20261113T122642089406Z-e2ec073c`.
- 소유자 증거 커밋: [8a3d171fa3e920e26c0b33b0a808f36fc89cd67a](https://github.com/xkg4real/quantgen/commit/8a3d171fa3e920e26c0b33b0a808f36fc89cd67a), 연구 브랜치 `claude/amazing-gauss-tdiguu`.
- 실행 anchor: `git:a2ac79b04bf2e31055c7bc486cb9cffb3727f2c4`. 증거 커밋의 직접 부모이며, 커밋은 run/card 두 파일만 추가했다. 새 소스 변경은 없다.
- 시작~종료: 2026-11-13 **21:26:42~21:27:32 KST**. run.json의 UTC 시각을 KST로 변환했다.
- D3 종료 0, D8 두 파일만 A, D9 두 파일 커밋, D10 원격 push, D11 빈 출력은 사용자의 콘솔 증거다. 원격에서 커밋·부모·두 파일 내용을 확인했다. 현재 소유자 PC를 원격 검사한 것은 아니다.
- 중간 `git add` 오류는 $run에 폴더가 아닌 카드 파일명을 넣은 경로 오류였다. 폴더 경로로 고친 뒤 동일한 결과 두 파일을 추가했으므로 최종 D6~D11을 무효로 만들지 않는다. 해당 오류는 파일럿 실행/판정 실패나 재실행 기록이 아니다.

## 핵심 수치

| 항목 | 관측값 | 적용 기준/뜻 |
|---|---:|---|
| 필수 패리티 | 10/10 조합 통과 | 설정5 × 비용10/20bp |
| 최소 수익률 상관 | 0.999999903862484 | ≥0.9999 |
| 최대 Sharpe 차이 | 0.00027736487978979874 | ≤0.01 |
| 선택 일치 | 29/29 | 진단 P11 |
| 원격 기록의 실패/경고 | 0/0 | 별도 보류 사유 없음 |
| QUANTGEN / Nautilus | PASS / PASS | agree.ok=true |
| 기준 카드 차이 | 없음 | reference.drift=[] |
| C3 등록 행 | 17→22 | 새 설정5개 |
| 시행 수 | 33 | family22 + U11; market8 별도 집계 |
| Nautilus OOS Sharpe | 1.1869744675362457 | 90% 구간 [0.7226758899, 1.6413346528] |
| 2배 비용 Sharpe | 1.1621213061361024 | 비용20bp |
| OOS/IS | 0.8950463251933403 | 기준 ≥0.5 |
| 포지션 변경 | 144 | 기준 ≥100 |
| 벤치마크 단측 p | 0.07 | 기존 기준 ≤0.1; 차이의 90% 구간은 0 포함 |

5개 설정에서는 PBO 약0.19044(Nautilus)/0.19091(QUANTGEN)를 참고로 보고하며,
실제 과탐색 판정은 `prob_loss_oos=0`을 사용한다. PBO 단독을 새 통과 기준으로 삼지 않았다.
기준 카드의 11년은 달력 연도 수이고 이번 9년은 온전한 연도 수다.
시행 수는 기존 카드11에서 이번33으로 바뀌므로 DSR 수치도 달라질 수 있으며, 정의된 reference drift 비교 범위를 따랐다.

**이 결과는 같은 자료·설정을 다른 엔진으로 재현한 증거다.** 새 독립 표본 성과나 실제 주문/수익을 입증하지 않는다.
기존 BTC 공급사 대조 FAIL·원인 미확인은 BTC-라 승인대로 그대로 남고, Step 10 실행 기록과 자료 접근 이력에 함께 적는다.

## 판독 점검표

[판독 절차 1.2~1.3](https://github.com/xkg4real/quantgen/blob/eba94f043765b04fdaa0b7ac41110d2cdfd47efc/docs/product/PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md)를 Pilot 2 조건으로 적용했다.
**24개 판독 항목이 모두 일치했다.** 새 Windows 테스트 24개를 실행했다는 뜻이 아니다.

| 번호 | 확인 항목 | 결과 |
|---|---|---|
| 1 | 최종 상태와 콘솔 | CARD_WRITTEN, 종료 0; 원격 기록과 일치 |
| 2 | 최종 기록 저장 | run.json 정상 저장, fallback/저장 오류 없음 |
| 3 | 결과 파일과 커밋 | 8a3d171은 지정 run/card 두 파일만 추가; Git blob 일치 |
| 4 | 실행 종류 | nautilus-bridge-run/2, of-record, C3-BTCUSD, stub_child=false |
| 5 | 카드 생성 | CARD_WRITTEN 및 지정 카드 존재 |
| 6 | 기준 커밋 | anchor=git:a2ac79b…; 실행 전 clean=true; 결과 커밋의 직접 부모 |
| 7 | 승인 표와 코드 지문 | 표 원문/정규 SHA256 재계산 일치; 기록된 코드 지문은 승인값 f995600b…와 일치 |
| 8 | 입력 메타데이터 | 2014-09-17~2026-09-25, 4,392세션, 승인된 prices_md5와 일치, rf 없음; 캐시 직접 검증 아님 |
| 9 | 출처 검사 | P0a/P0b true, benchmark 4,391행 일치 |
| 10 | 비용 | 기본 10bp, 스트레스 20bp |
| 11 | 외부 연결과 엔진 제한 | 기록상 egress blocked=true, BACKTEST; live/sandbox/live_clock 거부 |
| 12 | 등록 | 설정 5개 모두 신규 추가, C3 17→22행; 실제 원장은 직접 읽지 않음 |
| 13 | 하위 실행 | 10/10 종료 0, timeout/invalid 없음; 등록 후 해시 echo와 실행 시각 순서 일치 |
| 14 | 필수 패리티 | 10/10 조합 P1/P2/P3/P4/P7/P13 및 P12 두 비용 수준 통과 |
| 15 | 실패와 경고 | 실패 0, 경고 0; P5/P6/P8/P9/P10도 통과 |
| 16 | 시행 수 | 격자5·C3 22·시장8·U11·전체33=22+11 |
| 17 | 두 엔진 판정 | PASS/PASS; 5개 설정의 PBO는 참고, prob_loss_oos=0으로 과탐색 기준 통과 |
| 18 | 판정 일치 | agree.ok=true, 벤치마크 검사 유지 |
| 19 | 기준 카드 대조 | 승인된 기준 카드 MD5 일치; 정의된 비교값 허용오차 내 재현, drift=[]; 달력11년/온전한9년 |
| 20 | 설정 선택 | 29개 기점 모두 일치(29/29); P11 진단 |
| 21 | 보류 사유 | 없음 |
| 22 | 결과 카드 지문 | MD5 9eeacef79dc4f0d54c68622bc49bb6c0 일치 |
| 23 | 카드 연결과 수치 | card ID/run ID/등록 ID/시행 수/판정/Nautilus 통계/재현 한정 문구 일치 |
| 24 | 재실행과 정리 이력 | earlier_runs=[], supersedes/rerun_reason/error=null, cleanup_leftovers=[] |

## 증거 파일 식별

읽은 자료는 아래 원격 JSON과 사용자의 콘솔이다. 캐시나 실제 원장의 내용은 직접 열거나 해시하지 않았다.

| 파일 | Git blob | SHA256 |
|---|---|---|
| run.json | c2ae8d8819cfc3dc0cd42461e5626b7052696a3b | f355130ed4e020dbcdf36c5f5faa27f3ff44b9a0791a4611382c89c092361500 |
| 결과 카드 | 04f7acab63408461c418447f97cc637e08d1efdd | 7a697fce504c8fc262c4aede8b53e9c08ec1a65d07baa9fb9ece745b956c4718 |
| Pilot 2 등록 표 | 98710c1e89ffc10c50fe5c667b0399bf05d82175 | f7448fa99b2b2a2052e2c03fab1f18a5c0428430740d4ceb172614637bba9df5 |
| 기존 기준 카드 | 9521f7d5d177d6bda87c04f89bd9f5b5e0ee1342 | 08b847a0ea76936ebcbcca3f908968c4206c62efa53c56fcc81fc3668f1be568 |

- [run.json](https://github.com/xkg4real/quantgen/blob/8a3d171fa3e920e26c0b33b0a808f36fc89cd67a/docs/nautilus_bridge/runs/NB-20261113T122642089406Z-e2ec073c/run.json)
- [결과 카드](https://github.com/xkg4real/quantgen/blob/8a3d171fa3e920e26c0b33b0a808f36fc89cd67a/docs/nautilus_bridge/runs/NB-20261113T122642089406Z-e2ec073c/NB_C3_crypto_trend_btcusd.json)
- 표의 정규 SHA256은 owner_confirmed/host_fingerprint를 제외한 sorted compact UTF-8 JSON으로 재계산했다.
- 코드 지문 f995600b…는 기록과 승인값 일치만 확인했다. 이번 판독에서 27개 소스를 모두 다시 해시한 것으로 기록하지 않는다.
- 기준 카드의 지정 비교값을 실제 JSON끼리 대조했다. SR/구간/비율 등의 오차는 1e-9 이내였고, 거래수·세션수·최종 설정은 같았다. 자료 캐시의 md5는 기록된 값 대조에 한정된다.

## 바로 다음 작업 E절

[소유자 실행표 E절](https://github.com/xkg4real/quantgen/blob/eba94f043765b04fdaa0b7ac41110d2cdfd47efc/docs/product/PILOT_OWNER_RUN_2026-11-11.md#e-windows-전체-검사-step-10-앞부분)의 순서와 승인 조건을 그대로 따른다.

1. 소유자 PC에서 E1: A1~A5·A9·A10, A8 권장. D 직후에도 이 점검은 한다. D 직후의 10분 원장 대기는 E에 필요하지 않다.
2. 같은 연구 클론에서 `python tests/run_all.py`를 **추가 옵션 없이** 실행한다. 클라우드에서 대신 실행하지 않는다.
3. 끝난 직후 `$LASTEXITCODE`, 전체 검사 마지막 줄, E4 세 줄을 보존한다. 예상은 964행이고 핵심 조건은 FAIL0·nautilus 포함·guard5 PASS다. NOT_RUN을 PASS로 세지 않는다.
4. E4 조건이 다르면 E5로 이상 행을 출력하고 기존 예외 한 건만 적용한다. `nautilus/test_l2_05b_input_linked_to_env_refused` 단독 NOT_RUN은 E에서는 기존 허용 범위지만 F에서는 통과해야 한다. 그 밖의 오류·행수 차이는 판독 전 커밋하지 않는다.
5. 조건 충족 시 E6~E11로 소유자가 qa/acceptance_results.json **한 파일만** 커밋·push한다. 이 실제 결과를 받은 뒤 ⑦-1 후속 문서를 확정한다.

## Step 10에 넘길 내용과 남은 조건

이번 판독으로 마감 기록의 Pilot 2 절에 넣을 값과 D의 정상 완료 근거를 준비했다. 연구 브랜치에는 아직 마감 변경을 올리지 않았다.

- 채울 내용: 위 run ID/anchor/증거 커밋, 5×2 패리티, 신규 C3 등록5행, 시행33, PASS/PASS, drift 없음, PBO 참고용 처리, 29/29 선택, BTC-라/공급사 FAIL·자료 접근 이력.
- E 대기: 실제 Windows 전체 검사 결과·커밋·나열할 NOT_RUN 사유. 예전 844/964 결과를 이번 결과로 대체하지 않는다.
- 이어서 판독 문서 2.3~2.10의 마감 기록·README 집계·스펙 Status·공급사 요약 사본/지문을 준비한다. 소유자 소유인 NB run 폴더와 qa/acceptance_results.json은 에이전트가 수정하지 않는다.
- P2/P3는 지정 연구 마감 담당자의 범위다. 결정11은 후속 세션의 한 줄 승인을 별도로 다룬다. 이번 일반 후속 요청을 연구 브랜치 전체 수정이나 보호 범위 해제의 승인으로 확대하지 않는다. 연구 push 전에는 이 권한 및 실제 E 선행 결과를 구체 변경과 함께 확인해야 한다.
- main을 연구 브랜치에 합치는 P3는 마감 기록 뒤다. 그 뒤 새 확인 문장(결정8)과 F의 합친 상태 Windows 검사 및 소유자 main merge commit이 남아 있다. F 시작 전까지 기존 main 작업이 자동으로 동결되는 것은 아니다.
- ⑦-1/⑦-2, 실제 주문 기능, 실제 법률·라이선스 검토는 완료 처리하지 않는다. 실행표/Remaining Work의 다음 단계만 갱신한다.

이 보고서는 사용자의 직접 판독 요청으로 작성했다. 중단 요청된 반복 운영 문구를 자동 재개하거나 예약을 변경하지 않았다.
