# Resolve Jev routing issues #34–#37

- Status: approved implementation complete in five stacked PRs; final PR CI/review pending. No live studies run.
- Delivery and verification: [implementation report](../reviews/2026-09-22-routing-issues.md).
- Assessed: 2026-09-22, Guildhall `main` at `f0bb120` (merged PR #33).
- Planning branch: `codex/routing-issue-resolution-plan`.
- Scope: Guildhall native Claude, standalone Claude and Codex routing.
- GitHub inventory: four open Guildhall issues, no open IDD issues; all four
  issue comment threads were empty at assessment time.
- Planning does not invoke an IDD lifecycle or start a Guildhall execution quest.

## Outcome

Users can install everything needed for routing, choose a meaningful efficiency
objective, understand what their host can verify, run a bounded qualification
study, and enable qualified routing for any of Guildhall's 18 specialist roles.
Model-echo stays a diagnostic; the parent coordinator and external IDD agents
remain outside specialist routing. Guildhall and IDD remain independently usable.

## Issue assessment and closure map

| Issue | Assessment against current code | Planned closure |
|---|---|---|
| [#34 Subscription cost](https://github.com/GrillerGeek/guildhall/issues/34) | `objective: usage` and `usage_tokens` already exist in helper/evaluator. Setup, trustworthy measurements and terminology are insufficient. Dollar cost cannot be inferred from subscription tokens. | PR 2: working subscription setup, measured usage accounting and examples, with unknown cost preserved. |
| [#35 Only two roles](https://github.com/GrillerGeek/guildhall/issues/35) | The schema hard-codes docs-writer/pr-author; tests explicitly reject test-author. All 18 operational roles already exist in the role inventory. | PR 5: every specialist is representable and routable when explicitly enabled and qualified, with role contracts intact. |
| [#36 Codex attribution](https://github.com/GrillerGeek/guildhall/issues/36) | One `verified/unknown` field conflates several guarantees; no bundled preflight or supported evidence collector explains qualification. | PR 3: defined evidence guarantees and tested capability diagnosis, plus a supported procedure or precise documented limitation for each actual host. |
| [#37 Pilot findings](https://github.com/GrillerGeek/guildhall/issues/37) | Confirmed missing installed guide/evaluator, no interpreter check, outbound user-chosen IDs, no study harness or development headroom analysis. Alias reevaluation is mentioned generally but concrete resolved-model evidence/detection is absent. | PR 1 covers findings 3/5/6; PR 3 covers finding 4; PR 4 covers findings 1/2. Keep issue open until all six are addressed. |

The native-Claude pilot's 7 live calls, 8 attribution replies and 18 practice
runs are reporter evidence. This assessment did not independently inspect the
raw traces. They support investigating these gaps; they are not held-out
qualification and do not establish that one model is universally best.

## Recommended design decisions

1. **Subscription efficiency means measured usage.** Recommend the existing
   `usage` objective during subscription setup. Keep `cost` for known monetary
   measurements; never silently reinterpret it. Token counts are a documented
   proxy, not a promised conversion to remaining subscription limits.
2. **Separate evidence dimensions.** Record requested settings, host-recorded
   effective configuration and host-reported executed model separately. Track
   effort evidence separately as well; a concrete model ID does not prove effort.
3. **Preserve the strong default; consider a named configuration-based lane.**
   Recommend allowing an explicitly selected, separately qualified
   `configuration_verified` adaptive lane if the actual host exposes reliable
   per-worker/turn configuration and outcome correlation. It qualifies the
   measured host configuration, not a claim about the model served. The existing
   stronger execution-observed requirement remains the default. This is a
   proposed policy change, requiring a recorded design decision and renewed
   activation; implementation must not quietly reinterpret old `verified` data.
   If the investigation cannot establish even configuration evidence, that host
   remains shadow/explicit-choice only with a concrete explanation.
4. **Make all 18 roles eligible, never automatically qualified.** Retain explicit
   role allowlists and independent role/category/profile evidence. Existing
   policies keep their selected roles; an upgrade does not expand activation.
5. **Headroom is a study decision, not a weaker pass gate.** Insufficient measured
   opportunity should stop a study cheaply. Keep the held-out quality and 10%
   objective-improvement gates. Matching quality at lower usage already fits
   the usage objective; do not switch objectives after seeing holdout results.
6. **Opaque transport labels beat name heuristics.** Send request-local labels
   such as `p0`/`p1`, with a local mapping to policy IDs. Avoid trying to enumerate
   every sensitive model name, project name or alias in candidate-ID validation.
7. **Retain Python 3.12+ and enforce it.** Lowering the supported floor requires
   separate compatibility evidence. Normal off-mode quests continue to skip the
   helper entirely.

## PR 1 — Repair the installed package and immediate diagnostics

Priority: first; independent of live-model access. Addresses #37 findings 3/5/6.

- Move the canonical full user guide and evaluator into `plugin/portable/`
  resources, generating complete installed copies under
  `plugin/skills/guildhall-quest/`. Keep the root evaluator CLI as a thin
  compatibility entry point; avoid maintaining two implementations. Preserve
  repository guide URLs with a generated mirror or short linked entry page.
- Point installed README/CHARACTERS/skill links to bundled resources. Audit all
  affected installed routing links, including links inside the guide; intentional
  source-only references need absolute repository URLs. No sparse clone needed.
- Enforce the interpreter floor for helper CLI/API and transport child entry.
  Return a stable actionable unsupported-runtime result before network activity.
  The host adapter follows existing eligible-baseline-or-hold behavior. Preserve
  trusted quest state; an interpreter error cannot reset budget or suspension.
- Rewrite outbound IDs to opaque labels in state and question criteria, validate
  responses against that exact label set, then map locally. Preserve defer,
  request/receipt correlation and selected internal IDs. No model names or raw
  identifying policy IDs leave in categories mode.
- Add installation checks that actually run the installed evaluator demo and
  helper smoke after source removal, and resolve installed documentation links.

Primary ownership: `plugin/portable/references/`, `plugin/portable/scripts/`,
`scripts/build_portable.py`, `scripts/validate_portable.py`,
`scripts/test_install.py`, routing/packaging tests, user docs and manifests.

Acceptance: native and standalone copies contain a usable guide and evaluator;
supported interpreter smoke passes; unsupported interpreter produces no request
and a clear result; candidate IDs containing model/project names never appear in
captured outbound JSON; reordered candidates, singleton and defer still map
correctly. Unknown/stale provider labels are rejected.

## PR 2 — Make subscription usage a complete workflow

Depends on PR 1's installed tooling. Addresses #34 and informs #37's pilot.

- Add subscription and metered-API setup examples. Explain why smaller models
  can consume more total tokens through extra turns, tool calls and retries.
  Offer usage explicitly when monetary measurements are absent; changing an
  objective still changes the policy hash and needs activation.
- Define a versioned normalized usage record with host, worker, turn, response
  and attempt identity, source provenance, measurement basis and completeness.
  Keep host-provided input/output/cache/reasoning components where available.
  Define totals per source adapter: never add cache or reasoning components
  twice when a host total already includes them.
- Deduplicate repeated events and cumulative snapshots; distinguish retries
  that consumed tokens from replayed telemetry. Attribute actual measured work
  across the completed assignment and its retries. Missing data stays null or
  incomplete, never zero.
- Keep Jev service usage/cost separate from the host subscription meter. Report
  both overheads without claiming they consume the same quota. Use measured
  end-to-end latency where available and state exactly what each total covers.
- Introduce per-role/category measurement scope for reusable candidate estimates;
  docs results must not silently become the cost/usage estimate for security or
  implementation tasks. Preserve metric definitions and profile revisions.
- Share normalization with PR 3 collectors and PR 4 studies; retain one explicit
  record contract rather than incompatible per-host evaluator formats.

Acceptance: fixtures for incremental/cumulative usage, duplicate responses,
cache/reasoning overlap, partial records, retries and interrupted turns produce
correct totals or a clear incomplete result. Subscription examples run with
`cost_usd: null`; missing cost cannot accidentally satisfy a monetary ceiling.
Show one synthetic example where a smaller model uses more tokens. No claim of
exact session-limit savings without a documented host meter.

## PR 3 — Host preflight, attribution levels and drift detection

Depends on PR 2's normalized record contract. Addresses #36 and #37 finding 4.

- Add a read-only bundled preflight that identifies the actual executing host,
  client/build, worker tool, supported controls, evidence sources, interpreter,
  available routing modes and specific missing prerequisites. Report desktop and
  standalone CLI identities separately. Do not launch paid probes by default.
- Investigate actual installed-host schemas and supported records, not just a
  public source revision or another CLI's version. The official
  [Codex app-server documentation](https://learn.chatgpt.com/docs/app-server)
  documents version-specific schema generation, usage updates and reroute events.
  That page does not establish exhaustive served-model attribution for the
  user's desktop worker tool. Absence of a reroute event is not proof of identity.
- Add bounded collectors for explicitly supplied, task-owned host records.
  For native Claude, validate the pilot's `message.model`, usage and timestamps
  against sanitized fixtures and the measured client version. Record that as
  host-reported observation, with provenance, rather than independent provider
  attestation. For Codex, expose only what the actual records establish.
- Correlate every relevant response/turn with the dispatched worker. Handle mixed
  models, retries, interruptions, missing events and replay. Evidence must cover
  the assignment, not only its final message. Do not search all user sessions or
  export raw transcripts; keep reviewed evidence local.
- Add explicit evidence requirements to qualification and policy, with separate
  requested/configured/observed model and effort values. Bind evidence to actual
  host build/configuration, scope, profile, objective and expiry.
- Define the configuration-based lane through a short recorded design decision.
  Permit it only when the documented minimum correlation/configuration evidence
  and quality study pass. Clearly label its weaker guarantee in setup, receipts
  and reports. Unknown served identity remains unknown in that lane.
- Record requested aliases and resolved concrete IDs when observed. A changed
  concrete ID or conflicting/missing required evidence invalidates that profile
  for subsequent adaptive selections and requires reevaluation. Detect drift
  through available existing metadata; do not promise a pre-dispatch guarantee
  when the host exposes identity only after execution. Preserve in-flight work.
- If neither supported evidence lane can be established, ship an exact limitation
  and reproducible upstream request describing missing fields, affected build
  and sample schema. Do not require an upstream fix before shipping other work.

Acceptance: native Claude and Codex preflight explain their evidence and available
modes; configuration never becomes observed identity. Tests cover missing,
conflicting and mixed response identities, alias changes, effort unknowns,
duplicate/retried/interrupted/replayed records and no usage double counting.
Shadow, explicit choices, consent, call budgets and circuit state retain their
existing behavior. Old evidence gains no stronger guarantee through migration.

## PR 4 — Reproducible studies and development headroom

Depends on PRs 1–3. Addresses #37 findings 1/2 and supplies #35 qualification.

- Ship a study manifest and record builder first: fixture IDs/hashes, immutable
  development/holdout split, role/category, objective, candidate matrix, strategy
  configuration, repeats, quality rubric, host requirements and usage/time caps.
- Add a bounded runner using available supported worker dispatch. Where a host
  cannot automate dispatch, produce explicit run packets and importable records;
  never silently switch to nested CLIs or a different host to claim support.
- Allocate one owned disposable checkout per mutating run, preserve baseline and
  diff evidence, and resume only known unfinished work. Do not automatically
  replay uncertain dispatch or delete user-owned worktrees.
- Collect paired static/deterministic/Jev measurements and Jev routing overhead.
  Control or record caching, execution order and concurrency; randomize/balance
  order instead of assuming concurrent batches remove measurement bias.
- Build development candidate observations before headroom analysis. Current
  strategy-only records cannot establish which untried candidates are better.
  Return `insufficient_evidence` when coverage/quality/repeats are missing; with
  adequate development coverage, return `no_measured_headroom` when no acceptable
  candidate offers the prespecified gain. State the tested candidate/scope limits;
  do not assert global baseline optimality. Stop before spending on holdout.
- Report per-fixture attainable improvement as well as the best static candidate:
  conditional routing may help even when no single candidate wins every fixture.
  Treat development noise and routing overhead explicitly.
- Add blinded grading packets that hide strategy/model, freeze independent
  grading before joining metadata, and retain boundary checks separate from
  acceptance/critical-miss grading. Preserve test-author context restrictions.
- Keep study diagnostics separate from held-out qualification verdicts.
  Distinguish missing evidence, quality regression and insufficient improvement.
  Freeze objective/threshold before holdout; changing them requires a new study.
  The evaluator still reports `qualification: false` until independent review.

Acceptance: an offline fake-host study exercises creation, interruption/resume,
deduplication, boundary checks, blinded grading and export. Tests cover baseline
already best, conditional-routing headroom, missing candidate measurements,
noisy/insufficient samples, objective changes, split leakage, zero denominators
and existing nonfinite arithmetic defenses. Installed tooling performs the same
workflow without a source checkout. Live study execution requires a separately
selected host/candidate scope and explicit usage budget.

## PR 5 — Extend qualified routing to all specialist roles

Depends on PRs 2–4's stable evidence/qualification contracts. Addresses #35.

- Replace the two-role schema enumeration with the canonical 18-role inventory
  and remove scattered two-role assumptions across native/portable guidance,
  schemas, tests and setup. Keep model-echo excluded and the 19-definition
  inventory intact.
- Qualify by role/category/host/profile/objective and required evidence level.
  Do not infer competence or efficiency from tier names or reuse a docs study for
  a consequential reviewer. Existing explicit allowlists remain unchanged.
- Preserve test-author independence, writer scopes, fresh contexts, reviewer
  membership, lifecycle gates, tool permissions and retry limits for every model.
- Ship synthetic representative fixtures for authoring, implementation, review,
  diagnostics and operations; document how project owners supply appropriate
  acceptance rubrics. Include a matrix showing policy eligibility separately
  from the user's actually qualified roles.

Acceptance: parameterized tests cover all 18 roles through eligibility,
qualification, explicit overrides and fallback; unknown roles and diagnostic
routing fail. Host-route tests prove routing only changes supported model/effort
arguments. No upgrade auto-enables new roles. Live qualification is scoped and
incremental; enabling schema support does not require pretending every model/role
combination has already been measured.

## Compatibility, release and documentation

- PR 1 is a patch-sized installed-package fix; select the next available version
  from current main when publishing. Contract additions in subsequent PRs likely
  warrant a minor release. Increment all three manifests for every shipped
  installer-visible change; do not leave them at 0.10.0.
- Design the strict policy/request/evaluation schema migration before PR 2/3.
  Retain explicit v1 reading for unchanged behavior or return an actionable
  migration requirement. New dimensions belong to a new schema version. Do not
  silently rewrite policy bytes, hashes, activation or qualification meaning.
- Generate bundles from canonical sources. Update root/plugin READMEs, installed
  routing guide, host instructions, contributor guide, changelog and examples in
  the PR that changes behavior. Preserve historical evidence reports.
- Keep off as default and do not install personally, expose keys, activate a
  policy, run paid studies, merge or publish releases as part of this plan.

## Validation and issue handling

Each implementation PR needs focused regression tests plus the full existing
suite, build drift check, native/portable validators and whitespace check.
Packaging changes require isolated native Claude/Codex and pinned/latest skills
installations, byte/mode comparison, source removal and installed-tool execution.
Minimum Python 3.12 and the current supported interpreter must pass; exercise
the unsupported-version path explicitly. Inspect actual GitHub CI after pushing.

Separate offline synthetic checks, sanitized host-record fixture checks and live
observations in reports. Collect genuine failing cases before changing behavior;
update old tests that encode the intentional two-role restriction only when the
new contract is approved. Preserve invariants for consent, fallback, budgets,
unknown measurements, worker independence and non-replay across every PR.

Use issue references in the appropriate PRs. Close #34, #35 and #36 only when
their acceptance gates are met. Track #37's six findings separately in the PR
checklists and close it after the last component. Do not close #36 merely because
an upstream request was drafted; a tested supported procedure or precise tested
unsupported-host explanation must be delivered. Raw pilot claims remain labeled
until underlying evidence is reviewed. No GitHub comments or issue changes were
made during this assessment.

## Suggested execution order

PR 1 → PR 2 → PR 3 → PR 4 → PR 5. Attribution investigation can proceed alongside
the installed-package work, but schema changes should land in that order to
avoid conflicting contracts. Start with the concrete installed-package defects;
do not make those repairs wait for Codex attribution or a paid benchmark.
