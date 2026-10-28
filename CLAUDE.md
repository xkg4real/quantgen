# Notes for Claude sessions in this repository

## Handoff protocol

The code-free `handoff` branch holds one document, `CURRENT.md`, that lets another agent (GPT) pick up
the work when a Claude session stops. Its `README.md` defines the statuses and `TEMPLATE.md` the fields;
read both once with `git show origin/handoff:README.md` and `git show origin/handoff:TEMPLATE.md`.

- **Session start:** run `python3 tools/handoff/push_handoff.py --show`. On `status: returned`, read the
  whole document (`git show origin/handoff:CURRENT.md`) and continue from it. On `status: taken` by another
  agent, leave that task alone and tell the owner.
- **Task start:** for work that will take more than one commit, write the document from the template with
  `status: checkpoint` and publish it.
- **Each milestone** (a commit whose checks pass, a decision the owner made, a finished sub-step): update
  the document and publish it again. A reader with no access to this session must be able to continue from
  it alone: the owner's request quoted verbatim, the files it rests on, the decisions and why, where you
  stopped, the next steps as commands.
- **Stopping with work unfinished**, or when told the usage limit is near: set `status: handoff` with the
  matching `reason`, publish, and start no new work.
- Publish with `python3 tools/handoff/push_handoff.py <file>`; keep the file in your scratchpad, not in the
  repository. Exit code 3 means another agent holds the task: stop and tell the owner.
- No secrets in the document: name `.env` variables, never their values.
