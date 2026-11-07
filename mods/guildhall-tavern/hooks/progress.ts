// The quest's own account of its progress: the record Mordain keeps with progress.py
// beside the plan scroll (docs/guildhall/plans/<slug>/progress.json). Pure helpers; the
// pane and band in register.tsx draw what these return. Mirrors the helper's views.

import type { Asking, ProgressMilestone, QuestProgress } from '../types'

const PLAN = /^(?:.*\/)?docs\/guildhall\/plans\/[^/]+\.md$/

/** `… progress.py [--root R] --plan P …` → where that record lives; undefined for any other command. */
export function progressPathFromCommand(command: string): string | undefined {
  if (!/(^|[\s/'"])progress\.py(\s|['"]|$)/.test(command)) return undefined
  const arg = (flag: string) => {
    const m = new RegExp(`${flag}(?:=|\\s+)(?:'([^']*)'|"([^"]*)"|(\\S+))`).exec(command)
    return m ? (m[1] ?? m[2] ?? m[3]) : undefined
  }
  const plan = arg('--plan')
  if (plan === undefined || !PLAN.test(plan) || plan.split('/').includes('..')) return undefined
  const root = arg('--root')
  const record = `${plan.slice(0, -'.md'.length)}/progress.json`
  return root !== undefined && !plan.startsWith('/') ? `${root.replace(/\/+$/, '')}/${record}` : record
}

// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f-\u009f]/g

/** A copy with control characters stripped from every string: the record on disk is untrusted. */
const scrub = (value: unknown): unknown =>
  typeof value === 'string' ? value.replace(CONTROL, '')
    : Array.isArray(value) ? value.map(scrub)
      : typeof value === 'object' && value !== null ? Object.fromEntries(Object.entries(value).map(([k, v]) => [k, scrub(v)]))
        : value

const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)

/** The record, shape-checked; undefined for anything the pane should not trust. */
export function parseProgress(text: string): QuestProgress | undefined {
  let value: unknown
  try {
    value = JSON.parse(text)
  } catch {
    return undefined
  }
  if (!isObject(value) || value.schema_version !== 1 || typeof value.title !== 'string') return undefined
  for (const key of ['milestones', 'tasks', 'waypoints', 'loops']) if (!Array.isArray(value[key])) return undefined
  const ms = value.milestones as unknown[]
  if (ms.length === 0 || !ms.every(m => isObject(m) && typeof m.id === 'string' && typeof m.name === 'string' && typeof m.state === 'string')) {
    return undefined
  }
  if (!(value.tasks as unknown[]).every(t => isObject(t) && typeof t.name === 'string' && typeof t.state === 'string')) return undefined
  if (!(value.waypoints as unknown[]).every(w => isObject(w) && typeof w.need === 'string' && typeof w.state === 'string')) return undefined
  return scrub(value) as QuestProgress
}

export const elapsedShort = (ms: number) => {
  const s = Math.max(0, Math.floor(ms / 1000))
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
  return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`
}
const since = (now: number, at: number | null | undefined) => elapsedShort(now - (at ?? now / 1000) * 1000)

export function counted(p: QuestProgress): { done: number; total: number } {
  const live = p.milestones.filter(m => m.state !== 'skipped')
  return { done: live.filter(m => m.state === 'done').length, total: live.length }
}

export type NodeTone = 'done' | 'now' | 'loop' | 'you' | 'dim'
export type JourneyNode = { kind: 'milestone' | 'waypoint'; label: string; tone: NodeTone; glyph: string; badge: string }

export function journeyNodes(p: QuestProgress): JourneyNode[] {
  const nodes: JourneyNode[] = []
  for (const m of p.milestones) {
    if (m.state === 'skipped') continue
    const repeat = (m.pass ?? 0) >= 2
    const badge = repeat ? `↻${m.pass}` : m.loop ? '↻' : ''
    const tone: NodeTone = m.state === 'done' ? 'done' : m.state === 'current' ? (repeat ? 'loop' : 'now') : 'dim'
    const glyph = m.state === 'done' ? '●' : m.state === 'current' ? '◉' : '○'
    nodes.push({ kind: 'milestone', label: m.name, tone, glyph, badge })
    if (p.waypoints.some(w => w.after === m.id && w.state !== 'done')) {
      nodes.push({ kind: 'waypoint', label: 'You', tone: 'you', glyph: '⚑', badge: '' })
    }
  }
  return nodes
}

export type FocusTask = { name: string; state: string; who: string }
export type Focus = {
  kind: 'now' | 'loop' | 'you' | 'done' | 'next'
  label: string
  title: string
  goal: string
  lines: string[]
  tasks: FocusTask[]
  done: number
  total: number
  meta: string
}

const current = (p: QuestProgress): ProgressMilestone | undefined => p.milestones.find(m => m.state === 'current')

/** What the card says: your turn wins, then the current milestone (a loop pass says why), then next or done. */
export function focusOf(p: QuestProgress, asking: Asking | null, now: number): Focus {
  const base = { goal: '', lines: [] as string[], tasks: [] as FocusTask[], done: 0, total: 0, meta: '' }
  const waiting = p.waypoints.filter(w => w.state === 'waiting')
  if (asking !== null || waiting.length > 0) {
    const w = waiting.sort((a, b) => (b.waiting_since ?? 0) - (a.waiting_since ?? 0))[0]
    const need = asking?.need ?? w?.need ?? 'Mordain has a question'
    const planned = asking === null && w?.planned === true
    const waitingFor = asking !== null ? elapsedShort(now - asking.since) : since(now, w?.waiting_since)
    return {
      ...base, kind: 'you', label: 'YOUR TURN', title: need,
      lines: ['Mordain is waiting for your answer.'], meta: `waiting ${waitingFor} · ${planned ? 'planned' : 'unplanned'}`,
    }
  }
  const m = current(p)
  if (p.status !== 'active' || (m === undefined && p.milestones.every(x => x.state === 'done' || x.state === 'skipped'))) {
    const abandoned = p.status === 'abandoned'
    return { ...base, kind: 'done', label: abandoned ? 'ABANDONED' : 'DONE', title: abandoned ? 'Quest abandoned' : 'Quest complete' }
  }
  if (m === undefined) {
    const next = p.milestones.find(x => x.state === 'upcoming') ?? p.milestones[0]!
    return { ...base, kind: 'next', label: 'UP NEXT', title: next.name, goal: next.goal ?? '' }
  }
  const pass = Math.max(1, m.pass ?? 1)
  const tasks = p.tasks.filter(t => t.milestone === m.id && (t.pass ?? 1) === pass)
  const card: Focus = {
    ...base, kind: 'now', label: 'NOW', title: m.name, goal: m.goal ?? '',
    tasks: tasks.map(t => ({
      name: t.name,
      state: t.state,
      who: t.state === 'working' ? [t.who ?? '', since(now, t.started_at)].filter(Boolean).join(' ') : '',
    })),
    done: tasks.filter(t => t.state === 'done').length,
    total: tasks.length,
    meta: since(now, m.started_at),
  }
  if (pass >= 2) {
    const loop = [...p.loops].reverse().find(l => l.milestone === m.id)
    const limit = m.loop?.limit
    card.kind = 'loop'
    card.label = `NOW · PASS ${pass} OF ${m.name.toUpperCase()}`
    if (loop) card.lines.push(`Why: ${loop.why}`)
    card.lines.push(
      limit === undefined ? 'Not a planned repeat.'
        : pass <= limit ? `Expected — ${m.name} allows ${limit} passes.`
          : `This is beyond the planned ${limit} passes.`,
    )
  }
  return card
}

/** The lines under the card: your next touchpoint, what may repeat, Mordain's note. */
export function footerRows(p: QuestProgress): { tone: NodeTone; text: string }[] {
  const rows: { tone: NodeTone; text: string }[] = []
  const names = new Map(p.milestones.map(m => [m.id, m.name]))
  const ahead = p.waypoints.filter(w => w.state === 'upcoming')
  if (ahead.length > 0) {
    const first = ahead[0]!
    const later = ahead.length > 1 ? ` · ${ahead.length} checks` : ''
    rows.push({ tone: 'you', text: `⚑ You're needed after ${names.get(first.after) ?? first.after}${later}` })
    rows.push({ tone: 'dim', text: `  ${first.need}` })
  }
  const repeat = p.milestones.filter(m => m.loop && (m.state === 'upcoming' || m.state === 'current'))
  if (repeat.length > 0) {
    const who = repeat.length === 1 ? repeat[0]!.name : `${repeat.slice(0, -1).map(m => m.name).join(', ')} and ${repeat.at(-1)!.name}`
    const limits = new Set(repeat.map(m => m.loop!.limit))
    rows.push({ tone: 'dim', text: `↻ ${who} may repeat${limits.size === 1 ? ` · up to ${[...limits][0]} passes` : ''}` })
  }
  if (p.note) rows.push({ tone: 'dim', text: p.note })
  return rows
}

/** The band's amber line when the quest waits on the person; undefined otherwise. */
export function progressBand(p: QuestProgress | null, asking: Asking | null): string | undefined {
  if (asking !== null) return `⚑ Waiting on you: ${asking.need}`
  const w = p?.waypoints.find(x => x.state === 'waiting')
  return w ? `⚑ Waiting on you: ${w.need}` : undefined
}

/** The journey as three rows of text cells (path, labels, badges), spread across `width`. */
export function journeyRows(nodes: JourneyNode[], width: number): { cells: { text: string; tone: NodeTone }[][] } {
  let shown = nodes
  let labelLen = 12
  const cellsFor = (len: number) => shown.map(n => Math.max(2, Math.min(n.label.length, len) + 1, n.badge.length + 1))
  let cells = cellsFor(labelLen)
  for (const len of [12, 6, 4, 3, 0]) {
    labelLen = len
    cells = cellsFor(len)
    if (cells.reduce((a, b) => a + b, 0) + 1 <= width) break
  }
  if (cells.reduce((a, b) => a + b, 0) + 1 > width) {
    const keep = Math.max(1, Math.floor((width - 1) / 2))
    const at = Math.max(0, shown.findIndex(n => n.tone === 'now' || n.tone === 'loop'))
    const start = Math.max(0, Math.min(at - Math.floor(keep / 2), shown.length - keep))
    shown = shown.slice(start, start + keep)
    cells = shown.map(() => 2)
  }
  const spare = width - 1 - cells.reduce((a, b) => a + b, 0)
  const gaps = cells.length - 1
  if (spare > 0 && gaps > 0) cells = cells.map((w, i) => (i < gaps ? w + Math.floor(spare / gaps) + (i < spare % gaps ? 1 : 0) : w))
  const path: { text: string; tone: NodeTone }[] = [{ text: ' ', tone: 'dim' }]
  const labels: { text: string; tone: NodeTone }[] = [{ text: ' ', tone: 'dim' }]
  const badges: { text: string; tone: NodeTone }[] = [{ text: ' ', tone: 'loop' }]
  shown.forEach((n, i) => {
    const w = cells[i]!
    const last = i === shown.length - 1
    const solid = n.kind === 'milestone' && n.tone === 'done'
    path.push({ text: n.glyph, tone: n.tone })
    if (!last) path.push({ text: (solid ? '━' : '┈').repeat(w - 1), tone: solid ? 'done' : 'dim' })
    const label = labelLen === 0 ? '' : n.label.length > w - 1 ? `${n.label.slice(0, Math.max(0, w - 2))}…` : n.label
    labels.push({ text: label.padEnd(w), tone: n.tone })
    badges.push({ text: n.badge.padEnd(w), tone: 'loop' })
  })
  return { cells: [path, labels, badges] }
}
