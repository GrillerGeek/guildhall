# Guildhall

*A gathering place for adventurers.*

A TDD-ordered coding agent harness for Claude Code, tuned for Opus 4.7.

Generic Claude Code + Opus 4.7 produces more assumption-driven code than 4.6 did — 4.7 follows instructions literally and fills in fewer gaps. The remedy is a tuned harness, not cleverer prompting.

The Guildhall provides **one orchestrator on Opus** that plans and dispatches, plus **six adventurers on Sonnet** that each do one narrow job. Feature work follows a strict TDD red-green-refactor handoff. Prototype work skips the ceremony. Debug work starts with root-cause before any fix. An optional seventh agent drives Playwright for E2E UI tests.

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
│   ├── agents/                  # 7 adventurer definitions
│   ├── commands/
│   │   └── quest.md             # /quest slash command
│   └── README.md                # User-facing docs
├── README.md                    # This file
├── LICENSE
└── .gitignore
```

## Design decisions

- **Sequential worker dispatch.** TDD order is enforced. test-author fires before feature-implementer; parallel dispatch would break independence.
- **Orchestrator has no `Write` access.** Forcing function: it must dispatch a worker, can't drift into "let me just fix this."
- **Orchestrator absorbs the architect role.** No separate architect agent. The orchestrator is already on Opus — design thinking lives there, not in a duplicate layer.
- **Hybrid handoff.** Durable artifacts (specs, tests, code, commits) in the repo. Ephemeral context between agents via Claude Code's subagent chaining. Files only when there's a reader other than the immediately-next agent.

## Status

**Version 0.1.0** — Initial release. Not yet dogfooded end-to-end.

The Guildhall is a living system. Expect prompt iterations as real usage reveals friction. Changes to agents in `plugin/agents/` are the primary axis of iteration.

## License

MIT — see [LICENSE](LICENSE).
