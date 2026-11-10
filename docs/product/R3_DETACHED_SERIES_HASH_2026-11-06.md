# R3 supplied-array series digest

This bounded child provides a pure content SHA-256 for an already supplied
two-dimensional float64 array. It supports the dtype/shape/raw-array identity
part of R3 design §5.7. It does not implement the series file store, reader,
`series_ref`, recorder, Lab integration, fold, counts or the R3 parent.

Design reference: `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`
at `fa280591b9915b213a00e231a55bbe8d33b0d9d7`, §5.7. The design specifies the
ingredients but not their byte framing. The v1 framing below is a new explicit
engineering convention, not a claim of historical persisted-byte compatibility.

## API and exact v1 bytes

`core.quant.run_registry_series_hash` provides
`series_sha256(array: numpy.ndarray) -> str` and `SeriesHashError(ValueError)`.
The return is a lowercase 64-character SHA-256 hexadecimal digest of exactly:

```text
b"quantgen.r3.series/1\x00<f8\x00"
+ rows encoded as eight unsigned little-endian bytes
+ columns encoded as eight unsigned little-endian bytes
+ raw float64 words in canonical little-endian, logical C index order
```

The header is 25 bytes; the two dimensions bring the fixed framing to 41 bytes.
The dtype token is literal `<f8`, not the platform's dtype string or Python repr.
Two dimensions are implicit in this v1 input contract. There is no additional
delimiter, newline, JSON, file header, timestamp, label, path or metadata.
Different shapes remain distinct even when their flat raw bytes are identical.
The digest is of canonical array content, not `.npy` or other container bytes.

## Supported input and preservation

Only an exact `numpy.ndarray` with two dimensions, float64 dtype and no dtype
metadata is accepted. Metadata is refused even if its mapping is empty. Lists,
coercion objects, ndarray subclasses, masked arrays, memmap objects and other
dtypes/ranks are refused instead of cast. These are API-domain restrictions,
not research criteria. There is no implicit price/date/PnL conversion.

Both endian float64 inputs and C/F, read-only, reversed, non-unit, zero-stride
and valid unaligned arrays are supported. An unsigned integer view/conversion
changes only byte order. Signed zero, infinities and individual quiet/signalling
NaN payloads retain their IEEE bits; no rounding, finite-value filtering or NaN
normalization occurs. Logical row/column order is preserved.

Zero-length axes are allowed as array identity and remain shape-distinct. That
does not make an empty matrix a valid stored series or completed run. This
helper neither packs a day column nor checks calendar dates, configuration IDs,
labels, column meaning, prices or scientific validity. A later storage/packing
contract must specify those separately.

Input bytes, dtype, shape, strides and writeability are not mutated. The caller
must keep input stable during the call. There is no concurrent-write snapshot,
memory-budget or hostile-buffer guarantee; an exact ndarray type does not prove
its backing-buffer origin. The helper opens no files and performs no network,
clock, configuration or environment lookup. It does not persist data or hashes.

## Boundaries and future integration

A later writer/reader must explicitly adopt the same framing before producing
or checking persistent series names. This child migrates no existing file and
claims no compatibility with an unverified older `series_ref` implementation.
It leaves the distinct §5.4 `data_md5`, source hashes, planned keys, codec and
single-segment event store unchanged.

SHA-256 content identity alone proves no author, owner permission, source rights,
provider accuracy, date chronology, prices or research validity. A party can
replace both data and its unanchored hash. No actual ledger, research artifact,
holdout, preregistration, frozen study, criterion, trial count, `owner_confirmed`
or order path is accessed or changed.

File storage and rehash-on-read, pickle refusal, atomic writes, deduplication,
corrupt-target refusal, retries, error events and lifecycle remain separate
work. This helper does not establish those behaviors or Windows/sync durability.

## Verification

The maintained synthetic suite is `tests.run_registry_series_hash_acceptance`.
Literal full preimages and expected hashes were prepared with stdlib SHA-256
before implementation, without importing NumPy or the product helper. Coverage
includes exact framing, shape and empty-axis distinctions, endian/layout/stride
equivalence, IEEE raw bits, strict refusals, unchanged inputs and scoped
I/O/configuration/clock guards.

Local and hosted outcomes belong to their exact reviewed source receipts.
Synthetic helper checks are not actual provider, physical Windows app, pilot,
complete storage, research acceptance or full R3 completion evidence.
