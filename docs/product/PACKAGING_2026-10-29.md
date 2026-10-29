# PR-F runtime packaging verification

The wheel now includes the Home status reader, branding/fonts, calendar YAML and runtime schemas. `core.app_paths` resolves both source and installed resource roots. Build inputs are an explicit tracked-file allowlist; secrets, protected caches, frozen studies and user ledgers are never staged. No deployment or package publication is configured.

Local Linux/Python 3.12 evidence: 18 bounded tests passed; a 199-file stage built quantgen-2.0.0-py3-none-any.whl. Installed smoke outside the checkout passed imports, Home construction, recorded-status consistency and resource presence. The local venv uses system site packages; it is not evidence of a clean Windows install. Network and .env reads were blocked during the smoke; providers and engine startup were NOT_RUN. Matplotlib used a temporary cache because the managed home is read-only.

`.github/workflows/runtime-smoke.yml` tests clean Ubuntu and Windows Python 3.12 wheel installation. Workflow registration is not proof of CI success; see the actual run for the pushed commit. This is wheel/import/UI packaging coverage, not a signed native executable or installer release.
