import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

// Usage percent at which a window triggers the handoff; null leaves that window alone.
const THRESHOLDS: Record<string, number | null> = { seven_day: 98, five_hour: null }
const REASONS: Record<string, string> = { seven_day: 'usage_limit_weekly', five_hour: 'usage_limit_5h' }
const PCT_FIELDS: Record<string, string> = { seven_day: 'usage_weekly_pct', five_hour: 'usage_5h_pct' }
const SNAPSHOT = 'tools/handoff/auto_snapshot.py'
const PERIODIC_SECONDS = 1800
// How often tool activity may start the periodic script at all; the script itself enforces PERIODIC_SECONDS.
const POKE_MS = 5 * 60_000
const SECTION_ID = 'handoff-usage-watch:pending'
// The line push_handoff.py prints once CURRENT.md on the branch holds a handoff.
const PUBLISHED = /push_handoff: \S+ at [0-9a-f]{7} \(handoff /

// Set while a handoff is owed and the model has not yet published one this session.
let pending: string | undefined
let lastPoke: number | undefined
let isPoking = false

const reasonOf = (w: SessionRateLimit) => REASONS[w.kind] ?? 'usage_limit_weekly'

// The mod acts only in a repository that carries the handoff scripts.
async function hasScripts($: EngineInterface) {
  return $.fs.exists(`${await $.session.root()}/${SNAPSHOT}`)
}

async function snapshot($: EngineInterface, args: string[], stdin?: string) {
  const root = await $.session.root()
  const argv = [SNAPSHOT, ...args, '--session', await $.session.id()]
  for (const exe of ['python3', 'python']) {
    try {
      return await $.process.run([exe, ...argv], { cwd: root, timeoutMs: 120_000, stdin })
    } catch {
      // not on PATH under this name: try the next one
    }
  }
  return undefined
}

// One at a time: parallel tool calls must not each start the script.
async function periodic($: EngineInterface) {
  if (isPoking) return
  isPoking = true
  try {
    const now = await $.clock.now()
    if ((lastPoke !== undefined && now - lastPoke < POKE_MS) || !(await hasScripts($))) return
    lastPoke = now
    await snapshot($, ['--reason', 'periodic', '--min-interval', String(PERIODIC_SECONDS)])
  } finally {
    isPoking = false
  }
}

function instruction(w: SessionRateLimit, key: string, isSnapshotPushed: boolean): string {
  const pct = w.percentUsed.toFixed(1)
  const window = w.kind === 'seven_day' ? 'Weekly' : 'Five-hour'
  return [
    `${window} usage is at ${pct}% (the window resets ${w.resetsAt ?? 'at an unknown time'}).`,
    'Hand the work off now, before the limit stops this session: finish only the step in progress and',
    'start no new work or subagents. Commit and run git push -u origin HEAD on the work branch. Then follow',
    "the handoff protocol in CLAUDE.md: write the handoff document from the handoff branch's TEMPLATE.md with",
    `status: handoff, reason: ${reasonOf(w)}, ${PCT_FIELDS[w.kind] ?? 'usage_weekly_pct'}: ${pct},`,
    `usage_resets_at: ${w.resetsAt ?? 'unknown'}, done_ids and next_ids (roadmap IDs, none of next_ids already`,
    'in the ledger), and publish it with',
    `python3 tools/handoff/push_handoff.py <file> --key ${key}, adding a --done row for each roadmap ID finished`,
    'since the last ledger entry.',
    isSnapshotPushed
      ? 'A machine snapshot of the git state is already on the branch as AUTO_STATE.md.'
      : 'The machine snapshot could not be pushed, so the document is the only record: make it complete.',
    'If no task is in progress, publish nothing and say so in one line.',
  ].join(' ')
}

function blockedInstruction(w: SessionRateLimit): string {
  return [
    `${w.kind === 'seven_day' ? 'Weekly' : 'Five-hour'} usage is at ${w.percentUsed.toFixed(1)}%.`,
    "Another task's handoff, or another agent's lock, holds the handoff branch, so this session cannot hand",
    'off there. Finish only the step in progress, commit and run git push -u origin HEAD on the work branch,',
    'start no new work, and tell the owner where the work stands.',
  ].join(' ')
}

async function handOff($: EngineInterface, w: SessionRateLimit, key: string) {
  const ran = await snapshot($, [
    '--reason', reasonOf(w), '--key', key, '--pct', w.percentUsed.toFixed(1), '--resets-at', w.resetsAt ?? 'unknown',
  ])
  if (ran?.exitCode === 10) return // this window's handoff is published and not yet returned
  if (ran?.exitCode === 11) {
    $.prompt.submit({ text: blockedInstruction(w) }).catch(() => undefined)
    return
  }
  pending = instruction(w, key, ran?.exitCode === 0)
  $.ui.toast(`${w.kind} usage ${w.percentUsed.toFixed(1)}%: handing off to the handoff branch`)
  // Should the turn never start, the prompt.compose hook below still carries the instruction.
  $.prompt.submit({ text: pending }).catch(() => undefined)
}

export const register: Register = on => {
  on('session.measure', async ($, e, next) => {
    const result = await next(e)
    if (!e.changed.includes('rateLimits')) return result
    for (const w of e.rateLimits) {
      const threshold = THRESHOLDS[w.kind]
      if (threshold === null || threshold === undefined || w.percentUsed < threshold) continue
      const key = `${w.kind}@${w.resetsAt ?? 'unknown'}`
      // Once per session here; across sessions the branch decides (auto_snapshot.py exits 10).
      const flag = `fired:${await $.session.id()}:${key}`
      if ((await $.store.get(flag)) || !(await hasScripts($))) continue
      await $.store.set(flag, true)
      void handOff($, w, key)
    }
    return result
  })

  // A recent snapshot is on the branch even when a session stops without warning, mid-turn included.
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    // A failed turn is classic.StopFailure's to record.
    if (e.agentId === undefined && e.reason !== 'error') void periodic($).catch(() => undefined)
    return result
  })

  // The model cannot run once a turn fails on the limit; the script still can.
  on('classic.StopFailure', async ($, e, next) => {
    const result = await next(e)
    if (e.error === 'rate_limit' && (await hasScripts($))) {
      const input = { session_id: e.session_id, error: e.error, last_assistant_message: e.last_assistant_message }
      void snapshot($, ['--reason', 'rate_limit_error', '--hook-stdin'], JSON.stringify(input))
    }
    return result
  }).catch(($, e, next) => next(e))

  // Until the model publishes, every system prompt carries the instruction, in case the submitted turn never ran.
  on('prompt.compose', async ($, e, next) => {
    const composed = await next(e)
    if (!pending) return composed
    return { sections: [...composed.sections, { id: SECTION_ID, text: pending, scope: 'session' as const }] }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (pending && e.tool === 'Bash' && ran.isError !== true && PUBLISHED.test(ran.text ?? '')) pending = undefined
    void periodic($).catch(() => undefined)
    return ran
  }).catch(($, e, next) => next(e))
}
