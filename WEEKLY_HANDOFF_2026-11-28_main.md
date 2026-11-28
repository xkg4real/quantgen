# 2026년 11월 28일 메인 인수인계

**13:04 KST · 차례 15 완료.** 소유자 승인으로 [#153](https://github.com/xkg4real/quantgen/pull/153)을 `main`의 `ba021da5`에 병합했다. 고객용 검토 초안 두 파일의 원격 내용과 문서 CI를 확인했다. 시행일은 미정이다. 다음은 차례 16 통합 ②의 기준 main 갱신과 독립 검토다. 세부 결과는 [작업표](plans/2026-11-28/MAIN_PROGRESS.md)에 있다. 다음 단락부터는 이전 시점의 인계 기록이다.

**11월 28일 12:54 KST 갱신.** 차례 15의 회원 정책은 [#153](https://github.com/xkg4real/quantgen/pull/153)에서 고객용 문서 두 편으로 분리했고, [#152](https://github.com/xkg4real/quantgen/pull/152)는 병합 없이 닫았다. 운영 원본은 비공개로 보존했다. 원격 문서 검사와 독립 검토를 통과했으며 `main` 병합은 자동 승인 검토에서 차단되었다. 다음 담당자는 [작업표의 최신 P4 기록](plans/2026-11-28/MAIN_PROGRESS.md)을 확인한다. 아래 내용은 이 결정 전의 인계 기록이다.

## 0. 소유자 보고

통합 ① PR #150은 main에 병합했다. 차례 15의 회원 계정 정책 PR #152는 초안이다. 차례 16의 통합 ②는 작업 브랜치에만 있다. 소유자가 직접 인수를 지시할 때 다음 담당자가 재개한다.

## 1. 확인한 기준점

| 대상 | 커밋 | 확인 |
|---|---|---|
| main, #150 병합 | e5102983bcf5bb6671c6cf68e27aa8726f6fc282 | 병합 부모 de32ea1과 4f53f86, 검사한 head와 같은 트리 95b2ac9. GitHub 검사 10개, 합성 인계 테스트 17개 통과 |
| #152 원격 | ee1628dda35b2e27befe28a4448d92fe326a6a79 | 기존 Claude P4 후보. 현재 main과 충돌. 초안 |
| P4 로컬 통합 후보 | 9832bf31e97c7c8efc90dacc62b430d4f3b1ec98 | 두 부모를 대조하고 FACTS 양쪽 내용을 보존. 테스트 62개, 문서 20개·양식 20개 내보내기 검증. 공개 전 확인 65건 |
| 통합 ② gpt/main-handoff-20261128 | fa5dd535ccb29a603f2782f0a4fb1fbe2571f864 | Claude 원격 56e7b5eb 이후 변경 파일 24개를 원격 blob과 대조. 합성 테스트 256개 통과 |

## 2. Remaining Work

[항목별 증거](plans/2026-11-28/MAIN_PROGRESS.md)에 #150으로 main에 들어간 9개와 QuantGPT 연구 브랜치에서 확인한 8개를 기록했다. QGPT-11은 채점기만 확인했다. 세 데이터 묶음의 중복 검사에는 QGPT-10/a의 공통 ID 규칙이 필요하다. 17개 ID는 CURRENT의 done_ids에 반영했다. 기존 LEDGER.md는 보존했으며, 표준 형식의 추가 행과 WORKBOARD·MERGE_QUEUE의 갱신분은 비공개 전달 자료에 남겼다. 기존 원장에 반영하기 전에는 항목별 증거와 대조해야 한다.

## 3. 통합 ② 검토와 수정

- 3eff78c. 두 SQLite 연결이 같은 사건에 서로 다른 최종 판정을 기록하는 경합과, 규칙 버전을 바꾸었다 돌아왔을 때의 확정 판정 변경을 수정했다.
- a0aab45. GDELT의 파일 공개 시각, 행 발행 시각과 수신 시각을 검사한다. 과거 조회에 미래 자료가 들어오는 재현 사례를 고쳤다.
- 0563a7d. Linux 의존성 검사 실패를 누락 없음과 구분했다. Android 증거 점검 후속 d1b84d6의 파일 다섯 개를 함께 반영했다.
- fa5dd53. 출처가 확인되지 않은 행을 연구 표본에서 제외한다. Alpaca·Massive 연결 확인은 공급사별 요청 한 번, 기사 미저장으로 제한했다.
- 검증은 Linux의 격리된 저장소와 합성 자료에서 수행했다. 실제 기기, 실제 결제, 영업용 공급사 권리와 출시 여부는 별도 확인 대상이다.

## 4. 재현

통합 ②의 fa5dd535ccb29a603f2782f0a4fb1fbe2571f864에서 검증한 19개 모듈은 아래와 같다. 가짜 설정과 임시 SQLite를 사용하고 외부 네트워크 및 환경 파일 접근을 차단한 검증 환경이 필요하다. 원본 데이터로 시험하지 않는다.

```text
tests.didm_confirmation_acceptance  29
tests.didm_confirmations_store_acceptance  10
tests.didm_store_acceptance  13
tests.didm_terms_guard_acceptance  10
tests.didm_gdelt_files_acceptance  11
tests.didm_collection_status_acceptance  11
tests.didm_event_rules_acceptance  10
tests.didm_ingest_acceptance  28
tests.didm_fedwatch_acceptance  11
tests.didm_news_connectors_acceptance  14
tests.didm_edgar_history_acceptance  9
tests.didm_kalshi_history_acceptance  7
tests.home_reason_codes_acceptance  5
tests.qt_port_acceptance  18
tests.linux_runtime_report_acceptance  5
tests.android_apk_evidence_acceptance  51
tests.home_indicators_diagnose_acceptance  8
tests.gateway_remote_acceptance  1
tests.credentials_acceptance  5
```

P4 후보는 두 선행 커밋 e5102983bcf5bb6671c6cf68e27aa8726f6fc282와 ee1628dda35b2e27befe28a4448d92fe326a6a79를 가진 별도 로컬 저장소에서 변경분 번들을 검증했다. 후보 트리 991499ada704f4d953b71052867dbddd4150b410, 변경 파일 10개의 blob이 일치했다. 원격 #152에는 로컬 후보가 반영되기 전까지 이 테스트를 그 PR의 CI로 집계하지 않는다.

## 5. 남은 일과 병합 순서

1. #152. 내부 운영 이력과 전체 검토 기준선을 공개 저장소에 다시 전송하지 않고 정책 변경을 전달할 경로를 확정한다. 반영 후 실제 원격 head의 검사를 확인하고 P4 단독 PR을 병합한다.
2. 통합 ②. 갱신된 main과 합치고, 미결 검토·준법 기준선 및 해당 PR의 웹사이트 변경 기록을 최종 확인한 뒤 별도 PR과 실제 CI를 진행한다. P10은 OA-63 세 가지 결정 전 보류한다. P11의 완료 커밋은 확인되지 않았다.
3. #151. PER·PBR 해설 및 호가 잔량 막대가 있는 UI 후보는 별도 소유자 경로에서 검증한다. 원격 CI 12개 성공. 소유자 PC7 시각 확인과 UI 병합 차례가 남았다.
4. #148. 외부 자료의 재배포 권리와 도구 권한 등 11월 24일 독립 검토의 미해결 사항을 확인한다. 소유자가 라이선스 판단을 제공하기 전에 공개 배포하지 않는다.
5. Claude 연구 초안 3개는 원격 ref나 패치가 확인되지 않았다. 원래 복제본의 커밋 또는 패치를 먼저 대조한다. DIDM 표본과 상업 빌드에서 OA-56·62·63에 해당하는 결정은 작업표에 남아 있다.
6. 소유자의 직접 인수 요청 시에만 최신 CURRENT, 작업표, 병합 순서와 이번 기록을 읽고 이어간다.

[원래 Claude 인계](https://github.com/xkg4real/quantgen/blob/3f4741a5a6ada80cca1814f6b715be90f17d066b/CURRENT.md) · [#150](https://github.com/xkg4real/quantgen/pull/150) · [#152](https://github.com/xkg4real/quantgen/pull/152)
