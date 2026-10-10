import { expect, test } from 'claude-code/testing'

import { classify, flavor, characterOf, guildRole } from './roster'

const SURFACES = ['terminal', 'desktop', 'mobile', 'vscode'] as const
const PANE = { title: 'The Tavern', isFocused: false, bodyColumns: 100, placement: 'dock' } as never

test('a guild agent maps to its character and voice', async () => {
  expect(guildRole('guildhall:test-author')).toBe('test-author')
  expect(guildRole('Explore')).toBe(undefined)
  const { deed, target } = classify('Read', { file_path: '/repo/docs/specs/login.md' })
  expect(flavor(characterOf('test-author'), deed, target)).toBe(
    'Seraphine reads the spec as scripture: login.md',
  )
  // Reviewers have no write line of their own and fall back to the generic one.
  expect(flavor(characterOf('security-reviewer'), 'write', 'notes.md')).toBe('Oriana scribbles notes: notes.md')
})

test('a quest draws Mordain, the summoned adventurer and what they are doing', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'seraphine-1' }))
  on('tool.call', () => ({ result: '', text: '' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: ['desktop'] }))

  await $.command.run({
    command: 'quest',
    args: 'Add login rate limiting',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: true, columns: 120 },
  } as never)
  await $.agent.spawn({
    tool_use_id: 't1',
    prompt: 'Write failing tests from the spec',
    description: 'Write failing tests',
    subagentType: 'guildhall:test-author',
    provider: { plugin: 'guildhall', tier: 'user' },
    parentModel: 'opus',
    background: false,
    fork: false,
  } as never)
  await $.tool.call({ tool: 'Read', file_path: '/repo/docs/specs/login.md', agentId: 'seraphine-1' } as never)

  const panes = []
  for (const surface of SURFACES) {
    const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface, component: 'Pane', requestId: 'guildhall', props: PANE })
    panes.push(pane)
    expect(await pane.find({ text: /Add login rate limiting/ })).toBeDefined()
    expect(await pane.find({ text: /Build chain/ })).toBeDefined()
    expect(await pane.find({ text: /Seraphine reads the spec as scripture: login\.md/ })).toBeDefined()
  }

  await $.turn.complete({
    answer: 'done',
    durationMs: 1000,
    isAborted: false,
    turnId: 'turn-1',
    agentId: 'seraphine-1',
    reason: 'answer',
  } as never)

  for (const pane of panes) {
    expect(await pane.find({ text: /The test is its shadow/ })).toBeDefined()
    expect(await pane.find({ text: /Seraphine returns to the hall/ })).toBeDefined()
  }
})

test('where no surface places the pane, the command says why and prints the tavern', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'opus', agentId: 'oriana-1' }))
  on('tool.call', () => ({ result: '', text: '' }))
  on('ui.open', () => ({ value: { isPlaced: false, reason: 'the attached surface places no panes' } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: ['desktop'] }))

  await $.agent.spawn({
    tool_use_id: 't1',
    prompt: 'Review the tavern mod',
    description: 'Security review of the tavern',
    subagentType: 'guildhall:security-reviewer',
    provider: { plugin: 'guildhall', tier: 'user' },
    parentModel: 'opus',
    background: false,
    fork: false,
  } as never)
  await $.tool.call({ tool: 'Grep', pattern: 'password', agentId: 'oriana-1' } as never)

  const answer = await $.command.run({
    command: 'guildhall-tavern',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 80 },
  } as never)
  expect(answer.text).toContain('the attached surface places no panes')

  expect(answer.text).toContain('Review fan-out')
  expect(answer.text).toContain('Oriana searches for unwatched gates: password')
})

test('what reaches the screen carries no command text, URL query or terminal escapes', async () => {
  const bare = classify('Bash', { command: 'curl -H "Authorization: Bearer sk-secret" https://x' })
  expect(flavor(characterOf('feature-implementer'), bare.deed, bare.target)).toBe('Bruga quenches the blade')
  const described = classify('Bash', { command: 'npm test', description: 'Run unit tests' })
  expect(described.target).toBe('Run unit tests')
  expect(classify('WebFetch', { url: 'https://api.example.com/v1/items?token=abc#frag' }).target).toBe(
    'https://api.example.com/v1/items',
  )
  expect(classify('WebFetch', { url: 'https://user:pass@example.com/a?b=c' }).target).toBe('https://example.com/a')
  expect(classify('Read', { file_path: '/repo/evil\u001b]52;c;aGk=\u0007.md' }).target).toBe('evil ]52;c;aGk= .md')
})

test('with no surface attached, a pane that reads as placed still prints the tavern as text', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  const answer = await $.command.run({
    command: 'guildhall-tavern',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 80 },
  } as never)
  expect(answer.text).toContain('no surface that draws panes is attached')
  expect(answer.text).toContain('The tavern is quiet')
})

const spawnInput = (subagentType: string, description: string, parentAgentId?: string) =>
  ({
    tool_use_id: `t-${description}`,
    prompt: description,
    description,
    subagentType,
    provider: { plugin: 'guildhall', tier: 'user' },
    parentModel: 'opus',
    background: true,
    fork: false,
    parentAgentId,
  }) as never

const tavernCommand = {
  command: 'guildhall-tavern',
  args: '',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: false, columns: 80 },
} as never

test('inherited object keys are not roles', async () => {
  expect(guildRole('constructor')).toBe(undefined)
  expect(guildRole('guildhall:toString')).toBe(undefined)
  expect(characterOf('constructor').title).toBe('hireling')
})

test('a denied dispatch opens no quest', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ deny: 'not now' }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Review'))
  const answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('The tavern is quiet')
})

test('adventurers dispatched together share one quest, and a working child keeps its phase at work', async ($, on) => {
  let n = 0
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'sonnet', agentId: `a${++n}` }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await Promise.all([
    $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Security pass')),
    $.agent.spawn(spawnInput('guildhall:docs-writer', 'Docs pass')),
  ])
  await $.agent.spawn(spawnInput('Explore', 'Look around', 'a1'))
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't', agentId: 'a1', reason: 'answer' } as never)
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't', agentId: 'a2', reason: 'answer' } as never)

  const answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('Oriana')
  expect(answer.text).toContain('Cassian')

  const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'terminal', component: 'Pane', requestId: 'guildhall', props: PANE })
  expect(await pane.find({ text: /Review fan-out\s+1 at work/ })).toBeDefined()
})

// ── End-of-quest recap ────────────────────────────────────────────────────

import { parseReviewerLine, phaseSpans, planStatus, reviewerVerdicts } from './recap'

const PLAN = `---
quest: Add login rate limiting
status: completed
---

# Plan

## Reviewers selected

Always-on:
- Oriana (\`security-reviewer\`) — fires
- Cassian (\`docs-writer\`) — fires

Gated:
- Vance (\`observability-reviewer\`) — fired — request-time code path
- Thalia (\`reliability-reviewer\`) — skipped — no network I/O

## Decisions made by Mordain
- Skip Bruga: not a reviewer line
`

test('a reviewer bullet in either dialect becomes verdicts', async () => {
  expect(parseReviewerLine('Vance (`observability-reviewer`) — skipped — docs-only change')).toEqual([
    { role: 'observability-reviewer', fired: false, reason: 'docs-only change' },
  ])
  expect(parseReviewerLine('Oriana (`security-reviewer`) — fires')).toEqual([
    { role: 'security-reviewer', fired: true, reason: '' },
  ])
  expect(parseReviewerLine('Oriana security: API credential handling, untrusted input')).toEqual([
    { role: 'security-reviewer', fired: true, reason: 'API credential handling, untrusted input' },
  ])
  expect(parseReviewerLine('Skip Vera/Lior: no visual UI changes.')).toEqual([
    { role: 'ui-test-author', fired: false, reason: 'no visual UI changes.' },
    { role: 'accessibility-reviewer', fired: false, reason: 'no visual UI changes.' },
  ])
  expect(parseReviewerLine('Always-on:')).toEqual([])
})

test('the scroll is read only under Reviewers selected, with its status', async () => {
  const verdicts = reviewerVerdicts(PLAN)
  expect(verdicts.map(v => v.role)).toEqual([
    'security-reviewer', 'docs-writer', 'observability-reviewer', 'reliability-reviewer',
  ])
  expect(planStatus(PLAN)).toBe('completed')
  expect(planStatus('# no frontmatter')).toBe(undefined)
})

test('a parallel fan-out counts its wall-clock span once', async () => {
  const m = (id: string, role: string, startedAt: number, endedAt: number, parentId?: string) =>
    ({ id, role, status: 'done', task: '', line: '', deeds: 0, startedAt, endedAt, parentId }) as const
  const spans = phaseSpans(
    [
      m('a', 'test-author', 0, 60_000),
      m('b', 'feature-implementer', 60_000, 180_000),
      m('c', 'security-reviewer', 200_000, 260_000),
      m('d', 'docs-writer', 200_000, 230_000),
      m('e', 'Explore', 210_000, 290_000, 'c'), // Oriana's hireling stays in the fan-out
    ],
    999_999,
  )
  expect(spans).toEqual([
    { phase: 'build', label: 'Build chain', ms: 180_000 },
    { phase: 'review', label: 'Review fan-out', ms: 90_000 },
  ])
})

const questCommand = (args: string) =>
  ({ command: 'guildhall:quest', args, origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 120 } }) as never

test('when the hall falls quiet, the pane recaps the quest from its plan scroll', async ($, on) => {
  const reads: string[] = []
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'opus', agentId: 'oriana-1' }))
  on('tool.call', () => ({ result: '', text: '' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('fs.read', ($, e) => {
    reads.push(e.path)
    return { value: PLAN }
  })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.command.run(questCommand('Add login rate limiting'))
  // Mordain inks the scroll; a subagent's write elsewhere is not the plan.
  await $.tool.call({ tool: 'Write', file_path: '/repo/docs/guildhall/plans/2026-10-10-login.md', content: '' } as never)
  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Security pass'))
  await $.tool.call({ tool: 'Write', file_path: '/repo/docs/guildhall/plans/other.md', content: '', agentId: 'oriana-1' } as never)
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'oriana-1', reason: 'answer' } as never)
  await $.turn.complete({ answer: 'done', durationMs: 1, isAborted: false, turnId: 't0', reason: 'answer' } as never)

  expect(reads).toEqual(['/repo/docs/guildhall/plans/2026-10-10-login.md'])
  for (const surface of SURFACES) {
    const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface, component: 'Pane', requestId: 'guildhall', props: PANE })
    expect(await pane.find({ text: /Recap · completed/ })).toBeDefined()
    expect(await pane.find({ text: /Review fan-out \d+s/ })).toBeDefined()
    expect(await pane.find({ text: /✓ 🦉 Oriana/ })).toBeDefined()
    expect(await pane.find({ text: /· ⚡ Thalia.*no network I\/O/ })).toBeDefined()
    // Planned in the scroll, never summoned: the recap says so rather than trusting either side.
    expect(await pane.find({ text: /⚠ 📜 Vance.*planned, never summoned/ })).toBeDefined()
    expect(await pane.find({ text: /2026-10-10-login\.md/ })).toBeDefined()
  }
  const answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('Recap · completed')
})

test('a quest with no plan scroll, or an unreadable one, still recaps who was summoned', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'pip-1' }))
  on('tool.call', () => ({ result: '', text: '' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('fs.read', () => {
    throw new Error('ENOENT')
  })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.command.run(questCommand('Fix a README typo'))
  await $.agent.spawn(spawnInput('guildhall:prototype-builder', 'Docs fast lane'))
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'pip-1', reason: 'answer' } as never)
  await $.turn.complete({ answer: 'done', durationMs: 1, isAborted: false, turnId: 't0', reason: 'answer' } as never)
  let answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('Recap')
  expect(answer.text).toContain('🎒')
  expect(answer.text).toContain('no plan scroll')

  await $.command.run(questCommand('Bigger quest'))
  await $.tool.call({ tool: 'Write', file_path: 'docs/guildhall/plans/2026-10-10-big.md', content: '' } as never)
  await $.turn.complete({ answer: 'done', durationMs: 1, isAborted: false, turnId: 't2', reason: 'answer' } as never)
  answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('could not read 2026-10-10-big.md')
})

// ── The band above the prompt ─────────────────────────────────────────────

const BAND_SURFACES = ['terminal', 'desktop'] as const
const BAND = (hasSurvey = false) =>
  ({ hasSurvey, isWorking: true, maxRows: 6, bodyColumns: 100, scroll: { offset: 0, bodyRows: 5 }, view: {} }) as never
// The engine's own band, beneath the tavern: what shows when the tavern passes.
const engineBand = (on: never) =>
  (on as (event: string, hook: ($: never, e: never) => unknown) => void)('ui.render', ($, e) => {
    const { Text } = ($ as { ui: { resolve: (e: never) => { Text: never } } }).ui.resolve(e)
    return h(Text, {}, 'the engine band')
  })
const mountBand = ($: never, surface: (typeof BAND_SURFACES)[number], hasSurvey = false) =>
  ($ as { ui: { mount: (a: unknown) => Promise<{ find: (q: unknown) => Promise<unknown>; press: (q: unknown) => Promise<void> }> } }).ui.mount({
    plugin: 'guildhall-tavern', surface, component: 'AbovePrompt', props: BAND(hasSurvey),
  })

test('with the pane closed, the band names the phase at work and who', async ($, on) => {
  let n = 0
  let panes: { id: string; title: string; isShown: boolean; isFocused: boolean; isPlaced: boolean }[] = []
  const opened: string[] = []
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'opus', agentId: `r${++n}` }))
  on('ui.open', ($, e) => {
    opened.push(e.id)
    return { value: { isPlaced: true } }
  })
  on('ui.panes', () => ({ value: panes }))
  on('session.surfaces', () => ({ value: ['terminal'] }))
  engineBand(on as never)

  for (const surface of BAND_SURFACES) {
    // No quest, nothing to say.
    expect(await (await mountBand($ as never, surface)).find({ text: /⚔/ })).toBe(undefined)
  }

  await $.command.run(questCommand('Add login rate limiting'))
  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Security pass'))
  await $.agent.spawn(spawnInput('guildhall:docs-writer', 'Docs pass'))

  for (const surface of BAND_SURFACES) {
    const band = await mountBand($ as never, surface)
    expect(await band.find({ text: /⚔ Review fan-out · 🦉📖 at work/ })).toBeDefined()
    opened.length = 0
    await band.press({ key: 'open-tavern' })
    expect(opened).toEqual(['guildhall'])
    // A survey holds the band: the tavern yields.
    expect(await (await mountBand($ as never, surface, true)).find({ text: /⚔/ })).toBe(undefined)
  }

  // The pane in view says it all; the band stays out of the way.
  panes = [{ id: 'guildhall', title: 'The Tavern', isShown: true, isFocused: false, isPlaced: true }]
  for (const surface of BAND_SURFACES) {
    expect(await (await mountBand($ as never, surface)).find({ text: /⚔/ })).toBe(undefined)
  }
})

test('once the hall is quiet the band offers the recap, until the next prompt', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'pip-1' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('prompt.submit', ($, e) => ({ text: e.text }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: ['terminal'] }))
  engineBand(on as never)

  await $.command.run(questCommand('Fix a README typo'))
  for (const surface of BAND_SURFACES) {
    expect(await (await mountBand($ as never, surface)).find({ text: /⚔ Fix a README typo · 🧙/ })).toBeDefined()
  }
  await $.agent.spawn(spawnInput('guildhall:prototype-builder', 'Docs fast lane'))
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'pip-1', reason: 'answer' } as never)
  await $.turn.complete({ answer: 'done', durationMs: 1, isAborted: false, turnId: 't0', reason: 'answer' } as never)
  for (const surface of BAND_SURFACES) {
    expect(await (await mountBand($ as never, surface)).find({ text: /⚔ Fix a README typo · recap ready/ })).toBeDefined()
  }

  await $.prompt.submit({ text: 'thanks' } as never)
  for (const surface of BAND_SURFACES) {
    expect(await (await mountBand($ as never, surface)).find({ text: /⚔/ })).toBe(undefined)
  }
})
