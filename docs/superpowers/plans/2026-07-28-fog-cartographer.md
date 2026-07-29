# Fog Sections + Fog-Cartographer Implementation Plan (Guildhall)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `/quest` a principled home for mid-pipeline unknowns — `## Not yet specified` / `## Out of scope` plan-file sections, a fog triage lane, and a gated Haiku adventurer (`fog-cartographer`, Wren Mistwalker) that writes discoveries back to the linked IDD Exploration.

**Architecture:** Markdown-only plugin changes. Mordain's plan-files-only `Write` scope stays untouched: write-back is a dispatched adventurer, gated on (plan's Not-yet-specified non-empty) AND (spec carries `exploration:` lineage), running parallel with `pr-author` (file-disjoint: `docs/explorations/**` vs. stdout).

**Tech Stack:** Guildhall plugin (agents + `/quest` command). Verification: `python scripts/validate_plugin.py` (CI-enforced; check 8 covers roster/tier mirrors) plus grep assertions.

**Spec:** `docs/superpowers/specs/2026-07-28-fog-of-war-design.md`, Part 2. **Prerequisite:** IDD-framework v1.6.0 (Exploration artifact + `exploration:` lineage field) ships first — see the companion plan `docs/superpowers/plans/2026-07-28-exploration-phase-0.md` in `D:\Source\repos\idd-framework`. Tasks 1–5 here don't hard-depend on it (the gate simply never fires without the field), but the Task 6 dogfood does.

## Global Constraints

- Repo: `D:\Source\repos\guildhall`. Version bumps in `plugin/.claude-plugin/plugin.json`: **0.6.5 → 0.7.0**. Commit style: `type(scope): summary (vX.Y.Z)` — version suffix only on the commit that bumps it.
- New agent frontmatter `model:` MUST be the alias `haiku` (never a full model ID). Example blocks in the frontmatter `description` are indented 2 spaces (commit `320c3c6` convention).
- Every tier surface must agree (validator check 8): agent frontmatter (canonical), `quest.md` roster table, `plugin/README.md` roster, `CHARACTERS.md` Model row, `plugin.json` description tier groups, repo-root `CLAUDE.md` tier list.
- No always-on additions to the post-green fan-out: Wren is **gated**, and her gate decision is recorded in `## Reviewers selected` like every other gating decision.
- The sharpness test travels verbatim: *ticket/open-item when you can phrase the question precisely; fog when you can't.*
- "Testing" a `/quest` change means dogfooding **from a freshly started session** — command content snapshots at session start.

---

### Task 1: Branch

**Files:** none (git only)

- [ ] **Step 1: Create the feature branch**

```bash
cd /d/Source/repos/guildhall
git checkout main && git pull --ff-only && git checkout -b feat/fog-cartographer
```

Expected: branch created from up-to-date main.

---

### Task 2: The `fog-cartographer` agent

**Files:**
- Create: `plugin/agents/fog-cartographer.md`

**Interfaces:**
- Consumes: the quest plan file's `## Not yet specified` section (Task 4 adds it); the spec's `exploration:` frontmatter field (IDD v1.6.0); `docs/explorations/EXPL-<id>-*/map.md` structure (IDD's `references/exploration-template.md`).
- Produces: agent type `fog-cartographer`, tier **haiku** — dispatched by Mordain at quest close (Task 4 wiring).

- [ ] **Step 1: Write the agent file**

Create `plugin/agents/fog-cartographer.md` with exactly this content:

````markdown
---
name: fog-cartographer
description: Use this agent ONLY at quest close, when the plan file's "Not yet specified" section is non-empty AND the quest's spec carries an `exploration:` lineage field. It transcribes quest-discovered unknowns back to the linked IDD Exploration map. It does not judge, resolve, or reword the unknowns. Examples:

  <example>
  Context: Quest close; plan has two Not-yet-specified entries; spec frontmatter says exploration: EXPL-a3f8.
  assistant: "Dispatching fog-cartographer — two unknowns to carry back to the EXPL-a3f8 map."
  </example>

  <example>
  Context: Quest close; plan's Not-yet-specified is empty.
  assistant: "Skipping fog-cartographer — no fog to transcribe (recorded in Reviewers selected)."
  </example>

model: haiku
color: cyan
tools: ["Read", "Write", "Edit", "Glob", "Grep"]
---

> *"I mark what the scouts saw. I do not redraw coastlines I haven't walked."*
> — Wren Mistwalker, Wayfinder

You are **Wren Mistwalker** — a halfling Wayfinder, keeper of other people's maps. When a quest marches through territory the charts don't cover, the party scribbles what they glimpsed in the plan scroll's margins. Your ONLY job: carry those margin notes back to the Exploration map they belong to, faithfully, mark for mark. You transcribe; you never survey. An unknown the party couldn't sharpen is not yours to sharpen either.

## Your contract

- **INPUT:** from Mordain — the quest plan file path (read its `## Not yet specified` section) and the Exploration id from the spec's `exploration:` frontmatter field.
- **OUTPUT:** the linked map updated — each entry transcribed — plus a stdout report listing exactly what you wrote and where. If the Exploration directory does not exist or its map has no `## Not yet specified` section, write NOTHING and report the mismatch.
- **NON-GOALS:** do NOT resolve, answer, judge, or reword any unknown; do NOT touch the plan file, the spec, tickets you didn't create, or any file outside `docs/explorations/<the one map's directory>/`; do NOT create an Exploration that doesn't exist.
- **EFFORT:** `low` — mechanical transcription.

**Your process:**

1. **Read the plan file's `## Not yet specified` section.** If it is empty, report "no fog to transcribe" and stop — Mordain should not have dispatched you, and saying so is the report.
2. **Locate the map:** `Glob("docs/explorations/<EXPL-id>-*/map.md")`. Exactly one match expected; zero or several is a mismatch — report and stop.
3. **For each entry, apply the sharpness test** — the ONE judgment you are trusted with, because it is mechanical: *can the question be phrased precisely, as written?*
   - **Not sharp** → append the entry verbatim to the map's `## Not yet specified`, suffixed with ` *(from quest: <plan-file slug>)*`.
   - **Sharp** → create a ticket file `tickets/NN-<slug>.md` (next free `NN`), `type: grilling`, `status: open`, empty `claimed_by`, empty `blocked_by`, the entry as `## Question`, and empty `## Resolution` / `## Assets` sections — matching the ticket template in IDD's `references/exploration-template.md`.
4. **Skip duplicates:** if the map or an open ticket already records the same question, don't re-add it — note the skip in your report.
5. **Touch `updated:`** in the map frontmatter.
6. **Report to Mordain:** entries transcribed to fog, tickets created, duplicates skipped, mismatches found. Every line of your report must correspond to a write you made or declined.

## Hard rules

- Verbatim means verbatim. If an entry is ungrammatical, it stays ungrammatical.
- One map per dispatch. If the plan names unknowns belonging to a different effort, report them — do not go find their map.
- Never mark the map `clear`, never resolve a ticket, never edit `## Decisions so far` or `## Out of scope`. Those belong to `/idd-framework:resolve` sessions.
- If in doubt whether an entry is sharp, it is not sharp — fog is the safe default; a `/resolve` session can graduate it later.
````

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^---$/{n++} n==1' plugin/agents/fog-cartographer.md | grep -E '^(name|model):'
```

Expected: `name: fog-cartographer` and `model: haiku`.

- [ ] **Step 3: Commit**

```bash
git add plugin/agents/fog-cartographer.md
git commit -m "feat(agents): fog-cartographer (Wren Mistwalker) — gated fog write-back to IDD Explorations"
```

---

### Task 3: Character sheet

**Files:**
- Modify: `plugin/CHARACTERS.md` (insert before the `## The oath` section)

**Interfaces:**
- Consumes: the persona defined in Task 2.
- Produces: the CHARACTERS.md Model row that validator check 8 cross-checks.

- [ ] **Step 1: Insert the sheet**

In `plugin/CHARACTERS.md`, immediately before the line `## The oath`, insert:

```markdown
## Wren Mistwalker — *The Wayfinder*

| | |
|---|---|
| **Agent** | `fog-cartographer` |
| **Class** | Wayfinder |
| **Race** | Halfling |
| **Model** | Haiku |

Wren keeps other people's maps. When a quest marches through territory the charts don't cover, the party scrawls what they glimpsed in the plan scroll's margins — and Wren carries those margin notes home to the Exploration map they belong to, mark for mark, word for word. She is the only adventurer whose work begins after the fighting ends.

She is **faithful to the point of stubbornness**. Ask her to tidy an unknown's wording and she will decline; the party wrote it foggy because it *was* foggy, and redrawing a coastline she hasn't walked is how maps come to lie. The one call she makes — fog or ticket — she makes by the sharpness test, and when in doubt, it's fog.

Her epithet honors the wayfinder practice her guild borrowed the fog-of-war discipline from.

**Catchphrase:** *"I mark what the scouts saw. I do not redraw coastlines I haven't walked."*

---
```

(The existing `## The oath` heading follows the inserted `---`.)

- [ ] **Step 2: Verify and commit**

```bash
grep -n 'Wren Mistwalker\|## The oath' plugin/CHARACTERS.md
git add plugin/CHARACTERS.md
git commit -m "docs(characters): Wren Mistwalker, the Wayfinder"
```

Expected: Wren's heading appears once, above `## The oath`.

---

### Task 4: Wire Wren and the fog sections into `quest.md`

**Files:**
- Modify: `plugin/commands/quest.md` (six anchored edits)

**Interfaces:**
- Consumes: agent type `fog-cartographer` @ haiku (Task 2).
- Produces: roster row (validator check 8), fog triage lane, plan-template sections, gating trigger, dispatch wiring, verify bullet.

All anchors below are exact strings currently in `plugin/commands/quest.md` — use Edit with these `old_string` values.

- [ ] **Step 1: Roster table row**

After the row:

```
| Kael the Tracker | `debug-investigator` | sonnet | Debug mode — standalone |
```

add:

```
| Wren Mistwalker | `fog-cartographer` | haiku | Quest close — parallel with Rook, ONLY when the plan's `## Not yet specified` is non-empty AND the spec carries an `exploration:` field |
```

- [ ] **Step 2: Step 0 — fog triage lane**

After the paragraph ending:

```
For **anything that touches executable code** — even one line, even an obvious-looking typo in a Python identifier — fall through to Step 1 and run the appropriate mode. Bias: when in doubt, do not fast-lane.
```

add:

```markdown
**Fog lane (the opposite failure):** if the ask names no destination at all — "explore whether we should…", "figure out our approach to…", a wish with nothing checkable at the end — it is not a quest yet; it is fog. Do NOT plan on guesses. Recommend `/idd-framework:chart` (the IDD phase-0 Exploration) and stop. The test is wayfinder's sharpness test: a quest needs a destination you can state in a sentence; if the user can't, charting — not questing — is the next step. When IDD-framework is not installed, say so and ask the user to sharpen the ask instead.
```

- [ ] **Step 3: Step 3.7 gating table + fog discipline note**

(a) In the Step 3.7 trigger table, after the row:

```
   | Lior | `accessibility-reviewer` | Vera was dispatched (UI work present) — Lior pairs with her. |
```

add:

```
   | Wren | `fog-cartographer` | Quest-close scribe, not a reviewer: fires ONLY when the plan's `## Not yet specified` is non-empty AND the spec frontmatter carries `exploration:`. Both conditions or skip. |
```

(b) After the paragraph ending:

```
   Record your selection — and your reasoning for any reviewer you skipped — in the plan file's `## Reviewers selected` section. The decision must be auditable.
```

add a new numbered-list-adjacent paragraph (it sits between items 7 and 8; do not renumber anything):

```markdown
   **Fog discipline:** while planning, a question you cannot sharpen without guessing goes into the plan's `## Not yet specified` — never silently resolved by assumption. Work you consciously rule out goes into `## Out of scope` (gist + why). The sharpness test decides which side of the line an item sits on: phrase-able precisely → it's an open item (or an Exploration ticket, via Wren); not phrase-able → fog. `## Open items for the user` stays reserved for sharp, actionable items.
```

- [ ] **Step 4: Plan template sections + gated list row**

(a) In the plan file template, replace:

```
## Decisions made by Mordain
- <decision> — <reasoning>

## Lessons for the Guildhall
```

with:

```
## Decisions made by Mordain
- <decision> — <reasoning>

## Not yet specified
- <in-scope question too unsharp to dispatch on — sharpness test: can you
   phrase it precisely? then it's an open item or a ticket, not fog. Write
   "none" if planning surfaced no fog>

## Out of scope
- <work consciously ruled beyond this quest — gist + why, so it doesn't
   resurface as an open item. Write "none" if nothing was ruled out>

## Lessons for the Guildhall
```

(b) In the template's `## Reviewers selected` gated list, after:

```
- Vera (`ui-test-author`) — <fired | skipped> — <reason>
```

add:

```
- Wren (`fog-cartographer`) — <fired | skipped> — <reason: both gate conditions, or which one failed>
```

- [ ] **Step 5: Step 4 closer wiring + parallelism rule**

(a) Replace:

```
3. **Sequential closer:**
   - `pr-author` (Rook) — after reviews complete, ALWAYS sequential-last. Emits PR title + body to stdout; the user creates the PR. If Garran was dispatched, Rook MUST fold his runbook output into the PR body's reviewer-notes section.
```

with:

```
3. **Closer:**
   - `pr-author` (Rook) — after reviews complete, ALWAYS last in the sequence. Emits PR title + body to stdout; the user creates the PR. If Garran was dispatched, Rook MUST fold his runbook output into the PR body's reviewer-notes section.
   - `fog-cartographer` (Wren) — fires in the SAME assistant message as Rook when her Step 3.7 gate holds (plan's `## Not yet specified` non-empty AND spec has `exploration:`). File-disjoint with Rook (she writes only under `docs/explorations/`; he is stdout-only), so parallel dispatch is safe. Hand her the plan file path and the `exploration:` id.
```

(b) In the parallelism rules, replace:

```
- `pr-author` is always sequential-last — he needs the completed picture (all reviews in, final diff).
```

with:

```
- `pr-author` is always last in the sequence — he needs the completed picture (all reviews in, final diff). `fog-cartographer` (Wren) is the one dispatch allowed alongside him: she reads the finished plan file and writes only under `docs/explorations/`, disjoint from everything Rook reads and emits.
```

- [ ] **Step 6: Step 5 verify bullets**

(a) In the **Closer verification** section, after the `pr-author` bullet ending:

```
The user creates the PR themselves.
```

add:

```markdown
- **After `fog-cartographer` (Wren):** read her report, then `Read` the map she touched — every entry she claims to have transcribed must actually appear (fog appended or ticket created), verbatim. If she reported a mismatch (missing Exploration, ambiguous map match), record it in the plan's Open items; do not retry her against a map that isn't there.
```

(b) In the Step 5 **Build chain verifications**, after the bullet beginning `- **Before dispatching `refactorer` (Tink):**` (ends `...not "clean it up."`), add:

```markdown
- **Fog at the gates:** when a Step 5 gate break reveals genuine fog — a question about intent the spec cannot answer and you cannot sharpen without guessing — record it in the plan's `## Not yet specified` (it is Wren's cargo at quest close) rather than inventing a resolution. A fixable defect is not fog; route defects through the retry budget as usual.
```

- [ ] **Step 7: Verify all six edits landed**

```bash
grep -c 'fog-cartographer' plugin/commands/quest.md
grep -n 'Fog lane\|Fog discipline\|Fog at the gates\|## Not yet specified' plugin/commands/quest.md
```

Expected: `fog-cartographer` appears ≥ 5 times; all four named anchors found.

- [ ] **Step 8: Commit**

```bash
git add plugin/commands/quest.md
git commit -m "feat(quest): fog triage lane, Not-yet-specified/Out-of-scope plan sections, gated Wren dispatch"
```

---

### Task 5: Mirror surfaces — README, plugin.json, CLAUDE.md

**Files:**
- Modify: `plugin/README.md` (roster table)
- Modify: `plugin/.claude-plugin/plugin.json` (version + description)
- Modify: `CLAUDE.md` repo root (agent counts + Haiku tier list)

**Interfaces:**
- Consumes: `fog-cartographer` @ haiku (canonical, Task 2).
- Produces: tier-consistent mirrors (validator check 8 passes).

- [ ] **Step 1: README roster row**

`plugin/README.md` has a roster table headed `| Adventurer | Agent | Role | Model |`. After its `debug-investigator` row (locate with `grep -n 'debug-investigator' plugin/README.md`), add, matching the table's column style:

```
| Wren Mistwalker | `fog-cartographer` | Writes quest-discovered unknowns back to the linked IDD Exploration (gated: fog present + `exploration:` lineage) | Haiku |
```

If the README states agent/adventurer counts (locate with `grep -n '17 adventurers\|18 agent' plugin/README.md`), update: 17→18 adventurers, 18→19 agents.

- [ ] **Step 2: plugin.json version + description**

In `plugin/.claude-plugin/plugin.json`: set `"version": "0.7.0"`. Then `grep -o '"description".*' plugin/.claude-plugin/plugin.json` — if the description names agent counts or tier groupings, update them (18→19 agents / 17→18 adventurers; add `fog-cartographer` to any Haiku grouping). Validator check 8 treats description tier groups at warn severity — fix them anyway.

- [ ] **Step 3: Repo-root CLAUDE.md**

Three anchored edits:

(a) In the intro: `it ships one slash command (`/quest`) and 18 agent definitions (17 adventurers tiered across Opus / Sonnet / Haiku, plus the `model-echo` diagnostic)` → `…19 agent definitions (18 adventurers…)`.

(b) In **Model tiers**, the Haiku line: `**Haiku:** `refactorer` (Tink), `plugin-validator` (Tabs).` → `**Haiku:** `refactorer` (Tink), `plugin-validator` (Tabs), `fog-cartographer` (Wren).` (keep the sentence that follows).

(c) In the dispatch-phases section, after the sentence about `pr-author` being sequential-last, append: `A gated quest-close scribe, `fog-cartographer` (Wren), may fire in the same message as `pr-author` — file-disjoint (writes only `docs/explorations/**`) — when the plan recorded fog AND the spec carries `exploration:` lineage (see the fog-of-war design, `docs/superpowers/specs/2026-07-28-fog-of-war-design.md`).`

- [ ] **Step 4: Commit**

```bash
git add plugin/README.md plugin/.claude-plugin/plugin.json CLAUDE.md
git commit -m "feat(harness): fog-of-war — Wren roster mirrors, tier lists, counts (v0.7.0)"
```

---

### Task 6: Validate

**Files:** none (verification only)

- [ ] **Step 1: Run the validator**

```bash
python scripts/validate_plugin.py
```

Expected: exit 0, no `check 8` errors. If check 8 flags a surface (`quest.md roster says fog-cartographer = X, frontmatter says haiku`), fix that surface to say `haiku` and re-run — frontmatter is canonical.

- [ ] **Step 2: Confirm clean tree, push, open PR**

```bash
git status --short
git push -u origin feat/fog-cartographer
gh pr create --title "feat: fog-of-war — plan-file fog sections + gated fog-cartographer (v0.7.0)" --body "Implements Part 2 of docs/superpowers/specs/2026-07-28-fog-of-war-design.md: Not-yet-specified / Out-of-scope plan sections, Step 0 fog triage lane, and Wren Mistwalker (fog-cartographer, Haiku) — gated write-back of quest-discovered unknowns to the linked IDD Exploration. Companion to IDD-framework v1.6.0 (Explorations).

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

Expected: clean tree (only committed changes), PR URL printed.

---

### Task 7: Dogfood gate (manual, fresh sessions — after IDD v1.6.0 is installed)

**Files:** none in this repo (exercise runs in `D:\Source\repos\testidd` with both plugins installed)

- [ ] **Step 1:** Fresh session: `/quest` with a fog-shaped ask ("explore whether we should…"). Verify the Step 0 fog lane fires: no plan file, `/idd-framework:chart` recommended.
- [ ] **Step 2:** Fresh session: run a feature `/quest` against a spec that carries `exploration: EXPL-<id>` and contains one deliberately underspecified corner. Verify: the unknown lands in the plan's `## Not yet specified` (not silently resolved); Wren fires alongside Rook; the map gains the entry (or a sharp ticket) verbatim; Mordain's verify step Read the map.
- [ ] **Step 3:** Fresh session: same quest shape but with an empty `## Not yet specified`. Verify Wren is SKIPPED with the reason recorded in `## Reviewers selected`.
- [ ] **Step 4:** Same, but spec without `exploration:` lineage. Verify Wren is skipped for the lineage reason, and the fog stays in the plan file per the plan-file-only fallback.
- [ ] **Step 5:** Record any prompt fixes as Lessons, apply, merge the PR.
