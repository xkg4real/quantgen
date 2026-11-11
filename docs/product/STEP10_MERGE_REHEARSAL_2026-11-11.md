# Step 10 병합 리허설 (결정 P3), 2026-11-11

## 소유자용 요약 (다섯 줄)

1. 결정 P3(Step 10 확인이 끝난 뒤 Claude가 main을 연구 브랜치에 합치는 일)를 연습용 브랜치에서 미리 해 보았습니다. main은 앱의 기준 줄기이고, 연구 브랜치는 Nautilus 작업이 들어 있는 별도 작업 줄기입니다. push(GitHub에 올리는 일)는 하지 않았고 실제 병합도 아닙니다.
2. 충돌(양쪽이 같은 곳을 고쳐서 git이 스스로 합치지 못한 파일)은 5개였고 모두 풀었습니다. 4개는 정해진 규칙대로 풀리고, Bonds 화면 파일 하나(`ui/bonds_page.py`)는 아홉 군데를 손으로 합쳐야 했습니다. 그 뒤 검토에서 합친 Bonds 화면의 결함 다섯 가지가 더 나와, 연습용 브랜치의 둘째 커밋에서 고쳤습니다.
3. 문법 검사와 상태 파일 점검은 통과했습니다. Bonds 화면 검사(테스트)는 연구 브랜치 쪽 33개 중 5개, main 쪽 2개가 실패합니다. 모두 한쪽 검사가 다른 쪽이 바꾼 화면 문구를 기대해서 생긴 실패입니다. 수정 3개를 더하면 모두 통과합니다(저장소 밖 사본에서 확인). 3개 가운데 2개는 화면이 아니라 검사가 기대하는 문구를 바꾸는 것이고, 1개는 한글 문구를 더하는 것입니다.
4. 소유자가 정해 주실 것은 두 가지입니다. (가) 그 수정 3개와 준법 문서 기준선(검토한 파일들의 지문 목록) 갱신을 P3 병합에 함께 넣어도 되는지. (나) Bonds 화면에서 고른 방식 일곱 가지를 그대로 쓸지(본문 2.4): 라벨, 제공처 메시지, 표 머리글, 곡선 문장 위치, 칩 색, 숫자 입력 규칙, 한글 헤지 요약의 반올림과 매수·매도 표시. 일곱째는 PC 앱의 헤지 문구도 함께 바꿉니다. 예: 포지션 DV01 682.5, 전환계수 1이면 전에는 "반올림 10, 잔여 DV01 +32.50"이었고 지금은 위 타일과 같은 "반올림 11, 잔여 DV01 -32.50"입니다. 매도 포지션(-798.19)은 전에는 "선물 매도 -9.82계약 · 반올림 -10"이었고 지금은 "선물 매수 9.82계약 · 반올림 10"입니다.
5. 캐시 없는 전체 검사는 아직 하지 않았습니다(주 세션이 합니다). 캐시는 보호 대상 자료 폴더(`docs/asset_expansion/cache`)입니다. 연습하는 동안 main이 두 번 바뀌었습니다(`96cca1f`에서 `9fc3817`로, 다시 `83046c1`로). 이 연습은 `9fc3817` 기준입니다. main이 바뀌면 연습은 낡으므로 Step 10 때 다시 해야 합니다.

The rest of this document is in English. A statement marked "not verified" was not traced to a source line or a run.

## 1. What was merged into what

| Role | Commit | Note |
|---|---|---|
| Research head (merged into) | `8a8c2475b1a1480c7c6596a9d89619c755ab1e2a` | `origin/claude/amazing-gauss-tdiguu`, committed 2026-11-04 17:46 KST |
| main (merged in) | `9fc38175c79549b9cb2082193051832ab1d06f07` | `origin/main` after PR #102, committed 2026-11-11 12:21 KST |
| Merge base (the last commit both branches share) | `bb35b3b4bf4bf1eb602d138a396ac90e253c035b` | PR #69, the start of the old merge freeze |
| Rehearsal merge commit | `c582f150c3bbb8717f38a79fd831f7926cace5e1` | parents `8a8c247` and `9fc3817`; local branch `scratch/step10-rehearsal`, no upstream, never pushed |
| Review-fix commit | `a5f904aed76a93f0f99e907e3599ffcce4d547d9` | parent `c582f15`, same local branch, never pushed. Two files change, both among the five conflicted files; no test file is edited (section 2.3, 2.4) |
| main today | `83046c194bdbd7e01b528dd3ab910e0cc5f5d7c6` | `origin/main` after PR #103, 2026-11-11 13:53 KST. The rehearsal was not redone on it (section 7) |

The command was `git merge --no-ff --no-commit 9fc3817...` in a scratch worktree at the research head. This is the direction decision P3 names: main into the research branch. It is a rehearsal only. Decision H-D5 keeps main out of the research branch until the Step 10 checks are done. Both decisions are recorded on main: P3 in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` lines 706 and 758 at `83046c1`, H-D5 at line 508.

Since the merge base, main at `9fc3817` has 260 commits and 287 changed files; the research branch has 55 commits and 269 changed files, 247 of them new. These counts leave out `docs/asset_expansion/cache`, which was never listed. Eleven files changed on both sides. Five of them conflict. Git merges the other six by itself (section 3).

main moved twice while this work ran. The first pass merged `96cca1f`. At 12:21 KST main became `9fc3817` (PR #102, the provider parity tool, 16 commits). The first pass was dropped (`git merge --abort`) and the merge was redone on `9fc3817` with the same scripts. The conflict blocks of the three Python files were the same in both passes (same sha256 for each block) and the resolved files came out byte-identical. The rulings log gained 22 lines from main. The status snapshot differs only in its time stamp. At 13:53 KST main became `83046c1` (PR #103, 8 more commits, ten changed files). Of the five conflicted files only the rulings log changed there: one section appended, 69 lines, nothing above it touched. The other four are the same blobs on `9fc3817` and `83046c1`.

## 2. The five conflicts

A blob id is git's fingerprint of one version of one file. The table says which versions the rehearsal saw. The recipes below are valid as they stand only while both sides still have these blob ids.

| File | Research `8a8c247` | main `9fc3817` | Resolved in `c582f15` | After the review fixes, `a5f904a` |
|---|---|---|---|---|
| `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | `2fffce7151673c129d79daa6ae6fc1c7fc4df8dc` | `b02372ab20fafb820a0ee6d4273944760a76d84f` | `ed6fad0096b7c4b01c2df9e71bdab4eab002ef20` | unchanged |
| `qa/research_status.json` | `1ad0968939324884922d62d3260945988507d4cd` | `16d155ae0d31ebc8370fb49eec771da8647e20b5` | `49d14b2f74e1c1c4f016ea225d59c67cdd539ceb` | unchanged |
| `quantgen_desktop/bonds_portfolio_narrative.py` | `b537a19cade48a254b07b5280abbca701bab0d47` | `575406a8e43164564676a97bd1596fd525df1d31` | `b945bd62eea8849daf6b3114ae863a729d28d635` | `ead09e41d374d0ffa298cbfd62e7928142f38474` |
| `ui/bonds_page.py` | `f95b1e39e5da977a426465e349e46cf44bd740f3` | `141690cc5d1ddb91e465f7263d393cb6918d10f2` | `c849b40a8fb91788e3bafd2d1eea9c632dc47cae` | `e90d7f47da214aa955b76c54f5ab5cc56babd9ab` |
| `ui/qcharts.py` | `2dde50cc226109c31a2b58c4f07305af36404225` | `5795ad0eea3508bec8d9ac48459d22cc7719fae9` | `5795ad0eea3508bec8d9ac48459d22cc7719fae9` (main's blob) | unchanged |

### 2.0 Start

Run in a clean worktree of the research branch. Nothing here pushes.

```bash
R=$(git rev-parse HEAD)                 # research head
M=$(git rev-parse origin/main)          # main, as fetched for Step 10
B=$(git merge-base "$R" "$M")           # expect bb35b3b... while no other merge has happened
# The bridge's code hash must not move with the merge. Both tables' owner_confirmed quote it,
# and the runner refuses with R-11 when the tree no longer matches. This must print nothing:
git diff --name-only "$B" "$M" -- config.py docs/asset_expansion_study.py docs/macro_overlay_study.py \
  core/quant/gate_stats.py core/quant/gate_ledger.py core/quant/cardp.py core/quant/cards.py \
  core/quant/card_lines.py core/quant/instruments.py core/quant/costed.py core/quant/validate.py \
  core/quant/strategies.py core/quant/gjr.py core/quant/gate_package.py requirements-nautilus.txt tools/nautilus
git merge --no-ff --no-commit "$M"
git diff --name-only --diff-filter=U    # expect the five files of the table above
# One check per file: are both sides still the versions of the rehearsal?
same() { test "$(git rev-parse "$R:$1")" = "$2" && test "$(git rev-parse "$M:$1")" = "$3" && echo "same: $1" || echo "CHANGED: $1"; }
same quantgen_desktop/bonds_portfolio_narrative.py b537a19cade48a254b07b5280abbca701bab0d47 575406a8e43164564676a97bd1596fd525df1d31
same ui/bonds_page.py f95b1e39e5da977a426465e349e46cf44bd740f3 141690cc5d1ddb91e465f7263d393cb6918d10f2
same ui/qcharts.py    2dde50cc226109c31a2b58c4f07305af36404225 5795ad0eea3508bec8d9ac48459d22cc7719fae9
```

If the code-hash line prints a path, stop and tell the owner before merging: `owner_confirmed` would no longer quote the merged tree. The list is what the runner hashes (`tools/nautilus/runner.py` lines 183-190 on the research branch: every `.py` under `tools/nautilus`, the golden `.json` files, `requirements-nautilus.txt`, the eleven harness sources, the study script and `config.py`), plus `core/quant/gate_package.py`, which holds the list of harness sources (lines 36-38). The line compares main with the merge base, so it shows what main changed; main has no `tools/nautilus` folder today, and a file added there by main would be printed. It prints nothing for `bb35b3b..9fc3817` and for `bb35b3b..83046c1`. On the rehearsal the fourteen single files, `requirements-nautilus.txt` and the `tools/nautilus` tree (`411fbc2e`) have the same ids on `8a8c247`, `c582f15` and `a5f904a`, so the rehearsal leaves the code hash as it was.

If a line says `CHANGED`, the recipe for that file no longer applies as written. Resolve that file again by its rule below.

### 2.1 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`

- Research side since the base: three insertions. The first two merge by themselves: 11 lines inside the 2026-10-27 section, and 229 lines that end that section and add the sections of 2026-10-28 to 2026-10-30. The third is one new section at the end, "2026-11-04 (Step 7A 세션): 사전 점검, 결정, 7A.1 승인 문장" (commit `0bc9595`, 2026-11-04 04:00 KST).
- main side since the base: only text appended at the end. At `9fc3817` that is seven sections, from "2026-11-04 main 병합 동결 해제 (U4-나)" (commit `24e9ece`, 2026-11-04 16:25 KST) to "2026-11-11 ⑤-2 대조 도구의 버전 고정 위치 (P1)". At `83046c1` there is an eighth, "2026-11-11 ... 결정 요청 P·A·B·C·D 묶음에 대한 답 "전부승인"", which records P2, P3 and P4.
- Rule: keep every section of both sides, in date order, with no sentence changed. The research section is older than all of main's new sections, so it goes first. The result is the research file followed by the text main appended.
- Checked: the result equals `research file + main's appended text` byte for byte; no line of either side is missing; LF line endings. The merged file has 20 headings: 13 from the research file and 7 appended by main.
- Not changed: main's own three sections of 2026-11-04 are not in clock order among themselves (16:25, 17:48, 16:40 by commit time). They stay in main's order.

```bash
F=docs/nautilus_bridge/OWNER_RULINGS_LOG.md
n=$(git show "$B:$F" | wc -c)
cmp -n "$n" <(git show "$B:$F") <(git show "$M:$F") || echo "STOP: main changed text above its appended part"
{ git show "$R:$F"; git show "$M:$F" | tail -c +$((n+1)); } > "$F"
# The section dates must still rise through the whole file:
grep '^## ' "$F" | sed -E 's/^[^0-9]*(20[0-9]{2}-[0-9]{2}-[0-9]{2}).*/\1/' | sort -c && echo 'dates rise'
# Every heading of both sides must be there once:
diff <(cat <(git show "$R:$F" | grep '^## ') <(git show "$M:$F" | grep '^## ') | sort -u) <(grep '^## ' "$F" | sort) && echo 'every heading once'
git add "$F"
```

Both check lines pass on the merged file of the rehearsal (`dates rise`, `every heading once`). The fix helper also ran three negative tests: a heading out of date order, a missing heading and a doubled heading are each caught. The `cmp` line passes for main at `83046c1` too, so the recipe holds there as written.

The recipe stops being right if main edits an older section, or if the research branch adds a section newer than one of main's.

### 2.2 `qa/research_status.json`

- Both sides: the file is written by `tools/status/snapshot.py`. The conflict is the time stamp and the README fingerprint.
- Generator: it reads `README.md`, `qa/acceptance_results.json` and `core/calendars/data/MANIFEST.yaml` and nothing else (source: `tools/status/snapshot.py` line 23, `INPUTS`). It opens no protected path. Its output is fixed by those three files, except the `generated_at` time stamp.
- Rule: regenerate. This is what the earlier merge `92cc00f` did.
- The generator also rewrites its own block in `README.md`. In the rehearsal that changed one line (917): `749/870 PASS; 0 FAIL; 121 NOT_RUN` became `844/964 PASS; 0 FAIL; 120 NOT_RUN`. The numbers come from the Windows Step 7A `qa/acceptance_results.json` of the research branch. No other byte of `README.md` changed, and it stayed CRLF.
- `qa/acceptance_results.json` was not written: md5 `01ba606fa04d95bb32bf04507b492306` before and after, and the same on `a5f904a`.
- Finding: at the research head `8a8c247` the snapshot is already stale (`--check` fails there, tested on extracted copies of the four files). The merge message of `92cc00f` predicted this.

```bash
python -B -m tools.status.snapshot --write     # needs PyYAML; run on Linux
python -B -m tools.status.snapshot --check     # expect {"status": "consistent", ...}
md5sum qa/acceptance_results.json              # must not change
git add qa/research_status.json README.md
```

Run it on Linux: on Windows `write_text` would turn the file's line ends into CRLF (read from the code, line 145; not run on Windows). At Step 10 run it after the Windows full run has replaced `qa/acceptance_results.json` and after the README rows were updated, because all three inputs change the result.

### 2.3 `quantgen_desktop/bonds_portfolio_narrative.py`

- Research side (`2c299c9`): the DV01 sentence of the Korean bond read now says the DV01 is per basis point of the bond's own yield, and shows two decimals below 100.
- main side (`44c13da`, approved A1 words): 매콜리 became 맥컬리, 볼록성 became 컨벡시티(볼록성), 샤프비율 became 샤프 지수.
- These are two different changes in the same lines. Rule: main's words with the research sentence. The five resolved lines:

```python
        f'수익률 {_pct(a.ytm,3)}입니다. 맥컬리 듀레이션 {a.macaulay:.2f}y, '
        f'수정 듀레이션 {a.modified:.2f}, 컨벡시티(볼록성) {a.convexity:.1f}입니다.',
        f'명목금액 {_money(b.notional)}의 DV01은 채권 자체 수익률 bp당 '
        f'{_money(a.dv01) if abs(a.dv01) >= 100 else f"{a.dv01:,.2f}"}입니다. '
        f'그 수익률이 +100bp 오르면 컨벡시티를 반영하기 전 대략 {_money(a.dv01*100)}의 손실이 발생합니다.',
```

- Second change, made in `a5f904a` (review finding F1, choice 7 of section 2.4): `hedge_text` (lines 144-159) follows the side and the rounding that the research branch made the page show. It rounds with `core.ficc.bonds.round_contracts` (halves away from zero), names the side (매도 or 매수, Sell or Buy) and shows the contract counts without a sign, in both languages. So the rule for this file is now: main's words with the research sentence, and main's hedge lines adjusted to what the research branch made the page say.
- `hedge_text` also writes the hedge label of the native PC app (`quantgen_desktop/bonds.py` line 118). The label's source text at lines 110-112 of that file still uses `round()`; on screen it is replaced by `hedge_text` in both languages (`quantgen_desktop/localization.py` lines 25-28). That file is outside the five conflicted files and was left alone.
- Checked on `a5f904a`: `tests.desktop_bonds_portfolio_language_acceptance` passes 9 of 9. It holds the research test for the DV01 sentence, main's test for 샤프 지수, and a test that the English and Korean hedge lines carry the same numbers (line 136).

```bash
git checkout a5f904aed76a93f0f99e907e3599ffcce4d547d9 -- quantgen_desktop/bonds_portfolio_narrative.py   # if the local commit still exists
# otherwise: git checkout --ours <file>, then git apply the first patch of Appendix A, then git add <file>
# to take the other answer of choice 7 (main's hedge lines as they were): git checkout c582f150c3bbb8717f38a79fd831f7926cace5e1 -- <file>
```

### 2.4 `ui/bonds_page.py`

This is the one file that is not mechanical. Git reports nine conflict blocks.

- Research side (`4709cf2`, the owner-approved Bonds patch ②-5/b, +316/-74): strict number parsing with errors shown on the field, every input read once per Run, only the newest Run paints, a notice when inputs change after a Run, the hedge side with rounding and net DV01, more notices and tooltips, a larger payload.
- main side (`44c13da`, `c14f244`, `c8380a2`, +78/-52): the Korean screen of the owner UI review of 2026-11-10. Short labels with a helper line, grouped numbers, a hidden curve selector, one form row, Korean twins for tiles, chips and banners, Korean and English sections in the Analysis panel.
- main does not have the Bonds patch. The research branch does not have the Korean screen. So neither side is a later form of the other: both must be kept.
- Rule: the research branch's logic inside main's display. Where one side alone changed an element, that change is taken. Where both changed it, the English text and the state come from the research branch, and main's Korean twin is kept and adjusted only where the research branch changed what the element says.
- The rule did not hold everywhere in `c582f15`. Two of main's Korean texts are built outside the page and were not adjusted: the hedge lines (`hedge_text`) and the key-rate chart title (a pattern in `ui/fcharts.py` line 315). And main's regrouping of digits worked against the research branch's strict parser and its "inputs changed" notice. The review found these (its findings F1 to F4) and `a5f904a` fixes them; the table and the choices below describe `a5f904a`.

| Block | Research side | main side | Taken |
|---|---|---|---|
| 1 `_num` | strict parser, field errors, ranges | `parse_number` | research. Since `a5f904a` two helpers follow it: `_grouped` (lines 109-113) and `_strict_grouping` (lines 116-129) |
| 2 input fields | tooltips, hint, `hedge_row`, stale notice, lock and state, `_raw`, `on_input`, `on_tool` | `num()`, `with_helper`, `number_field`, `hide_source`, hedge fields hidden one by one | main's fields and labels; research's tooltips, hint, stale notice, state and handlers. Since `a5f904a`: main's regrouping on blur is kept only for text the strict parser reads (the three `number_field` inputs are wrapped, lines 156, 161, 169), and the input snapshot `_raw` (lines 183-188) takes those three fields as they read once editing ends |
| 3 banners and chips | new "Curve check" notice, new maturity warning, new chip wording, three chip colours | `synthetic_notice` (short banner in two languages, provider message folded under it), `lchip` | main's banner; research's two notices; `lchip` with research's English and colours and main's Korean |
| 4 risk tiles, narrative | tooltips, DV01 with decimals, a curve sentence added to the narrative | spacing, `bond_text`, `extra` | research tiles, main spacing; the narrative stays the plain bond read; the curve sentence is kept as `curve_line`, since `a5f904a` with a Korean twin `curve_line_ko` (lines 369-374) |
| 5 Carry tile | tooltip | Korean label (`ko_stat`) | both |
| 6 Breakeven tile | `n/a` when the bond matures inside the horizon, three tooltips | spacing | research tile, main spacing |
| 7 scenario table | header words "Shock (bp, cc zero rates)", "P&L % of MV" | `table_header` with Korean, `literal_text` cells | main's mechanism with research's header words |
| 8 hedge result to the end | side, rounding, net DV01, two warnings, conventions notice, `paint(blocks)` | Korean twin of the hedge notice, `hedge_en`, `extra`, `sections=localized(...)` | research content; Korean twin rewritten for the new numbers; main's sections; the curve line shown as a notice in both languages above the Analysis panel (lines 527-528) |
| 9 form row | two rows | `form_row` with `action` | main |

Edits outside the nine conflict blocks. In `c582f15`: `_SCENARIO_HEADERS_KO` (line 39) got the Korean for the two research headers. In `a5f904a`: the key-rate chart call, which git had merged by itself, now passes a Korean title (`title_ko`, line 414); the two helpers `_grouped` and `_strict_grouping` are new; and the import line from `ui.components` (lines 35-36), left as git merged it in `c582f15`, gains `group_digits`. `parse_number` is still imported and unused there.

Choices made inside this file. Each has another possible answer, so each is a point for the owner or the lead:

1. Field label `Position DV01` with the helper line "Blank = from the calculator" (main). The research tests look the field up by the old label `Position DV01 (blank = calculator)` (`tests/bonds_screen_acceptance.py` lines 503, 523, 532). main's test looks it up by the new label (`tests/ficc_pages_display_acceptance.py` line 152). No page can satisfy both tests.
2. Synthetic banner: main's short banner, with the provider's message folded under it (`ui/ficc_widgets.py` line 136). The research tests expect the failure reason inside the banner text (`tests/bonds_screen_acceptance.py` lines 559-560 and 583). The reason is still on the screen, one click away. main's fixed sentence says the curve is simulated "because FRED did not answer". That is not exact when FRED answered with values the research branch's new range check refuses. Not changed.
3. Scenario table headers: the research words, through main's Korean mechanism. main's test expects the old words `Shock` and `P&L %` (`tests/flet_a1_headers_acceptance.py` lines 194-195). The research test expects the new words (`tests/bonds_screen_acceptance.py` line 452). No page can satisfy both tests.
4. Curve sentence: the research branch added it to the narrative. main's test requires the narrative to equal the plain bond read and the Korean and English sections to hold the same parts (`tests/flet_korean_narratives_acceptance.py` lines 296-313). The rehearsal shows the sentence as its own notice above the Analysis panel, since `a5f904a` in Korean and in English. The cost: the Analysis panel itself no longer names the curve source in either language, in its narrative or in its sections. The research assertion at `tests/bonds_screen_acceptance.py` line 561 carries the comment "# narrative", but it matches any text on the screen; it now passes on the notice, not on the narrative. So "both sides' tests pass" does not show that the research behaviour is kept. The AI request is built from the payload, which still has `data_source` SYNTHETIC after the field filter (`ui/ai_panel.py` line 205).
5. Chip colour: the research three colours (error for synthetic, warning for a curve with a note, success otherwise) replace main's two.
6. Numbers: the research parser refuses `4,5`, `1_000`, spaces and the Unicode minus in all eight fields. main's `parse_number` accepted the last three. `1,000,000` is accepted by both. In `c582f15` that held for the three grouped fields (Notional, CTD DV01 / contract, Position DV01) only until the field lost focus: main's `number_field` regroups the digits on blur with its looser reader, so `4,5` became `45` and `1_000` became `1,000` before Run read them (`ui/components.py` lines 304-346). `a5f904a` keeps the research answer: these fields regroup only text the strict parser reads; anything else stays as typed and Run refuses it on the field. The other answer is main's reading for these three fields: remove the three `_strict_grouping` wrappers. Not verified: whether a live Flet window delivers the blur before the Run click; the handlers were called directly.
7. Korean hedge summary: main's test requires the Korean "선물 헤지" section of the Analysis panel to equal `hedge_text` (`tests/flet_korean_narratives_acceptance.py` lines 307-309), and `hedge_text` also writes the native PC app's hedge label. In `c582f15` that section disagreed with the tiles above it: `hedge_text` rounded with Python's `round` (half to even) and always said 매도, while the page rounds half away from zero and names the side. Each side agreed with itself before the merge; only the merged page contradicted itself. `a5f904a` changes `hedge_text` to the page's side and rounding in both languages, which changes the native label too. Two examples. Position DV01 682.5, CTD 65, CF 1: before "반올림 10" and "잔여 DV01 +32.50", now "반올림 11" and "잔여 DV01 -32.50", as the tiles say. Position DV01 -798.19, CTD 65, CF 0.8: before "선물 매도 -9.82계약 · 반올림 -10", now "선물 매수 9.82계약 · 반올림 10". The other answer: restore the file from `c582f15` and accept the disagreement on the Flet screen. Where the rounding rule comes from: audit finding BS-28 (`docs/audit/2026-10-27/bonds_screen_audit.md` line 499 on the research branch: round away from zero with `round_contracts`, marked applied), part of the Bonds patch the owner approved as a whole ("Bonds 패치 적용은 진행해주세요", research-branch `OWNER_RULINGS_LOG.md` line 475, recorded at line 488). The owner's request for that audit asks that the residual DV01 after rounding matches the screen text (`docs/audit/2026-10-27/bonds_screen_request.md` line 72). Not verified: an owner sentence that names the rounding rule itself; none was found in these files. One more fact for this choice: main's rulings log at `83046c1` (lines 737-741) quotes an owner decision UI-D1, "UI 기준 앱은 네이티브" (the native PC app is the reference app, the Flet web screen is not). The original record of UI-D1 was not found (not verified). It matters here because this choice changes the native app's label, and because choices 1 to 6 concern the Flet screen only.

Korean wording written by the rehearsal, to be reviewed:

| Where | Korean |
|---|---|
| Chip 2 (line 338) | `{method} (로그선형 할인계수), 만기 {n}개 {first}-{last}` |
| Hedge notice (lines 482-494) | `계약 수 = 포지션 DV01 × 전환계수 / CTD DV01 = … : {k}계약 매도/매수. 헤지 후 순 DV01은 1bp당 …입니다 (잔여 위험 없음 / 헤지 부족 / 헤지 초과). DV01 근사입니다: 선물 DV01 = CTD DV01 / 전환계수이며 CTD DV01은 계약 액면 기준입니다. CTD와 전환계수는 직접 입력한 값이며 시장 데이터가 아닙니다. CTD 교체, 베이시스, 인도 옵션, 인보이스 가격, 수익률 베타는 반영하지 않습니다.` |
| Table header (line 41) | `금리 충격 (bp, 연속복리 무이표 금리)` |
| Table header (line 42) | `손익률 % (시장가치 대비)` |
| Key-rate chart title (line 414), new in `a5f904a` | `무이표 곡선 만기별 DV01 (z-스프레드 {z} 고정)`. The words follow main's own Korean: 무이표 곡선 (`ui/structuring_page.py` line 240) and 만기별 DV01 (`ui/fcharts.py` line 317) |
| Curve line (lines 369-374), new in `a5f904a` | `금리 곡선은 합성 데이터입니다 (시뮬레이션, 기준일 {date}). z-스프레드, 캐리/롤다운, 만기별 DV01, 시나리오는 시장이 아니라 시뮬레이션한 곡선에서 나온 값입니다.` and, for a FRED curve, `곡선: {source} 미국 국채 파 금리 곡선, 최신 관측일 {date}.` followed by the provider's note as written |
| Hedge lines (`quantgen_desktop/bonds_portfolio_narrative.py` lines 154-156), changed in `a5f904a` | `선물 매도\|매수 {n}계약 · 반올림 {k}` and `반올림 후 잔여 DV01 {x} / bp · 실제 주문 없음`. main's words; only the side and the numbers changed |

Things seen and left alone:

- Eleven kinds of research-side text have no Korean and show in English on the Korean screen: the "Computed for" line, the "Inputs changed" notice, field error messages, the "Curve check" notice, the maturity warning, the conventions notice, the "Shocks move" notice, the override warning, the units warning, the tile labels `Position DV01 (calculator)`, `Position DV01 (override)`, `Contracts to buy`, `Net DV01 after hedge`, and the new tooltips. A probe that walks the Text controls and labels of the Korean screen counts 21 distinct English-only items on `a5f904a` (22 on `c582f15`, where the curve line was one of them). The probe does not see chart images; the key-rate chart title was missing from this list in the first version of this record and is Korean since `a5f904a`.
- The "Inputs changed" notice and main's regrouping. On `c582f15`, shown at control level: Notional typed `2000000`, Run, the field loses focus (the value becomes `2,000,000` with no change event), then any input event with nothing edited: the notice "Inputs changed since this result was computed" appeared. It also appeared when the blur landed between the Run click and the paint. The user had nothing to revert, so it could not be cleared. `a5f904a` fixes it: the snapshot compares the three grouped fields as they read after editing ends. After the fix: no notice after the blur and a later input event; none when the blur lands before the paint; a real edit is still marked; typing the same number without separators unmarks. The research tests never blur a field, so they could not see the fault or the fix. Not verified: the order of blur and click in a live Flet window.

```bash
git checkout a5f904aed76a93f0f99e907e3599ffcce4d547d9 -- ui/bonds_page.py   # if the local commit still exists
# otherwise: git checkout --ours ui/bonds_page.py, then git apply the second patch of Appendix A, then git add ui/bonds_page.py
```

### 2.5 `ui/qcharts.py`

- Both sides fixed the same fault: titles placed with `loc="left"` did not get the palette text colour. Research (`4709cf2`) calls `ax.set_title(..., color=pal.text)` for the three positions. main (`e57587a` and others) sets the colour on the three title objects.
- Rule: main's form is the later one and touches only the colour. The file becomes main's blob. The research branch has no other change in this file.
- Checked: the research test for this fault (`test_chart_left_titles_use_the_palette_text_colour`) passes on main's form. CRLF kept (441 lines, no bare LF).

```bash
git checkout --theirs ui/qcharts.py && git add ui/qcharts.py
git diff --cached --quiet "$M" -- ui/qcharts.py && echo "equals main's blob"
```

### 2.6 Commit

```bash
git diff --name-only --diff-filter=U    # must print nothing
git commit                              # at Step 10 the message lists each resolution, as 92cc00f did
```

The rehearsal merge commit has the subject "REHEARSAL ONLY, never push: merge origin/main 9fc3817 into the research head 8a8c247 (decision P3)". The review-fix commit has the subject "REHEARSAL ONLY, never push: review fixes F1 to F5 on the Bonds page of the rehearsal merge". At Step 10 the fixes belong inside the one merge commit, not in a second commit.

## 3. Files git merged by itself, as reviewed

| File | Who changed it since the base | What was checked | Result |
|---|---|---|---|
| `README.md` | both | read both sides' hunks; line endings | research: the suite list (line 932) and the `nautilus` row (957). main: three text hunks. No overlap. 1015 CRLF lines, no bare LF. Then the generator changed line 917 (section 2.2). |
| `tests/run_all.py` | research only | read, not run | equals the research blob. 163 CRLF lines. All 14 modules it imports exist in the merged tree. |
| `.github/workflows/runtime-smoke.yml` | main only | read | equals main's blob. It runs on pull requests, by a path list that holds `ui/**` and `qa/research_status.json`, and on pushes to two `gpt/` branches only (lines 2-6). A push to main does not start it. It runs `python -m tools.status.snapshot --check` (line 92) and the two main-side test modules that fail here (lines 109 and 129). Its path list names no `tools/nautilus` file and no `tests/bonds_screen_acceptance.py`. |
| `.github/workflows/compliance-review.yml` | neither | read | runs on every push to main. |
| `.github/workflows/nautilus-registration.yml` | research only (new) | read the triggers | arrives with the merge. |
| `requirements.txt`, `requirements-dev.txt` | neither | compared | the same on both sides. |
| `requirements-nautilus.txt` | research only (new) | read the header | 43 lines, hash-pinned, for the separate Nautilus environment only. |
| `pyproject.toml` | main only | compared | equals main's blob. Content not reviewed further. |
| `core/ficc/curves.py`, `core/ficc/insights.py`, `quantgen_desktop/bonds.py` | both | hunk positions, `py_compile`, the Bonds tests | hunks are apart; compile; the tests that use them pass (section 4). |
| `tests/desktop_bonds_portfolio_language_acceptance.py` | both | run | 9 of 9. |
| `tests/macro_m8_pipeline.py` | both | read only (running it is not allowed here) | research: a cache copy helper near line 847. main: 82 new lines near line 438. Apart; compiles. |
| `docs/compliance/source-review.json` | main only | compared | equals main's baseline at `9fc3817` (666 files). It changed again at `83046c1`. See section 5. |
| `tests/macro_m0_harness.py`, `tests/macro_registry.csv`, `.env.example` | research only | read the lists | the amended read-only test (T-RO-01) arrives with the merge. A text search of the merged tree outside `tools/nautilus` found none of its newly forbidden names. The test itself was not run. |
| The inputs of the bridge's code hash: `config.py`, `docs/asset_expansion_study.py`, the eleven harness sources, `core/quant/gate_package.py` (it holds the list), `requirements-nautilus.txt`, the `tools/nautilus` tree | main: none since the base. `requirements-nautilus.txt` and `tools/nautilus` exist on the research branch only and have not changed there since the Step 7A evidence commit `563db54` | blob and tree ids on `bb35b3b`, `8a8c247`, `9fc3817`, `83046c1`, `c582f15` and `a5f904a`; `git diff --name-only bb35b3b <main>` limited to these paths | the fourteen single files are the same blobs on all six commits; the `tools/nautilus` tree (`411fbc2e`) and `requirements-nautilus.txt` (`f2c1d52a`) are the same on the research head and on both rehearsal commits; the diff prints nothing for `9fc3817` and for `83046c1`. So `code_sha256` stays `f995600b…` and both `owner_confirmed` still quote the merged tree. A later pull request on main that edits one of these files, or adds a file under `tools/nautilus`, would change it without a conflict: section 2.0 has the check. |

Things that do not agree, reported and not changed:

1. The README test table has no `bonds` row, although line 932 names the suite and `tests/run_all.py` runs it. This is already so at `8a8c247`.
2. The README `Total` row still reads `743/864 passed, 0 failed, 121 not run (2026-10-23)`. README line 928 says those tables are the historical run. The status block now reads 844/964, from the Windows Step 7A file. Both describe the research tree before this merge. The merged tree has more tests. main added no macro test module: `git diff --name-status bb35b3b 9fc3817 -- 'tests/macro_*'` lists ten files, all modified, none added. main added tests inside those ten files (24 lines `+def test_` and 1 line `-def test_`, counted as text; one of the 24 is the removed name added back). main also added 36 other test files and one JSON fixture under `tests/`; none is a macro file and `tests/run_all.py` imports none of them. How many rows the merged tree's full run has: not verified.
3. The research head fails `tools.status.snapshot --check` as it stands (section 2.2).

## 4. Checks and their results

Environment: Linux, Python 3.13.17 from the scratch environment `v313`, PyYAML 6.0.3, `QT_QPA_PLATFORM=offscreen`. `HOME` pointed at an empty scratch folder, so nothing under `~/.nextgen` could be reached. Every test ran behind a Python audit hook that refuses and counts any open or listing of `docs/asset_expansion/cache`, of a file named `.env`, or of the real `~/.nextgen`. The count was 0 in every run. Each module was first searched for the cache path with `git grep -n "asset_expansion/cache" -- <module>`: no match in any of them. Modules were started the way `python -m tests.<module>` starts them.

One plain fact about git: `git status`, `git add`, `git commit` and `git diff --check` on a working tree stat every tracked file of that worktree, the protected folder included, as git always does. The rehearsal worktree is not sparse. No command named, listed, opened, hashed or searched that folder.

Who ran what. The `c582f15` column is from the first rehearsal, except its cells in the probe row and in the last two patch rows, which the helper that made the review fixes ran. The `a5f904a` column is from that helper; the session that finished this record ran the rows marked "(re-run)" again on `a5f904a` and got the same result.

| Check | On `c582f15` | On `a5f904a` |
|---|---|---|
| `py_compile` on Python 3.13.17 of the three resolved Python files | OK, all three | OK (re-run, compiled in memory) |
| `py_compile` on Python 3.13.17 of six merged-by-git Python files | OK, all six | OK |
| The same nine files compiled in memory on Python 3.11.17 (`compile(bytes, name, 'exec')`, nothing imported, nothing written) | not run | OK, nine of nine; the three resolved files (re-run) |
| `qa/research_status.json` is valid JSON | OK | unchanged file |
| `python -m tools.status.snapshot --check` | consistent: 844 PASS, 0 FAIL, 120 NOT_RUN, 964 rows | not run again; its three inputs and the snapshot are the same files in both commits |
| `git diff --check`, working tree | before the commit: no finding | no finding |
| `git diff --check c582f15 a5f904a` | | no finding (re-run) |
| `git diff --cached --check` against the research head | before the commit: with a carriage return at the line end allowed, four findings, all in files that are main's blobs unchanged: `ui/signals_page.py`, `docs/product/COMPACT_NATIVE_UI_20261107.md`, `core/quant/history.py` (blank line at the end), `assets/fonts/OFL-GothicA1.txt` (trailing space). None in the five resolved files. Without that allowance git flags every changed line of the CRLF files, because `.gitattributes` keeps them byte-exact (`* -text`). | before the commit: no finding |
| `tests.bonds_screen_acceptance` (research) | 28 of 33. FAIL: `test_hedge_798_x_08_over_65_side_rounding_and_residual`, `test_hedge_override_is_named_and_warned`, `test_rounding_is_half_away_from_zero_as_decided` (the label, choice 1); `test_stale_carried_forward_and_bad_unit_curves_are_flagged`, `test_synthetic_and_fred_are_labelled_apart_with_a_mocked_fetch` (the banner, choice 2) | 28 of 33, the same five failures and no new one (re-run) |
| `tests.flet_a1_headers_acceptance` (main) | 7 of 8. FAIL: `test_bond_scenarios_use_display_headers_without_payload_mutation` (the headers, choice 3) | 7 of 8, the same failure (re-run) |
| `tests.ficc_pages_display_acceptance` (main) | 23 of 24. FAIL: `test_every_page_chrome_is_korean_and_returns_to_english` for the Bonds page. The research branch's new empty-state sentence (it starts at line 543 of the page on `a5f904a`, merged by git) has no Korean entry in `core/ui_page_messages/ficc_pages.py`. | 23 of 24, the same failure (re-run) |
| `tests.flet_korean_narratives_acceptance` (main) | 17 of 17 | 17 of 17 (re-run) |
| `tests.desktop_bonds_portfolio_language_acceptance` | 9 of 9 | 9 of 9 (re-run) |
| `tests.bond_funding_acceptance` | 8 of 8 | 8 of 8 |
| `tests.desktop_operation_fixes_acceptance` | 7 of 7 | 7 of 7 |
| `tests.chart_c_theme_acceptance`, `tests.chart_reading_acceptance` | 6 of 6, 20 of 20 | 6 of 6, 20 of 20 |
| `tests.quant_acceptance` | The module has no runner of its own. Its one chart test, `test_every_chart_renders_a_data_uri_image`, was called alone: PASS. The other tests of the module were not run. | the same one test: PASS |
| `python -m ui.bonds_page` (the page's own self-check) | `ok` | `ok` (re-run) |
| Six more native PC app modules, run because choice 7 changes a native label: `tests.desktop_acceptance`, `tests.desktop_a3_layout_acceptance`, `tests.desktop_language_acceptance`, `tests.desktop_a1_terms_acceptance`, `tests.desktop_a3_reading_acceptance`, `tests.desktop_compact_ui_acceptance` | not run | 22 of 22, 8 of 8, 7 of 7, 5 of 5, 12 of 12, 4 of 4 |
| A probe of the review findings (`pilotprep_work/revfix/probe_after.py` in the session's scratch folder): the tiles against the Korean hedge section for 12 positions, 13 typed texts in each of the three grouped fields on blur and on Enter, the stale notice paths, the chart title drawn with the Korean locale | the findings reproduce | `FAILED checks: 0`; the log holds 45 `ok` lines (the helper's report says 46 checks) |
| The five Bonds modules with the follow-up patches S1 (second version), S2 and S3 of Appendix B | with the first S1: 33 of 33, 8 of 8, 24 of 24, 17 of 17, 9 of 9, in a copy of `c582f15` outside any checkout (`git archive`, no `docs/`) | 33 of 33, 8 of 8, 24 of 24, 17 of 17, 9 of 9, in a copy of `a5f904a` outside any checkout (re-run) |
| The same with the proposed S4 as well (four new tests) | 33 of 37: the four new tests fail, so they see findings F1 to F4 | 37 of 37, 8 of 8, 24 of 24, 17 of 17, 9 of 9 (re-run) |
| `python3 -B -m tools.compliance.check --check` | exit 1, as expected: `consistency_status FAIL`, "documents need review: 1 … 20". The tree has 679 monitored files, the baseline 666. The baseline was not refreshed. | not run again. The two changed files were already among the 13 that differ from the baseline |

What the compliance check sees. 13 files are new to the baseline: `.github/workflows/nautilus-registration.yml`, `requirements-nautilus.txt`, `tests/bonds_screen_acceptance.py`, `tests/nautilus_acceptance.py`, `tests/nautilus_registration_acceptance.py`, `tests/nautilus_stub_child.py`, and the seven files of `tools/nautilus/`. 13 files differ from the baseline: `README.md`, `core/ficc/bonds.py`, `core/ficc/curves.py`, `core/ficc/data.py`, `core/ficc/insights.py`, `quantgen_desktop/bonds.py`, `quantgen_desktop/bonds_portfolio_narrative.py`, `tests/bond_funding_acceptance.py`, `tests/desktop_bonds_portfolio_language_acceptance.py`, `tests/macro_m0_harness.py`, `tests/macro_m8_pipeline.py`, `tests/run_all.py`, `ui/bonds_page.py`. These numbers are for main at `9fc3817`. main's baseline changed at `83046c1`, so they are not verified for that main.

Limits of these checks:

- A compile on Python 3.13 cannot catch the fault that the repository's own syntax test names: f-string quoting that Python 3.12 and later accept and 3.10 and 3.11 reject (`tests/runtime_syntax_acceptance.py` lines 1-5; the CI syntax job runs 3.10 and 3.11, `.github/workflows/runtime-smoke.yml` lines 13-16). The nine files were therefore also compiled on Python 3.11.17 here; a control line that reuses the outer quote inside an f-string is rejected by 3.11 and accepted by 3.13, so that check can see the fault. Python 3.10 was not available: not verified. At Step 10 compile the three resolved files on the owner's Windows Python 3.10 or 3.11, or let the CI job do it. The repository's test itself was not run, because it lists every tracked path with `git ls-files` (its lines 16-18).
- Starting a module as `python -B tests/<module>.py` from the repository root does not run any test: it stops at import with `ModuleNotFoundError`, because these modules do not put the repository root on `sys.path`. With the root on `PYTHONPATH` the script form gives the same results as `python -m tests.<module>` (run by the fix helper for the 11 modules that have a runner).
- The page handlers were called directly. No live Flet window was opened, so the order of blur and click in a real window is not verified.

Not run, by rule or by scope: `tests/run_all.py`, `tests.macro_m8_pipeline`, `tests.macro_m9_lab`, the Nautilus suite, the provider parity tests, the read-only harness (`tests.macro_m0_harness`), the packaging tests, `tests/runtime_syntax_acceptance.py` and every other module.

## 5. Work the real merge will need afterwards

1. Three small fixes outside the conflicted files (Appendix B). Without them the merged tree cannot pass both sides' tests. They are in neither rehearsal commit, because the rehearsal was limited to the five conflicted files. All three still apply to `a5f904a` (`git apply --check`).
   - S1, `tests/bonds_screen_acceptance.py`: three lookups use the label `Position DV01`; two checks read the failure reason from the folded provider message; the comment at line 561 says that the assertion now reads the curve line, not the narrative.
   - S2, `tests/flet_a1_headers_acceptance.py`: the expected scenario headers, English and Korean.
   - S3, `core/ui_page_messages/ficc_pages.py`: Korean for the research branch's empty-state sentence. This Korean sentence is new wording, to be reviewed.
   Two of the three change what a test expects; only S3 changes what the screen shows. If the owner prefers the other answer for choice 1 or 3, the patch moves to the other side's test.
   S2 and S3 must be inside the P3 merge, not after it. The Runtime workflow runs the two main-side modules on pull requests only (section 3). The owner's merge push to main does not start it, so main would look green; the first later pull request that touches a listed path (`ui/**`, `qa/research_status.json` and others) would then fail on these two tests.
2. A proposal for the lead, in no commit: S4, four tests that can see review findings F1 to F4 (Appendix B.4). The research tests never blur a field, so they pass with or without the fixes. S4 applies after S1. It adds four rows to the `bonds` suite of `tests/run_all.py` (33 becomes 37), so the row counts of the merged tree change. If that is not wanted, the same tests can live in a main-side module that the full run does not count.
3. An owner ruling on scope. Decision P2 limits what the Claude session may commit on the research branch to four kinds of file: the Step 10 record, the spec, README and `docs/nautilus_bridge/runs/` (main's rulings log at `83046c1`, line 757). Decision P3 says that Claude merges main into the research branch, resolves the conflicts and runs the full test in a cache-free copy (line 758). A P3 merge that passes the tests holds more than conflict resolutions: the regenerated snapshot with the README line, S1 to S3, the review fixes and the Korean wording of section 2.4, and perhaps the compliance baseline (item 5). The two recorded texts do not say whether P3 covers these.
4. Regenerate `qa/research_status.json` once more at Step 10, after the Windows full run and the README rows (section 2.2).
5. Refresh the compliance baseline for all 20 documents (`tools.compliance.check --refresh-baseline`, with a reviewer and a note), in the merged tree before the owner merges or in a follow-up pull request. The Compliance workflow runs on every push to main. If the baseline is not refreshed first, it is expected to fail on the owner's merge push (read from the workflow file; GitHub was not checked).
6. `qa/acceptance_results.json` and the README counts describe the research tree before the merge. A Windows full run of the merged tree would be needed for them to describe main after the merge. Whether that run is required is the owner's decision (question 2 in section K of the owner's run sheet).
7. Korean for the eleven kinds of research-side Bonds text that still show in English (section 2.4). Product work, not merge work.
8. The lead's cache-free full test of the merged tree. On `a5f904a` as it stands, expect the five Bonds rows of section 4 to fail in the `bonds` suite. With S1 applied they pass (33 of 33 in the copy). The two main-side modules are not part of `tests/run_all.py`.
9. This file sits under `docs/product/`, which the compliance check monitors. Committing it changes the monitored file list.

The seven choices of section 2.4 and items 1, 3 and 5 above are one open question in the sibling documents: item 10 of section K in `docs/product/PILOT_OWNER_RUN_2026-11-11.md` and question 6 of section 5 in `docs/product/PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md`.

## 6. Full test

Full cache-free test of the rehearsal commit: PENDING (the lead fills this in)

The commit to test is `a5f904a`, the rehearsal merge with the review fixes.

## 7. This rehearsal goes stale

The rehearsal is true for research `8a8c247` and main `9fc3817` only. main moved twice while this work ran, the second time to `83046c1`, and more pull requests are waiting. Each new commit on main can change a conflict, add one, or change a count above. What is known about `83046c1` without redoing the rehearsal: the four conflicted files other than the rulings log are unchanged there; the rulings log gained one appended section and the recipe of 2.1 still holds; none of the hashed files of section 2.0 changed; `docs/compliance/source-review.json` changed, so the compliance numbers of section 4 are stale. Not verified: everything else about a merge with `83046c1`, the list of auto-merged files included.

The research branch will also change before Step 10 (the Step 10 record, the README rows, `qa/acceptance_results.json`, the run folders). The rehearsal must be repeated at Step 10, on the main and the research head of that day: run section 2.0, compare the blob ids, resolve again whatever changed, and run section 4 again.

## Appendix A. Patches from the research blobs to the resolved files

Each patch turns the research version of a file (`git checkout --ours <file>`) into the resolved version of `a5f904a`, the rehearsal with the review fixes. Use a patch only if section 2.0 says `same` for that file. Save a block to a file and run `git apply <file>`. Both were generated with `git diff 8a8c247 a5f904a -- <file>`. Applying them to the research blobs outside a repository gave the blobs of `a5f904a` byte for byte (`ead09e41…` and `e90d7f47…`).

### A.1 `quantgen_desktop/bonds_portfolio_narrative.py`

```diff
diff --git a/quantgen_desktop/bonds_portfolio_narrative.py b/quantgen_desktop/bonds_portfolio_narrative.py
index b537a19..ead09e4 100644
--- a/quantgen_desktop/bonds_portfolio_narrative.py
+++ b/quantgen_desktop/bonds_portfolio_narrative.py
@@ -20,7 +20,7 @@ _NOTE_PARTS = (
                          'Maximizing a non-positive Sharpe can favor higher volatility; these '
                          'weights are not evidence of an attractive or low-risk allocation.')),
      lambda m: '무위험금리보다 높은 추정 수익률을 가진 자산이 없습니다. '
-               '양수가 아닌 샤프비율을 최대화하면 더 높은 변동성을 선호할 수 있습니다. '
+               '양수가 아닌 샤프 지수를 최대화하면 더 높은 변동성을 선호할 수 있습니다. '
                '이 비중은 매력적이거나 위험이 낮은 배분이라는 근거가 아닙니다.'),
     (re.compile(r'Requested per-asset cap (?P<requested>\d+\.\d{10}%) was adjusted to '
                 r'(?P<effective>\d+\.\d{10}%) by the existing fully-invested feasibility bound '
@@ -54,11 +54,11 @@ def bond_korean(a, scenarios=()):
     name = b.name or f'{_pct(b.coupon)} {tenor_label(b.maturity)} 채권'
     lines = [
         f'{name}은 연 {b.freq}회 쿠폰을 지급하며 액면 {b.face:g}당 가격 {a.price:.3f}, '
-        f'수익률 {_pct(a.ytm,3)}입니다. 매콜리 듀레이션 {a.macaulay:.2f}y, '
-        f'수정 듀레이션 {a.modified:.2f}, 볼록성 {a.convexity:.1f}입니다.',
+        f'수익률 {_pct(a.ytm,3)}입니다. 맥컬리 듀레이션 {a.macaulay:.2f}y, '
+        f'수정 듀레이션 {a.modified:.2f}, 컨벡시티(볼록성) {a.convexity:.1f}입니다.',
         f'명목금액 {_money(b.notional)}의 DV01은 채권 자체 수익률 bp당 '
         f'{_money(a.dv01) if abs(a.dv01) >= 100 else f"{a.dv01:,.2f}"}입니다. '
-        f'그 수익률이 +100bp 오르면 볼록성을 반영하기 전 대략 {_money(a.dv01*100)}의 손실이 발생합니다.',
+        f'그 수익률이 +100bp 오르면 컨벡시티를 반영하기 전 대략 {_money(a.dv01*100)}의 손실이 발생합니다.',
     ]
     if a.krd:
         t,v = _top(a.krd)
@@ -88,9 +88,10 @@ def bond_korean(a, scenarios=()):
 def portfolio_korean(p):
     top = sorted(zip(p.symbols,p.weights),key=lambda x:-x[1])[:3]
     top_text = ', '.join(f'{s} {w*100:.0f}%' for s,w in top)
-    lines = [f'{p.objective.replace("_","-")} 포트폴리오의 주요 비중은 {top_text}입니다. '
+    objective = '최대 샤프 지수' if p.objective == 'max_sharpe' else p.objective.replace('_','-')
+    lines = [f'{objective} 포트폴리오의 주요 비중은 {top_text}입니다. '
              f'추정 연율 수익률 {p.ann_return*100:+.1f}%, 변동성 {p.ann_vol*100:.1f}%, '
-             f'샤프비율 {p.sharpe:.2f}입니다.']
+             f'샤프 지수 {p.sharpe:.2f}입니다.']
     if p.risk_contrib is not None:
         symbol,rc = sorted(zip(p.symbols,p.risk_contrib),key=lambda x:-x[1])[0]
         lines.append(f'{symbol}은 포트폴리오 전체 위험의 {rc*100:.0f}%를 기여합니다. '
@@ -107,7 +108,8 @@ def portfolio_scope_korean(portfolios, objective):
     p = portfolios[objective]
     cap = (f'{p.requested_max_weight:.2%} 요청 → {p.effective_max_weight:.8%} 유효'
            if p.requested_max_weight != p.effective_max_weight else cap_label(p))
-    return (f'선택 목적 {objective}: 종목당 상한 {cap}. 요청한 상한은 선택한 목적에만 적용합니다. '
+    display_objective = '최대 샤프 지수' if objective == 'max_sharpe' else objective
+    return (f'선택 목적 {display_objective}: 종목당 상한 {cap}. 요청한 상한은 선택한 목적에만 적용합니다. '
             '다른 목적의 행, 효율적 투자선과 무작위 구름은 종목당 상한 100%를 사용합니다. '
             '모두 롱온리·완전투자이며 equal_weight는 각 비중을 1/N로 고정합니다. '
             '상한이 다르면 동일 조건의 효율적 투자선 비교가 아닙니다.')
@@ -140,15 +142,21 @@ def bond_notes(out, language):
 
 
 def hedge_text(hedge, language):
+    """Three lines on the futures hedge. The side (sell against a long position, buy against a short
+    one), the whole-contract count (halves away from zero, `core.ficc.bonds.round_contracts`) and the
+    DV01 left after it are the ones the Flet Bonds page shows in its tiles."""
     if not hedge: return ''
+    from core.ficc.bonds import round_contracts
     pos,ctd,cf,n = hedge
+    k = round_contracts(n)
+    left = pos-k*(ctd/cf)
     if language == 'ko':
-        return (f'선물 매도 {n:,.2f}계약 · 반올림 {round(n):,}\n'
+        return (f'선물 {"매도" if n >= 0 else "매수"} {abs(n):,.2f}계약 · 반올림 {abs(k):,}\n'
                 f'포지션 DV01 {pos:,.2f} × 전환계수 {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
-                f'반올림 후 잔여 DV01 {pos-round(n)*ctd/cf:+,.2f} / bp · 실제 주문 없음')
-    return (f'Sell futures {n:,.2f} contracts · rounded {round(n):,}\n'
+                f'반올림 후 잔여 DV01 {left:+,.2f} / bp · 실제 주문 없음')
+    return (f'{"Sell" if n >= 0 else "Buy"} futures {abs(n):,.2f} contracts · rounded {abs(k):,}\n'
             f'Position DV01 {pos:,.2f} × CF {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
-            f'Residual DV01 after rounding {pos-round(n)*ctd/cf:+,.2f} per bp · no real orders')
+            f'Residual DV01 after rounding {left:+,.2f} per bp · no real orders')
 
 
 def portfolio_notes(out, language, disclosure):
```

### A.2 `ui/bonds_page.py`

```diff
diff --git a/ui/bonds_page.py b/ui/bonds_page.py
index f95b1e3..e90d7f4 100644
--- a/ui/bonds_page.py
+++ b/ui/bonds_page.py
@@ -28,8 +28,18 @@ from core.ficc.curves import curve_from_snapshot
 from core.ficc.data import load_treasury_curve
 from core.theme import RADII, active
 from ui import fcharts
+from ui.localization import table_header, literal_text
 from ui.ai_panel import analysis_panel
-from ui.components import card, chip, empty_state, notice, section, stat
+from ui.narrative_sections import korean, localized
+from quantgen_desktop.bonds_portfolio_narrative import bond_korean, hedge_text
+from ui.components import (card, empty_state, group_digits, notice, number_field, parse_number,
+                           section, stat)
+from ui.ficc_widgets import action, form_row, hide_source, ko_notice, ko_stat, lchip, synthetic_notice, with_helper
+
+_SCENARIO_HEADERS_KO = {'Scenario': '시나리오', 'Shock': '금리 충격', 'New price': '새 가격',
+                        'P&L': '손익', 'P&L %': '손익률 %',
+                        'Shock (bp, cc zero rates)': '금리 충격 (bp, 연속복리 무이표 금리)',
+                        'P&L % of MV': '손익률 % (시장가치 대비)'}
 
 _TOOLS = [("calc", "Calculator & risk"), ("scenarios", "Scenarios"),
           ("hedge", "Futures hedge")]
@@ -96,6 +106,29 @@ def _num(field: ft.TextField, default: Optional[float] = None, *, required: bool
     return v + 0.0                                # '-0' -> 0.0, never '-0.000%'
 
 
+def _grouped(text) -> str:
+    """The text as a grouped number field shows it once editing ends: digits in groups of three
+    ('2000000' -> '2,000,000') when the text has the form `_num` reads, otherwise as typed."""
+    raw = (text or "").strip()
+    return group_digits(raw) if raw and _NUM_RE.fullmatch(raw) else (text or "")
+
+
+def _strict_grouping(field: ft.TextField) -> ft.TextField:
+    """`number_field` regroups the digits when editing ends, with a looser reader than `_num`
+    ('4,5' -> '45', '1_000' -> '1,000'): a typo would turn into a number before Run reads it.
+    Here only text of the form `_num` reads is regrouped; anything else stays as typed, so Run
+    still refuses it on the field."""
+    def only_numbers(handler):
+        def on_event(e=None):
+            raw = (field.value or "").strip()
+            if handler is not None and raw and _NUM_RE.fullmatch(raw):
+                handler(e)
+        return on_event
+
+    field.on_blur, field.on_submit = only_numbers(field.on_blur), only_numbers(field.on_submit)
+    return field
+
+
 def _shock_text(shock) -> str:
     """Every key tenor with one decimal (the fly's -12.5 is not '-12'), in bp."""
     if isinstance(shock, (int, float)):
@@ -107,35 +140,40 @@ def build_bonds_page(page: ft.Page,
                      on_open_settings: Optional[Callable] = None) -> ft.Control:
     pal = active()
 
-    coupon = ft.TextField(label="Coupon %", width=110, value="4.50",
-                          border_radius=RADII["md"])
-    maturity = ft.TextField(label="Maturity (years)", width=140, value="10",
-                            border_radius=RADII["md"])
-    freq = ft.Dropdown(label="Coupons / year", width=150, value="2",
+    def num(label: str, value: str = "", width: int = 140, **kw) -> ft.TextField:
+        """A small number (percent, years, ratio): plain, right-aligned like every number."""
+        return ft.TextField(label=label, value=value, width=width, border_radius=RADII["md"],
+                            text_align=ft.TextAlign.RIGHT, **kw)
+
+    coupon = num("Coupon %", "4.50", 120)
+    maturity = num("Maturity (years)", "10", 120)
+    freq = ft.Dropdown(label="Coupons / year", width=180, value="2",
                        options=[ft.dropdown.Option(k, v) for k, v in _FREQS])
-    price = ft.TextField(label="Price (per 100)", width=140, helper="blank = from yield",
-                         border_radius=RADII["md"])
-    ytm = ft.TextField(label="Yield %", width=120, value="4.50", helper="blank = from price",
-                       border_radius=RADII["md"])
-    notional = ft.TextField(label="Notional", width=140, value="1000000",
-                            border_radius=RADII["md"])
-    source = ft.Dropdown(label="Curve source", width=240, value="auto",
-                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
-    ctd_dv01 = ft.TextField(label="CTD DV01 / contract", width=170, value="65",
-                            hint_text="per bp, per contract", border_radius=RADII["md"],
-                            tooltip="Your input, not market data: the CTD's DV01 in currency "
-                                    "per bp for one contract's face (e.g. $100,000 for ZN/ZF/ZB, "
-                                    "$200,000 for ZT).")
-    cf = ft.TextField(label="Conversion factor", width=150, value="0.8",
-                      border_radius=RADII["md"],
-                      tooltip="Your input, not market data: the exchange's conversion factor "
-                              "of the cheapest-to-deliver issue.")
-    pos_dv01 = ft.TextField(label="Position DV01 (blank = calculator)", width=250,
-                            border_radius=RADII["md"],
-                            tooltip="Currency per bp; negative for a short position.")
-    hedge_row = ft.Row([ctd_dv01, cf, pos_dv01], spacing=10, wrap=True, visible=False)
+    # Quote by price or by yield: the helper line says which blank means what.
+    price = with_helper(num("Price (per 100)", width=160, hint_text="blank = from yield"),
+                        "Blank = from yield")
+    ytm = with_helper(num("Yield %", "4.50", 160, hint_text="blank = from price"), "Blank = from price")
+    notional = _strict_grouping(number_field("Notional", "1000000", width=160))
+    # The app fetches the UST curve itself (FRED, else a labelled synthetic
+    # curve); the selector stays for tests and self-checks but is not shown.
+    source = hide_source(ft.Dropdown(label="Curve source", width=240, value="auto",
+                                     options=[ft.dropdown.Option(k, v) for k, v in _SOURCES]), "auto")
+    ctd_dv01 = _strict_grouping(number_field(
+        "CTD DV01 / contract", "65", width=180, hint_text="per bp, per contract",
+        tooltip="Your input, not market data: the CTD's DV01 in currency "
+                "per bp for one contract's face (e.g. $100,000 for ZN/ZF/ZB, "
+                "$200,000 for ZT)."))
+    cf = num("Conversion factor", "0.8", 160,
+             tooltip="Your input, not market data: the exchange's conversion factor "
+                     "of the cheapest-to-deliver issue.")
+    pos_dv01 = with_helper(_strict_grouping(number_field(
+        "Position DV01", width=180, tooltip="Currency per bp; negative for a short position.")),
+        "Blank = from the calculator")
+    hedge_fields = (ctd_dv01, cf, pos_dv01)          # shown only for the futures hedge
+    for f in hedge_fields:
+        f.visible = False
     busy = ft.ProgressRing(visible=False, width=20, height=20)
-    result_host = ft.Column(spacing=14)
+    result_host = ft.Column(spacing=16)
     stale = notice(STALE_TEXT, "warning", icon=ft.Icons.HISTORY)
     stale.visible = False
     lock = threading.Lock()
@@ -143,8 +181,11 @@ def build_bonds_page(page: ft.Page,
     fields = (coupon, maturity, price, ytm, notional, ctd_dv01, cf, pos_dv01)
 
     def _raw() -> tuple:
-        return tuple(c.value for c in (tool, coupon, maturity, freq, price, ytm, notional,
-                                       source, ctd_dv01, cf, pos_dv01))
+        """The inputs a result belongs to. The three grouped number fields are taken as they read
+        once editing ends, so the regrouping on blur (2000000 -> 2,000,000) is not an edit."""
+        return (tool.value, coupon.value, maturity.value, freq.value, price.value, ytm.value,
+                _grouped(notional.value), source.value, _grouped(ctd_dv01.value), cf.value,
+                _grouped(pos_dv01.value))
 
     def on_input(e=None) -> None:
         ctl = getattr(e, "control", None)
@@ -157,7 +198,8 @@ def build_bonds_page(page: ft.Page,
         page.update()
 
     def on_tool(e=None) -> None:
-        hedge_row.visible = tool.value == "hedge"
+        for f in hedge_fields:
+            f.visible = tool.value == "hedge"
         on_input(e)
 
     tool = ft.Dropdown(label="Tool", width=200, value="calc", on_select=on_tool,
@@ -275,8 +317,11 @@ def build_bonds_page(page: ft.Page,
                 blocks: list[ft.Control] = [
                     ft.Text(echo, size=11, color=pal.muted, selectable=True)]
                 if synthetic:
-                    blocks.append(notice("Synthetic data: " + panel.note, "error",
-                                         icon=ft.Icons.SCIENCE_OUTLINED))
+                    blocks.append(synthetic_notice(
+                        "합성 데이터: 금리 곡선을 FRED에서 받지 못해 시뮬레이션한 곡선으로 계산했습니다. "
+                        "아래 숫자는 계산 방식의 시연이며 시장 시세가 아닙니다.",
+                        "Synthetic data: the curve is simulated because FRED did not answer; every number "
+                        "below is a demonstration of the mechanics, not a market read.", panel.note))
                 elif panel.note:
                     blocks.append(notice("Curve check: " + panel.note, "warning",
                                          icon=ft.Icons.WARNING_AMBER_ROUNDED))
@@ -285,14 +330,16 @@ def build_bonds_page(page: ft.Page,
                         f"Maturity {bond.maturity:g}y is beyond the longest curve tenor "
                         f"({tenor_label(curve.tenors[-1])}): zero rates are held flat beyond it.",
                         "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
+                source_ko = "합성 데이터" if synthetic else curve.source
+                span = f"{tenor_label(curve.tenors[0])}-{tenor_label(curve.tenors[-1])}"
                 blocks.append(ft.Row([
-                    chip(f"curve: {src_tag}",
-                         "error" if synthetic else ("warning" if panel.note else "success")),
-                    chip(f"{curve.method} (log-linear DF), {len(curve.tenors)} tenors "
-                         f"{tenor_label(curve.tenors[0])}-{tenor_label(curve.tenors[-1])}"),
-                    chip(f"{bond.freq}x coupons"),
-                    chip(f"notional {_money(bond.notional)}"),
-                ], spacing=6, wrap=True))
+                    lchip(f"곡선 출처: {source_ko} · 기준일 {curve.date}", f"curve: {src_tag}",
+                          "error" if synthetic else ("warning" if panel.note else "success")),
+                    lchip(f"{curve.method} (로그선형 할인계수), 만기 {len(curve.tenors)}개 {span}",
+                          f"{curve.method} (log-linear DF), {len(curve.tenors)} tenors {span}"),
+                    lchip(f"연 {bond.freq}회 이자 지급", f"{bond.freq}x coupons"),
+                    lchip(f"명목금액 {_money(bond.notional)}", f"notional {_money(bond.notional)}"),
+                ], spacing=8, wrap=True))
                 blocks.append(ft.Row([
                     stat("Price", f"{a.price:.3f}",
                          tooltip="Full (dirty) PV per 100: no settlement date, no accrued split"),
@@ -306,12 +353,24 @@ def build_bonds_page(page: ft.Page,
                     stat("z-spread", bp_text(a.z_spread),
                          tooltip=f"Continuous, over the curve's zero rates; curve price "
                                  f"{a.curve_price:.3f}"),
-                ], spacing=10, wrap=True))
-                narrative = insights.narrate_bond(a, rows) + (
-                    f" The curve is SYNTHETIC (simulated, dated {curve.date}): z-spread, "
+                ], spacing=12, run_spacing=12, wrap=True))
+                narrative = insights.narrate_bond(a, rows)
+                bond_text = narrative           # the bond read alone; the hedge tool appends its sentence
+                extra = []
+                # Where the curve came from is shown on its own line above the Analysis panel: the
+                # panel keeps the canonical bond read, so its Korean and English sections state the
+                # same parts. The Analysis panel itself does not name the curve source.
+                curve_line = (
+                    f"The curve is SYNTHETIC (simulated, dated {curve.date}): z-spread, "
                     "carry/roll, key-rate DV01s and scenarios describe the generator, not the "
                     "market." if synthetic else
-                    f" Curve: {curve.source} UST par curve, newest observation {curve.date}."
+                    f"Curve: {curve.source} UST par curve, newest observation {curve.date}."
+                    + (f" {panel.note}" if panel.note else ""))
+                curve_line_ko = (
+                    f"금리 곡선은 합성 데이터입니다 (시뮬레이션, 기준일 {curve.date}). z-스프레드, "
+                    "캐리/롤다운, 만기별 DV01, 시나리오는 시장이 아니라 시뮬레이션한 곡선에서 나온 "
+                    "값입니다." if synthetic else
+                    f"곡선: {curve.source} 미국 국채 파 금리 곡선, 최신 관측일 {curve.date}."
                     + (f" {panel.note}" if panel.note else ""))
                 be_ok = math.isfinite(cr.breakeven_bp)
                 payload = {
@@ -332,9 +391,10 @@ def build_bonds_page(page: ft.Page,
                 }
                 if kind == "calc":
                     blocks.append(ft.Row([
-                        stat(f"Carry ({tenor_label(cr.horizon)})", f"{cr.carry:+.3f}",
-                             token="success" if cr.carry >= 0 else "error",
-                             tooltip="Per 100 over the horizon, not annualised"),
+                        ko_stat(stat(f"Carry ({tenor_label(cr.horizon)})", f"{cr.carry:+.3f}",
+                                     token="success" if cr.carry >= 0 else "error",
+                                     tooltip="Per 100 over the horizon, not annualised"),
+                                f"캐리 ({tenor_label(cr.horizon)})"),
                         stat("Roll-down", f"{cr.rolldown:+.3f}",
                              token="success" if cr.rolldown >= 0 else "error"),
                         stat("Carry + roll", f"{cr.total:+.3f}",
@@ -346,11 +406,12 @@ def build_bonds_page(page: ft.Page,
                                       if cr.total >= 0 else
                                       "Carry + roll is negative: yields must fall this much to "
                                       "break even")),
-                    ], spacing=10, wrap=True))
+                    ], spacing=12, run_spacing=12, wrap=True))
                     blocks.append(card(fcharts.price_yield_chart(bond, a.ytm)))
                     blocks.append(card(fcharts.krd_chart(
                         a.krd, title=f"Zero-curve key-rate DV01 (z-spread {bp_text(a.z_spread)} "
-                                     f"held)")))
+                                     f"held)",
+                        title_ko=f"무이표 곡선 만기별 DV01 (z-스프레드 {bp_text(a.z_spread)} 고정)")))
                 elif kind == "scenarios":
                     worst, best = min(rows, key=lambda r: r.pnl), max(rows, key=lambda r: r.pnl)
                     blocks.append(ft.Row([
@@ -358,13 +419,13 @@ def build_bonds_page(page: ft.Page,
                              token="error"),
                         stat("Best", f"{best.name}: {_money(best.pnl, signed=True)}",
                              token="success"),
-                    ], spacing=10, wrap=True))
+                    ], spacing=12, run_spacing=12, wrap=True))
                     blocks.append(card(fcharts.scenario_chart(rows)))
                     table = ft.DataTable(
-                        columns=[ft.DataColumn(ft.Text(h, size=11)) for h in
+                        columns=[ft.DataColumn(table_header(h, ko=_SCENARIO_HEADERS_KO.get(h), size=11)) for h in
                                  ("Scenario", "Shock (bp, cc zero rates)", "New price", "P&L",
                                   "P&L % of MV")],
-                        rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(v, size=11)) for v in (
+                        rows=[ft.DataRow(cells=[ft.DataCell(literal_text(v, size=11)) for v in (
                             r.name, _shock_text(r.shock_bp), f"{r.new_price:.3f}",
                             _money(r.pnl, signed=True), f"{r.pnl_pct * 100:+.2f}%")])
                             for r in rows],
@@ -414,15 +475,23 @@ def build_bonds_page(page: ft.Page,
                         stat("Net DV01 after hedge", f"{resid:+,.2f}",
                              tooltip="Position DV01 - rounded x futures DV01 (per bp): positive "
                                      "= still net long duration"),
-                    ], spacing=10, wrap=True))
-                    blocks.append(notice(
+                    ], spacing=12, run_spacing=12, wrap=True))
+                    side_ko = "매도" if n >= 0 else "매수"
+                    how_ko = {"flat": "잔여 위험 없음", "under-hedged": "헤지 부족",
+                              "over-hedged": "헤지 초과"}[how]
+                    blocks.append(ko_notice(notice(
                         f"contracts = position DV01 x CF / CTD DV01 = {pos:,.2f} x {c:.4f} / "
                         f"{_qty(ctd)} = {n:,.2f}: {side} {abs(k):,d}. Net DV01 after the hedge "
                         f"is {resid:+,.2f} per bp ({how}). A DV01 approximation: futures DV01 = "
                         f"CTD DV01 / CF, with CTD DV01 per contract face; CTD and CF are your "
                         f"inputs, not market data; CTD switches, basis, delivery options, "
                         f"invoice price and yield beta are not modelled.", "muted",
-                        icon=ft.Icons.INFO_OUTLINE))
+                        icon=ft.Icons.INFO_OUTLINE),
+                        f"계약 수 = 포지션 DV01 × 전환계수 / CTD DV01 = {pos:,.2f} × {c:.4f} / "
+                        f"{_qty(ctd)} = {n:,.2f}: {abs(k):,d}계약 {side_ko}. 헤지 후 순 DV01은 1bp당 "
+                        f"{resid:+,.2f}입니다 ({how_ko}). DV01 근사입니다: 선물 DV01 = CTD DV01 / 전환계수이며 "
+                        f"CTD DV01은 계약 액면 기준입니다. CTD와 전환계수는 직접 입력한 값이며 시장 데이터가 "
+                        f"아닙니다. CTD 교체, 베이시스, 인도 옵션, 인보이스 가격, 수익률 베타는 반영하지 않습니다."))
                     if override and abs(pos - a.dv01) > 0.01 * abs(a.dv01):
                         blocks.append(notice(
                             f"Position DV01 {pos:,.2f} is your override; this bond's calculator "
@@ -436,10 +505,12 @@ def build_bonds_page(page: ft.Page,
                             f"a per-100 input instead of one contract's face; CTD DV01 is per bp "
                             f"for one contract's face.",
                             "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
-                    narrative += (f" Hedging {pos:,.2f} per bp of DV01 with a future whose CTD "
-                                  f"has DV01 {_qty(ctd)} per contract and conversion factor "
-                                  f"{c:.4f} takes {abs(n):,.2f} contracts to {side} "
-                                  f"({abs(k):,d} rounded, net DV01 {resid:+,.2f} per bp, {how}).")
+                    hedge_en = (f"Hedging {pos:,.2f} per bp of DV01 with a future whose CTD "
+                                f"has DV01 {_qty(ctd)} per contract and conversion factor "
+                                f"{c:.4f} takes {abs(n):,.2f} contracts to {side} "
+                                f"({abs(k):,d} rounded, net DV01 {resid:+,.2f} per bp, {how}).")
+                    narrative += " " + hedge_en
+                    extra = [(("선물 헤지", "Futures hedge"), hedge_text(hedge, "ko").splitlines(), [hedge_en])]
                     payload["hedge"] = {"position_dv01": pos, "position_dv01_override": override,
                                         "ctd_dv01_per_contract": ctd, "conversion_factor": c,
                                         "futures_dv01": fut, "contracts": n, "side": side,
@@ -453,8 +524,12 @@ def build_bonds_page(page: ft.Page,
                     "muted", icon=ft.Icons.RULE))
                 if a.note:
                     blocks.append(notice(a.note, "muted", icon=ft.Icons.INFO_OUTLINE))
+                blocks.append(ko_notice(notice(curve_line, "muted", icon=ft.Icons.INFO_OUTLINE),
+                                        curve_line_ko))
                 blocks.append(analysis_panel(page, kind=f"bond_{kind}", narrative=narrative,
-                                             payload_fn=lambda p=payload: p))
+                                             payload_fn=lambda p=payload: p,
+                                             sections=localized(bond_text, korean(bond_korean, a, rows or ()),
+                                                                extra=extra)))
                 paint(blocks)
             except (FICCError, ValueError) as exc:
                 fail(str(exc))
@@ -474,12 +549,10 @@ def build_bonds_page(page: ft.Page,
         section("Bonds", subtitle="Price, yield, duration and convexity; key-rate DV01s, "
                                   "z-spread and carry/roll off the UST curve; curve "
                                   "scenarios; a Treasury-futures hedge."),
-        ft.Row([tool, coupon, maturity, freq, price, ytm, notional, source,
-                ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy],
-               spacing=10, wrap=True, vertical_alignment=ft.CrossAxisAlignment.START),
-        hedge_row,
+        form_row([tool, coupon, maturity, freq, price, ytm, notional, source, *hedge_fields,
+                  action(ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy)]),
         ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
-    ], spacing=14, expand=True)
+    ], spacing=16, expand=True)
 
 
 # --------------------------------------------------------------------------- #
@@ -491,7 +564,8 @@ if __name__ == "__main__":
     def walk(c):
         yield c
         for attr in ("controls", "rows", "cells", "columns"):
-            for child in getattr(c, attr, None) or []:
+            kids = getattr(c, attr, None)
+            for child in kids if isinstance(kids, (list, tuple)) else []:   # ResponsiveRow.columns is a number
                 yield from walk(child)
         for attr in ("content", "label"):
             child = getattr(c, attr, None)
```

## Appendix B. The follow-up patches (in neither rehearsal commit)

B.1 to B.3 apply to `a5f904a` (`git apply --check` passed). With all three, the five Bonds test modules pass in a copy of the tree (section 4). B.4 is the proposal of section 5 item 2 and applies after B.1.

### B.1 S1, `tests/bonds_screen_acceptance.py` (second version: it also corrects the comment at line 561)

```diff
--- a/tests/bonds_screen_acceptance.py
+++ b/tests/bonds_screen_acceptance.py
@@ -500,7 +500,7 @@
     note = next(t for t in _texts(h) if t.startswith("contracts = position DV01"))
     assert "798.19 x 0.8000 / 65.00 = 9.82: sell 10" in note and "over-hedged" in note
     assert "not modelled" in note and "per contract face" in note
-    h.tf["Position DV01 (blank = calculator)"].value = "-798.19"     # a short book buys
+    h.tf["Position DV01"].value = "-798.19"     # a short book buys
     s = _calc(h, tool="hedge")
     assert "Contracts to sell" not in s and s["Contracts to buy"] == "9.82"
     assert s["Rounded"] == "10" and s["Net DV01 after hedge"] == "+14.31"
@@ -520,7 +520,7 @@
                  (0.49999999999999994, 0), (2.0 ** 52 + 1, 2 ** 52 + 1), (-0.0, 0)):
         assert bonds.round_contracts(n) == _ind_round(n) == k, (n, bonds.round_contracts(n))
     h = _page()
-    h.tf["Position DV01 (blank = calculator)"].value = "682.5"
+    h.tf["Position DV01"].value = "682.5"
     h.tf["Conversion factor"].value = "1"
     s = _calc(h, tool="hedge")
     assert s["Contracts to sell"] == "10.50" and s["Rounded"] == "11"
@@ -529,7 +529,7 @@
 
 def test_hedge_override_is_named_and_warned():
     h = _page()
-    h.tf["Position DV01 (blank = calculator)"].value = "798"
+    h.tf["Position DV01"].value = "798"
     s = _calc(h, tool="hedge", coupon="4.5", notional="2,000,000")
     assert s["Position DV01 (override)"] == "798.00"
     assert any(t.startswith("Position DV01 798.00 is your override") for t in _texts(h))
@@ -556,9 +556,11 @@
         s = _calc(h)
         chip_ = _chip(h, "curve:")
         assert "SYNTHETIC" in chip_.value and _token_of(chip_) == "error"
-        banner = next(t for t in _texts(h) if t.startswith("Synthetic data"))
-        assert "FRED failed" in banner and banner.count("offline (bonds acceptance)") == 1
-        assert any("SYNTHETIC" in t and "not the market" in t for t in _texts(h))  # narrative
+        assert any(t.startswith("Synthetic data") for t in _texts(h))
+        reason = next(t for t in _texts(h) if t.startswith("FRED failed"))   # folded under the banner
+        assert reason.count("offline (bonds acceptance)") == 1
+        assert any("SYNTHETIC" in t and "not the market" in t for t in _texts(h))  # the curve line above
+        #   the Analysis panel (the merged page keeps this sentence out of the narrative)
         h = _page(source="fred")
         s = _calc(h)
         assert "Price" not in s and any(t.startswith("FRED served 0/11") for t in _texts(h))
@@ -580,7 +582,8 @@
         h = _page(source="auto")
         _calc(h)
         assert _token_of(_chip(h, "curve:")) == "error"
-        assert any(t.startswith("Synthetic data") and "outside" in t for t in _texts(h))
+        assert any(t.startswith("Synthetic data") for t in _texts(h))
+        assert any(t.startswith("FRED failed") and "outside" in t for t in _texts(h))   # folded under the banner
         h = _page(source="fred")
         s = _calc(h)
         assert "Price" not in s and any("outside" in t for t in _texts(h))
```

### B.2 S2, `tests/flet_a1_headers_acceptance.py`

```diff
--- a/tests/flet_a1_headers_acceptance.py
+++ b/tests/flet_a1_headers_acceptance.py
@@ -191,8 +191,9 @@
         select(root, "Curve source", "synthetic")
         click(root, "Run")
         self.assertEqual(len(payloads), 1)
-        self.roundtrip(root, ["Scenario", "Shock", "New price", "P&L", "P&L %"],
-                       ["시나리오", "금리 충격", "새 가격", "손익", "손익률 %"], payloads=payloads)
+        self.roundtrip(root, ["Scenario", "Shock (bp, cc zero rates)", "New price", "P&L", "P&L % of MV"],
+                       ["시나리오", "금리 충격 (bp, 연속복리 무이표 금리)", "새 가격", "손익",
+                        "손익률 % (시장가치 대비)"], payloads=payloads)
         self.assertIn("scenarios", payloads[0])
 
     def test_rates_curve_dynamic_lookback_preserves_numbers_and_payload(self):
```

### B.3 S3, `core/ui_page_messages/ficc_pages.py`

```diff
--- a/core/ui_page_messages/ficc_pages.py
+++ b/core/ui_page_messages/ficc_pages.py
@@ -150,6 +150,10 @@
     "connection the page runs on a labeled synthetic curve.":
         "가격과 수익률 중 하나만 입력하세요(다른 하나는 비워 둡니다). 금리 곡선은 앱이 FRED에서 키 없이 "
         "자동으로 가져오며, 연결되지 않으면 '합성' 표시가 붙은 곡선으로 계산합니다.",
+    "Quote it by price or by yield: fill exactly one of Price (per 100) and Yield %; the blank one is computed. "
+    "The curve comes from FRED without a key; without a connection the page runs on a labeled synthetic curve.":
+        "가격 (액면 100당)과 수익률 % 가운데 정확히 하나만 입력하세요. 비워 둔 값은 계산됩니다. 금리 곡선은 앱이 "
+        "FRED에서 키 없이 자동으로 가져오며, 연결되지 않으면 '합성' 표시가 붙은 곡선으로 계산합니다.",
     "z-spread": "z-스프레드",
     "Currency per bp, positive for a long": "금리 1bp당 통화 금액, 매수 포지션은 양수",
     "Roll-down": "롤다운",
```

### B.4 S4, proposed: four tests in `tests/bonds_screen_acceptance.py` that see review findings F1 to F4

```diff
--- a/tests/bonds_screen_acceptance.py
+++ b/tests/bonds_screen_acceptance.py
@@ -933,6 +933,79 @@
         plt.close(fig)
 
 
+def _blur(h, label: str) -> None:
+    """Leave a field the way Flet does: on_blur, when the field has one."""
+    f = h.tf[label]
+    if f.on_blur is not None:
+        f.on_blur(SimpleNamespace(control=f))
+
+
+def test_leaving_a_field_does_not_turn_a_typo_into_a_number():
+    for label in ("Notional", "CTD DV01 / contract", "Position DV01"):
+        for typo in ("4,5", "12,34", "1_000", "1 000"):
+            h = _page()
+            _pick(h, "Tool", "hedge")
+            _set(h, label, typo)
+            _blur(h, label)
+            assert h.tf[label].value == typo, (label, typo, h.tf[label].value)
+            _run(h)
+            assert f"{label}: {typo!r} is not a number." in _texts(h), (label, typo)
+    h = _page()
+    _set(h, "Notional", "2000000")
+    _blur(h, "Notional")
+    assert h.tf["Notional"].value == "2,000,000"         # a number is still regrouped
+    _run(h)
+    assert "notional 2,000,000" in next(t for t in _texts(h) if t.startswith("Computed for:"))
+
+
+def test_regrouping_on_blur_is_not_an_edit():
+    h = _page()
+    _set(h, "Notional", "2000000")
+    _run(h)
+    _blur(h, "Notional")
+    assert h.tf["Notional"].value == "2,000,000"
+    _pick(h, "Coupons / year", "2")                      # an input event with nothing edited
+    assert _STALE not in _texts(h), "regrouping the digits is not an edit"
+    _set(h, "Notional", "3,000,000")
+    assert _STALE in _texts(h), "a real edit is still marked"
+    _set(h, "Notional", "2000000")
+    assert _STALE not in _texts(h), "the same number typed without separators unmarks"
+    h = _page(queued=True)                               # the blur lands before the result paints
+    h.tf["Notional"].value = "2000000"
+    _run(h)
+    _blur(h, "Notional")
+    _step(h)
+    assert _STALE not in _texts(h)
+
+
+def test_korean_hedge_lines_state_the_side_and_rounding_of_the_tiles():
+    from quantgen_desktop.bonds_portfolio_narrative import hedge_text
+    for pos, cf in (("682.5", "1"), ("-682.5", "1"), ("-798.19", "0.8"), ("552.5", "1")):
+        h = _page()
+        h.tf["Position DV01"].value, h.tf["Conversion factor"].value = pos, cf
+        s = _calc(h, tool="hedge")
+        side = "sell" if "Contracts to sell" in s else "buy"
+        hedge = (float(pos), 65.0, float(cf), float(pos) * float(cf) / 65.0)
+        ko, en = hedge_text(hedge, "ko").splitlines(), hedge_text(hedge, "en").splitlines()
+        assert ko[0] == (f"선물 {'매도' if side == 'sell' else '매수'} {s[f'Contracts to {side}']}계약"
+                         f" · 반올림 {s['Rounded']}"), ko[0]
+        assert en[0] == (f"{side.capitalize()} futures {s[f'Contracts to {side}']} contracts"
+                         f" · rounded {s['Rounded']}"), en[0]
+        assert f"잔여 DV01 {s['Net DV01 after hedge']} / bp" in ko[2], ko[2]
+        assert f"rounding {s['Net DV01 after hedge']} per bp" in en[2], en[2]
+
+
+def test_key_rate_chart_is_given_a_korean_title():
+    import ui.bonds_page as page_module
+    seen = {}
+    real = page_module.fcharts.krd_chart
+    with _patched(page_module.fcharts, "krd_chart", lambda *a, **k: (seen.update(k), real(*a, **k))[1]):
+        _calc(_page())
+    z = seen["title"].split("z-spread ")[1].split(" held")[0]
+    assert seen["title"].startswith("Zero-curve key-rate DV01 (z-spread ")
+    assert z in seen["title_ko"] and any("가" <= ch <= "힣" for ch in seen["title_ko"]), seen
+
+
 def tests():
     return [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
```
