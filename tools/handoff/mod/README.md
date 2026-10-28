# handoff-usage-watch

A Claude Code hooks-module mod that hands the work off before the subscription's weekly usage limit stops a
session. It is inert until the owner turns it on (below); nothing in the repository loads it.

What it does, in a repository that has `tools/handoff/auto_snapshot.py`:

- **At 98% weekly usage** (`session.measure`, `seven_day` window): pushes a no-model git snapshot
  (`AUTO_STATE.md`) to the `handoff` branch, then submits a prompt telling Claude to finish the current step,
  push the work branch, write `CURRENT.md` with `status: handoff` and publish it with
  `tools/handoff/push_handoff.py --key <window>`. Until a publish prints `(handoff …)`, the instruction also
  rides in the system prompt. Each session asks once per weekly window. While that window's handoff is
  outstanding (its `handoff-key:` trailer is on the branch and `CURRENT.md` is `handoff` or `taken`), later
  sessions stay quiet; once it is returned, a session crossing 98% hands off its own work. When another task's
  handoff or lock holds the branch, the prompt says so and asks Claude to push and tell the owner instead.
- **During work:** a throttled snapshot after main-thread turns and tool calls (the script runs at most every
  5 minutes and pushes at most every 30, only when the git state changed), so the branch holds a recent state
  even when a session stops without warning. Only a session on `CURRENT.md`'s `work_branch` refreshes it.
- **When a turn fails with a rate-limit error** (`classic.StopFailure`): a last snapshot with the model's final
  message. The model cannot run at that point; the script can.

The five-hour window is off; set `THRESHOLDS.five_hour` in `hooks/register.ts` to turn it on.

## Turning it on

Claude Code on the web does not load plugins from a repository by itself. Set this environment variable on
the claude.ai cloud environment this repository's sessions use (environment settings, Environment
variables); sessions started after that load the mod from the clone:

```
CLAUDE_CODE_PLUGIN_DIRS=/home/user/quantgen/tools/handoff/mod
```

On a local machine, start Claude Code with `claude --plugin-dir <repo>/tools/handoff/mod`, or put
`CLAUDE_CODE_PLUGIN_DIRS` in the `env` block of `~/.claude/settings.json` (a project's settings cannot set it).
To turn it off, remove the variable.

## Checking it

```
claude plugin validate tools/handoff/mod
claude plugin test tools/handoff/mod
```
