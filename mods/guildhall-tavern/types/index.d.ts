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
  /** The progress record progress.py last touched this quest. */
  progressPath?: string
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

/** One milestone of the quest's progress record (progress.py, schema 1). Times are epoch seconds. */
export type ProgressMilestone = {
  id: string
  name: string
  goal?: string
  state: 'upcoming' | 'current' | 'done' | 'skipped'
  loop: { reason: string; limit: number } | null
  pass: number
  started_at: number | null
  finished_at: number | null
}

export type ProgressTask = {
  id: string
  milestone: string
  pass: number
  name: string
  state: 'upcoming' | 'working' | 'done'
  who: string | null
  started_at: number | null
}

export type ProgressWaypoint = {
  id: string
  need: string
  after: string
  state: 'upcoming' | 'waiting' | 'done'
  planned: boolean
  waiting_since: number | null
}

/** The quest's own account of its progress, kept beside the plan scroll. */
export type QuestProgress = {
  schema_version: 1
  title: string
  repo?: string
  branch?: string
  status: 'active' | 'completed' | 'abandoned'
  note?: string
  started_at: number
  milestones: ProgressMilestone[]
  tasks: ProgressTask[]
  waypoints: ProgressWaypoint[]
  loops: { milestone: string; pass: number; why: string; at: number; within_limit: boolean }[]
}

/** Mordain is asking the person something right now (AskUserQuestion in flight). */
export type Asking = { since: number; need: string }

declare module 'claude-code' {
  interface PluginState {
    'guildhall-tavern': {
      quest: GuildQuest | null
      members: GuildMember[]
      chronicle: ChronicleEntry[]
      earlier: string[]
      tick: number
      recap: Recap | null
      bandQuiet: boolean
      progress: QuestProgress | null
      asking: Asking | null
    }
  }
}
