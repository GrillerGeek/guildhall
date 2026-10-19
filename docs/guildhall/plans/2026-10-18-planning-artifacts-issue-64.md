# Quest 64: durable collaborative planning

## Context

- Mode: feature, non-IDD prose Spec.
- Spec: `docs/plans/2026-10-18-collaborative-planning-spec.md`.
- Started: 2026-10-19 00:45 UTC (2026-10-18 local).
- Status: root GREEN verified; independent post-green reviews starting.
- User requested the Guildhall quest workflow after reviewing the approach and
  completing the adapter spikes. No IDD Product chain or lifecycle is invented.
- Main coordinator: Mordain. Only this plan is writable by Mordain during the
  quest. Production implementation and other artifact edits are delegated.
- Quest baseline: `1e2701dfc21cc5850b5a672a8648fc7a017b7ccf`.
- Pre-existing work: modified prose Spec and untracked feasibility report.
  Preserve both; they are not changes authored by the quest implementer.
- No commit, push, global install, marketplace update or public deployment is
  required for this quest. Earlier checkpoint commit permission was scoped to
  that checkpoint. Workers report uncommitted paths.

## Host capabilities

Codex exposes `collaboration.spawn_agent`, messaging, interruption and waiting.
Fresh workers use `fork_turns: none`. Capacity: root plus three workers. Roles
inherit configured model/effort; trusted observed worker identity is unknown.
Filesystem restrictions remain the host's sandbox. Worker read/write scopes are
role instructions, not OS-enforced per-agent isolation. Actual browser access
and existing Playwright test setup must be checked before claiming UI acceptance.
Native Claude hooks do not execute as equivalent Codex enforcement.

Optional routing status was resolved for this project and `codex-skill` using
the installed 0.17.5 helper. Source: global, scope all-projects, mode shadow,
policy hash `f2d6ea4f3e7c7402dc4f5748491f6ed8054f822bc9e4e9c631deb02e935753e0`,
reason `host_evidence_required`, approval revision null, external_requests false.
No Jev request or activation is authorized or made. Ordinary inherited dispatch
continues; configuration and approvals remain unchanged. Recheck before workers.

## Preserved baseline evidence

All listed files have mode 0644. Check hashes after every writer handoff.

| File | SHA-256 |
| --- | --- |
| AGENTS.md | 10f211efbfdda42143d01dfe722604833ec3ccd36964e3abd03d575177f3d19f |
| plugin/hooks/quest_flag.py | d606c832ec6a49fe9d50d3276b4f3f71103d2925c24cbbea11b2f3013cd0fbdc |
| plugin/hooks/quest_write_guard.py | bab6cc4d4377c35faddaef2682f1042518b86de5370a4d497ab53495beb580b9 |
| plugin/hooks/hooks.json | 3ceb94c1f2ce6b71c60e4947ceb397d88afd869a5b382b30e3b09dd92559905d |
| docs/plans/2026-10-18-collaborative-planning-spec.md | 8387687f35fd11b6f3ab5bf28ab4a4ed19eb334df2a19bd3bc744cc1ce436ab6 |
| docs/reviews/2026-10-18-collaborative-planning-feasibility.md | b9c67416a3f8efe3508e3146ca38baf1606dff9ef992224a9e849ac5ab304d64 |

## Boundaries verbatim

1. Do not widen Mordain's plan-only write scope, change the native quest hooks,
   add an orchestrator subagent or add a twentieth native agent definition.
2. Preserve native Claude model aliases, explicit dispatch precedence, character
   voices, role independence, routing approvals and existing retry/review gates.
3. No changes to consuming-project IDD content/status or readiness facts from
   browser controls, checkpoint helpers or artifact/comment interactions.
4. No new public hosting, multiplayer backend, identity provider, automatic
   background synchronization, marketplace changes or global installation.
5. Do not claim local bridge controls are native artifact features, that a hosted
   URL is permanent, or that transport fixtures verify actual model quality.
6. Do not place credentials, private account IDs, raw chat transcripts, local
   absolute paths or logs in committed review/checkpoint records.
7. Generated files under plugin/skills/ must be regenerated, never hand-edited.
8. Python is optional for users who select the local companion/checkpoint helper;
   ordinary quests and host-native review paths retain their current prerequisites.
9. Retain completed spikes as labeled evidence; do not ship their synthetic model
   as a production adapter default or copy their permissive prototype code without
   implementing this spec's required checks.

## Dispatch sequence

1. Aldric, fresh pre-plan consultation, read-only, no test reads. Compare feasible
   architecture and identify ambiguity in the black-box public interface.
2. Resolve binding public API details from the Spec without implementation
   guesses. Consequential changes return to the user/author before tests.
3. Seraphine, fresh independent test-author. Only Spec, public API contract,
   project conventions and existing test conventions. Never receives spike
   implementation, architecture proposals, source analysis or parent transcript.
4. Mordain observes attributable RED and records error/failure/pass counts and
   test-file hashes. Unrelated broken setup blocks the chain.
5. Bruga, implementation only. Tests are read-only. Verify GREEN, protected
   baseline and all documented build/validation checks. Shared retry budget: one.
6. Tink only for a concrete narrow refactor; otherwise skip with rationale.
7. Post-green reviewers in capacity-bounded batches, with disjoint writes.
8. Fresh Aldric closing technical review after every writer has finished.
9. Rook prepares the PR draft after passing technical review. No publication.

## Reviewers selected

- Oriana security: required; HTTP input, paths, tokens, sessions and local writes.
- Cassian documentation: required; named user-facing docs only, disjoint scope.
- Vance observability: request/delivery state, errors, recovery and attribution.
- Thalia reliability: HTTP/RPC processes, timeouts, retries and concurrent writes.
- Cassia performance: bounded parsing, payload/history limits and malicious size.
- Garran operations: optional local service, configuration, disable and recovery.
- Vera UI tests: user-visible local browser behavior; actual test setup required.
- Lior accessibility: browser controls, selection, editable prose and export.
- Tabs plugin validation: manifests, generated bundles, tool allowlists and scope.
- Aldric closing technical review: mandatory complete Expectation/Boundary/
  Deliverable and verification coverage after implementation and writer changes.
- Skip Ysolde: new opt-in record schema; no existing database/schema migration
  or backfill. Revisit if compatibility/migration work appears.
- Skip Wren: no Exploration lineage or existing map for this work.

## Decisions

- The user explicitly selected a quest; this is the feature implementation
  workflow, not a new IDD authoring or lifecycle approval.
- Preserve native hooks and plan-only orchestration; do not adopt the obsolete
  earlier suggestion to widen Mordain's write scope.
- Use installed workflow contracts while modifying repository canonical sources;
  do not install the changes into this live session to test them.
- Synthetic adapter probes remain labeled evidence, not production acceptance.

## Public API handoff approved

The stakeholder accepted this requirements addendum with “Looks good. Approved”
in the main conversation after the Page review. It is not implementation guidance.
Do not give Seraphine Aldric's architecture
report, the spike implementation or the rest of this orchestration plan.

### Entry point and result envelope

```text
python3 review.py OP --root ABS --plan REL --host HOST --input-json FILE_OR_DASH
```

OP: init, inspect, checkpoint, export, serve. HOST: document, claude-artifact,
codex-space, opencode or pi. ROOT must already be a directory; PLAN must name a
Markdown plan under docs/guildhall/plans/. The helper never writes PLAN. Bundle
path is PLAN without its .md extension, containing only the named review files
and two helper-owned snapshots. Unknown input fields are rejected, not ignored.

Finite operations print exactly one JSON object, with schema_version=1,
operation, ok, result and error. Success has ok=true, result=object, error=null.
Failure has ok=false, result=null and error={code,message,details}. details is a
bounded object without secrets. Diagnostic text uses stderr. Exit 0 includes a
successfully observed content conflict; exit 2 means invalid arguments/input,
3 a path/concurrency/identity refusal, and 4 unavailable or failed operation.

### Durable record

Required top-level fields: schema_version, quest_id, plan_path, review_path,
html_path, surface, authority, checkpoint, feedback, decisions. All paths are
repository-relative and derived/validated against the selected bundle.

- surface: {kind,id,url}; id and URL are null for document/local-only modes,
  otherwise explicit opaque hosted ID and HTTPS URL. No automatic service lookup.
- authority: {display_label,source}; source is a bounded human-readable reference
  to the consuming project's owner designation or initiating-user decision.
- checkpoint: {state,common,pending}; common is null before the first complete
  checkpoint, otherwise {local_sha256,normalized_sha256,hosted_revision,
  source_ref,snapshot_path}. pending is null or a bounded proposed save/guard
  record, never an invented receipt. hosted_revision is string or null.
- feedback: up to 200 substantive entries, each {id,source_ref,source_revision,
  author,selection,text,disposition,rationale}. source_revision and author may be
  null when genuinely unknown. selection is null or {status,text}, with attached
  or detached status; detached text may be null. Dispositions: proposed,
  accepted, rejected, deferred or unresolved. Accepted records need an actual
  supplied decision source; the helper does not authenticate or invent approval.
- decisions: [{id,text,disposition,source_ref,authority_label,rationale}], keeping
  proposals distinct from decisions confirmed in the authorized handoff.

Hash strings are lowercase 64-character SHA-256 hex. Saved-byte hashes cover
exact UTF-8 bytes. Normalized comparison removes one leading UTF-8 BOM, converts
CRLF/CR to LF, and changes nothing else: no trimming, Unicode normalization,
reflow, case folding or terminal-newline insertion.

### Operation inputs and effects

**init:** {quest_id,content,authority,surface}. Create the missing review.md,
review.html and review-state.json only within the inferred bundle. Require the
plan to exist. Existing identical initialization is idempotent; unexpected files
or conflicting existing content are refused before mutation. No model/network
call, listener or credential lookup. Return bundle_path, created_paths and hashes.

**inspect:** {observation?,runtime_dir?}. observation is {surface_id,text,revision,source_ref,
feedback_complete,feedback}. revision may be null. Never infer completeness from
an absent list. Return state, local/normalized hashes, observed hosted hash and
revision, completeness, conflict detail and pending delivery counts. No writes,
subprocesses, listeners or model calls.

**checkpoint:** {phase,expected_state_hash,expected_review_hash,observation?,
checkpoint_id?,decisions?,resolution?,receipt?}. Phase is prepare or complete. Prepare validates
all guards, computes a merge and records a pending save without advancing common.
Return a checkpoint_id, state, merged content/hash, exact required local/hosted
save actions and changed paths. A conflict returns both versions and baseline;
it does not save an arbitrary winner. For a local-only surface, prepare may save
the guarded merged local content and reports a pending completion checkpoint.
For native surfaces, the worker performs the actual hosted save with observed
host guards; the helper never invokes an invented connector.

Complete requires the checkpoint_id and fresh local/content guards, plus the
actual hosted save receipt {surface_id,revision,content_sha256,source_ref} when
hosted output is required. A missing revision is null and cannot substitute for
the observed content hash/source. Advance common only once both sides are
observed saved. Record which side succeeded when only one does; retain pending
state and refuse replay of an already observed save. Resolution is an explicit
{content,source_ref,authority_label} from the owner resolving a named conflict;
never choose a winner because a timestamp is later.

**export:** {expected_review_hash}. Write only the bundle's review.html using the
maintained template; return source_sha256, output_sha256, output_path and
disabled_capabilities. It must open without a provider, server or credentials.
Do not overwrite an unexpected/symlink file or launch a model/network request.

**serve:** {runtime_dir,binding?,startup_timeout_seconds?,request_timeout_seconds?}.
Runtime directory must be explicit, outside the durable bundle and Git-tracked
files. Validate all inputs before any listener/process. No binding means local
document/comment mode with chat disabled. OpenCode binding names its loopback
server and exact session ID. Pi binding names a dedicated session file in runtime
storage and the existing host model selection; no arbitrary executable command
or reuse of a running TUI. Print one startup JSON record with origin, capability
summary, session identity and a one-time write token; token never enters durable
records. Shutdown closes owned resources; it never kills an unrelated host.

### Merge and checkpoint semantics

Merge prose by baseline lines, retaining their line endings after the specified
normalization. Edits to separate half-open line ranges merge; identical edits
are applied once. Different insertions at the same baseline position conflict.
Deletion versus edit of an overlapping range conflicts. Insertion at the boundary
of a replaced/deleted range is conservatively a conflict; adjacent non-insertion
edits remain disjoint. Never reorder competing edits by arrival time.

Decision entries with distinct IDs may be appended independently. Differing
edits under the same ID conflict. Surface identity, owner and path metadata are
guarded configuration, not automatically merged prose.

For a local-only surface, no hosted observation is required: clean means the
current local normalized text equals the common snapshot. No hosted surface is
different from a selected but inaccessible hosted surface, which is unavailable.
Conflict takes precedence over normal change states; pending save state remains
visible separately and cannot be cleared merely by inspecting content. Changed
local/hosted hashes relative to common determine local-changed, hosted-changed or
both-changed before a merge. No common snapshot yields local-changed plus
checkpoint_needed=true; it is not proof of synchronization. Inspection also
returns state_sha256 for the exact saved manifest bytes and review_sha256 for
the exact saved review bytes, so the next mutation can supply its guards.

### Browser protocol

- GET /state: document, revision, binding summary, available capabilities and
  bounded feedback; no write token or provider credentials in this response.
- PUT /document: {base_revision,content}; guarded edit, 264 KiB serialized limit
  and 256 KiB decoded-text limit. A 409 conflict preserves the browser draft.
- POST /feedback: {id,session_id,base_revision,selection,comment}; bounded 32 KiB
  body and 4,000-character selection/comment. Return request_id, delivery_state
  and response when observed. Empty comment or ambiguous selection is invalid.
- POST /checkpoint: finite prepare/complete payload above; never accepts a
  decision implicitly or changes the quest plan.
- POST /cancel: {request_id,session_id}; request normal host abort and return its
  observed outcome. Delivery remains unknown without a matching acknowledgement.
- POST /rebind: {expected_session_id,new_binding,source_ref}; explicit operator
  decision, refused while any unresolved in-flight request exists. Never replay
  old requests into the new session.

All write routes require the startup token and exact bound Host/Origin. Missing
or mismatched browser Origin is refused; CLI clients must supply that same
origin explicitly. Unknown routes or methods have no generic tool/shell effect.
Responses use stable JSON error envelopes; HTTP 400 invalid input, 403 origin/
token, 404 unknown route, 409 revision/identity conflict, 413 bounded input
overflow, 502 unavailable host. Browser interactions cannot alter the binding's
model/provider configuration or enable implementation tools.

Cassian review-document mode may invoke only the named init/inspect/checkpoint/
export operations for its designated bundle, and serve for its explicit runtime
directory. The maintained service owns bounded later browser mutations. This
permission does not grant arbitrary Bash, tool execution or post-green behavior
changes. Native paths can materialize the same record without Python.

### Wire names clarified for the approved scope

These names resolve test-author questions without changing the approved behavior.
Write authentication uses `X-Review-Token`. Startup is the normal success envelope;
result contains origin, write_token, session_id (null without binding), capabilities
{document,comments,chat,cancel,rebind} booleans. GET /state uses the same envelope,
result {document,revision,binding,capabilities,feedback,requests}; document is text,
revision is its exact SHA-256, binding is null or {kind,session_id}, requests are
bounded {request_id,session_id,delivery_state,response} entries. No secret token.
Write responses likewise use the envelope (operation is the route without slash).
For unbound local feedback, session_id is null; persist a proposed comment with
response=null and delivery_state=prepared, without calling any host. Bound sends
require the exact observed session_id. POST /feedback selection is a string or
null; a nonempty selection must occur exactly once in the guarded document.

Inspect result keys: state, checkpoint_needed, state_sha256, review_sha256,
normalized_sha256, hosted_sha256, hosted_revision, completeness, conflicts,
pending_delivery_counts. hosted_sha256 covers normalized observed text or null;
completeness is {feedback:boolean}; absent observation yields false. conflicts
is an array of {kind,baseline,local,hosted}, with text strings or null when absent;
kind is prose, decision, or identity. pending_delivery_counts maps the four named
delivery states to nonnegative counts only when an explicit runtime is observed;
otherwise it is null. delivery_coverage is complete or unavailable accordingly. Prepare result keys: checkpoint_id, state,
merged_content, merged_sha256, required_saves, changed_paths, conflicts.
required_saves is an array containing local and/or hosted. merged_content/hash
are null on conflict; no pending save is created on conflict. Complete returns
state, checkpoint_id, changed_paths. Init hashes is {review_sha256,html_sha256,
state_sha256}. Binding failure may leave document/comment mode available, but
reports chat=false plus a bounded unavailable_reason, never a successful chat.

OpenCode binding: {kind:"opencode",base_url,session_id}. base_url is an explicit
http://127.0.0.1:PORT or http://[::1]:PORT origin, no credentials/path/query/fragment;
no redirects, DNS hostnames, remote service or automatic server startup. Session
identity is validated with GET /session/{sessionID}; require returned id exactly.
Require its observed permission ruleset to be exactly one wildcard deny-all rule
{permission:"*",pattern:"*",action:"deny"}, otherwise disable chat. Never patch
permissions. GET /experimental/tool/ids returns string[]; disable every observed
tool in each prompt's tools map. Recheck identity/restrictions before each send.
No global/provider/model configuration writes. Use observed session model
{providerID,id} as per-message model {providerID,modelID}; if absent, use the most
recent user history info.model; unavailable if neither is observed.
GET /session/{sessionID}/message returns [{info,parts}]; prompt POST to that same
path sends parts:[{type:"text",text:REQUEST_TEXT}], tools and observed model.
REQUEST_TEXT is JSON text {review_request_id,base_revision,selection,comment}.
Track returned user/assistant identities; observe assistant info.parentID against
the corresponding user info.id and terminal info.time.completed with text parts.
Stable review_request_id appears in user text for history recovery; do not resend
when history is unavailable or response delivery is unknown. POST
/session/{sessionID}/abort returning true is observed cancellation acknowledgement,
not proof a previously unknown response was never delivered. Never use session
creation/deletion, shell, command or permission-reply endpoints.

Pi binding: {kind:"pi",session_file}. session_file is an absolute .jsonl path
inside the explicit runtime_dir, dedicated to this adapter, no symlink, and not
an arbitrary existing user/TUI session. Resolve only the normal pi executable
from PATH, no executable/arguments field. Launch --mode rpc --session SESSION
--no-tools --no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes
--no-context-files --no-approve --offline. Do not pass provider/model flags or
change settings. Use existing selected model observed in get_state, otherwise
chat unavailable. No startup prompt or model call. JSONL commands carry unique id;
responses match id,type:"response",command,success and data. get_state must
observe sessionFile and sessionId; get_messages data.messages provides history.
prompt carries message:REQUEST_TEXT above; its successful response is acceptance,
not completion. Observe assistant message_end then agent_settled before reporting
response-received; reject toolCall output as a restriction failure. Preserve
sent-unknown across timeout/disconnect; recover by request marker and subsequent
assistant history, never automatic resubmission. Cancellation first uses clear_queue (preserving returned text as unsent), then
abort; only its matching successful response is observed cancellation, and no
acknowledgement means unknown. Reject new sends when get_state observes streaming,
compaction or queued messages outside the sole adapter-owned active request.
Owned process exit releases runtime locks; restart may resume only the same
adapter-owned session after verifying its runtime ownership marker. Rebind never
transfers/replays requests. Tests may supply a fake pi on PATH implementing this
public protocol; this is synthetic transport evidence, not live-host acceptance.

Protocol sources: OpenCode 1.19.3 live /doc schema, inspected without any model
prompt or session mutation; official https://docs.opencode.ai/docs/sdk/ and
https://docs.opencode.ai/docs/tools/; Pi 1.3.0 --help and installed rpc-commands.md.
Actual hosts with incompatible/missing restriction or history capabilities must
fall back visibly. These protocol fixtures do not certify future host versions.

### Read-only runtime delivery inspection clarification

`inspect` optionally accepts runtime_dir. This names the same explicit external
runtime used by serve; it never searches the filesystem or discovers sessions.
Validate path/symlink safety and its persisted owner identity against this exact
root/plan before reading a bounded atomic journal snapshot. Return actual counts
for prepared, sent-unknown, response-received and failed-before-send, with
delivery_coverage="complete". Missing/inaccessible runtime/journal yields exit4
and no writes; foreign ownership or unsafe/symlink path yields exit3. Inspection
never creates runtime storage, sends/replays prompts, recovers via network,
launches a host or changes any journal/checkpoint.

Without runtime_dir, return pending_delivery_counts=null and
delivery_coverage="unavailable"; zero is not evidence of an unobserved runtime.
This coverage does not claim no other runtime exists. GET /state has its already
bound runtime and therefore can report observed counts. Runtime identity and
request journals remain outside portable records; no new durable private paths.
This is a technical clarification of E08/status truthfulness; product behavior,
write scope and authority are unchanged. Independent tests precede the delta.

### Review-regression clarifications within the existing API

- request_timeout_seconds is one monotonic total host-operation budget, including
  preflight, synchronization/write waits, sending, reading and recovery. Individual
  progress/trickle or acknowledgement cannot restart it. Preserve unknown delivery
  whenever a write may have reached the peer. Cancellation and owned shutdown
  remain bounded even when a peer stops reading its pipe.
- Existing runtime storage must have current-user filesystem ownership and private
  permissions before journal access or host startup. Refuse unsafe directories
  rather than silently chmod. An absent runtime/journal still reports exit4 with
  no creation; unsafe/foreign/symlink storage reports exit3 before use.
- Unexpected boundary failures retain the public envelope, with error.details
  containing bounded safe stage and error_class labels. Operation is already
  present in the outer envelope. Emit safe operation/stage/error_class stderr
  diagnostics where applicable; no raw exception paths, token, provider output
  or transcript. Expected validation refusals need not become noisy error logs.
- GET /state additionally reports unavailable_reason:string|null. A request entry
  may include recovery_error:null or {code,message,details:{stage,error_class}}.
  Correlation remains its request_id/session_id. These labels identify failure
  stages without forwarding raw host errors. Losing tool-restriction evidence
  disables chat while retaining unknown delivery. Connected UI keeps binding
  identity and the actual bounded unavailable reason visible.
- New comments between checkpoint prepare and complete must survive or completion
  safely refuses until incorporated. Failed publication retains a usable prior
  baseline. A feedback/rebind race cannot redirect the old request to a new
  session: reject rebind while reserved, or reject stale feedback after rebind.
- Pi terminal observations must belong to the exact active request; delayed
  events cannot satisfy a later send. Resume verifies observed stable session ID,
  as well as the same owned session file. No new mutation/recovery endpoint.

## Not yet specified

The public addendum above is accepted. Actual native worker access and complete
host acceptance remain empirical checks. Existing browser runtime is runnable and
the isolated Playwright config is authored; feature UI tests await a reachable
companion after GREEN. Missing tooling cannot waive the UI gate.

## Out of scope

New multi-user hosting, publishing, marketplace updates, global installs, model
routing activation and unrelated tavern work. No Spec or IDD status fabrication.

## Verification evidence

- Preflight: actual routing status returned external_requests false; no calls.
- Independent role contract for pre-plan Aldric and closing technical contract
  read. Some initial combined output was truncated; the missing Spec ownership,
  record, transport and Boundary sections were reread separately before writing.
- Worker delivery completeness is not inferred from hashes or worker assertion.
  Retain any actual chunk/visibility limitations with each handoff.
- RED/GREEN, full checks and host acceptance: pending.
- Existing baseline suite: `python3 -B -m unittest discover -s tests`, exit 0,
  197 tests, 18.177 seconds. This is baseline evidence, not new-feature GREEN.
- Aldric pre-plan result: architecture feasible, recommended shared portable
  record with optional Python/native paths; blocked independent tests on missing
  public CLI/schema, observation, merge, recovery, cancellation and writer-tool
  contracts. The addendum above makes those choices concrete for review.
- Aldric was fresh-context, read-only and did not read tests. Required-input
  completeness is supported by its reported bounded reads but host-visible
  read-output evidence is unavailable to Mordain; delivery attribution unknown.
- Cassian's first documentation-worker turn failed at inherited-model capacity.
  One same-agent/same-settings retry was requested; no model override or routing
  change is authorized. Verify Page state before any uncertain append.
- Cassian's retry completed: only the existing planning Page was changed,
  appending Quest interface proposal at sequence 11. Readback reported all 138
  pre-existing blocks/metadata and four attached comment selections preserved.
  No local file, commit, sharing or message action occurred. Rendering uninspected.
- All six protected/pre-existing file hashes verified unchanged after this
  handoff. The user approved the public contract; Seraphine was dispatched fresh-context.
  The implementation has not started; draft RED is not accepted until test handoff.

## Lessons

- Seraphine found missing wire names before implementation; precise public keys
  and source-verified adapter protocols were added before accepted RED.
- Runtime delivery-count omission was found during implementation; source writes
  paused for an independently authored regression, rather than claiming zeros.
- Routing recheck for that follow-up occurred immediately after dispatch rather
  than before it. Same shadow/inactive policy was verified, no external request
  or settings change occurred; future dispatches must check first.

## Open items

- Complete the independent test handoff and observe attributable RED.
- Production host/provider acceptance and any human-only QA remain pending.

## UI tooling preflight

A pre-acquired Playwright 1.61.1 runtime is available. A Chromium cache is also
present, but the runtime's expected executable was not found there. Only
dependency metadata and executable presence were inspected, not unrelated
application source. This does not yet establish a runnable browser, test
configuration or passing UI tests.
Vera will need named isolated config/tests under tests/fixtures/review/ and a
reachable companion. Supply local runtime locations out-of-band rather than
hardcoding machine paths into committed tests or review records. No browser
installation or user configuration change has occurred.

### Current test-author and browser evidence

Seraphine reported a first draft of 16 attributable assertion failures, all
explicitly identifying the promised missing review.py. Not accepted as final
RED: remaining merge/partial-save/adapter tests are being authored. She identified
wire-name/protocol omissions; Mordain clarified these in the approved API scope
from actual OpenCode /doc and Pi RPC documentation, without spike/source exposure.
The draft fixture HOME override was flagged before RED acceptance under the
session instruction against repurposing HOME; Seraphine owns that correction.

Playwright prerequisite check now succeeded using the already installed Edge
155.0.4283.62 with a disposable profile and synthetic in-memory page, no network
page or account access. Default sandbox launch failed; approved escalated launch
succeeded. This verifies runnable tooling only, not the feature UI. Runtime and
browser paths will be supplied through environment to a portable fixture config.
No dependency acquisition, global installation or user setting change occurred.

## Accepted RED handoff

Seraphine froze six files without commits. Mordain independently ran
`python3 -B` with unittest discovery for test_review*.py: 48 methods, 50 actual
assertion-failure events (subtests included), zero errors/passes/skips, exit 1.
All causes explicitly identify the promised missing review.py entry point.
Full discovery then ran 245 methods: 50 failure events, zero errors/skips, exit 1;
all failures have that same cause. Thus the existing 197 tests remain passing.
No unrelated fixture/setup failure remains. Goal: all 48 new test methods pass,
zero regressions in 197 baseline tests; preserve actual subtest classifications.

Frozen tests (read-only for implementer and later source writers):

| Path | Mode | SHA-256 |
| --- | --- | --- |
| tests/test_review_contract.py | 0644 | 2f7441c8b4383a34b08927b1805697c8b34bbecf6ea5532c12c8715877b7a0c4 |
| tests/test_review_adapters.py | 0644 | 11c4c2f1bbe6c8949733e7fa88be92d6148c5e1b0be94b793333385c1ed3e72e |
| tests/fixtures/review/artifact-agent.md | 0644 | f7fc9babb349b47d60f09d6f760e63b962f118ae2373852bc37b24cee72483f4 |
| tests/fixtures/review/pi | 0755 | d018e7a3f6068455457d714bf82a5cc31888492629b03f391a4627bd7410ec97 |
| tests/fixtures/review/playwright.config.cjs | 0644 | e44f2fcf3624d0efd35364f9ffedccc8ac1028e93b9504222ad8a7f10e125709 |
| tests/fixtures/review/unknown-tool-agent.md | 0644 | 7e3d1244af83a679a5bb1f1a85213c3daa00dc12ee357bfdc730eb803b35d1dc |

Coverage gaps are explicit: native surfaces/privacy/sharing, real model behavior,
Page-chat write-back, successful rebind/Pi restart recovery, offline browser UI
and accessibility, IDD/worker contract semantics require later review/acceptance.
Transport tests use synthetic peers only. Three-size hostile-input tests must
reach actual parsing/matching paths after implementation; missing entry RED
does not establish runtime performance. Worker completeness was reported with
bounded-read details; enforced isolation and actual model identity remain unknown.
All six protected/pre-existing hashes were rechecked unchanged. Fresh routing
status before Bruga: same global shadow policy, host_evidence_required, no
approval revision/external requests. Inherited settings, no override.

### Bruga dispatch

Fresh inherited-context-isolated worker dispatched after root-observed RED;
role/host guidance, full Spec and approved API plus all frozen tests are supplied.
Implementation scope is canonical deliverables and generated bundles via builder,
with tests, hooks, AGENTS, other roles and pre-existing docs read-only. No commit
authority. Bruga reported the exact minimal canonical file list before writes.
Post-green named user docs and verification report remain Cassian-owned.
A temporary synthetic service/export fixture is requested for Vera after GREEN;
this is test setup, not a real quest document mutation or native-host acceptance.

### Implementation progress (worker-reported, not root GREEN)

Bruga's first development runs reached 27/30 core/packaging methods and16/18
adapter methods passing. Reported causes were snapshot inspection, unfinished
packaging, runtime alias canonicalization and oversized-body early-close behavior.
He reports fixes and is rerunning. Default-sandbox socket PermissionErrors are
setup restrictions, not feature behavior. These are implementation-development
runs; the completed handoff and root verification have not occurred, so the one
post-handoff shared retry remains unused.

Post-green review batching will preserve independent/disjoint scopes: security,
reliability and observability; performance, accessibility and plugin validation;
UI tests and operations; then documentation/report synthesis with all available
results. Closing Aldric runs after all relevant writes, then Rook only afterPASS.

### Runtime-count ambiguity and targeted RED delta

Bruga found inspect cannot locate external request journals from observation-only
input. Reporting zero would be false confidence. Mordain chose explicit optional
read-only runtime_dir and unavailable coverage without it, as detailed in the
public API. All Bruga source writes are paused while Seraphine independently
authors the regression and root observes new RED. No new user permission is
needed for this technical read-only interface completion within approved E08.

Bruga paused all source writes. Worker-reported development results: original
contract30/30 (18.299s) and escalated adapter18/18 (8.939s) pass. Build140files,
check0changed, plugin19agents0errors0warnings and portable validator pass. A full
245-method run overlapped source changes, so it is not final evidence. Root
GREEN remains pending the new RED delta, implementation and fresh whole checks.

### Intended routing packaging expectation change

Root verified tests/test_routing_setup.py66-75 assumes every portable script and
resource is copied to routing setup. This older assertion contradicts approved
E12 and the new separation tests. Bruga's development full suite245 ran49.220s
with244passes/1error (missing excluded review.py), zero assertion failures.
This is an intentionally changed behavior, not an unrelated regression or a
reason to ship review resources into setup. Seraphine alone is authorized to
update that one expected inventory: exclude only scripts/review.py and
resources/review, explicitly assert absence, preserve all routing-byte checks.
No other baseline test may change. Original file mode0644/SHA-256:
82c41e2a56f2d0d925d15979284c39206a84664710cfb2636b6711fcade2ed16.

### Accepted targeted RED and updated freeze

Root independently ran all four new methods under approved localhost escalation:
4 assertion failures, zero errors/passes/skips, exit1,0.778s. Actual causes are
false zero counts without locator and unknown runtime_dir field (exit2 instead
of required4/0/3). New behavior is absent; no setup failure. Root also inspected
the sole baseline-test diff and verified the exact E12-only exclusion/absence
assertions. Seraphine observed focused routing test1/1pass.

Updated authoritative freeze (unchanged fixtures retain prior hashes):

| Path | Mode | SHA-256 |
| --- | --- | --- |
| tests/test_review_contract.py | 0644 | e47da99a5342e5bbe9a3c1da059cbbf40e71ced7305ee56b2801e94631edc3c3 |
| tests/test_review_adapters.py | 0644 | 4a74a75432b8819bac25d665f6a94e18f952b970cfb39ebad1b8fda17eabb6f4 |
| tests/test_routing_setup.py | 0644 | d190c824679eb02b281bab6bd1f6636b5d90f114df9cfdd20f273865fdee1c9e |

Bruga released to implement only the specified delta and finish checks after
this RED. Numeric goal52new +197existing methods (249total), with one intentional
E12 expectation update among the197. All other baseline assertions unchanged.
Fresh routing recheck before release: same inactive global shadow policy, no
external requests/approval. Shared post-handoff retry still unused.

## Review change evidence: source freeze

Base HEAD1e2701dfc21cc5850b5a672a8648fc7a017b7ccf to current worktree,
including all tracked and untracked paths below. No commits/staging required.
Two pre-existing files are explicitly attributed. This plan itself is the
coordinator's mutable orchestration output, excluded from its own recursive hash.
Review current contents plus `git diff HEAD -- <tracked paths>`; untracked
files must be read directly, not omitted as if base..HEAD covered them.

| Path | Attribution | Mode | SHA-256 |
| --- | --- | --- | --- |
| docs/plans/2026-10-18-collaborative-planning-spec.md | pre-existing preserved | 0644 | 8387687f35fd11b6f3ab5bf28ab4a4ed19eb334df2a19bd3bc744cc1ce436ab6 |
| docs/reviews/2026-10-18-collaborative-planning-feasibility.md | pre-existing preserved | 0644 | b9c67416a3f8efe3508e3146ca38baf1606dff9ef992224a9e849ac5ab304d64 |
| plugin/.claude-plugin/plugin.json | Bruga implementation/generated | 0644 | 8e89e8cc876e9d2eb1b129901d8a0a83a07711483112fb3d8947cdcebc764dce |
| plugin/.codex-plugin/plugin.json | Bruga implementation/generated | 0644 | 21c2e533d775a4f1d5c91739e803b5e3e7e5b98c77c4f3dd20a0194f066aca21 |
| plugin/agents/docs-writer.md | Bruga implementation/generated | 0644 | 2ac052099e49c88b5bab79e7662fb23f245da67efff509700c6ed0397a10f254 |
| plugin/commands/quest.md | Bruga implementation/generated | 0644 | 06dd2cbc549741a94fd170e1a82651d68da57a1b244d7a0bafdd5d1d68b320af |
| plugin/plugin.json | Bruga implementation/generated | 0644 | bc28bdc03bd87db4856b7d99bba43fa20b5d055fda79e067972454fbb7adeded |
| plugin/portable/SKILL.md | Bruga implementation/generated | 0644 | 3a1fff6c5a74accfd1d20be950e5663a84e73aef29e811a3fa51ec6058e4e36e |
| plugin/portable/references/collaborative-planning.md | Bruga implementation/generated | 0644 | 250a7c9008e9c46f77d198c25c2325bd0bc809d2bafe9b61f832b054423dea74 |
| plugin/portable/references/hosts.md | Bruga implementation/generated | 0644 | 3c77716ed9c9bd32b4c45d700671a47e693337bb103e8920ba9ff9135fe26869 |
| plugin/portable/references/quest.md | Bruga implementation/generated | 0644 | 11b99ba860dfda0e70b05ceeae6df7689ec791ff15926b14183d4a72c818d345 |
| plugin/portable/resources/review/example.json | Bruga implementation/generated | 0644 | af8ff954f2d479aaf9d8542ae981f07be5235063715bb80dab7512f34780e8b9 |
| plugin/portable/resources/review/record.schema.json | Bruga implementation/generated | 0644 | bb33bf7f3eed9a2754e9cc75eb8971db9c3c8f07a414864c73377e55fad30bed |
| plugin/portable/resources/review/template.html | Bruga implementation/generated | 0644 | 12c2e0d23b719b2859cb683d5d484d7ed1cebfdb5c0e106fb403df06c6fda6dd |
| plugin/portable/scripts/review.py | Bruga implementation/generated | 0644 | 7bb60a23a88ba47dc6c63b8b76d3ac0c49831418dfd002ff99e535d71000f855 |
| plugin/skills/guildhall-quest/SKILL.md | Bruga implementation/generated | 0644 | 3a1fff6c5a74accfd1d20be950e5663a84e73aef29e811a3fa51ec6058e4e36e |
| plugin/skills/guildhall-quest/references/collaborative-planning.md | Bruga implementation/generated | 0644 | 250a7c9008e9c46f77d198c25c2325bd0bc809d2bafe9b61f832b054423dea74 |
| plugin/skills/guildhall-quest/references/hosts.md | Bruga implementation/generated | 0644 | 3c77716ed9c9bd32b4c45d700671a47e693337bb103e8920ba9ff9135fe26869 |
| plugin/skills/guildhall-quest/references/quest.md | Bruga implementation/generated | 0644 | 11b99ba860dfda0e70b05ceeae6df7689ec791ff15926b14183d4a72c818d345 |
| plugin/skills/guildhall-quest/references/roles/docs-writer.md | Bruga implementation/generated | 0644 | b55606b0a553632c2a78db64134d7a432814464a3eaa6ceb381769e910b0e2a5 |
| plugin/skills/guildhall-quest/resources/review/example.json | Bruga implementation/generated | 0644 | af8ff954f2d479aaf9d8542ae981f07be5235063715bb80dab7512f34780e8b9 |
| plugin/skills/guildhall-quest/resources/review/record.schema.json | Bruga implementation/generated | 0644 | bb33bf7f3eed9a2754e9cc75eb8971db9c3c8f07a414864c73377e55fad30bed |
| plugin/skills/guildhall-quest/resources/review/template.html | Bruga implementation/generated | 0644 | 12c2e0d23b719b2859cb683d5d484d7ed1cebfdb5c0e106fb403df06c6fda6dd |
| plugin/skills/guildhall-quest/scripts/review.py | Bruga implementation/generated | 0644 | 7bb60a23a88ba47dc6c63b8b76d3ac0c49831418dfd002ff99e535d71000f855 |
| scripts/build_portable.py | Bruga implementation/generated | 0644 | 3c39e0416c9961efe8ae4bb83ae84d3a7fe6d3ebe9ec4dac1638a4427bc33e4d |
| scripts/validate_plugin.py | Bruga implementation/generated | 0644 | bc815346e9828060d4ca4cb0899641eab9024e23f2aa303ddc849b0d966067b0 |
| scripts/validate_portable.py | Bruga implementation/generated | 0644 | 88254df7ac1370fd0350d5cabd904a78e9bf9f8b4b5f443d79453efae4c2c574 |
| tests/fixtures/review/artifact-agent.md | Seraphine independent tests | 0644 | f7fc9babb349b47d60f09d6f760e63b962f118ae2373852bc37b24cee72483f4 |
| tests/fixtures/review/pi | Seraphine independent tests | 0755 | d018e7a3f6068455457d714bf82a5cc31888492629b03f391a4627bd7410ec97 |
| tests/fixtures/review/playwright.config.cjs | Seraphine independent tests | 0644 | e44f2fcf3624d0efd35364f9ffedccc8ac1028e93b9504222ad8a7f10e125709 |
| tests/fixtures/review/unknown-tool-agent.md | Seraphine independent tests | 0644 | 7e3d1244af83a679a5bb1f1a85213c3daa00dc12ee357bfdc730eb803b35d1dc |
| tests/test_review_adapters.py | Seraphine independent tests | 0644 | 4a74a75432b8819bac25d665f6a94e18f952b970cfb39ebad1b8fda17eabb6f4 |
| tests/test_review_contract.py | Seraphine independent tests | 0644 | e47da99a5342e5bbe9a3c1da059cbbf40e71ced7305ee56b2801e94631edc3c3 |
| tests/test_routing_setup.py | Seraphine independent tests | 0644 | d190c824679eb02b281bab6bd1f6636b5d90f114df9cfdd20f273865fdee1c9e |

## Root-observed GREEN and additional checks

`python3 -B -m unittest discover -s tests` under approved localhost escalation:
249tests,57.378s,OK,exit0. All52new methods and197existing methods pass, with the
one intentionally updated E12 inventory assertion noted above. No source writes
occurred during this final root run; complete Bruga source-freeze hashes match.
All updated test-freeze, protected hook/AGENTS and pre-existing hashes/modes match.

Root separately observed build --check140files0changed, plugin validator19agents
0errors0warnings, portable validator and git diff --check all exit0. Bruga also
ran actual regeneration and its own249tests56.213s exit0. No post-handoff retry
was consumed. Tink skipped: no concrete additional refactor needed for the Spec.

Fresh routing status resolved individually before security, reliability and
observability dispatches: same global shadow policy/hash, host_evidence_required,
no approval/external requests. All inherit configured settings, no overrides.
Read-only reviewer batch1 is now authorized on the source-freeze evidence.

Open recovery follow-up: unknown deliveries remain visible/bound until matching
host history is observed; cancel cannot invent completion and rebind is refused.
Operator inspection is required. No new abandonment/force-clear endpoint is
authorized by the current API; reviewers must assess this limit truthfully.
Native/paid-model acceptance remains separate pending evidence. Synthetic
companion/export fixture is reachable for later UI testing; private runtime paths
and write token are kept outside this durable plan.

## Review round1: repair required before closure

All reviewers read-only; no probes/provider calls/writes. Oriana0high/1med: existing
runtime filesystem ownership/privacy unchecked (review.py780). Vance0high/2med/1low:
recovery refusals silently discarded(837), unexpected boundary/process diagnostics
lost(988/1050/640), connected UI drops binding/disabled reason(template29,helper851).
Thalia3high/4med: feedback/rebind race(914), complete drops feedback added since
prepare(468), delayed Pi terminals assigned to next request(742); snapshot publication
can invalidate last common on failure(464), overall deadline not enforced(551),
blocking Pi pipe write/lock(688), Pi stable session ID not verified on restart(650).
Line numbers refer to frozen review version, not future repair positions.

Closure is stopped by high findings and required-validation gaps. No source writes
until independent regression RED. Root will route behavior-only requirements to
Seraphine; she receives no source lines, architecture or review transcript. Then
Bruga gets full findings with tests read-only. Repair stays in existing canonical
helper/UI/contracts scope and regenerates. All11findings are owned by Bruga, then
rechecked by original three reviewers; no knownfinding is silently deferred.
Other selected reviewers remain pending until repaired source freezes.
Fresh routing checked before author/implementer repair boundary: same inactive
shadow hash, host_evidence_required, no external requests/overrides.

## Current publication authorization

The user is away and explicitly directed: “Keep working until you have a PR
ready for me to review.” This supersedes the earlier checkpoint-only/no-new-commit
limit for final delivery: scoped commits, push of this feature branch and GitHub
PR creation are now authorized after all required gates. No merge, release,
global install or marketplace publication is authorized. Rook still drafts only;
Mordain may create the approved-scope PR after reviewing the concrete result.
Native-host/account-only acceptance stays explicitly pending, never fabricated.

Root resumed after a model-capacity interruption without changing model/routing.
Seraphine and Bruga correctly held source writes pending independent RED release.
The feedback race contract permits safe serialization: A may complete in A before
a successful B rebind, as well as refusal of either conflicting operation. The
unconditional invariant is no cross-session delivery or stale response attribution.

## Accepted review-regression RED before upstream integration

Root independently ran all10new methods:10assertion-failure events and2runtime
errors (missing explicitly promised public stage/recovery_error fields),0passes/
skips,exit1. All10methods nonpassing. Causes reproduce session-crossing, erased
comment, stale Pi answer, corrupt baseline,2.96s elapsed for1s budget, saturated
pipe exceeding5s, changed Pi identity accepted, unsafe0750/0770/0707 runtime,
and missing safe diagnostics. Both fault probes reached asserted boundaries.
These are attributable absent promised behaviors, not unrelated broken setup.
Race test now permits safe serialized completion-before-rebind.

Authoritative updated freeze:

| Path | Mode | SHA-256 |
| --- | --- | --- |
| tests/test_review_contract.py | 0644 | 0020ed7f20c551592d59b6b802fc7ad15fa40dec69aea5b465349132718d64f3 |
| tests/test_review_adapters.py | 0644 | e72916397de7b0b6375ad544ecadb4ddcd8be5d1c5c8257251ff1ec75dd22ad9 |
| tests/fixtures/review/pi | 0755 | 89440e85006e10341ca1ad4a7f6ef34514b72599a444d04cb7e3028b08b6216b |
| tests/fixtures/review/run_opaque.py | 0644 | eba72cb46a48d699b34268678eff56766016370673b81e8a03f2a274afd37ff0 |

User-authorized PR preparation refreshed origin/main to6bca2ad, including merged
PR69 removing Jev-assisted routing and earlier quest-gate improvements. This
branch still descends from530d5cf; a clean local checkpoint preserves all current
work before integrating main. Current main's intentional removals/improvements
are authoritative: do not resurrect routing setup or removed routing resources.
E12 separation becomes preservation of their absence. Native hooks remain exact.
Version must advance beyond upstream0.18.0. The old197baseline/249GREEN numbers
remain historical evidence; final gates must rebaseline/retest current main.
The local checkpoint contains known review RED and is not published as complete.
