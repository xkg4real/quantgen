# Strategy Lab run registry and ledger-based trial counting (owner ruling R3)

Date: 2026-10-27.

Status:
- **Revision 2 (after Claude review round 1).** This is stage ②-6 of the rulings log
  (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:82-88`). Two Claude referees reviewed revision 1:
  - quantitative methodology: `docs/superpowers/specs/2026-10-27-run-registry-review/round1_claude_quant.md`
    (ACCEPT_WITH_CHANGES; 13 major, 8 minor);
  - engineering and governance: `docs/superpowers/specs/2026-10-27-run-registry-review/round1_claude_eng.md`
    (ACCEPT_WITH_CHANGES; 3 blockers, 13 major, 9 minor).
- Every blocker, major and minor issue is applied. No issue is rejected. Six are applied in a changed form and two are
  extended; Appendix A gives the ruling, the reason and the sections for each of the 46 issues.
- Owner approval: **not given**.
- This document is a design only. No repository code was changed for it. No ledger row, registry event or card was
  written. No test suite was run. The study was not run. The four excluded cache files were not opened or hashed.
- Next: the owner answers the build questions of 10.2 A. The criteria questions of 10.2 B wait for ⑨-3d. ⑨-3a starts
  after that, and its edits to `ui/strategy_lab_page.py` start only after the audit's proposed patches to that file are
  decided (1.5).

Main changes in revision 2:
- The shadow never writes `GATE`. It replays the decision on a copy of the existing score (6.4).
- `register_trials` is not touched. A new pure key builder is pinned against it and against golden `config_id`s (9.2,
  T-RUNREG-01b).
- Tests run only against temporary ledgers and registries (9.3). Recorder hooks cannot change or block a verdict (6.4).
- N_raw is a set cardinality, so a configuration counts once before and after adoption (3.13).
- A card's trial history is cut at the card's anchored fix time (6.6). Later rows are POST_CARD, never COUNT (7.2 E).
- A data choice made after seeing results counts as a trial in the primary reading (4.2 row 9b).
- The E rows use the matched pairing (N_eff, null SE). A new probe shows that this pairing alone, at today's trial
  count, changes one card's decision (S_E8_pairs_kodex_tiger, REVISE to REJECT) and two cards' reasons. Such
  differences are labelled PAIRING and reported apart from trial history (6.3, 7.2 F, 7.3).
- The validation plan has a published fractional design, a fixed Monte Carlo precision, Layer B as the layer of
  record, a new candidate C7 and a freeze before the of-record report (section 8).
- The owner's questions are split: build questions now, criteria questions at ⑨-3d (10.2).

Inputs (QUANTGEN at `527cdf2`; the working tree adds this spec, the three maps, the two round-1 reviews and the audit
notes under `docs/audit/2026-10-27/`). In `research_notes/QUANTGEN run registry map/`: `01_strategy_lab_and_cards.md`
(map01), `02_gate_ledger_semantics.md` (map02) and `03_effective_trials_methods.md` (map03). House style:
`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` sections 1 to 3.

Citation keys:
- `file:line` is a QUANTGEN path at `527cdf2`.
- `map0N §n` points into a map. `map03 R-n` is a rule of map03 §5.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
  - `scratch:r3_spec_probe/` holds the two read-only probes of revision 1 (`replay.py`, `flip.py`).
  - `scratch:r3_rev2_probe/` holds the two read-only probes of revision 2. `replay_lab.py` builds synthetic price
    panels in memory, imports `core.quant.strategies` and `core.quant.validate`, and writes nothing.
    `se_null_flip.py` reads card JSON and imports `core.quant.gate_ledger`. Neither touches a ledger.
- `Q-nn` and `ENG-nn` are issues of the two round-1 reviews.
- UNVERIFIED marks anything nobody in this session could check.

Spot-checks of the maps (revision 1, this session). Each claim below was re-read in the code or the card files:
- the frozen harness list (`core/quant/gate_package.py:36-38`);
- the Lab's order of work and its verdict call with `n_trials=len(grid)` (`ui/strategy_lab_page.py:104-127`);
- `config_id` excludes the span, and unknown row fields are refused (`core/quant/gate_ledger.py:60-61`, `:168-171`,
  `:190-192`);
- `RegisterResult.row_md5` is a line hash on append and the stored content hash on dedup (`gate_ledger.py:346`, `:355`);
- the 16 DSR-bearing cards: decision, DSR, N, T and Sharpe match map01 §4.1 (card JSON in `docs/asset_expansion/cards/`);
- the flip thresholds of the three narrowest cards, under normal moments: 769, 89 and 81 trials; and
  S_S6_pairs_hyundai_kia's DSR at N = 2 (0.9406) and at N = 1 (0.966) (`scratch:r3_spec_probe/flip.py`);
- the crypto-trend vote lattice (`core/quant/strategies.py:344-346`).

Additional checks in revision 2:
- **Replay is exact.** On synthetic panels, a copy of the existing score with only `dsr` and `n_trials` replaced,
  re-decided by `V._decide_strategy`, equals a fresh `V.score_strategy` call with that n on every `StrategyScore` field
  (NaN-aware, `lines` included). Cases: `trend_switch` (G = 12) and `crypto_trend` (G = 6), n ∈ {1, 2, G, 89, 769,
  5,000}; 12 of 12 equal (`scratch:r3_rev2_probe/replay_lab.py`).
- **The null-SE pairing on the 16 DSR cards** (normal moments; `scratch:r3_rev2_probe/se_null_flip.py`). Values are in
  7.3.
- **Card dates.** The 34 card files entered this repository in commit `eacd57d` (2026-10-23T00:53:18+09:00, "Baseline:
  QUANTGEN before the TRADEGEN split"). Every DSR card's `created` field is 2026-09-27 (for example
  `docs/asset_expansion/cards/S_E8_pairs_kodex_tiger.json:179`).
- **Lab concurrency.** The worker clears the result area per click and runs in a thread; the Run button is never
  disabled (`ui/strategy_lab_page.py:228`, `:279`, `:283`).
- **The ledger's card rule.** `selection_factor` uses the time-and-span filter only to decide whether f = 1. Once one
  row qualifies, it takes N_eff over every row of the reading (`gate_ledger.py:709-731`).
- **This container.** `flet` is importable; NumPy is 2.3.5; Python is 3.13.

Corrections carried from revision 1: map01 §1.3 cites `GATE["dsr_min"]` at `validate.py:56`; it is at
`core/quant/validate.py:55`. Every stored DSR card can be re-decided exactly from its stored fields (6.6).

---

## 1. Status and scope

### 1.1 Owner ruling R3 (binding)

Channel and date: 2026-10-27, Claude Code chat (cloud session). Recorded verbatim at
`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:71-80`.

> Strategy Lab의 시행 횟수는 원장 기반으로 전환하는 방향을 추천합니다. 다만 원장 기반 전환과 기존 카드 판정의
> 보수화는 분리해서 진행해주세요.
> 각 전략 실행에 고유 ID를 부여하고, 전략 버전·데이터 기간·파라미터·비용 조건·실행 결과·판정·실행 상태를 기록하도록
> 설계해주세요. 전체 실행 횟수와 과최적화 평가에 유효한 전략 실험 횟수는 구분해야 합니다. 단순 재실행, 실패한 실행,
> 파라미터 탐색, 독립 검증을 동일한 시행으로 취급하지 않도록 기준을 명시해주세요.
> 우선 원장 기반 기록과 기존 판정 결과를 병행 산출하여 두 방식의 차이를 비교해주세요. 기존 카드의 판정 기준은 이
> 단계에서 변경하지 말고, 시행 이력을 반영했을 때 판정이 달라지는 사례와 그 근거를 제시해주세요. 과최적화 보정
> 기준의 타당성을 별도로 검증한 후 판정 기준 변경 여부를 결정하겠습니다.

English rendering (Claude's translation; the Korean text governs, as the log states at
`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:3-4`):

> I recommend moving Strategy Lab's trial count to a ledger basis. However, please keep the move to a ledger basis
> separate from making the existing cards' verdicts more conservative.
> Please design it so that every strategy run gets a unique ID and records the strategy version, data period,
> parameters, cost conditions, run results, verdict and run status. The total number of runs must be kept apart from
> the number of strategy experiments that are valid for assessing overfitting. Please state criteria so that simple
> re-runs, failed runs, parameter searches and independent validations are not treated as the same kind of trial.
> First, compute the ledger-based record and the existing verdicts in parallel and compare the two methods. Do not
> change the existing cards' verdict criteria at this stage. Show the cases where a verdict would change once the
> trial history is reflected, and the reasons. I will decide whether to change the verdict criteria after the
> overfitting-correction criterion has been validated separately.

Addendum found on 2026-10-28. The owner's Google Drive copy of `REMAINING_WORK_2026-10-27.docx` (modified
2026-10-27T08:38:43Z) carries one more sentence in the R3 cell, after the text above. It is not in the chat ruling and
is recorded in the rulings log as an addendum:

> 기존 실행 기록의 마이그레이션 가능성, 중복 기록 방지, 재현성, 데이터 무결성, 테스트 계획도 함께 제시해주세요.

English rendering: "Please also present the feasibility of migrating existing run records, prevention of duplicate
records, reproducibility, data integrity and a test plan." Rows T19 to T23 of section 2 trace it.

The rulings log splits the work into five stages (`OWNER_RULINGS_LOG.md:82-88`;
`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:95-120`):

| Stage | Work | Owner of the result |
|---|---|---|
| ②-6 | this design | Claude drafts; the owner approves |
| ⑨-3a | build the registry; compute ledger-based counts beside the existing verdicts | Claude |
| ⑨-3b | comparison report: the cards whose verdict would change, and why | Claude; the owner reads |
| ⑨-3c | validate the overfitting-correction criterion | Claude; recommendation to the owner |
| ⑨-3d | decide whether to change verdict criteria | the owner |

### 1.2 What this stage does

1. It defines a run registry. Every Strategy Lab run gets a unique run ID and records the seven items R3 names
   (section 5).
2. It defines TOTAL runs, N_raw, N_eff and N_validation, and the rules that classify each run (sections 3 and 4).
3. It defines a shadow computation. The existing verdict is computed exactly as today. Beside it, decisions with
   ledger-based trial counts are replayed and labelled. They are never written to a card (section 6).
4. It defines the comparison report of ⑨-3b (section 7) and the validation plan of ⑨-3c (section 8).
5. It lists the modules, tests and steps for ⑨-3a to ⑨-3c (section 9).
6. It lets a person change a count only through an event that cites an owner ruling (4.1 principle 2).

### 1.3 What this stage does not do

- It does not change `GATE` (`core/quant/validate.py:53-74`) or the decision rule `_decide_strategy`
  (`validate.py:536-622`). No new code assigns to `GATE` (6.1).
- It does not change the Lab's verdict call. The Lab keeps `n_trials=len(grid)` (`ui/strategy_lab_page.py:127`).
- It does not change stored cards. The 34 files in `docs/asset_expansion/cards/` stay byte-identical. They are a
  read-only tree of T-HERM-02 (`tests/macro_acceptance.py:26-27`).
- It does not edit a frozen harness file (`core/quant/gate_package.py:36-38`). The design imports `validate`,
  `gate_ledger`, `gate_stats` and `strategies`. It edits none of them.
- It does not change `register_trials` (`ui/strategy_lab_page.py:55-82`), the Lab's only writer of ledger rows. Its
  source stays byte-identical (T-RUNREG-01b). The registry never writes a ledger row.
- It does not change what the Lab writes to its family ledger, or when (5.8).
- It does not run or change `docs/asset_expansion_study.py`.
- It does not edit, import or run anything in `paper_live/` or `grokteam/`, including `tests/paper_live_acceptance.py`
  (9.3).
- It never needs the four excluded cache files: `docs/asset_expansion/cache/yf_SPY.csv`, `yf_BTC-USD.csv`,
  `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv` (7.4).

### 1.4 The separation R3 requires

Three things are kept apart.
- **Counting** moves to a ledger basis now, in shadow. It is recorded and printed. It decides nothing.
- **Pairing** is part of the verdict criterion. The DSR hurdle is N's expected maximum times a dispersion term. The gate
  uses the current grid's Sharpe dispersion (`validate.py:505-507`). Replacing it with the null standard error, at
  today's trial count, changes one card's decision and two cards' reasons (7.3). The report labels such differences
  PAIRING, never COUNT (7.2 E).
- **Verdict criteria** change only after ⑨-3c validates a criterion and the owner rules at ⑨-3d. Until then, every
  displayed verdict, every card and every input of the AI panel is what today's code produces.

### 1.5 Order with other rulings

- **Audit first.** Ruling ①-2 puts the owner's audit before other implementation (`OWNER_RULINGS_LOG.md:42-47`). Audit
  item P-01 names `ui/strategy_lab_page.py`. D-01 and D-02 target the cleaning in `core/quant/history.py`
  (`docs/audit/2026-10-27/00_request.md:20-22`). So ⑨-3a's edits to the Lab page start only after the audit's
  proposed patches to that file are decided (9.7 step 0b). A later D-01 or D-02 fix changes the cleaned data. The
  registry then records the same request as REMEASURE (4.2 row 9a); the changed `history.py` digest triggers a behaviour
  check, which finds no change on the canonical panel (row 8a).
- **Locked holdout.** Rule ⑧-2 locks all data from 2027-01-01 for every design
  (`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:122`). The Lab always loads the latest sessions
  (`ui/strategy_lab_page.py:104`). So from 2027 every real-data Lab run touches the locked data. The registry flags each
  such run HOLDOUT_TOUCHED (4.2 row 16) and the report lists them (7.2 H). Whether to block such runs is Q22.

---

## 2. Requirements traceability

| # | R3 clause (Korean) | Meaning | Satisfied by |
|---|---|---|---|
| T1 | 시행 횟수는 원장 기반으로 전환하는 방향 | trial counts move to a ledger basis | 3.13 (counts built on the family ledger); 5.4 "Ledger link"; 6.2 and 6.3; Q17 (shadow-only reading of "전환") |
| T2 | 원장 기반 전환과 기존 카드 판정의 보수화는 분리 | keep the ledger basis apart from stricter verdicts | 1.3, 1.4; 6.1 invariants; 6.4 (replay; no `GATE` write); 6.7 (never in a card); 7.2 E (COUNT against PAIRING); 9.7 step 9 |
| T3 | 각 전략 실행에 고유 ID | a unique ID per run | 3.2, 5.5; Q18 (Lab runs only in this stage) |
| T4 | 전략 버전 | strategy version | 3.3, 3.4, 3.7; 5.4 "Strategy version" and "Environment" |
| T5 | 데이터 기간 | data period | 3.5, 3.8; 5.4 "Data" |
| T6 | 파라미터 | parameters | 3.6; 5.4 "Grid" (STARTED) and `registered` (PROGRESS) |
| T7 | 비용 조건 | cost conditions | 5.4 "Cost"; 4.2 row 10 |
| T8 | 실행 결과 | run results | 5.4 "Results"; 5.7 |
| T9 | 판정 | verdict | 5.4 "Existing verdict" and SHADOW; 3.18; section 6 |
| T10 | 실행 상태 | run status | 5.4 FINISHED; 5.6 |
| T11 | 전체 실행 횟수와 ... 유효한 전략 실험 횟수는 구분 | keep TOTAL runs apart from valid experiments | 3.12 to 3.15; 4.2 (separate columns); 5.2 outage file (TOTAL gaps are bounded) |
| T12 | 단순 재실행, 실패한 실행, 파라미터 탐색, 독립 검증 ... 기준을 명시 | explicit criteria for re-runs, failures, searches, validations | 4.1 to 4.3; 4.2 rows 1 to 7b |
| T13 | 원장 기반 기록과 기존 판정 결과를 병행 산출 | compute both in parallel | section 6 |
| T14 | 두 방식의 차이를 비교 | compare the two | section 7 |
| T15 | 기존 카드의 판정 기준은 이 단계에서 변경하지 말고 | do not change card criteria now | 1.3; 6.1; T-RUNREG-01, -01b, -06, -07 (9.3) |
| T16 | 판정이 달라지는 사례와 그 근거 | the cases that would flip, with reasons | 6.6 (time-bounded card counts); 7.2 A, E and F; 7.3 |
| T17 | 과최적화 보정 기준의 타당성을 별도로 검증 | validate the correction criterion separately | section 8; 8.8 (freeze before the of-record report) |
| T18 | 그 후 판정 기준 변경 여부를 결정 | the owner decides afterwards | 8.5 (recommendation only); 9.7 step 9; 10.2 B |
| T19 | 기존 실행 기록의 마이그레이션 가능성 (addendum) | can existing run records be migrated | 9.6 (read-only: LEDGER_ONLY trials computed on the fly from the family ledgers; fields never invented; C3 BACKFILL only after Q9); 3.13 |
| T20 | 중복 기록 방지 (addendum) | no duplicate records | 5.2 (a second STARTED or FINISHED for one `run_id` is refused under the lock; a duplicate run ID is retried with a new token); 4.2 rows 1 and 6 (identical re-runs and semantic duplicates add no N_raw); T-RUNREG-02, T-RUNREG-05 |
| T21 | 재현성 (addendum) | reproducibility | 3.3 to 3.5 (code identity, behaviour fingerprint, `data_md5`); 5.4 "Environment"; 9.6 (each report stores the family hash and `n_raw`, so `snapshot(hash)` re-proves it); 8.6 (seeds); T-RUNREG-08 (identical bytes for one `as_of`), T-RUNREG-10 |
| T22 | 데이터 무결성 (addendum) | data integrity | 5.2 (canonical JSON, `row_md5` chain, `verify_chain` on every read and append, fail closed, never repaired; lock; segments and outages); 6.6 (stored cards never recomputed; MD5s unchanged); T-RUNREG-02, T-RUNREG-04, T-RUNREG-07 |
| T23 | 테스트 계획 (addendum) | a test plan | 9.3 (T-RUNREG-00 to -12) and 9.4 (suite registration, registry rows) |

---

## 3. Definitions

### 3.1 Run
One call of `run_family` (`ui/strategy_lab_page.py:85-136`) made by the Lab page with a recorder, whatever its outcome.
A run starts when the recorder writes its STARTED event at the entry of `run_family` (after the family lookup at
`strategy_lab_page.py:89`), before the argument checks at `:90-96`. So "no symbols" and "no cost row" are runs that
fail before any statistic (4.2 row 3). A parse error on the page before `run_family` is called
(`strategy_lab_page.py:232-235`) is not a run. The module self-check (`:320-330`) and the tests call `run_family`
without a recorder. They record nothing, as today.

### 3.2 Run ID
A string `LAB-<UTC compact>-<family_id>-<8 hex>`, for example `LAB-20261027T081530Z-E1-3f9a0c1d` (5.5). It is unique
in the registry. It never enters a result hash.

### 3.3 Strategy version and code identity
- `fn_qualname`: the strategy function, for example `core.quant.strategies.trend_switch`. For pairs it is
  `core.quant.strategies.pairs`; the Lab wraps it in a local adapter (`strategy_lab_page.py:109-112`).
- `fn_source_sha256`: SHA-256 of `inspect.getsource(fn)`, with CRLF normalised to LF, encoded as UTF-8.
  `fn_source_sha256_raw` keeps the hash of the unnormalised text. Git keeps the repository byte-exact
  (`.gitattributes:1-2`), but an editor or a sync client can change line endings on the owner's machine. The house
  precedent hashes LF-normalised text for this reason (`research_notes/QUANTGEN v2 integration
  map/spec_M7_gate_package.md:712`).
- `repo_anchor`: `gate_ledger.repo_anchor()`, that is `git:<HEAD sha>` or `UNVERSIONED` (`gate_ledger.py:122-131`). It
  reads only a loose ref file. A packed ref gives UNVERSIONED, and so does a copy that is not a git repository, as the
  owner's copy once was (`research_notes/QUANTGEN v2 integration map/code_tests_data.md:684`). It cannot see
  uncommitted edits (map02 §8, F10).
- `files`: for each decision-path file (5.4), the SHA-256 of its LF-normalised bytes and of its raw bytes. These carry
  the version when the anchor is UNVERSIONED or the tree is dirty.
- **Code identity** = (`fn_source_sha256`, the LF-normalised `files` digests).

### 3.4 Behaviour fingerprint
SHA-256 of one configuration's positions (rounded to 1e-10) and net P&L (rounded to 1e-12) on the canonical panel, at
the configuration's cost and the Lab's cash rate (5.4).
- The canonical panel is a fixed array shipped in the repository as a fixture, with its SHA-256 pinned in the new
  module. It is never regenerated at run time, so a NumPy upgrade cannot change it.
- It is computed once for each new (configuration, code identity) pair, after the display, and cached (5.3). It is
  compared only when a configuration's code identity differs from every earlier evaluation of the same `config_id`
  (4.3 step 3). An environment change alone never triggers a comparison (row 1b).
- It separates a refactor (map03 R-5a) from a logic change (R-5b). It also proposes semantic duplicates (R-3b); those
  stand only with equal real-data fingerprints as well (4.2 row 6).

### 3.5 Data snapshot, data period and data request
- `span`: the first and last date of the aligned panel.
- `data_md5`: MD5 of the panel's canonical bytes (5.4).
- Per symbol: the resolved symbol, its source, note, `adjustment` and `status` (`core/quant/history.py:55-68`), its first
  and last date, its session count and an MD5 of its closes.
- Data request: (`source_requested`, `days`), the two inputs the operator chooses (`strategy_lab_page.py:219-223`).

### 3.6 Configuration
The ledger's `config_id` of the row the Lab builds for one grid point (`gate_ledger.py:60-61`, `:168-171`;
`strategy_lab_page.py:73-81`). It covers the family rule, the grid point θ, the symbols, `cost_bps` and the timing
class. It does not cover the span, the data source, the run time or the code.

### 3.7 Code lineage
For one (`family_id`, `config_id`), the code identities that evaluated it form lineages. A new code identity joins
the lineage of the latest earlier code identity of that `config_id` when their behaviour fingerprints on the same
panel hash are equal. Otherwise it starts a new lineage. A lineage is named by its first code identity.

### 3.8 Data variant
For one (`family_id`, `config_id`, lineage), a data variant is a set of data requests. A request that row 9a admits
stays in the current variant. A request that row 9b classifies starts a new variant (4.2).

### 3.9 Experiment key
`(family_id, config_id, lineage, data variant)`. The distinct-data reading drops the data variant (4.4).

### 3.10 Trial (experiment)
An experiment key whose performance statistic was produced on real data. It is counted once per scope, however many
runs evaluate it (map03 §1).

### 3.11 Statistic and stage
A statistic is any per-configuration performance number. In the Lab the first one exists when `S.pnl_matrix` returns
(`strategy_lab_page.py:114`). The registry records the stage a run reached (5.6). The stage decides whether a failed run
counts.

### 3.12 TOTAL runs
The number of STARTED events in a scope. Every status and every class counts. Runs made while the registry was
unavailable are not in TOTAL. The outage file records them, and the report prints a lower bound for them (5.2, 7.2 G).

### 3.13 N_raw (a set cardinality)
For a scope and an instant `as_of`:

N_raw = |K| + |L \ cfg(K)|

- **K** is the set of experiment keys in the scope with at least one counting evaluation up to `as_of`, in chain order.
  A counting evaluation is a real-data evaluation that produced a statistic, other than an unspent VALIDATION (4.2
  row 7). K also holds the RECONSTRUCTED keys of ratified BACKFILL events (row 14). Ratified human events can merge two
  lineages into one key (row 8c).
- **L** is the set of `config_id`s of the family ledger in the scope, in the ledger snapshot used for `as_of` (7.1).
- **cfg(K)** is the set of `config_id`s that keys in K hold. The second term is the LEDGER_ONLY term (row 13).

Consequences:
- A configuration counts once, before and after a registry run adopts it (row 13a). This is pinned by T-RUNREG-05.
- The per-row deltas of 4.2 are the changes in this cardinality when one run is folded in chain order. A class
  explains a delta. It never computes one. Two runs that both label one key SEARCH (an interleaving, 5.4) still add
  one element to K.

Readings:
- **literal** (as above);
- **distinct-rule**: semantic duplicates (row 6) are one element of K;
- **distinct-data**: data variants of one (`config_id`, lineage) are one element of K.

Scopes:
- **family-wide** (all markets and all writers of the family ledger);
- **market-scoped** (rows and keys with the run's ledger market, `strategy_lab_page.py:71-72`);
- **universe-scoped**, for stored cards only: the card's symbol set (6.6).

The ledger itself defines the first two scopes (`gate_ledger.py:62`, `:708-709`).

### 3.14 N_eff
The correlation-adjusted count of the trials of a scope: `gate_ledger.n_eff(series).N_eff`, which is
`max(N_clusters, N_equiv)` (`gate_ledger.py:574-582`). Inputs and limits:
- Each trial's series is its full-sample daily net P&L column, the column the gate's dispersion term uses
  (`validate.py:505-506`). It is passed as a pandas Series indexed by the stored day number (5.7), so that `n_eff`
  aligns series by date.
- `n_eff` uses one common window, the intersection of all indices. It refuses fewer than 20 common observations
  (`gate_ledger.py:421-444`, `:76`). Mixed markets, pairs and eras can shorten or empty that window. Every N_eff is
  printed with its common-window length.
- A constant column makes the correlation refuse (`gate_ledger.py:447-457`). A configuration that never trades earns a
  constant cash P&L, so one such column makes the whole scope unavailable. The primary reading then prints "N_eff
  unavailable: <reason>". A secondary reading drops constant columns and says how many.
- `n_eff` is documented for difference series (`gate_ledger.py:16-17`, `:447-449`), not raw P&L. Its calibration does
  not transfer by assumption. ⑨-3c checks it on raw P&L (8.3, estimator checks).
- The clustering is the ledger's average-linkage cut at ρ = 0.5 (`gate_ledger.py:473-483`). It is not López de Prado
  and Lewis's ONC algorithm (map03 §2.3).
- N_eff is unavailable when any trial of the scope lacks a stored series. LEDGER_ONLY rows have none. So on the
  owner's machine E-FAM and E-MKT are expected to be unavailable for every family with rows from before the registry,
  unless Q11 is answered yes. The coverage `k of n` is printed.
- `N_eff(grid)` is the same quantity over one run's grid only.

### 3.15 Validation record and N_validation
A DECLARATION event (fixed configuration, pass rule, span, anchor) plus the run that evaluates it. N_validation counts
the runs that meet all four conditions of 4.2 row 7. N_validation is not part of N_raw.

### 3.16 Gate version
SHA-256 of the LF-normalised bytes of `core/quant/validate.py`, together with the canonical JSON of the effective `GATE`
at scoring. The effective `GATE` includes the Lab's bootstrap override (`strategy_lab_page.py:124-129`).

### 3.17 Environment
The Python, NumPy, SciPy and pandas versions, `platform.system()` and `platform.machine()`, recorded in STARTED. A
change of environment alone never creates a new key (4.2 row 1b).

### 3.18 Existing verdict and shadow decision
- **Existing verdict**: the decision, reason and revise target that `score_strategy(..., n_trials=len(grid))` returns
  today.
- **Shadow decision**: the decision the unchanged `_decide_strategy` gives on a copy of the existing score in which only
  `dsr` and `n_trials` are replaced (6.4). It is labelled "SHADOW — not a verdict" wherever it is shown.

### 3.19 SE_null
The per-period standard error of a zero Sharpe ratio under normal returns: SE_null(T) = 1 / √(T − 1). The primary T is
T_oos, the length of the walk-forward OOS series the gate tests (`validate.py:498-507`). A secondary reading uses
T_full, the length of the full-sample P&L. Reason: the statistic under test has T_oos observations, so its null
standard error has T_oos observations too (Q-10). ⑨-3c evaluates both (8.2).

---

## 4. Run classification rules

### 4.1 Principles

1. **Unit.** Each pair (run, registered configuration) gets a class. Registered keys are built from the resolved
   symbols and the resolved cost (5.4 PROGRESS). Planned keys, built from the typed symbols at the entry of
   `run_family`, are used only for display and for a run whose stage is unknown (5.6). The run gets a summary: the count
   per class.
2. **Default is to count.** A configuration leaves N_raw only for a reason that can be checked from stored fields, or
   through a human event that carries an owner ruling (5.4 "Human events"). A human event without an owner ruling
   changes only the secondary reading "with unratified human events" (4.4). This is map03's principle (§5), with the
   ratification rule of ENG-10.
3. **Pure function.** The class is a function of the registry events, the family ledger rows (read-only) and an
   `as_of` instant. A run's ledger state is the ledger prefix before its own registration (5.4 "Ledger link"), never a
   time cut on `run_utc`. The report recomputes every class. The class stored at write time stays for audit;
   differences are printed.
4. **Counts are set cardinalities** (3.13). A class labels a change; the change is computed from the sets.
5. **Contested cases print two readings.** The first is primary in the printed counts. Until ⑨-3d the primary is a
   display convention, not a verdict criterion (10.2).
6. **Classes never change the existing verdict.**

### 4.2 Decision table

Columns: TOTAL; change of literal N_raw (lit.); change of distinct-rule N_raw (rule); whether the trial's series enters
the N_eff input; N_validation (val.). "+k" means plus one per key of the run that is new to K. Every N_raw entry is the
change of the cardinality of 3.13 when the run is folded in chain order.

| # | Case (R3 term) | Test on stored fields | Class | TOTAL | lit. | rule | N_eff input | val. | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Identical re-run** | every key of the run was evaluated before, with the same `data_md5`, gate version, seed, bootstrap B and environment | RERUN | +1 | 0 | 0 | no new series | 0 | An exact duplicate cannot change the maximum of a set, so it cannot change a selection (map03 R-1, §4.2). The ledger reads a re-run as the same trial (`gate_ledger.py:14-15`). |
| 1a | identical re-run, different real-data result | as row 1; the result fingerprints differ | RERUN + flag NONDETERMINISTIC | +1 | 0 | 0 | no | 0 | A defect to fix, not a trial (map03 R-1). |
| 1b | **re-run in a changed environment** | as row 1, except that the environment differs (3.17) | ENV_CHANGE; flag RESULT_CHANGED when the result fingerprint differs | +1 | 0 | 0 | the key's series is replaced by the latest | 0 | A library or platform change is not a new hypothesis. R3 asks that simple re-runs not be counted as experiments (Q-08, ENG-08). |
| 2 | evaluation re-draw | same keys and data; only seed or bootstrap B differs | EVAL_REDRAW; flag VERDICT_UNSTABLE when the decisions differ | +1 | 0 | 0 | no | 0 | The strategy is unchanged. The 0 holds because the verdict of record is the one at the pre-registered seed and B (study seed 11, `GATE` B 2,000; `validate.py:54`, `:493`); choosing among re-draws would select on outcome (map03 R-1b; Simmons, Nelson & Simonsohn 2011; Gelman & Loken 2013). The Lab always uses B = 1,000 and seed 11 (`strategy_lab_page.py:86`; `validate.py:493`), so no pair of Lab runs is a re-draw today. A Lab verdict is itself a re-draw of a study verdict at B = 2,000 (map03 R-1b); the report says so when it sets a Lab run beside a card. |
| 3 | **Failed run, before any statistic** | stage below PNL_COMPUTED: no symbols (`strategy_lab_page.py:90-91`); no cost row (`:94-96`); a `HistoryError` from `load_history`; fewer than 60 shared sessions in `align_panel` (`core/quant/strategies.py:59-60`); a pairs panel that is not two columns wide (`strategy_lab_page.py:107-108`); an exception inside `pnl_matrix` | FAILED_BEFORE_STATS | +1 | 0 | 0 | no | 0 | No outcome existed, so nothing could be selected on (map03 R-2a). |
| 4 | **Failed run, after a statistic was computed or displayed** | stage PNL_COMPUTED or later: too few sessions for one walk-forward step (`validate.py:366-367`); a ledger refusal at registration; an exception in scoring; or ABORTED with its stage inferred from the last PROGRESS event, or unknown (5.6) | the class of rows 5 to 10 per configuration, with flag FAILED (and STAGE_UNKNOWN when unknown) | +1 | +k | +k (new rules) | yes, if its series was stored | 0 | The file-drawer problem (Rosenthal 1979); discarded results must be disclosed (López de Prado 2019). The registry fails closed when it cannot show that no statistic existed (map03 R-2b). Secondary reading: failures never displayed are left out. |
| 5 | **Parameter search** | a key not yet in K: a new θ, a revised grid, a new universe, a new cost, a new lineage (row 8b) or a new data variant (row 9b) | SEARCH | +1 | +k | +k (new rules) | yes | 0 | Every configuration tried is a trial for the DSR (Bailey & López de Prado 2014) and a column for PBO (Bailey, Borwein, López de Prado & Zhu 2017); map03 R-3a. |
| 6 | semantic duplicate | a new `config_id` whose params differ from an existing key's only in θ; equal behaviour fingerprints; and equal real-data fingerprints whenever both ran on the same `data_md5` | SEMANTIC_DUPLICATE | +1 | +1 | 0 | linked to the existing series, not added twice | 0 | Duplicates bias count-based estimators and PBO (map03 R-3b, §4.2, §4.4). The canonical panel has no tied prices, so a fingerprint match there does not settle ties on real data (4.5). |
| 7 | **Independent validation** | all four conditions below hold | VALIDATION | +1 | 0 | 0 | no | +1 | A pre-registered single test on untouched data makes no selection on that data (Nosek et al. 2018; Dwork et al. 2015). The ledger's f = 1 route encodes it (`gate_ledger.py:719-722`). Contested: CRY-1 counts a pre-registered split as one more trial (`docs/techfund_study.py:83-85`); the secondary reading counts it (map03 R-4). |
| 7a | validation condition fails | any of the four conditions fails | class of rows 5, 9 or 10, with reason "validation condition (i), (ii), (iii) or (iv) failed" | +1 | as that class | as that class | as that class | 0 | Default is to count. |
| 7b | **validation spent** | a later run evaluates a validated key on an overlapping span after the validation result | the validation record becomes VALIDATION_SPENT, and its keys join K from the validation run's position; the later run is classified by rows 5, 9 or 10 | +1 | +k (the validated keys, once) | +k | yes | 0 (the earlier +1 stays on record, marked spent) | The result was seen and the configuration was evaluated again, so the holdout became part of the search (Dwork et al. 2015). map03's counting table books "VALIDATION_SPENT → re-tuned run" as +1 (map03 §5, counting table). Only prospective incubation stays clean (`core/quant/tf_gov.py:487-489`). |
| 8a | **code-version change**, non-functional | same `config_id`; code identity differs; behaviour fingerprint equal | same lineage, so rows 1, 1b, 2, 8d or 9a per the other differences | +1 | 0 | 0 | as that row | 0 | map03 R-5a. |
| 8b | code-version change, logic | same `config_id`; code identity differs; behaviour fingerprint differs | new lineage, so row 5; flag ENV_CONFOUNDED when the environment also changed | +1 | +k | +k | yes | 0 | map03 R-5b. When the environment changed too, a library may have caused the difference. The key is still counted (default to count) and listed for the owner. |
| 8c | code-version change, bug fix | as 8b, plus an ANNOTATION with an owner ruling that names the defect and the test that shows it, and states that the fix applies to every configuration of the family | the earlier runs become SUPERSEDED; the new lineage merges into the old one | +1 | 0 | 0 | the corrected series replaces the old one | 0 | Contested (map03 R-5c). Without the owner ruling the merge appears only in the secondary reading, and the primary is row 8b. |
| 8d | gate change | code identity of the strategy and behaviour unchanged; gate version differs | GATE_CHANGE | +1 | 0 | 0 | no | 0 | A gate change is not a strategy trial. Verdict differences go to the gate, not to trials (map03 R-5d; `gate_package.py:241-255`). |
| 9a | **data-vintage change**, re-measurement | same key; `data_md5` differs; and either the same data request as the current data variant, or the same `source_requested` with `days` increased after a displayed decision whose revise target says "extend history" (`validate.py:590`, `:611`, `:620`, `:621`) | REMEASURE; flag DATA_FRAGILE when the decision differs from the previous evaluation; flag SOURCE_RESOLVED_CHANGED when the resolved source differs under the same requested source | +1 | 0 | 0 | the key's series is replaced by the latest | 0 | The configuration is unchanged; span is not in `config_id` (`gate_ledger.py:60-61`); map03 R-6a, R-6b. Extending history is the gate's own instruction, not a search. A changed resolution under `auto` (for example KRX symbols moving from the synthetic fallback to KIS once credentials exist, `core/quant/history.py:491-496`) is not the operator's choice. |
| 9b | **data-vintage change**, data choice | any other change of `source_requested` or `days` after a displayed evaluation of the key, including a decrease of `days` (a later start date) | DATA_CHOICE: a new data variant, so SEARCH | +1 | +k (primary) | +k | yes, a separate series | 0 | map03 R-6c: "that dimension was searched. Each alternative evaluated is an experiment." map03's counting table books R-6c under SEARCH. Secondary (distinct-data) reading: 0. |
| 10 | **cost-condition change** | `cost_bps` differs, so `config_id` differs (cost sits in `params`, `strategy_lab_page.py:75-76`) | SEARCH (row 5) with flag COST_VARIANT; also COST_SENSITIVITY when the cost is below the table rate and the verdict is withheld (`strategy_lab_page.py:92-103`) | +1 | +k | +k | yes | 0 | Every cost variant is a configuration (map03 R-3a, R-2c). Secondary reading leaves COST_SENSITIVITY keys out (map02 F2). The 2× stress inside every run is not a trial: it is computed for every configuration at a fixed multiplier (`core/quant/strategies.py:387`; `GATE["cost_stress"]`, `validate.py:57`). A change of the table rates (`validate.py:78`) is a gate change (row 8d). |
| 11 | **exploratory vs confirmatory** | every run is exploratory unless it carries a declaration that passes row 7; a run labelled confirmatory that fails a condition is exploratory | — | as its class | as its class | as its class | as its class | +1 only via row 7 | Pre-registration separates confirmatory from exploratory work (Nosek et al. 2018; map03 R-4). |
| 12 | synthetic data | any panel source is SYNTHETIC, including the `auto` fallback when no provider is configured (`core/quant/history.py:494-496`, `:504-506`, `:509-511`) | SYNTHETIC | +1 | 0 | 0 | no | 0 | map03 R-7; the Lab already registers nothing for synthetic runs (`strategy_lab_page.py:60-61`). |
| 13 | ledger row, no registry key | a `config_id` in L held by no key in K | LEDGER_ONLY | 0 (no known run) | +1 (second term of 3.13) | +1 | no series, so N_eff is unavailable for the scope | 0 | Unknown history is never zero (map03 R-8; map02 §10). |
| 13a | first registry evaluation of a LEDGER_ONLY configuration | the key's `config_id` was in the ledger prefix before this run's registration, and no earlier key in K holds it | ADOPTED | +1 | 0 (+1 in \|K\|, −1 in the LEDGER_ONLY term) | 0 | yes (adds the series) | 0 | One configuration, counted once. A `config_id` this run appended itself is SEARCH (row 5). When the ledger link cannot tell (another writer interleaved, 5.4), the key is SEARCH with flag INTERLEAVED; N_raw is the same either way. |
| 14 | trials before the registry, from a card's written history | a BACKFILL event with an owner ruling (C3, `docs/asset_expansion_study.py:340-343`; Q9) | RECONSTRUCTED | 0 | +k | as recorded | no | 0 | map03 R-8. Without an owner ruling: secondary reading only. |
| 15 | superseded | a later SUPERSEDED event names the run | status SUPERSEDED | stays +1 | per row 8c | per row 8c | per row 8c | 0 | The run stays in TOTAL (map03 R-5c). |
| 16 | locked holdout touched | any class; the panel span ends on or after 2027-01-01 | flag HOLDOUT_TOUCHED | as its class | as its class | as its class | as its class | as its class | Rule ⑧-2 (`REMAINING_WORK_2026-10-27.md:122`). A flag, not a class; the report lists such runs (7.2 H). |

**The four conditions of an independent validation (row 7).**
1. A DECLARATION event names the family, the `config_id`s, the `fn_source_sha256`, the pass rule (the `GATE` subset,
   seed and B) and the validation span. Its `anchor` is `git:<sha>` of a commit that contains the declaration, or
   `external:<ref>`, and `gate_ledger.anchored` accepts it (`gate_ledger.py:114-119`). The registry's own timestamp is
   not an anchor, because its clock is injected.
2. No run of the family touched the validation span before the anchor. "Touched" uses the family-wide reading over
   registry spans and ledger spans, with `gate_ledger.overlaps` (`gate_ledger.py:674-676`). The span is also not in the
   contamination log when one is configured (`core/quant/tf_gov.py:487-520`).
3. It is the first evaluation of those keys on that span.
4. The result is recorded whatever it is (a FINISHED event exists).

The Lab always loads the latest `days` sessions (`strategy_lab_page.py:86`, `:104`). It cannot evaluate a fixed
configuration on a chosen span. So no Lab path produces VALIDATION yet. The classifier and the DECLARATION event exist
so that a later validation mode needs no schema change (out of scope, 10.3).

### 4.3 Classification order for one (run, registered configuration)

1. Status FAILED_BEFORE_STATS → class FAILED_BEFORE_STATS (status and class share the name). No configuration is
   counted; TOTAL +1.
2. Any SYNTHETIC source → SYNTHETIC.
3. Compute the code identity. If it is new for this `config_id`, read or compute the behaviour fingerprint and assign
   the lineage (3.7); otherwise the lineage is the one already assigned. Determine the data variant by rows 9a and 9b.
   This gives the experiment key. Collect the key's earlier evaluations in the scope (registry events earlier in chain
   order).
4. A declaration is present → test the four conditions → VALIDATION, or record which condition failed (row 7a).
5. The key is new to K:
   - its `config_id` was in the ledger prefix before this run's registration and no earlier key in K holds it →
     ADOPTED;
   - else a semantic-duplicate match → SEMANTIC_DUPLICATE;
   - else → SEARCH, with flags COST_VARIANT, ENV_CONFOUNDED or INTERLEAVED as they apply. A new data variant is
     labelled DATA_CHOICE and a new lineage is labelled with its row (8b).
6. The key was seen. Compare with its latest earlier evaluation. Take the first difference in this order:
   1. data (`data_md5`) → REMEASURE (row 9a; a row 9b change made the key new in step 5);
   2. gate version → GATE_CHANGE;
   3. seed or B → EVAL_REDRAW;
   4. environment → ENV_CHANGE;
   5. none → RERUN (flag NONDETERMINISTIC when the result fingerprint differs).

   Add flag MULTI_CHANGE that names every difference found.
7. Status FAILED_AFTER_STATS or ABORTED: keep the class and add the flag FAILED.
8. Apply ratified SUPERSEDED, ANNOTATION and BACKFILL events last (rows 8c, 14, 15). Unratified ones change only the
   secondary reading.
9. Add the flags that do not depend on the class: HOLDOUT_TOUCHED, COST_SENSITIVITY, DATA_FRAGILE,
   SOURCE_RESOLVED_CHANGED.

Why this precedence (Q-16 (b), ENG-09). The only seen-key difference that counts is a data choice, and step 5 already
makes it a new key. Every other combination adds no new strategy information, so it adds nothing to N_raw. The flag
keeps the combination visible.

This follows map03 §5 "Classification order", with four additions: the adoption of ledger rows, the gate-change class,
the environment class and the precedence above.

### 4.4 Readings printed side by side

| Topic | Primary reading (in the counts) | Secondary reading (printed) | Source of the doubt |
|---|---|---|---|
| Duplicates | literal N_raw | distinct-rule N_raw | map03 R-3b |
| Data choice | each alternative a trial (+k) | not a trial (distinct-data N_raw) | map03 R-6c (changed in revision 2, Q-06) |
| Failed after statistics | all counted | only displayed failures counted | map03 R-2b (stage cut-off is reasoned) |
| Cost sensitivity | counted | left out | map02 F2, §14 Q2 |
| Validation | not a trial | one more trial (CRY-1) | map03 R-4; `docs/techfund_study.py:83-85` |
| Human events | ratified events only | with unratified events | ENG-10 |
| Scope, Lab runs | family-wide | market-scoped | `gate_ledger.py:679-686` takes the larger |
| Scope, stored cards | family-wide | market-scoped; universe-scoped | Q-04; 6.6 |
| Time cut, stored cards | rows before the card's anchored fix time | rows before the card's `created` date; all rows (POST_CARD) | Q-04, ENG-11; `gate_ledger.py:688-733` |

The dispersion pairing is not a reading of the count. It is a criterion. Rows that change it are shown apart (6.3,
7.2 F).

### 4.5 Worked examples

- **C3.** The card counts N = 11 (`docs/asset_expansion_study.py:339`): the 6-point grid of runs 2 and 3 plus the
  5-point lattice. The Lab's C3 grid is still the 6-point grid (`strategy_lab_page.py:42`). The composite is the mean of
  nine sign votes, and the rule goes long when it exceeds the hysteresis (`core/quant/strategies.py:344-346`).
  - With no zero vote, the composite takes odd ninths. Then 0.05 and 0.1 are one rule, 0.2 and 0.3 one, 0.4 and 0.5 one.
    The lattice 0.0, 0.222, 0.444, 0.667, 0.889 gives five rules that contain the old three (map01 §2.3). Literal N_raw
    is 11; distinct-rule N_raw is 5. The study comment says 0.05, 0.1 and 0.2 are one rule
    (`docs/asset_expansion_study.py:328-332`). This reading disagrees for 0.2.
  - The argument assumes no zero vote. `np.sign` returns 0 on equal prices (`core/quant/strategies.py:344`). With one
    zero vote the composite takes even ninths, and 2/9 ≈ 0.222 lies between 0.2 and 0.3, so h = 0.2 and h = 0.3 then
    act differently. KRW closes are integers, so ties can occur (UNVERIFIED for the cached series, which this design
    does not open).
  - So T-RUNREG-05 settles only the tie-free case, on the canonical panel. It also shows the tie case on a panel with
    tied closes. On real data, semantic duplicates stand only with equal real-data fingerprints (row 6).
- **A Lab E1 run, repeated the next day.** SPY, QQQ, TLT and GLD at the table cost.
  - Monday: 12 SEARCH, or 12 ADOPTED if the ledger already held them. N_raw rises by 12 in the first case. In the second
    it does not change: the rows were already in the LEDGER_ONLY term.
  - Tuesday: one more session, so `data_md5` differs under the same request: 12 REMEASURE. TOTAL 2; N_raw 12.
- **The same symbols with `days` lowered from 5,000 to 3,000** after a displayed REJECT. 12 DATA_CHOICE keys. Primary
  N_raw 24; distinct-data N_raw 12.
- **`days` raised from 3,000 to 5,000** after a displayed INSUFFICIENT_DATA with target "extend history". 12 REMEASURE.
  N_raw unchanged.
- **The same symbols at 5 bp per side**, below the 50 bp table rate. The run makes 12 new `config_id`s: SEARCH with
  COST_SENSITIVITY; the verdict is withheld. Primary N_raw 24; secondary 12.
- **A NumPy upgrade, then the same run.** Code identity unchanged, environment changed: 12 ENV_CHANGE. N_raw unchanged.
- **A Yahoo fetch fails.** FAILED_BEFORE_STATS. TOTAL +1; nothing else.
- **A symbol with no cost row and no typed cost.** FAILED_BEFORE_STATS at stage REQUESTED. TOTAL +1.
- **`score_strategy` raises after the walk-forward.** FAILED_AFTER_STATS. The ledger already holds G new rows
  (`strategy_lab_page.py:117-118`), and the registry counts the same keys once.

---

## 5. Data model

### 5.1 Location and files

The registry lives in `config.macro_dir() / "runs"`, the sibling of the Lab's ledger directory `macro_dir()/ledgers`
(`strategy_lab_page.py:67`; `config.py:176-178`).

| Path | Content |
|---|---|
| `runs/run_registry.jsonl` | the event log, segment 0 (5.2, 5.3) |
| `runs/run_registry.<n>.jsonl` | later segments (5.2) |
| `runs/run_registry.lock` | the OS lock sidecar |
| `runs/series/<sha256>.npy` | P&L matrices (5.7) |
| `runs/unrecorded.jsonl` | outage records, outside the chain (5.2) |
| `runs/reports/` | default output of the ⑨-3b report (section 7) |

The canonical panel is not here. It is a repository fixture, `data/r3/canonical_panel_v1.npy`, so that every machine
fingerprints the same bytes (5.4).

Why `macro_dir()`:
- `config.py:174-175` places mutable state under `macro_dir()` and keeps it out of the repository.
- The Lab's ledgers already live there (`strategy_lab_page.py:67`).
- T-HERM-02 snapshots `~/.nextgen/macro` and `QUANTGEN_MACRO_DIR` (`tests/macro_acceptance.py:113-138`). A test that
  writes the default path is therefore detected after the fact. Detection is not prevention: prevention is the
  directory injection and the temporary macro directory of 9.3 (ENG-01).
- The Lab already writes ledger rows under `~/.nextgen/macro` (`strategy_lab_page.py:67`). So using the Lab during a full
  suite run already trips T-HERM-02, and the registry adds files at the same root. Rule: do not use the Lab while the
  full suite runs (ENG-15 (e); 9.8).

Sync folders (ENG-15 (d)). The OS byte lock does not work across machines. Two machines that share a runs directory
through a sync client would fork the chain through conflict copies. So the recorder refuses a runs directory whose
resolved path lies under a OneDrive root (the `OneDrive`, `OneDriveConsumer` and `OneDriveCommercial` environment
variables), unless `QUANTGEN_R3_ALLOW_SYNC=1` is set (Q13). A refusal disables the recorder for the run (6.7). The
default `~/.nextgen/macro` is outside the owner's OneDrive repository folder
(`research_notes/QUANTGEN v2 integration map/code_tests_data.md:684`).

Alternatives refused:
- **Inside the ledger.** Unknown fields are refused (`gate_ledger.py:190-192`). Dedup drops re-runs (`:343-346`). The
  file is frozen (map02 §8).
- **A run ID inside `params`.** It changes `config_id`, so every configuration would be counted again (map02 §8).
- **A shadow family ledger written ledger-first.** It would duplicate the production ledger without the paper_live and
  CRY-1 rows. Two E1 ledgers invite a wrong read. The registry's events carry the same keys.
- **The repository**, as the Nautilus bridge does (`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:1093`).
  Lab runs are frequent operator state, not reviewed research outputs.

The core module never imports `config`; the directories are injected, as in `gate_ledger.py:26`. The page passes
`QC.macro_dir() / "runs"` and `QC.macro_dir() / "ledgers"`.

### 5.2 Line format, chain, lock, segments and outages

Lines and chain:
- One event per line, in canonical JSON: sorted keys, no whitespace, UTF-8, NaN refused
  (`core/ficc/macro_schema.py:303-305`). LF, binary append, flush and fsync, as the ledger does (`gate_ledger.py:350-354`).
- Non-finite floats, such as `bench_p` without a benchmark, are written as `null` and listed in the event's
  `nonfinite` field.
- `row_md5` is the MD5 of the canonical JSON without the chain fields. `prev_row_md5` is the MD5 of the previous line's
  bytes, `null` for the first line of segment 0. These mirror `gate_ledger.py:217-218`, `:348-349`.
- `verify_chain` re-hashes every line. A reformat, an edit, a dropped line or a moved line breaks the chain. Reads and
  appends refuse a broken chain (fail closed, as `gate_ledger.py:284-316`). The module never repairs a chain.
- Every event carries `schema = "qg-run-registry/1"`. Unknown event types and unknown top-level fields are refused at
  write.
- The store refuses a second STARTED and a second FINISHED for one `run_id`, under the lock (ENG-07 (b)).
- The module has no wall clock. `recorded_utc` comes from an injected clock; the page injects
  `datetime.now(timezone.utc)`.

Lock:
- A lock serialises read-verify-append: a process lock plus an OS byte lock on the sidecar, the pattern of
  `gate_ledger.py:242-262`. The new module implements it; `cards.chain_append` has no lock (`core/quant/cards.py:526-539`).
- Lock waits are bounded. Inside `run_family` a hook tries for at most 2 seconds; after the display, for at most
  10 seconds. A timeout disables the recorder for the run (6.4, 6.7).

Verified-prefix cache (ENG-22). The process keeps (segment, byte offset, MD5 of the last verified line). A later read
verifies only the new tail. A file shorter than the cached offset, or a different last-line MD5, forces a full
verification. A new process verifies fully once.

Segments:
- **Rollover.** When a segment exceeds 32 MB, the next append opens `run_registry.<n+1>.jsonl`. Its first event is
  SEGMENT_START with the previous segment's name, byte length, MD5 and last-line MD5. Its `prev_row_md5` is that
  last-line MD5, so the chain continues across files.
- **Recovery after a torn or broken tail** (ENG-07 (c)). A power loss during an append can leave half a line. The module
  then refuses, as above. `tools/r3/registry_segment.py`, run by the owner with an owner ruling, starts a new segment.
  Its SEGMENT_START records the old file's byte length and MD5, the number and MD5 of its last verified line, and the
  reason. The old file is never touched. Readers fold the old segment up to its last verified line and report the
  ignored tail. T-RUNREG-02 pins this with a half-written line in a temporary file.

Outage file (ENG-16). `runs/unrecorded.jsonl` is outside the chain. On any registry failure the recorder appends one
JSON line: the time from the injected clock, the family, the typed symbols, the stage, and the error type and message.
It appends with flush and fsync, under the process lock only. Counts never read it. The report reads it (7.2 G). If
that write also fails, the page shows its notice in the error colour (6.7).

### 5.3 Event types

| Event | Written when, by whom | Content |
|---|---|---|
| STARTED | at the entry of `run_family`, by the recorder | identity, request, strategy version, environment, grid, planned keys |
| PROGRESS | (1) after `pnl_matrix` returns, inside `run_family`, by the recorder; (2) after `run_family` returns or raises, by the page | (1) stage PNL_COMPUTED, data, cost, registered keys; (2) stage DISPLAYED or the failure stage, ledger link, results, existing verdict, series reference |
| FINGERPRINT | after the display, by the page, for (configuration, code identity) pairs not yet fingerprinted | behaviour fingerprints with their cache keys |
| SHADOW | after FINGERPRINT, by the page | counts, classes at write time, shadow rows, diagnostics, error |
| FINISHED | once per run, by the page, in a `finally` block | status, stage reached, error, displayed, duration, class summary |
| SUPERSEDED, DECLARATION, ANNOTATION, BACKFILL | by a person, through `tools/r3/annotate.py` | 5.4 "Human events" |
| SEGMENT_START | at rollover, or by the owner-approved recovery command | 5.2 |

The record of a run is the fold of its events. No event is ever edited.

Why the in-run events are small (ENG-07 (a), Q-02). Inside `run_family` the recorder writes only STARTED and the first
PROGRESS. Both are small, and their lock waits are bounded. The series file, the ledger reads, the fingerprints and the
counts all come after the existing verdict is displayed. So a crash inside `run_family` leaves its stage on record
(PNL_COMPUTED or not). A crash after the display loses at most the results block, and the fold counts that run fail
closed (5.6). The worker wraps everything after `run_family` in `try/finally`, so FINISHED is always attempted.

### 5.4 Record schema

"Req." means required in that event. Types: `str`, `int`, `float`, `bool`, ISO date `YYYY-MM-DD`, ISO instant
`YYYY-MM-DDTHH:MM:SS.ffffffZ`, lists and objects as stated.

**Identity (every event)**

| Field | Type | Req. | Note |
|---|---|---|---|
| `schema` | str | yes | `"qg-run-registry/1"` |
| `event` | enum | yes | 5.3 |
| `run_id` | str | yes, except DECLARATION, BACKFILL and SEGMENT_START | 5.5 |
| `recorded_utc` | ISO instant | yes | injected clock |
| `writer` | str | yes | `"ui/strategy_lab_page.py"` for run events; `"tools/r3/annotate.py"` or `"tools/r3/registry_segment.py"` for person events |
| `person` | str or null | yes for person events | who wrote it |
| `parent_run_id` | str or null | no | set when the operator re-runs from an earlier run's panel (future UI). Classification never relies on it |
| `row_md5`, `prev_row_md5` | str | yes | 5.2 |
| `nonfinite` | list of str | no | 5.2 |

**Request (STARTED)**

| Field | Type | Req. | Source |
|---|---|---|---|
| `family` | str | yes | Lab key (`strategy_lab_page.py:34-46`) |
| `family_id` | str | yes | `FAMILY_ID` (`strategy_lab_page.py:50-51`) |
| `symbols_typed` | list of str | yes | the page's text field |
| `source_requested` | str | yes | `auto`, `yfinance`, `kis`, `fmp`, `crypto` or `synthetic` (`strategy_lab_page.py:219-220`) |
| `cost_bps_requested` | float or null | yes | null means the table rate |
| `days` | int | yes | `strategy_lab_page.py:86`, `:223` |
| `bootstrap_B` | int | yes | 1000 in the Lab (`strategy_lab_page.py:86`) |
| `seed` | int | yes | 11 (`validate.py:493`) |
| `intent` | enum | yes | `exploratory` or `confirmatory` |
| `declaration_id` | str or null | yes | row 7 |
| `planned` | list of `{theta_index, config_id}` or null | yes | built from the typed symbols with the pure key builder (9.2); null when the cost cannot be resolved |

**Strategy version (STARTED)**

| Field | Type | Req. | Note |
|---|---|---|---|
| `fn_qualname` | str | yes | 3.3 |
| `fn_source_sha256`, `fn_source_sha256_raw` | str | yes | 3.3 |
| `repo_anchor` | str | yes | `gate_ledger.repo_anchor()`; may be UNVERSIONED (3.3) |
| `files` | object path → `{lf, raw}` | yes | `core/quant/strategies.py`, `core/quant/validate.py`, `core/quant/history.py`, `core/quant/gate_ledger.py`, `ui/strategy_lab_page.py` (Q12) |
| `gate_version` | str | yes | 3.16 |
| `canonical_panel` | `{path, sha256}` | yes | the fixture below |

**Environment (STARTED)**

| Field | Type | Req. | Note |
|---|---|---|---|
| `env` | `{python, numpy, scipy, pandas, system, machine}` | yes | 3.17 |

**Grid (STARTED)**

| Field | Type | Req. | Note |
|---|---|---|---|
| `grid` | list of objects | yes | θ per grid point, canonical |
| `grid_sha256` | str | yes | |

The canonical panel. `tools/r3/make_canonical_panel.py` generates it once from a fixed seed. It is committed as
`data/r3/canonical_panel_v1.npy` (float64, C order, about 48 KB), and its SHA-256 is a constant in
`core/quant/run_registry.py`. The module loads it with `allow_pickle=False` and refuses a hash mismatch. Then no
fingerprint is computed, a code-identity change starts a new lineage with flag FINGERPRINT_UNAVAILABLE, and the key is
counted (default to count). Shape: 1,500 business days from 2000-01-03, four columns. Columns 0 and 1 are a
cointegrated pair: column 1 follows column 0 through an Ornstein–Uhlenbeck spread, so that the pairs rule trades.
Columns 2 and 3 are random walks with 1.5 % daily volatility and drift segments of ±0.1 % per day that switch every
250 days, so that trend rules trade. `crypto_trend` uses column 0, `pairs` columns 0 and 1, the others all four. The
panel has no tied closes; T-RUNREG-05 uses a separate tied-close test panel (4.5).

**PROGRESS at PNL_COMPUTED (inside `run_family`)**

| Field | Type | Note |
|---|---|---|
| `stage` | `"PNL_COMPUTED"` | |
| `symbols_resolved` | list of str | `h.symbol` (`strategy_lab_page.py:118`) |
| `per_symbol` | list of `{symbol, source, note, adjustment, status, first, last, sessions, close_md5}` | from `History` (`core/quant/history.py:55-68`) |
| `span` | [ISO date, ISO date] | first and last date of the aligned panel |
| `sessions` | int | |
| `data_md5` | str | MD5 of: the dates joined by "\n", a zero byte, the symbols joined by "\n", a zero byte, the closes as little-endian float64 in C order |
| `synthetic` | bool | any source SYNTHETIC |
| `holdout_touched` | bool | span end on or after 2027-01-01 (4.2 row 16) |
| `cost` | object | the cost block below |
| `registered` | list of `{theta_index, config_id}` | the pure key builder on the resolved symbols and the resolved cost; equal by construction to the rows `register_trials` writes (T-RUNREG-01b) |
| `keys_changed_by_symbol_resolution` | bool | `planned` differs from `registered` (map01 §3.4) |

**Cost (inside PROGRESS at PNL_COMPUTED)**

| Field | Type | Note |
|---|---|---|
| `cost_bps` | float | the rate applied |
| `floor_bp` | float or null | `V.cost_floor_bp` (`validate.py:115-121`) |
| `classes` | object symbol → class or null | same call |
| `basis` | enum | `table`, `typed_at_or_above_table`, `sensitivity_below_table` or `no_cost_row` |
| `withheld` | bool | `strategy_lab_page.py:98-103` |
| `stress_multiplier` | float | 2.0 (`strategies.py:380`; `GATE["cost_stress"]`, `validate.py:57`) |
| `cash_daily` | float | 0.03 / 252 (`strategy_lab_page.py:113`) |

**PROGRESS after `run_family` (by the page): ledger link**

| Field | Type | Note |
|---|---|---|
| `family_id`, `ledger_file` | str | file relative to `macro_dir()` |
| `ledger_stage` | str | `"after_walk_forward"` (5.8) |
| `bytes_before`, `bytes_after` | int | the ledger file's size just before and just after `register_trials` at `:118`, read inside `run_family` with one `stat` each (0 when absent) |
| `rows_before`, `rows_after` | int | complete lines in those byte prefixes |
| `hash_before`, `hash_after` | str | `gate_ledger.ledger_hash` of those row prefixes, read after the display through `FamilyLedger.rows()` |
| `market` | str | `strategy_lab_page.py:71-72` |
| `rows` | list of `{theta_index, config_id, row_md5, appended}` | `row_md5` is the stored content hash of the row with that `config_id` (`gate_ledger.py:346`, `:349`); `appended` is true when the `config_id` is absent from the `rows_before` prefix |
| `interleaved` | bool | true when the rows between the two prefixes are not exactly this run's appended keys: another writer appended in between |
| `skipped` | null, `"synthetic"` or `"not reached"` | `register_trials` returns None for synthetic runs (`strategy_lab_page.py:60-61`) |

How the link works without touching `register_trials` (ENG-02, Q-05). The ledger is append-only and its chain is
verified on every read. So the prefix of the file up to `bytes_before` is the ledger as it was before this run's
registration. Inside `run_family` the recorder reads only two file sizes. After the display it reads the verified rows
once and takes the two prefixes. A partial last line inside a prefix (another writer mid-append) is excluded by
cutting at the last newline. Classes never come from a hash difference. An interleaving can mislabel ADOPTED as
SEARCH. It cannot change N_raw, which is a set cardinality (3.13).

**PROGRESS after `run_family` (by the page): results**

| Field | Type | Note |
|---|---|---|
| `stats` | object | every scalar field of `StrategyScore` (`validate.py:456-489`), the filter of `strategy_lab_page.py:154`, plus `regime`, `ci90` and `bench_ci`; null below SCORED |
| `sr_sd_daily` | float | computed as `validate.py:505-506` |
| `oos_moments` | `{T_oos, T_full, sr_daily, g3, g4}` | computed as `validate.py:229-232`; these are the inputs the cards lack (map01 §5) |
| `per_config` | list of `{theta_index, config_id, full_sr_daily, result_fingerprint}` | from PNL_COMPUTED on; the fingerprint is SHA-256 of the real-data P&L column rounded to 1e-12 |
| `chosen_last` | object | `strategy_lab_page.py:135` |
| `wf_note` | str | `wf.note` |
| `results_sha256` | str | SHA-256 of the canonical `stats` |
| `series_ref` or `series_error` | `{sha256, shape, columns}` or `{type, message}` | 5.7; `columns` lists the `config_id`s in grid order |

**PROGRESS after `run_family` (by the page): existing verdict**

| Field | Type | Note |
|---|---|---|
| `existing` | `{decision, reason, revise_target, n_trials, withheld, displayed_as}` | `n_trials` = `len(grid)`; `displayed_as` is the decision or `"WITHHELD"` (`strategy_lab_page.py:150-153`, `:249-251`) |
| `displayed` | bool | the page rendered the existing verdict |

**FINGERPRINT**

| Field | Type | Note |
|---|---|---|
| `fingerprints` | list of `{theta_index, config_id, code_identity, behaviour_sha256}` | only pairs not yet in the fold's cache |
| `cache_key` | object | (`fn_qualname`, code identity, θ, `cost_bps`, `cash_daily`, panel SHA-256, `env`) per entry |

**SHADOW**

| Field | Type | Note |
|---|---|---|
| `counts` | object | 6.2 |
| `classes` | list of `{theta_index, class, flags, reason}` | 4.3 at write time |
| `rows` | list | 6.3; each with n, dispersion term, DSR, decision, reason, revise target, changed predicates, ΔDSR and its baseline |
| `diagnostics` | object | 6.5 |
| `error` | null or `{type, message}` | a failure of the shadow computation |
| `classifier_version` | str | |

**FINISHED**

| Field | Type | Note |
|---|---|---|
| `status` | enum | 5.6 |
| `stage_reached` | enum | 5.6 |
| `error` | `{type, message}` or null | message cut at 500 characters |
| `displayed` | bool | |
| `duration_s` | float | from the injected clock |
| `class_summary` | object class → count | |
| `recorder_errors` | list of `{hook, type, message}` | contained hook failures (6.4) |

**Human events (SUPERSEDED, DECLARATION, ANNOTATION, BACKFILL)**

| Field | Type | Req. | Note |
|---|---|---|---|
| `owner_ruling` | `{log_path, lines, channel, date, quote_md5}` or null | yes | cites a verbatim entry of `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`. The report checks that the cited lines exist and that their text hashes to `quote_md5`. Without a valid ruling, the event changes only the secondary reading |
| `superseded_run_id`, `superseded_by`, `rule` | str | SUPERSEDED | for example rule R-5c |
| `declaration_id`, `family_id`, `config_ids`, `fn_source_sha256`, `pass_rule`, `span`, `anchor` | as named | DECLARATION | row 7 |
| `run_id`, `theta_index`, `claim`, `test_ref`, `why` | as named | ANNOTATION | row 8c |
| `family_id`, `params`, `provenance`, `why` | as named | BACKFILL | row 14 |

### 5.5 Run ID format

- `LAB-YYYYMMDDTHHMMSSZ-<family_id>-<8 hex>`.
- Regex: `^LAB-[0-9]{8}T[0-9]{6}Z-[A-Z0-9][A-Z0-9-]{0,31}-[0-9a-f]{8}$`. It uses `[0-9]` because Python's `\d` matches
  every Unicode digit (ENG-25).
- The 8 hex digits come from `secrets.token_hex(4)`; tests inject the token source.
- The append refuses a `run_id` that already has a STARTED event; the check runs under the lock. The recorder then
  draws a new token and retries, at most five times. After that it disables itself for the run and writes an outage
  record.
- `LAB` names the writer. `STUDY` and `BRIDGE` are reserved for later writers (Q18).

### 5.6 Status enum and stages

Statuses: STARTED, COMPLETED, FAILED_BEFORE_STATS, FAILED_AFTER_STATS, ABORTED, SUPERSEDED.

Stages, in order: REQUESTED, COST_RESOLVED, DATA_LOADED, PNL_COMPUTED, WALK_FORWARD_DONE, LEDGER_REGISTERED, SCORED,
DISPLAYED.

| Status | Meaning |
|---|---|
| STARTED | the STARTED event exists and no FINISHED event yet |
| COMPLETED | `run_family` returned and the page rendered the existing verdict. A shadow error does not change this; it is stored in SHADOW `error` |
| FAILED_BEFORE_STATS | an exception left the run below PNL_COMPUTED |
| FAILED_AFTER_STATS | an exception left the run at PNL_COMPUTED or later |
| ABORTED | written by a future cancel control; or inferred in the fold for a STARTED event with no FINISHED event, recorded more than 6 hours before `as_of`. Its stage is that of its last PROGRESS event. With no PROGRESS event and no outage record for it, the run never reached PNL_COMPUTED: it counts as FAILED_BEFORE_STATS with flag STAGE_INFERRED. Otherwise, when the stage is unknown, it counts as FAILED_AFTER_STATS with its planned keys and flag STAGE_UNKNOWN (fail closed, map03 R-2b). Younger orphans are OPEN: left out of counts, with a warning |
| SUPERSEDED | only through a SUPERSEDED event. The earlier terminal status is kept as `status_before_supersede` |

Transitions: STARTED → one of COMPLETED, FAILED_BEFORE_STATS, FAILED_AFTER_STATS or ABORTED. Any terminal status →
SUPERSEDED.

### 5.7 Series store

- The stored array is the T×G matrix `M` the gate sees as `full_pnl` (`strategy_lab_page.py:114`, `:127`). Column 0 holds
  the day number (days since 1970-01-01). Columns 1 to G follow the grid order. Type float64, C order, written with
  `numpy.save`; read with `allow_pickle=False`. Counts read each column as a pandas Series indexed by the day number
  (3.14).
- The file name is the SHA-256 of the array's dtype, shape and raw bytes, not of the file. A later compressed format
  can keep the names. The reader re-hashes the array.
- Writing (ENG-15 (a)). The writer uses `mkstemp` in the same directory, fsync, then `os.replace`. It retries up to
  10 times over 5 seconds on `PermissionError`, because OneDrive, Defender and the indexer open new files. This is the
  Nautilus bridge's rule (`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:794-797`). It skips a name that
  exists. After the last failure it records `series_error` and keeps the run.
- When. The matrix is captured as a read-only view at PNL_COMPUTED and written after the display, or in the page's
  failure path. So a run that fails after PNL_COMPUTED keeps its series, and the write never delays the verdict.
- Size: about 8 · T · (G + 1) bytes, so 5,000 sessions and 12 configurations take about 0.5 MB per run. Identical re-runs
  share one file. Retention is open (Q14).

### 5.8 Registration order

| | Today (unchanged in ⑨-3a) | Registry, shadow path (⑨-3a) | Ledger-first, after an owner ruling (not in this stage) |
|---|---|---|---|
| First write | ledger rows after the walk-forward, before scoring (`strategy_lab_page.py:116-118`) | STARTED at the entry of `run_family`, before `:90` | ledger rows right after `align_panel` (`:105`), before `pnl_matrix` (`:114`) |
| Argument error (`:90-96`) | nothing recorded | FAILED_BEFORE_STATS, stage REQUESTED | nothing in the ledger |
| Failure while loading or aligning (`:104-108`) | nothing recorded | FAILED_BEFORE_STATS | nothing in the ledger |
| Failure inside `pnl_matrix` (`:114`) | nothing recorded | FAILED_BEFORE_STATS, stage DATA_LOADED | G rows |
| Failure after `pnl_matrix` returned, before registration (the walk-forward, `:116`) | nothing recorded | FAILED_AFTER_STATS; keys counted | G rows |
| Failure in registration or scoring | G rows if registration succeeded | FAILED_AFTER_STATS | G rows |

- The ledger row cannot come before the load. `span` is a required ledger field (`gate_ledger.py:63`, `:174-179`), and
  the resolved symbols come from the loaded histories (`strategy_lab_page.py:118`). Both exist only after the load. So
  "before any computation" means before the first computation on prices.
- In ⑨-3a the registry is the record that is written before any computation. The ledger write stays where it is. So the
  Lab chip, the ledger hash and the tests that pin them are unchanged.
- The PROGRESS ledger link records `ledger_stage = "after_walk_forward"`. A later switch to the third column is therefore
  visible in every record.

### 5.9 What the registry never does

- It never calls `append`, `register_trial` or `TrialRegistry.register` (map02 §10). Its ledger reads are
  `FamilyLedger.rows()` and file sizes, which write nothing and create no lock file (map02 §0 item 8, §5).
- It never modifies `register_trials` and never assigns to `GATE` or to any module state of `validate`.
- It never writes a card, `results.csv`, `results.md`, `manifest.json` or anything under `docs/asset_expansion/`.
- It never puts a run ID, a clock value or a token into a result hash.
- It never stores prices; it stores hashes and P&L series.

### 5.10 Size and verification cost

Estimates for G = 12, to be measured in ⑨-3a (UNVERIFIED until built):
- STARTED: 3 to 5 KB (grid, planned keys, file digests, environment).
- PROGRESS at PNL_COMPUTED: 2 to 3 KB. PROGRESS after the display: 4 to 7 KB. FINGERPRINT: up to 2 KB. SHADOW: 3 to 5 KB.
  FINISHED: 1 KB.
- So about 15 to 25 KB of events per run, plus about 0.5 MB of series. A 32 MB segment holds about 1,500 runs.
- A new process reads and verifies every segment once, because the counts fold every event. After that, with the
  verified-prefix cache, an append verifies only the tail (5.2).

---

## 6. Parallel (shadow) computation

### 6.1 Invariants

These hold for every Lab run. T-RUNREG-01, -01b and -06 pin them (9.3).
1. The existing verdict call is unchanged (`strategy_lab_page.py:124-129`).
2. `run_family`'s return value, `payload(r)` and `narrative(r)` are equal with and without a recorder
   (`strategy_lab_page.py:132-155`). Equality is NaN-aware: two NaN values are equal, element by element in tuples
   (`bench_p`, `bench_diff` and `bench_ci` are NaN for pairs; `validate.py:482-484`, `:521`). This also holds when every
   hook raises and when every hook sleeps.
3. On every failure path the same exception object propagates, so its type and message are unchanged.
4. Ledger rows written with and without a recorder, into two separate temporary ledgers, are equal except `run_utc`,
   `row_md5` and `prev_row_md5`. The last two follow from `run_utc`, which is the wall clock as today
   (`strategy_lab_page.py:79`).
5. `register_trials`'s source is byte-identical to `527cdf2` (T-RUNREG-01b).
6. No new code assigns to `GATE` or to any module state of `validate`. The shadow reads `GATE` only through
   `_decide_strategy` (T-RUNREG-06 compares `GATE` before and after; T-RUNREG-09 scans the new modules for assignments).
7. No shadow number reaches the AI panel (`strategy_lab_page.py:275-276`), a card, a results file or anything under
   `docs/asset_expansion/`.
8. Hooks receive read-only views. A hook failure is contained (6.4).

### 6.2 Counts for each Lab run

Computed after the display, from the sets of 3.13.

| Count | Definition |
|---|---|
| G | `len(grid)` |
| TOTAL family, TOTAL market | 3.12 |
| N_raw ledger, family | rows in the ledger prefix after this run's registration: the number the Lab's chip shows (`strategy_lab_page.py:82`, `:254`) |
| N_raw ledger, market | rows of that prefix with the run's market |
| N_raw registry, family and market | 3.13, literal reading, LEDGER_ONLY term included |
| N_raw distinct-rule, distinct-data | 3.13 |
| N_eff family, market | 3.14, with coverage and common-window length; or "unavailable: <reason>" |
| N_eff grid | 3.14 over this run's grid |
| N_validation family | 3.15 |

`gate_ledger.emax_sim` draws 200,000 rows in chunks of 50,000 (`gate_ledger.py:486-502`), so its memory grows with the
number of trials K. The page computes N_eff only for K ≤ 200. Above that, the report tool computes it (section 7).

### 6.3 Shadow rows

**Block 1: trial history (R3).** A difference from the row's baseline is labelled COUNT (7.2 E).

| Id | n | Dispersion term | Baseline | Label printed with the row |
|---|---|---|---|---|
| EXISTING | G | current grid (`validate.py:505-506`) | — | today's verdict; recorded, not recomputed |
| L-FAM | N_raw, ledger, family-wide | current grid | EXISTING | "assumes the family's cross-trial Sharpe dispersion equals this grid's" |
| L-MKT | N_raw, ledger, market-scoped | current grid | EXISTING | same |
| R-FAM | N_raw, registry, literal, family-wide | current grid | EXISTING | same |
| R-MKT | N_raw, registry, literal, market-scoped | current grid | EXISTING | same |
| R-RULE | N_raw, registry, distinct-rule, family-wide | current grid | EXISTING | same |
| E-FAM | N_eff, family-wide (real) | SE_null(T_oos) | E-GRID | "matched pairing (map03 R-3d)" |
| E-MKT | N_eff, market-scoped (real) | SE_null(T_oos) | E-GRID | same |

**Dispersion sensitivity.** L-FAM and R-FAM are also printed with the dispersion term × 1.5 and × 2, as the k column
does for cards (7.3). These are sensitivity rows, not decision rows.

**Block 2: criterion change at today's trials — not trial history.** A difference here is labelled PAIRING (7.2 E). It
answers a ⑨-3c question, not the R3 comparison.

| Id | n | Dispersion term | Compared with | Label printed with the row |
|---|---|---|---|---|
| E-GRID | N_eff(grid) (real) | SE_null(T_oos) | EXISTING | "pairing change at today's grid" |
| G-SE | G | SE_null(T_oos) | EXISTING | "pairing change at today's count (candidate C5 at n = G)" |
| E-GRID-MIX | ⌈N_eff(grid)⌉ | current grid | EXISTING | "mismatched pairing, anti-conservative (map03 R-3d, §4.3 column b); disclosure only" |

Each row shows: n, DSR, the decision it would give, reason, revise target, the predicates that changed against its
baseline, and ΔDSR against its baseline.
- When G = 1, the grid dispersion is 0 (`validate.py:506`). Every grid-dispersion row then prints "n-invariant (one
  configuration)". The SE_null rows still depend on n.
- When N_eff is unavailable, the E rows print the reason, the coverage and the common-window length (3.14).

Why two blocks (Q-07). The gate's pairing uses one grid's dispersion. map03 R-3d allows (N_raw, raw dispersion) and
(N_eff, null SE), and forbids (N_eff, raw dispersion). The L and R rows pair a family-wide N with one grid's dispersion;
the label says so. The E rows use the matched pairing. Their baseline is E-GRID, the same pairing at today's grid, so a
difference between E-FAM and E-GRID comes from trial history alone. The pairing change itself shows up as E-GRID or
G-SE against EXISTING. This revision's probe shows that it is large: at today's count the null-SE pairing alone changes
one stored card's decision and two cards' reasons (7.3). Without the split, that criterion effect would be read as
trial history.

### 6.4 Method

**Replay, not re-scoring** (Q-01, ENG-05). For each row:
1. Compute the row's DSR.
   - Grid-dispersion rows: `dsr = V.deflated_sharpe(wf.pnl, n_trials=max(n, 1), sr_sd_daily=c · sd)`. Here `sd` is
     computed exactly as `validate.py:505-506` (with `V._col_sharpe` and `V.TRADING_DAYS`), and c is 1, 1.5 or 2.
   - SE_null rows: `dsr = gate_stats.psr(sr, T_oos, units="daily", sr0=SE_null(T_oos) · gate_ledger.emax_iid(N),
     skew=g3, kurt=g4)` (`core/quant/gate_stats.py:590-607`; `gate_ledger.py:519-527`). `sr`, `g3` and `g4` are computed
     from `wf.pnl` exactly as `validate.py:229-232`.
2. Copy the existing score: `s = dataclasses.replace(existing, dsr=dsr, n_trials=n_int, lines=[])`, where `n_int` is
   the integer n shown in the line text.
3. Call `V._decide_strategy(s)` (`validate.py:536-622`). It reads `GATE` and writes only the copy.

No `GATE` write, no bootstrap and no CSCV are involved. The cost is milliseconds.

**Exactness.** `n_trials` enters `score_strategy` only at `validate.py:507` (through the DSR) and in the stored field
(`:529`). `_decide_strategy` rebuilds `lines` (`:537-574`). So the replay equals a fresh `score_strategy` call with
that n on every field. This revision checked it on synthetic panels: 12 of 12 cases equal on every field
(`scratch:r3_rev2_probe/replay_lab.py`). T-RUNREG-06 keeps the fresh-call comparison, inside the test process only.

**Integer n.** Grid-dispersion rows need an integer n. A real N_eff is rounded up for E-GRID-MIX; the gate truncates
(`validate.py:213`), so N_eff = 1.45 passed as is would set the hurdle to 0 (map03 §4.5). When ⌊N_eff⌋ and ⌈N_eff⌉
give different predicates, the row says so. SE_null rows take the real N, because `emax_iid` accepts a real N
(`gate_ledger.py:519-527`). The rounding rule for a future criterion is Q3, decided at ⑨-3d.

**Predicates.** A helper computes `ci_ok` (`ci90[0] > 0`), `dsr_ok`, `pbo_ok`, `pbo_reject`, `stress_reject`,
`bench_fail`, the five engineering checks and the minimum-track-record branch, as `validate.py:576-611` does (Q-19).
The helper only explains which predicates changed. The decision always comes from `_decide_strategy`. T-RUNREG-06 pins
the helper against `_decide_strategy`, including a case where `dsr_ok` turns true while `ci_ok` is false.

**Containment and latency** (Q-02, ENG-04).
- Inside `run_family` the hooks do only in-memory work, two `stat` calls on the ledger file and two bounded registry
  appends (STARTED and the first PROGRESS; 5.3).
- Every hook call goes through one guard. The guard catches `Exception`, records the hook name and the error, disables
  the recorder for the rest of the run, and returns. `run_family`'s control flow never depends on the recorder.
- On an exception in `run_family`, the guard calls the recorder's `failed()` in a nested `try`. Then the original
  exception object is re-raised unchanged.
- Hooks receive read-only views of arrays (`v = a.view(); v.flags.writeable = False`). The walk-forward result is passed
  as is; the recorder copies what it keeps.
- Fingerprints, the series write, the ledger reads, the counts and the shadow run after the existing verdict is
  displayed. The extra time before the verdict is two file sizes and two appends, each bounded by a 2-second lock wait.
  It is printed in FINISHED (`duration_s`) and not asserted, because it is UNVERIFIED on the owner's machine.

**Withheld runs** (cost below the table rate). Counts are computed and recorded. No shadow decision is computed: the
existing decision is withheld (`strategy_lab_page.py:150-153`), so there is nothing to compare.

**Synthetic runs.** No ledger counts exist (no rows). The block reads "synthetic: not counted".

### 6.5 Diagnostics (printed, never a decision)

- **SE_null with T_full.** The E-FAM, E-MKT, E-GRID and G-SE DSR values recomputed with SE_null(T_full) (3.19). Printed
  beside the T_oos values.
- **DSR at a real N with the grid dispersion.** `gate_stats.psr(sr, T, units="daily", sr0=sd · gate_ledger.emax_iid(N),
  skew=g3, kurt=g4)` for N = N_eff family and N_eff grid. It avoids the integer truncation. It is labelled "mismatched
  pairing (map03 R-3d)".
- The moments are the ones stored in the record (5.4 "Results").
- A consistency test checks that the grid-dispersion diagnostic at an integer N equals `validate.deflated_sharpe` at
  that N within 1e-12 (T-RUNREG-06).

### 6.6 Stored cards: no recomputation of returns

- **Existing verdict.** The stored `decision`, `decision_reason` and `revise_target`.
- **Replay check.** Rebuild `V.StrategyScore` from the card's stored `stats` (every field is present). Call the unchanged
  `V._decide_strategy` (`validate.py:536-622`; `score_strategy` calls it at `:532`). Compare. Revision 1's probe
  (`scratch:r3_spec_probe/replay.py`): **16 of 16 DSR cards reproduce decision, reason and revise target exactly.** The
  printed lines differ in wording ("(15 years)" against today's "(N full years)", map01 §2.2). The wording does not enter
  a decision. A card that fails the replay is reported as gate drift and gets no shadow decision.
- **Shadow DSR, today's pairing.** From the stored SR, T and DSR, back out the dispersion under each moment scenario of
  map01 §5: (g3, g4) ∈ {(0, 3), (0, 10), (−1, 10), (+1, 10), (0, 30)}. Then
  `DSR_m(n) = Φ((SR − sd_m · e(n)) · √(T − 1) / √denom_m)`, with `e(n) = validate.expected_max_sharpe(n, 1)`. A
  scenario that implies sd < 0 is dropped (map01 §5). `expected_max_sharpe` returns `inf` for n ≥ 1e16, because
  1 − 1/n rounds to 1 (Q-18). So flips are searched only up to n = 1e6. A larger flip prints "> 1e6: no realistic n".
- **Shadow DSR, null-SE pairing.** `DSR_SE_m(n) = Φ((SR − SE_null(T) · emax_iid(n)) · √(T − 1) / √denom_m)`, with T the
  stored `n_sessions` (T_oos). It needs no dispersion, so it is exact from stored fields for each moment scenario. It
  feeds block 2 (6.3) and section F of the report.
- **Shadow decision.** Replace `dsr` and `n_trials` in the rebuilt score and call `_decide_strategy`. Over the scenarios
  this gives a set of decisions. The report prints the set.
- **Counts for a card** (Q-04, ENG-11). Three readings, each in three scopes:
  - **Pre-card (primary).** Ledger rows whose `run_utc` is earlier than the card's anchored fix time and whose `span`
    overlaps the card's data span (`data.start`, `data.end` in the card JSON), plus the grid keys of the sibling cards of
    the same Lab family. The anchored fix time of every stored card is the commit that added it to this repository:
    `eacd57d`, 2026-10-22T15:53:18Z. The cut uses an anchored instant because the ledger's own `t_fix` accepts only
    anchored instants (`gate_ledger.py:688-697`).
  - **Pre-created (secondary).** The same, cut at the card's `created` date (2026-09-27 for all 16 DSR cards). The study
    writes that date; nothing anchors it. It is the narrower reading.
  - **All-time (secondary).** Every row in the ledger snapshot of the report (revision 1's rule). A flip that appears
    only here is labelled POST_CARD (7.2 E): those rows could not have shaped the card's selection.
  - **Stored N** is printed beside them.
  - Details:
    - Ledger rows keep their first `run_utc`, because dedup keeps the first row (`gate_ledger.py:337-346`).
    - The ledger's own rule uses the time-and-span filter to decide whether f = 1, and then takes N_eff over every row
      of the reading (`gate_ledger.py:709-731`). The pre-card reading applies the filter to the count itself. The
      all-time reading is the count the ledger rule would use once triggered.
    - A row whose `run_utc_anchor` is unanchored is counted (default to count) and flagged. `selection_factor` would
      refuse it (`gate_ledger.py:713-716`).
    - Sibling cards: E8 holds four cards (S_E8_pairs_kodex_tiger, S_E8_pairs_gld_iau and the two S6 cards, 32
      configurations); E1, E2 and C3 hold two each. All carry the same `created` date. Their grid keys enter the family
      and market scopes.
  - Scopes: **universe** (rows whose `params.symbols` equal the card's symbols after the Lab's normalisation: upper
    case, sorted except for pairs, `strategy_lab_page.py:68-70`), **market** and **family**. KRX symbols may be stored
    as "069500" by a Lab run and as "069500.KS" on the card (risk 8). The universe scope lists such near-matches
    separately.
  - A card grid key is the `config_id` of a Lab-shaped row built from the card's `rules.grid`, `universe.symbols` and
    `costs.cost_bps` through the pure key builder (9.2). The Nautilus spec counts its U the same way
    (`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:113`).
  - The card family maps to the Lab's `FAMILY_ID` (`strategy_lab_page.py:50-51`). The S6 pairs cards read E8, as the Lab
    files them (map01 §3.4); a second reading "S6 alone" is printed.
  - S_V1, S_V3 and S_V4 have no Lab family. Their count is their stored N.
- **Floor.** An N_raw count never falls below the card's stored `trials.N_total` (C3: 11,
  `docs/asset_expansion_study.py:339`). That typed history is a back-fill (map03 R-8). N_eff counts have no floor.
- **N_eff for cards** cannot be computed from stored fields, because no series is stored. The report prints the
  null-SE flip N instead (7.3). Tier B can compute E-GRID exactly (7.4).

### 6.7 Where shown and how labelled

- **Lab run section.** A card below the existing blocks, titled "Shadow trial count (owner ruling R3) — not a verdict".
  - First line: "The verdict above is the gate's, with N = this run's grid. The rows below recount trials from the
    ledger and the run registry. They are not verdicts. They are not written to any card."
  - Then the counts line, block 1 with its sensitivity rows, block 2 under its own heading "Criterion change at today's
    trials — not trial history", and a run ID chip.
  - Decisions use the muted token, never the PASS or REJECT colours (`strategy_lab_page.py:32`), and read "would be
    REJECT".
- **The right run** (ENG-06). Each click increments a page-level generation counter. The worker appends the shadow card
  only if the result area still shows its own generation. Otherwise it writes its events and appends nothing.
- **Run button** (ENG-06; Q19). The button is disabled from the click until the run's work on screen ends: an error
  notice is shown, or the shadow card is appended, or 60 seconds pass after the existing verdict appears. FINISHED may
  still be pending then; it writes no screen element. Today the button is never disabled (`strategy_lab_page.py:283`).
  This is a change of availability, not of any verdict.
- **Scorecard detail (⑨-3b).** One muted line per card from the latest report CSV: "Shadow (R3, not a verdict): L-FAM
  n = …, decision would be …; report as of <as_of>; see <report path>". The reports directory is a parameter of the page
  builder, with default `QC.macro_dir() / "runs" / "reports"`. Tests patch it as they patch `CARDS_DIR`
  (`tests/macro_ui_views.py:263-283`). A missing or malformed CSV shows no line and raises nothing (ENG-25).
- **Report files** (section 7).
- **Never** in the card JSON, `results.csv`, `results.md`, the AI panel payload or narrative, or the ledger.
- **Registry failure** (ENG-16; Q16). The default is fail-open.
  - The existing verdict is still shown.
  - A muted notice reads "run registry unavailable: <reason> — this run is not recorded".
  - An outage record goes to `runs/unrecorded.jsonl` (5.2). If that write also fails, the notice uses the error colour.
  - Fail-open is an owner choice, not a requirement of R3. R3 forbids changing verdict criteria; it says nothing about
    availability. The ledger blocks the verdict on failure (`strategy_lab_page.py:117`); a fail-closed registry would do
    the same.

---

## 7. Comparison report (⑨-3b)

### 7.1 Inputs and where it runs

- Command: `python tools/r3/compare.py --cards docs/asset_expansion/cards --ledger-dir <dir> --runs-dir <dir> --out <dir>
  --as-of <ISO instant>`.
- It reads only the card JSON, the family ledgers (through `FamilyLedger.rows()`), the registry and the outage file.
  It writes only under `--out`; the default is `<runs-dir>/reports/`.
- **Cards.** It loads them through `V.load_cards` (`validate.py:847-856`), which skips unreadable files silently. So it
  also lists the directory, asserts 34 card files and 16 DSR cards, and prints any file `load_cards` skipped (ENG-25).
- **Ledger cut** (ENG-09). For an `as_of` in the past, each family ledger is cut at the prefix named by the latest
  `hash_after` recorded at or before `as_of` (`FamilyLedger.snapshot`, `gate_ledger.py:323-330`). When `as_of` is the
  report time, the whole ledger as read is used. The ledger hash is printed either way. Registry runs are never cut by
  the ledger's wall-clock `run_utc`. Only the card readings of 6.6 use `run_utc`, as `selection_factor` does
  (`gate_ledger.py:717`).
- **Of-record report.** It runs on the owner's machine, against the production ledgers read-only, because those ledgers
  are not in this container (map01 §3.3; map02 §0). The owner may copy one report into `docs/strategy_lab/r3/` for the
  record.
- **Rehearsal.** In the container it runs on an empty temporary ledger directory and the stored cards. With no ledger
  rows, every N_raw count equals the stored N, so the rehearsal shows no COUNT flips by construction. It does show the
  PAIRING rows of section F, which need no ledger.

### 7.2 Format

Two files, `r3_comparison_<as_of>.md` and `.csv`, UTF-8 with LF. The same inputs and `as_of` give the same bytes on one
platform with pinned library versions.

Header: `as_of`, repo anchor, gate version, each ledger file with its hash and `n_raw`, the registry chain head of each
segment, the outage count, the tool version.

| Section | Content |
|---|---|
| A. DSR cards | one row per stored DSR card: card ID, Lab family, G, stored N, T, SR_oos, stored DSR, existing decision and reason, replay result; the three readings of 6.6 in three scopes; per block 1 row: n, DSR range over the moment scenarios, decision set, predicate flipped, ΔDSR; the flip thresholds of 7.3; a reason in words |
| B. Other cards | the 18 cards without a DSR predicate, one line each: "no trial-dependent predicate", with the test that decides it (map01 §4.2) |
| C. Lab runs | every registry run: run ID, family, symbols, status, class summary and flags, existing decision, block 1 and block 2 decisions, differences |
| D. Counts | per family: TOTAL, N_raw in every reading of 4.4, N_eff with coverage and common window, N_validation, LEDGER_ONLY rows, writers (map02 §10), classes, flags |
| E. Attribution | every verdict difference gets one label: **COUNT** (only n changed, same pairing; for cards, under the pre-card reading), **POST_CARD** (appears only under the all-time reading), **PAIRING** (the dispersion term changed at today's n), **PAIRING+COUNT** (needs both a pairing change and more trials), **GATE** (the replay failed or the gate version differs), **DATA** (the data snapshot differs) or **ENV** (the environment differs). Only COUNT answers R3's "the verdict changes once trial history is reflected". PAIRING and PAIRING+COUNT are inputs to ⑨-3c and ⑨-3d |
| F. Criterion change at today's trials — not trial history | block 2 rows of Lab runs; the null-SE pairing of every DSR card (7.3); the S_S6_pairs_hyundai_kia case |
| G. Human events and outages | every SUPERSEDED, DECLARATION, ANNOTATION and BACKFILL event: who, why, whether its owner ruling verified, its count effect in both readings; every outage window from `runs/unrecorded.jsonl`, with the ledger's growth inside it as a lower bound on the runs missing from TOTAL |
| H. Locked holdout | every run flagged HOLDOUT_TOUCHED (4.2 row 16) |

### 7.3 Expected content: the stored DSR cards

From stored fields only, using the inventory of map01 §4.1 and §6 and this revision's probe.

**Table 1: today's pairing (grid dispersion).** Flip n holds the backed-out dispersion fixed; the main figure assumes
normal moments; brackets give the range over the moment scenarios. "k" is the factor by which the hurdle must grow to
flip, through n, the dispersion or both. The values for S_E8_pairs_kodex_tiger, S_E2_voltarget_kodex200,
S_E5_xsmom_sectors and S_S6_pairs_hyundai_kia were re-derived in revision 1 (`scratch:r3_spec_probe/flip.py`, normal
moments); the others are map01's.

| Card | Lab family | G | N | T | SR_oos | DSR | Existing decision | Flip n | k | PSR (n = 1) | DSR at 2N |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S_C3_crypto_trend_btcusd | C3 | 5 | 11 | 3,634 | 1.187 | 0.99998 | PASS | > 1e6: no realistic n | 5.3–11.1 | 1.0000 | 0.99997 |
| S_C3_crypto_trend_krwbtc | C3 | 5 | 11 | 2,530 | 1.216 | 0.99951 | PASS | > 1e6: no realistic n | 3.4–5.2 | 0.9999–1.0000 | 0.9993 |
| S_E8_pairs_kodex_tiger | E8 | 8 | 8 | 3,504 | 0.552 | 0.9691 | REVISE (execution) | **769 (320–3,505)** | 2.0–2.5 | 0.978–0.982 | 0.9659 |
| S_E2_voltarget_kodex200 | E2 | 8 | 8 | 3,496 | 0.531 | 0.9627 | REJECT (benchmark p 0.81) | **89 (60–167)** | 1.6–1.9 | 0.974–0.978 | 0.9588 |
| S_E5_xsmom_sectors | E5 | 12 | 12 | 6,197 | 0.476 | 0.9695 | REJECT (benchmark p 0.97) | **81 (70–97)** | 1.44–1.51 | 0.990–0.992 | 0.9627 |
| S_E1_trend_us | E1 | 12 | 12 | 4,711 | 0.840 | 0.99954 | REJECT (benchmark p 0.75) | > 1e6: no realistic n | 5.1–8.8 | 0.9998–0.9999 | 0.9994 |
| S_E2_voltarget_spy | E2 | 8 | 8 | 7,208 | 0.634 | 0.99917 | REJECT (benchmark p 0.18) | > 1e6: no realistic n | 5.9–9.7 | 0.9995–0.9997 | 0.9990 |
| S_E3_riskparity_us | E3 | 8 | 8 | 4,669 | 0.892 | 0.99981 | REJECT (benchmark p 0.25) | > 1e6: no realistic n | 5.9–12.0 | 0.9999–1.0000 | 0.9998 |
| S_S6_pairs_samsung_pref | E8 (S6) | 8 | 8 | 4,422 | 0.831 | 0.99970 | REJECT (benchmark p 0.61) | > 1e6: no realistic n | 14.7–136 | 0.9997–0.9998 | 0.9997 |
| S_S6_pairs_hyundai_kia | E8 (S6) | 8 | 8 | 4,615 | 0.426 | 0.8606 | REJECT (DSR) | passes only at n = 1 (DSR at n = 2 is 0.9406); see Table 2 and section F | — | 0.964–0.968 | 0.8185 |
| S_E1_trend_krx | E1 | 12 | 12 | 1,884 | 0.524 | 0.8416 | REJECT (DSR) | fails even at n = 1 | — | 0.920–0.927 | 0.8212 |
| S_B3_tsmom_futures | B3 | 12 | 12 | 5,634 | 0.082 | 0.2705 | REJECT (DSR) | fails even at n = 1 | — | 0.651 | 0.2117 |
| S_E8_pairs_gld_iau | E8 | 8 | 8 | 4,602 | −2.281 | 5.8e−165 | REJECT (DSR) | fails at every n (SR < 0) | — | 0.0000 | 0.0000 |
| S_V1_vix_rolldown | — | 8 | 8 | 3,197 | −0.143 | 0.2786 | REJECT (DSR) | fails at every n (SR < 0) | — | 0.305–0.306 | 0.2725 |
| S_V3_fx_momentum | — | 2 | 2 | 1,367 | −0.592 | 0.0623 | REJECT (DSR) | fails at every n (SR < 0) | — | 0.081–0.089 | 0.0446 |
| S_V4_dollar_carry | — | 1 | 1 | 1,429 | 0.273 | 0.7418 | REJECT (DSR) | n-invariant (one configuration): one column gives sr_sd = 0 (`validate.py:506`) | — | 0.740–0.744 | 0.7418 |

**The cases where trial history would change a verdict under today's pairing** (attribution COUNT when the count
comes from the pre-card reading; POST_CARD when only the all-time reading reaches it):

| Card | Existing | What would flip it | Decision then | Predicate and reason |
|---|---|---|---|---|
| S_E8_pairs_kodex_tiger | REVISE (execution) | n ≥ 769 (320–3,505); or the hurdle × 2.0–2.5 | **REJECT** | `dsr_ok` becomes false. REJECT is tested before REVISE (`validate.py:593` before `:613`). |
| S_E2_voltarget_kodex200 | REJECT (benchmark) | n ≥ 89 (60–167); or × 1.6–1.9 | REJECT, reason "deflated Sharpe below 0.95" | The reason prefers DSR (`validate.py:596-599`). The revise target follows the benchmark and stays (`:600`). |
| S_E5_xsmom_sectors | REJECT (benchmark) | n ≥ 81 (70–97); or × 1.44–1.51 | REJECT, reason changes | As above. |
| every other DSR card | — | no realistic n | unchanged | flips beyond 1e6 trials, SR < 0, failing at n = 1, or n-invariant |

Revision 1 listed S_S6_pairs_hyundai_kia here. It reaches REVISE only at n = 1, which no trial count can give: N_raw
is at least G = 8. Only a correlation adjustment of its own grid can reach it. That is not trial history (Q-07), so the
case moved to Table 2 and section F.

**Table 2: the null-SE pairing (candidate criteria C4 and C5; section F).** Normal moments,
`scratch:r3_rev2_probe/se_null_flip.py`; the report prints the range over the moment scenarios. "DSR at n = N" is
G-SE for a card. "Flip N" is the N (real) at which DSR_SE reaches 0.95; for a card that fails at n = N, it is the N_eff
its grid would need to pass.

| Card | Existing decision | DSR, null SE, at n = N | Decision then | Flip N, null SE | Attribution |
|---|---|---|---|---|---|
| S_C3_crypto_trend_btcusd | PASS | 0.9980 | PASS | 268 | PAIRING+COUNT at n ≥ 268 |
| S_C3_crypto_trend_krwbtc | PASS | 0.9870 | PASS | 41.6 | **PAIRING+COUNT at n ≥ 42: PASS → REJECT** |
| S_E8_pairs_kodex_tiger | REVISE (execution) | **0.7254** | **REJECT** (DSR) | 1.64 | **PAIRING at today's count**; under E-GRID it fails unless N_eff(grid) ≤ 1.64 |
| S_E2_voltarget_kodex200 | REJECT (benchmark) | 0.6984 | REJECT, reason DSR | 1.48 | PAIRING (reason only) |
| S_E5_xsmom_sectors | REJECT (benchmark) | 0.7559 | REJECT, reason DSR | 2.50 | PAIRING (reason only) |
| S_E1_trend_us | REJECT (benchmark) | 0.9754 | unchanged | 24.4 | PAIRING+COUNT (reason only) at n ≥ 25 |
| S_E2_voltarget_spy | REJECT (benchmark) | 0.9732 | unchanged | 14.2 | PAIRING+COUNT (reason only) at n ≥ 15 |
| S_E3_riskparity_us | REJECT (benchmark) | 0.9913 | unchanged | 40.4 | PAIRING+COUNT (reason only) at n ≥ 41 |
| S_S6_pairs_samsung_pref | REJECT (benchmark) | 0.9782 | unchanged | 17.2 | PAIRING+COUNT (reason only) at n ≥ 18 |
| S_S6_pairs_hyundai_kia | REJECT (DSR) | 0.6425 | unchanged | 1.23 | **PAIRING with a grid correlation adjustment: REJECT → REVISE (regime) if N_eff(grid) ≤ 1.23** (E-GRID) |
| S_E1_trend_krx | REJECT (DSR) | 0.4078 | unchanged | fails at N = 1 (0.9238) | — |
| S_B3_tsmom_futures | REJECT (DSR) | 0.1009 | unchanged | fails at N = 1 (0.6512) | — |
| S_E8_pairs_gld_iau | REJECT (DSR) | 0.0000 | unchanged | fails at every N | — |
| S_V1_vix_rolldown | REJECT (DSR) | 0.0245 | unchanged | fails at N = 1 (0.3053) | — |
| S_V3_fx_momentum | REJECT (DSR) | 0.0290 | unchanged | fails at N = 1 (0.0843) | — |
| S_V4_dollar_carry | REJECT (DSR) | 0.7422 | unchanged | fails at N = 1 | — (under this pairing n matters even with one configuration) |

Why the two pairings differ so much. The gate's dispersion term is the spread of the grid's Sharpe ratios. Grid
points of one rule are highly correlated, so that spread is small. For S_E8_pairs_kodex_tiger it backs out at about
0.0022 per day, while SE_null(3,504) is about 0.0169 per day, almost 8 times larger. The matched pairing therefore needs
N_eff, which is small for such a grid, and not G or N_raw. That is map03 R-3d's point. Which pairing is right is the
question of ⑨-3c (section 8). The S_S6_pairs_hyundai_kia and S_E8_pairs_kodex_tiger outcomes under E-GRID depend on
their grids' N_eff, which is UNVERIFIED because no series is stored; Tier B can compute it (7.4).

What this means for the owner's ledger counts.
- Under today's pairing, a Lab pairs run adds 8 configurations per universe and cost (`strategy_lab_page.py:44-45`).
  L-FAM flips S_E8_pairs_kodex_tiger only when the E8 ledger holds about 769 configurations in the pre-card reading:
  about 96 distinct pair-universe-cost combinations made before 2026-10-22T15:53:18Z with spans that overlap the card's.
  S_E2_voltarget_kodex200 needs about 89 (about 11 vol-target universes or costs of 8 each); S_E5_xsmom_sectors about 81
  (about 7 grids of 12). The last two would change only the reason text.
- Lab runs load the latest sessions, so nearly every Lab span overlaps every card span (cards end in September 2026).
  The time cut is therefore the filter that binds.
- Under the null-SE pairing, S_C3_crypto_trend_krwbtc would turn from PASS to REJECT once the C3 count reaches 42. The
  C3 ledger holds Lab, paper_live and CRY-1 rows (map02 F9). The owner has been asked for the `E1.jsonl` and `C3.jsonl`
  row counts (`REMAINING_WORK_2026-10-27.md:115`). Until then this is UNVERIFIED (map02 §10).

### 7.4 Where the numbers come from

**Tier A (default): stored card fields only.** No returns are recomputed. The report reads `stats` (including
`sr_oos`, `n_sessions`, `n_trials`, `dsr`), `trials.N_total`, `rules.grid`, `universe.symbols`, `costs.cost_bps`,
`data.start`, `data.end`, `created`, `decision`, `decision_reason` and `revise_target`. The moment scenarios bound what
the cards do not store (g3, g4 and the dispersion; map01 §5). ⑨-3b uses Tier A unless the owner rules otherwise.

**Tier B (optional, owner ruling Q10): exact recomputation for eight cards.** These are the DSR cards whose inputs avoid
the four excluded files and the network:

| Card | Cache files read (all in `docs/asset_expansion/cache/`) | Study function |
|---|---|---|
| S_E1_trend_krx | `yf_069500.KS`, `yf_152380.KS`, `yf_132030.KS`, `yf_229200.KS`, `fred_DGS3MO` | `run_trend` (`docs/asset_expansion_study.py:271-279`, `:725`) |
| S_E2_voltarget_kodex200 | `yf_069500.KS`, `fred_DGS3MO` | `run_vol_target` (`:282-290`, `:727`) |
| S_E5_xsmom_sectors | `yf_XLB`, `yf_XLE`, `yf_XLF`, `yf_XLI`, `yf_XLK`, `yf_XLP`, `yf_XLU`, `yf_XLV`, `yf_XLY` | `run_xs_momentum` (`:303-310`, `:729`) |
| S_B3_tsmom_futures | `yf_ZF_F`, `yf_ZN_F`, `yf_ZB_F`, `yf_GC_F`, `yf_SI_F`, `yf_CL_F`, `yf_NG_F`, `yf_ZC_F`, `yf_ZS_F`, `yf_HG_F`, `fred_DGS3MO` | `run_tsmom` (`:313-322`, `:730`) |
| S_E8_pairs_kodex_tiger | `yf_069500.KS`, `yf_102110.KS` | `run_pairs` (`:346-365`, `:733`) |
| S_S6_pairs_samsung_pref | `yf_005935.KS`, `yf_005930.KS` | `run_pairs` (`:734`) |
| S_S6_pairs_hyundai_kia | `yf_000270.KS`, `yf_005380.KS` | `run_pairs` (`:735`) |
| S_E8_pairs_gld_iau | `yf_IAU`, `yf_GLD` | `run_pairs` (`:736`) |

How Tier B runs (ENG-21):
- `tools/r3/tier_b.py` imports the study module and sets `REFRESH = False` (`docs/asset_expansion_study.py:844`).
- It replaces the study's `_cached` and `fred` (`:68-104`) with an allow-list wrapper. The wrapper raises before any
  `exists()` call for a name outside the list above, and also when a listed file is missing. It never calls the loader,
  so it can never reach the network or write a CSV (`_cached` would do both for a missing file, `:72-76`).
- Its exception derives from `BaseException`. So the study's `rf_daily`, which catches `Exception` and substitutes 3 %
  (`:148-153`), cannot swallow a refusal and turn it into silent drift.
- The tool asserts that each listed file of the card was read exactly once.
- It calls the card's `CANDIDATES` entry (`:723-758`) and never `write_results` (`:764-817`). So no card, results file or
  manifest is written.
- It runs under the T-HERM-01 network guard and saves into a temporary directory: the rebuilt score at the stored N,
  g3, g4, the dispersion and the T×G matrix.
- Step 1, drift check: the decision at the stored N must equal the stored decision; otherwise the card is labelled
  GATE. Step 2: the exact rows of 6.3, E-GRID included, by replay.
- T-RUNREG-12 tests the wrapper on a temporary cache directory of fake files, never on the real cache.

Not in Tier B, so Tier A is their only route (map01 §9 item 7):
- S_E1_trend_us, S_E2_voltarget_spy, S_E3_riskparity_us and S_V1_vix_rolldown read `yf_SPY`.
- The two S_C3 cards read `yf_BTC-USD` or `upbit_KRW-BTC`.
- S_V3 and S_V4 load FX data through `core.ficc.data` with source "auto" (`docs/asset_expansion_study.py:391-396`), which
  may reach the network.

---

## 8. Validation plan for the overfitting-correction criterion (⑨-3c)

### 8.1 Question

Which trial count N, paired with which dispersion term, keeps the gate's DSR predicate at or below its intended
false-positive rate when research involves several runs, revisions and correlated grids, and at what cost in power? The
answer is a recommendation. The owner decides at ⑨-3d.

### 8.2 Candidate criteria

| Id | N | Dispersion term | Computation |
|---|---|---|---|
| C0 | G of the reported run (today) | current grid | `validate.deflated_sharpe` |
| C1 | N_raw, literal, over all runs in scope | current grid | same |
| C1r | N_raw, distinct-rule | current grid | same |
| C2 | N_raw | Sharpe dispersion across all N_raw trials | same, with the dispersion replaced |
| C3 | ⌈N_eff⌉ | current grid | same; the mismatched pairing, kept to measure its error (map03 R-3d) |
| C4 | N_eff (real) | SE_null(T_oos) (3.19) | `gate_stats.psr` with `gate_ledger.emax_iid` |
| C4f | N_eff (real) | SE_null(T_full) | same |
| C5 | N_raw | SE_null(T_oos) | same |
| C5f | N_raw | SE_null(T_full) | same |
| C6 | K clusters | Sharpe dispersion of cluster returns (simplified, map03 §4.3 column c) | diagnostic only |
| C7 | R_wf: the number of distinct walk-forward experiments seen in scope (runs that added at least one key to K) | SE_null(T_oos) | same (Q-10) |

Why C7. The gate tests the walk-forward OOS series. Within one walk-forward the OOS segment is not selected on, so the
grid size G is not obviously the selection count (map03 R-3, "Open within R-3"; §6 item 7). What was selected on is
which walk-forward experiment to report. C7 counts those.

Map03's synthetic checks already show two things (map03 §4.3). Mixing a correlation-reduced N with the raw dispersion
(C3-like) raised the false-pass rate in correlated designs. The null-SE pairing (C4-like) stayed at or below 0.050.
Those checks used one seed per case and no walk-forward. They illustrate; they do not validate.

The criterion is chosen by simulation, not by formula. Effective-number methods do not in general control the
familywise error rate (Halle et al. 2016). The Sharpe haircut for multiple testing depends on how many strategies were
tested (Harvey & Liu 2015). The estimators disagree widely on the same matrix (map03 §4.1: 10 to 89 for one
100-configuration grid).

### 8.3 Synthetic designs

All data are generated. No data file, no network, no ledger and no registry write.

**Factors.**

| Factor | Levels |
|---|---|
| F1 distribution | g: Gaussian; t: Student t with 5 degrees of freedom, scaled to unit variance; h: GARCH(1,1) volatility with α = 0.08 and β = 0.90. Daily volatility 1 % |
| F2 length T | 1,260; 2,520; 5,040 sessions |
| F3 grid structure (K configurations per run) | S1 independent, K = 12; S2 equicorrelated ρ = 0.9, K = 8; S3 3 blocks of 4 (0.9 within, 0.3 between); S4 11 columns over 5 distinct rules (C3-like, AR(0.8) between rules); S5 independent, K = 8; S6 independent, K = 100; S7 equicorrelated ρ = 0.5, K = 8; S8 equicorrelated ρ = 0.95, K = 12; S9 10 blocks of 10 (0.9 within, 0.2 between); S10 the 5 rules of S4 alone |
| F4 runs R | 1, 2, 5, 10 |
| F5 process | P-IND: independent runs; P-FAC: runs share a factor with ρ = 0.5; P-ADA: adaptive, grid r + 1 is centred on the in-sample winner of grid r (Q-21) |
| F6 truth | null (all true Sharpe ratios 0); mixed null (true annual Sharpe ratios drawn from N(0, τ²), τ ∈ {0.1, 0.25, 0.5}); alternatives (6 below) |

**Fractional design, run by priority group.** A group is run completely or not at all. Groups run in this order:

| Group | Purpose | Points |
|---|---|---|
| G1 core calibration | F1 = g; F2 all; F3 ∈ {S1, S2, S3, S4, S10}; F4 all; F5 ∈ {P-IND, P-ADA}; null | 3 × 5 × 4 × 2 = 120 |
| G2 robustness | F1 ∈ {t, h}; F2 = 2,520; F3 ∈ {S1, S2, S3, S4}; F4 ∈ {1, 5}; P-IND; null | 2 × 4 × 2 = 16 |
| G3 mixed null | F1 = g; F2 = 2,520; F3 ∈ {S1, S2, S3, S4}; F4 ∈ {1, 5}; P-IND; τ ∈ {0.1, 0.25, 0.5} | 4 × 2 × 3 = 24 |
| G4 power | F1 = g; F2 all; F3 ∈ {S1, S2}; F4 ∈ {1, 5}; P-IND; four alternative levels per T (below) | 3 × 2 × 2 × 4 = 48 |
| G5 breadth | F1 = g; F2 = 2,520; F3 ∈ {S5, S6, S7, S8, S9}; F4 ∈ {1, 5}; P-IND; null (10 points). Plus P-FAC with F3 ∈ {S1, S2, S3, S4}, F4 ∈ {2, 5} (8 points) | 18 |

Total: 226 points per layer. The design table, with an index per point, is written to `design.json` before any
replication runs (8.8).

**Mixed null in Layer B** (Q-21). The selected configuration changes across walk-forward origins. A false positive is a
pass whose stitched OOS series has an OOS-length-weighted true Sharpe ≤ 0.

**Alternatives** (Q-12). One configuration (S1) or a block of four (S2 analogue) has a positive true Sharpe; the rest
are null. The levels are chosen per T by a pilot, so that C0's Layer B power is near 0.2, 0.5, 0.8 and 0.9. The pilot
searches true annual Sharpe ratios from 0.25 to 3.0 in steps of 0.25 and freezes the four levels in `design.json`
before the main run.

**Layers** (Q-10).

| Layer | What runs | Role | Replications per point | Monte Carlo SE at a rate of 0.05 |
|---|---|---|---|---|
| A | matrices only; the DSR predicate on the best configuration's full-sample series | formula check: C0 at R = 1 must reproduce map03 §4.3 column (a) (cases A, B, C, E at T = 1,260) within 3 MCSE | 2,000 for those four cases | about 0.005 |
| B | `V.walk_forward` on the synthetic matrix, then the DSR as `score_strategy` computes it (`validate.py:498-507`), on the walk-forward OOS series | **layer of record** for A1 to A4 and A7 | 2,000 (MCSE ≤ 0.005 needs at least 1,900) | about 0.0049 |
| C | the full gate: the seven Lab families' strategy functions (`strategy_lab_page.py:34-46`) on synthetic driftless price panels through `S.pnl_matrix`, `V.walk_forward` and `V.score_strategy`, with only `n_trials` varied; `GATE` unchanged (B = 2,000) | confirmation, and gate-level power | 300 per family, at F2 = 2,520, R ∈ {1, 5}, P-IND | about 0.013 |
| Estimator checks | N_eff on raw P&L from finite T against the population N_equiv (bias, spread); duplicate invariance (S4 against S10); monotonicity; floor against ceiling rounding | calibration of the inputs | as needed | — |

**Layer C null and cash** (Q-13). `simulate` credits the unallocated part of a long-only book with `cash_daily`
(`core/quant/strategies.py:84-87`), and the Lab uses 0.03/252 (`strategy_lab_page.py:113`). On driftless prices a
long/flat rule would then earn cash while flat, so its true Sharpe would be positive. Layer C calibration therefore uses
`cash_daily = 0` and cost 0. A second Layer C run uses the table cost, still with `cash_daily = 0`. Smoke check: C0's
Layer C PASS rate under the null is at most its Layer B predicate rate plus 3 MCSE.

### 8.4 Metrics

- False-positive rate per point and criterion: the estimate p̂ and its Monte Carlo SE, always both, never pass or fail
  alone (Q-09).
- Power per alternative level; the area under the power curve over the four levels; the minimum detectable Sharpe at
  50 % power, interpolated.
- Power loss against C0, with its Monte Carlo SE, at every point.
- In Layer C: the rates of PASS, of each other decision, and of "not rejected for DSR", under the null and the
  alternatives.
- The ratio of the criterion's N to the population N_equiv, and the resulting hurdle.

### 8.5 Acceptance criteria for recommending a criterion

| # | Criterion |
|---|---|
| A1 | Calibration, Layer B. At every null and mixed-null point of G1, G2 and G3, the estimated false-positive rate p̂ ≤ 0.05. A point with \|p̂ − 0.05\| ≤ 3 MCSE is re-run once with fresh pre-registered seeds (8.6), and the re-run's estimate decides. DSR ≥ 0.95 is not a size-0.05 test of the maximum (map03 §4.3, note under the table), so 0.05 is a ceiling, not a target; the report shows how far below it each criterion sits. |
| A2 | Robustness: A1 holds at the G2 points (t5 and GARCH). |
| A3 | Duplicate invariance: between S4 and S10, N and p̂ change by at most 2 MCSE. |
| A4 | Monotonicity: adding a new independent configuration never lowers N. |
| A5 | Matched pairing (reported property, not a filter): whether N and the dispersion term describe the same set of trials (map03 R-3d). |
| A6 | Computability (reported separately, not a filter): the share of the owner's Lab runs for which the criterion can be computed from registry fields, and the named fallback where it cannot. C1, C1r and C5 need counts only. C2, C3, C4 and C7 need series or run counts that LEDGER_ONLY rows lack; their fallback is C1 or C5 for those rows, as the recommendation states. |
| A7 | Power: among criteria that meet A1 to A4, the recommendation is the one with the largest area under the Layer B power curve; ties go to the smaller minimum detectable Sharpe. Its power loss against C0 is reported at every point, with Layer C's PASS and "not rejected for DSR" rates beside it. |
| A8 | Reproducibility: the same seeds give byte-identical result files on one platform with pinned library versions (ENG-25). |
| A9 | Confirmation: in Layer C, each recommended criterion's null rate of "not rejected for DSR" is at most its Layer B rate plus 3 MCSE of Layer C. A failure is reported and blocks the recommendation. |

Which candidates can be recommended (stated before the study runs, Q-11). C0, C1, C1r, C2, C3, C4, C4f, C5, C5f and C7
can all be recommended if they meet A1 to A4 and A9. C3 is expected to fail A1 in correlated designs (map03 §4.3
column b); it stays in the list so that the failure is measured. C6 is a diagnostic only: it is a simplified clustering,
not López de Prado and Lewis's procedure.

If no criterion meets A1 to A4 and A9, the recommendation is to keep C0 for verdicts and to keep the shadow counts as
disclosure. The report says why. The recommendation also lists every stored card whose verdict would change under it
(from ⑨-3b), with its attribution label (7.2 E).

### 8.6 Hermeticity, seeds and budget

- Seeds: `numpy.random.default_rng(SeedSequence([20261027, design_index, replication]))`. The re-run seeds of A1 are
  `SeedSequence([20261027, design_index, 1_000_000 + replication])`. Both are written to `seeds.json` before the run.
- The study imports `validate`, `gate_ledger`, `gate_stats` and `strategies` read-only. It never assigns to `GATE`.
  Integer criteria use the rounding of 6.4.
- Output goes to `--out`: a temporary directory in tests, `docs/strategy_lab/r3/validation/` for the of-record run.
- **Replications are never cut** (Q-09, ENG-13 (a)). A pilot of 10 replications per point measures run time and
  projects each group's time. Groups run in priority order within the owner's compute budget (Q20). A group that does
  not fit is reported "not run". A layer whose planned replications were not completed is "inconclusive", never a pass.
  A recommendation needs G1, G2, G3 and G4 complete in Layer B, and Layer C complete. Run times are UNVERIFIED.

### 8.7 Output

`design.json` (8.3), `results.csv` (one row per point, criterion and metric, with estimate and MCSE),
`validation_report.md` (tables per layer and group, the acceptance checklist, the recommendation, the stored-card list
with attribution labels) and `seeds.json`.

### 8.8 Pre-registration (ENG-13 (b))

- Before step 6 (the of-record ⑨-3b report), section 8 of this spec, `design.json` and `seeds.json` are frozen by a
  commit made on the owner's instruction. The SHA-256 of `design.json` is recorded in
  `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`.
- `tools/r3/null_study.py` refuses to run when its design hash differs from the recorded one.
- This spec already shows the card-level effect of some candidates (7.3). That is why the recommendation rule uses
  synthetic results only (A1 to A9), never card outcomes, and why the candidate list is frozen in this revision, before
  any owner ledger count is known.

---

## 9. Implementation outline

### 9.1 New files

None of these is in the frozen list (`core/quant/gate_package.py:36-38`).

| Path | Role |
|---|---|
| `core/quant/run_registry.py` | event schema and validation; canonical lines, chain, lock with bounded waits, verified-prefix cache, segments; fold; run ID with retry; strategy version (LF and raw hashes), environment, canonical panel loader with the pinned hash, behaviour fingerprint; data hash; series store with retry; the pure key builder `lab_config_ids(rule, is_pairs, symbols, grid, cost_bps)`; `LabRecorder` with guarded hooks; outage writer. No wall clock and no `config` import. |
| `core/quant/trial_counts.py` | classification (section 4); set counts (3.13); N_eff wrapper (dated Series, common window, constant-column reading); shadow rows by replay (6.3, 6.4); predicate helper; diagnostics (6.5); card replay, analytic shadow and time-bounded card readings (6.6). Pure functions. Ledgers are read only through `FamilyLedger.rows()` and file sizes. |
| `data/r3/canonical_panel_v1.npy` | the canonical panel fixture (5.4) |
| `tools/r3/__init__.py`, `tools/r3/make_canonical_panel.py` | generates the fixture once |
| `tools/r3/compare.py` | the ⑨-3b report command (section 7) |
| `tools/r3/annotate.py` | writes SUPERSEDED, DECLARATION, ANNOTATION and BACKFILL events through `run_registry`'s lock and validation; takes an `--owner-ruling` reference (ENG-10) |
| `tools/r3/registry_segment.py` | the owner-approved recovery segment (5.2) |
| `tools/r3/tier_b.py` | Tier B with its allow-list wrapper; runs only after Q10 |
| `tools/r3/null_study.py` | ⑨-3c (section 8), with the design-hash check |
| `tests/macro_r3_registry.py` | T-RUNREG-00 to T-RUNREG-12 |

### 9.2 Changes to `ui/strategy_lab_page.py` (not frozen; shadow only)

1. **`register_trials` is not changed** (Q-03, ENG-02). The registry builds its keys with the pure key builder of 9.1.
   T-RUNREG-01b pins the builder to rows written by the unchanged `register_trials` into a temporary ledger, and to
   golden `config_id`s computed at `527cdf2`. It also pins the SHA-256 of `register_trials`'s source, so any later
   change to the writer is a deliberate, reviewed event.
2. **`run_family(..., ledger_dir=None, recorder=None)`** (ENG-01). `ledger_dir` is passed to `register_trials` at `:118`;
   None keeps today's path (`QC.macro_dir() / "ledgers"`, `:67`). With `recorder=None` nothing else changes. When a
   recorder is passed, the function calls through the guard of 6.4:
   - `started(...)` after `:89`, before the argument checks at `:90`;
   - `cost_resolved(cost_bps, floor, classes, withheld)` after `:103`;
   - `data_loaded(hists, pn)` after `:105`;
   - `pnl_computed(M, Ms, Tv, dates)` after `:115`; this hook appends the first PROGRESS event;
   - `walk_forward_done(wf)` after `:116`;
   - `ledger_size_before()` and `ledger_size_after()` around `:118`;
   - `scored(sc)` after `:129`;
   - on any exception, `failed(stage, exc)` in a nested `try`, then the same exception object is re-raised.

   The `__main__` self-check (`:320-330`) and `tests/expansion_acceptance.py:338` (which runs that self-check) pass no
   recorder and write nothing.
3. **The page's `run` worker** (`:227-279`):
   - increments the generation counter and disables the Run button (6.7);
   - builds `LabRecorder(runs_dir=QC.macro_dir() / "runs", ledger_dir=QC.macro_dir() / "ledgers", clock, token)` inside
     a `try`; a failure there means no recorder for this click, an outage record and the muted notice;
   - calls `run_family` and renders the existing verdict exactly as today;
   - then, inside `try/finally`: the second PROGRESS event (ledger link, results, existing verdict, series), FINGERPRINT,
     SHADOW, the shadow card if the generation still matches, and FINISHED in the `finally` block;
   - in the two `except` branches (`:236-240`), shows the error exactly as today; the `finally` block then writes the
     failure PROGRESS (with the series when the stage reached PNL_COMPUTED) and FINISHED;
   - re-enables the Run button as 6.7 states.
4. **Scorecard detail** (⑨-3b): the muted shadow line of 6.7, with the reports directory as a parameter.

### 9.3 Tests

All tests live in `tests/macro_r3_registry.py`. Rules:
- **Hermetic directories** (ENG-01). Every test that calls `run_family` or the page worker runs inside a helper
  `temp_macro_dir()`. It sets `QUANTGEN_MACRO_DIR` to a new temporary directory (`config.macro_dir()` reads it on each
  call, `config.py:176-178`), asserts that `config.macro_dir()` resolves under `tempfile.gettempdir()` before yielding,
  and restores the variable in `finally`. Tests also pass `ledger_dir` and the runs directory explicitly. T-HERM-02 and
  T-RUNREG-00 detect a stray write after the fact; they are not the means of prevention.
- **Panels.** Synthetic, or from a patched `load_history` that returns synthetic closes labelled with a real source
  name. Such tests do register ledger rows, so they run only inside `temp_macro_dir()` with a temporary `ledger_dir`.
- **No paper_live** (ENG-03). `tests/paper_live_acceptance.py` imports `paper_live` at module level (`:19-21`). It is
  owner-run only and is never run or imported in this container. The assertions of its `test_17` and `test_18`
  (`:333-359`) need only `ui.strategy_lab_page` and `gate_ledger`; they are copied into T-RUNREG-01b and T-RUNREG-04.
- **Lazy UI imports.** `ui` modules are imported inside the tests that need them. When `flet` is missing, those tests
  raise `NotRun`.
- **Equality** is NaN-aware (6.1 item 2).

| Id | What it pins |
|---|---|
| T-RUNREG-00 | Hermetic frame. `test_00_*` takes `macro_acceptance.snapshot()` (`tests/macro_acceptance.py:141-142`); `test_zz_*` compares with the assertions of T-HERM-02 (`:203-207`). `temp_macro_dir()` resolves under the temporary directory and restores the variable. |
| T-RUNREG-01 | Byte-identity. With and without a recorder, on two temporary ledgers: equal `StrategyScore` fields, return values, `payload(r)` and `narrative(r)`; ledger rows equal except `run_utc`, `row_md5` and `prev_row_md5`. The same with a recorder whose every hook raises and with one whose every hook sleeps 0.2 s. Failure paths, each with the same exception type and message and the same ledger bytes: no symbols (`:90-91`), no cost row (`:94-96`), `HistoryError`, a broken ledger chain, a broken registry chain. |
| T-RUNREG-01b | Keys. For a fixed input set (each of the seven families; pairs order; lower-case and reordered symbols; cost 50 and 50.0; typed cost and table cost; a SYNTHETIC source), the pure key builder equals the `config_id`s that the unchanged `register_trials` writes into a temporary ledger; golden `config_id`s frozen at `527cdf2` match; the SHA-256 of `register_trials`'s source matches its pinned value. Includes the assertions of `test_17` (`tests/paper_live_acceptance.py:333-344`). |
| T-RUNREG-02 | Store. The chain verifies; an edit, a dropped line, a moved line and a reformat are each detected; unknown event types and fields are refused; a second STARTED and a second FINISHED for one run ID are refused; NaN becomes null and is listed; 5 threads × 10 events keep the chain; a broken chain refuses appends; a half-written last line is refused, and the recovery segment folds the verified prefix and leaves the old file byte-identical; rollover keeps the chain; the verified-prefix cache agrees with a full verification; a duplicate run ID is retried with a new token; the regex refuses non-ASCII digits. |
| T-RUNREG-03 | Lifecycle. STARTED exists before the argument checks; a loader error gives FAILED_BEFORE_STATS; an error inside `pnl_matrix` gives FAILED_BEFORE_STATS at DATA_LOADED; "too few sessions" in `align_panel` gives FAILED_BEFORE_STATS and in `walk_forward` FAILED_AFTER_STATS with its series stored; success gives COMPLETED; a rendering exception after the display still writes FINISHED; an orphan's stage comes from its last PROGRESS; ABORTED or OPEN depends on `as_of`; a SUPERSEDED event keeps the earlier status. |
| T-RUNREG-04 | Ledger link. Rows carry the stored `row_md5` on both the append and the dedup path (`gate_ledger.py:346`, `:349`); prefixes by byte size give the right `hash_before` and `hash_after`; registry reads create no lock file; a second writer appending between the two sizes sets `interleaved`; only temporary ledgers are touched. Includes the assertions of `test_18` (`tests/paper_live_acceptance.py:347-359`). |
| T-RUNREG-05 | Classification. One scenario per row of 4.2, asserting the TOTAL, N_raw (every reading), N_eff-input and N_validation deltas; a LEDGER_ONLY row counts exactly once before and after its adoption; the 9a and 9b branches (same request; `days` increased after "extend history"; `days` increased otherwise; `days` decreased; source changed; resolution changed under `auto`); combined differences with their precedence and MULTI_CHANGE; ENV_CHANGE and ENV_CONFOUNDED; each validation condition failing on its own; VALIDATION_SPENT adding its keys once; human events with and without a valid owner ruling; HOLDOUT_TOUCHED; the C3 lattice on the canonical panel (the 6-point grid gives 3 rules, the 5-point lattice 5, the union 5) and on a tied-close panel (h = 0.2 and h = 0.3 differ). |
| T-RUNREG-06 | Shadow. Each replayed row equals a fresh `V.score_strategy` call with that n on every field (NaN-aware); `GATE` is equal before and after; no shadow number in `payload(r)` or `narrative(r)`; the ceiling rule; the predicate helper agrees with `_decide_strategy`, including the minimum-track-record branch; SE_null rows equal `gate_stats.psr`; the grid-dispersion diagnostic equals `validate.deflated_sharpe` at integer N within 1e-12; "n-invariant" when G = 1. |
| T-RUNREG-07 | Cards. The replay of 6.6 reproduces decision, reason and revise target for all 16 DSR cards; the cards directory's MD5s are unchanged; the flip n is 769, 89 and 81 for the three narrow cards under normal moments; S_S6_pairs_hyundai_kia gives DSR 0.9406 ± 0.0001 at n = 2 and PSR ≥ 0.95 at n = 1; the null-SE values of Table 2 (7.3) within 1e-4; flips above 1e6 print "> 1e6"; on a fixture ledger, the pre-card, pre-created and all-time readings split rows correctly and an all-time-only flip is labelled POST_CARD. |
| T-RUNREG-08 | Report. `compare.py` on temporary ledger fixtures and the stored cards writes only under the temporary `--out`; never writes the cards directory; gives identical bytes on two runs with the same `as_of`; asserts 34 and 16 cards and lists a skipped file; cuts the ledger by `hash_after`; prints outage windows; the scorecard line reads an injected reports directory and survives a malformed CSV. |
| T-RUNREG-09 | Static rules. The new `core/` modules call no wall clock and import no `config` (the check of `tests/macro_m7_ledger.py:584-593`); they pass `gate_ledger.scan_forbidden` (`gate_ledger.py:851-888`); no new module imports `paper_live` or `grokteam`; no new module assigns to `GATE`; no new module names an excluded cache file (the test builds the names from fragments); `tools/r3/tier_b.py` holds only its allow-list; the canonical panel's SHA-256 equals the pinned constant. |
| T-RUNREG-10 | Null-study smoke test. A few seeded replications give identical CSV bytes twice; the Layer A formula check on one map03 case; the tool refuses a changed design hash. |
| T-RUNREG-11 | UI. Two overlapping synthetic runs through the page worker with a fake page: run A's shadow card never appears under run B; the Run button is disabled during a run's work on screen and re-enabled after; all inside `temp_macro_dir()`. |
| T-RUNREG-12 | Tier B wrapper, on a temporary directory of fake cache files: an unlisted name raises a `BaseException` subclass before any `exists()` call; a missing listed file raises; the loader is never called; each listed file is read once. |

### 9.4 Suite registration

- The module name starts with `macro_`, so the macro aggregator discovers it (`tests/macro_acceptance.py:216-234`). The
  aggregator's `_wrap` takes the T-HERM-02 snapshot once, before the first test, and runs each test under the T-HERM-01
  guard (`:145-153`). T-HERM-02 itself is a separate last check (`:198-207`). It runs only through the aggregator, which
  `tests/run_all.py` drives, and `run_all.py` is barred in this container because it rewrites
  `qa/acceptance_results.json` (`tests/run_all.py:136-137`). Revision 1 said the aggregator "wraps every test in the
  T-HERM-01 and T-HERM-02 guard"; that was inaccurate (ENG-14).
- `run_module` (`tests/macro_acceptance.py:237-264`) applies only the T-HERM-01 guard. So the module carries its own
  snapshot pair (T-RUNREG-00). `run_module` sorts tests by name (`:248`), so `test_00_*` runs first and `test_zz_*`
  last.
- Command in the container: `python -m tests.macro_r3_registry`. The module ends with
  `raise SystemExit(run_module(globals()))`.
- Its milestone tag is 0, because `tests/run_all.py:93-97` reads only `macro_m<k>` names.
- Fourteen rows go into `tests/macro_registry.csv` (T-RUNREG-00, -01, -01b, -02 to -12): tier `fast`, `runs_from` `M7`
  (the ledger's milestone; T-LEDGER-01 is M7 at `tests/macro_registry.csv:165`), modules `R-23`, feasibility `SYNTH`. The
  ids match the registry format (`tests/macro_m0_harness.py:22`). `implemented_in` is filled by
  `python -m tests.macro_acceptance`, which rewrites that CSV (`sync_registry`, `tests/macro_acceptance.py:277-295`). The
  format checks are `tests/macro_m0_harness.py:229-298`.
- Never `python tests/run_all.py` in this container.

### 9.5 UI changes

Only those of 6.7 and 9.2 items 3 and 4. Every shadow element is labelled "not a verdict" and uses muted tokens. The Run
button's disabled state is the only change to an existing control (Q19).

### 9.6 Migration of existing ledgers (read-only)

- No migration writes. LEDGER_ONLY trials are computed on the fly from `FamilyLedger.rows()` at each count.
- For each such row the report shows the first span, `run_utc`, anchor and writer (by `script` and `source`, map02 §10).
  How often it ran, its results and its verdict stay null; they are never invented (map02 §10).
- A broken chain gives "ledger unreadable at line N". The ledger-based rows of that family are then unavailable. The
  ledger is never repaired.
- Every report and every second PROGRESS event stores the family hash and `n_raw` it read, so `snapshot(hash)` can
  re-prove it.
- C3's written history becomes a BACKFILL event (RECONSTRUCTED: the 6-point grid of runs 2 and 3 on BTC-USD at the
  crypto table cost) only after the owner approves Q9, and the event cites that ruling. Until then the stored
  N_total = 11 is the floor (6.6).
- Optional series for LEDGER_ONLY Lab rows (Q11): the owner runs the ledger's configurations again on current data. Those
  runs are ADOPTED or REMEASURE; they add series and no N_raw.

### 9.7 Steps

| Step | Stage | Work | Done when |
|---|---|---|---|
| 0a | ②-6 | this spec | the owner's approval and answers to 10.2 A are recorded verbatim with channel and date |
| 0b | before ⑨-3a | the audit's proposed patches to `ui/strategy_lab_page.py` are decided (1.5) | the decision is recorded |
| 1 | ⑨-3a | `run_registry.py` store, canonical panel fixture, pure key builder | T-RUNREG-00, -01b (including the copied assertions of `test_17`) and -02 pass under `python -m tests.macro_r3_registry` |
| 2 | ⑨-3a | Lab hooks, recorder, worker | T-RUNREG-01, -03, -04 (including the copied assertions of `test_18`) and -11 pass. `tests/paper_live_acceptance.py` is not run here; the owner may run it on his machine |
| 3 | ⑨-3a | classification and counts | T-RUNREG-05 passes; the C3 lattice result is recorded |
| 4 | ⑨-3a | shadow rows and the Lab card | T-RUNREG-06 passes; a synthetic UI run inside a temporary macro directory shows the existing block and both shadow blocks |
| 5 | ⑨-3b | `compare.py`, card replay, analytic shadow | T-RUNREG-07 and -08 pass; a rehearsal report exists in the scratchpad |
| 5a | before step 6 | freeze section 8, `design.json` and `seeds.json` (8.8) | the commit exists on the owner's instruction; the design hash is in the rulings log |
| 6 | ⑨-3b | of-record report on the owner's machine | the report is written; the owner has read it |
| 7 | ⑨-3b | Tier B, only if Q10 is yes | T-RUNREG-12 passes; drift check and exact rows for the 8 cards |
| 8 | ⑨-3c | null study | T-RUNREG-10 passes; the design hash matches; the validation report and recommendation exist |
| 9 | ⑨-3d | the owner's decision | 10.2 B is answered verbatim; any change to verdict criteria gets its own spec |

### 9.8 Rules for implementers

- `core/` and `docs/` Python files are scanned by T-STEP3-02 (`tests/macro_m7_ledger.py:315-343`; patterns at
  `gate_ledger.py:851-865`). No design-effect shape. No line that assigns `n_raw`, `n_eff`, `n_equiv` or `n_clusters`
  and also contains the word "revision".
- Every `open`, `read_text` and `write_text` passes `encoding="utf-8"`; text writes pass `newline="\n"`.
- The repository is byte-exact (`.gitattributes:1-2`). New files use LF.
- No new dependency.
- Never call `run_family` with a real-labelled source outside `temp_macro_dir()`.
- Never import or run `tests/paper_live_acceptance.py`, `paper_live/` or `grokteam/` in this container.
- Do not use the Lab while the full suite runs (5.1).
- No commit or push without the owner's instruction.

---

## 10. Risks, open questions and out of scope

### 10.1 Risks

1. **A shadow decision read as a verdict.** Mitigation: the labels and muted tokens of 6.7; the generation check;
   never in cards or the AI payload.
2. **A pairing effect read as trial history.** The null-SE pairing alone changes one card's decision and two cards'
   reasons at today's count (7.3).
   Mitigation: block 2 and report section F; the PAIRING and PAIRING+COUNT labels (7.2 E).
3. **Under-count by the behaviour fingerprint.** A code change that affects only branches the canonical panel never
   runs keeps the old lineage. Mitigation: real-data fingerprints are compared whenever two runs share `data_md5`; file
   digests are stored for an offline check.
4. **Over-count by environment drift** (Q-08, ENG-08). Reduced: the panel is a fixture; the fingerprint is consulted
   only on a code change; an environment change alone is ENV_CHANGE. Remaining: a code change and an environment change
   together can split a lineage; such keys are flagged ENV_CONFOUNDED and listed.
5. **Orphans counted fail closed** may over-count after a crash. The last PROGRESS event narrows the stage. An
   ANNOTATION with an owner ruling can record the reason.
6. **Registry growth.** About 15 to 25 KB of events and 0.5 MB of series per run (5.10).
7. **`GATE` is module state.** The new code never writes it. The existing exposure remains: two overlapping Lab runs can
   interleave the bootstrap override at `strategy_lab_page.py:124-129` and leave `GATE["bootstrap_B"]` at 1,000. This
   predates the design. Disabling Run during a run (Q19) closes it within one page, not across windows. A lock around
   `:124-129` would close it fully, but it edits the existing verdict path; it belongs on the known-errors list (②-4).
8. **Symbol resolution.** "069500" and "069500.KS" may give different `config_id`s (UNVERIFIED, map01 §3.4). Card keys
   then look new and are over-counted. The universe scope lists near-matches (6.6).
9. **Mixed writers.** C3 holds Lab, paper_live and CRY-1 rows (map02 F9). L-FAM includes them. The report lists writers.
10. **Unknown owner ledgers.** The sizes of all ledger counts are UNVERIFIED until step 6 (①-5 asks the owner for the
    `E1.jsonl` and `C3.jsonl` row counts).
11. **Old gate text on stored cards.** The replay matched 16 of 16 decisions; only the line wording differs.
12. **Fail-open gaps.** A broken registry means unrecorded runs. The notice, the outage file and report section G make
    the gap visible and bound it (Q16).
13. **Latency before the verdict.** Two file sizes and two bounded appends inside `run_family`; printed, not asserted
    (6.4).
14. **Windows and OneDrive** (ENG-15). Replace retries; LF-normalised hashes; UNVERSIONED anchors carried by file
    digests; sync-folder refusal; no Lab use during a full suite run.
15. **Pre-registration.** The card-level effect of some candidates is already visible in this spec. Mitigation: 8.8.
16. **Locked holdout.** From 2027 every real-data Lab run touches locked data; flagged and listed (Q22).

### 10.2 Open questions for the owner

**A. Needed before ⑨-3a (build and display conventions).** These decide what is built and which reading is printed
first. None of them changes a verdict.

| # | Question | Default taken in this draft |
|---|---|---|
| Q5 | Do cost-sensitivity runs with a withheld verdict count as trials in the primary printed count? | yes; excluded in the secondary reading |
| Q6 | Is a switch of data source or window after seeing results a new trial in the primary printed count? | yes (+k); the distinct-data reading is printed (changed in revision 2, Q-06) |
| Q7 | Does a run that failed after statistics but displayed nothing count in the primary printed count? | yes |
| Q9 | May C3's runs 2 and 3 be back-filled as RECONSTRUCTED events? Does BTC-USD's history also count on KRW-BTC? | no back-fill; stored N_total = 11 as the floor |
| Q10 | May Tier B re-score the 8 cards of 7.4 into a temporary folder? | no; Tier A only |
| Q11 | May the owner's LEDGER_ONLY Lab rows be re-run to obtain series for N_eff? | no (so E-FAM and E-MKT stay unavailable for those families) |
| Q12 | Which files define the strategy version digests (5.4), or the whole harness list? | the five files of 5.4 |
| Q13 | Is `macro_dir()/runs` the right place, with sync folders refused unless `QUANTGEN_R3_ALLOW_SYNC=1`? | yes |
| Q14 | How long are series kept? | kept |
| Q16 | Should a registry failure leave the verdict shown (fail-open, with outage records) or block it like the ledger (fail-closed)? | fail-open |
| Q17 | R3's "전환": should the Lab's displayed N stay G, with the ledger basis in shadow only, until ⑨-3d? The Lab's live verdict is not an existing card. | yes, shadow only |
| Q18 | R3's "각 전략 실행에 고유 ID": Lab runs only in this stage, with study and bridge runs later (`STUDY`, `BRIDGE` reserved)? The cards come from study runs. | Lab runs only |
| Q19 | May the Run button be disabled while a run's work on screen is in progress? | yes |
| Q20 | What compute budget may the null study use? | pilot first; then every group to completion; replications never cut |
| Q21 | Which time cut is of record for a card's trial history: the anchored commit that added it (`eacd57d`) or its `created` date? | the anchored commit; the `created` cut and the all-time reading are printed |
| Q22 | Should Lab runs that reach data from 2027-01-01 be flagged only, or blocked or truncated? | flagged only |

**B. Decided at ⑨-3d, through the pre-registered criteria of ⑨-3c** (ENG-12). These choose verdict criteria. R3 places
them after the separate validation.

| # | Question | Until then |
|---|---|---|
| Q1 | Which N, paired with which dispersion term, is of record: today's (G, grid), a ledger count with the grid dispersion (L-FAM, R-FAM, R-RULE), or a matched pairing (C4, C5, C7)? | all printed; none gates |
| Q2 | Family-wide or market-scoped? The ledger takes the larger (`gate_ledger.py:679-685`). | both printed |
| Q3 | How is a real N_eff rounded when the gate needs an integer? | ceiling in the disclosure rows; floor printed when it differs |
| Q4 | May a ledger-based N fall below G? | printed in block 2 only |
| Q8 | Is a pre-registered validation a trial (CRY-1) or not (`selection_factor`)? | not a trial in the primary reading; both printed |
| Q15 | Should the ledger write move before `pnl_matrix` (5.8, third column)? | not moved |

### 10.3 Out of scope

- Any change to verdict criteria, `GATE`, stored cards or the Lab's verdict N.
- Moving the Lab's ledger write (5.8, third column).
- Registering study runs or Nautilus bridge runs (Q18). The prefixes `STUDY` and `BRIDGE` are reserved. The bridge's run
  record already holds a compatible registration block
  (`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:1093-1104`).
- A Lab validation mode that evaluates a fixed configuration on a chosen span.
- A lock around the existing bootstrap override (risk 7).
- PBO over the union of all trials (`core/quant/gate_stats.py:651-724`), Reality Check and SPA family tests (White
  2000; Hansen 2005; `core/quant/tf_gov.py:257-333`), and ONC clustering (López de Prado & Lewis 2019).
- Any edit to `paper_live/`, `grokteam/` or a frozen harness file.

---

## Appendix A. Review round 1: dispositions

"Accepted" means applied as the reviewer proposed. "Changed form" means the problem is fixed by a different means, for
the reason given. "Extended" means applied and taken further. No issue is rejected.

| Issue | Severity | Ruling | Sections |
|---|---|---|---|
| Q-01 | major | Accepted. The shadow replays the decision on a copy of the existing score; it never writes `GATE`. The shadow lock and revision 1's invariant "GATE restored" are removed. The fresh-call comparison stays in T-RUNREG-06 only. Replay exactness was checked on synthetic panels (12 of 12). | 6.1, 6.4, 9.3, 10.1 risk 7 |
| Q-02 | major | Accepted. Every hook goes through a guard; fingerprints, the series write, ledger reads, counts and the shadow run after the display; T-RUNREG-01 adds raising and sleeping recorders. | 5.3, 6.4, 9.2, 9.3 |
| Q-03 | major | Accepted in the reviewer's alternative form (as ENG-02): `register_trials` is not refactored; a pure key builder is pinned against it and against golden `config_id`s at `527cdf2` (T-RUNREG-01b). | 1.3, 9.2, 9.3 |
| Q-04 | major | Changed form (with ENG-11). Pre-card is the primary card reading, with sibling cards and a universe scope; all-time flips are POST_CARD. The cut instant is the anchored commit that added the card (`eacd57d`), because `t_fix` accepts only anchored instants; the unanchored `created` date gives a second reading. The owner chooses which is of record (Q21). | 4.4, 6.6, 7.2 A and E, 7.3, Q21 |
| Q-05 | major | Accepted. N_raw is a set cardinality with a LEDGER_ONLY term; ADOPTED is decided from the ledger prefix before the run's registration; classes never come from hash differences; interleavings are flagged and cannot change N_raw. | 3.13, 4.2 rows 13 and 13a, 4.3, 5.4, T-RUNREG-04 and -05 |
| Q-06 | major | Accepted. DATA_CHOICE counts +k in the primary reading; precedence between 9a and 9b is explicit, with "extend history" as the only exception for a longer window. | 3.8, 4.2 rows 9a and 9b, 4.4, 4.5, Q6, T-RUNREG-05 |
| Q-07 | major | Extended. The E rows use (N_eff, SE_null); the mismatched pairing is a labelled disclosure row; L and R rows carry the dispersion label and a × 1.5 and × 2 sensitivity; "n-invariant" when G = 1; E-GRID and the S6 case moved to a separate block and report section. Extension: PAIRING baselines (E-GRID, G-SE), because this revision's probe shows that the null-SE pairing alone, at today's count, changes one card's decision and two cards' reasons. | 6.3, 6.5, 7.2 E and F, 7.3 |
| Q-08 | major | Changed form (with ENG-08). The canonical panel is generated once and shipped as a repository fixture with a pinned hash, rather than stored under `runs/`, so every machine fingerprints the same bytes. The fingerprint is consulted only on a code-identity change; the environment is recorded; ENV_CHANGE is a class with N_raw 0. | 3.4, 3.7, 3.17, 4.2 rows 1b, 8a and 8b, 5.4 |
| Q-09 | major | Accepted (with ENG-13 (a)). Published fractional design with priority groups; MCSE ≤ 0.005 per point; replications never cut; A1 restated with a pre-registered re-run rule; estimates and MCSE always reported. | 8.3, 8.4, 8.5, 8.6 |
| Q-10 | major | Accepted. Layer B is the layer of record; Layer A is a formula check; C7 added; C4 and C5 evaluated with T_oos and T_full; T_oos justified as primary. | 3.19, 6.5, 8.2, 8.3 |
| Q-11 | major | Accepted. A5 and A6 are reported properties, not filters; the recommendable candidates are stated before the study. | 8.5 |
| Q-12 | major | Accepted. Alternatives chosen by a pilot so that C0's power spans about 0.2 to 0.9; area under the power curve and minimum detectable Sharpe; power at predicate and gate level; power loss with MCSE. | 8.3, 8.4, 8.5 A7 |
| Q-13 | major | Accepted. Layer C calibration uses `cash_daily = 0`; smoke check added. | 8.3, 8.5 A9 |
| Q-14 | minor | Accepted. Row 2 restores the verdict-of-record and instability conditions and notes that no pair of Lab runs is a re-draw today. | 4.2 row 2 |
| Q-15 | minor | Accepted (with ENG-17). STARTED is written at the entry of `run_family`; the 5.8 rows are corrected. | 3.1, 4.2 rows 3 and 4, 5.6, 5.8 |
| Q-16 | minor | (a) Accepted: VALIDATION_SPENT adds the validated keys once. (b) Changed form: an explicit precedence with flag MULTI_CHANGE, not SEARCH, because the only counting difference (a data choice) already makes the key new, and the other combinations carry no new strategy information. | 4.2 row 7b, 4.3 |
| Q-17 | minor | Accepted (with ENG-20). The tie assumption is stated; real-data fingerprints are required; a tied-close panel is added to T-RUNREG-05. | 4.2 row 6, 4.5, 9.3 |
| Q-18 | minor | Accepted. Flips are searched up to 1e6; beyond that "> 1e6: no realistic n". | 6.6, 7.3 |
| Q-19 | minor | Accepted. The predicate helper includes the minimum-track-record branch; the decision always comes from `_decide_strategy`. | 6.4, T-RUNREG-06 |
| Q-20 | minor | Accepted (with ENG-18). Limits of `n_eff` stated; common-window length printed; dated Series as input. | 3.14, 6.2 |
| Q-21 | minor | Accepted. Adaptive process P-ADA added; Layer B mixed-null false positive defined on the stitched series. | 8.3 |
| ENG-01 | blocker | Accepted. `run_family` takes `ledger_dir`; tests use `temp_macro_dir()` and explicit directories; T-HERM-02 is detection only. | 5.1, 9.2, 9.3, 9.8 |
| ENG-02 | blocker | Accepted. `register_trials` untouched; the ledger link comes from two file sizes read inside `run_family` and one verified read after the display (a cheaper form of the reviewer's before-and-after reads); keys pinned by T-RUNREG-01b. | 1.3, 5.4, 9.2, 9.3 |
| ENG-03 | blocker | Accepted. `test_17` and `test_18` assertions copied; `tests/paper_live_acceptance.py` is owner-run only. | 1.3, 9.3, 9.7 step 2, 9.8 |
| ENG-04 | major | Accepted. Guard, nested `failed()`, read-only views, failure-path tests. | 6.1, 6.4, 9.2, T-RUNREG-01 |
| ENG-05 | major | Accepted (same fix as Q-01). | 6.4 |
| ENG-06 | major | Changed form. Generation check as proposed. The Run button is disabled until the run's work on screen ends (shadow card appended, error shown, or 60 s), not until FINISHED, because the remaining events write nothing to the screen and fingerprints can take seconds. | 6.7, 9.2, Q19, T-RUNREG-11 |
| ENG-07 | major | (a) Changed form: inside `run_family` only STARTED and one PROGRESS (stage, data, cost, keys) are written; results, verdict and series go into a second PROGRESS after the display, to keep verdict latency (Q-02); `try/finally` added. (b) Accepted: the page is the only FINISHED writer; a second FINISHED is refused. (c) Accepted: append-only recovery segments. | 5.2, 5.3, 5.6, 9.2, T-RUNREG-02 and -03 |
| ENG-08 | major | Accepted, in the form of Q-08. Fingerprints are computed after the display and cached by the proposed key. | 3.4, 3.17, 4.2 rows 1b and 8b, 5.4 |
| ENG-09 | major | Accepted. Ledger state per run is the prefix before its registration; reports cut the ledger by `hash_after`; registered keys are classified; combined differences have a precedence. | 3.13, 4.1, 4.3, 5.4, 7.1 |
| ENG-10 | major | Extended. Every count-changing human event (lowering or raising) needs a verified owner ruling to enter the primary reading; `tools/r3/annotate.py` writes them; the report lists them. | 4.1, 4.2 rows 8c, 14 and 15, 5.4, 7.2 G, 9.1 |
| ENG-11 | major | Changed form, merged with Q-04. ENG-11 proposed the card's `created` date as the cut. That date is written by the study and is not anchored, so it gives the secondary pre-created reading; the anchored commit gives the primary one. Sibling cards, the three readings and the POST_CARD label (ENG-11's LATER_SEARCH) are as proposed. | 6.6, 7.2, 7.3, Q21 |
| ENG-12 | major | Accepted. Questions split into A (build) and B (⑨-3d); the card name removed from Q3. | 10.2 |
| ENG-13 | major | Accepted. (a) Planned MCSE, replications never cut, cut layers inconclusive. (b) Section 8 frozen by a commit before step 6, design hash in the rulings log, refused if changed. | 8.5, 8.6, 8.8, 9.7 step 5a |
| ENG-14 | major | Accepted. The module carries its own snapshot pair; the container command is named; UI imports are lazy; 9.4 corrected. | 9.3, 9.4 |
| ENG-15 | major | Accepted. (a) Retried `os.replace` with `series_error`. (b) LF-normalised and raw hashes. (c) UNVERSIONED documented. (d) Sync-folder refusal with override. (e) No Lab use during a full suite run. | 3.3, 5.1, 5.7, 9.8, 10.1 risk 14 |
| ENG-16 | major | Accepted. Outage file outside the chain; error-colour notice if it fails; report section G; fail-open is an owner question. | 5.2, 6.7, 7.2 G, Q16 |
| ENG-17 | minor | Accepted, merged with Q-15; both "too few sessions" sites listed. | 4.2 rows 3 and 4, 5.8 |
| ENG-18 | minor | Accepted, merged with Q-20; constant columns handled; expected E-FAM availability stated. | 3.14 |
| ENG-19 | minor | Accepted. NaN-aware equality; exemptions aligned; two temporary ledgers. | 6.1, T-RUNREG-01 and -06 |
| ENG-20 | minor | Accepted, merged with Q-17. | 4.5, T-RUNREG-05 |
| ENG-21 | minor | Accepted. Allow-list raises before `exists()`, never calls the loader, uses a `BaseException` subclass, asserts one read per file; the static test builds names from fragments. | 7.4, T-RUNREG-09 and -12 |
| ENG-22 | minor | Accepted. Bytes per event estimated; verified-prefix cache; 32 MB segments. | 5.2, 5.10 |
| ENG-23 | minor | Accepted. Both readings of R3 are owner questions with the drafted defaults. | Q17, Q18 |
| ENG-24 | minor | Accepted. HOLDOUT_TOUCHED flag and report section; ⑨-3a's page edits wait for the audit's patches; a D-01 or D-02 fix is recorded as REMEASURE. | 1.5, 4.2 row 16, 7.2 H, 9.7 step 0b, Q22 |
| ENG-25 | minor | Accepted. Run-ID retry and `[0-9]`; person writer fields; `adjustment` and `status` per symbol; 34 and 16 card assertions with skip list; injected reports path with `as_of` and malformed-CSV tolerance; A8 scoped to one platform. | 5.4, 5.5, 6.7, 7.1, 8.5 A8 |

---

## References

### Repository (read on 2026-10-27 at `527cdf2`)

- `ui/strategy_lab_page.py`: families `:34-46`; `FAMILY_ID` `:50-51`; `register_trials` `:55-82`; `run_family` `:85-136`;
  `narrative` `:139-145`; `payload` `:148-155`; run worker `:227-279`; ledger chip `:254-256`; Run button `:283`;
  self-check `:320-330`.
- `core/quant/validate.py`: `GATE` `:53-74`; cost table `:78`; `cost_floor_bp` `:115-121`; `expected_max_sharpe`
  `:211-217`; `deflated_sharpe` `:220-237`; `walk_forward` session check `:366-367`; `StrategyScore` `:456-489`;
  `score_strategy` `:492-533`; `_decide_strategy` `:536-622`; `load_cards` `:847-856`.
- `core/quant/gate_ledger.py`: readings `:10-24`; row schema `:54-66`; anchors `:114-131`; `config_id` `:168-171`;
  `validate_row` `:182-214`; lock `:242-262`; `FamilyLedger` `:265-368` (`snapshot` `:323-330`; `append` `:337-355`);
  `register_trial` `:379-386`; alignment and correlation `:421-457`; clusters and E[max] `:473-557`; `n_eff`
  `:574-582`; `deflated_dsr` `:588-592`; overlap and readings `:674-686`; `t_fix` `:688-697`; `selection_factor`
  `:700-733`; forbidden patterns `:851-888`; `temp_copy` `:927-933`.
- `core/quant/gate_stats.py:590-607` (`psr`), `:741-747` (`verdict_class`); `core/quant/gate_package.py:36-38`,
  `:241-255`; `core/quant/strategies.py:51-66`, `:69-90`, `:330-367`, `:379-389`; `core/quant/history.py:55-68`,
  `:464-511`; `core/quant/cards.py:526-539`; `core/quant/tf_gov.py:487-523`; `core/ficc/macro_schema.py:303-311`;
  `config.py:174-178`; `.gitattributes:1-2`.
- `docs/asset_expansion_study.py`: loaders `:68-153`; `strategy_card` `:173-215`; candidates `:271-365`, `:391-445`;
  `CANDIDATES` `:723-758`; `write_results` `:764-817`; `REFRESH` `:844`.
- `docs/asset_expansion/cards/*.json` (34 files; 16 with a DSR); commit `eacd57d` (the baseline that added them).
- `docs/techfund_study.py:83-85`.
- `tests/macro_acceptance.py:26-27`, `:101-153`, `:198-295`; `tests/macro_m0_harness.py:22`, `:229-298`;
  `tests/macro_m7_ledger.py:315-343`, `:584-593`; `tests/paper_live_acceptance.py:19-21`, `:333-359`;
  `tests/macro_ui_views.py:263-288`; `tests/expansion_acceptance.py:338`; `tests/run_all.py:93-97`, `:136-137`;
  `tests/macro_registry.csv:165`.
- `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:3-4`, `:20-47`, `:71-88`;
  `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:95-122`; `docs/audit/2026-10-27/00_request.md:20-22`;
  `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:113`, `:794-799`, `:1093-1104`.
- `research_notes/QUANTGEN run registry map/01_strategy_lab_and_cards.md`, `02_gate_ledger_semantics.md`,
  `03_effective_trials_methods.md`; `research_notes/QUANTGEN v2 integration map/code_tests_data.md:684`;
  `research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:712`.
- Reviews: `docs/superpowers/specs/2026-10-27-run-registry-review/round1_claude_quant.md` and `round1_claude_eng.md`.

### Literature

Status notes follow map03's convention. "Confirmed" means the bibliographic record was matched in a search record (by
map03 on 2026-10-27, or in this session where stated). Content statements in this spec are limited to what map03
records as confirmed; anything else is marked.

- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest
  overfitting, and non-normality. *Journal of Portfolio Management* 40(5), 94–107.
  https://doi.org/10.3905/jpm.2014.40.5.094 (confirmed, map03).
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The probability of backtest overfitting.
  *Journal of Computational Finance* 20(4), 39–69. https://doi.org/10.21314/JCF.2016.322 (confirmed, map03).
- Dwork, C., Feldman, V., Hardt, M., Pitassi, T., Reingold, O., & Roth, A. (2015). The reusable holdout: Preserving
  validity in adaptive data analysis. *Science* 349(6248), 636–638. https://doi.org/10.1126/science.aaa9375 (confirmed,
  map03).
- Gelman, A., & Loken, E. (2013). The garden of forking paths: Why multiple comparisons can be a problem, even when
  there is no "fishing expedition" or "p-hacking" and the research hypothesis was posited ahead of time. Working paper,
  Columbia University (title confirmed, map03; no URL checked: UNVERIFIED).
- Halle, K. K., Djurovic, S., Andreassen, O. A., & Langaas, M. (2016). Is the familywise error rate in genomics
  controlled by methods based on the effective number of independent tests? arXiv:1612.04535.
  https://arxiv.org/abs/1612.04535 (confirmed, map03; the quantitative referee could not reach arXiv from this
  container, so the author list is UNVERIFIED in this revision). Cited in 8.2 for the caution that effective-number
  methods need not control the familywise error rate (map03 §2.5).
- Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics* 23, 365–380
  (volume and pages confirmed in revision 1's session; the DOI 10.1198/073500105000000063 is UNVERIFIED). Out of scope
  here (10.3).
- Harvey, C. R., & Liu, Y. (2015). Backtesting. *Journal of Portfolio Management* 42(1), 13–28.
  https://doi.org/10.3905/jpm.2015.42.1.013 (confirmed, map03; one record lists 41(1)).
- López de Prado, M. (2019). A data science solution to the multiple-testing crisis in financial research. *Journal of
  Financial Data Science* 1(1), 99–110. https://doi.org/10.3905/jfds.2019.1.099 (confirmed, map03).
- López de Prado, M., & Lewis, M. J. (2019). Detection of false investment strategies using unsupervised learning
  methods. *Quantitative Finance* 19(9), 1555–1565. Record:
  https://ideas.repec.org/a/taf/quantf/v19y2019i9p1555-1565.html (confirmed in revision 1's session; the abstract
  describes an unsupervised algorithm that estimates the number of effectively uncorrelated trials). The DOI
  10.1080/14697688.2019.1622311 is UNVERIFIED.
- NumPy Enhancement Proposal 19, "Random number generator policy". https://numpy.org/neps/nep-0019-rng-policy.html
  (cited by both reviewers from memory for the claim that distribution outputs may change across NumPy versions while
  bit-generator streams are stable; not re-read in this session: UNVERIFIED). The design does not rely on it: the
  canonical panel is a stored fixture (5.4).
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *PNAS* 115(11),
  2600–2606. https://doi.org/10.1073/pnas.1708274114 (confirmed, map03; authors after Nosek UNVERIFIED).
- Rosenthal, R. (1979). The file drawer problem and tolerance for null results. *Psychological Bulletin* 86(3), 638–641.
  https://doi.org/10.1037/0033-2909.86.3.638 (confirmed, map03).
- Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: Undisclosed flexibility in data
  collection and analysis allows presenting anything as significant. *Psychological Science* 22(11), 1359–1366.
  https://doi.org/10.1177/0956797611417632 (confirmed, map03).
- White, H. (2000). A reality check for data snooping. *Econometrica* 68(5), 1097–1126.
  https://doi.org/10.1111/1468-0262.00152 (confirmed, map03). Out of scope here (10.3).
