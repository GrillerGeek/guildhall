# Quest Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every quest a glanceable progress record (milestones, tasks, declared loops, user waypoints) rendered as a journey + focus card in the Claude tavern pane, any terminal (`progress.py watch`) and a browser page (`progress.py watch --web`).

**Architecture:** One stdlib Python helper, `plugin/portable/scripts/progress.py` (copied into the skill bundle by `build_portable.py`), owns the JSON record beside the plan and renders it for terminal and web. Mordain seeds it from the plan and updates it with short commands on both hosts. The tavern mod reads the same JSON and draws it in Ink; it also detects `AskUserQuestion` for unplanned asks.

**Tech Stack:** Python 3.12 stdlib (`argparse`, `json`, `fcntl`, `http.server`), unittest; Claude Code mod API (TSX, `claude plugin test`).

**Spec:** `docs/superpowers/specs/2026-11-07-quest-progress-design.md`

## Global Constraints

- Python 3.12+, standard library only (matches `review.py`).
- Record path: `docs/guildhall/plans/<plan-slug>/progress.json`, derived from the plan path by dropping `.md`.
- States/colors: done = green, working = blue, repeating = violet, needs you = amber; plain language first; adventurer names only as a "who" tag.
- No ETAs. Elapsed time per milestone and per task only.
- Helper failure never blocks a quest; views are read-only spectators that fall through on any error.
- Mordain's added scope: only this record, only via `progress.py`. Enforcement for `Bash` stays prose-only.
- Docs fast lane writes no record. Debug skeleton: Plan → Reproduce → Root cause → Report. Prototype: Plan → Spike → Show.
- One release: bump `0.19.0 → 0.20.0` in all three plugin manifests; tavern `0.3.0 → 0.4.0`.
- Done count never decreases; skipped milestones are excluded from M.

## Review Focus

1. Missing, partial or corrupt `progress.json` → every view shows a calm "no progress record" line, never a traceback or a broken pane.
2. A command naming an unknown milestone/task/waypoint → refusal (exit 2, one-line message), record byte-identical.
3. Narrow terminal (≤ 40 columns) → journey and card truncate; box borders stay aligned.
4. Two commands at once (parallel reviewer fan-out bookkeeping) → file lock serializes; no lost update.
5. `--plan` outside `docs/guildhall/plans/` or not `.md` → refusal; nothing written anywhere.

---

### Task 1: Progress record + commands (`progress.py` core)

**Files:**
- Create: `plugin/portable/scripts/progress.py`
- Test: `tests/test_progress.py`

**Interfaces:**
- Produces (Python, importable by path):
  - `record_path(root: Path, plan: str) -> Path` — refuses (`Refusal`) when `plan` is not `docs/guildhall/plans/*.md` relative.
  - `init_record(title, plan, milestones: list[dict], waypoints: list[dict], repo='', branch='', host='', now=None) -> dict`
  - `apply(record: dict, op: str, args: dict, now: float) -> dict` — pure; ops below.
  - `load(path) -> dict` / `save(path, record)` (atomic, `fcntl` lock on `<path>.lock`).
  - `class Refusal(Exception)`.
- CLI: `progress.py --plan REL [--root ABS] OP ...` with ops
  `init --title T [--repo --branch --host] --skeleton-json FILE|-`,
  `start MILESTONE`, `done MILESTONE`, `skip MILESTONE --why W`,
  `add-milestone ID NAME --goal G --after ID --because B`,
  `task MILESTONE TASK_ID NAME [--who W] [--because B]`, `work TASK_ID [--who W]`, `finish-task TASK_ID`,
  `loop MILESTONE --why W`, `wait WAYPOINT_ID` | `wait --unplanned NEED`, `resume WAYPOINT_ID`,
  `note TEXT`, `close [--status completed|abandoned]`, `show [--width N] [--color]`, `watch [--web] [--port N] [--once]`.
  Exit 0 ok, 2 refusal (message on stderr), 4 I/O failure.
- Record (schema_version 1): `title, repo, branch, host, plan_path, status(active|completed|abandoned), note, started_at, updated_at, milestones[{id,name,goal,state(upcoming|current|done|skipped),loop:{reason,limit}|null,pass,started_at,finished_at,added_because,skipped_why}], tasks[{id,milestone,pass,name,state(upcoming|working|done),who,added_because,started_at,finished_at}], waypoints[{id,need,after,state(upcoming|waiting|done),planned,waiting_since,done_at}], loops[{milestone,pass,why,at,within_limit}]`.

- [ ] **Step 1: Write failing tests** — `test_record_path_refuses_outside_plans`, `test_init_seeds_milestones_and_waypoints`, `test_start_makes_single_current_and_done_never_decreases`, `test_loop_increments_pass_and_flags_over_limit` (limit 2: pass 2 within, pass 3 `within_limit` False), `test_tasks_scoped_to_current_pass`, `test_wait_and_resume_planned_and_unplanned`, `test_unknown_id_refuses_and_file_unchanged` (Review Focus 2), `test_concurrent_cli_updates_all_land` (10 parallel `task` subprocesses → 10 tasks; Focus 4), `test_cli_bad_plan_path_writes_nothing` (Focus 5).
- [ ] **Step 2:** `python3 -m unittest tests.test_progress -v` → FAIL (module missing).
- [ ] **Step 3:** Implement `progress.py` core and CLI.
- [ ] **Step 4:** Tests PASS.
- [ ] **Step 5:** Commit `feat(progress): quest progress record and helper`.

### Task 2: Terminal + web rendering, `watch`

**Files:**
- Modify: `plugin/portable/scripts/progress.py`
- Test: `tests/test_progress.py`

**Interfaces:**
- Produces: `journey(record) -> list[dict]` (nodes: `{kind: milestone|waypoint, label, state, badge}`), `render_text(record, width=60, color=False, now=None, frame=0) -> str`, `render_html(record, now=None) -> str` (full page with milestone timeline, full task list, "Where you come in"), `render_missing(width) -> str`.
- Terminal layout (top→bottom): title + "N of M"; repo · branch · day N; journey line (`●━━` done, `◉` current, `┈○` upcoming, `⚑` waypoint); labels; loop badges (`↻`, `↻2`); NOW card (header `NOW`, `NOW · PASS n OF <NAME>`, or `YOUR TURN`) with goal, `▰▱` bar + "k of n", task list (max 5 rows, then "○ n more"), loop why; footer "You're needed …" + "may repeat" note.
- `watch`: redraw every 1s on mtime change, alternate screen, Ctrl-C exits 0; missing record → `render_missing`. `--web`: `ThreadingHTTPServer` on 127.0.0.1 (default port 0 → prints URL); `/` page, `/fragment` body; page JS swaps fragment every 2s. `--once` prints one frame and exits (for tests).

- [ ] **Step 1: Failing tests** — `test_render_working_state_snapshot` (contains `NOW`, `3 of 7`, `⚑`), `test_render_loop_state_shows_pass_and_why`, `test_render_your_turn_takes_over_card`, `test_render_narrow_width_box_aligned` (every line ≤ 40 cols, all card lines same display width; Focus 3), `test_render_corrupt_record_is_calm` (Focus 1), `test_html_has_timeline_tasks_and_waypoints`, `test_watch_once_prints_frame`, `test_web_serves_page_and_fragment` (start server thread, GET both).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(progress): journey rendering for terminal and browser`.

### Task 3: Tavern pane journey view

**Files:**
- Create: `mods/guildhall-tavern/hooks/progress.ts`
- Modify: `mods/guildhall-tavern/hooks/register.tsx`, `mods/guildhall-tavern/types/index.d.ts`, `mods/guildhall-tavern/hooks/guildhall-tavern.test.ts`

**Interfaces:**
- Produces (`progress.ts`): `progressPath(planPath: string): string`, `parseProgress(text: string): QuestProgress | undefined` (shape-checks; undefined on anything wrong), `journeyNodes(p): JourneyNode[]`, `focus(p, asking?: Asking): Focus` (`{kind:'now'|'loop'|'you', title, subtitle, done, total, tasks, why?}`), `progressBand(p, asking?): string | undefined`, `planFromCommand(cmd: string): string | undefined` (parses `--plan X` from a `progress.py` Bash command).
- State atoms: `progress: QuestProgress | null`, `asking: { since: number; need: string } | null`.
- Refresh: after a main-agent plan `Write`; after a main-agent `Bash` whose command contains `progress.py` (path from `planFromCommand` or quest planPath); every 5s while a quest is set. Unplanned ask: main-agent `AskUserQuestion` sets `asking` before `next(e)` and clears after.
- Pane: journey section first (title, N of M, journey row, labels, loop badges, bordered card `borderStyle="round"` colored `suggestion` / `merged` / `warning`, "You're needed" line), then existing adventurer tree. Band: amber `⚑ waiting on you: …` wins over other band text.

- [ ] **Step 1: Failing tests** — `progress record draws the journey and card on every surface`, `a loop pass shows violet header and why`, `AskUserQuestion turns the card into YOUR TURN until answered`, `a corrupt record leaves the tavern as it was`, `planFromCommand finds the plan`.
- [ ] **Step 2:** `claude plugin test mods/guildhall-tavern` → FAIL. **Step 3:** implement. **Step 4:** PASS (all 19 existing too); `claude plugin validate mods/guildhall-tavern` clean.
- [ ] **Step 5:** Commit `feat(tavern): journey view of quest progress`.

### Task 4: Quest instructions, bundle, docs, version

**Files:**
- Modify: `plugin/commands/quest.md` (Step 3.10 seed, Step 4/5 update calls, AskUserQuestion wait rule, Step 6 close, Collaborative planning exception wording, Hard rules), `plugin/portable/references/quest.md`, `plugin/portable/references/collaborative-planning.md` and `plugin/portable/SKILL.md` source (exception wording), `plugin/hooks/quest_write_guard.py` docstring, `plugin/README.md`, `mods/guildhall-tavern/README.md`, `CLAUDE.md`, manifests (`0.20.0`), `mods/guildhall-tavern/.claude-plugin/plugin.json` (`0.4.0`), CHANGELOG if present.
- Regenerate: `python3 scripts/build_portable.py` → `plugin/skills/guildhall-quest/`.
- Test: `tests/test_progress.py::test_bundle_ships_helper` (bundle copy byte-identical to portable source), `test_quest_instructions_name_helper` (quest.md and portable quest.md mention `progress.py`, `wait`, skeletons).

- [ ] **Step 1:** failing instruction/bundle tests. **Step 2:** FAIL. **Step 3:** edit prose, rebuild bundle, bump versions. **Step 4:** `python3 scripts/validate_plugin.py && python3 scripts/validate_portable.py && python3 -m unittest discover -s tests` PASS.
- [ ] **Step 5:** Commit `feat(quest): seed and update progress records (v0.20.0)`.

### Task 5: Verification and PR

- [ ] Full CI-equivalent run; `claude plugin test mods/guildhall-tavern`.
- [ ] Dogfood: synthetic quest record driven through all three states via CLI; `show --color`, `watch --once`, `watch --web` fetched; screenshots of web page for the PR.
- [ ] Whole-branch review by a fresh reviewer; fix findings.
- [ ] Push branch, open PR with summary, test evidence, and Jason's pending live-surface review waypoint.
