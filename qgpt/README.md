# QuantGPT (`qgpt/`)

One open-weight language model wrapped in five fixed parts: an evidence store (RAG), calls to the host's
calculation engine, output contracts, a policy filter, and an evaluation harness. Nothing here trains a
model from scratch, and nothing here can place, draft or signal an order.

This directory is laid out as the root of a separate repository and is moved there later. It imports
nothing from the rest of this repository at run time; the standard library and `requests` are the only
runtime dependencies. Model weights and adapters are never committed.

| Path | What it holds |
| --- | --- |
| `quantgpt/envelope.py` | the common output envelope `qgpt-env-v1` |
| `quantgpt/router.py` | task code -> contract; requests without a task code are refused |
| `quantgpt/pipeline.py` | one request -> one envelope (admit, generate, contract, policy, numbers, citations, look-ahead) |
| `quantgpt/contracts/` | input/output contracts for the seven task types, strategy card QSS v0 |
| `quantgpt/policy/` | policy filter (blocks in `tool` mode, records only in `owner` mode) |
| `quantgpt/rag/` | evidence store and `as_of` filter |
| `quantgpt/tools/` | host tool protocol (calculation and stored cards only) |
| `quantgpt/backends/` | model backends (fake backend for tests first) |
| `quantgpt/checks/` | number, citation, schema and look-ahead checks |
| `quantgpt/registry/` | append-only attempt ledger |
| `eval/`, `train/`, `deploy/` | harness, adaptation and device export (empty for now) |

Tests need no network and no GPU:

```
cd qgpt && python -B -m unittest discover -s tests
```
