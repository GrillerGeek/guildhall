# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Guildhall is a **Claude Code plugin**. As of v0.8.1 it ships one slash command (`/quest`), 19 agent definitions (18 adventurers tiered across Opus / Sonnet / Haiku, plus the `model-echo` diagnostic), and two hooks (`plugin/hooks/` — a UserPromptSubmit quest-flag and a PreToolUse write guard that deterministically enforce Mordain's plan-file-only `Write` rule during quests). There is no application code and no build step; automation is `scripts/validate_plugin.py` — a mechanical implementation of plugin-validator's nine checks — which CI (`.github/workflows/validate.yml`) runs on every push and PR, and which a repo-local PostToolUse hook (`.claude/settings.json` → `scripts/validate_plugin_hook.py`) also runs at edit time on any change under `plugin/`. Hooks (both the plugin's and the repo's) load at session start — editing them requires a fresh session to take effect, like commands. "Running" the plugin means installing it into Claude Code and issuing `/quest`; "testing" a change means dogfooding a quest against a real task — **from a freshly started session**: Claude Code snapshots command/skill content at session start, so a `/quest` issued in the session that edited `quest.md` exercises the stale snapshot, not your change (verified 2026-06-10). Agent files are read at dispatch time and don't have this constraint.

Install for local development:

```bash
claude --plugin-dir <repo>/plugin
```

Version is bumped in `plugin/.claude-plugin/plugin.json`. Recent commit messages follow `type(scope): summary (vX.Y.Z)` — see `git log` for the established style before writing a new one.

## Architecture — the load-bearing facts

Reading any one file tells you *what* Guildhall does. These are the cross-file facts that determine *why* the pieces are arranged the way they are.

### Mordain lives in `/quest`, not in `agents/`

The orchestrator ("Mordain the Keeper") is embodied in `plugin/commands/quest.md`, not a subagent. When this design was set, Claude Code did not surface the `Agent` dispatch tool inside a subagent's tool context, so an "orchestrator agent that dispatches worker agents" could not actually dispatch (commit `f5d9cd5` — `refactor!: move Mordain into /quest command, drop orchestrator agent`; see `plugin/CHARACTERS.md`).

**Re-verified 2026-09-01: current Claude Code DOES allow nested dispatch.** A diagnostic subagent held the `Agent` tool and successfully ran a nested general-purpose dispatch (Anthropic's steering guide documents nesting up to five levels). The top-level seat is retained **by design** regardless: Mordain needs `AskUserQuestion` (mode ambiguity, scope stops — no user channel exists inside a subagent), inherits the parent session's model (the Opus/Fable seat the cost posture assumes), writes the plan file, and keeps every dispatch visible in the main transcript. **Do not propose moving orchestration back into a subagent** — the reasons are now stated intent rather than platform limitation, and older Claude Code versions in the field still lack nested dispatch besides.

### `/quest`'s `Write` access is scoped to plan files only

`plugin/commands/quest.md` frontmatter lists `allowed-tools: Agent, Bash, Read, Write, Grep, Glob, TodoWrite, AskUserQuestion, WebFetch`. `Write` was added in v0.3.0 specifically so Mordain can create the quest's plan file at `docs/guildhall/plans/YYYY-MM-DD-<slug>.md`. The forcing function lives in prose AND, since v0.8.0, in a deterministic hook: `plugin/hooks/quest_write_guard.py` (PreToolUse on `Write`) denies main-agent Writes outside `docs/guildhall/plans/*.md` while a quest turn is in flight (flagged by `plugin/hooks/quest_flag.py` on `/quest` submission, cleared on the next non-quest prompt). Subagent Writes are exempt (the hook input's `agent_id` marks them) — adventurers are governed by their own tool lists. Commands cannot carry frontmatter hooks (only skills/agents can), which is why the guard ships as plugin-level hooks with its own quest-in-flight scoping. If you are editing `quest.md`, keep the narrow-scope wording — the prose is what steers Mordain before the hook ever fires, and it's the only guard on older sessions and on the `Bash` escape hatch.

### Dispatch is phased: sequential build, parallel reviews, sequential closer

- **TDD build chain stays strictly sequential:** (optional `architecture-reviewer`) → `test-author` → `feature-implementer` → (optional `refactorer`). This preserves the **independence guardrail** — `test-author` must not see the implementation.
- **Post-green reviews fan out in parallel:** two always-on (`security-reviewer` ∥ `docs-writer`) plus six gated production-readiness reviewers (`observability-reviewer`, `reliability-reviewer`, `performance-reviewer`, `ops-readiness-reviewer`, `migration-safety-reviewer`, `accessibility-reviewer`) and `ui-test-author` — each fires only when its trigger applies. Mordain fires the selected set in a SINGLE assistant message with multiple `Agent(...)` calls. Independence is verified by file-disjointness (the eight reviewers other than `docs-writer` and `ui-test-author` are stdout-only; `docs-writer` writes to named docs; `ui-test-author` writes to test files).
- **Gating decisions are auditable.** Mordain records which gated reviewers fired and which were skipped (with one-line reasons) in the plan file's `## Reviewers selected` section. The bias on ambiguous triggers is **fire** — a missed reviewer is more expensive than an unnecessary one. Gating triggers are documented in `quest.md` Step 3.7.
- **`pr-author` is always sequential-last.** It needs the completed picture, and folds Garran's runbook output verbatim into the PR body when `ops-readiness-reviewer` fired. A gated quest-close scribe, `fog-cartographer` (Wren), may fire in the same message as `pr-author` — file-disjoint (writes only `docs/explorations/**`) — when the plan recorded fog AND the spec carries `exploration:` lineage (see the fog-of-war design, `docs/superpowers/specs/2026-07-28-fog-of-war-design.md`).
- **Standalone adventurers** (no chain): `prototype-builder`, `debug-investigator`. `debug-investigator` specifically does NOT fix — it reports root cause and returns to Mordain.

When editing `quest.md`, preserve this three-phase shape. Serializing the review fan-out wastes the whole point of those agents' independence; parallelizing the TDD build chain breaks the independence guardrail.

### Subagent model routing requires the explicit `model` dispatch parameter

When this workaround shipped, Claude Code's subagent dispatch did **not** honor the `model:` field in an agent file's frontmatter directly — the agent inherited the parent session's model instead (verified via `model-echo` diagnostic on 2026-04-23). Guildhall works around this by having Mordain pass each adventurer's tier **explicitly** as the `model` parameter on every `Agent(...)` dispatch. The `Agent` tool's `model` parameter IS honored. As of v0.6.1 Mordain resolves tiers from the roster table inside `quest.md` itself (a validator-enforced mirror of the canonical frontmatter — check 8) instead of Glob+Reading every agent file per quest; the file-read path remains as fallback for agents missing from the table.

**Re-verified 2026-06-10:** current Claude Code now honors the frontmatter `model:` when no dispatch parameter is given (model-echo dispatched with no `model` param reported Sonnet under a non-Sonnet parent), and the explicit parameter still works and takes precedence over frontmatter. The explicit-param workaround is **retained** as belt-and-braces — older Claude Code versions in the field still need it, and the cost posture depends on routing being right; PR 4 (v0.6.1) settled the retire-or-keep decision as **keep** (see `docs/superpowers/specs/2026-06-10-model-refresh-design.md`). As of v0.6.4 the Step 2 self-check dispatches `model-echo` with `model: "haiku"` — deliberately different from its `sonnet` frontmatter — so the reply distinguishes param-honored from frontmatter-honored routing instead of being unable to tell them apart.

This means: (a) every `Agent(...)` call in `quest.md` must include the `model` parameter — no exceptions; (b) every agent file must declare `model:` in alias form (`sonnet` / `opus` / `haiku`), never a full model ID; (c) when adding a new agent, add its row to the `quest.md` roster table (Mordain's dispatch-time tier source) — plugin-validator check 8 will fail if the row and the frontmatter ever disagree.

### IDD-framework is the upstream spec producer

Guildhall is the implementation-side complement to the separate [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. The empty `docs/{products,intentions,expectations,specs,reviews}/` directories are the IDD artifact layout — they are consumers' scaffolding, not Guildhall's own. `test-author` and `feature-implementer` both read IDD Spec files (Expectations, Boundaries blocks) as first-class input. When modifying those two agents, preserve the contract that the Expectations block is load-bearing for `test-author` and Boundaries constrains `feature-implementer`.

### Model tiers

`/quest` (Mordain) runs on whatever model the user's session is on — the current Opus (Opus 5) is the recommended default seat (per Anthropic's choosing-a-model guidance: "for most agent workloads, start with Claude Opus 5"), and a Claude Fable 5 session is the recommended seat for the hardest quests. The whole harness exists *because* Opus-tier models from 4.7 onward follow instructions literally and fill in fewer gaps; 4.8 additionally under-reaches for subagents unless told exactly when to dispatch — the explicit dispatch triggers throughout `quest.md` are that telling. The prompt style was tuned on Opus 4.8 (v0.5.0 re-baseline) and carries forward; when re-baselining the tuning claim onto a newer Opus, dogfood a quest from that seat first. **Fable spend is Mordain-only:** no adventurer is ever dispatched with `model: "fable"` — the plugin cannot set Mordain's model (it inherits the session), so "Fable for Mordain" is a documented recommendation, not a dispatch parameter. Each quest's plan file records the orchestrating model in `parent_model` frontmatter for attribution.

**Adventurer tiers (post-v0.4.0):**

- **Opus:** `architecture-reviewer` (Aldric), `security-reviewer` (Oriana), `reliability-reviewer` (Thalia), `migration-safety-reviewer` (Ysolde). The four classes where a miss is hardest to reverse — bad architecture, bad security, cascading prod failures, irreversible data changes.
- **Sonnet:** `test-author`, `feature-implementer`, `ui-test-author`, `docs-writer`, `pr-author`, `prototype-builder`, `debug-investigator`, `observability-reviewer` (Vance), `performance-reviewer` (Cassia), `ops-readiness-reviewer` (Garran), `accessibility-reviewer` (Lior). The majority — execution and structured checklist work.
- **Haiku:** `refactorer` (Tink), `plugin-validator` (Tabs), `fog-cartographer` (Wren). Narrowly-scoped behavior-preserving refactors and mechanical regex / structural checks, and faithful transcription.
- **Diagnostic:** `model-echo` (declared Sonnet in frontmatter, but dispatched with `model: "haiku"` — the deliberate mismatch is what makes its routing check discriminating).

Every agent's `model:` field must use an alias (`sonnet` / `opus` / `haiku`), not a full model ID — full IDs surface as warnings from `plugin-validator`. **Agent frontmatter `model:` is the canonical tier source.** Every other surface — the `quest.md` roster table, the `plugin/README.md` roster table, the `CHARACTERS.md` Model rows, the `plugin.json` description, and the tier list above — is a mirror of frontmatter, and `plugin-validator`'s cross-file tier-consistency check (check 8) flags drift between them. Mordain reads frontmatter at dispatch time per the explicit-`model`-param workaround above.

## Editing conventions for agent and command prompts

- **State the contract explicitly.** Inputs, outputs, in-scope, out-of-scope. Opus-tier models (4.7 onward) are literal-friendly — hand-waves produce drift. Agents open with `## Your contract` (INPUT / OUTPUT / NON-GOALS bullets) and close with `## Hard rules`; between those, the build-chain agents (test-author, feature-implementer, refactorer) use bold inline labels for process and non-goals, while the eight reviewers use a `## What you look for` section instead of a process heading. Match the family you're joining, not a generic template.
- **Each adventurer has ONE job.** Don't broaden an agent's description to cover an adjacent case; that's what a different adventurer (or a new one) is for.
- **A multi-line `description:` MUST be a block scalar (`description: |`), and its body — including `<example>` blocks — is indented 2 spaces** (see commit `320c3c6` for the indent convention). This is not cosmetic: a bare multi-line plain scalar makes Claude Code's frontmatter loader discard the agent's entire metadata and substitute the placeholder `"Agent from guildhall plugin"`, so the agent still dispatches but can no longer be routed to on merit — nothing in the agent list says what it does. Every guildhall agent shipped this way until v0.7.1. The 2-space indent is what sets the block's indentation, so a continuation line at fewer than 2 spaces silently truncates the description. Never leave a plain scalar containing `: ` either (`model: sonnet` inside prose) — that is invalid YAML on any line count. Check 9 enforces both.
- **Character voice is load-bearing.** The D&D personas in `CHARACTERS.md` are not decoration — they're the in-character forcing function that makes violating the contract feel wrong (e.g., Seraphine "has never read an implementation and does not intend to start"). When editing an agent's system prompt, keep the voice; when adding a new agent, write a character sheet in `CHARACTERS.md` too.

## What NOT to add

- No generic "coder" agent. The point of the guild is that each adventurer refuses jobs outside their class.
- No parallelization of the TDD build chain. `test-author` → `feature-implementer` is strictly sequential — the review fan-out parallelism only applies post-green, among agents that don't depend on each other.
- No orchestrator-as-subagent. Mordain stays in `/quest` by design: `AskUserQuestion`, the parent-model seat, plan-file `Write`, and dispatch visibility all live at the top level. (Historically the `Agent` tool was absent in subagent contexts — commit `f5d9cd5`; re-verified 2026-09-01 that current Claude Code allows nested dispatch, but older versions in the field do not.)
- No skipping the explicit `model` parameter on dispatch. Every `Agent(...)` call in `quest.md` must include `model: <alias>`; the frontmatter alone was not honored by older Claude Code versions (re-verified working 2026-06-10, but the explicit param is retained as belt-and-braces) and cost posture depends on routing being right.
- No `Write` access for Mordain beyond plan files. If a new artifact type is needed, either dispatch an adventurer (who has `Write`) or design a new adventurer specifically for it.
- No always-on additions to the post-green fan-out beyond `security-reviewer` and `docs-writer`. New reviewers must be GATED with an explicit trigger documented in `quest.md` Step 3.7, recorded in the plan file's `## Reviewers selected` section. The selectivity is the scaling mechanism — making everything always-on negates the design.
