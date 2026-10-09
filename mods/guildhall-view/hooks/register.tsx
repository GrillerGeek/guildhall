import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderChildren } from 'claude-code'

import type { ChronicleEntry, GuildMember, GuildQuest } from '../types'
import { KEEPER, PHASES, characterOf, classify, flavor, guildRole } from './roster'
import type { Character } from './roster'

const PANE = 'guildhall'
const TITLE = 'The Guildhall'
const SPINNER = ['◐', '◓', '◑', '◒']
const CHRONICLE_LENGTH = 8

const quest = atom({ plugin: 'guildhall-view', key: 'quest' } as const, null as GuildQuest | null)
const members = atom({ plugin: 'guildhall-view', key: 'members' } as const, [] as GuildMember[])
const chronicle = atom({ plugin: 'guildhall-view', key: 'chronicle' } as const, [] as ChronicleEntry[])
const tick = atom({ plugin: 'guildhall-view', key: 'tick' } as const, 0)

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
  await record($, KEEPER.icon, `${KEEPER.name}: “${KEEPER.catchphrase}”`)
  // A surface that cannot seat the pane leaves the ledger kept; /guildhall-view opens it later.
  await $.ui.open({ id: PANE, title: TITLE }).catch(() => undefined)
}

async function setKeeper($: EngineInterface, line: string, isKeeperBusy = true) {
  await update($, quest, q => (q ? { ...q, keeperLine: line, isKeeperBusy } : q))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'guildhall-view',
      description: 'Open the Guildhall pane: who is on the quest and what they are doing',
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

  on('command.run', { command: 'guildhall-view' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    return { text: 'The Guildhall doors swing open.' }
  })

  // A /quest begins a fresh ledger. The hook only watches; the command runs as typed.
  on('command.run', async ($, e, next) => {
    if (isQuestCommand(e.command)) {
      await beginQuest($, e.args.trim() || 'An unnamed quest')
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('agent.spawn', async ($, e, next) => {
    const role = guildRole(e.subagentType)
    let q = await read($, quest)
    if (role === undefined && q === null) return next(e)
    if (q === null) {
      // A guild agent dispatched outside /quest still gets a hall to work in.
      await beginQuest($, e.description || 'An impromptu errand')
      q = await read($, quest)
    }

    const spawned = await next(e)
    if (spawned.deny !== undefined || spawned.agentId === undefined) return spawned

    const who = role ? characterOf(role) : characterOf(e.subagentType)
    const member: GuildMember = {
      id: spawned.agentId,
      role: role ?? e.subagentType,
      parentId: e.parentAgentId,
      status: 'working',
      task: e.description,
      line: `${who.name} answers the summons`,
      deeds: 0,
      model: spawned.model,
      startedAt: Date.now(),
    }
    await update($, members, list => [...(list ?? []), member])
    if (e.parentAgentId === undefined) {
      await setKeeper($, `${KEEPER.name} summons ${who.name}`)
    }
    await record($, who.icon, `${who.name} ${who.title} takes up: ${e.description}`)
    return spawned
  }).catch(($, e, next) => next(e)) // the pane is a spectator: a bookkeeping failure never blocks a dispatch

  on('tool.call', async ($, e, next) => {
    const q = await read($, quest)
    if (q === null) return next(e)
    const { deed, target } = classify(String(e.tool), e as unknown as Record<string, unknown>)

    if (e.agentId === undefined) {
      // The main loop is Mordain; his summons are drawn by agent.spawn.
      if (e.tool !== 'Agent') await setKeeper($, flavor(KEEPER, deed, target))
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
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const q = await read($, quest)
    if (q === null) return done

    if (e.agentId === undefined) {
      await setKeeper($, flavor(KEEPER, 'idle', ''), false)
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
    return done
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const q = await read($, quest)
    const list = (await read($, members)) ?? []
    const log = (await read($, chronicle)) ?? []
    const frame = SPINNER[((await read($, tick)) ?? 0) % SPINNER.length]
    const now = Date.now()

    if (q === null) {
      return (
        <Box flexDirection="column">
          <Text bold>{KEEPER.icon} The hall is quiet.</Text>
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

    const ids = new Set(list.map(m => m.id))
    const roots = list.filter(m => m.parentId === undefined || !ids.has(m.parentId))
    const groups = PHASES.map(p => ({
      ...p,
      list: roots.filter(m => memberCharacter(m).phase === p.phase),
    })).filter(g => g.list.length > 0)

    groups.forEach((g, i) => {
      const last = i === groups.length - 1
      const working = g.list.filter(m => m.status === 'working').length
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
