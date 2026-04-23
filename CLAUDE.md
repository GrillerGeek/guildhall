# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Guildhall is a **Claude Code plugin** — markdown-only. As of v0.3.0 it ships one slash command (`/quest`) and 12 agent definitions (11 adventurers tiered across Opus / Sonnet / Haiku, plus the `model-echo` diagnostic). There is no application code, no build step, no test suite, no linter. "Running" the plugin means installing it into Claude Code and issuing `/quest`; "testing" a change means dogfooding a quest against a real task.

Install for local development:

```bash
cc --plugin-dir <repo>/plugin
```

Version is bumped in `plugin/.claude-plugin/plugin.json`. Recent commit messages follow `type(scope): summary (vX.Y.Z)` — see `git log` for the established style before writing a new one.

## Architecture — the load-bearing facts

Reading any one file tells you *what* Guildhall does. These are the cross-file facts that determine *why* the pieces are arranged the way they are.

### Mordain lives in `/quest`, not in `agents/`

The orchestrator ("Mordain the Keeper") is embodied in `plugin/commands/quest.md`, not a subagent. This is not a stylistic choice — **Claude Code does not surface the `Agent` dispatch tool inside a subagent's tool context**, so an "orchestrator agent that dispatches worker agents" cannot actually dispatch. The `/quest` command runs at the top level, where `Agent` works.

Mordain's origin story (see `plugin/CHARACTERS.md`, and commit `f5d9cd5` — `refactor!: move Mordain into /quest command, drop orchestrator agent`) records this. **Do not propose moving orchestration back into a subagent.** If you're tempted to add a seventh agent that dispatches others, it will fail silently at runtime.

### `/quest`'s `Write` access is scoped to plan files only

`plugin/commands/quest.md` frontmatter lists `allowed-tools: Agent, Bash, Read, Write, Grep, Glob, TodoWrite, AskUserQuestion, WebFetch`. `Write` was added in v0.3.0 specifically so Mordain can create the quest's plan file at `docs/guildhall/plans/YYYY-MM-DD-<slug>.md`. The forcing function is preserved in prose: Mordain must NOT `Write` any other file type. If you are editing `quest.md`, keep the narrow-scope wording — removing the "plan file only" constraint collapses the whole design.

### Dispatch is phased: sequential build, parallel reviews, sequential closer

- **TDD build chain stays strictly sequential:** (optional `architecture-reviewer`) → `test-author` → `feature-implementer` → (optional `refactorer`). This preserves the **independence guardrail** — `test-author` must not see the implementation.
- **Post-green reviews fan out in parallel:** `security-reviewer` ∥ `docs-writer` ∥ (optional `ui-test-author`). Mordain fires them in a SINGLE assistant message with multiple `Agent(...)` calls. Independence is verified by file-disjointness (reviewers either write to different files or are stdout-only).
- **`pr-author` is always sequential-last.** It needs the completed picture.
- **Standalone adventurers** (no chain): `prototype-builder`, `debug-investigator`. `debug-investigator` specifically does NOT fix — it reports root cause and returns to Mordain.

When editing `quest.md`, preserve this three-phase shape. Serializing the review fan-out wastes the whole point of those agents' independence; parallelizing the TDD build chain breaks the independence guardrail.

### Subagent model routing requires the explicit `model` dispatch parameter

Claude Code's subagent dispatch does **not** honor the `model:` field in an agent file's frontmatter directly — the agent inherits the parent session's model instead. Verified via `model-echo` diagnostic on 2026-04-23. Guildhall works around this by having Mordain read each adventurer's `model:` from its frontmatter (the documented source of truth) and pass it **explicitly** as the `model` parameter on every `Agent(...)` dispatch. The `Agent` tool's `model` parameter IS honored.

This means: (a) every `Agent(...)` call in `quest.md` must include the `model` parameter — no exceptions; (b) every agent file must declare `model:` in alias form (`sonnet` / `opus` / `haiku`), never a full model ID; (c) when adding a new agent, also add the read-model step in `quest.md`'s Step 3 if the new agent is dispatched outside the existing sequence.

### IDD-framework is the upstream spec producer

Guildhall is the implementation-side complement to the separate [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. The empty `docs/{products,intentions,expectations,specs,reviews}/` directories are the IDD artifact layout — they are consumers' scaffolding, not Guildhall's own. `test-author` and `feature-implementer` both read IDD Spec files (Expectations, Boundaries blocks) as first-class input. When modifying those two agents, preserve the contract that the Expectations block is load-bearing for `test-author` and Boundaries constrains `feature-implementer`.

### Model tiers

`/quest` (Mordain) runs on whatever model the user's session is on — Opus 4.7 is the intended target; the whole harness exists *because* Opus 4.7 follows instructions literally and fills in fewer gaps than 4.6.

**Adventurer tiers (post-v0.3.0):**

- **Opus:** `architecture-reviewer` (Aldric), `security-reviewer` (Oriana). Missed architecture and missed security are the expensive classes of error.
- **Sonnet:** `test-author`, `feature-implementer`, `refactorer`, `ui-test-author`, `docs-writer`, `pr-author`, `prototype-builder`, `debug-investigator`. The majority — execution and structured summarization.
- **Haiku:** `plugin-validator`. Mechanical regex / structural checks.
- **Diagnostic:** `model-echo` (declared Sonnet; its purpose is verifying the routing workaround).

Every agent's `model:` field must use an alias (`sonnet` / `opus` / `haiku`), not a full model ID — full IDs surface as warnings from `plugin-validator`. The tier assignments are the source of truth that Mordain reads at dispatch time per the explicit-`model`-param workaround above.

## Editing conventions for agent and command prompts

- **State the contract explicitly.** Inputs, outputs, in-scope, out-of-scope. Opus 4.7 is literal-friendly — hand-waves produce drift. Existing agents follow an `## Your contract` / `## Your tools` / `## Your process` / `## Explicit non-goals` / `## Hard rules` skeleton; match it.
- **Each adventurer has ONE job.** Don't broaden an agent's description to cover an adjacent case; that's what a different adventurer (or a new one) is for.
- **Frontmatter example blocks are indented 2 spaces** (see commit `320c3c6`). Keep that when adding `<example>` blocks to an agent's `description`.
- **Character voice is load-bearing.** The D&D personas in `CHARACTERS.md` are not decoration — they're the in-character forcing function that makes violating the contract feel wrong (e.g., Seraphine "has never read an implementation and does not intend to start"). When editing an agent's system prompt, keep the voice; when adding a new agent, write a character sheet in `CHARACTERS.md` too.

## What NOT to add

- No generic "coder" agent. The point of the guild is that each adventurer refuses jobs outside their class.
- No parallelization of the TDD build chain. `test-author` → `feature-implementer` is strictly sequential — the review fan-out parallelism only applies post-green, among agents that don't depend on each other.
- No orchestrator-as-subagent. The `Agent` dispatch tool is not available inside subagent contexts, so moving Mordain out of `/quest` into an agent file would fail silently. (Historical: commit `f5d9cd5` records this lesson.)
- No skipping the explicit `model` parameter on dispatch. Every `Agent(...)` call in `quest.md` must include `model: <alias>`; the frontmatter alone is not honored by Claude Code and cost posture depends on this.
- No `Write` access for Mordain beyond plan files. If a new artifact type is needed, either dispatch an adventurer (who has `Write`) or design a new adventurer specifically for it.
