---
title: Guildhall v0.3 — Opus 4.7 revamp
date: 2026-04-23
status: approved (brainstorming phase)
author: Jason Robey (design); brainstormed with Claude Opus 4.7
supersedes: plugin/README.md v0.2.2 roster and cost posture sections
---

# Guildhall v0.3 — Opus 4.7 revamp

## Context

Guildhall v0.2.2 was built around Opus 4.6. Opus 4.7 (released April 2026) is **more literal**: it will not silently generalize an instruction, will not infer requests the user did not make, and uses fewer tool calls and fewer subagents by default. Anthropic's own migration guidance calls this out: *"prompts written for earlier models can sometimes now produce unexpected results."*

In addition, dogfooding surfaced two structural gaps:

1. **Model routing does not work.** All six adventurers appeared to run on Opus even though five declared `model: sonnet` in frontmatter and one declared `model: claude-sonnet-4-6`. The cost-posture story in the README is aspirational, not operational.
2. **Roster is TDD-complete but coding-lifecycle-incomplete.** The six existing adventurers cover test → implement → refactor → debug → prototype → UI-test, but the harness has no security review, no architecture review, no docs writer, no PR author, and no plugin validator — all of which recur in the user's real work mix (web apps, CLI tools, plugin meta-work, DevOps/data).

v0.3 addresses both: expand the roster to eleven adventurers plus Mordain, add a durable plan artifact, adopt parallel fan-out for post-green review work, standardize on alias-only model frontmatter, add a self-check diagnostic, and tighten every prompt for 4.7's literalness.

## Goals

- **Make cost-posture real.** After v0.3, a feature quest should spend roughly 20% of tokens on Opus (orchestration + heavy review), 75% on Sonnet (execution), and 5% on Haiku (mechanical checks). A diagnostic self-check at quest start surfaces drift.
- **Cover the full coding lifecycle** for web apps + CLI tools + plugin development + DevOps/data work, without bloat.
- **Produce durable artifacts.** Every quest writes a committed plan file that is reviewable, resumable across sessions, and auditable.
- **Stay token-efficient.** Fewer, sharper specialists over many mediocre ones. Every adventurer has one job with explicit non-goals.
- **Align prompt style with 4.7 literalness.** Explicit INPUT / OUTPUT / NON-GOALS / EFFORT blocks in every agent; no hand-waves.

## Non-goals

- **Not replacing Superpowers.** Guildhall stands alone. No imports, no chains, no entanglement. Users who have both installed pick the tool by intent.
- **Not integrating with Azure DevOps or GitHub tooling.** The `pr-author` agent emits platform-agnostic markdown to stdout. The user runs `az repos pr create` (or the web UI, or `gh`) themselves.
- **Not adding a formal tiering abstraction in this release.** The Opus / Sonnet / Haiku split is present per-agent but not yet a routing function in `/quest`. That becomes v1.0 work if the v0.3 roster proves out.
- **Not changing `/quest`'s user-facing surface.** Still `/quest <task description>`. All changes are internal.

## Approach summary

Approach A from brainstorming: **Tight Guild** — keep the six existing adventurers, add five specialists (security-reviewer, architecture-reviewer, docs-writer, pr-author, plugin-validator) plus one diagnostic (model-echo), adopt committed plan.md + parallel fan-out, standardize frontmatter, and tighten prompts.

Rejected alternatives:
- *Broad Guild* (8–10 new agents): too much maintenance for specialists that will be rarely used. Add them later on demand.
- *Tiered Guild* (formal `route(task) → tier` function): premature; commits us to a model-routing mechanism we have not yet verified.

## Section 1 — Roster

### Retained (prompts tightened, behavior unchanged)

| # | Name | Agent | Model | Role |
|---|---|---|---|---|
| 1 | Pip Quickfoot | `prototype-builder` | sonnet | Fast spike, disposable |
| 2 | Seraphine Dawnveil | `test-author` | sonnet | Red tests from spec |
| 3 | Bruga Ironseam | `feature-implementer` | sonnet | Green code from blueprint |
| 4 | Tink Whiffletree | `refactorer` | sonnet | Narrow refactors, behavior-preserving |
| 5 | Kael the Tracker | `debug-investigator` | sonnet | Root cause, no fix |
| 6 | Vera Nightwhistle | `ui-test-author` | sonnet | Playwright E2E |

### New adventurers

| # | Name | Agent | Model | Class/Race | When dispatched |
|---|---|---|---|---|---|
| 7 | Oriana the Watcher | `security-reviewer` | **opus** | Paladin, Oath of Vigilance | Post-green, parallel. Diff + spec in; findings out; read-only. |
| 8 | Aldric Stonemap | `architecture-reviewer` | **opus** | Diviner Wizard (Mordain's protégé) | Pre-dispatch in feature mode when work is novel or cross-cutting. |
| 9 | Cassian Inkwell | `docs-writer` | sonnet | Bard, College of Lore | Post-green, parallel. Updates README / CLI help / docstrings / API docs. |
| 10 | Rook Mossbrook | `pr-author` | sonnet | Rogue (Mastermind) | Quest close. Platform-agnostic PR title + body to stdout. |
| 11 | Tabs Grinspoon | `plugin-validator` | **haiku** | Artificer's Apprentice, Gnome | On demand for plugin meta-work. Lints manifest / frontmatter / conventions. |
| — | *model-echo* | `model-echo` | sonnet | (diagnostic, no character) | First action of every quest; verifies model routing. |

### Deliberate non-additions (and why)

- **perf-profiler** — one-off work; `debug-investigator` + explicit ask covers it.
- **migration-specialist** — rare; Mordain's design-pass + feature chain handles.
- **devops-specialist** — mostly mechanical editing; `feature-implementer` handles.
- **data-modeler** — folded into `architecture-reviewer`.
- **prompt-reviewer** — covered by `architecture-reviewer` + `plugin-validator`.
- **commit-author** — Superpowers has this; we keep them separate.

## Section 2 — Orchestration and plan.md

### New `/quest` flow

1. **Mode selection** — feature / prototype / debug (unchanged).
2. **Model self-check** (NEW) — Mordain dispatches `model-echo`. Result cached in plan.md. Banner on mismatch; does not block.
3. **Plan** — Mordain reads spec (feature), repro (debug), or ask (prototype); greps/reads relevant code; optionally dispatches `architecture-reviewer` for novel work; writes `docs/guildhall/plans/YYYY-MM-DD-<slug>.md` and mirrors as TodoWrite.
4. **Dispatch** — sequential TDD chain, then parallel review fan-out, then sequential closer.
5. **Verify gates** — red after test-author, green after feature-implementer, still-green after refactorer, reviewers report-only.
6. **Report** — Mordain updates plan.md with outcome, emits a concise report.

### plan.md template (committed artifact)

```markdown
---
quest: <one-line ask>
mode: feature | prototype | debug
started: <ISO8601>
spec: <path to IDD spec if feature mode>
slug: <kebab-case>
status: in_progress | completed | abandoned
model_check: <result from model-echo, e.g., "sonnet (ok)" or "opus (MISMATCH)">
---

# Plan

## Context
- Spec's Expectations (quoted verbatim)
- Cited patterns from the codebase
- Any relevant decisions already made

## Dispatch sequence

### Sequential build
1. [ ] <adventurer> — <agent type>
   - Input: <paths, spec sections>
   - Expected: <artifact>

### Parallel reviews (after green)
- [ ] <adventurer> — <agent type>
   - Input: <diff + spec>
   - Focus: <narrow area>

### Closer
- [ ] <adventurer> — <agent type>

## Decisions made by Mordain
- <decision> — <reasoning>

## Open items for the user
- <filled at quest close>
```

### Parallel-dispatch mechanics

- Mordain fires multiple `Agent(...)` calls in **a single assistant message** to parallelize.
- Parallel batch is **post-green only**. TDD chain stays strictly sequential.
- Two agents are parallel-safe iff their outputs touch disjoint files AND neither depends on the other's report.
- Safe parallel batch: `security-reviewer ∥ docs-writer ∥ (ui-test-author if UI)`.
- `pr-author` is always sequential-last (needs the full picture).

### Plan location

All Guildhall artifacts live under `docs/guildhall/`. Distinct from IDD's `docs/specs/` (specs) and Superpowers' `docs/superpowers/specs/` (designs).

## Section 3 — Model routing and effort

### Rule 1: aliases only

Every agent's `model:` frontmatter uses `sonnet` | `opus` | `haiku` — never full IDs. This matches the documented path that is confirmed to work across Claude Code subagent dispatch.

Migration: revert `test-author.md` from `model: claude-sonnet-4-6` to `model: sonnet`. All five new agents ship with alias-only.

### Rule 2: model-echo self-check

Every quest's first action. Dispatches a diagnostic agent with `model: sonnet` and asks it to report the model it is running on. Mordain caches the result in plan.md under `model_check` in the frontmatter.

On mismatch (self-check says Opus): emit a non-blocking warning banner naming likely causes (`ANTHROPIC_MODEL` env var, Opus-only plan, plugin frontmatter bug). Quest proceeds. User can Ctrl-C if they do not want to pay.

Rationale: blocking would kill flow; non-blocking with clear surfacing preserves cost awareness as a choice.

### Rule 3: explicit effort in each adventurer's prompt

Each agent's prompt body states its expected effort level. Not a YAML field (frontmatter does not support effort), but a prompt-level contract that 4.7 will honor literally and that future harness plumbing can key off.

| Agent | Effort |
|---|---|
| Mordain (`/quest`) | xhigh |
| `architecture-reviewer` | xhigh |
| `security-reviewer` | xhigh |
| `debug-investigator` | xhigh |
| `test-author` | high |
| `feature-implementer` | high |
| `refactorer` | high |
| `ui-test-author` | high |
| `prototype-builder` | medium |
| `docs-writer` | medium |
| `pr-author` | medium |
| `plugin-validator` | low |

### Rule 4: cost posture (documented, not enforced)

Expected mix for a typical feature quest:

- Opus: ~20% (Mordain + `security-reviewer` + optional `architecture-reviewer`)
- Sonnet: ~75% (TDD chain + UI tests + docs + PR)
- Haiku: ~5% (`plugin-validator`, model-echo)

If the self-check banner fires, this mix is void — investigate.

### Rule 5: out of scope for this release

- Not reading `ANTHROPIC_MODEL` and conditionally aborting.
- Not bolting CLI `--model` flags onto `/quest`.
- Not removing frontmatter to "accept Opus everywhere" — defeats the cost goal.

## Section 4 — Handoff contracts

Every `Agent(...)` dispatch from Mordain uses the fixed handoff template:

```
You are <Name>, the <Role>.

=== MISSION (this dispatch) ===
<1–2 sentences>

=== INPUTS ===
- <artifact paths or inline content>

=== EXPECTED OUTPUT ===
<shape of output Mordain needs back>

=== EXPLICIT NON-GOALS ===
<reminders pulled from the agent's contract>

=== HANDOFF CONTEXT FROM PRIOR ADVENTURERS ===
<only what this agent needs, not the full plan.md>
```

This template is documented in `quest.md`. It is the load-bearing mechanism for Opus 4.7 literalness: explicit inputs, explicit outputs, explicit non-goals, no hand-waves.

### Per-agent contracts

**`prototype-builder`** — input: one-line ask + repo conventions. Output: working code + one-line "works / doesn't" summary. Non-goals: no tests, no error handling for cases not seen.

**`test-author`** — input: IDD spec path (Expectations load-bearing). Output: failing test files + paths. Non-goals: do NOT read implementation; if spec ambiguous, flag and stop.

**`feature-implementer`** — input: spec + failing-test paths + Boundaries block. Output: passing code. Non-goals: do NOT modify tests; do NOT add features outside Expectations; if blueprint malformed, return to Mordain.

**`refactorer`** — input: scoped instruction + current test state (green). Output: behavior-preserving diff + green confirmation. Non-goals: do NOT broaden scope one line; mention unrelated issues in report only.

**`debug-investigator`** — input: bug repro + error trace + relevant paths. Output: written root-cause report. Non-goals: do NOT propose fix; do NOT edit files; if uncertain, say so and list ruled-outs.

**`ui-test-author`** — input: spec + running-app URL + feature code paths. Output: Playwright test files + selector notes.

**`security-reviewer`** (Opus, xhigh) — input: diff + spec + optional prior reports. Output: findings list (severity / file:line / category / description / remediation) + summary line. Non-goals: read-only; no code outside diff unless reached from diff; no infra speculation.

**`architecture-reviewer`** (Opus, xhigh) — input: spec or prose description + Mordain's stated question + surveyed paths. Output: 2–3 alternatives with pros/cons + recommendation + reasoning + deviation call-outs. Non-goals: no Write/Edit; do not commit to one approach without alternatives; do not read tests.

**`docs-writer`** (Sonnet, medium) — input: diff + spec + explicit surface list (README, CLI help, docstrings, API docs, CHANGELOG) + 1–2 style examples. Output: edits to named files + one-line summary per file. Non-goals: no new docs for unrelated code; code changes allowed only for docstrings on touched functions; do not invent API behavior.

**`pr-author`** (Sonnet, medium) — input: plan.md path + `git diff base...HEAD` + commit subjects + detected platform (`azure-devops` | `github` | `other`, from `git remote -v`; defaults to `other`). Output (stdout only): PR title + markdown body (Summary / Plan reference / Test plan / Reviewer notes) + a platform-appropriate "How to create this PR" footer. Non-goals: NEVER run `az repos pr create` or `gh pr create`; NEVER push; no AI co-author footer unless repo history has one.

**`plugin-validator`** (Haiku, low) — input: plugin directory path + optional check list. Output: findings list (file:line / category / severity / description / suggested fix) + summary. Checks: manifest schema, agent frontmatter required fields, example-block indentation (2 spaces), alias-only model, valid tool names, commands' allowed-tools set, no secrets. Non-goals: report-only; static only, do not run the plugin.

**`model-echo`** (Sonnet, low) — input: none. Output: single line `model: <string>` derived from introspection (env, harness exposure). Non-goals: do nothing else.

## Section 5 — Folder layout and migration

### Final plugin layout after v0.3

```
guildhall/
├── plugin/
│   ├── .claude-plugin/plugin.json             # version 0.3.0
│   ├── agents/
│   │   ├── prototype-builder.md               # tightened
│   │   ├── test-author.md                     # alias reverted
│   │   ├── feature-implementer.md             # tightened
│   │   ├── refactorer.md                      # tightened
│   │   ├── debug-investigator.md              # tightened
│   │   ├── ui-test-author.md                  # tightened
│   │   ├── security-reviewer.md               # NEW (Oriana, Opus)
│   │   ├── architecture-reviewer.md           # NEW (Aldric, Opus)
│   │   ├── docs-writer.md                     # NEW (Cassian, Sonnet)
│   │   ├── pr-author.md                       # NEW (Rook, Sonnet)
│   │   ├── plugin-validator.md                # NEW (Tabs, Haiku)
│   │   └── model-echo.md                      # NEW (diagnostic)
│   ├── commands/quest.md                      # rewritten
│   ├── CHARACTERS.md                          # +5 sheets + diagnostic footnote
│   └── README.md                              # updated roster + cost posture
├── docs/
│   └── guildhall/
│       └── plans/                             # NEW — per-quest plan files
│           └── .gitkeep
├── CLAUDE.md                                  # pointer to v0.3 changes
├── README.md                                  # updated
└── LICENSE
```

### Staircase release plan

Each rung is independently valuable. We can stop or pivot at any rung.

| Version | Change | Rationale |
|---|---|---|
| v0.2.3 | Revert `test-author` to `model: sonnet` alias | One-line fix; validates the alias-over-full-ID hypothesis. |
| v0.2.4 | Add `model-echo.md` + wire self-check into `quest.md` (minimal) | Surfaces the routing bug deterministically. Gets data. |
| v0.2.5 | Tighten the six existing prompts for 4.7 literalness | Prompt hygiene; explicit INPUT/OUTPUT/NON-GOALS/EFFORT blocks. No new agents yet. |
| v0.3.0 | Ship the five new adventurers, new `quest.md` with plan.md + parallel fan-out, updated README / CHARACTERS / CLAUDE | Main release. |
| v0.3.1 | Tuning pass based on one dogfooded quest per mode (feature / prototype / debug) | Real-use friction drives real fixes. |

### Breaking changes

None. `/quest` surface is unchanged. `docs/guildhall/plans/` is additive.

### What this design does NOT commit us to

- A formal `route(task) → tier` routing function. That is a v1.0 concern if v0.3 proves out.
- An Azure DevOps MCP integration. `pr-author` stays stdout-only until one exists.
- Rebuilding Mordain's orchestration around Superpowers skills. They stay separate.

## Open questions resolved during brainstorming

| Question | Resolution |
|---|---|
| Scope of revamp | Full revamp: tune + expand + rethink orchestration |
| Work types to optimize for | All four (web, CLI, plugin meta, DevOps/data) |
| Superpowers relationship | Fully separate; no integration |
| Plan artifact durability | Committed plan.md + TodoWrite mirror |
| Parallelism appetite | Parallel where independent; TDD chain stays sequential |
| Model routing strategy | Aliases + per-agent effort tuning |
| Self-check on mismatch | Non-blocking warning; user can Ctrl-C |
| PR author platform | Stdout-only (Azure DevOps; no CLI hook yet) |
| Release shape | Staircase (v0.2.3 → v0.2.4 → v0.2.5 → v0.3.0 → v0.3.1) |

## Risks and mitigations

- **Risk:** the self-check at v0.2.4 reveals alias frontmatter is broken too, not just full IDs. **Mitigation:** pause the staircase, open an upstream Claude Code issue, fall back to explicit `--model` in session as a workaround until fixed. **Update (2026-04-23):** dogfood run confirmed the bug and v0.2.5 documented the pause; staircase subsequently resumed at v0.2.6 on the reframe that roster value and prompt clarity are independent of model-tier routing — the cost posture activates latently when upstream ships a fix.
- **Risk:** Opus 4.7's "fewer subagents by default" behavior causes Mordain to under-dispatch the new reviewers. **Mitigation:** each adventurer's trigger condition is explicit in the `/quest` command text, and the plan.md template names the full dispatch sequence before Mordain starts dispatching.
- **Risk:** prompt maintenance burden grows with 11 agents. **Mitigation:** the handoff template is centralized in `quest.md`; each agent's contract block is short and diff-reviewable; `plugin-validator` catches frontmatter drift.
- **Risk:** the plan.md format ossifies and becomes a straitjacket. **Mitigation:** template is advisory, not validated by any agent. Treat the first 3 quests as calibration and revise the template in v0.3.1 if friction is high.

## Next step

Invoke `superpowers:writing-plans` to produce the implementation plan for the v0.2.3 rung (the smallest, safest first step). Subsequent rungs get their own plans as we move up the staircase.
