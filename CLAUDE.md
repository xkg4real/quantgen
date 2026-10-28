# Notes for Claude sessions in this repository

## Handoff protocol

The code-free `handoff` branch holds one document, `CURRENT.md`, that lets another agent (GPT) pick up
the work when a Claude session stops. Its `README.md` defines the statuses and `TEMPLATE.md` the fields;
read both once with `git show origin/handoff:README.md` and `git show origin/handoff:TEMPLATE.md`.

- **Session start:** run `python3 tools/handoff/push_handoff.py --show`.
  - `status: returned`: read the whole document (`git show origin/handoff:CURRENT.md`) and continue from it.
  - `status: taken` by another agent, or `status: unreadable`: leave that task alone and tell the owner.
  - `status: handoff` for a task other than the one you were given: start no new work over it; ask the owner
    whether to resume it here or leave it for GPT.
- **Task start:** for work that will take more than one commit, write the document from the template with
  `status: checkpoint` and publish it.
- **Each milestone** (a commit whose checks pass, a decision the owner made, a finished sub-step): push the
  work branch (`git push -u origin HEAD`), then update the document and publish it again. A reader with no
  access to this session must be able to continue from it alone: the owner's request quoted verbatim, the
  files it rests on, the decisions and why, where you stopped, the next steps as commands. Before a long step
  that changes no files, publish a checkpoint or set `waiting_on`, so the branch does not look stale.
- **Stopping with work unfinished**, or when told the usage limit is near: push the work branch, set
  `status: handoff` with the matching `reason`, publish, and start no new work.
- Publish with `python3 tools/handoff/push_handoff.py <file>`; keep the file in your scratchpad, not in the
  repository. Exit code 3 is a refusal (another agent holds the task, the remote document is unreadable, or
  another task's handoff is still untaken): stop and tell the owner; `--force` only with the owner's say-so.
- `AUTO_STATE.md` and `AUTO_STATE.patch` on the same branch are written without the model by
  `tools/handoff/auto_snapshot.py` (git state only); never edit them by hand. Where the owner has turned on the
  `tools/handoff/mod` mod, it pushes that snapshot and tells you when weekly usage reaches 98%: hand off as it
  says, publishing with the `--key` it gives.
- No secrets in the document: name `.env` variables, never their values.
