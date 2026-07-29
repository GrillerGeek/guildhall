# Wayfinder vs. IDD + Guildhall: A Comparison

**Date:** 2026-07-28
**Sources examined:**

- [Wayfinder skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder) (Matt Pocock's skills repo) — full `SKILL.md` plus its `agents/openai.yaml` harness shim
- [IDD-framework](https://github.com/grillergeek/idd-framework) v1.5.2 — orchestration skill, agent roster, spec reference
- [Guildhall](https://github.com/grillergeek/guildhall) v0.6.5 — `/quest` command and agent architecture

This comparison treats **IDD + Guildhall as a single paired system** (IDD produces Specs; Guildhall executes them via the documented integration contract) and measures it against wayfinder.

---

## TL;DR

Treated as a pair, IDD + Guildhall is a **strictly larger system** than wayfinder: it covers wayfinder's territory (getting from fuzzy intent to a clear, buildable definition) *and* an entire execution-and-verification phase wayfinder deliberately refuses to enter. The head-to-head is really on the planning half, and there the two embody opposite philosophies: **IDD demands completeness before execution** (the gap-check gate exists to prove a Spec has no holes), while **wayfinder formalizes incompleteness** (the fog of war exists to admit the map has holes and manage them). Wayfinder still wins one regime the pair handles awkwardly — the genuinely foggy, multi-week, multi-person effort where no one can answer an interviewer's questions yet.

## What wayfinder is

A single ~12 KB skill. Given a loose idea too big for one agent session, it charts a **shared map** on the repo's issue tracker: a map issue (Destination / Notes / Decisions so far / Not yet specified / Out of scope) whose child issues are **decision tickets** — questions whose resolution is a decision, not slices of a build. Four ticket types (research, prototype, grilling, task), each tagged human-in-the-loop or agent-driven. Hard rules: plan don't do; one ticket resolved per session; the map is an index, never a store. The effort is done when the way is clear — then it hands off to *something else* to actually build.

## Structural mapping — the pair covers wayfinder almost 1:1

| Wayfinder concept | IDD + Guildhall equivalent |
|---|---|
| Destination | Product → Intentions (`docs/products/`, `docs/intentions/`) |
| Grilling tickets (HITL, the default) | The interview / define-intentions / define-expectations sessions (AskUserQuestion-driven, Haiku-tiered) |
| Prototype tickets (HITL) | Guildhall's `prototype-builder` — but see coverage gaps below |
| Research tickets (AFK, parallel subagents) | No direct equivalent — closest is `debug-investigator`, which is diagnostic, not decision-feeding |
| Task tickets (do work to unblock a decision) | No equivalent — the pair assumes prerequisites exist |
| "The way is clear" (map done) | Spec passes `/gap-check` → status ready |
| — (nothing) | Execution: `/quest`'s TDD chain, 8 gated reviewers, `pr-author` |
| Resolution comments + closed tickets | Execution Reports, validation reports (`docs/reviews/`) |
| Map's Decisions-so-far index | `docs/idd-ledger.yaml` — archived artifacts distilled to records, originals deleted, recoverable via git tags |
| Tracker's native blocking edges / frontier | Artifact status lifecycle + directory globs |

> **Two observations from the mapping:**
>
> 1. **IDD and Guildhall are visibly the same design lineage.** IDD's orchestration skill contains a "CRITICAL: Model Dispatch Rule" that is word-for-word the same workaround as Guildhall's explicit-`model`-param rule, and both tier agents Haiku/Sonnet/Opus by blast-radius (IDD puts `gap-checker` and `tech-lead-reviewer` on Opus exactly as Guildhall does its four irreversible-miss reviewers). The "pair" isn't an accident of compatibility; it's one system published as two plugins, joined by the documented contract that `test-author` reads Expectations and `feature-implementer` obeys Boundaries.
> 2. **Both systems converge on the same memory architecture from opposite directions.** Wayfinder's map-as-index ("a decision lives in exactly one place — its ticket — the map only gists and links") and IDD's archival ledger ("distill to a compact record, delete the YAML, recover via git tag") are the same insight: the always-loaded artifact must stay low-resolution, with detail fetched on demand. That's context-window economics expressed as information design.

## The real philosophical divide

### 1. Completeness: gate vs. fog

IDD's spine is the gap-check — an *adversarial* Opus agent that simulates the implementing agent and blocks execution on ambiguity. The whole pipeline is teleological: every phase exists to make the Spec complete enough to pass that gate. Wayfinder inverts this: "don't chart what you can't yet see," with an explicit test (can you *phrase* the question sharply, even if you can't answer it?) and a graduation mechanism as fog clears. IDD has no formal home for known-unknowns; wayfinder has no formal proof of known-completeness. Each is missing the other's core primitive.

### 2. Where state lives: tracker vs. repo

Wayfinder's map is issues with native blocking edges — the frontier renders *visually in the tracker UI*, assignee-is-claim gives it real concurrent-session semantics, and non-technical stakeholders can watch. The pair's state is YAML and markdown in `docs/` — versioned, greppable, reviewable in a PR, but invisible to anyone not reading the repo, and with no claim mechanism (the pair implicitly assumes one driver at a time). This cuts both ways depending on the tracker in play: wayfinder's tracker abstraction would map onto Azure DevOps work items with parent/child and predecessor links, while the pair's git-native state works identically everywhere.

### 3. Pacing and human involvement

Wayfinder is metered — one decision per session, hard rule — and human-in-the-loop is *constitutive* ("a grilling agent that answers its own questions has broken this"). The pair is throughput-oriented: `quick-spec` collapses three phases into one session, and once a Spec is gated, `/quest` runs largely autonomously to a PR. Wayfinder buys decision quality with calendar time; the pair buys speed with the risk that a one-session interview locked in a premature answer.

### 4. Verification asymmetry — where the pair runs away with it

Post-decision, wayfinder has nothing: a resolution comment and a closed ticket, quality guaranteed only by the human in the loop. The pair verifies at *five* distinct layers:

1. Tech-review and gap-check on the Spec
2. The TDD independence guardrail during build (`test-author` never sees the implementation)
3. Eight gated post-green reviewers, fired in parallel with auditable selection reasons
4. `review-spec` validating output against the original Expectations
5. The archival classify-then-apply manifest

Wayfinder isn't worse at this — it's simply not playing; its scope ends where the fog ends.

### 5. Other differences

| Dimension | Wayfinder | IDD + Guildhall |
|---|---|---|
| Cost engineering | Silent on models | Explicit Haiku/Sonnet/Opus tiering with a mandatory dispatch-time `model` parameter in both plugins |
| Domain | Deliberately domain-agnostic (engineering, course content, "whatever fits the shape") | Software-repo-scoped |
| Harness portability | Multi-harness (Claude Code + Codex via `openai.yaml` shim) | Claude Code plugins |
| Dependencies | An ecosystem — assumes `/grilling`, `/domain-modeling`, `/research`, `/prototype`, and a tracker-setup doc | Two plugins with a documented integration contract |

## Verdict

**For repo-scoped software work, the pair is better, and it isn't close.** It spans idea-to-merged-PR with auditable gates, cost-tiered dispatch, and validation back against original intent, where wayfinder covers only the front third and then hands off to nothing in particular.

**Wayfinder is better in exactly one regime:** the effort so foggy that IDD's entry point fails. `/interview` presumes a stakeholder who can answer questions *now*, in one sitting; `quick-spec` presumes the fog clears in a session. When the honest state is "we'll know what to ask in three weeks, after we've seen the data's shape and reacted to a prototype," wayfinder's fog-of-war, its ticket types (especially Task — do a thing *to unblock a decision*), and its tracker persistence model that reality, and the pair simply doesn't. Wayfinder is also the only one of the three built domain-agnostic and multi-harness.

## The seams worth patching

The pair's weakest point is pre-interview fog and mid-pipeline discovery of unknowns. Two concrete steals from wayfinder:

1. **A wayfinder-style "phase 0"** in front of `/interview` for efforts that can't yet survive an interview, with fog patches graduating into IDD Intentions instead of tickets.
2. **`Not yet specified` / `Out of scope` sections in Guildhall's plan-file template**, so a quest that hits unsharp territory mid-flight has somewhere principled to record it besides `## Open items for the user`. Wayfinder's distinction — in-scope-but-unsharp vs. consciously-ruled-out — is worth preserving exactly.

Conversely, if wayfinder wanted one thing from the pair, it's the gap-check: an adversarial test for "is the way *actually* clear," rather than trusting the vibe of an empty frontier.
