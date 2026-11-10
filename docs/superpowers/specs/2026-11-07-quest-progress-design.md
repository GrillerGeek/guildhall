# Quest progress visibility — design

Date: 2026-11-07 · Status: decisions settled; awaiting approval · Branch: `Plan-viz`

## Intent

A running quest is a black box. While the camp-planner `feature/mcp` quest ran
in Codex for a week, Jason could not tell what it was working on or when it
would finish. The facts existed, buried in a 336-line plan file that serves as
an evidence log (hashes, counts, dense prose), with no marker of the current
step, no time per step, and recovery loops narrated out of order.

The goal: a user glances at a pane next to the chat and, in about two seconds,
knows **how far along the whole quest is and how much is left** — on Claude and
Codex, terminal and desktop.

**Success bar (Jason's words, paraphrased):** people look at it and say "that
is beautiful and helpful." The failure that would make this a miss even if it
technically works: people look at it and are confused.

## Goals

1. **Overall progress first.** Milestones done / current / upcoming, and tasks
   remaining in the current milestone. This is the primary question; "who is
   working right now" is secondary.
2. **Loops are declared up front.** Milestones that can repeat are marked in
   the plan before they repeat, with the reason they would and their limit.
   When a loop happens it reads as "pass 2, because X, expected," never as
   backsliding.
3. **The user's touchpoints are declared up front.** Every point where the
   quest expects to need the user — decision, approval, manual acceptance —
   is listed in advance with roughly when. When one is reached, it dominates
   the view. Unplanned asks appear the same way, tagged unplanned.
4. **One truth, every surface.** A single host-neutral progress record per
   quest; Claude terminal, Claude desktop, Codex terminal (AgentPanel split
   panes) and Codex desktop all render it.
5. **Highly visual, low cognitive load, good-looking** on each surface.

## Non-goals

- **No time estimates / ETAs.** Progress is measured in milestones and tasks.
  Elapsed time per milestone and per task is shown so a stall is visible.
  *(Claude's call — Jason did not ask for estimates; revisit if wanted.)*
- No retrofit of quests already in flight (camp-planner continues as is).
  Progress tracking starts with quests planned after this ships.
- Not a replacement for the plan file. The plan stays the evidence log and
  canonical record; progress is a separate, glanceable account.
- No control surface. Views are read-only spectators; answering the user's
  turn still happens in the chat.

## Anti-goals

- Confusion or clutter. If a newcomer can't read it cold, it has failed.
- A progress bar that sits still for days or jumps backwards (loops must not
  look like regression).
- Progress tracking that changes quest behavior: it must never alter
  dispatch, reviewers, retry budgets, independence guardrails or Mordain's
  write scope beyond what is decided below.
- Hashes, SHAs and test-count walls in the view. Plain words first.

## The visual design (decided)

Jason chose **layout B — journey + focus card** over a vertical trail and a
dial, and approved the polished terminal states and the desktop pane/page.
Mockups: `.superpowers/brainstorm/74949-1794062366/content/`
(`journey-states-v2.html`, `desktop.html`) — local only, not committed.

### Structure (all surfaces)

1. **Header:** quest title; repo · branch (· day N); "N of M" milestones.
2. **Journey:** one horizontal path across the whole quest. Done milestones
   solid green with ✓; the current one a pulsing blue node; upcoming dotted;
   user waypoints as amber ⚑ placed where they fall in the sequence. Loop
   badges sit above milestones that can repeat: `↻` (may loop), `↻2` (on or
   completed pass 2).
3. **Focus card ("NOW"):** the current milestone's goal in plain words, a task
   bar ("3 of 7 tasks"), the task list (✓ done, spinner on the active one with
   a small "who · elapsed" tag, ○ remaining — collapsed to "N more" in narrow
   views). On a repeat pass the card header reads `NOW · PASS 2 OF BUILD` and
   carries one sentence of *why it looped* plus whether that was within plan.
4. **You:** the next user waypoint as one line ("You're needed after the PR ·
   2 checks"), and a note of which milestones may repeat and their limits.

### States and color (each color means one thing)

| State | Color | Behavior |
|---|---|---|
| Done | green | ✓, solid path |
| Working | blue | pulsing node, spinner on active task |
| Repeating | violet | `↻`, card header `PASS n`, one-line why; "last pass allowed — next miss asks you" when at limit |
| Needs you | amber | card becomes **YOUR TURN**: what's asked, where to answer ("Answer in the chat"), how long it has waited, planned/unplanned |

Plain language leads. Adventurer names appear only as the small "who's on it"
tag. No in-character flavor text in this view (the tavern's adventurer tree
keeps its voice).

### Surface variants

- **Terminal pane** (Claude tavern mod; `guildhall watch` in an AgentPanel /
  tmux / Supacode split): the layout above in box-drawing + color. The
  renderer measures text width and draws borders; nothing is hand-padded.
- **Desktop side pane (~380px)** (Claude desktop mod surface): same layout,
  rendered richly — real progress bar, animated spinner, rounded cards.
- **Full page** (Codex desktop / any browser): adds detail Jason explicitly
  kept — a **milestone list with time spent** per milestone and loop pills,
  the **full task list** for the current milestone, and a **"Where you come
  in"** list including waypoints already passed.

## The progress record

### What it holds

Per quest:
- quest title, repo, branch, plan path, started-at, host
- **milestones** (ordered): id, plain-language name, goal sentence, state
  (upcoming / current / done / skipped), started/finished timestamps, and
  `loop: {may: bool, reason, limit, pass}`
- **tasks** per milestone: name, state, who (role), started/finished,
  added-because (e.g. "security review B5") for tasks added mid-flight
- **waypoints** (user touchpoints): what is needed, expected position (after
  milestone X), state (upcoming / waiting / done), planned vs unplanned,
  waiting-since
- **loop events**: milestone, pass number, trigger in one sentence, within
  limit or not
- a one-line current "what's happening"

### Seeded by the plan

When Mordain writes the plan he also declares the milestones, which may loop
(with limits taken from existing retry budgets — e.g. the shared implementer
retry), and the expected user waypoints. That is what makes "how much is
left" knowable from minute one. Tasks are added as work unfolds.

Default milestone skeleton for a feature quest follows the existing phase
shape: Plan & scope → (Architecture) → Tests → Build → (Refactor) → Reviews →
(UI walkthrough) → Draft PR, with gated milestones present only when the plan
selects them. Debug and prototype modes get their own short skeletons.

### Who writes it — decided: option (a)

Both hosts must produce identical records, and views must never parse prose.
Claude's recommendation: a small stdlib Python helper, `progress.py`, beside
the existing `scripts/review.py` (same conventions: Python 3.12+, standard
library only, atomic writes, refusals with bounded messages). Mordain calls
short commands — `start-milestone build`, `add-task build "Photo replacement
race" --because "security review B5"`, `loop build --why "..."`,
`wait-user <waypoint>`, `done-task ...` — and the helper keeps the record
valid. Jason chose option (a) below: an explicit, narrow widening of Mordain's
scope to this record via this helper only.

### Where it lives

Beside the plan: `docs/guildhall/plans/<plan-slug>/progress.json`, alongside
the existing `review-state.json` pattern. *(Claude's call.)*

## Surfaces and how each is built

| Surface | Delivery | Reads |
|---|---|---|
| Claude Code terminal | `guildhall-tavern` mod gains the journey view as the pane's top section; existing adventurer tree, chronicle, band and recap remain below/alongside | progress record (file) + existing `agent.spawn`/`tool.call` events for live "who" |
| Claude desktop | same mod, desktop surface | same |
| Codex / any terminal (AgentPanel split) | `guildhall watch [plan-or-dir]` — stdlib Python, ANSI rendering, redraws on file change, finds the newest active quest when no path given | progress record |
| Codex desktop / browser | `guildhall watch --web` serves the full page on localhost (auto-refreshing); optional static HTML export | progress record |

The band above the Claude prompt gains the amber state: `⚑ waiting on you`.

*(Claude's calls: watcher in stdlib Python to match `review.py` and run
anywhere Codex runs; Codex desktop gets a local page rather than a Codex Space
Page, because Space Pages are editable prose, not live HTML — per
`references/collaborative-planning.md`.)*

## Constraints

- Preserve the three-phase dispatch shape, independence guardrail (test-author
  must not see progress detail that leaks implementation — task names written
  by Mordain must stay at the level already permitted in its handoff; progress
  is never part of a worker handoff), reviewer gating and retry budgets.
- Views are spectators: read-only, fall through on any error, never block or
  slow the quest.
- Portable route parity: the skill under `plugin/skills/guildhall-quest/` and
  `plugin/portable/` carry the same helper and instructions.
- Version bump synchronized across the three plugin manifests; validator and
  tavern roster tests keep passing.
- Command content is session-snapshotted: dogfood from a fresh session.

## Decisions (Jason's)

1. **Mordain's write scope.** Today Mordain may write only the plan file, and
   `collaborative-planning.md` says he "must not invoke a mutating helper to
   evade that scope." Options:
   - **(a) Narrow, explicit widening — CHOSEN:** Mordain may also update
     the quest's progress record, only via `progress.py`. Prose + write-guard
     docs updated; the record holds no source or evidence.
   - (b) Progress lives inside the plan `.md` as a structured block — no rule
     change, but every update rewrites the whole plan (Claude's Mordain has
     `Write`, not `Edit`), and views must parse markdown.
   - (c) A sidecar `docs/guildhall/plans/<slug>.progress.md` — passes the
     existing hook's literal `*.md` check but stretches the prose rule.

2. ~~Release scope~~ — **decided (Jason): one release**, single version bump
   covering record + helper, Claude mod, `watch` terminal and `--web` page.

## Settled after builder check (Claude's calls)

- **Helper failure never blocks a quest.** If Python or `progress.py` is
  unavailable or refuses, the quest continues; Mordain notes "progress
  unavailable" once in the plan and views show nothing / a stale marker.
- **Write-scope enforcement stays prose-only for `Bash`**, matching today's
  rule that the write guard covers `Write` only; no new Bash hook.
- **Packaging:** `progress.py` ships in the skill bundle beside `review.py`
  (both native and portable copies), invoked by path. `guildhall watch` is
  the helper's `watch` subcommand (`progress.py watch [--web]`); the docs may
  suggest a shell alias. No console entry point.
- **How the Claude mod finds and refreshes the record:** it already learns the
  plan path from Mordain's `Write`; the record path derives from it. The mod
  re-reads the record on `tool.call` events for `progress.py` (and on its
  existing tick) rather than relying on file watching.
- **Unplanned asks on Claude:** the mod sees `AskUserQuestion` in `tool.call`
  and shows YOUR TURN (unplanned) directly, clearing on the next prompt. On
  Codex it relies on Mordain's prose rule to call `wait-user` before asking.
- **Milestone count stability:** "Reviews" is always declared at plan time
  (security + docs are always on); its tasks fill in at Step 3.7. Gated
  milestones the plan anticipates are declared up front; ones not needed are
  marked *skipped* (shown faint, excluded from M). A milestone may be added
  mid-quest only as a tagged addition. The done count never decreases; loops
  add passes, not regressions.
- **Mode skeletons:** debug — Plan → Reproduce → Root cause → Report (→ fix
  via build chain if requested); prototype — Plan → Spike → Show; docs fast
  lane — no record. Quest close (`pr-author`, Wren) is the "Draft PR"
  milestone.
- **Verification bar:** automated helper tests, tavern tests, and a terminal
  render snapshot; then Jason reviews each shipped surface live on a real
  quest before it's called done (a planned user waypoint).

## Left to the builder

- Exact record schema and helper command names.
- Tavern pane arrangement: journey on top, adventurer tree beneath, or a
  toggle — provided the journey is what you see first.
- Narrow-width degradation (collapsing labels, "N more").
- File-watch mechanism for `guildhall watch` (polling is fine).
- How Mordain's existing `TodoWrite` mirror relates to the record on Claude
  (likely: keep it, generated from the same milestones).
- Test strategy (helper unit tests; tavern tests extended; snapshot of the
  terminal render).
