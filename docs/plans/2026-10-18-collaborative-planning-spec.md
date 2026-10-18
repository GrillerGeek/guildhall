# Collaborative planning implementation specification

- Status: draft for stakeholder review; not a ready IDD Spec or execution authorization.
- Issue: [64](https://github.com/GrillerGeek/guildhall/issues/64).
- Design: [collaborative planning](2026-10-18-collaborative-planning-artifacts.md).
- Evidence: [OpenCode and Pi spikes](../../spikes/planning-artifacts/README.md).
- Review: [planning Page](https://chatgpt.com/space/page_4e1962051cf48191890273dbf93560bc).
- Scope basis: durable artifacts, full supported interaction, one Page per quest,
  project-owner decision authority, concise decision provenance, and both adapter
  spikes were confirmed. The local-companion-first release boundary follows the
  subsequent accepted recommendation. Detailed contracts below remain proposals.

## Context

Guildhall currently saves a quest plan in source control but presents most
planning material in its main conversation. Users should be able to explore a
proposal, highlight a passage, discuss it, and collaborate in the host's richest
available surface. Another contributor must still understand the decisions and
reopen the portable explanation from a checkout.

Use Claude artifacts for supported Claude Code sessions and a Page in ChatGPT
Space for Codex sessions with the required connector tools. Discover capabilities
in the actual session. A product name, installed plugin or shared thread snapshot
does not prove that the required artifact tools are callable.

OpenCode 1.19.3 and Pi 1.3.0 passed isolated local browser/session transport probes
with a synthetic responder. Use a shared local browser companion with separate
adapters for these hosts. This release does not create a hosted collaboration
service for them. The probe did not establish paid-provider compatibility,
multi-user permissions or live model quality.

The repository's own spec is prose, without an IDD Product chain. Consuming
projects retain their actual IDD authoring, readiness, review and lifecycle rules.

### Architecture and ownership

Keep Mordain in the main conversation. Mordain selects the review mode, owns
planning decisions and writes only the existing quest plan during execution.
The native Write guard, its hooks and the nineteen-role inventory stay intact.
Mordain must not launch a mutating helper through Bash to evade this rule.

Extend Cassian's docs-writer contract with one explicit `review-document` mode.
It receives a bounded proposal/Spec/decision handoff and named documentation
outputs instead of a post-green code diff. It may create or update only those
review documents, companion records and the named hosted surface. It does not
design implementation, decide acceptance, alter IDD artifacts, run tests or
dispatch other agents. Preserve its existing post-green mode and character.

HTML and interaction scaffolding come from a maintained helper/template, not
arbitrary application code authored in review-document mode. If rendering
requires invoking that helper, allow only its named, scoped operation in this
mode; Cassian's other Bash use remains the current read-only git inspection.
Required host tools must actually be available in the writer's context. Missing
worker access is a capability limitation, not permission for Mordain to write
outside the plan or simulate independent work.

The helper handles bounded document/feedback persistence. Host adapters handle
session transport. Neither is a specialist or an autonomous lifecycle controller.
Browser input is planning feedback; it cannot invoke arbitrary tools or shell
commands, start a quest, or change a Spec status.

### Planning bundle

Preserve the canonical plan path and add a scoped companion directory:

```text
docs/guildhall/plans/YYYY-MM-DD-slug.md
docs/guildhall/plans/YYYY-MM-DD-slug/
  review.md              # editable portable review content
  review.html            # standalone explanation, with useful local controls
  review-state.json      # identity, last checkpoint, decision provenance
  snapshots/             # bounded baselines needed for conflict detection
```

Runtime processes, temporary credentials, raw session logs, transient request
journals and machine-specific paths stay outside this bundle. Native Page text
is editable prose; do not place the entire proposal inside an HTML embed.
Embed interactive explanations where they improve a decision. The plan links
to its review source, standalone explanation and optional hosted URL.

Use schema version 1 for the checkpoint record. Required fields identify the
quest, repository-relative plan/review paths, surface kind and stable ID/URL if
available, content hashes, linked IDD inputs, baseline snapshot references,
checkpoint state, and decision/feedback dispositions. Each substantive entry
has a stable ID, source reference and available revision, author display label,
selection or explicit detached-anchor state, decision text, disposition and
rationale. Never invent missing author, revision or approval facts.

Do not hash the manifest into itself. Hash exact saved document bytes and the
explicitly normalized exported text representation separately where needed.
Record only the model-visible part of widget state needed for a material choice;
do not replace provider-owned state from that partial projection.

### Local transport

The companion binds to loopback on an available port. Require a per-process
write token, check Host/Origin against the bound origin, reject cross-origin
writes and do not enable wildcard CORS. Browser code talks to the companion,
which makes the host call; the browser never receives provider credentials.

OpenCode attaches to an explicitly selected server session; show the session
identity before accepting feedback. Pi uses a dedicated adapter-owned planning
session through JSONL RPC and its explicit session file. It does not silently
take over an existing Pi TUI or assume it can attach to its stdin. Persist the
binding outside source control and require an explicit rebind on mismatch.

Use the user's existing host model/provider selection. Do not install a provider,
copy credentials, activate Guildhall routing, or replace their model configuration.
The review session runs without implementation tools. If the host cannot provide
the required tool restrictions, use document/comment interaction without an
agent-backed chat and explain that limitation. No hidden model probe on startup.

## Expectations

| ID | Behavior | Acceptance |
| --- | --- | --- |
| E01 | Select a supported review surface | Discover host capabilities; prefer native Claude artifact or Codex Space Page, then local OpenCode/Pi companion, then Markdown/HTML plus conversation. Report the selected surface and unavailable features. |
| E02 | Maintain one review workspace per quest | Reuse its stable identity on resume. Create a private surface by default when no destination is specified; reuse an explicitly supplied writable destination. Never silently widen sharing or create duplicate Pages after uncertain saves. |
| E03 | Present material for review in that workspace | Include options, recommendation, tradeoffs, unresolved questions and relevant IDD links. Use native editable text and interactive explanations where useful. Short status messages and raw verification logs need not become separate artifacts. |
| E04 | Preserve the richest supported feedback | Allow available chat, anchored comments, direct edits and useful control interaction. Collect retrievable outcomes at checkpoints; identify gaps instead of requiring manual copy/paste when a working integration exists. |
| E05 | Save portable review material | A checkout contains review prose, a standalone HTML explanation and accepted decisions. HTML opens without the provider, credentials or a running harness. Disable unavailable agent/chat actions clearly; preserve meaningful local controls and explanation. |
| E06 | Reconcile before relying on changed material | On save/proceed, handoff, resume and closure, compare current hosted/local content with the last common baseline. Merge disjoint changes; surface conflicting content. Do not overwrite either side or substitute stale execution inputs. |
| E07 | Preserve feedback provenance and decision authority | Retain substantive decisions and dispositions with source references. Project-designated owner, otherwise initiating user, may accept. AI replies, control selections and another collaborator's suggestions do not establish acceptance. |
| E08 | Recover interrupted transport without duplicate work | Persist request identity before sending. Identical resubmission returns its observed state; changed content under the same ID conflicts. A pending/unknown send is inspected, never blindly replayed. Resume the exact bound host session and verify its identity. |
| E09 | Keep mutation scopes explicit | Mordain changes only the plan. Cassian review-document mode owns named hosted review/document outputs. Helpers reject paths outside that bundle, symlink escapes and unexpected files. Preserve pre-existing content and unrelated edits. |
| E10 | Preserve IDD and worker independence | Discovery is separate from feature execution. Changes to reviewed IDD content return to its authoring/review flow. Seraphine receives only its existing Spec/API/test handoff, without review HTML, solution proposals, Page chats or inherited transcripts. |
| E11 | Provide a bounded local companion | OpenCode and Pi adapters support passage feedback, chat when tool restrictions are available, response display, direct editing of review prose, persistence, export and reconnect. Concurrent browser edits use revisions; no silent last-writer-wins overwrite. |
| E12 | Distribute and document truthful support | Generated skills contain the canonical contract and helper/resources. Routing setup remains independent of review resources. Native Claude commands, roles, aliases and hooks retain their contracts. Documentation distinguishes packaging checks, transport probes and live-host acceptance. |

### Edge behavior

These are proposed acceptance cases, not recorded stakeholder confirmations.

- **No callable integration:** retain full portable documents and collect feedback
  through the conversation; never claim that an uncalled artifact tool ran.
- **Comment listing is truncated:** retrieve the remainder where the API supports
  it. If completeness cannot be established, report partial coverage and do not
  claim that all feedback is reconciled. Detached selections require interpretation.
- **Page chat is separate:** its agent saves proposed outcomes to native Page
  content or comments for retrieval. Never use meeting-transcript APIs as a
  substitute for arbitrary Page chat history or assume the coding session resumed.
- **Hosted link is deleted or access is lost:** preserve the local explanation
  and checkpoint. Do not create a replacement or alter sharing without an
  explicit recovery choice. Already reconciled work remains inspectable.
- **Both sides change the same decision:** show both versions and the last
  common version; wait for the designated owner to resolve the specific conflict.
- **One side saves and the other fails:** keep an incomplete checkpoint with
  the observed successful side. Resume from current content and guards; never
  mark the checkpoint complete or blindly repeat a creation.
- **Timeout after sending:** record unknown delivery, inspect host history by
  request ID/session binding, and require a recovery decision if still ambiguous.
- **Session switches during a browser request:** reject the request; do not send
  it into the new session. Reopening the view does not itself accept a rebind.
- **Two browser tabs edit prose:** only a matching base revision can save. The
  second tab sees a conflict with its draft preserved for comparison.
- **Limits exceeded:** reject a request over 32 KiB, comment or selection over
  4,000 characters, review document over 256 KiB UTF-8, or checkpoint over 200
  substantive feedback entries. Offer explicit splitting/archival; never silently
  discard or truncate content and call it reconciled. Host-specific lower limits
  take precedence and must be reported.
- **Browser closes:** persisted review feedback survives. Unsaved browser drafts
  are described as unsaved, and cannot be presented as accepted decisions.
- **Tool-free review chat is unavailable:** keep reading, editing and commenting
  available locally and record why model chat is disabled.

## Boundaries

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

## Deliverables

| Surface | Required change and ownership |
| --- | --- |
| plugin/portable/references/collaborative-planning.md | Canonical review, ownership, reconciliation, capability and recovery contract |
| plugin/portable/scripts/review.py | Optional bounded local review/checkpoint CLI; public operations init, serve, inspect, checkpoint and export, with explicit root/plan/host selection |
| plugin/portable/resources/review/ | Shared HTML/UI and portable record schema/example; export has no mandatory host API |
| plugin/portable/SKILL.md and references/quest.md, hosts.md | Route planning/review handoffs through the contract without widening Mordain's writes |
| plugin/commands/quest.md | Native Claude review presentation and scoped writer handoff; retain native tool/dispatch conventions |
| plugin/agents/docs-writer.md | Explicit review-document mode, exact input/output/tool scope and creation permission; preserve post-green mode |
| scripts/build_portable.py | Bundle review resources into guildhall-quest; exclude them from unrelated guildhall-routing-setup copies |
| scripts/validate_portable.py and relevant packaging checks | Validate record/example agreement, resource links, generated inventory and host-independent packaging |
| tests/test_review*.py and browser fixtures | Independent contract tests for persistence, bounds, idempotency, conflict/recovery and path scope; UI behavior checks in an isolated browser fixture |
| plugin/skills/guildhall-quest/ | Regenerated complete bundle, including portable role adaptation |
| README.md, plugin/README.md, docs/installation.md, docs/contributing-agents.md, docs/guildhall/plans/README.md | User-facing setup, support matrix, write ownership, checkpoint/recovery and export guidance |
| Three plugin manifests | Increment aligned installer-facing versions when this behavior ships |
| docs/reviews/ | Implementation verification report with exact baseline/diff, checks, real-host gaps and acceptance status |

The review CLI must have no startup model call. Host/server/session arguments
and allowed document paths are validated before opening a listener or mutating
files. Read-only inspection reports status without changing checkpoints.
Checkpoint never accepts a decision or changes the main plan on its own;
Mordain applies accepted decisions to the plan from verified worker evidence.
The durable record preserves actual confirmed decisions separately from proposals.

Host-specific connector calls remain tool-discovered orchestration operations;
the Python helper does not scrape accounts, invent MCP tool names or store
connector credentials. A host lacking worker access to a native surface must
report that limitation and use a supported alternative.

## Validation

### Automated and isolated

- Independent behavior tests must cover every Expectation and edge case above.
  Observe attributable RED before implementation in a requested feature quest;
  existing passing spike probes are supporting evidence, not Spec coverage.
- Test request identities, interrupted sends, same-content retries, conflicting
  retries, exact session binding, restart recovery and retained draft state.
- Exercise all partial-save orderings, concurrent updates, unavailable hosted
  revisions, detached anchors, incomplete comment listings and access loss.
- Verify path containment, symlink refusal, protected-file preservation, strict
  size/count limits, loopback binding, origin/token checks, display escaping and
  absence of generic command/tool endpoints. Probe malicious-size inputs where
  parsing/patterns run on untrusted text.
- Verify offline exported HTML at narrow and desktop widths: editable content
  remains readable, meaningful local controls work, and unavailable chat actions
  explain the limitation. No network/provider dependency for core explanation.
- Verify ordinary quests do not acquire a Python requirement and routing setup
  does not absorb review resources unintentionally.
- Run the documented portable build/check, both validators, Python unit suite
  and diff checks. Use isolated installation probes only if packaging needs them.

### Host acceptance

Record each result separately; missing evidence remains pending.

| Host | Required live acceptance |
| --- | --- |
| Claude Code | Callable writer artifact access, native review interactions, feedback retrieval, portable export and reconciliation, unchanged quest hook behavior |
| Codex with Space | Native editable Page, selection comment, separate Page chat write-back, interactive embed, guarded update and saved repository checkpoint |
| OpenCode | Configured tool-free review session, local passage feedback and chat, direct prose edit, reconnect, checkpoint and offline export |
| Pi | Dedicated planning RPC session with tools disabled, same local workflow, exact session recovery and graceful shutdown |

Select existing reviewers from the eventual diff. Security and documentation
review remain required; the network/process/persistence path triggers reliability
and observability, the browser UI triggers accessibility/UI verification, and
package changes trigger plugin validation. Run the required closing technical
review after all writer changes. Do not infer enforcement or approval from a
passing syntax check, mocked model, screenshot, or package installation.

### Review before implementation

Confirm the scoped Cassian mode, checkpoint helper contract and proposed edge
behavior with the stakeholder through the planning Page. This document is the
concrete proposal to review; it does not manufacture content confirmation,
human peer review, IDD readiness or a quest invocation.
