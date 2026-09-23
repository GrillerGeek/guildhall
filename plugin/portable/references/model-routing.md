# Optional Jev-assisted model routing

Guildhall 0.10.1 can ask Jev to recommend a model for a specialist assignment.
One bundled Python helper serves native Claude, the standalone Claude skill and
the Codex skill/plugin. Guildhall validates the result and dispatches through
the host's actual worker tool. The helper does not launch agents or write files.
IDD is optional and its external agents are outside this router.

| Mode | Behavior |
|---|---|
| `off` (default) | Ordinary host dispatch; absent/off policy skips the helper and makes no Jev calls. |
| `shadow` | Records recommendations and dispatches the eligible baseline. Profiles need supported settings, not adaptive qualification. |
| `adaptive` | Can change dispatch only for evaluated `docs-writer` and `pr-author` assignments with reviewed host/profile evidence. |

**No live-qualified profiles ship.** There are no measured cost, latency or
quality improvements claimed for this release. The [verification report](https://github.com/GrillerGeek/guildhall/blob/main/docs/reviews/2026-09-21-jev-routing.md)
separates offline tests, synthetic arithmetic and installation from live evidence.
An API key or repository policy file alone never enables routing.

## Prepare before starting a quest

Install or update [Guildhall](https://github.com/GrillerGeek/guildhall/blob/main/docs/installation.md), then restart the host. Version
0.10.1 includes the complete installed guide and evaluator. Normal skill use and off-mode
dispatch do not need the routing runtime, Jev or a key. Enabled routing needs
Python **3.12+** with only its standard library. Native Claude's existing hooks
have their own Python prerequisite, unchanged by this feature.

Prepare the optional project policy at `.guildhall/routing.json` in an ordinary
setup conversation before invoking a quest. Mordain can write only the quest
plan during execution. A useful setup request is:

```text
Help me prepare Guildhall's optional model routing for this project before a
quest. Read the installed routing guide, policy schema and off-policy example.
Discover the actual host worker tool and supported model/effort settings without
paid probes. Prepare .guildhall/routing.json in off mode with real candidate
profiles and a baseline supported by host/configuration evidence. Keep unknown
metrics null and qualification null. Show me the proposed shadow mode, objective,
candidate scope, outbound fields and any unresolved baseline evidence. Wait for
my explicit activation before external requests. Do not print credentials or
change host settings to manufacture model controls.
```

Use the installed skill's `resources/examples/off-policy.json` as the complete
policy template; it contains placeholders, not a working model catalog. Source
links to the bundled files:

- [Off policy](../resources/examples/off-policy.json)
- [Complete off request](../resources/examples/off-request.json)
- [Policy schema](../resources/schemas/policy.schema.json)
- [Request schema](../resources/schemas/request.schema.json)
- [Host adapter and routing contract](routing.md)

Profiles bind an opaque candidate ID to one actual host model/effort pair, roles,
task categories, capabilities, context capacity, metrics and profile revision.
Discover settings through the host's exposed capabilities and trusted
configuration; do not translate Claude aliases to invented Codex tiers or probe
every model with paid requests. Keep unknown quality, latency, usage and cost
null. Unknown cost/latency cannot satisfy a configured ceiling. The example's
confidence threshold is illustrative, not a calibrated recommendation.

Native Claude retains its roster/frontmatter baseline and passes a literal model
argument. Skills normally inherit host configuration: baseline model and effort
are both null. With routing active, that inherited baseline needs a trusted
configuration mapping in `host.baseline_candidate` and reviewed host evidence
whose hash appears in `activation.evidence_hashes`. A concrete baseline must
exactly match an eligible profile. An unresolved or ineligible fallback holds
dispatch. Null effort means omit the argument; it does not prove inherited effort.

## Credentials and activation

For external calls, provide `TYPESAFE_API_KEY` to the terminal/process that
launches the host, using your existing secret-management method. The policy
stores only `key_env: "TYPESAFE_API_KEY"`, never the value. Do not paste a key into
chat, JSON, shell arguments or receipts, and do not print the environment to
check it. A GUI host may not inherit a key set in a different terminal.

Once the proposed policy and baseline are ready, explicitly request shadow mode
and approve its displayed objective, candidate scope and outbound fields. The
adapter records activation against `policy_hash(policy)`, the SHA256 of sorted,
compact UTF-8 JSON. **Any policy change requires renewed activation.** Changing
the file alone supplies no consent. Start a quest only after setup is complete.

Shadow can recommend without model-selection controls. It never changes the
worker settings. A singleton eligible choice needs no API call; multiple eligible
choices require the key unless routing falls back first. Other Guildhall roles
can participate in shadow if their profiles cover the assignment. Adaptive is
limited to the two roles above, and never activates automatically.

## Safe offline smoke check

Replace the placeholder below with the actual installed `guildhall-quest`
directory containing `SKILL.md`, `scripts/` and `resources/`. Native Claude's
path is `${CLAUDE_PLUGIN_ROOT}/skills/guildhall-quest` inside its plugin context;
Codex and standalone paths depend on installation scope. This command uses the
bundled off request, leaves its placeholders untouched and makes no external call:

```sh
GUILDHALL_SKILL_ROOT='/absolute/path/to/installed/guildhall-quest'
GUILDHALL_SKILL_ROOT="$(realpath "$GUILDHALL_SKILL_ROOT")"
python3 --version
python3 "$GUILDHALL_SKILL_ROOT/scripts/route_model.py" \
  < "$GUILDHALL_SKILL_ROOT/resources/examples/off-request.json"
```

Expect exit 0, `status: "dispatch"`, `reason: "router_disabled"`, null baseline
dispatch arguments, `calls_used: 0` and observed model/effort `unknown`. This tests
the installed helper, not host model control. Ordinary off-mode quests skip the
helper entirely. The adapter prepares active requests from the schema and passes
JSON on stdin; users do not need to handcraft the full request packet. There is
no `--enable` CLI flag and the helper does not read the project policy itself.

## What leaves the host

Default `categories` mode sends role, task category, risk, ambiguity, context-size
bucket, required-capability count, objective, request-local opaque labels and numeric
profile facts/compatibility booleans. Policy candidate IDs remain local; the helper replaces them with `p0`, `p1`
and similar labels before sending a request. The request envelope names the requested Jev router model. It does not send
host model names/versions, paths, raw code, diffs, Specs, transcripts, evidence
references or the full policy.

Optional `summary` mode adds only the exact previewed task summary, at most 1000
characters. It requires approval of that text and its exact UTF-8 SHA256 in
`activation.summary_preview_hash`. Preview, for example: “Update the named setup
guide to match the supplied public interface.” Never include secrets or raw
project material. A changed summary needs a matching new preview approval.
Summary text remains untrusted data and is omitted from receipts/fingerprints.

The fixed endpoint is `https://api.typesafe.ai/v1/systemone`, with verified TLS,
no redirects and no proxy credential forwarding. Requests/responses are bounded
to 64 KiB. The example configures a two-second attempt budget and eight calls per
quest. A parent watchdog covers the HTTP child's DNS/socket/body work, subtracts
launch time and kills/reaps the child on timeout. OS process creation and final
reaping can exceed the configured budget; this is not an absolute portable
wall-clock return guarantee. Receipt latency includes that elapsed work. Each
call has one attempt, no automatic retry. Provider failures suppress further
calls for that quest.

## Decisions, fallback and receipts

Valid per-dispatch user choice takes precedence over an explicit role choice,
then active routing, then eligible baseline. Explicit choices need supported
host controls and hard eligibility, but no adaptive qualification. Invalid
explicit choices hold instead of quietly substituting another model. Claude
adventurers still cannot use Fable, including full Fable model IDs.

The coordinator initializes `calls_used: 0`, `provider_failed: false` and
`adaptive_suspended: false` once per quest. It resolves helper calls serially and
passes returned state to the next decision, even when workers run concurrently.
Retries, resumes and policy edits do not reset this state. A rejected request
preserves independently valid incoming state. When state is missing, invalid or
unreadable, the hold marks provider failure and adaptive suspension true with a
placeholder zero call count. The adapter must retain its last trusted quest state
and must never treat that placeholder as a reset or initialize state to recover.
The router does not
change role instructions, test-author independence, reviewers, permissions,
lifecycle gates or retry budgets.

| Reason | Operator response |
|---|---|
| `router_disabled`, `shadow`, `selected`, `single_candidate` | Inspect mode/source; shadow keeps baseline and singleton avoids a call. |
| `activation_required` | Review and explicitly activate the current policy/summary before proceeding. |
| `invalid_request`, `invalid_override`, `no_candidates`, `baseline_ineligible` | Dispatch is held. Correct schema, support, scope or baseline evidence; do not bypass constraints. |
| `provider_unavailable` | Missing key/runtime uses an eligible baseline or holds. Check the host process environment/runtime without exposing the key. |
| `provider_failed` | Timeout, transport/parse failure or open circuit; keep eligible baseline. No more provider calls this quest. |
| `budget_exhausted`, `low_confidence`, `defer` | Keep eligible baseline; do not reset state to force a recommendation. |
| `adaptive_unqualified` | Missing qualification/control, excluded role or suspended state; keep eligible baseline. |
| `router_changed` | Returned router identity differs from reviewed evidence; adaptive suspends and falls back. Reevaluate before later activation. |

Fallback becomes `baseline_ineligible` when its constraints cannot be met.
The CLI returns 2 for a hold and 0 for dispatch; fallback is not an error exit.
Missing Python is handled by the adapter, since the helper cannot run then.

Receipts go in the quest plan; pre-plan receipts are buffered and no-plan fast
lanes report them in the final response. They record policy/input hashes,
profile revision, host snapshot, baseline, recommendation, requested settings,
router identity, elapsed call time and validated usage when available. The
coordinator appends worker identity, outcomes, checks and actual retries after
execution. The helper's observed model/effort starts as `unknown`. Only trusted
host execution metadata can establish observation; a request, model-echo or
worker self-report cannot. Missing billing stays unknown. Fingerprints support
correlation; they do not anonymize secrets.

## Adaptive promotion and rollback

Before adaptive use, independently review real host attribution and per-role,
per-category evaluations against both static and deterministic baselines. The
qualification binds report/profile hashes, host revision, expiry, role/category
scope and requested/observed router identities. The helper validates references,
not the truth of a report. The offline evaluator's `eligible_for_review` result
is not qualification and its output always retains `qualification: false`.

Profile/model/effort changes, host configuration changes, expired evidence or
changed router identity require reevaluation and renewed policy activation.
Trusted host substitution or lost attribution suspends further adaptive choices.
Keep work already in flight; never automatically replay an uncertain dispatch.

To disable, explicitly select `off` or remove the optional project policy before
future dispatches. This stops future routing calls and restores ordinary host
behavior. It does not cancel, reassign or restart existing workers. Retain partial
work and receipts for review. No personal app settings need to change.


## Installed evaluator

The offline evaluator ships beside the routing helper. Run it without cloning
source code:

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/evaluate_routing.py" --demo
python3 "$GUILDHALL_SKILL_ROOT/scripts/evaluate_routing.py" < reviewed-records.json
```

The demo is synthetic and always reports `qualification: false`. A source checkout
retains `python3 scripts/evaluate_routing.py` as a compatibility entry point.

## Unsupported interpreter

The routing CLI and API return `unsupported_runtime` with a hold on Python older
than 3.12, preserving valid incoming quest state. Use a supported interpreter;
the host adapter may retain an eligible baseline or hold, and must keep its last
trusted state. The HTTP child exits 2 without a request on unsupported Python.
Off-mode quests still skip the helper and have no new Python dependency.
