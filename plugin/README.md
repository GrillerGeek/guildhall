# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.8.

## The guild

**Mordain the Keeper** — the Guildmaster — is embodied in the `/quest` command itself. He is not a dispatchable adventurer. When you issue a quest, Mordain is the one planning, picking mode, dispatching adventurers, and verifying their handoffs. His `Write` access is scoped narrowly to the quest's plan file at `docs/guildhall/plans/*.md` — a forcing function that keeps him from doing the adventurers' code-writing work.

The seventeen adventurers:

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

## Design principles

1. **Each adventurer has ONE job.** No multi-purpose coder.
2. **Prototype-mode ≠ feature-mode.** Different ceremony, different bars.
3. **Independence as a guardrail.** test-author is independent of feature-implementer. debug-investigator does NOT fix.
4. **Consume IDD artifacts directly.** test-author and feature-implementer both read IDD Spec files (Expectations, Boundaries) as first-class inputs.
5. **Literal-friendly for Opus 4.8.** Prompts state the contract explicitly — inputs, outputs, in-scope, out-of-scope. No hand-waves.

## Integration with IDD-framework

Guildhall is the implementation-side complement to the [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. IDD handles specs (Intentions → Expectations → Spec → review); Guildhall handles code (plan → test → implement → refactor) from those specs. For how the two map onto the broader seven-stage AI coding workflow (Grill → Research → Prototype → PRD/Plan → Issues/Tasks → Implement → Review), see [How Guildhall fits the AI coding workflow](../README.md#how-guildhall-fits-the-ai-coding-workflow).

## Cost posture

The orchestrator runs on the parent session model for reasoning-heavy planning — Opus 4.8 by default; run `/quest` from a Claude Fable 5 session for the hardest quests (orchestration is the one seat where top-tier spend pays for itself; adventurers never dispatch on `fable`). Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter. Every quest's plan file records the orchestrating model in its `parent_model` frontmatter, so cost and quality are attributable per quest.

**How routing works:** each adventurer declares its intended model in its `plugin/agents/<name>.md` frontmatter — the canonical tier source. At dispatch time Mordain resolves each tier from the roster table inside `quest.md` (a validator-enforced mirror of that frontmatter, since v0.6.1 — reading the agent file directly only as a fallback) and passes it explicitly as the `model` parameter on the `Agent(...)` dispatch call. This is a workaround for an upstream Claude Code issue where subagent frontmatter `model:` values were silently ignored — the explicit dispatch parameter is honored where the frontmatter alone was not. (Re-verified 2026-06-10: current Claude Code honors the frontmatter again when no parameter is given; the explicit parameter still takes precedence and is retained as a belt-and-braces measure.) The `model-echo` self-check at the start of every quest verifies routing is functioning — Mordain dispatches it with `model: "haiku"`, deliberately different from its `sonnet` frontmatter, so the reply reveals *which* mechanism routed it: `haiku` means the dispatch parameter is honored, `sonnet` means only the frontmatter is honored (cost posture intact, workaround inert), anything else means neither.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, neither the dispatch parameter nor the agent frontmatter was honored (environment variable, enterprise plan constraint, or deeper Claude Code issue). Investigate before trusting the cost posture for that quest. A softer note — "param ignored; frontmatter honored" — means tier routing still landed and cost posture holds, but the belt-and-braces parameter is inert on your Claude Code version.
