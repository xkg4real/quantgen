## 2026-11-23T04:52:13+09:00 · 내부 개발 병합 순서

Android #141 병합 및 tree 확인을 마쳤습니다. 다음은 실제 main 666e0064까지 통합한 Alpaca #143 5039835a의 전체 CI와 최종 검토입니다. 다음 공유 변경을 병합하기 전에 그때의 main과 기술 지문을 대조합니다. #140은 별도 Windows PC7 확인이 남습니다. #144·#145와 T8-6을 같은 공유 파일에 동시에 병합하지 않습니다.

## 2026-11-23T03:47:46+09:00 · DIDM, Android 및 T8-5

Massive 뉴스 메타데이터를 처리하는 [초안 PR #144](https://github.com/xkg4real/quantgen/pull/144)을 열었습니다. 작업 브랜치 `gpt/didm-b6-massive-news-20261123`, head `6a0336e5cf8e7f52294f518ab437662e3f4869db`, 기준 main `d835d9f495102a6d3244413018db1f9219341716`입니다. 네 파일과 PR 설명·head를 원격에서 대조했습니다. 기사 발행 시각과 직접 수신 시각을 구분하고, 동일 ID의 버전·종목별 감성·페이지 순서를 보존합니다. 원문 링크의 쿼리를 잘라 서로 다른 기사를 같은 주소로 만들던 문제와 커서 처리 문제를 수정했습니다.

제품 시험 18개와 별도 회귀 사례 18개가 Python 3.12 및 3.13에서 통과했습니다. 기술 문서 정합성 검사는 소스 849개·문서 20개에서 통과했고 기존 공개 차단 65건은 유지했습니다. 실제 Massive 수집, 저장소 연결, 역사적 감성의 가용성과 상업 이용 권한은 미확인입니다.

기존 Kalshi 고정 소스는 20번째 페이지에 다음 커서가 있을 때 40개 합성 행에 대해 미완료로 반환합니다. 커서가 소진된 동일 규모는 완료로 반환합니다. 저장된 개별 행에는 배치 단위 완료 플래그가 없으므로 이를 전체 시장의 증거로 해석할 수 없습니다. Atlanta Fed MPT는 공식 파일 헤더·단위·시각 설명이 필요합니다.

T8-5는 소유자가 승인한 증권사 화면 안내의 범위와 KIS·법률 검토 질문을 담은 비공개 초안을 작성했습니다. 실제 주문이나 외부 발송, 공개 구현은 없습니다. 수동 인계 게시 도구 T8-6은 기존 순서를 따릅니다.

Android 빌드 경로·Flet 진입점·GBM 의존성 선언을 재검토했습니다. 소스상 새 차단 결함은 발견되지 않았습니다. APK·실기기와 UI Windows PC7은 계속 확인이 필요합니다. 각 PR의 실행 상태는 아래와 같습니다.

- [#140](https://github.com/xkg4real/quantgen/pull/140) `97152abd` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45055309365) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45055309366) success
- [#141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success
- [#143](https://github.com/xkg4real/quantgen/pull/143) `3b8f39ca` · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054408521) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054408511) in_progress
- [#144](https://github.com/xkg4real/quantgen/pull/144) `6a0336e5` · 원격 재조회 시 확인될 새 CI 결과 대기

## 법인 설립 전 Remaining Work · 2026-11-23T03:30:31+09:00

EODHD 제공 자료 파싱만 main d835d9f로 병합되었습니다. Android와 UI는 이 main을 통합했습니다. 아래 세 PR은 각각 최신 코드와 테스트를 원격에서 다시 확인한 초안입니다. 준법 문서 CI와 전체 Runtime은 별개로 기록합니다.

- [PR #140](https://github.com/xkg4real/quantgen/pull/140) `97152abd` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45055309365) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45055309366) success
- [PR #141](https://github.com/xkg4real/quantgen/pull/141) `a35b2f8b` · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054882429) in_progress · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054882305) success
- [PR #143](https://github.com/xkg4real/quantgen/pull/143) `3b8f39ca` · [Compliance document review](https://github.com/xkg4real/quantgen/actions/runs/45054408521) success · [Runtime packaging smoke](https://github.com/xkg4real/quantgen/actions/runs/45054408511) in_progress

Android 예시 계산·staging과 UI 동일 테마 재적용 수정은 합성 검증을 통과했습니다. 다음은 Android APK와 기기 증거, Windows PC7, Alpaca 전체 CI 및 실제 공급사 권리 확인입니다. 상위 Remaining Work는 계속 열려 있습니다. 자세한 재현 순서와 결제 OA43 증거는 [주간 인수인계](WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md)에 있습니다.

## DIDM · EODHD 입력 검증 코드 병합

[PR #142](https://github.com/xkg4real/quantgen/pull/142)를 main `d835d9f495102a6d3244413018db1f9219341716`에 병합했습니다. 병합 부모는 기존 main `dec979a`와 작업 head `90d3b4b`이고 병합 tree `b10e572badde546a7c8544321490b872611a1291`은 검증한 코드와 같습니다. 두 SHA와 실제 PR 종료·병합 상태를 다시 읽었습니다. Runtime 45043431571의 여섯 작업과 문서 일관성 45043431652가 성공했고 GitHub check-run 8개가 통과했습니다. 별도 Vercel 배포 상태는 실패이며 SESSION_PIPELINE의 제품 코드 병합 규칙을 적용했습니다. 공식 출시는 이루어지지 않았습니다.

EODHD 단위는 제공된 경제 이벤트의 값·시각·예상치 근거 및 페이지 분할 계약까지입니다. 실제 데이터 수집, 발표 전 컨센서스의 역사 버전, 상업 사용권, 모델 검증은 남았습니다. 다음 단위는 같은 main을 기준으로 Alpaca 뉴스 메타데이터를 검증하고, Android PR #141에 최신 main을 통합하는 것입니다. UI #140은 Qt 테마 중복 적용 및 시험 창 정리 보정을 검증 중입니다. 다른 세션은 같은 파일을 중복 수정할 필요가 없습니다.

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

# MERGE_QUEUE — main 병합 순서와 동결 (메인 세션이 관리)

updated_at: 2026-11-21T19:48:44+09:00
전체 업무 체크리스트: `WORKBOARD.md` · 세션 연결 규칙: `SESSION_PIPELINE.md` (2026-11-19 23:00 KST 무렵 소유자 지시)
coordinator: QUANTGEN 메인 Codex (소유자 단일 요청 창구 지정·2026-11-21 승인; 이전 Claude 기록 보존)
freeze: **OFF** — 2026-11-19T01:32:00+09:00 해제. 소유자 F22 완료 보고("F22까지 성공적으로 마무리했습니다."), main `6e077dc`(소유자 `--no-ff` 병합, 부모 `8e026ab`·`13f4dea`), 그 push의 Compliance success, PR #4 merged. (동결 기간: 2026-11-18T19:10:45+09:00 ~ 위 시각)

## 실제4g병합완료·현재4h — 2026-11-21T19:48:44+09:00

**4g DIDM PR138/head6cff → main53e5e723 완료**, exact6Runtime/문서CI/8checks·부모/tree023/ref대조. 공식DIDM-1/DS4a코드·합성만기록, 실API/모델/법률/운영·DS1등미완료. **현재4h KEY45**: 실제main023=준비candidate6cff를대조했고root최종845/20baseline/check·CASコード/새PR/전체CI순서. 지금새활성대기PR없음(역사PR12미변경). UI/K2a는WIP·PC7/OSgo/최종조건보존. 아래시각별문구는이력이다.

## 현재 실제 대기 — 2026-11-21T19:10:18+09:00

4g DIDM PR138/6cff 단일활성대기, 문서/Linux/문법success·Windows전체Runtime진행중. 4h KEY45+candidate6cff local준비83/123/17·독립/20정책/실제845소스검증완료이나 실제4gmain전 새원격code/PR/finalbaseline없음. UI K1d630은원격검증WIP·화면16files36sites·PC7/OSgo/최종UI조건미완료이며 새PR없음. 기존기록은시각별이력으로보존한다.

## 현재 실제 대기 — 2026-11-21T18:14:17+09:00

4g DIDM **PR138/6cff168** 단일활성대기, 문서CI성공/전체Runtime44887223811진행중. 오래된PR12는승인안에기록된이력으로미변경. 4h KEY45는독립local45+미병합6cff준비만허용, 실제4gmain병합전새원격code/PR/finalbaseline없음. K1c b93는검증WIP·18화면39접점/PC7·OSgo·최종UI조건미완료. 기존4fDS-H/code 완료/실OA09부모미완료유지.

## 현재 차례 — 2026-11-21T17:35:29+09:00

4f DS-H/code PR137→main6d25a33 완료, 실제OA09/홈실연결/부모는 미완료다. **지금4g DIDMabd**에 실제최신main을 합쳐 source/20정책/최종baseline·합성/독립검토 후 PR한다. 현재새대기PR없음. 무조건ref이동/force/rebase없음. 다음4hKEY45db, UI/K1b053보존·PC/OSgo유지. 아래시각별기록은이력이다.

## 최신 부분 인계 — 2026-11-21T14:54:13+09:00

4e OS136→main72a 완료. 4f **DS-H 초안PR137/head4973111** 유일 대기, 문서CI/독립검토PASS·전체Runtime44871383992진행 중(14:53판독, 실패0). OA09 실제진단/홈 실연결과 code-only 기술 통합 조건을 구분한다. 후속 배정·소유자 중앙승인 안에서 전체 필수통과시 code범위만 ready/merge 가능하며 parent DS-H/실제진단 완료로 확대하지 않는다. 다음4gDIDMabd→4hKEY45db, 최신main후 최종20정책/CI. UI/K1b053은WIP이고 새PR없음·PC/OSgo필수. 아래는 이력이다.

## 현재 차례 — 2026-11-21T14:36:47+09:00

4e OS-F2 PR136→main72a055f 완료. **4f DS-H 초안 PR137, head4973111**이 유일한 대기 PR이다. 최신 main의 부모/정확5본문·tree·ref를 확인했고 합성172/준법47/실제809소스·20문서 정합성 PASS(중복 합산X). 전체 Runtime44871383992 진행 중·Compliance44871383936 성공. OA09 실제 진단 미제출과 원래 진단 뒤 조건은 보존하며 draft 생성으로 면제/완료를 뜻하지 않는다. 독립 최종 검토 PASS를 받았으며 전체 CI 및 조건 대조 전 main 병합하지 않는다. 이어4gDIDMabd→4hKEY45db; 다른 새 PR은 열지 않는다. UI822/K1ad2는 WIP이며 실제 PC/OSgo 조건 유지. 아래 시각별 기록은 이력이다.

## 중앙 후속 관측 — 2026-11-21T14:11:37.000+09:00

4e PR13664ff58e는유일대기PR, Windows3.12한환경만최종진행중이며나머지5Runtime/Compliance성공. 통과전병합없음. 4fDSH7ce의최종source-review20재검토입력준비/실구조오류0, OA09실제진단은미완료그대로다. 4gDIDMabd10c6→4hKEY45db2be순서유지. UI822와후속K1a d2는격리WIP원격보존/독립검증이며새PR없음·5/6/7기존PC/OSgo조건을지운것아님. [이번인계](WEEKLY_HANDOFF_2026-11-21_1bfaa7d8.md).

## 최신 병합 완료·다음 차례 — 2026-11-21T14:21:16.000+09:00

**4e OS-F2 PR136 → main 72a055fb05a7e63b641bad07423503fa56e7b4b8 완료**, 전체6Runtime/Compliancesuccess·검사tree동일readback. 실제owner자료이전/출시를완료로세지않는다. **현재4f DS-H7ce**의최종baseline/검증·code-only draftPR준비차례, OA09실제진단/원문조건충돌유지. 이어4gDIDMabd→4hKEY45db, UI/K1은원격WIP·새PR없음. 아래과거OS대기문구는이력이다.

## 최신 담당 전환 — 2026-11-21T12:10:34+09:00

사용자가 DIDM·UI 인계완료후메인Codex총괄·5하위담당을승인했다. 과거의별도세션브랜치는보존하고중앙담당이격리gpt브랜치에서작업한다. [진행표](CENTRAL_CODEX_STATUS_2026-11-21.md). UI7화면PC실행확인·OSgo·실제연구/권리/배포조건은유지. OS-F24e가현재PR차례이며다른PR은독립구현/검증준비만한다.

## 중앙 관측 — 2026-11-21T12:33:42+09:00

4e OS-F2 [PR136](https://github.com/xkg4real/quantgen/pull/136) **64ff58e**가현재유일병합대기PR이다. 최초74dce42의Windowsfixture실패수정후새Compliance성공/새Runtime대기, 통과전병합금지. DSH7ce3791·DIDMabd10c6·KEY45db2be는원격보존/검증됐으나위순서대로최신main·준법·필수CI뒤PR한다. 기존Claude행의과거중단문구는이력으로보존한다. [중앙누적인계](WEEKLY_HANDOFF_2026-11-21_a3da2627.md).

## 지금 순서

| # | 항목 | 브랜치·PR | 상태 | 병합 |
|---|---|---|---|---|
| 1 | ~~R3 outage 기록 (GPT)~~ | PR #122 | **병합 완료 main `f058145`** (11-17 23:1x KST) | 메인 |
| 2 | ~~UI 세션 PR (시장 메인·지표 결론부)~~ | PR #124 | **병합 완료 main `8e026ab`** (⑬-2/market-hub/main) | 메인 |
| 3 | ~~⑦-1 Step 10 마감 기록~~ | 연구 브랜치 | **완료 `efe5bb2`** (11-17 22:06 KST) | — |
| 4 | ~~P3: main → 연구 브랜치 병합, 소유자 F1~F22~~ | PR #4 | **완료** main `6e077dc` (⑦-2, 11-19 01:32 KST freeze 해제) | 소유자 F21 |
| 5 | ~~결정 기록 PR (11-17 소유자 답, 자진 보고)~~ | ⑦-1/rulings | **완료** `7c33955` | 메인 |

## F21 뒤 — 지금 순서 (2026-11-19 01:40 KST 메인이 정함; 준비된 것부터)

| # | 항목 | 브랜치·PR | 상태 |
|---|---|---|---|
| 1 | ~~⑦-2/a 병합 뒤 main 정리~~ | PR #126 | **병합 완료 main `56fe32a`** (2026-11-19 03:08 KST, CI 전부 녹색) |
| 2 | ~~OS 작은 PR~~ | PR #127 | **병합 완료 main `c28b1d7`** (2026-11-19 05:09 KST, CI 전부 녹색) |
| 3 | ~~KEY-2~~ | PR #128 | **병합 완료 main `3249af7`** (2026-11-19 10:40 KST). code_sha256 → `10c27010…` |
| 3b | ~~KEY-2/b~~ | PR #129 | **병합 완료 main `ca5da08`** (2026-11-19 12:18 KST) |
| 4 | ~~정책 문서 PR-1~~ | PR #130 | **병합 완료 main `edbe9f7`** (2026-11-19 15:03 KST). PR-2(계정 서비스 설명)는 AWS 풀·웹 계정 화면 뒤 |
| 4a | ~~CI 겹친 실행 자동 취소 + GH-1 기록~~ | PR #131 | **병합 완료 main `ab24dec`** (2026-11-19 16:58 KST) |
| 4b | ~~KEY-3 (게이트웨이)~~ | PR #132 | **병합 완료 main `9f76b07`** (2026-11-19 19:07 KST) |
| 4c | ~~KEY-4~~ | PR #133 | **병합 완료 main `8445187`** (2026-11-20 03:27 KST, CI 10개 녹색, 메인 검토 4회) |
| 4d | ~~메인 문서 PR (CLAUDE.md Session pipeline, OWNER_RULINGS_LOG 2026-11-20)~~ | PR #135 | **병합 완료 main `fa78df1`** (2026-11-20 03:4x KST), 원장 SESSION-PIPELINE |
| 4d' | ~~KEY-4/a 계정 문서 고침 (F1–F9, OA-42·OA-44 반영, 자체 시험 1줄)~~ | PAYMENTS PR #134 @ `aa4be94` | **병합 완료 main `f065ec9`** (2026-11-20 05:36 KST), CI 7개 녹색, 원장 KEY-4/a (handoff 40b9378) |
| 5 | UI 7쪽 + PySide6 준비 | UI `claude/friendly-bardeen-r6xe8f` | 소유자 실행 확인 뒤 (UI 세션 브랜치는 아무도 고치지 않음) |
| 6 | PySide6 전환 (`pyqt6_to_pyside6 --apply` + `switch_day.py --apply`, 화면 문구 3곳은 UI 세션) | OS | 5 뒤 (OS 세션 제안 순서: UI PR → 전환) |
| 4e | ~~OS-F2 (~/.nextgen → core.app_paths.user_data_dir, config.py 포함 → Nautilus 지문 bcaf33d9…) + OS PySide6 종료 원인 기록(5커밋, 작업 A: PySide6 320회 abort 0)~~ | gpt/os-f2-data-dir-20261121@64ff58e · PR136 → **main72a055f**; 이전준비: OS `claude/os-f2-data-dir-20261120` @ **`e44c48e`** (main f065ec9 합침, 충돌 없음) | **코드병합완료 2026-11-21T14:21:16.000+09:00**; 실제owner이전미검증. 이전상태: **병합: OS** (2026-11-20 05:40 KST 메인). OS가 최신 main `f065ec9` 합침 → 기준선(source-review.json) 마지막에 갱신 → `--check` PASS → PR. 메인 독립 검토 뒤 CI 녹색이면 병합 **11-20 05:4x OS 세션 주간 98%로 중단: 2단계(CRLF·엔진 4파일)까지 끝, 3~6단계(회귀·code_sha256·기준선·PR) 남음 → OS_SESSION_CURRENT 6절** |
| 4f | ~~DS-H/code 홈 지표6종 데이터 계약·코드 통합~~ (OA09 실제진단/전체DS-H부모는 별도 미완료) | gpt/ds-home-indicators-20261121@4973111 · PR137 → main6d25a33 | 코드 통합 완료 2026-11-21T17:35:29+09:00; 전체6Runtime/문서CI/독립PASS·검사tree정확일치. 이전준비7ce 보존 |
| 4g | DS·DIDM 코드 통합(실제 API/모형/운영·부모는 별도) | gpt/data-source-didm-20261121@6cff168 · PR138 | 현재차례: 최종844소스/20정책·합성/독립/문서CI PASS, 전체Runtime진행 중; 이전abd준비보존 |
| 4h | KEY-5/a gateway 준비 3건 (data.kis_stream 입구, kis_workspace 순수 값 목록, QuoteFeed 하위 클래스 공용 모듈) | PAYMENTS `gpt/key5a-fixes-20261121` @ `45db2be73e7f87954cab6782ca4b2717dc97fc62` (dc936d4 기반 수정·검증; PR차례전) | 4g 뒤 (11-20 메인이 정함). 메인 검토 결과 `plans/2026-11-20/KEY5A_REVIEW.md`: 주요 2건(M1 feed가 지운 키·막힌 FMP 계속 사용, M2 _refresh_krx 비원자적 fail-open) PR 전 고칠 것 |
| 7 | KEY-5 (4f 뒤) (화면 쪽 22파일/44곳 + quantgen_desktop/paper.py, 키·연결 화면) | PAYMENTS 요청문(handoff plans/2026-11-20/KEY5_UI_REQUEST.md) + UI 구현(소유자 경유) | 6 뒤 권장, 4e 뒤 |
| 8 | ~~DS·DIDM~~ → 4g로 당김 (11-20 메인) | DS | — |
| 제안 | 정책 문서 PR-2 (계정 서비스 설명) | 메인/PAYMENTS | AWS 운영 풀 + 웹 계정 화면 뒤 |
| 미정 | GH-2 정리 PR (test_npu.py, mindmap/, launch.json, _backup/ 태그 뒤) | 메인 | 빈 자리에 |

한 번에 PR 하나만 main 병합 대기에 둡니다(모두 `docs/compliance/source-review.json`을 바꾸므로 앞 PR이 병합된 뒤 최신 main을 합치고 기준선을 다시 갱신).

아래 목록은 위 순서의 근거입니다.

### F21 뒤 (근거)

- ~~GH-1: CI 줄이기 / Windows 검사를 소유자 PC로 + 비공개 전환~~ — **닫힘 (2026-11-19 15:08 KST 소유자 "두번째꺼 (비용부담 없음)로 하겠습니다"): 공개 유지.** runtime-smoke 겹친 실행 자동 취소만 적용(PR #131), Windows 3버전 유지.
- OS 작은 PR(도구·`app_identity`·패키징 초안, 공유 파일 `core/app_paths.py`·`runtime-smoke.yml` 경로·`platform-build.yml`) — **F21 뒤 첫 자리**, 그다음 OS: PySide6 전환 PR (D9 나안). P3 전에는 받지 않음: P3 병합 후보(`local/p3-candidate` 끝 `f0c8872`)가 main `7c33955` 기준이라 main이 바뀌면 병합과 전체 검사를 다시 해야 함. `qa/` 두 파일을 휠에 넣을지는 지금 그대로 두고 그 PR에서 근거와 함께 제안.
- P3 상태 (2026-11-18): 병합·전체 검사 끝, push 보류 — 코드 지문 판정(P3-가/나/다) 소유자 답 대기.
- 정책 문서 PR (메인, D11 소유자 답 Q1~Q3 반영) — F21 뒤 앞쪽. 소유자 원문(2026-11-19 00:19 KST, PAYMENTS 세션; 메인이 그 세션 대화 기록에서 확인): "Q1 답변 : 예, 다만 제가 법인 설립 설립이 완료되었다고 여기에 말하는 순간 바로 해당 법인 명으로 수정 가능하도록 해주세요 / Q2 답변 : 일단 contact@quantgeneration.com으로 하겠습니다. 현재 웹사이트의 구조도 이렇게 되어있습니다. / Q3 답변 : 예". 값: 브랜치 `claude/payments-keys-20261117` @ `687bf65` `docs/commercial/accounts/ACCOUNT_SETUP.md` 4부 (운영자 개인·"(주)" 없음, 책임자 같은 사람, 메일 contact@quantgeneration.com, 최소 연령 14/유료 19). 대상 문서 01·02·04·06·07·08·16·17·18·20, release-profile.json.
- KEY-2 → KEY-3 → KEY-4 → KEY-5 — **D7-G 소유자 승인됨 (2026-11-18 14:15 KST, OS 세션에서, 원문: "그러면 D7-G의 방식대로 진행하겠습니다")**. 브랜치 작업은 지금 시작 가능, main 병합은 F21 뒤 이 순서.
- DS·DIDM PR — 각 세션 차례가 오면.

## 규칙

- 하부 세션은 자기 항목이 이 표의 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 엽니다 (GitHub는 공개 유지 — 2026-11-19 소유자 GH-1 결정. 그래도 PR 하나씩: 모두 `docs/compliance/source-review.json`을 바꾸므로).
- 병합 버튼은 메인이 누릅니다 (CI 통과 시, merge commit).
- UI/UX 세션과 웹사이트 세션의 브랜치·인계 파일은 아무도 고치지 않습니다. 그 세션에 줄 요청은 소유자를 거칩니다.
- **owner_confirmed 다시 쓰기 (2026-11-19 메인이 정함):** 다음 Nautilus 기록 실행 직전에 한 번만(OS-F2가 config.py를 또 바꾸므로 지금은 하지 않음). 소유자가 최신 main 클론의 보통 앱 Python으로 `python -B -m tools.nautilus.runner --fingerprint --table <두 표>`(읽기만) → 각 표의 "owner_confirmed" 한 줄만 출력된 form으로(UTF-8, BOM 없음; host_fingerprint는 같으면 그대로) → 브랜치 `owner/nautilus-confirm-<YYYYMMDD>` + PR(main 직접 push 금지) → 메인이 Linux에서 code_sha256 재계산해 대조, CI 녹색이면 병합. 그날 이 표에 자리를 둠. Claude는 이 줄을 쓰지 않음.
- **코드 지문 주의 (2026-11-18):** `config.py`는 Nautilus 브리지 code_sha256의 입력입니다. P3-가(소유자 11-18 "1번 : (가) 승인")로 지문은 ec72fab3…가 되고, F21 뒤 KEY-2(`config.py` 변경)가 들어가면 또 바뀝니다. 그런 PR은 본문에 이 사실을 적고, 다음 기록 실행 전에 소유자가 owner_confirmed 두 줄을 새로 씁니다(Claude는 쓰지 않음).
