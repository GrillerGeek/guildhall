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

## Run it

Function-hook mods need Claude Code 2.1.295 or newer.

```bash
claude --plugin-dir <repo>/plugin --plugin-dir <repo>/mods/guildhall-tavern
```

Or name the folder in `CLAUDE_CODE_PLUGIN_DIRS` (in the environment or the
`env` block of `~/.claude/settings.json`) where no flag can be given, as in
a desktop-app session.

The pane opens itself when a `/quest` starts, or when a guild agent is
dispatched outside one. `/guildhall-tavern` opens it any time.

## Where things live

- `hooks/roster.ts`: one entry per agent in `plugin/agents/`, voiced from
  `plugin/CHARACTERS.md`. A new adventurer needs a row here or it shows as a
  hireling.
- `hooks/register.tsx`: the hooks and the pane.
- `types/index.d.ts`: the session state the pane draws from.

## Check it

```bash
claude plugin validate mods/guildhall-tavern
claude plugin test mods/guildhall-tavern
```
