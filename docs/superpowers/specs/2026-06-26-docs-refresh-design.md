# Documentation full refresh — design

**Date:** 2026-06-26
**Status:** approved (Jason, 2026-06-26)
**Scope:** Full review and refresh of user-facing documentation. Two headline goals: (1) teach what Guildhall does, how it works, and its overall workflow; (2) position Guildhall against the seven-stage AI-coding flow circulating publicly (Matt Pocock's Grill → Research → Prototype → PRD/Plan → Issues/Tasks → Implement → Review). No code/agent-prompt changes — documentation surfaces only.

## Context

The plugin is at **v0.6.3** but the root `README.md` `## Status` section stops at **v0.4.0 / v0.3.2** — the entire v0.5.x / v0.6.x line is undocumented for users. Separately, a popular framing of "how AI coding works" is circulating as seven labeled stages, and Guildhall maps cleanly onto the back half of that arc while its sibling plugin **IDD-framework** owns the front half. Making that mapping explicit is the primary ask.

Guildhall has five mirror surfaces that CLAUDE.md requires to agree (agent frontmatter is canonical; `quest.md` roster table, `plugin/README.md` table, `CHARACTERS.md` Model rows, and `plugin.json` description are mirrors; `plugin-validator` check 8 enforces this). Any refresh must not introduce drift across these.

## Fixed decisions (from brainstorming)

- **Comparison lives in the root `README.md`** as a new section (not a standalone doc) — single discoverable landing-page home.
- **Position as a pair with IDD-framework.** Tell the full arc honestly: IDD owns Grill/Research/PRD/Tasks; Guildhall owns Prototype/Implement/Review. Complementary pair covering the whole flow.
- **Refresh, not restructure.** No new CHANGELOG file, no reorganization of `plugin/README.md`. Fix drift and staleness in place.
- **Read-only verification before edits.** Fix only confirmed drift; report healthy surfaces rather than rewriting them.

## Deliverable 1 — Workflow-comparison section (root README)

New section titled **"How Guildhall fits the AI coding workflow"**, placed after the intro paragraphs and before `## Installation`. Structure:

1. One paragraph naming the seven-stage arc and crediting Pocock (with a link to his channel / skills repo), framed as "a useful summary of best practices the coding world is converging on."
2. A mapping table (stage # → stage name → the question it answers → where it lives: IDD-framework, Guildhall, or the user's own tooling).
3. A "what's different" paragraph: Pocock's stages are *skills you invoke in order*; Guildhall turns **Implement** and **Review** from single skills into a guild of narrow specialists with independence guardrails — the test author never sees the implementation; "Review" becomes eight role-separated reviewers that fire only on matching triggers. The arc is the same; the discipline is enforced by *who is allowed to do what*.

Mapping (canonical for the table):

| # | Stage | Question | Where it lives |
|---|---|---|---|
| 1 | Grill | How do I brief the AI well? | IDD-framework `/interview` |
| 2 | Research (opt) | How do I stay grounded? | User's sources / either plugin; not a formal Guildhall stage |
| 3 | Prototype (opt) | Test an idea before committing? | Guildhall prototype mode (Pip) |
| 4 | PRD/Plan | How do we reach the right place? | IDD Intentions→Spec; Guildhall plan file (+ optional architecture-reviewer) |
| 5 | Issues/Tasks | How do I break it down? | IDD Expectations; Guildhall Mordain sequences dispatch |
| 6 | Implement | When do I let it run? | Guildhall feature mode — TDD: test-author → feature-implementer → refactorer |
| 7 | Review | Did it get it right? | Guildhall post-green fan-out (8 reviewers) + IDD review gate |

## Deliverable 2 — Status/version refresh (root README)

Replace the `## Status` section (current: v0.4.0 + v0.3.2 paragraphs) with current-state-first prose:

- Lead with **v0.6.3** and what the harness *is now* (17 adventurers + 1 diagnostic, tuned for Opus 4.8, Fable-5-aware orchestration, three-phase dispatch).
- Condense the gap into a single version-history line: v0.5.0 (Opus 4.7→4.8 rebaseline), v0.6.0 (Fable 5-aware Mordain, parent-model attribution), v0.6.1 (roster-table tier resolution + model-echo hardening), v0.6.2 (plugin-namespaced agent dispatch), v0.6.3 (`minimal:` shortcut-marking convention).
- Collapse the verbose v0.4.0 / v0.3.2 paragraphs into history rather than retaining them at full length.

## Deliverable 3 — Drift sweep

Read-only verification of the five mirror surfaces for tier/roster/count agreement, plus `plugin/README.md` staleness check. Fix only confirmed drift. Add a cross-link from `plugin/README.md` to the new workflow section. Report findings (healthy vs. fixed) in the execution summary. Do not restructure `plugin/README.md`.

## Non-goals

- No code or agent-prompt changes.
- No new standalone docs (CHANGELOG, WORKFLOW.md).
- No restructure of `plugin/README.md` or `CHARACTERS.md`.
- No version bump unless the user requests one (docs-only change; version-bump policy is the user's call at commit time).

## Validation

Manual read-through for accuracy against git history and the live agent files. If `plugin-validator` (Tabs) is run, it must stay clean on the plugin tree (the sweep must not introduce mirror drift). No automated tests exist — this repo's "testing" is dogfooding, not applicable to a docs-only change.
