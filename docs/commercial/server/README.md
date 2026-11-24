# 회사 데이터 서버 (PAY-3)

법인·공급사 계약 뒤 앱의 `company` 길이 닿을 서버의 설계 문서를 둡니다. 지금은 **설계만** 있고 코드·AWS 자원·계약은 없습니다. 앱 쪽 길은 `core/gateway/remote.py`에 이미 있으며 꺼져 있습니다 (`core/app_identity.py`의 `DATA_API_BASE = ""`).

| 문서 | 내용 |
|---|---|
| [COMPANY_DATA_SERVER_DESIGN.md](COMPANY_DATA_SERVER_DESIGN.md) | 위치와 상관없이 같은 부분 (앱 쪽 계약, 인증·이용 권한, 회사 키 보관, 장애 때 동작, 사용 기록·요청 제한·표시 권리, 비용 항목)과 위치마다 다른 부분 (A 시드니 / B 서울 / C Cloudflare Workers), 결정 목록 |

- 위치는 소유자 결정 **OA-40** 대기입니다. 이 세션의 제안은 A (국내 IP 요구가 확인되면 B).
- 관련: `docs/commercial/GATEWAY_DESIGN.md` 5·8절, `docs/commercial/payments/` (이용 권한의 요금제 상태), `docs/commercial/accounts/` (회원 계정, 데스크톱 로그인 PAY-1).
- 비용·요금 숫자는 모두 미검증이며, 법률 관련 줄은 법률 자문이 아닙니다.
