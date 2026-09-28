# Task-level Jev routing for Codex and Claude

- Status: proposed implementation plan; no personal policies or approvals changed.
- Requested outcome: Jev selects an appropriate model for each specialist
  assignment, beyond fixed role assignments, without requiring a qualification
  study before ordinary use. Support Codex and both Claude routes.
- Assessed source: Guildhall 0.16.0 at `198ae32`. Before implementation, refresh
  onto the merged successor containing global configuration and the setup wizard.
- This plan does not invoke a quest, run worker/model probes, install personally,
  spend a study budget, or activate routing.

## Product outcome

A user runs the wizard once per host, reviews the allowed models, task-routing
preferences, fallback behavior, outgoing data and spending limits, then enables
**Dynamic routing**. For each new specialist assignment, Guildhall describes the
actual work to Jev, validates its choice and dispatches through the host's normal
worker tool. A simple documentation correction and a difficult documentation
reconstruction can select different models even though both use `docs-writer`.

Codex can start using supported per-worker model/effort controls without a matrix
of benchmark runs or proof of provider-served identity. Claude retains its existing
role defaults and explicit dispatch arguments as the fallback layer; Jev can
override defaults for an eligible task. Neither host inherits the other's model
names, tiers, effort options or evidence guarantees.

Dynamic routing means user-approved selection whose quality/savings have not been
established by a benchmark. Qualification remains an optional stronger assurance.
The wizard clearly distinguishes usable routing from proven improvement, without
making users complete a research workflow just to turn routing on.

## Findings motivating the change

1. `route_model.py` currently offers off, shadow and adaptive. Adaptive requires
   every selected profile to pass `qualified(...)`; explicit user/role choices do
   not require that study. This couples permission to select a model with proof
   that a routing strategy outperformed baselines.
2. Setup defaults to execution-observed evidence. The bundled Codex collectors
   establish configuration-level evidence, while served model/effort remain
   unknown. Native Claude can sometimes expose host-reported model identity,
   but requested effort still must not be relabeled as observed effort.
3. `provider_payload(...)` gives every choice the same generic criterion and
   mostly numeric measurements. With unknown measurements and only capability
   counts, Jev has insufficient information to distinguish useful profiles.
   Removing qualification alone would leave that decision-quality problem.
4. The user's saved study report found truncated reference reads in all 12
   Sol/Luna trials. The 8/18 accepted outputs and raw token totals do not establish
   a model ranking or savings. The same report documents successful requested
   configuration/capture accounting, which can be reused within its valid scope.
   Account-wide weekly usage readings cannot isolate study consumption.

The TypeSafe [quickstart](https://docs.typesafe.ai/introduction/quickstart), checked
2026-09-27, documents a text `state`, per-choice descriptive `criteria`, and a
response with choice, confidence and probabilities. This supports richer task
and candidate descriptions through the existing API; it does not establish
Jev's coding-model selection accuracy. Keep the current fixed endpoint and
bounded transport rather than adding another provider or SDK for this change.

The user's private study stays outside the repository. Preserve its original
results and grades; do not recategorize invalid comparisons as qualification.

## 1. Separate operating mode from benchmark assurance

Introduce routing policy/request **schema v5**, retaining v1–v4 behavior unchanged.
Use these user-facing modes and wire semantics:

| UI label | Policy mode | Changes worker model? | Study required? |
|---|---|---|---|
| Off | `off` | Only existing explicit user choices | No |
| Observe recommendations | `shadow` | No; dispatch baseline | No |
| Dynamic routing | `dynamic` (new) | Yes, among approved eligible candidates | No |
| Benchmark-qualified routing | `adaptive` (existing meaning) | Yes, among independently qualified candidates | Yes |

Installation stays off. Once the user requests automatic selection, recommend
Dynamic routing as the ordinary setup path; shadow is optional, not a compulsory
stage. Do not silently reinterpret an existing adaptive policy as unqualified
dynamic routing, auto-enable roles, or reuse its approval for different semantics.

In v5, use an explicit `routing_roles` allowlist for dynamic/qualified selection.
Migration copies the user's selected scope from `adaptive_roles` only after the
wizard reviews it; an empty legacy list is not permission to enable all roles.
All 18 operational specialists remain representable. The parent coordinator,
model-echo and external IDD assignments stay outside Jev routing.

Keep dispatch precedence: explicit per-assignment user selection → explicit role
override → enabled Jev routing → valid baseline. Distinguish an intentional locked
role choice from a default fallback, especially for prior Claude configurations:
importing every existing default as a lock would prevent the desired dynamic use.
The wizard exposes which roles are locked and which Jev may choose for.

## 2. Make activation lightweight and truthful

Dynamic activation needs actual exposed worker controls, valid supported settings,
an eligible fallback, a reviewed policy and user consent to external routing.
It does not need a study report, trial execution, worker trace inventory or
served-model observation. Discover through the actual callable tool and current
host configuration; an unrelated installed CLI is not evidence of desktop controls.

Add a separate `control_basis` record for the current capability/configuration
snapshot, with source and fingerprint. Keep this separate from execution evidence
levels and benchmark qualification. An exposed model argument establishes that a
request can be made; it does not establish which model actually served it.
Allow observation to remain unknown when no stronger host metadata is available.

For a configured inherited baseline whose identity cannot be determined, offer
an explicit supported fallback profile. Do not guess the parent's model or launch
paid workers to discover it. If no valid fallback/control can be established,
explain that specific limitation and retain ordinary/off behavior.

Extend persistent activation with a versioned approval contract binding mode,
role/candidate scope, effective policy hash, host/control fingerprint, catalog
revision and outbound-data contract. Dynamic approval references reviewed control
facts rather than demanding worker-execution evidence hashes. Keep v1 approvals
readable for unchanged legacy modes. Migrating to v5 requires a new reviewed
approval, never fabricated evidence hashes or a boolean that claims qualification.

Policy, host controls or catalog changes invalidate the corresponding approval.
Reordering/formatting unrelated host entries does not. Setup remains offline until
an approved quest asks Jev for a choice. No activation probe, connectivity call,
automatic study or minimum paid-run count is introduced.

## 3. Supply Jev with useful candidate and task information

### Candidate catalog

Add versioned, host-specific catalog records that bind exact supported model and
effort settings to bounded task-relevant descriptors. Maintain the catalog as
canonical portable resources and generate it into both installed skills.
Validate the catalog against current host support during setup; stale or
unsupported entries are not selectable.

Separate three kinds of information:

- **Hard facts:** supported controls, capabilities and known context limits,
  with provenance. Unknown facts cannot satisfy an enforced hard constraint.
- **Routing preferences/priors:** suitable work types, preferred reasoning depth,
  complexity/risk suitability and qualitative efficiency preferences. Label them
  as documented descriptions or user-approved judgments, never measured scores.
- **Observations:** optional role/category/host-scoped outcomes, latency, usage
  and cost. Keep source, sample count, completeness and revision. Missing values
  stay null; no artificial quality score is required for activation.

Use official model documentation and actual host metadata when authoring starter
descriptors. Verify those sources at implementation time; do not invent rankings,
hard-code this conversation's model roster as universal, or translate Claude
aliases into Codex quality tiers. Do not turn a documented price or speed claim
into measured end-to-end task cost. User overrides remain explicit preferences.

Pin the effective reviewed catalog snapshot in the policy/approval. An installed
catalog update proposes a change; it cannot silently expand an approved candidate
set. Aliases retain requested/resolved identities separately when observable.

### Assignment description

Build a small typed routing brief from the worker's permitted handoff: role and
task class, ambiguity, expected reasoning depth, change breadth, risk/consequence,
context demand, required capabilities, expected output and verification needs.
Include why this assignment differs from another task for the same role through
controlled descriptors, not an entire transcript or a second model classification
call. Unknown attributes stay unknown rather than defaulting every task to hard.

For test-author, every routing fact must come from its Spec/API/test handoff;
implementation reads or another worker's solution cannot inform its brief.
Jev chooses a supported model/effort pair, not a different specialist, role
contract, tool set, permission, reviewer roster or retry policy.

### Outbound payload and choices

Retain request-local opaque labels (`p0`, `p1`, …). Send distinct descriptive
criteria for each candidate, derived from a reviewed controlled vocabulary, plus
the bounded task brief. Model names, local IDs, paths, source URLs and evidence
hashes stay local; the request still necessarily identifies the Jev router model.
Do not interpolate arbitrary catalog/repository prose into provider instructions.

Version the enriched categories data contract and show its expanded fields in the
activation preview. The categories path must work with useful descriptors and no
free-text project summary. Retain optional exact-summary approval for users who
want more task detail; global activation does not approve arbitrary future text.
Raw code, diffs, transcripts and secrets remain excluded by default.

The response remains a typed choice among exactly the eligible labels or `defer`.
Preserve response size/shape checks, probability checks and label validation.
Record available confidence without treating it as calibrated coding success.
Do not manufacture an explanation the provider did not return; a local receipt
can instead summarize the supplied task/profile facts and decision rule.

## 4. Host behavior and fallbacks

| Concern | Codex | Native Claude | Standalone Claude skill |
|---|---|---|---|
| Dispatch | Actual worker tool with supported model/effort arguments | Namespaced specialist agent with explicit resolved model | Actual fresh worker tool and bundled role body |
| Baseline | Inherited settings when known, otherwise explicitly selected supported fallback | Existing per-role roster/frontmatter default, subject to user overrides | Configured inherited or explicitly selected fallback; no native agent registration assumed |
| Effort | Pass only supported values; fresh context when an override requires it | Omit unless this actual interface supports effort selection | Discover independently; do not copy Codex effort names |
| Dynamic prerequisite | Callable supported controls and reviewed control/configuration facts | Same; retain native aliases/hooks and honor actual allowlists/forced configuration | Same; native plugin hooks are not assumed |
| Observation | Record configuration evidence where available; served identity may stay unknown | Use trusted transcript metadata when available; effort can remain unknown | Report only what this host exposes |

Native Claude's existing model aliases remain baseline metadata, not mandatory
locks that defeat routing. Preserve its explicit-model convention, agent namespace
resolution, nineteen-definition inventory and current Fable exclusion for workers.
Do not silently broaden parent/worker scope or remove those policies in this work.

Before calling Jev, filter unsupported settings, role/task exclusions, insufficient
known capacity and violations of user constraints. Ensure the chosen baseline
satisfies applicable constraints too. A sole eligible candidate needs no API call;
zero candidates or an invalid explicit choice produces an actionable hold.

Low confidence, defer, missing credentials, timeout, invalid provider response,
budget exhaustion and provider failure use the valid fallback. If it is not valid,
hold; never bypass constraints by dispatching an arbitrary parent model. Preserve
the single-attempt transport and quest-local failure circuit/call budget.

Known forced substitution or unsupported overrides suspend further dynamic choices
for that host/quest and preserve in-flight work. Unknown telemetry alone is not
a dynamic failure: otherwise Codex would return to the study prerequisite through
another path. Losing evidence needed by the stronger qualified mode still follows
its stronger rules. Never replay an uncertain worker automatically.

Dynamic mode records the returned Jev identity but does not borrow a nonexistent
qualification identity. If a moving router alias changes its observed concrete
identity during a quest, suspend further dynamic choices pending review, without
paid version probes. Cross-session history may propose catalog/policy review;
it cannot silently invalidate host evidence or claim a new benchmark result.

## 5. Wizard, normal-work feedback and delivery integrity

Update `plugin/routing-setup/` so both hosts get the same short journey:
discover controls → choose scope/objective/candidates/fallback → review dynamic
mode and outbound fields → save/activate → report effective source. Default to
the selected host and global scope; honor existing project overrides/locks.
No generic “study failed, run another study” branch belongs in normal setup.

Offer benchmark-qualified mode under an advanced option. Preserve completed
study records without regrading, expanding qualification or automatically retrying.
Explain configuration-versus-execution evidence only to the degree needed for
the user's decision, without demanding unfamiliar hashes or JSON editing.

Collect lightweight observations from ordinary already-authorized work: requested
settings, any trusted configuration/execution metadata, tests/review outcomes,
actual retries and complete usage when available. No background duplicate runs,
independent grading model, full-corpus replay or extra retry is authorized by
feedback collection. Initially keep observations as local proposals for reviewed
catalog updates; do not silently self-train, change candidate weights or mutate
approved policy. This avoids a second activation burden on each ordinary receipt.

For subscriptions, raw tokens are a proxy, not interchangeable allowance units
across models. Preserve cache/reasoning accounting and unknown monetary/quota
figures. Never infer a per-task subscription percentage from account-wide readings.
Offer usage-based preferences without promising that a smaller model saves quota.

Fix the input-delivery failure separately from model qualification. Introduce a
shared bounded-handoff procedure for normal worker instructions and optional
study packets. Split required references into bounded identified chunks, track
expected material, and check host-visible truncation/omission before considering
the handoff complete. Use actual output-budget controls, including literal exec
pragmas where applicable; prose requests for more output are not controls.
Source-file hashes prove source integrity, not successful delivery or reading.

When delivery is incomplete, retrieve only missing authorized chunks within the
existing budget or report an input-delivery failure. Worker assertions alone do
not prove delivery. Where the host cannot expose completeness, record unknown
instead of making a guarantee. Mark affected optional study trials invalid for
model comparison before grading/efficiency conclusions. Do not rerun the user's
18-trial matrix to validate this fix: exercise truncation and recovery offline.

## Implementation sequence and ownership

### PR 1 — New policy, approval and control contracts

- Add v5 policy/request schemas, examples and runtime validation in
  `plugin/portable/scripts/route_model.py` and `resources/schemas/`.
- Split hard eligibility, dynamic selection permission and benchmark qualification.
- Extend `routing_config.py` with versioned dynamic approval/control records,
  migration previews and unchanged global/project/source precedence.
- Update preflight in `routing_evidence.py` to distinguish dynamic availability
  from optional qualification capability; no paid discovery.
- Add tests for v1–v4 compatibility, explicit opt-in, approval invalidation,
  missing telemetry with valid controls, unsupported controls and fallback.

Acceptance: v5 can authorize dynamic selection with null qualification; legacy
adaptive still requires its existing qualification. No study/evidence fiction
is needed, and no existing policy activates or changes meaning on upgrade.

### PR 2 — Catalog and meaningful Jev decisions

- Add catalog resources/schema, provenance handling and bounded routing-brief
  fields. Share one canonical implementation across both installed skills.
- Update provider payload/criteria and decision receipts; keep opaque labels,
  changed-data consent, filtering, bounded transport and failure behavior.
- Use fake provider responses conditioned on materially different same-role task
  briefs to verify distinct selection and dispatch; inspect captured outbound
  payloads for distinguishable candidates and excluded data.

Acceptance: Jev is supplied useful role-independent task/candidate distinctions
without prefilled measured quality/savings. Null measurements remain valid in
dynamic mode. Tests prove correct plumbing, not live recommendation accuracy.

### PR 3 — Codex/Claude integration and wizard

- Update native `plugin/commands/quest.md`, portable host/quest/routing references,
  `plugin/routing-setup/` and `CLAUDE.md` together.
- Cover pre-plan consultation, docs fast lane, prototype/debug, sequential build,
  gated review fan-out and PR drafting on all three routes. Retain user/role locks,
  baseline defaults, independence, hooks and original role contracts.
- Update both READMEs, installation/setup guides, role eligibility and changelog.
  Regenerate both skills, align manifests at the next available minor version,
  and extend isolated installer checks.

Acceptance: first-time users can reach Dynamic routing through a single reviewed
setup, on Codex or Claude, with zero study runs. A global entry can be activated
behind a retained project override, and the effective project behavior is clear.

### PR 4 — Delivery integrity and optional evidence workflow

- Add reusable bounded delivery instructions and offline checks/fixtures for
  complete, truncated, omitted and duplicated chunks on each host adapter.
- Update `study_runner.py`, study documentation and records to distinguish input
  failure from model output failure; preserve prior schemas/results truthfully.
- Record ordinary-work feedback with existing usage/receipt tools without
  autonomous retraining, duplicate work or extra paid grading.
- Keep the existing benchmark improvement gate for the advanced qualified label,
  not dynamic enablement. An invalid study remains invalid.

Acceptance: incomplete input cannot silently become a valid performance sample.
The fix is tested offline, and dynamic use does not wait for a benchmark pass.

Sequence PRs 1 → 2 → 3 for the usable feature. Delivery integrity can be developed
independently once shared receipt fields are fixed, and should ship with the
release; repairing study records must not turn studies back into an activation gate.

## Validation and release criteria

Run the full unit suite on Python 3.12 and the current supported interpreter,
native/portable validators, generated-resource checks, skill validation and
whitespace checks. Existing isolated native Codex/Claude installs plus pinned
skills-installer checks must pass with each skill installed independently and
source files removed. Use fake transports and synthetic host records by default.

The behavioral matrix must include:

- Same role/different task selecting different allowed profiles; both Codex and
  Claude retaining the correct fallback when Jev defers.
- All 18 roles on all three routes; parent/diagnostic/external roles excluded.
- Valid model control with unknown served identity; unsupported effort; known
  forced settings; alias/catalog drift; invalid explicit choice and no candidates.
- Null performance facts; stale/unsupported catalog entries; no fabricated model
  ranking; forbidden outgoing fields and malicious catalog/task strings.
- Failed provider, low confidence, timeout, invalid label, exhausted budget,
  resume/retry, revocation and concurrent quests without state reset or replay.
- Legacy policy/approval compatibility, v5 opt-in, locked-role precedence,
  global/project override, opt-out, masked global setup, cancellation and save-off.
- Truncated/missing input classified before comparison; complete bounded recovery
  within the original budget; genuinely unavailable completeness metadata.

No live qualification run is required to ship. An optional live smoke test must
name the host, assignment, candidate scope, external fields and a small explicit
call/token cap in advance; it is a separate user-authorized action. Existing
valid capture evidence can be reused within its scope. Do not manufacture live
verification from mocked choices, instructions or a successful installation.

Done means a user can enable task-level Jev model selection on Codex and Claude
without running a benchmark, with useful decision inputs, preserved existing
defaults/constraints and accurate assurance labels. The wizard and installed
bundles must deliver that experience; merely adding a flag that bypasses
`qualified(...)` is insufficient.
