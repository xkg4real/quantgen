# NEW-M6-18 — keep account holdings out of AI commentary

At product main `51bac97366ddac5e063bb6a5f9174e9d05e18be3`, the shared Crypto
payload still copied Upbit account holdings into the browser's AI request.
The native Qt report preview already removed these fields, but this did not
protect Flet or callers of the shared HTTP function.

The approved §10 correction removes holdings from the Crypto commentary payload,
filters known private structured field names at the Flet request and final HTTP
serialization boundaries, and reuses that filter in the existing native preview.
Market calculations and their verdicts remain intact. The local read-only
holdings display keeps its original data. Flet now states the external service
and the account-data exclusion next to the explicit Deep analysis action.

Validation uses invented holdings and an injected HTTP transport. The original
Crypto payload and Flet request reproduced the exposure; a separately corrected
HTTP test fixture also failed on the old code. All three regressions pass after
the change, together with five existing native commentary tests. No real account,
API key or provider request was used. The full bounded packaging/native workflow
will validate the exact PR head on Windows and Ubuntu.

This filter classifies structured field names; it is not a detector for private
details typed into an arbitrary question. Source arrays/metrics, model equations,
stored cards, gates and approval rules are unchanged. It does not resolve the
separate AI truncation/non-finite serialization findings or validate live AI text.

This is the second implemented canonical §10 group after NEW-M6-01. The other
65 groups and 14 observation-model entries remain open; 15 source-ID mappings
still need disambiguation. Original evidence: research `2da6469`, model register
§6 M6-11/M6-18/M6-19, and the §10 inventory in this directory.
