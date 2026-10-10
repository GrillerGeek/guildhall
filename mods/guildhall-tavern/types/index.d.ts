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
  /** The plan scroll Mordain last wrote this quest, as the Write named it. */
  planPath?: string
}

/** One gating verdict from the plan's `## Reviewers selected`. */
export type ReviewerVerdict = { role: string; fired: boolean; reason: string }

/** What the plan scroll said when the hall last fell quiet. */
export type Recap = {
  at: number
  planPath?: string
  status?: string
  reviewers: ReviewerVerdict[]
  /** Why the scroll could not be read, when it could not. */
  problem?: string
}

export type ChronicleEntry = { at: number; icon: string; text: string }

declare module 'claude-code' {
  interface PluginState {
    'guildhall-tavern': {
      quest: GuildQuest | null
      members: GuildMember[]
      chronicle: ChronicleEntry[]
      tick: number
      recap: Recap | null
      bandQuiet: boolean
    }
  }
}
