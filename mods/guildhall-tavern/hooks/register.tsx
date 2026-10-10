import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderChildren } from 'claude-code'

import type { ChronicleEntry, GuildMember, GuildQuest, Recap } from '../types'
import { isPlanScroll, phaseSpans, planStatus, reviewerVerdicts, rootPhase } from './recap'
import { KEEPER, PHASES, characterOf, classify, flavor, guildRole, shorten } from './roster'
import type { Character } from './roster'

const PANE = 'guildhall'
const TITLE = 'The Tavern'
const SPINNER = ['◐', '◓', '◑', '◒']
const CHRONICLE_LENGTH = 8
const MEMBER_LIMIT = 40

const quest = atom({ plugin: 'guildhall-tavern', key: 'quest' } as const, null as GuildQuest | null)
const members = atom({ plugin: 'guildhall-tavern', key: 'members' } as const, [] as GuildMember[])
const chronicle = atom({ plugin: 'guildhall-tavern', key: 'chronicle' } as const, [] as ChronicleEntry[])
const tick = atom({ plugin: 'guildhall-tavern', key: 'tick' } as const, 0)
const recap = atom({ plugin: 'guildhall-tavern', key: 'recap' } as const, null as Recap | null)
// Set once the person moves on from a settled quest: the band has said its piece.
const bandQuiet = atom({ plugin: 'guildhall-tavern', key: 'bandQuiet' } as const, false)

// Which surfaces have asked this module to draw the pane since it loaded: diagnostics only.
const drawnOn = new Set<string>()

async function whereText($: EngineInterface): Promise<string> {
  const surfaces = await $.session.surfaces()
  const pane = (await $.ui.panes()).find(p => p.id === PANE)
  const state = pane ? `placed ${pane.isPlaced}, shown ${pane.isShown}` : 'not open'
  const drawn = drawnOn.size > 0 ? [...drawnOn].join(', ') : 'none yet'
  return `Surfaces attached: ${surfaces.join(', ') || 'none'} · pane: ${state} · drawn on: ${drawn}`
}

const isQuestCommand = (command: string) => command === 'quest' || command === 'guildhall:quest'

const elapsed = (ms: number) => {
  const s = Math.max(0, Math.floor(ms / 1000))
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m${String(s % 60).padStart(2, '0')}s`
}

const memberCharacter = (m: GuildMember): Character => characterOf(m.role)

async function record($: EngineInterface, icon: string, text: string) {
  await update($, chronicle, list => [...(list ?? []), { at: Date.now(), icon, text }].slice(-CHRONICLE_LENGTH))
}

async function beginQuest($: EngineInterface, title: string) {
  await update($, quest, () => ({
    title,
    startedAt: Date.now(),
    keeperLine: `${KEEPER.name} reads the whole scroll before speaking`,
    isKeeperBusy: true,
  }))
  await update($, members, () => [])
  await update($, chronicle, () => [])
  await update($, recap, () => null)
  await update($, bandQuiet, () => false)
  await record($, KEEPER.icon, `${KEEPER.name}: “${KEEPER.catchphrase}”`)
  // A surface that cannot seat the pane leaves the ledger kept; /guildhall-tavern opens it later.
  await $.ui.open({ id: PANE, title: TITLE }).catch(() => undefined)
  await refreshStatus($)
}

/**
 * A guild agent dispatched outside /quest still gets a hall to work in. Created only
 * when none exists, in one write, so agents dispatched together share one quest.
 */
async function ensureQuest($: EngineInterface, title: string) {
  await update($, quest, current =>
    current ?? {
      title,
      startedAt: Date.now(),
      keeperLine: `${KEEPER.name} sends adventurers out on an errand`,
      isKeeperBusy: true,
    },
  )
  await $.ui.open({ id: PANE, title: TITLE }).catch(() => undefined)
}

async function setKeeper($: EngineInterface, line: string, isKeeperBusy = true) {
  await update($, quest, q => (q ? { ...q, keeperLine: line, isKeeperBusy } : q))
  await refreshStatus($)
}

type RecapRow = { text: string; tone: 'head' | 'ok' | 'skip' | 'warn' | 'dim' }

const fileName = (path: string) => shorten(path.split('/').pop() ?? path, 60)

/** The recap as rows both the pane and the text fallback draw; none while anyone works. */
function recapRows(r: Recap | null, list: GuildMember[], now: number): RecapRow[] {
  if (r === null || list.some(m => m.status === 'working')) return []
  const fallen = list.filter(m => m.status === 'fallen').length
  const icons = list.map(m => memberCharacter(m).icon).join('')
  const rows: RecapRow[] = [
    { text: `Recap · ${r.status ?? 'the hall is quiet'}`, tone: 'head' },
    { text: `  Summoned ${icons || 'nobody'} · ${list.length} answered, ${fallen} fallen`, tone: 'dim' },
  ]
  const spans = phaseSpans(list, now)
  if (spans.length > 0) {
    rows.push({ text: `  Time     ${spans.map(s => `${s.label} ${elapsed(s.ms)}`).join(' · ')}`, tone: 'dim' })
  }
  const summoned = new Set(list.map(m => m.role))
  for (const v of r.reviewers) {
    const who = characterOf(v.role)
    const label = `${who.icon} ${who.name}`
    const why = v.reason ? ` — ${v.reason}` : ''
    if (v.fired && summoned.has(v.role)) rows.push({ text: `  ✓ ${label}${why}`, tone: 'ok' })
    else if (!v.fired && !summoned.has(v.role)) rows.push({ text: `  · ${label} skipped${why}`, tone: 'skip' })
    else if (v.fired) rows.push({ text: `  ⚠ ${label} planned, never summoned${why}`, tone: 'warn' })
    else rows.push({ text: `  ⚠ ${label} skipped in the scroll, yet summoned${why}`, tone: 'warn' })
  }
  const scroll =
    r.planPath === undefined
      ? 'no plan scroll (fast lane or prototype)'
      : r.problem !== undefined
        ? `could not read ${fileName(r.planPath)}: ${r.problem}`
        : `Scroll ${fileName(r.planPath)}`
  rows.push({ text: `  ${scroll}`, tone: 'dim' })
  return rows
}

/** Mordain's turn ended with nobody in the field: read the scroll and settle the recap. */
async function settle($: EngineInterface) {
  const q = await read($, quest)
  const list = (await read($, members)) ?? []
  if (q === null || list.some(m => m.status === 'working')) return
  const planPath = q.planPath
  let next: Recap = { at: Date.now(), planPath, reviewers: [] }
  if (planPath !== undefined) {
    try {
      const text = await $.fs.read(planPath)
      next = { ...next, status: planStatus(text), reviewers: reviewerVerdicts(text) }
    } catch (error) {
      next = { ...next, problem: shorten(error instanceof Error ? error.message : String(error), 60) }
    }
  }
  await update($, recap, () => next)
}

/**
 * The band's one line, for when the pane is out of view: the phases at work and
 * who is in them, else Mordain's own line, else a pointer to the recap.
 */
function bandText(q: GuildQuest | null, list: GuildMember[], r: Recap | null, isQuiet: boolean): string | undefined {
  if (q === null || isQuiet) return undefined
  const working = list.filter(m => m.status === 'working')
  if (working.length > 0) {
    const phases = PHASES.flatMap(p => {
      const here = working.filter(m => rootPhase(list, m) === p.phase)
      return here.length > 0 ? [`${p.label} · ${here.map(m => memberCharacter(m).icon).join('')} at work`] : []
    })
    return `⚔ ${phases.join(' · ')}`
  }
  if (r !== null) return `⚔ ${shorten(q.title, 40)} · recap ready${r.status ? ` (${r.status})` : ''}`
  return `⚔ ${shorten(q.title, 40)} · ${KEEPER.icon} ${q.keeperLine}`
}

/** The pane is in view somewhere: the band would only repeat it. */
async function isPaneInView($: EngineInterface): Promise<boolean> {
  const pane = (await $.ui.panes()).find(p => p.id === PANE)
  return pane !== undefined && pane.isShown && pane.isPlaced
}

/** The tavern as plain text: the command's answer where no surface draws the pane. */
function tavernText(q: GuildQuest | null, list: GuildMember[], log: ChronicleEntry[], r: Recap | null, now: number): string {
  if (q === null) return `${KEEPER.icon} The tavern is quiet. ${KEEPER.name} waits by the hearth.`
  const mark = (m: GuildMember) => (m.status === 'working' ? '▶' : m.status === 'done' ? '✓' : '✗')
  const lines = [
    `⚔ ${q.title} (${elapsed(now - q.startedAt)} on the road)`,
    `${q.isKeeperBusy ? '▶' : '·'} ${KEEPER.icon} ${KEEPER.name} ${KEEPER.title}: ${q.keeperLine}`,
  ]
  for (const p of PHASES) {
    const group = list.filter(m => memberCharacter(m).phase === p.phase)
    if (group.length === 0) continue
    lines.push(`  ${p.label}`)
    for (const m of group) {
      const who = memberCharacter(m)
      lines.push(`    ${mark(m)} ${who.icon} ${who.name} ${who.title} (${m.role}, ${elapsed((m.endedAt ?? now) - m.startedAt)}, ${m.deeds} deeds): ${m.line}`)
    }
  }
  lines.push(...recapRows(r, list, now).map(row => `  ${row.text}`))
  if (log.length > 0) lines.push('  Chronicle', ...log.map(entry => `    ${entry.icon} ${entry.text}`))
  return lines.join('\n')
}

/** One status-line entry that follows the quest on every surface, pane or no pane. */
async function refreshStatus($: EngineInterface) {
  const q = await read($, quest)
  if (q === null) return $.ui.status(undefined)
  const list = (await read($, members)) ?? []
  const working = list.filter(m => m.status === 'working')
  if (working.length > 0) {
    return $.ui.status(`⚔ ${working.map(m => `${memberCharacter(m).icon} ${m.line}`).join(' · ')}`)
  }
  $.ui.status(`⚔ ${KEEPER.icon} ${q.keeperLine}${list.length > 0 ? ` · ${list.length} summoned, all returned` : ''}`)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'guildhall-tavern',
      description: 'Open the Guildhall tavern: who is on the quest and what they are doing',
    })
    // Spinners and running clocks advance only while someone is at work.
    $.clock.every(500, () => {
      void (async () => {
        const list = (await read($, members)) ?? []
        const q = await read($, quest)
        if (list.some(m => m.status === 'working') || q?.isKeeperBusy) {
          await update($, tick, n => (n ?? 0) + 1)
        }
      })()
    })
    return next(e)
  })

  on('command.run', { command: 'guildhall-tavern' }, async $ => {
    const opened = await $.ui.open({ id: PANE, title: TITLE })
    await update($, tick, n => (n ?? 0) + 1) // the band redraws: the pane may now be in view
    // With no surface attached (a cloud session viewed from an app) every pane reads
    // as placed, yet nothing draws it: only this command's text reaches the person.
    const surfaces = await $.session.surfaces()
    if (opened.isPlaced && surfaces.length > 0) {
      return { text: `The tavern door swings open. (${await whereText($)})` }
    }
    const why = opened.isPlaced ? 'no surface that draws panes is attached to this session' : opened.reason
    const snapshot = tavernText(
      await read($, quest),
      (await read($, members)) ?? [],
      (await read($, chronicle)) ?? [],
      await read($, recap),
      Date.now(),
    )
    return { text: `The pane cannot be drawn here (${why}). Run /guildhall-tavern again for a fresh look.\n\n${snapshot}` }
  })

  // A /quest begins a fresh ledger. The hook only watches; the command runs as typed.
  on('command.run', async ($, e, next) => {
    if (isQuestCommand(e.command)) {
      await beginQuest($, shorten(e.args ?? '', 80) || 'An unnamed quest')
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('agent.spawn', async ($, e, next) => {
    const role = guildRole(e.subagentType)
    if (role === undefined && (await read($, quest)) === null) return next(e)

    const spawned = await next(e)
    if (spawned.deny !== undefined || spawned.agentId === undefined) return spawned
    if (role !== undefined) await ensureQuest($, shorten(e.description ?? '', 80) || 'An impromptu errand')

    const who = role ? characterOf(role) : characterOf(e.subagentType)
    const member: GuildMember = {
      id: spawned.agentId,
      role: role ?? e.subagentType,
      parentId: e.parentAgentId,
      status: 'working',
      task: shorten(e.description ?? '', 80),
      line: `${who.name} answers the summons`,
      deeds: 0,
      model: spawned.model,
      startedAt: Date.now(),
    }
    await update($, members, list => [...(list ?? []), member].slice(-MEMBER_LIMIT))
    await update($, bandQuiet, () => false)
    await refreshStatus($)
    if (e.parentAgentId === undefined) {
      await setKeeper($, `${KEEPER.name} summons ${who.name}`)
    }
    await record($, who.icon, `${who.name} ${who.title} takes up: ${member.task}`)
    return spawned
  }).catch(($, e, next) => next(e)) // the pane is a spectator: a bookkeeping failure never blocks a dispatch

  on('tool.call', async ($, e, next) => {
    const q = await read($, quest)
    if (q === null) return next(e)
    const { deed, target } = classify(String(e.tool), e as unknown as Record<string, unknown>)

    if (e.agentId === undefined) {
      // The main loop is Mordain; his summons are drawn by agent.spawn.
      if (e.tool !== 'Agent') await setKeeper($, flavor(KEEPER, deed, target))
      const path = (e as { file_path?: unknown }).file_path
      if (deed === 'write' && typeof path === 'string' && isPlanScroll(path)) {
        await update($, quest, current => (current ? { ...current, planPath: path } : current))
      }
      return next(e)
    }

    const agentId = e.agentId
    const list = (await read($, members)) ?? []
    const member = list.find(m => m.id === agentId)
    if (member === undefined) return next(e)
    const line = flavor(memberCharacter(member), deed, target)
    await update($, members, all =>
      (all ?? []).map(m => (m.id === agentId ? { ...m, line, deeds: m.deeds + 1 } : m)),
    )
    await refreshStatus($)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const q = await read($, quest)
    if (q === null) return done

    if (e.agentId === undefined) {
      await setKeeper($, flavor(KEEPER, 'idle', ''), false)
      await settle($)
      return done
    }

    const agentId = e.agentId
    const list = (await read($, members)) ?? []
    const member = list.find(m => m.id === agentId)
    if (member === undefined || member.status !== 'working') return done
    const who = memberCharacter(member)
    const fell = e.isAborted || e.reason === 'error' || e.reason === 'refusal'
    await update($, members, all =>
      (all ?? []).map(m =>
        m.id === agentId
          ? {
              ...m,
              status: fell ? 'fallen' : 'done',
              line: fell ? `${who.name} was called back from the field` : `“${who.catchphrase}”`,
              endedAt: Date.now(),
            }
          : m,
      ),
    )
    await record(
      $,
      who.icon,
      fell ? `${who.name} returns empty-handed` : `${who.name} returns to the hall (${elapsed(Date.now() - member.startedAt)})`,
    )
    await refreshStatus($)
    return done
  }).catch(($, e, next) => next(e)) // replays the turn's own answer; nothing runs twice

  // A settled quest's band stands down once the person moves on.
  on('prompt.submit', async ($, e, next) => {
    const list = (await read($, members)) ?? []
    if ((await read($, recap)) !== null && !list.some(m => m.status === 'working')) {
      await update($, bandQuiet, () => true)
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // Closing the pane brings the band back: redraw it.
  on('ui.close', async ($, e, next) => {
    const closed = await next(e)
    if (e.id === PANE) await update($, tick, n => (n ?? 0) + 1)
    return closed
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    await read($, tick) // redraw with the pane's comings and goings
    const line = bandText(
      await read($, quest),
      (await read($, members)) ?? [],
      await read($, recap),
      (await read($, bandQuiet)) ?? false,
    )
    if (line === undefined || (await isPaneInView($))) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    return (
      <Box>
        <Text wrap="truncate-end">{line} </Text>
        <Button key="open-tavern" label="Tavern" onPress={() => $.ui.open({ id: PANE, title: TITLE })} />
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    drawnOn.add(e.surface)
    const q = await read($, quest)
    const list = (await read($, members)) ?? []
    const log = (await read($, chronicle)) ?? []
    const settled = recapRows(await read($, recap), list, Date.now())
    const frame = SPINNER[((await read($, tick)) ?? 0) % SPINNER.length]
    const now = Date.now()

    if (q === null) {
      return (
        <Box flexDirection="column">
          <Text bold>{KEEPER.icon} The tavern is quiet.</Text>
          <Text dimColor>{KEEPER.name} waits by the hearth. Issue /quest to call the guild.</Text>
        </Box>
      )
    }

    const statusMark = (m: GuildMember) =>
      m.status === 'working' ? frame : m.status === 'done' ? '✓' : '✗'
    const statusColor = (m: GuildMember) =>
      m.status === 'working' ? 'claude' : m.status === 'done' ? 'success' : 'error'

    const rows: RenderChildren[] = []
    const drawMember = (m: GuildMember, indent: string) => {
      const who = memberCharacter(m)
      const clock = elapsed((m.endedAt ?? now) - m.startedAt)
      rows.push(
        <Text wrap="truncate-end">
          {indent}
          <Text color={statusColor(m)}>{statusMark(m)}</Text> {who.icon} <Text bold>{who.name}</Text>
          <Text dimColor> {who.title} · {m.role}{m.model ? ` · ${m.model}` : ''} · {clock} · {m.deeds} deeds</Text>
        </Text>,
      )
      rows.push(
        <Text wrap="truncate-end" dimColor={m.status !== 'working'} italic>
          {indent}     {m.line}
        </Text>,
      )
      for (const child of list.filter(c => c.parentId === m.id)) drawMember(child, indent + '   ')
    }

    const withDescendants = (m: GuildMember): GuildMember[] => [
      m,
      ...list.filter(c => c.parentId === m.id).flatMap(withDescendants),
    ]
    const ids = new Set(list.map(m => m.id))
    const roots = list.filter(m => m.parentId === undefined || !ids.has(m.parentId))
    const groups = PHASES.map(p => ({
      ...p,
      list: roots.filter(m => memberCharacter(m).phase === p.phase),
    })).filter(g => g.list.length > 0)

    groups.forEach((g, i) => {
      const last = i === groups.length - 1
      const working = g.list.flatMap(withDescendants).filter(m => m.status === 'working').length
      rows.push(
        <Text>
          <Text dimColor>{last ? '└─ ' : '├─ '}</Text>
          <Text bold>{g.label}</Text>
          <Text dimColor>{working > 0 ? `  ${working} at work` : '  done'}</Text>
        </Text>,
      )
      for (const m of g.list) drawMember(m, last ? '   ' : '│  ')
    })

    const atWork = list.filter(m => m.status === 'working').length
    return (
      <Box flexDirection="column">
        <Text bold wrap="truncate-end">⚔ {q.title}</Text>
        <Text dimColor>
          {elapsed(now - q.startedAt)} on the road · {atWork} at work · {list.length} summoned
        </Text>
        <Text> </Text>
        <Text wrap="truncate-end">
          <Text color={q.isKeeperBusy ? 'claude' : 'subtle'}>{q.isKeeperBusy ? frame : '·'}</Text> {KEEPER.icon}{' '}
          <Text bold>{KEEPER.name}</Text>
          <Text dimColor> {KEEPER.title} · Guildmaster</Text>
        </Text>
        <Text wrap="truncate-end" italic dimColor={!q.isKeeperBusy}>
          {'     '}{q.keeperLine}
        </Text>
        {rows}
        {settled.length > 0 && <Text> </Text>}
        {settled.map(row => (
          <Text
            wrap="truncate-end"
            bold={row.tone === 'head'}
            dimColor={row.tone === 'dim' || row.tone === 'skip'}
            color={row.tone === 'ok' ? 'success' : row.tone === 'warn' ? 'warning' : undefined}
          >
            {row.text}
          </Text>
        ))}
        {log.length > 0 && <Text> </Text>}
        {log.length > 0 && <Text bold dimColor>Chronicle</Text>}
        {log.map(entry => (
          <Text wrap="truncate-end" dimColor>
            {entry.icon} {entry.text}
          </Text>
        ))}
      </Box>
    )
  })
}
