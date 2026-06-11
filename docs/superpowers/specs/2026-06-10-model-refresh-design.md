# Guildhall model refresh — design

**Date:** 2026-06-10
**Status:** approved (Jason, 2026-06-10)
**Shape:** four sequential, dogfood-gated PRs. Each PR merges only after a real `/quest` run validates it. One concern per PR — never bundle PR N+1 work into PR N.

## Context

Guildhall v0.4.0 is "tuned for Opus 4.7." Since that tuning:

- **Opus 4.8** is the current Opus — same API surface as 4.7, behaviorally re-tuned.
- **Claude Fable 5** exists as a tier above Opus. The `Agent` dispatch tool now accepts `model: "fable"`. Anthropic's Fable 5 migration guidance warns that prompts written for prior models are often *too prescriptive* and reduce output quality — in direct tension with Guildhall's literal-friendly design philosophy.
- The recent `speed/` PR series moved Tink (`refactorer`) to Haiku in frontmatter only, leaving six other surfaces saying Sonnet — proof that the tier policy has no single source of truth.

Because this repo's code is prompts, a model upgrade is a breaking dependency change, and prompt changes can't be unit-tested. The substitute is bisectable prompt engineering: small sequential PRs, each validated by dogfooding.

## Fixed decisions (do not re-litigate)

- **Tink (`refactorer`) lands on `haiku`** — alias form, per the speed-series intent.
- **Fable spend is Mordain-only.** Mordain runs on the parent session model (the plugin cannot set it); "Fable for Mordain" means tuning `quest.md` for a Fable 5 parent and documenting the recommendation. No adventurer dispatches on `fable`.
- **Adventurer tier ceiling stays Opus** (4.8 after PR 2).
- **All load-bearing gates are preserved:** Mordain's `Write` scope stays plan-files-only; TDD build chain stays strictly sequential; every `Agent(...)` dispatch keeps an explicit `model` parameter in alias form; post-green reviewers stay gated (no new always-ons); no orchestrator-as-subagent.
- **Docs updated in the same PR** as the change they describe. No follow-up doc PRs.
- **Non-goals:** no new adventurers; no tier changes beyond Tink→haiku; no rewrite of adventurer prompts for Fable (they stay tuned for their own tiers).

## PR 1 (v0.4.1) — drift cleanup & tier single source of truth

**Principle established:** agent frontmatter `model:` is the canonical tier source. Every other surface is a mirror, and the validator checks mirrors against frontmatter.

Tink tier drift — all seven surfaces brought to `haiku`:

| Surface | Today |
|---|---|
| `plugin/agents/refactorer.md` frontmatter | `claude-haiku-4-5-20251001` (right tier, wrong form — violates alias-only rule) |
| `plugin/commands/quest.md` roster table | `sonnet` |
| `plugin/README.md` roster table | Sonnet |
| `plugin/CHARACTERS.md` Tink sheet Model row | Sonnet |
| `CLAUDE.md` model-tiers section | Sonnet |
| `plugin/.claude-plugin/plugin.json` description | refactorer grouped under Sonnet |
| root `README.md` | no tier claim, but stale roster counts ("eleven adventurer agents", "12 adventurer/diagnostic definitions" — actual 17 + 1) |

**Validator extension (Tabs, `plugin-validator`):** new check 8 — cross-file tier consistency. For each agent, frontmatter `model:` is truth; compare against the `quest.md` roster table and the `plugin/README.md` roster table (structured tables → mismatch is `error`), and against the `CHARACTERS.md` Model rows, `plugin.json` description grouping, and `CLAUDE.md` tier lists (prose-ish → mismatch is `warn`). Stays mechanical: exact-match on tier aliases, no semantic judgment.

**Routing re-verification:** the frontmatter-ignored workaround was verified 2026-04-23; re-verify on current Claude Code via two `model-echo` dispatches:

1. *No `model` param* → tests whether frontmatter (`sonnet`) is honored now. A report of the parent model (Fable/Opus) means the workaround is still required.
2. *Explicit `model: "haiku"`* (deliberately ≠ frontmatter) → disambiguates: `haiku` = param honored; `sonnet` = frontmatter honored; parent model = neither.

Record results in this doc's appendix and, if behavior changed, file follow-up scope into PR 4 — do not redesign routing inside PR 1.

**Mismatch-check generalization (small reliability fix):** `quest.md` Step 2 warns only when model-echo's reply contains "opus". On a Fable 5 parent, a routing failure reports `fable` and the warning never fires. Generalize to: warn when the reply names any model other than Sonnet; keep the `model: unknown` carve-out. Same generalization in `model-echo.md`'s description if it hardcodes "opus".

## PR 2 (v0.5.0) — re-baseline Opus 4.7 → Opus 4.8

Retarget every "tuned for Opus 4.7" premise, reference, and keyword (`quest.md`, both READMEs, `plugin.json` description + keywords, `CLAUDE.md`). Re-validate the literal-instruction-following premise against 4.8 by dogfooding. No tier moves, no prompt-philosophy changes.

## PR 3 — Fable 5-aware Mordain

`quest.md` tuned for a Fable 5 parent session, per the claude-api skill's `shared/model-migration.md` → Fable 5 behavioral-shift guidance (read it before writing — anti-overplanning, grounded progress claims, trimming over-prescription where Fable infers correctly). Keep every load-bearing gate verbatim in force. Add: Mordain records the parent session model in plan-file frontmatter (quest attribution); document "run `/quest` from a Fable session" in both READMEs. Adventurer prompts untouched.

## PR 4 — capability improvements

Scoped after PRs 1–3 dogfooding. Candidate pool: smarter post-green batching, quest-level token budget awareness, chronicle improvements, anything routing re-verification surfaced. Scope decided then; non-goals above still bind.

**Scope as decided (v0.6.1)** — three items, each from observed friction:

1. **model-echo hardening** — on Haiku it prepended an `$ANTHROPIC_MODEL` explanation, violating its one-line contract (appendix, test B). Two prompt-hardening rounds reduced but did not eliminate Haiku's preamble (each round verifiably changed behavior — confirming agent files ARE read at dispatch time, unlike command content). Resolution: robust parse contract instead — the reply MUST end with the `model:` line, and quest.md Step 2.3 parses that line, ignoring any narration before it. Observed Haiku outputs already satisfy this.
2. **Workaround decision: retain the explicit `model` param, retire the per-quest file reads.** The explicit param stays (older Claude Code in the field; cost posture). But Step 3.9's Glob+Read of every agent file per quest is replaced by reading the quest.md roster table — trustworthy because check 8 (PR 1) validator-enforces it as a mirror of frontmatter. File-read path remains as fallback for table-missing agents. Saves N file-read roundtrips per quest.
3. **Dogfood protocol documented** — command/skill content is snapshotted at session start (observed when the PR 1 gate quest ran a pre-speed-series quest.md), so dogfooding a quest.md change requires a freshly started session. Recorded in CLAUDE.md; agent files are dispatch-time reads and unaffected.

Skipped (no observed friction, YAGNI): post-green batching changes, quest-level token budget awareness, chronicle format changes.

## Validation strategy

Per PR: Tabs (`plugin-validator`) clean on the plugin tree, then a real `/quest` dogfood run (the repo's definition of testing), then merge. Commit style `type(scope): summary (vX.Y.Z)`.

## Appendix — routing re-verification results (2026-06-10)

Parent session model: Fable 5. Agent under test: `model-echo` (frontmatter `model: sonnet`).

| Test | Dispatch | Reported | Conclusion |
|---|---|---|---|
| A | no `model` param | `claude-sonnet-4-6` | Frontmatter **is now honored** — under the old (2026-04-23) behavior this would have inherited the Fable 5 parent. |
| B | explicit `model: "haiku"` | `claude-haiku-4-5-20251001` | Explicit param still works and **overrides frontmatter**. |

The upstream issue that motivated the explicit-param workaround appears fixed in current Claude Code. Per this design's pre-commitment, no routing redesign happens in PR 1: the workaround stays as belt-and-braces (older Claude Code versions in the field still need it). **PR 4 candidate:** decide whether to retire the workaround — which would simplify `quest.md` Steps 2, 3.9, and 4.

Incidental observation: in test B, model-echo (on Haiku) prepended an explanatory line, violating its own "exactly one line" hard rule. Minor; candidate for PR 4 prompt-hardening.
