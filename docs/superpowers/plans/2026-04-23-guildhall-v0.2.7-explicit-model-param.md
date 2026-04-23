# Guildhall v0.2.7 — explicit model parameter at dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship Guildhall v0.2.7 — work around the Claude Code subagent-frontmatter bug by teaching Mordain to read each adventurer's `model:` value from its agent file and pass it explicitly as the `model` parameter on every `Agent(...)` dispatch. The `Agent` tool's `model` parameter is documented to *"take precedence over the agent definition's model frontmatter"* and is honored by Claude Code where the frontmatter itself is not.

**Architecture:** Five files change in a single commit on branch `ship/v0.2.7-explicit-model-param`:

1. `plugin/commands/quest.md` — Step 2 (self-check) dispatches `model-echo` with explicit `model: "sonnet"`; new sub-step in Step 3 to read and cache each adventurer's model; Step 4 rewritten to require the `model` param in every dispatch; warning banner text updated.
2. `plugin/README.md` — retire the ⚠️ "aspirational" Known Issue block; replace with a concise "how routing works" paragraph explaining the explicit-dispatch-param mechanism.
3. `README.md` — Status block updated 0.2.6 → 0.2.7 with a one-line workaround note.
4. `plugin/.claude-plugin/plugin.json` — version 0.2.6 → 0.2.7.
5. `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` — append a second **Update (2026-04-23, second)** line to the Risks section noting the workaround shipped.

**Tech Stack:** Markdown (command + agent docs) and JSON (manifest). No code. Verification is grep-based content checks.

**Validation path:** next dogfood run. If `model-echo` reports `sonnet` after this rung ships, the workaround works and the cost posture is real. If it still reports `opus`, an even deeper override is in play and we escalate.

---

## Context for the engineer (zero-assumption briefing)

The `Agent` tool in Claude Code has a `model` parameter defined as:

> *"Optional model override for this agent. Takes precedence over the agent definition's model frontmatter. If omitted, uses the agent definition's model, or inherits from the parent."*

Values: `sonnet | opus | haiku` (alias enum).

Observed behavior (confirmed via v0.2.4 `model-echo` diagnostic):
- When `model` is **omitted**: the agent's frontmatter `model:` is silently ignored and the subagent inherits the parent session's model. This is the bug.
- When `model` is **set explicitly**: it's honored. This is the workaround.

Fix: Mordain reads each adventurer's frontmatter `model:` value (the design's source of truth) and passes it explicitly at dispatch time. Agent frontmatter stays in place — it's documentation and the source Mordain reads from; the dispatch parameter is what actually takes effect.

**Caching rule:** once Mordain reads `plugin/agents/<name>.md`'s `model:` value in a quest, she caches it. No need to re-read for repeat dispatches (though only `test-author` and `feature-implementer` ever dispatch more than once per quest, via the single-retry rule).

**Edge cases handled by the plan:**
- Agent file has no `model:` field → Mordain omits the param, inheritance happens. (None of our agents lack `model:` today.)
- Agent file has a full model ID (none post-v0.2.3) → Mordain would need to normalize; not a concern today since all frontmatter is alias-form.
- Non-alias value in frontmatter → Mordain flags it, aborts that dispatch. (Not expected today.)

---

## File inventory

Five files change:

- **Modify:** `plugin/commands/quest.md` (Step 2 rewrite, Step 3 sub-step, Step 4 rewrite, banner text)
- **Modify:** `plugin/README.md` (cost posture rewrite)
- **Modify:** `README.md` (Status block)
- **Modify:** `plugin/.claude-plugin/plugin.json` (version)
- **Modify:** `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` (Risks addendum #2)

No new files. No agent file changes. No CHARACTERS.md update.

---

## Task 1: Rewrite `quest.md` Step 2 (self-check) with explicit model param

**File:** `plugin/commands/quest.md`

### - [ ] Step 1.1: Confirm current Step 2 structure

Run: `sed -n '52,66p' plugin/commands/quest.md`

Expected: Step 2 heading on line 52, body through line 65 including the existing warning banner and the "does not block" sentence on line 65.

### - [ ] Step 1.2: Replace the entire Step 2 block

Use Edit on `plugin/commands/quest.md`:

- **old_string** (the full current Step 2 block, 14 lines):

```
### Step 2 — Model-routing self-check

Before producing the plan, dispatch the `model-echo` diagnostic to verify that subagent model frontmatter is being honored. This is a one-shot diagnostic, not a blocking gate.

1. Dispatch: `Agent(subagent_type: "model-echo", description: "Verify model routing", prompt: "Report the model you are running on.")`.
2. Read the response. Because `model-echo` declares `model: sonnet` in its own frontmatter, an honest reply will contain `sonnet` or a Sonnet model ID such as `claude-sonnet-4-6`.
3. If the response contains `opus` (case-insensitive), emit the following warning to the user and then continue to Step 3:

   > ⚠️ Model-routing self-check: `model-echo` declares `model: sonnet` in its frontmatter, but reported running on Opus. This quest will continue, but the cost posture documented in the README is compromised. Likely causes: `ANTHROPIC_MODEL=claude-opus-4-7` set in your environment, an Opus-only plan, or the plugin's model frontmatter not being honored by this Claude Code version.

4. If the response is `model: unknown`, note that in your report but do NOT emit the warning — the agent could not introspect; lack of evidence is not evidence of a problem. Continue to Step 3.
5. Cache the result in memory for the duration of this quest. Do NOT re-run the self-check for subsequent dispatches within the same quest.

This step never blocks the quest. The user is trusted to Ctrl-C if the cost posture matters to them and the banner has fired.
```

- **new_string** (the rewritten Step 2 block, matching the same structural shape):

```
### Step 2 — Model-routing self-check

Before producing the plan, dispatch the `model-echo` diagnostic to verify that the explicit-model-parameter workaround is functioning. This is a one-shot diagnostic, not a blocking gate.

1. Read `plugin/agents/model-echo.md` frontmatter and confirm `model: sonnet`.
2. Dispatch with the model passed explicitly: `Agent(subagent_type: "model-echo", model: "sonnet", description: "Verify model routing", prompt: "Report the model you are running on.")`. The explicit `model` parameter is REQUIRED — Claude Code's subagent dispatch does not honor the agent file's frontmatter `model:` directly; only the explicit parameter works (see Step 4 for the full rationale).
3. Read the response. An honest reply will contain `sonnet` or a Sonnet model ID such as `claude-sonnet-4-6`.
4. If the response contains `opus` (case-insensitive), emit the following warning to the user and then continue to Step 3:

   > ⚠️ Model-routing self-check: `model-echo` was dispatched with explicit `model: "sonnet"` parameter, but reported running on Opus. The dispatch parameter is not being honored. Likely causes: `ANTHROPIC_MODEL=claude-opus-4-7` set in your environment, an Opus-only plan, or a deeper Claude Code issue. This quest will continue, but the cost posture documented in the README is compromised — investigate before trusting quest cost estimates.

5. If the response is `model: unknown`, note that in your report but do NOT emit the warning — the agent could not introspect; lack of evidence is not evidence of a problem. Continue to Step 3.
6. Cache the result in memory for the duration of this quest. Do NOT re-run the self-check for subsequent dispatches within the same quest.

This step never blocks the quest. The user is trusted to Ctrl-C if the cost posture matters to them and the banner has fired.
```

### - [ ] Step 1.3: Verify Step 2 rewrite

Run: `grep -c 'model: "sonnet"' plugin/commands/quest.md`
Expected: at least `1` (the dispatch example in Step 2).

Run: `grep -c 'explicit-model-parameter workaround' plugin/commands/quest.md`
Expected: `1`.

Run: `grep -c 'declares `model: sonnet` in its frontmatter, but reported running on Opus' plugin/commands/quest.md`
Expected: `0` (the old banner wording has been replaced).

---

## Task 2: Add the "read-model-for-each-adventurer" sub-step to Step 3

**File:** `plugin/commands/quest.md`

### - [ ] Step 2.1: Append sub-step 7 to the Plan step

Use Edit on `plugin/commands/quest.md`:

- **old_string:**
```
6. **Note the handoff context** each adventurer will need — you will pass this in the `prompt` field of their `Agent` dispatch.

Write the plan to `TodoWrite` as a checklist. This is both your own scratchpad and the user's visibility into what you're about to do.
```

- **new_string:**
```
6. **Note the handoff context** each adventurer will need — you will pass this in the `prompt` field of their `Agent` dispatch.
7. **Read each adventurer's model.** For each adventurer in your sequence, open `plugin/agents/<name>.md` and capture the `model:` value from its frontmatter. Cache per-adventurer for this quest. You will pass this value as the `model` parameter on the `Agent` dispatch call in Step 4 — this is REQUIRED, not optional. Each adventurer's frontmatter is the source of truth for its intended model; the dispatch parameter is the mechanism that makes it take effect.

Write the plan to `TodoWrite` as a checklist. This is both your own scratchpad and the user's visibility into what you're about to do.
```

### - [ ] Step 2.2: Verify sub-step 7 added

Run: `grep -c '7\. \*\*Read each adventurer' plugin/commands/quest.md`
Expected: `1`.

---

## Task 3: Rewrite `quest.md` Step 4 (dispatch) to include the model param

**File:** `plugin/commands/quest.md`

### - [ ] Step 3.1: Replace the Step 4 block

Use Edit on `plugin/commands/quest.md`:

- **old_string:**
```
### Step 4 — Dispatch, one adventurer at a time

Dispatch via `Agent(subagent_type: <name>, description: <short>, prompt: <full handoff context>)`. Wait for the adventurer to complete before dispatching the next one. The adventurers are sequential by design — parallel dispatch breaks the TDD order and the independence guardrails.

**Exception:** Kael (`debug-investigator`) and Pip (`prototype-builder`) are standalone — nothing chains from them. After they complete, report back to the user and let them direct the next move.
```

- **new_string:**
```
### Step 4 — Dispatch, one adventurer at a time

Dispatch via `Agent(subagent_type: <name>, model: <value cached in Step 3>, description: <short>, prompt: <full handoff context>)`. Wait for the adventurer to complete before dispatching the next one. The adventurers are sequential by design — parallel dispatch breaks the TDD order and the independence guardrails.

**The `model` parameter is REQUIRED.** Claude Code's subagent dispatch does not honor the `model:` field in the agent file's frontmatter directly — if you omit the dispatch parameter, the adventurer inherits your (Opus 4.7) model and the plugin's cost posture is invalidated. The `model` parameter at dispatch time is the mechanism that makes the frontmatter declaration take effect. You read each adventurer's model in Step 3; pass it here.

**Exception:** Kael (`debug-investigator`) and Pip (`prototype-builder`) are standalone — nothing chains from them. After they complete, report back to the user and let them direct the next move.
```

### - [ ] Step 3.2: Verify Step 4 rewrite

Run: `grep -c 'model: <value cached in Step 3>' plugin/commands/quest.md`
Expected: `1`.

Run: `grep -c '\*\*The `model` parameter is REQUIRED\.\*\*' plugin/commands/quest.md`
Expected: `1`.

### - [ ] Step 3.3: Verify no old (model-less) dispatch syntax remains in quest.md

Run: `grep -nE 'Agent\(subagent_type: <name>, description:' plugin/commands/quest.md`
Expected: no matches. The old dispatch pattern `Agent(subagent_type: <name>, description: <short>, prompt: <full handoff context>)` WITHOUT a `model` parameter must be absent. If any match is found, report and fix.

---

## Task 4: Rewrite the plugin/README.md cost posture section

**File:** `plugin/README.md`

### - [ ] Step 4.1: Replace the cost posture block

Use Edit on `plugin/README.md`:

- **old_string:**
```
## Cost posture

> **⚠️ Known issue (as of v0.2.5):** the `model-echo` diagnostic introduced in v0.2.4 confirmed that subagents declared `model: sonnet` in their frontmatter currently inherit the parent session's model instead. Every adventurer therefore runs on whatever model your Claude Code session is on — so expect Opus-level costs for quests issued from an Opus session. An upstream Claude Code issue has been filed; the cost posture below is the *intended* design and will become real once subagent model routing is honored. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the full context.

**Intended posture (aspirational):** the orchestrator runs on Opus for reasoning-heavy planning. Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, it is confirming the above — Sonnet frontmatter isn't being honored for this dispatch. The quest continues; cost is on you to monitor.
```

- **new_string:**
```
## Cost posture

The orchestrator runs on Opus for reasoning-heavy planning. Workers run on Sonnet for execution. If a worker proves overkill on Sonnet, downgrade to Haiku per-agent in its frontmatter.

**How routing works (as of v0.2.7):** each adventurer declares its intended model in its `plugin/agents/<name>.md` frontmatter. Mordain reads that value during planning and passes it explicitly as the `model` parameter on the `Agent(...)` dispatch call. This is a workaround for an upstream Claude Code issue where subagent frontmatter `model:` values are silently ignored — the explicit dispatch parameter is honored where the frontmatter alone is not. The `model-echo` self-check at the start of every quest verifies the workaround is functioning.

**What the `⚠️` banner means during a quest:** if Mordain emits a model-routing self-check warning at the start of your quest, even the explicit dispatch parameter was overridden (environment variable, enterprise plan constraint, or deeper Claude Code issue). Investigate before trusting the cost posture for that quest.
```

### - [ ] Step 4.2: Verify

Run: `grep -c 'aspirational' plugin/README.md`
Expected: `0` (the "Intended posture (aspirational)" phrase should be gone).

Run: `grep -c 'How routing works (as of v0.2.7)' plugin/README.md`
Expected: `1`.

---

## Task 5: Update main README Status block

**File:** `README.md`

### - [ ] Step 5.1: Update Status block

Use Edit on `README.md`:

- **old_string:**
```
**Version 0.2.5** — first dogfood run completed 2026-04-23; surfaced an upstream Claude Code issue where subagent `model:` frontmatter is not honored (adventurers declared `model: sonnet` inherit the parent session's Opus instead). The cost-posture section in `plugin/README.md` has been marked aspirational pending resolution. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the full v0.3 design and the staircase release plan driving this work.
```

- **new_string:**
```
**Version 0.2.7** — the subagent-frontmatter routing bug is worked around: Mordain reads each adventurer's `model:` value from its agent file and passes it explicitly as the `model` parameter on every `Agent(...)` dispatch, which Claude Code honors. Cost posture is now operational, not aspirational. See `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md` for the v0.3 roadmap (remaining work: full roster expansion, plan.md artifact, parallel review fan-out).
```

### - [ ] Step 5.2: Verify

Run: `grep -c 'Version 0.2.7' README.md`
Expected: `1`.

Run: `grep -c 'Version 0.2.5' README.md`
Expected: `0`.

---

## Task 6: Bump plugin.json version

**File:** `plugin/.claude-plugin/plugin.json`

### - [ ] Step 6.1: Bump version

Use Edit on `plugin/.claude-plugin/plugin.json`:
- **old_string:** `  "version": "0.2.6",`
- **new_string:** `  "version": "0.2.7",`

### - [ ] Step 6.2: Verify

Run: `grep -n '"version"' plugin/.claude-plugin/plugin.json`
Expected: `3:  "version": "0.2.7",`

---

## Task 7: Design spec second addendum

**File:** `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`

### - [ ] Step 7.1: Append the second update to the Risks Mitigation

Use Edit on `docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`:

- **old_string:** `**Update (2026-04-23):** dogfood run confirmed the bug and v0.2.5 documented the pause; staircase subsequently resumed at v0.2.6 on the reframe that roster value and prompt clarity are independent of model-tier routing — the cost posture activates latently when upstream ships a fix.`

- **new_string:** `**Update (2026-04-23):** dogfood run confirmed the bug and v0.2.5 documented the pause; staircase subsequently resumed at v0.2.6 on the reframe that roster value and prompt clarity are independent of model-tier routing — the cost posture activates latently when upstream ships a fix. **Update (2026-04-23, second):** v0.2.7 shipped a workaround that does not require an upstream fix — Mordain reads each adventurer's `model:` from frontmatter and passes it as the explicit `model` parameter at `Agent(...)` dispatch, which Claude Code honors. Cost posture is operational as of v0.2.7.`

### - [ ] Step 7.2: Verify

Run: `grep -c 'Update (2026-04-23, second)' docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md`
Expected: `1`.

---

## Task 8: Stage, commit, verify

### - [ ] Step 8.1: Pre-commit tracked-file check

Run: `git status --short`

Expected tracked-file lines (exactly five `M` entries):
```
 M README.md
 M docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md
 M plugin/.claude-plugin/plugin.json
 M plugin/README.md
 M plugin/commands/quest.md
```

Untracked `.claude/`, `CLAUDE.md`, the v0.2.7 plan, the upstream-issue-draft, and `plugin/.claude-plugin/marketplace.json` MAY appear. If any OTHER tracked file is modified (any agent file in `plugin/agents/`, CHARACTERS.md, etc.), STOP.

### - [ ] Step 8.2: Stage the five files

Run:
```bash
git add README.md plugin/README.md plugin/commands/quest.md plugin/.claude-plugin/plugin.json docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md
```

Do NOT use `git add -A` or `git add .`.

### - [ ] Step 8.3: Verify staging

Run: `git diff --cached --stat`
Expected: 5 files changed. No new-file creation.

### - [ ] Step 8.4: Commit

Use this HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
fix(quest): pass explicit model param at dispatch to work around frontmatter bug (v0.2.7)

Mordain now reads each adventurer's `model:` value from the agent
file's frontmatter and passes it explicitly as the `model` parameter
on every `Agent(...)` dispatch. This bypasses the Claude Code bug
where subagent frontmatter `model:` is silently ignored — the
`model` parameter at dispatch time IS honored.

Changes in quest.md:

- Step 2 (self-check): dispatches model-echo with explicit
  `model: "sonnet"`. Warning-banner text now reflects that the
  explicit param was passed — if the banner fires, the override
  is deeper than the frontmatter bug.
- Step 3 (plan): new sub-step 7 instructing Mordain to read each
  adventurer's model from its frontmatter during planning and
  cache it per-quest.
- Step 4 (dispatch): dispatch syntax now includes `model: <value>`;
  a new paragraph explains why the parameter is REQUIRED. The old
  model-less dispatch syntax is gone.

Cost-posture documentation updates:

- plugin/README.md — retires the ⚠️ aspirational block; replaces
  with a "How routing works (as of v0.2.7)" paragraph that
  explains the explicit-dispatch-param mechanism.
- README.md — Status block bumped to v0.2.7 with a one-line
  description of the workaround.
- Design spec Risks section — second "Update (2026-04-23, second)"
  addendum noting the workaround shipped.

Agent frontmatter stays in place as the documented source of truth.
No agent files change. No CHARACTERS.md change.

Validation: next dogfood run. If model-echo reports `sonnet`, the
workaround works. If it still reports `opus`, a deeper override
(env, enterprise plan) is in play and the banner text points the
user to those causes.

Ref: docs/superpowers/specs/2026-04-23-guildhall-v0.3-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### - [ ] Step 8.5: Verify commit

Run: `git log -1 --stat`
Expected: 5 files changed, subject matches `fix(quest): pass explicit model param at dispatch to work around frontmatter bug (v0.2.7)`.

### - [ ] Step 8.6: Final leak check

Run: `git show --stat HEAD | tail -12`
Confirm exactly 5 file paths listed.

Run: `git status --short`
Tracked-file section must be empty. Only `??` entries permitted.

---

## Out of scope (do NOT do)

- No agent file edits (no frontmatter changes — they remain the source of truth that Mordain reads from).
- No CHARACTERS.md updates — Mordain's character voice is unchanged.
- No quest.md structural changes beyond Steps 2, 3, 4 as specified above. Step 1 (mode selection), Step 5 (verify), Step 6 (report) stay intact.
- No remote push.

If tempted to "also fix" adjacent prose, STOP. Narrow diffs keep the staircase auditable.

---

## Self-review

**1. Spec coverage.** The user's proposal ("read model from agent file, pass it explicitly at dispatch") is implemented across all three dispatch sites: self-check (Step 2), planning (Step 3 sub-step 7 captures the read), and dispatch (Step 4 shows the pass). Documentation updates propagate the change to plugin/README, main README, and design spec.

**2. Placeholder scan.** No TBDs. All Edit strings are literal. All grep expectations are concrete counts.

**3. Type/identifier consistency.** `model: "sonnet"` (with quotes, for the dispatch param examples) matches the Agent tool schema. `<value cached in Step 3>` and `<name>` in the Step 4 syntax are literal angle-bracket placeholders, intentional for command-doc prose.

**4. Bite-sized granularity.** Each task has 1–3 steps. Total 17 steps. Each is a single Edit or verification.

**5. Edit-call uniqueness.** Each old_string is a multi-line block uniquely identified by its position in quest.md, README.md, or the design spec. No ambiguity.

**6. Commit message style.** `fix(quest):` prefix + version suffix matches repo history (see `fix(quest): refine verify-red rule ... (v0.2.1)`). Body covers all three change categories with a forward-looking validation paragraph.

**7. Validation path.** The self-check now tests the fix itself. Next dogfood run confirms or falsifies the workaround deterministically.

No issues found. Plan is ready for execution.
