# Fog-of-War Design — Absorbing Wayfinder's Lessons into IDD + Guildhall

**Date:** 2026-07-28
**Status:** approved (design); implementation not started
**Origin:** [Wayfinder vs. IDD + Guildhall comparison](../2026-07-28-wayfinder-vs-idd-guildhall.md) — "the pair's weakest point is pre-interview fog and mid-pipeline discovery of unknowns."
**Upstream inspiration:** [wayfinder skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder) (Matt Pocock)

## Problem

The IDD + Guildhall pipeline has no formal home for **known-unknowns**:

1. **Pre-interview fog.** IDD's entry point, `/idd-framework:interview`, presumes a stakeholder who can answer questions *now*, in one sitting. Efforts that are genuinely foggy — "we'll know what to ask after we've seen the data's shape" — cannot survive the interview, and the pipeline offers nothing earlier.
2. **Mid-pipeline discovery.** A `/quest` that hits unsharp territory mid-flight (a question too foggy to dispatch on) has nowhere principled to record it. Discoveries strand in `## Open items for the user` or get silently resolved by assumption.

Wayfinder solves both with its **fog of war**: a deliberately incomplete map whose "Not yet specified" section holds in-scope questions not yet sharp enough to ticket, graduating them as decisions land.

## Decisions made during brainstorming

| Question | Decision |
|---|---|
| Audience for the fog map | Teammates who read the repo — **repo-native artifact**, but claim/concurrency semantics matter |
| Mid-quest unknowns | **Write back to IDD fog** (conditional — Guildhall stays functional standalone) |
| Pacing | Adopt wayfinder's **one non-research decision per session** hard rule |
| Approach | **A: new Exploration artifact type** in IDD + fog sections and gated write-back in Guildhall (over B: extend Product template; C: tracker-based port) |

## Part 1 — IDD: the Exploration artifact (phase 0)

### Layout

One directory per foggy effort:

```
docs/explorations/EXPL-<id>-<slug>/
  map.md
  tickets/
    01-<slug>.md
    02-<slug>.md
```

The wayfinder law is preserved: **the map is an index, not a store.** A decision lives in exactly one place — its ticket file. The map gists and links, never restates.

### `map.md`

YAML frontmatter:

```yaml
id: EXPL-<id>            # from bin/idd-next-id, new EXPL prefix
title: <short name>
status: charting          # charting | resolving | clear | abandoned
created: <ISO8601>
updated: <ISO8601>
```

Body sections:

- `## Destination` — what reaching the end looks like (a spec to hand off, a decision to lock, a change made in place). One or two lines; every session orients to it before choosing a ticket. Naming it is the first act of charting and fixes the scope.
- `## Notes` — domain, skills every session should consult, standing preferences.
- `## Decisions so far` — one line per resolved ticket: gist + relative link to the ticket file. Index only.
- `## Not yet specified` — the fog: in-scope questions not yet sharp enough to ticket. Written as loosely or fully as the view allows; doubles as a signpost for collaborators.
- `## Out of scope` — work consciously ruled beyond the destination: gist + why + link to any closed ticket. Never graduates; returns only if the destination is redrawn, as a fresh effort.

The **sharpness test** ships verbatim as a template comment: *ticket when you can phrase the question precisely (even if blocked); fog when you can't. Don't pre-slice fog into ticket-sized pieces — one patch may graduate into several tickets, or none.*

### Ticket files

Frontmatter:

```yaml
type: grilling            # research | prototype | grilling | task
status: open              # open | claimed | resolved | out_of_scope
claimed_by:               # git-committed name IS the claim; empty = unclaimed
blocked_by: []            # ticket ids
```

Body: `## Question` (sized to one agent session); `## Resolution` and `## Assets` (links, not pastes) filled at close.

Ticket types carry wayfinder's HITL/AFK split:

- **research** (AFK) — surface a fact a decision waits on; resolved by parallel subagents.
- **prototype** (HITL) — raise discussion fidelity with a cheap concrete artifact to react to; may hand to Guildhall's `prototype-builder`.
- **grilling** (HITL, the default) — conversation, one question at a time. The agent never stands in for the human's side.
- **task** (HITL or AFK) — manual work that must happen before a decision *can* be made (provision access, move data). The one type that does rather than decides; earns its place by unblocking a decision.

The **frontier** = open, unblocked, unclaimed tickets — mechanically computable from frontmatter, so a script can list it. Claim semantics: set `claimed_by` and commit; a race produces a merge conflict, which *is* the conflict-detection mechanism (acceptable for a repo-reading dev audience).

### `/idd-framework:chart <loose idea>`

New agent: `exploration-charter` — **Sonnet** (not Haiku like the interviewer: naming the destination is the highest-leverage act of the effort and shapes every ticket). Session shape, mirroring wayfinder:

1. **Name the destination** — HITL, one question at a time.
2. **Breadth-first fog sweep** — deliberately shallow across the whole space; surface open decisions and first steps takeable now.
3. **Escape hatch** — if no fog surfaces, the way is already clear: tell the user they don't need a map and route to `/interview` or `/quick-spec`. The absence of fog is a successful charting outcome.
4. **Create the map and specifiable tickets** — create-then-wire: tickets need identities before `blocked_by` can reference them, so wire blocking in a second pass. Unspecifiable material stays in `## Not yet specified`.
5. **Fire research subagents** in parallel for each research ticket.
6. **Stop** — charting is one session's work; it hand-resolves nothing.

### `/idd-framework:resolve [EXPL-id] [ticket]`

New agent: `exploration-resolver` — **Sonnet**. Session shape:

1. Load **only `map.md`** (low resolution); zoom into ticket bodies on demand.
2. Choose the ticket — user-named, else first frontier ticket. **Claim it before any work.**
3. Resolve per type (grilling/prototype HITL; research/task AFK where possible).
4. Record `## Resolution` in the ticket, flip status to `resolved`, add the one-line index entry to the map's `## Decisions so far`.
5. **Graduate fog** the answer sharpened into new tickets (create-then-wire); rule mis-scoped tickets `out_of_scope` with a map entry; update or delete tickets the decision invalidated.

**Hard rule: one non-research ticket per session.** Research tickets may fan out in parallel.

**Terminal state:** frontier empty + fog empty → `status: clear`. The command directs the user to `/interview` or `/quick-spec` seeded with the map path.

### Integration with existing IDD machinery

- **Lineage:** downstream artifacts gain an optional `exploration: EXPL-<id>` frontmatter field, carried Product → Intention → Spec at creation time. This is the hook Guildhall's write-back keys on.
- **Model dispatch table** (orchestration SKILL.md): add `exploration-charter` (sonnet) and `exploration-resolver` (sonnet) rows; the CRITICAL explicit-`model`-param rule applies unchanged.
- **`bin/idd-next-id`:** learns the `EXPL` prefix.
- **Archival:** `clear` and `abandoned` are terminal statuses; the archivist classifies whole Exploration directories, distills map + resolutions into `docs/idd-ledger.yaml` records, tags HEAD, deletes the directory — same two-step classify/apply flow as other artifacts.
- **New reference file:** `skills/idd-orchestration/references/exploration-template.md`; orchestration SKILL.md gains a phase-0 row in the workflow table and a "too foggy to interview?" entry point.

## Part 2 — Guildhall: mid-pipeline fog

### Plan-file template additions

Two sections inserted between `## Decisions made by Mordain` and `## Open items for the user` in the `quest.md` plan template:

```markdown
## Not yet specified
- <in-scope question too unsharp to dispatch on — sharpness test:
   can you phrase it precisely? then it's an open item or a ticket, not fog>

## Out of scope
- <work consciously ruled beyond this quest — gist + why, so it doesn't
   resurface as an open item>
```

The distinction matters: *Not yet specified* is in-scope-but-unsharp (may graduate); *Out of scope* is consciously ruled out (never graduates). `## Open items for the user` remains for sharp, actionable items.

### `quest.md` touch-points

- **Step 0 (Triage)** — new lane: if the ask itself is fog (no nameable destination — "explore whether we should…"), Mordain recommends `/idd-framework:chart` and stops. Planning on guesses is the failure mode this design exists to prevent.
- **Step 3 (Plan)** — a question Mordain cannot sharpen without guessing goes to `## Not yet specified` instead of being silently resolved by assumption.
- **Step 5 (Verify)** — a gate break that reveals genuine fog (not a fixable defect) records there too.

### Write-back: the `fog-cartographer` adventurer

Mordain's `Write` is scoped to plan files only — a load-bearing constraint that must not widen. Per the established rule (new artifact type → new adventurer), write-back is a dispatch:

- **New adventurer:** `fog-cartographer`, persona **Wren the Cartographer** (character sheet to be written in `CHARACTERS.md` at implementation — voice is load-bearing: Wren copies the mapmaker's marks faithfully and never redraws a coastline she hasn't walked). **Haiku** — the job is a mechanical, faithful transcription, not judgment.
- **One job:** at quest close, transcribe the plan file's `## Not yet specified` entries into the linked Exploration — fog section for unsharp entries, new tickets for any that pass the sharpness test.
- **Gated** (no always-on additions): fires only when BOTH hold — the plan's `## Not yet specified` is non-empty, AND the quest's spec carries an `exploration:` lineage field. Recorded in `## Reviewers selected` like every gating decision.
- **Sequencing:** runs parallel with `pr-author` — file-disjoint (`docs/explorations/**` vs. PR body).
- **Standard additions:** frontmatter `model: haiku` (alias form), roster-table row in `quest.md` (validator check 8), `plugin/README.md` roster, `CHARACTERS.md` sheet.

Conditional coupling preserves the existing contract style: Guildhall never hard-depends on IDD — the cartographer simply never fires in a repo with no Explorations, exactly as `test-author` reads Expectations only when a spec exists.

## Rollout

**Ship IDD first, Guildhall second.** The plan-file sections and triage lane work standalone, but the cartographer's gate reads the `exploration:` field, so IDD's artifact must exist first.

- **IDD-framework** (repo: `D:\Source\repos\idd-framework`): Exploration template + reference doc, `/chart` + `/resolve` commands, two new agents, dispatch-table rows, `idd-next-id` EXPL prefix, archivist classification rules, README + orchestration SKILL.md updates, version bump.
- **Guildhall** (repo: `D:\Source\repos\guildhall`): plan-template sections, Step 0/3/5 wording, `fog-cartographer` agent + roster row + README + CHARACTERS.md, version bump per `type(scope): summary (vX.Y.Z)` convention, `validate_plugin.py` must pass (check 8 covers the new row).

## Testing (dogfood)

All from **fresh sessions** (command content snapshots at session start):

1. `/chart` a genuinely foggy effort in `demoidd/` or `testidd/`; verify map + tickets + wired blocking; verify the no-fog escape hatch on a *sharp* effort routes to `/interview`.
2. `/resolve` two or three tickets across separate sessions — verify claim semantics, one-per-session enforcement, fog graduation, out-of-scope handling.
3. Drive the Exploration to `clear`; seed `/quick-spec` from it; confirm `exploration:` lineage lands on the Spec.
4. Run `/quest` against the resulting spec with a planted unknown; confirm it lands in `## Not yet specified` and the fog-cartographer fires and writes back.
5. Confirm the cartographer is correctly **skipped** (with recorded reason) when the section is empty or lineage is absent.
6. Archive the cleared Exploration; verify ledger record and directory deletion.

## Explicit non-goals

- No tracker integration (GitHub Issues / ADO) — ruled out by audience decision; revisit only if non-repo-readers need visibility.
- No changes to the TDD build chain, review fan-out, or any existing adventurer's scope.
- No always-on cartographer — the gate is the design.
- No `archived` status for Explorations — they follow the existing terminal-artifact deletion convention.
- No widening of Mordain's `Write` scope.
