# Integration PR 1 (claude/integration-20261124 @ 3e2af60) — independent review, 2026-11-24

Five reviewers (DIDM, data sourcing, OS and payments, main documents, policy impact). Sections are added as each reviewer finishes. Paths are relative to the repository root. This file records findings and their outcome; fixes come as commits on the owning session's branch.

## DIDM (merge of claude/didm-dev-20261124 @ 3626913) — reviewer findings, 2026-11-24

Status: reviewer findings, not yet verified by a second reader. The code owner fixes each one or refutes it with evidence.

| ID | Severity | File:line | Claim |
|---|---|---|---|
| DIDM-CUT-1 | major | `core/didm/llm/cutoffs.py:148` | Eligibility is decided from received_at alone, so a backfilled old article counts as eligible for a model whose training data covers it. |
| DIDM-TEST-1 | major | `tests/didm_contract_acceptance.py:200` | No test checks what assemble_record writes into the record beyond ESS, entropy, novelty_0_100 and model_version, so the field-origin rule of the contract can be broken with every test green. |
| DIDM-CI-1 | major | `docs/compliance/source-review.json:100` | The compliance baseline has no entries for the six new DIDM source files and is stale for 18 other files of this branch, so the compliance check fails. |
| DIDM-JUD-1 | minor | `core/didm/llm/judgement.py:195` | A probability given as a very large integer raises OverflowError instead of JudgementError, and run_scorer then aborts the whole batch. |
| DIDM-JUD-2 | minor | `core/didm/llm/judgement.py:165` | validate_judgement accepts direction_probs that the record schema rejects, so a judgement counted as valid cannot be assembled. |
| DIDM-SCO-1 | minor | `core/didm/llm/scorer.py:185` | Reject reasons carry model output verbatim, against the 'no article text' comment at line 166 and SCORER_CONTRACT_V0.md line 27, and they split reject_counts. |
| DIDM-SCO-2 | minor | `core/didm/llm/scorer.py:113` | assemble_record cannot detect a judgement joined to another article's DIDM-side values, and the request check is optional, so a model-chosen entity can reach a record. |
| DIDM-TEST-2 | minor | `tests/didm_cutoffs_acceptance.py:179` | The 'no network or clock' tests miss ordinary import forms. |
| DIDM-CUT-2 | minor | `core/didm/llm/cutoffs.py:155` | Any card labelled Rule.BASELINE is eligible for every date once it is pinned. The code does not limit the rule to the two baselines PREREG 5.4 names, and it ignores a cutoff on such a card. |
| DIDM-SCH-1 | minor | `tools/didm/export_schema.py:28` | The exported patterns copy regexes that the Python validator applies with fullmatch. A Python JSON Schema validator applies them with search, where '$' also matches before a final newline. |
| DIDM-TEST-3 | minor | `tests/didm_contract_acceptance.py:95` | Three judgement rules have no test that fails when they are removed or loosened, and the schema text does not follow the tolerance in the code. |
| DIDM-JUD-3 | nit | `core/didm/llm/judgement.py:158` | A key that is not the most probable is accepted as event_type when it is within 1e-6 of the top probability. |
| DIDM-TEST-4 | nit | `tests/didm_contract_acceptance.py:105` | Two tests check less than their names say, and export_schema.check() has a branch that can never report anything. |

### DIDM-CUT-1 (major) — `core/didm/llm/cutoffs.py:148`

- Claim: Eligibility is decided from received_at alone, so a backfilled old article counts as eligible for a model whose training data covers it.
- Scenario: A record with published_at 2020-03-02T13:00Z and received_at 2026-11-24T03:00Z (fetched today, which is what received_at means in core/didm/ingest/* and in PREREG_V0.md line 92), model_version claude-fable-5-2 (cutoff 2026-06-30, eligible from 2026-09-30). The call shown in docs/didm/MODEL_CUTOFFS.md line 44, REGISTRY.eligibility("claude-fable-5-2", record.received_at), is made.
- Evidence: Ran in a copy: validate_record accepts the record; eligibility on received_at returns Eligibility(eligible=True, 'received on or after cutoff + 3 months'); the same call on published_at returns eligible=False. PREREG line 92 says a backfill's received_at is today and historical studies use published_at + a fixed delay; line 96 allows only articles after cutoff + 3 months. The month arithmetic itself is correct. No caller exists yet (git grep), so no stored result is wrong today.
- Proposed fix: Make eligibility() take both published_at and received_at (or the PREREG 5.1 as-of time) and compare the earlier day with cutoff + 3 months. Add the backfill case to tests/didm_cutoffs_acceptance.py. Reword MODEL_CUTOFFS.md rule 2 (line 10) and the usage example (line 44).

### DIDM-TEST-1 (major) — `tests/didm_contract_acceptance.py:200`

- Claim: No test checks what assemble_record writes into the record beyond ESS, entropy, novelty_0_100 and model_version, so the field-origin rule of the contract can be broken with every test green.
- Scenario: One-line changes to assemble_record in core/didm/llm/scorer.py, each in a fresh copy: (a) event_type='none' for every record; (b) target_kind='none' and entity_id=None; (c) raw['relevance_0_100'] = 100 * judgement.p_subject, i.e. the model fills a DIDM-side field; (d) raw['origin_cluster_id'] = judgement.article_id; (e) prompt_sha256='0'*64.
- Evidence: After each of the five changes tests.didm_contract_acceptance (30), tests.didm_cutoffs_acceptance (19) and tests.didm_schema_acceptance (26) all pass. test_every_accept_example_yields_a_valid_record (line 86) only checks that the record validates; FieldSplit (line 169) compares constant tuples, not behaviour; the fixtures use a prompt_sha256 of 64 zeros. The shipped code itself does take these fields from the right place (read and probed).
- Proposed fix: Put the expected record in each tests/fixtures/didm/conformance/accept/judgement-*.json and assert assemble(case).record.as_dict() equals it. Use a non-zero prompt hash in the fixtures. Add a test that changing p_subject or claim_status leaves all nine ASSEMBLY_FIELDS unchanged.

### DIDM-CI-1 (major) — `docs/compliance/source-review.json:100`

- Claim: The compliance baseline has no entries for the six new DIDM source files and is stale for 18 other files of this branch, so the compliance check fails.
- Scenario: python -m tools.compliance.check --check --report-dir <dir> at HEAD 3e2af60. This is the step 'Check source and document review fingerprints' of .github/workflows/compliance-review.yml, which runs on pull_request.
- Evidence: In the copy: exit code 1, consistency_status FAIL, 'documents need review: 1, 2, ... 20'. report.json lists 24 changed sources, all changed by this branch, among them added core/didm/llm/cutoffs.py, judgement.py, scorer.py, tests/didm_contract_acceptance.py, tests/didm_cutoffs_acceptance.py and tools/didm/export_schema.py. The baseline file is identical to origin/main. This is branch-wide, not caused by the DIDM merge alone.
- Proposed fix: Refresh docs/compliance/source-review.json with the refresh command of tools.compliance.check (reviewer and note) as the last commit of the branch, after the review fixes are in.

### DIDM-JUD-1 (minor) — `core/didm/llm/judgement.py:195`

- Claim: A probability given as a very large integer raises OverflowError instead of JudgementError, and run_scorer then aborts the whole batch.
- Scenario: A scorer returns the judgement-macro example with "p_subject": 10**400 (json.loads of a 401-digit integer literal gives an int). The same happens for an entry of direction_probs or event_type_probs.
- Evidence: validate_judgement raises OverflowError 'int too large to convert to float' (from float(value) in schema._num, line 279, which is frozen). run_scorer propagates it because it catches only SchemaError (scorer.py line 184), so the judgements already kept in that batch are lost. assemble_record with Assembly(relevance_0_100=10**400) also raises OverflowError; scorer._checked_probs (math.isfinite, line 194) has the same weakness by reading.
- Proposed fix: schema.py is frozen, so catch OverflowError in judgement._wrap and re-raise JudgementError('... must be finite'). Do the same in scorer._checked_probs and around validate_record in assemble_record. Add a reject fixture.

### DIDM-JUD-2 (minor) — `core/didm/llm/judgement.py:165`

- Claim: validate_judgement accepts direction_probs that the record schema rejects, so a judgement counted as valid cannot be assembled.
- Scenario: direction_probs [0.5000004, 0.5000004, 0.0] (sum 1.0000008, inside the 1e-6 tolerance).
- Evidence: validate_judgement accepts it and run_scorer keeps it. assemble_record then raises SchemaError 'p_positive + p_negative exceeds 1', because schema.ess_like allows only 1e-9 on P(+1)+P(-1) (scorer.py line 148). The item is not in Batch.rejected, so the reject counts miss it and the caller gets an exception at assembly time.
- Proposed fix: In validate_judgement also call ess_like(direction[0], direction[1]) (or require P(+1)+P(-1) <= 1 + 1e-9) so the judgement is rejected and counted. Add the case to the reject fixtures and to x-didm-cross-field-rules.

### DIDM-SCO-1 (minor) — `core/didm/llm/scorer.py:185`

- Claim: Reject reasons carry model output verbatim, against the 'no article text' comment at line 166 and SCORER_CONTRACT_V0.md line 27, and they split reject_counts.
- Scenario: A scorer returns event_type set to a sentence copied from the article, or an unknown key whose name is free text.
- Evidence: batch.rejected == (('art-0001', "unknown event_type: 'FULL ARTICLE TEXT FULL ARTICLE TEXT ...'"),) and "unknown judgement fields: ['some long model text key ...']". reject_counts gets one key per distinct value.
- Proposed fix: Store a fixed reason per rule in Batch.rejected (for example 'unknown event_type', 'unknown judgement fields') and keep the offending value out, or truncate and clean it. Test that a long value does not appear in rejected.

### DIDM-SCO-2 (minor) — `core/didm/llm/scorer.py:113`

- Claim: assemble_record cannot detect a judgement joined to another article's DIDM-side values, and the request check is optional, so a model-chosen entity can reach a record.
- Scenario: (a) The judgement for art-0002 / KR:005930 is assembled with the Assembly built for art-0001 / US.FFR (record conf-j-0001). (b) validate_judgement(raw) is called without a request, and the model answered entity_id 'AAPL.US' to a US.FFR request.
- Evidence: (a) returns a valid record conf-j-0001 with entity KR:005930 and the other pair's relevance 88.0. (b) returns a record with entity_id AAPL.US. Assembly has no article or target field, and request defaults to None in validate_judgement (judgement.py line 131). The tests themselves assemble judgements validated without a request (tests/didm_contract_acceptance.py lines 223, 232, 241).
- Proposed fix: Give Assembly article_id, target_kind and entity_id (or pass the ScoreRequest to assemble_record) and reject a mismatch. Make request mandatory in validate_judgement, or mark a Judgement as request-checked and require that mark in assemble_record.

### DIDM-TEST-2 (minor) — `tests/didm_cutoffs_acceptance.py:179`

- Claim: The 'no network or clock' tests miss ordinary import forms.
- Scenario: Add to core/didm/llm/cutoffs.py: 'from urllib.request import urlopen', or 'import http.client', or 'from data import didm'. Add to core/didm/llm/scorer.py: 'from datetime import datetime, timezone' and '_STARTED = datetime.now(timezone.utc)'.
- Evidence: All four changed copies pass every DIDM test. The cutoffs test searches the unparsed source for substrings ('import urllib', 'data.didm', '.now('). The contract test (tests/didm_contract_acceptance.py line 334) bans the module 'time' only and does not list cutoffs.py. tests/gateway_boundary_acceptance.py covers data.didm in core (not run against the changed copy), but its provider list has no urllib, http or socket.
- Proposed fix: Add core/didm/llm/cutoffs.py to FILES of the contract test and drop the substring check. Add an AST check for calls of now, today and utcnow on all three files.

### DIDM-CUT-2 (minor) — `core/didm/llm/cutoffs.py:155`

- Claim: Any card labelled Rule.BASELINE is eligible for every date once it is pinned. The code does not limit the rule to the two baselines PREREG 5.4 names, and it ignores a cutoff on such a card.
- Scenario: ModelCard(key='any-llm-2030', family='x', rule=Rule.BASELINE, snapshot_id='s', source_url='https://example.org/x', checked_on=date(2026,11,24), cutoff=date(2030,1,1)).
- Evidence: eligibility(card, date(2015,1,2)) returns eligible=True with reason 'baseline named in PREREG_V0 5.4'. Registry.with_card accepts such a card. Nothing in the shipped REGISTRY uses this: its two BASELINE rows are unverified.
- Proposed fix: Keep an explicit set of baseline keys (loughran-mcdonald, ProsusAI/finbert) and treat any other BASELINE card as not verified. Add a test.

### DIDM-SCH-1 (minor) — `tools/didm/export_schema.py:28`

- Claim: The exported patterns copy regexes that the Python validator applies with fullmatch. A Python JSON Schema validator applies them with search, where '$' also matches before a final newline.
- Scenario: record_id 'conf-r-0001\n' in an otherwise valid record. The same holds for article_id, entity_id, source_id, origin_cluster_id and prompt_sha256 with a trailing newline.
- Evidence: validate_record rejects it ('record_id must be an identifier string'). jsonschema.Draft202012Validator with docs/didm/schema/didm-score-v0.schema.json accepts it. An ECMA-262 regex engine should reject it (unverified here). The test's own small validator also uses re.search (tests/didm_contract_acceptance.py line 49), so the test cannot see this.
- Proposed fix: Export the patterns with an end that is strict in both dialects (for example add '(?!\n)' after '$'). Add a trailing-newline reject fixture with json_schema_detects true.

### DIDM-TEST-3 (minor) — `tests/didm_contract_acceptance.py:95`

- Claim: Three judgement rules have no test that fails when they are removed or loosened, and the schema text does not follow the tolerance in the code.
- Scenario: In copies: SUM_TOLERANCE = 1e-2 (or 1e-3) in judgement.py; the request check reduced to 'if entity != request.entity_id' so a target_kind mismatch is no longer rejected; validate_request no longer rejects an entity_name when target_kind is none.
- Evidence: All 75 DIDM tests pass in each case. With the changed tolerance, 'python -m tools.didm.export_schema --check' still prints OK, although both schema files say 'within 1e-6'; that text is hard-coded in export_schema.py (lines 86-88 and 131-135). The reject fixtures miss a sum of 1 by 0.1 or more.
- Proposed fix: Add boundary fixtures (sum off by 2e-6 rejected, by 5e-7 accepted), a reject fixture with the request's entity but another target_kind, and a request case with target none and a name. Build the x-didm rule text from SUM_TOLERANCE.

### DIDM-JUD-3 (nit) — `core/didm/llm/judgement.py:158`

- Claim: A key that is not the most probable is accepted as event_type when it is within 1e-6 of the top probability.
- Scenario: event_type 'inflation' with event_type_probs inflation 0.4999996 and monetary_policy 0.5000004, all other keys 0.
- Evidence: validate_judgement accepts it; with a gap of 2e-6 it rejects. SCORER_CONTRACT_V0.md line 39 and the schema text say the most probable key, with a free choice only on a tie. Comparing two parsed numbers needs no tolerance. Exact ties (0.5/0.5 and three keys at 1/3) are accepted for any tied key, as documented.
- Proposed fix: Compare without tolerance ('< top'), or state the 1e-6 tie width in the contract document and in the schema text.

### DIDM-TEST-4 (nit) — `tests/didm_contract_acceptance.py:105`

- Claim: Two tests check less than their names say, and export_schema.check() has a branch that can never report anything.
- Scenario: test_reject_examples_fail_for_one_reason_only asserts only that at least 25 distinct 'expect' strings exist. test_examples_contain_no_secret_looking_or_long_text (line 110) checks only the length of request title/body and the word 'Synthetic' or '합성'. tools/didm/export_schema.py lines 167-172 run only after the file text equals the generated text.
- Evidence: By reading. The enum and required comparison in check() cannot differ once the text is equal. My own diff of the fixtures shows every reject example is in fact one change away from an accept example, so the fixtures are sound today.
- Proposed fix: Rename the tests or implement the claim (diff each reject example against its base accept example and assert one changed leaf). Remove the dead branch in check().

### Checked and found correct

- core/didm/llm/schema.py and docs/didm/PREREG_V0.md are identical to origin/main (git diff --quiet). On the whole branch core/engine, qa/acceptance_results.json, quantgen_desktop, ui and tests/desktop_* are unchanged.
- The DIDM merge 55ae24f adds 54 files, all DIDM (3 modules in core/didm/llm, tools/didm/export_schema.py, 2 docs, 2 JSON Schemas, 2 tests, 44 fixtures); no owner_confirmed or host_fingerprint writes; no IP address, key or account pattern in the new files.
- Tests run in a copy with Python 3.13: tests.didm_contract_acceptance 30 OK, tests.didm_cutoffs_acceptance 19 OK, tests.didm_schema_acceptance 26 OK, tests.gateway_boundary_acceptance 15 OK. The 75 DIDM tests also pass on Python 3.11 and 3.12. The contract document's count (56 = 30 + 26) and fixture counts (accept 10 = 6 records + 4 judgements, reject 34 = 19 + 15) match.
- Judgement validation rejects: each of the 9 fields missing, unknown fields (also non-string keys), wrong version, non-mapping input, bool/string/None numbers, NaN and +-inf, out-of-range values, direction_probs of wrong type or length, sums off by more than 1e-6, missing or unknown event_type_probs keys, event_type that is not the top key, p_subject above 0 with no target, article or target different from the request. Exact ties accept any tied key.
- Record assembly: the result always passes through validate_record (removing that call fails 8 tests); bad DIDM-side values, bad calibrator output, a calibrator without a version and a version without a calibrator are rejected; raw direction probabilities, p_subject and claim_status are kept beside the record. In the code no ASSEMBLY field is taken from the judgement.
- Cutoff arithmetic: 2023-12-31 -> 2024-03-31 (2024-03-30 not eligible, 2024-03-31 eligible); 2023-11-30 -> 2024-02-29; 2022-11-30 -> 2023-02-28; 2024-11-29 and 2024-11-30 -> 2025-02-28; 2024-02-29 -> 2024-05-29; month-only '2024-02' -> 2024-02-29, '2100-02' -> 2100-02-28, '2026-06' -> 2026-06-30 -> 2026-09-30. The UTC day is used; a naive datetime and a string are refused.
- Unknown cutoff, missing snapshot, source or check date, and a model outside the registry are never eligible. In-house model: cutoff is the later of base and fine-tune day; either part unknown or an unverified base gives not eligible. This matches PREREG_V0.md lines 93-97 (the code is stricter than line 97 for name-masked prompts, which it does not model).
- MODEL_CUTOFFS.md table equals REGISTRY (9 rows, same order; changing the Claude cutoff or filling a baseline row in code fails the table test). The source page for the four Claude rows was fetched on 2026-11-24: Training data cutoff 'Jun 2026' and Reliable knowledge cutoff 'Jun 2026' for claude-fable-5-2, claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5, and the pinned-snapshot sentence, as the document quotes.
- export_schema --check compares with the code: exit code 1 after adding or renaming an EventType, renaming a MarketConfirmation value, adding a claim status, changing the ID pattern, reordering ASSEMBLY_FIELDS, adding a judgement field, and after hand-editing either JSON file. Both schema files are valid Draft 2020-12 (python-jsonschema check_schema), and a real validator agrees with the json_schema_detects flag of all 34 reject examples and accepts all 10 accept examples.
- Mutation runs in fresh copies: 73 distinct one-change mutants, 57 failed at least one test, 16 survived. Survivors are reported in DIDM-TEST-1, DIDM-TEST-2, DIDM-TEST-3; one more is equivalent (the sum check in _checked_probs is repeated by entropy()). Harness and probes: <scratch> (mutate.py, muts1.py to muts4.py, probe1.py to probe4.py).
- No network or model download: the three new core modules and export_schema.py import only the standard library and core.didm.llm; no data.didm import anywhere in core/didm/llm; the 75 tests run in under 0.2 s offline.
- CI: tests.didm_contract_acceptance and tests.didm_cutoffs_acceptance are on the unittest line of .github/workflows/runtime-smoke.yml (line 98), next to tests.didm_schema_acceptance; the sparse checkout there does not exclude docs/didm or tests/fixtures/didm.
- UNVERIFIED: Python 3.10 and 3.14 and Windows (not installed here; CI uses 3.11, 3.12 and 3.14 on Windows and Ubuntu). JSON Schema 'format: date-time' with format assertion switched on (no RFC 3339 checker installed). Behaviour of the exported patterns in an ECMA-262 regex engine. Whether the compliance-review workflow is a required check for merging.
