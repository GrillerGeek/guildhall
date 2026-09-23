# Host evidence and preflight

Version 0.12.0 separates requested settings, host-recorded configuration and
host-reported execution identity. These are different guarantees. A worker's own
answer is never an evidence source. Evidence helpers are read-only: they inspect
explicitly supplied task-owned files, do not search your sessions, run models,
change host settings, or qualify profiles automatically.

## Check before paying for a study

Use the [preflight template](../resources/examples/preflight.json) with the actual
host application's executable/build, worker tool and capability facts. Confirm
identity through an active-process association or a host handshake; a convenient
`codex --version` elsewhere on PATH is not sufficient. Mark uncertain association
`unconfirmed`. The helper diagnoses the supplied facts; it does not authenticate
them or discover processes itself.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/routing_evidence.py" < preflight.json
```

`record_access` is `none`, `claude-owned-transcript` or `codex-owned-jsonrpc`.
The report identifies missing runtime, controls, capture access, review and study
requirements. A candidate evidence lane is a possible next step, not activation.
The default available modes remain off and shadow pending evidence review.
Preflight works without an API key or live probe.

## Read a task-owned capture

The examples are deliberately synthetic: [Claude](../resources/examples/claude-capture.json)
and [Codex](../resources/examples/codex-capture.json). Supply actual host identity,
worker/session IDs, requested settings, complete turn/attempt/response inventory,
and records. Missing or incomplete inventory cannot establish attribution.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/routing_evidence.py" < capture.json
```

For an existing JSONL trace, prepare the same context without its `records` field:

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/routing_evidence.py" \
  --context reviewed-context.json --records task-owned-trace.jsonl
```

Inputs are bounded to 16 MiB and 100,000 records. No raw prompts, content blocks,
transcripts or credentials appear in the output. Keep capture/report hashes and
review the underlying local evidence before using them. Synthetic reports never
advertise adaptive availability. `qualification` always remains false.

## Native Claude

Use the exact subagent transcript identified by the host, not the parent's final
text. The [Claude hook reference](https://code.claude.com/docs/en/hooks) describes
subagent transcript paths; [subagent documentation](https://code.claude.com/docs/en/sub-agents)
describes their lifecycle. The pilot in issue #37 reports `message.model` as a
concrete executed ID. This adapter treats it as host-reported observation, not
independent provider attestation.

`claude-transcript-v1` reads assistant records with matching `agentId` and
`sessionId`, `message.id`, `message.model` and `message.usage`. A single bounded
turn can use the context's turn ID; multi-turn captures must provide explicit
`turn_id` correlation. Every expected response must be present, with one
consistent model across the assignment. Missing/mixed identities or incomplete
turns yield unknown evidence. Effort remains unknown unless a supported source
is added; model identity alone does not prove effort.

Repeated message IDs are normalized once, with monotonic usage updates. Cache
read/write inputs are separate from uncached input for this adapter. Incompatible
counter shapes fail rather than inventing consumption. This field profile has
synthetic regression coverage; revalidate it against the actual client version
before qualifying a deployment. This release does not assert a new live Claude
qualification run.

## Codex

The supported `codex-app-server-v2` input is a task-owned, complete JSON-RPC
capture with both outgoing requests and incoming responses/notifications. Pair
request IDs for `thread/start` and `turn/start`, correlate the acknowledged
worker/session/turn, and use `turn/completed` agent-message IDs and statuses.
The starting thread must have no prior turns. Unacknowledged model/effort
overrides, missing records or reported substitutions make attribution unknown.

The acknowledged thread configuration is **configuration_verified**, never
observed execution identity. Thread usage totals are cumulative; normalize
monotonic per-turn differences for sequential turns instead of summing snapshots.
Reject interleaved counter streams that cannot be attributed safely. Unknown
billing stays unknown. Response item IDs are not described as provider response IDs.

[Codex app-server documentation](https://learn.chatgpt.com/docs/app-server)
describes version-specific schema generation, usage updates and reroute events.
Inspected local runtime 0.154.0-alpha.6.2 explicitly describes Thread.model and
Thread.reasoningEffort as configuration rather than per-turn telemetry.
Its completion schema has no executed model field. `model/rerouted` exposes
`highRiskCyberActivity`; its absence does not prove that no substitution occurred.
This is evidence about that inspected build, not certification of the different
0.155.0-alpha.9.2 desktop build reported in issue #36.

The current `collaboration.spawn_agent` result does not itself supply a complete
app-server capture. If your desktop provides no supported task-owned capture,
use `record_access: none`: adaptive qualification remains unavailable through
this adapter. Do not silently replace desktop workers with CLI sessions. A future
adapter may use reviewed native session records after their actual build-specific
contract is established; this release does not infer one from private filenames.

## Explicit qualification lanes (routing schema v3)

V1 and V2 policies retain their existing attribution behavior. V3 adds
`policy.required_evidence` and `host.evidence_level`; the required level defaults
to **execution_observed in setup**, and the schema requires an explicit value.
Qualification adds `evidence_level`, `observed_model`, `observed_effort` and
`objective`, in addition to all prior hashes, host revision, scope and expiry.

- `execution_observed`: a reviewed concrete model observation is mandatory.
  Nonnull requested effort additionally requires matching observed effort.
- `configuration_verified`: a separately reviewed study may qualify effective
  host configuration, while served model/effort remains unknown. The user must
  explicitly select this weaker requirement and activate the changed policy.

Both lanes require actual model controls, fresh independent workers, reviewed
capture/report hashes, per-role quality evidence, matching objective and profile
hashes, unexpired scope, and the existing router identity checks. Changing the
objective invalidates V3 qualification. Reading a report does not add its hash to
approved evidence automatically. Do not label a configuration study as a
served-model benchmark or infer that every Codex host supports this lane.

See [policy v3](../resources/schemas/policy-v3.schema.json) and
[request v3](../resources/schemas/request-v3.schema.json). Migration is explicit:
set both versions to 3, keep V2 scoped measurements, select the evidence requirement,
clear old qualifications, obtain matching review and renew activation. Never
reinterpret legacy `verified` as one of the new levels automatically.

## Detect drift after execution

Record the alias requested and the concrete ID observed when available. Compare
new evidence with the previously reviewed report for that profile. The importable
`drift(previous, current)` returns suspension reasons for changed host/configuration,
lost evidence or changed observed model/effort, and always sets `replay: false`.
The coordinator carries `adaptive_suspended: true` to future routing decisions.
Preserve existing workers and partial work. Reevaluate and reactivate explicitly.

If identity only arrives after execution, no pre-dispatch guarantee against alias
drift exists. Keep that limitation visible. For a host without suitable telemetry,
an upstream request should identify the actual build, worker/turn/response IDs,
the missing executed model/effort fields, substitution coverage and a minimal
redacted schema/capture example. Do not attach private transcript content.
