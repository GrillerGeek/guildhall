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

// ── PR Lens review on #55 ──────────────────────────────────────────────────

test('a bullet that skips several reviewers in turn records each with its own reason', async () => {
  expect(parseReviewerLine('Skip Ysolde: no persistence migration. Skip Vera/Lior: no visual UI changes.')).toEqual([
    { role: 'migration-safety-reviewer', fired: false, reason: 'no persistence migration.' },
    { role: 'ui-test-author', fired: false, reason: 'no visual UI changes.' },
    { role: 'accessibility-reviewer', fired: false, reason: 'no visual UI changes.' },
  ])
})

test('background adventurers returning after Mordain settle the recap, and the fallen are not counted as returned', async ($, on) => {
  let n = 0
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'opus', agentId: `b${++n}` }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.command.run(questCommand('Review fan-out'))
  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Security pass'))
  // Mordain is still at the table: a return mid-quest is no recap.
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'b1', reason: 'answer' } as never)
  expect((await $.command.run(tavernCommand)).text).not.toContain('Recap')

  await $.agent.spawn(spawnInput('guildhall:docs-writer', 'Docs pass'))
  await $.agent.spawn(spawnInput('guildhall:observability-reviewer', 'Logs pass'))
  await $.turn.complete({ answer: 'waiting', durationMs: 1, isAborted: false, turnId: 't0', reason: 'answer' } as never)
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: true, turnId: 't2', agentId: 'b2', reason: 'answer' } as never)
  expect((await $.command.run(tavernCommand)).text).not.toContain('Recap')
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't3', agentId: 'b3', reason: 'answer' } as never)

  const answer = (await $.command.run(tavernCommand)).text
  expect(answer).toContain('Recap')
  expect(answer).toContain('2 returned, 1 fallen')
})

test('a plan write that fails does not become the scroll the recap reads', async ($, on) => {
  const reads: string[] = []
  on('command.run', () => ({ text: '' }))
  on('tool.call', ($, e) =>
    String((e as { file_path?: string }).file_path).includes('broken')
      ? { isError: true, result: 'EACCES', text: 'EACCES' }
      : { result: '', text: '' },
  )
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('fs.read', ($, e) => {
    reads.push(e.path)
    return { value: PLAN }
  })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.command.run(questCommand('Add login rate limiting'))
  await $.tool.call({ tool: 'Write', file_path: 'docs/guildhall/plans/2026-10-10-good.md', content: '' } as never)
  await $.tool.call({ tool: 'Write', file_path: 'docs/guildhall/plans/2026-10-10-broken.md', content: '' } as never)
  await $.turn.complete({ answer: 'done', durationMs: 1, isAborted: false, turnId: 't0', reason: 'answer' } as never)
  expect(reads.map(path => path.split('/').pop())).toEqual(['2026-10-10-good.md'])
})

test('a quest started through the Skill tool, or a new plan scroll, clears the hall; finished rows keep their task', async ($, on) => {
  on('command.run', () => ({ text: '' }))
  on('agent.spawn', () => ({ model: 'opus', agentId: 'oriana-1' }))
  on('tool.call', () => ({ result: '', text: '' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('fs.read', () => ({ value: PLAN }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))

  await $.command.run(questCommand('First'))
  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Audit the login flow'))
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'oriana-1', reason: 'answer' } as never)
  let answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('Audit the login flow')

  await $.tool.call({ tool: 'Skill', skill: 'guildhall:quest', args: 'Second' } as never)
  answer = await $.command.run(tavernCommand)
  expect(answer.text).not.toContain('Audit the login flow')
  expect(answer.text).toMatch(/Earlier: First · 1 summoned/)

  await $.tool.call({ tool: 'Write', file_path: '/repo/docs/guildhall/plans/2026-10-10-a.md', content: '' } as never)
  await $.agent.spawn(spawnInput('guildhall:security-reviewer', 'Second quest task'))
  await $.tool.call({ tool: 'Write', file_path: '/repo/docs/guildhall/plans/2026-10-11-b.md', content: '' } as never)
  answer = await $.command.run(tavernCommand)
  expect(answer.text).not.toContain('Second quest task')
})

// ---------------------------------------------------------------- quest progress journey

import { focusOf, journeyNodes, parseProgress, progressBand, progressPathFromCommand } from './progress'

const milestone = (id: string, name: string, state: string, extra: Record<string, unknown> = {}) => ({
  id, name, goal: '', state, loop: null, pass: state === 'upcoming' ? 0 : 1,
  started_at: 0, finished_at: null, added_because: null, skipped_why: null, ...extra,
})
const task = (id: string, name: string, state: string, extra: Record<string, unknown> = {}) => ({
  id, milestone: 'build', pass: 1, name, state, who: null, added_because: null, started_at: 0, finished_at: null, ...extra,
})
const RECORD = {
  schema_version: 1, title: 'MCP agent access', repo: 'camp-planner', branch: 'feature/mcp', host: 'claude',
  plan_path: 'docs/guildhall/plans/2026-11-07-mcp.md', status: 'active', note: '', started_at: 0, updated_at: 0,
  milestones: [
    milestone('plan', 'Plan', 'done'),
    milestone('tests', 'Tests', 'done'),
    milestone('build', 'Build', 'current', { goal: 'Make the new tests pass', loop: { reason: 'reviews may block', limit: 2 } }),
    milestone('review', 'Review', 'upcoming', { loop: { reason: 'fixes are re-reviewed', limit: 2 } }),
    milestone('ui', 'UI', 'skipped'),
    milestone('pr', 'PR', 'upcoming'),
  ],
  tasks: [
    task('t0', 'Read consistency', 'done'), task('t1', 'Grocery tools', 'done'),
    task('t2', 'Photo replacement race', 'working', { who: 'Bruga' }), task('t3', 'Full suite green', 'upcoming'),
  ],
  waypoints: [
    { id: 'scope', need: 'Approve mode and scope', after: 'plan', state: 'done', planned: true, waiting_since: null, done_at: 0 },
    { id: 'accept', need: 'Muse/Dots acceptance', after: 'pr', state: 'upcoming', planned: true, waiting_since: null, done_at: null },
  ],
  loops: [],
}
const RECORD_PATH = '/repo/docs/guildhall/plans/2026-11-07-mcp/progress.json'
const PROGRESS_CMD = 'python3 /plugin/skills/guildhall-quest/scripts/progress.py --root /repo --plan docs/guildhall/plans/2026-11-07-mcp.md start build'

test('progress helpers read the record and the command that changed it', async () => {
  expect(progressPathFromCommand(PROGRESS_CMD)).toBe(RECORD_PATH)
  expect(progressPathFromCommand("python3 progress.py --plan 'docs/guildhall/plans/x.md' note hi")).toBe('docs/guildhall/plans/x/progress.json')
  expect(progressPathFromCommand('python3 review.py --plan docs/guildhall/plans/x.md')).toBe(undefined)
  expect(progressPathFromCommand('python3 progress.py --plan ../../etc/x.md start a')).toBe(undefined)
  expect(parseProgress(JSON.stringify(RECORD))?.title).toBe('MCP agent access')
  for (const bad of ['{not json', '{}', '[]', JSON.stringify({ ...RECORD, milestones: 'x' }), JSON.stringify({ ...RECORD, schema_version: 2 })]) {
    expect(parseProgress(bad)).toBe(undefined)
  }
  const hostile = parseProgress(JSON.stringify({ ...RECORD, title: 'Evil\u001b]0;pwned\u0007 title', note: 'x\u009b2J' }))!
  expect(hostile.title).toBe('Evil]0;pwned title')
  expect(hostile.note).toBe('x2J')
  const p = parseProgress(JSON.stringify(RECORD))!
  expect(journeyNodes(p).map(n => n.label)).toEqual(['Plan', 'Tests', 'Build', 'Review', 'PR', 'You'])
  expect(journeyNodes(p).map(n => n.badge)).toEqual(['', '', '↻', '↻', '', ''])
  const card = focusOf(p, null, 60_000)
  expect(card.kind).toBe('now')
  expect([card.done, card.total]).toEqual([2, 4])
  expect(progressBand(p, null)).toBe(undefined)
})

const progressHooks = (on: any, files: Record<string, string>, toolCall?: (...a: any[]) => unknown) => {
  on('command.run', () => ({ text: '' }))
  on('tool.call', toolCall ?? (() => ({ result: '', text: '' })))
  on('turn.complete', ($: unknown, e: { answer: string }) => ({ text: e.answer }))
  on('fs.read', ($: unknown, e: { path: string }) => {
    if (!(e.path in files)) throw new Error('ENOENT')
    return { value: files[e.path] }
  })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.surfaces', () => ({ value: [] }))
  on('ui.status', () => ({ value: undefined }))
}

test('a progress record draws the journey and the NOW card above the guild, on every surface', async ($, on) => {
  progressHooks(on, { [RECORD_PATH]: JSON.stringify(RECORD) })
  await $.command.run(questCommand('MCP agent access'))
  await $.tool.call({ tool: 'Bash', command: PROGRESS_CMD } as never)
  for (const surface of SURFACES) {
    const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface, component: 'Pane', requestId: 'guildhall', props: PANE })
    expect(await pane.find({ text: /2 of 5/ })).toBeDefined()
    expect(await pane.find({ text: /NOW/ })).toBeDefined()
    expect(await pane.find({ text: /Make the new tests pass/ })).toBeDefined()
    expect(await pane.find({ text: /2 of 4 tasks/ })).toBeDefined()
    expect(await pane.find({ text: /Photo replacement race/ })).toBeDefined()
    expect(await pane.find({ text: /You're needed after PR/ })).toBeDefined()
    expect(await pane.find({ text: /Muse\/Dots acceptance/ })).toBeDefined()
  }
  const answer = await $.command.run(tavernCommand)
  expect(answer.text).toContain('2 of 5')
})

test('a loop pass shows its pass number and why it repeated', async ($, on) => {
  const looped = {
    ...RECORD,
    milestones: RECORD.milestones.map(m => (m.id === 'build' ? { ...m, pass: 2 } : m)),
    tasks: [task('p1', 'Stale read fence', 'working', { pass: 2 })],
    loops: [{ milestone: 'build', pass: 2, why: 'security review found a stale read', at: 0, within_limit: true }],
  }
  progressHooks(on, { [RECORD_PATH]: JSON.stringify(looped) })
  await $.command.run(questCommand('MCP agent access'))
  await $.tool.call({ tool: 'Bash', command: PROGRESS_CMD } as never)
  const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'terminal', component: 'Pane', requestId: 'guildhall', props: PANE })
  expect(await pane.find({ text: /PASS 2 OF BUILD/ })).toBeDefined()
  expect(await pane.find({ text: /Why: security review found a stale read/ })).toBeDefined()
  expect(await pane.find({ text: /Expected — Build allows 2 passes/ })).toBeDefined()
  expect(await pane.find({ text: /Read consistency/ })).toBe(undefined)
})

test('an AskUserQuestion from Mordain turns the card into YOUR TURN until it is answered', async ($, on) => {
  let paneDuring: unknown
  progressHooks(on, { [RECORD_PATH]: JSON.stringify(RECORD) }, async (_: unknown, e: any) => {
    if (e.tool === 'AskUserQuestion') {
      const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'desktop', component: 'Pane', requestId: 'guildhall', props: PANE })
      paneDuring = await pane.find({ text: /YOUR TURN/ })
      const band = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'terminal', component: 'AbovePrompt', props: { hasSurvey: false } })
      expect(await band.find({ text: /⚑ Waiting on you: Ship it with hosted checks pending\?/ })).toBeDefined()
    }
    return { result: '', text: '' }
  })
  await $.command.run(questCommand('MCP agent access'))
  await $.tool.call({ tool: 'Bash', command: PROGRESS_CMD } as never)
  await $.tool.call({ tool: 'AskUserQuestion', questions: [{ question: 'Ship it with hosted checks pending?' }] } as never)
  expect(paneDuring).toBeDefined()
  const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'terminal', component: 'Pane', requestId: 'guildhall', props: PANE })
  expect(await pane.find({ text: /YOUR TURN/ })).toBe(undefined)
  expect(await pane.find({ text: /NOW/ })).toBeDefined()
})

test('a missing or corrupt record leaves the tavern as it was', async ($, on) => {
  progressHooks(on, { [RECORD_PATH]: '{not json' })
  await $.command.run(questCommand('MCP agent access'))
  await $.tool.call({ tool: 'Bash', command: PROGRESS_CMD } as never)
  await $.tool.call({ tool: 'Bash', command: PROGRESS_CMD.replace('2026-11-07-mcp', '2026-11-08-gone') } as never)
  const pane = await $.ui.mount({ plugin: 'guildhall-tavern', surface: 'terminal', component: 'Pane', requestId: 'guildhall', props: PANE })
  expect(await pane.find({ text: /MCP agent access/ })).toBeDefined()
  expect(await pane.find({ text: /NOW/ })).toBe(undefined)
})
