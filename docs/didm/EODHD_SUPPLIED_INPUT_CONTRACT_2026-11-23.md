# EODHD Economic Events — supplied-input contract

Base: `dec979a7fae65d5f749e12193fad3d0a9ce8ddf3`.
Branch: `gpt/didm-b6-eodhd-20261123`.

`core/didm/ingest/eodhd.py` is a pure, stdlib-only parser and request-planning contract for a supplied
Economic Events response. It does not fetch data, read keys/configuration, write store rows, start a
scheduler, or register a new source/scorer in the existing DIDM V0 pipeline. Source selection, label
definitions, frozen research criteria, and the existing Polymarket hold are unchanged.

Provider schema reference: <https://eodhd.com/financial-apis/economic-events-data-api>.
Actual endpoint/schema compatibility, plan entitlement, retained historical coverage, timestamp semantics,
commercial display/storage/training rights, and forecast-vintage quality still need independent evidence.
This adapter does not establish them or authorize a subscription or commercial use.

## Time and value boundaries

- Values preserve numeric zero and null separately; booleans, nonfinite values, malformed country/time,
  conflicting offsets, and invalid page bounds are refused rather than converted into plausible data.
- A naive event clock is not guessed as UTC. A separately supplied offset remains unverified without
  explicit verification/evidence; RFC3339 `-00:00` stays unknown.
- Event date and application receipt time never become forecast-publication evidence. Ordinary response
  rows lack verified forecast-publication/version evidence and remain historically ineligible by default.
- Optional caller-reviewed publication/version evidence is a condition for the estimate field only. The
  parser cannot independently verify that the evidence belongs to this row/value. It does not apply a
  research as-of cutoff or certify historical PIT of actual, previous, or the whole response. A later
  integration must verify those conditions separately and preserve the actual receipt time.
- `raw_payload_json` retains original and unknown JSON fields. It is not secret redaction; callers must
  supply authorized, appropriately scoped input without credentials.

## Complete-range planning

Date windows are inclusive and disjoint. A full page at the maximum documented offset requests a split,
never an out-of-range next offset or a fabricated completion. Saturating a single-date window raises
`PartitionExhausted` and leaves completeness unresolved. A short page ends only that page plan; the caller
must still establish that previous pages/ranges are present and consistent. No actual acquisition or
whole-history completeness is claimed by these helpers.

## Reproduction and scope

```sh
python -B -m unittest tests.didm_eodhd_acceptance -v
```

The 18 synthetic methods cover numeric/missing values, raw-field retention, explicit/unknown/conflicting
time zones, caller-evidence limitations, receipt-time preservation, rejected false publication bases,
invalid date/page bounds, disjoint splitting, and unresolved single-day saturation. They use no live
provider, model, credentials, real store, ledger, or frozen study. The runtime workflow includes this
module alongside existing DIDM tests.

The original source passed the author's 18 methods under a final clean bounded guard. Independent review
then requested the explicit evidence-association/as-of/redaction limitation above. Only the module
docstring changed; executable AST equality was checked. Earlier guard-probe diagnostics and their source
hashes remain preserved separately. The final independent confirmation is recorded in the PR validation
and handoff; neither repeated attempts nor overlapping methods are summed into a larger test count.

Final clarified-source independent confirmation: the same 18 methods passed with 0 failures, errors,
or skips, guard violations 0, and all 6 source/package-marker inputs unchanged.

This is a completed synthetic input-contract unit, not completion of B6 acquisition, DIDM training,
historical PIT qualification, commercial data rights, or launch readiness.
