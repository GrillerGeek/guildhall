# Guildhall v0.2.3 — Revert test-author model pin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Guildhall v0.2.3 — revert `plugin/agents/test-author.md`'s frontmatter from `model: claude-sonnet-4-6` to `model: sonnet` to standardize on alias-only model declarations, and bump plugin version from 0.2.2 to 0.2.3.

**Architecture:** Single-file behavior change plus version bump, committed together. This is rung 1 of the 5-rung staircase defined in `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`. Later rungs (v0.2.4 model-echo, v0.2.5 prompt tightening, v0.3.0 new adventurers, v0.3.1 tuning pass) are **out of scope for this plan** and get their own plans when this one lands.

**Tech Stack:** Markdown frontmatter (YAML), JSON manifest. No code. No tests. No runtime verification in this rung — runtime verification arrives in v0.2.4 with the `model-echo` diagnostic agent.

**Why no TDD here:** TDD applies when there is behavior to verify in automation. Frontmatter field values are validated by (a) grep assertion on the file content and (b) downstream use. The v0.3.0 `plugin-validator` agent will eventually lint this mechanically; until then, `grep` is the verification.

---

## Context for the engineer (zero-assumption briefing)

This repository is a **Claude Code plugin**, not an application. It ships only markdown agent definitions and JSON manifest — no code to compile, no tests to run, no lint to pass. "Building" = editing files. "Testing" = dogfooding the plugin against a real Claude Code session.

Background on why this one-line change matters:
- Claude Code subagent dispatch honors `model:` frontmatter per [official docs](https://docs.claude.com/en/docs/claude-code/sub-agents), accepting either aliases (`sonnet`, `opus`, `haiku`) OR full IDs (`claude-sonnet-4-6`).
- However, community reports (GitHub issue #34821 and others) suggest the Task tool's internal `model:` parameter is hardcoded to the alias enum, and full IDs can silently fall back to parent-inherit behavior.
- Commit `b05060e` pinned `test-author` to the full ID `claude-sonnet-4-6`. If the community reports are correct, that "fix" may have inadvertently caused `test-author` to inherit Opus from the parent session — the opposite of the intent.
- Five other agents use the `sonnet` alias and were observed also running on Opus, which may have a different root cause (env var, plan restriction). v0.2.3 does not address those. v0.2.4's `model-echo` agent will isolate the variables.

**The change:** revert `test-author.md` to `model: sonnet` so all six adventurers use aliases uniformly. This is cheap, immediately shippable, and validates the alias hypothesis when combined with v0.2.4's runtime check.

---

## File inventory

Exactly two files change in this plan:

- **Modify:** `plugin/agents/test-author.md` (line 11 only)
- **Modify:** `plugin/.claude-plugin/plugin.json` (line 3 only)

No new files. No deletions. No CLAUDE.md touch (that file is untracked and owned by the user's earlier `/init` work).

---

## Task 1: Revert test-author model pin and bump version

**Files:**
- Modify: `plugin/agents/test-author.md:11`
- Modify: `plugin/.claude-plugin/plugin.json:3`

### - [ ] Step 1: Confirm current state of test-author.md frontmatter

Run:
```bash
grep -n "^model:" plugin/agents/test-author.md
```

Expected output:
```
11:model: claude-sonnet-4-6
```

If the output is instead `11:model: sonnet`, STOP — the revert has already happened. Report to the user and abort this task.

If the line number is not 11, continue but note the actual line number; the Edit in Step 3 keys on the exact string, not the line number.

### - [ ] Step 2: Confirm current state of plugin.json version

Run:
```bash
grep -n '"version"' plugin/.claude-plugin/plugin.json
```

Expected output:
```
3:  "version": "0.2.2",
```

If the version is already `0.2.3` or higher, STOP and report — someone else bumped it already.

### - [ ] Step 3: Edit test-author.md — replace the model line

Use the Edit tool with:

- **file_path:** `plugin/agents/test-author.md`
- **old_string:** `model: claude-sonnet-4-6`
- **new_string:** `model: sonnet`

Only one occurrence of that string exists in the file (it is the frontmatter value). Do not use `replace_all`.

### - [ ] Step 4: Verify the edit landed correctly

Run:
```bash
grep -n "^model:" plugin/agents/test-author.md
```

Expected output:
```
11:model: sonnet
```

If the output still shows `claude-sonnet-4-6`, the Edit failed — re-run Step 3 after reading the file to confirm exact whitespace.

### - [ ] Step 5: Edit plugin.json — bump version to 0.2.3

Use the Edit tool with:

- **file_path:** `plugin/.claude-plugin/plugin.json`
- **old_string:** `"version": "0.2.2",`
- **new_string:** `"version": "0.2.3",`

### - [ ] Step 6: Verify the version bump

Run:
```bash
grep -n '"version"' plugin/.claude-plugin/plugin.json
```

Expected output:
```
3:  "version": "0.2.3",
```

### - [ ] Step 7: Verify no other files changed

Run:
```bash
git status --short
```

Expected output (exactly these two lines, in any order; untracked `.claude/`, `CLAUDE.md`, or `docs/` directories may also appear and are acceptable):
```
 M plugin/.claude-plugin/plugin.json
 M plugin/agents/test-author.md
```

If any OTHER tracked file shows as modified, STOP and investigate before committing.

Then run:
```bash
git diff plugin/agents/test-author.md plugin/.claude-plugin/plugin.json
```

Expected: exactly two line changes — one in each file, matching Steps 3 and 5. If the diff shows anything else (whitespace, line endings, additional edits), STOP and investigate.

### - [ ] Step 8: Stage and commit

Run:
```bash
git add plugin/agents/test-author.md plugin/.claude-plugin/plugin.json
```

Do NOT use `git add -A` or `git add .` — that would include the untracked `.claude/`, `CLAUDE.md`, and `docs/` paths that are NOT part of this rung.

Then commit using this exact message (HEREDOC format to preserve formatting):

```bash
git commit -m "$(cat <<'EOF'
fix(test-author): revert model pin to sonnet alias (v0.2.3)

Reverts b05060e which pinned test-author to the full model ID
claude-sonnet-4-6. Community reports (GitHub issue #34821 and others)
indicate Claude Code's Task-tool model dispatch may silently fall back
to parent-inherit when a full model ID is supplied, whereas aliases
(sonnet/opus/haiku) are the documented working path.

Standardizes all six adventurers on alias-only frontmatter. Runtime
verification that Sonnet is actually honored lands in v0.2.4 with the
model-echo diagnostic agent.

Ref: docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### - [ ] Step 9: Verify the commit

Run:
```bash
git log -1 --stat
```

Expected output:
- The commit subject matches `fix(test-author): revert model pin to sonnet alias (v0.2.3)`.
- The stat line shows exactly 2 files changed, 2 insertions(+), 2 deletions(-) OR 1 file changed, 1 insertion(+), 1 deletion(-) for each file — total is 2 insertions and 2 deletions across 2 files.

If the commit includes more than those two files, STOP. Reset with:
```bash
git reset HEAD~1
```
Then investigate which extra files got staged and redo Steps 8–9.

### - [ ] Step 10: Verify nothing else leaked into the commit

Run:
```bash
git show --stat HEAD
```

Confirm the file list contains ONLY:
- `plugin/.claude-plugin/plugin.json`
- `plugin/agents/test-author.md`

If any other file appears, use `git reset HEAD~1` and redo Steps 8–9 with explicit paths.

---

## Out of scope for this plan (do NOT do these)

These belong to later rungs and MUST NOT be added to this v0.2.3 commit:

- Creating the `model-echo` agent (that is v0.2.4).
- Modifying any other agent's frontmatter (no other agent needs a revert — they already use aliases).
- Tightening any agent prompt for 4.7 literalness (that is v0.2.5).
- Adding new adventurers (that is v0.3.0).
- Modifying `quest.md` (touched in v0.2.4 minimally and v0.3.0 substantially).
- Updating README, CHARACTERS.md, or CLAUDE.md. The README's "cost posture" paragraph is aspirational and will be updated in v0.3.0; leaving it stale in v0.2.3 is acceptable and intentional.
- Pushing the commit to the remote. User will push when ready.

If the engineer feels tempted to "also fix" something adjacent, STOP and report to the user instead. This rung's small surface is the point — it is what makes the staircase auditable.

---

## Self-review

Running inline before transition to execution.

**1. Spec coverage check.** The spec's Section 5 staircase table row `v0.2.3 | Revert test-author to model: sonnet alias | One-line fix; validates the alias-over-full-ID hypothesis.` — this plan covers that row fully. The "validates the hypothesis" language is correctly deferred to v0.2.4 where `model-echo` provides runtime proof; v0.2.3 alone does not "validate" at runtime and the plan's context section says so explicitly.

**2. Placeholder scan.** No TBDs. No "add appropriate error handling." No "similar to Task N." All commands and expected outputs are literal. ✓

**3. Type/identifier consistency.** No types or identifiers defined across tasks — only string values. The `model: sonnet` value is consistent across all references in the plan. ✓

**4. Bite-sized granularity.** 10 steps, each a single action under 2 minutes. ✓

**5. File-path precision.** All paths are exact relative paths from repo root. ✓

**6. Commit-message style match.** Drafted message matches the repo's conventional-commit style (`fix(scope):` prefix, version in parens at end of subject, multi-paragraph body with a Ref: line — consistent with `fix(quest): refine verify-red rule and make refactor step conditional (v0.2.1)` and `test(v0.2.2): pin test-author to full model ID claude-sonnet-4-6`). ✓

**7. Destructive-action handling.** Step 9's `git reset HEAD~1` is the only destructive operation and is gated by a verification failure — not run optimistically. ✓

No issues found. Plan is ready for execution.
