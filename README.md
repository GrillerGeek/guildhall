# Guildhall

*A gathering place for adventurers.*

[![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FGrillerGeek%2Fguildhall%2Fmain%2Fplugin%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&prefix=v&color=blue)](plugin/.claude-plugin/plugin.json)
[![validate](https://github.com/GrillerGeek/guildhall/actions/workflows/validate.yml/badge.svg)](https://github.com/GrillerGeek/guildhall/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-blueviolet.svg)](https://claude.com/claude-code)
[![marketplace](https://img.shields.io/badge/marketplace-grillergeek--plugins-green.svg)](https://github.com/GrillerGeek/skills)

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.8.

Opus-tier models from 4.7 onward follow instructions literally and fill in fewer gaps than their predecessors — and Opus 4.8 is additionally conservative about reaching for subagents unless told exactly when to dispatch them. The remedy is the same as it ever was: a tuned harness with explicit contracts and dispatch triggers, not cleverer prompting.

Mordain (the `/quest` orchestrator) runs on whatever model your session is on. Opus 4.8 is the tuned default; for the hardest quests, **run `/quest` from a Claude Fable 5 session** — orchestration is the one seat where top-tier reasoning pays for itself, and the adventurers stay on their own cheaper tiers regardless (`fable` is never used for adventurer dispatch).

The Guildhall provides the **`/quest` slash command** — inhabited by Mordain the Keeper, Guildmaster — that plans, writes a durable plan file, and dispatches, plus **eighteen adventurer agents tiered across Opus / Sonnet / Haiku** that each do one narrow job. Feature work follows a strict TDD red-green-refactor handoff for the build, then fans out post-green reviews (security, docs, optional Playwright UI tests) in parallel, and closes with a platform-agnostic PR draft. Prototype work skips the ceremony. Debug work starts with root-cause before any fix.

## How Guildhall fits the AI coding workflow

If you've watched how people build software with AI lately, you've probably seen the arc that's emerging as a shared best practice — Matt Pocock frames it as [seven labeled stages](https://github.com/mattpocock/skills), each backed by a Skill: **Grill → Research → Prototype → PRD/Plan → Issues/Tasks → Implement → Review**. It's a good summary of what the coding world is converging on: get clear, get grounded, decide the destination, break it down, *then* act, then check.

Guildhall doesn't replace that arc — it covers the back half of it with enforced discipline, and pairs with its sibling plugin [IDD-framework](https://github.com/grillergeek/idd-framework), which owns the front half:

| # | Stage | The question it answers | Where it lives |
|---|---|---|---|
| 1 | **Grill** | How do I brief the AI well? | **IDD-framework** — `/interview` has the AI interview *you* into a Product artifact |
| 2 | **Research** *(opt)* | How do I stay grounded in current facts? | Your own sources / either plugin; not a formal Guildhall stage |
| 3 | **Prototype** *(opt)* | How do I test an idea before I commit? | **Guildhall** — prototype mode (Pip): fast spikes, no tests, disposable code |
| 4 | **PRD/Plan** | How do we end up at the right place? | **IDD** Intentions → Spec; **Guildhall** Mordain writes the durable plan file (+ optional architecture review) |
| 5 | **Issues/Tasks** | How do I break a big job into pieces? | **IDD** Expectations decomposition; **Guildhall** Mordain sequences the dispatch |
| 6 | **Implement** | When do I let the AI actually run? | **Guildhall** feature mode — enforced TDD: test-author → feature-implementer → refactorer |
| 7 | **Review** | How do I know it got it right? | **Guildhall** post-green fan-out — eight role-separated reviewers (+ IDD's review gate) |

**What's different.** Pocock's seven stages are *skills you invoke in order* — the discipline lives in remembering to run the next one. Guildhall takes the two stages that are hardest to get right — **Implement** and **Review** — and turns them from single skills into a **guild of narrow specialists with independence guardrails**. "Let the AI run" becomes a disciplined red → green → refactor handoff in which the test author *never sees the implementation*. "Review" stops being one QA pass and becomes eight reviewers (security, docs, observability, reliability, performance, ops-readiness, migration-safety, accessibility) that fire only when the diff matches their trigger. The arc is the same; the discipline is enforced by *who is allowed to do what*, not by remembering to invoke the next skill.

## Installation

### From the marketplace (recommended)

Guildhall is distributed through the [grillergeek-plugins marketplace](https://github.com/GrillerGeek/skills). Run these once inside any Claude Code session:

```
/plugin marketplace add GrillerGeek/skills
/plugin install guildhall@grillergeek-plugins
```

No local clone required.

### From a local clone

If you've cloned the repo yourself:

```bash
# Replace <path-to-repo> with the directory where you cloned guildhall
claude --plugin-dir <path-to-repo>/plugin
```

### Keeping up to date

Plugin updates are picked up automatically when Claude Code is restarted. If you installed via `--plugin-dir`, pull the latest changes and restart:

```bash
cd <path-to-repo>
git pull
```

If you installed from the marketplace, Claude Code manages the copy for you — restart Claude Code to pick up the latest version.

## Quick start

Once installed, issue a quest from any Claude Code session:

```
/quest Build a Python CLI that polls Recreation.gov availability for a campground ID.
```

See [`plugin/README.md`](plugin/README.md) for the full usage reference.

## Repository layout

```
guildhall/
├── plugin/                      # What gets installed
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/                  # 19 adventurer/diagnostic definitions
│   ├── commands/
│   │   └── quest.md             # /quest slash command (Mordain lives here)
│   ├── CHARACTERS.md            # Full character sheets for the cast
│   └── README.md                # User-facing docs
├── scripts/
│   └── validate_plugin.py       # Mechanical validator (plugin-validator's checks) run by CI
├── .github/
│   └── workflows/
│       └── validate.yml         # Runs the validator on every push / PR
├── README.md                    # This file
├── LICENSE
└── .gitignore
```

## Design decisions

- **Orchestration lives in the `/quest` command, not in a subagent.** Claude Code doesn't surface the `Agent` dispatch tool inside a subagent's tool context, so an "orchestrator agent that dispatches worker agents" can't actually dispatch. `/quest` runs at the top level where dispatch works. Mordain is the guildmaster inside the command.
- **Sequential adventurer dispatch.** TDD order is enforced. `test-author` fires before `feature-implementer`; parallel dispatch would break independence.
- **The `/quest` command has scoped `Write` access — plan files only.** Mordain can write the durable plan at `docs/guildhall/plans/*.md`. He cannot write anything else; that forcing function keeps him from doing the adventurers' code-writing work.
- **Mordain absorbs the architect role.** No separate architect agent. The command-level session is already on Opus — design thinking lives there, not in a duplicate layer.
- **Hybrid handoff.** Durable artifacts (specs, tests, code, commits) in the repo. Ephemeral context between adventurers via the `Agent` tool's `prompt` field. Files only when there's a reader other than the immediately-next adventurer.

## Status

**Version 0.7.0.** The harness is tuned for **Opus 4.8** and aware of **Claude Fable 5** as the recommended seat for orchestrating the hardest quests. The roster is **18 adventurers + 1 diagnostic** (model-echo), tiered across Opus / Sonnet / Haiku. A feature quest runs Mordain through a three-phase dispatch: a sequential TDD build chain (optional architecture review → test-author → feature-implementer → optional refactor), a parallel post-green fan-out (two always-on reviewers — security, docs — plus six gated production-readiness reviewers and optional Playwright UI tests), and a sequential PR draft to close. Gated reviewers fire only when the diff matches their trigger; the bias on ambiguous triggers is **fire**, and Mordain records each gating decision in the plan file's `## Reviewers selected` section.

**Version history since v0.4.0:**

- **v0.5.0** — re-baselined the harness premise from Opus 4.7 to **Opus 4.8**.
- **v0.6.0** — **Fable 5-aware Mordain**: parent-model attribution recorded in each plan file's `parent_model` frontmatter, plus orchestration tuning for a top-tier parent session.
- **v0.6.1** — **roster-table tier resolution**: Mordain resolves adventurer tiers from the roster table inside `quest.md` (a validator-enforced mirror of the canonical agent frontmatter) instead of reading every agent file per quest; model-echo's output contract hardened.
- **v0.6.2** — `/quest` dispatches use **plugin-namespaced agent types** (`guildhall:<agent>`) for reliable resolution.
- **v0.6.3** — feature-implementer marks deliberate shortcuts with `minimal:` comments so reviewers and the PR author can see them.
- **v0.6.4** — corrected install docs (marketplace-based install, `claude --plugin-dir`); **discriminating model-echo self-check** (dispatched on `haiku`, deliberately ≠ its `sonnet` frontmatter, so param-honored and frontmatter-honored routing are distinguishable); **CI validation** (`scripts/validate_plugin.py` implements plugin-validator's checks on every PR); `quest.md` consistency fixes (pre-plan dispatch exceptions, IDD-framework dispatch guidance, step-number corrections).
- **v0.6.5** — lessons ledger, project-verify gate, quantitative goals, loop docs.
- **v0.7.0** — fog-of-war: Not-yet-specified/Out-of-scope plan sections, fog triage lane, fog-cartographer (Wren) write-back to IDD Explorations.

Earlier milestones: **v0.4.0** added the six gated production-readiness reviewers (observability, reliability, performance, ops-readiness, migration-safety, accessibility); **v0.3.x** added the security/architecture/docs/pr/validator roster, durable plan files, the parallel review fan-out, and the explicit-`model`-param routing workaround. See `docs/superpowers/specs/` for the v0.3 and model-refresh design docs, and [`plugin/CHARACTERS.md`](plugin/CHARACTERS.md) for the full cast.

The Guildhall is a living system. Expect prompt iterations as real usage reveals friction. Changes to agents in `plugin/agents/` are the primary axis of iteration.

## License

MIT — see [LICENSE](LICENSE).
