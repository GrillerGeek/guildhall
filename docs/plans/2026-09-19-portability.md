# Guildhall portability assessment and implementation plan

Baseline: main `5286df9231557bdad9dcd356eb057180a1437dfd`, plugin 0.8.1.
The existing checkout remains on `feat/loops-article-improvements`; work occurs
on `codex/portable-guildhall` in an isolated worktree. The nine-check baseline
validator passes: 19 agents, zero errors and warnings.

## Outcome

Make Guildhall installable in Codex and skill-compatible hosts while preserving
Claude's native workflow. Installation support and behavioral certification are
separate. The first portable entry point is one complete `guildhall-quest` skill;
roles are internal references, not nineteen independent skills that could be
mistaken for isolated workers.

## Assessment

| Surface | Current coupling | Required treatment |
|---|---|---|
| `plugin/commands/quest.md` | Claude `Agent`, `TodoWrite`, `AskUserQuestion`, explicit model aliases | Portable quest protocol plus host adapter; main conversation remains orchestrator |
| `plugin/agents/*.md` | Nineteen Claude frontmatters; mostly portable role bodies | Generate bundled role references from canonical files; declare and validate narrow portability substitutions |
| Model routing | Opus/Sonnet/Haiku and introspective model-echo | Preserve Claude native routing; inherit host model by default; only use explicit supported overrides; never infer execution identity from self-report |
| Hooks | Claude event schema, session flag, `Write` matcher | Preserve Claude hooks; explicitly report absent enforcement elsewhere; no OS-sandbox claim |
| Test independence | Test-author may not read implementation; parent reads it when planning | Fresh worker context without inherited parent transcript; minimal verbatim Spec/convention handoff; stop if unavailable |
| Review fan-out | Multiple Claude `Agent` calls; fixed assumed capacity | Independent host workers; batch to real capacity, serialize file conflicts, join all results before closing |
| UI author | Exact Claude Playwright MCP names | Discover actual browser tools; retain existing Playwright configuration prerequisite |
| IDD | Native slash commands and named agents | Resolve installed portable IDD skills; preserve current ready/gap-check/Boundary/lifecycle contract rather than bypassing it |
| Repository guidance | `CLAUDE.md` only | Shared `AGENTS.md` and contributor guide |
| Distribution | Claude manifest and external marketplace | Separate portable/Codex manifests, repository catalogs and complete skill bundle; no external marketplace edit |
| Verification | Nine structural checks, no automated behavior suite | Packaging/resource tests, unchanged Claude-source checks, isolated installs, realistic host observations before certification |

The Claude write guard is a narrow backstop, not a general write sandbox: it
matches `Write`, exempts subagents, fails open on malformed inputs, and resets on
a non-quest prompt. Portability must not present these properties as stronger
than they are or silently promise their enforcement on another host.

## Decisions

1. Follow IDD's distribution pattern; retain MIT licensing and Python stdlib
   contributor tooling. Consumers need no Python just to read/invoke the skill.
2. Keep existing Claude commands/agents/hooks canonical and unchanged initially.
   Portable quest orchestration is an explicit adapter with its own ownership;
   shared role text is deterministically bundled from current agents.
3. Use native host dispatch only when independent worker contexts are available.
   An app with skills but no delegation can inspect/plan; it cannot complete a
   feature quest by impersonating test-author and implementer in one context.
4. Preserve Claude tier routing. Codex and other hosts inherit configured models
   unless the user provides an available host-specific override. Record unknown
   model identity honestly; do not map Haiku/Sonnet/Opus to invented equivalents.
5. Portable role restrictions are instructions and verifiable output scopes,
   not a replacement for host permissions. Missing isolation needed by a task
   must be reported; users are not told that prose enforces file access.
6. Prepare plugin 0.9.0 for the new distribution surface, with every manifest
   synchronized. No release tag or external marketplace change is implicit.

## Implementation sequence and acceptance

1. Shared contributor guidance and this assessment; preserve baseline artifacts.
2. Complete quest skill, host adapter and bundled roles. Cover modes, IDD gates,
   fresh test-author context, numeric RED/GREEN evidence, shared retry budget,
   review triggers, Wren's exploration updates and PR-draft-only closer.
3. Deterministic assembly and consistency/resource tests; reject unknown outputs
   instead of deleting them. Preserve all native Claude agent/command/hook bytes.
4. Native Codex/portable manifests and repository-local Codex/Claude catalogs;
   validate schemas and version agreement. Add copy-install smoke checks with
   source removal and a pinned standalone installer.
5. Review realistic capability/refusal and feature-handoff scenarios. Report
   model/host observations separately from mechanical checks and packaging.
6. Document supported invocation paths and limitations; prepare reviewable local
   commits. Publish or install into personal clients only on user instruction.

## Known content issues to preserve visibly or resolve deliberately

- Native quest Step 4 calls all reviewers read-only, but docs/UI authors write.
  Portable scheduling must reserve named docs/test outputs explicitly.
- The native runbook verification text says reviewer-notes while Rook's contract
  requires a dedicated Runbook section. Portable closer uses Rook's contract.
- Native Wren prohibits judging/rewording unknowns but performs a limited
  sharpness classification. Preserve that limited exception and verbatim text.
- A prompt excerpt must not carry implementation findings into test-author.
- Do not advertise remote install, native alias execution or hook parity from
  a successful local manifest check.

## Follow-up decisions: execution verification, candidate 0.9.1

- Use ordinary persisted Codex session records for behavioral observations. The
  earlier ephemeral prototype run did not expose a complete spawn trace. Preserve
  that limited observation; do not retroactively upgrade it.
- Keep model/authentication configuration inherited. Disposable model runs use
  existing credentials; install-only probes retain separate credential-free homes.
- Fix the portable closing review integration: installed IDD technical review
  requires its main conversation to write Spec annotations, conflicting with
  Mordain's plan-only rule. Use Aldric's bundled post-green, read-only Guildhall
  technical review; formal IDD review remains separate. Native Claude is unchanged.
- Explicitly order technical review before report assembly. The reviewer covers
  underlying evidence and pending orchestration outputs; lifecycle finish then
  verifies the actual saved report and every Deliverable before status review.
- Use labeled synthetic readiness and gap-check inputs only in the disposable
  feature evaluation. Do not claim actual human approval from these test inputs.
- Increment all three manifests to 0.9.1 for installer-visible protocol changes.
  Preserve historical 0.9.0 observations and reports.

- Bundle the standard eleven IDD readiness checks instead of relying on discovery
  of a separate personal installation. Stricter consuming-project rules still apply.
- Clarify portable test-author RED classification: preserve runner failure/error
  counts, accept errors directly witnessing absent promised behavior, reject
  broken setup/unrelated dependency errors, and never inspect implementation to
  guess. Running the suite after authoring is distinct from probing implementation
  before writing tests. Native Claude wording stays unchanged.
