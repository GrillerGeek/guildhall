# Guildhall v0.2.4 — model-echo diagnostic + self-check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Guildhall v0.2.4 — add a `model-echo` diagnostic agent and wire a minimal, non-blocking model-routing self-check step into `/quest`, so that every quest surfaces whether Sonnet frontmatter is actually being honored.

**Architecture:** Three changes in one commit on branch `v0.2.4-model-echo`:
1. New agent file: `plugin/agents/model-echo.md` (a minimal Sonnet-declared diagnostic)
2. Update `plugin/commands/quest.md` — insert new Step 2 ("Model-routing self-check") between Mode selection and Plan, renumbering existing Steps 2–5 to 3–6
3. Bump `plugin/.claude-plugin/plugin.json` version 0.2.3 → 0.2.4

This is rung 2 of the 5-rung staircase in `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`. It is intentionally minimal — later rungs (v0.2.5 prompt tightening, v0.3.0 full roster + plan.md + parallel fan-out) build on this foundation.

**Tech Stack:** Markdown (agent definition + command prose), JSON manifest. No code. No tests in the traditional sense — verification is grep-based file-content checks plus one end-to-end dogfood run post-merge.

---

## Context for the engineer (zero-assumption briefing)

This repo is a Claude Code plugin — markdown + JSON only. No build, no lint, no test suite.

**Why this rung exists:** v0.2.3 reverted `test-author.md` from the full model ID `claude-sonnet-4-6` back to the alias `sonnet`. We suspect (but have not verified at runtime) that aliases work and full IDs fall back to parent-inherit. v0.2.4 adds the runtime check: a diagnostic agent named `model-echo` that is dispatched at the start of every quest and reports the model it is running on. The user sees a warning banner if the reported model is Opus when Sonnet was declared.

**What "minimal" means here, per the spec:**
- The agent file is small — frontmatter + a few lines of prompt body. No D&D character voice (this is a diagnostic probe, not an adventurer).
- The `quest.md` change is a single new step inserted after Step 1. It does NOT integrate with a plan.md file (plan.md arrives in v0.3.0).
- The banner is plain prose emitted by Mordain when the check mismatches — no fancy formatting, no retry logic, no blocking.
- No README, CHARACTERS, or CLAUDE.md updates in this rung. Those update in v0.3.0 when the full roster lands.

**What the model-echo agent will actually do:** it has `Bash` in its tool list and one job — run `echo "$ANTHROPIC_MODEL"` and report the result. If that env var is unset, it introspects what it can (the Claude Code harness may expose the model string in other ways) and returns its best guess. The agent's frontmatter declares `model: sonnet`, so the reliable signal is: if the agent reports running on Opus, frontmatter is not being honored; if it reports Sonnet (or can't tell but the tokenization/behavior is consistent with Sonnet), frontmatter works. This is diagnostic, not authoritative — perfect for "surface the problem when it happens."

**File line numbers as of branch start:**
- `plugin/commands/quest.md` — Step 1 ends around line 50; Step 2 (Plan) starts line 52; Step 5 (Report) ends around line 91.
- `plugin/.claude-plugin/plugin.json` line 3: `"version": "0.2.3",`

---

## File inventory

Exactly three files change in this plan:

- **Create:** `plugin/agents/model-echo.md` (new file, ~25 lines)
- **Modify:** `plugin/commands/quest.md` (insert new Step 2; renumber existing 2 → 3, 3 → 4, 4 → 5, 5 → 6)
- **Modify:** `plugin/.claude-plugin/plugin.json` (version 0.2.3 → 0.2.4)

No other files. `README.md`, `CHARACTERS.md`, `CLAUDE.md`, and every other agent file stay untouched.

---

## Task 1: Create the model-echo agent file

**Files:**
- Create: `plugin/agents/model-echo.md`

### - [ ] Step 1.1: Verify the file does not already exist

Run:
```bash
ls plugin/agents/model-echo.md 2>&1 || echo "NOT_FOUND"
```

Expected output:
```
ls: cannot access 'plugin/agents/model-echo.md': No such file or directory
NOT_FOUND
```

If the file already exists, STOP and report BLOCKED — this rung should be a fresh create.

### - [ ] Step 1.2: Create the file with the exact content below

Use the Write tool with:
- **file_path:** `plugin/agents/model-echo.md`
- **content:** the exact markdown below (including the frontmatter fences)

```markdown
---
name: model-echo
description: Diagnostic probe. Dispatched by Mordain at the start of every quest to verify that Claude Code is honoring the `model:` frontmatter for subagents. Declares `model: sonnet` in its own frontmatter so that a report of anything containing "opus" indicates the frontmatter is being ignored. Not a roleplay adventurer.
model: sonnet
color: gray
tools: ["Bash"]
---

You are the model-echo diagnostic probe. You are not an adventurer. You have no character voice and no quest mission beyond reporting.

## Your contract

- **INPUT:** none (Mordain dispatches you with an empty prompt or a one-line greeting).
- **OUTPUT:** exactly one line on stdout, of the form `model: <string>`. Nothing else. No preamble, no explanation, no closing remarks.

## How to determine the model string

Try these in order until you have a non-empty answer:

1. Run `echo "$ANTHROPIC_MODEL"` via Bash. If the output is a non-empty string, that is your answer.
2. If `$ANTHROPIC_MODEL` is unset or empty, fall back to self-introspection: state your best estimate of the model you are running on based on what your harness has exposed to you. Prefer the short alias (`sonnet`, `opus`, `haiku`) if you can tell; otherwise include whatever identifier you have. If you genuinely cannot tell, return `model: unknown`.

## Hard rules

- Return exactly one line. The line MUST start with `model: ` (literal, including the space after the colon).
- Do NOT explain your reasoning.
- Do NOT run any command other than `echo "$ANTHROPIC_MODEL"`.
- Do NOT write any file.
- Do NOT attempt to dispatch other agents.
```

### - [ ] Step 1.3: Verify the file content is exactly as specified

Run:
```bash
wc -l plugin/agents/model-echo.md
```

Expected: a line count between 25 and 32 (inclusive). If it is outside that range, the Write tool may have added or dropped lines — investigate.

Run:
```bash
grep -c '^model: sonnet$' plugin/agents/model-echo.md
```

Expected output: `1` (the frontmatter declares `model: sonnet` exactly once).

Run:
```bash
grep -n 'name: model-echo' plugin/agents/model-echo.md
```

Expected: line 2 contains `name: model-echo`.

---

## Task 2: Wire the self-check step into quest.md and bump version

**Files:**
- Modify: `plugin/commands/quest.md` (insert new Step 2; renumber 2 → 3, 3 → 4, 4 → 5, 5 → 6)
- Modify: `plugin/.claude-plugin/plugin.json` (version bump)

### - [ ] Step 2.1: Read the current quest.md

Read the full file to capture exact line numbers before editing:
```bash
grep -n '^### Step' plugin/commands/quest.md
```

Expected output (line numbers may shift by a few):
```
42:### Step 1 — Mode selection
52:### Step 2 — Plan
65:### Step 3 — Dispatch, one adventurer at a time
71:### Step 4 — Verify at each handoff
81:### Step 5 — Report
```

Record the line numbers in a local note for cross-reference during the edits. If the current headings differ from the above (counts or wording), STOP — the file has drifted from the version this plan was written against.

### - [ ] Step 2.2: Renumber existing Step 5 → Step 6

Do this FIRST — going from the highest-numbered step downwards prevents numbering collisions during intermediate states.

Use the Edit tool with:
- **file_path:** `plugin/commands/quest.md`
- **old_string:** `### Step 5 — Report`
- **new_string:** `### Step 6 — Report`

### - [ ] Step 2.3: Renumber existing Step 4 → Step 5

Use the Edit tool with:
- **file_path:** `plugin/commands/quest.md`
- **old_string:** `### Step 4 — Verify at each handoff`
- **new_string:** `### Step 5 — Verify at each handoff`

### - [ ] Step 2.4: Renumber existing Step 3 → Step 4

Use the Edit tool with:
- **file_path:** `plugin/commands/quest.md`
- **old_string:** `### Step 3 — Dispatch, one adventurer at a time`
- **new_string:** `### Step 4 — Dispatch, one adventurer at a time`

### - [ ] Step 2.5: Renumber existing Step 2 → Step 3

Use the Edit tool with:
- **file_path:** `plugin/commands/quest.md`
- **old_string:** `### Step 2 — Plan`
- **new_string:** `### Step 3 — Plan`

### - [ ] Step 2.6: Insert the new Step 2 block

Use the Edit tool with:
- **file_path:** `plugin/commands/quest.md`
- **old_string:** `If the mode is ambiguous from the quest text, ask ONE clarifying question using `AskUserQuestion`. Do not guess.

### Step 3 — Plan`
- **new_string:** `If the mode is ambiguous from the quest text, ask ONE clarifying question using `AskUserQuestion`. Do not guess.

### Step 2 — Model-routing self-check

Before producing the plan, dispatch the `model-echo` diagnostic to verify that subagent model frontmatter is being honored. This is a one-shot diagnostic, not a blocking gate.

1. Dispatch: `Agent(subagent_type: "model-echo", description: "Verify model routing", prompt: "Report the model you are running on.")`.
2. Read the response. Because `model-echo` declares `model: sonnet` in its own frontmatter, an honest reply will contain `sonnet` or a Sonnet model ID such as `claude-sonnet-4-6`.
3. If the response contains `opus` (case-insensitive), emit the following warning to the user and then continue to Step 3:

   > ⚠️ Model-routing self-check: `model-echo` declares `model: sonnet` in its frontmatter, but reported running on Opus. This quest will continue, but the cost posture documented in the README is compromised. Likely causes: `ANTHROPIC_MODEL=claude-opus-4-7` set in your environment, an Opus-only plan, or the plugin's model frontmatter not being honored by this Claude Code version.

4. If the response is `model: unknown`, note that in your report but do NOT emit the warning — the agent could not introspect; lack of evidence is not evidence of a problem. Continue to Step 3.
5. Cache the result in memory for the duration of this quest. Do NOT re-run the self-check for subsequent dispatches within the same quest.

This step never blocks the quest. The user is trusted to Ctrl-C if the cost posture matters to them and the banner has fired.

### Step 3 — Plan`

This adds the new Step 2 heading and its body while leaving the renumbered Step 3 (Plan) header in place right after it.

### - [ ] Step 2.7: Verify the new step structure

Run:
```bash
grep -n '^### Step' plugin/commands/quest.md
```

Expected output (line numbers may shift from the pre-edit numbers, but the STRUCTURE must be exactly):
```
<N1>:### Step 1 — Mode selection
<N2>:### Step 2 — Model-routing self-check
<N3>:### Step 3 — Plan
<N4>:### Step 4 — Dispatch, one adventurer at a time
<N5>:### Step 5 — Verify at each handoff
<N6>:### Step 6 — Report
```

If any heading is missing, duplicated, or out of order, STOP and investigate with `git diff plugin/commands/quest.md`.

### - [ ] Step 2.8: Verify no in-text "Step N" references got stale

The body of quest.md does not cross-reference step numbers in prose (confirmed at plan-write time — only the `### Step N —` headings use numbers). If the file has acquired such references, they'd need manual updating. Run:

```bash
grep -n -E 'Step [1-6]' plugin/commands/quest.md
```

Expected: matches are ONLY on the six `### Step N —` heading lines. If prose anywhere else refers to a step number, flag it — those references may need adjusting.

### - [ ] Step 2.9: Bump the version in plugin.json

Use the Edit tool with:
- **file_path:** `plugin/.claude-plugin/plugin.json`
- **old_string:** `"version": "0.2.3",`
- **new_string:** `"version": "0.2.4",`

### - [ ] Step 2.10: Verify the version bump

Run:
```bash
grep -n '"version"' plugin/.claude-plugin/plugin.json
```

Expected output:
```
3:  "version": "0.2.4",
```

### - [ ] Step 2.11: Verify only the expected files are changed

Run:
```bash
git status --short
```

Expected (order-insensitive; tracked-file section must match exactly):
```
 M plugin/.claude-plugin/plugin.json
 M plugin/commands/quest.md
?? plugin/agents/model-echo.md
```

Untracked `.claude/` and `CLAUDE.md` MAY appear and are acceptable. If ANY other tracked file shows as modified, STOP and investigate before staging.

Then run:
```bash
git diff plugin/commands/quest.md plugin/.claude-plugin/plugin.json | head -80
```

Confirm the visible diff contains ONLY:
- Six Step-heading renumbers (5 → 6, 4 → 5, 3 → 4, 2 → 3) plus the new Step 2 insertion in quest.md
- The single version line change in plugin.json
- No whitespace-only drift, no line-ending changes in untouched sections

### - [ ] Step 2.12: Stage the three files

Run:
```bash
git add plugin/agents/model-echo.md plugin/commands/quest.md plugin/.claude-plugin/plugin.json
```

Do NOT use `git add -A` or `git add .`.

### - [ ] Step 2.13: Verify staging contents

Run:
```bash
git diff --cached --stat
```

Expected:
- 3 files changed
- `plugin/agents/model-echo.md` shows a creation with roughly 25-35 lines added
- `plugin/commands/quest.md` shows additions for the new Step 2 plus four heading-number edits
- `plugin/.claude-plugin/plugin.json` shows 1 insertion, 1 deletion

### - [ ] Step 2.14: Commit

Use this exact HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
feat(quest): add model-echo diagnostic and self-check step (v0.2.4)

Adds plugin/agents/model-echo.md, a minimal diagnostic probe declared
as model: sonnet. When dispatched, it reports the model it is actually
running on via $ANTHROPIC_MODEL or harness introspection, returning a
single-line `model: <string>` response.

Wires a new Step 2 into plugin/commands/quest.md — Mordain now runs the
self-check at the start of every quest. If model-echo reports running
on Opus despite its sonnet frontmatter, the user sees a non-blocking
warning banner naming likely causes (ANTHROPIC_MODEL env, Opus-only
plan, or frontmatter not being honored by this Claude Code version).

Existing Steps 2–5 renumbered to 3–6. No other changes.

This is rung 2 of the v0.3 staircase. Surfaces the routing bug
deterministically; prompt tightening and the full roster expansion
follow in v0.2.5 and v0.3.0 respectively.

Ref: docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### - [ ] Step 2.15: Verify the commit

Run:
```bash
git log -1 --stat
```

Expected:
- Subject: `feat(quest): add model-echo diagnostic and self-check step (v0.2.4)`
- Exactly 3 files changed
- `plugin/agents/model-echo.md` shows as a new file
- `plugin/.claude-plugin/plugin.json` shows 1 insertion, 1 deletion
- `plugin/commands/quest.md` shows a small net-positive diff (roughly 15–25 new lines, 4 heading edits)

If any other file appears in the commit, run `git reset HEAD~1` and investigate which extra files got staged. Redo Steps 2.12–2.15 with explicit paths.

### - [ ] Step 2.16: Verify nothing leaked

Run:
```bash
git show --stat HEAD
```

Confirm the file list contains ONLY:
- `plugin/agents/model-echo.md`
- `plugin/commands/quest.md`
- `plugin/.claude-plugin/plugin.json`

No other entries.

---

## Out of scope (do NOT do)

- No plan.md file creation or integration — that is v0.3.0.
- No updates to README.md, CHARACTERS.md, or CLAUDE.md — those land in v0.3.0 alongside the full roster.
- No prompt tightening on any existing agent — that is v0.2.5.
- No new adventurers beyond model-echo — that is v0.3.0.
- No push to remote.
- No modification to Mordain's allowed-tools in the command frontmatter — `Agent` is already there, which is all the self-check needs.

If tempted to "also fix" an adjacent thing, STOP and report. Narrow diffs keep the staircase auditable.

---

## Self-review

**1. Spec coverage.** Spec Section 5 row `v0.2.4 | Add model-echo.md + wire self-check into quest.md (minimal) | Surfaces the routing bug deterministically. Gets data.` — Task 1 adds the agent; Task 2 wires the self-check plus bumps the version. Fully covered.

**2. Placeholder scan.** Angle-bracket placeholders in the "expected output" blocks (`<N1>:### Step 1 ...`) are LINE-NUMBER placeholders, not TBDs — intentional because exact line numbers shift after edits. Everything else is literal. No "TBD", no "similar to Task N", no "add appropriate error handling." ✓

**3. Type/identifier consistency.** Agent name `model-echo` is consistent across the agent file (`name: model-echo` in frontmatter) and the quest.md invocation (`subagent_type: "model-echo"`). Model string `sonnet` is consistent. Version `0.2.4` is consistent. ✓

**4. Bite-sized granularity.** Task 1 has 3 steps; Task 2 has 16 steps. Each step is a single action (one Edit, one grep, one Bash command, one commit). ✓

**5. Renumbering safety.** Steps 2.2–2.6 renumber headings from HIGHEST to LOWEST to prevent collisions — critical detail. For example, renumbering `Step 2 → 3` before renumbering `Step 3 → 4` would collapse both into `### Step 3`, creating two identical headings and breaking subsequent Edit calls. The plan's order prevents this. ✓

**6. Edit-call uniqueness.** Every `old_string` for Edit calls is verified unique by the file context: Step-heading lines appear exactly once each; the insertion anchor in Step 2.6 (`### Step 3 — Plan` preceded by the "Do not guess." sentence) is unique because no other Plan heading exists and the preceding sentence appears only once in the file. ✓

**7. Commit message style.** Subject uses `feat(quest):` prefix matching the repo's conventional-commit style (see `feat: cast the guild` and `fix(quest): refine verify-red rule` in git log). Includes version suffix `(v0.2.4)`. Body explains what, why, and forward-links. Ref line included. Co-author trailer included. ✓

No issues found. Plan is ready for execution.
