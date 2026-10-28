import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'

const RESETS = '2026-11-03T08:00:00.000Z'
const COMPOSE = { model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null, traits: [] }
const PUBLISHED = 'push_handoff: handoff at abc1234 (handoff task-a)'

const measure = (percentUsed: number, kind = 'seven_day') => ({
  context: { window: 200_000 },
  rateLimits: [{ kind, percentUsed, resetsAt: RESETS }],
  changed: ['rateLimits' as const],
})

const turn = (agentId?: string) =>
  ({ answer: 'a', durationMs: 1, isAborted: false, turnId: 't', reason: 'answer' as const, ...(agentId ? { agentId } : {}) })

async function settle() {
  for (let i = 0; i < 500; i++) await Promise.resolve()
}

function engine(on: On, { exitCode = 0, isQuantgen = true } = {}) {
  const runs: string[][] = []
  const stdins: (string | undefined)[] = []
  const prompts: string[] = []
  const store = new Map<string, unknown>()
  const world = { session: 'sess-1', toolText: '' }
  const clock = mock.clock(on)
  on('store.get', (_, e) => ({ value: store.get(e.key) }))
  on('store.set', (_, e) => (store.set(e.key, e.value), { value: undefined }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  on('session.root', () => ({ value: '/repo' }))
  on('session.id', () => ({ value: world.session }))
  on('fs.exists', () => ({ value: isQuantgen }))
  on('process.run', (_, e) => {
    runs.push([...e.argv])
    stdins.push(e.init?.stdin)
    return { value: { exitCode, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('prompt.submit', (_, e) => {
    prompts.push(e.text)
    return { text: e.text }
  })
  on('ui.toast', () => ({ value: undefined }))
  on('prompt.compose', () => ({ sections: [{ id: 'intro', text: 'x', scope: 'shared' as const }] }))
  on('tool.call', () => ({ result: {}, text: world.toolText }))
  on('turn.complete', () => ({ text: '' }))
  on('classic.StopFailure', () => ({}))
  return { runs, stdins, prompts, world, clock }
}

const snapshots = (runs: string[][], reason: string) => runs.filter(r => r.includes(reason))
type Composer = { prompt: { compose: (e: typeof COMPOSE) => Promise<{ sections: readonly { id: string }[] }> } }
const isPending = async ($: Composer) =>
  (await $.prompt.compose(COMPOSE)).sections.some(s => s.id === 'handoff-usage-watch:pending')

test('below the threshold nothing happens', async ($, on) => {
  const { runs, prompts } = engine(on)
  await $.session.measure(measure(97.9))
  await settle()
  expect(runs.length).toBe(0)
  expect(prompts.length).toBe(0)
})

test('at 98% weekly: one snapshot and one prompt per session and window', async ($, on) => {
  const { runs, prompts, world } = engine(on)
  await $.session.measure(measure(98.3))
  await settle()
  await $.session.measure(measure(99.0))
  await settle()
  expect(snapshots(runs, 'usage_limit_weekly').length).toBe(1)
  expect(runs[0]).toContain(`seven_day@${RESETS}`)
  expect(prompts.length).toBe(1)
  expect(prompts[0]).toContain('status: handoff')
  expect(prompts[0]).toContain('usage_weekly_pct: 98.3')
  expect(prompts[0]).toContain(`--key seven_day@${RESETS}`)
  expect(prompts[0]).toContain('git push -u origin HEAD')

  // Another session asks the branch again rather than trusting this session's flag.
  world.session = 'sess-2'
  await $.session.measure(measure(99.1))
  await settle()
  expect(snapshots(runs, 'usage_limit_weekly').length).toBe(2)
})

test('the five-hour window is off by default', async ($, on) => {
  const { runs } = engine(on)
  await $.session.measure(measure(99.5, 'five_hour'))
  await settle()
  expect(runs.length).toBe(0)
})

test('a window already handed off on the branch gets no prompt', async ($, on) => {
  const { prompts } = engine(on, { exitCode: 10 })
  await $.session.measure(measure(98.0))
  await settle()
  expect(prompts.length).toBe(0)
})

test('outside a repository with the scripts, nothing happens', async ($, on) => {
  const { runs, prompts } = engine(on, { isQuantgen: false })
  await $.session.measure(measure(99.0))
  await $.turn.complete(turn())
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await settle()
  expect(runs.length).toBe(0)
  expect(prompts.length).toBe(0)
})

test('the instruction stays in the system prompt until a handoff is actually published', async ($, on) => {
  const { world } = engine(on)
  await $.session.measure(measure(98.5))
  await settle()
  expect(await isPending($)).toBe(true)

  world.toolText = 'status: checkpoint\ntask: task-a'
  await $.tool.call({ tool: 'Bash', command: 'python3 tools/handoff/push_handoff.py --show' })
  world.toolText = 'push_handoff: handoff at abc1234 (checkpoint task-a)'
  await $.tool.call({ tool: 'Bash', command: 'python3 tools/handoff/push_handoff.py /tmp/c.md' })
  expect(await isPending($)).toBe(true)

  world.toolText = PUBLISHED
  await $.tool.call({ tool: 'Bash', command: 'python3 tools/handoff/push_handoff.py /tmp/h.md --key k | tail -1' })
  expect(await isPending($)).toBe(false)
})

test('periodic snapshots: main-thread turn ends and tool activity, at most every five minutes', async ($, on) => {
  const { runs, clock } = engine(on)
  await $.turn.complete(turn())
  await settle()
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await settle()
  expect(snapshots(runs, 'periodic').length).toBe(1)
  expect(runs[0]).toContain('1800')

  await clock.advance(6 * 60_000)
  await $.turn.complete(turn('sub'))
  await settle()
  expect(snapshots(runs, 'periodic').length).toBe(1)
  await $.tool.call({ tool: 'Read', file_path: '/repo/x' })
  await settle()
  expect(snapshots(runs, 'periodic').length).toBe(2)
})

test('a turn that fails on the rate limit pushes a snapshot with the last message', async ($, on) => {
  const { runs, stdins } = engine(on)
  await $.classic.StopFailure({ error: 'rate_limit', last_assistant_message: 'editing core/x.py' })
  await settle()
  await $.classic.StopFailure({ error: 'server_error' })
  await settle()
  expect(snapshots(runs, 'rate_limit_error').length).toBe(1)
  expect(stdins[runs.findIndex(r => r.includes('rate_limit_error'))]).toContain('editing core/x.py')
})
