## K2b 파생상품 준비 상태 입구 전환 — 2026-11-21

K2a `7fb6b032e2ab24c681700120ab0abd5b6dd5c6e3`에서 이어지는 승인 ID20 코드 WIP입니다. `ui/derivatives_page.py`의 import와 builder 내부 준비 상태 조회 두 줄만 바꿨습니다. 같은 위치에서 기존 `gateway.keys_ready("kis_quote")`를 사용하며 hidden Board, 명시 선택, 기존 선택 유지, 오류 전파와 인자·계산·문구·레이아웃을 보존합니다. LF196행과 함수 본문 중 나머지 부분도 유지했습니다.

- 원본630에 고정한 before 14사례와 변경 후 14사례를 작성자 및 독립 검토자가 각각 재현해 같은 불변 semantic oracle과 일치함을 확인했습니다. 실제 gateway 진입은 builder별 1회/합계14이며 config 정상 bool13·합성 오류1·가짜 메모리 credential GET20을 구별합니다. 키 존재를 실제 공급사 연결·라이선스 검증으로 해석하지 않습니다.
- 실제 import 73개의 집합은 동일하며 변경된 import 원문의 지문은 대상 파일1개뿐입니다. 새 후보의 실제 부모7fb와 역사적 before 원본630을 분리해 기록하고, 원본 작성기·oracle·manifest와 최초 실패/정정 이력을 보존했습니다.
- 기존 공개 회귀 `GroupedNumbers.test_derivatives_paths_are_grouped_and_read_back` 1개를 수정 없이 실행해 수집·실행·기록 각각1, 실패·오류·skip0을 확인했습니다. 가짜 snapshot이 즉시 FICCError를 내는 경로에서 Paths 기본3000·입력12000 전달과 오류표시를 확인합니다. builder-only 14의 worker0과 이 가짜 worker 경로를 구별하며, 이 수들을 합산하지 않습니다.
- 공개 회귀의 실행 중 쓰기는 임시 fixture 영역에 제한했고, source412 및 고정 증거의 실행 전후 raw SHA·Git blob·mode를 대조했습니다. 폰트 탐색 `fc-list --help` 1회는 시작 전에 거절됐고 실제 subprocess 실행0입니다. 이 결과는 실제 GUI·Windows·소유자PC·모델·공급사/API·동결연구·원장 검증을 뜻하지 않습니다.
- ROOT가 실제 사라진 `config.kis_ready` 항목1개만 known에서 제거했습니다. 최종 경계13 PASS, new/gone/errors=0, 남은 화면13파일32접점과 frozen core feed1파일입니다. ceiling22/44·SCREEN_FILES22·frozen 내용은 불변입니다. 공개 입력412개 중 부모7fb 대비 변경은 제품1개·known1개이며 나머지410개와 mode는 동일합니다. 원래 source1/known6792 시점의 검증·manifest는 새 최종 freeze와 분리해 보존했습니다.

공개 테스트와 준법 baseline을 수정하지 않았습니다. 전체 UI/KEY5, 최신 main·선행 KEY5a 통합, 최종 준법/source-review·전체 UI CI/PR·소유자PC7/OS go는 여전히 미완료입니다. 웹사이트 영향 검토 큐는 NOT_SENT이며 실제 전달·반영·배포는 미실시입니다. 원본과 앞선 후보 이력은 아래에 보존합니다.

## K2a 금리·구조화의 기존 gateway 입구 전환 — 2026-11-21

K1d `630e9ba44d84867b01dddce55a5785acc7958269`에서 이어진 코드 WIP입니다. 승인된 KEY-5 요청 34·35·44의 `ui/rates_page.py`와 `ui/structuring_page.py`에 한정해 기존 FICC facade를 원래 조회 시점에 사용합니다. 기본 앱은 계속 native PyQt이며 Flet 화면은 기존 기능 유지 범위입니다. 원래 인자·단위·기본 일수·계산·한국어 문구·배치와 줄바꿈을 보존했습니다.

- 직접 import 3개를 제거하고 loader 표현식 5곳을 `gateway.ficc()`로 연결했습니다. 실제 앱 콜백 4곳과 정적 검토만 수행한 CLI self-check 1곳을 구별합니다. CLI self-check를 실행했다고 주장하지 않습니다.
- 공개 테스트 5파일의 patch 대상 11곳만 실제 조회 위치에 맞췄습니다. 테스트 사례·assertion·fixture의 의미는 유지했습니다. ROOT가 known 목록에서 해당 직접 import 3개만 제거했으며 ceiling 22파일/44접점과 frozen feed 항목은 보존했습니다.
- 검증은 서로 합산하지 않습니다: 기존 공개 회귀 15 PASS, 독립 의미 비교 16 MATCH, 별도 차단 시나리오 12 PASS, 최종 경계 13 PASS. 독립 비교는 합성 provider leaf 15개와 분석 호출 10개를 구별하고 실제 gateway의 off/company/invalid 경로에서 provider·원격·분석·차트·네트워크 호출이 발생하지 않음을 검사했습니다.
- 최종 스캐너 new/gone/errors=0. 남은 직접 호출은 frozen core feed 1파일과 화면 14파일/33접점입니다. 최초 ceiling과 SCREEN_FILES 22개를 낮추지 않았습니다. 보존한 공개 입력 412개 중 404개는 원본과 동일하며 변경은 제품 2개·공개 테스트 5개·known 1개입니다.
- 실제 앱 import 비교는 원본 93개에 기존 `core/app_identity.py` 1개가 gateway의 지연 import로 추가된 누적 94개입니다. 해당 파일의 원본 SHA를 확인하고 출처 메타데이터만 별도로 검증했습니다. 불변 before writer·golden과 계산/인자/사례 비교는 유지했습니다.
- 최초 검증 실패와 guard 보완 이력을 비공개 증거에 보존했습니다. 실제 연구 함수·모델·원장·keyring·외부 API를 실행하지 않았으며 폰트 탐색 subprocess 1회는 시작 전에 거부했습니다. 실제 GUI 렌더링·소유자 PC·OS go·공급사 또는 법률/라이선스 검증을 완료로 표시하지 않습니다.

기존 UI/main 통합, 최종 source-review, UI PR/필수 CI 및 병합은 아직 남았습니다. KEY-5 전체와 UI 부모 항목은 미완료입니다. 웹사이트 영향은 원격 데이터 입구의 동작 일치 여부 검토 대상으로 큐에 보존하며, 지원되는 다른 대화 전송 도구가 없어 전달·실제 웹사이트 반영·배포는 미실시입니다. 본 작업은 배포하지 않습니다.

## K1d 랭킹·QScore의 기존 gateway 입구 전환 — 2026-11-21T19:04:00+09:00

K1c b93fed6609af27c0b73ba41d572266a814c57768 뒤의 별도 보존 후보다. 승인 KEY5 ID10·11·15만 처리했으며 전체 UI·KEY5 또는 main 병합 완료가 아니다.

- market_rankings의 순수 해외 상세 상수 조회·기본 서비스 생성과 qscore의 기본 서비스 생성 3접점을 같은 위치에서 기존 gateway.provider('data.kis_workspace')로 옮겼다. 명시 false-y 주입·락/캐시·생성 오류/재시도·no-arg 생성·shared client identity·키 snapshot/명시 reload를 보존했다. 모듈·fixed_local 정책·키 저장/API는 바꾸지 않았다.
- 독립 고정 before factory13 MATCH(생성시도6·서비스4·ready6), 실제 gateway 대상8진입·참조1·기존 import1을 분리 확인했다. 정확한 module 위치인자/source=None·workspace 모듈 identity·rankings 락 안 조회 및 대상 route/table/order/remote/data/network0을 확인했다. factory13은 GUI13화면이 아니다. writer/oracle/comparator와 before 증거를 보존했고 project import 전 외부 bootstrap guard로도 재생했다.
- 별도 기존 회귀18·경계13 PASS(실패/오류/skip0), 제품2파일 Python3.10 grammar PASS. 기존 market-cap 합성 회귀의 FMP route1/table1은 target workspace route0과 별도다. 초기 keyring 미설치·희소 routes 입력 관련 private 하네스 실패도 보존했고 공개 tests/assertions는 변경하지 않았다.
- actual scanner의 소멸 known3만 삭제했다. 신규/누락/오류0; 잔여 총17파일은 동결 core feed1 + 화면16파일이며 화면36접점이다. ceiling22/44·SCREEN_FILES22·FROZEN 불변. 기존 source399 중 target2 외397은 불변이며 추가 app·기존 시험/helper·정적 routes는 exact b93 공개 입력이다.
- 최신 선행 main/G1–G3 합침·전체 UI 회귀/CI·최종 준법 baseline·UI PR·소유자 PC7화면/OSgo는 미완료다. 실제 provider/API·권리/법률·연구 성과·웹 적용/배포 근거를 추가하지 않았다. 실제 UI PR에서 웹 영향 기록과 전달·적용 증거를 별도로 남긴다.


---

# Central UI integration candidate — 2026-11-21

This work-in-progress branch preserves Claude UI `414eceb90ce42e67113f9cc592229f3f36f37c83` together with main `f065ec92dbce1e1b34e4adb0b6dbed724305a2f4`. It is not a merged release or a replacement for the owner PC acceptance gate.

The merge retains main's number formatting, restores the approved compact Korean/English portfolio empty-state instructions, and preserves both sides of the FACTS history. The redesigned System presence list obtains its existing presence-only loaders through `core.gateway.status_loaders()` in the original KRX/FICC/crypto/quant display order. It still returns only id, label, ready, setting names and note. No key values or probe results are invented.

Bounded Linux validation: 14 distinct selected UI cases passed across the recorded runs, with initial fixture/selector mistakes and the corrected portfolio regression retained in the evidence. The System bridge passes the unchanged 13-case gateway boundary suite (22 files/44 existing sites) and four selected presence/bilingual cases; independent before/after function checks pass three cases. These groups overlap and are not an entire UI-suite pass. Seven routes have Korean wide and English narrow offscreen captures using synthetic inputs. They do not establish Windows, DPI or live-provider results.

`docs/compliance/source-review.json` deliberately preserves the main baseline at this checkpoint. It is stale for the integrated UI and must be reviewed and refreshed on the final dependency tree. There is no source/document-consistency PASS claim for this candidate. The original Qt binding and the approved eight top-level pages/nine market categories remain unchanged.

Before a UI merge: incorporate the latest ordered OS-F2 → DS-H → DS/DIDM → KEY-5/a prerequisites, complete the final source/document review and required CI, record the UI PR website impact, and obtain the existing seven-page owner PC confirmation. The later PySide6 switch still requires its OS go. Full KEY-5 routing and the DS-H home adapter remain distinct unfinished work. Website delivery, application and deployment are unverified.

## KEY-5 K1a: Home and market-summary default series loaders

The separate K1a candidate changes only the default series entry points in `home_view.load_market_history` and `market_summary.production_series` to the existing FICC gateway. Explicit loader injection, source, days, observed values and dates, Home's authored error reason and Summary's exception propagation remain intact. No data-layer model, key policy, route policy, app entry or frozen engine file changes here.

The original main oracle and a separate pre-gateway UI oracle stay fixed. The approved redesign has 23 pre-existing text/period-display differences from main; request order, values, sources, units, observation dates and reason codes have zero differences. After K1a, all ten UI-oracle cases match the UI baseline with actual candidate module paths/hashes checked. The new seven-case public module passes, fourteen related Home/Summary cases pass, and independent review verifies twelve real gateway entry scenarios under synthetic off/company/invalid-route conditions with zero provider/network calls. These groups overlap; they are not a full KEY-5/platform run. The new regression suite fails on the old two functions; the explicit-off example previously reached the fake leaf twice and now reaches it zero times.

The boundary inventory removes exactly the two obsolete direct-import exemptions and now contains 20 screen files/42 sites plus the unchanged frozen feed entry. Its existing 22-file/44-site maximum and screen-file constants stay unchanged; restoring either direct import is a new violation. All thirteen boundary tests pass. Runtime CI includes the new public module in the existing native/offline command after Qt installation, with existing tests and security/environment settings retained.

This remains an unmerged work-in-progress candidate. The final source-review baseline and full required CI are pending. Sparse test assets produced font/SVG warnings, so the fourteen-case semantic run establishes no new pixel, owner Windows or live-provider result. Remaining 42 screen sites, system route/state presentation, DS-H UI integration, owner PC acceptance, OS go, website delivery and deployment remain separate unfinished work.

## KEY-5 K1b: automatic derivatives-board readiness

This follow-up to K1a changes only KEY5 ID13 in DerivativesPane.automatic_board: the existing config readiness check is obtained through core.gateway.keys_ready("kis_quote"). That source is already fixed-local. The source/key policy, automatic kis/synthetic selection, hidden and explicit selections, request fields and pricing/model functions remain unchanged.

The original target file and three selection/request functions match immutable main72a and K1a d2. A separate immutable before oracle captures nine real Qt UI steps and five readiness reads, including False/True/False and explicit overrides. After the bounded edit, all nine steps match; all seven request fields and explicit-override zero-read behavior are preserved. Independent runtime observation confirms five actual keys_ready entries with source kis_quote, zero route/table reads and zero provider/network calls inside those entries. One existing empty-source data.net session-module resolution during imports is outside the entry scope and is not represented as a global provider-call-zero result. Initial observer classification failures were retained and corrected without changing product, golden or comparator.

Seventeen existing selected tests pass with zero failures/errors/skips: the two existing native derivatives cases, fixed-local/dynamic configuration contracts and thirteen unchanged boundary cases. These checks overlap other recorded suites and must not be summed. No public test, CI command, ceiling or frozen feed entry changed. The known inventory removes exactly one obsolete market_tools exemption, leaving nineteen screen files/forty-one sites plus the unchanged frozen core entry.

The separate branch is prepared from K1a d2; it is not a final ordered dependency merge or a clean local checkout claim. It remains WIP with final baseline/full required CI, G1-G3/full KEY5 PR order, owner PC confirmation, OS go, website impact/delivery and release gates outstanding. The earlier fourteen-case candidate record is history; the central handoff separately records sixty-four selected UI regression passes on the pre-K1a UI822 source, not on this entire new branch.

## KEY-5 K1c: the two shared-service factories

This follow-up to K1b changes only KEY5 request IDs1/2 in app.py: the function-local MarketDataService imports in _production_card_router and _ProductionProfileLoader.__call__ use the existing gateway.provider('data.kis_workspace').MarketDataService. Lookup stays at its original location before the profile lock, with the same no-argument constructor. The source is the already fixed-local kis_quote; no new API, routing/key policy or automatic credential rebuild is introduced.

The target factory/init/call ASTs match base053 and main72a although their full app files differ. An immutable before oracle records fifteen factory/service contract cases, not GUI-screen cases: real MarketDataService/KISClient/KISMarkets/router identities, deferred construction, one cached service with fresh routers, four concurrent first calls creating one service, constructor error/lock release/retry, and existing readiness snapshot/explicit reload behavior. After K1c, independent replay matches all fifteen cases, with six real services, seven constructor attempts and ten readiness/reload leaf evaluations. Profile/pricing/data-loader bodies are blocked.

An independent actual gateway call-through observer confirms fifteen target entries(card2/profile13) with exact data.kis_workspace/source=None; fixed-local route/table/order/remote lookups and target data/network calls are zero. Two separate existing module resolutions during imports are outside that target scope; no global provider-zero claim is made. All121 imported-source hashes and original golden/writer/metadata remain checked. Thirteen negative comparator probes were used during independent before review; they are not additional factory cases.

Fifteen existing boundary/fixed-local/current-service regression tests pass with zero failures/errors/skips. This is a separate overlapping suite, not a thirty-case aggregate. No public test or CI was added/changed. The known inventory removes exactly the two obsolete app.py imports: eighteen screen files/thirty-nine sites plus the unchanged frozen core entry remain, with the original22-file/44-site ceiling and screen constants unchanged. Root also verified exact two import substitutions and no other product-byte change.

This branch remains preparation from K1b053, with final ordered dependencies, source-review baseline, full required CI, UI/KEY5 PR, owner PC confirmation, OS go, website receipt/application and release unfinished. It establishes factory behavior and synthetic regression only; full GUI/Windows/live-provider results are not claimed. Previous candidate/checkpoint sections remain history on their stated source versions.
