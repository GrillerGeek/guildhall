export type MemberStatus = 'working' | 'done' | 'fallen'

export type GuildMember = {
  id: string
  role: string
  parentId?: string
  status: MemberStatus
  task: string
  line: string
  deeds: number
  model?: string
  startedAt: number
  endedAt?: number
}

export type GuildQuest = {
  title: string
  startedAt: number
  keeperLine: string
  isKeeperBusy: boolean
}

export type ChronicleEntry = { at: number; icon: string; text: string }

declare module 'claude-code' {
  interface PluginState {
    'guildhall-tavern': {
      quest: GuildQuest | null
      members: GuildMember[]
      chronicle: ChronicleEntry[]
      tick: number
    }
  }
}
