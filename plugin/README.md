# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, with a portable skill for
Claude and Codex. Mordain uses the model configured for the parent session.

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

These Model entries mirror native Claude frontmatter defaults. Explicit user
choices and qualified optional routing can override dispatch settings.

Plus one diagnostic: **`model-echo`** — requested on a model different from its
frontmatter to collect an unverified hint. Its self-report cannot establish
which model executed or which routing mechanism took precedence. Trusted host
metadata is required; otherwise observed identity stays `unknown`.

Full character sheets in [`CHARACTERS.md`](CHARACTERS.md).

## Installation

Version **0.10.1 includes the installed routing tools**. The [installation guide](https://github.com/GrillerGeek/guildhall/blob/main/docs/installation.md)
covers this repository's Codex, Claude and standalone routes, updates and removal.
The `main` route receives 0.10.1 after merge; the separate marketplace below is
not updated by this change.

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

For a feature quest, Mordain runs: **model-echo diagnostic → (optional Aldric) → Seraphine → Bruga → (optional Tink) → parallel fan-out (Oriana + Cassian always; Vance / Thalia / Cassia / Garran / Ysolde / Vera / Lior gated by trigger) → Rook** — with a committed `plan.md` opening the quest and a PR draft closing it. The plan file's `## Reviewers selected` section records which gated reviewers fired and why.

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

Guildhall is the implementation-side complement to the [IDD-framework](https://github.com/grillergeek/idd-framework) plugin. IDD handles specs (Intentions → Expectations → Spec → review); Guildhall handles code (plan → test → implement → refactor) from those specs. For how the two map onto the broader seven-stage AI coding workflow (Grill → Research → Prototype → PRD/Plan → Issues/Tasks → Implement → Review), see [How Guildhall fits the AI coding workflow](https://github.com/GrillerGeek/guildhall/blob/main/README.md#how-guildhall-fits-the-ai-coding-workflow).

## Cost posture

The orchestrator inherits the parent session model. The roster supplies native
worker defaults; Fable remains forbidden for Claude adventurers. Assess model
changes by completed-task quality, retries and measured usage, not token price
alone. Plan records retain evidence, but requested settings and model self-reports
do not establish execution identity or billing. Missing usage/cost stays unknown;
subscription usage cannot be converted into an assumed API bill.

**How routing works:** valid per-dispatch user selection precedes a role override,
then activated routing, then the eligible roster/frontmatter baseline. Native
Claude always receives the resolved literal model argument, including a full ID
when actually supported. Frontmatter aliases remain defaults. Host settings may
override or substitute the request; record trusted observed settings separately
or `unknown`. Earlier model-echo observations were diagnostic history, not proof
of precedence or cost.

## Optional Jev-assisted routing

The single bundled helper serves native Claude and portable Claude/Codex.
`off` is the default and skips the helper; `shadow` records recommendations while
preserving baseline dispatch; `adaptive` can apply reviewed qualifications only
for `docs-writer` and `pr-author`. Shadow does not require qualified profiles.
No live-qualified profiles ship, and no cost or quality improvement is claimed.

Use [the setup and operations guide](skills/guildhall-quest/references/model-routing.md) before a quest.
Enabled routing needs Python 3.12+ and explicit policy activation; external calls
read `TYPESAFE_API_KEY` from the host process environment. An API key alone enables
nothing. Ordinary Guildhall needs neither Jev nor IDD. The
[shared contract](skills/guildhall-quest/references/routing.md) defines data,
qualification, fallback, receipts and serial per-quest state. The helper cannot
change reviewers, permissions, lifecycle gates or retry budgets.

## Portable quest candidate

Version 0.10.1 ships `skills/guildhall-quest/SKILL.md` for capable
non-Claude hosts. It bundles its role references and uses host-native independent
workers. The Claude command/agent/hook route documented above is preserved;
standalone installation does not register those native Claude components.
