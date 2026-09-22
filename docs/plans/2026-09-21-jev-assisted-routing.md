# Jev-assisted subagent model routing

- Date: 2026-09-21
- Status: proposed implementation plan; no routing code or live API calls yet
- Repository: Guildhall
- Baseline: `a26e2aa` (merged onboarding PR #32)
- Planning branch: `codex/jev-routing-plan`

## Outcome

Let Guildhall select a suitable available model for each specialist assignment
using task requirements and measured model profiles. Jev recommends a candidate;
Guildhall validates the recommendation and dispatches through the actual host.
Support native Claude Code and the portable skill in Codex and Claude Code.

The objective is to reduce total execution cost or time while preserving task
quality. “Best” means a model meeting the role's quality requirements within the
user's constraints, not a universal ranking of model names. An explicit user
selection always takes precedence over Jev, subject to host and project limits.

Guildhall owns this first implementation because it owns specialist dispatch.
IDD Specs supply useful requirements and risk context when present. Neither IDD
nor Guildhall becomes dependent on the other, and neither requires Jev for normal
use. Routing standalone IDD workflows is a separate follow-up, after this shared
contract has evidence; existing external IDD agent assignments remain unchanged
in this release.

## Evidence and limits

- The [TypeSafe quickstart](https://docs.typesafe.ai/introduction/quickstart)
  documents a typed `choice` API at `POST https://api.typesafe.ai/v1/systemone`,
  bearer authentication through `TYPESAFE_API_KEY`, and responses containing the
  selected choice, confidence, probabilities, model identity and token usage.
  These are sufficient for a small HTTP client. Confidence is not measured
  downstream coding success.
- [Claude's subagent documentation](https://code.claude.com/docs/en/sub-agents)
  describes per-invocation model selection, frontmatter defaults, environment
  overrides and organization allowlist substitutions. Precedence changes across
  versions; force settings can disable per-call selection. Requested and actual
  models must therefore be recorded separately.
- [Official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
  describes model/effort inheritance and explicit selection, with custom-agent
  settings able to take precedence. The callable interface remains a runtime
  capability. This session exposes fresh-context model/effort overrides; that
  does not establish availability in every Codex app, CLI or account.
- Local Codex is `0.154.0-alpha.6.2`. Its CLI `--model` option selects a process
  model; that option alone is not evidence of per-worker routing.
- Guildhall's native quest currently requires explicit Claude model parameters
  and treats `model-echo` self-report as evidence that an override worked. The
  portable host contract already rejects that inference. Reconcile this as part
  of the implementation: self-report can be diagnostic context, never proof.
- No Jev accuracy, latency, cost savings or live cross-host routing has been
  measured during this planning work. Published examples establish feasibility,
  not a production acceptance result for Guildhall.

## Decisions for the first release

1. **Three modes:** `off` is the default; `shadow` records recommendations but
   uses existing routing; `adaptive` can apply evaluated recommendations. An API
   key by itself does not enable the feature. Shadow also requires opt-in since
   it makes external requests.
2. **Preserve existing defaults:** Claude's role frontmatter and roster remain
   fallback assignments. Codex retains host-configured behavior without an
   approved override. Do not translate Claude aliases into Codex quality tiers.
3. **One optional, bundled helper:** use Python 3.12+ and its standard library,
   consistent with repository tooling. No mandatory TypeSafe SDK, LangChain,
   MCP server, daemon or additional installed skill. Python is a prerequisite
   only for routing; ordinary skill use continues without it. Missing Python
   follows the same fallback contract as missing Jev access.
4. **Model selection only:** Jev does not choose reviewers, change tools, expand
   permissions, rewrite role instructions, select the parent model or alter
   lifecycle gates. Claude's existing prohibition on Fable adventurers remains.
5. **Fixed effort per approved candidate profile:** Jev chooses a candidate ID
   representing an approved model and supported effort configuration. It does
   not independently tune reasoning effort in v1. Record a host-default effort
   honestly when it is not exposed; do not pretend the parent effort survived a
   model change.
6. **Conservative initial activation:** start adaptive routing with bounded
   docs-only and PR-draft assignments after evaluation. Other roles remain
   eligible for shadow analysis. Test author, implementer and consequential
   reviewers require separate role-specific evidence before adaptive activation.
7. **No automatic promotion:** collecting enough examples does not turn on
   adaptive mode. Promotion uses a reviewed evaluation report and explicit
   policy activation. No automatic online learning or profile rewriting.

## Routing contract

```text
Role + bounded task facts + host capabilities + approved policy
                              |
                 Deterministic candidate filtering
                              |
             Jev choice among eligible IDs or “defer”
                              |
             Schema, policy and confidence validation
                              |
           Claude / Codex dispatch with unchanged role
                              |
            Host evidence + normal verification results
```

### Configuration and precedence

Use an optional project policy at `.guildhall/routing.json`, explicitly selected
or enabled by the user. Treat repository configuration as data, not permission
to make external requests or change app settings. Record the policy hash when
activated; a materially changed policy must not silently broaden that consent.
Store only a key environment-variable name, never a credential, in this file.

The versioned policy defines mode, approved host-specific candidate profiles,
role eligibility, baseline behavior, model/effort overrides, evaluation profile
revision, data-sharing mode, timeout and per-quest routing-call limits. Reject
unknown schema versions and invalid fields. Ship examples with placeholders and
`off`; do not pre-approve a universal list of models or speculative prices.

Resolve an explicit per-dispatch user choice first, then an explicit role
override. Validate both against the actual host and constraints; if invalid,
report the conflict rather than quietly substituting Jev's preference. Otherwise
use the current mode and its validated baseline. The precedence contract must
be identical in both host adapters even though their dispatch syntax differs.

### Inputs and eligibility

Create a compact request with role, task category, ambiguity/risk flags, required
capabilities, context-size estimate, baseline, candidate profiles and objective.
Profiles describe observed quality by task class, latency/usage observations,
context/tool compatibility, evaluation provenance and freshness. Unevaluated
profiles can be explored in shadow but cannot justify adaptive changes.

Filter deterministically before calling Jev: user allowlist, actual host model
controls, role qualification, effort compatibility, required tools/context,
configured resource limits and any higher-priority constraints. No eligible
model means a blocked dispatch. One eligible model needs no API call. Discovery
never means probing every model with paid requests; use exposed capabilities and
validated configured candidates, then scheduled evaluation evidence.

Use fixed-category task facts and size buckets by default. Exclude repository
paths, code, diffs, full Specs, transcripts, secrets and user-identifying text.
An optional bounded text-summary mode needs explicit activation and a preview
of the outbound fields. If facts are too sparse, defer to the baseline. Task
text is untrusted input and cannot add candidates or override policy.

For test-author routing, derive facts solely from its permitted Spec/API/test
handoff. Do not use implementation analysis, other workers' solutions or the
parent transcript. The worker receives its original role contract and permitted
handoff, not Jev's routing context or other models' outputs.

### Jev transport and decision handling

The helper consumes bounded JSON on stdin and returns a versioned JSON envelope
on stdout. It does not launch agents or write project files. Build the provider
request internally with one choice question: eligible opaque candidate IDs plus
`defer`. The helper maps a validated ID to the host-specific dispatch settings.
Do not execute or interpret arbitrary provider text as commands or model names.

Read the credential from the process environment without echoing it. Use the
fixed HTTPS TypeSafe endpoint, TLS verification, bounded request/response sizes
and a total deadline; do not forward credentials through redirects or accept an
endpoint from task text. Start with a configurable two-second deadline, one
attempt and no automatic retry. Tune the deadline from observed latency. Stop
making routing calls after a provider failure for the remainder of that quest;
future quests may try again. The orchestrator carries this state explicitly.

Validate the exact question/result type, choice membership, finite numeric
confidence/probabilities and required response fields. Use policy thresholds
calibrated on development tasks and verified on held-out cases; no universal
confidence cutoff is assumed safe.
Malformed output, low confidence, `defer`, timeout, missing key/runtime, transport
failure or exhausted routing budget selects the validated baseline and records
a reason. If that baseline violates a hard constraint or cannot be established,
hold the dispatch. An explicit `off` restores existing behavior; adaptive mode
must not silently bypass a user-configured constraint to keep working.

Pin the router model where TypeSafe supports a stable identifier; verify support
during implementation. If only a moving alias is available, record the returned
version and require reevaluation when it changes before applying recommendations.
Do not infer that a version shown in a response is an accepted request identifier.

### Dispatch, receipts and recovery

Attach the decision to the quest's existing plan: role, input fingerprint,
policy/profile version, host capability snapshot, eligible IDs, baseline,
recommended model, requested model/effort, observed model/effort (or `unknown`),
decision source, fallback reason, router version, latency and available usage.
After completion, add worker identity, outcome, verification evidence and retry
count. Distinguish estimates from measured usage and cost; absent billing data is
unknown. Subscription usage is not automatically equivalent to API dollar cost.

Mordain stays within its plan-only write scope. The helper returns receipts;
it does not create a log directory or mutate the policy. Buffer pre-plan records
until the plan exists. Fast-lane quests that intentionally omit a plan include
their receipt in the final response. Diagnostic calls remain outside adaptive
routing, so the router does not change the probe it is trying to interpret.

Resolve once per worker. Resume/follow-up retains its selected settings when the
host supports them. Recheck capabilities before a new worker, not in the middle
of a mutating dispatch. Never automatically replay an uncertain dispatch.
Model escalation may use an already-authorized retry but cannot create another
retry, reset RED/GREEN gates or relax isolation. Preserve partial edits and
report uncertain execution through the existing recovery contract.

## Host adapters

| Route | Planned behavior | Limit requiring baseline/shadow or a hold |
|---|---|---|
| Native Claude plugin | Explicit `Agent` invocation model from the validated decision; existing role definition and tools preserved | Host ignores/forces/substitutes model; unsupported alias or unavailable metadata |
| Standalone skill in Claude | Fresh native worker with bundled role body and supported per-call selection | Named plugin agents/hooks are absent; do not assume registration from skill installation |
| Codex skill/plugin | Actual exposed worker interface with fresh context and validated model/effort fields | No per-worker override, conflicting custom-agent settings, or no verifiable dispatch evidence |

Capability discovery must distinguish syntax support from a demonstrated applied
override. Record CLI/app version, provider, selection mechanism and observed
precedence. Do not edit `~/.codex`, Claude environment settings or project host
config to manufacture support. A host lacking per-worker control can use shadow
recommendations and retain existing dispatch; a host lacking independent workers
still cannot execute a Guildhall feature quest.

Correct the Claude diagnostic's evidence language in the native command and role.
Use trusted host metadata where available; worker prose is explicitly unverified.
Keep the diagnostic nonblocking for ordinary routing. Adaptive eligibility needs
a validated host configuration and actual model attribution; unobservable hosts
remain shadow-only. If a supposedly verified route later substitutes a model or
loses attribution, preserve the in-flight work, report the mismatch and suspend
further adaptive choices. Do not report that the intended model executed.

For Codex, discover allowed model/effort combinations from the callable interface
and applicable configuration. Use fresh context (`fork_turns: none` where offered)
and provide the complete role contract. A new user-visible task, a nested CLI
process or a permissive agent profile is not a substitute for worker dispatch.

## Implementation slices and file ownership

Each slice gets a reviewable change and its stated checks. First re-read current
main and reconcile any changes since the planning baseline.

| Slice | Owned surfaces and deliverables | Acceptance gate |
|---|---|---|
| 1. Contract and policy | New `docs/model-routing.md`; canonical `plugin/portable/references/routing.md`; routing schema/examples; shared role eligibility and receipt contract | Off/shadow/adaptive, override precedence, failure modes and privacy examples are unambiguous; no changed role gates |
| 2. Shared helper | Canonical `plugin/portable/scripts/route_model.py` and any sibling modules; schema/profile resources under `plugin/portable/`; fake HTTP fixtures and routing tests | Offline tests cover eligibility, transport, strict parsing, deadlines, fallbacks, redaction and no-write behavior |
| 3. Host integration | `plugin/commands/quest.md`, `plugin/agents/model-echo.md`, portable `SKILL.md`, `references/hosts.md` and `references/quest.md`; necessary model claims in `CLAUDE.md` | Every intended dispatch path uses one policy contract; off preserves selections; shadow never alters them; role independence and retry limits hold |
| 4. Distribution | `scripts/build_portable.py`, validators, packaging/install tests and generated `plugin/skills/guildhall-quest/` | Native and skills-copy installs contain an independently runnable helper and resources; no reference reaches back into the source checkout |
| 5. Evaluation | New `scripts/evaluate_routing.py`, synthetic fixtures, reviewed candidate profiles and `docs/reviews/` report | Host attribution demonstrated separately from package validity; quality/latency/usage compared to static and deterministic baselines |
| 6. Rollout and docs | Root and plugin READMEs, contributor guide, relevant character/cost descriptions, release notes and all three manifests | Optional setup/disable instructions work on both hosts; only evaluated role/host combinations can activate; aligned installer-visible version bump |

The portable source is the single maintained runtime implementation. Generate
the complete skill bundle from it; native Claude invokes the same generated
helper through its plugin-local path. Add explicit invocation-path fixtures for
both layouts. Never hand-edit generated output. Existing tier validators should
continue checking static fallback consistency while new checks cover routing
policy consistency. Keep the 19-role inventory; the router is not another agent.

Inspect all model/cost/diagnostic claims in `README.md`, `plugin/README.md`,
`CHARACTERS.md`, `CLAUDE.md`, agent contracts, commands, examples and validators.
Update affected current guidance while preserving historical reports as evidence.
Use the next available minor release, provisionally `0.10.0`, with all three
plugin manifest versions aligned. Planning alone requires no version bump.

## Verification and rollout gates

### Offline correctness

- Exercise off, shadow, adaptive, explicit override and fallback behavior with
  a fake provider. Off makes zero requests; shadow dispatches exactly the baseline.
- Cover rejected candidates, unsupported effort, stale profiles, empty/single
  candidate sets, missing runtime/key, malformed JSON, invalid numbers, unknown
  choice, provider errors, oversized responses and bounded timeout behavior.
- Ensure injected task text cannot widen permissions, candidates or role scope.
  Assert test-author routing inputs and handoffs contain no implementation data.
- Verify receipts distinguish recommendation/request/observation and never log
  keys, raw task content or fabricated billing. Interrupted workers are not
  replayed; routing does not increase the shared retry budget.
- Run the existing build, validators and unittest suite plus `git diff --check`.
  Extend copy-install/source-removal checks for both native layouts and the
  pinned/latest skills installer checks. Use `python3 helper.py` so execution
  does not depend on installer-preserved executable bits.

### Real host observations

Create disposable fixtures with opt-in live execution, using approved existing
credentials and models; never run paid probes in default CI. Record exact client
versions, provider/settings, fixture revision and the limits of exposed telemetry.
Demonstrate at least two distinct applied candidate models on each supported
route, including a changed request, resume behavior and a rejected/forced model.
When a failure mode cannot be reproduced, label simulation separately.

Exercise native Claude, standalone Claude skill and Codex skill/plugin packaging.
For each route compare off, shadow and adaptive; verify fresh test-author context,
unchanged gates and write scopes. If trusted model identity cannot be obtained,
mark adaptive verification blocked for that route and keep its rollout in shadow.
Successful package installation is not successful routing verification.

### Evaluation quality

Build a stratified set of bounded docs, PR drafting, implementation, test-author,
debug and consequential review tasks. Begin with approximately 30–50 independent
fixtures as a pilot, with repeat runs to expose variance. This is an engineering
pilot, not a claim of statistical equivalence for every role.

Partition development and held-out cases before tuning. Run evaluated candidates
on identical isolated starting states for representative cases: a shadow
recommendation alone gives no evidence about how its alternative would perform.
Compare current routing, a simple deterministic task-policy router, and Jev.
Use independent acceptance checks and human review of a sample, including seeded
review defects and held-out correctness tests; model self-grades are insufficient.

Measure verified task success, consequential missed defects, scope violations,
retries, total elapsed time, router overhead, token usage and attributable cost.
Before evaluating the holdout, record the role's pass criteria and allowed quality
margin. Initial docs/PR activation requires zero scope/gate violations, no missed
critical acceptance item, no lower observed acceptance rate than baseline, and
at least a 10% improvement in the chosen measured efficiency objective including
router/retry overhead. Report uncertainty and all excluded/failed runs. Broaden
the sample if results are inconclusive; do not sell pilot results as a guarantee.

Calibrate confidence on development cases only. Freeze the policy, threshold,
profiles and router version for held-out evaluation. A weak or unnecessary Jev
result is valid evidence to retain deterministic routing. New models, changed
aliases, provider versions or host precedence require requalification of affected
profiles; do not silently reuse old savings claims.

### Release progression and rollback

1. Land contract/helper/adapters with `off` as default and offline checks passing.
2. Enable shadow in opted-in projects; collect local receipts and run the pilot.
3. Publish the evaluation report with verified and unsupported host combinations.
4. Enable adaptive only for passing docs/PR task classes in explicitly opted-in
   projects. Expand role by role after equivalent evaluation, not merely because
   the same model worked on documentation.
5. On attribution drift, repeated fallbacks or quality regression, suspend adaptive
   routing for the affected profile. `off` immediately restores existing routing
   for future dispatches; preserve in-flight work and historical receipts.

## Completion criteria

- One optional routing implementation is distributed through both native plugins
  and the complete skills bundle, with no companion-plugin requirement.
- Claude and Codex behavior is documented against actual tested host capabilities;
  unsupported configurations remain usable with existing routing.
- Decisions are reviewable, explicit user choices win, secrets stay out of
  receipts, and all test/review/lifecycle contracts remain intact.
- An evaluation report supports each adaptive configuration offered to users,
  or the release clearly limits that configuration to shadow mode.
- Installers receive an aligned version increment and setup documentation explains
  the optional Python/key requirements, data sent, modes and disable path.

## Implementation-time decisions still requiring evidence

These do not block building the offline contract and helper: the exact candidate
models available to the user's accounts; TypeSafe stable-version pin support and
account limits; trusted per-worker metadata on each host; calibrated confidence
thresholds; observed costs and the appropriate evaluation sample size. Resolve
them through capability inspection and bounded evaluation, record the result,
and retain the baseline when evidence is missing. No credential or paid call is
needed to review this plan.
