# 감사 제안 패치 (적용하지 않음)

구현 감사(`docs/audit/2026-10-27-implementation-audit-report.md`) §11이 출처로 드는 diff 가운데, 보고서에 경로만 있고 세션
임시 폴더에만 있던 것을 보존한 사본입니다. ②-5 대기열 2단계(`docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md`
4.1)입니다. 어느 것도 저장소에 적용하지 않았습니다. 적용은 해당 PT의 순서와 소유자 결정을 따릅니다.

| 파일 | PT | 감사 출처 |
|---|---|---|
| `proposed_d01_d02.diff` (CRLF 보존), `proposed_d01_d02_lf.diff` (읽기용 LF) | PT-18 | d01_d02 본 diff |
| `proposed_data_flow.diff` (CRLF 보존), `proposed_data_flow.lf.diff` (읽기용 LF) | PT-03 Crypto hunk, PT-14, PT-19 | data_flow 본 diff |
| `sl_all.diff` | PT-01 | functional_completeness 검증 절의 Strategy Lab 합본 |
| `proposed_d04_d05.diff` (CRLF 보존) | PT-09, PT-10 | d04_d05 7.1, 7.2 |
| `proposed_suspension_alt.diff`, `proposed_future_guard.diff` | PT-09 | d04_d05 검증 절(D0405-V02, D0405-V01) |
| `m02_proposed.diff` | PT-03 | suppliers 검증 절 |
| `calendars_pt07_audit_versions/proposed_*.diff` | PT-07 | calendars 7.1~7.4. PT-07은 `d865c7f`에서 검토를 거친 판으로 적용됐으므로, 이 사본은 기록용입니다 |

"applies cleanly" 여부는 이 사본을 만든 시점의 HEAD 기준이며, 커밋 메시지에 적었습니다.
