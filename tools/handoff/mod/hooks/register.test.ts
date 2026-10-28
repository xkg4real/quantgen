import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'

const RESETS = '2026-11-03T08:00:00.000Z'
const COMPOSE = { model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null, traits: [] }

const measure = (percentUsed: number, kind = 'seven_day') => ({
  context: { window: 200_000 },
  rateLimits: [{ kind, percentUsed, resetsAt: RESETS }],
  changed: ['rateLimits' as const],
})

async function settle() {
  for (let i = 0; i < 50; i++) await Promise.resolve()
}

function engine(on: On, exitCode = 0, isQuantgen = true) {
  const runs: string[][] = []
  const stdins: (string | undefined)[] = []
  const prompts: string[] = []
  const store = new Map<string, unknown>()
  on('store.get', (_, e) => ({ value: store.get(e.key) }))
  on('store.set', (_, e) => (store.set(e.key, e.value), { value: undefined }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  on('session.root', () => ({ value: '/repo' }))
  on('session.id', () => ({ value: 'sess-1' }))
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
  on('tool.call', () => ({ result: {} }))
  on('turn.complete', () => ({ text: '' }))
  on('classic.StopFailure', () => ({}))
  return { runs, prompts, stdins }
}

test('below the threshold nothing happens', async ($, on) => {
  const { runs, prompts } = engine(on)
  await $.session.measure(measure(97.9))
  await settle()
  expect(runs.length).toBe(0)
  expect(prompts.length).toBe(0)
})

test('at 98% weekly: one snapshot, one prompt, once per window', async ($, on) => {
  const { runs, prompts } = engine(on)
  await $.session.measure(measure(98.3))
  await settle()
  await $.session.measure(measure(99.0))
  await settle()
  expect(runs.length).toBe(1)
  expect(runs[0]).toContain('tools/handoff/auto_snapshot.py')
  expect(runs[0]).toContain(`seven_day@${RESETS}`)
  expect(prompts.length).toBe(1)
  expect(prompts[0]).toContain('status: handoff')
  expect(prompts[0]).toContain('usage_weekly_pct: 98.3')
})

test('the five-hour window is off by default', async ($, on) => {
  const { runs } = engine(on)
  await $.session.measure(measure(99.5, 'five_hour'))
  await settle()
  expect(runs.length).toBe(0)
})

test('a window an earlier session handed off is left alone', async ($, on) => {
  const { prompts } = engine(on, 10)
  await $.session.measure(measure(98.0))
  await settle()
  expect(prompts.length).toBe(0)
})

test('the system prompt carries the instruction until the model publishes', async ($, on) => {
  engine(on)
  await $.session.measure(measure(98.5))
  await settle()
  const before = await $.prompt.compose(COMPOSE)
  expect(before.sections.some(s => s.id === 'handoff-usage-watch:pending')).toBe(true)

  await $.tool.call({ tool: 'Bash', command: 'python3 tools/handoff/push_handoff.py /tmp/h.md' })
  const after = await $.prompt.compose(COMPOSE)
  expect(after.sections.some(s => s.id === 'handoff-usage-watch:pending')).toBe(false)
})

test('outside a repository with the scripts, nothing happens', async ($, on) => {
  const { runs, prompts } = engine(on, 0, false)
  await $.session.measure(measure(99.0))
  await settle()
  expect(runs.length).toBe(0)
  expect(prompts.length).toBe(0)
})

test('each main-thread turn end asks for a throttled snapshot; a subagent turn does not', async ($, on) => {
  const { runs } = engine(on)
  await $.turn.complete({ answer: 'a', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })
  await settle()
  await $.turn.complete({ answer: 'b', durationMs: 1, isAborted: false, turnId: 't2', agentId: 'sub', reason: 'answer' })
  await settle()
  expect(runs.length).toBe(1)
  expect(runs[0]).toContain('periodic')
  expect(runs[0]).toContain('1800')
})

test('a turn that fails on the rate limit pushes a snapshot with the last message', async ($, on) => {
  const { runs, stdins } = engine(on)
  await $.classic.StopFailure({ error: 'rate_limit', last_assistant_message: 'editing core/x.py' })
  await settle()
  await $.classic.StopFailure({ error: 'server_error' })
  await settle()
  expect(runs.length).toBe(1)
  expect(runs[0]).toContain('rate_limit_error')
  expect(stdins[0]).toContain('editing core/x.py')
})
