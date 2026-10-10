// The end-of-quest recap: who answered, how long each phase held the road, and the
// gating verdicts Mordain recorded in the plan scroll's `## Reviewers selected`.

import type { GuildMember, ReviewerVerdict } from '../types'
import { PHASES, ROSTER, characterOf, shorten } from './roster'
import type { Phase } from './roster'

/** Where Mordain keeps plan scrolls; the folder's README is not one. */
export const isPlanScroll = (path: string) =>
  /(^|\/)docs\/guildhall\/plans\/[^/]+\.md$/.test(path) && !/\/README\.md$/i.test(path)

/** `Oriana`, `oriana`, `security-reviewer` → `security-reviewer`; undefined for anyone else. */
export function roleByName(name: string): string | undefined {
  const wanted = name.trim().replace(/^`|`$/g, '').toLowerCase()
  if (Object.hasOwn(ROSTER, wanted)) return wanted
  return Object.keys(ROSTER).find(role => ROSTER[role]?.name.toLowerCase() === wanted)
}

/** The bullets under `## Reviewers selected`, up to the next `## ` heading. */
export function reviewerBullets(markdown: string): string[] {
  const lines = markdown.split(/\r?\n/)
  const start = lines.findIndex(l => /^##\s+Reviewers selected\s*$/i.test(l))
  if (start < 0) return []
  const bullets: string[] = []
  for (const line of lines.slice(start + 1)) {
    if (/^##\s/.test(line)) break
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line)
    if (bullet?.[1]) bullets.push(bullet[1])
  }
  return bullets
}

/**
 * One bullet → the verdicts it records. Plan scrolls come in two dialects:
 *
 *   template:  Vance (`observability-reviewer`) — skipped — docs-only change
 *              Oriana (`security-reviewer`) — fires
 *   freeform:  Oriana security: API credential handling, untrusted input
 *              Skip Vera/Lior: no visual UI changes.
 *
 * A bullet naming nobody on the roster (`Always-on:` stray text) yields [].
 */
export function parseReviewerLine(line: string): ReviewerVerdict[] {
  // "Skip Ysolde: no migration. Skip Vera/Lior: no UI." is one bullet holding two clauses.
  const clauses = line.split(/(?<=[.;])\s+(?=skip\b)/i)
  return clauses.flatMap(parseClause)
}

function parseClause(line: string): ReviewerVerdict[] {
  // Names are read from the head only, so a reviewer mentioned in a reason is not a verdict.
  // A bullet with no separator ("Tink only if a refactor is needed") records no verdict.
  const dashed = line.split(/\s+[—–]\s+/)
  const colon = line.indexOf(':')
  const [head, verdict, reason] =
    dashed.length > 1
      ? [dashed[0] ?? '', dashed[1] ?? '', dashed.slice(2).join(' — ')]
      : colon > 0
        ? [line.slice(0, colon), '', line.slice(colon + 1)]
        : ['', '', '']
  const fired = !/^\s*skip\b/i.test(head) && !/^skip(ped|s)?\b/i.test(verdict.trim())
  const roles = new Set(head.split(/[\s/,()`]+/).flatMap(word => roleByName(word) ?? []))
  return [...roles].map(role => ({ role, fired, reason: reason.trim() }))
}

/** Every verdict in the section; a later bullet about the same role wins. */
export function reviewerVerdicts(markdown: string): ReviewerVerdict[] {
  const byRole = new Map<string, ReviewerVerdict>()
  for (const bullet of reviewerBullets(markdown)) {
    for (const v of parseReviewerLine(bullet)) {
      byRole.set(v.role, { ...v, reason: shorten(v.reason, 60) })
    }
  }
  return [...byRole.values()]
}

/** The frontmatter's `status:` (in_progress, completed, abandoned), if the scroll has one. */
export function planStatus(markdown: string): string | undefined {
  const front = /^---\r?\n([\s\S]*?)\r?\n---/.exec(markdown)?.[1]
  const status = front && /^status:\s*([\w-]+)/m.exec(front)?.[1]
  return status || undefined
}

/** The phase a member works in: its root's, so a hireling counts with whoever hired it. */
export function rootPhase(list: GuildMember[], m: GuildMember): Phase {
  let at = m
  for (let hops = 0; at.parentId !== undefined && hops < list.length; hops++) {
    const parent = list.find(p => p.id === at.parentId)
    if (parent === undefined) break
    at = parent
  }
  return characterOf(at.role).phase
}

/**
 * Wall-clock time each phase held the road: first summons to last return, so a
 * parallel fan-out counts once, not once per reviewer. A child counts with its root.
 */
export function phaseSpans(list: GuildMember[], now: number): { phase: Phase; label: string; ms: number }[] {
  return PHASES.flatMap(p => {
    const group = list.filter(m => rootPhase(list, m) === p.phase)
    if (group.length === 0) return []
    const start = Math.min(...group.map(m => m.startedAt))
    const end = Math.max(...group.map(m => m.endedAt ?? now))
    return [{ phase: p.phase, label: p.label, ms: Math.max(0, end - start) }]
  })
}
