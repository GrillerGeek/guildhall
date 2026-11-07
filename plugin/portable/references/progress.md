# Quest progress record

The user follows a quest through a progress record kept beside the plan at
`docs/guildhall/plans/<slug>/progress.json`. It is the quest's glanceable account:
milestones, tasks, declared loops and the points where the user is needed. The
tavern pane (Claude), `progress.py watch` (any terminal, including an AgentPanel or
tmux split) and `progress.py watch --web` (a local browser page) all draw it.
It holds plain-language names only. Source, diffs, hashes and evidence stay in the
plan.

## Write scope and failure

This is the single exception to Mordain's plan-only writes. Mordain may update the
quest's progress record only through `progress.py`. Never edit `progress.json` with
a file-writing tool, shell redirection or `apply_patch`. Never use the helper to
write anything else; it refuses paths outside `docs/guildhall/plans/`.

Progress bookkeeping never blocks a quest. If Python or the helper is unavailable,
or a command is refused, note `progress unavailable: <reason>` once in the plan and
continue. It never changes dispatch, reviewers, retry budgets, gates, IDD ownership
or a worker handoff. Never put progress details in a test-author brief.

## Call form

The helper ships in this skill at `scripts/progress.py`; resolve its absolute path
once from the installed skill directory. Python 3.12+, standard library only.

```bash
python3 <skill-dir>/scripts/progress.py --root <project-root> --plan docs/guildhall/plans/<slug>.md <op> ...
```

Exit 0 is applied, 2 is a refusal (one line on stderr, record unchanged), 4 is an
I/O failure.

## Seed it with the plan

Right after writing the plan, run `init` with a skeleton on stdin:

```bash
python3 <helper> --root <root> --plan <plan> init --title "<quest name>" \
  --repo <repo> --branch <branch> --host <claude|codex|...> --skeleton-json - <<'JSON'
{"milestones": [
  {"id": "plan", "name": "Plan", "goal": "Agree mode and scope"},
  {"id": "tests", "name": "Tests", "goal": "Write the failing tests"},
  {"id": "build", "name": "Build", "goal": "Make the new tests pass",
   "loop": {"reason": "the one implementer retry", "limit": 2}},
  {"id": "review", "name": "Review", "goal": "Independent reviews",
   "loop": {"reason": "blocking findings go back to Build", "limit": 2}},
  {"id": "pr", "name": "Draft PR", "goal": "Draft the pull request"}],
 "waypoints": [
  {"id": "scope", "need": "Approve mode and scope", "after": "plan"},
  {"id": "pr-review", "need": "Review the draft PR", "after": "pr"}]}
JSON
```

Milestone skeletons by mode:

- **Feature:** Plan → (Architecture) → Tests → Build → (Refactor) → Review →
  (UI walkthrough) → Draft PR. Review is always present. Include the gated
  milestones the plan anticipates; `skip` any that turn out unneeded.
- **Debug:** Plan → Reproduce → Root cause → Report. If a fix is requested, add
  the build milestones with `add-milestone`.
- **Prototype:** Plan → Spike → Show.
- **Docs fast lane:** no record.

Declare `loop` on every milestone that can repeat, with the limit taken from the
budget that already governs it (Build: one implementer retry, so 2 passes).
Declare a waypoint for every point you expect to need the user: mode/scope
approval, an architecture choice, a high-severity finding, PR approval, human or
live-client acceptance. `after` names the milestone it follows.

Ids are short lowercase words (`a-z`, `0-9`, `-`, `_`). Names are plain words of up
to about 12 characters; goals are one plain sentence. No adventurer flavor in
names: the `--who` tag carries the adventurer.

## Keep it current

One short call per event:

| When | Command |
| --- | --- |
| A milestone begins / ends | `start <milestone>` / `done <milestone>` |
| A gated milestone is not needed | `skip <milestone> --why "<reason>"` |
| Unplanned milestone needed | `add-milestone <id> "<Name>" --goal "<goal>" --after <id> --because "<trigger>"` |
| Each unit of work (a dispatch, a reviewer, a fix) | `task <milestone> <id> "<name>" [--who <Adventurer>] [--because "<trigger>"]` |
| It starts / is verified | `work <id>` / `finish-task <id>` |
| Work goes back (failed gate, blocking review) | `loop <milestone> --why "<one sentence>"` |
| Immediately before asking or stopping for the user | `wait <waypoint>`, or `wait --unplanned "<question>"` |
| The user has answered | `resume <waypoint-id>` |
| A one-line status is useful | `note "<what is happening>"` |
| Quest close | `close --status completed` or `--status abandoned` |

A `loop` past the declared limit is recorded as beyond plan; the record never
lowers the done count. Unplanned `wait` waypoints get ids `ask-1`, `ask-2`, ….

## Tell the user how to watch

At plan time, tell the user once how to follow along: the tavern pane in Claude
Code, `python3 <helper> --root <root> watch` in a terminal split next to the
session, or `python3 <helper> --root <root> watch --web` for a browser page (local
only, 127.0.0.1). `watch` without `--plan` follows the newest active quest.
