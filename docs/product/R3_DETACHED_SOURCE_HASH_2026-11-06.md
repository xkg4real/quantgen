# R3 supplied-source hashes

This bounded child implements the raw/LF SHA-256 operation in R3 design §3.3. It accepts source content already supplied by a caller. It does not inspect functions, open source files, collect repository metadata, combine code identity, or connect to a run registry.

Design reference: `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md` at `fa280591b9915b213a00e231a55bbe8d33b0d9d7`, §3.3. This is the supplied-content primitive from that design, not completion of the full source collector or R3 parent.

## API and exact bytes

`core.quant.run_registry_source_hash` provides:

- `source_text_hashes(source: str) -> dict[str, str]`: accepts an exact plain string and encodes it as strict UTF-8. Unpaired surrogates are refused.
- `source_bytes_hashes(source: bytes) -> dict[str, str]`: accepts exact plain bytes, including invalid UTF-8 and NUL. No decoding or encoding detection occurs.
- `SourceHashError(ValueError)`: reports input outside these supported types or text that cannot encode as strict UTF-8.

Each call returns a fresh dictionary with exactly `lf` and `raw`, each a lowercase 64-character SHA-256 hexadecimal digest. Empty input is valid. Subclasses, bytearrays, memoryviews, paths, streams and objects with conversion methods are refused without coercion. These are explicit API restrictions, not new research criteria.

The raw preimage is the original supplied bytes, or the supplied text encoded as UTF-8. The LF preimage replaces each original `CRLF` pair with `LF` in one pass. Original lone `CR` characters remain. In particular, `CR CR LF` becomes `CR LF`, not `LF`: normalization is not repeated until stable, and it is not a general newline conversion.

No stripping, dedenting, trailing-newline insertion, BOM removal, Unicode normalization, parsing or AST normalization occurs. Indentation, trailing spaces, lone CR, Unicode line separators, Unicode composition and final-newline presence therefore remain significant. The two digests can differ for CRLF content. The single-pass transformation is deliberately not idempotent for overlapping `CR CR LF` input.

## Boundaries

The helper itself performs no file, network, environment, configuration, clock, source-inspection or git operations. Inputs are immutable and retained unchanged. Returned dictionaries can be changed by their caller without affecting later results. Resource limits for very large supplied inputs remain the caller's responsibility; this is not a sandbox or streaming collector.

A SHA-256 value records the supplied content under this byte recipe. It does not prove origin, authorship, licence, authenticity, complete strategy-code coverage or semantic equivalence. The helper does not determine whether the supplied source is permitted to disclose; it does not log or persist either content or digests. No collector, `fn_source_sha256`/file-metadata integration, provider verification, actual ledger, frozen research, owner approval, holdout, criterion or trading path is changed.

## Verification

The maintained synthetic suite is `tests.run_registry_source_hash_acceptance`. Literal Unicode/BOM, opaque binary and overlapping-CRLF preimages and expected hashes were prepared independently of the helper. The suite also checks type and surrogate refusals, formatting distinctions, fresh results, unchanged inputs and execution with I/O/discovery functions blocked.

Local and hosted verification results are recorded with the reviewed commit in the implementation evidence. A synthetic helper test does not establish physical Windows app, provider, pilot or full R3 completion evidence.
