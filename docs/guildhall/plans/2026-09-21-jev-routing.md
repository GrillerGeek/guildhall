# Jev routing implementation quest

- Mode: feature, non-IDD prose specification.
- Status: implementation complete, all reviews PASS; PR #33 created.
- Source specification: [approved implementation plan](../../plans/2026-09-21-jev-assisted-routing.md).
- Human authorization: user requested Guildhall implementation of that plan,
  documentation and a PR. This is not IDD artifact/lifecycle approval.
- Baseline: `c73a887`; main `a26e2aa`, refreshed before execution; clean worktree.
- Host: Codex desktop, native `collaboration.spawn_agent`, fresh context via
  `fork_turns: none`, three workers alongside Mordain. No model/effort overrides;
  observed worker models unknown unless host metadata supplies evidence.
- Isolation: fresh conversations; file-read/write restrictions are instructions,
  not OS-enforced per-role sandboxes. Existing host permissions remain in force.
- Closing review: repository 0.9.1 read-only Guildhall technical review. Installed
  0.9.0's formal-IDD closing instruction is superseded by the previously merged
  portability correction; no personal skill installation is changed.

## Context

Guildhall uses Python 3.12+ standard-library checks, canonical Claude roles and
a generated standalone skill. The approved source plan provides feature scope,
edge cases, acceptance and rollout requirements. This quest records its concrete
public interfaces without creating an IDD hierarchy or claiming ready/done states.
The source plan remains historical and unchanged. Native Claude, portable Claude
and portable Codex are in scope; standalone IDD routing is not.

## Expectations

Implement all six slices of the approved plan: strict optional routing policy,
stdlib helper, host instructions, complete packaging, evaluation tooling and
user documentation with aligned installer-visible version 0.10.0. Off preserves
existing dispatch and makes no API calls. Shadow records recommendations without
changing dispatch. Adaptive applies only qualified approved candidates and obeys
all original role constraints. Invalid explicit choices hold instead of silently
falling back; provider failure uses an eligible baseline or holds.

The implementation must distinguish recommendation, request and observation,
bound external requests, preserve test-author independence and stop repeated
routing calls after provider failure. Credentials and raw task content must not
appear in receipts. No profile ships as live-qualified without real evidence.
The source plan's offline failure cases and rollout evaluation criteria are
incorporated verbatim by reference; the public contract below resolves testable
interfaces before test authoring.

## Boundaries

The following source-plan boundaries apply to every writer. Each writer must
repeat them with its comprehension before modifying its assigned files.

- "Do not translate Claude aliases into Codex quality tiers."
- "Do not execute or interpret arbitrary provider text as commands or model names."
- "Do not edit `~/.codex`, Claude environment settings or project host config to manufacture support."
- "Never automatically replay an uncertain dispatch."
- "Never hand-edit generated output."
- "Keep the 19-role inventory; the router is not another agent."

Comprehension: model options come from the current host and explicit policy;
provider responses remain data; no personal configuration changes; uncertain
workers retain their partial state; generated files come from the builder;
the helper is deterministic orchestration support, not an additional character.
The implementer cannot edit tests. Mordain writes only this plan. Preserve
existing hooks and role contracts except the explicitly owned routing guidance
and model-echo evidence correction.

## Deliverables

- Canonical self-contained routing helper, schemas/examples and routing reference,
  generated into the portable bundle for all supported installation paths.
- Claude/Codex protocol integration, corrected model-identity claims and aligned
  0.10.0 manifests; all role defaults remain valid fallbacks.
- Independent tests, offline evaluation/receipt tooling and packaging verification.
- Root/plugin README discovery, full setup/mode/disable documentation, release
  notes, contributor instructions and honest evaluation report.
- This completed chronicle and a created GitHub PR with validation and limitations.

## Validation

- Automated: independent routing tests; existing unit suite; builder drift check;
  native/portable validators; isolated native and skills copy/source-removal
  probes; offline evaluation; whitespace checks.
- Human/live follow-up: qualified host attribution and Jev effectiveness study.
  `TYPESAFE_API_KEY` is absent (presence-only check). Runtime implementation and
  simulated behavior can be verified; no live success, pricing, quality gain or
  adaptive qualification may be fabricated. Ship off by default and explicitly
  unqualified profiles, consistent with the source plan's shadow-only release gate.

## Public interface contract

Aldric recommended a stateless stdlib helper over a persistent process. Adopted:
the orchestrator carries routing state, applies host dispatch and records later
observations. The helper cannot acquire orchestration or write authority.

### Inputs and outputs

Promised new module: `plugin/portable/scripts/route_model.py` with
`route(request, *, transport=None, now=None) -> dict` and
`policy_hash(policy) -> str`. `now` is an optional Unix-seconds number for tests;
default is current UTC time. Injected transport is `transport(payload, timeout_ms)`
returning a provider response dict. The default transport alone reads the key.
CLI consumes one JSON object on stdin and emits one JSON object on stdout;
exit 0 for dispatch, 2 for hold. No project writes or subprocess worker dispatch.
Imports must work when the single script is loaded with importlib from a copied
bundle. An injected fake transport never requires a real key.

All object fields below are required unless explicitly optional; reject unknown
fields recursively, duplicate JSON keys, nonfinite numbers, booleans as numbers,
and wrong primitive types. Maximum input and provider response: 64 KiB each.
Identifiers are nonempty bounded strings; candidate IDs match `[a-z][a-z0-9_-]{0,31}`
and cannot be `defer`. Hashes are 64 lowercase hex characters. Lists have no
duplicates. Maximum candidates 16, capabilities per list 16, string size 256
characters except explicitly bounded summaries and report/evaluation evidence.

Request keys:

```text
schema_version: 1
policy: policy object below
activation: {policy_hash: hash|null, external_requests: bool,
             summary_preview_hash: hash|null, evidence_hashes: [hash]}
host: {route: claude-native|claude-skill|codex-skill,
       client_version: string, provider: string, worker_tool: string,
       independent_workers: bool, fresh_context: bool,
       model_selection: bool, effort_selection: bool,
       attribution: verified|unknown, configuration_revision: string,
       evidence_hash: hash|null,
       baseline_candidate: candidate ID|null,
       allowed_settings: [{model: string, effort: null|effort}]}
task: {role: Guildhall role except model-echo,
       category: docs|pr|implementation|tests|debug|review|prototype|refactor,
       ambiguity: low|medium|high, risk: low|medium|high,
       required_capabilities: [identifier], context_bucket: small|medium|large,
       summary: string|null}
baseline: {model: string|null, effort: null|effort}
selection: {user_candidate: candidate ID|null, role_candidate: candidate ID|null}
state: {calls_used: integer >= 0, provider_failed: bool, adaptive_suspended: bool}
```

Effort enum: `none|minimal|low|medium|high|xhigh|max|ultra`; actual valid pairs
still require a match in host.allowed_settings. Null means omit the argument,
never evidence of an inherited identity. Context bucket required capacity:
small=4096, medium=32768, large=131072 tokens (conservative upper bounds).

Policy keys:

```text
schema_version: 1
mode: off|shadow|adaptive
router_model: bounded nonempty string (example jev-latest)
key_env: environment variable name (example TYPESAFE_API_KEY; never a value)
timeout_ms: integer 1..10000 (example 2000)
max_calls: integer 0..100 (example 8)
data_mode: categories|summary
objective: latency|usage|cost
min_confidence: number 0..1 (example only, not an asserted safe threshold)
allowed_candidates: [candidate ID]
adaptive_roles: subset of [docs-writer, pr-author] in this release
max_cost_usd: nonnegative number|null
max_latency_ms: nonnegative number|null
candidates: [candidate object below]
```

Candidate keys: `id`, `host` (route enum), `model` (nonempty string), `effort`,
`roles` (nonempty role list), `categories` (nonempty category list),
`capabilities` (identifier list), `context_tokens` (integer 1..10000000),
`quality` (number 0..1|null), `latency_ms` (nonnegative number|null),
`cost_usd` (nonnegative number|null), `usage_tokens` (nonnegative integer|null),
`profile_revision` (string), `qualification` (null or object):

```text
{report_hash: hash, profile_hash: hash, expires_at: positive Unix seconds,
 host_revision: string, router_request: string, router_identity: string,
 roles: nonempty role list, categories: nonempty category list}
```

Qualification is an explicit reference to independently reviewed evidence, not
a boolean claiming truth. Adaptive requires the candidate report_hash AND host
evidence_hash in activation.evidence_hashes, verified host attribution, matching
configuration revision, unexpired scope, matching requested router selector and
matching returned concrete router identity. Qualification.profile_hash is SHA256
of canonical candidate JSON excluding its qualification field, binding model,
effort, metrics, scope and revision to the reviewed profile.
The host adapter must verify the underlying report/records before populating
activation. The helper verifies supplied matching fields, not report truth.
No production candidate ships qualified. Model names/efforts, aliases and router
versions changing require renewed evidence; documentation must state that duty.

`policy_hash` is SHA256 of sorted-key compact UTF-8 JSON (ensure_ascii=False).
Shadow/adaptive require an exact activated hash and external_requests=true.
Category payloads send only enumerated facts, opaque candidate IDs and numeric
profile/capability facts. Never send host versions, paths, model names, evidence
references or full policy. Optional summary is at most 1000 characters; categories
mode rejects non-null summary. Summary mode requires a matching SHA256 of its
exact UTF-8 summary text before any transmission. Summary is the ONLY additional
outbound field in this mode; documentation previews it. Do not return it in a receipt.

Precedence and behavior:

1. Malformed input holds without transport. Valid explicit user/role selection
   takes precedence over mode; require host controls and hard eligibility but not
   adaptive qualification. Invalid explicit selection holds. Fable remains
   forbidden for Claude adventurers, including configured full Fable model IDs.
2. Off: preserve baseline without API use; ordinary adapters skip the helper
   entirely when policy is absent/off, preserving no-Python operation.
3. Activated policy filters hard-eligible profiles by allowed ID, host route/settings, role/category,
   capability/context and resource ceilings. Unknown cost/latency cannot satisfy
   a specified ceiling. Shadow may recommend settings even if model_selection is
   unavailable; it never applies them. Zero eligible candidates holds. A singleton
   needs no network; shadow uses baseline, adaptive still requires qualification.
4. Baseline must match a hard-eligible candidate's exact model/effort. Reject
   duplicate profiles with the same host/model/effort triple. Inherited baseline
   (both arguments null) needs host.baseline_candidate naming a hard-eligible
   profile from trusted host/configuration evidence; retain null dispatch fields
   and unknown observation. Unresolved inherited or ineligible concrete baseline
   holds `baseline_ineligible` whenever a fallback would be required. Null model
   with nonnull baseline effort is invalid in v1.
5. Unqualified adaptive candidates cannot change dispatch. For a singleton,
   expected router identity comes from its reviewed qualification; receipt's
   newly observed router_identity remains null because no call occurred.
   Compute qualified candidates AFTER hard eligibility; adaptive provider choices
   contain only qualified IDs. Unverified host, ineligible adaptive role,
   suspended adaptive state or no qualified candidate yields eligible baseline.
   Applying an override requires host.model_selection; applying nonnull effort
   additionally requires effort_selection. Null effort requires no effort control.
   Candidate settings always exactly match a host.allowed_settings entry.
6. Provider request shape is `{model: policy.router_model, state: JSON string,
   questions: {route: {type: "choice", instructions: string,
   criteria: {candidate_id: string, ..., defer: string}}}}`.
   Question key is `route`, type `choice`; criteria are eligible opaque
   IDs plus `defer`. Request model=policy.router_model; state is a JSON string of
   the allowlisted facts. Validate response `{model, answers: {route:
   {type: choice, choice, confidence, probabilities}}, usage?}`. Probabilities
   cover exactly requested IDs plus defer, finite 0..1, sum to 1 within 1e-6;
   confidence finite 0..1. Usage, if present, has nonnegative integer
   input_tokens/output_tokens. Unknown/malformed answers fall back safely.
7. Missing key, low confidence, defer or exhausted budget returns eligible
   baseline. Increment calls_used once immediately before transport. Transport,
   timeout or provider-parse failure sets provider_failed=true and prevents
   subsequent calls in that quest. Low confidence/defer do not open the circuit.
   No hidden retries. Moving router identity mismatch suspends adaptive mode.
8. Default HTTP transport uses fixed HTTPS endpoint, verified TLS, no credential
   forwarding redirects and a total deadline including body reading. Errors are
   reason codes, never provider exception/body echoes. Enforce outer deadline
   independently of individual socket timeouts, including slow reads/DNS.

Response keys: `schema_version`, `status` (`dispatch|hold`), `source`
(`user_override|role_override|off|baseline|single_candidate|jev`), `reason`
(stable documented code), `dispatch` (settings or null on hold),
`recommended_candidate` (ID|null), `eligible_candidates` (ID list), `receipt`,
and `state` (updated same three fields). Receipt includes input_fingerprint,
policy_hash, profile_revision, host_snapshot, baseline, requested, observed
(`{model: unknown, effort: unknown}` until host observation), router_identity,
latency_ms and usage; no raw content/secrets/errors. Stable tested codes:
`invalid_request`, `invalid_override`, `router_disabled`, `activation_required`,
`no_candidates`, `baseline_ineligible`, `shadow`, `single_candidate`,
`adaptive_unqualified`, `provider_unavailable`, `provider_failed`,
`budget_exhausted`, `low_confidence`, `defer`, `router_changed`, `selected`.
All fields remain present on holds; unavailable receipt values may be null.
Recovery clarification: even when another request field is malformed, preserve
independently valid incoming state exactly in the hold envelope. Correcting an
input must never clear a spent budget, open circuit or adaptive suspension.
When incoming state itself is invalid/missing/unreadable, return a hold with
both provider_failed and adaptive_suspended true; calls_used may be a placeholder
zero, not an observed usage count. The adapter must retain its last trusted quest
state on such rejection, never adopt placeholder state or initialize a new quest
to recover from a malformed packet. Without trusted state, remain held.
Successful explicit selections use reason `selected`. Missing credential uses
`provider_unavailable`; transport/timeout/provider parse errors use `provider_failed`.
Receipt's host_snapshot contains only route, client_version, provider, worker_tool,
configuration_revision and attribution. Its input_fingerprint hashes canonical
JSON of `{task: task without summary, policy_hash: computed hash, host: host_snapshot}`;
it is correlation, not secret anonymization. Nested baseline/requested are settings
objects or null on invalid input/hold. Profile revision is that of the dispatched
candidate when known, otherwise null. Latency is numeric elapsed milliseconds
only if a transport was attempted; usage is null or the provider's validated
input_tokens/output_tokens object. No provider error text appears anywhere.
The default network/TLS/redirect/deadline implementation also requires independent
security/reliability review; tests need not assume an internal HTTP library.

### Offline evaluation contract

Promised `scripts/evaluate_routing.py`: importable `evaluate(payload) -> dict`,
CLI JSON stdin or `--demo` synthetic 32-fixture pilot; no API/model execution.
Payload: `{schema_version:1, synthetic:bool, objective:latency|usage|cost,
records:[record]}`. Record required keys: `fixture_id`, `repeat` (integer >=0),
`split` (development|holdout), `role`, `category`, `strategy`
(static|deterministic|jev), `accepted` (bool), `critical_misses` (integer >=0),
`violations` (integer >=0), `elapsed_ms` (positive number), `retries` (integer >=0),
`usage_tokens` (integer >=0|null), `cost_usd` (nonnegative number|null),
`evidence` (nonempty string list). Invalid/duplicate records must be rejected,
never silently dropped. Every fixture/repeat has matching three strategies and
split/role/category; missing pairs remain visible and block eligibility.

Return `{schema_version:1, synthetic:bool, qualification:false, status:
eligible_for_review|inconclusive|failed, issues:[string], metrics:object}`.
Only held-out records determine acceptance. Report each strategy's acceptance,
critical misses, violations, elapsed time, retries, measured usage/cost; missing
measurements stay null. Compare Jev against BOTH static and deterministic
baselines: no lower observed acceptance, zero critical misses/violations, at
least 10% aggregate objective improvement versus each. Missing evidence, absent
holdout or incomplete strategy pairs is inconclusive, not a pass. Synthetic
results always remain qualification=false, even when arithmetic passes. No
automatic activation or policy edits. This analyzer is not a substitute for the
separate live/independent quality study required by the source specification.

Evaluator details: invalid input raises ValueError from evaluate; CLI returns
exit 2 with a sanitized JSON error. Duplicate identity is
`(fixture_id, repeat, strategy)`; one fixture_id must keep the same split,
role/category across repeats (no development/holdout leakage). Empty evidence
is invalid. An empty/absent holdout is inconclusive.
Metrics shape: `{development_records: int, heldout_records: int, groups: [group]}`.
Each group is `{role, category, status, strategies: {static: stats,
deterministic: stats, jev: stats}, improvement: {static: number|null,
deterministic: number|null}}`; stats has `runs`, `accepted`, `acceptance_rate`
(null if no runs), `critical_misses`, `violations`, `elapsed_ms`, `retries`,
`usage_tokens`, `cost_usd`. Missing any usage/cost value makes that sum null.
Qualification criteria apply independently to each (role, category). Improvement
is `(baseline_total - jev_total) / baseline_total` using objective elapsed_ms,
usage_tokens or cost_usd, only for complete pairs and positive baseline totals.
Zero baseline or unknown objective measurements is inconclusive. Known Jev
critical misses/violations or lower acceptance on comparable pairs yields failed
even if another case is incomplete; otherwise incompleteness yields inconclusive;
complete data missing the 10% objective gate yields failed. Overall status uses
failed before inconclusive before eligible_for_review. No group can compensate
for a different group's quality regression. Demo fixtures use explicit synthetic
evidence labels, development/holdout partitions and at least two task scopes.
Finite observations whose aggregation overflows to nonfinite totals/ratios are
invalid evaluation input: raise ValueError, with the same sanitized CLI exit 2.
They cannot yield eligibility. This numerical validation clarifies the existing
finite-number rule without accepting a weaker evaluation result.

## Dispatch sequence

1. Aldric: pre-plan architectural consultation, read-only.
2. Seraphine: independent tests from this contract and existing test conventions;
   no implementation reads or inherited parent context.
3. Mordain: observe RED, numeric counts and accepted test hashes.
4. Bruga: implementation and generated bundle; accepted tests read-only.
5. Mordain: GREEN, regression and package checks, with one shared build retry.
6. Cassian: documentation; independent reviewers in capacity-limited batches.
7. Aldric: post-green technical review after all relevant writes.
8. Rook: PR draft; Mordain verifies the report, commits, pushes and creates PR as
   explicitly authorized by the user.

## Reviewers selected

- Oriana security: API credential handling, untrusted input and file scope.
- Cassian documentation: always; user explicitly requested feature/setup docs.
- Vance observability: decision receipts, attribution and failure reasons.
- Thalia reliability: HTTP deadlines, failures, retries and dispatch state.
- Cassia performance: bounded payloads and efficiency/evaluation claims.
- Garran operations: optional runtime/key setup, rollout, disable and recovery.
- Tabs plugin validation: generated resources, versions and installation paths.
- Aldric closing technical review: full requirements and evidence coverage.
- Skip Ysolde: no persistence migration. Skip Vera/Lior: no visual UI changes.
- Skip Wren: no Exploration lineage. Tink only if a concrete refactor is needed.

## Decisions

- User-approved prose plan is the non-IDD specification; no invented Product,
  human peer review, YAML gate evidence or lifecycle transitions.
- Use the repository's previously merged 0.9.1 closing-review correction.
- All quest specialists inherit current model/effort settings. This feature is
  not used to route the workers implementing it.
- Tests and offline evidence precede implementation. Live qualification stays
  visibly pending when credentials or trustworthy host telemetry are unavailable.
- Aldric's pre-plan review selected explicit stateless routing state. Its follow-up
  identified inherited-baseline ambiguity, missing profile binding, router alias
  versus identity confusion, effort-control ambiguity and cross-role evaluation
  masking. Resolved in the public contract before accepting tests.
- Native clients available for isolated install probes: Claude Code 2.1.278 and
  Codex CLI 0.154.0-alpha.6.2. Pinned skills 1.5.25 acquired with lifecycle scripts
  disabled in `/tmp/guildhall-jev-skills-pinned`; existing 1.7.0 is available for
  the current compatibility probe. No personal plugins/settings changed.

## Not yet specified

Real candidate profiles, calibrated
thresholds, TypeSafe version pin availability and host qualification need later
observations; placeholder examples cannot authorize adaptive behavior.

## Out of scope

Parent-model routing, review membership changes, additional worker retries,
expanded permissions, external IDD agents, mandatory companion tools, personal
plugin installation, releases/tags and external marketplace edits.

## Verification evidence

### Accepted RED and immutable tests

Mordain independently ran unittest discovery after Seraphine's handoff:
70 tests, 16 passed, 0 assertion failures, 54 errors, exit 1. Causes were
35 missing promised canonical routing module, 17 missing promised evaluator,
and 2 missing promised generated routing helper. These import errors establish
the specified absent deliverables; they are not mislabeled assertion failures.
Bruga's numeric goal: all 54 accepted RED cases pass and all 16 baseline tests
remain passing. Initial build retry budget remains one; no retry consumed.

Accepted SHA256 values (test files are read-only for implementation):

```text
cc8daba52f9f5ea61ce46e2cbdf42a08ed753835b9c76be820bf0fc418658cd6 tests/test_routing.py
0e73b09a5caa312a23150064e471013f1fa9b66def290d12a22738469b885f86 tests/test_routing_evaluation.py
1a2b4372e5fa865f7f69de13df85b6cd537c31278b8c6fe27d611ab9dad33365 tests/test_routing_packaging.py
f4278256ed16688d83d1bf99843be2f047b90c3bc10a031287f6915d16c30e29 tests/fixtures/routing/README.md
```

Seraphine's actual write scope matched her assignment; no implementation reads
were reported and she had a fresh context. Default HTTP internals require the
additional independent security/reliability reviews, not assumptions in tests.

A root black-box boundary probe before implementation handoff found that finite
`1e308` observations could produce infinite sums and an erroneous eligible result.
Seraphine independently encoded the public finite-arithmetic rule in a separate
`tests/test_routing_evaluation_limits.py`, without implementation reads or edits
to accepted tests. Its initial result: 3 tests, 4 assertion failures (subtests),
0 errors; overflow sums/ratios failed to raise ValueError and CLI returned 1
instead of sanitized 2. Hash:
`698f346e30c9bbd384c5c177485c19cfc654a574fb3990bceb872f219b45f3df`.
Bruga's final goal is now 73 passing tests. This supplemental test-first
correction was discovered during the initial implementation, before formal
GREEN acceptance or any post-green review; no completed build retry is consumed.

### Baseline

- Baseline: `python3 -m unittest discover -s tests -v`: 16 passed.
- Baseline build: 26 files, zero drift.
- Baseline native validator: 19 agents, zero errors/warnings.
- Baseline portable validator: passed.
- Baseline file contents and modes preserved by Git commit `c73a887`; no
  pre-existing tracked or untracked edits.

## Open items

All requested implementation, documentation, local automated checks, selected
reviews and PR publication are complete. Live Jev and host qualification remain
an explicit follow-up, not a claim of this release.

## Review findings and correction cycle

- Oriana initial security review: zero findings across 26 runtime/protocol files
  (5,457 lines including generated copies); supplied initial hashes matched.
- Thalia reliability: one medium finding, validation rejection resets otherwise
  valid quest state; one low finding, process launch/final reap may exceed the
  advertised strict wall-clock deadline. No worker replay/retry bypass found in
  the normal paths. Both are being addressed before closure.
- State correction follows a fresh independent regression witness, then a scoped
  implementer repair. Existing accepted tests stay immutable.
- Recovery RED confirmed independently by Mordain: 4 tests, 23 assertion failures
  across subtests, zero errors. New `tests/test_routing_recovery.py` SHA256 is
  `8d9f25b1b83e8a784c795c1310b0f884c5c1a0f4625dde647b8fd6a06afac8b8`.
  Final numeric goal is 77 passing tests; all five previously accepted test/fixture files
  plus this new file remain read-only to the repair writer.
- Deadline decision: retain kill/reap transport isolation. Define timeout as the
  network-attempt watchdog budget including DNS and response reading, with
  elapsed launch time deducted before communicate. OS process creation and final
  reaping cannot have a strict portable wall-clock guarantee; document this
  limitation instead of claiming an absolute bound or leaving an un-reaped
  child to meet an artificial return-time target. Measured receipt latency still
  includes the entire attempt and cleanup. This narrows the guarantee honestly;
  it does not add retries or permit an HTTP child to outlive normal cancellation.

## Initial installation observations

All ten isolated cases passed: native Codex and Claude, plus both hosts through
explicit-bundle and repository-root skills copy installs at pinned 1.5.25 and
current 1.7.0 (current version verified with npm). Exact contents/modes and source
removal were checked. Receipts: `guildhall-install-x0enlquo/report.json` and
`guildhall-install-q6__65a8/report.json` in the host temporary directory. No personal
installations/configuration or model calls. Runtime correction will require a
fresh final package check; these receipts describe the initial GREEN snapshot.

## Initial GREEN and review snapshot

Mordain independently verified 73 tests passed, zero failures/errors (2.034s).
All five accepted test hashes match. Builder: 32 files, zero drift. Native
validator: 19 agents, zero errors/warnings. Portable validator and whitespace
checks passed. Bruga's changed files matched the assigned scope; no hooks,
unrelated roles, tests, user docs or personal settings were modified. No build
retry consumed. Tink skipped: no concrete refactor needed.

Review baseline is `c73a887` plus ALL working-tree changes/untracked files listed
below. All are quest changes; the initial worktree was clean. Canonical/generated
pairs share hashes. Documentation writers have disjoint named scopes; later
relevant runtime changes require re-review.

| File | SHA256 at initial GREEN |
|---|---|
| `plugin/.claude-plugin/plugin.json` | `5fe7b99e50151cfb9412ab16593e5e4ce8814bae9cd1c79bb212904b45276247` |
| `plugin/.codex-plugin/plugin.json` | `2ab09207b46d9fbfdd35e62ad1d96a99465cbdd226fd8202d0f4e32098857f79` |
| `plugin/agents/model-echo.md` | `774f61b1ea9988ce139e8f83f100a75560be421ede4bd2095499871d08c02de8` |
| `plugin/commands/quest.md` | `325b79c39540ab02339021ddf83ad7247068dd6943520cf7bf1e6547a46bd516` |
| `plugin/plugin.json` | `fcfb7c3661ae2518af273ed58f79e6009a354a03bf35fe4535b7a03177406831` |
| `plugin/portable/SKILL.md` | `9d43e72c4afd544f98eef540168db47ad2f3155033fd8a66e7e6c34201083bda` |
| `plugin/portable/references/hosts.md` | `686f35c5c2b26e72a34e9c590db0ad8be7c3d9354d7be0b96d3722a23757a900` |
| `plugin/portable/references/quest.md` | `4ad83e4b4e68de16586797ce99b3d0e5e8db6150776241c8f59bf0f8abb3a4b2` |
| `plugin/portable/references/routing.md` | `eac922a2544c20adbfc0660721d9ce4ea976e0dc4ce815c91edbd0dd2ad9faf0` |
| `plugin/portable/resources/examples/off-policy.json` | `1ac42f94b246b18d03db3d80b51df11ea134d2d29a25ab266b09c4a6ec12eaf5` |
| `plugin/portable/resources/examples/off-request.json` | `725d6a4bb60e9f456a5f65bf63376527b0dcd271f1411bfe4978a7d5c76a5cad` |
| `plugin/portable/resources/schemas/policy.schema.json` | `abca15413783db768431208149d1dff4bd83c26270fe069b83b10eb08d84c27c` |
| `plugin/portable/resources/schemas/request.schema.json` | `26b644d055677b53e7c7cd9b8bd850950351616e45e8faf73919c9ed5705a4e9` |
| `plugin/portable/scripts/route_model.py` | `fa79e3304d778f1467e43ce805e0891a0fb2d8638badf63dba48f86174e51ca5` |
| `plugin/skills/guildhall-quest/SKILL.md` | `9d43e72c4afd544f98eef540168db47ad2f3155033fd8a66e7e6c34201083bda` |
| `plugin/skills/guildhall-quest/references/hosts.md` | `686f35c5c2b26e72a34e9c590db0ad8be7c3d9354d7be0b96d3722a23757a900` |
| `plugin/skills/guildhall-quest/references/quest.md` | `4ad83e4b4e68de16586797ce99b3d0e5e8db6150776241c8f59bf0f8abb3a4b2` |
| `plugin/skills/guildhall-quest/references/roles/model-echo.md` | `264286082a399bc4f196d0fb79be0b4836460d3d547671290c02aeffada8076f` |
| `plugin/skills/guildhall-quest/references/routing.md` | `eac922a2544c20adbfc0660721d9ce4ea976e0dc4ce815c91edbd0dd2ad9faf0` |
| `plugin/skills/guildhall-quest/resources/examples/off-policy.json` | `1ac42f94b246b18d03db3d80b51df11ea134d2d29a25ab266b09c4a6ec12eaf5` |
| `plugin/skills/guildhall-quest/resources/examples/off-request.json` | `725d6a4bb60e9f456a5f65bf63376527b0dcd271f1411bfe4978a7d5c76a5cad` |
| `plugin/skills/guildhall-quest/resources/schemas/policy.schema.json` | `abca15413783db768431208149d1dff4bd83c26270fe069b83b10eb08d84c27c` |
| `plugin/skills/guildhall-quest/resources/schemas/request.schema.json` | `26b644d055677b53e7c7cd9b8bd850950351616e45e8faf73919c9ed5705a4e9` |
| `plugin/skills/guildhall-quest/scripts/route_model.py` | `fa79e3304d778f1467e43ce805e0891a0fb2d8638badf63dba48f86174e51ca5` |
| `scripts/evaluate_routing.py` | `6fdf85e179a68f95f9bc7efde3d66ff1e8e84f2374af1ba180f255267d48c403` |
| `scripts/validate_portable.py` | `9f91294dbcaa153008e82337b8edebb9150cc56c81d6f6943bf76cb917a491ce` |
| `tests/fixtures/routing/README.md` | `f4278256ed16688d83d1bf99843be2f047b90c3bc10a031287f6915d16c30e29` |
| `tests/test_routing.py` | `cc8daba52f9f5ea61ce46e2cbdf42a08ed753835b9c76be820bf0fc418658cd6` |
| `tests/test_routing_evaluation.py` | `0e73b09a5caa312a23150064e471013f1fa9b66def290d12a22738469b885f86` |
| `tests/test_routing_evaluation_limits.py` | `698f346e30c9bbd384c5c177485c19cfc654a574fb3990bceb872f219b45f3df` |
| `tests/test_routing_packaging.py` | `1a2b4372e5fa865f7f69de13df85b6cd537c31278b8c6fe27d611ab9dad33365` |

## Lessons

Independent recovery and numeric-edge review exposed two real bugs beyond the
initial happy-path tests. Both gained independent regression witnesses before
repair. Native model-echo self-report had been overstated as attribution; this
release corrects those claims across current guidance without rewriting history.

## Post-correction GREEN and documentation snapshot

Mordain independently verified 77 tests passed (1.845s), zero failures/errors;
32-file bundle with zero drift, native 19-agent validator with zero findings,
portable validator and whitespace checks all passed. All accepted tests retain
their recorded hashes. Oriana re-reviewed the repair and current privacy docs:
zero findings. Thalia re-reviewed both findings: resolved, zero remaining.

Cassian wrote exactly nine assigned documentation surfaces. They cover optional
setup, installed examples, all modes, independent use, consent/data, recovery,
watchdog limits, evidence qualification and rollback. Final evidence report
updates remain pending the remaining reviews and refreshed install receipts.

The table below replaces changed hashes in the initial GREEN snapshot and adds
all new files. Together the tables cover the complete current change set versus
`c73a887`, excluding only this evolving orchestration plan.

| Changed/new file | SHA256 after repair and docs |
|---|---|
| `CHANGELOG.md` | `35d15b0bfdc9914ab6e08c778dcc24a29783287c9f0e1c70b0f6b2142ff9068a` |
| `CLAUDE.md` | `c29ec57b3978e8307f96d90362216d59d25c9adf485a6709191aa35be2eb701d` |
| `README.md` | `b3ec4c40c673bf3e06cd766be10f0f55f28d75f1d30b0cebf24daf01e585cbb0` |
| `docs/contributing-agents.md` | `7bb314999c65e52e48cf459383e33db15f056545874f40fc896c12f6a355aef6` |
| `docs/installation.md` | `dd4c741c3e271347f1e2994706688c06200fd7603876c5f63538710b86d2eee7` |
| `docs/model-routing.md` | `0fb46d0c74c420e45d2767d44c12615d4f0cd07793b2775588a1e1beac7ae893` |
| `docs/reviews/2026-09-21-jev-routing.md` | `7f99bcac8b00f6af09a2f676950380864ab93f8112fefdb84c9b6308ab5f46b6` |
| `plugin/CHARACTERS.md` | `219f38225f4c9f00df922bd911b6af0bc4346727b757978e767f1fa80bcc9ed8` |
| `plugin/README.md` | `03fa4c9825f9e70806db0910e86c5851850dfb04253ebad517249de6ae0f0d28` |
| `plugin/portable/references/routing.md` | `a39b1aa51ae18bcb40c935e5f35728629f8d1558f29e7a265f03f139617255f7` |
| `plugin/portable/scripts/route_model.py` | `e7e78107da835c29b2df4af5a9e05506bbd3703cf19b5c0fa75bef3615adc9e2` |
| `plugin/skills/guildhall-quest/references/routing.md` | `a39b1aa51ae18bcb40c935e5f35728629f8d1558f29e7a265f03f139617255f7` |
| `plugin/skills/guildhall-quest/scripts/route_model.py` | `e7e78107da835c29b2df4af5a9e05506bbd3703cf19b5c0fa75bef3615adc9e2` |
| `tests/test_routing_recovery.py` | `8d9f25b1b83e8a784c795c1310b0f884c5c1a0f4625dde647b8fd6a06afac8b8` |

## Final installation and specialist review evidence

The corrected snapshot passed all ten isolated installation cases. Native Codex
and Claude plus skills 1.5.25 explicit-bundle/repository discovery for both hosts
are recorded in `/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-07f2eb3o/report.json`.
The four equivalent skills 1.7.0 cases are recorded in the sibling
`guildhall-install-wa7c8035/report.json`. These are local ephemeral receipts;
this committed chronicle preserves their outcomes. Exact copied bytes/modes and
source removal passed. Personal installations/settings remain unchanged.

The documented off-request smoke ran from the isolated installed native Codex
0.10.0 bundle under Python 3.12.2: exit 0, dispatch with null model/effort,
`router_disabled`, calls_used 0 and observed identity unknown. It made no provider
call and does not qualify live routing. Local Markdown file links in all nine
authored documentation surfaces resolved.

Oriana (security), Thalia (reliability re-review), Vance (observability) and Cassia
(performance) each report zero high/medium/low/informational findings. They
performed static analysis, not independent test execution. Garran reports no
operational blocker for off-by-default, unqualified release. Tabs structural
review and Aldric closing technical review remain pending at this entry.

## Garran operational runbook

The following is Garran's verbatim handoff. His final installation question was
answered by the refreshed receipts above, obtained after his review handoff.

### Deploy plan

- Ship 0.10.0 with routing off and profiles unqualified. No operational blocker found for that scope. Record refreshed installation results and completed reviews before treating the corrected package as verified.
- Update through the existing installation route in `docs/installation.md`, then restart the host. Use one Guildhall entry point per quest. No migration or external marketplace update is required.
- Before optional activation, prepare `.guildhall/routing.json` outside quest execution. Replace example placeholders with supported host profiles and establish an eligible baseline. Enabled routing requires Python 3.12+; external requests require `TYPESAFE_API_KEY` in the process launching the host. Check credential presence without printing its value.
- Start with explicitly approved shadow mode. Approval binds the exact policy hash, candidate scope, objective and outbound fields; summary mode additionally needs approval of the exact summary. A file or key alone is not activation.
- Run the installed bundle’s off-request smoke command from `docs/model-routing.md`. Expect exit 0, `router_disabled`, zero calls and unknown observed identity. This establishes helper availability, not live provider or host qualification.
- Keep adaptive promotion blocked until independently reviewed live evidence qualifies the specific host/profile/role/category. Only `docs-writer` and `pr-author` are eligible for adaptive routing.

### What to watch (first hour)

- Inspect decision receipts in the quest plan, or final response for a no-plan fast lane. Shadow dispatch must retain baseline settings; recommendations and observations must remain separately recorded.
- Investigate any hold: CLI exit 2, `invalid_request`, `invalid_override`, `activation_required`, `no_candidates` or `baseline_ineligible`. Stop dispatch and correct the reported prerequisite.
- After `provider_failed`, verify subsequent decisions make no further provider calls for that quest. `calls_used` must carry forward through retries, resumes and policy edits.
- Watch receipt latency and call count against the approved policy. The example uses 2,000 ms and eight calls; OS launch/reaping can exceed the watchdog budget. Exit 0 alone does not establish provider success: eligible fallback also exits 0.
- Preserve unknown model/effort and billing values when evidence is absent. Trusted substitution, lost attribution or `router_changed` must suspend subsequent adaptive choices while preserving existing workers.

### Rollback plan

- Explicitly select routing off before the next worker dispatch, or remove the optional policy through an authorized setup action. Future dispatch returns to ordinary host behavior without routing calls.
- Preserve in-flight workers, partial changes and receipts. Do not cancel, reassign or automatically replay an uncertain dispatch.
- If the package itself prevents ordinary operation, restore the previously verified 0.9.1 bundle through the same installation route and restart the host. Avoid installing a second route alongside it. Preserve project work separately from plugin replacement.
- No schema migration or router-owned data fixup is required. Review worker-produced changes individually; disabling routing does not undo them.

### On-call notes

- Start with `docs/model-routing.md` and the installed `references/routing.md`. The helper only returns decisions; the coordinator invokes workers and retains quest state.
- A missing key/runtime permits an eligible baseline or holds. GUI hosts may not inherit terminal environment variables. Do not expose credentials while investigating.
- Singleton choices can avoid provider calls. `defer`, `low_confidence`, budget exhaustion and unavailable qualification can legitimately retain baseline dispatch.
- Invalid requests preserve valid incoming state. Missing/unreadable state returns a closed placeholder; its zero count is not a replenished budget. Retain the last trusted state or stop for an explicit recovery decision.
- Model-echo is diagnostic context, not execution attribution. The offline evaluator always returns `qualification: false`; synthetic results authorize no promotion.

### Open ops questions

- Live Jev compatibility, host attribution, calibrated thresholds, router version behavior and measured quality/cost/latency remain unverified. Who owns obtaining and independently reviewing that evidence before adaptive promotion?
- No routing dashboard, alert integration or SLO is supplied. Initial operation relies on receipt inspection; the activating operator must own that review.
- Final corrected-snapshot installation receipts were pending at review handoff. Record their outcome in the release verification report before closing verification.

## Structural review and final evidence report

Tabs completed all nine structural categories. Three manifests agree at 0.10.0;
19 role frontmatters, aliases, tools, examples, scalars and tier mirrors pass.
32 generated files and all 11 canonical portable copies match. Resource paths,
JSON resources, modes and catalogs pass. Tabs independently ran the native
validator: 19 agents, zero errors/warnings.

Tabs reports two mandatory broad-pattern secret errors, both literal credential
prefix examples in the existing plugin-validator checklist and its generated
copy (`plugin/agents/plugin-validator.md:43` and generated role line 32). Mordain
dismisses these as confirmed documentation false positives: no credential value,
no new secret, no fix needed. Nine informational lines are clean checklist
confirmations, not unresolved findings. Zero actionable structural findings.

Cassian finalized the verification report with corrected 77-test results, all
ten installation cases, installed smoke and known live-evidence limits. SHA256:
`39f4bae64523d58ff30314786df886b08cb5db8eb984a0f0d084610ac639152a`.
This supersedes the report hash in the earlier snapshot. Runtime, adapters,
tests and other documentation have not changed since their final review.

## Closing technical review — PASS

Aldric completed the read-only post-green review of the full approved prose
specification, current quest contract/history, tracked and untracked changes,
implementation, tests, documentation and supplied reviewer results. All 41
implementation/evidence files matched the combined SHA256 snapshot, with no
missing files or mismatches. No findings or unresolved technical corrections.
This PASS applies to the off-by-default, unqualified 0.10.0 candidate; it does
not assert live qualification, human approval or an IDD lifecycle transition.

| Coverage | Evidence and conclusion |
|---|---|
| Strict policy/interface | Runtime schemas, exact fields/types, hashes, duplicates, ranges, finite numbers and bounded input covered by independent tests. |
| Off/shadow/precedence | All three host routes, zero-call off, user-before-role override, invalid override holds, unsupported controls, null effort and baseline-preserving shadow covered. |
| Eligibility/baseline | Allowlist, host/settings, role/category, capabilities/context, ceilings including unknowns, empty/singleton sets and Claude Fable exclusion covered. Inherited baseline requires evidence while retaining null arguments. |
| Adaptive | Evidence/profile hashes, expiry, host revision, scope, attribution, router selector, suspension and docs/PR restriction covered. Unqualified fallback and changed router identity covered. |
| Provider/transport | Typed opaque choices, defer, response/usage/probability validation, missing key, timeout/error, confidence/budget/circuit behavior covered. Fixed TLS endpoint, no redirects/proxies/key argv, bounded child and honest OS timing limitation inspected. |
| Privacy/receipts | Agreed categories/numeric facts, exact summary approval, redaction, recommendation/request/observation separation and unknown billing covered. |
| Recovery/independence | Four independent regression tests; valid-state preservation and closed invalid-state holds. Adapter maintains serial state, role/test independence, retry limits and uncertain-dispatch non-replay. |
| Evaluation | Both baselines, exact 10% threshold, paired holdouts/repeats, per-scope quality, missing measurements, leakage/duplicates, zero denominators and overflow covered. qualification remains false. |
| Host integration | Native/portable worker paths share the contract; trusted observation required; hooks, gates, reviewers and external IDD assignments preserved. |
| Boundaries | All six pass: no alias translation, provider text execution, personal configuration edits, worker replay, generated hand edits or new role. Accepted test hashes preserved. |
| Deliverables | Canonical/generated helper/resources, host integration, three 0.10.0 manifests, independent tests/evaluator, comprehensive user/contributor/release/evidence documentation complete. |
| Automated checks | Final Python 3.12.2 run: 77 tests in 1.907s, zero failures/errors; 32 generated files zero drift; native 19-agent validator zero errors/warnings; portable and whitespace checks pass. |
| Installation/demo | Ten isolated native/skills installations and source-removal checks pass; installed off smoke passes. Demo has 32 synthetic fixtures, two repeats, three strategies, 48 development/144 holdout records; no live claims. |
| Independent reviews | Security, reliability, observability, performance, operations and structural reviews completed; two literal-prefix false positives dismissed with evidence. |

Aldric inspected both final installation receipts independently. Test and smoke
execution are coordinator evidence, not claimed reviewer reruns. Final chronicle
and PR were expressly pending orchestration outputs at review time. This entry
records the review result; publication is the remaining authorized action.

Live Jev compatibility, stable router selectors, trusted host attribution,
confidence calibration and real quality/cost/latency comparisons remain follow-up.
The activating operator owns obtaining and independently reviewing that evidence
before adaptive promotion. Observed worker models remain unknown without trusted
host metadata. Any subsequent relevant implementation/evidence change requires
re-review. No such change occurred after this PASS.

## Publication and final deliverable verification

Rook drafted the PR title/body from the full reviewed branch, carrying Garran's
runbook verbatim and clearly distinguishing offline evidence from live follow-up.
Mordain verified the saved documentation, complete 41-file implementation/evidence
snapshot, plan coverage and all deliverables before publication. No relevant
implementation/evidence bytes changed after Aldric's PASS; this final plan entry
is the permitted closing orchestration output.

Implementation commit: `271b854` (`feat: add optional Jev-assisted routing for
Claude and Codex`). The prior `c73a887` planning commit is included. Mordain pushed
`codex/jev-routing-plan` and created [GitHub PR #33](https://github.com/GrillerGeek/guildhall/pull/33)
against `main`, as explicitly requested. Publication uses Rook's draft with its
create-PR instruction/footer and pending-publication quote removed now that the
PR exists; the operational runbook remains verbatim. GitHub check results live
on that PR; local verification is recorded above.

All requested outputs exist. No merge, release, tag, personal installation or
external marketplace change was performed. Standalone IDD routing, live Jev
compatibility and adaptive qualification remain the documented next phase.
