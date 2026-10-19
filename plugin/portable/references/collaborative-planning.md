# Collaborative planning review

Mordain stays in the main conversation and writes only the quest plan at
`docs/guildhall/plans/YYYY-MM-DD-slug.md`. Review documents are Cassian's named
outputs in **review-document** mode. A helper is bounded bookkeeping and transport,
not another specialist, lifecycle controller or a way around the plan-only guard.
The removed routing setup and Jev integration remain absent; review support does
not reinstall or reactivate them.

## Choose a real capability

Discover tools callable in this session **and in the writer's context**. Prefer a
native Claude artifact, then a native editable Codex Space Page, then the local
OpenCode/Pi companion, then Markdown/HTML plus the main conversation. Report the
selected surface, stable identity and unavailable features. Product names and
installed plugins do not establish capability. Missing worker access requires a
supported alternative; Mordain must not write the review himself.

Use one workspace per quest. With no destination, create a private surface using
the supported tool's actual sharing controls; reuse a supplied writable destination.
Record the returned stable ID and URL. Resume that exact identity. Never widen
sharing or recreate a Page after an uncertain save, deletion or loss of access.
Ask for an explicit recovery choice while preserving local material. Do not
promise a hosted URL is permanent.

Native Page content is editable prose, not an HTML-only embed. Present options,
a recommendation, tradeoffs, unresolved questions and relevant IDD links. Add
interactive explanations only where useful. Preserve available chat, selections,
comments, direct edits and control outcomes; collect retrievable substantive
results at checkpoints. Page chat is a separate agent context: have it write
proposed outcomes back to native content/comments. Meeting transcripts are not
arbitrary Page chat history. Retrieve every comments page when supported; state
partial coverage when completeness is unknown. Detached anchors need human
interpretation. Record only material model-visible widget state, never replace
provider-owned state with that partial projection.

## Ownership and handoffs

Dispatch Cassian with mode, bounded approved proposal/Spec/decision inputs,
explicit document paths, selected hosted ID/destination, authority source and
creation permission for missing outputs. He may create/update **only** those
named review documents, records and hosted surface. The maintained helper/template
provides scaffolding. No application code, test running, implementation design,
acceptance decisions or agent dispatch belongs in review-document mode.

Native Claude adds the documented `Artifact` built-in to Cassian's explicit tool
allowlist, preserving his other tools. Discover actual support first; the allowlist
is not proof of account access or hook equivalence. Portable writers call actual
host tools, never copied Claude tool names. Native paths remain usable without
Python: save the same bounded record and review files with supported file/host
tools. Ordinary quests require neither Python nor this companion.

A project-designated owner, otherwise the initiating user, may accept decisions.
AI responses, another collaborator's suggestions and control selections are
proposals. Preserve actual source references, author labels and observed revisions;
unknown values stay null. Do not invent acceptance, identity or revision facts.
Changed reviewed IDD content returns to its authoring/review flow; review controls
never establish readiness or advance statuses. Seraphine receives only the existing
Spec/API/test handoff: no review HTML, solution proposals, Page chats, model replies
or inherited orchestration transcripts. Discovery remains separate from execution.

## Portable workspace and record

The plan links to its sibling `slug/review.md`, `slug/review.html`, and hosted URL
when available. The bundle contains only `review.md`, `review.html`,
`review-state.json`, `snapshots/common.md` and `snapshots/pending.md`. Keep one
last-common and one pending snapshot. Refuse unknown files before mutation;
inspection can read guards without deleting a user's extra snapshot. Never follow
symlinks or delete user files. The helper never writes the main plan.

[Record schema](../resources/review/record.schema.json) and the
[unaccepted example](../resources/review/example.json) describe schema version 1.
Required fields: schema_version, quest_id, plan_path, review_path, html_path,
surface {kind,id,url}, authority {display_label,source}, checkpoint
{state,common,pending}, feedback and decisions. Paths are derived repository-relative
paths. Native hosted surfaces require explicit ID/HTTPS URL; local-only modes use
null identity. No account lookup or connector credentials belong in the helper.

Common records contain local_sha256, normalized_sha256, hosted_revision,
source_ref and snapshot_path. Hash exact saved UTF-8 bytes separately from normalized
exported text. Normalize by removing one leading BOM and converting CRLF/CR to LF;
change nothing else. Do not hash the record into itself. Feedback has stable id,
source_ref, source_revision, author, selection, text, disposition and rationale;
selection is null or {status:attached|detached,text}. Decisions have id, text,
disposition, source_ref, authority_label and rationale. Accepted entries require
actual supplied decision sources and designated authority. Do not store credentials,
private account IDs, raw chat transcripts, machine paths or logs in these records.
Runtime bindings, request journals, transient answers and tokens stay outside the
repository in explicitly selected private runtime storage.

## Optional CLI

```text
python3 scripts/review.py OP --root ABS --plan REL --host HOST --input-json FILE_OR_DASH
```

Resolve scripts from the installed quest bundle. OP is init, inspect, checkpoint,
export or serve. HOST is document, claude-artifact, codex-space, opencode or pi.
Root must exist; plan must already exist directly under docs/guildhall/plans/.
Unknown fields, duplicate keys, path escapes and malformed data are refused.
Finite operations print one schema_version=1 JSON envelope with operation, ok,
result and error. Errors have code,message,details without secrets. Exit 0 includes
observed content conflicts; 2 invalid input; 3 path/identity/concurrency refusal;
4 unavailable operation. No startup model call, provider installation, routing
activation, credential copy or host configuration changes.

- **init**: {quest_id,content,authority,surface}. Creates only missing named files;
  identical initialization is idempotent, conflicts refuse before writes.
- **inspect**: {observation?,runtime_dir?}; observation is {surface_id,text,revision,source_ref,
  feedback_complete?,feedback?}. Read-only; no baseline advancement or side effects.
  Missing feedback completeness is false. Reports state, checkpoint_needed,
  state_sha256, review_sha256, normalized_sha256, hosted_sha256, hosted_revision,
  completeness, conflicts, pending_delivery_counts and delivery_coverage. Without an
  explicit runtime locator, counts are null and coverage is unavailable. With a
  safely observed external runtime, require exact canonical root/plan/quest
  ownership and count the journal without creating files, recovering requests,
  contacting a host or changing bytes/modes/times. Missing runtime/journal is
  unavailable; foreign ownership and symlinks are refused. Companion GET /state
  also supplies the actual runtime counts in its checkpoint summary.
- **checkpoint**: {phase,expected_state_hash,expected_review_hash,observation?,
  checkpoint_id?,decisions?,resolution?,receipt?}. Prepare verifies both exact-byte
  guards, computes merge and writes pending snapshot only. It returns checkpoint_id,
  state, merged_content/hash, required_saves, changed_paths and conflicts. Local-only
  mode may save guarded local content. A conflict returns both versions and baseline,
  with no writes and no arbitrary winner. Resolution is explicit owner-supplied
  {content,source_ref,authority_label}. Complete requires the exact pending ID, fresh
  local guards and, for native hosted surfaces, a fresh observation and actual receipt
  {surface_id,revision,content_sha256,source_ref}. Null revision needs the observed
  content hash and source. Only both saved representations advance common. Record
  successful hosted receipt when local save fails; retain pending. Completed IDs
  cannot be replayed. Metadata identity/authority/path changes never auto-merge.
- **export**: {expected_review_hash}. Guarded review.html update using the maintained
  template. Standalone HTML needs no network, provider, credentials or harness;
  editing, comparison and downloads work offline. Chat is clearly disabled.
- **serve**: {runtime_dir,binding?,startup_timeout_seconds?,request_timeout_seconds?}.
  Runtime storage must be outside the repository and durable bundle. No binding
  enables document/comment mode with chat disabled. Deadlines default to 30/60
  seconds and are capped at 300. Validate before listener/process creation. Startup
  envelope reports origin, write_token, session_id and capabilities; token never
  enters durable records. Paste the token into the companion page to save/send.

Merge baseline line edits using half-open ranges. Identical edits apply once;
separate edits merge; competing same-position insertions, overlapping edits and
insertions touching a replacement/deletion boundary conflict. Adjacent replacements
are disjoint. Distinct decision IDs append; differing same-ID entries conflict.
The bounded diff refuses exceptionally complex line products with an explicit
split request rather than silently truncating content.

States: clean, local-changed, hosted-changed, both-changed, conflict,
pending-local-save, pending-hosted-save, unavailable. Clean means normalized
representations match common, never acceptance. Missing common yields local-changed
and checkpoint_needed. Selected inaccessible hosted surfaces are unavailable,
not local mode. Pending saves remain visible even when content matches.

## Companion and recovery

Bind loopback only. All writes require exact Host, exact Origin and X-Review-Token;
there is no wildcard CORS or generic tool/shell/configuration endpoint. GET /state
returns document, exact revision, binding summary, capabilities, bounded feedback
and requests without the token. PUT /document {base_revision,content} refuses stale
revisions with 409 and preserves the tab's draft. POST /feedback
{id,session_id,base_revision,selection,comment} requires exact session and a passage
occurring exactly once, or null for unanchored chat. POST /checkpoint uses the CLI
contract; /cancel {request_id,session_id} asks normal host cancellation; /rebind
{expected_session_id,new_binding,source_ref} is explicit and refuses unresolved sends.
Errors: 400 invalid, 403 origin/token, 404 unknown route, 409 guard/identity,
413 overflow, 502 host unavailable. Browser input cannot change model/provider,
enable tools, run a quest or accept/change a Spec.

Persist request identity before send. Delivery is prepared, sent-unknown,
response-received or failed-before-send. Identical retries inspect existing state;
changed payload under the same ID conflicts. Only failed-before-send permits new
submission without host-history reconciliation. Unknown delivery is inspected by
marker/session history, never replayed. Host cancellation acknowledgement does not
prove an unknown answer never arrived. Closing the browser preserves saved feedback;
unsaved drafts are clearly labeled. Graceful shutdown closes only owned resources.

OpenCode binding is {kind:opencode,base_url,session_id}. The explicit base_url must
be a bare http loopback IP origin with a port; no DNS, redirects or server startup.
GET the exact selected session, require its returned ID and exactly one wildcard
deny-all permission rule. Never patch permissions. GET tool IDs and disable every
observed tool per message. Recheck before each send. Use observed selected session
model or latest user-history model, never replace configuration. Prompt only the
same session/message endpoint with JSON text {review_request_id,base_revision,
selection,comment}. Recover by that marker, corresponding user ID, assistant
parentID and terminal completion. Only the selected session abort endpoint is used.

Pi binding is {kind:pi,session_file}; absolute .jsonl path must be in private runtime,
new/unowned only at first launch, with an adapter ownership marker for restart.
Resolve normal pi from PATH; launch --mode rpc --session SESSION --no-tools
--no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes
--no-context-files --no-approve --offline. No arbitrary executable, model/provider
flags or takeover of a running TUI. Match JSONL command IDs and success responses;
get_state verifies sessionFile/sessionId and existing model. Refuse unrelated
streaming, compaction or queued work. Prompt acknowledgement is not completion:
require assistant message_end and agent_settled, reject toolCall output. Recover
from marker plus settled assistant history. Cancellation clear_queue precedes
abort; preserve unsent text only in runtime. Release runtime locks on owned exit.

Review document limit: 256 KiB UTF-8. Full edit request limit: 264 KiB serialized,
independent of decoded text size; heavy escaping may reach it first. Feedback
requests: 32 KiB; comment/selection: 4,000 characters; substantive feedback: 200.
Reject rather than truncate; preserve drafts and offer splitting/archival. Report
lower host limits. No paid-model/native-account acceptance is implied by packaging,
mock transport, generated output or completed historical spikes. Retain those
spikes as labeled evidence; no synthetic responder ships as the adapter default.
