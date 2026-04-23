# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.7.

## The guild

**Mordain the Keeper** — the Guildmaster — is embodied in the `/quest` command itself. He is not a dispatchable adventurer. When you issue a quest, Mordain is the one planning, picking mode, dispatching adventurers, and verifying their handoffs. His `Write` access is scoped narrowly to the quest's plan file at `docs/guildhall/plans/*.md` — a forcing function that keeps him from doing the adventurers' code-writing work.

The eleven adventurers:

| Adventurer | Agent | Role | Model |
|---|---|---|---|
| **Aldric Stonemap** *(optional)* | `architecture-reviewer` | Cartographer. 2–3 alternatives with trade-offs; recommends one. | Opus |
| **Seraphine Dawnveil** | `test-author` | Oracle. Red tests from the Spec; never reads implementation. | Sonnet |
| **Bruga Ironseam** | `feature-implementer` | Smith. Green code from the blueprint. No scope creep. | Sonnet |
| **Tink Whiffletree** | `refactorer` | Enchanter. Narrow scoped refactors; preserves behavior. | Sonnet |
| **Vera Nightwhistle** *(optional)* | `ui-test-author` | Playwright. Drives Playwright E2E tests against the running app. | Sonnet |
| **Oriana the Watcher** | `security-reviewer` | Sentinel. Reviews diff for authn / authz / secrets / injection. | Opus |
| **Cassian Inkwell** | `docs-writer` | Scribe. Updates named doc surfaces + docstrings on touched code. | Sonnet |
| **Rook Mossbrook** | `pr-author` | Herald. PR title + body to stdout; never creates the PR itself. | Sonnet |
| **Tabs Grinspoon** *(optional)* | `plugin-validator` | Apprentice. Mechanical lint of Claude Code plugins. | Haiku |
| **Pip Quickfoot** | `prototype-builder` | Scout. Fast spikes, no tests, disposable code. | Sonnet |
| **Kael the Tracker** | `debug-investigator` | Ranger. Finds root cause; does NOT fix. | Sonnet |

Plus one diagnostic: **`model-echo`** — dispatched first in every quest to verify that the explicit-model-param workaround is routing correctly.

Full character sheets in [`CHARACTERS.md`](CHARACTERS.md).

## Flow at a glance

For a feature quest, Mordain runs: **model-echo self-check → (optional Aldric) → Seraphine → Bruga → (optional Tink) → parallel fan-out (Oriana ∥ Cassian ∥ optional Vera) → Rook** — with a committed `plan.md` opening the quest and a PR draft closing it.

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
5. **Literal-friendly for Opus 4.7.** Prompts state the contract explicitly — inputs, outputs, in-scope, out-of-scope. No hand-waves.

## Integration with IDD-framework

Guildhall is the implementation-side complement to the [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. IDD handles specs (Intentions → Expectations → Spec → review); Guildhall handles code (plan → test → implement → refactor) from those specs.

## Cost posture

The orchestrator runs on Opus for reasoning-heavy planning. Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter.

**How routing works (as of v0.2.7):** each adventurer declares its intended model in its `plugin/agents/<name>.md` frontmatter. Mordain reads that value during planning and passes it explicitly as the `model` parameter on the `Agent(...)` dispatch call. This is a workaround for an upstream Claude Code issue where subagent frontmatter `model:` values are silently ignored — the explicit dispatch parameter is honored where the frontmatter alone is not. The `model-echo` self-check at the start of every quest verifies the workaround is functioning.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, even the explicit dispatch parameter was overridden (environment variable, enterprise plan constraint, or deeper Claude Code issue). Investigate before trusting the cost posture for that quest.
