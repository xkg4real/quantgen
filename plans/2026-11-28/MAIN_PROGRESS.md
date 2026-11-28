# 메인 세션 진행 기록 · 2026년 11월 28일

## 병합 대기열

- 12~14번 통합 ①은 PR #150으로 main에 병합했다. 결과 커밋 `e5102983bcf5bb6671c6cf68e27aa8726f6fc282`의 트리와 검사한 head `4f53f86`의 트리가 일치한다. GitHub 검사 10개와 인계 테스트 17개가 통과했다.
- **병합: PAYMENTS_ACCOUNT_KEYS (P4)**. 차례 15는 회원 계정 정책 단독 PR이다. 문서 초안의 기술 병합과 실제 상업 공개는 별개다.
- 차례 16의 통합 ②는 후속 검토 중이다. 매출용 P10은 OA-63 결정을 기다린다.

## Remaining Work 확인 기록

| ID | 범위 | 커밋 | 확인 내용 |
|---|---|---|---|
| DIDM-2 | main · #150 | `ba28b021f1a907c105409f2089e710834b39e631` | 계약·JSON Schema와 적합성 예시. 통합 검토 수정 feed288. |
| DIDM-3/a | main · #150 | `3626913987d1b3be8439ef3985b919eead8ba2d0` | 마감일+3개월 자격 규칙과 근거가 있는 행. 3/b 미포함. |
| DS-4a/2 | main · #150 | `593c943c3c2f221f2301fd00ea06b0b9e96c463f` | ALFRED 개정 유효기간을 입력과 조회에서 검사. 검토 후속 d6f6847. |
| DS-4e/2 | main · #150 | `77c37c5e5a866d3162b0675b5480378d1c2ead28` | Kalshi 가격·수량·페이지 검사. 기존 77c37c5 원장 기록을 포괄하는 11/24 공식 하위 ID. 실공급 확인 별도. |
| DS-H/diag | main · #150 | `b70a78d24c4545368c19986b55aaf81865f67a8b` | 홈 지표 진단 명령 및 격리 시험. OA-09 사용자 PC 진단 전. |
| KEY-5/a/2 | main · #150 | `502802e15ce1f23718799637128018a668d7449b` | F5 클래스명 어절 경계 회귀 시험. KEY-5 전체는 별도. |
| OS-A1/apk-evidence | main · #150 | `94f257d98382c709ac29ccd3884dd8dac92b8af4` | 합성 APK 증거 도구와 수동 워크플로. 시작 c28194f, 검토 후속 7d6936e. 실제 빌드·기기 미확인. |
| OS-F2/guide | main · #150 | `000e210daf3e5cbd5770acd34aff7bf528b7a86c` | 소유자 자료 폴더 점검·이전·복구 안내. 문서 변경으로 실자료 이전은 수행하지 않음. |
| SESSION-PIPELINE/2 | main · #150 | `3e2af606c25ac0c0039293e6a8738c0abbeae1c3` | 인계 도구·문서의 5개 하부 세션 등록, 이름 회귀 시험. |
| QGPT-01/a | QuantGPT 연구 브랜치 | `c7e749432cc37c3a439cc7bac3cd63d7351693e3` | qgpt 패키지 골격. 01/b 라이선스 미포함. |
| QGPT-02 | QuantGPT 연구 브랜치 | `073725bf3976446f51fad5c0283d1008a9ce30df` | qgpt-env-v1 봉투·7개 작업 출력 계약·QSS v0. |
| QGPT-04 | QuantGPT 연구 브랜치 | `3e76b35ab60e561d78d363c96679404783abb4c4` | 숫자·인용·시점 누출 검사와 기권 규칙. |
| QGPT-05 | QuantGPT 연구 브랜치 | `735e2c0d36050e92faf7efc31dcfb5e1a155c048` | 합성 연구용 시도 기록 및 DSR 구현. |
| QGPT-21 | QuantGPT 연구 브랜치 | `30b327941830a20be9fefacc517eeffde8463ce6` | 세 가지 호스트 도구 프로토콜. |
| QGPT-03 | QuantGPT 연구 브랜치 | `7478f82364bba54a3ee5a24aa05011aadab1772b` | PF-1~6 정책 필터의 코드와 제한된 시드 규칙. |
| QGPT-02/replay | QuantGPT 연구 브랜치 | `88e42d3a7c36bd747825d4d43bf7d224d2a0ed18` | 요청→봉투, 가짜 백엔드 재생. 하부 인계 QGPT-replay를 공식 QGPT-02/replay로 표기. |
| QGPT-20 | QuantGPT 연구 브랜치 | `273cdec34dbd7b40588bae9fda83a28ca1d98f18` | as_of 시점 검색이 적용되는 SQLite FTS5 인덱스. |

QGPT-11은 부분 완료다. 연구 브랜치에서 채점기의 합성 시험 5개가 통과했다. 평가·학습·보정 데이터 간 중복 검사와 공통 ID 규칙(QGPT-10/a)이 남았다. 실제 학습, 공급사 이용권, 기기 실행과 출시 판정은 이 기록의 완료 범위 밖이다.

[이전 메인 인계](https://github.com/xkg4real/quantgen/blob/3f4741a5a6ada80cca1814f6b715be90f17d066b/CURRENT.md) · [PR #150](https://github.com/xkg4real/quantgen/pull/150)

## 차례 15 회원 정책 문서 분리 · 12:54 KST

- [PR #153](https://github.com/xkg4real/quantgen/pull/153) `f362fa0f7c92f878362a3db22d4bc32662bce556`의 고객용 두 파일은 회원 개인정보 안내 및 가입·광고 수신 문구다. 원본 10개와 운영 근거는 비공개로 보존했다. [#152](https://github.com/xkg4real/quantgen/pull/152)는 대체되어 병합 없이 닫았다.
- 사용자 문구를 정책 7종과 대조했다. 로컬 테스트 62개, 정책 20종·소스 865개 정합성 검사, 원격 [문서 검사](https://github.com/xkg4real/quantgen/actions/runs/46104907296) 통과. 전체 정책 묶음의 공개 전 확인 65건이 남았다.
- #153은 열려 있다. 자동 승인 검토에서 기본 브랜치로의 병합을 차단했다. 차례 16은 계속 대기한다. 회원 화면과 동의 절차를 서비스에 게시하는 결정은 별도다.
