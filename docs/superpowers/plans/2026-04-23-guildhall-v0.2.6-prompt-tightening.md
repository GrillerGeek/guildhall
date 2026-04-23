# Guildhall v0.2.6 — prompt tightening for 4.7 literalness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Guildhall v0.2.6 — add a standardized `## Your contract` block to each of the six existing adventurer prompts (INPUT / OUTPUT / NON-GOALS / EFFORT), fix the two wording nits surfaced by the v0.2.4 code-quality review on `model-echo`, update the design spec's Risks section with a one-line un-pause note, and bump the plugin version to 0.2.6.

**Architecture:** Ten edits across eight files in a single commit on branch `ship/v0.2.6-prompt-tightening`. No new files. No new agents. Prompt hygiene only — the observable behavior of `/quest` is unchanged; the contract blocks make the agent expectations explicit so Opus 4.7's literal interpretation has the structured hooks to latch onto.

**Tech Stack:** Markdown (agent bodies). No code. Verification is structural (grep for the new heading in each file) plus a final cross-check that no prose outside the new blocks drifted.

**This is rung 3 of the 5-rung staircase in `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` (v0.2.3 → v0.2.4 → v0.2.5 → v0.2.6 → v0.3.0).**

**Why we're proceeding despite the paused routing bug:** roster value and prompt clarity are independent of model-tier routing. Tighter prompts help Opus 4.7 follow the contract literally regardless of tier. The cost-posture payoff activates when the upstream fix lands; everything in this rung is valuable today at any tier.

---

## Context for the engineer (zero-assumption briefing)

**Repo state at plan-write time:**
- Working on branch `ship/v0.2.6-prompt-tightening`, cut from `main` at commit `dccaa60` (the merge commit from PR #1).
- Six existing adventurer files live at `plugin/agents/<name>.md`. Each has YAML frontmatter, a character quote, then an opening "You are **Name** —" paragraph, then agent-specific body prose.
- `plugin/agents/model-echo.md` is the v0.2.4 diagnostic — also gets two small edits.
- `plugin/.claude-plugin/plugin.json` is at version `0.2.5`; bumps to `0.2.6` in this rung.
- `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` has a "Risks and mitigations" section that currently treats the paused staircase as terminal; a one-line addendum is added.

**Why the contract block pattern:** Opus 4.7 interprets prompts literally and does not fill in gaps. An explicit INPUT / OUTPUT / NON-GOALS / EFFORT block gives the model fixed hooks: what does it receive, what must it produce, what must it refuse, and at what effort level. The design spec Section 4 defines the target contract for each agent; this plan is the execution of that section for the six existing adventurers.

**Where the contract block is inserted in each file:**

Immediately after the opening "You are **<Name>** — ..." paragraph, with a blank line above and below. In some agents, the opening paragraph is followed by a list (e.g., prototype-builder's "Your ceremony is ZERO"). The new section is inserted between the paragraph and that list, leaving existing content intact.

---

## File inventory

Eight files change in this plan:

- **Modify:** `plugin/agents/prototype-builder.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/test-author.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/feature-implementer.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/refactorer.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/debug-investigator.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/ui-test-author.md` (insert `## Your contract` block)
- **Modify:** `plugin/agents/model-echo.md` (two wording nits)
- **Modify:** `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` (Risks addendum)
- **Modify:** `plugin/.claude-plugin/plugin.json` (version bump)

No new files. CHARACTERS.md untouched. README.md untouched. Single commit.

---

## Task 1: Add `## Your contract` block to each of the six existing adventurers

**Shared insertion rule:** for each of the six agent files, locate the opening paragraph that begins `You are **<Name>** —`. The next non-empty line should either be a list, a heading, or another paragraph. Insert the new `## Your contract` section with a blank line before and after, BETWEEN the opening paragraph and that next block, preserving all existing content exactly.

### - [ ] Step 1.1: prototype-builder.md

**File:** `plugin/agents/prototype-builder.md`

Read the file to find the exact opening paragraph text, then use Edit with:

- **old_string:** the opening paragraph line (`You are **Pip Quickfoot** — a halfling scout who returns from every expedition with a working thing and a crooked grin. Your ONLY job: get a working spike in front of Jason as fast as possible.`) followed by the blank line and the exact next non-empty line (whichever it is — a heading, a bulleted item, etc.).

- **new_string:** the same opening paragraph, followed by the new contract block, followed by the same next line preserved exactly. The new block:

```markdown
## Your contract

- **INPUT:** a one-line ask from Mordain plus (where relevant) cited repo conventions — language choice, existing framework, running-environment notes.
- **OUTPUT:** working code in the repo (new file or edit), plus a one-line "works / doesn't" status report back to Mordain. No tests, no README, no polish.
- **NON-GOALS:** do NOT write tests, do NOT handle errors you have not actually seen happen, do NOT design for cases the ask did not mention, do NOT refactor existing code beyond what the ask touches.
- **EFFORT:** `medium` — speed over rigor. This is disposable code.
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/prototype-builder.md` → `1`.

### - [ ] Step 1.2: test-author.md

**File:** `plugin/agents/test-author.md`

Same pattern. Opening paragraph: `You are **Seraphine Dawnveil** — an elven Cleric who reads the IDD Spec as scripture. Your ONLY job: write tests that cover the Expectations block of the Spec, independently of any implementation.`

**Contract block to insert:**

```markdown
## Your contract

- **INPUT:** the path to an IDD Spec file. The Expectations block is load-bearing — every expectation maps to at least one test.
- **OUTPUT:** one or more failing test files plus the list of file paths you wrote. Tests must fail against a blank implementation and pass against a correct one.
- **NON-GOALS:** do NOT read any implementation code in `src/` / `lib/` / equivalent, do NOT run existing tests to confirm state, do NOT guess about ambiguous spec wording — if the spec is ambiguous, flag it and stop, do not invent a resolution.
- **EFFORT:** `high` — strict spec-to-test mapping is the entire value.
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/test-author.md` → `1`.

### - [ ] Step 1.3: feature-implementer.md

**File:** `plugin/agents/feature-implementer.md`

Opening paragraph begins `You are **Bruga Ironseam**`. Read the file to get the exact opening sentence.

**Contract block:**

```markdown
## Your contract

- **INPUT:** an IDD Spec (Expectations and Boundaries blocks both load-bearing) plus the path(s) to the failing test file(s) produced by test-author.
- **OUTPUT:** code that turns the failing tests green, plus the list of files you wrote or changed. No new tests written; tests in scope for you are READ ONLY.
- **NON-GOALS:** do NOT modify test files, do NOT add features beyond the Expectations, do NOT stray outside the Boundaries block, do NOT refactor existing code unless refactoring is explicitly required to make tests pass. If the blueprint (spec) is malformed or self-contradicting, drop the hammer and return to Mordain.
- **EFFORT:** `high` — structured work with a known success criterion (green tests).
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/feature-implementer.md` → `1`.

### - [ ] Step 1.4: refactorer.md

**File:** `plugin/agents/refactorer.md`

Opening paragraph begins `You are **Tink Whiffletree**`.

**Contract block:**

```markdown
## Your contract

- **INPUT:** a narrowly scoped instruction from Mordain ("extract X", "rename Y to Z") plus confirmation that the current test state is green.
- **OUTPUT:** a behavior-preserving diff plus confirmation that tests are still green after your changes. If your refactor breaks any test, back out completely — every time, no exceptions.
- **NON-GOALS:** do NOT broaden the scope by one line beyond what Mordain asked, do NOT "also clean up" unrelated code even if it is bothering you (mention in report; do not fix), do NOT change behavior — any behavior delta is a failed refactor.
- **EFFORT:** `high` — mechanical but verification-sensitive.
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/refactorer.md` → `1`.

### - [ ] Step 1.5: debug-investigator.md

**File:** `plugin/agents/debug-investigator.md`

Opening paragraph begins `You are **Kael the Tracker**`.

**Contract block:**

```markdown
## Your contract

- **INPUT:** a bug reproduction (steps or code that triggers the issue), the error trace, and the relevant file paths Mordain has already surveyed.
- **OUTPUT:** a written root-cause report naming the actual point of origin. If you cannot prove the cause, say "uncertain" explicitly and list what you ruled out.
- **NON-GOALS:** do NOT propose a fix, do NOT edit any file, do NOT refactor "while you are here", do NOT speculate — claims must be traceable to evidence in the code or logs.
- **EFFORT:** `xhigh` — root causes hide; open-ended investigation warrants the tokens.
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/debug-investigator.md` → `1`.

### - [ ] Step 1.6: ui-test-author.md

**File:** `plugin/agents/ui-test-author.md`

Opening paragraph begins `You are **Vera Nightwhistle**`.

**Contract block:**

```markdown
## Your contract

- **INPUT:** an IDD Spec (Expectations block load-bearing), a running-app URL, and the code paths for the feature being tested. You ARE permitted to read implementation code here — this is the exception to the test-authoring independence rule, because you cannot write selector-level tests against an interface you have not examined.
- **OUTPUT:** Playwright test files plus selector notes explaining the decisions behind non-obvious locators.
- **NON-GOALS:** do NOT modify implementation code, do NOT rewrite tests to match a botched performance — if an actor misses a cue, that is a bug in the UI, not your script; do NOT add unit tests (those are Seraphine's domain), do NOT spin up your own dev server — the running app URL is given to you.
- **EFFORT:** `high` — structured work with a running reference.
```

**Verify:** `grep -c '^## Your contract$' plugin/agents/ui-test-author.md` → `1`.

### - [ ] Step 1.7: Cross-check all six insertions

Run:
```bash
grep -l '^## Your contract$' plugin/agents/*.md | sort
```

Expected output (exactly these 7 lines, in alpha order):
```
plugin/agents/debug-investigator.md
plugin/agents/feature-implementer.md
plugin/agents/model-echo.md
plugin/agents/prototype-builder.md
plugin/agents/refactorer.md
plugin/agents/test-author.md
plugin/agents/ui-test-author.md
```

(`model-echo.md` already had `## Your contract` from v0.2.4 — so the total is 7 files with the heading after Task 1 completes.)

Then verify nothing else was corrupted — each of the six files should still have their frontmatter intact:
```bash
for f in plugin/agents/prototype-builder.md plugin/agents/test-author.md plugin/agents/feature-implementer.md plugin/agents/refactorer.md plugin/agents/debug-investigator.md plugin/agents/ui-test-author.md; do
  head -1 "$f" | grep -q '^---$' && echo "OK $f" || echo "FAIL $f"
done
```

Expected: six `OK` lines.

---

## Task 2: Fix the two model-echo wording nits

**File:** `plugin/agents/model-echo.md`

Both nits come from the v0.2.4 code-quality review.

### - [ ] Step 2.1: Fix the INPUT contradiction

The current contract says `INPUT: none (Mordain dispatches you with an empty prompt or a one-line greeting)`. But Mordain now passes the literal string `"Report the model you are running on."` — so "none" whiplashes. Reframe as a greeting.

Use Edit on `plugin/agents/model-echo.md`:
- **old_string:** `- **INPUT:** none (Mordain dispatches you with an empty prompt or a one-line greeting).`
- **new_string:** `- **INPUT:** a one-line greeting from Mordain (e.g., "Report the model you are running on."). You do not need to parse it — your job is fixed regardless of the greeting text.`

### - [ ] Step 2.2: Fix the "no other command" rule contradiction

The Hard Rules block says `Do NOT run any command other than \`echo "$ANTHROPIC_MODEL"\``. But the "self-introspection" fallback doesn't run any command at all — so a strict reading forbids the fallback. Narrow the rule to Bash commands.

Use Edit on `plugin/agents/model-echo.md`:
- **old_string:** `- Do NOT run any command other than \`echo "$ANTHROPIC_MODEL"\`.`
- **new_string:** `- Do NOT run any Bash command other than \`echo "$ANTHROPIC_MODEL"\`. (Self-introspection requires no command at all and remains allowed per the fallback above.)`

### - [ ] Step 2.3: Verify

Run:
```bash
grep -c 'one-line greeting from Mordain' plugin/agents/model-echo.md
```
Expected: `1`.

Run:
```bash
grep -c 'any Bash command other than' plugin/agents/model-echo.md
```
Expected: `1`.

---

## Task 3: Update the design spec Risks section (un-pause addendum)

**File:** `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`

### - [ ] Step 3.1: Append the un-pause line to the first Risk item

Read the file's "Risks and mitigations" section. The first Risk item currently reads (approximately):

> - **Risk:** the self-check at v0.2.4 reveals alias frontmatter is broken too, not just full IDs. **Mitigation:** pause the staircase, open an upstream Claude Code issue, fall back to explicit `--model` in session as a workaround until fixed.

Use Edit to append an un-pause addendum immediately after the mitigation sentence — insert `**Update (2026-04-23):** ...` text inline with the existing mitigation. Specifically:

- **old_string:** `**Mitigation:** pause the staircase, open an upstream Claude Code issue, fall back to explicit `--model` in session as a workaround until fixed.`
- **new_string:** `**Mitigation:** pause the staircase, open an upstream Claude Code issue, fall back to explicit `--model` in session as a workaround until fixed. **Update (2026-04-23):** dogfood run confirmed the bug and v0.2.5 documented the pause; staircase subsequently resumed at v0.2.6 on the reframe that roster value and prompt clarity are independent of model-tier routing — the cost posture activates latently when upstream ships a fix.`

### - [ ] Step 3.2: Verify

Run:
```bash
grep -c 'Update (2026-04-23)' docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md
```
Expected: `1`.

---

## Task 4: Bump version, stage, commit, verify

### - [ ] Step 4.1: Bump plugin.json version

Use Edit on `plugin/.claude-plugin/plugin.json`:
- **old_string:** `"version": "0.2.5",`
- **new_string:** `"version": "0.2.6",`

### - [ ] Step 4.2: Verify the bump

Run: `grep -n '"version"' plugin/.claude-plugin/plugin.json`
Expected: `3:  "version": "0.2.6",`

### - [ ] Step 4.3: Pre-commit tracked-file check

Run: `git status --short`

Expected tracked-file lines (exactly eight `M` entries, order-insensitive):
```
 M docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md
 M plugin/.claude-plugin/plugin.json
 M plugin/agents/debug-investigator.md
 M plugin/agents/feature-implementer.md
 M plugin/agents/model-echo.md
 M plugin/agents/prototype-builder.md
 M plugin/agents/refactorer.md
 M plugin/agents/test-author.md
 M plugin/agents/ui-test-author.md
```

Wait — that's nine files total (six adventurers + model-echo + design spec + plugin.json). Let me recount:

1. plugin/agents/prototype-builder.md
2. plugin/agents/test-author.md
3. plugin/agents/feature-implementer.md
4. plugin/agents/refactorer.md
5. plugin/agents/debug-investigator.md
6. plugin/agents/ui-test-author.md
7. plugin/agents/model-echo.md
8. docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md
9. plugin/.claude-plugin/plugin.json

Nine modified files total. Untracked `.claude/`, `CLAUDE.md`, `docs/superpowers/plans/2026-04-23-guildhall-v0.2.6-prompt-tightening.md`, `docs/superpowers/upstream-issue-draft.md`, and `plugin/.claude-plugin/marketplace.json` MAY appear and are acceptable — they are NOT staged in this commit.

If any OTHER tracked file shows as modified (e.g., README, CHARACTERS.md), STOP and investigate.

### - [ ] Step 4.4: Diff sanity-check — no prose drift outside the new blocks

For the six adventurer edits, confirm the diff ADDS a `## Your contract` block and nothing else. Run:

```bash
git diff plugin/agents/prototype-builder.md | grep -cE '^\+'
```
Expected: 8 lines added (1 heading + 1 blank + 4 bullets + 1 blank + 1 trailing blank, approximately — accept 7 to 10).

Repeat for each of the other five adventurer files and `model-echo.md`. If any file's addition count is vastly outside that range, the diff may have drifted — read the diff.

Also spot-check that no line was REMOVED outside the model-echo edits:

```bash
for f in plugin/agents/prototype-builder.md plugin/agents/test-author.md plugin/agents/feature-implementer.md plugin/agents/refactorer.md plugin/agents/debug-investigator.md plugin/agents/ui-test-author.md; do
  removed=$(git diff "$f" | grep -cE '^-[^-]' || echo 0)
  echo "$f: $removed removed"
done
```

Expected: `0 removed` for each of the six adventurers (they are pure additions). If any show non-zero removals, the Edit corrupted existing prose — STOP and investigate.

`model-echo.md` will legitimately show 2 removed lines (the two nits being replaced).

### - [ ] Step 4.5: Stage the nine files

Run:
```bash
git add plugin/agents/prototype-builder.md plugin/agents/test-author.md plugin/agents/feature-implementer.md plugin/agents/refactorer.md plugin/agents/debug-investigator.md plugin/agents/ui-test-author.md plugin/agents/model-echo.md docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md plugin/.claude-plugin/plugin.json
```

Do NOT use `git add -A` or `git add .`.

### - [ ] Step 4.6: Verify staging

Run: `git diff --cached --stat`

Expected: 9 files changed. All existing files (no new files).

### - [ ] Step 4.7: Commit

Use this HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
feat: tighten adventurer prompts for 4.7 literalness (v0.2.6)

Adds an explicit `## Your contract` block (INPUT / OUTPUT / NON-GOALS /
EFFORT) to each of the six existing adventurer prompts, so Opus 4.7's
literal interpretation has structured hooks to latch onto:

- prototype-builder (Pip) — medium effort; disposable code
- test-author (Seraphine) — high effort; spec-to-test mapping
- feature-implementer (Bruga) — high effort; structured green
- refactorer (Tink) — high effort; verification-sensitive
- debug-investigator (Kael) — xhigh effort; investigation is open-ended
- ui-test-author (Vera) — high effort; selector-level tests with running ref

Folds in two wording nits from the v0.2.4 model-echo code-quality review:
INPUT contract now acknowledges Mordain's greeting string; the "no other
command" hard rule now narrows to Bash commands, unblocking the
self-introspection fallback.

Appends a one-line un-pause note to the v0.3 design spec's Risks
section documenting the reframe: roster value and prompt clarity are
independent of model-tier routing, so the staircase resumed at v0.2.6
despite the upstream routing bug remaining unresolved. Cost posture
remains aspirational; contracts still pay off at every tier.

No new files. No new adventurers. No quest.md changes. Observable
behavior of /quest is unchanged.

Ref: docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### - [ ] Step 4.8: Verify the commit

Run: `git log -1 --stat`

Expected:
- Subject: `feat: tighten adventurer prompts for 4.7 literalness (v0.2.6)`
- 9 files changed
- Net-positive line count (approximately 60 insertions, 2 deletions)

If a different file count appears, run `git reset HEAD~1` and redo Steps 4.5–4.8.

### - [ ] Step 4.9: Final leak check

Run: `git show --stat HEAD | tail -15`

Confirm the file list contains exactly the nine expected files and nothing else.

Run: `git status --short`

Confirm the tracked-file section is empty (working tree clean post-commit). Only `??` untracked entries remain.

---

## Out of scope (do NOT do)

- No new agents — that is v0.3.0.
- No changes to quest.md — the self-check + existing process stay intact for this rung.
- No changes to CHARACTERS.md — character voice is unchanged.
- No changes to README.md or CLAUDE.md — no user-facing behavior to document.
- No rewrite of existing prose in the adventurer files — only additive `## Your contract` blocks plus the two model-echo nits.
- No remote push.

If tempted to "also fix" adjacent prose, STOP. Narrow diffs keep the staircase auditable.

---

## Self-review

**1. Spec coverage.** Design spec Section 4 defines contracts for each existing adventurer. The six contract blocks above are the concrete realization of those Section 4 descriptions. Model-echo nits come from the Section 5 "minor wording" observations in the v0.2.4 review. Un-pause addendum closes the Risks section loop.

**2. Placeholder scan.** No TBDs. No "similar to Task N" — every contract block's content is written out in full.

**3. Type/identifier consistency.** Agent names match across frontmatter and prose throughout the repo. Effort levels (`medium` / `high` / `xhigh` / `low` for model-echo) are consistent with the spec's Section 3 effort table.

**4. Bite-sized granularity.** Task 1 is 6 sub-steps (one per agent) plus a cross-check; Task 2 is 3 steps; Task 3 is 2 steps; Task 4 is 9 steps. Each step is a single Edit or verification.

**5. Edit-call uniqueness.** Each agent's opening `You are **<Name>** —` sentence appears exactly once in its file. Each `## Your contract` heading being added will be the only such heading in each agent file (model-echo's existing heading is different context — its contract is being EDITED by Task 2, not replaced).

**6. Diff-drift safety net.** Step 4.4 explicitly counts removed lines per adventurer file — catches any Edit that accidentally broke existing prose while inserting the contract block.

**7. Commit message style.** `feat:` prefix for a prompt-tightening change matches repo convention (see `feat: cast the guild` in history). Body summarizes the three distinct changes (adventurer contracts, model-echo nits, spec addendum). Ref line present. Co-author trailer present.

No issues found. Plan is ready for execution.
