// The guild as the pane draws it: one entry per agent in plugin/agents/,
// voiced from plugin/CHARACTERS.md. `{x}` in a line is the deed's target.

export type Phase = 'build' | 'review' | 'closer' | 'standalone' | 'hireling'

export type Deed = 'read' | 'search' | 'write' | 'run' | 'ask' | 'ledger' | 'idle'

export type Character = {
  name: string
  title: string
  icon: string
  phase: Phase
  catchphrase: string
  lines: Partial<Record<Deed, string>>
}

export const PHASES: { phase: Phase; label: string }[] = [
  { phase: 'build', label: 'Build chain' },
  { phase: 'review', label: 'Review fan-out' },
  { phase: 'closer', label: 'Closer' },
  { phase: 'standalone', label: 'Field work' },
  { phase: 'hireling', label: 'Hirelings' },
]

export const KEEPER: Character = {
  name: 'Mordain',
  title: 'the Keeper',
  icon: '🧙',
  phase: 'standalone',
  catchphrase: 'First, the plan. Then, the adventurers.',
  lines: {
    read: 'reads the whole scroll before speaking: {x}',
    search: 'consults the archives for {x}',
    write: 'inks the plan: {x}',
    run: 'sends a runner on an errand: {x}',
    ask: 'awaits the patron’s word',
    ledger: 'updates the ledger',
    idle: 'rests in the high chair by the hearth',
  },
}

export const ROSTER: Record<string, Character> = {
  'prototype-builder': {
    name: 'Pip', title: 'the Scout', icon: '🎒', phase: 'standalone',
    catchphrase: 'Here, it runs! Don’t ask what happens on Tuesday.',
    lines: {
      read: 'peeks at {x} between bites', search: 'rummages around for {x}',
      write: 'lashes together {x}', run: 'pokes it to see if it runs: {x}',
      idle: 'chews thoughtfully',
    },
  },
  'test-author': {
    name: 'Seraphine', title: 'the Oracle', icon: '🔮', phase: 'build',
    catchphrase: 'The spec is written. The test is its shadow.',
    lines: {
      read: 'reads the spec as scripture: {x}', search: 'seeks the Expectation of {x}',
      write: 'inscribes a prophecy: {x}', run: 'watches the prophecy fail, as foretold: {x}',
      idle: 'meditates on the spec, eyes averted from the code',
    },
  },
  'feature-implementer': {
    name: 'Bruga', title: 'the Smith', icon: '🔨', phase: 'build',
    catchphrase: 'Show me the blueprint.',
    lines: {
      read: 'studies the blueprint: {x}', search: 'sorts the scrap pile for {x}',
      write: 'forges {x}', run: 'quenches the blade: {x}',
      idle: 'stokes the forge',
    },
  },
  refactorer: {
    name: 'Tink', title: 'the Enchanter', icon: '✨', phase: 'build',
    catchphrase: 'Same stone. Better setting.',
    lines: {
      read: 'turns {x} in the light', search: 'hunts loose settings in {x}',
      write: 'resets the stone: {x}', run: 'checks the shine holds: {x}',
      idle: 'polishes quietly',
    },
  },
  'architecture-reviewer': {
    name: 'Aldric', title: 'the Cartographer', icon: '📐', phase: 'build',
    catchphrase: 'Three paths lie open. Only one leads forward without debt.',
    lines: {
      read: 'surveys the terrain of {x}', search: 'traces the roads to {x}',
      run: 'paces the distance: {x}', idle: 'weighs three paths',
    },
  },
  'debug-investigator': {
    name: 'Kael', title: 'the Tracker', icon: '🏹', phase: 'standalone',
    catchphrase: 'I know WHY. What you do next is not my tale to tell.',
    lines: {
      read: 'reads the tracks in {x}', search: 'follows the trail of {x}',
      write: 'marks the trail: {x}', run: 'sets a snare: {x}',
      idle: 'kneels to study the ground',
    },
  },
  'ui-test-author': {
    name: 'Vera', title: 'the Playwright', icon: '🎭', phase: 'review',
    catchphrase: 'The curtain has risen. Let us see if the play matches the script.',
    lines: {
      read: 'reads the script: {x}', search: 'scouts the stage for {x}',
      write: 'writes the scene: {x}', run: 'raises the curtain: {x}',
      idle: 'rehearses the blocking',
    },
  },
  'security-reviewer': {
    name: 'Oriana', title: 'the Watcher', icon: '🦉', phase: 'review',
    catchphrase: 'Trust no path you have not walked.',
    lines: {
      read: 'walks the wall past {x}', search: 'searches for unwatched gates: {x}',
      run: 'tests the lock: {x}', idle: 'keeps the watch',
    },
  },
  'docs-writer': {
    name: 'Cassian', title: 'the Scribe', icon: '📖', phase: 'review',
    catchphrase: 'A song is only as true as the singer who remembers it.',
    lines: {
      read: 'reads the old songs: {x}', search: 'seeks the verse about {x}',
      write: 'sets down the verse: {x}', run: 'checks the tune: {x}',
      idle: 'sharpens the quill',
    },
  },
  'observability-reviewer': {
    name: 'Vance', title: 'the Chronicler', icon: '📜', phase: 'review',
    catchphrase: 'What happened, and would we know if it happened again?',
    lines: {
      read: 'reads the chronicle of {x}', search: 'searches for unrecorded deeds: {x}',
      run: 'listens for echoes: {x}', idle: 'asks: would we know?',
    },
  },
  'reliability-reviewer': {
    name: 'Thalia', title: 'the Stormwarden', icon: '⚡', phase: 'review',
    catchphrase: 'The wind will come. The wall must hold.',
    lines: {
      read: 'tests the walls of {x}', search: 'searches for cracks: {x}',
      run: 'summons a squall: {x}', idle: 'reads the sky',
    },
  },
  'performance-reviewer': {
    name: 'Cassia', title: 'the Smith of Cycles', icon: '⏳', phase: 'review',
    catchphrase: 'Every cycle costs something. Pay it knowingly.',
    lines: {
      read: 'counts the cycles in {x}', search: 'hunts hot loops: {x}',
      run: 'times the forge: {x}', idle: 'weighs the cost',
    },
  },
  'ops-readiness-reviewer': {
    name: 'Garran', title: 'the Quartermaster', icon: '📦', phase: 'review',
    catchphrase: 'No army marches without a wagon train.',
    lines: {
      read: 'inspects the supply lines in {x}', search: 'inventories {x}',
      run: 'loads the wagon: {x}', idle: 'drafts the marching orders',
    },
  },
  'migration-safety-reviewer': {
    name: 'Ysolde', title: 'the Gravedigger', icon: '🪦', phase: 'review',
    catchphrase: 'Some doors close behind you. Be sure before you walk through.',
    lines: {
      read: 'reads the gravestones of {x}', search: 'searches for one-way doors: {x}',
      run: 'tests the ground: {x}', idle: 'weighs what cannot be undone',
    },
  },
  'accessibility-reviewer': {
    name: 'Lior', title: 'the Lampbearer', icon: '🏮', phase: 'review',
    catchphrase: 'A door without a handle is a wall.',
    lines: {
      read: 'carries the lamp through {x}', search: 'looks for doors without handles: {x}',
      run: 'walks the path in the dark: {x}', idle: 'trims the wick',
    },
  },
  'pr-author': {
    name: 'Rook', title: 'the Herald', icon: '📯', phase: 'closer',
    catchphrase: 'The deed is done. Now let the tale be told precisely.',
    lines: {
      read: 'reviews the deeds in {x}', search: 'gathers witnesses: {x}',
      write: 'drafts the proclamation: {x}', run: 'consults the ledger: {x}',
      idle: 'clears the throat',
    },
  },
  'fog-cartographer': {
    name: 'Wren', title: 'the Wayfinder', icon: '🧭', phase: 'closer',
    catchphrase: 'I mark what the scouts saw. I do not redraw coastlines I haven’t walked.',
    lines: {
      read: 'reads the scouts’ notes: {x}', search: 'seeks the fog line near {x}',
      write: 'marks the map: {x}', run: 'checks the bearings: {x}',
      idle: 'watches the fog',
    },
  },
  'plugin-validator': {
    name: 'Tabs', title: 'the Apprentice', icon: '🔩', phase: 'standalone',
    catchphrase: 'Small checks, small surprises.',
    lines: {
      read: 'checks {x}, line by line', search: 'counts the rivets: {x}',
      write: 'notes it down: {x}', run: 'runs the checks: {x}',
      idle: 'ticks the checklist',
    },
  },
  'model-echo': {
    name: 'Echo', title: 'the Diagnostic', icon: '🔔', phase: 'standalone',
    catchphrase: 'An echo is a hint, never proof.',
    lines: { idle: 'rings once and listens' },
  },
}

const GENERIC: Record<Deed, string> = {
  read: 'reads {x}',
  search: 'searches for {x}',
  write: 'scribbles notes: {x}',
  run: 'runs a command: {x}',
  ask: 'asks the patron a question',
  ledger: 'updates the ledger',
  idle: 'is at work',
}

/** A subagent type the guild does not employ: `Explore`, `general-purpose`. */
export function hireling(subagentType: string): Character {
  return {
    name: shorten(subagentType, 40),
    title: 'hireling',
    icon: '🧳',
    phase: 'hireling',
    catchphrase: 'Paid in full.',
    lines: {},
  }
}

/** `guildhall:test-author` → `test-author`; undefined for a non-guild agent. */
export function guildRole(subagentType: string): string | undefined {
  const role = subagentType.startsWith('guildhall:')
    ? subagentType.slice('guildhall:'.length)
    : subagentType
  return role in ROSTER ? role : undefined
}

export function characterOf(role: string): Character {
  return ROSTER[role] ?? hireling(role)
}

/** One line of plain text: control characters (terminal escapes) dropped, cut to `max`. */
export const shorten = (text: string, max = 48) => {
  const one = text.replace(/[\u0000-\u001f\u007f-\u009f\u200e\u200f\u202a-\u202e\u2066-\u2069]+/g, ' ').replace(/\s+/g, ' ').trim()
  return one.length > max ? one.slice(0, max - 1) + '…' : one
}

// A URL's query and fragment can carry tokens: only its host and path are shown.
const withoutQuery = (url: string) => {
  try {
    const parsed = new URL(url)
    return parsed.origin + parsed.pathname // drops user:pass@ too
  } catch {
    return url.split(/[?#]/)[0]?.replace(/\/\/[^/@]*@/, '//') ?? ''
  }
}

const basename = (path: string) => shorten(path.split('/').filter(Boolean).pop() ?? path)

/** Which kind of deed a tool call is, and what it is done to. */
export function classify(
  tool: string,
  input: Record<string, unknown>,
): { deed: Deed; target: string } {
  const str = (key: string) => (typeof input[key] === 'string' ? (input[key] as string) : '')
  switch (tool) {
    case 'Read':
    case 'NotebookRead':
      return { deed: 'read', target: basename(str('file_path') || str('notebook_path')) }
    case 'Write':
    case 'Edit':
    case 'MultiEdit':
    case 'NotebookEdit':
      return { deed: 'write', target: basename(str('file_path') || str('notebook_path')) }
    case 'Grep':
    case 'Glob':
      return { deed: 'search', target: shorten(str('pattern'), 32) }
    case 'WebFetch':
      return { deed: 'search', target: shorten(withoutQuery(str('url')), 40) }
    case 'WebSearch':
      return { deed: 'search', target: shorten(str('query'), 40) }
    case 'Bash':
      // A bare command can hold a credential; only the call's own description is shown.
      return { deed: 'run', target: shorten(str('description'), 40) }
    case 'AskUserQuestion':
      return { deed: 'ask', target: '' }
    case 'TodoWrite':
    case 'TaskCreate':
    case 'TaskUpdate':
      return { deed: 'ledger', target: '' }
    default:
      return { deed: 'idle', target: shorten(tool, 40) }
  }
}

/** The in-character line for a character doing one deed. */
export function flavor(who: Character, deed: Deed, target: string): string {
  const template = who.lines[deed] ?? GENERIC[deed]
  // A deed with no target to show drops its trailing `: {x}`.
  const line = target ? template.replace('{x}', target) : template.replace(/:\s*\{x\}$/, '').replace('{x}', 'something')
  return `${who.name} ${line}`
}
