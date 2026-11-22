# QUANTGEN 법인 설립 전 인수인계 · 2026년 11월 23일

## 2026-11-23T05:08:36+09:00 · 법인 설립 전 진행

- **DIDM B6.** 사용자 제공 구성표에 따른 비교안은 B3 8개와 EODHD Fundamentals를 합친 9개입니다. MPT 공식 해설의 두 관측일·계약 분기를 대조했습니다. 분기별 3개월 복리평균 SOFR 분포로 해석하며, 역사 파일의 확률 단위·공표 시각 및 상업 제공 권리는 별도 확인합니다. Alpaca·Massive 합성 45개 사례가 두 Python 버전에서 각각 통과했습니다.
- **DIDM 통합 순서.** #143의 문서 검사와 두 문법 검사가 성공했고 설치 환경 4개가 진행 중입니다. 다음 #144와의 CI 파일에서 텍스트 충돌 한 곳을 재현했습니다. Alpaca 다음에 Massive 시험만 추가한 후보를 검증했습니다. 실제 다음 main에서 입력·기술 지문·전체 CI를 다시 검증합니다.
- **Remaining Work GH-2.** [작업 커밋](https://github.com/xkg4real/quantgen/commit/18d5e507014ff6ce28da40df51788218f860796b)에서 미사용 NPU 예제와 mindmap 파일 5개를 정리하고 개발 실행 설정 하나를 제거했습니다. 연구 화면 문서 2개와 quantgen-web 진입점을 보존했습니다. 합성 패키징·런처 시험 10개, 기술 문서 20개 및 원격 변경 범위를 확인했습니다. 첫 wheel 검증의 시험 경로 문제를 고친 뒤 최종 합성 시험을 통과했습니다. 전용 브랜치까지 완료했고 PR·GH-2 전체 종료는 대기합니다.
- **Android·UI·결제.** Android 내부 프리뷰는 main 666e0064에 있습니다. Android 단독 APK와 기기 확인, UI #140의 Windows PC7, OA-43의 동일 기간 Usage type × Region 자료가 각각 남았습니다.

- [#143](https://github.com/xkg4real/quantgen/pull/143) `5039835a` [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45063116174) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45063116183) success
- [#144](https://github.com/xkg4real/quantgen/pull/144) `270f5daa` [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45058539887) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45058539869) success
- [#145](https://github.com/xkg4real/quantgen/pull/145) `21a0fbf4` [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45058155099) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45058155071) success
- [#140](https://github.com/xkg4real/quantgen/pull/140) `f17df92b` [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45061279851) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45061279863) in_progress

## 법인 설립 전 작업 기록 · 2026-11-23T04:52:13+09:00

- **Android.** 내부 프리뷰 #141을 main `666e0064d446244bfff6a058441c135eeaab825c`에 병합했습니다. 6개 Runtime 작업과 기술 문서 검사가 성공했고 병합 tree를 재확인했습니다. APK를 만들려면 Platform build에서 main을 선택하고 Android만 켭니다. 기기의 Quant Lab → 예시 계산하기에서 101.01·104.69·108.95를 대조합니다. APK 및 기기 증거는 대기 상태입니다.
- **DIDM.** EODHD 입력은 main에 있습니다. Alpaca #143은 새 main을 통합한 `5039835ae7d0f99fde2df2f2cef084a70e11b6d9`입니다. 원격 부모·tree와 네 파일을 대조했습니다. 합성 시험 49개와 데스크톱·모바일 staging을 확인했습니다. Massive #144에서 원래 실패한 import 경계는 Windows 세 버전·Ubuntu에서 모두 통과했습니다. V0 식별자 #145도 같은 네 환경에서 해당 단계에 통과했습니다. 세 PR은 실제 수집 또는 상업권 승인을 포함하지 않습니다. MPT는 공식 파일의 헤더와 단위 근거가 남았습니다.
- **UI.** #140 `f17df92`에서 툴바 배지의 생성 순서를 수정했습니다. 같은 실제 8페이지 Qt 창과 합성 입력의 Linux 시험에서 주창 표시 전 배지 창은 5개에서 0개가 됐습니다. 메인 창은 두 경우 모두 한 번 표시됐습니다. 새 커밋의 전체 CI와 소유자 Windows PC7 실측은 별도로 확인합니다.
- **Payment/AWS.** 기존 소유자 증거를 비공개 비용 분석에 대조했습니다. 같은 기간의 Usage type × Region 내역이 있어야 비용 귀속을 끝낼 수 있습니다. 결제 문의 및 구독 설계 초안은 기존 결정을 따릅니다.
- **Remaining Work.** T8-6 수동 게시 도구의 [작업 커밋](https://github.com/xkg4real/quantgen/commit/2d2e7ad5373b2839f4716e741f9c5c5811dcf611)을 검증했습니다. 임시 Git 시험 16개와 독립 조건 30개를 확인했습니다. 공유 변경 PR은 앞선 변경을 반영한 실제 main 기준으로 진행합니다.

- [#140](https://github.com/xkg4real/quantgen/pull/140) `f17df92b` [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45061279851) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45061279863) in_progress
- [#141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` 병합됨 · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) success
- [#143](https://github.com/xkg4real/quantgen/pull/143) `5039835a` [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45063116183) in_progress · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45063116174) queued
- [#144](https://github.com/xkg4real/quantgen/pull/144) `270f5daa` [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45058539887) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45058539869) success
- [#145](https://github.com/xkg4real/quantgen/pull/145) `21a0fbf4` [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45058155099) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45058155071) success

## 2026-11-23T03:47:46+09:00 · DIDM, Android 및 T8-5

Massive 뉴스 메타데이터를 처리하는 [초안 PR #144](https://github.com/xkg4real/quantgen/pull/144)을 열었습니다. 작업 브랜치 `gpt/didm-b6-massive-news-20261123`, head `6a0336e5cf8e7f52294f518ab437662e3f4869db`, 기준 main `d835d9f495102a6d3244413018db1f9219341716`입니다. 네 파일과 PR 설명·head를 원격에서 대조했습니다. 기사 발행 시각과 직접 수신 시각을 구분하고, 동일 ID의 버전·종목별 감성·페이지 순서를 보존합니다. 원문 링크의 쿼리를 잘라 서로 다른 기사를 같은 주소로 만들던 문제와 커서 처리 문제를 수정했습니다.

제품 시험 18개와 별도 회귀 사례 18개가 Python 3.12 및 3.13에서 통과했습니다. 기술 문서 정합성 검사는 소스 849개·문서 20개에서 통과했고 기존 공개 차단 65건은 유지했습니다. 실제 Massive 수집, 저장소 연결, 역사적 감성의 가용성과 상업 이용 권한은 미확인입니다.

기존 Kalshi 고정 소스는 20번째 페이지에 다음 커서가 있을 때 40개 합성 행에 대해 미완료로 반환합니다. 커서가 소진된 동일 규모는 완료로 반환합니다. 저장된 개별 행에는 배치 단위 완료 플래그가 없으므로 이를 전체 시장의 증거로 해석할 수 없습니다. Atlanta Fed MPT는 공식 파일 헤더·단위·시각 설명이 필요합니다.

T8-5는 소유자가 승인한 증권사 화면 안내의 범위와 KIS·법률 검토 질문을 담은 비공개 초안을 작성했습니다. 실제 주문이나 외부 발송, 공개 구현은 없습니다. 수동 인계 게시 도구 T8-6은 기존 순서를 따릅니다.

Android 빌드 경로·Flet 진입점·GBM 의존성 선언을 재검토했습니다. 소스상 새 차단 결함은 발견되지 않았습니다. APK·실기기와 UI Windows PC7은 계속 확인이 필요합니다. 각 PR의 실행 상태는 아래와 같습니다.

- [#140](https://github.com/xkg4real/quantgen/pull/140) `97152abd` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45055309365) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45055309366) success
- [#141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success
- [#143](https://github.com/xkg4real/quantgen/pull/143) `3b8f39ca` · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054408521) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054408511) in_progress
- [#144](https://github.com/xkg4real/quantgen/pull/144) `6a0336e5` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45057055218) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45057055229) success (2026-11-23T03:48:47+09:00)


주 작업은 상업용 QUANTGEN의 Android 내부 시험(⑮-5)입니다. 사용자가 지정한 단일 요청 창구에서 DIDM·OS·UI·결제·Remaining Work를 분담합니다. 다음 작업자는 최신 CURRENT와 LEDGER의 커밋을 먼저 대조합니다. 이전 Claude 상시 감시는 취소 상태입니다.

| Remaining Work 범위 | 이번 실행에서 확인한 변경 | 다음 검증 |
| --- | --- | --- |
| Data Source / DIDM · B6 | EODHD 경제 이벤트의 제공 자료 파서와 페이지·시각 검증을 PR #142로 main에 병합. 합성 18개, Runtime 6개 작업과 문서 CI 성공. Alpaca News 제목·종목·생성/수정/수신 시각과 페이지 토큰 검증은 PR #143 초안, 합성 20개 통과 | 각 공급원의 상업 수집·저장·표시 권리와 실제 계정 권한. EODHD 과거 예상치가 발표 전에 어떤 버전으로 존재했는지 확인. Alpaca 제공 지연도 확인 필요. 기존 Polymarket V0 보류 유지 |
| OS · ⑮-5 | PR #141에 데스크톱 GBM 계산을 실행하는 모바일 예시 버튼을 구현. 합성 종가 30개, 5일, 256경로, 시드 7. 호스트에서 버튼을 두 번 눌러 15개 출력 대조, 중앙값 104.69와 가운데 90% 구간 101.01–108.95 일치. 데스크톱 5개 설정 호환, 모바일 시험 8개 성공. 실제 staging 스크립트가 출력한 파일 401개와 manifest 확인 | 최종 커밋 Runtime, debug APK, 설치 가능한 실제 Android 기기에서 첫 화면·예시 계산·APK 크기·기동 시간 기록 |
| UI/UX · 데스크톱 PC7 | PR #140에서 같은 테마를 다시 적용할 때 41개 합성 Qt 위젯에 발생한 스타일 이벤트를 81→0건으로 줄임. 실제 테마 전환 81건 유지. 테스트 창 6개의 정상 닫기와 닫기 거부 확인. 원격 웹사이트 기록 갱신, 미전송 | 새 CI 결과. Windows에서 시작·종목 상세·가이드 첫 사례 차트·하단 선 범례·툴팁·호가 막대·창 깜빡임을 확인한 뒤 PC7 판정 |
| Payment / AWS · OA43 | 기존 비용표의 EC2-Other 집중을 확인. 세부 리소스 귀속은 미확정 | 같은 날짜·비용 지표, Credit 제외, EC2-Other만 선택해 Usage type × Region 비용 내역 확인. 기존 결제 문의와 정기결제 초안은 OA32·39 결정 대기 |
| 제품 마감 | 지정된 Remaining Work 페이지에서 ⑮-5와 ⑮-10·11의 조건을 대조. 이번 실행은 보고용 기록 | ⑮-10·11 웹 로그인/계정 및 PG 조건, 실기기·권리 증거와 기술 시험을 각각 확인 |

## 재현과 이어서 할 일

1. 저장된 주 브랜치는 `gpt/android-commercial-preview-20261123`, 커밋 `a35b2f8b3be6e1a757028cb8dd0f14dcc4e58050`입니다. UI `97152abd2ed5159914adbc38f67eabc16f6f71da`와 Alpaca `3b8f39ca7b20d57624601f35310277ad2b4c2abc`는 별도 PR입니다. 세 브랜치 모두 main `d835d9f495102a6d3244413018db1f9219341716`를 포함합니다.
2. Android 빌드는 기존 GitHub Actions **Platform build → Run workflow**에서 Android 브랜치를 선택하고 Android만 켭니다. Windows·macOS·font_probe는 끄고 qt_binding은 기본 PyQt6입니다. 성공 시 실행 Summary의 Artifacts에서 `QUANTGEN-android-debug-<커밋 SHA>`를 받아 실제 기기에서 확인합니다. 현재 클라우드의 Flutter 다운로드 경로는 403이어서 APK를 여기서 만들지 못했습니다. [빌드 화면](https://github.com/xkg4real/quantgen/actions/workflows/platform-build.yml)
3. 세 PR의 최신 head와 전체 CI, 충돌, F 병합 자리, 리뷰·결정 대기를 다시 확인합니다. 병합은 한 번에 하나씩 진행하고 다른 PR은 새 main을 포함한 결과를 재검증합니다. UI의 Windows PC7와 공개 여부는 별개로 기록합니다.
4. B6 공급원 표는 사용자 답변으로 구성 확인을 마쳤습니다. 기존 ALFRED/GDELT/Kalshi와 겹치는 재구현을 피합니다. Atlanta Fed MPT 원본 파일 구조와 Massive Basic 권한을 대조하고, 자체 LLM 평가에 필요한 모델 기준시점·검증 표본과 공급사 확인이 남습니다. 실계정·자동 수집·유료 계약 승인 여부를 추정하지 않습니다.
5. 각 PR, 증거 종류와 미완료 이유를 비공개 Notion 동기화 대기열에 남깁니다. 실제 제공권·결제·실기기 근거 전에는 상위 항목을 완료 처리할 수 없습니다.

[병합된 EODHD #142](https://github.com/xkg4real/quantgen/pull/142) · [Android #141](https://github.com/xkg4real/quantgen/pull/141) · [UI #140](https://github.com/xkg4real/quantgen/pull/140) · [Alpaca #143](https://github.com/xkg4real/quantgen/pull/143)

## 현재 커밋의 CI · 2026-11-23T03:30:31+09:00

- [PR #140](https://github.com/xkg4real/quantgen/pull/140) `97152abd` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45055309365) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45055309366) success
- [PR #141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success
- [PR #143](https://github.com/xkg4real/quantgen/pull/143) `3b8f39ca` · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054408521) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054408511) in_progress

## B6 공급원 후속 확인 · 2026-11-23T03:32:27+09:00

현재 main에는 FRED/ALFRED·GDELT·Kalshi 세 공급원의 수집·정규화 경로가 있습니다. 이번 실행에서는 세 공급원을 실계정으로 호출하지 않았습니다. Polymarket은 V0 보류이고 자체 LLM은 평가·입력 뼈대 단계입니다. Atlanta Fed MPT의 분기 SOFR 분포와 FOMC 회의별 확률은 구분합니다.

Massive 공식 뉴스 안내에서 개인 Stocks Basic의 종목 뉴스가 시간 단위 갱신과 2년 이력으로 제공됨을 확인했습니다. API 문서의 published_utc는 발행사 시각이며 서비스 수신 시각과 감성 점수의 과거 가용 시각은 따로 확인해야 합니다. 다음 구현 단위는 제공된 합성 뉴스의 메타데이터를 검증하는 것입니다. 실제 자동 수집과 상업용 QUANTGEN 고객 표시는 기업 계약·권리 확인 뒤 진행합니다. [뉴스 명세](https://massive.com/docs/rest/stocks/news) · [공급사 이력 FAQ](https://massive.com/knowledge-base/article/how-far-back-does-massives-news-and-sentiment-data-go) · [기업 약관](https://massive.com/legal/businesses-terms-of-service)
