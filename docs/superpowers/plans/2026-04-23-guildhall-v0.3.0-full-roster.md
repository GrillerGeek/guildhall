# Guildhall v0.3.0 — full roster + new quest.md + plan.md Implementation Plan

> **Executive summary.** v0.3.0 closes the staircase defined in `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`. Four substantive commits on `ship/v0.3.0-full-roster` plus one doc-fix commit from the final sanity sweep. Shipped differently than prior rungs — no per-step subagent dispatch; plan drove main-context writing directly because the content is prose-heavy against a well-defined design spec.

**Goal:** Ship Guildhall v0.3.0 — add the five new adventurers (security-reviewer, architecture-reviewer, docs-writer, pr-author, plugin-validator), rewrite `/quest` for the new three-phase flow (sequential build → parallel reviews → sequential closer), write durable plan-file artifacts, and update all documentation.

**Architecture:** Five commits on `ship/v0.3.0-full-roster` branch:

1. `679f82b` — Five new agent files (`plugin/agents/*.md`), each with standardized contract block + process + hard rules, matching the design-spec Section 4 templates.
2. `b976ac5` — Five new character sheets appended to `plugin/CHARACTERS.md` (Oriana, Aldric, Cassian, Rook, Tabs), matching the existing 6-character format.
3. `36aecae` — `plugin/commands/quest.md` wholesale rewrite for the v0.3.0 flow: added Aldric to Step 3, phased dispatch in Step 4 (sequential build / parallel reviews / Rook-last closer), new gates in Step 5 for every new adventurer, plan-file writing in Step 6. Frontmatter gains narrow `Write` access for plan files only.
4. `edac0f2` — Doc propagation (READMEs, CLAUDE.md first-time commit, manifest version 0.2.7 → 0.3.0, `docs/guildhall/plans/` directory scaffolded).
5. `742bf7c` — Final-sweep fix: stale "six adventurers" language in `README.md` line 9, and "as of v0.2.7" in `plugin/README.md` cost-posture block.

**Tech Stack:** Markdown (agent bodies + command prose + character sheets + READMEs) and JSON (manifest). No code. Verification via final sanity-sweep subagent that checked 13 structural invariants across the branch.

**Deviation from the v0.2.x pattern:** Prior rungs used subagent-driven-development religiously (implementer → spec review → code quality review per task). v0.3.0 had too much prose-heavy creative writing (new agent bodies + character sheets) for that overhead to pay off; content was written in main context against the design spec. One final sanity-sweep subagent caught the two stale-reference issues that got the `742bf7c` fix.

---

## Context for future engineers (zero-assumption briefing)

Everything listed above is in the design spec — this plan does not re-derive design decisions, it executes them.

**Why the prose was written in main context rather than via subagents:**
- Agent body prompts require holding the whole character voice + contract + project conventions simultaneously. A subagent with only the contract text as input produces generic prose; a main-context write with CHARACTERS.md open produces voice-matched prose.
- Character sheets for CHARACTERS.md require internal consistency with the other six — tonal echoes, D&D class knowledge, catchphrase echoing. Hard to delegate cleanly.
- quest.md rewrite preserves the existing structure where possible; subagent rewrite would have risked rewriting from scratch and losing nuance (e.g., the refactor-skip-judgment paragraph in Step 5).

**Why the sanity-sweep subagent caught real issues:**
- Main-context writing is fast but drifts from mechanical consistency checks (cross-file reference counts, stale version strings). A focused subagent with a 13-point checklist found two issues that a manual pass missed.

---

## File inventory

Twelve files touched across the branch:

- **Create:** `plugin/agents/security-reviewer.md`
- **Create:** `plugin/agents/architecture-reviewer.md`
- **Create:** `plugin/agents/docs-writer.md`
- **Create:** `plugin/agents/pr-author.md`
- **Create:** `plugin/agents/plugin-validator.md`
- **Modify:** `plugin/CHARACTERS.md` (append 5 character sheets)
- **Modify:** `plugin/commands/quest.md` (wholesale rewrite)
- **Modify:** `plugin/README.md` (roster table, flow overview, as-of-v0.3.0 fix)
- **Modify:** `README.md` (Status block, stale-roster-language fix)
- **Modify:** `plugin/.claude-plugin/plugin.json` (version + description)
- **Create:** `CLAUDE.md` (first-time tracked commit)
- **Create:** `docs/guildhall/plans/README.md` (directory scaffold)

---

## Task decomposition

### Task 1: Write five new agent files

Follow the design-spec Section 4 contract templates for each adventurer. Each file has: frontmatter (name, description with examples, model, color, tools), opening quote, opening paragraph in D&D voice, `## Your contract` block (INPUT / OUTPUT / NON-GOALS / EFFORT), `## Your process` (numbered list), `## Hard rules`.

Design-spec pointers per agent:
- `security-reviewer` — Section 4, Oriana. Opus, xhigh, read-only. Tools: Read, Grep, Glob, Bash (read-only git).
- `architecture-reviewer` — Section 4, Aldric. Opus, xhigh, read-only. Tools: Read, Grep, Glob. NO Bash.
- `docs-writer` — Section 4, Cassian. Sonnet, medium. Tools: Read, Write, Edit, Grep, Glob.
- `pr-author` — Section 4, Rook. Sonnet, medium. Tools: Read, Bash (read-only git). Stdout-only; never runs gh/az.
- `plugin-validator` — Section 4, Tabs. Haiku, low. Tools: Read, Grep, Glob, Bash (read-only). Seven explicit checks documented in-prompt.

Committed as `679f82b` on the branch.

### Task 2: Append 5 character sheets to CHARACTERS.md

Insert BETWEEN Vera's sheet (ends with her catchphrase line) and `## The oath` heading. Order: Oriana → Aldric → Cassian → Rook → Tabs (matching design-spec Section 1 roster order for new adventurers).

Each sheet format (matches existing 6):
- `## <Name> — *<Epithet>*`
- Two-column table: Agent / Class / Race / Model
- Two character paragraphs (intro + discipline)
- `**Catchphrase:** *"..."*` — matches the opening quote in the agent file
- `---` separator

Committed as `b976ac5`.

### Task 3: Rewrite quest.md for the v0.3.0 flow

Preserve all v0.2.x hard-won behaviors (self-check, explicit-model-param requirement, IDD integration rules) while adding:

- **Frontmatter:** `allowed-tools` gains `Write` for plan files only.
- **`## Your tools` table:** expand from 6 to 11 + 1 diagnostic rows. Add tier column.
- **Step 3 (Plan):** new sub-step 4 "decide whether to dispatch Aldric" for novel/cross-cutting work; new sub-step 9 "Write the plan file" following the template in spec Section 2.
- **Step 4 (Dispatch):** new "Dispatch sequence per mode" subsection with three phases (sequential build, parallel reviews, sequential closer); "Parallelism rules (strict)" subsection; handoff template documented in-place.
- **Step 5 (Verify):** gates added for Aldric, Oriana, Cassian, Vera, Tabs, Rook. Oriana `high` finding triggers STOP before Rook.
- **Step 6 (Report):** now includes updating the plan-file status and pasting Rook's PR draft.
- **Hard rules:** add "every dispatch MUST include the model parameter, no exceptions".

Committed as `36aecae`.

### Task 4: Doc propagation

- `plugin/README.md` — roster table from 6 → 11 with tier column + diagnostic note. New "Flow at a glance" paragraph.
- `README.md` — Status block rewritten to describe v0.3.0.
- `plugin/.claude-plugin/plugin.json` — version + description.
- `CLAUDE.md` — first-time-tracked commit. Obsolete content corrected (test-author pin, "no parallel dispatch", "no architect agent").
- `docs/guildhall/plans/README.md` — new directory README placeholder so plan-file path exists out of the box.

Committed as `edac0f2`.

### Task 5: Sanity-sweep follow-up

Dispatch one subagent with a 13-point structural checklist (branch state, agent inventory, frontmatter alias usage, contract block count, quest.md agent references, allowed-tools, plugin.json version, README version hits, character sheet count, plans directory, stale-language scan, commit count).

Caught two stale references that survived main-context writing:
- `README.md` line 9 said "six adventurer agents on Sonnet" — fixed to "eleven adventurer agents tiered across Opus / Sonnet / Haiku" with a sentence about the new three-phase flow.
- `plugin/README.md` cost-posture paragraph said "as of v0.2.7" — bumped to "as of v0.3.0".

Committed as `742bf7c`.

---

## Staircase completion status after this rung

- ✅ v0.2.3 — test-author alias revert
- ✅ v0.2.4 — model-echo diagnostic + self-check
- ✅ v0.2.5 — docs pause (and subsequent un-pause in v0.2.6)
- ✅ v0.2.6 — prompt tightening (contract blocks on all adventurers)
- ✅ v0.2.7 — explicit-model-param workaround for dispatch
- ✅ v0.3.0 — full roster expansion + new quest.md + plan.md (this)

Design-spec Section 5's staircase is now fully executed. v0.3.0-alpha was the intermediate gate envisioned in the spec; we shipped alpha.1 / alpha.2 / alpha.3 as commit suffixes on the branch rather than separate releases, then the `edac0f2` commit (version 0.3.0) and `742bf7c` (docs-fix) close out the v0.3.0 release.

## Dogfood validation (post-merge, user-driven)

- Install from main: `/plugin install https://github.com/GrillerGeek/guildhall`.
- Feature-mode quest: issue `/quest <feature ask with spec>`. Observe that Mordain:
  - Runs the model-echo self-check.
  - Writes `docs/guildhall/plans/<slug>.md` before any adventurer dispatch.
  - Dispatches the TDD chain sequentially.
  - Fires the post-green review fan-out in a single assistant message (three parallel `Agent` calls).
  - Ends with Rook's PR draft to stdout.
  - Updates plan-file status to completed before reporting.
- If any of the above doesn't happen, open a v0.3.1 concern.

## Known pending items

- Upstream Claude Code issue filing (draft at `docs/superpowers/upstream-issue-draft.md`, still untracked; user to post when ready — documents the subagent-frontmatter routing bug whose workaround shipped in v0.2.7).
- `plugin/.claude-plugin/marketplace.json` is untracked in the working tree; it appears to be auto-generated by Claude Code during plugin install and is not part of our source tree. Leave untracked.
