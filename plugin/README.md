# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus-tier orchestration — Opus 5 is the recommended seat.

## The guild

**Mordain the Keeper** — the Guildmaster — is embodied in the `/quest` command itself. He is not a dispatchable adventurer. When you issue a quest, Mordain is the one planning, picking mode, dispatching adventurers, and verifying their handoffs. His `Write` access is scoped narrowly to the quest's plan file at `docs/guildhall/plans/*.md` — a forcing function that keeps him from doing the adventurers' code-writing work.

The eighteen adventurers:

| Adventurer | Agent | Role | Model |
|---|---|---|---|
| **Aldric Stonemap** *(optional)* | `architecture-reviewer` | Cartographer. 2–3 alternatives with trade-offs; recommends one. | Opus |
| **Seraphine Dawnveil** | `test-author` | Oracle. Red tests from the Spec; never reads implementation. | Sonnet |
| **Bruga Ironseam** | `feature-implementer` | Smith. Green code from the blueprint. No scope creep. | Sonnet |
| **Tink Whiffletree** *(optional)* | `refactorer` | Enchanter. Narrow scoped refactors; preserves behavior. | Haiku |
| **Vera Nightwhistle** *(gated: UI)* | `ui-test-author` | Playwright. Drives Playwright E2E tests against the running app. | Sonnet |
| **Oriana the Watcher** | `security-reviewer` | Sentinel. Always-on. Reviews diff for authn / authz / secrets / injection. | Opus |
| **Cassian Inkwell** | `docs-writer` | Scribe. Always-on. Updates named doc surfaces + docstrings on touched code. | Sonnet |
| **Vance Quillmark** *(gated: runtime code)* | `observability-reviewer` | Chronicler. Reviews log structure, error capture, redaction, silent failures. | Sonnet |
| **Thalia Stormgale** *(gated: I/O / concurrency)* | `reliability-reviewer` | Stormwarden. Reviews timeouts, retries, idempotency, degradation. | Opus |
| **Cassia Thornquick** *(gated: DB / hot paths)* | `performance-reviewer` | Smith of cycles. Reviews N+1, unbounded loops, hot-path allocations. | Sonnet |
| **Garran Dunwall** *(gated: user-visible deploy)* | `ops-readiness-reviewer` | Quartermaster. Produces deploy plan / alerts / rollback / on-call notes that Rook folds into the PR. | Sonnet |
| **Ysolde Hollowmoor** *(gated: schema / migrations)* | `migration-safety-reviewer` | Gravedigger. Reviews migrations for lock contention, irreversibility, backfill safety. | Opus |
| **Lior Brightpath** *(gated: UI; pairs with Vera)* | `accessibility-reviewer` | Lampbearer. Reviews UI for keyboard, focus, ARIA, contrast, alt text, motion. | Sonnet |
| **Rook Mossbrook** | `pr-author` | Herald. PR title + body to stdout; never creates the PR itself. | Sonnet |
| **Tabs Grinspoon** *(optional)* | `plugin-validator` | Apprentice. Mechanical lint of Claude Code plugins. | Haiku |
| **Pip Quickfoot** | `prototype-builder` | Scout. Fast spikes, no tests, disposable code. | Sonnet |
| **Kael the Tracker** | `debug-investigator` | Ranger. Finds root cause; does NOT fix. | Sonnet |
| **Wren Mistwalker** *(gated: fog + exploration lineage)* | `fog-cartographer` | Wayfinder. Writes quest-discovered unknowns back to the linked IDD Exploration. | Haiku |

Plus one diagnostic: **`model-echo`** — dispatched first in every quest, deliberately on a model different from its own frontmatter, to verify which routing mechanism (explicit dispatch parameter, frontmatter, or neither) is actually in effect.

Full character sheets in [`CHARACTERS.md`](CHARACTERS.md).

## Installation

### From the marketplace (recommended)

Guildhall is distributed through the [grillergeek-plugins marketplace](https://github.com/GrillerGeek/skills). Run these once inside any Claude Code session:

```
/plugin marketplace add GrillerGeek/skills
/plugin install guildhall@grillergeek-plugins
```

### From a local clone

```bash
# Replace <path-to-repo> with the directory where you cloned guildhall
claude --plugin-dir <path-to-repo>/plugin
```

### Keeping up to date

Restart Claude Code to pick up the latest version. If using `--plugin-dir`, pull first:

```bash
cd <path-to-repo>
git pull
```

## Flow at a glance

For a feature quest, Mordain runs: **model-echo self-check → (optional Aldric) → Seraphine → Bruga → (optional Tink) → parallel fan-out (Oriana + Cassian always; Vance / Thalia / Cassia / Garran / Ysolde / Vera / Lior gated by trigger) → Rook** — with a committed `plan.md` opening the quest and a PR draft closing it. The plan file's `## Reviewers selected` section records which gated reviewers fired and why.

Prototype mode skips to Pip. Debug mode starts with Kael.

## Issuing a quest

```
/quest <task description>
```

Examples:

```
/quest Build a Python CLI that polls Recreation.gov availability for a campground ID.
/quest Implement the reservation feature from spec docs/specs/2026-04-18-reservations.md
/quest The /api/reservations endpoint is returning 500s — figure out why.
```

The orchestrator picks the mode (prototype / feature / debug) and dispatches the right worker(s) in TDD order.

## Quests on a schedule

`/quest` composes with Claude Code's loop primitives — no extra configuration needed:

```
# Babysit a PR: re-run every 30 minutes until you cancel
/loop 30m /quest Address new review comments on PR #12 and fix any failing CI.

# Recurring maintenance as a scheduled cloud routine
/schedule a nightly routine that runs: /quest Apply patch-level dependency bumps and verify the full suite stays green.
```

Two rules of thumb keep scheduled quests cheap and safe:

1. **Give the task text a verifiable stop condition** ("until CI is green", "only patch-level bumps") — Mordain's gates handle correctness within a run, but the loop needs to know when a run has nothing to do.
2. **Match the interval to how often the underlying state actually changes.** A PR that gets one human review a day does not need a five-minute loop.

Docs-fast-lane and debug quests loop cheaply. Full feature quests on a schedule are best reserved for well-defined recurring work (dependency upgrades, triage sweeps) — the spec-or-route-to-`spec-author` rule still applies on every iteration.

## Design principles

1. **Each adventurer has ONE job.** No multi-purpose coder.
2. **Prototype-mode ≠ feature-mode.** Different ceremony, different bars.
3. **Independence as a guardrail.** test-author is independent of feature-implementer. debug-investigator does NOT fix.
4. **Consume IDD artifacts directly.** test-author and feature-implementer both read IDD Spec files (Expectations, Boundaries) as first-class inputs.
5. **Literal-friendly for Opus-tier models.** Prompts state the contract explicitly — inputs, outputs, in-scope, out-of-scope. No hand-waves. (The prompt style was tuned on Opus 4.8 and carries forward.)
6. **Hard rules get hooks, not just prose.** Mordain's plan-file-only `Write` rule is enforced by a deterministic plugin hook, not only by instructions (see below).

## Hooks the plugin installs

Installing Guildhall registers two small hooks (`plugin/hooks/`), both stdlib-Python and both inert outside quests:

- **`quest_flag.py`** (UserPromptSubmit) — marks the session "quest in flight" when you submit `/quest` (or `/guildhall:quest`), and clears the mark on your next non-quest prompt.
- **`quest_write_guard.py`** (PreToolUse on `Write`) — while a quest is in flight, denies any **main-agent** `Write` outside `docs/guildhall/plans/*.md`, with a message steering Mordain to dispatch an adventurer instead. Adventurers (subagents) are never touched — their write access is governed by each agent's own tool list.

This is the deterministic backstop for the design rule that Mordain plans and dispatches but never writes code himself. Ordinary (non-quest) sessions are unaffected. Hooks load at session start, so the guard first takes effect in the next session after installing or updating the plugin.

## Integration with IDD-framework

Guildhall is the implementation-side complement to the [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. IDD handles specs (Intentions → Expectations → Spec → review); Guildhall handles code (plan → test → implement → refactor) from those specs. For how the two map onto the broader seven-stage AI coding workflow (Grill → Research → Prototype → PRD/Plan → Issues/Tasks → Implement → Review), see [How Guildhall fits the AI coding workflow](../README.md#how-guildhall-fits-the-ai-coding-workflow).

## Cost posture

The orchestrator runs on the parent session model for reasoning-heavy planning — the current Opus (Opus 5) by default, per Anthropic's guidance that most agent workloads should start on Opus; run `/quest` from a Claude Fable 5 session for the hardest quests (orchestration is the one seat where top-tier spend pays for itself; adventurers never dispatch on `fable`). Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter — but judge the downgrade by **cost per completed task, not per token**: a cheaper model that breaks gates, burns Mordain's retry budget, or returns blocked costs more than the token savings. The plan files are the measurement instrument — gates held/broken and retries are recorded per quest, and a bad downgrade shows up as recurring entries in `## Lessons for the Guildhall`. Every quest's plan file also records the orchestrating model in its `parent_model` frontmatter, so cost and quality are attributable per quest.

**How routing works:** each adventurer declares its intended model in its `plugin/agents/<name>.md` frontmatter — the canonical tier source. At dispatch time Mordain resolves each tier from the roster table inside `quest.md` (a validator-enforced mirror of that frontmatter, since v0.6.1 — reading the agent file directly only as a fallback) and passes it explicitly as the `model` parameter on the `Agent(...)` dispatch call. This is a workaround for an upstream Claude Code issue where subagent frontmatter `model:` values were silently ignored — the explicit dispatch parameter is honored where the frontmatter alone was not. (Re-verified 2026-06-10: current Claude Code honors the frontmatter again when no parameter is given; the explicit parameter still takes precedence and is retained as a belt-and-braces measure.) The `model-echo` self-check at the start of every quest verifies routing is functioning — Mordain dispatches it with `model: "haiku"`, deliberately different from its `sonnet` frontmatter, so the reply reveals *which* mechanism routed it: `haiku` means the dispatch parameter is honored, `sonnet` means only the frontmatter is honored (cost posture intact, workaround inert), anything else means neither.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, neither the dispatch parameter nor the agent frontmatter was honored (environment variable, enterprise plan constraint, or deeper Claude Code issue). Investigate before trusting the cost posture for that quest. A softer note — "param ignored; frontmatter honored" — means tier routing still landed and cost posture holds, but the belt-and-braces parameter is inert on your Claude Code version.
