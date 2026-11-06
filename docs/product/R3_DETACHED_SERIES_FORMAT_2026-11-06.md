# R3 in-memory series format

This bounded child encodes supplied arrays into NPY bytes and decodes supplied
bytes after format, size and content-hash verification. It implements a detached
part of R3 design §5.7, before any file store, reader path, recorder or Lab link.

Design reference: `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`
at `fa280591b9915b213a00e231a55bbe8d33b0d9d7`, §5.7. The supported profile below
is an explicit new implementation convention. It is not general support for all
NPY files or a claim of compatibility with unverified historical series files.

## API and byte limits

`core.quant.run_registry_series_format` provides:

- `encode_series(array, *, max_bytes) -> bytes`
- `decode_series(payload, expected_sha256, *, max_bytes) -> numpy.ndarray`
- `SeriesFormatError(ValueError)` for unsupported input or malformed format.

`max_bytes` is required and must be an exact plain positive integer no larger
than `numpy.iinfo(numpy.intp).max`. Bool, integer subclasses and coercible values
are refused. It limits serialized bytes, not all temporary allocations, peak
memory, CPU, parser complexity or hostile input behavior. Allocation failures
such as `MemoryError` propagate; a failed call returns no fabricated result.
Header parser recursion is a controlled format refusal, not a valid array.

The array must be an exact two-dimensional float64 ndarray with no dtype
metadata, even an empty metadata mapping. Lists, coercion objects, subclasses,
masked arrays, memmap objects and other dtypes/ranks are refused. Each dimension
must be a plain integer in `0..min(np.iinfo(np.intp).max // 8, 2**64 - 1)`.
The axis limit also applies when another axis is zero. Zero-length axes are
valid for this content identity/format, not proof of a valid stored run.

## Encoding

Before copying array content, the encoder validates types/dimensions and checks
the raw byte size using Python integer arithmetic. It prepares only a small
NPY1 header and checks header plus raw bytes against the caller's budget.

Canonicalization uses unsigned integer word views/conversion into little-endian
float64 in logical C order. It performs no floating arithmetic, rounding, finite
filtering or NaN normalization. Signed zero, infinities and distinct quiet and
signalling NaN payload bits are retained. Supported endian, C/F, reversed,
non-unit/zero-stride, read-only and valid unaligned input is not mutated.

`numpy.save` writes to an internal bounded `BytesIO` with `allow_pickle=False`.
Every write checks actual buffer bytes, including multidimensional memoryviews,
before growing the serialized buffer above the ceiling. The actual final size
and supported version/header are checked again. Exact serialized-size budgets
succeed; smaller budgets refuse. NumPy may still allocate temporary chunks or
canonical copies, so this is not a total-memory guarantee. Caller input must
remain stable during the call; no concurrent-mutation snapshot is promised.

## Decoding before array allocation

The payload must be exact plain `bytes`. The expected content digest must be an
exact plain string of 64 lowercase ASCII hexadecimal characters. Payload length
must fit the supplied budget before parsing.

The supported stored profile is NPY version 1.0, literal dtype descriptor
`'<f8'`, `fortran_order` exactly `False`, and a tuple of two plain integer axes.
NPY2/3, ZIP archives, object/pickle/structured dtypes, big-endian or alias dtype
descriptors and Fortran order are refused. There is no permissive fallback.

Before `numpy.load`, the reader checks:

1. Exact magic/version and the two-byte little-endian header-length field.
2. Header length at most 10,000 bytes and fully present in the payload.
3. Final header LF and a prefix-plus-header offset divisible by 16. The current
   writer's 64-byte alignment is also valid; 64 is not required for all accepted
   NPY1 headers. Key ordering and nonsemantic whitespace/padding may differ.
4. Bounded AST literal dictionary syntax with exactly three unique literal
   keys: `descr`, `fortran_order`, `shape`. Duplicate/extra/missing/unpacked keys
   are refused before `ast.literal_eval`. No `eval` is used. Exact field types
   reject bool axes and dtype aliases even if NumPy would normalize them.
5. Bounded axes and Python-integer `rows * columns * 8` exactly equal to the
   remaining raw bytes. Truncation, trailing garbage and concatenated arrays
   are refused before array loading, including oversized declared shapes.

Only after these checks does `numpy.load(BytesIO(...), allow_pickle=False,
max_header_size=10000)` run. The result's shape, dtype, metadata, C layout and
complete stream consumption are checked. NumPy may normalize a stored `<f8`
descriptor to native `=` on a little-endian host; the strict stored descriptor
has already been checked directly rather than inferred from that normalized
dtype. Header limits reduce parsing exposure without claiming a sandbox.

The reader recomputes the existing `series_sha256` content identity and compares
it with the supplied expected digest. Only a match is returned. The result is
read-only as a convenience: its owner can re-enable writeability. Separate calls
return independent arrays; this flag is not immutability or access control.

## Boundaries

The content digest is the existing versioned dtype/shape/raw-word recipe, not
the SHA-256 of NPY container bytes. Two accepted headers with different ordering
or padding can therefore represent the same content. Existing data/source/key/
codec/event-store helpers and their byte contracts remain unchanged.

Neither payload nor expected hash authenticates its origin or proves data
rights, prices, dates, PnL validity, configuration order or owner authority. The
helper does not pack a day column, create `series_ref`, collect data or touch
files, network, clocks, environment or configuration. Exact ndarray input also
does not prove the provenance of its backing buffer.

Filesystem persistence, fsync/replace, deduplication, existing-target integrity,
concurrent writers, retries, retention, error events, folds, counts, recorder and
Lab integration remain separate work. No actual ledger, frozen research,
holdout, preregistration, criterion, trial count, `owner_confirmed` or order path
is read, executed or changed. Parent R3 and the full series store remain open.

## Verification

`tests.run_registry_series_format_acceptance` uses independently prepared literal
NPY headers/raw bytes/content digests; those fixtures were made with stdlib only
before implementing this encoder. The suite covers exact budget boundaries,
header/type/shape refusal before `numpy.load`, raw IEEE and layout preservation,
container/content hash distinction, corruption, pickle-disabled calls, bounded
writes, parser/resource failure distinction and read-only reversibility.

An initial test tried constructing an oversized empty ndarray that NumPy itself
refuses before the encoder. That fixture error is retained in the validation
history; above-limit decoder headers and the valid encoder boundary cover the
intended cases. A long unary header was refused locally through ordinary literal
validation; explicit parser recursion injection tests that separate boundary
without claiming the long header reproduced it on every interpreter.

Exact local and hosted results belong to their reviewed-source receipts.
In-memory synthetic checks establish neither physical Windows/OneDrive behavior,
actual provider/pilot evidence, complete persistent storage nor full R3 completion.
