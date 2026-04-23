# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.7.

## The guild

**Mordain the Keeper** — the Guildmaster — is embodied in the `/quest` command itself. He is not a dispatchable adventurer. When you issue a quest, Mordain is the one planning, picking mode, dispatching adventurers, and verifying their handoffs. He has no `Write` or `Edit` tools — a forcing function that keeps him from doing the adventurers' work.

The six adventurers:

| Adventurer | Agent | Role | Model |
|---|---|---|---|
| **Pip Quickfoot** | `prototype-builder` | Scout. Fast spikes, no tests, disposable code. | Sonnet |
| **Seraphine Dawnveil** | `test-author` | Oracle. Red tests from the Spec; never reads implementation. | Sonnet |
| **Bruga Ironseam** | `feature-implementer` | Smith. Green code from the blueprint. No scope creep. | Sonnet |
| **Tink Whiffletree** | `refactorer` | Enchanter. Narrow scoped refactors; preserves behavior. | Sonnet |
| **Kael the Tracker** | `debug-investigator` | Ranger. Finds root cause; does NOT fix. | Sonnet |
| **Vera Nightwhistle** *(optional)* | `ui-test-author` | Playwright. Drives Playwright E2E tests against the running app. | Sonnet |

Full character sheets in [`CHARACTERS.md`](CHARACTERS.md).

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

> **⚠️ Known issue (as of v0.2.5):** the `model-echo` diagnostic introduced in v0.2.4 confirmed that subagents declared `model: sonnet` in their frontmatter currently inherit the parent session's model instead. Every adventurer therefore runs on whatever model your Claude Code session is on — so expect Opus-level costs for quests issued from an Opus session. An upstream Claude Code issue has been filed; the cost posture below is the *intended* design and will become real once subagent model routing is honored. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the full context.

**Intended posture (aspirational):** the orchestrator runs on Opus for reasoning-heavy planning. Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, it is confirming the above — Sonnet frontmatter isn't being honored for this dispatch. The quest continues; cost is on you to monitor.
