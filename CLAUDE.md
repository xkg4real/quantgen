# Notes for Claude sessions in this repository

## Handoff protocol

The code-free `handoff` branch holds `CURRENT.md`, the one live handoff document, and `LEDGER.md`, the
append-only record of finished work, so that another agent (GPT) can pick up the work when a Claude session
stops and neither agent does the same work twice. Its `README.md` defines the statuses and the owner's weekly
schedule, `TEMPLATE.md` the fields; read both once with `git show origin/handoff:README.md` and
`git show origin/handoff:TEMPLATE.md`.

The owner's week: Claude's usage refills on Tuesday 17:00 KST and Claude hands off at 98% weekly usage; GPT
checks the branch hourly from Thursday 00:00 KST, works from the handoff, and returns it before the next
Tuesday 17:00 KST. One task runs at a time.

- **Session start, before any new work:** run `python3 tools/handoff/push_handoff.py --show`.
  - `status: returned`: GPT has handed the work back. Read the whole document
    (`git show origin/handoff:CURRENT.md`) and the ledger (`python3 tools/handoff/push_handoff.py --ledger`).
    Check what GPT says it did against git: its commits on `work_branch` (`git log`), the files they change,
    and the checks it reports, run again. Continue from GPT's `work_branch` at `work_commit` (branch from it,
    or merge it into your work branch), take the next work from `next_ids` and section 6, and publish a
    checkpoint saying what you verified before you change anything.
  - `status: taken` by another agent, or `status: unreadable`: GPT is still working or the document is
    broken. Start nothing that overlaps it; tell the owner.
  - `status: handoff` for a task other than the one you were given: start no new work over it; ask the owner
    whether to resume it here or leave it for GPT.
- **Before starting any roadmap item:** look it up in the ledger by ID and by the files it would change. An ID
  already there is finished: do not do it again. IDs come from `docs/nautilus_bridge/REMAINING_WORK_*.md`
  (the newest); a part of an item is `③-2/a`, more work the owner asks for on a finished item is `③-2/2`.
- **Task start:** for work that will take more than one commit, write the document from the template with
  `status: checkpoint`, `cycle`, `done_ids` and `next_ids`, and publish it.
- **Each milestone** (a commit whose checks pass, a decision the owner made, a finished sub-step): push the
  work branch (`git push -u origin HEAD`), then update the document and publish it again. When a roadmap ID is
  finished, publish with `--done "<id> | <what> | <files> | <commit> | <check and result>"`, move the ID from
  `next_ids` to `done_ids`, and never list a ledger ID in `next_ids`. A reader with no access to this session
  must be able to continue from the document alone: the owner's request quoted verbatim, the files it rests
  on, the decisions and why, where you stopped, the next steps as commands with their done criteria. Before a
  long step that changes no files, publish a checkpoint or set `waiting_on`, so the branch does not look stale.
- **Stopping with work unfinished**, or when told the usage limit is near: push the work branch, record any
  finished ID with `--done`, set `status: handoff` with the matching `reason`, publish, and start no new work.
- Publish with `python3 tools/handoff/push_handoff.py <file>`; keep the file in your scratchpad, not in the
  repository. It reads the commit back from the remote and says `verified`; anything else is not published.
  Exit code 3 is a refusal (another agent holds the task, the remote document is unreadable, another task's
  handoff is still untaken, or the work is already in the ledger): stop and tell the owner; `--force` (locks
  only) only with the owner's say-so. Exit code 2 names the input to fix.
- `AUTO_STATE.md` and `AUTO_STATE.patch` on the same branch are written without the model by
  `tools/handoff/auto_snapshot.py` (git state only); never edit them by hand. Where the owner has turned on the
  `tools/handoff/mod` mod, it pushes that snapshot and tells you when weekly usage reaches 98%: hand off as it
  says, publishing with the `--key` it gives.
- No secrets in the document or the ledger: name `.env` variables, never their values.
