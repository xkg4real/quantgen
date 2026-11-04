# A3 설계 초안 (UI-9, UI-11b, UI-12)

> **상태: 미검증 초안 (handoff 자료).** 2026-11-05 Claude 세션이 주간 사용량 한도로 멈출 때 백그라운드 워크플로 결과를 그대로 옮겼습니다.
> 소유자 승인 전이며, 반박 검토(challenge) 단계 전에 멈췄습니다. 본문의 `/tmp/claude-0/...` 경로는 그 세션의 임시 폴더라 이제 열 수 없습니다.
> 이 폴더는 main에 병합하지 않습니다. 확정본은 새 PR에서 `docs/product/` 아래 정식 문서로 만듭니다.

# A3 설계 문서: UI-9 · UI-11b · UI-12 (Native PyQt6, quantgen_desktop/)

기준 트리: s10 516953a. `git diff faf9f3b HEAD`가 비어 있어 main faf9f3b와 내용이 같습니다. 이번 조사는 읽기 전용이었고, `git status --short`는 처음과 끝 모두 비어 있었습니다.
표기:
- [읽음]: 제가 그 줄을 직접 읽었습니다.
- [측정]: 조사 스크립트(A3 sweep, UI-12 sweep)가 오프스크린으로 실행해 잰 값입니다.
- [미확인]: 읽지도 실행하지도 않았습니다.

스크린샷 폴더(아래 경로는 모두 이 폴더 안에 있습니다): /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/

---

## 0. 질문에 대한 답: A3와 A1을 동시에 진행할 수 있나요?

네, 할 수 있습니다. 다음 네 가지 조건을 지키면 됩니다. 자세한 내용은 file_ownership에 적었습니다.

1. **두 작업을 시작하기 전에 준비 커밋(P0)을 하나 먼저 넣습니다.** 화면은 하나도 바뀌지 않고, 두 트랙이 서로의 파일을 건드리지 않게 이음매만 만들어 둡니다.
2. **파일마다 담당 트랙을 하나로 정합니다.** 나누는 기준은 "말은 A1, 배치는 A3"입니다.
   - A1: 용어, 번역, 상태어. 번역 목록(catalog)과 해설 모듈, 각 분석 화면(pane) 파일을 맡습니다.
   - A3: 레이아웃, 접힘, 칩, 패널. app.py, bonds.py, tools.py, chart_study.py, typography.py와 새 파일을 맡습니다.
3. **세 파일만 줄 범위로 나눕니다.**
   - app.py 1002-1009는 A1입니다.
   - strategy.py 18-21은 A3입니다.
   - bonds_portfolio_narrative.py의 `bond_notes()` 함수는 A3입니다.
4. **A3 일부(A3-b)는 A1을 병합한 뒤에 합니다.** A1이 번역하는 파일(시장 차트, 종목 프로필, 포트폴리오, ETF 입력 설명)의 화면 정리가 여기에 해당합니다.

그리고 두 트랙이 쓸 말은 P0에서 소유자가 승인하는 **용어 기준표 v0**(금융 용어, 상태어, 단위어 25-40개) 하나로 맞춥니다. 그래야 A3가 새로 쓰는 문장도 A1과 같은 단어를 씁니다.

---

## 1. 공통 원칙

**A3 문자열 규칙**
- A3가 새로 만드는 화면 문자열(패널 제목, 접힘 제목, 칩, 버튼)은 영어 원문을 키로 씁니다. 한국어는 새 번역 목록 `quantgen_desktop/reading_language.py`에 둡니다. 이 파일은 A3 담당이고, P0에서 translations.py에 연결합니다.
- A3는 app.py 같은 곳에 있는 **한국어 원문 문자열을 그 자리에서 고치지 않습니다.**
  - 이유: 지금 Native는 한국어 원문을 translations.py의 짝으로 거꾸로 찾아 영어를 보여 줍니다(EN[ko]=en, translations.py:592-595 [읽음]). 한쪽만 고치면 영어 화면이 깨집니다.
  - 그래서 영어 키로 바꾸고 짝은 reading_language.py에 넣습니다. 쓰이지 않게 된 옛 짝은 A1이 정리합니다.
- **금융 용어 라벨의 한국어는 A1이 씁니다.** 예: 채권 표 항목명 'Macaulay duration · years'. A3는 P0에서 영어 키 목록만 확정합니다.

**표시와 원문 분리**
- 표시는 바꿔도 원문은 그대로 둡니다. 쓰는 장치는 기존 `UiLabel.localized_text` / `display_variants`입니다(localization.py:24-27, bonds_portfolio_narrative.py:168-171 [읽음]).
- `source_text`, 내보내기(`self.sections`, `exports.report`), 실행 기록(run record), AI 해설에 보내는 자료는 바꾸지 않습니다.

**모든 항목에서 바뀌지 않는 것**
- 숫자, 판정(verdict), 연구 결과, 내보내기 안의 영어 원문.
- 글자 크기 체계: caption 12px, 본문 14px, heading 18px. tests/desktop_typography_acceptance.py:326-327이 고정합니다 [읽음].
- PANEL_DEPTH 색값: typography.py:30-33. 테스트 :345-348이 고정합니다 [읽음].
- 그림자 효과 금지 규칙(QGraphicsDropShadowEffect): typography.py:27-29, 테스트 :325 [읽음].
- ChartStudy의 2:1 분할과 820px 기준(chart_study.py:7, :17 [읽음]).
- 툴팁에 들어 있는 출처·시각 정보(PR #71).
- AI 동의 절차(commentary.py).
- Flet 브라우저 앱. 이번 A3에서는 바꾸지 않습니다(open_questions 8).

---

## 2. UI-9 · 설계/검증 화면 오른쪽 설명

### 2.1 현재 상태

스크린샷:
- 1360px 전체: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_full_ko.png (영어 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_full_en.png)
- 결과 영역: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_result_ko.png
- 1000px: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_1000w_full_ko.png
- 측정값: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/a3_measure_ko.json

문제는 다섯 가지입니다.
- **배치 버그** [읽음]: app.py:575 `inner.insertWidget(0, ChartStudy(...))`가 panel()이 넣은 제목(app.py:144-145)보다 위에 차트를 넣습니다. 그래서 "분포와 근거" 제목이 차트 아래에 나옵니다.
- **오른쪽 설명이 한 덩어리입니다** [읽음]: muted 라벨 하나(app.py:573)에 13줄을 "\n"으로 이어 붙입니다(app.py:909-930). 이 안에는 다음이 섞여 있습니다.
  - 공급사와 관측 기간(909)
  - "FMP_API_KEY is not configured; …"(h.note)
  - "rf 3.00% assumed · FRED unavailable"(analysis.py:73)
  - 개발자용 출력: `converged=True`, `at_bound: ('alpha',)`, 17자리 실수 `(0.0, 0.0919318057082417)`
  - 겹치는 줄: note가 GARCH fit 줄을 반복하고, se_note가 note 끝을 반복합니다.
- **한국어 화면인데 영어입니다** [측정]: 한국어 화면에서 13줄 중 12줄이 영어로 나옵니다.
- **높이가 맞지 않습니다** [측정]: 1360px에서 설명 열은 344x527인데 차트는 688x240입니다. 차트 아래에 287px이 빕니다.
- **표 마지막 행이 가려집니다** [측정]: 결과 표 quant_metrics의 최소 높이는 280인데(app.py:571 [읽음]) 8행에는 324px이 필요합니다. 그래서 마지막 행 "Horizon-average vol (ann.)"이 표 안쪽 스크롤 뒤에 숨습니다.

### 2.2 제안 디자인

패널 "분포와 근거" 안의 순서:
1. 제목
2. ChartStudy(왼쪽 차트 | 오른쪽 읽기 열)
3. 결과 표(행 수에 맞춘 높이, 안쪽 스크롤 없음)
4. caption

읽기 열은 `QFrame#reading`으로 만들고 배경을 투명하게 둡니다. 일반 QWidget을 쓰면 typography.py:166의 `QWidget { background: p.bg }` 때문에 패널 안에 회색 상자가 생깁니다 [측정].

한국어 화면 기본 상태(접힘). 숫자는 sweep이 실행한 GARCH(1,1)-t, AAPL, 키 없음 상태의 값입니다 [측정].

```
[칩] 합성 데이터 · 실제 시장 데이터가 아닙니다        ← 합성일 때만
가정                                                  ← eyebrow 12px/600
• 무위험금리 3.00%(가정값) + 주식위험프리미엄 4.00% = 기대수익률 7.00%
• 로그 추세 +0.72%/년 (볼록성 보정 6.28% 차감)
모형
• GARCH(1,1)-t · 꼬리가 정규분포에 가까워 상한 없이 추출합니다
• 변동성: 다음 거래일 조건부 예측을 252거래일 기준으로 연율화
• 지속성 0.9910 · 반감기 76.47거래일
▸ 모형 진단 자세히 보기
```

펼친 상태(details):

```
α 0.0000 · β 0.9910 · ν 510.930
수렴: 예 · 표본 503거래일 · 일간 평균 −0.084%(고정)
경계에 걸린 계수: α
표준오차: 계산할 수 없음 (최적점에서 정보행렬이 양의 정부호가 아님)
η(=1/ν) 95% 프로파일 구간: 0.0000–0.0919
기간 평균 변동성: √(예측 일간 분산의 평균) × √252
볼록성 보정: 경로별 조건부 분산으로 단계마다 계산해 기간 평균
```

**숫자 출처와 표시 규칙**
- 숫자는 모두 결과 객체의 필드에서 그대로 가져옵니다. 새로 계산하지 않습니다.
  - 가정 줄: MCResult의 rf_rate, erp, mu_annual, correction_annual, drift_mode, z_bound(montecarlo.py:77-109 [읽음])
  - 진단 줄: GarchFit의 alpha, beta, nu, n_obs, mean_daily, converged, at_bound, se, se_note, eta_interval, interval()(garch.py:98-133 [읽음])
- 자릿수는 지금 쓰는 형식을 따릅니다(:.2%, :.4f, :.3f, :.2f).
- 구간은 'lo–hi'로 표시합니다. η 구간을 :.4f로 줄이는 것은 표시 반올림이므로 소유자 확인이 필요합니다(open_questions 6).

**모형별 줄**
- 무위험금리 뒤의 "(가정값)"은 FRED 조회에 실패해 3% 대체값을 쓴 경우에만 붙입니다. 판별할 수 있게 analysis.py:73의 문장을 상수 `RF_FALLBACK_NOTE`로 만들어 같은지 비교합니다.
- 블록 부트스트랩일 때는 BOOTSTRAP_TEXT_KO / BOOTSTRAP_TEXT 전문을 "모형" 아래에 그대로 둡니다. 꼭 보여야 하는 공시 문장입니다.
- 목표가가 있으면 "목표가 확률: 5거래일 뒤 최종 가격 ≥ 100.00 (마지막 거래일만 사용)" 한 줄을 넣습니다.
- jump_note가 있으면 "모형" 아래 한 줄로 넣습니다.

**화면에서 빼는 것** (source_text에는 남습니다)
- FMP_API_KEY / KIS 자격 증명 문장
- 공급사 이름
- "; cached …" 표시
- 관측 기간
- FRED 이름과 날짜
- 'note:'와 'se_note:' 원문 줄(내용은 진단 행으로 모두 옮겨짐)

키 설정 상태는 System > 연결 화면이 맡습니다.

**위젯과 테스트**
- `quant_notes`는 지금처럼 원문 전체를 가진 UiLabel로 남깁니다. 다만 화면에서는 "자세히" 접힘 안의 근거 전문 라벨이 됩니다.
- 화면 표시 변형(localized_text en/ko)은 새 모듈 `quantgen_desktop/mc_reading.py`가 만듭니다.
- 이렇게 하면 아래 테스트가 그대로 통과할 것으로 봅니다. 다만 실행해 보지 않았으므로 [미확인]입니다.
  - desktop_acceptance.py:390 (영어 'annualized using 252 sessions')
  - desktop_acceptance.py:404 ('final price >= 100.00 after 5 sessions')
  - mc_bootstrap_disclosure_acceptance.py:530-556 (한국어에 BOOTSTRAP_TEXT_KO, source_text 불변)
- 요약은 새 라벨 `quant_summary`가 보여 줍니다.

**데이터 출처 콤보**
- 'Auto · KIS / FMP' 항목 이름을 'Auto'로 바꿉니다(app.py:536). 한국어 '자동'은 translations.py:261에 이미 있습니다 [읽음].
- FMP 항목을 숨길지는 소유자 결정입니다(B1).

**화면 머리말**
- 부제 "Quant Lab · 기존 계산 엔진으로 가격 분포 분석"(app.py:521)과 홈 버튼 "Quant Lab에서 연구 시작 →"(app.py:373)은 영어 키로 바꿉니다.
  - 부제 → '몬테카를로 · 가격 분포 분석'
  - 버튼 → '몬테카를로에서 연구 시작 →'
- 원래 A1 목록에 있던 MX-8 항목인데, app.py를 A3가 맡으므로 A3로 옮깁니다.

**Strategy Lab 탭**
- 왼쪽 결과 열의 출처 문단(strategy.py:45, 48)은 4.A의 ToolPane 접힘 규칙을 따릅니다.
- 입력란 위 긴 caption 두 개(strategy.py:19-21)는 한 줄로 줄입니다: "실데이터 실행만 연구 원장에 기록됩니다". 나머지는 "규칙·노출 설명" 접힘으로 옮깁니다.
- 판정 줄 "Decision: …"(strategy.py:51)은 접지 않습니다.

시제품 측정 [측정]: ChartStudy 높이가 527→240(ko), 544→293(en)으로 줄어 차트와 설명 열 높이가 맞습니다.
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_buildtest_1360w_full_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_buildtest_1000w_full_ko.png

### 2.3 상호작용
- "▸ 모형 진단 자세히 보기"는 checkable QToolButton입니다. 처음에는 접혀 있습니다. 접고 펼친 상태는 이번 앱 세션 동안만 기억하고 저장하지 않습니다.
- 펼치면 ChartStudy 높이가 다시 계산되고(updateGeometry), 페이지 스크롤이 늘어납니다.
- 1000px 창에서는 기존대로 차트 위, 읽기 열 아래로 쌓입니다.

### 2.4 접근성
- 펼침 버튼에는 접근 이름 "모형 진단 자세히 보기"를 붙이고, 상태는 "펼침/접힘"으로 알립니다. Space와 Enter로 열고 닫습니다.
- 포커스 테두리는 기존 `:focus` 규칙에 `QToolButton[fold='true']:focus`를 더해 보입니다.
- 칩 대비 [계산]: 기존 flat 색 기준 밝은 테마 #646E68 / #F3F4EE = 4.78:1, 어두운 테마 #A7B8AC / #26342C = 6.27:1. 둘 다 AA 4.5:1 이상입니다.
- 모든 라벨은 지금처럼 마우스로 선택할 수 있습니다(app.py:107 [읽음]).

### 2.5 바뀌지 않는 것
- 실행 기록, 지표 값, 차트, 판정(NOT_RUN 유지), 내보내기(ResearchRun JSON에는 설명이 들어가지 않습니다), `quant_notes.source_text`.
- 상태 줄 "COMPLETED · 검증 NOT_RUN …"(app.py:931)의 번역은 A1 담당입니다(translations.py:132).

### 2.6 바꿀 파일 (A3)
- quantgen_desktop/app.py: make_quant 520-577, job_succeeded의 MC 블록 903-931, 홈 버튼 373
- 새 파일 quantgen_desktop/mc_reading.py
- 새 파일 quantgen_desktop/reading.py (ReadingColumn, Fold, StatusChips, fit_table_height)
- quantgen_desktop/reading_language.py (P0에서 만든 빈 파일을 채움)
- quantgen_desktop/typography.py: chip 역할, QFrame#reading과 #fold 투명 규칙, 펼침 버튼 스타일
- core/research/analysis.py: RF_FALLBACK_NOTE 상수
- core/research/mc_disclosure.py: 변동성 설명의 한국어 변형
- quantgen_desktop/strategy.py: 18-21만 A3

### 2.7 테스트

새 파일 tests/desktop_a3_layout_acceptance.py에서 확인할 것:
1. 패널 첫 위젯이 제목이고, 두 번째가 ChartStudy입니다.
2. 1360px, ko와 en, GARCH fixture에서 읽기 열 높이 ≤ 차트 높이 + 60px입니다.
3. quant_metrics의 세로 스크롤 최대값이 0입니다.
4. details는 기본으로 숨겨져 있고, 펼침 버튼을 누르면 보입니다.
5. 한국어 화면의 요약과 details에 'FMP_API_KEY', 'FRED', 'KIS', 공급사 이름, '(', 'converged=' 같은 원시 표기가 없습니다.
6. 요약 속 숫자 문자열이 같은 필드를 같은 형식으로 쓴 문자열과 같습니다.
7. source_text가 현재 방식으로 만든 문자열과 같습니다.
8. 블록 부트스트랩 공시문이 ko와 en에서 정확히 한 번 나옵니다.

기존 테스트 desktop_acceptance.py와 mc_bootstrap_disclosure_acceptance.py는 그대로 통과해야 합니다.

### 2.8 위험
- 요약 문장의 금융 용어(무위험금리, 주식위험프리미엄, 지속성, 반감기)가 A1의 용어 결정과 어긋날 수 있습니다. P0의 용어 기준표 v0로 막습니다.
- 펼친 상태에서 오른쪽 열이 다시 길어집니다. 의도한 동작입니다.
- 모형마다 줄 구성이 다릅니다(GBM, jump, bootstrap). 화면에서 확인한 것은 GARCH-t 하나뿐이고 나머지 셋은 [미확인]입니다.

---

## 3. UI-11b · 채권 표 두 개를 가로로 나란히, 빈 오른쪽 공간 제거, 유리 질감으로 구분

### 3.1 현재 상태

스크린샷:
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_calc_full_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_tables_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_scenarios_full_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_calc_1000w_full_ko.png
- 영어는 각 파일 이름의 _ko를 _en으로 바꾼 파일입니다.

**세로 순서** [읽음, bonds.py:25-61]:
1. 입력 패널
2. metrics 표(bonds.py:51)
3. ChartStudy(bonds.py:58, index 2)
4. KRD 표(bonds.py:53)
5. scenarios(bonds.py:54)
6. hedge
7. 내보내기

두 표 사이에 차트가 끼어 있고, 입력 패널 말고는 모두 패널 없이 페이지 바탕에 바로 놓여 있습니다.

**오른쪽이 비는 이유**
- table()(app.py:149-162 [읽음])은 머리글이 7개 이하인 표의 모든 열을 Stretch로 늘립니다.
- 그래서 2열 표가 1114px 폭을 다 씁니다 [측정]. 열 하나가 552px인데 내용은 114-144px만 필요합니다.

**행이 잘리는 이유** [측정]
- metrics: 12행에 468px이 필요한데 최소 높이가 360입니다. 마지막 3행이 표 안쪽 스크롤 뒤에 숨습니다.
- KRD: 9행에 360px이 필요한데 260입니다. 10·20·30년 행이 숨고 '10' 행은 가장자리에서 잘립니다.
- 위젯끼리 실제로 겹치는 현상은 1360x900과 1000x700에서 재현되지 않았습니다. 소유자가 말한 "겹침"은 이렇게 잘리고 가려진 행을 가리킨다고 추정합니다 [미확인].

**충격 칸**: 시나리오 표의 "Shock · bp" 칸은 `str(r.shock_bp)`입니다(bonds.py:90 [읽음]). 곡선 모양 시나리오에서는 원시 dict가 그대로 나오고 1375px 폭이 필요합니다 [측정].

**출처 줄**: 설명에 출처 줄과 같은 문장이 두 번 나옵니다. bond_notes(bonds_portfolio_narrative.py:122-134 [읽음])가 panel.note와 curve.note를 모두 넣기 때문입니다.

### 3.2 제안 디자인

시제품 [측정]:
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_bonds_calc_view_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_bonds_calc_1360w_full_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_bonds_calc_1000w_full_ko.png
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_bonds_scenarios_1360w_full_ko.png
- 측정값: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/proto_bonds_measure_ko.json

```
[입력 패널 — 지금과 같음]
┌ 핵심 지표 (패널) ─────────┐  ┌ 만기별 DV01 (패널) ───────┐   ← QHBoxLayout, 간격 18
│ 항목            │      값 │  │ 만기 · 년 │  DV01 · 통화/bp │
│ 12행, 스크롤 없음        │  │ 9행, 스크롤 없음           │
└──────────────────────────┘  └───────────────────────────┘
┌ 가격-수익률 곡선 (패널) ─────────────────────────────────┐
│ [차트 2/3]                    │ [칩] 합성 곡선 · 현재 시장 데이터 아님 │
│                               │ 해설(narrative)                      │
│                               │ ▸ 출처·가정 보기 (접힘)               │
└────────────────────────────────────────────────────────────┘
┌ 금리 시나리오 (패널, '시나리오' 도구일 때만) ─────────────┐
│ 시나리오 | 금리 충격 | 변동 후 가격 | 손익 | 손익률 %         │
└────────────────────────────────────────────────────────────┘
[선물 헤지 결과 — 'hedge' 도구일 때: 선택안 (b)는 오른쪽 열 KRD 아래]
[내보내기]
```

**표 설정** (두 채권 표에만 적용, A3 helper `compact_columns`, `fit_table_height`)
- 0열은 ResizeToContents, 마지막 열은 Stretch, 숫자 열은 오른쪽 정렬입니다.
- 높이는 머리글 + 행 높이 합 + 테두리로 맞추고 세로 스크롤바는 끕니다.
- 시제품에서 ko와 en 모두, 1360과 1000 모두 가로·세로 스크롤 최대값이 0이었습니다 [측정].

**폭** [측정]
- 1360: 열 하나 548/545px, 표 502/499px
- 1000: 열 하나 368/365px, 표 322/319px
- 필요한 폭은 245(metrics)와 266(KRD)이므로 최소 창 1000px에서도 들어갑니다.

**오른쪽 빈 공간** (소유자 선택, M2-c 목업)
- (a) 두 패널 높이를 같게 둡니다(AlignTop 없음). KRD 패널 아래쪽 약 108px이 패널 안쪽 여백으로 보입니다. 권장안입니다.
- (b) hedge 도구일 때 선물 헤지 결과를 KRD 아래에 둡니다.

**단위 표기**
- 값 칸의 영어 단위('years', 'currency / bp')를 항목명으로 옮기고, 값 칸에는 숫자만 둡니다.
  - 예: 'Macaulay duration · years' / '8.163', 'DV01 · currency / bp' / '798.12'
- 이 영어 키 12개 + 머리글 키 4개는 P0에서 확정합니다. 한국어는 A1이 translations.py에 넣습니다. 예: 맥컬리 듀레이션 · 년, 볼록성(컨벡시티), DV01은 영어 그대로.
- metrics 표에는 localized_columns [0]을 붙입니다(지금은 없음, bonds.py:51 [읽음]).
- 내보내기는 analytics 객체를 저장하므로 표 문자열이 바뀌어도 영향이 없습니다(bonds.py:105-111 [읽음]).

**충격 칸 표시**
- 평행 이동은 '+25bp 평행 이동' / '+25bp parallel'로 씁니다.
- 곡선 모양은 테너별로 '3m +0 · 1y +0 · 2y +0 · 3y +2 · 5y +5 · …'처럼 씁니다. dict에 있는 테너를 모두 보여 주고, 원래 값은 툴팁에 둡니다.
- Flet ui/bonds_page.py:52-56의 _shock_text는 5개 테너만 보여 주므로 그대로 옮기지 않습니다.
- 정수 bp로 반올림하는 것은 소유자 확인이 필요합니다(open_questions 5).

**설명 정리**
- `bond_notes()`의 반환을 "칩 + 해설"로 바꿉니다. 이 함수만 A3 담당입니다.
- 출처 줄, panel.note, curve.note(같으면 한 번만), 모형 메모는 새 함수 `bond_fold_notes()`가 "출처·가정 보기" 접힘용으로 따로 만듭니다.
- `self.notes`는 계속 bond_notes를 보여 줍니다. 그래서 아래 테스트가 그대로 성립합니다.
  - tests/desktop_bonds_portfolio_language_acceptance.py:126 `notes.text()==bond_notes(out,lang)`
  - desktop_acceptance.py:310 'Synthetic curve'
- 내보내기용 `notes.source_text`(bonds.py:98-101)는 바꾸지 않습니다.
- bonds.py:48 caption의 한·영 혼용("Price를 입력할 때는 Yield를 비웁니다")은 영어 키로 바꿉니다: "가격과 수익률 중 하나만 입력하세요. 가격을 입력하면 수익률 칸은 비워 두세요."

**유리 질감** (GLASS, 소유자 선택, M3 목업)
- G1: 기존 패널(QFrame#panel의 그라데이션, 밝은 윗선, 2px 아랫선, 14px 둥근 모서리)로 각 블록을 감쌉니다. 새 색 토큰이 필요 없습니다.
- G2: 스타일시트만 쓰는 새 변형 `QFrame#panel[variant='glass']`입니다. 새 토큰 PANEL_GLASS를 typography.py에 더하고 PANEL_DEPTH는 건드리지 않습니다. 제안값은 다음과 같고, 보이는 모습은 [미확인]입니다.
  - 밝은 테마: top rgba(255,255,255,0.78), bottom rgba(250,249,244,0.62), edge_top rgba(255,255,255,0.95), border rgba(210,213,201,0.70), edge_bottom #D2D5C9(고정값 유지)
  - 어두운 테마: top rgba(27,42,35,0.80), bottom rgba(21,32,27,0.66), edge_top rgba(63,86,73,0.95), edge_bottom #0A110E
- Qt는 뒤쪽을 흐리게 하는 blur가 없습니다. 그래서 "유리"는 반투명 그라데이션과 위쪽 하이라이트로만 표현합니다. 그림자 효과는 금지입니다.

### 3.3 상호작용
- 도구(계산 / 시나리오 / 헤지)를 바꾸면 해당 패널만 보이거나 숨습니다. 지금 동작과 같습니다(bonds.py:91).
- 창 폭이 바뀌면 두 표 열은 가로를 유지하고, 차트와 해설은 820px 아래에서 위아래로 쌓입니다.
- 1000px에서 표 하나의 폭은 322px이고 필요한 폭은 266px입니다. 따라서 두 표를 세로로 바꾸는 기준점은 두지 않습니다. A1 한국어가 들어간 뒤 다시 잽니다.

### 3.4 접근성
- 패널마다 제목(heading 18px)이 있어 화면낭독기에서 구역 이름으로 읽힙니다.
- 표의 접근 이름은 패널 제목과 같게 둡니다.
- G2 대비는 목업에서 잽니다. 기존 muted #646E68은 흰 바탕에서 5.29:1, #FAF9F4 바탕에서 5.02:1입니다 [계산].

### 3.5 바뀌지 않는 것
- 계산, 값, 행 수(12, 9, 9 → tests/desktop_acceptance.py:307-309), 차트 계열, 내보내기 report와 source_text, 헤지 문장(hedge_text는 A1).

### 3.6 바꿀 파일 (A3)
- quantgen_desktop/bonds.py 전체
- bonds_portfolio_narrative.py의 bond_notes()와 새 bond_fold_notes()
- quantgen_desktop/reading.py
- quantgen_desktop/typography.py
- quantgen_desktop/reading_language.py ('Key metrics', 'Price–yield curve', 'Rate scenarios', 'Sources and assumptions' 등 화면 틀 문자열)
- 'Key-rate DV01'은 A1의 Rates 키(rates.py:89)와 같은 키를 씁니다.

### 3.7 테스트

tests/desktop_a3_layout_acceptance.py에서 확인할 것:
1. metrics 패널과 KRD 패널의 y좌표가 같고 x좌표가 다릅니다(1360, 1000, ko, en).
2. 두 표의 가로·세로 스크롤 최대값이 0입니다.
3. 형제 위젯끼리 geometry가 겹치지 않습니다.
4. 충격 칸에 '{'가 없습니다.
5. 언어를 바꾸기 전후 exports.report가 같습니다(deepcopy 비교, 기존 패턴).
6. 블록마다 objectName이 'panel'입니다.
7. G2를 고르면 스타일시트에 variant 규칙이 있고, PANEL_DEPTH 고정값과 그림자 금지 테스트가 유지됩니다.

### 3.8 위험
- A1 한국어 항목명 때문에 0열이 넓어질 수 있습니다. 병합 뒤 다시 잽니다.
- 행 높이에 맞춘 표는 행 수가 늘면 페이지가 길어집니다. 페이지 스크롤이므로 괜찮습니다.
- bonds_portfolio_narrative.py를 함수 단위로 나눠 맡습니다. A1이 먼저 병합하고, A3가 rebase해서 확인합니다.

---

## 4. UI-12 · 지저분한 설명과 작은 글씨 정리 + "알아보기" 용어 패널

현재 상태:
- 스크린샷은 아직 없습니다. 목업 M4와 M5에서 "현재" 프레임을 함께 찍습니다.
- 라벨 측정: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ui12/out/labels_ko.json (1766건), /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ui12/out/labels_en.json
- 선택 감지 시제품: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ui12/proto_select.py
- 용어 찾기 시제품: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ui12/proto_match.py

### 4.A 설명 정리

**현재** [측정]
- ToolPane.text()(tools.py:211-222 [읽음])는 결과 하나에 muted 14px 문단을 2-8개 쌓습니다. 한국어 화면 기준:

  | 결과 화면 | 문단 수 | 글자 수 |
  |---|---|---|
  | 파생(derivatives) | 6 | 1,949 |
  | ETF | 6 | 1,929 |
  | Strategy 실행 | 7 | 2,285 |

- 이 문단에 공급사·관측일 줄, "합성 데이터"를 2-3번 반복하는 문장, 같은 문장의 중복이 섞여 있습니다. 같은 문장 중복은 rates.py:59-60, structuring.py:40-42에서 p.note와 c.note가 같아서 생깁니다.
- 모든 결과 위에 caption "분석 해설 · 선택 언어로 표시하며 내보내기에는 원문 유지"(tools.py:249-251)가 붙습니다.
- 모든 도구가 같은 상태 줄(tools.py:257)을 씁니다.

**제안 규칙** (앱 전체)
1. 결과의 오른쪽 읽기 열(tools.py:144-148의 result_reading)은 위에서부터 이렇게 구성합니다.
   - ① 상태 칩 줄: 합성 데이터 · 실제 시장 데이터 아님 / 지연 자료 / 일부 이력 등. 중복은 하나로 합칩니다.
   - ② 해설(narrative)
   - ③ "출처·가정 보기" 접힘(기본은 접힘). 출처 문단을 여기로 옮기고 같은 줄은 한 번만 보여 줍니다.
2. 왼쪽 결과 열에는 표와 차트, 그리고 결과에 속하는 문장만 남깁니다. 예: 판정 줄, PCA 미실행 이유.
3. tools.py:249-251 caption은 화면에서 지웁니다. 같은 뜻은 내보내기 버튼 툴팁 "원문은 내보내기 파일에 그대로 보관됩니다"로 옮깁니다.
4. tools.py:257 상태 줄은 "계산 완료" + 칩 "공식 판정 아님"으로 바꿉니다.
5. caption(12px)은 60자 미만의 입력란 이름과 짧은 메타데이터에만 씁니다. 긴 문장은 14px 본문으로 접힘 안에 둡니다. 글자 크기 체계는 바꾸지 않습니다.
6. 출처·관측일·관측 수는 화면 본문에 두지 않습니다. 접힘 안에 넣고 툴팁에도 둡니다. 합성, 지연, 실패 상태는 칩으로 늘 보입니다. 이것은 PR #71 결정을 분석 결과 본문까지 넓히는 것이므로 소유자 확인이 필요합니다(open_questions 1).

**구현 방식**
- P0에서 각 화면의 해당 text() 호출에 `kind='provenance'` 또는 `kind='notice'` 표시만 붙여 둡니다. 화면 변화는 없습니다.
- A3는 tools.py에서 kind를 보고 위치를 정합니다.
  - provenance → 접힘
  - notice → 칩
- kind는 self.sections에 저장하지 않으므로 내보내기와 AI 해설 자료는 같습니다.
- 표시 대상:
  - provenance: rates.py:59, :118 / structuring.py:42 / signals.py:30 / strategy.py:45 / macro.py:45 / market_tools.py:44, :125, :196
  - notice: fx.py:37 / macro.py:48 / strategy.py:48 / market_tools.py:46, :127, :198
- 판정 줄(strategy.py:51), 공급자 실패 줄(market_tools.py:261), 결과 해설은 표시하지 않습니다(그대로 보임).

**A3-a에서 할 곳** (A3 파일)
- 모든 ToolPane(Rates, FX, Structuring, Macro, Signals, Strategy, Derivatives, ETF, Crypto, KRX): tools.py의 규칙 하나로 처리
- Bonds(3장), Build & Test(2장)
- 홈 카드 caption(app.py:358-362, 375): 세 번 반복을 카드 줄 아래 한 번으로 줄입니다. "이번 세션 몬테카를로 실행 수 · 투자 판정 아님", "P5–P95: 시뮬레이션 중앙 90% 구간"
- System 패널(app.py:665-676): "개발 정보" 접힘 하나로 묶고, 기본 화면에는 "이 데스크톱은 미리보기 버전입니다" 한 줄만 둡니다. 상태어(미검증, 미동결 …)는 용어 기준표를 따릅니다.
- 데이터 권리(data_rights.py:24, 29): 법률 문구는 뜻을 바꾸지 않고 14px 본문 3문장 이내로 줄입니다. URL은 "근거 보기" 링크 버튼으로 바꿉니다.
- 기술지표 가이드 caption 합치기(indicator_guide.py:168+179, 183+188)

**A3-b에서 할 곳** (A1 병합 뒤, A1이 번역하던 파일)
- market_chart.py: indicator_help 문단(335/1068) 제거, limitations(351)를 접힘으로, 밴드 값 소수 6자리 → 정수 표시(1150-1154)
- markets_view.py:725 / stock_profile.py: "DO-NOT-BUILD TF-12" 제거, "제공되지 않는 정보" 9행을 1행으로
- portfolio.py:39, 45-46, 75-78
- market_tools.py:110-112 (ETF 입력 caption → 툴팁)
- Library caption 칩(app.py:613). 상태어 라벨 함수가 A1에서 오므로 여기에 둡니다.
- watchlist.py의 Q-SCORE "?"를 패널로 연결

### 4.B "알아보기" 패널

**선택 감지** [시제품 확인, proto_select.py]
- 모든 라벨이 이미 마우스로 선택됩니다(app.py:107, market_chart.py:371, watchlist.py:77).
- 새 모듈 `quantgen_desktop/term_panel.py`가 QApplication에 이벤트 필터를 하나 겁니다. localization.py는 A1 파일이므로 쓰지 않습니다.
- 마우스를 놓을 때(MouseButtonRelease) 선택된 글이 있고 용어가 찾아지면, 놓은 자리 오른쪽 아래 8px에 작은 칩 "알아보기: 수정 듀레이션"을 띄웁니다.
  - 칩은 포커스를 가져오지 않습니다.
  - 다른 곳을 클릭하거나, 스크롤하거나, Esc를 누르거나, 라벨 글자가 바뀌면 닫힙니다.
  - 칩을 누르면 패널이 열립니다.
- 더블클릭으로 고른 '듀레이션과'처럼 조사가 붙은 말도 조사를 떼고 찾습니다.

**오른쪽 클릭**
- 라벨: 메뉴를 직접 만듭니다. 항목은 "복사 / 모두 선택 / 알아보기: <용어>"이고, 용어가 없으면 마지막 항목은 빠집니다. QLabel에는 공개된 기본 메뉴 함수가 없어서 직접 만들어야 합니다.
- 표: viewport 메뉴에서 현재 셀을 씁니다. 항목명 열은 영어 원문(CAPTION_ROLE, app.py:169-170 [읽음])으로 찾습니다. 키보드로 연 메뉴(Shift+F10, 메뉴 키)도 같은 메뉴입니다 [시제품 확인].

**키보드**
- F1: 패널을 열고 검색창에 포커스를 둡니다. 선택한 글이나 현재 표 셀의 용어가 미리 들어갑니다.
- Esc: 패널을 닫고 원래 포커스로 돌아갑니다.
- 지금 앱에는 QShortcut이 없습니다 [읽음, git grep].

**용어 찾기**
- 새 순수 모듈 `core/education/term_lookup.py`에 `terms_in(text, scope)`를 둡니다.
  - 조사를 뗍니다(과·와·은·는·이·가·을·를·의·에·로·으로 …).
  - 가장 긴 별칭부터 맞춥니다. 영어는 단어 경계로 자릅니다.
  - 화면 범위(scope)를 보고 애매한 별칭을 가립니다. 예: 'forward'는 fx 화면에서만 fx_forward, 'bootstrap'은 rates/bonds에서만 금리 부트스트래핑이고 MC의 'Block bootstrap'은 막습니다. rates 시뮬레이션의 'Theta'는 연결하지 않습니다.
  - 표 항목명 지도 `CAPTION_TERMS`({영어 항목명: 용어 키})도 둡니다.
- 지금 있는 `glossary.search()`(glossary.py:421 [읽음])는 앞부분 일치 방식이라 선택한 글에 맞지 않습니다. 시제품에서 'VaR를'이 CVaR로 잘못 잡혔습니다 [측정].

**패널 위치**
- 폭 340px입니다.
- 창 폭 1280px 이상: 루트 가로 레이아웃(app.py:227-229, 282 [읽음])의 세 번째 열로 붙여 내용을 밉니다.
- 1280px 미만: 내용 위에 겹쳐 띄웁니다. 왼쪽 테두리와 패널 질감이 있습니다.
- 최소 창 1000px(app.py:224)에서 내용 폭이 약 800px이므로 밀면 입력 폼이 잘립니다. 그래서 겹치는 방식을 씁니다.
- 크기가 바뀌면 두 방식 사이를 바로 바꿉니다. 열린 상태는 세션 동안만 기억합니다.

**AI 호출 없음**
- 네트워크와 AI를 쓰지 않습니다. 로컬 용어집과 화면에 이미 표시된 값만 씁니다.
- "AI에게 더 묻기"는 1단계에 넣지 않습니다(open_questions 7).

### 4.C 접근성
- 패널은 QFrame#termPanel입니다. 접근 이름은 "용어 설명", 구역 이름은 "개념", "적용", "이 화면에서의 의미", "한계"입니다.
- Tab 순서: 검색 → 후보 칩 → 본문 → "가이드에서 자세히" → 닫기
- 화면낭독기 사용자는 떠 있는 칩을 읽지 못하므로 F1 경로를 씁니다. 칩에도 접근 이름을 붙입니다.
- 본문은 14px, 구역 제목은 eyebrow 12px/600입니다. 모든 색은 기존 토큰으로 밝은·어두운 테마를 모두 지원합니다.
- 마우스 올리기 밑줄 링크는 1단계에서 넣지 않습니다(라벨이 PlainText이기 때문, app.py:104 [읽음]).

### 4.D 바뀌지 않는 것, 바꿀 파일, 테스트, 위험

**바뀌지 않는 것**
- 라벨 선택 동작, 기존 복사.
- 기술지표 가이드 화면. "가이드에서 자세히"는 navigate('guide') + IndicatorGuide.choose(key)(indicator_guide.py:258 [읽음])만 부릅니다.
- AI 해설 동의 절차, 내보내기.

**바꿀 파일 (A3)**
- 새 파일: quantgen_desktop/term_panel.py, core/education/term_lookup.py
- app.py: 패널 붙이기, F1
- indicator_guide.py: _render_detail(353-370)의 상세 위젯을 패널과 같이 쓰도록 분리
- tools.py, reading.py, typography.py, reading_language.py

**테스트**
- 새 파일 tests/term_lookup_acceptance.py
  - proto_match.py의 14문장
  - 조사 붙은 말
  - 'VaR를'→var
  - 화면 범위로 가리는 별칭
  - 32개 용어 모두 한국어 이름과 영어 이름으로 찾아짐
- 새 파일 tests/desktop_term_panel_acceptance.py
  - QLabel.setSelection 뒤 MouseButtonRelease를 합성하면 칩이 보이고 접근 이름이 맞습니다.
  - 칩을 누르면 패널 제목이 glossary.name과 같습니다.
  - "이 화면에서" 행의 값이 표 셀 글자와 같습니다.
  - F1로 열면 검색창에 포커스가 가고, Esc로 닫으면 포커스가 돌아옵니다.
  - 1000px에서는 겹침(내용 폭 그대로), 1360px에서는 붙임입니다.
  - requests/socket과 jobs.start를 막아 두고도 통과합니다(네트워크와 계산 없음).
- 4.A의 ToolPane 테스트(desktop_a3_layout_acceptance.py)
  - rates 곡선 fixture에서 출처 문단이 기본으로 안 보이고 접힘 안에 있습니다.
  - 같은 줄은 한 번만 나옵니다.
  - 합성 칩이 보입니다.
  - sections와 report가 변경 전과 같습니다.
  - 판정 줄(strategy)은 보입니다.

**위험**
- 앱 전체 이벤트 필터의 비용: MouseButtonRelease, ContextMenu, F1만 처리해서 줄입니다.
- 실시간 시세가 갱신되어 라벨 글자가 바뀌면 선택이 풀립니다. 그때 칩을 닫습니다.
- 겹쳐 띄운 패널이 입력란을 가립니다. 닫기 버튼과 Esc로 해결합니다.
- kind 표시를 잘못 붙이면 중요한 문장이 접힘에 숨습니다. P0 리뷰와 4.D 테스트로 막습니다.
- 용어집에 없는 용어가 많습니다. 표 항목명 403개 중 86개만 연결됩니다 [측정]. 그래서 처음에는 "용어집에 없는 말입니다"가 자주 나옵니다. 새 용어 추가는 A1이 맡습니다.
- Windows, 125·150% 배율, 어두운 테마, Narrator는 [미확인]입니다.

---

## 5. 용어집이 채우는 사이드 패널 내용 모델

데이터 원천: core/education/glossary.py. 32개 용어, 범주 8개, 필드는 name/summary/meaning/use/limit이고 지표 용어는 meaning/look/interpret/limit입니다 [읽음, glossary.py:17-19, 381-389].
- glossary.py는 A1이 맡습니다. 표준 이름, 새 용어, 별칭을 A1이 정합니다.
- A3는 읽기만 합니다.

| 패널 영역 | 내용 원천 | 규칙 |
|---|---|---|
| 제목 | glossary.name(key, ctx). 한국어 모드에서는 영어 이름을 작게 덧붙임 | 표준 이름은 UI-10 결정을 따름. DV01처럼 한국에서도 영어로 쓰는 말은 영어 그대로 |
| 분류 | glossary.category(key, ctx) | |
| 한 줄 요약 | glossary.summary | |
| 개념 | sections()[0]: meaning (지표도 meaning) | 그대로 인용 |
| 적용 | sections()[1]: use. 지표는 look + interpret | 그대로 인용 |
| 이 화면에서의 의미 | 화면 맥락 제공자의 행: "현재 결과: 수정 듀레이션 = 8.163" | 화면에 이미 있는 글자를 그대로 인용. 새 계산이나 숫자 재진술 없음. 공급사 hint는 다시 보여 주지 않음(PR #71). 값이 없으면 "이 화면에는 이 용어의 값이 없습니다." |
| 한계 | sections()[-1]: limit | 그대로 인용 |
| 관련 용어 | terms_in()이 함께 찾은 다른 후보 | 칩으로 바꿔 보기 |
| 더 보기 | "가이드에서 자세히 보기" | navigate('guide') + choose(key) |

**구역 제목**: '개념 / 적용 / 이 화면에서의 의미 / 한계'는 A3 번역 목록(reading_language.py)에 둡니다. 가이드의 기존 제목(ctx.t 'meaning', 'glossary_use', 'limit')은 바꾸지 않습니다.

**화면 맥락 제공자** (A3)
- 공통: 지금 보이는 페이지의 QTableWidget에서 0열의 CAPTION_ROLE 영어 원문이 CAPTION_TERMS로 그 용어와 이어지는 행을 찾아, 화면에 보이는 항목명과 값을 그대로 보여 줍니다.
- 화면별 추가 (1단계, A3 파일):
  - Bonds: metrics와 KRD 행
  - Build & Test: quant_metrics 행(P5/P50/P95, VaR 95 / CVaR, 변동성)
- 화면별 추가 (A3-b):
  - Markets 차트: 커서 위치의 지표 값(market_chart.py:1150-1154), 기존 reading_text 문장(core/education/chart.py:143-163)
  - 종목 프로필 행(markets_view.py:885-893)
  - Portfolio
  - Home의 Q-SCORE
- 2단계 (소유자 검토 뒤): 용어별 해석 문장. 예: "수정 듀레이션 4.21 → 금리 1%p 상승 시 약 4.2% 하락". 숫자를 다시 말하는 새 문장이라 1단계에서는 넣지 않습니다.

**A1이 용어집에 더할 것** (패널이 저절로 쓰게 됨)
- 새 필드 `label`: 화면 표기. 예: '볼록성' (name은 '볼록성 · 컨벡시티')
- 새 필드 `keep_english`: DV01, ATM, SABR, CVaR, PBO처럼 영어 그대로 쓰는지
- 새 용어. 우선 후보: z-스프레드, 롤다운, 손익분기, 만기수익률(YTM), 금리차(2s10s), 선도금리, 애뉴이티, 파 금리, 스왑션, 캡·플로어, 리스크 리버설·ATM, 베이시스, 김치 프리미엄, 펀딩비, PBO, 표본 내/표본 외·순차 전진, 디플레이티드 샤프 지수, 효율적 투자선, 위험 기여도, 리스크 패리티, 손실 확률, 주식위험프리미엄·드리프트, 블록 부트스트랩, 52주 범위, PER·EPS·시가총액

A3의 term_lookup은 별칭을 A3 파일 안의 보조 지도로 더할 수 있어서 glossary.py를 고치지 않습니다.

---

## 6. 확인하지 않은 것 [미확인]
- 테스트는 하나도 실행하지 않았습니다. run_all.py는 금지라 실행하지 않았습니다.
  - 2.2와 3.2의 "그대로 통과"는 해당 줄을 읽고 내린 판단입니다.
  - 제안한 문구 변경에 걸리는 테스트가 위 목록 밖에 더 있는지는 모릅니다.
- 화면에서 본 것은 GARCH-t 하나와 Bonds 계산·시나리오 도구뿐입니다. GBM, jump, bootstrap 화면, Bonds 헤지 도구, Strategy Lab 탭 결과는 보지 않았습니다.
- G2 유리 질감이 실제로 어떻게 보이는지, Windows와 DPI 배율, 어두운 테마, 화면낭독기 동작.
- 두 트랙 git 병합이 실제로 충돌 없이 되는지는 해 보지 않았습니다. 줄 범위를 나눈 근거는 git의 3-way 병합이 겹치지 않는 hunk를 자동으로 합친다는 일반 규칙입니다.
- 로컬 origin/handoff 사본(84e584c… 아님, 커밋 84c76b4, 2026-11-04 17:10 UTC)의 원장에는 ⑬-2/a3-type, a3-rail, a3-controls만 있고 UI-9, UI-11b, UI-12는 없습니다. 원격 최신 원장은 네트워크가 막혀 확인하지 못했습니다. 작업을 시작할 때 `--show`와 `--ledger`로 다시 확인해야 합니다.
- QUANTGEN_REMAINING_2026-11-03 문서는 저장소에 없습니다. 소유자 요청 문구는 작업 지시문에서 가져왔습니다.

## 시안(목업) 계획

목업은 모두 오프스크린 PyQt6 시제품으로 만듭니다. 실제 앱 폰트와 실제 위젯 크기를 그대로 쓰므로 정적 HTML보다 정확합니다. 저장소 파일은 바꾸지 않고, 메모리 안에서만 위젯을 다시 배치하고 번역 사전을 바꿉니다.

정적 HTML은 이미지를 한 장에 모아 보는 목록(contact sheet) 하나만 만듭니다. 소유자에게 공유할지는 상위 세션이 정합니다.

## 공통 실행 조건

**실행 환경**
- 이미 쓴 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shoot_a3.py, /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/proto_bonds.py, /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/proto_buildtest.py의 보호 장치를 그대로 씁니다.
  - dotenv.load_dotenv와 dotenv_values를 패치해 .env를 읽지 않습니다.
  - requests와 socket을 막습니다.
  - config.fmp_key/fmp_ready/kis_ready는 빈 값과 False로 둡니다.
  - HOME과 XDG 경로는 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/home 으로 돌립니다.
  - core.quant.gate_ledger.family_ledger를 막습니다.
- Python은 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/v313/bin/python -B, cwd는 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10 입니다.
- 환경 변수: PYTHONPATH=., QT_QPA_PLATFORM=offscreen, QT_SCALE_FACTOR=1, PYTHONDONTWRITEBYTECODE=1

**파일 위치**
- 새 스크립트: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/mock/
- 결과 이미지와 측정 JSON: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/mock/out/
- 실행 전후에 s10에서 `git status --short`가 비어 있는지 확인합니다.

**언어·크기·테마**
- 모든 목업을 한국어(기본)와 영어로 하나씩 만듭니다.
- 창 크기는 1360x900과 1000x700입니다.
- 테마는 밝은 테마입니다. M3만 어두운 테마도 만듭니다.

**용어 표시**
- A3 화면에 나오는 금융 용어는 A1 sweep이 제안한 한국어를 메모리에서 translations.KO에 넣어 보여 줍니다. 대상은 BD-1~BD-4, NR-1, CL-10 등입니다.
- 이미지 아래 캡션에는 "용어는 A1 제안안(미확정)"이라고 적습니다.

**측정 JSON** (프레임마다 남김)
- 위젯별 geometry
- 표의 가로·세로 스크롤 최대값
- 읽기 열 높이와 차트 높이
- 패널 바탕 대비 글자 대비율

## M1 · 설계/검증 Monte Carlo (UI-9) — mock_ui9.py

**입력**
- AAPL, 데이터 출처 '자동'(키 없음 → 합성 대체), GARCH(1,1)-t, 위험 프리미엄 추세, 126거래일, 경로 5000, 시드 7, ERP 4
- FRED 로더는 실패하게 둡니다. 그러면 "rf 3.00% assumed" 경로를 탑니다.
- 운영 코드의 execute_analysis를 그대로 씁니다.

**프레임**
- M1-a 현재: 이미 있는 이미지를 다시 씁니다.
  - /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_full_ko.png
  - /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/buildtest_full_en.png
- M1-b 제안, 접힘, 1360
  - 패널 순서: 제목 "분포와 근거" → [차트 | 읽기 열] → 결과 표(8행, 스크롤 없음) → caption
  - 읽기 열 내용(한국어):
    - 칩 "합성 데이터 · 실제 시장 데이터가 아닙니다"
    - eyebrow "가정"
      - • 무위험금리 3.00%(가정값) + 주식위험프리미엄 4.00% = 기대수익률 7.00%
      - • 로그 추세 +0.72%/년 (볼록성 보정 6.28% 차감)
    - eyebrow "모형"
      - • GARCH(1,1)-t · 꼬리가 정규분포에 가까워 상한 없이 추출합니다
      - • 변동성: 다음 거래일 조건부 예측을 252거래일 기준으로 연율화
      - • 지속성 0.9910 · 반감기 76.47거래일
    - 버튼 "▸ 모형 진단 자세히 보기"
  - 영어판:
    - 칩 "Synthetic data · not market data"
    - Assumptions
      - • Risk-free 3.00% (assumed) + equity risk premium 4.00% = expected return 7.00%
      - • Log drift +0.72%/yr (after a 6.28% convexity correction)
    - Model
      - • GARCH(1,1)-t · tails close to normal, drawn without a cap
      - • Volatility: next-session conditional forecast, annualized using 252 sessions
      - • Persistence 0.9910 · half-life 76.47 sessions
    - 버튼 "▸ Show model diagnostics"
  - 숫자는 실행한 결과 객체에서 그대로 넣습니다.
  - 위 값은 sweep에서 측정한 값입니다. 실행 환경이 달라 값이 다르면 실제 값을 씁니다.
- M1-c 제안, 펼침, 1360. M1-b 아래에 다음 행이 더해집니다.
  - α 0.0000 · β 0.9910 · ν 510.930
  - 수렴: 예 · 표본 503거래일 · 일간 평균 −0.084%(고정)
  - 경계에 걸린 계수: α
  - 표준오차: 계산할 수 없음 (최적점에서 정보행렬이 양의 정부호가 아님)
  - η(=1/ν) 95% 프로파일 구간: 0.0000–0.0919
  - 기간 평균 변동성: √(예측 일간 분산의 평균) × √252
  - 볼록성 보정: 경로별 조건부 분산으로 단계마다 계산해 기간 평균
  - 영어판도 같은 행 구성입니다.
- M1-d 제안, 접힘, 1000x700: 차트 위, 읽기 열 아래로 쌓인 모습
- M1-e 데이터 출처 콤보를 연 상태: '자동 / FMP / KIS · KRX / 합성 데이터 시연'

**측정**
- ChartStudy 높이, 차트 높이, 읽기 열 높이. 목표는 읽기 열 ≤ 차트 + 60px입니다.
- quant_metrics 세로 스크롤 최대값. 목표는 0입니다.

## M2 · 채권 (UI-11b) — mock_bonds.py

**입력**
- tests.desktop_acceptance.bond_fixture, 기본 BondRequest
- 도구는 계산(calc), 시나리오(scenarios), 헤지(hedge)

**프레임**
- M2-a 현재: 이미 있는 이미지를 다시 씁니다.
  - /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_calc_full_ko.png
  - /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/bonds_tables_ko.png
- M2-b 제안, 계산 도구, 1360과 1000. 위에서부터:
  - 입력 패널
  - 가로 한 줄에 두 패널
    - [패널 "핵심 지표" / "Key metrics": 항목 | 값, 12행]
    - [패널 "만기별 DV01" / "Key-rate DV01": 만기 · 년 | DV01 · 통화/bp, 9행]
  - 패널 "가격-수익률 곡선" / "Price–yield curve": 차트 | 읽기 열(칩 "합성 곡선 · 현재 시장 데이터 아님" + 해설 + "▸ 출처·가정 보기" 접힘)
  - 내보내기
- 핵심 지표 12개 항목명(A1 제안안): 가격 · 액면 100당 / 만기수익률 / 맥컬리 듀레이션 · 년 / 수정 듀레이션 / 볼록성(컨벡시티) / DV01 · 통화/bp / Z-스프레드 · bp / 곡선 기준 가격 / 캐리 · 0.25년 / 롤다운 / 캐리+롤다운 / 손익분기 금리 변화 · bp
  - 값 칸에는 단위 없이 숫자만 둡니다.
  - 숫자 열은 오른쪽 정렬이고, 0열은 내용에 맞춘 폭, 1열은 늘립니다.
- M2-c 빈 공간 선택안, 계산 도구, 1360
  - (a) 두 패널 높이를 같게 둔 모습
  - (b) 헤지 도구일 때 "선물 헤지" 패널을 KRD 아래에 둔 모습
  - 두 장을 나란히 놓습니다.
- M2-d 시나리오 도구, 1360
  - 패널 "금리 시나리오"
  - 열: 시나리오 | 금리 충격 | 변동 후 가격 | 손익 | 손익률 %
  - 충격 칸 예: "+25bp 평행 이동", "3m +0 · 1y +0 · 2y +0 · 3y +2 · 5y +5 · 7y +9 · 10y +14 · 20y +32 · 30y +50"
  - 실제 테너와 값은 fixture를 따릅니다. 반올림 규칙은 소유자 확인이 필요하다고 캡션에 적습니다.
- M2-e "▸ 출처·가정 보기"를 펼친 상태
  - 같은 출처 문장이 한 번만 나옵니다.
  - 출처 줄 "SYNTHETIC · 날짜 · bootstrap · 30 거래일"은 접힘 안에만 있습니다.

**측정**
- 두 패널의 y좌표가 같은지(가로 배치인지)
- 표의 가로·세로 스크롤 최대값(목표 0)
- 형제 위젯끼리 겹침 0
- 페이지 높이

## M3 · 유리 질감 비교 (GLASS) — mock_glass.py

**같은 M2-b 화면(1360, 한국어)을 세 변형 × 두 테마 = 6장으로 만듭니다.**
- G0 현재: 표와 차트가 페이지 바탕에 바로 놓임
- G1 기존 패널 질감: QFrame#panel의 그라데이션, 밝은 윗선, 2px 아랫선, 14px 모서리
- G2 새 'glass' 변형
  - 밝은 테마: top rgba(255,255,255,0.78) → bottom rgba(250,249,244,0.62), 윗선 rgba(255,255,255,0.95), 테두리 rgba(210,213,201,0.70), 아랫선 #D2D5C9
  - 어두운 테마: rgba(27,42,35,0.80) → rgba(21,32,27,0.66), 윗선 rgba(63,86,73,0.95), 아랫선 #0A110E

**측정**
- 각 패널 바탕에서 본문색과 muted색의 대비율. 목표는 4.5:1 이상입니다.
- 그림자 효과를 쓰지 않았다는 확인

## M4 · 분석 도구 설명 정리 (UI-12, 일반 규칙) — mock_toolpane.py

**입력**
- tests/desktop_acceptance.py의 합성 fixture로 Rates 곡선과 Derivatives(KOSPI200, synthetic)를 만듭니다.

**프레임 (1360, 한국어와 영어)**
- M4-a 현재
- M4-b 제안, 접힘
  - 오른쪽 열: 칩 "합성 데이터 · 실제 시장 데이터 아님" → 해설 → "▸ 출처·가정 보기"
  - 왼쪽 열: 표와 차트만
  - "분석 해설 · 선택 언어로 표시하며…" caption이 없어졌습니다.
  - 상태 줄은 "계산 완료" + 칩 "공식 판정 아님"입니다.
- M4-c 제안, 펼침
  - Rates의 "Simulated Treasury par curve … no market data provider was used." 문장이 한 번만 나옵니다.
  - Derivatives의 "synthetic · expiry … · as of …" 줄도 접힘 안에 들어 있습니다.
- M4-d 홈 카드 세 개와 System 패널을 정리하기 전과 후로 비교합니다.
  - 홈: 카드 아래 "이번 세션 몬테카를로 실행 수 · 투자 판정 아님" 한 번
  - System: 기본 화면에 "이 데스크톱은 미리보기 버전입니다" 한 줄과 "▸ 개발 정보"

## M5 · 알아보기 패널 상호작용 (UI-12) — mock_term_panel.py

순서대로 보는 화면 묶음(storyboard)입니다. 시제품 패널은 glossary.py의 기존 32개 용어 문장을 그대로 씁니다.

- M5-a Bonds 결과(M2-b)
  - 해설 라벨에서 "수정 듀레이션"을 프로그램으로 선택합니다(setSelection).
  - 놓은 자리 옆에 칩 "알아보기: 듀레이션"이 뜹니다.
- M5-b 1360에서 오른쪽 340px 열로 붙은 패널
  - 제목 "<glossary.name('duration')>"
  - 부제 "Duration · 금리"
  - 한 줄 요약
  - 구역: 개념(meaning) / 적용(use) / 이 화면에서의 의미 / 한계(limit)
  - "이 화면에서의 의미" 내용: "현재 결과: 맥컬리 듀레이션 · 년 = <표의 셀 글자>", "현재 결과: 수정 듀레이션 = <셀 글자>"
  - 아래쪽 버튼 "가이드에서 자세히 보기"
  - 후보 칩: 볼록성, DV01
- M5-c 1000x700에서 내용 위에 겹쳐 띄운 패널(내용 폭은 그대로)
- M5-d 핵심 지표 표의 "볼록성" 행에서 오른쪽 클릭 메뉴: "복사 / 모두 선택 / 알아보기: 볼록성"
- M5-e F1을 누른 상태
  - 검색창에 포커스가 있습니다.
  - 미리 들어간 말: "볼록성"
  - 검색창 안내 문구: "용어 검색"
- M5-f 설계/검증 결과 표에서 "VaR 95 / CVaR"를 선택한 상태
  - 패널은 VaR이고 후보 칩은 CVaR입니다.
  - "이 화면에서의 의미": "현재 결과: VaR 95 / CVaR = <셀 글자>"
- M5-g 용어를 찾지 못한 상태: "용어집에 없는 말입니다. 검색어를 바꿔 보세요."
- 영어판: 같은 프레임의 영어 버전. 제목은 Duration, 구역은 Concept / How it applies / On this screen / Limits

**측정**
- 칩 위치가 창 안에 있는지
- 패널 폭 340
- 1000px 겹침 모드에서 내용 폭이 변하지 않는지
- 포커스가 되돌아오는지

## 모아 보기

**contact sheet**
- 위치: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/mock/out/index.html
- 정적 HTML이고 외부 스크립트가 없습니다.
- M1-M5 순서로 이미지, 캡션, 측정값 요약을 담습니다.
- 각 목업 아래에 소유자 결정 항목을 표시합니다: open_questions 1, 2, 3, 4, 5, 6, 7

**만드는 순서와 승인**
- M1, M2, M3을 먼저 만들고 소유자 승인을 받습니다. A3-a 구현이 이것에 달려 있습니다.
- M4와 M5는 그 다음입니다.
- 승인 결과는 handoff 문서 결정란에 소유자 말 그대로 적습니다.

## 파일 담당과 병합 순서 (A1 ∥ A3)

원칙: 파일 하나에는 담당 트랙 하나를 둡니다. 말(용어, 번역, 상태어, 해설 문장)은 A1이, 배치(레이아웃, 접힘, 칩, 패널, 유리 질감)는 A3가 맡습니다. 예외는 아래 "줄 범위로 나눈 파일" 3개뿐입니다.

## 단계와 병합 순서

**P0 · 이음매 커밋**
- 두 브랜치를 만들기 전에 main에 넣는 작은 커밋 1개입니다.
- 화면 변화는 0입니다.
- 내용:
  1. `quantgen_desktop/reading_language.py` 새 파일(`PAIRS = ''`)을 만들고, translations.py에서 display_prose_catalog import 바로 뒤(587-588)에 한 줄을 넣습니다: `from .reading_language import PAIRS as _READING; _PAIRS += _READING`
  2. tools.py의 `text(..., kind=None)`와 `result_table(..., localized_columns=None)` 키워드를 만듭니다.
     - kind는 위젯 속성에만 저장하고 self.sections에는 넣지 않습니다. 그래서 내보내기와 AI 자료가 같습니다.
     - localized_columns를 주지 않으면 지금 규칙(headers[0]=='Metric')을 그대로 씁니다.
  3. 아래 호출 위치에 kind를 표시합니다.
     - provenance: rates.py:59, :118 / structuring.py:42 / signals.py:30 / strategy.py:45 / macro.py:45 / market_tools.py:44, :125, :196
     - notice: fx.py:37 / macro.py:48 / strategy.py:48 / market_tools.py:46, :127, :198
  4. 새 영어 키 목록을 확정합니다(문서로). 대상: 채권 표 항목명 12개, 머리글 4개, A3 화면 틀 문자열.
  5. 소유자가 승인한 용어 기준표 v0(금융 용어, 상태어, 단위어)를 docs/product/UI_TERMS_2026-11.md로 넣습니다. 이 파일은 이후 A1이 맡습니다.
- 확인 방법:
  - 관련 테스트(아래 표의 기존 파일들)가 P0 전후로 같은 결과를 냅니다.
  - A1 sweep harness(/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/harness.py)로 다시 만든 화면 문자열 목록 all.txt가 P0 전후로 같습니다.

**A1 ∥ A3-a**
- P0가 병합된 main에서 두 브랜치를 만듭니다. 예: claude/ui-a1-terms, claude/ui-a3-layout

**병합 순서**
- 권장은 A1을 먼저 병합하는 것입니다. A3-a는 rebase한 뒤 A1 한국어가 들어간 상태로 폭과 높이를 다시 재서(M1/M2 측정 스크립트) 병합합니다.
- A3-a가 먼저 끝나면 먼저 병합해도 됩니다. 이때 A1은 rebase만 하면 되고, 위 규칙을 지켰다면 충돌이 없습니다.

**A3-b**
- 두 트랙이 다 병합된 main에서 시작합니다. A1이 맡던 파일의 화면 정리입니다.

**통합 점검**
- harness로 한국어·영어 화면을 다시 훑습니다.
- 1360과 1000, 밝은 테마와 어두운 테마로 스크린샷을 찍습니다.

## A1 단독 파일

**번역 목록과 해설 모듈**
- quantgen_desktop/translations.py: P0 한 줄을 뺀 전부
- quantgen_desktop/display_prose_catalog.py
- quantgen_desktop/macro_narrative_language.py
- quantgen_desktop/market_narrative_language.py
- quantgen_desktop/market_diagnostics_language.py
- quantgen_desktop/model_narrative_language.py
- quantgen_desktop/rates_narrative.py
- quantgen_desktop/fx_narrative.py
- quantgen_desktop/bonds_portfolio_narrative.py: bond_notes()와 새 bond_fold_notes()를 뺀 전부

**분석 화면 파일**
- quantgen_desktop/rates.py, fx.py, structuring.py, macro.py, macro_records.py, signals.py, market_tools.py, portfolio.py
- quantgen_desktop/strategy.py: 18-21을 뺀 전부

**그 밖의 Native 파일**
- quantgen_desktop/watchlist.py, markets_view.py, market_chart.py, paper.py, connections.py, commentary.py
- quantgen_desktop/localization.py: QTreeWidget 머리글 번역(FM-6)
- quantgen_desktop/app.py 1002-1009: refresh_views의 실행 표와 홈 요약, ST-3 상태어

**core**
- core/ui_legacy_messages.py, core/ui_messages.py, core/i18n.py, core/ui_dynamic_messages.py
- core/education/glossary.py: 표준 이름, label/keep_english 필드, 새 용어, 별칭
- core/research/stock_profile.py
- core/research/connections.py: 표시용 상태어 지도가 필요할 때만
- core/ficc/forward_conventions.py: '오 년'
- 새 파일 core/status_labels.py: 두 앱이 함께 쓰는 상태어 라벨

**Flet**
- ui/*.py와 main.py 전부. 이번에 A3는 Flet을 건드리지 않습니다.

**문서**
- docs/product/UI_TERMS_2026-11.md

## A3 단독 파일

**Native**
- quantgen_desktop/app.py: 1002-1009를 뺀 전부
  - make_quant 520-577, MC 블록 903-931, 홈 caption 358-375, Library caption 613(A3-b), System 665-680
  - 패널 붙이기와 F1
- quantgen_desktop/bonds.py
- quantgen_desktop/tools.py: P0 키워드 이후 전부
- quantgen_desktop/chart_study.py, typography.py, charts.py, report_actions.py
- quantgen_desktop/indicator_guide.py: 상세 위젯 분리, caption 합치기. 가이드 문장 자체는 A1이 core/ui_messages.py와 glossary.py에서 바꿉니다.
- quantgen_desktop/data_rights.py: 배치만. 문구는 A1이 core/ui_messages.py에서 바꿉니다.
- quantgen_desktop/strategy.py 18-21
- bonds_portfolio_narrative.py의 bond_notes()와 새 bond_fold_notes()

**새 파일**
- quantgen_desktop/reading_language.py (P0에서 빈 파일로 만듦), reading.py, mc_reading.py, term_panel.py
- core/education/term_lookup.py

**core 수정**
- core/research/analysis.py: RF_FALLBACK_NOTE 상수
- core/research/mc_disclosure.py: 변동성 설명의 한국어 변형

## 줄 범위로 나눈 파일 (충돌을 피하는 방법)

1. **quantgen_desktop/app.py**
   - A1은 1002-1009만 고칩니다. 그 밖의 줄은 A3가 맡습니다.
   - A1이 필요한 나머지는 모두 번역 목록에서 처리합니다: 메뉴 이름(설계/검증, 분석), Light/Dark, 몬테카를로 탭, 표 머리글.
2. **quantgen_desktop/strategy.py**
   - A3는 18-21(입력 caption)만 고칩니다. P0의 kind 표시(45, 48)는 이미 기반에 들어 있습니다.
   - A1은 12(출처 콤보), 35-65(표와 문장)를 고칩니다.
3. **quantgen_desktop/bonds_portfolio_narrative.py**
   - A3는 bond_notes()(현재 122-134)와 그 바로 뒤에 새로 넣을 bond_fold_notes()만 고칩니다.
   - A1은 bond_korean(56 부근), hedge_text(137-) 등 나머지를 고칩니다.
   - hunk 사이에 바뀌지 않는 줄이 남도록 A3는 함수 본문 안에서만 고칩니다.

## 순서로 충돌을 막는 공유 파일

- **translations.py와 tools.py**: P0가 한 번만 건드립니다. 그 뒤로는 각각 A1, A3만 고칩니다.
- **ToolPane 분석 화면 파일들**: P0가 kind 표시를 넣은 뒤로는 A1만 고칩니다. A3는 tools.py 안에서 kind로만 위치를 정합니다.
- **reading_language.py와 translations.py의 키 겹침**
  - A3 테스트가 reading_language.PAIRS의 영어 키가 translations._PAIRS/_TERMS, macro_narrative_language.PAIRS와 겹치지 않는지 검사합니다.
  - 겹치면 A1 키가 이깁니다. 'Key-rate DV01'처럼 이미 있는 키는 A3가 새로 넣지 않습니다.
- **core/education/glossary.py**: A1만 고칩니다. A3의 term_lookup.py는 TERMS, BY_KEY, name/summary/sections를 읽기만 하고, 모자란 별칭은 자기 파일의 보조 지도에 둡니다.
- **README.md와 docs**
  - 두 브랜치 모두 README.md를 고치지 않습니다.
  - 두 번째로 병합하는 트랙이 README 한 커밋에서 이름 변경(A1)과 알아보기 기능 설명(A3)을 함께 적습니다.

## 테스트 파일 담당

**A1**
- tests/desktop_language_acceptance.py (:62, :77)
- tests/desktop_market_tabs_acceptance.py (:22)
- tests/desktop_watchlist_acceptance.py (:88)
- tests/desktop_macro_language_acceptance.py
- tests/desktop_bonds_portfolio_language_acceptance.py
  - :126의 bond_notes 비교는 A3가 바꿀 필요가 없도록 설계했습니다. bond_notes()의 반환이 바뀌어도 같은 함수와 비교하기 때문입니다.
- tests/research_home_acceptance.py (:93, :166)
- tests/desktop_startup_acceptance.py
- tests/glossary_search_acceptance.py
- tests/macro_ui_views.py
- 새 파일 tests/desktop_terms_a1_acceptance.py

**A3**
- tests/desktop_acceptance.py (:307-310, :390, :404)
- tests/mc_bootstrap_disclosure_acceptance.py (:530-556)
- tests/chart_c_theme_acceptance.py (:72-95)
- tests/desktop_typography_acceptance.py (:325-348)
- 새 파일 tests/desktop_a3_layout_acceptance.py, tests/term_lookup_acceptance.py, tests/desktop_term_panel_acceptance.py

**위 목록에 없는 테스트가 깨질 때**
- 그 테스트를 깨뜨린 트랙이 자기 브랜치에서 고칩니다.
- 그 파일을 상대 트랙이 맡고 있으면 handoff 문서에 적고, 상대가 고친 뒤 병합합니다.
- 전체 테스트를 실행해 본 적이 없으므로 이 목록이 완전한지는 [미확인]입니다.

## handoff 규칙과의 관계

CLAUDE.md의 push_handoff.py는 다른 작업의 handoff나 살아 있는 checkpoint가 branch에 있으면 exit 3으로 거부합니다(CLAUDE.md [읽음]). 그래서 두 트랙을 따로 두 작업으로 등록하면 서로 막힙니다.

권장 방식:
- **작업 하나**로 등록합니다. 예: "⑬-2 A1+A3"
- CURRENT.md 하나에 두 브랜치(work_branch 두 개는 문서 6장에 따로 적음)와 각 트랙의 done_ids/next_ids를 둡니다.
- 문서 게시는 한 세션(조정자)만 합니다.
- 다른 트랙의 작업자는 handoff를 게시하지 않고, 조정자에게 커밋과 검사 결과를 넘깁니다.

## 원래 A1 목록에서 A3로 옮기는 항목 (파일 담당에 맞춤)

- NR-2: MC 설명 문장 한국어화. UI-9와 같은 코드(app.py:909-929)입니다.
- MX-8: Build & Test 부제와 홈 버튼(app.py:521, 373)
- ST-4: System 패널 상태어(app.py:665-676). 단어는 용어 기준표를 따릅니다.
- N-22/MX-3: bonds.py:48 caption
- BD-1~BD-4의 코드 부분: localized_columns, 단위를 항목명으로 옮기기. 한국어 항목명은 A1이 translations.py에 넣습니다.

## A3에서 A1로 넘기는 항목

- RL-1: Macro와 FX 표의 출처·관측일 열. macro.py와 fx.py가 A1 파일입니다. 소유자 결정 뒤에 합니다.
- bond_notes 밖에 있는 채권 해설 문장 다듬기

## 소유자께 여쭐 것

1. **출처·관측일 줄을 어디까지 가릴까요?** PR #71 결정은 "라이브 화면에 공급사·관측일 열 없음"이었습니다. 이것을 분석 결과 본문까지 넓혀도 되는지 정해 주세요.
   - 대상: 분석 도구, 채권, 설계/검증 설명
   - 처리: 출처·관측일·관측 수 줄을 "출처·가정 보기" 접힘으로 옮기고 툴팁에도 남깁니다. 합성, 지연, 실패 상태는 칩으로 늘 보입니다.
   - 같은 질문: Macro 지표표의 Source와 Observed date 열, FX의 Data sources 표(RL-1)도 화면에서 숨길까요?
2. **유리 질감은 어느 안으로 할까요?**
   - G1: 기존 패널 질감을 그대로 씁니다.
   - G2: 반투명 'glass' 변형을 새로 만듭니다. 그림자와 blur는 쓰지 않습니다.
   - 범위도 정해 주세요: 채권 화면에만 적용할지, 모든 결과 블록에 적용할지.
3. **채권 표를 가로로 놓은 뒤 오른쪽 빈 공간을 어떻게 할까요?**
   - (a) 두 패널 높이를 같게 둡니다(권장).
   - (b) 헤지 도구일 때 선물 헤지 결과를 만기별 DV01 아래에 둡니다.
4. **채권 표의 단위를 항목명으로 옮겨도 될까요?** 예: '맥컬리 듀레이션 · 년' + 값 '8.163'.
5. **표시 반올림을 허용할까요?** 내보내기의 원래 값은 바뀌지 않습니다.
   - 시나리오 충격 칸: 정수 bp('3y +2'). 원래 값은 툴팁에 둡니다.
   - MC 구간 값: 4자리('0.0000–0.0919').
   - 시장 차트 볼린저 밴드 값: 정수(A3-b).
6. **설계/검증 화면에서 두 가지를 정해 주세요.**
   - FRED 조회에 실패해 3%를 쓸 때 "(가정값)" 표시를 남길까요? 실행 기록에는 이 사실이 저장되지 않습니다.
   - 데이터 출처 콤보에서 'FMP' 항목을 그대로 둘까요, 숨길까요? B1: FMP 키 없음, 대체 공급사 미정. 항목 이름 'Auto · KIS / FMP' → '자동'은 표시만 바뀝니다.
7. **알아보기 패널 1단계 범위는 아래와 같습니다. 이대로 확인해 주세요.**
   - 로컬에서만 동작하고 AI는 부르지 않습니다. "AI에게 더 묻기"는 넣지 않습니다.
   - 창 폭 1280px 이상에서는 옆에 붙이고, 그보다 좁으면 내용 위에 겹쳐 띄웁니다.
   - F1로 열고 Esc로 닫습니다.
   - "이 화면에서의 의미"는 화면에 이미 있는 값만 인용합니다.
   - 용어별 해석 문장(숫자를 다시 말하는 새 문장)은 2단계로 미루고 소유자 검토를 받습니다.
8. **Flet 브라우저 앱에도 A3를 적용할까요?** 이전 결정에 따라 이번 계획에서는 Flet을 바꾸지 않습니다. 하려면 A1을 병합한 뒤 별도 단계로 합니다. 해당 작업:
   - card()에 ft.Blur 적용
   - ResponsiveRow로 가로 배치
   - Text.on_selection_change로 고정 위치 "알아보기" 버튼
9. **글자 크기 체계를 그대로 둘까요?** 이번 계획은 caption 12px을 유지하고, 긴 문장은 14px 본문으로 접힘 안에 둡니다. caption을 키우려면 이미 승인하신 글자 크기 체계와 테스트를 바꿔야 합니다.
10. **P0 용어 기준표 v0를 승인해 주세요.** 두 트랙이 동시에 시작하는 전제 조건입니다.
    - 기준표가 정할 것:
      - 모형 / 모델
      - 제공처 / 공급자 / 공급처
      - 샤프 지수
      - 행사가격
      - 맥컬리
      - 몬테카를로
      - 거래일 수 / 관찰 기간
      - 상태어: 완료, 미실행, 부분, 미검증, 미동결, 합성 데이터
    - 함께 정할 것: UI-15 "분석"이 왼쪽 메뉴의 "분석 도구"와 나란히 놓이는데 괜찮은지(A1 sweep 지적).
11. **원장 ID를 확인해 주세요.**
    - 제안: ⑬-2/a3-ui9, ⑬-2/a3-ui11b, ⑬-2/a3-ui12/a(설명 정리), ⑬-2/a3-ui12/b(알아보기 패널), ⑬-2/a3-ui12/c(A3-b), P0는 ⑬-2/a1a3-p0
    - ID를 정의하는 QUANTGEN_REMAINING_2026-11-03 문서가 저장소에 없습니다.
    - 원격 최신 원장은 네트워크가 막혀 확인하지 못했습니다. 로컬 사본(84c76b4)에는 a3-type, a3-rail, a3-controls만 있습니다.
12. **새 용어 약 30개의 설명은 누가 쓸까요?** 개념·쓰임·한계를 한국어와 영어로 써야 합니다. 이 계획은 A1에 넣었고, 금융 정의이므로 소유자 검토가 필요합니다.
13. **진행 중인 다른 작업과 겹치는지 확인이 필요합니다.** §10 재작업(Crypto → Options → Models/ETF → AI)이 market_tools.py나 MC 쪽 파일을 고친다면 세 번째 트랙이 됩니다. 그 작업의 파일 목록은 보지 않았습니다 [미확인].
