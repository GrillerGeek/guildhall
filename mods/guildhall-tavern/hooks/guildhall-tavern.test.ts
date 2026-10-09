import { expect, test } from 'claude-code/testing'

import { classify, flavor, characterOf, guildRole } from './roster'

const SURFACES = ['terminal', 'desktop'] as const
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
  expect(classify('Read', { file_path: '/repo/evil\u001b]52;c;aGk=\u0007.md' }).target).toBe('evil ]52;c;aGk= .md')
})
