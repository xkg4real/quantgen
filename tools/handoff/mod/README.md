# handoff-usage-watch

A Claude Code hooks-module mod that hands the work off before the subscription's weekly usage limit stops a
session. It is inert until the owner turns it on (below); nothing in the repository loads it.

What it does, in a repository that has `tools/handoff/auto_snapshot.py`:

- **At 98% weekly usage** (`session.measure`, `seven_day` window): pushes a no-model git snapshot
  (`AUTO_STATE.md`) to the `handoff` branch, then submits a prompt telling Claude to finish the current step,
  write `CURRENT.md` with `status: handoff` and publish it with `tools/handoff/push_handoff.py`. Until that
  publish runs, the instruction also rides in the system prompt. It fires once per weekly window, keyed by
  the window's reset time, across sessions (the key is a commit trailer on the `handoff` branch).
- **After each main-thread turn:** a throttled snapshot (at most every 30 minutes, only when the git state
  changed), so the branch holds a recent state even when a session stops without warning.
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
