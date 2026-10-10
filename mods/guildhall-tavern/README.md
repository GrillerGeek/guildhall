# guildhall-tavern

A Claude Code mod that draws the Guildhall tavern as a live pane while a `/quest`
runs: Mordain at the top, every adventurer he summons grouped by phase
(Build chain, Review fan-out, Closer, Field work, Hirelings), each with an
icon, a spinner while at work, the model the spawn resolved to, elapsed
time, a deed count, and one in-character line for what they are doing right
now ("Bruga forges rate_limit.ts", "Oriana searches for unwatched gates:
password"). A short chronicle under the tree records summons and returns.

It is a spectator. It reads `agent.spawn`, `tool.call`, `turn.complete` and
`command.run`, never changes them, and every hook falls through to the
engine if its own bookkeeping fails. It does not touch the `guildhall`
plugin, its agents or `/quest`.

## Install

From the [GrillerGeek plugin marketplace](https://github.com/GrillerGeek/skills),
alongside Guildhall:

```bash
claude plugin marketplace add https://github.com/GrillerGeek/skills.git
claude plugin install guildhall-tavern@grillergeek-plugins
```

Or in a Claude Code session: `/plugin install guildhall-tavern --marketplace GrillerGeek/skills`.

Already have the marketplace from installing Guildhall? A copy added before the
tavern was listed does not show it until refreshed:

```bash
claude plugin marketplace update grillergeek-plugins
```

It is a function-hook mod, written and tested against Claude Code 2.1.295.
For local development, load the folder directly:

```bash
claude --plugin-dir <repo>/plugin --plugin-dir <repo>/mods/guildhall-tavern
```

The pane opens itself when a `/quest` starts, or when a guild agent is
dispatched outside one. `/guildhall-tavern` opens it any time.

The pane needs a surface that draws mod UI: the Claude Code terminal (a pane
you did not ask for waits for 144 columns; asked for, it opens at any width)
or a local session in the desktop app. A cloud session viewed from the
Claude app attaches no such surface, so there `/guildhall-tavern` prints the
tavern as text instead; run it again for a fresh look.

## Where things live

- `hooks/roster.ts`: one entry per agent in `plugin/agents/`, voiced from
  `plugin/CHARACTERS.md`. A new adventurer needs a row here or it shows as a
  hireling; `tests/test_tavern_roster.py` fails CI until it has one, and when
  a roster name drifts from its character sheet.
- `hooks/register.tsx`: the hooks and the pane.
- `types/index.d.ts`: the session state the pane draws from.

## Check it

```bash
claude plugin validate mods/guildhall-tavern
claude plugin test mods/guildhall-tavern
```
