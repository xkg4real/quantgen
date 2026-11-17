# ⑨-1 재현 스크립트 (2026-11-04)

`docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md`가 [검사]로 인용하는 재현입니다. 시장 데이터, 네트워크, 원장(`~/.nextgen`),
`.env`, 보호 캐시를 쓰지 않습니다. 저장소 파일을 쓰지 않습니다.

| 파일 | 보고서 | 하는 일 |
|---|---|---|
| `probe_lag_audit.py` | 3절, LA-08, LA-16, LA-19, LA-23 | `lag_audit` 검사 P1~P7(stub 시계 P4, 서명 달력 P5 등) |
| `keys_binding.py` | LA-01 | NAV 라인 종가의 바인딩이 `forward_sim`으로 덮이는 키 충돌 재현 |
| `registry_roles.py` | 3절 | 레지스트리 73개 시계열의 역할 바인딩 집계(28개가 감사 대상 역할) |
| `la01_nav_line.py` | LA-01 | 합성 저장소로 `run_decision`을 돌려 NAV 종가 결측(A)과 이른 도장(B)의 결과 확인 |
| `causality_slack.py` | 5절 | 인과 가중치와 한 봉 앞을 보는 가중치를 같은 검사로 구분(numpy만 사용) |

실행(저장소 루트를 첫 인수로; numpy 2.3.5, pandas 2.3.3, scipy 1.18.0 인터프리터; `HOME`과 `TMPDIR`은 빈 임시 디렉터리):

```
python -B docs/nautilus_bridge/lookahead_evidence_2026-11-04/la01_nav_line.py .
```

2026-11-04 결과(Linux, `bb35b3b`): `la01_nav_line.py`의 B에서 `lag_audit.status=fail`, `halted=[]`, KR 두 북 `ARMED`.
