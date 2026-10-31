# Claude commentary connection diagnostics

Scope: optional AI commentary in the Windows PyQt6 app and retained Flet browser.
The application uses the Anthropic Messages API directly, with
`ANTHROPIC_API_KEY` and the model configured by `QUANTGEN_AI_MODEL`.
It does not use the Claude desktop/web login or subscription as API credentials.

Previously, HTTP 401 displayed only "rejected the key"; other failures displayed
raw provider messages and transport exceptions. Errors now have a safe category,
HTTP status when received, and an actionable message. Provider bodies and exception
text are not displayed. Native and Flet messages follow the selected English/Korean
language without resending the request when the language changes.

| Result | Next action |
| --- | --- |
| 401 authentication | Check an active Anthropic Console API key and intended workspace locally. |
| 403 permission | Check workspace/model permissions. |
| 404 model/resource | Check `QUANTGEN_AI_MODEL` against available models; do not assume invalid key. |
| 400 credit-balance error / 402 | Check API balance/billing, separate from Claude app subscription. |
| Other 400 / 413 | Check model, request format or size. |
| 429 | Check API usage limits and wait before manually retrying. |
| 5xx, including 529 | Service failure; retry later. |
| Network / timeout | Check connectivity to `api.anthropic.com`; not evidence of rejected credentials. |

After changing local configuration, fully close and restart QUANTGEN. Configuration
loads dotenv without overriding existing process environment values: a stale
`ANTHROPIC_API_KEY` in the launching environment takes precedence over `.env`.
Presence-only connection indicators do not prove that Anthropic accepted a key.
Do not paste keys, credential files, full request bodies or account data into issues.
Report only the diagnostic category and HTTP status.

No automatic retries, fallback models, credential replacement, new provider
connection, or changes to verdicts/calculations are introduced. Failed commentary
does not create a successful AI report. Local analysis remains available.
Payload privacy filtering and explicit preview/consent remain in place.

Verification uses mocked HTTP failures/success, fake keys and offscreen native
widgets. It covers HTTP classification, billing, malformed bodies, transport
failures, non-disclosure, language switching and export failure boundaries.
No live key was read or validated. User Windows connection acceptance remains
NOT_RUN until a real explicit request succeeds on that installation.
