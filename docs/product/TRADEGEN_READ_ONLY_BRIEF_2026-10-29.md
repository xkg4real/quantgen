# ⑪-1 TRADEGEN integration brief v1

Status: QUANTGEN-side contract prepared and fixture-tested. No TRADEGEN file, environment, process or account was inspected or changed. Execution of this brief belongs to the separate TRADEGEN task after its isolation checks.

## Direction and identity
QUANTGEN → explicit `quantgen.read-only-export/1` JSON → a read-only TRADEGEN research inbox. The payload is `quantgen.research-run/1`; use `core.research.runs.read_export` as the reference validator. Envelope fields are format, audience=personal_research, order_capable=false, payload_json (canonical JSON text) and payload_sha256 (the UTF-8 payload_json bytes). This explicit text representation avoids cross-language float serialization ambiguity. Unknown versions, unexpected fields, duplicate JSON keys, non-finite metrics, invalid timestamps and checksum mismatches are refused. SHA256 detects accidental change, not authenticity; accept files only through an authenticated owner-controlled channel.

The prototype supports Monte Carlo observations, not a strategy or order contract. Provider+symbol remain observational identifiers; canonical execution instrument/venue/cost mapping is NOT_VERIFIED until PR-B is approved and implemented. No automatic conversion to tradable assets. COMPLETED means the computation finished, NOT_RUN means no formal investment gate was evaluated, and SYNTHETIC describes inputs. These fields cannot authorize live trading.

## Isolation prerequisites before any TRADEGEN execution
Use its own venv and state roots: macro/trading/runs/FICC cache, token/DART paths and any study data. No QUANTGEN actual ledger reads/writes through a shared root. No frozen/preregistered/holdout readouts or forward looks. The consumer must reject duplicate (run_id, payload_sha256) and flag conflicting hashes for the same run_id, maintain its own import receipt, and never update producer history. Missing/unsupported evidence remains unavailable; do not fill an assumed PASS. Import parser must not evaluate code, follow filesystem references or execute a model.

## Feedback control (R2)
TRADEGEN → separate observational report → owner/research review. Reports include strategy/version, time window, fees/slippage assumptions, observed data timestamps, deviations and uncertainty. Exclude account/credential identifiers. Feedback is not an instruction channel and cannot write into QUANTGEN trial ledgers. A proposed model change becomes a new preregistered experiment with a new ID and untouched future evidence; no tuning on the already-consumed frozen holdout and no rewriting earlier judgments.

## Moonshot isolation (R4)
Moonshot remains outside QUANTGEN, in a separately isolated TRADEGEN study with its own ledger, preregistration, lawful venue and the previously agreed $30 loss cap. This brief neither implements orders nor enables the study. Its admissibility, risk enforcement and owner-scope checks belong to that separate execution task.

## Consumer acceptance cases
Valid synthetic observation imports as research-only; tampered checksum rejected; duplicate ID/hash idempotent; same ID/different hash flagged; unknown version rejected; RUNNING/FAILED remain non-completed; NOT_RUN/REJECT never shown as approved; no raw path/code/order execution; no producer writes; no credentials exported. Current Python tests cover producer/roundtrip/parser integrity. Consumer isolation, dedup storage and deployment are NOT_RUN because TRADEGEN was not modified.
