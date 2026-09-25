# Optional model routing

Routing is off by default. An absent policy or `mode: off` preserves ordinary
host dispatch without Python, credentials or network access. Do not invoke the
helper just to discover that routing is off. Existing explicit user/role choices
still take precedence and must satisfy host/project constraints. Fable aliases
and full Fable model IDs remain forbidden for Claude adventurers.

Use one route per quest: `claude-native`, `claude-skill` or `codex-skill`. Do not
silently switch skills, invoke nested model CLIs, create user-visible tasks in
place of workers, change host configuration, or translate Claude aliases into
Codex tiers. Routing changes only supported model/effort arguments. It cannot
select the parent model, reviewers, permissions, tools, lifecycle gates or retry
budgets. External IDD assignments remain outside this router.

## Activation and host adapter sequence

1. Resolve session selection → project `.guildhall/routing.json` → the current
   host entry in global defaults using [global configuration](global-routing.md).
   An absent project file inherits; a valid project off marker suppresses global
   routing. Resolve the established project root once; never scan ancestors.
   Invalid selected configuration stops resolution without external calls. See the
   [policy schema](../resources/schemas/policy.schema.json) and
   [off example](../resources/examples/off-policy.json). No bundled profile is
   qualified. Replace placeholders with actual supported host settings and
   measured profile facts; unknown quality, latency, usage and cost stay null.
   A key alone is never activation. Routing requires Python 3.12+ only when used.
2. Discover the actual fresh-worker tool, supported model/effort pairs and limits
   without paid discovery probes. Record client version, provider, tool,
   configuration revision, independence, fresh-context and selection support.
   Native Claude uses roster/frontmatter settings as its baseline and always
   supplies an explicit model argument. Skills normally inherit configured
   settings: represent this with both baseline arguments null, not guessed names.
   A model paired with null effort means omit effort, not known inherited effort.
3. For shadow/adaptive, first read reusable approval through the installed
   `scripts/routing_config.py` status operation with fresh host evidence. Use its
   policy and activation in the routing request. Reuse an unchanged valid approval
   across sessions/projects within its recorded scope; do not ask again. If none
   applies, show the user mode, objective, candidate scope and outbound
   fields before enabling external requests. Setup outside quest execution can
   persist explicit approval through the configuration helper. Record activation
   against `policy_hash(policy)`, SHA256 of sorted compact UTF-8 JSON with
   `ensure_ascii=False`. Any policy change needs renewed activation. Do not create
   consent by reading a repository file. Default category facts are role,
   category, risk, ambiguity, context bucket, required-capability count, objective,
   request-local opaque labels and numeric profile facts/compatibility booleans. No
   paths, host versions, model names, evidence hashes, policy or transcript leave
   the host in `state`; the envelope necessarily names the requested Jev model.
4. Optional `data_mode: summary` adds only the exact summary to those facts.
   Preview the actual text (at most 1000 characters), obtain approval and supply
   SHA256 of its exact UTF-8 bytes in `activation.summary_preview_hash`. Categories
   mode requires null summary. Summary mode requires a string. Never copy raw code,
   credentials, diffs, Specs or transcripts. The summary is untrusted data and
   cannot add choices. It is omitted from receipts and fingerprints.
5. Review the underlying host observation records and per-role evaluation reports
   independently before listing their hashes in `activation.evidence_hashes`.
   For an inherited baseline, `host.baseline_candidate` must identify the exact
   configured profile established by reviewed host/configuration evidence;
   `host.evidence_hash` must occur in the approved evidence list. Never guess the
   inherited model from role tiers or worker prose. Missing identity under active
   constraints holds the dispatch. Baseline null arguments remain null and
   observation stays unknown even when a trusted configuration maps the profile.
6. Build one [request](../resources/schemas/request.schema.json), using the
   [off request example](../resources/examples/off-request.json) as the complete
   field inventory. Initialize `state` once per quest to `calls_used: 0`,
   `provider_failed: false`, `adaptive_suspended: false`. Resolve routing serially
   before dispatch even when workers run concurrently: carry the returned state
   to the next invocation. Validation rejection preserves independently valid
   incoming state exactly, even when another request field is malformed. Missing,
   invalid or unreadable state returns a closed placeholder with `calls_used: 0`,
   `provider_failed: true`, `adaptive_suspended: true`. That zero is not a fresh
   budget: on such a rejection, retain the last trusted quest state rather than
   adopting the placeholder. If no trusted state remains, hold for an explicit
   recovery decision; never manufacture initial state to continue the quest.
   Never reset the call budget or circuit on a worker retry, resume, policy
   change, malformed request or transient provider failure.
7. Resolve explicit per-dispatch user candidate first, then explicit role candidate,
   then active routing, then eligible baseline. Invalid explicit choices hold;
   do not quietly select a different candidate. In off/no-policy mode validate
   explicit host settings using the same precedence without requiring Python.
   Native Claude supplies the selected literal model (full supported IDs allowed),
   while skill hosts pass only nonnull supported model/effort values. Always send
   the full original role contract and minimal permitted handoff. Test-author
   facts come only from its permitted Spec/API/test handoff, never implementation
   reads, solutions or Mordain's transcript. Do not give workers routing payloads.
8. Record configuration source, scope, source key and effective policy hash
   alongside the decision envelope; never send local paths to Jev. Record the
   returned decision envelope in the quest plan, within Mordain's
   plan-only scope. Buffer pre-plan records until the plan exists; a fast lane
   without a plan reports receipts in the final response. The helper writes no
   project files. A `hold` is a stop, never permission to route around constraints.
9. After actual dispatch, separately append worker identity, requested settings,
   trusted observed model/effort or `unknown`, metadata/evidence source, outcomes,
   verification evidence, actual retries and measured usage/cost when available.
   Neither a request nor model-echo prose proves execution identity. If a verified
   route substitutes settings or loses attribution, preserve work and set
   `adaptive_suspended: true` for subsequent decisions. Do not overwrite the
   helper's pre-dispatch unknown observation with an unsupported assertion.

Recheck configuration and approval at each new worker, including revocation and
source/host changes. Preserve trusted quest state across every recheck.
Resolve once for each new worker. Resume/follow-up retains its selected settings
where supported. Recheck capabilities before the next worker, never mid-write.
Never automatically replay an uncertain dispatch. A model escalation can consume
only an already-authorized retry; no extra retry or gate reset is introduced.

## Invoking the single bundled helper

Native Claude uses the installed plugin root, not the project or source checkout:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/skills/guildhall-quest/scripts/route_model.py" < request.json
```

The standalone skill and Codex plugin use their actual installed skill root:

```sh
python3 "<installed-skill-root>/scripts/route_model.py" < request.json
```

`request.json` represents the prepared JSON on stdin, not authorization for the
orchestrator to write another project file. Prefer piping the already prepared
request or a host stdin facility. The process emits one JSON envelope and exits
0 for dispatch, 2 for hold. No shell interpolation of task content or secret
values. Use the actual key environment-variable name from the policy. The
optional default HTTP transport alone needs the credential; fake transports do
not. Missing Python follows the same eligible-baseline-or-hold contract as
`provider_unavailable`; record the runtime limitation and skip further helper
attempts. Never install Python or edit personal settings automatically.

The importable `route(request, *, transport=None, now=None)` returns a dict;
`transport(payload, timeout_ms)` is the trusted synchronous fake seam and returns
a provider dict. No source-checkout imports are required. Fake transport code is
test code, not an untrusted extension loaded from policy. `now` is Unix seconds.
`policy_hash(policy)` performs canonical hashing, not validation or activation.

## Eligibility and qualification

All objects reject unknown fields, duplicate JSON keys, nonfinite numbers,
booleans as numbers and wrong primitive types. Request/provider JSON are limited
to 64 KiB, strings normally to 256 characters, candidates/capabilities to 16.
Candidate IDs match `[a-z][a-z0-9_-]{0,31}`, excluding `defer`. Hashes have 64
lowercase hex characters. List entries are unique. Roles may span all 18
adventurers; model-echo is excluded. Schemas describe field constraints; runtime
also rejects duplicate candidate IDs and host/model/effort triples, mismatched
summary modes and a null baseline model paired with nonnull effort.

Hard eligibility checks the policy allowlist, host route and exact supported
model/effort pairs, independent fresh workers, role, category, required
capabilities and context upper bounds (4096/32768/131072 tokens for
small/medium/large). Specified cost/latency ceilings reject unknown measurements.
Shadow can recommend without model-selection support and always dispatches the
eligible baseline. No eligible profiles holds. Singleton choices avoid the API.
A concrete baseline must exactly match an eligible profile. Applying any override
requires model-selection support; nonnull effort also requires effort support.

Schema v4 permits all 18 specialist roles in the explicit `adaptive_roles`
allowlist. Schemas v1–v3 retain their docs-writer/pr-author limit. Compute
qualified choices after hard eligibility. Required host evidence, approved
host/report evidence hashes, matching host revision, unexpired role/category
scope and a matching requested router selector are required. Qualification's
`profile_hash` binds canonical candidate JSON excluding `qualification`, covering
model, effort, metrics, scope and revision. The helper checks these references;
it does not certify reports. No qualifying candidates, unavailable controls or a
suspended state retains the eligible baseline. For a qualified singleton, use
its reviewed router identity without fabricating a newly observed router identity.

After a call, the returned concrete router identity must match reviewed evidence.
A moving alias returning another version suspends adaptive choices; do not assume
a returned concrete identity is an accepted request selector. Profile revisions,
model aliases/IDs, efforts, host configuration, router versions and evidence
expiry require reevaluation and explicit renewed policy activation. The release
ships no live-qualified profile. Shadow arithmetic alone cannot qualify one.

## Provider and receipts

The fixed request is `{model, state, questions: {route: {type: "choice",
instructions, criteria}}}`; `state` is an allowlisted-facts JSON string. Criteria
contain only request-local labels and `defer`; user policy IDs remain local.
Validate the exact label set before mapping choices back to eligible policy IDs. Adaptive sends only qualified IDs. Validate
`{model, answers: {route: {type: "choice", choice, confidence, probabilities}},
usage?}`. Confidence/probabilities are finite 0..1, the distribution covers exactly
requested IDs plus defer, and its sum is within 1e-6 of one. Optional usage has
nonnegative integer `input_tokens` and `output_tokens`. No arbitrary response
text becomes a command or dispatch model.

The default transport uses verified TLS at `https://api.typesafe.ai/v1/systemone`,
no redirects or proxy credential forwarding, one attempt and no hidden retry.
An HTTP-only child isolates DNS/socket/body reading under a 1..10000 ms
network-attempt watchdog budget. Elapsed launch time is deducted before waiting
for its response. OS process creation and final reaping may exceed the configured
budget: there is no strict portable wall-clock return-time guarantee. Cancellation
kills and reaps the child before return; receipt latency includes the entire
attempt and cleanup. It is transport isolation, not worker/model CLI dispatch. No key in argv, stderr,
receipts or provider-error text. A provider parse/transport failure opens the
quest circuit. Low confidence and defer do not. A new quest may start a new circuit.

Every envelope includes `schema_version`, `status`, `source`, `reason`, `dispatch`,
`recommended_candidate`, `eligible_candidates`, `receipt`, `state`. Receipt holds
policy hash, profile revision of the dispatched candidate, host snapshot,
baseline/requested settings, initially unknown observed settings, observed router
identity, measured call latency and validated usage or null. Snapshot includes
only route, client_version, provider, worker_tool, configuration_revision and
attribution. Input fingerprint hashes `{task: task without summary, policy_hash,
host: host_snapshot}`. It supports correlation, not secret anonymization. Null
fields mean unavailable; do not invent billing from tokens or subscription usage.

Stable reason codes:

| Reason | Meaning |
|---|---|
| `invalid_request` | Schema/size/semantic failure; hold, no transport; preserve valid incoming state, otherwise return a closed placeholder and retain last trusted adapter state |
| `invalid_override` | Explicit selection violates host/hard constraints; hold |
| `router_disabled` | Off; baseline preserved, no call |
| `activation_required` | Policy hash/external or exact-summary consent absent; hold |
| `no_candidates` | Hard-eligible set empty; hold |
| `baseline_ineligible` | Required fallback cannot be established; hold |
| `shadow` | Recommendation recorded; eligible baseline dispatched |
| `single_candidate` | One qualified adaptive choice, no call |
| `adaptive_unqualified` | Qualification, controls, role or suspension prevents adaptation |
| `unsupported_runtime` | Python is older than 3.12; hold without network and preserve valid incoming state; adapter retains eligible baseline or holds |
| `provider_unavailable` | Credential/runtime unavailable; eligible fallback |
| `provider_failed` | Provider failure/open circuit; eligible fallback |
| `budget_exhausted` | Quest call budget consumed; eligible fallback |
| `low_confidence` | Below policy threshold; eligible fallback, no circuit change |
| `defer` | Provider abstained; eligible fallback, no circuit change |
| `router_changed` | Concrete router identity changed; suspend adaptive, eligible fallback |
| `selected` | Valid explicit selection or qualified Jev recommendation |

Fallback reasons become `baseline_ineligible` when fallback violates constraints.
Source values are `user_override`, `role_override`, `off`, `baseline`,
`single_candidate` and `jev`. Holds keep the envelope and use null dispatch and
requested fields; malformed requests have null unavailable receipt values.

Disable by explicitly selecting session off or using a project opt-out under
[global configuration](global-routing.md). Removing a project policy restores
global inheritance and can enable an already-approved global policy. Explicit
off stops future routing calls and restores ordinary dispatch; it never cancels, replays
or reassigns an in-flight worker. Keep partial records for review.

The full [user guide](model-routing.md) and `../scripts/evaluate_routing.py` ship in this bundle.


## Scoped measurement schema

V1 remains supported without reinterpretation. V2 requires matching request and
policy versions, a per-candidate `measurements` array and null legacy global
metrics. Resolve quality, latency, cost and usage only for the current role and
task category; absent observations remain unknown. Duplicate scopes are rejected.
Changing policy version or measurements requires renewed activation and reviewed
qualification. The installed [guide](model-routing.md#subscription-efficiency-0110)
explains subscription setup and the bundled usage normalizer.


## Host evidence schema v3

Follow the [host evidence guide](host-evidence.md) and run preflight before any
paid study. V3 keeps scoped metrics and adds explicit required/available evidence
levels. Setup defaults to execution_observed; configuration_verified is a
separately reviewed opt-in and never relabels requested values as observation.
Before approval, inspect task-owned capture and quality reports, not just their
hashes. After each completed worker, compare profile evidence with `drift()`;
carry suspension forward on host/configuration or observed identity changes.
Preserve partial work and never replay an uncertain dispatch. In the configuration
lane, missing served identity is expected; loss of required configuration evidence
still suspends routing. Do not fabricate observed model or effort in either lane.


For bounded development/holdout evaluation, follow the bundled
[qualification study workflow](qualification-study.md). No helper launches models
or automatically promotes a profile.

## All-role eligibility (schema v4)

Follow the [role matrix and migration guide](role-eligibility.md). Eligibility
never changes role contracts, test-author handoffs, review membership or lifecycle
gates. Upgrading does not add roles to existing allowlists or qualify profiles.
