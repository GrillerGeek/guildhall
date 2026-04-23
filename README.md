# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.7.

Generic Claude Code + Opus 4.7 produces more assumption-driven code than 4.6 did — 4.7 follows instructions literally and fills in fewer gaps. The remedy is a tuned harness, not cleverer prompting.

The Guildhall provides the **`/quest` slash command** — inhabited by Mordain the Keeper, Guildmaster — that plans and dispatches, plus **six adventurer agents on Sonnet** that each do one narrow job. Feature work follows a strict TDD red-green-refactor handoff. Prototype work skips the ceremony. Debug work starts with root-cause before any fix. One of the six adventurers, the optional Playwright `ui-test-author`, drives a real browser for E2E UI tests.

## Quick start

```bash
# Install locally for development
cc --plugin-dir /Users/jasonrobey/Repos/guildhall/plugin
```

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
│   ├── agents/                  # 6 adventurer definitions
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
- **The `/quest` command has no `Write` / `Edit` access.** Forcing function: Mordain must dispatch an adventurer, can't drift into "let me just fix this."
- **Mordain absorbs the architect role.** No separate architect agent. The command-level session is already on Opus — design thinking lives there, not in a duplicate layer.
- **Hybrid handoff.** Durable artifacts (specs, tests, code, commits) in the repo. Ephemeral context between adventurers via the `Agent` tool's `prompt` field. Files only when there's a reader other than the immediately-next adventurer.

## Status

**Version 0.3.0** — full v0.3 roster is in place: 11 adventurers + 1 diagnostic. New since v0.2.x: security-reviewer (Oriana, Opus), architecture-reviewer (Aldric, Opus), docs-writer (Cassian, Sonnet), pr-author (Rook, Sonnet), plugin-validator (Tabs, Haiku). `/quest` now writes a durable `docs/guildhall/plans/<slug>.md` for every feature and debug quest, dispatches post-green reviews in parallel, and closes with Rook drafting a platform-agnostic PR title + body to stdout. Subagent model routing uses the explicit `model` dispatch parameter (workaround shipped in v0.2.7) — cost posture is operational. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the v0.3 design, and [`plugin/CHARACTERS.md`](plugin/CHARACTERS.md) for the full cast.

The Guildhall is a living system. Expect prompt iterations as real usage reveals friction. Changes to agents in `plugin/agents/` are the primary axis of iteration.

## License

MIT — see [LICENSE](LICENSE).
