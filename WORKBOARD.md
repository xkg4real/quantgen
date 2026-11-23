## 법인 설립 전 Remaining Work · 2026-11-23T06:47:19+09:00

| 분야 | 확인한 개발 결과 | 다음 업무 |
| --- | --- | --- |
| Data Source · DIDM B6 | EODHD·Alpaca·Massive 입력 처리에 이어 05f97df63b · V0 ID·해시 검사가 [main](https://github.com/xkg4real/quantgen/commit/05f97df63b7357c614c699428f8a9fc3088eaa3e)에 반영됐습니다. Kalshi 가격·거래량·페이지 검사는 [작업 브랜치](https://github.com/xkg4real/quantgen/commit/77c37c5e5a866d3162b0675b5480378d1c2ead28)에서 검증했습니다. | 기존 대기열 뒤에 Kalshi를 통합합니다. EODHD 발표 전 예상치, Alpaca 계정의 실제 수신 지연, 공급사별 상업권은 확인이 필요합니다. |
| UI/UX | [#140](https://github.com/xkg4real/quantgen/pull/140) 170369e1 · 도움말의 글꼴·색을 보존하고 테마 변경을 현재 툴팁에 한정했습니다. Linux Qt 5/5, 렌더링 16쌍 일치, 시장 시험 뒤 잔류 창 2→0입니다. | 새 head 전체 CI와 소유자 Windows PC7에서 앱 열 때 깜빡임을 확인한 뒤 병합 여부를 결정합니다. |
| Android ⑮-5 | [상업용 앱 내부 프리뷰 #141](https://github.com/xkg4real/quantgen/pull/141)은 main에 있습니다. [APK 검사 코드](https://github.com/xkg4real/quantgen/commit/c28194f2bb75a888c68b76f3ea6e88fe753bd477)를 실제 SDK 34로 검증했습니다. 서명한 시험 APK 통과, 변조본·서명 없는 파일 거부를 확인했습니다. | T8-6·GH-2 뒤 검사 도구를 PR로 반영하고, Android 단독 수동 빌드에서 실제 APK를 받은 뒤 소유자 폰 첫 실행·예시 계산을 확인합니다. |
| 결제·AWS | 문의 7건과 국내 카드 구독 설계의 기존 초안이 준비돼 있습니다. | 문의 발송 OA-32, 구독 조건 OA-39, 서버 위치 OA-40. 같은 기간 Usage type × Region 비용 내역이 들어오면 OA-43 EC2-Other 귀속을 마칩니다. |
| Remaining Work · 메인 | 5200b6c0da · T8-6 수동 인계 도구를 [PR #146](https://github.com/xkg4real/quantgen/pull/146)로 열었습니다. [GH-2 정리](https://github.com/xkg4real/quantgen/commit/18d5e507014ff6ce28da40df51788218f860796b)는 작업 브랜치에 있습니다. | T8-6 전체 CI와 병합 후 실제 main에서 GH-2를 검증해 PR을 엽니다. 이후 Android APK 검사와 Kalshi가 대기합니다. |

[주간 인계](WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md) · [병합 순서](MERGE_QUEUE.md)

## 법인 설립 전 Remaining Work · 2026-11-23T05:12:36+09:00

| 분야 | 개발·검증 결과 | 다음 업무 |
| --- | --- | --- |
| Android ⑮-5 | [내부 프리뷰 #141](https://github.com/xkg4real/quantgen/pull/141)을 main `666e0064`에 병합했습니다. | [Platform build](https://github.com/xkg4real/quantgen/actions/workflows/platform-build.yml)에서 Android APK를 만들고 휴대폰에서 첫 화면과 예시 계산을 확인합니다. |
| Data Source · DIDM B6 | EODHD 입력 처리는 main에 있습니다. Alpaca·Massive의 합성 입력 45개가 두 Python 버전에서 각각 통과했습니다. | [Alpaca #143](https://github.com/xkg4real/quantgen/pull/143)의 전체 검사와 검토가 먼저입니다. 이후 [Massive #144](https://github.com/xkg4real/quantgen/pull/144)와 [V0 #145](https://github.com/xkg4real/quantgen/pull/145)를 각각 최신 main에서 확인합니다. 공급원별 실수집·상업권 근거는 남았습니다. |
| UI/UX | [UI #140](https://github.com/xkg4real/quantgen/pull/140)의 Linux Qt 시험에서 주창 표시 전 별도 배지 창이 5개에서 0개로 줄었습니다. | 전체 검사와 소유자 Windows PC7에서의 깜빡임을 확인합니다. |
| 결제·AWS | 결제 문의와 구독 설계 초안을 준비했고 AWS CPU 문제의 조치 기록을 대조했습니다. | 문의 발송과 구독 조건은 OA-32·39, EC2-Other 비용 귀속은 OA-43입니다. 비용 귀속에는 같은 기간·비용 기준의 사용 유형별·리전별 명세가 필요합니다. |
| Remaining Work · 메인 | [T8-6 수동 인계](https://github.com/xkg4real/quantgen/commit/2d2e7ad5373b2839f4716e741f9c5c5811dcf611)와 [GH-2 승인 항목 정리](https://github.com/xkg4real/quantgen/commit/18d5e507014ff6ce28da40df51788218f860796b)를 작업 브랜치에서 검증했습니다. | 공유 파일 변경은 중앙 병합 순서에 맞춰 최신 main에서 검증한 뒤 PR로 검토합니다. |

[주간 인계](WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md) · [병합 순서](MERGE_QUEUE.md)

## 법인 설립 전 Remaining Work · 2026-11-23T03:30:31+09:00

EODHD 제공 자료 파싱만 main d835d9f로 병합되었습니다. Android와 UI는 이 main을 통합했습니다. 아래 세 PR은 각각 최신 코드와 테스트를 원격에서 다시 확인한 초안입니다. 준법 문서 CI와 전체 Runtime은 별개로 기록합니다.

- [PR #140](https://github.com/xkg4real/quantgen/pull/140) `97152abd` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45055309365) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45055309366) success
- [PR #141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success
- [PR #143](https://github.com/xkg4real/quantgen/pull/143) `3b8f39ca` · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054408521) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054408511) in_progress

Android 예시 계산·staging과 UI 동일 테마 재적용 수정은 합성 검증을 통과했습니다. 다음은 Android APK와 기기 증거, Windows PC7, Alpaca 전체 CI 및 실제 공급사 권리 확인입니다. 상위 Remaining Work는 계속 열려 있습니다. 자세한 재현 순서와 결제 OA43 증거는 [주간 인수인계](WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md)에 있습니다.

## PR141 Windows fixture 최소수리 전달 checkpoint — 2026-11-23T02:49:20+09:00

- 같은root771b8c78-a4da-492e-bdf3-309980124cbc/task/handoff/OS잠금24775가latestCURRENT5e10785와저장STATE·9c원격ref를대조한뒤동일gpt/android-commercial-preview-20261123에 `693e7cbb39f6e883a093f7484375985eafa83c2a`를expected9c CAS로push/read-back했습니다. 단일부모9c·tree69a2098b036c31198919be3cb324d177dc5926cf·정확3경로본문/blob/compare/PR141head/body가일치합니다. 세경로는시험파일,source-review12,기존PR141웹JSONrevision입니다.
- 시험두표현(temporary root.resolve/relativepath.as_posix)만보정했습니다. Productionstage/앱/정책·모든assertion/8방법/skip/timeout/threshold불변. 같은11방법독립PASS/guard0·source473other불변/actualstage399·기존HEAD/index보존. 기술12만갱신한actual20문서/source848정합PASS·old19및정책/profile/registry/checker불변·publicationBLOCKED65입니다. baseline e06076ff9410fd335bf03419bca1aef0682d067f6bd218a975aab2e745e822fe.
- 기존9c Runtime45043106514의3Windows실패는원문보존했고8.3별칭원인은미확정입니다. **새정확693e7cbb Runtime45051411309/Compliance45051411310는진행중**이며새Windows/전체CI성공을아직주장하지않습니다. PR141draft·main미병합·APK/서명/ownerphone/MonteCarlo parity미실시. CODE조건과OS-A1실증완료를분리하며새owner재승인을요구하지않습니다.
- DIDM PR142@90d3b4bf/Compliance45043431652SUCCESS·Runtime45043431571마지막진행중, UI140@b1Runtime45031992373cancelled/준법SUCCESS·PC7미실시입니다. UI6fixture정리·누적시간측정은다음별도단위이며원인미측정상태로production변경/CI120분상향/검사생략을하지않습니다. 기존법인전Goal활성/자동Claude감시·예약·run_now취소유지, 모든부모·정식완료ID미완료입니다.
- 자세한코드/로그/재현·다음작업은WEEKLY_HANDOFF_2026-11-22_771b8c78.md 최신절과비공개 PR141_WINDOWS_FIX_REMOTE_READBACK_771b8c78.json에보존했습니다. 다음실행은저장execution771/task/handoff/primary693및CURRENT일치를검증한OS잠금→latestSHA CAS+새execution/readback으로현재Goal범위만이어갑니다. 실제Windows/라이선스/API/연구/배포증거를합성으로대체하지않습니다.

---

## 기존 Goal 진행 checkpoint · PR141/142 및 최신 CI — 2026-11-23T02:32:46+09:00

- root execution771b8c78-a4da-492e-bdf3-309980124cbc, 같은task/handoff/session·환경·OS잠금24775의연속소유권을검증했습니다. 기존법인전다섯갈래Goal은활성입니다. 자동Claude감시/자동인수/예약/run_now는취소상태를유지합니다. 현재기록은전체완료·상업출시·Claude자동반환이아닙니다.
- Android OS-A1 [PR141](https://github.com/xkg4real/quantgen/pull/141), gpt/android-commercial-preview-20261123@9c95b9ee1e9621ce887b0217f0c867bcaf6ed724(code2bcd44f9). 모바일전용내부shell·명시staging override·기존글꼴/테마, 같은11방법독립PASS/guard0·stage399/source474불변·source848/docs20기술정합PASS. 원격8경로/부모/tree/본문/blob/PRreadback완료. Compliance45043106562SUCCESS이나 **Runtime45043106514FAILURE**로최신확인됐고첫실패로그분석중입니다. host11PASS로전체CI를대체하지않습니다. desktopmain/core/data/수학/의존성/주문정책은불변입니다.
- DIDM/B6 [PR142](https://github.com/xkg4real/quantgen/pull/142), gpt/didm-b6-eodhd-20261123@90d3b4bf029312430a4ec4692ef7fb90ef548463. supplied EODHD 파싱·forecast시각증거·날짜/page범위계약만구현, 최종04f4d3bf/b9af87ba에서같은18방법독립PASS/guard0/source6불변. source847/docs20기술정합PASS·원격5경로본문/blob/tree/부모/PRreadback. Compliance45043431652SUCCESS/Runtime45043431571진행중. HTTP/키/수집CLI/store/V0/scorer/정답·연구기준연결은없습니다. caller-evidence flag는evidence진위/estimate연결/as-of/actual·previous전체PIT/상업권리를보증하지않고rawJSON은비밀제거기가아닙니다.
- UI PR140@b1a421a565a1d37245a089fc4ef863e58f3e7791: Compliance45031992365SUCCESS, Runtime45031992373은4installed가step14에서cancelled(syntax2SUCCESS). 선행같은53방법은네환경실제PASS이지만전체Runtime통과아닙니다. 4완료로그는“The operation was canceled.”만확인돼명시timeout/단일교착원인은미확정입니다. 다음후보는기존6 ResearchWindow fixture의DeferredDelete 소유창정리/누적시간측정; 실제원인확정전120분상향/시험생략/기준완화없음. 기존PC7/정확최종CI/main조건유지.
- 사용자full본문으로B3/B6구성표공백은해소됐습니다. B6참고구성과기존수집기/미구현·권리/PIT 차이를비공개 B6_PROVIDER_MAPPING_2026-11-23.md/JSON에기록했습니다. 비용·coverage는보고서가정이며상업견적/알파/완료율이아닙니다. 기존Kalshi선택/Polymarket hold·DIDM V0판정기준유지. 실제B6수집/모델평가/권리확정은미완료입니다.
- Android의시장·MonteCarlo·로그인은내부shell에미제공이며APK/서명/휴대폰/parity는미실시입니다. 태스크전용Flet0.85.2/JDK17/Android35 도구8명령은실제exit0이나Flutter SDK/mobilewheelhost CONNECT403으로빌드는미수행입니다. 기존[platform-build](https://github.com/xkg4real/quantgen/actions/workflows/platform-build.yml) Run workflow: ref=gpt/android-commercial-preview-20261123, android=true,windows=false,macos=false,font_probe=false. 현연결도구dispatch미지원/CLI인증실패로실행하지못했고정책우회/환경이전은없습니다.
- 세PR은모두draft/미병합, 실제main은dec979a7fae65d5f749e12193fad3d0a9ce8ddf3입니다. 필수CI/리뷰/소유권/기존F자리조건이통과한CODE범위만한PR씩병합할수있습니다. 141/142의공유source-review/workflow는후속실제main통합과자기delta기준선재검증이필요합니다. OS-A1/DIDM/부모UI·정식완료ID는닫지않으며APK부재를코드검토의새사업승인으로만들지않습니다. F진행중다른main병합금지유지.
- 이전main의OS-F2/DS-H-code/DIDM-1·DS4a/KEY5a는중복하지않습니다. 남음: DS-H실진단/OA46, DIDM실제gold/cutoff/모델평가, KEY5K3/OS-F1 ownergo, PAY/AWS계정·법인/PG/UsageType근거. PAY/AWS는읽기검토만, 자원/과금/실PG변경없음. 정책20/status/registry/profile/checker와old20/실패이력보존, publicationBLOCKED65·선택GPT/Gemini추가spec공개심사NOT_PERFORMED유지.
- Notion은sapientia전용비공개queue부분진척2건/실제pagewrite0, 웹PR141기록queued/NOT_SENT·미적용/미배포입니다. .env/cache/동결·holdout/실제주문·원장/TRADEGEN/로컬PC/공유설정변경0. 작성자/독립은같은11/18이라22/36으로합산하지않습니다.
- 재현문서: codebranches의docs/product/ANDROID_INTERNAL_PREVIEW_VALIDATION_2026-11-23.md와docs/didm/EODHD_SUPPLIED_INPUT_CONTRACT_2026-11-23.md. 같은Flet0.85.2에서python -B -m unittest tests.mobile_startup_acceptance tests.packaging_policy_acceptance -v; DIDM은python -B -m unittest tests.didm_eodhd_acceptance -v.
- 다음안전시작: STATE/환경/OS잠금→저장execution771/task/handoff/primaryAndroid9c와원격CURRENT일치→latestSHA CAS+새execution/readback. 그후PR141진짜CI실패최소수리, UI6fixture측정·정리단위별도배정, PR142정확headCI검증을현재Goal범위에서계속합니다. 보호증거나owner결정을코드/합성으로대체하지않습니다. 상세누적인계 WEEKLY_HANDOFF_2026-11-22_771b8c78.md. 인계일괄저장은도구응답단절후ref미반영을확인했으며동일latesthead에서파일blob별저장으로복구합니다.

---

## UI 네 건 후속 전달 · 주간 Remaining Work 판독 — 2026-11-22T15:29:58+09:00

- 사용자 수동 요청으로만 진행했습니다. execution `6e1ca7eb-74bb-41c3-b056-313bbe8b141c`, 같은 task/handoff ID·branch·직전 fed639d·STATE 일치 및 OS 잠금 후 최신 CURRENT70c488의 소유권을 검증했습니다. 자동감시·자동 인수·예약·run_now는 재개하지 않습니다.
- `gpt/ui-guide-chart-first-20261121@0e78c0897a43cf46bd92ab42ceca311feecd0d14` 전달 완료. 부모 fed639d, tree e23517517873ba98437fec2cafd811fd635c3e5d. 정확13경로 본문/blob·단일부모/tree·compare·expected-head CAS·branch/PR read-back 일치. PR140 draft/open, main dec979a 유지, 병합하지 않았습니다.
- 오늘 구현은 네 건뿐입니다: 부모에 넣은 뒤 표시해 시작 임시 창 방지 / 원사례 첫 화면과 우측하단 실제 선모양 작은 범례 / PER·PBR 교육용 예시 구간·중립 위치 / 파란 매도·빨간 매수 수량과 중앙 가격의 3→10단계씩 호가. 원사례·선택·cursor·zoom·보고서·공유 계산/renderer·데이터/조회/주문 규칙은 보존했습니다. 긴 수량은 실제 글꼴의 전체 문자열 폭을 반영합니다.
- 최종871 동결 fc4075e5에서 실제 고유53개(4/5/19/8/2/2/7/3/3) PASS, 실패/오류/skip0. 별도 실제330px 종목 호스트3조건/6상태, 6→20행/12→40숫자, 가림0, 정상 가로스크롤0·극단값279. 실제QG·17차트+12종목PNG·소스871/private 전후 일치·안전counter0·0700prefix비움. 보고6e2ab1a5/outer3d374442/독립579e20ac. 전체 앱/Windows/실제 공급사·모델·원장 증거는 아닙니다.
- 이전 시작 구성요소11 임시Show→수정후0. 첫 후속53 후보 FAIL(98 subtest/오류1)과 원본 로그를 보존했습니다. 실제 긴수량 가림을 고쳤고, 실제 SVG 순서/태그·유효 합성case명·기존 missing-depth 쌍 계약을 검사하도록 시험의 잘못된 oracle을 수정했습니다. 원 폭/폰트/전체수치/세로 경계 기준은 완화하지 않았습니다.
- 기존 fed639d Runtime44982209688은 전체 FAIL: Windows3환경 동일 정상330폭 가로스크롤106 실패, Linux focused45 이후 전체job취소. 이번 정확0e78 Compliance44993932294 SUCCESS, Runtime44993932277 진행중. 과거 실패/취소를 PASS로 대체하지 않습니다.
- 원checker 20문서/871소스 정합PASS, 공개BLOCKED65 유지. 최종기준선92538507/raw14d55e74. 정책본문/registry/profile/권리·승인 불변이며 기술기록만 갱신했습니다. 웹 PR-140 revision은 NOT_SENT/미적용/미배포. Notion 직접쓰기는 하지 않고 사용자 붙여넣기 보고로 준비했습니다.
- 남음: 정확 후보 필수CI·기존 PC7 후 PR140 조건부 병합 → KEY-5 K3 13접점 → OS-F1 Qt 바인딩 PyQt6→PySide6(OS go 필요). OS-F2 저장분리 코드는 이미 main이며 실제 소유자 자료이전은 별도입니다. DS-H 실진단/OA46·DIDM 평가/실증·PAY 계정/법인/PG/권리 조건은 미완료입니다. ROE/PSR 실수치·검증된 테마 평균은 만들지 않습니다.
- DIDM은 PR138 `53e5e723`에 수집·append-only/as-of 저장·점수 계약·신규성 틀과137 합성시험을 통합한 단계입니다. 과거 소유자 PC의 GDELT/ALFRED/EDGAR/Kalshi/ECOS/OpenDART 수집 증거는 존재하지만 실제 모형 성능·계속 운영·표시권 증거는 아닙니다. DS-4b 무료뉴스는 확인된 이용불가로 보류, V0·14유형·3개월여유·Kalshi 결정을 다시 묻지 않습니다.
- 상세 주간 완료/미완료·DIDM 단계/재현·다음 시작점: [WEEKLY_HANDOFF_2026-11-22_6e1ca7eb.md](WEEKLY_HANDOFF_2026-11-22_6e1ca7eb.md). 오늘 KEY/OS/DIDM/PAY 추가 구현은 하지 않았습니다. 상위UI/KEY/DIDM 완료ID 추가0, 사용자 요청 없이 재개하지 않습니다.

---

## 사례 차트·종목 상세 스타일 수정 전달 — 2026-11-22T12:49:15+09:00

- 사용자 정정: 기존 사례 차트가 가이드 첫 화면에 그대로 보이고 그 실제 선·값·구간 위에 짧은 안내를 넣습니다. 모든 UI는 기존 시장→종목 상세의 QG Interface/N3·색·간격·카드·숫자·펼침 버튼 기준을 재사용합니다. 예시 세션 이름은 보고 형식 설명이며 실제 세션 재편 지시가 아닙니다.
- execution47c97545-1d6c-4871-8a44-fbaca1eb2f82 / 같은 환경·OS잠금73428 / 직전e3f와task/handoff/branch/ab0e·STATE 일치 후 latestCURRENT CAS+readback으로 수동 재개했습니다. 자동감시/예약/run_now는 재개하지 않았습니다.
- 원격 코드 `gpt/ui-guide-chart-first-20261121@fed639d27268defe13969d9718757718bd876df4`, tree716b2f88828f4a1c27a3fee35d7bbd0d6cc3f72d, 부모ab0e71f. 정확13경로 본문/blob·부모/tree·compare13·expected-head CAS 및 branch ref/PR read-back 완료. PR140 draft/open·main미병합, 실제 main dec979a 유지.
- 원사례/date/source/선택/커서/확대/보고서·Signals·공유엔진/renderer/fontpolicy는 보존했습니다. 기존사례는 접지 않고 첫 도표, 가상보조그림만 아래에서 기본접힘입니다. 실제사례 값·기존 좌표에 주석을 붙이며 없는값은 만들지 않습니다. 수급/공매도/호가의 기존데이터·시각·단위/질의 동작은 보존했습니다.
- 최종 동결869/source60246ef7에서 실제45개(5/19/8/2/2/6/3) 수집·실행·고유ID 전부PASS, 실패/오류/skip0. 동일실행의 실제sdSide/sdPage 호스트3조건·접힘/펼침6상태는 별도관측이며 test수에더하지 않습니다. 정상3행12셀·추가7행28셀 모두세로표시, 큰가격은가로스크롤로보존, KOlight/ENdark 실제표면색 확인. 17가이드+6호스트 PNG/실제QG등록·안전6counter0/source869 raw5+정규화·private전후일치/0700prefix비움. 결과04ec0908/outer927afb54/독립bf1939ae.
- 원광역45 PASS66fb537b 뒤 실제호스트 추가3검사에서 2 normal사례의 3번째행(bottom96>viewport82) 가림을 발견했고 FAIL1b7bdb77/캡처를 보존했습니다. 기존45를행표시완료로바꾸지않았습니다. 실제레이아웃/글꼴/표시변경에 따른 측정과 실제셀bottom으로 수정하고 기존stylebookmethod를12/28셀top/bottom검증으로강화했습니다. 원임계값/체크를완화하지않았습니다. 이전missingBabel·JSON-only 로그분류 전수집0실패도보존했습니다.
- 최종 원checker20문서/869소스 정합PASS, 공개준비BLOCKED65. 기준선c6f0d20f(raw867df69a), 독립검토b52542b4. 정책20본문/registry/profile/승인불변, 영향17개기술기록만갱신하고4·5·19객체보존. 실제법률/권리·소유자승인·출시승인아님.
- 정확fed의 Compliance44982209689 SUCCESS, Runtime44982209688 진행중이라는 실관측입니다. 이전Runtime44927449412는cancelled로보존합니다. 전체Runtime/전체앱/소유자Windows PC7·실API/모델/원장 성공을주장하지않습니다. PC7 전UI/main병합·OSgo 전실바인딩변경금지, ROE/PSR/테마실수치·법률/라이선스 조건 유지입니다.
- 웹 PR-140 JSON의 이번revision을 갱신했으나 NOT_SENT/미적용/미배포입니다. Notion은 사용자가 붙여넣을 Remaining Work 기준보고를 요청했으므로 이번회차 직접페이지수정/부모취소선은 하지 않았습니다. 비공개sync queue에 보고준비상태를 남깁니다. 추가 GPT/Gemini spec공개/심사는 선택 NOT_PERFORMED.
- 상세주간인계 [WEEKLY_HANDOFF_2026-11-22_47c97545.md](WEEKLY_HANDOFF_2026-11-22_47c97545.md). 다음은 사용자PC 미리보기확인/정확Runtime결과 판독 및 기존승인조건충족후PR140 병합입니다. 별도미완료 KEY5K3 factory/stream13, OS-F1, DS-H실진단/DS1·DIDM실근거/PAY문서·사업조건은 Remaining Work대로 남깁니다. 기존 Pilot/E/Step10/P3/F·DSHcode137·DIDM138·KEY139 완료를 재실행/삭제하지 않습니다. UI/전체Remaining Work 완료아니며 정식완료ID추가0입니다.

---


## PR140 CI 시험 수리 수동 반환 — 2026-11-22T02:01:59+09:00

- 사용자 “오늘 작업 다 끝난거?” 질문으로 실제상태를 확인해 **전체완료가아님**을보고했습니다. 승인된 UI/CI 범위 안에서만 추가수리했고 자동감시/예약/자동인수/run_now는 재개하지 않았습니다. execution `e3f60f75-beca-4b67-9e22-33bbc4db8f19`, OS배타잠금30394, 동일환경/revision4/cwd를확인했고 직전2f27·task/handoff/branch/head/STATE일치를검증한 CURRENT latestSHA CAS+readback 이후에만 작성했습니다.
- 현재코드 `gpt/ui-guide-chart-first-20261121@ab0e71f515e258f6df37f41f52523c59dc1fd130`, tree `ea05c97c2c7fee0060cd38e25c4e436f4d2e910a`, 부모eb61463. 정확변경4경로는 tests/desktop_workflow_guidance_acceptance.py, tests/desktop_indicator_guide_acceptance.py, tests/guide_docking_acceptance.py 및 docs/compliance/source-review.json뿐입니다. 각원격본문/blob/ref·비교4경로를read-back했고 제품runtime/계산/데이터/외관은0변경입니다. [PR140](https://github.com/xkg4real/quantgen/pull/140)은 draft/open·main미병합입니다. 소유자UI실화면은이전미리보기와같고 branchHEAD만test/검토기록으로갱신됐습니다.
- 원Runtime44917383160은 syntax2 PASS, installed4 FAIL입니다. Ubuntu 및Windows3.11/3.12/3.14 **4개원로그**를모두읽고보존했으며 같은42시험의workflow line69 `29 not greater than 100` 1건에서실패했습니다. 새35/live-score/A3단계는그실행의4개installed에서성공했으나 이후skip은PASS가아닙니다. 원실패증거는 private ci-reading-position-e3f60f75/ORIGINAL4_FAILURE_READBACK.json (401caf05...)와4decoded원로그입니다.
- 원원인은새 chart-first UI의사례차트 기본접힘으로교육화면이짧아졌는데옛시험이3개선택시자동으로큰스크롤이생긴다고가정한것입니다. 앱높이/패딩을추가하거나 >100/offset100 임계값을완화하지않았습니다. 실제context_toggle를열고 checked/visible를검증한뒤 기존조건을유지하고 복귀후 **현재canvas의scrollbar**를다시조회합니다. 인접old guide의 vector grab/background/width·hint/failrow/결론시험도 실제사례열기 fixture만추가해모든기존assertion·수식·자료·다른method를보존했습니다.
- 실제로컬합성 **36개(guide5/data19/risk8/glue2/dock2)** 수집/실행/고유ID모두PASS·실패/오류/skip0입니다. 새actualQt Guide/Workspace/QStack2페이지의 사례열기/100복귀를포함합니다. actual source866 raw5+normalized·private·이전FAIL·0700prefix 전후동일, 안전counter0·실제API/model/ledger0. module mapinit1/memorysub1/on_change memory1(실제refresh0)/fixed120EMA3+SMA3은별도관측이며추가test로합산하지않습니다. 원제품863raw동일, 정확test3만변경. fullResearchWindow legacy6+2/원42전체를로컬에서돌린것은아니며 **새installed CI의 실제결과가아직필요**합니다. 원결과73ba7bff/outerab959f79·독립post407c1bee·정적SOURCE3dcc7a712/독립65e905d0를연결합니다.
- 원checker는20문서/source866 정합PASS·공개준비BLOCKED65입니다. test3의registry영향인 **12 claims의기술source fingerprint만** 갱신했고 다른19review object·20정책본문·registry/profile/승인필드는그대로입니다. 새baseline blob `bf0608430be304ebc34da634dbd0a471ca4fd445`, rawSHA `1e2ac8a217c80ff2ea69c224d449fe851563fb794397672c64b7f6e7758c2a29`; 독립readback8e26a08e. 실제법률/권리·소유자승인·출시준비를승인한것이아닙니다.
- 새정확head ab0e71f의 Compliance [44927449415](https://github.com/xkg4real/quantgen/actions/runs/44927449415) SUCCESS, Runtime [44927449412](https://github.com/xkg4real/quantgen/actions/runs/44927449412) 진행중이라는실관측을남깁니다. **전체CI재검사완료·UI/main완료를아직선포하지않습니다.** Runtime이끝나면사용자다음수동지시로해당head/run/job실제결과를읽고후속실패만수리합니다. 자동재실행/예약감시는없고 CI는승인된기존PR push에따른정상검사입니다.
- sapientia Remaining Work 최소추가 `UI_PR140-CI-context-e3f60f75-20261122`는warning없는page_id응답으로synced, 원25queue기록보존/부모취소선0입니다. 기존PR-140 website JSON/NOT_SENT10기록은제품변경없는test수리로그대로보존하며사이트수신·실반영·배포0입니다. 원2f27의UI35/Native8/PNG3/폰트62of64·미등록2clipping·K2d원strictFAIL과그보조검증한계를지우거나이36과합산하지않습니다.
- 남은실제조건은 Runtime전체통과, 소유자Windows PC7와그뒤UI/main병합, OSgo후실제binding, ROE/PSR실제회계·단위/테마구성·비교데이터·실API/법률/라이선스근거입니다. 사용자가없다고확인한증거를코드/합성으로대체하지않고 GPT/Gemini추가spec공개/심사는선택 NOT_PERFORMED로유지합니다. 원Pilot/E/Step10/P3/F완료기록/연구판정·사전등록·동결/holdout/주문·TRADEGEN·.env/보호cache는변경하거나재실행하지않았습니다.
- 그주전체이력은아래2f27인계의 DSH PR137·DIDM PR138·KEY139 main반영과모든UI후보에그대로이어집니다. 전체Remaining Work완료아닙니다. KEY5K3 factory/stream13은기존private prep미완료입니다. 다음수동작업은 STATE/current_claim의이execution/작업branch/ab0e71f·handoffID를최신CURRENT/LEDGER와대조하고 OS잠금→newexecution/CURRENT 최신SHA CAS/readback 후해당승인범위만재개합니다. 계정사용량은unknown, 완료수/등록/last_run으로성공이나잔량을추정하지않습니다.


---



## 수동 인수인계 / PR140 미리보기 준비 — 2026-11-22T00:12:02+09:00

**자동 감시·예약·자동 Claude 인수·run_now는 취소 상태 그대로입니다.** 동일 ROOT execution `2f27d0c2-57cc-46e7-97d6-fc141d4065c9`, task `claude-resume-20261103`, 기존 handoff ID/session과 OS lock20162를 유지해 처리했습니다. 이번 UI 코드·합성 검증 범위를 보존하고 실제 PC7/전체 CI·실데이터 근거가 필요한 경계에서 수동 반환합니다. UI/KEY5/법률·실운영 전체 완료가 아닙니다. 다음 작업은 사용자의 수동 지시로 이 최신 기록을 읽고 소유권을 검증해 시작하며 예약을 만들거나 재개하지 않습니다.

### 현재 정확한 ref / 검증 범위

| 대상 | 실제 상태 |
|---|---|
| main | `dec979a7fae65d5f749e12193fad3d0a9ce8ddf3`, 이번 UI를 main에 병합하지 않음 |
| 검증 코드 | `bb32d03be3528f6a048fc09eb657a0efd794d771`, tree `4ccfc1843e23844565cb090c7ef45ed201b4e5ae` |
| 소유자 미리보기 | `gpt/ui-guide-chart-first-20261121@eb61463b958bcfd7147b08fd34742afae4cff4e4`, tree `22be9396fa612396c5cd9059372c29404702ee91` |
| PR | [140](https://github.com/xkg4real/quantgen/pull/140), draft/open, main 대비108경로; 보호 캐시/.env 변경0 |
| 마지막 코드 뒤 변경 | eb61463은 bb32d03 뒤 `docs/product/ui_website_updates/PR-140.json` 1개만 추가; 부모/tree/비교/본문/ref read-back으로 확인 |

검증 코드 bb32의 부모는 실제651e16e·maindec979a·K2d7d9a 세 개입니다. 원 Claude UI414ece/중앙822aff/K1a–K2c 이력과 K2d11본문/known52fc, main의 OS-F2·DSH·DIDM·KEY139를 보존했습니다. main/UI의 workflow·FACTS·app 및 새config/KISclient 겹침을 원공통f065 기준으로 합쳤습니다. 실제main의 app.main AST/저장소 준비9행, config OS 경로와 KIS 토큰 경로를 유지했고 config에는 요청된 readonly ccnl 1행만 추가했습니다. 강제 push/Claude·main 직접 push/배포0입니다.

### 이번 UI 결과

- 기술지표27 교육용 차트에 선의 의미·값 비교·관찰/한계 단계를 추가했습니다. 실제자료·Signals·원 계산/공유renderer·원 보고서입력은 유지하며 가상학습 값을 섞지 않습니다. EMA는 최근가격에 가중하는12/26 span, bounded축·NaN gap·선색/점선·실제좌표 주석을 유지합니다. 원사례 차트/날짜/출처는 별도 접기 영역입니다.
- 시가총액 등 분리된 Qt tooltip에 앱의 글꼴/팔레트/논리화면폭 줄바꿈을 적용했고 값·출처·수신/관측 시각·원문 Unicode를 유지했습니다. PER/PBR/ROE/PSR 뜻은 valuation 카드에서 간결하게 설명합니다.
- KIS 기존 quote PBR/BPS와 기존 수급의 gross 매수/매도를 연결하고 5/20일 coverage를 표시합니다. net-only를 매수비율로 만들지 않습니다. readonly 호가/체결강도 snapshot은 준비된 국내클라이언트 경로에각1회/retryFalse이며 새 polling/paging/stream수명주기0입니다. 공매도 거래비중은 잔고와 구분합니다. 실제API·권리 검증을 완료한 것은 아닙니다.
- VaR/CVaR은 짧은 뜻과 실제 기간/신뢰수준/단위/계산기준 hover로 연결했습니다. 저장된신뢰수준누락은 미기록으로 남기고95를채우지 않습니다. MC terminal loss·stock historical loss·hedge signed worst5%P&L(bp)·rates PV금액손실을 구분하며 계산/숫자/record schema/원내보내기수식0변경입니다.
- 실제컨테이너 검사에서 preselected-undocked→dock 칩에bar가없는 기존버그를 찾아 UI칩만재생성했습니다(기본빈선택앱이항상실패한다는뜻아님). 실제PNG의 과도한QVBox세로간격은 AlignTop1줄로 줄였고 제목·차트·간결설명이 첫화면에 보입니다. SVG/math/text18함수는 이 레이아웃변경과 동일합니다.

### 실제 검증 / 실패 기록 / 한계

- 최종통합 **35개**: guide5/data19/risk8/glue2/dock1, 수집/실행/고유ID35·실패/오류/skip0. 실제 source866 raw/normalized/blob/bytes/mode·private·첫FAIL·0700prefix 전후일치, 안전counter0. fake_get4/inertimport2/mapinit1/sub1 및 main의 pure on_change 등록1만 관측, 실제refresh0. synthetic120 dock문맥의 EMA3/SMA3은 primitive6호출이지 추가test가 아닙니다. 독립post `ca0c07e6`, 결과 `e19320a1`/outer `71b97ac8`; 원bootstrap listener거절/cleanup 실패 ef35·log4c10 보존, exact module-registration+cleanup 하네스만 수정했습니다.
- 실제 Guide/Workspace **8계약·PNG3**는 별도 PASS입니다. source153/private32/prefix/guard를 확인했고 in-memory ZIP 원입력을 유지했습니다. 현재 b54df931 lesson/ee9df7cf indicator, 독립visual28bde5b2·4b3f7470. 초기 동적UI문구입력 누락2회와 preselected UI오류1회, 수정 전후 결과를 모두 보존했습니다. fullSignalsPane/전체앱/실제Windows·DPI·설치/실디스크보고서 성공을 대신하지 않습니다. KOcollapsed 캡처의 사례toggle 위치/글자 노출은 실제PC7에서 스크롤·포커스와 함께 확인할 관찰사항이며 실제8 toggle/focus 계약은 통과했습니다.
- Stage1 V3 geometry92/별도pure7/gap1/PNG2 및 tooltip64는 별도범위로 유지합니다. tooltip은 동봉QG32/32 적합이나 총62/64이며 미등록2xENlong2개clipping/tofu 한계를 원flag대로 보존했습니다. 실제Windows 글꼴문제를 Linux재현으로 확정하지 않았고 Qt/Fontconfig의 모든 native C I/O 관측을 주장하지 않습니다.
- risk 추가공개8+realQt4, stock glue2 및 원data19의 최초18PASS1ERROR/수정후19PASS는 서로 겹칩니다. 합산해 전체성공건수를 만들지 않습니다. 기존stock34 suite/activechart/productionFoldSection 전체 실행을 대신하지 않습니다. 기존stock시험34중 의도된2method만 수정했고 나머지 AST와 EPS/risk/source/time/legend 검증은 보존했습니다.
- 통합 gateway boundary는 **실제main의15개** stdlib AST 검사 PASS입니다(이전K2d13과다름). K2d 원 normal strict raw-call 비교의 빈label 전달3곳 FAIL은 그대로이며 기존golden/비교기를 바꾸지 않았습니다. 별도 default-bound/응답 의미보조판독 및 공개6/거절12/경계13이 strict PASS를 대신하지 않습니다.
- 실제원checker의20문서/source866 **정합성PASS / 공개준비BLOCKED65**. 기준선blob `d609823b85fc4757633205b7c68cc33e7818c655`, rawSHA `79591342...`; 실제main 기준선blob9a5e와 main commitdec979를 혼동하지 않습니다. 독립20정책검토565845/f77b12+최종기준선abb1a3a 확인, source_commit은격리plaincopy의null이며 cleanGit checkout attestation이 아닙니다. 법률/라이선스/실제소유자승인을 추가하지 않았습니다.

### 실제 CI / 전달 / 다음 작업

- 이시점 정확 eb61463의 Compliance [44917383129](https://github.com/xkg4real/quantgen/actions/runs/44917383129) SUCCESS, Runtime [44917383160](https://github.com/xkg4real/quantgen/actions/runs/44917383160) 진행중입니다. 전체CI 성공을 선포하지 않습니다. PC7 전 UI/main 병합 및 OSgo 전 실제바인딩전환 금지라는 기존조건을 유지하며 F진행중 다른main PR을 병합하지 않습니다.
- sapientia Remaining Work에 PR140 코드·합성 검증 진척을 최소추가했고 queue `UI_PR140-preview-code-20261122-2f27d0c2`가 warning없는 page_id 성공응답으로 synced입니다. 부모UI/KEY5 취소선0; 이전계정/f77 우회0. `NOTION_SYNC_QUEUE.json`24기록과 원문/이력을 보존했습니다.
- 사이트 기록PR-140.json은 원격blob4b208662로 확인했으며 비공개 website queue10번째는 NOT_SENT/appliedfalse/deployedfalse입니다. 실제HTML반영/사이트배포를 하지 않았습니다.
- 소유자 PC에서 앱을 닫고 기존연구clone에서 다음을 실행합니다: `git fetch origin && git switch gpt/ui-guide-chart-first-20261121 && git pull --ff-only origin gpt/ui-guide-chart-first-20261121 && Start-QUANTGEN-Desktop.cmd`. 예상HEAD eb61463. reset/clean/강제stash/환경·설정·로컬PC변경을 클라우드에서실행하지 않습니다. 연구캐시·실제원장·판정/동결/holdout/사전등록/주문경로/TRADEGEN0변경입니다.
- 남은 UI 조건: 실제Windows PC7/수신데이터/hover·언어/scroll·DPI, 전체CI와실제공급사근거; ROE/PSR 회계/단위 계약과 테마구성종목·동일기간/단위 근거. 업종을테마로임의대체하거나 평균을만들지않으며 기존비동기소유자질문은답변미수신입니다. 추가 GPT/Gemini spec심사/공개는 선택 NOT_PERFORMED로유지하며 그미실시만으로Windows인계를막지않습니다.
- 후속독립 KEY5 K3 factory/stream13접점은 private prep으로보존된 미완료 작업입니다. 사용자의 다음수동작업에서 최신동일handoff/LEDGER·branch/head/직전execution2f27·STATE를대조하고 OS잠금획득→CURRENT최신SHA CAS/newexecution/readback 후 별도승인된범위만이어갑니다. 이UI PC미리보기 ref를 소유자확인중에 임의로바꾸거나 별도Claude/UI/DIDM세션과중복하지않습니다.

### 그 주 전체 인계 연결

앞선 아래기록을 삭제하지 않습니다. 이번 실행에서 DSH code PR137→main6d25a33, DIDM code/synthetic PR138→main53e5e723, KEY139→maindec979a(실제fullCI/parents/tree/readback)를 끝냈고 각각 DS-H/code·DIDM-1/DS-4a·KEY-5/a 범위만닫았습니다. 실제OA09/DS-H부모·DS1실provider/DS4d/e실model/법률·전체KEY5·실OS/PC증거는 남습니다. 기존소유자 Pilot/E/Step10/P3/F 완료증거는 보존하고 재실행/누락으로되돌리지 않습니다. 계정사용량은unknown이며42%등과거값이나등록/last_run/완료수로성공·잔량을추정하지않습니다.


---

## 새 UI 구현·검증 진척 및 위험 용어 후속 범위 — 2026-11-21T23:12:39+09:00

- 동일 ROOT execution 2f27d0c2-57cc-46e7-97d6-fc141d4065c9/OS lock20162, primary gpt/ui-guide-chart-first-20261121@b3731cf 유지. UI 소스는 아직 로컬 WIP이며 사용자에게 CMD를 넘기기 전 최신 main dec979a 및 K2d7d9a와 통합·검토합니다. 실제 PC7은 최종UI병합 전, OSgo는 실제바인딩전환 전 조건이며 준비/draft PR을 막는 새 관문은 만들지 않습니다. 감시/예약/자동 인수/run_now 취소 유지입니다.
- **교육27 학습 그림 V3 검증:** 원 계산·가상 입력/engine/공유renderer/outlook/export 변경0. 실제92기하(27×3+11변형)·별도7pure·NaNgap1·PNG2가 통과했고 source36/private16/prefix 전후 일치. RSI 등 bounded축은원0–100/해당bounds, EMA는빠른12·느린26을선에직접표시하고단계1숫자범례를간결화, 값은단계2/tooltip/accessibility에보존했습니다. 기본 학습 그림 하나·원사례차트 접기/한영·전체다크팔레트·원실선점선도확인했습니다. 원형V2 PASS/PNG와초기하네스실패2는별도보존/합산0. 실제컨테이너/undocked Signals/report/DPI·Windows는 아직 후속입니다.
- **초보용어 실제판독:** stock actualdisplay AST16(동적97.5%/unknown에95%기본부여0/원값·tone·출처hint suffix 불변) 및별도 금융정의 반환8을 확인했습니다. guard/공개7/private3/prefix 불변, 실제Qt/전체앱/모형/실API가 아닙니다. 최초stdlib datetime 지연import guard실패는 원문보존하고 stdlib한줄 선행import만으로해결했으며 금융조건/원함수는 바꾸지 않았습니다.
- **툴팁 V3 실제관측:** 원문을자르지않고logical screen폭을기준으로max-width를적용했습니다. 4배율(1/1.25/1.5/2) childexit0·원문64exact·PNG64/불변proof. 정상번들QG32는모두화면안에표시, 실제long KO폭952→476/줄바꿈확인. 미등록font32는별도이며클라우드에fallback face가없는2x ENlong2건은tofu/세로잘림으로남았습니다(전체fit62/64). 이2건/원PNG를숨기거나성공으로대체하지않고 실제Windows/fallback확인조건을보존합니다. 원Linux등록폰트가이미14px/400이었으므로사용자Windows글꼴문제를Linuxbefore에서재현했다고주장하지않습니다.
- **주식정보 Program7:** PBR/BPS·실제투자자매수/매도수량·REST호가/체결강도/panel 구현 및실앱source연결확인. 실제app._ProductionProfileLoader→준비된domestic service.client→stock_profile.load_profile→readonly orderbook/executions각1·retryFalse이며새poll/WS/hoverI/O0. optional은missing/unready/failure격리이며 defaultFalse flag가있는것은아닙니다. 신규실API성공/단위실측/권리승인으로확대하지않습니다.
- 원19검사 첫실행은18PASS/1ERROR/skip0, source425/privatepins 불변/guard0였습니다. 실제Qt언어·테마재렌더에서QLayoutItem.widget가setParent후None이되는제품버그를발견해로컬widget참조를보존하는1곳을수정했습니다. 원V2/첫실패/19assertion은보존하고sourceV3 panel82b28만갱신한공통425V2(36498682, 나머지424불변)로독립판독후재실행중입니다. 성공을미리계상하지않습니다.
- **DIDM 추가 구현 GO(위재실행425 postcheck 뒤에만 source수정):** 사용자VaR/CVaR등을초보자가읽게해달라는지시에따라 기존app.py Quant표시접점과 추가 quantgen_desktop/page_kit.py, risk_page.py, library_view.py, market_tools.py, rates.py의표시/도움말metadata접점만허용합니다. page_kit은기존3값tuple계약과값/tone을보존하면서선택help만추가가능합니다. 기존순수 metric_help를재사용하여MC는실제기간/신뢰·초기spot손실%, hedge는부호있는하위5%평균P&L bp, rates는선택시점PV금액손실, stock은실제var_level의일간log손실로구분합니다. 저장metadata가없으면기준미확인, 고정1일95/최대손실/양수loss관례를전역복제하지않습니다. 숫자·모형·저장원문/연구/원장을바꾸지않고짧은표시와hover로설명하며전체앱/모형실행없이합성결과객체·필요Qt로독립검증합니다. ROE자본0은정의불가라는copy명료화도같은단계에서1곳반영가능합니다.
- Native 실제Guide/Workspace/접기·undocked 기본off·언어·원save_report의memoryZIP입력보존검증은stage2 좁은graph로진행합니다. 수동합성history만주입하고실historical fixture/캐시는열지않습니다. 원legacy context의core.quant.signals.sma/ema2는 exact catalog.indicator_values caller의합성배열계산만관측예외, 새lesson은원core.education.compute_study만씁니다. 실제SignalsPane전체/ResearchWindow/StockDetail전체·MC/GARCH/실history/API/DB/원장·Windows검증으로확대하지않습니다.
- 신규code공개경로는현재Native2+DIDM5+Program7와위추가5가비겹침분담입니다. 각원형/diff/정확SHA/실테스트·실패를보존하고공통425의변경row를새freeze로연결합니다. 테마질문은대기/업종대체0, ROE단위·회계범위/PSR분모·주식기준/실제peer집합은아직부족합니다. sapientia는KEY139코드완료·K2d7d9a부분/신규요청scope반영성공, website9큐 NOT_SENT/실제전달·적용·배포0, 선택GPT/Gemini추가spec공개·심사는NOT_PERFORMED입니다.

---

## KEY-5/a 실제 병합 완료·K2d 검증 — 2026-11-21T22:00:53+09:00

- ROOT execution 2f27d0c2-57cc-46e7-97d6-fc141d4065c9·OS lock20162·동일 task/handoff/cycle 아래 직접 승인 작업을 계속합니다. 자동 감시/예약/자동 인수/run_now는 취소 상태입니다.
- **KEY-5/a 코드 완료:** PR139/head0413cc52a9692710a2febf3aa3a6611fdb59d846를 expected-head 조건으로 merge했고 실제 main은 dec979a7fae65d5f749e12193fad3d0a9ce8ddf3입니다. 부모53e5e723·0413cc52 및 tree8c121c92e7d806aaeba16e8a65cc35bf55b8e60c가 검증된 tree와 동일하며 main ref·PR closed/merged를 read-back했습니다. 동결 제품/시험/문서10+최종 baseline11의 raw/blob 불변, 실제845source/20policy 정합성 PASS(publication BLOCKED65), 독립 최종검토362893e8 PASS. Runtime44897148350 전체6job·Compliance44897148302·Nautilus 임시원장44897148304 및 exact head check-run10 모두 SUCCESS, 리뷰/코드스레드0. 기존 SESSION_PIPELINE 규칙에 따라 별도 Vercel 실패는 무시했고 설정/배포를 바꾸지 않았습니다.
- data.kis_stream 입구 등록·workspace 순수 값 목록·QuoteFeed 공용 모듈과 M1 stale FMP 무효화/M2 KRX 원자 갱신을 코드/합성 범위로 완료합니다. 이것은 실제 자격증명·공급사·소유자 PC·권리/법률·운영 및 전체 KEY5/UI 완료가 아닙니다. baseline source_commit45db는 역사적 working-tree 감사 정보이며 실제0413 head와 동일SHA라고 주장하지 않습니다. 실제 source/blob·tree·CI로 연결했습니다.
- **K2d local WIP:** 실제 b373 부모의 source413에서 제품4+기존 공개5의 정확9파일만 변경, freeze f06a9d0e16aebc888facc58ddad5d74fdf7a2873e4a27d991db1ae60bcdeee92/나머지404·모드·CRLF 불변. 승인6ID/앱8loader·CLI1 AST-only, math/단위/default/문구/CONSTANTS/helper 유지. known e0ba/최종 UI baseline/원격 K2d 코드는 아직 변경0입니다.
- 원 normal after8c 첫 엄격 비교는 **FAIL 유지**입니다. 원 golden d0d009·writer fdc075·비교기/기준/제품을 성공 목적에 맞춰 고치지 않았습니다. 관찰-only exit1 진단과 두 독립 판독에서 유일3차이는 USD3case의 raw supplied kwargs에 label="" 기본값을 명시 전달한 것입니다. 실제 AST서명으로 재결합한 고정17call·응답·10case UI/분석 의미는 별도 pure 보조판독 e61e3f60에서 일치, 메모리 변조7은 모두 거절됐습니다. 이는 strict PASS/전체 source 동치/실제 API 성능이 아니며 새 앱·모델 실행0입니다. 원 postproof 미도달·outer23/inner24의 역사적 mode 사후증거 한계도 보존합니다.
- **공개6 재실행 PASS:** 최초4PASS/1FAIL/1ERROR와 실패2 notice 진단은 보존합니다. 실제 원인은 core.app_identity의 선택적 core._build_info 부재를 private finder가 AssertionError로 바꿔 원 ImportError fallback을 막은 도구 문제였습니다. exact 경로·6후보 metadata 부재에만 정상 ModuleNotFoundError를 유지하는 R2Bf63f66/binding789418·독립1d1668 검토 뒤 정확6을 재실행해 수집/실행/기록6·실패/오류/skip0을 확인했습니다. source413/privatepins/원시험/assertion/fixture 전후 불변, optional 부재1과 실제 import200을 분리, 일반 guard위반0·font시도1은 시작 전 거절/실제process0. 기존 합성 SABR·AI메모리payload·offscreenchart 범위로만 판독하며 누락 Hangul glyph 경고·실제 PC 검수 미실시를 보존합니다.
- 다음은 K2d 거절12 초안 정적검토→ROOT GO→경계13/실제gone6만 known삭제→검증 코드 WIP 보존입니다. K3 원본 factory/lifecycle 준비는 읽기·private초안만이며 제품/실행0입니다. actual G1은 이제 main dec979a의 gateway blob86752로 확인됐지만 K3의 실제 작업 부모는 아직 정하지 않습니다.
- sapientia는 K2c까지 부분 반영 상태이며 KEY-5/a 공식 완료 동기화가 다음입니다. website8큐는 NOT_SENT·실제 전달/적용/배포0. 전체 KEY5/UI·최종 UI의 최신 main 통합/준법/전체CI/PR·owner PC7/OSgo·실제API/공급사/모델/법률·라이선스/동결연구는 남습니다. 선택 GPT/Gemini 추가 spec 공개·심사는 NOT_PERFORMED입니다.

---

# 중앙 K2c 보존·K2d 검증 진척 — 2026-11-21T21:08:53+09:00

- 동일 ROOT execution `2f27d0c2-57cc-46e7-97d6-fc141d4065c9`·OS lock20162 아래 직접 승인 작업을 계속합니다. primary KEY139/0413cc52와 task/handoff/cycle은 유지합니다. 감시/자동 인수/예약/run_now/배포는 취소 상태입니다.
- **K2c 검증 코드 원격 보존:** `gpt/ui-key5-flet-k2c-20261121@b3731cf3a41932afba4f480049fc2e52c35d9eef`, 실제 부모d660296/tree5693004eb101f2754b559486320bd4d680508368. 제품1·known1·기록의 정확3본문/경로/blob/부모/tree·expected d660 ref CAS/read-back 확인. 원본UI822/K1a/b/c/d/K2a7fb/K2bd660은 보존했습니다. 아직 UI PR/main/최종 baseline은 없습니다.
- ID25 Any/type-only import 제거/annotation 세 편집은 승인blob32721b에 명시돼 있습니다. 실제 구현 f6acf2aa/blob04e0cc31, 함수 body raw0b9c0323/AST·args/default·주입 gateway7호출·callback·문구/배치는 동일하고 annotation/import 부작용 차이는 의도된 변경입니다. 독립 정적 검토와 기존 public1 첫실행 PASS(수집/실행/기록1·실패/오류/skip0), 별도 boundary13 첫실행 PASS/Python3.10 문법 PASS. 새 골든·시험/준법 baseline 수정0. 합성 표5종의 소스 선언을 동적 subcase 수로 주장하지 않습니다.
- ROOT known 정확1 삭제 후 blob e0ba25c519612c20378a3b59b684867f08ac9640, scan new/gone/errors0·화면12파일31접점+동결feed1·ceiling22/44/SCREEN_FILES22 유지. source412 raw/blob/mode, 실제부모d660 대비 제품1+known1 외410 불변·최종freeze4e431d4d. old788/source1 bd753 시점 검증/원증거는 별도 보존, known만 바꾼 뒤 public1은 반복하지 않았습니다. 공개1의 engine5모듈은 선언 import만·guard265함수 실제 실행 위반0, 내부 font probe1은 시작 전 거절·실제 subprocess0입니다. 실제 GUI/공급사/API/모델/연구/원장/PC 결과로 확대하지 않습니다.
- sapientia Notion `K2cb373-partial-20261121-2f27d0c2` 부분 반영 성공·부모 취소선0, 비공개 website 큐8개 NOT_SENT·실제 전달/적용/배포0. 실제 UI PR의 PR-번호 기록/대상 대화 수신 및 웹 적용 증거는 남습니다.
- **K2d 별도 병렬 소유권:** `gpt/ui-key5-flet-k2d-20261121`을 실제b3731cf 부모에서 만들고 ref를 다시 읽었습니다. 승인 ID18/21/22·23·24/33의 bonds/fx/quant_lab/fcharts source4, 등록import6·실제 loader9식(앱8/CLI1 AST-only) 범위입니다. 해당 실제 구현 부모는 b373이며 before oracle의 원본7fb 및 역사적 origin630과 분리합니다. 제품 GO는 아직0, private 최소패치·after-only 인터페이스를 검토 중이며 새 source copy/제품/공개test/known/baseline/원격 변경은 아직 없습니다.
- K2d Native R2정적 PASS1c17b1de, frozen writer fdc0758c/binding34db8388. author before10 PASS와 독립 첫QA replay10 PASS: 함수 시그니처 bound 합성loader17·결정적 Bond/FX 분석capture3·순수 predicate4를 합산하지 않습니다. 실제 history/runs/provenance/MC/GARCH/SABR/engine/API/network/DB/backend/원장0, public412/private10pins raw/blob/mode 전후 불변·actual import80 출처 확인. before golden d0d009dc5615f74ae9defc4b4a3315a8e32275b8bce76ca2816c47aa0769d890. 최초 bytecode probe 거절은 계산/골든 전 실패로 원문 보존, 원code/guard 변경 없이 child `-I -B -X pycache_prefix=<각 전용 새 빈 private prefix>`로 source cache를 읽지 않고 재현했습니다. prefix 전후 빈 상태·캐시 쓰기0, 전역환경/HOME 변경0입니다. 실제 CLI/plot/GUI/PC 완료는 아닙니다.
- **FICC 정책 원문 정정:** ROOT의 KRW fixed-local 추정은 철회했습니다. actual local.py blob82c6be84의 load_short_rate 전체는 FRED_ONLY이며 KRW도 FRED monthly IR3TIB01KRM156N을 사용합니다. off/company/invalid면 KRW는 거절→Quant .03, USD load_series(auto)는 SYNTHETIC 대체→.03입니다. before 정상KRW .027/USD .038 및 fallback .03/.03과 구별합니다. 새 KRW 예외/정책을 만들지 않으며 기존 단위·기본days·math/CONSTANTS/helper/진입 시점만 보존합니다.
- **K3 읽기 계획:** actual d660의 native market_chart6/watchlist2/Flet market_chart5=known13, runtime 호출수는 아직0입니다. watchlist만 lambda가 기존 service를 캡처하고 호출 시 service.client 속성을 평가합니다. native/Flet은 기존0인자·factory 주입/None-only 대 false-y fallback 시점을 그대로 보존합니다. provider(data.kis_stream/workspace) class/helper를 원래 조회 위치에서 사용하는 안은 기존 G1등록86752에 맞지만 실제 G1 main 반영은 아직입니다. 원지도는 별도 dd87 정정·8f0 연결로 보존, K3계획1dced384·future code parent None·writer/실행/제품0.
- **KEY139 최신 관찰:** main53e5e723·head0413cc52 유지. Runtime44897148350에서 문법2/Linux3.12/Windows3.11 SUCCESS, Windows3.12·3.14 owner14 UI 단계 진행 중·관찰된 실패0. Compliance44897148302·Nautilus 임시원장44897148304 SUCCESS. source845/docs20 정합성 PASS(publication BLOCKED65) 및 별도 local83/123/17·독립8/main4 유지. 전체3workflow/필수checks·리뷰·main·freeze·ROOT 소유권을 확인할 때만 expected-head merge/KEY-5/a 코드 완료를 기록합니다. DIDM138/main53e의 DIDM-1·DS-4a 코드/합성 하위만 완료는 유지합니다.
- 전체UI/KEY5·최신의존성 통합·최종 source-review/전체UI CI/PR·owner PC7/OSgo·실제 API/공급사/모델성과/법률·라이선스/운영 증거는 남았습니다. 다음은 K2d private 최소패치와 after-interface 독립 검토 후 source4만 GO, K3는 실제G1 main 후, KEY139 전체CI 확인입니다. 미실시/선택사항 GPT/Gemini spec 추가 공개·검토는 NOT_PERFORMED로 유지합니다.

---

# 중앙 K2b 보존·K2c 진행 범위 — 2026-11-21T20:44:38+09:00

- ROOT execution `2f27d0c2-57cc-46e7-97d6-fc141d4065c9`가 OS 잠금20162 아래 계속 수행 중입니다. primary는 KEY139/0413cc52이며 task/handoff/cycle 및 이전 기록은 유지합니다. 자동 감시·중복 예약·run_now·배포는 재개하지 않았습니다.
- **K2b 원격 보존:** `gpt/ui-key5-flet-k2b-20261121@d66029642efa4bcd7e92b897139b9d947ad01fec`, 실제 부모K2a7fb6b032/tree629f209d25947504bdd26bc8c8cb85bcbada6a19. 제품1·known1·기록의 원격3본문/경로/blob/부모/tree 및 expected7fb ref CAS/read-back 확인. 원본UI822/K1a/K1b/K1c/K1d/K2a는 보존됐으며 새 UI PR/main 병합은 없습니다.
- 승인 ID20의 import·readiness 조회 두 줄만 기존 gateway.keys_ready(kis_quote)로 옮겼습니다. before14·after14 작성자/독립 MATCH, gateway14/config bool13+합성오류1/fake GET20, actualimports73 동일집합(target1 raw만 변경). 기존 공개1 PASS(수집/실행/기록 각1·실패/오류/skip0), 최종 경계13 PASS는 서로 합산하지 않습니다. builder14의 worker0과 공개1의 fake snapshot/동기 worker 경로를 구별합니다. 실제 GUI/공급사/API/모델/연구/원장/PC 검증은 추가하지 않았습니다. 폰트 탐색시도1은 시작 전 거절·실제 subprocess0입니다.
- ROOT가 actualgone1만 known에서 삭제했습니다: blob788a461d2b67fec0f124b8360bbce520aaf527fc. full412 raw/blob/mode 확인, a9aa source1 시점 대비 known1만·실제 부모7fb 대비 제품1+known1/나머지410 불변. 최종 scan new/gone/errors0, 화면13파일32접점+동결feed1·ceiling22/44·SCREEN_FILES22 유지. old6792 snapshot/a9aa·561e/원R2·oracle527d는 새 finalfreeze5b4ebbac와 분리해 보존했습니다. 공개시험·준법 baseline 수정0.
- sapientia Notion `K2bd660-partial-20261121-2f27d0c2` 부분 진척 반영 성공·부모 취소선0. 웹사이트 큐7개는 NOT_SENT, 실제 전달/적용/배포0입니다. 실제 UI PR의 PR-번호 기록·수신/적용 증거는 남습니다.
- **K2c 병렬 소유권/다음 범위:** `gpt/ui-key5-flet-k2c-20261121`을 실제 d660296 부모에서 생성하고 ref를 재조회했습니다. d660의 ui/krx_page.py 원blob314b787b8eb934c90ba01853f832c966832f3756도 확인했습니다. 승인 원blob32721b의 ID25가 명시한 타입 Any 전환(typing import·직접 KRXGateway import 제거·annotation 세 편집)만 허용합니다. 실제 source1 구현 전이며 독립 정적 검토 PASS, 전체 함수 body raw/AST·args/default·주입 gateway7호출·문구/배치 보존 증거가 있습니다. 이 checkpoint CAS+execution/read-back과 STATE 저장 뒤 별도 verified source412 copy에서 해당 최소 patch와 기존 public KRX1만 진행합니다. 새로운 before 골든/시험은 만들지 않습니다.
- K2d ID18/21/22·23·24/33은 공개 source4파일의 앱 loader8식+CLI1 AST-only, 계획 before10입니다. private초안 b425d758은 Native331f9a72 정적검토에서 CHANGES_REQUIRED로 SQLite/fork/DNS·실제history/runs/provenance 차단·안전한 새 출력·동일 source/proof 사후검증 보강 중입니다. 역사적 freeze.base630과 실제 원격7fb의 연결을 별도 receipt로 표시하며 원manifest를 고치지 않습니다. 실제 before/골든/제품/공개test/known/원격 실행은0입니다.
- **KEY139 현황:** actualhead0413cc52·main53e5e723 기준 source845/docs20 정합성 PASS(publication BLOCKED65), local83/123/17·독립8/main4 별도 PASS. Runtime44897148350 진행 중(문법2 PASS, 설치4 진행·관찰된 실패0), Compliance44897148302 및 Nautilus 임시원장44897148304 SUCCESS. 전체3workflow/필수checks·리뷰·main·freeze·ROOT 소유권을 확인하기 전 merge/KEY-5/a 완료를 기록하지 않습니다. DIDM138/main53e5e723의 공식 DIDM-1·DS-4a 코드·합성 하위 완료는 유지하며 실제 API/모델 성과/법률·라이선스·운영 부모는 미완료입니다.
- 전체 UI/KEY5, 실제 최신 의존성 통합·최종 source-review/전체CI/UI PR·owner PC7/OS go 및 공급사/법률/라이선스/실행 승인 조건은 남습니다. 다음은 K2c 검증 코드 보존, K2d guard 정적 재검토 후 원본 before만 GO, 그리고 KEY139 전체CI 확인입니다. 더 긴 단계는 실제 증거에 맞춰 계속 기록합니다.

---

# 중앙 K2a 원격 보존 및 다음 검증 — 2026-11-21T20:13:03+09:00

- ROOT execution `2f27d0c2-57cc-46e7-97d6-fc141d4065c9`의 기존 OS 잠금 아래 직접 승인 작업을 계속합니다. 자동 감시·예약·run_now는 취소 상태이며 재개하지 않았습니다.
- **K2a 원격 보존 완료:** `gpt/ui-key5-flet-k2a-20261121@7fb6b032e2ab24c681700120ab0abd5b6dd5c6e3`, 부모630e9ba/tree bebe159532c5425c12186314eaaab369441b70d3. 제품2·공개시험5·known·기록의 정확9본문/경로/blob/부모/tree와 expected630 ref CAS·read-back 확인. 원본UI822/K1a/K1b/K1c/K1d 브랜치는 보존했습니다.
- K2a ID34·35·44 기존 FICC 조회 입구만 전환했습니다. 공개 회귀15 PASS, 독립 의미16 MATCH, 별도 차단12 PASS, 최종 경계13 PASS는 서로 합산하지 않습니다. 합성 leaf15/분석10·실제 앱4조회/CLI1정적검토 구별, 실제 누적 import94=기존93+고정원본 app_identity1 출처 대조. 제품 CRLF/계산·인자·한국어/배치·기존 assertion/골든 유지. 최초 실패/guard 보완 기록도 보존했습니다.
- known 소멸3만 삭제, 잔여14화면파일33접점+동결 core feed1, 상한22/44·SCREEN_FILES22 불변. 이 결과는 실제 GUI 렌더링/소유자 PC/OS go/실제 공급사/모델/연구/원장 검증을 뜻하지 않습니다. UI/KEY5 부모 완료와 UI PR/main 병합·최종source-review는 아직입니다.
- **KEY5a PR139:** 실제head0413cc52a9692710a2febf3aa3a6611fdb59d846·실제main53e5e723 유지. 최종845소스/20문서 정합성 PASS(publication BLOCKED65), 83/123/17 및 독립8/main4 별도 PASS. Runtime44897148350 진행 중(문법2 PASS·설치4 진행, 실패관찰0), Compliance44897148302·Nautilus 임시원장44897148304 SUCCESS. 3workflow 전체·필수checks/리뷰/메인/freeze/소유권 재확인 후에만 병합합니다. CODE 완료 ID는 아직 추가하지 않습니다.
- DIDM138 전체CI/실제main53e5e723 병합과 공식 DIDM-1·DS-4a 코드/합성 하위만 완료는 유지합니다. 실제API/모델성과/라이선스·법률·운영 부모는 미완료입니다.
- sapientia Remaining Work K2a 부분 진척 반영 성공(`K2a7fb-partial-20261121-2f27d0c2`), 부모 취소선 추가0. 웹사이트 비공개 큐6개는 **NOT_SENT**, 실제전달/반영/배포0. 지원되는 대상 대화 발송 도구가 없어 실제 UI PR의 PR-번호 기록·수신증거가 남습니다. KEY139는 화면/문구 변경 없이 backend gateway 수정이므로 UI 개선 PR로 임의 확대하지 않습니다.
- 다음 안전 시작점: KEY139 전체 CI 확인과 K2b ID20 파생상품 단일 readiness 입구 검증. R2 writer fa212401 및 original manifest9f300은 Native 정적 독립검토 PASS이고 author before14를 승인했으나 실제 실행 결과는 아직 대기입니다. 독립QA GO/제품 변경 전 원본630·402입력·schema7·guard·불변 oracle을 확인합니다.

---

> **2026-11-21T18:14:17+09:00 진행:** DIDM138/6cff 실제45본문/blob·부모/tree/ref대조,844소스/20정책·47export/35문법/독립PASS·문서CI성공·전체Runtime진행. K1c b93 원격보존/기존15+별도factory15(합산X)·18화면39접점. 다음KEY45는미병합6cff와별도local준비만, actual4gmain전원격/PR/finalbaseline없음. 부모/실PC/법률·권리/실API/배포완료로세지않는다.

## 중앙 최신 완료·현재 차례 — 2026-11-21T19:48:44+09:00

- [x] 공식DIDM-1·DS-4a 코드/합성검사: PR138/head6cff→실제main53e5e723, all6Runtime/Compliance/8checks·독립검토·testedtree023/ref대조, 실제844source/20docs PASS/publicationBLOCKED65. LEDGER2행추가. 실API/실모델/권리·법률/운영/DS1OA10/DS4d/e전체완료가아니다.
- [ ] 현재4hKEY45 최종actualmain23/845sources·20정책baseline/check→CAScode/PR/fullCI/merge. 앞4g가실제완료되어준비후보트리동일성검증함.
- [x] K2a local2제품/5시험mock11·기존15PASS/정확7변경·기존405불변확인. 코드WIP부분이며부모완료아님.
- [ ] K2a independentafter94/blocked12·rootknown3정리/경계13·원격보존. 전체UI/KEY5/PC7/OSgo·웹5미수신/미반영미완료.
- [ ] sapientia Notion DIDM138실제병합/공식완료2ID 최소동기화(현재pending). K1d630부분반영은이미성공.
- K2bID20 before준비만, 자동감시/배포없음. [누적인계](WEEKLY_HANDOFF_2026-11-21_2f27d0c2.md).


## 중앙 검증 진척 — 2026-11-21T19:10:18+09:00

- [x] K1d 승인3조회 전환 코드WIP: gpt/ui-key5-native-k1d-20261121@630e9ba, 독립13·기존18/경계13·원격4본문/ref대조, actualscreen16files36sites, Notion부분동기화성공. 전체KEY5/부모완료행아님.
- [x] KEY5a local45+candidate6cff 준비: synthetic83/123/17·독립8/AST4·20정책소스영향, 실제845소스/구조·링크0. 첫실패이력과미커밋원본보존.
- [ ] DIDM138 exact6cff 전체Runtime Windows3환경 결과/최종리뷰·실제main통합; actualmain6d 유지.
- [ ] 위4g실제병합후 KEY5a최신main/최종baseline·check·4hPR/전체CI/merge.
- [ ] K2 before16의afteradapter 독립마감후기존승인범위로제품배정; UI최종선행·전체준법/CI·실PC7/OSgo·웹5큐수신/적용.
- 실제 OA09/OA10/권리/법률/모형성과·운영관문은그대로미완료. [전체근거](WEEKLY_HANDOFF_2026-11-21_2f27d0c2.md). 자동감시/예약취소유지.


> **2026-11-21T17:35:29+09:00: DS-H/code PR137→main6d25a33 완료.** 전체6Runtime/Compliance·독립검토PASS, 검사tree/parents/ref정확일치. 실제OA09진단/홈실연결·DS-H부모는미완료. 다음4gDIDMabd 최신main통합·20정책검토/최종baseline·합성/독립/전체CI 차례, 새PR없음. 원문글사본38값과파생171칸의증거범위를구분하며이번실제XLSX재검사미실시. [현재실행](WEEKLY_HANDOFF_2026-11-21_2f27d0c2.md).

> **2026-11-21T14:54:13+09:00 부분 인계:** OS136 main72a 완료, DS-H draft137/497의 문서CI·독립PASS/전체Runtime진행. K1b053(승인ID13) 기존17PASS·9UI기록MATCH·원격3본문확인, 남은19화면41접점·전체KEY5/실PC/OSgo미완료. DIDM08/20 기술정정안은비공개R2만검토/보존, 최신main합류뒤적용. 새완료ID는OS-F2뿐이며 OA09 실제진단/법률·권리/출시를완료로대체하지않는다. [다음안전시작/전체인계](WEEKLY_HANDOFF_2026-11-21_1bfaa7d8.md).

> **2026-11-21T14:36:47+09:00: DS-H 초안 PR137/head4973111 게시.** main72a 반영·정확5파일/parents/tree/ref 대조, 합성172 및 준법47 PASS(중복),20정책·809소스 정합성PASS/publicationBLOCKED. 독립 최종 검토 PASS·전체 CI 진행 중, OA09 실제 진단 미제출·조건 차이 보존. 새 완료ID·DS-H 부모 취소선 없음. 다음4gDIDMabd→4hKEY45db 순서, UI822/K1ad2 및 실제 PC/OSgo 유지.

> **2026-11-21T14:21:16.000+09:00: OS-F2 코드 scope 완료·LEDGER 추가.** PR136→main72a055f, 6Runtime/Compliance성공·검사tree동일readback. 다음4fDSH실트리/최종baseline·draftPR준비, OA09진단미제공/원문조건충돌은그대로. UI/KEY5/실PC·사업/출시전체완료아님.

> **2026-11-21T14:11:37.000+09:00 중앙 관측:** OS136은Windows3.12한환경만최종진행중(나머지5 Runtime+Compliance성공); mainf065/freezeOFF·유일대기PR136유지. UI822+K1a d2f675db 원격보존/검증. DSH actual809source·4delta·구조0/stale20, baseline·PR·main/실OA09미완료. [전체인계](WEEKLY_HANDOFF_2026-11-21_1bfaa7d8.md).

> **2026-11-21T13:24:33.000+09:00 후속:** UI후보 head822aff9 / 제품c36f22cd 원격보존·본문대조, system새4직접참조제거(기존22/44상한유지), 확대64회귀진행중. R3이미병합된2하위의Notion상태를실제CI/LEDGER로정정; 새완료ID는없다. OS136전체CI계속대기, [현재진행표](CENTRAL_CODEX_STATUS_2026-11-21.md).

# QUANTGEN WORKBOARD — 전체 업무 구조도와 체크리스트

## 최신 중앙 Codex 배정 — 2026-11-21T12:10:34+09:00

소유자 단일요청창구·5담당계획 승인후메인Codex가총괄한다. [실제담당·진행·검증근거표](CENTRAL_CODEX_STATUS_2026-11-21.md)를 우선한다. DIDM/UI기존세션은handoff/새구현중지확인완료. 데이터는최신GPT DSH7ce37917/DIDM87812679를이어받는다. 구현·회귀는병렬, 병합은OS-F2→DS-H→DS/DIDM→KEY5a순차. 아래과거시각의중단·대기·배정문구는이력이며자동완료로바꾸지않는다. 현재새완료ID/병합은없다.

> **2026-11-21T13:06:45+09:00 문서 대조 보정:** 현재 원격 보존 head는 OS-F2 `64ff58e`(PR136), DS-H `7ce3791`, DS·DIDM `abd10c6`, KEY-5/a `45db2be`다. 위 `87812679`는 DIDM 수정 전 이력이다. CURRENT 13:04:53과 MERGE_QUEUE 12:33:42 기준으로 main `f065ec92` 유지, OS-F2 전체 CI 진행 중이며 새 병합·완료 ID는 없다. 아래 11-20 기준 자료의 대기/분담은 당시 이력으로 읽는다.


상시 지침: `SESSION_PIPELINE.md` (메인·하부 세션 연결 규칙). 이 문서는 메인이 작업 하나가 끝날 때마다 고친다.

기준 시각: 2026-11-20 05:40 KST (2.1·2.2·세션 지도 갱신) / 첫판 2026-11-20 00:45 KST (첫판: 메인 세션 조사 workflow wf_0be17a88-d74 + 완결성 검토, 그 뒤 메인이 KEY-4·OA-01 갱신)
git 기준: main 9f76b07 · PR #133 head 148504a · UI 브랜치 490562d · OS 브랜치 8262d6c · DS 브랜치 df05b21
자료: REMAINING_WORK_2026-11-17.md(공식 ID 출처, 10-27판의 열린 ID도 그대로 유효), REMAINING_WORK_2026-10-27.md, LEDGER.md(KEY-3까지 280줄), CURRENT.md, MERGE_QUEUE.md, 하부 세션 CURRENT 문서 5개, 하부 세션 대화 기록, Notion "REMAINING WORK"(11-19 15:10), GitHub REST. 참고만: REMAINING_WORK_2026-10-29.md(GPT PR #12 브랜치에만, main 미병합)
원칙: 자료끼리 다르면 git(원장·병합 대기열·PR 상태)을 따른다. 다른 점은 별도 "충돌" 목록에 있다.

---

## 0) 읽는 법

| 기호 | 뜻 |
|---|---|
| [x] | 완료 (원장 행 또는 main 병합 커밋 있음. 웹사이트는 다른 저장소라 handoff 기록 커밋으로 대신) |
| [~] | 진행 중, 또는 끝났다는 근거(원장 행·병합 커밋)가 아직 없음 |
| [ ] | 대기 (앞 작업이나 차례를 기다림) |
| [!] | 막힘. 소유자 손이 필요함 |
| [-] | 보류 또는 쓰지 않음 |

**세션 지도**

> **2026-11-21T13:06:45+09:00 담당 보정:** 아래 표는 11-20 Claude 중단 시점 이력이다. 최신 담당은 메인 Codex 총괄과 승인된 하위 담당이며, DATA/UI 별도 채팅은 handoff·새 구현 중단 상태다. UI 원본 `414eceb`는 보존하고 중앙의 격리 gpt 후보에서 통합을 검증한다. PAY-0/PAY-2는 준비 문서와 OA-32/OA-39 대기 상태를 유지한다. 이 주석은 소유자 PC 확인·OS go·사업/법률 결정이나 웹사이트 실제 반영을 대체하지 않는다.

| 세션 | 종류 | 연락 방법 | 지금 |
|---|---|---|---|
| MAIN | 메인(조정·병합) | — | 11-20 05:50 KST: **주간 98% → GPT 인계**(CURRENT.md). PR #134 병합(f065ec9), 4e OS-F2 OS가 e44c48e까지, KEY-5/a 검토 결과 plans/2026-11-20/KEY5A_REVIEW.md |
| PAYMENTS_ACCOUNT_KEYS | 하부 (D6) | 메인이 직접 | KEY-4/a 병합(f065ec9), KEY-5/a dc936d4 메인 검토 대기(push 보류), PAY-2 재검증 0a24f02 끝 → OA-39 대기 |
| OS_EXPANSION | 하부 (D6) | 메인이 직접 | 18:42부터 쉼 (문서상 waiting_on owner, 실제로는 UI가 490562d로 패치를 이미 반영함 → 메인이 알려야 함) |
| DATA_SOURCE_DIDM | 하부 (D6) | 메인이 직접 | 15:00부터 쉼, 소유자 PC 실행을 기다림. KEY-3 병합 소식 아직 못 받음 |
| UI/UX | 별도 세션 | 소유자를 거쳐서만 (MERGE_QUEUE 규칙) | 소유자 실행 확인을 기다림 |
| WEBSITE/AWS | 별도 세션 | 소유자를 거쳐서만 (MERGE_QUEUE 규칙) | 11-13 이후 멈춤 |

**규칙 요약**
- PR은 한 번에 하나만 병합을 기다린다. 병합 버튼은 메인이 누른다. 하부 세션은 자기 행이 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 연다.
- 공유 파일(source-review.json, FACTS.md, config.py, workflows)은 PR 하나씩만 바꾼다. 앞 PR이 병합되면 최신 main을 합치고 기준선을 다시 만든다.
- UI/UX·웹사이트 세션의 브랜치와 인계 파일은 아무도 고치지 않는다. 다른 세션이 그 브랜치를 시험할 때는 읽기·시험만 하고 push하지 않는다. 그 세션에 줄 요청은 소유자를 거친다.
  - **2026-11-21 우선 정정:** UI에 대해서는 소유자의 메인 Codex 단일 창구 지정과 UI 인계가 위 과거 요청 경유 절차보다 우선한다. 중앙에서 기존 승인 범위의 UI 통합·검증과 하위 담당 배정을 진행하며 원본 Claude/UI 브랜치는 보존한다. 실제 PC 확인·OS go·새 UI/사업 결정 조건은 남는다. WEBSITE/AWS에 대한 인수·배포 승인이 추가로 확인된 것은 아니므로 웹사이트 전달/실제 반영은 기존 조건을 유지한다.
- 원장에 있는 ID는 끝난 것이다. 다시 하지 않는다. 추가 작업은 `/2`, 부분 작업은 `/a`를 붙인다.
- 하부 세션은 LEDGER를 직접 쓰지 않고 `--done` 문자열을 자기 인계 파일에 적어 메인에 알린다 (REMAINING_WORK_2026-11-17 0절).
- 하나가 끝나면: 작업 브랜치 push → 메인이 ledger `--done` → CURRENT next_ids에서 빼고 done_ids로 → 이 문서에 [x] → MERGE_QUEUE 줄 긋기 → Notion.
- 주간 사용량 98%면 handoff (CLAUDE.md). 다음 리셋 2026-11-24 17:00 KST.
- 11-13 소유자 방침(자동 감시·자동 인수 취소)과 11-19 요청이 다르다: 메인→하부 3세션의 자동 배정은 11-19 요청을 따르고, UI·웹사이트는 계속 소유자 경유.
- 소유자가 24시간 안에 손으로 할 일이 5개 이상이면 Claude 앱 푸시 알림을 보낸다. **지금 10개라서 알림 대상이다** (3절).

---

## 1) 지금 진행 중

**11-20 00:50 KST 메인 배정:** OS — UI 브랜치에서 종료 고침 재확인(읽기·시험만) + OS-F2 브랜치 시작 / DATA — main 9f76b07 합치기·시험·인계 문서 갱신(PR 직전 상태로 준비) / PAYMENTS — KEY-4 push 보류, PAY-0 초안 병행

형식: ID — 무엇 — 담당 세션 — 다음 행동 — 근거

- [x] **KEY-4** — PR #133 → main `8445187` (11-20 03:27 KST), 원장 KEY-4 (handoff 4aa4d10). 후속: 4d 메인 문서 PR, 4d' KEY-4/a, 4e OS-F2, 4f KEY-5/a
- [~] **소유자 AWS 운영 풀** — Golden Hour Code 계정의 시드니 사용자 풀 — PAYMENTS가 안내, 소유자가 실행 — MFA 결정(1/2/3) → 15단계 계정 복구 → 16·17단계 앱 클라이언트 quantgen-web, Client ID → T1 시험 — 세션 기록 22:04–23:52 KST. 13·14단계 끝
- [~] **PySide6 간헐 종료 고침** (OS-F1 선행, ID 없음) — 시험 도우미가 QThread.currentThread() 객체를 붙잡고 있던 문제를 threading.get_ident()로 바꿈 — OS(재확인), UI(반영 끝) — 메인이 OS에 "UI가 490562d로 반영함"을 전달 → OS가 UI 브랜치를 읽기·시험만(push 금지)으로 다시 시험 → PYSIDE6_TRIAL 9절 판정 복구 → OS 브랜치 8262d6c(5파일: lint 15, 점검표 15, TRIAL 10-1, 패치)의 main 자리를 메인이 정함(OS-F1 PR에 묶거나 작은 PR) — OS 8262d6c, UI 브랜치 head 490562d(23:24 KST)
- [!] **UI 7쪽 + PySide6 준비 병합** (MERGE_QUEUE 5) — claude/friendly-bardeen-r6xe8f — UI(소유자 경유) — 소유자가 PC 2대(skymi, whydi)에서 실행 확인 → UI 세션에 "PR 만들어" → 메인이 '병합: UI' — MERGE_QUEUE 5행. OS-F1과 KEY-5가 이것을 기다림
- [!] **DS·DIDM 브랜치** (DS-1, DIDM-0, DIDM-1, DS-4a, DS-4b, DS-4d, DS-4e) — 코드 끝, **main 9f76b07 합침 완료(f60e314) → head eb4f3a5, PR 직전 상태** (DIDM 시험 98 OK, 게이트웨이·자격증명 208 OK = main과 같음, core/ 밖 변경 0줄; 메인 확인 11-20 00:25) — DATA_SOURCE_DIDM — 남은 것: 소유자 PC 결과(OA-07, OA-08) 반영 → 8행 차례에 최신 main 합치기·기준선·PR — DATA 보고 11-20 00:23
  - **2026-11-21T13:06:45+09:00 현재 상태:** 위 `eb4f3a5`와 OA-07/OA-08 대기는 과거 이력이다. 공식·무료 공급원 6곳은 소유자 PC 확인이 끝났고, 무료 뉴스 3곳은 이용 불가 확인에 따라 DS-4b 보류 상태다. 이어받을 코드는 **4f DS-H `gpt/ds-home-indicators-20261121@7ce3791` → 4g DS·DIDM `gpt/data-source-didm-20261121@abd10c6`**다. 합성 검증·원격 보존까지 확인했으며 최신 main 통합·준법 기준선·필수 CI·PR·병합은 남았다. OA-09/10/38/46의 실제 사용자 입력은 유지한다.
- [!] **웹사이트 정책 문구 다시 만들기** — PR-130.json 반영 — WEBSITE(소유자 경유) — 소유자가 받은 프롬프트를 웹사이트 세션에 붙이기 — CURRENT "웹사이트 세션 전달은 소유자 경유"
- [x] **OS-F2 코드 구현·자동 검증·main 병합** — **11-21 PR136/main72a055f 완료**(원격tree/전체CI대조, 실제owner자료이전은미검증). 이전정의/진행기록: — config.py·data/krx/kis_client.py·data/krx/opendart_client.py의 ~/.nextgen 경로 전환 — OS(브랜치), MAIN(자리) — 관문 KEY-2(3249af7) 풀림. KEY-4와 파일 겹침 없음(KEY-4는 config.py·data/krx를 바꾸지 않음) → OS 브랜치 작업은 지금 시작 가능. 메인은 MERGE_QUEUE에 행 추가, owner_confirmed 다시 쓰기는 그 뒤로 — MERGE_QUEUE에 행 없음
  - **2026-11-21T13:06:45+09:00 현재 상태:** 위 'MERGE_QUEUE에 행 없음'은 이전 관측이다. 실제 차례는 **4e OS-F2**, `gpt/os-f2-data-dir-20261121@64ff58e` / [PR136](https://github.com/xkg4real/quantgen/pull/136)이다. 첫 Windows fixture 실패를 수정한 새 Compliance44861453813은 성공했고 Runtime44861453849 전체는 CURRENT 관측 시 진행 중이다. 아직 병합·OS-F2 완료는 아니다.

---

## 2) 트랙별 체크리스트

### 2.1 MAIN (조정·병합·결정 기록)

**관문**
- [x] F 동결 — 2026-11-19 01:32 해제, main 6e077dc (소유자 F22 완료 보고)
- [x] D7-G — 소유자 승인 2026-11-18 14:15 ("D7-G의 방식대로"), ⑦-1/rulings/2 002a658
- [~] 병합 차례 — PR 하나씩, 메인이 병합. 4d' KEY-4/a 병합(f065ec9). **지금 4e OS-F2 (병합: OS, 05:40)** → 4f DS-H → 4g DS·DIDM → 4h KEY-5/a
- [~] F21 뒤 목록 — GH-1, KEY-2, KEY-3 끝. KEY-4, OS-F1, KEY-5, DS·DIDM 남음
- [!] G1 법인 설립 — 소유자. D-U-N-S, Apple 조직, Windows OV, PAY-4의 관문
- [!] G2 유사투자자문업 — 소유자(변호사와)
- [!] G3 PG 심사 — G1 뒤
- [!] L 변호사 의견서 — 규제, Polymarket·Kalshi, LGPL, 웹 거래
- [!] 표시권 — 공급처별 표시·재배포 권리

**F21 뒤 병합 (1–4b 끝)**
- [x] ⑦-2/a — PR #126, 56fe32a
- [x] OS 작은 PR (OS-P0-a~f) — PR #127, c28b1d7
- [x] KEY-2 — PR #128, 3249af7 / KEY-2/b — PR #129, ca5da08
- [x] 정책 PR-1 (원장 PAY-A2/a) — PR #130, edbe9f7
- [x] GH-1 — PR #131, ab24dec. 공개 유지, runtime-smoke 겹친 실행 취소
  - 빠진 범위: Compliance 결과물 보관 30→7일(compliance-review.yml 73·92행 아직 30), export.py 링크 안내. 필요하면 GH-1/2로 새로 잡기
- [x] KEY-3/design, KEY-3 — PR #132, 9f76b07
- [x] KEY-4 — PR #133 → main 8445187, 원장 KEY-4 (handoff 4aa4d10)
- [ ] GH-2 — test_npu.py, mindmap/, .claude/launch.json 'godseye-dev'(12행) 삭제. archive-2026-11 태그(아직 없음) 뒤 _backup/ 삭제. 비밀 검사 CI를 넣을지는 소유자 결정. 로드맵은 "GH-1과 한 PR"이었으나 GH-1은 따로 닫힘
- [ ] 정책 문서 PR-2 — 계정 서비스 설명(시드니 저장, 탈퇴, 보안 기록, 처리 위탁). AWS 풀과 웹 계정 화면이 생긴 뒤
- [ ] 2.7 웹 거래 결정 메모 (D12-A) → M-12 — ⑦-2 뒤 관문 풀림. 변호사·KIS 문의는 소유자
- [ ] 2.7 push_handoff.py --doc — 하부 세션 문서 게시용 (main 9f76b07에 아직 없음)

**결정 기록**
- [x] 2.7 결정 기록 PR — ⑦-1/rulings(7c33955), ⑦-1/rulings/2(002a658). 11-19분은 56fe32a, edbe9f7, ab24dec에 포함
- [x] 2.7 P3·F 뒤 main PR — ⑦-2, ⑦-2/a
- [~] 2.7 회원가입 정책 문서 PR — PR-1 끝, PR-2 남음
- [x] 기록 — PR #135 → main fa78df1: 세션 연결 지시, 계정 결정 3건, OA-42·OA-44, 메인 결정 2건 (원장 SESSION-PIPELINE). 남은 기록: D9 답, OA-38, OA-46

**메인 문서 손볼 것**
- [x] MERGE_QUEUE — 4c head·상태, 7행 KEY-5만, 윗표 줄 긋기, "비공개 뒤 CI 유료" 규칙 정정, 4d·OS-F2·OS 종료 원인 기록·정책 PR-2 행 — 11-20 메인 (WORKBOARD 첫판과 같은 handoff 커밋)
- [ ] CURRENT.md — next_ids에 진행 중 ID 넣기(KEY-4, KEY-5, OS-F1, OS-F2, GH-2, PAY-0, PAY-2, DS-1 등, 원장 ID는 빼고). 낡은 "PR121 상태" 줄 정리
- [ ] "역방향 의존 없음" 정정 확인 — MASTER_WORK_DESIGN에는 그 문장이 없음(검색 0건). Notion 플랫폼 계획 7.2 M2 문장은 OS가 11-18 개정 2판에서 고쳤다고 기록(OS_SESSION_CURRENT) → 메인이 확인하고 닫기
- [ ] D14_RAVENPACK_ALTERNATIVES.md 1절 "3단계" 고치기 (= 대안 9개. DIDM 3단계 아님) — 4d 메인 문서 PR에 넣음. DS-3 관문은 확인 끝(2.4절)
- [ ] OS-F3 판단 — KEY-2(3249af7)로 끝난 것으로 적을지, macOS·모바일 키체인 범위를 새로 잡을지
- [ ] OS-P0-d Notion 기록 맞추기 (원장은 "소유자 몫", OS는 "이미 반영")
- [ ] Notion REMAINING WORK 갱신 (충돌 목록 참고)
- [ ] 변호사 질문 묶음 — L, G2, ⑩-1/b, Polymarket·Kalshi, LGPL 5문항, D12, 15-12, 투자 자문 경계
- [ ] 오래 열린 GPT PR #12 (gpt/handoff-continuation-20261029) 처리 여부를 소유자에게 묻기. 이 브랜치의 REMAINING_WORK_2026-10-29가 ⑫-4, ⑬-3~⑬-7, ⑭-1~⑭-3을 정의하므로 공식 ID 출처로 쓸지도 함께 정함
- [ ] 원장에 없는 상위 ID 정리 — ④-2, ④-3, ⑤-2, ⑨-1, ⑨-4, ⑨-3a/recorder/1: 닫을지(원장 행) 남은 범위를 적을지

**상품·이월 (MAIN 담당)**
- [~] ⑩-1 규제·외부 공개 검토 — ⑩-1/a 끝 / [!] ⑩-1/b 전문가 의견
- [~] ⑩-2 동반 앱 MVP — ⑩-2/a 끝 / [ ] ⑩-2/b (Notion의 ⑩-2/b-private-offline-mvp는 근거 커밋 7e9e112가 어느 원격에도 없음)
- [x] 10-3 상업 README·현황 문서 — 51bac97 (main에 있음, 원장 행 없음)
- [~] ⑩-4 비교·상업화 보고서 — Notion은 지웠지만 본문은 "최종본 미완료". ⑩-4/a 초안은 Notion에서만 완료 (원장 행·커밋 없음)
- [~] ⑪-1 TRADEGEN 연계 요약 — ⑪-1/a 끝, 소유자 승인 남음
- [~] 11-2, 11-3 TRADEGEN PR #14, #15, #16 (다른 저장소)
- [~] M-12 주문 안전 설계 — M-12/design-draft/1 끝(eba94f0). D8, D10, 계좌 평가 정의 남음
- [ ] 14-1 ⑫–⑭ 후속 범위 확인
- [ ] ⑭-1 시나리오 스토리보드, ⑭-2 교육 템플릿(공개는 ⑩-1 뒤), ⑭-3 선택형 제품 분석 — 10-29판 ID(PR #12에만). 14-1에서 범위 확인
- [!] 12-7 감사 12절 상품 우선순위 승인 (소유자)

### 2.2 PAYMENTS (PAYMENTS_ACCOUNT_KEYS)

- [x] KEY-1 — docs/commercial/ENV_NAMES.md — 3249af7 (PR #128)
- [x] PAY-A1 — ADMIN_GUIDE.md — 3249af7. v0.2는 부록 C 결과 뒤
- [x] PAY-A2 — ACCOUNT_SETUP.md, OWNER_STEPS.md — 3249af7 (OWNER_STEPS는 PR #133에서 v1.3.2, 로컬 6a489aa에서 v1.4)
- [x] PAY-A2/a — 정책 PR-1 — edbe9f7 (PR #130)
- [x] KEY-2 — core/credentials (환경변수 → OS 키 보관함 → 개발 빌드만 .env) — 3249af7. code_sha256 ec72fab3→10c27010
- [x] KEY-2/b — KEY-2 검토 후속 — ca5da08 (PR #129)
- [x] KEY-3/design — GATEWAY_DESIGN.md v0.2 — 9f76b07
- [x] KEY-3 — core/gateway + 경계 시험 — 9f76b07 (PR #132)
- [x] KEY-4 — PR #133 → main 8445187, 원장 KEY-4
- [x] KEY-4/a — 계정 문서 고침(F1–F9) + OA-42·OA-44 반영 + 자체 시험 1줄 — PR #134 @ aa4be94 → **main f065ec9** (11-20 05:36 KST), CI 7개 녹색, 원장 KEY-4/a (handoff 40b9378)
- [~] KEY-5 — 화면 쪽 22파일/44곳 + quantgen_desktop/paper.py + 키·연결 화면(gateway.status()) — 구현은 UI 세션 몫(소유자 경유). **요청문 초안 끝: handoff `plans/2026-11-20/KEY5_UI_REQUEST.md` (0df90ec, PAYMENTS)** — KEY-4 병합 뒤 메인 확정 신호 → 줄 번호 재정렬 → 소유자가 UI 세션에 붙여 넣음. OS-F1 뒤 적용 권장. 앞서 정할 것: set_backend(None) 가/나 안(OA-41)
- [~] KEY-5/a — KEY-5 앞 gateway 준비 3건 (G1 data.kis_stream 입구, G2 kis_workspace 순수 값 목록, G3 main.py QuoteFeed 하위 클래스를 공용 모듈로 → paper.py 재사용) — PAYMENTS, KEY-4 병합 뒤 main에서 브랜치, 대기열 **4h**. **코드 끝: `claude/payments-key5a-20261120` @ `dc936d4`** (main 8445187에서, 10파일, + PR #133 3차 검토 C 항목 A1R3-1/4/5·F2/F5/F6/F7). 메인 확인 11-20 04:10: 동결 엔진 4개 바이트 같음, main.py CRLF, code_sha256 10c27010 그대로, 게이트웨이 시험 71 OK. 메인 검토 결과 handoff `plans/2026-11-20/KEY5A_REVIEW.md` (주요 M1·M2, 작은 것 S1–S7) → PAYMENTS/이어받는 쪽이 고침
- [~] PAY-0 — 문의 7건 초안 + 목록 표 (docs/commercial/inquiries/, 문서 8개) — **초안 끝: `claude/payments-pay0-20261120` @ `7f8939c`** (main 9f76b07에서, 메인 확인 11-20 01:00: 문서만, 비밀값·다른 연락처 없음). PR은 대기열 자리 뒤, 원장은 병합 때. 발송은 소유자(OA-32)
- [~] PAY-2 — 결제 설계(시나리오 A) — **초안 끝: `claude/payments-pay0-20261120` @ `d0da1b2`** (docs/commercial/payments/ 4개: PAYMENT_DESIGN, PG_COMPARISON, PRIVACY_POLICY_PROPOSAL, README; 메인 확인 11-20 01:05: 문서만). 소유자 결정 P2-01..P2-15(OA-39), 법률 확인 걸린 것 P2-05·06·08·09·10·11·12·14. 약관 02 제4조·03·01 반영은 정책 PR-2. PR은 PAY-0과 함께 대기열 자리 뒤 **재검증 11-20: `0a24f02`** (main fa78df1 합침 909a3fa 위, PAYMENT_DESIGN·PG_COMPARISON만): 정기결제 증액·유료 전환 동의 30일(2025-02-14 시행) 확인, 다크패턴 시행일 확인, 디지털콘텐츠 철회 제한 요건 해설로 확인(조문 원문 미확인), PG 수수료·정산 주기는 미검증 유지 → PAY-0 03 문의 회신으로 확정. 메인 확인 04:15: 문서 2개만, 비공개 정보 없음. 후속 `e869064`: 2026-12-17 전자금융거래법 개정 건은 PG 문의 질문 후보(미검증)로만.
- [!] PAY-1 — 데스크톱 로그인 core/account/** — 웹 계정 공개(AUTH_UI_ENABLED) 뒤
- [!] PAY-3 — 회사 데이터 서버 — 법인·계약 전에는 설계만. 위치는 소유자에게 묻기
- [!] PAY-4 — 카드 PG 연동 — G1, G3 뒤
- [ ] 15-11 앱 계정·구독 화면 — 사업자 등록, 통신판매 신고, PG 뒤
- [ ] 15-12 서버 기능 플래그 (requires_filing / filing_accepted) — 법무 확인 뒤
- [ ] 15-13 앱·웹 주문 기반 — M-12, 모의 거래 20거래일, 변호사 의견(D-14), KIS 답 뒤
- [~] 소유자 AWS 안내 (OWNER_STEPS 25단계) — 13·14단계 끝, MFA는 이메일 MFA 유지로 결정(OA-01 완료), 15–17단계 진행 중(OA-02)

### 2.3 OS (OS_EXPANSION)

- [x] OS-P0-a — tools/qt_port 변환 도구 — c28b1d7 (PR #127)
- [x] OS-P0-b — packaging/, 바인딩 중립 spec, platform-build.yml(수동·v* 태그만), stage.py --profile mobile — c28b1d7
- [x] OS-P0-c — core/app_paths.py, core/app_identity.py — c28b1d7 (Notion 15-3의 파일 만들기도 이것으로 끝)
- [x] OS-P0-d — 플랫폼 계획 2판 — c28b1d7
- [x] OS-P0-e — PySide6 정식 시범, UI 점검표 — c28b1d7
- [x] OS-P0-f — 글꼴 대안, 세그폴트 최소 재현 — c28b1d7
- [~] PySide6 간헐 종료 고침 — UI 브랜치 414eceb에서 OS 재시험 끝(PySide6 160×2회 abort 0, PyQt6 18단계 종료코드 5025c6f와 같음, 9절 판정 복구). 기록 5커밋은 OS-F2 PR(4e)에 묶음. 병합 때 원장 OS-F1/a
- [!] OS-F1 — PySide6 전환 날 (UI는 pyqt6_to_pyside6 --apply, OS는 switch_day.py --apply, 그날 quantgen_desktop/**와 tests/desktop_* 잠금) — MERGE_QUEUE 6행. UI 7쪽 병합, 고침 확인, 소유자 "OS go"가 필요
- [~] OS-F2 — ~/.nextgen 경로 → core.app_paths.user_data_dir — **브랜치 `claude/os-f2-data-dir-20261120` @ `f9a3a75`** (main 8445187 합침, abort 기록 5커밋 묶음, 14파일; 관련 33파일 실패 목록 main과 같음, 통과 855→868; 지문 bcaf33d9…). 대기열 4e, owner_confirmed는 이것 병합 뒤
- [ ] OS-F3 — 키 저장, KEY-2와 맞춤 — KEY-2로 덮였는지 메인이 판단
- [ ] OS-F4 — macOS 차이 — OS-F1, OS-F2 뒤
- [ ] OS-F5 — macOS CI (로드맵은 "범위 미기재", 플랫폼 계획 2판이 정함) — OS-F4 뒤
- [ ] OS-M2 — macOS .app (ad-hoc 서명) — OS-F4, OS-F5 뒤
- [ ] OS-M3 — "Mac 없이 macOS" 질문 시점. 클라우드 Mac 24시간 약 $21 승인
- [ ] OS-A1 — Android(Flet) 2일 시험 — OS-F2 뒤. 컨테이너에서 pypi.flet.dev, dl.google.com이 막힘(403)
- [ ] 15-7 판매 빌드 준비 (제외 목록, PySide6 LGPL 점검표)
- [ ] 15-3 남은 것 — app_identity와 QSettings·windows_branding.py 연결. OS 순서(04 8절 "app_identity 연결")에 있지만 quantgen_desktop/windows_branding.py는 UI 세션 파일 → 소유자 경유

### 2.4 DATA_SOURCE/DIDM

- [~] DS-1 — VENDOR_EVAL_2026-11.md (대안 9개 × 정보 19종). 소유자 답(8절) 반영. 브랜치에만 있음
- [~] DIDM-0 — PREREG_V0.md. 소유자 승인 11-18. 열린 질문 2개
- [~] DIDM-1 — SCORE_SCHEMA_V0.md, core/didm/llm/schema.py (14종, novelty_0_100)
- [~] DS-4a — GDELT, ALFRED + 시점 저장소. 소유자 PC 확인 끝
- [-] DS-4b — Alpha Vantage·Tiingo·CryptoPanic 모두 무료로 뉴스 불가(소유자 PC 11-20) → 보류, 커넥터 코드는 남김. 뉴스·감성·엔티티는 GDELT+자체 NLP, 공시는 EDGAR·OpenDART (c206b10). 유료 공급원은 Stage 3 뒤 판단(소유자 답 2)
- [ ] DS-4c — CME FedWatch 종가판. DIDM 2단계 시작 때 (약 $25/월)
- [x] DS-4d — OpenDART·KIND(→OpenDART), SEC EDGAR, ECOS — 6곳 모두 소유자 PC 확인 끝 (OpenDART 819건, c6fda98, 11-20). 원장은 DS·DIDM PR 병합 때
- [~] DS-4e — Kalshi 브랜치에 있음(236개 시장). Polymarket은 변호사 확인 전까지 꺼둠
- [~] DS-H — 홈 지표 6개 데이터 계층 — **브랜치 끝: `claude/ds-home-indicators-20261120` @ `f80b3b0`** (main 8445187에서, 4파일, gateway 경유 확인, 새 시험 20 OK, 회귀 묶음 main과 같음; 메인 확인 11-20 03:5x). 대기열 4f. 남은 것: OA-09 진단 반영, BTC 단위 결정(OA-46), 병합 뒤 UI 세션에 계약 전달(소유자 경유)
- [-] DS-3 — RavenPack RPA 1.0 견적, Bigdata.com 비교. **관문 확인 끝(11-20 메인):** 소유자 11-18 답(OWNER_RULINGS_LOG 2026-11-18 절, 질문 1)으로 D14 "3단계" = RavenPack 대안 9개(DIDM Stage 3 아님), D14는 대안으로 구성·Bigdata.com 시험 안 함 → DS-3은 계획에 없음. 소유자가 RavenPack 견적을 원하면 다시 엶 (OA-38)
- [-] DS-2 — Bigdata.com Pro 시범. 쓰지 않음
- [ ] DS 앱 연결 (ID 없음) — 공급처마다 core/gateway/routes.json 한 줄 + display_rights.json + 법률 의견. 표시권, L 뒤. 구조 변경이라 소유자에게 먼저 알림
- [ ] core/didm/novelty.py — DS·DIDM PR에 포함
- [ ] DIDM 키를 Windows 자격 증명 관리자로 옮기기 (선택. KEY-3 병합으로 이제 가능. DATA 세션에 아직 안 알림)

### 2.5 UI (UI/UX 세션, 소유자 경유)

**main에 있음**
- [x] ⑬-2/market-rail-categories-only, ⑬-2/market-hub/1, ⑬-2/indicator-scroll-stability/1, ⑬-2/indicator-conclusions/1 (da0ea20) → ⑬-2/market-hub/main (8e026ab, PR #124)

**UI 브랜치에만 있음 (main 병합은 MERGE_QUEUE 5)**
- [x] ⑬-2/page-redesign/quant, ⑬-2/page-redesign/home, ⑬-2/page-redesign/tools, ⑬-2/page-redesign/guide, ⑬-2/page-redesign/risk, ⑬-2/page-redesign/library, ⑬-2/page-redesign/system (7902381)
- [x] ⑬-2/pyside6-prep/1 (75336f3), ⑬-2/pyside6-prep/2 (5025c6f), ⑬-2/pyside6-verify/1 (847b25c)
- [~] 종료 고침 반영 490562d (원장 행 없음, main 미병합. OS 재확인과 5행 병합 뒤 [x])

**남은 일**
- [!] UI 7쪽 + PySide6 준비 main 병합 — 소유자 실행 확인
- [ ] ⑬-2/page-redesign/system/2 — API 키 화면. KEY-5와 묶어서
- [ ] ⑬-2/page-redesign/home 실데이터 연결 — DS-H 뒤. 새 하위 ID는 UI 세션이 정함 (UI 문서는 `<route>/2`를 소유자 피드백용으로 씀)
- [ ] KEY-5 UI 몫
- [ ] OS-F1 전환 날 UI 몫 (pyqt6_to_pyside6 --apply, 화면 문구 3곳)
- [!] 용어 "캔들 차트 · 봉" 이름 바꾸기 (소유자 결정. "봉"은 금지어)
- [!] 지표 결론 문구·근거 수준 검토, 투자 자문 경계 법률 검토 (공개는 막혀 있음)

**예전 로드맵**
- [x] ⑬-2/a ~ ⑬-2/j, ⑬-2/a4-a, a4-b, a4-c, a4-d, a2, a4-b/2, a4-c/2, a4-d/2, a4-e, a3-type, a3-rail, a3-controls, a3-layout-reading, a1, compact-ui (19a7375), ⑬-2/k/cloud-runtime
- [x] 11-11~11-14 UI 원장 33행: ⑬-2/owner-14-flet, ⑬-2/owner-14-native, ⑬-2/owner-14-native/2, ⑬-2/ui-base-owner-decision, ⑬-2/ui-d7-home-markets-rail, ⑬-2/ui-d8-stock-detail, ⑬-2/us-market-cap, ⑬-2/compliance-ui-d7-d8, ⑬-2/ui-d9-stock-detail, ⑬-2/chart-test-midnight-flake, ⑬-2/ui-d10-markets, ⑬-2/compliance-ui-d7-d8/2, ⑬-2/ui-ci-windows, ⑬-2/ui-d12-chart-zoom-drag, ⑬-2/ui-d9-side-overflow, ⑬-2/ui-d11-rail/a, ⑬-2/ui-d11-review/b, ⑬-2/ui-d11-review/c, ⑬-2/ui-d13-score, ⑬-2/ui-d14-report, ⑬-2/ui-d15-rank, ⑬-2/ui-progressive-guide, ⑬-2/market-nav-v2, ⑬-2/guide-catalog-v2, ⑬-2/taskbar-brand-v2, ⑬-2/market-first-paint, ⑬-2/chart-risk-reward, ⑬-2/indicator-signal-context, ⑬-2/market-menu-click/1, ⑬-2/market-menu-depth/1, ⑬-2/research-workspace-readability/1, ⑬-2/chart-risk-reward/2, ⑬-2/indicator-reading-cues/1 (11-17~11-19 15행은 위 두 묶음)
- [x] ⑬-8/ui-handoff-40, ⑬-8/ui-handoff-43-44, ⑬-8/ui-handoff-49, ⑬-8/ui-handoff-51, ⑬-9/ui-handoff-46 — 웹사이트 검토용 JSON 기록만 끝. 원장이 "실제 전달 미완료"라고 적음 (2.6 전달 목록)
- [~] ⑬-2/a3 — 남은 A3: UI-12 설명, UI-9/11b 결과표, "더 알아보기" 창. **담당 MAIN (CURRENT next_ids, a3-* 앞부분도 MAIN이 함)**. 화면 파일이 UI 브랜치와 겹치므로 시작 전 소유자 경유로 UI 세션과 범위 확인
- [!] ⑬-2/k — 13-7 Windows 실화면, DPI, 키보드, 파일 대화상자, 실데이터·AI 확인 (소유자 PC). 담당 MAIN (CURRENT next_ids)
- [~] ⑬-1 — ⑬-1/a, ⑬-1/b 끝 / [ ] ⑬-1/c (담당 MAIN, CURRENT next_ids)
- [~] ⑬-8 — 끝: ⑬-8/a, b1, b2/a, b2/b, b2/b/2, b2/c/a, b2/c/b/a, b2/c/b/b/native. 남음: 13-8/b, b2, b2/c, b2/c/b
- [~] ⑬-9 — ⑬-9/a 끝 / [!] 13-9/b Windows에서 실제 Claude 요청 성공 확인
- [ ] ⑬-3 모델 증거 카드 확장, ⑬-4 실행 비교, ⑬-5 통합 위험 보기, ⑬-6 취소 가능한 작업, ⑬-7 읽기 전용 SDK — 10-29판 ID(GPT PR #12 브랜치에만). 공식 ID인지부터 정함 (14-1, OA-36). Notion의 13-7·13-8 번호와 다름

### 2.6 WEBSITE/AWS (소유자 경유, 다른 저장소 xkg4real/website)

- [x] W1–W6 — 법인 전 준비, M365 안내, ZIP, KO/EN 정책 HTML 검토본 (handoff dfb6a58, 84daa39, 9d0e678)
- [x] P1–P2 — 저장소, Amplify, Cloudflare DNS, 공개 배포 (SHA 1dbd9ded…, 599bd8c. 다른 저장소라 여기서 확인 못 함)
- [~] W7 — 웹 기록을 handoff에 쌓고 Notion REMAINING WORK 갱신 (상시, 11-13 뒤 기록 없음)
- [x] R1 AWS 읽기 확인 일부 — 시드니 SES·DKIM 정상, quantgen-dev 풀 있음, 서울은 SCP로 막힘
- [-] R1 남은 것 — api.quantgeneration.com/healthz 읽기 확인 (보류)
- [!] ACC-1 가입 화면 — 붙인 날짜 기록 없음 (이 저장소에서 확인 불가)
- [!] ACC-2 메일 인증 (6자리, 재전송)
- [!] ACC-3 로그인 (SRP, MFA, 드러내지 않는 오류 문구)
- [!] ACC-4 비밀번호 찾기·새 비밀번호
- [!] ACC-5 계정 페이지 (메일·비밀번호 변경, 2FA, 마케팅 메일, 탈퇴, 데이터 내려받기)
- [!] ACC-6 머리글·문구 (플래그 뒤 로그인·가입. 운영자 문구는 정책 PR-1 병합으로 관문 풀림)
- [!] ACC-7 보안 (고정 라이브러리, CSP, 토큰 저장)
- [!] ACC-8 바닥글 (개인정보 처리방침 강조, 개인정보 문의 메일)
- [!] ACC-9 시험 (개발 풀 자동 e2e, 운영 풀 수동 1회)
- [!] ACC-10 앱 클라이언트 설정 점검표와 플래그 전 점검표를 소유자에게
- [ ] WEB-0 웹 CI — 상태 모름
- [ ] WEB-1 색 추가 (D10-A) — 상태 모름
- [ ] WEB-2 문구 정리 — 상태 모름. 뜻이 바뀌면 main docs/compliance 먼저
- [-] WEB-3 출시 알림 폼 — ACC로 대체
- [-] WEB-4 자체 로그인 UI — ACC로 대체
- [ ] WEB-5 로그인 뒤 화면 틀 — ACC 뒤
- [ ] 15-6 releases.json 스키마 2
- [!] 웹사이트 세션 재개와 전달 — 정책 문구 다시 만들기(PR-130.json), 비밀번호 규칙 "특수문자 1개 이상", ACC 묶음, 풀 ID·Client ID, 그리고 docs/product/ui_website_updates/ JSON 43개(모두 delivery.status queued, 전달 기록 없음). 11-13 뒤 것: PR-112, PR-115, PR-117, PR-119, PR-124, PR-130
- [ ] 가격 이름 충돌 (Free/Pro/Ultra와 Research/Pro/Team Pilot)
- [ ] Track A (Cognito/SES/API) 범위
- [!] W8 Microsoft 365 (구매, 테넌트, Cloudflare 라우팅, 법률 검토). contact@ 선택으로 바뀔 수 있음
- [ ] AUTH_UI_ENABLED 켜기 전 점검 (ACC-10, 출시 전 8항목)

### 2.7 RESEARCH/Nautilus 로드맵

- [x] ① 묶음 — ①-1 (완료 시각 미검증), ①-2, ①-2/2, ①-2/3, ①-3, ①-4, ①-5, ①-2/4/a
- [ ] ①-2/4 — Notion 1-7은 지웠지만 원장에는 ①-2/4/a만 있음. 범위 확인
- [x] ② 묶음 — ②-1, ②-1/b, ②-2, ②-3, ②-4, ②-5/a (4.1 대기열 순서 승인, 185b56c), ②-5/b, ②-5/c, ②-6
- [x] ②-5 하위 31묶음 — ②-5/§10-a, NEW-M6-01, NEW-M6-18, M4-N5, M3-N07, N-M1-09, N-M1-10, N-M1-11, N-M1-03, N1, NEW-M6-03, NEW-M6-02/a, M4-N2, M4-N1, M4-N12, M3-N04, M4-N8, M3-N08, M4-N3, M4-N6, M4-N11, N11, M3-N06, NEW-M6-14/15/22, M4-N4/N7/N9, N-M1-02/a, NEW-M6-04, NEW-M6-05, NEW-M6-12, NEW-M6-19
- [~] ②-5 상위 — §10 결함 67묶음 중 31 끝, 36 남음 (관찰 모델 14, ID 대응 15 포함)
- [-] ②-5/N-M1-02/b — 소유자 보류 (11-05)
- [x] 2-8 R3 rev2/10.2 A 범위 — 소유자 "전부 다 승인" (db07005)
- [x] ③-1 ~ ③-6
- [~] 3-7 기존 가드 기술 조건 확인 — Notion에서만 완료. 원장 행·커밋 없음 → 근거 찾아 원장으로 닫기
- [-] ④-1 GPT·Gemini 추가 심사 — NOT_PERFORMED, 소유자 면제 (원장 행 없음)
- [x] ④-2/a O2~O15 결정 양식 (0a91f26) / [~] ④-2 상위 — 판정은 받음(⑤-1이 끝남), 원장 행 없음
- [x] ④-3/O11-A2/a, ④-3/O8/a, ④-3/O11-A2/c (0510719, main)
- [~] 4-3/O11-A2/b 실제 Windows 등록 — Notion에서만 완료. 원장 행·커밋 없음
- [~] ④-3 상위 — 하위는 끝, 상위 원장 행 없음. 닫을지 결정
- [x] ⑤-1, ⑤-1/a (원장: Claude 7A 사전 작업), ⑤-1/b, ⑤-1/c
- [x] ⑤-2/a, ⑤-2/a2, ⑤-2/b, ⑤-2/b/2, ⑤-2/d, ⑤-2/e, ⑤-2/e/2, ⑤-2/f, ⑤-2/g
- [~] ⑤-2 상위 — 원장 행으로 닫기 (BTC FAIL 원인 미확인 기록은 남김)
- [x] ⑥-1 (a2ac79b), ⑥-1/readout, ⑥-1/prep, ⑥-1/prep/2, ⑥-1/rulings, ⑥-1/rulings/2, ⑥-2 (8a3d171), ⑥-2/readout
- [x] ⑦-1 (efe5bb2), ⑦-1/E-readout, ⑦-2/p3 (888f121), ⑦-2 (888f121, d895873, 13f4dea, 6e077dc)
- [ ] ⑦-2 후속 — F7 종료 코드 1 원인 미검증. F6·F7 다시 돌릴지 소유자 답 ("F7 재실행 생략 승인" 문구 또는 재실행)
- [x] ⑦-4/BS-21 (Notion 9-7) — 0cc30c3
- [~] ⑧-1 H2 holdout — ⑧-1/a(판독 준비), ⑧-1/b(판독 완료·유효, 11-05 소유자 PC. 커밋 칸 a76af7d는 main 커밋 안내서) 끝. H-D5 main 커밋 남음. 기한 약 2026-12-19, 경고 작업 12-05
- [ ] ⑧-2 2027-01-01부터 잠금 holdout 규칙 (상시 규칙)
- [ ] ⑧-3 GROKTEAM 전망 — 2027-02-01 뒤 태그 클론에서 한 번
- [ ] ⑧-4 분리 명세 2단계 (LAZYOWEN) — ⑧-1 뒤
- [x] ⑨-1/a (7749450), ⑨-1/2/a, ⑨-1/2/b, ⑨-1/2/c, ⑨-1/2/d, ⑨-1/2/d/2, ⑨-1/2/e
- [~] ⑨-1 상위 — 원장 행 없음. [!] L-2 남은 것 — T-FIX-01 보류, I-05 (LA-30 데이터 필요), A-2 파일 이름 답
- [~] ⑨-2 거시 데이터·라이선스 — ⑨-2/a, ⑨-2/c 끝. 실제 데이터와 라이선스 확인 남음
- [~] ⑨-3 상위
- [x] ⑨-3a 하위 — codec/1, store/1, keys/1, data-hash/1, source-digests/1, series-digest/1, series-format/1, series-files/1, series-files/2, series-files/3, fold/1, fold/2, recorder/1/lifecycle (5888d05), recorder/1/outage (f058145)
- [ ] ⑨-3a/recorder/1 상위 — 끝난 것으로 기록할지, 남은 부분을 정할지
- [ ] ⑨-3a 상위 — 병행 산출 완료 기준 확인 뒤 원장
- [ ] ⑨-3b R3 비교 보고서 — ⑨-3a 뒤
- [ ] ⑨-3c R3 과최적화 보정 기준 타당성 검증 (DSR 시행 수 정의, 유효 시행 수, 시뮬레이션) — ⑨-3b 뒤
- [ ] ⑨-3d R3 판정 기준 변경 여부 (소유자 결정) — ⑨-3c 뒤
- [ ] 9-4 Q8, Q15, 판단 기준 B 묶음 — Notion은 지웠지만 본문은 "나중에 따로 결정" (⑨-3d와 묶여 있음)
- [x] ⑨-4/a (c814d22), ⑨-4/2/a, ⑨-4/2/b, ⑨-4/2/c (5f08973 등)
- [~] ⑨-4 상위 — 원장 행 없음. [!] 남은 것 — Q1–Q5, Q7, N_raw 뜻 답
- [ ] ⑨-5 거시 카드 실행, 기술주 펀드 판정 — ⑨-2 뒤
- [ ] 9-7/b 채권 화면 수동 검토, 실제 자금 가격 확인
- [x] ⑫-0, ⑫-1/a, ⑫-1/a/2, ⑫-3, ⑫-2/a, ⑫-2/b/1, ⑫-1/display-owner-decision
- [!] 12-5 (⑫-2 상위, ⑫-2/b) PR-B 실제 resolver — 12.8/K-f와 동결 하네스 결정
- [~] 12-6 (⑫-1 상위) 남은 범위
- [ ] ⑫-4 형식 관문 막힘 대장 — 10-29판 ID(PR #12에만), ⑨-2·⑨-5 뒤. 14-1에서 범위 확인
- [!] owner_confirmed 두 줄 다시 쓰기 — 다음 Nautilus 기록 실행 직전에 한 번, OS-F2 뒤 (지금 code_sha256 10c27010)

---

## 3) 소유자 수동 작업 (OWNER_ACTIONS)

**24시간 안 열린 항목: 7개 (OA-03 ~ OA-06, OA-09, OA-10, OA-43). 기준 5개 이상 → Claude 앱 푸시 알림 (SESSION_PIPELINE 5절).**

push_log:
- 2026-11-20 00:51 KST 메인 — 9건 (OA-02~OA-10) — PushNotification "Mobile push requested"
- 2026-11-20 01:40 KST 메인 — OA-02 완료, OA-43 추가로 9건 그대로. 마지막 알림 뒤 6시간 안이라 다시 보내지 않음 (다음 가능 07:51)

정기 점검: 메인 세션 예약 작업 "QUANTGEN pipeline check (3h)" (trig_01P2NBVZFChNHJGjVdtrDTyC, 매 3시간 :20, 첫 실행 11-20 03:20 KST)

### 3.1 24시간 안 (지금 세션을 막고 있음)

| ID | 무엇 | 요청한 세션 | 요청 시각 | 기한(24h 안?) | 상태 |
|---|---|---|---|---|---|
| OA-01 | 회원 MFA·계정 복구 결정 | PAYMENTS | 11-19 23:43 | — | **완료** 소유자 "지금 그대로: 이메일 MFA 유지" 선택(11-20 00:00 무렵, PAYMENTS 전달). OWNER_RULINGS_LOG 기록은 메인의 다음 PR |
| OA-02 | AWS 운영 풀 단계 (Golden Hour Code 계정) | PAYMENTS | 11-19 22:45 | — | **완료** 1~23c·25 끝(11-20, PAYMENTS 보고; 23a/23b는 CloudShell 명령, 24는 기존 월 예산 사용). 기록은 OWNER_STEPS 1-2 |
| OA-03 | SES no-reply@가 바로 Verified였는지, Cloudflare 규칙이 필요했는지 한 줄 답 | PAYMENTS | 11-19 23:09 | 24h 안 | 대기 |
| OA-04 | 웹사이트 세션에 "비밀번호 규칙에 특수문자 1개 이상 추가" 문장 붙이기 | PAYMENTS | 11-19 23:37 | 24h 안 | 대기 |
| OA-05 | 웹사이트 세션 재개 지시 + 정책 문구 다시 만들기 프롬프트(PR-130.json) 붙이기 | MAIN | 11-19 | 24h 안 | 대기 |
| OA-06 | UI 7쪽을 skymi, whydi PC에서 실행 확인 → UI 세션에 "PR 만들어" | UI, OS, MAIN | 11-18, 11-19 03:13, 05:11 | 지금 (KEY-4 다음 차례를 막음) | 대기 |
| OA-07 | OpenDART 확인 다시 실행 | DATA | 11-19 01:29 | — | **완료** 소유자 PC: 9쪽, 공시 819건 저장 (DATA 보고 11-20 01:57, VENDOR_EVAL 3.1 기록 c6fda98). 공식·무료 공급원 6곳 모두 확인 끝 |
| OA-08 | 무료 키 확인 | DATA | 11-19 15:00 | — | **완료** 소유자 PC 재실행(11-20): Alpha Vantage 뉴스 = 유료 전용(premium endpoint), Tiingo 뉴스 = 403 권한 없음 → 무료로 되는 뉴스 공급원 0 → DS-4b 전체 보류(코드 남김), 뉴스·감성은 GDELT+자체 NLP로 (c206b10) |
| OA-09 | 마스터 부록 H4 홈 지표 진단 명령 실행, 출력 붙이기 | DATA (명령은 MAIN) | 11-17 22:13 (4번 요청, 마지막 11-19 15:00) | 지금 (DS-H 막힘) | 대기 |
| OA-10 | DIDM 질문 답: (a) novelty 보조 조건을 정식으로? (b) 자체 LLM 기반 모델과 학습 데이터 마지막 날짜 (c) 평가표 판단 2칸(자체 NLP 열의 수집 F·실시간 J = X, 자체 NLP 관련성 = X)이 맞는지 — 세 개 모두 DATA 인계 8절에 있음 | DATA | 11-19 00:09 (11-20 00:23 갱신) | 24h 안 | 대기 |
| OA-43 | AWS 비용 출처 확인 — 소유자 11월 막대(11-20 01:5x 공유): EC2-Other $39.47(81%), EC2-Instances $5.55, VPC $2.11, Amplify $1.57, 합 $48.71 → 하루 약 $2.6, 이대로면 월 약 $77–81. 메인 추정(미검증): 작은 인스턴스 1대(t3.micro 급, 약 17.5일)+공인 IPv4 1개(약 17.6일)가 함께 켜져 있고, EC2-Other는 NAT 게이트웨이 또는 t3 unlimited CPU 크레딧 초과(CPU 100% 지속 시 하루 약 $2.16 — 폭주 프로세스나 침해 가능성)와 금액이 맞음. 다음: Cost Explorer EC2-Other를 '사용 유형'으로 묶은 화면 → 메인이 판정. 끄거나 지우지 않음 | PAYMENTS→MAIN | 11-20 01:39 | 24h 안 (권장) | **11-20 소유자 확인**: 음수는 Charge type=Credit 필터 → 크레딧이 갚는 중, 현재 청구 $0.00. CPU 그래프 100% 고정 확인 → 소유자가 크레딧 사양 Unlimited→**Standard로 바꿈**(초과 요금 멈춤). 보안 그룹 인바운드 22·80·443 모두 0.0.0.0/0, IAM 사용자 없음, CloudTrail RunInstances 2026-10-12 20:27 KST, 만든 주체 = 소유자 콘솔 역할 세션(임시 키). 10월 크레딧 요금 약 $5.2 → 100%는 10월 말(약 10-28~29)부터로 추정(미검증). 메인 판단: 원인 미확정(헛도는 프로그램 또는 SSH 침입 뒤 채굴), 22번 전체 개방 + 출시 2주 뒤 갑자기 100%라 침입 가능성 배제 못 함. 다음(소유자): 이 서버를 웹사이트가 쓰는지 확인 → 안 쓰면 Stop / 쓰면 22번을 My IP로 좁히고 로그인해 top으로 프로세스 확인(모르는 프로세스면 정리하지 말고 새로 만들기), Billing Credits 잔액·만료일, CPU 그래프 기간 늘려 100% 시작일 확인 / **11-20 DNS 확인**: 이 EC2 = `api.quantgeneration.com` (Cloudflare 프록시 켬), 본 사이트는 CloudFront(Amplify) → 웹사이트 API 서버라 Stop 대신 ① 22번 Source를 소유자 IP로 ② 접속해 읽기 전용 명령으로 CPU 프로세스·cron·로그인 기록 확인(지우거나 끄지 않음) → 결과 보고 판정. 원 서버 IP는 공개 저장소에 적지 않음(Cloudflare 뒤 원 IP 노출 방지). 뒤에 할 것: 80/443을 Cloudflare IP 대역으로 좁히기 / **11-20 접속 시도**: 소유자가 CloudShell에서 먼저 실행(서버 아님) → EC2 Instance Connect 'Failed to connect'(CPU 묶임 추정). 시스템 로그(Amazon Linux 2023, t3.micro급 913MB, 재부팅 없음, OOM 없음): 10-21 19:0x KST 포트 80 SYN flooding, 10-30 14:2x KST debugfs tracing 자동 마운트(보통 API 서버에 없음, 100% 시작 추정 시점과 가까움), 10-31 SSM Agent 재시작, **11-11 18:4x KST 1GB swapfile 추가 + daemon-reload 여러 번(누가 했는지 소유자 확인 필요)**. 시각은 부팅=생성 시각 가정(추정). 다음: Unlimited 잠깐 되돌려 재접속 → 안 되면 Session Manager(SSM Agent 있음, IAM 역할 필요) 또는 Reboot / 11-20: CPU credit balance 0 고정 확인(접속 실패 원인 추정 맞음). 11-11 스왑은 소유자 작업, 이유 "메모리가 부족해서" → 그때 이미 자원 부족. 원인(앱 헛돎 vs 침입) 미정, 2단계(Unlimited 잠깐 → 접속 → 프로세스 확인) 대기 / **11-20 원인 확정(메인 판단)**: 서버 안 프로세스 목록에서 `sudo nano /usr/share/nginx/html/index.html` 2개(root)가 각각 CPU 약 63%, 실행 21일 8시간 → 시작 10-30 14:26 KST무렵 = 시스템 로그 10-30 기록·10월 크레딧 요금 역산과 일치. 브라우저 터미널을 닫으며 남은 편집기(sudo) 프로세스가 헛도는 것으로 판단. 침입 흔적 없음: 낯선 프로세스·/tmp 파일 없음, 서비스는 nginx·postgresql·quantgen-api(QUANTGEN Account API)·SSM 등 정상, 로그인 성공은 AWS 브라우저 접속 대역과 소유자 IP뿐, 11-13~15 ssh-rsa 거절(인증 전 실패)만. 다음(소유자): 두 프로세스 kill → CPU 하락 확인 → 크레딧 Standard 유지 → 22번 My IP+EC2 Instance Connect 목록, CPU 경보. 뒤에: 이 서버 PostgreSQL(계정 API) 백업 여부를 웹사이트 세션에 확인 / **11-20 23:0x KST 해결**: 소유자가 두 프로세스 종료(SIGTERM 무시 → kill -9로 종료). 직후 CPU 100% idle, load 3.6→1.8 하락, quantgen-api·nginx·postgresql active. `index.html.save`(1바이트, 10-30 05:26 UTC)로 편집기 시작 시각 재확인. 남은 것(소유자): 크레딧 Standard로 되돌림, 10~30분 뒤 CPU 그래프 확인, 22번 좁히기, (선택) CPU 경보, .save 파일 정리 |
| OA-44 | 이메일 MFA 회원 분실(두 번째 확인 수단 없음) | PAYMENTS→MAIN | 11-20 02:0x | — | **완료** 소유자 "2로 권장합니다. Payment세션에다가 전달해주세요"(2026-11-20 02:04:06 KST) → ② 관리자가 옛 계정을 지우고 같은 이메일로 재가입. PAYMENTS에 전달, OWNER_RULINGS_LOG는 4d |
| OA-45 | OWNER_STEPS T14: CloudTrail 회원 쪽 이벤트 하나를 View event로 열어 username/sub가 있는지 확인 (6.1 ② 확정용) | PAYMENTS | 11-20 02:0x | 아님 | 대기 |
| OA-46 | 홈 BTC 단위: 실시간은 Upbit 원화, 일별·그래프는 Yahoo 달러(D8 BTC-USD) → ① 지금처럼 따로 표시 / ② 일별도 Upbit 원화 / ③ 실시간을 해외 거래소 달러로 (메인 권장 ③ 검토: D8과 같은 달러 기준, 원화가는 김치 프리미엄이 섞여 다름 — 표시권 미검증) | DATA→MAIN | 11-20 03:5x | 아님 | 대기 |

### 3.2 나중 또는 조건부

| ID | 무엇 | 요청한 세션 | 요청 시각 | 기한(24h 안?) | 상태 |
|---|---|---|---|---|---|
| OA-11 | 관리 계정의 시험 풀 2개 삭제 (OWNER_STEPS 1-3 경우 1: 삭제 보호 끄기 → Delete) | PAYMENTS | 11-19 22:23 (11-20 갱신) | 아님 | 대기 |
| OA-12 | 웹사이트 세션에 ACCOUNT_SETUP 3부 블록 + OWNER_STEPS 2단계 메시지(풀 ID·클라이언트 ID 채워짐, ACC-3/ACC-4 새 문구 포함) 전달 — PR #133 병합 뒤 최신본으로 | PAYMENTS | 11-20 (KEY-4 3차 반영) | 아님 | 대기 |
| OA-13 | ADMIN_GUIDE 부록 C 시험(C1~C8), T1 시험, 출시 전 8항목·118문항 | PAYMENTS | 11-18, 11-19 | 아님 (풀 완성 뒤) | 대기 |
| OA-14 | D9 "예상 시간"이 작업 시간만인지 한 줄 답 (지금은 나안으로 진행) | MAIN | 11-17 (11-18, 11-19 다시) | 아님 | 대기 |
| OA-15 | ⑦-2 F6·F7 다시 실행할지 ("F7 재실행 생략 승인" 문구로 생략 가능) | MAIN | 11-19 01:18 | 아님 | 대기 |
| OA-16 | 용어 "봉" 바꾸기, 지표 결론 문구 검토 | UI | 11-17 | 아님 | 대기 |
| OA-17 | GH-2에 비밀 검사 CI 넣을지 | MAIN | 11-17 | 아님 | 대기 |
| OA-18 | 전환 날 "OS go" | OS | 미래 | 아님 (UI 병합 뒤) | 보류 |
| OA-19 | owner_confirmed 두 줄 다시 쓰기 (--fingerprint, owner/nautilus-confirm-<날짜> 브랜치 PR). 소유자의 15:30 "완료" 답은 실제와 다름(표는 아직 f995600b, 브랜치 없음) → 지금은 하지 말고 다음 기록 실행 직전에 하라고 알림 | MAIN | 11-19 | 아님 (다음 기록 실행 직전, OS-F2 뒤) | 보류 |
| OA-20 | 변호사 질문: 규제·G2·⑩-1/b, Polymarket·Kalshi, LGPL·공증·iOS 5문항, D12 웹 거래(+KIS), 15-12, 투자 자문 경계 | OS, DATA, MAIN | 11-18 02:43 등 | 아님 | 대기 |
| OA-21 | G1 법인 설립 → "법인 설립 완료: <이름>" 알리기. 이어서 G3 PG, 사업자 등록, 통신판매 신고 | PAYMENTS, MAIN | 상시 | 아님 | 보류 |
| OA-22 | G2 유사투자자문업 판단·신고 | MAIN | 상시 | 아님 | 대기 |
| OA-23 | 표시권 확보, DIDM 결과를 앱에 언제 넣을지 | DATA, MAIN | 상시 | 아님 | 대기 |
| OA-24 | Windows 글꼴 확인 (선택) | OS | 11-18 00:21 | 아님 | 선택 |
| OA-25 | DIDM 키를 자격 증명 관리자로 옮기기 (선택) | DATA | 11-19 15:00 | 아님 | 선택 |
| OA-26 | ⑧-1 H-D5 main 커밋을 소유자 PC의 별도 클론에서 (판독 ⑧-1/b는 끝, 안내서 a76af7d 검토), 12-05 경고 작업 처리 | MAIN | 11월 | 아님 (약 2026-12-19) | 대기 |
| OA-27 | 연구 답: ⑨-4 Q1–Q5·Q7·N_raw, ⑨-1 A-2·LA-30 데이터, ⑨-2 데이터·라이선스, 12-5, 12-7, ②-5/N-M1-02/b 재개 여부, 9-4 | MAIN | 11-05~11-11 | 아님 | 대기 |
| OA-28 | M-12 D8·D10·계좌 평가 정의, ⑪-1 승인, TRADEGEN PR #14·#15·#16 병합과 승인 명령 | MAIN | 11월 | 아님 | 대기 |
| OA-29 | Windows 확인: ⑬-2/k (13-7), 13-9/b | MAIN, UI | 11월 | 아님 | 대기 |
| OA-30 | 빌드 승인: platform-build.yml 실행, 클라우드 Mac 약 $21, Android 폰 시험, 네트워크 허용(pypi.flet.dev, dl.google.com, docs.aws.amazon.com 선택) | OS, PAYMENTS | 11-18 | 아님 | 보류 |
| OA-31 | 유료: CME FedWatch(2단계, 약 $25/월), Trading Economics 견적(3단계 뒤) | DATA | 11-19 15:00 | 아님 | 보류 |
| OA-32 | PAY-0 문의 7건(docs/commercial/inquiries/) 검토·발송과 각 "보내는 방법" 창구 확인, 01 세무사 선정, 07 금융위 문의 전 변호사 검토 여부 결정; 이어서 PAY-2 확인, PAY-3 서버 위치 | PAYMENTS | 11-20 01:00 (초안 7f8939c) | 아님 | 대기 |
| OA-33 | 웹사이트: W8 Microsoft 365, Track A 범위, 가격 이름 충돌, healthz 확인, 전달 대기 JSON(PR-112, PR-115, PR-117, PR-119, PR-124 등 43개 모두 queued) 전달 | WEBSITE | 11-13 | 아님 | 대기 |
| OA-34 | KEY-5 요청을 UI 세션에 전달 | PAYMENTS | KEY-4 뒤 | 아님 | 보류(이전 기록). **11-21 중앙 정정:** 단일창구인계로별도채팅전달불필요; 실제KEY5/PC/OSgo완료아님 |
| OA-35 | ⑧-3 GROKTEAM 한 번 실행 | MAIN | — | 아님 (2027-02-01 뒤) | 보류 |
| OA-36 | 오래 열린 GPT PR #12 닫을지, 그 안의 REMAINING_WORK_2026-10-29 ID(⑫-4, ⑬-3~⑬-7, ⑭-1~⑭-3)를 쓸지 | MAIN | 아직 묻지 않음 (메인이 물을 것) | 아님 | 대기 |
| OA-37 | GPT 로컬 커밋 a2d93c2(Notion ⑤-1/a), 7e9e112(Notion ⑩-2/b-private-offline-mvp)가 남아 있는지, push할지 버릴지 | MAIN | 아직 묻지 않음 | 아님 | 대기 |
| OA-38 | DS-3(RavenPack 견적·Bigdata.com 비교)을 계획에서 빼도 되는지 한 줄 확인 (11-18 D14 답 기준 메인 해석: 뺌) | MAIN | 아직 묻지 않음 | 아님 | 대기 |
| OA-39 | PAY-2 소유자 결정 P2-01..P2-15 (docs/commercial/payments/PAYMENT_DESIGN.md 결정 표; 특히 P2-08 단순 해지 일할 환불 없음, P2-09 7일 철회 반환 기준, P2-10 가격 인상 미동의 시 종료 — 법률 확인과 함께), PAY-0 03번 PG 문의에 PG_COMPARISON 3절 질문 6개 추가 여부 | PAYMENTS | 11-20 01:05 | 아님 | 대기 |
| OA-40 | PAY-3 회사 데이터 서버 위치: A 시드니(같은 AWS 계정) / B 서울 / C Cloudflare Workers — 장단점·비용(미검증)은 handoff plans/2026-11-20/KEY5_UI_REQUEST.md 부록, 제안 A | PAYMENTS | 11-20 01:10 | 아님 | 대기 |
| OA-41 | KEY-5 전: core.credentials.set_backend(None) 가 안(시험에서만) / 나 안(앱도 .env만) — 같은 파일 0절 3항 | PAYMENTS | 11-20 01:10 | 아님 (KEY-5 전) | 대기(이전 기록). **11-21 메인 기술선택:** 요청문'소유자/메인'허용에따라가안, 기존앱keyring유지/시험만memory·None격리. 명시OA41답수신으로세지않음. 앱keyring끄기·.env전용화는선택안함 |
| OA-42 | 이메일 MFA 회원의 비밀번호 분실 처리(ADMIN_GUIDE 6.1) — 임시 비밀번호가 MFA 코드와 같은 메일함으로 가는 맞교환 | MAIN (3차 검토 DOC3-3) | 11-20 01:24 | — | **완료** 소유자 "권장으로 가겠습니다"(11-20 01:25:49 KST) → ② 발급 전 두 번째 확인 + 강제 변경 때 인증 앱 권장. PAYMENTS가 KEY-4 같은 push에 반영, OWNER_RULINGS_LOG는 4d |

---

## 4) 병합 순서 (MERGE_QUEUE 거울)

MERGE_QUEUE.md의 번호를 그대로 둔다. 번호 없는 "제안" 행은 메인 정리안이고 MERGE_QUEUE.md에 행을 넣어야 한다.

**2026-11-21T13:06:45+09:00 현재 거울 보정** (아래 종전 표는 11-20 관측 이력으로 보존):

| 순서 | 현재 확인된 상태 | 근거 |
|---|---|---|
| 4c / 4d / 4d' | KEY-4·중앙 문서·KEY-4/a는 이미 병합 완료 | PR133 `8445187`, PR135 `fa78df1`, PR134 `f065ec9`; MERGE_QUEUE 완료 행 |
| 4e | OS-F2 PR136, 최신 `64ff58e`, 전체 CI 대기; 현재 유일 병합 대기 PR | CURRENT 13:04:53·MERGE_QUEUE 12:33:42 |
| 4f / 4g / 4h | DS-H `7ce3791` → DS·DIDM `abd10c6` → KEY-5/a `45db2be`, 각각 앞 PR 병합 뒤 최신 main 검증·기준선·CI·PR | MERGE_QUEUE의 현재 순서; 원격 보존을 병합으로 세지 않음 |
| 5 / 6 | 중앙 UI 통합 준비, 실제 PC 확인 뒤 UI 병합; 이후 OS go와 PySide6 전환 조건 유지 | UI_SESSION_CURRENT 최신 인계 |

아래 표의 'KEY-4 재검증 중', '4d 대기', 'OS-F2 행 없음', 'DS 8행'은 위 현재 거울의 실행 지시로 쓰지 않는다.


| 순서 | 무엇 | 세션 | 상태 | 근거 |
|---|---|---|---|---|
| 1 | ⑦-2/a | MAIN | [x] | PR #126, 56fe32a |
| 2 | OS 작은 PR (OS-P0-a~f) | OS | [x] | PR #127, c28b1d7 |
| 3 | KEY-2 | PAYMENTS | [x] | PR #128, 3249af7 |
| 3b | KEY-2/b | PAYMENTS | [x] | PR #129, ca5da08 |
| 4 | 정책 PR-1 (PAY-A2/a) | PAYMENTS | [x] | PR #130, edbe9f7 |
| 4a | GH-1 + CI concurrency | MAIN | [x] | PR #131, ab24dec |
| 4b | KEY-3 | PAYMENTS | [x] | PR #132, 9f76b07 |
| 4c | KEY-4 | PAYMENTS | [~] | PR #133 148504a, 메인 3차 재검증 중 |
| 4d | 메인 문서 PR: CLAUDE.md(SESSION_PIPELINE 포인터, "법인 설립 완료" → INCORPORATION_CHECKLIST.md), OWNER_RULINGS_LOG(11-19 계정 결정 3건) | MAIN | [ ] | KEY-4 바로 뒤 (11-20 메인이 정함) |
| 5 | UI 7쪽 + PySide6 준비 (+490562d) | UI (소유자 경유) | [!] | 소유자 실행 확인 뒤 |
| 6 | OS-F1 PySide6 전환 | UI + OS | [ ] | 5 뒤, 소유자 "OS go" |
| 7 | KEY-5 (MERGE_QUEUE의 "KEY-3 → KEY-4 → KEY-5"는 낡음 → KEY-5만) | PAYMENTS(요청) + UI(구현, 소유자 경유) | [ ] | 6 뒤 권장 |
| 8 | DS·DIDM | DATA | [ ] | MERGE_QUEUE 8행 "차례가 오면" |
| 제안 | OS-F2 경로 전환 | OS | [ ] | MERGE_QUEUE.md에 행 없음. 브랜치 작업은 지금 가능. Nautilus 지문이 바뀜 |
| 제안 | OS PySide6 종료 원인 기록 (claude/os-pyside6-abort-20261119 8262d6c, 5파일) | OS | [ ] | 행 없음. OS-F1 PR에 묶거나 작은 PR |
| 제안 | 정책 PR-2 | MAIN/PAYMENTS | [ ] | AWS 풀 + 웹 계정 화면 뒤 |
| 미정 | GH-2 정리 PR | MAIN | [ ] | 빈 자리에 |
| 뒤 | owner_confirmed 소유자 PR | 소유자 | [-] | 다음 기록 실행 직전, OS-F2 뒤 |

메모
- UI 소유자 확인이 늦어지면 DS·DIDM(8)을 5보다 앞으로 당길지 메인이 정한다. DS는 소유자 PC 결과만 있으면 준비된다. 브랜치끼리 겹치는 파일은 공유 파일뿐이다(runtime-smoke.yml: KEY-4·UI·DS, source-review.json: KEY-4·UI).
- PR을 여는 조건: 자기 행이 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때. 최신 main 합치기 → 시험 → compliance 기준선은 맨 마지막 → --check PASS → PR.
- 병합 뒤: ledger --done → 이 문서 [x] → MERGE_QUEUE 줄 긋기 → Notion.

---

## 5) 최종 단계 — 가상환경 시험과 파일 전달

모든 트랙이 끝나면(2절에 [ ], [~], [!]가 없고 [-]만 남으면) 메인이 아래를 한다.

**빌드 목록 (자료에 나온 것)**

| 앱/빌드 | 만드는 곳 | 지금 | 최종 시험 (가상환경) | 넘길 파일 |
|---|---|---|---|---|
| 데스크톱 Windows | packaging/quantgen_desktop.spec (PyInstaller), platform-build.yml (수동·v* 태그) | 초안 끝(OS-P0-b), 실제 실행 아직 | 새 venv에서 설치 → runtime-smoke 묶음 → packaging/selfcheck.py → Windows 러너 산출물 실행 확인 | 실행 파일/설치본, packaging/licenses 제3자 고지. 코드 서명(Windows OV)은 G1 뒤 |
| 데스크톱 macOS | platform-build.yml, 클라우드 Mac | OS-F4, OS-F5, OS-M2 대기 | ad-hoc .app 실행 확인 (클라우드 Mac 24시간) | .app 또는 .dmg. 공증은 법인·Apple 조직 뒤 |
| 데스크톱 Linux | 컨테이너 로컬 빌드 | selfcheck 11/11 (PyQt6·PySide6). 판매 대상인지 미정 | 새 venv selfcheck | 소유자가 원하면 |
| Android APK | Flet, stage.py --profile mobile | OS-A1 시험 전. 컨테이너 네트워크 막힘 | 소유자 폰: 크기, 첫 실행 시간, import, Quant Lab 결과 1개 데스크톱과 비교 | debug .apk |
| iOS | — | 계획 없음 (LGPL 정적 링크 변호사 확인 전) | — | — |
| 웹사이트 | xkg4real/website, Amplify (다른 저장소) | 공개 페이지 배포됨, 계정 화면(ACC) 대기 | 개발 풀 e2e, 운영 풀 수동 1회(ACC-9), 배포 커밋 대조 | 배포 주소와 커밋 |
| 동반 앱 MVP (⑩-2) | 별도 | ⑩-2/b 남음 | 합성 데이터 시험 | 소유자가 원하면 |
| TRADEGEN | 다른 저장소 | PR #14–#16 대기 | 이 보드 범위 밖 | — |

**최종 점검표**
- [ ] main 전체 CI 녹색, compliance --check PASS
- [ ] Nautilus 지문 확인, owner_confirmed 두 줄이 지금 지문과 맞음
- [ ] 빌드마다 새 가상환경(또는 새 VM)과 빈 사용자 데이터 폴더에서 설치·실행 시험
- [ ] 결과 보고와 파일을 소유자에게 전달, 원장에 기록
- 주의: Windows·macOS 빌드는 이 컨테이너에서 직접 못 만든다 → platform-build.yml 실행(소유자 승인). Android는 네트워크 허용이 필요하다(pypi.flet.dev, dl.google.com). 환경 변경도 소유자 승인.
