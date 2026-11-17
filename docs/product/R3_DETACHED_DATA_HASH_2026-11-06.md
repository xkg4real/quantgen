# Detached R3 supplied-panel data hash

Bounded child **⑨-3a/data-hash/1** implements the data MD5 recipe in the approved
R3 revision 2, section 5.4 (line 719 at
`fa280591b9915b213a00e231a55bbe8d33b0d9d7`). It is a standalone function,
`core.quant.run_registry_data_hash.data_md5(dates, symbols, closes)`.

The exact preimage is UTF-8 dates joined by LF, one NUL byte, UTF-8 symbols joined
by LF, one NUL byte, then the close matrix's little-endian float64 raw bytes in
C order. There is no additional dtype/shape header, JSON, provider metadata,
trailing LF or file header. The result is lowercase MD5, a compatibility
fingerprint rather than authentication or proof of semantic price equality.

The supported input domain is deliberately narrower than arbitrary Python data:

- Dates and symbols must be nonempty ordinary lists/tuples of plain strings.
  Dates must be valid ASCII `YYYY-MM-DD` calendar strings. This only validates
  their representation; it does not verify trading days, sessions, provenance,
  an observation period or a holdout. Date order and duplicates are preserved.
- Symbols remain literal, including case, spaces, CR and Unicode codepoints.
  Empty strings, LF/NUL delimiters and text that cannot encode as strict UTF-8
  are refused. There is no trimming, sorting, deduplication, Unicode normalization
  or instrument/provider/market lookup.
- `closes` must have exact type `numpy.ndarray`, two dimensions, float64 dtype
  and shape `(len(dates), len(symbols))`. Empty axes, other numeric types,
  object/structured/complex arrays, subclasses, masked arrays and memmaps are
  refused rather than cast or filled. These are implementation input bounds,
  not new research criteria or price-validity rules.
- Either endian, C/F order, arbitrary strides and read-only arrays are supported.
  Integer views perform endian conversion without floating-point arithmetic, so
  signed zero, infinities and NaN payload/signalling bits remain part of the
  fingerprint. Nonfinite bits are not replaced with null and prices are not
  rounded or repaired. Equal numeric-looking values need not have equal raw bits.

The helper does not mutate inputs. Callers must keep them stable during the
call; no coherent snapshot under concurrent mutation is promised. Its code does
not read files, use a clock, consult config/environment, load providers, align a
panel or initiate any run, storage, ledger, key registration or trial count.
Existing source functions, gates, research criteria, approval rules and Lab/UI
calls remain unchanged.

Acceptance uses invented labels and arrays only, with independently prepared
literal preimages/digests, endian/layout/stride and raw IEEE cases, malformed
input refusals and nonmutation/no-I/O checks. The maintained module passed
**15 guarded tests in 0.013 seconds, exit 0**. Independent implementation probes
passed **10 tests in 0.009 seconds, exit 0**, including separate literal bytes
and signalling/quiet NaN payloads under NumPy floating-error refusal. These
overlapping checks are separate results, not an aggregate test count.

The combined guarded check of data hash, keys, store and codec passed **61 tests
in 1.382 seconds, exit 0**; it includes those same 15 maintained data-hash tests.
Any memmap refusal fixture is created only in an isolated temporary directory.
Local runtime evidence is Linux. Exact-head Windows/Ubuntu Runtime and Compliance
must succeed before merge; physical Windows acceptance and scientific evidence
are not established by these synthetic checks.

This is not the series-store SHA-256 framing contract, a recorder, lifecycle
fold, complete payload validator, data-rights check or completion of parent
⑨-3a/full R3. Physical Windows/API/provider/legal/license/pilot and frozen
research evidence remain separate. Publication remains BLOCKED; optional
additional GPT/Gemini spec review remains NOT_PERFORMED.
