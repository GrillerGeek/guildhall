# Collaborative planning feasibility review

- Issue: [64](https://github.com/GrillerGeek/guildhall/issues/64).
- Baseline: `1e2701d` on `Artifacts`.
- Scope: primary-agent technical review of the draft prose spec and existing
  repository contracts. This is not an independent Guildhall review, IDD
  readiness evidence or live-host certification.
- Spec: [implementation proposal](../plans/2026-10-18-collaborative-planning-spec.md).

## Findings addressed in the draft

### Native artifact tool access

Cassian's existing frontmatter permits Read, Write, Edit, Bash, Grep and Glob.
That allowlist excludes native artifact tools even when the main session has
them. The proposed review-document mode therefore needs an explicit `Artifact`
entry; merely describing artifact work in its prompt would not enable the tool.

Claude's official subagent documentation lists Artifact as available to
background subagents and explains allowlist filtering. It supports the proposed
worker path without removing the allowlist, widening Mordain's writes or changing
the native hook. Account availability and actual worker tool access still need
an installed-host exercise. Sources: [subagent capabilities](https://code.claude.com/docs/en/sub-agents#control-subagent-capabilities)
and [artifact availability](https://code.claude.com/docs/en/artifacts#availability).

The repository's `scripts/validate_plugin.py` KNOWN_TOOLS set does not yet list
Artifact. The spec now names that validator update and a focused fixture so the
new tool allowance does not ship as an unexplained warning. Unknown-tool warnings
must remain in place.

Portable workers must discover the Page connector in their actual tool pool.
A parent session's successful connector call is not proof of worker access.
Do not fork the parent transcript into Seraphine or route the proposal through
the test author's context to obtain a tool.

### Request and document limits

The draft allowed 256 KiB review prose but capped every request at 32 KiB.
That would prevent saving a supported full document through the browser.
The spec now distinguishes 32 KiB feedback/control requests from document saves
bounded by both a 256 KiB decoded document limit and a 264 KiB serialized request
limit. Error handling must preserve the unsaved draft.

### Checkpoint and delivery states

The first draft described partial-save recovery without defining its states.
It now distinguishes local/hosted changes, conflicts, unavailable content and
which side remains to be saved. Feedback delivery has a separate state machine;
unknown delivery cannot be mistaken for failure-before-send or automatic retry.
Neither a clean checkpoint nor a received answer implies an accepted decision.

Snapshots are bounded to a last-common baseline and one pending reconciliation
snapshot. Unknown hosted revision metadata stays null and uses the observed
exported-content hash. This avoids assuming equal provider/file serialization.

### Optional runtime and timeouts

Native-only review paths must be able to write the record and portable review
using their supported host/file tools. Python remains optional unless the local
companion or automated checkpoint helper is selected. Startup and host-call
deadlines are explicit; cancellation retains unknown delivery until reconciled.

### Packaging cross-contamination

`scripts/build_portable.py` currently copies all portable scripts/resources into
the routing-setup bundle. Adding review resources without changing that selection
would install the companion into an unrelated skill. The spec already requires
an explicit build filter and independent copied-bundle checks. Retain this as a
required implementation test rather than relying on directory naming alone.

## Ordered implementation sequence

1. **Record and persistence contract.** Define the public version-1 record,
   path/size bounds, clean/partial/conflict states and immutable inputs. Write
   behavior tests before the optional helper implementation. No host process or
   model call is needed for this step.
2. **Checkpoint, inspection and export.** Implement bounded file operations,
   baseline comparison, guarded saves, partial-state recovery and standalone
   HTML. Inspection must not mutate state. Verify export without network access.
3. **Local browser companion.** Add direct prose editing, selected-passage
   feedback, revision conflicts and retained drafts. Verify loopback binding,
   Host/Origin/token checks and display escaping with an isolated fixture.
4. **Host transports.** Implement OpenCode's explicit session binding and Pi's
   dedicated planning RPC session, completion/cancellation, request identities
   and ambiguous-delivery recovery. Use synthetic transports first; retain
   real-host/provider acceptance as separate evidence.
5. **Guildhall handoffs.** Add Cassian's scoped review-document mode and native
   Artifact allowance; update native/portable planning guidance. Preserve the
   existing hooks, roster, post-green documentation behavior and test-author
   independence.
6. **Packaging and documentation.** Regenerate complete quest resources, keep
   routing setup independent, align package versions and run required checks.
7. **Host acceptance and closing review.** Verify each actual interaction path,
   report inaccessible host capabilities, and select the independent reviewers
   required by the implementation diff. A passing synthetic probe cannot stand
   in for a hosted collaboration run.

## Remaining stakeholder review

The architecture keeps the already agreed durable-artifact and local-companion
scope. The proposed Cassian mode, helper interface and detailed edge behavior
are now concrete enough to review on the existing planning Page. No spec
confirmation or execution authorization is inferred from this technical pass.
