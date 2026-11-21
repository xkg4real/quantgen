# OS-F2: explicit preparation of per-user storage

This change selects the mutable data folder; it does not move real user data
automatically, change a research ledger, implement deletion, or approve release.

## Selection and startup

Path getters remain read-only. Selection order is `QUANTGEN_DATA_DIR`,
`FLET_APP_STORAGE_DATA`, a marked platform folder, an existing `~/.nextgen`,
then the platform folder. Platform defaults are Windows LocalAppData/QUANTGEN,
macOS Library/Application Support/QUANTGEN, and Linux XDG_DATA_HOME/quantgen.
Existing per-feature trading/macro/FICC overrides retain their precedence.

Native `quantgen_desktop.app.main` and the maintained Flet `main(page)` call
`ensure_user_data_dir()` before creating stores or GUI objects. This covers
the module entry point, installed desktop entry point and packaged launcher.
An import or the packaging self-check does not prepare storage. Preparation
failure stops startup without printing a potentially sensitive filesystem path.

Preparation pins one selection, creates the selected folder, and creates or
validates the platform marker before returning. The marker contains only app
name, creation date and format version. A malformed marker, link or nonregular
entry is refused; it is not silently replaced. The newly created selected POSIX data folder requests
mode 0700; Windows ACL security is not established by POSIX mode assertions.
Explicit overrides and existing legacy folders do not receive a platform marker.

The default KIS token-file and OpenDART corp-code writers prepare their root
before writing. Their explicitly injected test paths remain supported.
Other standalone callers of trading/macro/FICC stores must explicitly prepare
storage before constructing stores; the frozen engine files are unchanged.
Path calculation alone is not a write-preparation API.

## Consent-only migration

`migrate_legacy_data(confirmed=True)` is a detached API, not an automatic
migration or a newly delivered consent screen. It refuses overrides, links,
an existing destination and an unconfirmed request. Consent must explain that
moving the shared legacy folder ends file sharing with other applications.

The marker is prepared in the source before an exclusive native rename:
Linux renameat2/RENAME_NOREPLACE, macOS renamex_np/RENAME_EXCL, or Windows
os.rename. A destination appearing concurrently is refused rather than merged,
nested or overwritten. Cross-filesystem and unsupported operations fail closed;
there is no copy/delete fallback. A refused rename can leave the small marker
in the unchanged legacy folder. This is not a crash-durability, backup, hostile
filesystem sandbox or multi-process application-lifecycle guarantee.

## Verification and limits

All local migration and token examples use synthetic temporary folders.
The app-path, startup and independent failure-injection checks cover refusal
and preservation. Independent checks overlap the acceptance suite and must
not be added together as unique test counts. Exact test results, platform CI
and review status belong to the PR/handoff; a prepared branch is not a pass.

No actual home store, protected cache, account, provider, frozen study or owner
PC was used. Actual Windows/macOS filesystem behavior remains subject to the
corresponding verification. Publication, licensing and legal gates stay open.
