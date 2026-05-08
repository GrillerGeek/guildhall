# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.7.

Generic Claude Code + Opus 4.7 produces more assumption-driven code than 4.6 did — 4.7 follows instructions literally and fills in fewer gaps. The remedy is a tuned harness, not cleverer prompting.

The Guildhall provides the **`/quest` slash command** — inhabited by Mordain the Keeper, Guildmaster — that plans, writes a durable plan file, and dispatches, plus **eleven adventurer agents tiered across Opus / Sonnet / Haiku** that each do one narrow job. Feature work follows a strict TDD red-green-refactor handoff for the build, then fans out post-green reviews (security, docs, optional Playwright UI tests) in parallel, and closes with a platform-agnostic PR draft. Prototype work skips the ceremony. Debug work starts with root-cause before any fix.

## Installation

### From GitHub (recommended)

Claude Code can install plugins directly from a GitHub URL. Run this once inside any Claude Code session:

```
/install-github-app https://github.com/GrillerGeek/guildhall
```

Claude Code will clone the repository and register the plugin automatically. No local clone required.

### From a local clone

If you've cloned the repo yourself:

```bash
# Replace <path-to-repo> with the directory where you cloned guildhall
cc --plugin-dir <path-to-repo>/plugin
```

### Keeping up to date

Plugin updates are picked up automatically when Claude Code is restarted. If you installed via `--plugin-dir`, pull the latest changes and restart:

```bash
cd <path-to-repo>
git pull
```

If you installed via GitHub URL, Claude Code manages the copy for you — restart Claude Code to pick up the latest version.

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
│   ├── agents/                  # 12 adventurer/diagnostic definitions
│   ├── commands/
│   │   └── quest.md             # /quest slash command (Mordain lives here)
│   ├── CHARACTERS.md            # Full character sheets for the cast
│   └── README.md                # User-facing docs
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

**Version 0.4.0** — production-readiness coverage. The roster grows to 17 adventurers + 1 diagnostic with six new gated post-green reviewers: observability-reviewer (Vance, Sonnet), reliability-reviewer (Thalia, Opus), performance-reviewer (Cassia, Sonnet), ops-readiness-reviewer (Garran, Sonnet), migration-safety-reviewer (Ysolde, Opus), accessibility-reviewer (Lior, Sonnet). Two reviewers remain always-on (security, docs); the six new ones fire only when their trigger applies (network I/O, DB / hot paths, user-visible deploys, schema changes, UI work, etc.). The bias on ambiguous triggers is fire — a missed reviewer is more expensive than an unnecessary one. Mordain records the gating decision (which reviewers fired, which were skipped, and why) in the plan file's `## Reviewers selected` section. Rook now folds Garran's runbook output verbatim into the PR body when `ops-readiness-reviewer` was dispatched.

**Version 0.3.2** — documentation improvements (installation guide, updated agent count, corrected design notes). Full v0.3 roster: 11 adventurers + 1 diagnostic. New since v0.2.x: security-reviewer (Oriana, Opus), architecture-reviewer (Aldric, Opus), docs-writer (Cassian, Sonnet), pr-author (Rook, Sonnet), plugin-validator (Tabs, Haiku). `/quest` writes a durable `docs/guildhall/plans/<slug>.md` for every feature and debug quest, dispatches post-green reviews in parallel, and closes with Rook drafting a platform-agnostic PR title + body to stdout. Subagent model routing uses the explicit `model` dispatch parameter (workaround shipped in v0.2.7) — cost posture is operational. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the v0.3 design, and [`plugin/CHARACTERS.md`](plugin/CHARACTERS.md) for the full cast.

The Guildhall is a living system. Expect prompt iterations as real usage reveals friction. Changes to agents in `plugin/agents/` are the primary axis of iteration.

## License

MIT — see [LICENSE](LICENSE).
